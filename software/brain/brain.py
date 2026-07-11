"""Parviz brain daemon: the LLM is the single source of truth for behavior.

The Tier-2 loop from docs/AWARENESS.md, live: every tick it assembles a
digest from EVERYTHING the robot senses right now --

  /dev/shm/parviz_vision.json   all YuNet + landmarker features (presence,
                                position, size, facing, smile, ear,
                                mouth_open, brow_gap, visible_expression,
                                confidences, timings)
  procfs/sysfs                  cpu temp/load, memory, uptime, time of day
  event ring                    person arrived/left, expression changes,
                                the brain's own recent actions

-- sends it to the local llama-server (Qwen3-0.6B, the schema-constrained
v2 prompt from scenarios.py), and publishes the decision to
/tmp/parviz_decision.json. The face APPLIES those actions (expression,
gaze, say) and treats the file's mtime as the brain heartbeat: stale =>
the face falls asleep by itself. `log` actions append to journal.log;
`escalate`/`move` are journaled stubs until the big-brain hook and motors
exist.

Run:      python3 brain.py            (loop; also parviz-brain.service)
One tick: python3 brain.py --once
"""

import argparse
import json
import os
import time

from scenarios import ask   # v2 prompt + few-shots + grammar schema

VISION_JSON = "/dev/shm/parviz_vision.json"
DECISION_FILE = "/tmp/parviz_decision.json"
HERE = os.path.dirname(os.path.abspath(__file__))
JOURNAL = os.path.join(HERE, "journal.log")
HOST = os.environ.get("PARVIZ_LLM", "127.0.0.1:8081")
TICK_S = 15.0   # inference is 7-15 s; shorter ticks ran the LLM at 100%
                # duty and pushed the (fanless) Pi past 80C


def read_vision():
    try:
        if time.time() - os.path.getmtime(VISION_JSON) > 4.0:
            return None
        with open(VISION_JSON) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def read_sys():
    out = {}
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            out["temp_c"] = int(f.read()) // 1000
    except OSError:
        pass
    try:
        with open("/proc/loadavg") as f:
            out["load_pct"] = int(float(f.read().split()[0])
                                  / (os.cpu_count() or 4) * 100)
    except OSError:
        pass
    try:
        mi = {}
        with open("/proc/meminfo") as f:
            for line in list(f)[:3]:
                k, v = line.split(":")
                mi[k] = int(v.split()[0])
        out["mem_pct"] = int(100 - mi["MemAvailable"] / mi["MemTotal"] * 100)
    except (OSError, KeyError, ValueError):
        pass
    return out


class Events:
    """Tiny ring of notable transitions so the digest has a memory."""

    def __init__(self, keep=6):
        self.ring = []
        self.keep = keep
        self._present = None
        self._vexpr = None

    def add(self, text):
        self.ring = (self.ring + [(time.time(), text)])[-self.keep:]

    def update_from_vision(self, vis):
        present = bool(vis and vis.get("person_present"))
        if present != self._present and self._present is not None:
            self.add("person arrived" if present else "person left")
        self._present = present
        vexpr = (vis or {}).get("visible_expression")
        if present and vexpr and vexpr != self._vexpr:
            self.add(f"person now looks {vexpr}")
        self._vexpr = vexpr

    def line(self):
        if not self.ring:
            return "nothing notable recently"
        now = time.time()
        return "; ".join(f"{t} ({int(now - ts)}s ago)"
                         for ts, t in self.ring[-3:])


def build_digest(vis, sy, events, last_actions, cur_expr):
    if vis and vis.get("person_present"):
        person = (f'present, {vis["n_faces"]} face(s), conf {vis["conf"]}, '
                  f'position x{vis["cx"]:+.2f} y{vis["cy"]:+.2f} of camera '
                  f'view, size {vis["size"]}, '
                  f'{"FACING the robot" if vis.get("facing_camera") else "not facing the robot"}')
        if "visible_expression" in vis:
            person += (f'; looks {vis["visible_expression"]} '
                       f'(smile {vis.get("smile", 0)}, eye-openness '
                       f'{vis.get("ear", 0)}'
                       f'{", EYES CLOSED" if vis.get("eyes_closed") else ""}'
                       f', mouth_open {vis.get("mouth_open", 0)}, brow_gap '
                       f'{vis.get("brow_gap", 0)})')
        person += (f'; head-aim suggestion pan {vis.get("pan_deg", 0)} '
                   f'tilt {vis.get("tilt_deg", 0)}')
    elif vis:
        person = "none visible"
    else:
        person = "vision offline"
    ev = events.line()
    acted = (", ".join(last_actions[-3:])) if last_actions else "none yet"
    return "\n".join([
        f"EVENT: {ev}",
        f"person: {person}",
        "sound: mics not wired yet",
        f'env: cpu {sy.get("temp_c", "?")}C load {sy.get("load_pct", "?")}% '
        f'mem {sy.get("mem_pct", "?")}% | wall power ok',
        "sonar: not wired | tracks: not wired | look_at moves the EYES "
        "only for now",
        f'time {time.strftime("%H:%M %a")} | current face expression: '
        f'{cur_expr} | my recent actions: {acted}',
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--tick", type=float, default=TICK_S)
    args = ap.parse_args()

    events = Events()
    last_actions = []
    cur_expr = "neutral"
    jf = open(JOURNAL, "a")

    def journal(line):
        jf.write(f"{time.strftime('%m-%d %H:%M:%S')} {line}\n")
        jf.flush()

    journal("brain up")
    while True:
        t0 = time.monotonic()
        vis = read_vision()
        events.update_from_vision(vis)
        digest = build_digest(vis, read_sys(), events, last_actions,
                              cur_expr)
        try:
            parsed, ok, dt, usage = ask(HOST, digest, temperature=0.2,
                                        timeout=60, prompt="v2")
        except Exception as e:
            journal(f"LLM unreachable: {e}")   # no decision write ->
            time.sleep(3)                      # face falls asleep on stale
            if args.once:
                break
            continue
        if ok:
            verbs = []
            for a in parsed.get("actions", []):
                if not isinstance(a, dict):
                    continue
                do = a.get("do")
                verbs.append(do)
                if do == "set_expression" and a.get("name"):
                    cur_expr = a["name"]
                elif do == "log":
                    journal(f"LLM log: {a.get('note', '')}")
                elif do == "escalate":
                    journal(f"ESCALATE (stub): {a.get('task', '')}")
                    events.add("I escalated a task to the big brain")
                elif do == "move":
                    journal(f"move (no motors yet): {a}")
            payload = dict(parsed)
            payload["ts"] = time.time()
            tmp = DECISION_FILE + ".tmp"
            with open(tmp, "w") as f:
                json.dump(payload, f)
            os.replace(tmp, DECISION_FILE)
            last_actions.append("+".join(v for v in verbs if v) or "?")
            last_actions = last_actions[-6:]
            journal(f"{dt:5.1f}s {verbs} :: "
                    f"{str(parsed.get('reason', ''))[:80]}")
        else:
            journal(f"unparseable answer ({dt:.1f}s)")
        if args.once:
            print(digest)
            print(json.dumps(parsed, indent=1))
            break
        time.sleep(max(1.0, args.tick - (time.monotonic() - t0)))


if __name__ == "__main__":
    main()

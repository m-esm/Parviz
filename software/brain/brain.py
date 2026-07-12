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
import threading
import time

import llm
from scenarios import ask, ask_chain   # prompts + few-shots + schema

VISION_JSON = "/dev/shm/parviz_vision.json"
SPEECH_JSON = "/dev/shm/parviz_speech.json"
DECISION_FILE = "/tmp/parviz_decision.json"
READ_TRIGGER = "/dev/shm/parviz_read_text"   # read_text -> perception OCR
HERE = os.path.dirname(os.path.abspath(__file__))
JOURNAL = os.path.join(HERE, "journal.log")
# Comma-separated FAILOVER CHAIN of backend specs (llm.py): e.g.
# "claude-live:,127.0.0.1:8081" = cloud sonnet session, local Qwen when
# offline. Single spec = no failover. PARVIZ_BIG is the Tier-3 deep
# thinker the escalate action calls (one-shot, cloud-only by design).
HOST = os.environ.get("PARVIZ_LLM", "127.0.0.1:8081")
BIG = os.environ.get("PARVIZ_BIG", "claude:fable")
COOL_ENTER = float(os.environ.get("PARVIZ_COOL_ENTER", 80.0))
COOL_EXIT = float(os.environ.get("PARVIZ_COOL_EXIT", 70.0))
COOLING_MARK = "/dev/shm/parviz_cooling"


def cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return int(f.read()) / 1000
    except OSError:
        return None
TICK_IDLE_S = 1.0    # cycle cadence: re-evaluate inputs every second
TICK_MIN_S = 1.0     # cooldown after a tick; the skip/cache layer is
                     # what keeps 1 Hz cycles off the LLM (and thermals)
# PERMANENT decision cache (user): never expires by time, persists to
# disk across restarts, cleared only manually -- touch CACHE_CLEAR (or
# run brain.py --clear-cache). Size-capped, oldest-first eviction.
CACHE_FILE = os.path.join(HERE, "decision_cache.json")
CACHE_CLEAR = "/dev/shm/parviz_cache_clear"
CACHE_MAX = 4096


def cache_load():
    try:
        with open(CACHE_FILE) as f:
            return dict(json.load(f))
    except (OSError, ValueError):
        return {}


def cache_save(cache):
    tmp = CACHE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cache, f)
    os.replace(tmp, CACHE_FILE)


def semantic_key(vis, sy, events, speech_ts=None):
    """The SEMANTIC inputs of a tick: what should actually change a
    decision. Raw digests always differ (clock, jittering floats), so
    the skip/cache layer keys on this instead: person state, coarse
    distance band, event ring texts, bucketed health, hour of day."""
    v = vis or {}
    return json.dumps([
        v.get("person_present") if vis else "offline",
        v.get("person_name"),
        v.get("visible_expression"),
        v.get("gesture"),
        v.get("pose"),
        bool(v.get("body_present")),
        sorted(v.get("objects") or []),
        v.get("held_object"),
        v.get("ocr_ts"),        # each OCR read is one fresh LLM tick
        speech_ts,              # each finished utterance likewise
        bool(v.get("facing_camera")),
        bool(v.get("eyes_closed")),
        int((v.get("size") or 0) * 3),   # coarse distance band (flap-shy)
        [t for _, t in events.ring[-3:]],
        None if sy.get("temp_c") is None else int(sy["temp_c"] // 10),
        None if sy.get("mem_pct") is None else int(sy["mem_pct"] // 20),
        time.strftime("%H"),
    ])


def cacheable(parsed):
    """Only pure decisions (expression/say/log/nothing) may be replayed;
    escalate, move and read_text have side effects, must re-run for real."""
    return not any(isinstance(a, dict)
                   and a.get("do") in ("escalate", "move", "read_text")
                   for a in parsed.get("actions", []))


def read_vision():
    try:
        if time.time() - os.path.getmtime(VISION_JSON) > 4.0:
            return None
        with open(VISION_JSON) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def read_speech():
    """Voice daemon state, or None if the ears are down/stale."""
    try:
        if time.time() - os.path.getmtime(SPEECH_JSON) > 3.0:
            return None
        with open(SPEECH_JSON) as f:
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
        self._name = None

    def add(self, text):
        self.ring = (self.ring + [(time.time(), text)])[-self.keep:]

    def update_from_vision(self, vis):
        present = bool(vis and vis.get("person_present"))
        name = (vis or {}).get("person_name")
        if present != self._present and self._present is not None:
            self.add(f"{name or 'person'} arrived" if present
                     else "person left")
        self._present = present
        if present and name and name != self._name:
            if name == "stranger":
                self.add("an UNRECOGNIZED person is here")
            elif name != "unenrolled":
                self.add(f"recognized {name}")
        self._name = name if present else None
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


SPEECH_FRESH_S = 12.0   # how long an utterance stays in the digest


def build_digest(vis, sy, events, last_actions, cur_expr, speech=None):
    if vis and vis.get("person_present"):
        who = vis.get("person_name")
        who_s = f" ({who})" if who else ""
        person = (f'present{who_s}, {vis["n_faces"]} face(s), '
                  f'conf {vis["conf"]}, '
                  f'position x{vis["cx"]:+.2f} y{vis["cy"]:+.2f} of camera '
                  f'view, size {vis["size"]}, '
                  f'{"FACING the robot" if vis.get("facing_camera") else "not facing the robot"}')
        if vis.get("pose") and vis["pose"] != "upright":
            person += f'; pose {vis["pose"]}'
        if "visible_expression" in vis:
            person += (f'; looks {vis["visible_expression"]} '
                       f'(smile {vis.get("smile", 0)}, eye-openness '
                       f'{vis.get("ear", 0)}'
                       f'{", EYES CLOSED" if vis.get("eyes_closed") else ""}'
                       f', mouth_open {vis.get("mouth_open", 0)}, brow_gap '
                       f'{vis.get("brow_gap", 0)})')
        if vis.get("gesture"):
            person += f'; gesture {vis["gesture"]}'
    elif vis and vis.get("body_present"):
        person = (f'BODY visible but no face (turned away?)'
                  f'{"; pose " + vis["pose"] if vis.get("pose") else ""}')
    elif vis:
        person = "none visible"
    else:
        person = "vision offline"
    objs = (vis or {}).get("objects") or []
    scene = ", ".join(o.replace("_", " ") for o in objs) or "nothing notable"
    if (vis or {}).get("held_object"):
        scene += (f'; a {vis["held_object"].replace("_", " ")} is HELD UP '
                  f'close to the camera')
    sp = speech or {}
    heard_age = (time.time() - sp["final_ts"]) if sp.get("final_ts") else 1e9
    if sp.get("partial"):
        sound = f'user is speaking right now: "{sp["partial"]}..."'
    elif sp.get("final") and heard_age < SPEECH_FRESH_S:
        sound = f'user said ({int(heard_age)}s ago): "{sp["final"]}"'
    elif speech is not None:
        sound = "quiet (ears live)"
    else:
        sound = "ears offline"
    # EVENT leads with the CURRENT salient situation (tiny models act on
    # the top line); the ring history follows inside it. SPEECH OUTRANKS
    # everything: being spoken to is the most salient thing there is.
    if sp.get("final") and heard_age < SPEECH_FRESH_S:
        ev = f'the user SPOKE to me: "{sp["final"]}"'
    elif vis and vis.get("person_present"):
        who = vis.get("person_name")
        ges = (f', gesture {vis["gesture"]}'
               if vis.get("gesture") and vis["gesture"] != "none" else "")
        ev = (f'person{f" ({who})" if who else ""} present: looks '
              f'{vis.get("visible_expression", "unknown")}{ges}, '
              f'{"FACING the robot" if vis.get("facing_camera") else "not facing"}')
    else:
        ev = events.line()
    acted = (", ".join(last_actions[-3:])) if last_actions else "none yet"
    lines = [
        f"EVENT: {ev}",
        f"person: {person}",
        f"scene: {scene}",
    ]
    if (vis or {}).get("ocr_ts"):
        age = int(time.time() - vis["ocr_ts"])
        lines.append(
            f'text (read {age}s ago): "{vis["ocr_text"][:200]}"'
            if vis.get("ocr_text")
            else f"text: OCR ran {age}s ago, no readable text found")
    return "\n".join(lines + [
        f"sound: {sound}",
        f'env: cpu {sy.get("temp_c", "?")}C load {sy.get("load_pct", "?")}% '
        f'mem {sy.get("mem_pct", "?")}% | wall power ok',
        "sonar: not wired | tracks: not wired",
        f'time {time.strftime("%H:%M %a")} | current face expression: '
        f'{cur_expr} | my recent actions: {acted}',
    ])


def _event_wait(tick_s, t0, vis):
    """Cooldown, then EVENT-DRIVEN wait: return immediately when the
    person's presence, expression or gesture changes; heartbeat at
    tick_s otherwise."""
    time.sleep(max(0.5, TICK_MIN_S - (time.monotonic() - t0)))
    key = ((vis or {}).get("person_present"),
           (vis or {}).get("visible_expression"),
           (vis or {}).get("gesture"))
    waited = time.monotonic() - t0
    while waited < tick_s:
        v2 = read_vision()
        if ((v2 or {}).get("person_present"),
                (v2 or {}).get("visible_expression"),
                (v2 or {}).get("gesture")) != key:
            break
        time.sleep(1.0)
        waited = time.monotonic() - t0


_TIER3_BUSY = threading.Lock()


def tier3(task, digest, journal, events):
    """Run an escalate action on the big model (BIG, default fable) in a
    background thread; its actions publish as a follow-up decision that
    the face executes like any tick. Cloud-only: offline it just
    journals the failure. Single-flight: a second escalate while one
    runs is dropped."""
    if not _TIER3_BUSY.acquire(blocking=False):
        journal(f"tier3 busy, dropped: {task[:60]}")
        return

    def run():
        try:
            ask_text = (
                f"TIER-3 ESCALATION. The ambient brain wants: {task}\n\n"
                f"Situation digest:\n{digest}\n\n"
                "Think as deeply as needed, then answer in the same JSON "
                "action format; say/set_expression will be executed by "
                "the face. Do not escalate again.")
            parsed, ok, dt, _usage = ask(BIG, ask_text, timeout=240,
                                         prompt="v3")
            if ok:
                payload = dict(parsed)
                payload.update(ts=time.time(), latency_s=round(dt, 1),
                               backend=BIG, tier=3)
                tmp = DECISION_FILE + ".tmp"
                with open(tmp, "w") as f:
                    json.dump(payload, f)
                os.replace(tmp, DECISION_FILE)
                journal(f"tier3 {dt:5.1f}s :: "
                        f"{str(parsed.get('reason', ''))[:80]}")
                events.add("the big brain answered")
            else:
                journal(f"tier3 unparseable ({dt:.1f}s)")
        except Exception as e:
            journal(f"tier3 failed: {str(e)[:120]}")
            events.add("big brain unavailable")
        finally:
            _TIER3_BUSY.release()

    threading.Thread(target=run, daemon=True).start()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--tick", type=float, default=TICK_IDLE_S,
                    help="idle heartbeat interval (events tick sooner)")
    ap.add_argument("--clear-cache", action="store_true",
                    help="empty the permanent decision cache and exit")
    args = ap.parse_args()
    if args.clear_cache:
        try:
            os.remove(CACHE_FILE)
        except OSError:
            pass
        with open(CACHE_CLEAR, "w") as f:   # running daemon clears too
            f.write("1")
        print("decision cache cleared")
        return

    events = Events()
    last_actions = []
    cur_expr = "neutral"
    cur_backend = None
    last_key, last_payload = None, None   # skip layer
    last_speech_ts = None                 # utterances already evented
    cache, skips = cache_load(), 0        # permanent decision cache
    ticks = llm_calls = hits = skips_total = 0   # HUD stats
    hit_logged = 0.0
    t_up = time.time()

    def extras():
        """Live brain internals, refreshed into every published
        decision; the face's BRAIN panel renders these."""
        return {
            "stats": {"ticks": ticks, "llm": llm_calls, "hits": hits,
                      "skips": skips_total, "cache": len(cache)},
            "broken": llm.broken(),
            "t3": "busy" if _TIER3_BUSY.locked() else None,
            "brain_up_s": int(time.time() - t_up),
        }
    jf = open(JOURNAL, "a")

    def journal(line):
        jf.write(f"{time.strftime('%m-%d %H:%M:%S')} {line}\n")
        jf.flush()

    journal(f"brain up (llm {HOST})")
    cooling = False
    while True:
        t0 = time.monotonic()
        # THERMAL CIRCUIT BREAKER: pause all LLM work while the SoC is
        # hot; the marker file tells the face to sweat instead of doze.
        t = cpu_temp()
        if cooling:
            if t is not None and t <= COOL_EXIT:
                cooling = False
                try:
                    os.remove(COOLING_MARK)
                except OSError:
                    pass
                journal(f"cooled down to {t:.0f}C, resuming")
            else:
                with open(COOLING_MARK, "w") as f:
                    f.write(f"{t or 0:.0f}")
                time.sleep(2)
                continue
        elif t is not None and t >= COOL_ENTER:
            cooling = True
            journal(f"COOLING DOWN: {t:.0f}C >= {COOL_ENTER:.0f}C, "
                    "brain paused")
            continue
        vis = read_vision()
        events.update_from_vision(vis)
        sy = read_sys()
        speech = read_speech()
        if (speech and speech.get("final_ts")
                and speech["final_ts"] != last_speech_ts
                and time.time() - speech["final_ts"] < SPEECH_FRESH_S):
            last_speech_ts = speech["final_ts"]
            events.add(f'user said: "{speech["final"][:60]}"')
        digest = build_digest(vis, sy, events, last_actions, cur_expr,
                              speech)
        skey = semantic_key(vis, sy, events, last_speech_ts)
        ticks += 1

        # MANUAL cache clear (the only way it empties): also drops the
        # skip state so the very next tick re-asks the LLM.
        if os.path.exists(CACHE_CLEAR):
            try:
                os.remove(CACHE_CLEAR)
            except OSError:
                pass
            cache = {}
            cache_save(cache)
            last_key, last_payload = None, None
            journal("cache CLEARED manually")

        # SKIP: inputs unchanged since the last decision -> no LLM call;
        # re-touch the decision file (marked cached, the face keeps its
        # heartbeat but does not re-speak) and wait for a change.
        if skey == last_key and last_payload is not None and not args.once:
            skips_total += 1
            last_payload.update(ts=time.time(), cached=True, **extras())
            tmp = DECISION_FILE + ".tmp"
            with open(tmp, "w") as f:
                json.dump(last_payload, f)
            os.replace(tmp, DECISION_FILE)
            skips += 1
            if skips in (1, 30) or skips % 90 == 0:
                journal(f"inputs unchanged, {skips} ticks skipped")
            _event_wait(args.tick, t0, vis)
            continue
        skips = 0

        # CACHE: inputs seen before -> replay that decision, forever
        # (never cached: escalate/move/read_text). cur_expr still
        # updates so the digest stays truthful.
        hit = cache.get(skey)
        if hit is not None and not args.once:
            hits += 1
            parsed = hit[0]
            for a in parsed.get("actions", []):
                if (isinstance(a, dict) and a.get("do") == "set_expression"
                        and a.get("name")):
                    cur_expr = a["name"]
            payload = dict(parsed)
            payload.update(ts=time.time(), cached=True,
                           backend=hit[1], latency_s=0.0, **extras())
            tmp = DECISION_FILE + ".tmp"
            with open(tmp, "w") as f:
                json.dump(payload, f)
            os.replace(tmp, DECISION_FILE)
            last_payload, last_key = payload, skey
            if time.time() - hit_logged > 30:   # 1 Hz flaps: log sparsely
                hit_logged = time.time()
                journal(f"cache hit :: "
                        f"{str(parsed.get('reason', ''))[:60]}")
            _event_wait(args.tick, t0, vis)
            continue

        llm_calls += 1
        try:
            parsed, ok, dt, usage, backend, note = ask_chain(
                HOST, digest, temperature=0.2, timeout=60, prompt="v3")
        except Exception as e:
            journal(f"LLM unreachable: {e}")   # no decision write ->
            time.sleep(3)                      # face falls asleep on stale
            if args.once:
                break
            continue
        if note:
            journal(f"failover: {note}")
        if backend != cur_backend:
            journal(f"backend -> {backend}")
            cur_backend = backend
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
                    journal(f"ESCALATE -> {BIG}: {a.get('task', '')}")
                    events.add("I escalated a task to the big brain")
                    tier3(str(a.get("task", "")), digest, journal, events)
                elif do == "move":
                    journal(f"move (no motors yet): {a}")
                elif do == "read_text":
                    try:
                        with open(READ_TRIGGER, "w") as f:
                            f.write("1")
                        journal("read_text -> OCR triggered")
                        events.add("I am reading the text shown to me")
                    except OSError as e:
                        journal(f"read_text trigger failed: {e}")
            payload = dict(parsed)
            payload["ts"] = time.time()
            payload["latency_s"] = round(dt, 1)
            payload["backend"] = backend
            payload.update(**extras())
            tm = (usage or {}).get("timings") or {}
            if tm:
                payload["prompt_ms"] = round(tm.get("prompt_ms", 0))
                payload["gen_ms"] = round(tm.get("predicted_ms", 0))
            tmp = DECISION_FILE + ".tmp"
            with open(tmp, "w") as f:
                json.dump(payload, f)
            os.replace(tmp, DECISION_FILE)
            last_actions.append("+".join(v for v in verbs if v) or "?")
            last_actions = last_actions[-6:]
            last_payload, last_key = payload, skey
            if cacheable(parsed):
                while len(cache) >= CACHE_MAX:   # oldest insertion out
                    cache.pop(next(iter(cache)))
                cache[skey] = (parsed, backend)
                cache_save(cache)
            journal(f"{dt:5.1f}s {verbs} :: "
                    f"{str(parsed.get('reason', ''))[:80]}")
        else:
            journal(f"unparseable answer ({dt:.1f}s)")
        if args.once:
            print(digest)
            print(json.dumps(parsed, indent=1))
            break
        _event_wait(args.tick, t0, vis)


if __name__ == "__main__":
    main()

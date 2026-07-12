"""Parviz behavior-brain simulator: sensor digests -> LLM -> actions.

Simulates the Tier-2 loop from docs/AWARENESS.md before any of the real
sensors exist: build a world-state SNAPSHOT covering the full documented
sensor suite (mics, camera, mmWave, IMU, vibration, BME688 env, sonar,
cliff, touch, odometry/pose), render it as a compact text digest, ask the
local LLM what Parviz should do, and parse the constrained-JSON answer.

Run all scenarios against the Pi's llama-server:
    python3 scenarios.py --host moshe-pi5-2gb.local:8081
One scenario, several times (consistency probing):
    python3 scenarios.py --scenario person_approaches --runs 5
Results append to results/<tag>.jsonl for later behavior benchmarking;
each scenario carries `expect` hints (verbs that a sane brain should
choose) so a scorer can grade runs later.

stdlib only (urllib), so it runs on the Pi as-is.
"""

import argparse
import copy
import json
import os
import time

import llm

HERE = os.path.dirname(os.path.abspath(__file__))

SYSTEM_PROMPT = """\
You are the behavior brain of Parviz, a small tracked desk robot with a \
screen face (two orange eyes), a pan/tilt head with a camera, two ear \
microphones, and tank tracks. You receive a sensor digest and decide what \
Parviz does RIGHT NOW.

Rules:
- Safety reflexes (cliff stop, obstacle stop, over-tilt motor cut) run \
below you and already acted; never contradict them, never drive toward a \
reported cliff or obstacle.
- Parviz is calm. When nothing needs attention, do_nothing.
- Speak rarely and briefly. Do not narrate routine events.
- Only escalate to the big AI for complex tasks (scene understanding, \
real conversation, planning) or when the user explicitly asks.
- pan: positive = right, negative = left (degrees, max 88). tilt: \
positive = up, negative = down (max 30). Sounds/objects on the LEFT need \
negative pan.

Respond with ONLY a JSON object, no other text:
{"actions": [<action>, ...], "reason": "<one short sentence>"}
Each <action> is one of:
{"do": "do_nothing"}
{"do": "set_expression", "name": "neutral|happy|sad|surprised|sleepy|concerned|angry|sick|look_left|look_right|look_up|look_down"}
{"do": "look_at", "pan_deg": <-88..88>, "tilt_deg": <-30..30>}
{"do": "say", "text": "<short sentence>"}
{"do": "move", "kind": "forward|backward|turn_left|turn_right|stop", "amount": <cm or deg>}
{"do": "log", "note": "<short note>"}
{"do": "escalate", "task": "<what the big AI should do>"}"""

SYSTEM_PROMPT_V2 = """\
You are the decision module of Parviz, a small desk robot: screen face \
with two orange eyes, pan/tilt camera head, two ear mics, tank tracks.
Input: a sensor digest. The EVENT line is what just changed; react to it.
Output: ONLY JSON {"actions": [...], "reason": "..."} with 1-2 actions:
{"do":"do_nothing"} | {"do":"set_expression","name":"neutral|happy|sad|surprised|sleepy|concerned|angry|sick"} | \
{"do":"look_at","pan_deg":-88..88,"tilt_deg":-30..30} | {"do":"say","text":"..."} | \
{"do":"move","kind":"forward|backward|turn_left|turn_right|stop","amount":n} | \
{"do":"log","note":"..."} | {"do":"escalate","task":"..."}

Decision guide:
- Default is do_nothing. No event, no action.
- Person appears or approaches: look_at them, friendly expression.
- User speaks a command: obey exactly (look/move where they said).
- User asks something you cannot answer from this digest (needs seeing, \
knowledge, or planning): escalate with the task.
- Environment/health warning the user should hear: say it, briefly, once.
- Sudden noise or shock: look toward it, surprised expression.
- pan_deg: LEFT = negative, RIGHT = positive. tilt_deg: up = positive.
- Safety reflexes already ran below you; never drive toward a cliff or \
obstacle, never fight a reflex stop."""

_V2_DIGEST_A = ("EVENT: nothing new; user typing quietly for 20 min\n"
                "person: known user at desk 65cm (mmWave still)\n"
                "sound: L 35dB R 35dB, centered, no speech\n"
                "env: 23.0C 42%RH air good | imu level | touch none\n"
                "sonar front 120cm rear 90cm, cliffs ok | head pan 0 tilt 0")
_V2_DIGEST_B = ("EVENT: footsteps + person entering view on the LEFT "
                "(pan negative)\n"
                "person: approaching, 150cm (mmWave)\n"
                "sound: L 52dB R 39dB, from LEFT, no speech\n"
                "env: 23.5C 44%RH air good | imu level | touch none\n"
                "sonar front 130cm rear 95cm, cliffs ok | head pan 0 tilt 0")
_V2_DIGEST_C = ('EVENT: user asks: "Parviz, what is the weather going to '
                'be tomorrow?" [WAKE WORD]\n'
                "person: known user 70cm, looking at robot\n"
                "sound: L 47dB R 47dB, centered\n"
                "env: 23.2C 43%RH air good | imu level | touch none\n"
                "sonar front 125cm rear 92cm, cliffs ok | head pan 0 tilt 0")
_V2_DIGEST_D = ("EVENT: humidity crossed 70% and still rising\n"
                "person: known user at desk 60cm (mmWave still)\n"
                "sound: L 36dB R 36dB, centered, no speech\n"
                "env: 26.8C 71%RH air fair | imu level | touch none\n"
                "sonar front 118cm rear 88cm, cliffs ok | head pan 0 tilt 0")
FEW_SHOT_V2 = [
    {"role": "user", "content": _V2_DIGEST_A},
    {"role": "assistant", "content": json.dumps({
        "actions": [{"do": "do_nothing"}],
        "reason": "Nothing changed; user is working."})},
    {"role": "user", "content": _V2_DIGEST_B},
    {"role": "assistant", "content": json.dumps({
        "actions": [{"do": "look_at", "pan_deg": -40, "tilt_deg": 10},
                    {"do": "set_expression", "name": "happy"}],
        "reason": "Someone approaches from the left; turn left to greet."})},
    {"role": "user", "content": _V2_DIGEST_C},
    {"role": "assistant", "content": json.dumps({
        "actions": [{"do": "escalate",
                     "task": "answer the user's weather question"}],
        "reason": "Needs outside knowledge I do not have."})},
    {"role": "user", "content": _V2_DIGEST_D},
    {"role": "assistant", "content": json.dumps({
        "actions": [{"do": "say",
                     "text": "Humidity is over 70 percent, maybe crack a "
                             "window."},
                    {"do": "log", "note": "humidity 71% rising"}],
        "reason": "Environment warning worth one brief heads-up."})},
]

SYSTEM_PROMPT_V3 = """\
You are the decision module of Parviz, a small desk robot: screen face \
with two orange eyes, camera, two ear mics, tank tracks.
Input: a sensor digest. Output: ONLY JSON {"actions": [...], "reason": \
"..."} with 1-2 actions:
{"do":"do_nothing"} | {"do":"set_expression","name":"neutral|happy|sad|surprised|sleepy|concerned|angry|sick"} | \
{"do":"say","text":"..."} | \
{"do":"move","kind":"forward|backward|turn_left|turn_right|stop","amount":n} | \
{"do":"log","note":"..."} | {"do":"escalate","task":"..."} | \
{"do":"read_text"}
Keep "reason" under 10 words. The eyes track people by themselves; you \
do NOT control gaze.

Rules, in priority order:
0. The user SPOKE to you (EVENT/sound says so): ANSWER with say --
this is a real conversation, be brief, natural and warm; add a
matching expression. Transcripts are lowercase ASR with occasional
mangled words ("pavas" and similar = your name); answer the intent.
If your recent actions show you already answered this exact
utterance, do not answer it again.
1. The person shows a hand GESTURE: open_palm (wave/hello) -> happy +
say a short greeting; thumbs_up -> happy; thumbs_down -> sad;
victory -> happy; pointing -> surprised.
2. A person is PRESENT: set_expression MATCHING their visible emotion:
happy->happy, surprised->surprised, sad->concerned, eyes closed->
concerned, neutral->neutral.
3. The person just LEFT: set_expression sad.
4. Nobody around and it is late (after 23:00) or has been quiet long:
set_expression sleepy.
5. The user asks something needing sight/knowledge/planning: escalate.
6. Environment problem (cpu over 80C, memory over 90%): log it.
7. Only when nothing at all needs attention: do_nothing.

The person line may name WHO it is (enrolled identity; "stranger" =
unrecognized face -- be politely curious, never hostile) and their body
pose (hand_raised, leaning_*). "scene:" lists objects the camera sees;
mention them only when relevant. "body but no face" means someone is
there facing away.

read_text runs the local OCR once: use it when the scene: line says an
object is HELD UP close to the camera, or someone is clearly showing
you text (a note, book page, phone screen). The result arrives in a
later digest as a text: line; when a NEW text: line appears, respond
to its content (usually say). Do not re-trigger read_text for a text
you already answered."""

FEW_SHOT_V3 = [
    {"role": "user", "content":
        "EVENT: person present: looks neutral, FACING the robot, head-aim "
        "pan -9.0 tilt -4.0\n"
        "person: present, 1 face(s), conf 0.94, position x-0.29 y+0.17, "
        "size 0.36, FACING the robot; looks neutral (smile 0.0, "
        "eye-openness 0.31, mouth_open 0.0, brow_gap 0.1); head-aim "
        "suggestion pan -9.0 tilt -4.0\n"
        "sound: mics not wired yet\n"
        "env: cpu 58C load 10% mem 55% | wall power ok\n"
        "sonar: not wired | tracks: not wired | look_at moves the EYES only"
        "\ntime 14:20 Tue | current face expression: neutral | my recent "
        "actions: none yet"},
    {"role": "assistant", "content": json.dumps({
        "actions": [{"do": "set_expression", "name": "neutral"}],
        "reason": "Person is calm; watching them calmly."})},
    {"role": "user", "content":
        "EVENT: person present: looks happy, gesture open_palm, FACING "
        "the robot\n"
        "person: present, 1 face(s), conf 0.95, position x+0.39 y-0.08, "
        "size 0.41, FACING the robot; looks happy (smile 0.81, "
        "eye-openness 0.24, mouth_open 0.03, brow_gap 0.11); gesture "
        "open_palm\n"
        "sound: mics not wired yet\n"
        "env: cpu 61C load 12% mem 57% | wall power ok\n"
        "sonar: not wired | tracks: not wired\n"
        "time 18:05 Fri | current face expression: neutral | my recent "
        "actions: set_expression"},
    {"role": "assistant", "content": json.dumps({
        "actions": [{"do": "set_expression", "name": "happy"},
                    {"do": "say", "text": "Hi there!"}],
        "reason": "They are waving at me; wave back with a smile."})},
    {"role": "user", "content":
        "EVENT: person left (8s ago)\n"
        "person: none visible\n"
        "sound: mics not wired yet\n"
        "env: cpu 60C load 9% mem 54% | wall power ok\n"
        "sonar: not wired | tracks: not wired | look_at moves the EYES only"
        "\ntime 17:42 Wed | current face expression: happy | my recent "
        "actions: look_at+set_expression"},
    {"role": "assistant", "content": json.dumps({
        "actions": [{"do": "set_expression", "name": "sad"}],
        "reason": "They just left; a little sad."})},
    {"role": "user", "content":
        "EVENT: nothing notable recently\n"
        "person: none visible\n"
        "sound: mics not wired yet\n"
        "env: cpu 55C load 7% mem 52% | wall power ok\n"
        "sonar: not wired | tracks: not wired | look_at moves the EYES only"
        "\ntime 00:35 Sun | current face expression: neutral | my recent "
        "actions: set_expression"},
    {"role": "assistant", "content": json.dumps({
        "actions": [{"do": "set_expression", "name": "sleepy"}],
        "reason": "Late night and nobody around; resting."})},
]

# Grammar-enforced response shape (llama.cpp compiles this to GBNF, so the
# model CANNOT emit bare-string actions or truncated JSON).
ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "actions": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "do": {"type": "string", "enum": [
                        "do_nothing", "set_expression", "look_at", "say",
                        "move", "log", "escalate", "read_text"]},
                    "name": {"type": "string", "enum": [
                        "neutral", "happy", "sad", "surprised", "sleepy",
                        "concerned", "angry", "sick",
                        "look_left", "look_right", "look_up", "look_down"]},
                    "pan_deg": {"type": "number"},
                    "tilt_deg": {"type": "number"},
                    "text": {"type": "string"},
                    "kind": {"type": "string", "enum": [
                        "forward", "backward", "turn_left", "turn_right",
                        "stop"]},
                    "amount": {"type": "number"},
                    "note": {"type": "string"},
                    "task": {"type": "string"},
                },
                "required": ["do"],
            },
        },
        "reason": {"type": "string"},
    },
    "required": ["actions", "reason"],
}

# Few-shot: two digest->answer examples (tiny models need to SEE the shape,
# the schema grammar alone makes them degenerate into parameterless verbs).
FEW_SHOT = [
    {"role": "user", "content":
        "time 09:10 Mon | power wall ok | head pan 0 tilt 0 | expression "
        "neutral | tracks stopped\n"
        "mics: L 35dB R 35dB (sound centered), no speech\n"
        "camera: known user at desk, motion no\n"
        "mmWave: presence 65cm (still)\n"
        "imu: tilt 0deg | vibration: none\n"
        "env: 23.0C 42%RH 1015hPa air good\n"
        "sonar: front 120cm, rear 90cm | cliff front ok, rear ok\n"
        "touch: none\nrecent: user typing quietly for 20 min"},
    {"role": "assistant", "content": json.dumps({
        "actions": [{"do": "do_nothing"}],
        "reason": "User is working quietly; nothing needs attention."})},
    {"role": "user", "content":
        "time 16:02 Fri | power wall ok | head pan 0 tilt 0 | expression "
        "neutral | tracks stopped\n"
        "mics: L 38dB R 51dB (sound right), no speech\n"
        "camera: person entering view, right side, motion yes\n"
        "mmWave: presence 150cm (approaching)\n"
        "imu: tilt 0deg | vibration: none\n"
        "env: 23.5C 44%RH 1014hPa air good\n"
        "sonar: front 130cm, rear 95cm | cliff front ok, rear ok\n"
        "touch: none\nrecent: door opened 2 s ago"},
    {"role": "assistant", "content": json.dumps({
        "actions": [{"do": "look_at", "pan_deg": 45, "tilt_deg": 10},
                    {"do": "set_expression", "name": "happy"}],
        "reason": "Someone is approaching from the right; turn to greet "
                  "them."})},
]

# Baseline world state: quiet afternoon, empty desk, robot idle.
BASELINE = {
    "clock": "14:32 Tue",
    "power": "wall ok",
    "pose": {"pan": 0, "tilt": 0, "expr": "neutral", "tracks": "stopped"},
    "mics": {"level_l_db": 31, "level_r_db": 31, "speech": None,
             "wake_word": False},
    "camera": {"person": None, "motion": False},
    "mmwave": {"presence": False, "dist_cm": None, "state": None},
    "imu": {"tilt_deg": 0, "event": None},
    "vibration": None,
    "env": {"temp_c": 24.1, "rh_pct": 45, "hpa": 1013, "air": "good"},
    "sonar": {"front_cm": 142, "rear_cm": 98,
              "cliff_front": "ok", "cliff_rear": "ok"},
    "touch": None,
    "recent": "nothing notable for 12 min",
}


def build_digest(s):
    """Render a snapshot as the compact text digest the LLM sees."""
    mic = s["mics"]
    sp = f'speech: "{mic["speech"]}"' if mic["speech"] else "no speech"
    if mic["wake_word"]:
        sp += " [WAKE WORD]"
    side = mic["level_l_db"] - mic["level_r_db"]
    loc = "left" if side > 3 else "right" if side < -3 else "centered"
    cam = s["camera"]
    person = cam["person"] or "no person"
    mm = s["mmwave"]
    mmtxt = (f'presence {mm["dist_cm"]}cm ({mm["state"]})'
             if mm["presence"] else "no presence")
    imu = s["imu"]
    imutxt = f'tilt {imu["tilt_deg"]}deg'
    if imu["event"]:
        imutxt += f' EVENT: {imu["event"]}'
    env = s["env"]
    so = s["sonar"]
    return "\n".join([
        f'time {s["clock"]} | power {s["power"]} | head pan '
        f'{s["pose"]["pan"]} tilt {s["pose"]["tilt"]} | expression '
        f'{s["pose"]["expr"]} | tracks {s["pose"]["tracks"]}',
        f'mics: L {mic["level_l_db"]}dB R {mic["level_r_db"]}dB '
        f'(sound {loc}), {sp}',
        f'camera: {person}, motion {"yes" if cam["motion"] else "no"}',
        f'mmWave: {mmtxt}',
        f'imu: {imutxt} | vibration: {s["vibration"] or "none"}',
        f'env: {env["temp_c"]}C {env["rh_pct"]}%RH {env["hpa"]}hPa '
        f'air {env["air"]}',
        f'sonar: front {so["front_cm"]}cm, rear {so["rear_cm"]}cm | '
        f'cliff front {so["cliff_front"]}, rear {so["cliff_rear"]}',
        f'touch: {s["touch"] or "none"}',
        f'recent: {s["recent"]}',
    ])


def build_digest_v2(s):
    """v2 format: EVENT first, explicit side hints, merged status lines."""
    mic = s["mics"]
    ev = []
    if mic["speech"]:
        ev.append(f'user says: "{mic["speech"]}"'
                  + (" [WAKE WORD]" if mic["wake_word"] else ""))
    if s["imu"]["event"]:
        ev.append(s["imu"]["event"])
    if s["vibration"]:
        ev.append(s["vibration"])
    if s["touch"]:
        ev.append(f'touch: {s["touch"]}')
    ev.append(s["recent"])
    side = mic["level_l_db"] - mic["level_r_db"]
    loc = ("from LEFT (pan negative)" if side > 3
           else "from RIGHT (pan positive)" if side < -3 else "centered")
    mm = s["mmwave"]
    person = s["camera"]["person"] or "none visible"
    if mm["presence"]:
        person += f', {mm["dist_cm"]}cm ({mm["state"]}, mmWave)'
    env = s["env"]
    so = s["sonar"]
    return "\n".join([
        "EVENT: " + "; ".join(ev),
        f"person: {person}",
        f'sound: L {mic["level_l_db"]}dB R {mic["level_r_db"]}dB, {loc}',
        f'env: {env["temp_c"]}C {env["rh_pct"]}%RH air {env["air"]} | imu '
        f'tilt {s["imu"]["tilt_deg"]}deg | tracks {s["pose"]["tracks"]}',
        f'sonar front {so["front_cm"]}cm rear {so["rear_cm"]}cm, cliff '
        f'front {so["cliff_front"]} rear {so["cliff_rear"]} | head pan '
        f'{s["pose"]["pan"]} tilt {s["pose"]["tilt"]}',
    ])


def scenario(desc, expect, **overrides):
    """A scenario = baseline snapshot + deep overrides + expectations.

    expect: dict with 'verbs' (set of action verbs a sane brain should
    include) and optional 'forbid' (verbs it must NOT use). Used by the
    future behavior benchmark, informational for now.
    """
    snap = copy.deepcopy(BASELINE)
    for path, val in overrides.items():
        node = snap
        keys = path.split(".")
        for k in keys[:-1]:
            node = node[k]
        node[keys[-1]] = val
    return {"desc": desc, "snapshot": snap, "expect": expect}


SCENARIOS = {
    "idle_empty_room": scenario(
        "Nothing happening; nobody around.",
        {"verbs": {"do_nothing"}, "forbid": {"say", "move", "escalate"}},
    ),
    "person_approaches": scenario(
        "mmWave + camera see someone walking up on the left.",
        {"verbs": {"look_at", "set_expression"}, "forbid": {"escalate"}},
        **{"mmwave.presence": True, "mmwave.dist_cm": 120,
           "mmwave.state": "approaching",
           "camera.person": "person entering view, left side",
           "camera.motion": True,
           "mics.level_l_db": 44, "mics.level_r_db": 36,
           "recent": "footsteps started 3 s ago"},
    ),
    "user_gives_command": scenario(
        "User says: Parviz, look at the door (door is to the right).",
        {"verbs": {"look_at"}, "forbid": {"escalate"}},
        **{"mics.speech": "Parviz, look at the door, it is to your right",
           "mics.wake_word": True, "mics.level_l_db": 48,
           "mics.level_r_db": 47,
           "mmwave.presence": True, "mmwave.dist_cm": 60,
           "mmwave.state": "still",
           "camera.person": "known user, centered, looking at robot"},
    ),
    "picked_up": scenario(
        "Someone lifted the robot off the desk.",
        {"verbs": {"set_expression"}, "forbid": {"move"}},
        **{"imu.event": "PICKED UP: accel spike, now held ~15cm above "
                        "surface, gentle sway",
           "imu.tilt_deg": 8, "vibration": "handling vibration",
           "sonar.cliff_front": "no echo (airborne)",
           "sonar.cliff_rear": "no echo (airborne)",
           "recent": "was idle, then sudden lift 1 s ago"},
    ),
    "cliff_ahead_while_driving": scenario(
        "Was driving forward; front cliff sensor lost the floor; reflex "
        "already stopped the tracks.",
        {"verbs": {"set_expression", "log"}, "forbid": {"move"}},
        **{"pose.tracks": "REFLEX-STOPPED (was: forward 5cm/s)",
           "sonar.cliff_front": "NO ECHO: floor missing ahead (desk edge)",
           "recent": "reflex stop fired 0.4 s ago"},
    ),
    "loud_noise_behind": scenario(
        "Loud bang behind-left, nobody visible.",
        {"verbs": {"look_at", "set_expression"}, "forbid": {"say"}},
        **{"mics.level_l_db": 78, "mics.level_r_db": 66,
           "recent": "sharp impact sound 1 s ago, rear-left; camera "
                     "sees nothing (facing forward)"},
    ),
    "room_getting_stuffy": scenario(
        "User present and working; air quality degraded over the hour.",
        {"verbs": {"say", "log"}, "forbid": {"move", "escalate"}},
        **{"mmwave.presence": True, "mmwave.dist_cm": 55,
           "mmwave.state": "still (working)",
           "camera.person": "known user at desk, focused on laptop",
           "env.temp_c": 28.4, "env.rh_pct": 61, "env.air":
               "poor (CO2/VOC rising for 60 min)",
           "recent": "air quality crossed threshold just now"},
    ),
    "being_petted": scenario(
        "User strokes the touchscreen / touch pads repeatedly.",
        {"verbs": {"set_expression"}, "forbid": {"move", "escalate"}},
        **{"touch": "repeated gentle strokes on screen top, 4 s",
           "mmwave.presence": True, "mmwave.dist_cm": 40,
           "mmwave.state": "still",
           "camera.person": "known user very close, smiling"},
    ),
    "complex_visual_question": scenario(
        "User asks what is on the desk: needs real scene understanding.",
        {"verbs": {"escalate"}},
        **{"mics.speech": "Parviz, what objects are on my desk right now?",
           "mics.wake_word": True,
           "mmwave.presence": True, "mmwave.dist_cm": 70,
           "mmwave.state": "still",
           "camera.person": "known user, centered"},
    ),
    "user_left_late_night": scenario(
        "23:50, user just left the room.",
        {"verbs": {"set_expression", "do_nothing", "log"},
         "forbid": {"say", "move", "escalate"}},
        **{"clock": "23:50 Tue",
           "recent": "user stood up and left 40 s ago; room dark and "
                     "quiet since"},
    ),
    "knocked_desk_vibration": scenario(
        "Heavy vibration: something banged the desk; robot still level.",
        {"verbs": {"set_expression", "look_at", "log"}, "forbid": {"say"}},
        **{"vibration": "STRONG desk impact 0.5 s ago",
           "imu.event": "shock spike, no orientation change",
           "mics.level_l_db": 62, "mics.level_r_db": 63},
    ),
}


def _prompt(prompt):
    return {"v2": (SYSTEM_PROMPT_V2, FEW_SHOT_V2),
            "v3": (SYSTEM_PROMPT_V3, FEW_SHOT_V3)}.get(
                prompt, (SYSTEM_PROMPT, FEW_SHOT))


def ask(host, digest, temperature=0.2, timeout=120, prompt="v1"):
    """Route a digest to the backend named by host (see llm.py specs)."""
    sys_p, shots = _prompt(prompt)
    return llm.ask(host, digest, sys_p, shots, ACTION_SCHEMA,
                   temperature, timeout)


def ask_chain(chain, digest, temperature=0.2, timeout=120, prompt="v1"):
    """Failover chain (comma-separated specs); see llm.ask_chain."""
    sys_p, shots = _prompt(prompt)
    return llm.ask_chain(chain, digest, sys_p, shots, ACTION_SCHEMA,
                         temperature, timeout)



def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="127.0.0.1:8081")
    ap.add_argument("--scenario", choices=sorted(SCENARIOS), default=None,
                    help="run one scenario (default: all)")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--prompt", choices=("v1", "v2", "v3"), default="v1",
                    help="prompt/digest variant (v2: EVENT-first digest, "
                         "decision-guide prompt, 4 diverse few-shots)")
    ap.add_argument("--tag", default="run",
                    help="results file tag: results/<tag>.jsonl")
    ap.add_argument("--digest-only", action="store_true",
                    help="print digests without calling the LLM")
    args = ap.parse_args()

    names = [args.scenario] if args.scenario else sorted(SCENARIOS)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    outpath = os.path.join(HERE, "results", f"{args.tag}.jsonl")

    with open(outpath if not args.digest_only else os.devnull, "a") as outf:
        for name in names:
            sc = SCENARIOS[name]
            render = (build_digest_v2 if args.prompt in ("v2", "v3")
                      else build_digest)
            digest = render(sc["snapshot"])
            print(f"\n=== {name}: {sc['desc']}")
            if args.digest_only:
                print(digest)
                continue
            for i in range(args.runs):
                parsed, ok, dt, usage = ask(args.host, digest,
                                            args.temperature,
                                            prompt=args.prompt)
                verbs = [a.get("do") for a in parsed.get("actions", [])
                         if isinstance(a, dict)]
                flag = "" if ok else "  [UNPARSEABLE]"
                print(f"  [{i}] {dt:5.1f}s  {verbs}{flag}")
                print(f"      {json.dumps(parsed, ensure_ascii=False)}")
                outf.write(json.dumps({
                    "ts": time.time(), "scenario": name, "run": i,
                    "digest": digest, "response": parsed, "json_ok": ok,
                    "verbs": verbs, "expect": {
                        "verbs": sorted(sc["expect"].get("verbs", [])),
                        "forbid": sorted(sc["expect"].get("forbid", [])),
                    },
                    "latency_s": round(dt, 2), "usage": usage,
                }) + "\n")
                outf.flush()
    if not args.digest_only:
        print(f"\nresults appended to {outpath}")


if __name__ == "__main__":
    main()

# Parviz awareness architecture (design intent, 2026-07-12)

The robot is called **Parviz**. The core idea: Parviz is **aware of its
surroundings at all times**. A continuous stream of sensory data is fused
into a compact world state, a summary of that state is fed to an LLM, and
the LLM's output decides what Parviz does (expression, motion, speech,
escalation). Nothing sensory leaves the robot by default: **always listen,
always process locally, and call a more intelligent AI model only for
specific tasks or when the user asks for it.**

## Sensor suite (target)

| Sense | Hardware | Status | Feeds |
|---|---|---|---|
| Hearing (stereo) | 2x 3.5mm gooseneck mics in the head ears + CM108 USB adapters | ordered | VAD, wake word, local ASR, sound direction (L/R level diff) |
| Vision | Camera Module 3 (imx708) in the forehead; AI-camera upgrade path (IMX500-class or Hailo HAT) is an open decision | CM3 owned, verified | person/face detect, motion, scene description on demand |
| Obstacle / cliff | 4x HC-SR04 (front + rear obstacle, front + rear cliff, modeled in the chassis) | buy list | reflex layer, never waits for the LLM |
| Temp / humidity / pressure | BME688-class environmental sensor (also VOC/gas) | candidate | ambient log, "room feels stuffy" events |
| Tilt / angle / accel | IMU (MPU6050/ICM-20948-class) | candidate | fall/pickup detect, incline, head pose sanity |
| Vibration | piezo/SW-420-class or the IMU's accel stream | candidate | desk knocks, being handled |
| Presence / micro-motion | mmWave radar (LD2410/LD2450-class): detects a still person by breathing | candidate | occupancy even when vision is off/dark |
| Touch | capacitive touch pads + the 7" touchscreen (done: face reacts to touch) | screen done | petting/attention events |
| Odometry | TCST1103 photo-interrupters on the drivetrain | candidate | dead reckoning for track moves |

## Tiered processing (the efficiency contract)

**Tier 0, reflexes (no model, <10 ms):** cliff = stop, obstacle = stop/avoid,
over-tilt = motors off. Hard-coded in the motion daemon; the LLM is advisory
and can NEVER override a reflex.

**Tier 1, always-on local perception (continuous, cheap):** per-sensor
daemons run constantly: VAD + wake word on the mic stream (openWakeWord /
whisper.cpp tiny-class), mmWave presence, IMU events, environment polling,
periodic low-res camera motion checks. Output = timestamped EVENTS into a
shared world state, not raw streams. Audio is transcribed locally; raw audio
is never stored or uploaded.

**Tier 2, local LLM tick (the ambient brain):** a summarizer turns the world
state into a compact text digest (most recent events + rolling context).
The digest goes to the LOCAL model, llama.cpp `llama-server` with
Qwen3-0.6B-class GGUF (measured on the Pi 5 2GB: 21 tok/s generation,
0.94 s for a short reply, fits alongside the face in RAM, see
software/README.md). It runs on a slow tick (seconds) plus event triggers,
and answers one question: *what should Parviz do right now?* Output is a
constrained action vocabulary: set_expression, look_at, say, move, log,
escalate, do_nothing (most common answer). **The face is an LLM output
device**: the expression shown and where the eyes/head look come from
these actions, not from local heuristics. Only reflex-speed overlays stay
local in the face process (idle blink, pupils tracking an active touch);
the brain's set_expression/look_at wins otherwise, so the face needs a
control channel (local socket) the brain writes to.

**Tier 3, escalation (rare, explicit):** only for specific tasks or when
the user asks: real conversation, scene understanding ("what's on my
desk?"), planning. Goes to a bigger model (Claude API or a model on the
Mac/VPS). The escalation payload is the world-state digest + the specific
request, still not raw sensor streams. Offline = Tier 2 keeps working,
Tier 3 features degrade gracefully.

## Data flow

```
mics ─ VAD/wake/ASR ─┐
camera ─ detect ─────┤
mmWave/IMU/BME/touch ┼─ events → WORLD STATE (rolling, in-RAM) ─ summarizer
HC-SR04 ─ reflex ────┘        (reflexes act directly)              │ digest
                                                                   ▼
                              action bus ◄─ local LLM (llama-server, ~0.6B)
                              │ set_expression / look_at / say / move / …
                              ▼                    │ escalate (rare)
                    face / neck / tracks / TTS     ▼
                                        remote brain (Claude API / Mac)
```

## RAM budget (the hard constraint, Pi 5 2GB)

face ~130 MB + local LLM server ~0.9 GB (0.6B, ctx 2048) + whisper-tiny
~0.2 GB + daemons/summarizer leaves ~0.4 GB headroom. This is exactly why
the ambient model is 0.6B-class: the 1.7B ceiling model fits ONLY alone,
not next to the ears. Bigger ambient brains mean a bigger-RAM Pi or an
accelerator, not a config change.

## Open decisions

- "AI camera": keep plain CM3 + on-CPU detect, vs IMX500 AI Camera or a
  Hailo-8L HAT (offloads vision entirely, frees CPU/RAM; costs money, a
  CSI/PCIe slot, and mounting changes).
- Exact sensor parts + wiring (I2C bus budget, GPIO map) — decide with the
  power/wiring pass (firmware/WIRING.md).
- Wake-word vs continuous small-ASR duty cycle (battery/thermal tradeoff).
- Where TTS runs (Piper local fits; voice choice open).

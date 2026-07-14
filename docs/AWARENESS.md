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
| Vision | Camera Module 3 (imx708) in the forehead; **AI Camera (IMX500) ordered 2026-07-14** -- on-sensor NPU runs detection on the camera itself, decision resolved (cam pod re-fit VERIFY_ON_ARRIVAL) | CM3 owned; IMX500 ordered | person/face detect ON-SENSOR, motion, scene description on demand |
| Obstacle / cliff | 4x HC-SR04 (front + rear obstacle, front + rear cliff, modeled in the chassis) | buy list | reflex layer, never waits for the LLM |
| Temp / humidity / pressure | **Sense HAT Rev2** (LPS25H pressure/temp + HTS221 humidity/temp), on the chassis equipment base via the neck I2C drop; BME688 now only if VOC/gas is wanted | ordered 2026-07-14 | ambient log ("room feels stuffy" needs the optional BME688) |
| Tilt / angle / accel | **Sense HAT Rev2** LSM9DS1 9-DoF (accel + gyro + magnetometer -- compass heading is new) | ordered 2026-07-14 | fall/pickup detect, incline, heading, head pose sanity |
| Light / color | **Sense HAT Rev2** TCS3400 ambient light + color | ordered 2026-07-14 | lights-on/off events, day/night rhythm, "someone turned the lights off" |
| Vibration | piezo/SW-420-class or the IMU's accel stream | candidate | desk knocks, being handled |
| Presence / micro-motion | mmWave radar (LD2410/LD2450-class): detects a still person by breathing | candidate | occupancy even when vision is off/dark |
| Touch | capacitive touch pads + the 7" touchscreen (done: face reacts to touch) + **Sense HAT 5-way joystick** (hidden physical input on the base) | screen done; joystick ordered | petting/attention events, service-menu input |
| Odometry | TCST1103 photo-interrupters on the drivetrain | candidate | dead reckoning for track moves |

The Sense HAT also brings an **8x8 RGB LED matrix** (an OUTPUT, not a sense):
mounted on the equipment base it is invisible with the deck on, so treat it as
a service/debug display (world-state heartbeat visible when the deck is lifted)
unless a later pass gives it a window.

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

## RAM budget (the hard constraint, Pi 5 2GB -- 8GB ORDERED 2026-07-14)

face ~130 MB + local LLM server ~0.9 GB (0.6B, ctx 2048) + whisper-tiny
~0.2 GB + daemons/summarizer leaves ~0.4 GB headroom. This is exactly why
the ambient model is 0.6B-class: the 1.7B ceiling model fits ONLY alone,
not next to the ears. Bigger ambient brains mean a bigger-RAM Pi or an
accelerator, not a config change.

**Both halves of that sentence were ordered 2026-07-14:** a Pi 5 **8GB**
(the bigger-RAM Pi -- the 1.7B-class ambient model plus a larger ASR now
fit NEXT TO the face, with room for longer context) and the **AI Camera**
(the accelerator -- detection moves onto the sensor's NPU, freeing the CPU
share the 1-2 Hz vision loop eats today). Re-run the software/README.md
benchmarks on the 8GB board when it arrives; the 0.6B numbers stay valid
as the fallback/2GB profile.

## Arduino I/O plane (decided direction, 2026-07-12)

Most of the electrical components do NOT wire to the Pi's GPIO: they
connect to an **Arduino dev board**, and the Arduino connects to the Pi 5
over **one USB cable** (serial telemetry + commands + power + flashing on
the same wire). The Pi keeps only what needs its bandwidth: camera (CSI),
mics (USB), display (DSI).

Why:
- **Real-time belongs on the microcontroller**: HC-SR04 echo timing,
  vibration debounce, LED strip protocols, encoder counting, stepper
  pulse trains — all jitter-free there, all jittery under Linux.
- **Electrical decoupling**: sensor mistakes fry a $5 board, not the Pi;
  5V-tolerant pins; one clean harness instead of a GPIO spaghetti.
- **The Pi can REPROGRAM the Arduino on the fly using its AI.** With
  `arduino-cli` installed on the Pi, firmware is just another artifact
  the LLM tier can write: generate sketch -> compile -> flash over the
  same USB cable -> verify over serial. New sensor arrives, the robot
  can (with the big-brain tier) write, flash, and test its own firmware
  for it. Firmware lives in the repo (`firmware/arduino/`) like any code.

Protocol intent: line-based JSON over serial (~10 Hz telemetry into the
world state: sonar distances, IMU, env, touch events; commands back:
motors, LEDs). The Arduino is a Tier-0/Tier-1 peripheral, reflexes like
cliff-stop can live IN the firmware, below even the Pi.

Open here: which board (classic Uno/Nano AVR vs RP2040/ESP32-class with
more headroom — check the parts inventory before buying), and which of
pan/tilt steppers + TT motors move behind it vs stay on Pi GPIO/ULN2003.

## Open decisions

- ~~"AI camera"~~ **RESOLVED 2026-07-14: IMX500 AI Camera ordered.** Remaining
  sub-decision: swap it into the forehead pod (needs a cam-pod re-fit,
  VERIFY_ON_ARRIVAL) vs bench-validate first with CM3 staying in the head.
- ~~Exact IMU/env sensor parts~~ **RESOLVED 2026-07-14: Sense HAT Rev2** on the
  chassis equipment base over the neck I2C drop (firmware/WIRING.md has the
  wire-level plan + I2C address map). Still open: mmWave exact module, TTP223
  head-top placement.
- Wake-word vs continuous small-ASR duty cycle (battery/thermal tradeoff) —
  the 8GB Pi widens the options here.
- Where TTS runs (Piper local fits; voice choice open).

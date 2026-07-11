# desk-pi software

Parviz robot software. Awareness/LLM design intent: ../docs/AWARENESS.md.
Software spike for the tracked desk robot: face renderer, neck stepper
driver, camera check. Lives here in the repo and mirrored to `~/parviz-sw`
on the Pi (`ssh moshe@moshe-pi5-2gb.local`, key auth).

## Deploy

```sh
rsync -av --exclude __pycache__ software/ moshe@moshe-pi5-2gb.local:parviz-sw/
```

## Pieces

### face/face.py, fullscreen face (800x480, official 7" touchscreen)

Rigid-line robot face (2026-07-11 revision, per user): two rectangular
outlined eyes with square pupils, NO mouth, NO eyebrows, single color =
the body's safety orange (`src/geo.py COLORS["accent"]` = 232,116,34) on
black. Expressions come from lid height, top-corner tilt and pupil
position; every stroke is straight. Layout scales off the panel size
(eyes 224x192 centered at 240/560). Idle blink stays.
`FaceRenderer.set_expression(name)` API; expressions: neutral, happy, sad,
surprised, sleepy, look_left, look_right, look_up, look_down.

TOUCH: while a finger is on the panel the pupils track it and the eyes
widen slightly; lifting the finger blinks and returns to the current
expression. Handles both SDL FINGER* events (the DSI ft5x06 panel) and
mouse-drag (windowed dev).

Headless visual check (no compositor to screenshot through):
`kill -USR1 <pid>` makes the next frame land in `/tmp/face_frame.png`.

### face/parviz-face.service, boot service

The Pi boots to console (`sudo systemctl set-default multi-user.target`,
desktop disabled; revert with `graphical.target`) and systemd starts the
face fullscreen via KMS/DRM. SDL scans the DRM cards for a connected
connector, which is always the DSI panel (HDMI unplugged), so no device
index is pinned. DRM card numbers shuffle between boots; never hardcode
`/dev/dri/cardN`.

```sh
sudo cp face/parviz-face.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now parviz-face
```

Needs pygame (check `python3 -c "import pygame"`; else
`pip3 install --user pygame`, no sudo).

```sh
# Over SSH, console owns the display (no desktop session):
SDL_VIDEODRIVER=kmsdrm python3 face/face.py --demo --seconds 10
# (face.py sets SDL_VIDEODRIVER=kmsdrm itself when no DISPLAY/WAYLAND_DISPLAY)

# If a Wayland desktop session owns the display, kmsdrm will fail
# ("Could not initialize KMSDRM", the compositor holds DRM master).
# Run inside the session instead:
WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 python3 face/face.py --seconds 10
# X11 desktop: DISPLAY=:0 python3 face/face.py --seconds 10

# Dev on a laptop:
python3 face/face.py --windowed --demo --seconds 10
```

`--seconds N` auto-exits (SSH smoke tests, nothing left running). Esc/q quits.

### motion/steppers.py, 28BYJ-48 half-step driver (lgpio)

`PanStepper` / `TiltStepper` on a shared `LimitedStepper`:

- **Pins are required, no defaults**, nothing is wired yet.
- **Pan hard clamp default ±88°** (constructor param `limit_deg`). The Pi
  power service loop in the neck must never over-wind; the ±90 mechanical
  target keeps a 2° software margin. `move_to`/`move_by` both clamp; relative
  moves cannot creep past.
- **Tilt clamp ±30°**, `gear_ratio=12` (single-start worm, 12T wheel). Worm
  self-locks, so coils release after every move (default `hold=False`).
- `dry_run=True` records coil writes in `.trace` instead of touching GPIO;
  lgpio imports lazily, so the module runs anywhere.

```sh
# Unit tests (any machine, no GPIO):
cd motion && python3 -m unittest test_steppers -v

# On the robot (once wired; BCM pin numbers for the ULN2003 IN1..IN4):
python3 -c "from steppers import PanStepper; PanStepper(pins=(17,18,27,22)).move_to(30)"
```

lgpio comes from the OS package `python3-lgpio` (should be present on
Raspberry Pi OS trixie; if not: `pip3 install --user lgpio`).

### camera/preview.py, one-frame capture check

Tries Picamera2, falls back to `rpicam-still`. Writes `/tmp/desk_pi_cam.jpg`
and prints backend + resolution (parses JPEG SOF, no PIL needed).

```sh
python3 camera/preview.py
# expect: OK: /tmp/desk_pi_cam.jpg (... KB) via picamera2, resolution 4608x2592
```

## Hardware verification status (2026-07-11)

**All three pieces verified on the Pi** (`moshe-pi5-2gb.local`, Pi 5 2GB,
Debian 13 trixie, kernel 6.18, Python 3.13.5; pygame 2.6.1 / lgpio /
picamera2 / numpy all present from the OS):

- `camera/preview.py`: full-res capture works,
  `OK: /tmp/desk_pi_cam.jpg (694 KB) via picamera2, resolution 4608x2592`
  (imx708 on CAM1). Frame pulled back and inspected, real image.
- `motion/test_steppers.py`: 19/19 pass on the Pi (no GPIO wired yet, so
  only dry-run coverage; live coil test waits on the ULN2003 wiring).
- `face/face.py --demo --seconds 12`: renders fullscreen on the 7" DSI
  panel (800x480); expression demo verified frame-by-frame via screenshots.
- **Boot service verified 2026-07-12**: `parviz-face.service` active after
  a real reboot, holding the DSI card via kmsdrm, ~10% of one core,
  system RAM 306 MB used (desktop disabled freed ~120 MB).
- **Touch verified end-to-end** with a virtual multitouch device
  (python3-evdev uinput, MT slots + `INPUT_PROP_DIRECT`): pupils track a
  synthetic drag-and-hold, release blinks. NOTE: a single-touch ABS
  uinput device does NOT work for this, SDL classifies it as a
  pointer and only the press comes through; emulate real MT.

Remote screenshots: desktop session up -> `grim -o DSI-2 out.png`;
console/service mode -> `kill -USR1 $(pgrep -fn face.py)` and fetch
`/tmp/face_frame.png` (the service renders into a DRM dumb buffer, there
is nothing for grim to grab).

## Next hardware step

Wire one 28BYJ-48 + ULN2003 to the Pi (pick 4 BCM pins, e.g. 17/18/27/22),
then run the first live coil test:
`python3 -c "from steppers import PanStepper; PanStepper(pins=(17,18,27,22)).move_to(30)"`.
After that: pin map into a `pins.py` (or config), and a supervisor that
ties face + camera + motion together.

## LLM on the Pi (measured 2026-07-12)

The Pi 5 2GB runs small LLMs fine, CPU-only. Runtime: **llama.cpp**,
built natively on the Pi (`~/llama.cpp/build/bin`, Cortex-A76 dotprod
kernels; `cmake -B build -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=ON`).
Use **Q4_0** quants: llama.cpp runtime-repacks Q4_0 for the ARM dotprod
path, so it beats Q4_K_M on this CPU. Ollama was rejected: it wraps
llama.cpp anyway and its resident Go server wastes RAM the 2GB board
does not have. Models live in `~/models/`.

Measured with `llama-bench -t 4` (pp = prompt tokens/s, tg = generation
tokens/s), face service running throughout:

| model (Q4_0)        | weights  | pp256 | tg64  | verdict |
|---------------------|----------|-------|-------|---------|
| Qwen3-0.6B          | 403 MiB  | 204   | 21.4  | daily driver |
| LFM2-1.2B           | 661 MiB  |  94   | 11.0  | quality alt |
| Llama-3.2-1B        | 730 MiB  |  84   |  9.0  | slower than LFM2, skip |
| Qwen3-1.7B          | 1002 MiB |  55   |  6.5  | fits, sluggish; ceiling |

End-to-end serving check (Qwen3-0.6B, `llama-server -t 4 -c 2048`):
short persona reply in **0.94 s** wall clock cold; server RSS 937 MB;
face + server coexist with 1.17 GB still available. Qwen3 is a thinking
model, append `/no_think` to the system prompt for latency.

Serve command:

```sh
~/llama.cpp/build/bin/llama-server -m ~/models/Qwen3-0.6B-Q4_0.gguf \
    -t 4 -c 2048 --host 127.0.0.1 --port 8081
# OpenAI-compatible: POST localhost:8081/v1/chat/completions
```

Honest quality note: 0.6B-1.7B models handle persona lines, command
parsing and simple Q&A; they are not good conversationalists. For real
conversation quality the right architecture is a remote brain (API or a
bigger box) with the local model as the offline/latency fallback.
Budget rule: keep model + KV under ~1.2 GB so the face, camera and
supervisor never fight the OOM killer.

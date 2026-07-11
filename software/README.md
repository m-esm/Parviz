# desk-pi software

Software spike for the tracked desk robot: face renderer, neck stepper
driver, camera check. Lives here in the repo and mirrored to `~/parviz-sw`
on the Pi (`ssh moshe@moshe-pi5-2gb.local`, key auth).

## Deploy

```sh
rsync -av --exclude __pycache__ software/ moshe@moshe-pi5-2gb.local:parviz-sw/
```

## Pieces

### face/face.py, fullscreen face (800x480, official 7" touchscreen)

Design-ref face (see `reference/design/front.jpg`): dark navy background,
two cyan outlined eyes with offset pupils + highlight dots, arc brows,
smile arc, idle blink. `FaceRenderer.set_expression(name)` API stub;
expressions: neutral, happy, sad, surprised, sleepy, look_left, look_right,
look_up, look_down.

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
  panel (`card1-DSI-2`, 800x480). A `labwc` Wayland session owns the
  display, so it ran with `WAYLAND_DISPLAY=wayland-0
  XDG_RUNTIME_DIR=/run/user/1000`; verified via a mid-demo `grim -o DSI-2`
  screenshot (expressions animate, blink works).

`grim` + `wlr-randr` are installed on the Pi; `grim -o DSI-2 out.png` is
the standard way to screenshot the panel for remote verification.

## Next hardware step

Wire one 28BYJ-48 + ULN2003 to the Pi (pick 4 BCM pins, e.g. 17/18/27/22),
then run the first live coil test:
`python3 -c "from steppers import PanStepper; PanStepper(pins=(17,18,27,22)).move_to(30)"`.
After that: pin map into a `pins.py` (or config), and a supervisor that
ties face + camera + motion together.

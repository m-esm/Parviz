"""desk-pi face renderer: fullscreen animated face for the official 7" display.

Look (2026-07-12, third revision per user): RIGID LINES ONLY, two
CHAMFERED-corner eyes drawn as TWO THIN OUTLINES (outer + inset echo,
no bold ring) riding HIGH on the screen, chamfered pupils that DILATE
with mood, a rigid 3-segment MOUTH (smile/frown polyline, chamfered-O
when open/surprised), and a bottom TELEMETRY bar (CPU temp, network,
power + placeholders for unwired sensors). No eyebrows. Single hue:
body safety orange (src/geo.py COLORS["accent"] = 232,116,34) on black.
Expressions = lid + bottom-lid squint + corner tilt + pupil size +
mouth curve/open; every stroke is a straight line. TOUCH: while a finger is on the panel the
pupils track it (eyes widen slightly); lifting it blinks and returns
to the current expression; each press spawns a fading chamfered ripple.

Modern-UX layer (2026-07-12): micro-saccades + slow breathing so the
face never freezes, a 1.6 s power-on curtain reveal with a typed
"PARVIZ // BOOT" line, and DIM-orange HUD chrome (corner viewfinder
brackets, "PARVIZ // <EXPRESSION>" status line with blinking cursor,
a breathing heartbeat pip bottom-right). Same hue only, eyes stay king.

Display target: 800x480 (official RPi 7" touchscreen, DSI).

Running over SSH with no desktop session (console owns the display):
    SDL_VIDEODRIVER=kmsdrm python3 face.py
KMS/DRM needs the 'render'+'video' groups (default for the first user on
Raspberry Pi OS) and a free (non-desktop) VT. If a Wayland/X desktop session
owns the display, kmsdrm will fail with "Could not initialize KMSDRM",
in that case run it INSIDE the session instead:
    WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/$(id -u) python3 face.py
(or DISPLAY=:0 on X11). Don't fight the compositor for the DRM master.

Headless verification (e.g. under the systemd service, no compositor to
screenshot through): `kill -USR1 <pid>` makes the next frame land in
/tmp/face_frame.png.

Dev on a laptop:  python3 face.py --windowed --seconds 10

API stub: FaceRenderer.set_expression(name), supported names in EXPRESSIONS.
pygame is imported lazily so this module imports (and its geometry is
testable) on machines without pygame.
"""

import argparse
import collections
import json
import math
import os
import random
import signal
import socket
import subprocess
import sys
import time

SCREEN_W, SCREEN_H = 800, 480

# Palette. ORANGE is the FACE's color (eyes + mouth) and only the face's.
# The HUD lives in cool muted tones so telemetry never competes with the
# expression (user 2026-07-12: orange is just for the face).
BG = (0, 0, 0)
ORANGE = (232, 116, 34)
DIM = (93, 46, 14)            # legacy dim orange (boot label)
HUD_FG = (176, 179, 183)      # light gray: values
HUD_MID = (128, 131, 135)     # mid gray: graphs, cursor, pip
HUD_DIM = (88, 91, 95)        # dark gray: labels, brackets
HUD_FAINT = (62, 64, 68)      # faintest: raw model output, secondary lines
HUD_BAD = (220, 80, 64)       # reserved for alerts

RED = (225, 45, 38)   # stress tint target: the face reddens as the
                      # system heats/loads up (user 2026-07-12)

DECISION_FILE = "/tmp/parviz_decision.json"   # brain writes, face EXECUTES
BRAIN_STALE_S = 45.0   # no fresh decision for this long -> face sleeps

BOOT_LEN_S = 1.6             # power-on reveal
SACCADE_EVERY_S = (1.2, 3.5)  # micro gaze jumps (life between blinks)
SACCADE_MAG = 0.07
BREATH_PERIOD_S = 4.4        # slow size oscillation
BREATH_MAG = 0.012
RIPPLE_LEN_S = 0.35          # touch feedback outline

# Layout scales off the panel size (800x480). Eyes sized down + pulled
# together (2026-07-12, user) so the side panels get real room.
EYE_W = int(SCREEN_W * 0.21)          # 168
EYE_H = int(SCREEN_H * 0.30)          # 144
EYE_CX = (int(SCREEN_W * 0.36), int(SCREEN_W * 0.64))   # 288, 512
EYE_CY = int(SCREEN_H * 0.365)         # eyes ride high; mouth + telemetry below
MOUTH_CY = int(SCREEN_H * 0.72)
MOUTH_HALF = 92
STROKE = 4                             # outer outline width (thin, not bold)
STROKE_IN = 2                          # inner outline width
GAP = 11                               # spacing between the two outlines
CHAMFER = 0.20                         # corner cut as a fraction of the eye opening

FRAME_DUMP = "/tmp/face_frame.png"

# name -> dict of pose targets the animator eases toward.
#   gaze:   (-1..1, -1..1) pupil offset, +x = viewer's right, +y = down
#   lid:    0 open .. 1 closed (straight shutter from the top)
#   squint: 0 open .. 1 bottom lid raised (happy squint, distinct from lid)
#   tilt:   -1 outer top corners drop (sad) .. +1 outer top corners rise
#   size:   eye height scale (surprised > 1)
#   pupil:  pupil dilation, <1 alert/pinpoint, >1 relaxed/interested
#   mouth:  -1 frown .. 0 flat .. 1 smile (3-segment rigid polyline)
#   open:   0 closed .. 1 mouth open (chamfered O, surprise/speech)
EXPRESSIONS = {
    "neutral":    dict(gaze=(0.0, 0.0),  lid=0.0,  squint=0.0,  tilt=0.0,
                       size=1.0, pupil=1.0, mouth=0.1, open=0.0),
    "happy":      dict(gaze=(0.0, -0.1), lid=0.05, squint=0.45, tilt=0.6,
                       size=0.95, pupil=1.2, mouth=0.85, open=0.0),
    "sad":        dict(gaze=(0.0, 0.35), lid=0.3,  squint=0.0,  tilt=-0.7,
                       size=1.0, pupil=0.85, mouth=-0.7, open=0.0),
    "surprised":  dict(gaze=(0.0, -0.2), lid=0.0,  squint=0.0,  tilt=0.1,
                       size=1.3, pupil=0.55, mouth=0.0, open=0.9),
    "sleepy":     dict(gaze=(0.0, 0.3),  lid=0.55, squint=0.15, tilt=-0.2,
                       size=1.0, pupil=1.1, mouth=0.05, open=0.0),
    "concerned":  dict(gaze=(0.0, -0.1), lid=0.1,  squint=0.0,  tilt=-0.35,
                       size=1.05, pupil=0.8, mouth=-0.35, open=0.0),
    "angry":      dict(gaze=(0.0, 0.0),  lid=0.25, squint=0.15, tilt=0.9,
                       size=1.0, pupil=0.7, mouth=-0.5, open=0.0),
    "sick":       dict(gaze=(0.0, 0.45), lid=0.45, squint=0.1,  tilt=-0.5,
                       size=0.95, pupil=0.75, mouth=-0.3, open=0.35),
    # dozing is FACE-INTERNAL (no-brain state); the LLM cannot choose it
    "dozing":     dict(gaze=(0.0, 0.35), lid=0.6,  squint=0.1,  tilt=-0.25,
                       size=0.95, pupil=1.15, mouth=0.03, open=0.0),
    "look_left":  dict(gaze=(-0.9, 0.0), lid=0.0,  squint=0.1,  tilt=0.0,
                       size=1.0, pupil=0.9, mouth=0.1, open=0.0),
    "look_right": dict(gaze=(0.9, 0.0),  lid=0.0,  squint=0.1,  tilt=0.0,
                       size=1.0, pupil=0.9, mouth=0.1, open=0.0),
    "look_up":    dict(gaze=(0.0, -0.9), lid=0.0,  squint=0.1,  tilt=0.2,
                       size=1.05, pupil=0.9, mouth=0.1, open=0.0),
    "look_down":  dict(gaze=(0.0, 0.9),  lid=0.15, squint=0.0,  tilt=0.0,
                       size=1.0, pupil=0.9, mouth=0.0, open=0.0),
}

BLINK_EVERY_S = (2.5, 6.0)   # random interval range
BLINK_LEN_S = 0.18


def _ease(cur, target, dt, speed=8.0):
    """Exponential ease toward target (frame-rate independent)."""
    a = 1.0 - math.exp(-speed * dt)
    return cur + (target - cur) * a


class FaceState:
    """Pure animation state (no pygame): eased pose + idle blink clock."""

    def __init__(self, now=0.0):
        self.pose = dict(EXPRESSIONS["neutral"])
        self.pose["gaze"] = tuple(self.pose["gaze"])
        self.target = dict(self.pose)
        self.expression = "neutral"
        self._blink_t0 = None
        self._next_blink = now + random.uniform(*BLINK_EVERY_S)
        # micro-life: saccade offset (decays fast) + breathing size factor
        # + pupil hippus (tiny dilation twitches alongside the saccades)
        self.sacc = (0.0, 0.0)
        self.breath = 1.0
        self.pupil_jit = 0.0
        self.touch_pt = None     # (-1..1, -1..1) screen point while touched
        self._next_sacc = now + random.uniform(*SACCADE_EVERY_S)

    def set_expression(self, name):
        if name not in EXPRESSIONS:
            raise ValueError(
                f"unknown expression {name!r}; one of {sorted(EXPRESSIONS)}"
            )
        self.expression = name
        self.target = dict(EXPRESSIONS[name])

    def touch(self, gaze):
        """Touchscreen hook: each eye aims at the finger INDEPENDENTLY
        (renderer reads touch_pt), so a touch between the eyes goes
        cross-eyed; that also opens a small silly 'o' mouth. None on
        release restores the expression + an acknowledging blink."""
        if gaze is None:
            self.touch_pt = None
            self.target = dict(EXPRESSIONS[self.expression])
            self._blink_t0 = None
            self._next_blink = 0.0     # blink on the next tick
            return
        gx = max(-1.0, min(1.0, gaze[0]))
        gy = max(-1.0, min(1.0, gaze[1]))
        self.touch_pt = (gx, gy)
        self.target = dict(self.target)
        self.target.update(lid=0.0, size=1.1, pupil=1.3)
        if abs(gx) < 0.28 and gy < 0.35:   # poked between the eyes
            self.target.update(open=0.55, mouth=0.15)
        else:
            base = EXPRESSIONS[self.expression]
            self.target.update(open=base["open"], mouth=base["mouth"])

    def set_gaze(self, gx, gy):
        """Brain look_at: aim the eyes without changing the expression."""
        self.target = dict(self.target)
        self.target["gaze"] = (max(-1.0, min(1.0, gx)),
                               max(-1.0, min(1.0, gy)))

    def tick(self, now, dt):
        gx, gy = self.pose["gaze"]
        tx, ty = self.target["gaze"]
        self.pose["gaze"] = (_ease(gx, tx, dt), _ease(gy, ty, dt))
        for k in ("lid", "squint", "tilt", "size", "pupil", "mouth", "open"):
            self.pose[k] = _ease(self.pose[k], self.target[k], dt)

        # Micro-life. Saccade: a small instant gaze offset that eases back
        # to zero; breathing: slow sine on eye size. Both are subliminal.
        if now >= self._next_sacc:
            self._next_sacc = now + random.uniform(*SACCADE_EVERY_S)
            self.sacc = (random.uniform(-SACCADE_MAG, SACCADE_MAG),
                         random.uniform(-SACCADE_MAG, SACCADE_MAG))
            self.pupil_jit = random.uniform(-0.06, 0.09)
        self.sacc = (_ease(self.sacc[0], 0.0, dt, speed=3.0),
                     _ease(self.sacc[1], 0.0, dt, speed=3.0))
        self.pupil_jit = _ease(self.pupil_jit, 0.0, dt, speed=1.8)
        self.breath = 1.0 + BREATH_MAG * math.sin(
            now * 2.0 * math.pi / BREATH_PERIOD_S)

        # Idle blink: brief triangular lid pulse layered over the pose.
        if self._blink_t0 is None and now >= self._next_blink:
            self._blink_t0 = now
        blink = 0.0
        if self._blink_t0 is not None:
            ph = (now - self._blink_t0) / BLINK_LEN_S
            if ph >= 1.0:
                self._blink_t0 = None
                self._next_blink = now + random.uniform(*BLINK_EVERY_S)
            else:
                blink = 1.0 - abs(2.0 * ph - 1.0)  # 0->1->0
        return max(self.pose["lid"], blink)  # effective lid closure this frame


PREVIEW_JPG = "/dev/shm/parviz_preview.jpg"   # written by perception
VISION_JSON = "/dev/shm/parviz_vision.json"   # written by perception


class CamPreview:
    """Live camera window for the HUD, ghost-feed style (user): grayscale,
    alpha-blended into the black background, scanlines drawn on top. The
    face does NOT own the camera: the perception daemon does, and shares
    160x120 JPEG frames via /dev/shm. Stale/absent -> hidden, CAM '--'."""

    SIZE = (128, 96)
    ALPHA = 110

    def __init__(self):
        self.ok = False
        self._img = None
        self._t = -1e9

    def surface(self, pygame, now):
        if now - self._t >= 0.25:
            self._t = now
            try:
                self.ok = (time.time() -
                           os.path.getmtime(PREVIEW_JPG)) < 4.0
                if self.ok:
                    img = pygame.image.load(PREVIEW_JPG)
                    img = pygame.transform.scale(img, self.SIZE)
                    img = pygame.transform.grayscale(img)
                    img.set_alpha(self.ALPHA)
                    self._img = img
            except (OSError, pygame.error):
                self.ok = False
        return self._img if self.ok else None


class VisionGaze:
    """Person-following idle gaze: reads perception's interaction state;
    while a person is present (and nothing stronger is going on) the eyes
    drift toward them. Touch and non-neutral expressions win."""

    def __init__(self):
        self._t = -1e9
        self.want = None      # (gx, gy) in gaze space, or None
        self.present = False
        self.raw = None       # last parsed state dict (raw model output)

    def poll(self, now):
        if now - self._t < 0.25:
            return
        self._t = now
        self.want = None
        self.present = False
        self.raw = None
        try:
            if time.time() - os.path.getmtime(VISION_JSON) > 2.5:
                return
            with open(VISION_JSON) as f:
                st = json.load(f)
            self.raw = st
            if st.get("person_present"):
                self.present = True
                self.want = (max(-1.0, min(1.0, st["cx"] * 1.3)),
                             max(-1.0, min(1.0, st["cy"] * 1.3)))
        except (OSError, ValueError, KeyError):
            pass


class Telemetry:
    """Cheap system/sensor sampling for the HUD. Fast items every 2 s
    (CPU temp -> history for the sparkline, load, memory), slow items
    every 30 s (IP, uptime, wifi signal). Every read is a tiny procfs /
    sysfs file; failures degrade to '--', never raise."""

    def __init__(self):
        self.load_hist = collections.deque(maxlen=48)
        self.mem_hist = collections.deque(maxlen=48)
        self.temp = None
        self.load_pct = None
        self.mem_pct = None
        self.net_dev = "--"
        self.ssid = ""
        self.ip = "--"
        self.sig = None          # 0..1 wifi link quality
        self.uptime = "--"
        self.watts = None        # board power, sum of PMIC rail V*A
        self.watts_hist = collections.deque(maxlen=36)
        self.core_v = None
        self.throttled = None    # int from vcgencmd get_throttled
        self._t_fast = -1e9
        self._t_slow = -1e9
        self._t_pwr = -1e9

    @staticmethod
    def _read(path):
        with open(path) as f:
            return f.read()

    def sample(self, now):
        if now - self._t_fast >= 2.0:
            self._t_fast = now
            try:
                self.temp = int(self._read(
                    "/sys/class/thermal/thermal_zone0/temp").strip()) / 1000
            except OSError:
                self.temp = None
            try:
                self.load_pct = min(100, int(float(
                    self._read("/proc/loadavg").split()[0])
                    / (os.cpu_count() or 4) * 100))
                self.load_hist.append(self.load_pct)
            except OSError:
                self.load_pct = None
            try:
                mi = {}
                for line in self._read("/proc/meminfo").splitlines()[:3]:
                    k, v = line.split(":")
                    mi[k] = int(v.split()[0])
                self.mem_pct = int(100 - mi["MemAvailable"] /
                                   mi["MemTotal"] * 100)
                self.mem_hist.append(self.mem_pct)
            except (OSError, KeyError, ValueError):
                self.mem_pct = None
        if now - self._t_pwr >= 10.0:
            self._t_pwr = now
            try:
                out = subprocess.run(
                    ["vcgencmd", "pmic_read_adc"], capture_output=True,
                    text=True, timeout=2).stdout
                volts, amps = {}, {}
                for line in out.splitlines():
                    name, val = line.split("=")
                    rail = name.split()[0]
                    v = float(val.rstrip("VA\n "))
                    if rail.endswith("_V"):
                        volts[rail[:-2]] = v
                    elif rail.endswith("_A"):
                        amps[rail[:-2]] = v
                self.watts = sum(volts[r] * a for r, a in amps.items()
                                 if r in volts)
                self.watts_hist.append(self.watts)
                self.core_v = volts.get("VDD_CORE")
                th = subprocess.run(
                    ["vcgencmd", "get_throttled"], capture_output=True,
                    text=True, timeout=2).stdout
                self.throttled = int(th.split("=")[1], 16)
            except (OSError, ValueError, IndexError,
                    subprocess.SubprocessError):
                self.watts = None
                self.core_v = None
                self.throttled = None
        if now - self._t_slow >= 30.0:
            self._t_slow = now
            self.net_dev = "--"
            for dev in ("wlan0", "eth0"):
                try:
                    if self._read(
                            f"/sys/class/net/{dev}/operstate").strip() == "up":
                        self.net_dev = dev.upper()
                        break
                except OSError:
                    pass
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("10.255.255.255", 1))  # no packet actually sent
                self.ip = s.getsockname()[0]
                s.close()
            except OSError:
                self.ip = "--"
            self.sig = None
            try:
                for line in self._read("/proc/net/wireless").splitlines()[2:]:
                    if line.split(":")[0].strip() == "wlan0":
                        self.sig = min(1.0, float(
                            line.split()[2].rstrip(".")) / 70.0)
            except (OSError, ValueError, IndexError):
                pass
            self.ssid = ""
            try:
                out = subprocess.run(
                    ["iw", "dev", "wlan0", "info"], capture_output=True,
                    text=True, timeout=2).stdout
                for line in out.splitlines():
                    line = line.strip()
                    if line.startswith("ssid "):
                        self.ssid = line[5:].strip()
                        break
            except (OSError, subprocess.SubprocessError):
                pass
            try:
                up = float(self._read("/proc/uptime").split()[0])
                self.uptime = (f"{int(up // 3600)}h{int(up % 3600 // 60):02d}"
                               if up >= 3600 else f"{int(up // 60)}m")
            except OSError:
                self.uptime = "--"


def chamfer(poly, c):
    """Cut every corner of a convex polygon with a straight facet: each
    vertex becomes two points, one along each adjacent edge at distance c
    (clamped to 40% of the edge so short edges never invert)."""
    out = []
    n = len(poly)
    for i in range(n):
        vx, vy = poly[i]
        for qx, qy in (poly[i - 1], poly[(i + 1) % n]):
            dx, dy = qx - vx, qy - vy
            d = math.hypot(dx, dy) or 1.0
            t = min(c, 0.4 * d) / d
            out.append((vx + dx * t, vy + dy * t))
    return out


def eye_geometry(cx, cy, side, gaze, lid, tilt, size, squint=0.0,
                 pupil_k=1.0, w=EYE_W, h=EYE_H):
    """Straight-line eye geometry, no pygame: (outer_poly, inner_poly, pupil).

    The eye is TWO thin chamfered outlines (outer + inset echo) with a
    filled chamfered pupil that dilates with pupil_k. lid closes from the
    top, squint raises the bottom lid (happy squint reads different from
    a drooping lid). outer_poly is None when the eye is effectively shut
    (caller draws a chamfered bar instead); pupil is None when the opening
    is too short for it.
    side: -1 left eye, +1 right (tilt moves the OUTER top corner).
    """
    hh = h * size / 2.0
    l, r = cx - w // 2, cx + w // 2
    top, bot = cy - hh, cy + hh
    # tilt: outer top corner rises (+) / drops (-); inner nudges opposite.
    d_out, d_in = -tilt * 30.0, tilt * 8.0
    tl = top + (d_out if side < 0 else d_in)
    tr = top + (d_out if side > 0 else d_in)
    # lid: shutter descends from the top; squint: bottom lid rises.
    lid = max(0.0, min(1.0, lid))
    squint = max(0.0, min(1.0, squint))
    tl += (bot - tl) * lid
    tr += (bot - tr) * lid
    b = bot - 2.0 * hh * 0.5 * squint
    if min(b - tl, b - tr) < 14:
        return None, None, None  # effectively shut
    quad = [(l, tl), (r, tr), (r, b), (l, b)]
    c = CHAMFER * min(w, min(b - tl, b - tr))
    outer = chamfer(quad, c)
    # inner outline: an inset echo of the outer, parallel facets
    iquad = [(l + GAP, tl + GAP), (r - GAP, tr + GAP),
             (r - GAP, b - GAP), (l + GAP, b - GAP)]
    if min(p[1] for p in iquad[2:]) - max(iquad[0][1], iquad[1][1]) < 10:
        inner = None
    else:
        inner = chamfer(iquad, max(2.0, c - GAP * 0.414))

    # Human-pupil anatomy (user): the orange disc is the IRIS and its size
    # is FIXED; the black dot inside is the PUPIL, it DILATES with pupil_k
    # and rides the gaze. Ring outline frames the iris.
    base = min(w, h) * 0.36               # iris disc side (constant)
    ir = base * 1.42                      # iris ring side
    px = cx + gaze[0] * (w / 2.0 - ir / 2.0 - GAP - 4)
    py = cy + gaze[1] * (hh - ir / 2.0 - GAP - 4)
    # clamp the iris box inside the (tilted/lidded/squinted) opening
    top_at_px = tl + (tr - tl) * ((px - l) / (r - l))
    i_top = max(py - ir / 2.0, top_at_px + 6)
    i_bot = min(py + ir / 2.0, b - 6)
    if i_bot - i_top < 14:
        return outer, inner, None
    ibox = [(px - ir / 2, i_top), (px + ir / 2, i_top),
            (px + ir / 2, i_bot), (px - ir / 2, i_bot)]
    iris = chamfer(ibox, 0.29 * min(ir, i_bot - i_top))
    pad = (ir - base) / 2.0
    c_l, c_t = px - ir / 2 + pad, i_top + pad
    c_r, c_b = px + ir / 2 - pad, i_bot - pad
    if c_b - c_t < 8:
        return outer, inner, {"iris": iris, "core": None, "glint": None}
    cbox = [(c_l, c_t), (c_r, c_t), (c_r, c_b), (c_l, c_b)]
    core = chamfer(cbox, 0.29 * min(c_r - c_l, c_b - c_t))
    dot = None
    g = base * max(0.16, min(0.62, 0.30 * pupil_k))   # dilating pupil dot
    if c_b - c_t > g * 1.6:
        # the dot RIDES THE GAZE: it sits on the side the eye looks toward
        gcx = (c_l + c_r) / 2.0 + gaze[0] * ((c_r - c_l) - g) / 2.0 * 0.7
        gcy = (c_t + c_b) / 2.0 + gaze[1] * ((c_b - c_t) - g) / 2.0 * 0.7
        g_l = max(c_l + 3, min(c_r - g - 3, gcx - g / 2))
        g_t = max(c_t + 3, min(c_b - g - 3, gcy - g / 2))
        gbox = [(g_l, g_t), (g_l + g, g_t), (g_l + g, g_t + g),
                (g_l, g_t + g)]
        dot = chamfer(gbox, 0.3 * g)
    return outer, inner, {"iris": iris, "core": core, "glint": dot}


def shut_bar(cx, cy, w=EYE_W):
    """Chamfered-end bar for a fully shut eye (the trim-block silhouette)."""
    half, hh = w * 0.45, 5.0
    rect = [(cx - half, cy - hh), (cx + half, cy - hh),
            (cx + half, cy + hh), (cx - half, cy + hh)]
    return chamfer(rect, hh)


class FaceRenderer:
    """pygame drawing of a FaceState. Construct only where pygame exists."""

    def __init__(self, windowed=False):
        import pygame  # lazy
        self.pygame = pygame
        pygame.init()
        flags = 0 if windowed else pygame.FULLSCREEN
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
        pygame.display.set_caption("desk-pi face")
        pygame.mouse.set_visible(False)
        self.clock = pygame.time.Clock()
        self.state = FaceState(now=time.monotonic())
        self._dump_req = False
        self._boot_t0 = time.monotonic()
        self._ripples = []          # [(x, y, t0)] touch feedback
        self.status = None          # HUD status override (demo / brain)
        self.tele = Telemetry()
        self.campre = CamPreview()
        self.vision = VisionGaze()
        self._font_sm = pygame.font.SysFont(
            "dejavusansmono,menlo,consolas,monospace", 14)
        self._font_xs = pygame.font.SysFont(
            "dejavusansmono,menlo,consolas,monospace", 11)
        self._eye_gaze = {-1: (0.0, 0.0), 1: (0.0, 0.0)}  # per-eye eased
        self.face_col = ORANGE      # drifts toward RED under stress
        self._brain_ever = False    # any decision applied since start?
        self._nobrain = False
        self._dec_obj = None        # latest parsed brain decision
        self._dec_mt = None
        self._dec_t = -1e9
        self._dec_stale = False     # heartbeat: stale brain -> sleep
        self._dec_applied_mt = 0.0
        self._dec_pending = None
        self._status_until = None
        self._font = pygame.font.SysFont(
            "dejavusansmono,menlo,consolas,monospace", 17)
        self._text_cache = {}       # str -> rendered Surface
        signal.signal(signal.SIGUSR1, self._on_usr1)

    def _on_usr1(self, _sig, _frm):
        self._dump_req = True

    def set_expression(self, name):
        self.state.set_expression(name)

    # ------------------------------------------------------------- drawing

    def _eye(self, surf, cx, cy, side, lid, dt):
        pg = self.pygame
        st = self.state.pose
        tp = self.state.touch_pt
        if tp is not None:
            # each eye aims at the finger; but poked BETWEEN the eyes the
            # face goes full derp (user ref image): the eye nearer the
            # finger stares at it, the OTHER rolls up and outward.
            between = abs(tp[0]) < 0.28 and tp[1] < 0.35
            stare = -1 if tp[0] <= 0 else 1
            if between and side != stare:
                want = (0.7 * side, -1.0)
            else:
                tx = (tp[0] + 1) / 2 * SCREEN_W
                ty = (tp[1] + 1) / 2 * SCREEN_H
                want = (max(-1.0, min(1.0, (tx - cx) / (EYE_W * 0.75))),
                        max(-1.0, min(1.0, (ty - cy) / (EYE_H * 0.75))))
        elif self.vision.want is not None:
            # TRACKING BYPASS (user): person-following is a fast reflex
            # again; the LLM decides everything else but not gaze.
            want = self.vision.want
        else:
            want = st["gaze"]
        eg = self._eye_gaze[side]
        eg = (_ease(eg[0], want[0], dt, speed=12.0),
              _ease(eg[1], want[1], dt, speed=12.0))
        self._eye_gaze[side] = eg
        gaze = (eg[0] + self.state.sacc[0], eg[1] + self.state.sacc[1])
        outer, inner, pupil = eye_geometry(cx, cy, side, gaze, lid,
                                           st["tilt"],
                                           st["size"] * self.state.breath,
                                           squint=st["squint"],
                                           pupil_k=st["pupil"] *
                                           (1.0 + self.state.pupil_jit))
        if outer is None:
            pg.draw.polygon(surf, self.face_col, shut_bar(cx, cy))
            return
        # Two thin outlines (outer + inset echo), then the layered pupil:
        # iris ring outline, filled core, BG glint notch.
        pg.draw.polygon(surf, self.face_col, outer, STROKE)
        if inner is not None:
            pg.draw.polygon(surf, self.face_col, inner, STROKE_IN)
        if pupil is not None:
            pg.draw.polygon(surf, self.face_col, pupil["iris"], STROKE_IN)
            if pupil["core"] is not None:
                pg.draw.polygon(surf, self.face_col, pupil["core"])
            if pupil["glint"] is not None:
                pg.draw.polygon(surf, BG, pupil["glint"])

    def _text(self, s, color=HUD_FG, small=False, tiny=False):
        key = (s, color, small, tiny)
        if key not in self._text_cache:
            if len(self._text_cache) > 96:
                self._text_cache.clear()
            font = (self._font_xs if tiny
                    else self._font_sm if small else self._font)
            self._text_cache[key] = font.render(s, True, color)
        return self._text_cache[key]

    def _mouth(self, surf):
        pg = self.pygame
        st = self.state.pose
        m, op = st["mouth"], st["open"]
        if op > 0.25:
            # open mouth: small chamfered O outline, height grows with open
            hw, hh = 26.0, 7.0 + 20.0 * op
            rect = [(400 - hw, MOUTH_CY - hh), (400 + hw, MOUTH_CY - hh),
                    (400 + hw, MOUTH_CY + hh), (400 - hw, MOUTH_CY + hh)]
            pg.draw.polygon(surf, self.face_col, chamfer(rect, min(hw, hh) * 0.5),
                            STROKE)
            return
        # closed mouth: rigid 3-segment polyline, ends swing with the mood
        ye = MOUTH_CY - m * 24.0
        ym = MOUTH_CY + m * 9.0
        pts = [(400 - MOUTH_HALF, ye), (400 - 34, ym),
               (400 + 34, ym), (400 + MOUTH_HALF, ye)]
        pg.draw.lines(surf, self.face_col, False, pts, STROKE)

    def _spark(self, surf, x, y, w, h, hist, lo=0.0, hi=100.0):
        """Tiny fixed-scale sparkline (0..100%) with a hairline baseline."""
        pg = self.pygame
        pg.draw.line(surf, HUD_DIM, (x, y + h + 2), (x + w, y + h + 2), 1)
        if len(hist) < 2:
            return
        span = max(hi - lo, 1e-6)
        pts = [(x + i * w / (len(hist) - 1),
                y + h - min(1.0, max(0.0, (v - lo) / span)) * h)
               for i, v in enumerate(hist)]
        pg.draw.lines(surf, HUD_MID, False, pts, 2)

    def _decision_line(self, now):
        """Poll DECISION_FILE every 2 s: display line, NEW decisions queued
        for execution (self._dec_pending), staleness for the sleep rule."""
        if now - self._dec_t >= 2.0:
            self._dec_t = now
            self._dec_stale = True
            try:
                mt = os.path.getmtime(DECISION_FILE)
                self._dec_mt = mt
                self._dec_stale = (time.time() - mt) > BRAIN_STALE_S
                with open(DECISION_FILE) as f:
                    self._dec_obj = json.load(f)
                if mt != self._dec_applied_mt:
                    self._dec_applied_mt = mt
                    self._dec_pending = self._dec_obj
            except (OSError, ValueError):
                self._dec_obj = None

    @staticmethod
    def _wrap(s, width, max_lines=5):
        words, lines, cur = s.split(), [], ""
        for w in words:
            if len(cur) + len(w) + 1 > width and cur:
                lines.append(cur)
                cur = w
            else:
                cur = f"{cur} {w}".strip()
        if cur:
            lines.append(cur)
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = lines[-1][:width - 1] + "…"
        return lines

    def _header(self, surf, x, y, w, label):
        img = self._text(label, HUD_DIM, tiny=True)
        surf.blit(img, (x, y))
        my = y + img.get_height() // 2 + 1
        self.pygame.draw.line(surf, HUD_FAINT,
                              (x + img.get_width() + 6, my), (x + w, my), 1)
        return y + img.get_height() + 5

    def _panel_vision(self, surf, now):
        """Left side: everything the vision models see, in one place."""
        pg = self.pygame
        x0, w = 22, 124
        y = self._header(surf, x0, 76, w, "VISION")
        cimg = self.campre.surface(pg, now)
        raw = self.vision.raw
        if cimg is not None:
            cw, chh = CamPreview.SIZE
            surf.blit(cimg, (x0, y))
            for sy in range(y, y + chh, 3):
                pg.draw.line(surf, BG, (x0, sy), (x0 + cw - 1, sy), 1)
            pg.draw.rect(surf, HUD_FAINT,
                         pg.Rect(x0 - 1, y - 1, cw + 2, chh + 2), 1)
            if raw and raw.get("box"):
                bx, by, bw, bh = raw["box"]
                pg.draw.rect(surf, HUD_MID, pg.Rect(
                    x0 + int(bx * cw / 320), y + int(by * chh / 240),
                    max(2, int(bw * cw / 320)),
                    max(2, int(bh * chh / 240))), 1)
            y += chh + 7
        lines = []
        if raw is None:
            lines.append(("offline", HUD_MID))
        elif raw.get("person_present"):
            lines.append((f'face {raw["n_faces"]}  conf {raw["conf"]:.2f}',
                          HUD_FAINT))
            lines.append((f'x {raw["cx"]:+.2f}  y {raw["cy"]:+.2f}',
                          HUD_FAINT))
            lines.append((f'size {raw["size"]:.2f}', HUD_FAINT))
            lines.append((f'facing '
                          f'{"yes" if raw.get("facing_camera") else "no"}',
                          HUD_FAINT))
            if "visible_expression" in raw:
                lines.append((f'looks {raw["visible_expression"]}',
                              HUD_MID))
                lines.append((f'smile {raw.get("smile", 0):.2f}  ear '
                              f'{raw.get("ear", 0):.2f}', HUD_FAINT))
            if raw.get("gesture") and raw["gesture"] != "none":
                lines.append((f'gesture {raw["gesture"]}', HUD_MID))
            lines.append((f'{raw.get("infer_ms", 0):.0f}ms det  '
                          f'{raw.get("lm_ms", 0):.0f}ms lmk '
                          f'{raw.get("hand_ms", 0):.0f}ms hnd', HUD_FAINT))
        else:
            lines.append(("no face", HUD_MID))
            lines.append((f'{raw.get("infer_ms", 0):.0f}ms det', HUD_FAINT))
        for s, col in lines:
            surf.blit(self._text(s, col, tiny=True), (x0, y))
            y += 14

    def _panel_brain(self, surf, now):
        """Right side: what the LLM decided, clearly labeled as such."""
        x0, w = 654, 124
        y = self._header(surf, x0, 76, w, "BRAIN")
        if self._dec_stale:
            state, col = (("OFFLINE -> dozing", HUD_BAD)
                          if self._brain_ever else ("WARMING UP", HUD_MID))
        else:
            state, col = "LIVE", HUD_MID
        age = (f'  {int(time.time() - self._dec_mt)}s'
               if self._dec_mt else "")
        surf.blit(self._text(f"{state}{age}", col, tiny=True), (x0, y))
        y += 16
        d = self._dec_obj
        if not d:
            return
        # cycle latency, prominent (user): how long the brain thought
        if d.get("latency_s") is not None:
            lat = f'cycle {d["latency_s"]:.1f}s'
            if d.get("prompt_ms") is not None:
                lat += (f' {d["prompt_ms"] / 1000:.0f}+'
                        f'{d.get("gen_ms", 0) / 1000:.0f}')
            surf.blit(self._text(lat[:19], HUD_FG, tiny=True), (x0, y))
            y += 15
        for a in d.get("actions", [])[:4]:
            if not isinstance(a, dict):
                continue
            do = a.get("do", "?")
            arg = (a.get("name") or a.get("text") or a.get("note")
                   or a.get("task") or "")
            if do == "look_at":
                arg = f'{a.get("pan_deg", 0)},{a.get("tilt_deg", 0)}'
            s = f'{do} {arg}'.rstrip()[:19]
            surf.blit(self._text(s, HUD_MID, tiny=True), (x0, y))
            y += 13
        y += 4
        for line in self._wrap(str(d.get("reason", "")), 20):
            surf.blit(self._text(line, HUD_FAINT, tiny=True), (x0, y))
            y += 12

    def _apply_brain(self, now):
        """Execute the LLM's decision: the brain is the ONLY source of
        truth for expression/gaze/speech. A stale brain puts the face to
        sleep until decisions flow again."""
        d, self._dec_pending = self._dec_pending, None
        if d:
            acts = [a for a in d.get("actions", []) if isinstance(a, dict)]
            seen_expr = [a for a in acts if a.get("do") == "set_expression"]
            if len(seen_expr) > 1:   # contradictory duplicates: last wins
                acts = [a for a in acts if a.get("do") != "set_expression"
                        ] + [seen_expr[-1]]
            for a in acts:
                if not isinstance(a, dict):
                    continue
                do = a.get("do")
                if do == "set_expression" and a.get("name") in EXPRESSIONS:
                    self.set_expression(a["name"])
                elif do == "look_at":
                    pass   # gaze is a tracking reflex now (user); ignore
                elif do == "say" and a.get("text"):
                    self.status = f'"{str(a["text"])[:56]}"'
                    self._status_until = now + 6.0
        if self._status_until is not None and now > self._status_until:
            self.status = None
            self._status_until = None
        if d:
            self._brain_ever = True
        if self._dec_stale:
            # NO-BRAIN state: dozing face + animated status, two flavors
            dots = "." * (1 + int(now * 2) % 3)
            self.status = (f"BRAIN OFFLINE{dots}" if self._brain_ever
                           else f"BRAIN STARTING{dots}")
            self._nobrain = True
            if self.state.expression != "dozing":
                self.set_expression("dozing")
            # slow breath of the lids while dozing
            self.state.target["lid"] = 0.55 + 0.18 * math.sin(now * 0.7)
        elif self._nobrain:
            self._nobrain = False
            self.status = None
            if self.state.expression == "dozing":
                self.set_expression("neutral")

    def _hud(self, surf, now):
        """Corner telemetry blocks in cool HUD tones (orange belongs to the
        face): SYS + temp sparkline top-left, NET top-right, status line
        bottom-left, sensor slots + heartbeat pip bottom-right."""
        pg = self.pygame
        self.tele.sample(now)
        te = self.tele
        m, ln, wd = 14, 26, 3
        for cx, sx in ((m, 1), (SCREEN_W - m, -1)):
            for cy, sy in ((m, 1), (SCREEN_H - m, -1)):
                pg.draw.line(surf, HUD_DIM, (cx, cy), (cx + sx * ln, cy), wd)
                pg.draw.line(surf, HUD_DIM, (cx, cy), (cx, cy + sy * ln), wd)

        # --- top-left: SYS block, one labeled sparkline row per metric
        x0, y0 = m + 12, m + 12
        t = f"{te.temp:.0f}C" if te.temp is not None else "--"
        ld = f"{te.load_pct:2d}%" if te.load_pct is not None else "--"
        mem = f"{te.mem_pct:2d}%" if te.mem_pct is not None else "--"
        rows = ((f"CPU {ld} {t}", te.load_hist),
                (f"MEM {mem}", te.mem_hist))
        for i, (label, hist) in enumerate(rows):
            ry = y0 + i * 20
            surf.blit(self._text(label, HUD_FG, small=True), (x0, ry))
            self._spark(surf, x0 + 118, ry + 3, 96, 12, hist)

        # --- top-center: dedicated PWR block (real PMIC numbers)
        if te.watts is not None:
            uv_now = bool(te.throttled and te.throttled & 0x1)
            uv_past = bool(te.throttled and te.throttled & 0x10000)
            state = "UV!" if uv_now else ("OK*" if uv_past else "OK")
            cv = f"{te.core_v:.2f}V" if te.core_v is not None else "--"
            ptxt = self._text(f"PWR {te.watts:.1f}W {cv} {state}",
                              HUD_BAD if uv_now else HUD_FG, small=True)
            px0 = 268   # fixed slot between the SYS and NET blocks
            surf.blit(ptxt, (px0, m + 12))
            self._spark(surf, px0 + ptxt.get_width() + 12, m + 15, 46, 10,
                        te.watts_hist, lo=0.0, hi=12.0)

        # --- top-right: NET block (right-aligned)
        ssid = f" {te.ssid}" if te.ssid else ""
        line1 = f"NET {te.net_dev}{ssid}  {te.ip}"
        img = self._text(line1, HUD_FG, small=True)
        surf.blit(img, (SCREEN_W - m - 12 - img.get_width(), m + 12))
        # signal bar: 5 segments
        bx = SCREEN_W - m - 12 - 5 * 14
        by = m + 34
        for i in range(5):
            r = pg.Rect(bx + i * 14, by, 10, 12)
            if te.sig is not None and te.sig >= (i + 1) / 5.0 - 0.001:
                pg.draw.rect(surf, HUD_MID, r)
            else:
                pg.draw.rect(surf, HUD_DIM, r, 1)
        up = self._text(f"UP {te.uptime}", HUD_DIM, small=True)
        surf.blit(up, (bx - up.get_width() - 12, by - 1))

        # --- bottom band: hairline separator ties status + sensors together
        pg.draw.line(surf, HUD_FAINT, (m + 12, SCREEN_H - 48),
                     (SCREEN_W - m - 12, SCREEN_H - 48), 1)
        # --- bottom-left: status line
        label = self.status or f"PARVIZ // {self.state.expression.upper()}"
        img = self._text(label)
        surf.blit(img, (m + 12, SCREEN_H - m - img.get_height() - 12))
        if int(now * 2) % 2 == 0:  # blinking block cursor
            pg.draw.rect(surf, HUD_MID, pg.Rect(
                m + 16 + img.get_width(),
                SCREEN_H - m - img.get_height() - 10, 9,
                img.get_height() - 4))

        # --- side panels: provenance-labeled VISION (left) / BRAIN (right)
        self._decision_line(now)   # refresh heartbeat + pending decision
        self._panel_vision(surf, now)
        self._panel_brain(surf, now)

        # --- bottom-right: sensor slots (fill in as hardware arrives)
        cam_s = "OK" if self.campre.ok else "--"
        sens = self._text(f"MIC --  CAM {cam_s}  RDR --  IMU --", HUD_FAINT,
                          tiny=True)
        sx = SCREEN_W - m - 34 - sens.get_width()
        sy = SCREEN_H - m - sens.get_height() - 14
        surf.blit(sens, (sx, sy))
        # heartbeat pip: breathes with the eyes (proof of life)
        k = (self.state.breath - 1.0) / BREATH_MAG  # -1..1
        r = 5 + 2 * k
        pg.draw.rect(surf, HUD_MID, pg.Rect(
            int(SCREEN_W - m - 12 - r), int(SCREEN_H - m - 18 - r),
            int(2 * r), int(2 * r)))

    def _draw_ripples(self, surf, now):
        pg = self.pygame
        keep = []
        for (x, y, t0) in self._ripples:
            ph = (now - t0) / RIPPLE_LEN_S
            if ph >= 1.0:
                continue
            keep.append((x, y, t0))
            half = 14 + 46 * ph
            col = tuple(int(c * (1.0 - ph)) for c in self.face_col)
            rect = [(x - half, y - half), (x + half, y - half),
                    (x + half, y + half), (x - half, y + half)]
            pg.draw.polygon(surf, col, chamfer(rect, half * 0.35), 2)
        self._ripples = keep

    def _stress_tint(self, dt):
        """Face color: orange -> red as the WORST of temp/cpu/mem climbs.
        Eased so the hue breathes instead of flickering."""
        te = self.tele

        def norm(v, lo, hi):
            return 0.0 if v is None else max(0.0, min(1.0,
                                                      (v - lo) / (hi - lo)))
        stress = max(norm(te.temp, 60.0, 85.0),
                     norm(te.load_pct, 50.0, 100.0),
                     norm(te.mem_pct, 60.0, 95.0))
        want = tuple(ORANGE[i] + (RED[i] - ORANGE[i]) * stress
                     for i in range(3))
        self.face_col = tuple(
            min(255, max(0, int(round(_ease(self.face_col[i], want[i], dt,
                                            speed=1.2)))))
            for i in range(3))

    def draw(self, lid, dt=1.0 / 30):
        surf = self.screen
        now = time.monotonic()
        surf.fill(BG)
        boot_ph = (now - self._boot_t0) / BOOT_LEN_S
        self.vision.poll(now)
        self._stress_tint(dt)
        self._hud(surf, now)
        for side, ex in ((-1, EYE_CX[0]), (1, EYE_CX[1])):
            self._eye(surf, ex, EYE_CY, side, lid, dt)
        self._mouth(surf)
        if boot_ph < 1.0:
            # power-on: curtains sweep open from the center line outward,
            # and the status line types itself out.
            f = 1.0 - (1.0 - max(0.0, boot_ph)) ** 3  # ease-out cubic
            w_open = int((SCREEN_W / 2) * f)
            surf.fill(BG, self.pygame.Rect(0, 0, SCREEN_W // 2 - w_open,
                                           SCREEN_H))
            surf.fill(BG, self.pygame.Rect(SCREEN_W // 2 + w_open, 0,
                                           SCREEN_W, SCREEN_H))
            boot_label = "PARVIZ // BOOT"
            img = self._text(boot_label[:max(1, int(len(boot_label) * f))],
                             DIM)
            surf.blit(img, (26, SCREEN_H - 14 - img.get_height() - 6))
        self._draw_ripples(surf, now)
        if self._dump_req:
            self._dump_req = False
            try:
                self.pygame.image.save(surf, FRAME_DUMP)
                print(f"frame dumped to {FRAME_DUMP}", flush=True)
            except Exception as e:  # never kill the face over a debug dump
                print(f"frame dump failed: {e}", file=sys.stderr, flush=True)
        self.pygame.display.flip()

    # ---------------------------------------------------------------- loop

    def run(self, seconds=None):
        pg = self.pygame
        t_start = time.monotonic()
        last = t_start
        while True:
            now = time.monotonic()
            dt = min(0.1, now - last)
            last = now
            if seconds is not None and now - t_start >= seconds:
                break
            for ev in pg.event.get():
                if ev.type == pg.QUIT:
                    return
                if ev.type == pg.KEYDOWN and ev.key in (pg.K_ESCAPE, pg.K_q):
                    return
                # Touchscreen: pupils track the finger, release blinks.
                # (SDL also synthesizes mouse events from touch; handle both,
                # the duplicate state updates are idempotent.)
                if ev.type in (pg.FINGERDOWN, pg.FINGERMOTION):
                    self.state.touch((ev.x * 2 - 1, ev.y * 2 - 1))
                    if ev.type == pg.FINGERDOWN:
                        self._ripples.append((ev.x * SCREEN_W,
                                              ev.y * SCREEN_H, now))
                elif ev.type == pg.FINGERUP:
                    self.state.touch(None)
                elif ev.type == pg.MOUSEBUTTONDOWN or \
                        (ev.type == pg.MOUSEMOTION and ev.buttons[0]):
                    x, y = ev.pos
                    self.state.touch((x / SCREEN_W * 2 - 1,
                                      y / SCREEN_H * 2 - 1))
                    if ev.type == pg.MOUSEBUTTONDOWN:
                        self._ripples.append((x, y, now))
                elif ev.type == pg.MOUSEBUTTONUP:
                    self.state.touch(None)
            if self.state.touch_pt is None:
                # The LLM is the only source of truth for behavior.
                self._apply_brain(now)
            lid = self.state.tick(now, dt)
            self.draw(lid, dt)
            self.clock.tick(30)


def main(argv=None):
    ap = argparse.ArgumentParser(description="desk-pi face renderer")
    ap.add_argument("--windowed", action="store_true",
                    help="800x480 window instead of fullscreen (dev)")
    ap.add_argument("--seconds", type=float, default=None,
                    help="auto-exit after N seconds (for SSH smoke tests)")
    ap.add_argument("--expression", default="neutral",
                    choices=sorted(EXPRESSIONS), help="initial expression")
    args = ap.parse_args(argv)

    # A SIGUSR1 (frame-dump request) arriving before the renderer installs
    # its handler must not kill the process (default disposition is TERM).
    signal.signal(signal.SIGUSR1, signal.SIG_IGN)

    # Headless console (SSH, no desktop): default SDL to KMS/DRM.
    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY") \
            and "SDL_VIDEODRIVER" not in os.environ:
        os.environ["SDL_VIDEODRIVER"] = "kmsdrm"

    try:
        face = FaceRenderer(windowed=args.windowed)
    except Exception as e:
        drv = os.environ.get("SDL_VIDEODRIVER", "(auto)")
        print(f"FATAL: cannot open display (SDL driver {drv}): {e}",
              file=sys.stderr)
        print("If a desktop session owns the screen, run inside it "
              "(WAYLAND_DISPLAY=wayland-0 or DISPLAY=:0) instead of kmsdrm.",
              file=sys.stderr)
        return 1
    face.set_expression(args.expression)
    face.run(seconds=args.seconds)
    face.pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())

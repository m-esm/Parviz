"""desk-pi face renderer: fullscreen animated face for the official 7" display.

Look (2026-07-12 revision, styled after the rendered CAD model): RIGID
LINES ONLY, two CHAMFERED-corner eyes drawn as thick orange ring frames
(the chassis fascia's grille ring / the design-ref bezel octagon) with
chamfered square pupils; a shut eye is a chamfered-end bar like the
trim blocks. No mouth, no eyebrows. Single color: the body's safety
orange (src/geo.py COLORS["accent"] = 232,116,34) on black. Expressions
are carried by lid height, top-corner tilt and pupil position, every
stroke is a straight line. TOUCH: while a finger is on the panel the
pupils track it (eyes widen slightly); lifting it blinks and returns
to the current expression.

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
import math
import os
import random
import signal
import sys
import time

SCREEN_W, SCREEN_H = 800, 480

# Single-color palette: body safety orange (src/geo.py COLORS["accent"]).
BG = (0, 0, 0)
ORANGE = (232, 116, 34)

# Layout scales off the panel size (800x480): big eyes that own the screen.
EYE_W = int(SCREEN_W * 0.28)          # 224
EYE_H = int(SCREEN_H * 0.40)          # 192
EYE_CX = (int(SCREEN_W * 0.30), int(SCREEN_W * 0.70))   # 240, 560
EYE_CY = SCREEN_H // 2
STROKE = 12                            # ring-frame wall, reads like the grille ring
CHAMFER = 0.20                         # corner cut as a fraction of the eye opening

FRAME_DUMP = "/tmp/face_frame.png"

# name -> dict of pose targets the animator eases toward.
#   gaze: (-1..1, -1..1) pupil offset, +x = viewer's right, +y = down
#   lid:  0 open .. 1 closed (straight shutter from the top)
#   tilt: -1 outer top corners drop (sad) .. +1 outer top corners rise
#   size: eye height scale (surprised > 1)
EXPRESSIONS = {
    "neutral":    dict(gaze=(0.0, 0.0),  lid=0.0,  tilt=0.0,  size=1.0),
    "happy":      dict(gaze=(0.0, -0.1), lid=0.2,  tilt=0.6,  size=0.9),
    "sad":        dict(gaze=(0.0, 0.35), lid=0.25, tilt=-0.7, size=1.0),
    "surprised":  dict(gaze=(0.0, -0.2), lid=0.0,  tilt=0.1,  size=1.3),
    "sleepy":     dict(gaze=(0.0, 0.3),  lid=0.6,  tilt=-0.2, size=1.0),
    "look_left":  dict(gaze=(-0.9, 0.0), lid=0.0,  tilt=0.0,  size=1.0),
    "look_right": dict(gaze=(0.9, 0.0),  lid=0.0,  tilt=0.0,  size=1.0),
    "look_up":    dict(gaze=(0.0, -0.9), lid=0.0,  tilt=0.2,  size=1.05),
    "look_down":  dict(gaze=(0.0, 0.9),  lid=0.15, tilt=0.0,  size=1.0),
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

    def set_expression(self, name):
        if name not in EXPRESSIONS:
            raise ValueError(
                f"unknown expression {name!r}; one of {sorted(EXPRESSIONS)}"
            )
        self.expression = name
        self.target = dict(EXPRESSIONS[name])

    def touch(self, gaze):
        """Touchscreen hook: gaze=(-1..1, -1..1) while a finger is down
        (pupils track it, eyes widen a little), None on release (back to
        the current expression + an acknowledging blink)."""
        if gaze is None:
            self.target = dict(EXPRESSIONS[self.expression])
            self._blink_t0 = None
            self._next_blink = 0.0     # blink on the next tick
            return
        gx = max(-1.0, min(1.0, gaze[0]))
        gy = max(-1.0, min(1.0, gaze[1]))
        self.target = dict(self.target)
        self.target.update(gaze=(gx, gy), lid=0.0, size=1.1)

    def tick(self, now, dt):
        gx, gy = self.pose["gaze"]
        tx, ty = self.target["gaze"]
        self.pose["gaze"] = (_ease(gx, tx, dt), _ease(gy, ty, dt))
        for k in ("lid", "tilt", "size"):
            self.pose[k] = _ease(self.pose[k], self.target[k], dt)

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


def eye_geometry(cx, cy, side, gaze, lid, tilt, size,
                 w=EYE_W, h=EYE_H, stroke=STROKE):
    """Straight-line eye geometry, no pygame: (outer_poly, inner_poly, pupil).

    The eye is a chamfered-corner ring frame (the model's grille-ring motif):
    outer_poly filled in orange, inner_poly punched back to black, pupil a
    filled chamfered square clamped inside the opening. outer_poly is None
    when the eye is effectively shut (caller draws a chamfered bar instead);
    pupil is None when the opening is too short for it.
    side: -1 left eye, +1 right (tilt moves the OUTER top corner).
    """
    hh = h * size / 2.0
    l, r = cx - w // 2, cx + w // 2
    top, bot = cy - hh, cy + hh
    # tilt: outer top corner rises (+) / drops (-); inner nudges opposite.
    d_out, d_in = -tilt * 30.0, tilt * 8.0
    tl = top + (d_out if side < 0 else d_in)
    tr = top + (d_out if side > 0 else d_in)
    # lid: shutter descends from the top, straight edge.
    lid = max(0.0, min(1.0, lid))
    tl += (bot - tl) * lid
    tr += (bot - tr) * lid
    if min(bot - tl, bot - tr) < stroke * 1.5:
        return None, None, None  # effectively shut
    quad = [(l, tl), (r, tr), (r, bot), (l, bot)]
    c = CHAMFER * min(w, min(bot - tl, bot - tr))
    outer = chamfer(quad, c)
    # Inner frame edge: inset the quad by the wall, chamfer with the facet
    # kept parallel to the outer one (a 45-deg facet inset by s sits at
    # corner distance c - s*(sqrt(2)-1)).
    iquad = [(l + stroke, tl + stroke), (r - stroke, tr + stroke),
             (r - stroke, bot - stroke), (l + stroke, bot - stroke)]
    inner = chamfer(iquad, max(2.0, c - stroke * 0.414))

    pw = int(w * 0.30)
    ph_full = int(h * 0.42)
    px = cx + gaze[0] * (w / 2.0 - pw / 2.0 - stroke * 2)
    py = cy + gaze[1] * (hh - ph_full / 2.0 - stroke * 2)
    # clamp the pupil under the (possibly tilted/lowered) top edge
    top_at_px = tl + (tr - tl) * ((px - l) / (r - l))
    p_top = max(py - ph_full / 2.0, top_at_px + stroke * 1.5)
    p_bot = min(py + ph_full / 2.0, bot - stroke * 1.5)
    if p_bot - p_top < 10:
        return outer, inner, None
    prect = [(px - pw / 2, p_top), (px + pw / 2, p_top),
             (px + pw / 2, p_bot), (px - pw / 2, p_bot)]
    pupil = chamfer(prect, 0.28 * min(pw, p_bot - p_top))
    return outer, inner, pupil


def shut_bar(cx, cy, w=EYE_W, stroke=STROKE):
    """Chamfered-end bar for a fully shut eye (the trim-block silhouette)."""
    half, hh = w * 0.45, stroke * 0.7
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
        signal.signal(signal.SIGUSR1, self._on_usr1)

    def _on_usr1(self, _sig, _frm):
        self._dump_req = True

    def set_expression(self, name):
        self.state.set_expression(name)

    # ------------------------------------------------------------- drawing

    def _eye(self, surf, cx, cy, side, lid):
        pg = self.pygame
        st = self.state.pose
        outer, inner, pupil = eye_geometry(cx, cy, side, st["gaze"], lid,
                                           st["tilt"], st["size"])
        if outer is None:
            pg.draw.polygon(surf, ORANGE, shut_bar(cx, cy))
            return
        # Ring frame: fill the chamfered outline, punch the opening back out.
        pg.draw.polygon(surf, ORANGE, outer)
        pg.draw.polygon(surf, BG, inner)
        if pupil is not None:
            pg.draw.polygon(surf, ORANGE, pupil)

    def draw(self, lid):
        surf = self.screen
        surf.fill(BG)
        for side, ex in ((-1, EYE_CX[0]), (1, EYE_CX[1])):
            self._eye(surf, ex, EYE_CY, side, lid)
        if self._dump_req:
            self._dump_req = False
            try:
                self.pygame.image.save(surf, FRAME_DUMP)
                print(f"frame dumped to {FRAME_DUMP}", flush=True)
            except Exception as e:  # never kill the face over a debug dump
                print(f"frame dump failed: {e}", file=sys.stderr, flush=True)
        self.pygame.display.flip()

    # ---------------------------------------------------------------- loop

    def run(self, seconds=None, demo=False):
        pg = self.pygame
        t_start = time.monotonic()
        demo_seq = list(EXPRESSIONS)
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
                elif ev.type == pg.FINGERUP:
                    self.state.touch(None)
                elif ev.type == pg.MOUSEBUTTONDOWN or \
                        (ev.type == pg.MOUSEMOTION and ev.buttons[0]):
                    x, y = ev.pos
                    self.state.touch((x / SCREEN_W * 2 - 1,
                                      y / SCREEN_H * 2 - 1))
                elif ev.type == pg.MOUSEBUTTONUP:
                    self.state.touch(None)
            if demo:
                idx = int((now - t_start) / 2.0) % len(demo_seq)
                if demo_seq[idx] != self.state.expression:
                    self.set_expression(demo_seq[idx])
            lid = self.state.tick(now, dt)
            self.draw(lid)
            self.clock.tick(30)


def main(argv=None):
    ap = argparse.ArgumentParser(description="desk-pi face renderer")
    ap.add_argument("--windowed", action="store_true",
                    help="800x480 window instead of fullscreen (dev)")
    ap.add_argument("--seconds", type=float, default=None,
                    help="auto-exit after N seconds (for SSH smoke tests)")
    ap.add_argument("--expression", default="neutral",
                    choices=sorted(EXPRESSIONS), help="initial expression")
    ap.add_argument("--demo", action="store_true",
                    help="cycle through all expressions every 2 s")
    args = ap.parse_args(argv)

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
    face.run(seconds=args.seconds, demo=args.demo)
    face.pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())

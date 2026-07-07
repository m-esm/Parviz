"""desk-pi face renderer: fullscreen animated face for the official 7" display.

Design ref: reference/design/front.jpg, near-black screen, two big cyan
outlined round eyes with offset pupils + white highlight dots, thin arc
eyebrows, small smile arc. Idle blink every few seconds.

Display target: 800x480 (official RPi 7" touchscreen, DSI).

Running over SSH with no desktop session (console owns the display):
    SDL_VIDEODRIVER=kmsdrm python3 face.py
KMS/DRM needs the 'render'+'video' groups (default for the first user on
Raspberry Pi OS) and a free (non-desktop) VT. If a Wayland/X desktop session
owns the display, kmsdrm will fail with "Could not initialize KMSDRM",
in that case run it INSIDE the session instead:
    WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/$(id -u) python3 face.py
(or DISPLAY=:0 on X11). Don't fight the compositor for the DRM master.

Dev on a laptop:  python3 face.py --windowed --seconds 10

API stub: FaceRenderer.set_expression(name), supported names in EXPRESSIONS.
pygame is imported lazily so this module imports (and its geometry is
testable) on machines without pygame.
"""

import argparse
import math
import os
import random
import sys
import time

SCREEN_W, SCREEN_H = 800, 480

# Palette pulled from the design render (front.jpg vibe).
BG = (7, 12, 26)            # near-black navy
GLOW = (90, 200, 235)       # cyan line work (eyes, brows, mouth)
GLOW_DIM = (34, 80, 105)    # outer glow pass
PUPIL = (120, 215, 245)
HIGHLIGHT = (235, 250, 255)

# name -> dict of pose targets the animator eases toward.
#   gaze: (-1..1, -1..1) pupil offset, +x = viewer's right, +y = down
#   lid:  0 open .. 1 closed
#   brow: -1 angry .. 0 neutral .. 1 raised
#   smile: 0 flat .. 1 big smile, negative = frown
EXPRESSIONS = {
    "neutral":    dict(gaze=(0.0, 0.0),  lid=0.0, brow=0.15, smile=0.45),
    "happy":      dict(gaze=(0.0, -0.1), lid=0.15, brow=0.6, smile=1.0),
    "sad":        dict(gaze=(0.0, 0.35), lid=0.35, brow=-0.4, smile=-0.6),
    "surprised":  dict(gaze=(0.0, -0.2), lid=-0.2, brow=1.0, smile=0.15),
    "sleepy":     dict(gaze=(0.0, 0.3),  lid=0.65, brow=0.0, smile=0.2),
    "look_left":  dict(gaze=(-0.9, 0.0), lid=0.0, brow=0.15, smile=0.45),
    "look_right": dict(gaze=(0.9, 0.0),  lid=0.0, brow=0.15, smile=0.45),
    "look_up":    dict(gaze=(0.0, -0.9), lid=0.0, brow=0.5, smile=0.45),
    "look_down":  dict(gaze=(0.0, 0.9),  lid=0.2, brow=0.0, smile=0.3),
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

    def tick(self, now, dt):
        gx, gy = self.pose["gaze"]
        tx, ty = self.target["gaze"]
        self.pose["gaze"] = (_ease(gx, tx, dt), _ease(gy, ty, dt))
        for k in ("lid", "brow", "smile"):
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

    def set_expression(self, name):
        self.state.set_expression(name)

    # ------------------------------------------------------------- drawing

    def _eye(self, surf, cx, cy, r, gaze, lid):
        pg = self.pygame
        # soft outer glow + main ring
        pg.draw.circle(surf, GLOW_DIM, (cx, cy), r + 6, 10)
        pg.draw.circle(surf, GLOW, (cx, cy), r, 7)
        # pupil: offset disc with two highlight dots (design-ref look)
        px = cx + int(gaze[0] * r * 0.42)
        py = cy + int(gaze[1] * r * 0.42)
        pr = int(r * 0.52)
        pg.draw.circle(surf, PUPIL, (px, py), pr)
        pg.draw.circle(surf, HIGHLIGHT, (px - pr // 3, py - pr // 3),
                       max(3, pr // 4))
        pg.draw.circle(surf, HIGHLIGHT, (px + pr // 3, py + pr // 5),
                       max(2, pr // 7))
        # lid: BG-colored shutter descending from above the eye
        if lid > 0.02:
            cover = int((r + 12) * 2 * min(1.0, lid))
            rect = pg.Rect(cx - r - 12, cy - r - 12, (r + 12) * 2, cover)
            pg.draw.rect(surf, BG, rect)
            if lid < 0.98:  # lid edge line
                y = rect.bottom
                pg.draw.line(surf, GLOW, (cx - r, y), (cx + r, y), 5)

    def _brow(self, surf, cx, cy, r, brow, side):
        pg = self.pygame
        lift = int(brow * 14)
        w, h = int(r * 1.7), int(r * 0.9)
        rect = pg.Rect(cx - w // 2, cy - r - 38 - lift, w, h)
        # slight inner tilt when negative (angry)
        a0, a1 = math.radians(25), math.radians(155)
        pg.draw.arc(surf, GLOW, rect, a0, a1, 6)

    def _mouth(self, surf, cx, cy, smile):
        pg = self.pygame
        w = 120 + int(40 * abs(smile))
        h = max(10, int(56 * abs(smile)))
        if smile >= 0:
            rect = pg.Rect(cx - w // 2, cy - h, w, h * 2)
            pg.draw.arc(surf, GLOW, rect, math.radians(200),
                        math.radians(340), 7)
        else:
            rect = pg.Rect(cx - w // 2, cy, w, h * 2)
            pg.draw.arc(surf, GLOW, rect, math.radians(20),
                        math.radians(160), 7)

    def draw(self, lid):
        surf = self.screen
        surf.fill(BG)
        st = self.state.pose
        eye_r = 68
        ey = 190
        for side, ex in ((-1, 280), (1, 520)):
            self._brow(surf, ex, ey, eye_r, st["brow"], side)
            self._eye(surf, ex, ey, eye_r, st["gaze"], lid)
        self._mouth(surf, 400, 360, st["smile"])
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

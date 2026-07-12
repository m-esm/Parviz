#!/usr/bin/env python3
"""Wall-thickness gate for the desk-pi PRINTED-PART set (`make wallcheck`).

Adapted from the 3d-print-modeling skill's wallcheck.py (self-thickness mode):
ray-based material depth along the inward normal (trimesh.proximity.thickness)
over surface samples of every printed STL in stl/<subsystem>/. Reports the 1st
percentile (robust against grazing rays) and the absolute minimum with its
location.

Gate rules (exit 1 on any failure, so the Makefile can gate on it):
  * mesh must be WATERTIGHT -- an open print mesh is itself a defect, and the
    ray thickness numbers on it are meaningless (rays escape through the holes
    and read near-zero).
  * p1 thickness >= MIN_WALL (0.8 mm), unless the part carries a WHITELIST
    entry with a documented reason and its own floor.
  * absolute minima below SPOT_LIMIT are printed with their location as
    informational findings (NON-gating: single-ray minima are dominated by
    grazing rays on chamfer facets and designed micro-steps).

The printed set mirrors the EXPORT list in CLAUDE.md "Print notes", with the
print-in-place track STRIPS standing in for the assembled track_L/R loop
meshes (the strips are what actually prints; track_L/R.stl are the posed
assembly loops and duplicate them).

Python 3.9; trimesh + numpy only. Deterministic (seeded sampling).
"""
import os
import sys
import warnings

import numpy as np

warnings.filterwarnings("ignore", category=RuntimeWarning)  # trimesh boolean prep noise

import trimesh  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stlpaths import stlp  # noqa: E402

MIN_WALL = float(os.environ.get("MIN_WALL", "0.8"))   # FDM: 2 x 0.4 nozzle perimeters
SPOT_LIMIT = 0.5        # report (not gate) single-ray minima below this
N_SAMPLES = 1500
SEED = 0

# ---------------------------------------------------------------------------
# Printed-part set = the EXPORT list (CLAUDE.md "Print notes"), as STL files.
# track strips replace track_L/R (see module docstring); *_real.stl gear pair
# excluded (committed single-start alternates; worm_starts=3 builds placeholders).
# ---------------------------------------------------------------------------
PRINTED = [
    # chassis / base
    "chassis_lower_front.stl", "chassis_lower_rear.stl",
    "chassis_deck_front.stl", "chassis_deck_center.stl", "chassis_deck_rear.stl",
    "belly_plate.stl",
    "track_strip_L1.stl", "track_strip_L2.stl", "track_strip_L3.stl", "track_strip_L4.stl",
    "track_strip_R1.stl", "track_strip_R2.stl", "track_strip_R3.stl", "track_strip_R4.stl",
    "track_wheels_L.stl", "track_wheels_R.stl",
    "track_keeper_L.stl", "track_keeper_R.stl",
    "track_pod_rail_L.stl", "track_pod_rail_R.stl",
    # neck / pan
    "neck_clevis.stl", "tilt_carrier.stl",
    "pan_platform.stl", "pan_race.stl", "pan_clips.stl", "pan_cage.stl", "pan_gears.stl",
    "trim_neckfoot.stl", "worm_wheel.stl", "tilt_worm.stl",
    # head
    "head_bezel_L.stl", "head_bezel_R.stl",
    "head_back_frame_L.stl", "head_back_frame_R.stl",
    "head_back_panel_L.stl", "head_back_panel_R.stl",
    "head_door.stl", "screen_tray.stl", "cam_cover.stl", "sd_plug.stl",
    "antenna_L.stl", "antenna_R.stl", "ant_bracket.stl",
]

# ---------------------------------------------------------------------------
# WHITELIST: intentional thin features. name -> (p1 floor mm, documented reason).
# A whitelisted part still FAILS if its p1 drops below its own floor (a real
# regression under the known-thin feature must not hide behind the whitelist).
# ---------------------------------------------------------------------------
WHITELIST = {
    # Placeholder 3-start worm: helical thread CRESTS taper below 0.8 by nature
    # of the m1.25 profile; the printed part is the generated-teeth regen per
    # docs/WORM.md, this placeholder only holds the envelope. Measured p1 0.79.
    "tilt_worm.stl": (0.6, "placeholder worm thread crests (real teeth per docs/WORM.md)"),
    # Screen-pocket LOCATOR STEP: the pocket stops 0.11 over the glass by design
    # (2026-07-11 LCD-seated-watertight pass), and the window's bezel_overlap lip
    # corner slivers sample near-zero on the step faces at (x ~+-94, y 31.1).
    # These are designed micro-ledges, not walls. Measured p1 0.44 / 0.38.
    "head_bezel_L.stl": (0.3, "designed 0.11 screen-pocket locator step + window lip corners"),
    "head_bezel_R.stl": (0.3, "designed 0.11 screen-pocket locator step + window lip corners"),
    # Back-panel rim-tab seam: the panel's side tabs inter() into the corner mass
    # (2026-07-10 4-piece head_back split); samples on the tab seam plane at
    # (x ~+-97, y -66) graze coincident faces and read near-zero. The 4 mm slab
    # itself is fine (bulk thickness 4.0). Measured p1 0.33 / 0.71.
    "head_back_panel_L.stl": (0.25, "frame-tab seam coincident-face slivers at (+-97, -66)"),
    "head_back_panel_R.stl": (0.25, "frame-tab seam coincident-face slivers at (+-97, -66)"),
    # Track link KEELS + inner-face draft chamfers taper to their corner lines by
    # design (2026-07-12 print-in-place strips: 45 deg self-supporting buttresses).
    # Strips actually measure p1 ~1.9 -- the entry is here so a future keel
    # sharpening can not fail the gate without a documented decision.
    "track_strip_L1.stl": (0.8, "keel/chamfer corner taper (PIP strips 2026-07-12)"),
    "track_strip_L2.stl": (0.8, "keel/chamfer corner taper (PIP strips 2026-07-12)"),
    "track_strip_L3.stl": (0.8, "keel/chamfer corner taper (PIP strips 2026-07-12)"),
    "track_strip_L4.stl": (0.8, "keel/chamfer corner taper (PIP strips 2026-07-12)"),
    "track_strip_R1.stl": (0.8, "keel/chamfer corner taper (PIP strips 2026-07-12)"),
    "track_strip_R2.stl": (0.8, "keel/chamfer corner taper (PIP strips 2026-07-12)"),
    "track_strip_R3.stl": (0.8, "keel/chamfer corner taper (PIP strips 2026-07-12)"),
    "track_strip_R4.stl": (0.8, "keel/chamfer corner taper (PIP strips 2026-07-12)"),
}


def self_thickness(mesh, n=N_SAMPLES):
    """(p1, min, argmin location) of ray-based material thickness."""
    pts, _ = trimesh.sample.sample_surface(mesh, n, seed=SEED)
    th = trimesh.proximity.thickness(mesh, pts, method="ray")
    ok = np.isfinite(th) & (th > 1e-3)
    th, pts = th[ok], pts[ok]
    if th.size == 0:
        return None, None, None
    i = int(np.argmin(th))
    return float(np.percentile(th, 1)), float(th[i]), pts[i]


def main():
    fails, findings = [], []
    print("wallcheck: %d printed parts, min wall %.2f mm, %d samples/part (seed %d)"
          % (len(PRINTED), MIN_WALL, N_SAMPLES, SEED))
    for name in PRINTED:
        path = stlp(name)
        if not os.path.exists(path):
            fails.append((name, "STL missing -- run EXPORT=1 python3 src/build.py"))
            print("  X  %-26s STL MISSING" % name)
            continue
        m = trimesh.load(path)
        floor, reason = WHITELIST.get(name, (MIN_WALL, None))
        if not m.is_watertight:
            fails.append((name, "mesh NOT WATERTIGHT (thickness untrustworthy)"))
            print("  X  %-26s NOT WATERTIGHT (%d bodies, euler %d)"
                  % (name, m.body_count, m.euler_number))
            continue
        p1, tmin, loc = self_thickness(m)
        if p1 is None:
            fails.append((name, "no valid thickness rays"))
            print("  X  %-26s NO VALID RAYS" % name)
            continue
        tag = "ok "
        if p1 < floor:
            tag = "X  "
            fails.append((name, "p1 %.2f mm < %.2f%s"
                          % (p1, floor, " (whitelisted floor)" if reason else "")))
        elif reason and p1 < MIN_WALL:
            tag = "w  "     # whitelisted, below the global gate but above its floor
        line = "  %s%-26s p1 %5.2f  min %5.2f" % (tag, name, p1, tmin)
        if tmin < SPOT_LIMIT:
            line += "  spot at (%.1f, %.1f, %.1f)" % (loc[0], loc[1], loc[2])
            findings.append((name, tmin, loc))
        if reason:
            line += "   [WL: %s]" % reason
        print(line)

    if findings:
        print("\nspot minima < %.2f mm (informational, grazing rays included):" % SPOT_LIMIT)
        for name, tmin, loc in findings:
            print("  !  %-26s %.2f mm at (%.1f, %.1f, %.1f)"
                  % (name, tmin, loc[0], loc[1], loc[2]))
    if fails:
        print("\nFAIL: %d part(s) below the wall gate" % len(fails))
        for name, why in fails:
            print("  X  %s: %s" % (name, why))
        sys.exit(1)
    print("\nPASS: all printed parts >= %.2f mm p1 wall (or whitelisted floor)" % MIN_WALL)
    sys.exit(0)


if __name__ == "__main__":
    main()

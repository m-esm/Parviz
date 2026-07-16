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
    "chassis_lower_front.stl", "chassis_lower_rear.stl", "chassis_lower_tail.stl",
    "chassis_side_L_front.stl", "chassis_side_L_rear.stl",
    "chassis_side_R_front.stl", "chassis_side_R_rear.stl",
    "chassis_deck_front.stl", "chassis_deck_center.stl", "chassis_deck_rear.stl",
    "belly_plate.stl", "chassis_base.stl", "chassis_pedestal.stl",
    "track_strip_L1.stl", "track_strip_L2.stl", "track_strip_L3.stl", "track_strip_L4.stl",
    "track_strip_R1.stl", "track_strip_R2.stl", "track_strip_R3.stl", "track_strip_R4.stl",
    "track_wheels_L.stl", "track_wheels_R.stl",
    "track_keeper_L.stl", "track_keeper_R.stl",
    # neck / pan
    "neck_clevis.stl", "tilt_carrier.stl",
    "pan_platform.stl", "pan_race.stl", "pan_retainer.stl", "pan_cage.stl", "pan_gears.stl",
    "trim_neckfoot.stl", "worm_wheel.stl", "tilt_worm.stl",
    # head
    "head_bezel_L.stl", "head_bezel_R.stl",
    "head_back_frame_L.stl", "head_back_frame_R.stl",
    "head_back_panel_L.stl", "head_back_panel_R.stl",
    "head_door.stl", "screen_tray.stl", "cam_cover.stl", "sd_plug.stl",
    "antenna_L.stl", "antenna_R.stl", "ant_bracket.stl",
    "ant_motor_gear_L.stl", "ant_motor_gear_R.stl",
    "ant_idler_gear_L.stl", "ant_idler_gear_R.stl",
    "ant_idler_axle_L.stl", "ant_idler_axle_R.stl",
    "ant_output_L.stl", "ant_output_R.stl",
    # plastic hardware stand-ins (2026-07-15, src/standins.py): interim prints
    # for the buy-list metal -- gate them like any printed part
    "hw_m4_bolt.stl", "hw_m4_nut.stl", "hw_m8_bolt.stl", "hw_m8_nut.stl",
    "hw_m8_washer.stl", "hw_f688_bushing.stl", "hw_pan_ring.stl",
    "hw_tilt_axle.stl", "hw_seam_dowel.stl", "hw_foot_pin.stl",
]

# ---------------------------------------------------------------------------
# WHITELIST: intentional thin features. name -> (p1 floor mm, documented reason).
# A whitelisted part still FAILS if its p1 drops below its own floor (a real
# regression under the known-thin feature must not hide behind the whitelist).
# ---------------------------------------------------------------------------
WHITELIST = {
    # REAL ISO THREADS (2026-07-16 stand-in rework, src/threads.py). No true thread can
    # pass an 0.8 mm wall gate: the ISO 68-1 crest flat is p/8 BY DEFINITION -- 0.125 at
    # M4x1.0, 0.156 at M8x1.25 -- and the lead-in chamfers/countersinks slice those
    # crests to a feather where they run out, exactly like the incomplete thread on a
    # metal nut. The ray gate measures flank-to-flank across a V-tooth and reads that
    # taper as a wall. It is not one: every tooth is fully backed by the core (bolts) or
    # the nut wall (nuts) along its whole helix, the bulk sections are 2.1-2.4 mm, and
    # the crest never carries load (0.25 radial clearance to its mate). Same class as
    # the tilt_worm run-out feathers and the 14T tooth tips below. Verified by census:
    # ~100% of each part's thin population sits in the thread band. Floors are set under
    # the measured p1 (which jitters with where the chamfer truncates the helix), so a
    # REAL regression -- a thin nut wall or a hollowed shank -- still fails.
    "hw_m4_bolt.stl": (0.25, "M4x1.0 ISO crest flats (p/8 = 0.125 by form) + tip lead-in "
                             "feather; the shank under them is solid Ø3.9"),
    "hw_m4_nut.stl": (0.08, "M4x1.0 ISO crest flats + the run-out feather at the 45deg "
                            "countersink mouth; bulk flat-to-bore section is 2.14"),
    "hw_m8_bolt.stl": (0.25, "M8x1.25 ISO crest flats (p/8 = 0.156 by form) + tip lead-in "
                             "feather; the shank under them is solid Ø8.0"),
    "hw_m8_nut.stl": (0.08, "M8x1.25 ISO crest flats + the run-out feather at the Ø9.0 "
                            "countersink mouth; bulk flat-to-bore section is 2.375"),
    # 14T conjugate sprocket tooth tips (running-gear v2 2026-07-14): the larger
    # pitch radius makes the swept-envelope tooth tips taper thinner than the old
    # 12T's. Mesh probe-verified (tools/probe_track_pip.py: CR 1.48, skip barrier
    # 2.14, conjugate penetration -0.187 = clearance, 3D keeled sweep clean);
    # tips ride greased pins under weight preload, no wall-normal load.
    "track_wheels_L.stl": (0.6, "14T conjugate tooth-tip lands (probe-verified mesh)"),
    "track_wheels_R.stl": (0.6, "14T conjugate tooth-tip lands (probe-verified mesh)"),
    # Rear glacis / floor-top tangent: the 33 deg hull bevel (2026-07-10 toy-tank
    # glacis) exits through the floor top plane at y -110.8, leaving a designed
    # full-width knife wedge that tapers to zero (spot (22.7, -110.7, 12.0)). Same
    # family as the deck-tip acute edge the user had truncated -- surfaced only
    # 2026-07-14 when the tail entered this gate (it was missing from PRINTED).
    # Prints seam-up so the wedge lies flat on the floor slab; cosmetic.
    "chassis_lower_tail.stl": (0.2, "rear glacis/floor-top tangent knife wedge "
                                    "(designed 33deg hull bevel; tail first gated 2026-07-14)"),
    # FRONT twin of the tail's glacis wedge (y +110.8): always present, but it only
    # crossed the p1 percentile 2026-07-14 round 5 when the keep strap + pedestal +
    # ULN posts left the part (smaller sample population, same designed geometry).
    "chassis_lower_front.stl": (0.2, "front glacis/floor-top tangent knife wedge "
                                     "(designed 33deg hull bevel; surfaced when the "
                                     "belly strap left the part, round 5)"),
    # Equipment base: the boolean hull-relief (sub(base, hull shells)) thins the
    # plate edge to ~0.75 where the belly-opening lip pocket crosses it at
    # (44.4, -62.3, 12.3). Local skin over a clearance pocket, not a load wall;
    # base first gated 2026-07-14 (was missing from PRINTED).
    "chassis_base.stl": (0.6, "hull-relief clearance pocket skins at the belly-lip "
                              "edge (base first gated 2026-07-14)"),
    # REAL generated 3-start worm (docs/WORM.md; the old 0.60 floor was set against
    # the placeholder). Thin population censused 2026-07-13 (20k samples): ~2.4% read
    # < 0.6, median 0.04 mm from a trim face = the thread RUN-OUT WEDGES where the
    # helical rib meets the flat end cuts at the 25 deg flank angle (machined worms
    # carry the same feather unless a run-out relief is cut), plus grazing rays on the
    # 1.147-wide crest band. None sit in the mesh zone (the ends are dead thread past
    # the wheel-envelope overlap, zero load); prints VERTICAL, so the bottom wedge
    # lies on the bed and the slicer tip-rounds the top one -- cosmetic on a greased
    # drive gear. The 0.6 crest end chamfers (cooler pass) already broke the sharpest
    # corners. Measured p1 0.25-0.27.
    "tilt_worm.stl": (0.2, "3-start thread run-out feathers at the trim faces (unloaded "
                           "dead-thread ends, prints vertical) + crest grazing rays"),
    # REAL 12T helical wheel (same regen): thin samples sit at r ~7.5 from the axle
    # axis (the pitch circle) ON the x +-3.5 face planes (probed 2026-07-13: min spot
    # (3.5, -17.91, 160.48), r 7.48) = the tooth FACE-EDGE FEATHERS where the 22.8 deg
    # helix twist meets the flat face cut -- the wheel-side twin of the worm's run-out
    # wedges. Mesh probe-verified (coupled sweep 0.000 mm3), greased drive gear; the
    # wheel prints on its face so the feather edge lies in-plane. Measured p1 0.53-0.58.
    "worm_wheel.stl": (0.4, "helical tooth face-edge feathers at the x +-3.5 face cuts "
                            "(pitch-circle band, prints on its face)"),
    # Pan spur pair: every sub-0.8 sample sits at r 13.58..13.60 off the motor gear
    # axis (-19.2, 0) in the z 45..50 gear band = the 32T m0.8 ADDENDUM circle
    # (tip r = 12.8 + 0.8 = 13.6, probed 2026-07-13 at 6000 samples, p1 0.77).
    # Real m0.8 tooth tips taper below 0.8 by nature of the involute profile; the
    # mesh itself is probe-verified per docs/WORM.md (pan spur section, coupled
    # sweep 0.000 mm3) and runs greased. Not a wall: no load normal to the tip land.
    "pan_gears.stl": (0.75, "real m0.8 tooth tips, mesh probe-verified, greased drive gear"),
    # The 12T member of each m0.8 antenna compound idler has a theoretical involute
    # tip land just under two 0.4 mm lines.  The hub, bore wall and gear root all exceed
    # the global floor; only unloaded tooth tips enter this exception.  Exact coupled
    # sweeps live in tests/test_antenna_drive.py.
    "ant_idler_gear_L.stl": (0.70, "m0.8 involute tooth tips; coupled mesh sweep verified"),
    "ant_idler_gear_R.stl": (0.70, "m0.8 involute tooth tips; coupled mesh sweep verified"),
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
    # Frame rear rim: the y -66 panel/frame split plane slices the footprint's rear
    # corner ROUND, so the side wall feathers to zero at its tangency with the back
    # wall plane (probed 2026-07-13: every sub-0.8 sample sits at x +-87..91 /
    # y -66..-65.88, the rim wedge; thickness grows smoothly off the tangent line).
    # Designed split geometry -- the panel's corner mass backs the wedge in assembly.
    # Frames only became measurable 2026-07-13 (export watertight repair); p1 0.34.
    # Floor 0.25 -> 0.20 (2026-07-16): restoring the flange dowel bore (it had been
    # silently deleted -- an enclosed void read as a speck to the body sort) shifted
    # this part's p1 0.37 -> 0.248 WITHOUT adding a thin wall. Censused at the new
    # geometry: of the 24 sub-0.5 samples, 79% sit within 2 mm of the same y -66 seam
    # feather this row has always covered and 0% are within 8 mm of the dowel bore.
    # So the feature is unchanged and p1 (a percentile) just moved with the sample
    # population. min is ~0.00-0.01 either way and always was.
    "head_back_frame_L.stl": (0.20, "split-plane feather rim where the y -66 seam cuts the corner round"),
    "head_back_frame_R.stl": (0.20, "split-plane feather rim where the y -66 seam cuts the corner round"),
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

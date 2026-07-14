#!/usr/bin/env python3
"""Task #22: Bambu A1 test plate to validate the track-link design before committing to
the 72-link production run. One plate, one spool (PETG), settings baked in:

  * 5x track link (_track_link), printed GROUSER-UP / inner-face-down. Grouser-down is
    unprintable support-free: the web+bridge underside (z=-4.5 local) is a full-width 90deg
    overhang hovering 1.5 mm above the bed, held only by the 2 mm grouser strip. Flipped,
    the six knuckle crowns sit on the bed and the web underside becomes a ~4 mm self-
    bridging span between the two knuckle rows -- the 45deg inner-face draft chamfers in
    _track_link exist exactly to ramp that bridge. Pin bores are horizontal either way
    (identical layer orientation / strength: link tension is in-plane of the layers).
  * 1x sprocket (_sprocket(+1)), gear-face down / hub up per docs/PRINTABILITY.md plate D
    ("sprockets gear-face down": the one-sided hub self-supports; the D-socket and the
    Ø6 free bore become vertical holes; the M2 counterbore is a recess in the bed face).
  * pin gauge coupon 15x10x8: three HORIZONTAL through-bores Ø1.9/2.0/2.1 (same bore
    attitude as the links' printed pin bores, so the fit transfers), labeled 1/2/3 by
    notch grooves in the top face, to dial the Ø1.75 filament hinge-pin fit.
  (The pod-rail joint coupon was RETIRED 2026-07-14 round 3: pod_rail_L/R deleted,
  the wheel beam is integral to the chassis_side panels and the M3/dowel joint no
  longer exists.)

Writes per-part STLs (scratchpad or STL_DIR env) + exports/test_plate_links.3mf.
No edits to src/build.py -- geometry is imported. Regenerate after any track change.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
SKILL = os.path.expanduser("~/.claude/skills/bambu-3mf-export/scripts")
if not os.path.isdir(SKILL):
    sys.exit("bambu-3mf-export skill scripts not found at " + SKILL)
sys.path.insert(0, SKILL)

import numpy as np
import trimesh
import trimesh.transformations as tf

import build                                   # desk-pi geometry (import-safe: main guard)
from build import P, box, cyl, sub
from bambu3mf import write_bambu_3mf

BED = 256.0
STL_DIR = os.environ.get("STL_DIR", os.path.join(ROOT, "exports"))
OUT_3MF = os.path.join(ROOT, "exports", "test_plate_links.3mf")


# ---------------------------------------------------------------- parts (print pose)
def track_link_print():
    """Link flipped grouser-UP (rotate pi about X: outer face -z -> +z)."""
    lk = build._track_link()
    lk.apply_transform(tf.rotation_matrix(np.pi, [1, 0, 0]))
    return lk


def sprocket_print():
    """+X-pod sprocket, rotated +90deg about Y so +X (gear outer face) points -Z:
    gear face on the bed, hub + D-socket vertical, opening upward."""
    spr = build._sprocket(+1)
    spr.apply_transform(tf.rotation_matrix(np.pi / 2, [0, 1, 0]))
    return spr


def pin_gauge():
    """15x10x8 block, bores through Y (HORIZONTAL, like the link pin bores print).
    Ø1.9 / 2.0 / 2.1 at x = -5 / 0 / +5, notch-count labels 1 / 2 / 3 on top."""
    g = box(15, 10, 8)
    g.apply_translation((0, 0, 4))                       # bed at z=0
    for i, d in enumerate((1.9, 2.0, 2.1)):
        b = cyl(d / 2, 14, axis="y")
        b.apply_translation((-5 + 5 * i, 0, 4))
        g = sub(g, b)
        for n in range(i + 1):                           # grooves: 0.8 wide, 0.6 deep
            nt = box(0.8, 4.0, 1.2)
            nt.apply_translation((-5 + 5 * i + (n - i / 2) * 1.6, 0, 8))
            g = sub(g, nt)
    return g


# ---------------------------------------------------------------- checks
def overhang_report(name, m, bed_anchor_z=1.25):
    """Area of downward faces steeper than 45deg above the bed-anchored zone."""
    n = m.face_normals
    zc = m.triangles_center[:, 2]
    bad = (n[:, 2] < -np.sin(np.radians(45)) - 1e-6) & (zc > bed_anchor_z)
    area = float(m.area_faces[bad].sum())
    return area


def main():
    os.makedirs(STL_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUT_3MF), exist_ok=True)

    link = track_link_print()
    parts = [(f"track_link_{i+1}", link.copy()) for i in range(5)]
    parts += [("sprocket_test", sprocket_print()),
              ("pin_gauge_190_200_210", pin_gauge())]

    # bed-relative positions (origin = plate centre), brim 5 -> footprint + 10 per axis;
    # links go portrait (17 wide) so five fit one row with >= 8 mm brim-to-brim air.
    ROTZ = tf.rotation_matrix(np.pi / 2, [0, 0, 1])
    POS = {"track_link_1": (-72, -60), "track_link_2": (-36, -60), "track_link_3": (0, -60),
           "track_link_4": (36, -60), "track_link_5": (72, -60),
           "sprocket_test": (-70, 40),
           "pin_gauge_190_200_210": (44, 40)}

    print("part                     footprint (w x d mm)  height  watertight  overhang>45deg")
    plate_parts, ok = [], True
    for name, m in parts:
        if name.startswith("track_link"):
            m.apply_transform(ROTZ)                      # portrait on the plate
        wt = m.is_watertight
        e = m.bounds[1] - m.bounds[0]
        oh = overhang_report(name, m)
        ok &= wt
        print(f"  {name:22s}  {e[0]:6.1f} x {e[1]:5.1f}      {e[2]:5.1f}   {str(wt):5s}"
              f"       {oh:6.1f} mm2")
        m.export(os.path.join(STL_DIR, name + ".stl"))
        plate_parts.append(dict(name=name, mesh=m, pos=POS[name],
                                obj_settings={"enable_support": "0"}))
    if not ok:
        sys.exit("FAIL: non-watertight part")

    # brim-aware bed check (5 mm outer brim + require >= 8 mm air between footprints)
    BRIM, GAP = 5.0, 8.0
    boxes = []
    for prt in plate_parts:
        e = prt["mesh"].bounds[1] - prt["mesh"].bounds[0]
        fw, fd = e[0] + 2 * BRIM, e[1] + 2 * BRIM
        cx, cy = BED / 2 + prt["pos"][0], BED / 2 + prt["pos"][1]
        if cx - fw / 2 < 0 or cx + fw / 2 > BED or cy - fd / 2 < 0 or cy + fd / 2 > BED:
            sys.exit(f"FAIL: {prt['name']} (brim incl.) off the 256x256 plate")
        boxes.append((prt["name"], cx - fw / 2, cy - fd / 2, cx + fw / 2, cy + fd / 2))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            dx = max(a[1], b[1]) - min(a[3], b[3])       # gap if positive
            dy = max(a[2], b[2]) - min(a[4], b[4])
            if max(dx, dy) < GAP - 1e-6:
                sys.exit(f"FAIL: {a[0]} vs {b[0]} brim gap {max(dx, dy):.1f} < {GAP}")
    print("bed check: all parts on-plate, brim-to-brim air >= 8 mm")

    SETTINGS = {
        # process: 0.2 mm, grid 30 %, NO supports (orientations are support-free by design)
        "layer_height": "0.2", "wall_loops": "3",
        "top_shell_layers": "4", "bottom_shell_layers": "3",
        "sparse_infill_density": "30%", "sparse_infill_pattern": "grid",
        "enable_support": "0",
        "brim_type": "outer_only", "brim_width": "5",
        # Generic PETG @ A1 (template baseline is PLA; per the skill's PETG override set)
        "filament_settings_id": ["Generic PETG @BBL A1"],
        "filament_type": ["PETG"], "filament_vendor": ["Generic"],
        "nozzle_temperature": ["250"], "nozzle_temperature_initial_layer": ["250"],
        "nozzle_temperature_range_low": ["230"], "nozzle_temperature_range_high": ["260"],
        "textured_plate_temp": ["80"], "textured_plate_temp_initial_layer": ["80"],
        "hot_plate_temp": ["80"], "hot_plate_temp_initial_layer": ["80"],
        "close_fan_the_first_x_layers": ["3"],
        "fan_min_speed": ["30"], "fan_max_speed": ["60"],
        "filament_max_volumetric_speed": ["10"],
        "curr_bed_type": "Textured PEI Plate",
    }
    write_bambu_3mf(OUT_3MF, plate_parts, SETTINGS, plate_name="Track link test")
    print(f"wrote {OUT_3MF}  ({len(plate_parts)} parts, PETG 0.2 mm, grid 30%, no support)")


if __name__ == "__main__":
    main()

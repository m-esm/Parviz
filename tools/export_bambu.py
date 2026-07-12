#!/usr/bin/env python3
"""Production Bambu Lab A1 export for desk-pi: every PRINTED part, oriented for print,
packed onto category-named PLATES inside ONE .3mf project, settings BAKED IN (opens as a
real Bambu project, not "load geometry data only").

Run `EXPORT=1 python3 src/build.py` first so stl/ is current, then `python3 tools/export_bambu.py`.
Output: exports/bambu.3mf (THE canonical name, always reused/overwritten -- user
2026-07-12: one file, same name every export; gitignored, regenerable) with these plates:

  Chassis            lower front/rear + deck front/center/rear + belly plate (2026-07-10
                     print-speed splits; every piece <= 180x180)
  Head               bezel L/R + back frames L/R + flat back panels L/R + door +
                     screen tray + cam cover + sd plug
  Antennas           2 masts (racks up) + the drive bracket
  Neck and pan       neck clevis, tilt carrier, pan platform/race/cage/clips
  Worm drive         worm wheel + worm (real generated teeth)
  Track gear         4 sprockets (2 optional-motor spares), 4 end idlers, 10 road
                     wheels, 2 pod rails, 2 keeper bars
  Track links        8 PRINT-IN-PLACE strips (4/side: 16+16+16+15 links, integral
                     Ø2.0 pins, keeled, support OFF) + 2 master links

A category that overflows the 256x256 bed spills to "Cat 1 of N", "Cat 2 of N".
ONE file, many plates: swap the spool / pick per-plate settings in Studio per plate.

Global profile is Generic PLA @ A1, 0.20 mm. (A single .3mf shares one process/filament
profile; the design still WANTS PETG for the worm drive + tracks + load-bearing mechanism,
print those plates in PETG and nudge their temps/bed in Studio.) Per-object overrides set
support + walls + infill.

BOUGHT parts excluded on purpose: 28BYJ/TT motors, ULN2003, 695-2RS/F688ZZ bearings, pan-race
BBs, F688ZZ idler bodies (proxy geometry riding a bought bearing), M2/M3 hardware, PD/buck power set.
"""
import os
import sys

import numpy as np
import trimesh
import trimesh.transformations as tf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
SKILL = os.path.expanduser("~/.claude/skills/bambu-3mf-export/scripts")
if not os.path.isdir(SKILL):
    sys.exit("bambu-3mf-export skill scripts not found at " + SKILL)
sys.path.insert(0, SKILL)

import tracks                                      # noqa: E402  (split modules,
from params import P                               # noqa: E402   2026-07-10 refactor)
from bambu3mf import write_bambu_3mf               # noqa: E402

BED = 256.0
OUT = os.path.join(ROOT, "exports", "bambu.3mf")


def R(axis, deg):
    return tf.rotation_matrix(np.radians(deg), axis)


X, Y, Z = [1, 0, 0], [0, 1, 0], [0, 0, 1]

# per-object overrides
TREE = {"enable_support": "1", "support_type": "tree(auto)", "support_threshold_angle": "30"}
NOSUP = {"enable_support": "0"}
STRUCT = {**TREE, "wall_loops": "4", "sparse_infill_density": "20%"}   # big shells / load parts

# print orientation per STL-loaded part (rotations applied to the as-built mesh) + its overrides
# Goal: best print face on the bed, shortest sensible height, cavities/detail up.
PARTS = {  # name: (subsystem, [rotations], obj_settings)
    "chassis_lower_front": ("base", [],         STRUCT),   # open-top tub halves, seam up
    "chassis_lower_rear":  ("base", [],         STRUCT),
    "chassis_deck_front":  ("base", [(X, 180)], STRUCT),   # deck pieces, top face down
    "chassis_deck_center": ("base", [(X, 180)], STRUCT),
    "chassis_deck_rear":   ("base", [(X, 180)], STRUCT),
    "belly_plate":     ("base", [],          TREE),     # flat plate (H 9)
    "head_back_frame_L": ("head", [(X, 90)], STRUCT),   # wall ring, front face -> bed:
    "head_back_frame_R": ("head", [(X, 90)], STRUCT),   #  NO back-wall ceiling anymore
    "head_back_panel_L": ("head", [(X, -90)], TREE),    # flat 4mm wall slab, outer
    "head_back_panel_R": ("head", [(X, -90)], TREE),    #  face (rebate) up
    "head_bezel_L":    ("head", [(X, -90)],  STRUCT),   # glass face -> bed, aperture up
    "head_bezel_R":    ("head", [(X, -90)],  STRUCT),
    "antenna_L":       ("head", [(X, -90)],  TREE),     # mast flat, rack teeth UP
    "antenna_R":       ("head", [(X, -90)],  TREE),
    "ant_bracket":     ("head", [(X, 90)],   TREE),     # wall-spine face -> bed
    "head_door":       ("head", [(X, 90)],   TREE),     # flat back on bed, panel up (H 10)
    "screen_tray":     ("head", [(X, -90)],  STRUCT),   # mount plate -> bed, pillars up (H 88)
    "cam_cover":       ("head", [(X, 90)],   TREE),     # flat (H 5.5)
    "sd_plug":         ("head", [(X, 90)],   NOSUP),    # lay flat (H 6)
    "neck_clevis":     ("neck", [(X, 90)],   STRUCT),   # "on its back" (H 58)
    "tilt_carrier":    ("neck", [(X, 90)],   TREE),     # ear plate flat (H 12)
    "pan_platform":    ("neck", [],          TREE),     # disc, D-hub down (H 14)
    "pan_race":        ("neck", [],          TREE),     # ring (H 5)
    "pan_cage":        ("neck", [],          TREE),     # thin ball cage (H 1.8)
    "pan_clips":       ("neck", [],          TREE),     # 3 flat clips (H 7)
    "worm_wheel_real": ("neck", [(Y, 90)],   TREE),     # gear face -> bed (H 7)
    "tilt_worm_real":  ("neck", [(X, 90)],   TREE),     # stand on shaft end (H 14)
    "track_pod_rail_L": ("base", [(Y, 90)],  TREE),     # outer face -> bed (H 8)
    "track_pod_rail_R": ("base", [(Y, 90)],  TREE),
    "track_keeper_L":  ("base", [(X, 90)],   NOSUP),    # rolled onto the wide face
    "track_keeper_R":  ("base", [(X, 90)],   NOSUP),    # (bed 14->29 mm2, overhang halved)
}

# category -> ordered part names (or generated-unit tokens); each becomes 1+ named plates
CATEGORIES = [
    ("Chassis",      ["chassis_lower_front", "chassis_lower_rear", "chassis_deck_front",
                      "chassis_deck_center", "chassis_deck_rear", "belly_plate"]),
    ("Head",         ["head_back_frame_L", "head_back_frame_R", "head_back_panel_L",
                      "head_back_panel_R", "head_bezel_L", "head_bezel_R",
                      "head_door", "screen_tray", "cam_cover", "sd_plug"]),
    ("Antennas",     ["antenna_L", "antenna_R", "ant_bracket"]),
    ("Neck and pan", ["neck_clevis", "tilt_carrier", "pan_platform", "pan_race", "pan_cage", "pan_clips"]),
    ("Worm drive",   ["worm_wheel_real", "tilt_worm_real"]),
    ("Track gear",   ["@drivegear"]),
    ("Track links",  ["@links"]),
]

# single shared profile: Generic PLA @ A1, 0.20 mm standard
PROFILE = {
    "layer_height": "0.2", "wall_loops": "3", "top_shell_layers": "4", "bottom_shell_layers": "3",
    "sparse_infill_density": "15%", "sparse_infill_pattern": "grid",
    "enable_support": "1", "support_type": "tree(auto)", "support_threshold_angle": "30",
    "brim_type": "auto_brim", "brim_width": "5",
    "curr_bed_type": "Textured PEI Plate",
}


def clean(m):
    """Drop zero/near-zero-volume boolean slivers (they trip is_watertight, not printable)."""
    comps = m.split(only_watertight=False)
    real = [c for c in comps if c.volume > 0.5]
    if len(real) == len(comps):
        return m
    return trimesh.util.concatenate(real) if len(real) > 1 else real[0]


def load_part(name):
    sub, rots, obj = PARTS[name]
    m = clean(trimesh.load(os.path.join(ROOT, "stl", sub, name + ".stl")))
    for ax, dg in rots:
        m.apply_transform(R(ax, dg))
    m.apply_translation((0, 0, -m.bounds[0][2]))
    return (name, m, obj)


def drivegear_units():
    """Rails + keepers + EVERY running-gear body split straight out of the exported
    track_wheels STLs (2026-07-11: recipe duplication drifted -- roadwheel_count died,
    end idlers were missing, dual sprockets landed). Per side: 2 sprockets (one for
    the OPTIONAL 2nd motor -- print it anyway, it's cheap) + 2 end idlers + 5 road
    wheels = 9 bodies. Wheels stand on a face (axis was X in-assembly -> R(Y,90))."""
    out = [load_part(n) for n in ("track_pod_rail_L", "track_pod_rail_R",
                                  "track_keeper_L", "track_keeper_R")]
    for side in ("L", "R"):
        m = trimesh.load(os.path.join(ROOT, "stl", "base", f"track_wheels_{side}.stl"))
        bodies = m.split(only_watertight=False)
        ns, ni, nw = 0, 0, 0
        for b_ in sorted(bodies, key=lambda p: p.centroid[1]):
            cy = b_.centroid[1]
            if abs(b_.bounds[0][2]) < 12 and b_.bounds[0][2] < 10:  # dips to the pin line
                pass
            if min(abs(cy - P["spr_y"]), abs(cy - P["spr_y2"])) < 5:
                ns += 1; nm, ob = f"sprocket_{side}{ns}", NOSUP
            elif abs(abs(cy) - P["track_wheelbase"] / 2) < 5:
                ni += 1; nm, ob = f"end_idler_{side}{ni}", NOSUP
            else:
                nw += 1; nm, ob = f"road_wheel_{side}{nw}", NOSUP
            b_ = b_.copy()
            b_.apply_transform(R(Y, 90))
            # ORIENTATION-NORMALIZE (2026-07-12 print pass): the L/R STLs are
            # mirrored, so one uniform rotation lands L sprockets DISC-UP -- a
            # ~1050 mm2 tree-forest ceiling over the toothed disc at z 24 (the R
            # side lands disc-down with ~28 mm2 residual). Data-driven fix: if the
            # high half carries big >45deg down-facing area, flip 180. With the
            # disc down, the only ceilings left on sprockets/idlers are 1-2 mm
            # annular bore steps (counterbore, F688 flange recess) that BRIDGE
            # cleanly -- so support is OFF above: tree pillars inside press bores
            # scar the very faces the bearings/D-shaft seat on.
            b_.apply_translation((0, 0, -b_.bounds[0][2]))
            fn_, fc_, fa_ = b_.face_normals, b_.triangles_center, b_.area_faces
            high_ov = fa_[(fn_[:, 2] < -0.707) & (fc_[:, 2] > 10.0)].sum()
            if high_ov > 200.0:
                b_.apply_transform(R(X, 180))
            out.append((nm, b_, ob))
        assert (ns, ni, nw) == (2, 2, 5), f"unexpected running gear split {side}: {(ns, ni, nw)}"
    for _, m, _ in out:
        m.apply_translation((0, 0, -m.bounds[0][2]))
    return out


def strip_units():
    """PRINT-IN-PLACE STRIPS (2026-07-12, replaced link_units after the chain print
    failure chain: grouser-up NOSUP = floating regions; standing NOSUP sliced clean
    but toppled ON the printer; grouser-down + tree printed but scarred and 126
    loose links still had to be pinned by hand). Per side 4 straight strips of
    (16,16,16,15) links at pitch, ONE mesh each (CONCATENATED, never boolean-
    unioned: the 0.35 PIP hinge gaps must survive), lying grouser-down. The 45deg
    knuckle KEELS make that pose fully self-supporting (bed = grousers + keel
    feet, web bridges anchored), so support is OFF -- that is the whole point --
    with the profile's 5 mm brim. Strips ride stl/base/track_strip_*.stl written
    by EXPORT=1 build (the ghost pattern), so `make export` stays one pipeline.
    MASTER links stay separate, grouser-up NOSUP as today (C-jaw prints clean;
    they close the loop at assembly)."""
    out = []
    for side in ("L", "R"):
        for si in (1, 2, 3, 4):
            nm = f"track_strip_{side}{si}"
            m = trimesh.load(os.path.join(ROOT, "stl", "base", nm + ".stl"))
            bodies = m.split(only_watertight=False)
            expect = 15 if si == 4 else 16           # position 0 is the master
            if len(bodies) != expect:
                sys.exit(f"FAIL: {nm} has {len(bodies)} bodies, expected {expect} "
                         "(PIP gap fused, or a link split?)")
            e = m.bounds[1] - m.bounds[0]
            brim = float(PROFILE.get("brim_width", 5))
            if max(e[0], e[1]) + 2 * brim > 180.0:
                sys.exit(f"FAIL: {nm} {e[0]:.0f}x{e[1]:.0f} + {brim:.0f} brim "
                         "exceeds the 180 bed")
            out.append((nm, m, NOSUP))
    master = tracks._track_master_link()[0]; master.apply_transform(R(X, 180))
    out += [("track_master_link", master.copy(), NOSUP) for _ in range(2)]
    for _, m, _ in out:
        m.apply_translation((0, 0, -m.bounds[0][2]))
    return out


def shelf_pack(items, brim_default, gap=6.0):
    """items: (name, mesh, obj). Returns list of plates (each a list of part dicts), brim-aware."""
    sized, seen = [], {}
    for name, m, obj in items:
        e = m.bounds[1] - m.bounds[0]
        if e[1] > e[0]:
            m.apply_transform(R(Z, 90)); e = m.bounds[1] - m.bounds[0]
        seen[name] = seen.get(name, 0) + 1
        nm = name if seen[name] == 1 else f"{name}_{seen[name]}"
        b = 0.0 if obj.get("brim_type") in ("no_brim", "none") else float(obj.get("brim_width", brim_default))
        sized.append([nm, m, e[0] + 2 * b, e[1] + 2 * b, obj])
    sized.sort(key=lambda s: -s[3])
    plates, x, y, rowh = [[]], gap, gap, 0.0
    for nm, m, fw, fd, obj in sized:
        if fw + 2 * gap > BED or fd + 2 * gap > BED:
            sys.exit(f"FAIL: {nm} footprint {fw:.0f}x{fd:.0f} (brim incl.) exceeds the {BED:.0f} bed")
        if x + fw + gap > BED:
            x, y, rowh = gap, y + rowh + gap, 0.0
        if y + fd + gap > BED:
            plates.append([]); x, y, rowh = gap, gap, 0.0
        c = (x + fw / 2 - BED / 2, y + fd / 2 - BED / 2)
        if abs(c[0]) + fw / 2 > BED / 2 + 0.1 or abs(c[1]) + fd / 2 > BED / 2 + 0.1:
            sys.exit(f"FAIL: {nm} off plate")
        plates[-1].append(dict(name=nm, mesh=m, fw=fw, fd=fd, pos=c, obj_settings=obj))
        x += fw + gap; rowh = max(rowh, fd)
    return plates


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    brim = float(PROFILE.get("brim_width", 0))
    tokens = {"@drivegear": drivegear_units, "@links": strip_units}

    plates, manifest = [], []
    for cat, members in CATEGORIES:
        items = []
        for m in members:
            items += tokens[m]() if m in tokens else [load_part(m)]
        bad = [n for n, mesh, _ in items if not mesh.is_watertight]
        if bad:
            sys.exit(f"FAIL: non-watertight after clean in '{cat}': {bad}")
        packed = shelf_pack(items, brim)
        for i, parts in enumerate(packed, 1):
            name = cat if len(packed) == 1 else f"{cat} {i} of {len(packed)}"
            plates.append({"name": name, "parts": parts})
            counts = {}
            for p in parts:
                k = p["name"].rsplit("_", 1)[0] if p["name"][-1].isdigit() else p["name"]
                counts[k] = counts.get(k, 0) + 1
            manifest.append((name, len(parts),
                             ", ".join(f"{k}x{v}" if v > 1 else k for k, v in counts.items())))

    write_bambu_3mf(OUT, plates, dict(PROFILE))

    print("=" * 78 + f"\n{os.path.relpath(OUT, ROOT)}  --  {len(plates)} plates, PLA 0.20 mm\n" + "=" * 78)
    print(f"  {'plate':18s} {'parts':>5}  contents")
    total = 0
    for name, n, contents in manifest:
        total += n
        print(f"  {name:18s} {n:5d}  {contents}")
    print(f"  {'':18s} {total:5d}  total printed bodies")
    print("\n  EXCLUDED (bought): 28BYJ x4 / TT x2 / ULN2003 x4, 695-2RS + F688ZZ bearings,")
    print("  pan-race 6mm BBs, antenna m0.8 spur set + Ø4 shafts (buy, or print later with")
    print("  generated teeth like docs/WORM.md; the placeholder discs are NOT printable teeth),")
    print("  F688ZZ idler bodies (proxy, ride a bought bearing), M2/M3 hardware, PD+bucks.")
    print("  FAST PAN/TILT (2026-07-12): pan_gears + the pan_platform's integral 16T pinion")
    print("  are PLACEHOLDER teeth (real generated spur pass pending) -- hold the platform")
    print("  print if the pan drive must work; and the Worm-drive plate is the OLD")
    print("  SINGLE-START pair (12:1, self-locking) -- the design is now worm_starts=3")
    print("  (4:1): regenerate per docs/WORM.md before printing, or print the old pair")
    print("  for a slow self-locking fallback.")
    print("  Design wants PETG for Worm drive + Track plates + load-bearing parts: print those in")
    print("  PETG and set 250C / 80C textured-PEI in Studio. Large-shell orientations set for")
    print("  support-free faces but not visually verified per-part; Auto-orient shells in Studio.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Production Bambu Lab A1 export for desk-pi: every PRINTED part, oriented for print,
packed onto category-named PLATES inside ONE .3mf project, settings BAKED IN (opens as a
real Bambu project, not "load geometry data only").

Run `EXPORT=1 python3 src/build.py` first so stl/ is current, then `python3 tools/export_bambu.py`.
Output: exports/parviz_plates.3mf (gitignored, regenerable) with these plates:

  Chassis            chassis, belly_plate
  Head               head shells + screen tray + cam cover + sd plug
  Neck and pan       neck clevis, tilt carrier, pan platform/race/cage/clips
  Worm drive         worm wheel + worm (real generated teeth)
  Track gear         2 sprockets, 4 road wheels, 2 pod rails, 2 keeper bars
  Track links        72 articulated links (70 plain + 2 master)

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

import build                                       # noqa: E402  (import-safe: main guard)
from bambu3mf import write_bambu_3mf               # noqa: E402

BED = 256.0
OUT = os.path.join(ROOT, "exports", "parviz_plates.3mf")


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
    "chassis_lower":   ("base", [],          STRUCT),   # open-top lower tub, seam up
    "chassis_deck":    ("base", [(X, 180)],  STRUCT),   # shallow removable deck, top face down
    "belly_plate":     ("base", [],          TREE),     # flat plate (H 9)
    "head_back":       ("head", [(X, 90)],   STRUCT),   # open front face -> bed (H 72)
    "head_bezel":      ("head", [(X, -90)],  STRUCT),   # glass face -> bed, aperture up (H 29)
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
    "track_keeper_L":  ("base", [],          NOSUP),    # tiny bars flat (H 5.5)
    "track_keeper_R":  ("base", [],          NOSUP),
}

# category -> ordered part names (or generated-unit tokens); each becomes 1+ named plates
CATEGORIES = [
    ("Chassis",      ["chassis_lower", "chassis_deck", "belly_plate"]),
    ("Head",         ["head_back", "head_bezel", "head_door", "screen_tray", "cam_cover", "sd_plug"]),
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
    """2 sprockets (gear-face down) + 4 road wheels (bore vertical, stand) + rails + keepers."""
    out = [load_part(n) for n in ("track_pod_rail_L", "track_pod_rail_R",
                                  "track_keeper_L", "track_keeper_R")]
    for sx in (-1, 1):
        spr = build._sprocket(sx); spr.apply_transform(R(Y, 90))
        out.append((f"sprocket_{'L' if sx < 0 else 'R'}", spr, TREE))
    rd = build.P["roadwheel_d"]
    for i in range(build.P["roadwheel_count"] * 2):
        rw = build.sub(build.cyl(rd / 2, 30.0, axis="x"), build.cyl(2.1, 34.0, axis="x"))
        rw.apply_transform(R(Y, 90))
        out.append((f"road_wheel_{i+1}", rw, NOSUP))
    for _, m, _ in out:
        m.apply_translation((0, 0, -m.bounds[0][2]))
    return out


def link_units():
    """35 plain links/side + 1 master/side, grouser-up (self-supporting -> support off)."""
    plain = build._track_link(); plain.apply_transform(R(X, 180))
    master = build._track_master_link()[0]; master.apply_transform(R(X, 180))
    n = build.P["track_links"]
    out = [("track_link", plain.copy(), NOSUP) for _ in range((n - 1) * 2)]
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
    tokens = {"@drivegear": drivegear_units, "@links": link_units}

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
    print("\n  EXCLUDED (bought): 28BYJ x2 / TT x2 / ULN2003, 695-2RS + F688ZZ bearings, pan-race")
    print("  6mm BBs, F688ZZ idler bodies (proxy, ride a bought bearing), M2/M3 hardware, PD+bucks.")
    print("  Design wants PETG for Worm drive + Track plates + load-bearing parts: print those in")
    print("  PETG and set 250C / 80C textured-PEI in Studio. Large-shell orientations set for")
    print("  support-free faces but not visually verified per-part; Auto-orient shells in Studio.")


if __name__ == "__main__":
    main()

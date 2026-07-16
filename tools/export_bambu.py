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
                     wheels, 2 keeper bars (wheel beams are integral to side panels)
  Track links        8 PRINT-IN-PLACE strips (4/side: 16+16+16+15 links, integral
                     Ø2.0 pins, keeled, support OFF) + 2 master links
  Track coupon       5-link PIP test strip + 1 master + 2 keeper bars (~48 min sliced):
                     print + measure THIS before the 6.8 h strip plates

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
import re
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
# threshold stays 30 (support pass 2026-07-14): in Bambu semantics the value is
# the overhang slope BELOW which support generates -- RAISING it adds support
# (measured: +15-30 min/plate at 45). Overhang reduction is done in GEOMETRY
# (teardrops, 45deg scarfs, bridge-anchored cage strips), not the threshold.
TREE = {"enable_support": "1", "support_type": "tree(auto)", "support_threshold_angle": "30"}
NOSUP = {"enable_support": "0"}
STRUCT = {**TREE, "wall_loops": "6", "sparse_infill_density": "8%"}   # load parts: 6 walls +
                                                        # token infill for top-skin bridging

# print orientation per STL-loaded part (rotations applied to the as-built mesh) + its overrides
# Goal: best print face on the bed, shortest sensible height, cavities/detail up.
PARTS = {  # name: (subsystem, [rotations], obj_settings)
    "chassis_lower_front": ("base", [],         STRUCT),   # open-top tub halves, seam up
    "chassis_lower_rear":  ("base", [],         STRUCT),
    "chassis_lower_tail":  ("base", [],         STRUCT),   # rear cap (cheeks + rear wall)
    "chassis_base":        ("base", [],         TREE),     # drop-in equipment base, flat
    "chassis_pedestal":    ("base", [],         TREE),     # pan pedestal, flange down
    "chassis_side_L_front": ("base", [], STRUCT),  # bolt-in wall panels w/ integral
    "chassis_side_L_rear":  ("base", [], STRUCT),  #  wheel beam: print UPRIGHT as
    "chassis_side_R_front": ("base", [], STRUCT),  #  built (z12 edge + rib feet +
    "chassis_side_R_rear":  ("base", [], STRUCT),  #  foot pads coplanar on the bed;
                                                   #  beam chamfer self-supports,
                                                   #  tree catches the boss bottoms)
    "track_shoe_L_rear": ("base", [], NOSUP),
    "track_shoe_L_front": ("base", [], NOSUP),
    "track_shoe_R_rear": ("base", [], NOSUP),
    "track_shoe_R_front": ("base", [], NOSUP),
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
    "ant_motor_gear_L": ("head", [(Y, 90)],  NOSUP),
    "ant_motor_gear_R": ("head", [(Y, 90)],  NOSUP),
    "ant_idler_gear_L": ("head", [(Y, 90)],  NOSUP),
    "ant_idler_gear_R": ("head", [(Y, 90)],  NOSUP),
    "ant_idler_axle_L": ("head", [(Y, 90)],  NOSUP),
    "ant_idler_axle_R": ("head", [(Y, 90)],  NOSUP),
    "ant_output_L":    ("head", [(Y, 90)],   NOSUP),
    "ant_output_R":    ("head", [(Y, 90)],   NOSUP),
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
    "track_keeper_L":  ("base", [(X, 90)],   NOSUP),    # rolled onto the wide face
    "track_keeper_R":  ("base", [(X, 90)],   NOSUP),    # (bed 14->29 mm2, overhang halved)
}

# category -> ordered part names (or generated-unit tokens); each becomes 1+ named plates
CATEGORIES = [
    ("Chassis",      ["chassis_lower_front", "chassis_lower_rear", "chassis_lower_tail",
                      "chassis_side_L_front", "chassis_side_L_rear",
                      "chassis_side_R_front", "chassis_side_R_rear",
                      "track_shoe_L_rear", "track_shoe_L_front",
                      "track_shoe_R_rear", "track_shoe_R_front",
                      "chassis_deck_front", "chassis_deck_center", "chassis_deck_rear",
                      "belly_plate", "chassis_base", "chassis_pedestal"]),
    ("Head",         ["head_back_frame_L", "head_back_frame_R", "head_back_panel_L",
                      "head_back_panel_R", "head_bezel_L", "head_bezel_R",
                      "head_door", "screen_tray", "cam_cover", "sd_plug"]),
    ("Antennas",     ["antenna_L", "antenna_R", "ant_bracket",
                       "ant_motor_gear_L", "ant_motor_gear_R",
                       "ant_idler_gear_L", "ant_idler_gear_R",
                       "ant_idler_axle_L", "ant_idler_axle_R",
                       "ant_output_L", "ant_output_R"]),
    ("Neck and pan", ["neck_clevis", "tilt_carrier", "pan_platform", "pan_race", "pan_cage", "pan_clips"]),
    ("Worm drive",   ["worm_wheel_real", "tilt_worm_real"]),
    ("Track gear",   ["@drivegear"]),
    ("Track links",  ["@links"]),
    ("Track coupon", ["@coupon"]),
    ("Hardware stand-ins", ["@standins"]),   # plastic interim metal (src/standins.py)
]

# single shared profile: Generic PLA @ A1, 0.20 mm standard
# 0% INFILL + MORE WALLS (2026-07-14, user: "0% infill and more walls to save
# time and cost"): shells carry the strength; grid infill mostly heated air in
# these wall-dominated parts. Exceptions stay per-object (STRUCT keeps a token
# 8% for the load-bearing shells' long bridging top skins).
PROFILE = {
    "layer_height": "0.2", "wall_loops": "5", "top_shell_layers": "5", "bottom_shell_layers": "4",
    "sparse_infill_density": "0%", "sparse_infill_pattern": "grid",
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
    """Keepers + EVERY running-gear body split straight out of the exported
    track_wheels STLs (2026-07-11: recipe duplication drifted -- roadwheel_count died,
    end idlers were missing, dual sprockets landed). Per side: 2 sprockets (one for
    the OPTIONAL 2nd motor -- print it anyway, it's cheap) + 2 end idlers + 5 road
    wheels = 9 bodies. Wheels stand on a face (axis was X in-assembly -> R(Y,90)).
    (pod rails deleted 2026-07-14 round 3: the wheel beam is integral to the
    chassis_side panels on the Chassis plates.)"""
    out = [load_part(n) for n in ("track_keeper_L", "track_keeper_R")]
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


def coupon_units():
    """TEST COUPON plate (2026-07-13): a 5-link print-in-place strip + ONE loose
    master link + its two keeper bars -- the complete joint set (integral-pin PIP
    hinge, keels, open boundary bores, C-jaw + keeper slide) in ~48 min of plastic,
    to be printed and measured BEFORE committing to the 6.8 h strip plates. Strip
    rides stl/base/track_coupon.stl (EXPORT=1 ghost, concatenated like the big
    strips, grouser-down SUPPORT OFF); master + keepers generate live exactly like
    the strip-plate master spares / keeper STLs (grouser-up NOSUP, keepers rolled
    onto the wide face)."""
    m = trimesh.load(os.path.join(ROOT, "stl", "base", "track_coupon.stl"))
    n = len(m.split(only_watertight=False))
    if n != 5:
        sys.exit(f"FAIL: track_coupon has {n} bodies, expected 5 "
                 "(PIP gap fused, or a link split?)")
    out = [("track_coupon_strip", m, NOSUP)]
    body, keepers = tracks._track_master_link()
    body.apply_transform(R(X, 180))                    # grouser-up like the spares
    out.append(("track_master_link", body, NOSUP))
    for k in keepers:
        k.apply_transform(R(X, 90))                    # rolled onto the wide face
        out.append(("track_keeper_bar", k, NOSUP))
    for _, mm, _ in out:
        mm.apply_translation((0, 0, -mm.bounds[0][2]))
    return out


def standin_units():
    """PLASTIC HARDWARE STAND-INS (2026-07-15, user: dry-assemble in plastic until
    the buy-list metal arrives -- src/standins.py has the full part rationale).
    One canonical STL per unique part in stl/hardware/, replicated here to the
    assembly counts. All self-supporting (bolts head-down, rings flat, axle lying
    round-down): NOSUP. The Ø5x209 tilt axle exceeds a 180 bed straight, so it
    goes on the plate DIAGONAL (same portability rule as the strip plates)."""
    sys.path.insert(0, os.path.join(ROOT, "src"))
    from standins import STANDINS
    out = []
    for name, (_build, count) in STANDINS.items():
        m0 = clean(trimesh.load(os.path.join(ROOT, "stl", "hardware", name + ".stl")))
        if name == "hw_tilt_axle":
            m0.apply_transform(R(Z, 45))
        m0.apply_translation((0, 0, -m0.bounds[0][2]))
        for _ in range(count):
            out.append((name, m0.copy(), NOSUP))
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
    tokens = {"@drivegear": drivegear_units, "@links": strip_units,
              "@coupon": coupon_units, "@standins": standin_units}

    # BAMBU PER-CATEGORY ARRANGE (2026-07-15, user: "arrange can be asked from
    # bambu"): each category is shelf-packed naively, round-tripped through
    # BambuStudio's own ARRANGE engine in a temp project, and the packed layout is
    # read back (bambu_autopack.packed_plates) -- so packing density is Bambu's
    # while plates stay CATEGORY-PURE (a global arrange pass mixed coupon strips
    # with head shells and made selective printing impossible). --orient stays OFF:
    # every part's pose here is deliberate (the PARTS table carries the reasons)
    # and a probe run showed the orient engine flipping 16 of them against those
    # reasons (deck_center cosmetic face into supports, master links grouser-down
    # = the 2026-07-12 floating-C-jaw failure, the O5x209 axle stood on end).
    # arrange + allow-rotations only yaws parts; deliberate="*" hard-fails if
    # anything gets TILTED. Falls back to the naive layout without BambuStudio.app.
    import tempfile
    plates, cli_plates, naive_plates = [], 0, 0
    use_cli_pack = os.environ.get("BAMBU_AUTOPACK", "0") == "1"
    packed_plates = None
    if use_cli_pack:
        from bambu_autopack import packed_plates
    for cat, members in CATEGORIES:
        items = []
        for m in members:
            items += tokens[m]() if m in tokens else [load_part(m)]
        bad = [n for n, mesh, _ in items if not mesh.is_watertight]
        if bad:
            sys.exit(f"FAIL: non-watertight after clean in '{cat}': {bad}")
        packed = shelf_pack(items, brim)
        settings = {p["name"]: p["obj_settings"] for pl in packed for p in pl}
        with tempfile.TemporaryDirectory() as td:
            tmp = os.path.join(td, "cat.3mf")
            write_bambu_3mf(tmp, [{"name": cat, "parts": pl} for pl in packed],
                            dict(PROFILE))
            res = (packed_plates(tmp, deliberate=("*",), brim=brim)
                   if packed_plates is not None else None)
        # BEST-OF-BOTH (measured 2026-07-15): Bambu's engine wins on many-small-part
        # categories (stand-ins 2 -> 1 plate, links 3 -> 2) but loses on few-big-part
        # ones (its bed margins/spacing put Chassis 6 -> 7, Head 5 -> 7). Keep
        # whichever layout needs fewer plates; tie goes to the naive nest (known
        # layout, zero read-back risk).
        if res is not None and len(res["plates"]) < len(packed):
            cli_plates += len(res["plates"])
            cat_plates = [[dict(p, obj_settings=settings[p["name"]]) for p in pl]
                          for pl in res["plates"]]
        else:
            naive_plates += 0 if res is not None else len(packed)
            cat_plates = packed
        for i, parts in enumerate(cat_plates, 1):
            name = cat if len(cat_plates) == 1 else f"{cat} {i} of {len(cat_plates)}"
            plates.append({"name": name, "parts": parts})
    if not use_cli_pack:
        print("NOTE: deterministic brim-aware shelf packing used. Set BAMBU_AUTOPACK=1 "
              "to opt into Bambu Studio arrangement.")
    elif naive_plates:
        print("NOTE: BambuStudio.app not found -- naive shelf-pack layout on "
              "%d plate(s)" % naive_plates)

    write_bambu_3mf(OUT, plates, dict(PROFILE))

    manifest, total = [], 0
    for pl in plates:
        counts = {}
        for p in pl["parts"]:
            k = re.sub(r"_\d+$", "", p["name"])
            counts[k] = counts.get(k, 0) + 1
        manifest.append((pl["name"], len(pl["parts"]),
                         ", ".join(f"{k}x{v}" if v > 1 else k for k, v in counts.items())))

    print("=" * 78 + f"\n{os.path.relpath(OUT, ROOT)}  --  {len(manifest)} plates, PLA 0.20 mm\n" + "=" * 78)
    print(f"  {'plate':28s} {'parts':>5}  contents")
    for name, n, contents in manifest:
        total += n
        print(f"  {name:28s} {n:5d}  {contents}")
    print(f"  {'':28s} {total:5d}  total printed bodies")
    print("\n  EXCLUDED (bought): 28BYJ x4 / TT x2 / ULN2003 x4, 695-2RS bearings (owned),")
    print("  M2/M3 hardware (owned), PD+bucks. The 'Hardware stand-ins' plate carries")
    print("  PLASTIC INTERIM copies of the buy-list metal (M4x40/M8x70 bolt-axles, nuts,")
    print("  washers, F688ZZ->bushings, pan BBs->slip ring, Ø5 tilt axle, dowels) --")
    print("  dry-assembly only, swap for metal on arrival (src/standins.py).")
    print("  FAST PAN/TILT (real teeth 2026-07-13): pan_gears + the platform's integral")
    print("  16T pinion carry REAL generated involute teeth (tools/gears/gen_pan_spurs.py)")
    print("  and the Worm-drive plate is the 3-START pair (4:1, NOT self-locking -- see")
    print("  PARAMS worm_starts). build.py falls back to placeholders on any PARAMS vs")
    print("  meta-sidecar mismatch; if this export printed after a params change, re-run")
    print("  the generators per docs/WORM.md first.")
    print("  ANTENNAS: the m0.8 involute gears, compound idlers, axles, output shafts,")
    print("  pinions, and true racks are all printable and included on Antennas plates.")
    print("  Design wants PETG for Worm drive + Track plates + load-bearing parts: print those in")
    print("  PETG and set 250C / 80C textured-PEI in Studio. Large-shell orientations set for")
    print("  support-free faces but not visually verified per-part; Auto-orient shells in Studio.")


if __name__ == "__main__":
    main()

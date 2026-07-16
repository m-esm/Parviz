#!/usr/bin/env python3
"""Assembly interference gate for desk-pi.

Static mode (default):
    python3 src/assembly_check.py [web/assembly.glb]
  Pairwise boolean interference over every node pair in the GLB (manifold
  engine, AABB prefilter). Fails on any un-whitelisted overlap > THRESHOLD.

Sweep mode:
    python3 src/assembly_check.py --sweep
  Rebuilds the scene across a pan x tilt pose grid (PAN/TILT/OUT env into
  src/build.py, OUT=_check.glb, removed afterwards) and probes:
    - HEAD group vs FIXED group at every pose
    - HEAD group vs PAN group at pan=0 poses
    - PAN group vs FIXED group at tilt=0 poses

Exit 0 = clean, exit 1 = interference (or a boolean/build error).

Python 3.9. Requires trimesh + manifold3d.
"""
import argparse
import itertools
import os
import subprocess
import sys
import warnings

# numpy inside trimesh emits divide-by-zero / invalid-value RuntimeWarnings
# during boolean prep on some meshes; they are noise here.
warnings.filterwarnings("ignore", category=RuntimeWarning)

import trimesh  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_GLB = os.path.join(REPO, "web", "assembly.glb")
CHECK_GLB = os.path.join(REPO, "web", "_check.glb")

THRESHOLD = 0.01  # mm^3 -- anything below is numerical noise / kissing faces

# The screen+Pi reference mesh is NOT watertight; manifold booleans on it
# raise. It is a bought part posed against measured geometry, so skip it.
# The downloaded real bought meshes (refparts: motors, HC-SR04, Uno, CM3) join
# it when REALPARTS is on -- non-watertight/decimated, same skip. With
# PLACEHOLDER_PARTS=1 the set is empty and the analytic placeholders are checked.
import refparts
EXCLUDE = {"screen_ref"} | refparts.excluded_nodes()

# --- pose-group membership (EDIT ME when parts are added) -------------------
# Any node that rides the TILT joint (moves with the head) must be listed in
# HEAD_NODES; anything that rides only the PAN joint goes in PAN_NODES.
# Every other node (except EXCLUDE) is treated as FIXED by default, so a new
# head-riding part that is NOT added here will be swept as if it were fixed
# and will false-positive against the real fixed parts. Add new head/pan
# parts to these lists.
HEAD_NODES = {
    "head_bezel", "head_back", "trim_rail_L", "trim_rail_R", "led_strip",
    "antenna_stub", "trim_hatch_frame", "camera_pod", "arm_L", "arm_R",
    "worm_wheel", "tilt_axle", "cam_cover", "camera_ref", "head_door",
    "sd_plug", "screen_tray", "pi5_cooler",   # COOLER=1 keep-out (default off)
    "antenna_L", "antenna_R", "ant_bracket",
    "ant_motor_gear_L", "ant_motor_gear_R",
    "ant_idler_gear_L", "ant_idler_gear_R",
    "ant_idler_axle_L", "ant_idler_axle_R", "ant_output_L", "ant_output_R",
    "ant_oring_L", "ant_oring_R",
}
PAN_NODES = {"pan_platform", "neck_clevis", "tilt_worm", "motor_tilt", "tilt_carrier",
             "trim_neckfoot"}

# Intended (designed-contact) couplings, order-independent.
# print-speed sub-splits (2026-07-10): pieces of one object alias to the parent for
# whitelist lookups, and pieces of the SAME parent may touch (their designed seam).
SPLIT_ALIAS = {
    "head_back_frame_L": "head_back", "head_back_frame_R": "head_back",
    "head_back_panel_L": "head_back", "head_back_panel_R": "head_back",
    "head_bezel_L": "head_bezel", "head_bezel_R": "head_bezel",
    "chassis_lower_front": "chassis_lower", "chassis_lower_rear": "chassis_lower",
    "chassis_lower_tail": "chassis_lower",
    # bolt-in side panels (2026-07-14 round 2): carved from the lower tub's wall
    # bands, so they alias to it like the tail cap -- inherits the drive/rail/BME/
    # deck/base pairs and allows the designed floor-rest + deck-edge contact.
    "chassis_side_L_front": "chassis_lower", "chassis_side_L_rear": "chassis_lower",
    "chassis_side_R_front": "chassis_lower", "chassis_side_R_rear": "chassis_lower",
    "chassis_deck_front": "chassis_deck", "chassis_deck_center": "chassis_deck",
    "chassis_deck_rear": "chassis_deck",
}

WHITELIST = {
    frozenset(("worm_wheel", "tilt_worm")),      # gear mesh
    frozenset(("worm_wheel", "neck_clevis")),    # spacer tube in bearing seats
    frozenset(("pan_platform", "pan_balls")),    # captured-BB groove (upper race)
    frozenset(("pan_race", "pan_balls")),        # captured-BB groove (lower race)
    frozenset(("pan_gears", "motor_pan")),       # 32T gear on the D-shaft (fast-pan 2:1)
    frozenset(("pan_gears", "pan_platform")),    # 32T <-> integral 16T pinion mesh
                                                 # (placeholder teeth, real pass later)
    frozenset(("ant_output_L", "antenna_L")),    # involute rack/pinion working contact
    frozenset(("ant_output_R", "antenna_R")),
    frozenset(("ant_oring_L", "antenna_L")),     # designed gland and mast contact
    frozenset(("ant_oring_R", "antenna_R")),
    frozenset(("ant_oring_L", "head_back")),     # bought ring captured by split shell gland
    frozenset(("ant_oring_R", "head_back")),
    frozenset(("ant_motor_gear_L", "motor_ant_L")), # G1 keyed to each 28BYJ D-shaft
    frozenset(("ant_motor_gear_R", "motor_ant_R")),
    frozenset(("axle_hw_L", "chassis_lower")),   # M4 nuts in the panel beam slots +
    frozenset(("axle_hw_R", "chassis_lower")),   # M8 washers on the panel END TOWERS
                                                 # (pylons deleted 2026-07-14 round 4;
                                                 # panels alias to chassis_lower)
    # equipment base (2026-07-14): drops into the rear bay, bolts to the hull floor,
    # carries the Arduino/IMU/SW-420 seats (SW-420 rides its fence nubs).
    frozenset(("chassis_base", "chassis_lower")),   # base rests on the hull floor + bolts
    frozenset(("chassis_pedestal", "belly_plate")),  # pedestal seats + pins + bolts on the
                                                     # plate plug (round 5)
    frozenset(("chassis_pedestal", "motor_pan")),    # can/ears in the pedestal
                                                     # (placeholder-mode runs)
    frozenset(("chassis_base", "sensor_vib")),      # SW-420 in its seat fence
    frozenset(("chassis_base", "sensor_imu")),      # IMU on its posts
    frozenset(("chassis_base", "board_arduino")),   # Uno on its posts (refpart, excl.)
}

# Sweep pose grid: (pan_deg, tilt_deg)
SWEEP_POSES = [
    (0, 0), (0, 30), (0, -30),
    (20, -30),
    (45, 30), (45, -30),
    (-45, -30), (-20, -30),
    (90, 0), (-90, 0),
    (90, 30), (90, -30), (-90, 30), (-90, -30),
]


def load_meshes(path):
    """GLB -> {node_name: world-space Trimesh}, EXCLUDE dropped."""
    scene = trimesh.load(path, force="scene")
    grouped = {}
    for node in scene.graph.nodes_geometry:
        T, geom_name = scene.graph[node]
        if geom_name in EXCLUDE:
            continue
        g = scene.geometry[geom_name].copy()
        g.apply_transform(T)
        # granular children ("parent.child", 2026-07-11) re-group under their parent
        grouped.setdefault(geom_name.split(".")[0], []).append(g)
    return {k: (v[0] if len(v) == 1 else trimesh.util.concatenate(v))
            for k, v in grouped.items()}


def bbox_overlap(a, b):
    amin, amax = a.bounds
    bmin, bmax = b.bounds
    return bool((amax >= bmin).all() and (bmax >= amin).all())


def overlap_volume(a, b):
    """Boolean-intersection volume in mm^3 (0.0 if AABBs are disjoint).
    DIRECT manifold3d (2026-07-14): trimesh's boolean wrapper injected phantom
    slivers on complex meshes (see geo.py) -- the gate must not report them."""
    if not bbox_overlap(a, b):
        return 0.0
    import manifold3d as m3
    import numpy as np

    def _man(t):
        return m3.Manifold(m3.Mesh(
            vert_properties=np.asarray(t.vertices, dtype=np.float64),
            tri_verts=np.asarray(t.faces, dtype=np.uint32)))
    return abs(float((_man(a) ^ _man(b)).volume()))


def check_pairs(meshes, pairs, context, violations):
    """Run the boolean gate over (name_a, name_b) pairs; append violations."""
    for na, nb in pairs:
        na_ = SPLIT_ALIAS.get(na, na); nb_ = SPLIT_ALIAS.get(nb, nb)
        if na_ == nb_ or frozenset((na_, nb_)) in WHITELIST:
            continue
        try:
            vol = overlap_volume(meshes[na], meshes[nb])
        except Exception as e:  # a boolean that throws is a defect, not a pass
            violations.append((context, na, nb, None, "boolean failed: %s" % e))
            continue
        if vol > THRESHOLD:
            violations.append((context, na, nb, vol, None))


def static_check(glb_path):
    meshes = load_meshes(glb_path)
    names = sorted(meshes)
    print("assembly_check: %s -- %d nodes, %d pairs (excl. %s)"
          % (glb_path, len(names),
             len(names) * (len(names) - 1) // 2, ", ".join(sorted(EXCLUDE))))
    violations = []
    check_pairs(meshes, itertools.combinations(names, 2), "static", violations)
    return violations


def build_pose(pan, tilt):
    """Invoke src/build.py at a pose; returns the path to the temp GLB."""
    env = dict(os.environ)
    env["PAN"] = str(pan)
    env["TILT"] = str(tilt)
    env["OUT"] = os.path.basename(CHECK_GLB)
    r = subprocess.run(
        [sys.executable, os.path.join(REPO, "src", "build.py")],
        cwd=REPO, env=env, capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError("build.py failed at pan=%s tilt=%s:\n%s"
                           % (pan, tilt, r.stderr[-2000:]))
    return CHECK_GLB


def sweep_check():
    violations = []
    # Run each pose in a fresh process. manifold3d retains native allocations beyond
    # Python's mesh lifetime; an in-process grid was killed after 1-2 poses and could
    # never produce a verdict even with explicit gc.collect(). Process isolation makes
    # peak memory constant and turns a killed worker into a visible failed pose.
    for pan, tilt in SWEEP_POSES:
        print("sweep: pan=%+d tilt=%+d ... " % (pan, tilt), end="", flush=True)
        r = subprocess.run([sys.executable, __file__, "--pose", str(pan), str(tilt)],
                           cwd=REPO, capture_output=True, text=True)
        if r.returncode == 0:
            print("OK")
        else:
            msg = (r.stdout + "\n" + r.stderr).strip()[-4000:]
            print("FAILED")
            violations.append(("pan=%+d tilt=%+d" % (pan, tilt),
                               "pose-worker", "mechanism", 0.0, msg))
    return violations


def pose_check(pan, tilt):
    try:
        meshes = load_meshes(build_pose(pan, tilt))
        names = set(meshes)
        head = sorted(names & HEAD_NODES)
        pang = sorted(names & PAN_NODES)
        fixed = sorted(names - HEAD_NODES - PAN_NODES)
        ctx = "pan=%+d tilt=%+d" % (pan, tilt)
        violations = []
        check_pairs(meshes, itertools.product(head, fixed),
                    ctx + " head-vs-fixed", violations)
        if pan == 0:
            check_pairs(meshes, itertools.product(head, pang),
                        ctx + " head-vs-pan", violations)
        if tilt == 0:
            check_pairs(meshes, itertools.product(pang, fixed),
                        ctx + " pan-vs-fixed", violations)
        return violations
    finally:
        if os.path.exists(CHECK_GLB):
            os.remove(CHECK_GLB)


def main():
    ap = argparse.ArgumentParser(description="desk-pi assembly interference gate")
    ap.add_argument("glb", nargs="?", default=DEFAULT_GLB,
                    help="GLB scene to check (default web/assembly.glb)")
    ap.add_argument("--sweep", action="store_true",
                    help="rebuild + probe across the pan x tilt pose grid")
    ap.add_argument("--pose", nargs=2, type=int, metavar=("PAN", "TILT"),
                    help=argparse.SUPPRESS)
    args = ap.parse_args()

    if args.pose:
        violations = pose_check(*args.pose)
    else:
        violations = sweep_check() if args.sweep else static_check(args.glb)

    if violations:
        print("\nFAIL: %d un-whitelisted interference(s) > %g mm^3"
              % (len(violations), THRESHOLD))
        for ctx, na, nb, vol, err in violations:
            if err:
                print("  [%s] %s x %s: %s" % (ctx, na, nb, err))
            else:
                print("  [%s] %s x %s: %.3f mm^3" % (ctx, na, nb, vol))
        sys.exit(1)
    print("\nPASS: no un-whitelisted overlaps > %g mm^3" % THRESHOLD)
    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Pi 5 Active Cooler fit probe (2026-07-13).

Rebuilds the assembly at NEUTRAL pose (COOLER off -- the probe constructs the
keep-out envelope itself from PARAMS so it can measure PENETRATION, not just
gate-fail), then reports:

  1. STATIC: signed clearance of every part within 6 mm of the envelope
     (surface-sampled; + = press INTO the envelope).
  2. TILT SWEEP: the envelope rides the head, so pan-frame drivetrain parts
     (tilt_worm / motor_tilt / tilt_carrier / neck_clevis / pan_platform /
     trim_neckfoot) move relative to it across the +-33.8 deg stall range.
     Worst signed distance per part per pose.

screen_ref is skipped everywhere (not watertight; and the cooler CONTAINS its
own Pi components by construction -- that overlap is the point of a keep-out).

Verdict as of 2026-07-13 evening (see the COOLER block in src/build.py): PASS.
Static min 0.78 (neck_clevis); sweep worst -0.60 (neck_clevis) / -0.61
(tilt_worm) at the -33.8 stall, after the worm-tail redesign (worm_len 13 +
0.6 crest end chamfers, tail stub deleted, crest-riding cradle + stall-swept
front trim in build_neck_clevis). The morning fail was +2.71 (tail stub) /
+1.76 (cradle pad) at the same pose.

Python 3.9; trimesh + manifold3d. Run: python3 tools/probe_cooler.py
"""
import os
import subprocess
import sys
import warnings

warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

import numpy as np             # noqa: E402
import trimesh                 # noqa: E402
from trimesh.transformations import rotation_matrix as R   # noqa: E402
from params import P, DEG      # noqa: E402
from geo import box            # noqa: E402

GLB = os.path.join(REPO, "web", "_cooler_probe.glb")
PAN_DRIVE = ["neck_clevis", "tilt_worm", "motor_tilt", "tilt_carrier",
             "pan_platform", "trim_neckfoot"]
STALL = 33.8                   # tilt homing hard-stop angle


def build_neutral():
    env = dict(os.environ)
    env.update(PAN="0", TILT="0", ANT="0", OUT=os.path.basename(GLB))
    env.pop("COOLER", None)
    r = subprocess.run([sys.executable, os.path.join(REPO, "src", "build.py")],
                       cwd=REPO, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("build failed:\n" + r.stderr[-2000:])


def load():
    scene = trimesh.load(GLB, force="scene")
    grouped = {}
    for node in scene.graph.nodes_geometry:
        T, gname = scene.graph[node]
        if gname == "screen_ref":
            continue
        g = scene.geometry[gname].copy()
        g.apply_transform(T)
        grouped.setdefault(gname.split(".")[0], []).append(g)
    return {k: (v[0] if len(v) == 1 else trimesh.util.concatenate(v))
            for k, v in grouped.items()}


def envelope(tilt_deg=0.0):
    w, d, h = P["pi5_cooler_wdh"]
    bcx, bcz = P["pi5_cooler_board_c"]
    X0, Z0 = P["pi5_board_org"]
    c = box(w, d, h)
    c.apply_translation((X0 + bcx, P["pi5_comp_face_y"] - d / 2, Z0 + bcz))
    if tilt_deg:
        c.apply_transform(R(tilt_deg * DEG, (1, 0, 0),
                            (0, P["tilt_axis_y"], P["tilt_axis_z"])))
    return c


def worst(cool, mesh, n=5000):
    lo = np.maximum(cool.bounds[0], mesh.bounds[0])
    hi = np.minimum(cool.bounds[1], mesh.bounds[1])
    if np.any(lo - hi > 6.0):
        return None
    pts, _ = trimesh.sample.sample_surface(mesh, n)
    d = trimesh.proximity.signed_distance(cool, pts)   # >0 = inside the envelope
    k = int(np.argmax(d))
    return float(d[k]), [round(float(x), 1) for x in pts[k]]


def main():
    print("building neutral scene ...")
    build_neutral()
    M = load()
    try:
        cool = envelope()
        print("\nenvelope (world):", np.round(cool.bounds, 2).tolist())
        print("\n=== STATIC (neutral) -- parts within 6 mm ===")
        fail = False
        for n in sorted(M):
            r = worst(cool, M[n])
            if r and r[0] > -6.0:
                tag = "PRESS" if r[0] > 0 else "clear"
                print("  %-22s %s %+7.2f mm  at %s" % (n, tag, r[0], r[1]))
                fail |= r[0] > 0
        print("\n=== TILT SWEEP (+-%.1f, pan-frame drivetrain vs head-riding "
              "envelope) ===" % STALL)
        peak = {}
        for t in np.linspace(-STALL, STALL, 15):
            c = envelope(t)
            for n in PAN_DRIVE:
                r = worst(c, M[n])
                if r is None:
                    continue
                if n not in peak or r[0] > peak[n][0]:
                    peak[n] = (r[0], t, r[1])
        for n, (d, t, at) in sorted(peak.items(), key=lambda kv: -kv[1][0]):
            tag = "PRESS" if d > 0 else "clear"
            print("  %-22s %s %+7.2f mm  at tilt %+6.1f  %s" % (n, tag, d, t, at))
            fail |= d > 0
        print("\n%s" % ("FAIL: envelope penetrated -- see the COOLER verdict in "
                        "src/build.py" if fail else "PASS: envelope clear"))
        return 1 if fail else 0
    finally:
        if os.path.exists(GLB):
            os.remove(GLB)


if __name__ == "__main__":
    sys.exit(main())

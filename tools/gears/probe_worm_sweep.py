#!/usr/bin/env python3
"""Assembly-pose probes for the generated worm pair (run after gen_worm_drive.py).

1. ASSEMBLY-POSE phase scan: in build.py the worm center sits at wheel-local
   (0, dy=-6, -CD) (worm yc = tilt_axis_y - 6; the wheel midplane crosses the
   worm at worm-local y +6). Scan the wheel phase over one tooth pitch (30 deg)
   for the zero-interference window -> the cosmetic clocking constant baked in
   build.py (the old single-start value was 24.5).
2. COUPLED ROTATION SWEEP: drive the worm through a full revolution while the
   wheel follows at the kinematic ratio (STARTS teeth per worm rev); max boolean
   intersection over the sweep must stay ~0 for a kinematically clean pair.

Run from the repo root:
  PYTHONPATH=tools/gears tools/gears/.venv/bin/python tools/gears/probe_worm_sweep.py
"""
import numpy as np
import trimesh

import gen_worm_drive as g

DY = -6.0                    # worm center y offset in wheel-local coords (build.py)
ROT = lambda deg, ax: trimesh.transformations.rotation_matrix(np.radians(deg), ax)


def ivol(a, b):
    ix = trimesh.boolean.intersection([a, b], engine="manifold")
    return 0.0 if ix.is_empty else abs(ix.volume)


def posed_worm(worm, psi_deg=0.0):
    w = worm.copy()
    w.apply_transform(ROT(psi_deg, (0, 1, 0)))
    w.apply_translation((0, DY, -g.CD))
    return w


def main():
    wheel = trimesh.load(g.OUT_WHEEL)
    worm = trimesh.load(g.OUT_WORM)
    wp = posed_worm(worm)

    # 1. assembly-pose phase scan (0.25 deg steps over one tooth pitch)
    zeros, best = [], (np.inf, 0.0)
    for phi in np.linspace(0, 30, 121):
        w = wheel.copy()
        w.apply_transform(ROT(phi, (1, 0, 0)))
        v = ivol(w, wp)
        if v < best[0]:
            best = (v, phi)
        if v == 0.0:
            zeros.append(phi)
    if zeros:
        # the window may wrap the 0/30 seam; unwrap before averaging
        z = np.array(zeros)
        if z.max() - z.min() > 15:
            z = np.where(z < 15, z + 30, z)
        center = float(np.mean(z)) % 30.0
    else:
        center = best[1]
    print(f"assembly-pose scan (worm at (0,{DY},-{g.CD})): min {best[0]:.4f} mm3, "
          f"zero window {len(zeros)}/121, center {center:.2f} deg  "
          f"<- build.py clocking constant")

    # 2. coupled sweep: worm psi 0..360, wheel center + s*psi*STARTS/12 (try both signs)
    ratio = g.STARTS / g.Z_WHEEL
    for sgn in (+1, -1):
        worst = 0.0
        for psi in np.linspace(0, 360, 49):
            w = wheel.copy()
            w.apply_transform(ROT(center + sgn * psi * ratio, (1, 0, 0)))
            worst = max(worst, ivol(w, posed_worm(worm, psi)))
        print(f"coupled sweep sign {sgn:+d} (49 steps over one worm rev = "
              f"{g.STARTS} wheel teeth): max intersection {worst:.4f} mm3")


if __name__ == "__main__":
    main()

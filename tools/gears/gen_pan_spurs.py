#!/usr/bin/env python3
"""Real involute spur teeth for the fast-pan 2:1 gear-up (PARAMS pan_gear_*).

Replaces the readable gear_disc placeholders on both members of the pan drive:

  stl/neck/pan_gear32_real.stl   32T m0.8 spur, axis Z, width 5.0, centered at origin
                                 (the pan_gears part on the 28BYJ double-D shaft;
                                 build.py cuts the D-bore -- the blank is SOLID)
  stl/neck/pan_pinion_real.stl   16T m0.8 spur, axis Z, width 5.5, centered at origin
                                 (integral to the pan_platform underside, src/pan.py;
                                 solid -- it fuses into the hub shank)
  stl/neck/pan_gears_real_meta.json  generation record; src/gears.py pan_real_ok()
                                 compares it to PARAMS and falls back to placeholders
                                 on ANY mismatch (same honesty gate as the worm pair)

Run from the repo root with the tools/gears venv:
  tools/gears/.venv/bin/python tools/gears/gen_pan_spurs.py

Design notes (mm / degrees):
  - m 0.8, PA 20 deg, 32T + 16T -> CD = 0.8*(32+16)/2 = 19.2 (PARAMS-derived, zero
    profile shift). 16T is BELOW the 17.1T rack-undercut limit but meshing a 32T
    GEAR (not a rack) the interference limit is ~14.2T, so no undercut relief is
    needed: the lowest contact point on the pinion flank sits at r 6.018, 0.004
    above the base circle 6.014.
  - Full-depth teeth: addendum 1.0m, dedendum 1.25m -> 32T tip r 13.6 (cluster
    reach 19.2 + 13.6 = 32.8 <= 33.0 race-ID budget), 16T tip r 7.2 (< the deck's
    r14.5 gear pocket), root radial clearance 19.2 - 13.6 - 5.4 = 0.2 = 0.25m.
  - Backlash 0.20 circular total, thinned 0.10 per member at the pitch line --
    the middle of the FDM 0.1-0.3 band; each flank sits ~0.09 normal off its mate.
  - Teeth are generated tooth-centered-on-+X for BOTH blanks. 16 and 32 are even,
    so at the assembly pose (gear at azimuth 180 from the pan axis) both members
    present a tooth on the center line; build.py bakes the meshing phase into the
    32T (measured below and stored in the meta as gear32_mesh_deg).
"""

import json
import os
import sys

import numpy as np
import trimesh
import manifold3d as m3

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "src"))
from params import P as _P                    # noqa: E402  (params imports numpy only)

# ---------------------------------------------------------------------------
# PARAMETERS (from PARAMS -- the single source of truth)
# ---------------------------------------------------------------------------
MODULE = float(_P["pan_gear_m"])              # 0.8, matches the antenna module
Z_GEAR = int(_P["pan_gear_motor_t"])          # 32T on the motor D-shaft (drives)
Z_PIN = int(_P["pan_gear_pinion_t"])          # 16T integral to the platform (driven)
PA_DEG = 20.0                                 # standard PA; 16T ok vs a 32T (see header)
BACKLASH = 0.20                               # circular total, split 0.10 per member
ADD = 1.0 * MODULE                            # full-depth addendum 0.8
DED = 1.25 * MODULE                           # dedendum 1.0
W_GEAR = _P["pan_gear_z"][1] - _P["pan_gear_z"][0]        # 5.0 tooth band
W_PIN = W_GEAR + 0.5                          # 5.5: pinion roots fuse 0.5 into the shank

CD = MODULE * (Z_GEAR + Z_PIN) / 2.0          # 19.2, matches build.py cd_pan
PA = np.radians(PA_DEG)

OUT_GEAR = "stl/neck/pan_gear32_real.stl"
OUT_PIN = "stl/neck/pan_pinion_real.stl"
OUT_META = "stl/neck/pan_gears_real_meta.json"


def inv(phi):
    return np.tan(phi) - phi


def spur_outline(z):
    """CCW outer outline of a z-tooth involute spur in the transverse plane,
    tooth centered on +X. Radial flank below the base circle, root arcs between
    teeth (same construction as gen_worm_drive.wheel_outline)."""
    r_p = MODULE * z / 2.0
    r_b = r_p * np.cos(PA)
    r_tip = r_p + ADD
    r_root = r_p - DED
    s_p = np.pi * MODULE / 2.0 - BACKLASH / 2.0   # tooth thickness at pitch, thinned

    def half_angle(r):
        phi = np.arccos(np.clip(r_b / r, -1, 1))
        return s_p / (2 * r_p) + inv(PA) - inv(phi)

    psi_base = s_p / (2 * r_p) + inv(PA)
    pitch_ang = 2 * np.pi / z
    r_lo = max(r_root, r_b) if r_root < r_b else r_root

    pts = []
    n_flank, n_tip, n_root = 14, 5, 7
    for k in range(z):
        c = k * pitch_ang
        pts.append((r_root, c - psi_base))
        for r in np.linspace(r_lo if r_root < r_b else r_root, r_tip, n_flank):
            pts.append((r, c - half_angle(max(r, r_b))))
        psi_t = half_angle(r_tip)
        for a in np.linspace(-psi_t, psi_t, n_tip)[1:-1]:
            pts.append((r_tip, c + a))
        for r in np.linspace(r_tip, r_lo if r_root < r_b else r_root, n_flank):
            pts.append((r, c + half_angle(max(r, r_b))))
        pts.append((r_root, c + psi_base))
        for a in np.linspace(psi_base, pitch_ang - psi_base, n_root)[1:-1]:
            pts.append((r_root, c + a))
    rr = np.array([p[0] for p in pts])
    aa = np.array([p[1] for p in pts])
    return np.column_stack([rr * np.cos(aa), rr * np.sin(aa)])


def build_spur(z, width):
    cs = m3.CrossSection([spur_outline(z).tolist()], m3.FillRule.EvenOdd)
    man = m3.Manifold.extrude(cs, width)
    mm = man.to_mesh()
    mesh = trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3],
                           np.asarray(mm.tri_verts), process=False)
    mesh.apply_translation((0, 0, -width / 2))    # center on origin, axis Z
    return mesh


ROT_Z = lambda deg: trimesh.transformations.rotation_matrix(np.radians(deg), (0, 0, 1))


def ivol(a, b):
    ix = trimesh.boolean.intersection([a, b], engine="manifold")
    return 0.0 if ix.is_empty else abs(ix.volume)


def scan_phase(gear, pin, cd, n=121):
    """Pinion at origin, gear at (-cd, 0) (the assembly layout: pan_shaft_azim 180).
    Scan the gear rotation over one tooth pitch for the zero-interference window;
    return (window center, min volume, [zero phases])."""
    pitch = 360.0 / Z_GEAR
    pin_p = pin
    zeros, best = [], (np.inf, 0.0)
    for psi in np.linspace(0, pitch, n):
        g = gear.copy()
        g.apply_transform(ROT_Z(psi))
        g.apply_translation((-cd, 0, 0))
        v = ivol(g, pin_p)
        if v < best[0]:
            best = (v, psi)
        if v == 0.0:
            zeros.append(psi)
    center = float(np.mean(zeros)) if zeros else best[1]
    return center, best[0], zeros


def main():
    print(f"m {MODULE}  {Z_GEAR}T + {Z_PIN}T  PA {PA_DEG} deg  CD {CD}  "
          f"backlash {BACKLASH} circular (split)")
    print(f"gear32: pitch r {MODULE*Z_GEAR/2}  tip r {MODULE*Z_GEAR/2+ADD}  "
          f"root r {MODULE*Z_GEAR/2-DED}  width {W_GEAR}")
    print(f"pin16 : pitch r {MODULE*Z_PIN/2}  tip r {MODULE*Z_PIN/2+ADD}  "
          f"root r {MODULE*Z_PIN/2-DED}  width {W_PIN}")
    print(f"cluster reach {CD + MODULE*Z_GEAR/2 + ADD:.1f} (budget 33.0, race ID 34); "
          f"pinion tip {MODULE*Z_PIN/2+ADD:.1f} vs deck pocket r 14.5")

    gear = build_spur(Z_GEAR, W_GEAR)
    pin = build_spur(Z_PIN, W_PIN)
    for name, mesh in (("gear32", gear), ("pin16", pin)):
        print(f"{name}: watertight {mesh.is_watertight}  volume {mesh.is_volume}  "
              f"bounds {np.round(mesh.bounds, 3).tolist()}  vol {mesh.volume:.1f} mm3")

    center, vmin, zeros = scan_phase(gear, pin, CD)
    print(f"phase scan @ CD {CD}: min intersection {vmin:.4f} mm3, zero window "
          f"{len(zeros)}/{121} samples, center {center:.3f} deg")

    # backlash: shrink CD at the window-center phase until flank contact appears
    g0 = gear.copy(); g0.apply_transform(ROT_Z(center))
    for d in (0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40):
        g = g0.copy(); g.apply_translation((-(CD - d), 0, 0))
        print(f"  CD - {d:.2f}: intersection {ivol(g, pin):.4f} mm3")

    # coupled rotation sweep: pinion +theta, gear center-phase - theta*Z_PIN/Z_GEAR
    # (external mesh, both about +Z -> opposite senses). One full pinion tooth pitch
    # in 45 steps; max penetration must stay 0 for a kinematically clean pair.
    worst = 0.0
    for th in np.linspace(0, 360.0 / Z_PIN, 46):
        p = pin.copy(); p.apply_transform(ROT_Z(th))
        g = gear.copy(); g.apply_transform(ROT_Z(center - th * Z_PIN / Z_GEAR))
        g.apply_translation((-CD, 0, 0))
        worst = max(worst, ivol(g, p))
    print(f"coupled rotation sweep (46 steps over one pinion pitch): "
          f"max intersection {worst:.4f} mm3")

    gear.export(OUT_GEAR)
    pin.export(OUT_PIN)
    meta = {
        "module": MODULE, "gear_teeth": Z_GEAR, "pinion_teeth": Z_PIN,
        "pa_deg": PA_DEG, "cd": CD, "backlash": BACKLASH,
        "gear_w": W_GEAR, "pinion_w": W_PIN,
        # meshing phase for build.py's cosmetic clocking: rotate the 32T by
        # gear32_mesh_deg (mod 360/32) when the pinion sits tooth-on-+X at pan=0
        "gear32_mesh_deg": round(center, 3),
    }
    with open(OUT_META, "w") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")
    print(f"wrote {OUT_GEAR}, {OUT_PIN} and {OUT_META}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Real involute worm-drive tooth geometry for the desk-pi tilt axis.

Replaces the readable placeholders (`gear_disc` / `worm` in src/build.py) with
a properly meshing pair:

  stl/neck/worm_wheel_real.stl  12T helical involute wheel, axis X, centered at origin
  stl/neck/tilt_worm_real.stl   trapezoidal-thread worm (STARTS threads), axis Y, centered
  stl/neck/worm_real_meta.json  generation record; build.py compares it to PARAMS and
                                falls back to placeholders on ANY mismatch (honesty gate)

Run from the repo root with the tools/gears venv:
  tools/gears/.venv/bin/python tools/gears/gen_worm_drive.py

Design derivation (all mm / degrees; see docs/WORM.md for the full story):
  - module 1.25 and z=12 fix the wheel pitch radius at 7.5 and the worm axial
    pitch at pi*m = 3.92699 (lead = starts * axial pitch).
  - The Ø7 solid worm core (for the double-D bore build.py cuts) forces
    worm root r >= 3.5. Root = pitch_r - dedendum, and the wheel teeth must
    dip below the worm pitch line, so pitch_r = 3.5 + wheel_addendum + clearance
    = 3.5 + 0.75 + 0.15 = 4.4  ->  CD = 7.5 + 4.4 = 11.9.
  - Lead angle = atan(lead / (2*pi*4.4)): 8.085 deg at 1 start (self-locking),
    23.08 deg at 3 starts (fast-tilt 2026-07-12 -- NOT self-locking, tradeoff
    in PARAMS["worm_starts"]).
  - Pressure angle 25 deg: 12T undercuts at 20 deg (limit 17T); at 25 deg the
    limit is 11.2T, so zero profile shift and full-strength roots.
  - Wheel is HELICAL, helix angle = worm lead angle (same hand), so the teeth
    track the thread across the 7 mm face (a spur wheel would clash ~0.5 mm at
    the face edges). Stub proportions: wheel addendum 0.6m, worm addendum 0.7m.

STARTS defaults to PARAMS["worm_starts"] (src/params.py = the single source of
truth); override with STARTS=<n> env for experiments.
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
# PARAMETERS
# ---------------------------------------------------------------------------
MODULE = 1.25                     # matches PARAMS["worm_module"] in src/build.py
Z_WHEEL = 12                      # matches PARAMS["worm_wheel_teeth"]
PA_DEG = 25.0                     # pressure angle. 25 (not 20): no undercut at 12T
FACE_W = 7.0                      # wheel face width = PARAMS["worm_wheel_w"]
BORE_D = 5.2                      # axle bore through the wheel (Ø5 axle + clearance)
BACKLASH = 0.25                   # circular backlash, all taken on the wheel tooth

WORM_PITCH_R = 4.4                # derived: 3.5 core + 0.75 wheel addendum + 0.15 clr
WORM_LEN = float(_P["worm_len"])  # thread span along Y (single source of truth: PARAMS)
END_CH = 0.6                      # 45 deg crest chamfer at both thread ends (cooler pass
                                  # 2026-07-13: kills the swung-envelope corner hit at the
                                  # -33.8 tilt stall + the machined-worm-style edge break)
WORM_ROOT_R = 3.5                 # Ø7 solid core: wall for the Ø~5.2 double-D bore
WORM_ADD = 0.7 * MODULE           # 0.875 -> worm tip r 5.275 (OD 10.55)
WHEEL_ADD = 0.6 * MODULE          # 0.75  -> wheel tip r 8.25 (stub, clears the core)
CLEAR = 0.15                      # radial bottom clearance, both members

STARTS = int(os.environ.get("STARTS", _P["worm_starts"]))   # 3 = fast-tilt 4:1
OUT_SUFFIX = os.environ.get("OUT_SUFFIX", "")
HAND = +1                         # +1 right-hand worm & wheel (flip both to reverse)

# derived
PITCH = np.pi * MODULE            # 3.92699 axial pitch = wheel transverse circ. pitch
LEAD = PITCH * STARTS
PA = np.radians(PA_DEG)
R_P = MODULE * Z_WHEEL / 2.0      # 7.5 wheel pitch radius
R_B = R_P * np.cos(PA)            # 6.7973 base circle
R_TIP_G = R_P + WHEEL_ADD         # 8.25
R_ROOT_G = R_P - (WORM_ADD + CLEAR)   # 6.475 (clears worm tips by CLEAR)
R_TIP_W = WORM_PITCH_R + WORM_ADD     # 5.275
CD = R_P + WORM_PITCH_R           # 11.9 center distance
LEAD_ANGLE = np.arctan(LEAD / (2 * np.pi * WORM_PITCH_R))   # 8.085 deg

OUT_WHEEL = f"stl/neck/worm_wheel_real{OUT_SUFFIX}.stl"
OUT_WORM = f"stl/neck/tilt_worm_real{OUT_SUFFIX}.stl"
OUT_META = f"stl/neck/worm_real_meta{OUT_SUFFIX}.json"


def inv(phi):
    """Involute function."""
    return np.tan(phi) - phi


# ---------------------------------------------------------------------------
# Wheel: 2D involute outline -> manifold twisted extrude -> axis X
# ---------------------------------------------------------------------------
def wheel_outline():
    """CCW outer outline of the 12T involute gear in the transverse plane."""
    s_p = PITCH / 2.0 - BACKLASH          # tooth thickness at pitch (backlash thinned)

    def half_angle(r):
        """Half tooth-thickness angle at radius r on the involute flank."""
        phi = np.arccos(np.clip(R_B / r, -1, 1))
        return s_p / (2 * R_P) + inv(PA) - inv(phi)

    psi_base = s_p / (2 * R_P) + inv(PA)  # half angle where flank meets base circle
    pitch_ang = 2 * np.pi / Z_WHEEL

    pts = []
    n_flank, n_tip, n_root = 14, 5, 7
    for k in range(Z_WHEEL):
        c = k * pitch_ang
        # leading flank: radial rise root->base, involute base->tip (angle increasing)
        pts.append((R_ROOT_G, c - psi_base))
        for r in np.linspace(R_B, R_TIP_G, n_flank):
            pts.append((r, c - half_angle(r)))
        # tip arc
        psi_t = half_angle(R_TIP_G)
        for a in np.linspace(-psi_t, psi_t, n_tip)[1:-1]:
            pts.append((R_TIP_G, c + a))
        # trailing flank: involute tip->base, radial drop base->root
        for r in np.linspace(R_TIP_G, R_B, n_flank):
            pts.append((r, c + half_angle(r)))
        pts.append((R_ROOT_G, c + psi_base))
        # root arc to next tooth
        for a in np.linspace(psi_base, pitch_ang - psi_base, n_root)[1:-1]:
            pts.append((R_ROOT_G, c + a))
    rr = np.array([p[0] for p in pts])
    aa = np.array([p[1] for p in pts])
    return np.column_stack([rr * np.cos(aa), rr * np.sin(aa)])


def build_wheel():
    outer = wheel_outline()
    th = np.linspace(0, 2 * np.pi, 97)[:-1]
    bore = np.column_stack([BORE_D / 2 * np.cos(-th), BORE_D / 2 * np.sin(-th)])  # CW hole

    cs = m3.CrossSection([outer.tolist(), bore.tolist()], m3.FillRule.EvenOdd)
    # helix: total twist over the face width. Tooth traces x*tan(beta)/r_p about the axis.
    twist = np.degrees(FACE_W * np.tan(LEAD_ANGLE) / R_P)     # 7.60 deg (1 start) / 22.79 (3)
    man = m3.Manifold.extrude(cs, FACE_W, n_divisions=48, twist_degrees=HAND * twist)
    mm = man.to_mesh()
    mesh = trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3],
                           np.asarray(mm.tri_verts), process=False)
    mesh.apply_translation((0, 0, -FACE_W / 2))               # center on origin
    # extrusion axis Z -> wheel axis X (rotate +90 about Y): (x,y,z)->(z,y,-x)
    mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))
    return mesh


# ---------------------------------------------------------------------------
# Worm: trapezoidal thread swept along a helix + core cylinder, trimmed to length
# ---------------------------------------------------------------------------
def build_worm():
    # axial-section rib profile (dy, r), a trapezoid whose base is buried in the core
    hw_tip = PITCH / 4 - WORM_ADD * np.tan(PA)                 # 0.5737 crest half-width
    base_r = WORM_ROOT_R - 0.3                                 # embed 0.3 into the core
    hw_base = PITCH / 4 + (WORM_PITCH_R - base_r) * np.tan(PA)  # flank line extended down
    prof = np.array([
        (-hw_base, base_r),
        (-hw_tip, R_TIP_W),
        (hw_tip, R_TIP_W),
        (hw_base, base_r),
    ])

    # sweep one rib per START along its helix (lead = STARTS * axial pitch, phase
    # offset a full turn / STARTS), overshooting the trim slab by ~a pitch each end
    y_over = WORM_LEN / 2 + 1.5 * PITCH
    t_max = y_over * 2 * np.pi / LEAD
    n_steps = 900
    threads = []
    for s in range(STARTS):
        phase = 2 * np.pi * s / STARTS
        ts = np.linspace(-t_max, t_max, n_steps)
        rings = []
        for t in ts:
            yc = HAND * LEAD * t / (2 * np.pi)
            ring = []
            for dy, r in prof:
                y = yc + dy
                # 45 deg crest END CHAMFER: clamp vertex radius to a cone that starts
                # END_CH inside each trim face and drops END_CH at it (constant past the
                # face so the overshoot stays a valid ring; the trim slab discards it).
                r_cap = R_TIP_W - max(0.0, min(abs(y), WORM_LEN / 2)
                                      - (WORM_LEN / 2 - END_CH))
                ring.append((min(r, r_cap) * np.sin(t + phase), y,
                             min(r, r_cap) * np.cos(t + phase)))
            rings.append(ring)
        rings = np.array(rings)                                 # (T, 4, 3)

        T, P = rings.shape[0], rings.shape[1]
        verts = rings.reshape(-1, 3)
        faces = []
        for i in range(T - 1):
            for j in range(P):
                a = i * P + j
                b = i * P + (j + 1) % P
                c = (i + 1) * P + (j + 1) % P
                d = (i + 1) * P + j
                faces += [(a, b, c), (a, c, d)]
        faces += [(0, 1, 2), (0, 2, 3)]                         # start cap
        o = (T - 1) * P
        faces += [(o, o + 2, o + 1), (o, o + 3, o + 2)]         # end cap
        thread = trimesh.Trimesh(verts, np.array(faces), process=True)
        thread.fix_normals()
        assert thread.is_volume, f"thread sweep (start {s}) not a volume"
        threads.append(thread)

    rotx = trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0))
    core = trimesh.creation.cylinder(radius=WORM_ROOT_R, height=WORM_LEN + 8,
                                     sections=192, transform=rotx)
    slab = trimesh.creation.box((30, WORM_LEN, 30))
    worm = trimesh.boolean.intersection(
        [trimesh.boolean.union([core] + threads, engine="manifold"), slab],
        engine="manifold")
    return worm


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
def mesh_check(wheel, worm):
    """Static mesh test: worm axis Y at (0,0,-CD); scan wheel phase over one tooth
    pitch for the minimum boolean-intersection volume (the assembled phase)."""
    worm_p = worm.copy()
    worm_p.apply_translation((0, 0, -CD))
    best = (np.inf, 0.0)
    worst = 0.0
    for phi in np.linspace(0, 30, 61):
        w = wheel.copy()
        w.apply_transform(trimesh.transformations.rotation_matrix(
            np.radians(phi), (1, 0, 0)))
        ix = trimesh.boolean.intersection([w, worm_p], engine="manifold")
        v = 0.0 if ix.is_empty else abs(ix.volume)
        if v < best[0]:
            best = (v, phi)
        worst = max(worst, v)
    return best, worst


def main():
    print(f"module {MODULE}  z {Z_WHEEL}  PA {PA_DEG} deg  backlash {BACKLASH}  "
          f"STARTS {STARTS}")
    print(f"wheel: pitch r {R_P}  tip r {R_TIP_G}  root r {R_ROOT_G:.3f}  "
          f"base r {R_B:.4f}  face {FACE_W}  bore {BORE_D}")
    print(f"worm : pitch r {WORM_PITCH_R}  tip r {R_TIP_W} (OD {2*R_TIP_W})  "
          f"root r {WORM_ROOT_R} (core {2*WORM_ROOT_R})  len {WORM_LEN}")
    print(f"lead {LEAD:.5f}  LEAD ANGLE {np.degrees(LEAD_ANGLE):.3f} deg  "
          f"CENTER DISTANCE {CD}")
    hw_tip = PITCH / 4 - WORM_ADD * np.tan(PA)
    print(f"worm crest width {2*hw_tip:.3f} mm (printable > 0.6)  end chamfer {END_CH}")

    wheel = build_wheel()
    worm = build_worm()
    for name, mesh in (("wheel", wheel), ("worm", worm)):
        print(f"{name}: watertight {mesh.is_watertight}  volume-mesh {mesh.is_volume}  "
              f"bounds {np.round(mesh.bounds, 3).tolist()}  vol {mesh.volume:.1f} mm3")

    (v, phi), worst = mesh_check(wheel, worm)
    print(f"mesh check @ CD {CD}: min intersection {v:.4f} mm3 at wheel phase "
          f"{phi:.1f} deg (worst over scan {worst:.2f} mm3)")

    wheel.export(OUT_WHEEL)
    worm.export(OUT_WORM)
    # generation record: src/gears.py compares this to PARAMS (worm_real_ok) and
    # build.py falls back to placeholders on ANY mismatch, so a params change without
    # a regen can never silently ship stale teeth (the old rule hard-coded starts != 1)
    meta = {
        "starts": STARTS, "module": MODULE, "wheel_teeth": Z_WHEEL,
        "worm_pitch_r": WORM_PITCH_R, "cd": CD, "pa_deg": PA_DEG,
        "backlash": BACKLASH, "lead_angle_deg": round(float(np.degrees(LEAD_ANGLE)), 3),
        "face_w": FACE_W, "worm_len": WORM_LEN, "hand": HAND,
        "end_chamfer": END_CH,
    }
    with open(OUT_META, "w") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")
    print(f"wrote {OUT_WHEEL}, {OUT_WORM} and {OUT_META}")


if __name__ == "__main__":
    main()

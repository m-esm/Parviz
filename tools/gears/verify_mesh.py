#!/usr/bin/env python3
"""Deeper verification of the generated worm pair.

1. Hand check: rebuild the wheel with the OPPOSITE helix hand; a wrong-hand
   wheel cannot find a zero-interference phase, the correct one can.
2. Engagement check: at the best phase, shrink the center distance in steps;
   contact volume must appear within ~backlash (proves flanks are ~0.1-0.2 mm
   apart, i.e. really meshing, not floating in air).
3. Section plot: x=0 cross-section of wheel + worm at the assembled pose
   (the classic worm-mesh diagram) -> .claude/renders/worm_mesh_section.png
"""
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import gen_worm_drive as g

ROT_X = lambda deg: trimesh.transformations.rotation_matrix(np.radians(deg), (1, 0, 0))


def scan(wheel, worm, cd, n=61):
    worm_p = worm.copy()
    worm_p.apply_translation((0, 0, -cd))
    best = (np.inf, 0.0)
    for phi in np.linspace(0, 30, n):
        w = wheel.copy()
        w.apply_transform(ROT_X(phi))
        ix = trimesh.boolean.intersection([w, worm_p], engine="manifold")
        v = 0.0 if ix.is_empty else abs(ix.volume)
        if v < best[0]:
            best = (v, phi)
    return best


def main():
    worm = trimesh.load(g.OUT_WORM)
    wheel = trimesh.load(g.OUT_WHEEL)

    # 1. hand check
    g.HAND = -1
    wheel_wrong = g.build_wheel()
    g.HAND = +1
    v_right, phi_right = scan(wheel, worm, g.CD)
    v_wrong, _ = scan(wheel_wrong, worm, g.CD)
    print(f"hand check: correct-hand min {v_right:.4f} mm3 @ {phi_right:.1f} deg | "
          f"wrong-hand min {v_wrong:.4f} mm3")

    # 2. engagement: contact must appear within ~backlash of CD reduction
    w = wheel.copy()
    w.apply_transform(ROT_X(phi_right))
    for d in (0.0, 0.05, 0.10, 0.15, 0.20, 0.30):
        worm_p = worm.copy()
        worm_p.apply_translation((0, 0, -(g.CD - d)))
        ix = trimesh.boolean.intersection([w, worm_p], engine="manifold")
        v = 0.0 if ix.is_empty else abs(ix.volume)
        print(f"  CD - {d:.2f}: intersection {v:.4f} mm3")

    # 3. section plot at x=0
    worm_p = worm.copy()
    worm_p.apply_translation((0, 0, -g.CD))
    fig, ax = plt.subplots(figsize=(8, 9))
    for mesh, col, lab in ((w, "tab:blue", "wheel (12T helical)"),
                           (worm_p, "tab:red", f"worm ({g.STARTS}-start)")):
        sec = mesh.section(plane_origin=(0, 0, 0), plane_normal=(1, 0, 0))
        if sec is None:
            continue
        first = True
        for ent in sec.discrete:            # 3D polyline loops in the x=0 plane
            ax.plot(ent[:, 1], ent[:, 2], color=col, lw=1.0,
                    label=lab if first else None)
            first = False
    ax.axhline(-g.CD, color="gray", ls=":", lw=0.7)
    ax.plot(0, 0, "k+", ms=10)
    ax.plot(0, -g.CD, "r+", ms=10)
    th = np.linspace(0, 2 * np.pi, 200)
    ax.plot(g.R_P * np.sin(th), g.R_P * np.cos(th), "b--", lw=0.5)
    ax.plot(g.WORM_PITCH_R * np.sin(th), -g.CD + g.WORM_PITCH_R * np.cos(th),
            "r--", lw=0.5)
    ax.set_aspect("equal"); ax.grid(alpha=0.3); ax.legend(loc="upper right")
    ax.set_title(f"x=0 section, CD={g.CD}, wheel phase {phi_right:.1f} deg "
                 f"(dashed = pitch circles)")
    ax.set_xlim(-11, 11); ax.set_ylim(-19, 10)
    fig.savefig(".claude/renders/worm_mesh_section.png", dpi=140,
                bbox_inches="tight")
    print("wrote .claude/renders/worm_mesh_section.png")

    # zoomed contact region
    ax.set_xlim(-5, 5); ax.set_ylim(-10.5, -3.5)
    fig.savefig(".claude/renders/worm_mesh_zoom.png", dpi=160, bbox_inches="tight")
    print("wrote .claude/renders/worm_mesh_zoom.png")


if __name__ == "__main__":
    main()

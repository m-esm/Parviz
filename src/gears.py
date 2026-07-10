"""Worm-drive gear helpers: generated-tooth STL loading + placeholder gears.

Split out of the original monolithic build.py (2026-07-10); see
build.py for the assembly entry point and the overall design notes.
"""
import os
import numpy as np
import trimesh
from trimesh.transformations import rotation_matrix as R
from stlpaths import webpath, stlp
from params import EXPORT, P, TAU
from geo import box, cyl, uni


def worm_cd():
    """Tilt worm center distance = wheel pitch r + worm pitch r = 7.5 + 4.4 = 11.900
    (docs/WORM.md: the generated involute pair needs CD 11.9; was 11.5 off worm_od*0.4).
    Single source of truth for the neck bracket AND the assembly: the worm, tilt motor,
    bracket plate, cradle, riser and can pocket all key off this and drop 0.4 together."""
    return P["worm_module"] * P["worm_wheel_teeth"] / 2 + P["worm_pitch_r"]


def gear_disc(pitch_r, teeth, width, tooth_h, axis="x"):
    """A spur/worm-wheel disc with simple trapezoidal teeth (a readable gear, not a print-ready
    involute -- generate the final teeth with BOSL2 in a venv). Rotates about `axis`, centered
    at the origin. Root cylinder + `teeth` radial tooth prisms around the rim."""
    root_r = pitch_r - 0.5 * tooth_h
    parts = [cyl(root_r, width, axis=axis)]
    tw = max(2 * np.pi * pitch_r / teeth * 0.55, 0.8)   # tooth tangential width
    # tooth prism is tooth_h+1 tall, centered at pitch_r-0.5: sinks 1.0 into the root disc
    # (the old exact root..root+tooth_h span only LINE-touched the root cylinder, so every
    # tooth split off as its own body -- PRINTABILITY 3). Tip circle unchanged (root+tooth_h).
    for i in range(teeth):
        a = TAU * i / teeth
        if axis == "x":
            t = box(width, tw, tooth_h + 1.0); t.apply_translation((0, 0, pitch_r - 0.5))
            t.apply_transform(R(a, (1, 0, 0)))
        elif axis == "y":
            t = box(tw, width, tooth_h + 1.0); t.apply_translation((0, 0, pitch_r - 0.5))
            t.apply_transform(R(a, (0, 1, 0)))
        else:  # z
            t = box(tw, tooth_h + 1.0, width); t.apply_translation((0, pitch_r - 0.5, 0))
            t.apply_transform(R(a, (0, 0, 1)))
        parts.append(t)
    return uni(parts)


def worm(pitch_r, length, starts=1, axis="y"):
    """Single-start worm: a core cylinder wrapped by a helical rib (approximated by a stack of
    short rotated ribs -- reads as a worm thread; final thread from BOSL2). Axis along `axis`."""
    core = cyl(pitch_r * 0.72, length, axis=axis)
    ribs = [core]
    n = 48
    lead = length / 3.0                                  # visual lead per turn
    for i in range(n):
        f = i / n
        a = TAU * f * (length / lead)
        seg = box(2.0, 2.0, 2.0)
        pos_axis = -length / 2 + f * length
        if axis == "y":
            seg.apply_translation((0, 0, pitch_r * 0.85)); seg.apply_transform(R(a, (0, 1, 0)))
            seg.apply_translation((0, pos_axis, 0))
        elif axis == "x":
            seg.apply_translation((0, 0, pitch_r * 0.85)); seg.apply_transform(R(a, (1, 0, 0)))
            seg.apply_translation((pos_axis, 0, 0))
        else:
            seg.apply_translation((pitch_r * 0.85, 0, 0)); seg.apply_transform(R(a, (0, 0, 1)))
            seg.apply_translation((0, 0, pos_axis))
        ribs.append(seg)
    return uni(ribs)


def load_gear_stl(name):
    """Load a generated real-tooth gear blank (tools/gears/gen_worm_drive.py, docs/WORM.md).
    Both blanks are committed under stl/neck/; hard-fail with the regen pointer if one is
    missing so EXPORT/regeneration flows don't crash cryptically mid-boolean."""
    path = stlp(name)
    if not os.path.exists(path):
        raise SystemExit(
            f"build.py: missing real gear mesh {path}\n"
            "  Regenerate with tools/gears/gen_worm_drive.py (docs/WORM.md 'How to "
            "regenerate'), or set PLACEHOLDER_GEARS=1 to build with the readable "
            "gear_disc/worm placeholders.")
    m = trimesh.load(path, force="mesh")
    if not m.is_volume:
        raise SystemExit(f"build.py: {path} is not watertight -- regenerate it (docs/WORM.md)")
    return m



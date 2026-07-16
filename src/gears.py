"""Worm-drive gear helpers: generated-tooth STL loading + placeholder gears.

Split out of the original monolithic build.py (2026-07-10); see
build.py for the assembly entry point and the overall design notes.
"""
import json
import os
import numpy as np
import trimesh
from trimesh.transformations import rotation_matrix as R
from stlpaths import webpath, stlp
from params import EXPORT, P, TAU
from geo import box, cyl, uni
from geo import extrude_polygon, sub
from shapely.geometry import Polygon


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


def involute_spur(teeth, module, width, axis="x", bore_d=0.0,
                  pressure_angle=20.0, backlash=0.20):
    """Printable full-depth involute spur gear, tooth-centred on the profile +X axis.

    This is the runtime counterpart of tools/gears/gen_pan_spurs.py, used for the
    antenna cartridges whose old `gear_disc` objects were disconnected placeholders.
    """
    pa = np.radians(pressure_angle)
    rp = module * teeth / 2.0
    rb = rp * np.cos(pa)
    rt = rp + module
    rr = rp - 1.25 * module
    tooth_t = np.pi * module / 2.0 - backlash / 2.0

    def inv(phi):
        return np.tan(phi) - phi

    def half_angle(r):
        phi = np.arccos(np.clip(rb / r, -1, 1))
        return tooth_t / (2 * rp) + inv(pa) - inv(phi)

    psi_base = tooth_t / (2 * rp) + inv(pa)
    pitch = TAU / teeth
    rlo = max(rr, rb)
    polar = []
    for k in range(teeth):
        c = k * pitch
        polar.append((rr, c - psi_base))
        for r in np.linspace(rlo, rt, 14):
            polar.append((r, c - half_angle(max(r, rb))))
        ht = half_angle(rt)
        for a in np.linspace(-ht, ht, 5)[1:-1]:
            polar.append((rt, c + a))
        for r in np.linspace(rt, rlo, 14):
            polar.append((r, c + half_angle(max(r, rb))))
        polar.append((rr, c + psi_base))
        for a in np.linspace(psi_base, pitch - psi_base, 7)[1:-1]:
            polar.append((rr, c + a))
    pts = [(r * np.cos(a), r * np.sin(a)) for r, a in polar]
    mesh = extrude_polygon(Polygon(pts), width)
    mesh.apply_translation((0, 0, -width / 2.0))
    if bore_d > 0:
        mesh = sub(mesh, cyl(bore_d / 2.0, width + 2.0))
    if axis == "x":
        mesh.apply_transform(R(np.pi / 2, (0, 1, 0)))
    elif axis == "y":
        mesh.apply_transform(R(np.pi / 2, (1, 0, 0)))
    return mesh


def worm(pitch_r, length, starts=1, axis="y"):
    """Placeholder worm: a core cylinder wrapped by `starts` helical ribs (approximated by
    stacks of short rotated ribs -- reads as a worm thread; final thread is a generated
    pass, docs/WORM.md). Multi-start (fast-tilt 2026-07-12) draws the interleaved ribs so
    the 3-start swap is visible in review renders. Axis along `axis`."""
    core = cyl(pitch_r * 0.72, length, axis=axis)
    ribs = [core]
    n = 48
    lead = length / 3.0 * starts                         # visual lead per turn (per start)
    for s in range(starts):
        phase = TAU * s / starts
        for i in range(n):
            f = i / n
            a = phase + TAU * f * (length / lead)
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


def _meta_ok(meta_name, expect):
    """Honesty gate for generated-teeth STLs: the generator writes a sidecar JSON
    recording what it generated; the build compares it to PARAMS and falls back to
    placeholders on ANY mismatch (missing file included). This replaced the hard-coded
    `worm_starts != 1` rule when the 3-start pair landed -- a params change without a
    regen can never silently ship stale teeth."""
    path = stlp(meta_name)
    if not os.path.exists(path):
        return False
    with open(path) as f:
        meta = json.load(f)
    for k, v in expect.items():
        got = meta.get(k)
        if got is None:
            return False
        if isinstance(v, (int, float)):
            if abs(float(got) - float(v)) > 1e-9:
                return False
        elif got != v:
            return False
    return True


def worm_real_ok():
    """True when the committed worm pair (stl/neck/*_real.stl) matches PARAMS."""
    return _meta_ok("worm_real_meta.json", {
        "starts": P["worm_starts"], "module": P["worm_module"],
        "wheel_teeth": P["worm_wheel_teeth"], "worm_pitch_r": P["worm_pitch_r"],
        "face_w": P["worm_wheel_w"], "worm_len": P["worm_len"]})


def pan_real_ok():
    """True when the committed pan spur pair matches PARAMS pan_gear_*."""
    return _meta_ok("pan_gears_real_meta.json", {
        "module": P["pan_gear_m"], "gear_teeth": P["pan_gear_motor_t"],
        "pinion_teeth": P["pan_gear_pinion_t"],
        "gear_w": P["pan_gear_z"][1] - P["pan_gear_z"][0]})


def pan_gear_mesh_deg():
    """The 32T's zero-backlash-window center measured by tools/gears/gen_pan_spurs.py
    (both blanks tooth-centered on +X, gear at azimuth 180 from the pan axis)."""
    with open(stlp("pan_gears_real_meta.json")) as f:
        return float(json.load(f)["gear32_mesh_deg"])


def load_gear_stl(name):
    """Load a generated real-tooth gear blank (tools/gears/gen_worm_drive.py, docs/WORM.md).
    Both blanks are committed under stl/neck/; hard-fail with the regen pointer if one is
    missing so EXPORT/regeneration flows don't crash cryptically mid-boolean."""
    path = stlp(name)
    if not os.path.exists(path):
        raise SystemExit(
            f"build.py: missing real gear mesh {path}\n"
            "  Regenerate with tools/gears/gen_worm_drive.py or gen_pan_spurs.py "
            "(docs/WORM.md 'How to regenerate'), or set PLACEHOLDER_GEARS=1 to build "
            "with the readable gear_disc/worm placeholders.")
    m = trimesh.load(path, force="mesh")
    if not m.is_volume:
        raise SystemExit(f"build.py: {path} is not watertight -- regenerate it (docs/WORM.md)")
    return m


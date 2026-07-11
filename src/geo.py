"""Geometry utilities: primitives, boolean helpers, orientation, colors.

Split out of the original monolithic build.py (2026-07-10); see
build.py for the assembly entry point and the overall design notes.
"""
import numpy as np
import trimesh
import shapely.geometry as sg
from trimesh.creation import extrude_polygon
from trimesh.transformations import rotation_matrix as R
from params import P, TAU


# Design-reference colorway (reference/design/*.jpg): matte black body + safety-orange
# accents, silver mechanicals. NOTE the bundled viewer re-colors by NODE NAME (PAL in
# web/viewer_glb.html) -- keep both palettes in sync.
COLORS = {
    "screen":  [26, 30, 38, 255],
    "cradle":  [46, 50, 56, 255],       # matte charcoal (head bezel)
    "back":    [54, 58, 65, 255],       # charcoal (head back, covers)
    "neck":    [52, 56, 63, 255],       # matte charcoal mechanicals (neck styling pass
                                        # 2026-07-12: bright steel read as raw CAD; the
                                        # ref neck blocks are near-black plastic)
    "fork":    [154, 160, 168, 255],    # worm_wheel: silver gear metal (split from neck)
    "pan":     [46, 50, 56, 255],       # near-black turret (was graphite; ref two-tone)
    "base":    [44, 48, 54, 255],       # matte charcoal chassis
    "track":   [35, 37, 41, 255],       # near-black rubber
    "motor":   [154, 160, 168, 255],    # silver actuation
    "camera":  [30, 33, 38, 255],       # black camera pod
    "pi":      [56, 150, 96, 255],
    "axle":    [196, 200, 206, 255],    # bright steel
    "accent":  [232, 116, 34, 255],     # safety orange (design-ref two-tone)
    "lamp":    [232, 168, 60, 255],     # amber indicator
    "led":     [242, 244, 246, 255],    # white light strip
    "sensor":  [184, 188, 194, 255],    # silver sensor barrels
    "antenna": [42, 45, 51, 255],       # black knurled stub
    "arm":     [51, 55, 62, 255],       # charcoal gripper arms
}


def _color(m, key):
    m.visual.vertex_colors = COLORS[key]
    return m


def box(w, d, h):
    return trimesh.creation.box(extents=(w, d, h))


def cyl(r, h, axis="z", sections=64):
    m = trimesh.creation.cylinder(radius=r, height=h, sections=sections)
    if axis == "x":
        m.apply_transform(R(TAU / 4, (0, 1, 0)))     # 90deg: Z-cyl -> X
    elif axis == "y":
        m.apply_transform(R(TAU / 4, (1, 0, 0)))     # 90deg: Z-cyl -> Y
    return m


def rounded_box(w, d, h, r):
    """Box with rounded vertical edges (rounded-rect footprint extruded along +Z)."""
    poly = sg.box(-w / 2, -d / 2, w / 2, d / 2).buffer(-r, join_style=1).buffer(r, join_style=1)
    return extrude_polygon(poly, h)          # in XY, extruded z=0..h


def hex_prism(af, h):
    """Hexagonal prism (for a captive-nut pocket), axis +Z, across-flats = af."""
    return trimesh.creation.cylinder(radius=af / np.sqrt(3), height=h, sections=6)


def _orient(m, normal):
    """Rotate a +Z-aligned mesh so +Z points along `normal`."""
    n = np.asarray(normal, float); n /= np.linalg.norm(n)
    z = np.array([0, 0, 1.0]); v = np.cross(z, n); s = np.linalg.norm(v)
    if s > 1e-6:
        m.apply_transform(R(np.arctan2(s, np.dot(z, n)), v / s))
    return m


def screw_post(pos, normal, depth):
    """A cylindrical boss starting at `pos`, extending `depth` along `normal`."""
    m = cyl(P["boss_r"], depth); m.apply_translation((0, 0, depth / 2))
    _orient(m, normal); m.apply_translation(pos)
    return m


def fix_pin(r, length, direction, face_pt, bury=1.0):
    """Locating pin (POSITIVE): radius r, protruding `length` along `direction` from a
    part face at `face_pt`, buried `bury` into the part so uni() fuses (a face-tangent
    cylinder does not fuse -- see the stage-4 D4 ULN standoff defect). `direction` must
    not be exactly -Z (_orient's antiparallel gap); no fixing here needs it."""
    L = length + bury
    m = cyl(r, L)
    m.apply_translation((0, 0, L / 2 - bury))
    _orient(m, direction)
    m.apply_translation(face_pt)
    return m


def blind_socket(r, deep, out_dir, face_pt, overshoot=1.0):
    """Blind pin-socket NEGATIVE: radius r, cut `deep` into a wall whose outer face
    passes through `face_pt`; `out_dir` points OUT of the wall. The `overshoot` past the
    face avoids a coincident boolean face at the opening."""
    L = deep + overshoot
    m = cyl(r, L)
    m.apply_translation((0, 0, L / 2 - deep))
    _orient(m, out_dir)
    m.apply_translation(face_pt)
    return m


def sub(a, b):
    return trimesh.boolean.difference([a, b], engine="manifold")


def uni(parts):
    return trimesh.boolean.union(parts, engine="manifold")


def inter(a, b):
    return trimesh.boolean.intersection([a, b], engine="manifold")


def dbore_neg(length, axis="z", clear=0.12, round_clear=None, flat_clear=None):
    """Negative solid for a 28BYJ-48 double-D shaft socket (torque via the flats, not friction).

    A round bore of Ø motor_shaft_d intersected with a slab motor_shaft_flat wide -> the
    familiar D (two arcs + two flats). `clear` loosens it for a snug press in PLA.
    round_clear/flat_clear override it per feature: a LOOSE round + snug flats makes a
    mini-Oldham (flats drive, something else -- e.g. the pan race -- locates radially).
    """
    d = P["motor_shaft_d"] + 2 * (clear if round_clear is None else round_clear)
    flat = P["motor_shaft_flat"] + 2 * (clear if flat_clear is None else flat_clear)
    round_bore = cyl(d / 2, length, axis=axis)
    big = d + 4
    if axis == "z":
        slab = box(flat, big, length)
    elif axis == "x":
        slab = box(length, flat, big)
    else:  # y
        slab = box(flat, length, big)
    return inter(round_bore, slab)


def dbore_hub(outer_r, length, axis="z"):
    """A printed hub (cylinder) with a double-D socket down its axis, for coupling to the
    28BYJ-48 D-shaft. Caller positions/orients it; grub-screw boss is left to the caller."""
    hub = cyl(outer_r, length, axis=axis)
    return sub(hub, dbore_neg(length + 2, axis=axis))


def _T(x, y, z):
    m = np.eye(4); m[:3, 3] = (x, y, z); return m


def frustum(r_bottom, r_top, h, sections=96):
    """Truncated cone from z=0 (r_bottom) to z=h (r_top)."""
    if abs(r_bottom - r_top) < 1e-6:
        c = cyl(r_bottom, h, sections=sections)
        c.apply_translation((0, 0, h / 2))
        return c
    h_full = h * r_bottom / (r_bottom - r_top)      # height to the apex
    c = trimesh.creation.cone(radius=r_bottom, height=h_full, sections=sections)
    cut = box(2 * r_bottom + 20, 2 * r_bottom + 20, h_full)
    cut.apply_translation((0, 0, h + h_full / 2))   # remove everything above z=h
    return sub(c, cut)


def R_x(ang):
    return R(ang, (1, 0, 0))



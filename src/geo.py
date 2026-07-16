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


def export_stl(mesh, path):
    """EXPORT-path STL writer with a WATERTIGHTNESS GATE (wallcheck pass 2026-07-13).

    slice_mesh_plane(cap=True) splits (the head_back frames) can leave non-manifold
    cap junctions -- edges shared by 4 faces (measured: 2 such edges per frame, zero
    open edges) -- which make the printed mesh non-watertight and ray-thickness
    numbers on it meaningless. Repair = a manifold3d ROUND-TRIP: it merges the
    junctions without moving a vertex (verified volume delta 0.0%, bbox identical).
    Multi-body-by-design meshes (track strips/keepers, pan_clips) are watertight per
    body and pass through untouched (repair only runs on a non-watertight mesh).
    Guards: repair must not change printed geometry (volume < 0.1%, bbox < 0.01 mm)
    and the written mesh MUST be watertight -- regressions fail loudly at export.

    NOTE the check runs on a FLOAT32-QUANTIZED, POSITION-MERGED copy: STL stores
    float32 per-triangle vertices, so writing collapses nearly-equal float64
    vertices into exactly-equal ones and every reader then merges them -- an
    in-memory mesh can look watertight on its own vertex indices while the FILE it
    writes is not (the frame defect hid exactly there; merge_vertices alone on the
    float64 mesh still read watertight). If the quantized copy is clean, the
    ORIGINAL bytes are written unchanged; only a defective mesh gets the repair."""
    chk = trimesh.Trimesh(vertices=np.asarray(mesh.vertices, dtype=np.float32)
                          .astype(np.float64),
                          faces=mesh.faces.copy(), process=True)
    if not chk.is_watertight:
        import manifold3d
        mg = manifold3d.Mesh(
            vert_properties=np.asarray(chk.vertices, dtype=np.float32),
            tri_verts=np.asarray(chk.faces, dtype=np.uint32))
        out = manifold3d.Manifold(mesh=mg).to_mesh()
        rep = trimesh.Trimesh(vertices=np.asarray(out.vert_properties)[:, :3],
                              faces=np.asarray(out.tri_verts))
        dvol = abs(rep.volume - mesh.volume) / max(abs(mesh.volume), 1e-9)
        dbox = float(np.abs(np.asarray(rep.bounds) - np.asarray(mesh.bounds)).max())
        assert dvol < 1e-3 and dbox < 0.01, (
            "export repair changed %s: dvol %.4f%%, dbbox %.4f mm" % (path, 100 * dvol, dbox))
        assert rep.is_watertight, "export mesh NOT WATERTIGHT after repair: %s" % path
        mesh = rep
    mesh.export(path)


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


def teardrop(r, length, axis="y", up="z"):
    """Self-supporting HOLE CUTTER for a horizontal bore: a `cyl(r)` with a 45deg
    pointed cap on the `up` side (the teardrop). Subtracting it gives a bore whose
    roof never exceeds 45deg, so it FDM-prints WITHOUT support and without a sagging
    ceiling (classic teardrop-hole technique). `axis` = bore direction, `up` = the
    print-up direction the apex points toward. Only the horizontal cases used in the
    seam-up / wall-up prints are supported (axis x or y, up z). The cap is a `box(r)`
    rotated 45deg about the bore axis, bottom vertex at the bore centre, apex at
    r*sqrt(2) along +up -- so a large counterbore whose apex would clear the part top
    simply opens into a self-supporting slot (the 'flat-roof teardrop' variant)."""
    if up != "z":
        raise ValueError("teardrop(): up must be 'z'")
    base = cyl(r, length, axis=axis)
    if axis == "y":
        cap = box(r, length, r); cap.apply_transform(R(TAU / 8, (0, 1, 0)))
    elif axis == "x":
        cap = box(length, r, r); cap.apply_transform(R(TAU / 8, (1, 0, 0)))
    else:
        raise ValueError("teardrop(): axis must be 'x' or 'y' for up='z'")
    cap.apply_translation((0, 0, r * np.sqrt(0.5)))
    return uni([base, cap])


NUT = {"M2": (4.0, 1.6), "M2.5": (5.0, 2.0), "M3": (5.5, 2.6), "M4": (7.0, 3.2)}
# hex nut (across-flats, thickness); M3 matches the proven chassis_pedestal traps.
NUT_NIB_PROUD = 0.25
NUT_NIB_RUN = 1.2
NUT_NIB_SEAT_CLEAR = 0.1
NUT_NIB_MIN_EXTRA = 1.5


def nut_ac(size="M3"):
    """Hex nut ACROSS-CORNERS span. A nut with its FLATS on the slot walls spans
    this much along the insertion run -- NOT the across-flats figure. Getting
    this wrong is what broke every captive trap in the first print (see below)."""
    return NUT[size][0] * 2.0 / np.sqrt(3.0)


def nut_slot(center, screw_axis="z", open_dir=(0, 1, 0), size="M3",
             length=14.0, c_af=0.2, c_t=0.2, seat=True, nib=False):
    """Slide-in captive hex-nut trap NEGATIVE (standardized for the 2026-07-15
    fastening campaign): a rectangular slot, width = nut AF + c_af (the flats
    ride the walls = the rotation lock), thickness = nut_t + c_t along the screw
    axis, running from a closed SEAT out through the part's open face along
    `open_dir`. Pair it with a cyl()/teardrop() screw bore on `screw_axis`
    through `center`; keep >= 1.2 wall beyond the slot, and place things so the
    screw tip lands ~2 threads past the nut.

    `center` IS THE SCREW AXIS (and, once the nut is pushed home, the nut's own
    centre): the slot is cut from `center - open_dir*ac/2` -- half the nut's
    ACROSS-CORNERS span behind the axis -- out to `center + open_dir*(length -
    ac/2)`. So a nut slid in and pushed to the seat lands dead on the bore, and
    the seat is what aligns it: hands-free, no fiddling while you drive.

    WHY THE ac/2 MATTERS (2026-07-15, the whole reason this helper exists): the
    original hand-built chassis_pedestal trap ran its box FROM the bore axis
    away from it. A hex spans ac = AF*2/sqrt(3) (6.35 for M3, not 5.5) along the
    run, so the nut could only ever reach axis + 3.175 -- a 3.175 mm miss on a
    1.5 mm thread radius. The screw could NEVER catch the nut. That "reference
    good" joint was broken as printed, which is why even the chassis's one real
    nut pocket failed. Probe any new trap with a checks.py nut-reach assertion.

    `screw_axis` is 'x'/'y'/'z' or a vector; `open_dir` must be perpendicular to
    it. `seat=False` omits the backstop (slot runs both ways from `center`) for
    the rare pass-through case where another feature does the locating.

    `nib=True` subtracts two wedge volumes from this NEGATIVE, leaving printed
    crush ribs on the AF walls when the caller subtracts the slot from a part.
    Each rib is 0.25 mm proud, runs 1.2 mm, spans the nut thickness, and has a
    45 degree mouth lead-in plus a 60 degree service-extraction back face. The
    back face starts at least nut AC + 0.1 mm from the seat, so the seated nut
    is clear. Nibbed slots require length >= AC + 1.5 mm."""
    axv = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}.get(screw_axis, screw_axis)
    a = np.asarray(axv, float); a /= np.linalg.norm(a)
    o = np.asarray(open_dir, float); o /= np.linalg.norm(o)
    if abs(np.dot(a, o)) > 1e-6:
        raise ValueError("nut_slot(): open_dir must be perpendicular to screw_axis")
    af, nut_t = NUT[size]
    back = nut_ac(size) / 2.0 if seat else length / 2.0
    if length <= back:
        raise ValueError("nut_slot(): length %.2f must exceed the nut seat %.2f"
                         % (length, back))
    if nib and (not seat or length < nut_ac(size) + NUT_NIB_MIN_EXTRA):
        raise ValueError("nut_slot(): nib needs a seated length >= %.2f, got %.2f"
                         % (nut_ac(size) + NUT_NIB_MIN_EXTRA, length))
    b = box(af + c_af, length, nut_t + c_t)      # x=flats, y=slot run, z=screw axis
    T = np.eye(4)
    T[:3, 0] = np.cross(o, a); T[:3, 1] = o; T[:3, 2] = a
    T[:3, 3] = np.asarray(center, float) + o * (length / 2.0 - back)
    b.apply_transform(T)
    if nib:
        y0 = -length / 2.0 + nut_ac(size) + NUT_NIB_SEAT_CLEAR
        y1 = y0 + NUT_NIB_RUN
        back_ramp = NUT_NIB_PROUD / np.tan(np.deg2rad(60.0))
        lead_ramp = NUT_NIB_PROUD
        half_w = (af + c_af) / 2.0
        ribs = []
        for side in (-1.0, 1.0):
            wall = side * half_w
            inner = side * (half_w - NUT_NIB_PROUD)
            poly = sg.Polygon([(wall, y0), (wall, y1),
                               (inner, y1 - lead_ramp),
                               (inner, y0 + back_ramp)])
            rib = extrude_polygon(poly, nut_t + c_t)
            rib.apply_translation((0, 0, -(nut_t + c_t) / 2.0))
            rib.apply_transform(T)
            ribs.append(rib)
        b = sub(b, uni(ribs))
    return b


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


# DIRECT manifold3d booleans IN FLOAT64 END TO END (2026-07-14): trimesh 4.12's
# boolean wrapper (and any float32 mesh roundtrip -- Manifold.to_mesh() returns
# f32!) INJECTED PHANTOM GEOMETRY on complex meshes. Probe-verified: an
# inter(lower, prism) grew a 0.2-thick bulge on a rib face that neither input
# had; the pure Manifold chain (L ^ PR) ^ cube read exactly 0.0 there, while
# re-manifolding the f32 to_mesh() output read 0.016 -- f32 quantization folds
# the boolean's thin facets into macroscopic slivers. Every CSG call routes
# through these three, so they talk to manifold3d directly with Mesh64/
# to_mesh64 and re-wrap with process=False.
import manifold3d as _m3


def _to_man(mesh):
    # np.array(...) not asarray: trimesh hands out TrackedArray subclasses that
    # nanobind's strict ndarray signature rejects; force plain C-ordered arrays.
    # f32 Mesh on purpose: the f64 Mesh64 path produced its own artifacts here
    # (a non-watertight panel + a split deck on this trimesh/manifold combo),
    # while f32 direct gave every part single + watertight. Sub-0.02 mm3 facet
    # residue can survive near coincident faces -- design clearances, not the
    # pipeline, own that margin (keep placeholder gaps >= 0.3).
    return _m3.Manifold(_m3.Mesh(
        vert_properties=np.array(mesh.vertices, dtype=np.float32, order="C", subok=False),
        tri_verts=np.array(mesh.faces, dtype=np.uint32, order="C", subok=False)))


def _from_man(man):
    out = man.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(out.vert_properties)[:, :3],
                           faces=np.asarray(out.tri_verts), process=False)


def sub(a, b):
    return _from_man(_to_man(a) - _to_man(b))


def uni(parts):
    m = _to_man(parts[0])
    for p in parts[1:]:
        m = m + _to_man(p)
    return _from_man(m)


def inter(a, b):
    return _from_man(_to_man(a) ^ _to_man(b))


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


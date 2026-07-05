"""desk-pi -- pan/tilt head assembly around the real 7" touchscreen.

Coordinate system: Z up, robot looks toward +Y (screen glass faces +Y).
Origin (0,0,0) = center of the desk contact plane (later: top of the wheeled chassis).

Kinematic chain (bottom -> top):
    base                 fixed (later bolts onto a wheeled chassis via BASE_BOLT_CIRCLE)
      -> PAN joint       yaw about vertical Z, driven by motor_pan in the base
        -> pan_platform + neck_post + tilt fork  (rotate as one)
          -> TILT joint  pitch about horizontal X, driven by motor_tilt on the fork
            -> head_cradle + screen + camera      (the head)

Tilt is a REAR FORK (two pivots behind the head), not a side gimbal: reads as a neck,
narrow, compatible with wheels later. Cost is a ~CANTILEVER mm forward offset of the
screen CoM from the tilt axis -> small constant gravity torque the tilt motor holds.

Motors are UNDECIDED. motor_* are MG996R-class servo placeholders (see MOTOR params) just
to prove the joints have room. Swap the box dims when the real motor is chosen.

Run:  python3 src/build.py            -> web/assembly.glb
      EXPORT=1 python3 src/build.py   -> also writes per-part STLs into stl/<subsystem>/
"""
import os
import numpy as np
import trimesh
import shapely.geometry as sg
from trimesh.creation import extrude_polygon
from trimesh.transformations import rotation_matrix as R

from stlpaths import webpath, stlp

TAU = 2 * np.pi           # full turn (was wrongly set to pi; fixed in the screen-orientation pass)
DEG = np.pi / 180.0

# ---------------------------------------------------------------------------
# PARAMETERS (mm). Every value carries the reason it is what it is.
# ---------------------------------------------------------------------------
P = {
    # --- Real 7" touchscreen module, MEASURED from the reference STL bbox ---
    "screen_w": 193.0,      # width  (X)
    "screen_d": 25.0,       # depth  (Y) incl. driver board bump on the back
    "screen_h": 110.8,      # height (Z)
    "screen_ref_stl": "reference/rpi-7in-touchscreen-model/files/"
                      "Raspberry_Pi_Touch_Screen_Assembly_v12.stl",
    "screen_flip": True,    # glass faced -Y (into the head); 180 about X faces it +Y (front)

    # --- Head shell: SIMPLE rounded box (a clean tablet-head; screen upright on the front) ---
    "head_wall": 4.0,
    "head_w": 205.0,        # shell outer width (screen 193 + walls + margin)
    "face_angle": 0.0,      # upright front face (the neck's tilt gives the look-up/down)
    "body_front_y": 31.0,   # front face plane (glass sits flush here)
    "body_back_y": -31.0,   # back face plane (behind the tilt axis; Pi bay)
    "body_z_bot": 113.0,    # shell bottom height above desk
    "body_z_top": 243.0,    # shell top height
    "corner_r": 16.0,       # rounded vertical edges (friendly, clean)
    "bezel_overlap": 3.5,   # front lip over the screen edge (retains the module)
    "screen_clear": 0.5,    # clearance around the module in its pocket
    "bezel_back": 4.0,      # split plane sits this far behind the screen back

    # --- Tilt joint: REAR CLEVIS entering the shell underside; axle near the CoM ---
    "tilt_axis_z": 178.0,   # tilt axis height above the desk (inside the box, near CoM)
    "tilt_cantilever": 18.5,# screen center FORWARD (+Y) of the tilt axis (glass flush w/ front)
    "pivot_boss_r": 10.0,   # head-side pivot boss radius (internal side walls)
    "pivot_bore_r": 3.1,    # M6 axle / servo horn bore
    "clevis_half": 22.0,    # neck cheek half-span (cheeks at +-22 in X)
    "cheek_t": 8.0,         # clevis cheek thickness (X)

    # --- Neck column (carries the clevis, rides the pan platform) ---
    "neck_w": 48.0,         # column width (X) -- squarer + rounded reads as a neck, not a plank
    "neck_d": 46.0,         # column depth (Y)
    "neck_round": 10.0,     # corner rounding radius
    "neck_top_z": 150.0,    # where the column stops and the clevis cheeks rise
    "neck_y": -38.0,        # column sits behind the head

    # --- Pan joint + platform ---
    "pan_plate_d": 96.0,    # rotating platform diameter (sits on the base slew ring)
    "pan_plate_t": 8.0,
    "pan_bore_r": 4.2,      # pan axle / motor shaft bore

    # --- Tank-tread chassis: central body + two side track pods (mobile base) ---
    "base_h": 52.0,         # body top = pan-mount plane (keeps the neck/head at the same height)
    "chassis_w": 130.0,     # body width between the tracks (X)
    "chassis_l": 156.0,     # body length front-back (Y)
    "chassis_clear": 7.0,   # ground clearance under the body
    "track_r": 30.0,        # drive/idler wheel radius
    "track_belt": 5.0,      # belt thickness wrapping the wheels
    "track_width": 30.0,    # track thickness (X)
    "track_wheelbase": 132.0,   # front idler <-> rear drive wheel spacing (Y)
    "track_gap": 4.0,       # body side <-> track inner face

    # --- Motor placeholder: 28BYJ-48 5V geared stepper (owned x6, + ULN2003 x9). ---
    "motor_d": 28.0,        # motor can diameter
    "motor_body_h": 19.0,   # can height
    "motor_gear_h": 9.0,    # gearbox stack in front of the can
    "motor_shaft_off": 8.0, # output shaft offset from the can axis (28BYJ-48 quirk)
    "motor_shaft_d": 5.0,

    # --- Reference electronics (visual, for fit) ---
    "cam_w": 25.0, "cam_h": 24.0, "cam_d": 12.0,   # Camera Module 3 board
    "pi_w": 85.0, "pi_h": 56.0, "pi_t": 18.0,      # Raspberry Pi 5 board footprint
    "pi_hole_dx": 58.0, "pi_hole_dy": 49.0,        # Pi 5 mount-hole pattern (M2.5)
    "pi_y_in_head": -16.0,  # Pi board-center Y in the head (behind the tilt axis, standoff room)

    # --- Fastening: M3 screws into CAPTIVE HEX NUTS (user choice) ---
    "m3_clear_r": 1.75,     # M3 screw clearance
    "m3_nut_af": 5.7,       # M3 hex nut across-flats (+ clearance)
    "m3_nut_h": 2.8,        # nut pocket depth
    "boss_r": 4.3,          # screw boss outer radius
    "m25_clear_r": 1.45,    # M2.5 clearance (Pi standoffs)
    "uln_w": 35.0, "uln_h": 32.0,   # ULN2003 driver board footprint

    # --- Preview pose (view only; does NOT change printed geometry) ---
    "preview_pan_deg": 22.0,
    "preview_tilt_deg": -12.0,   # negative = look slightly down at a seated user
}

EXPORT = os.environ.get("EXPORT") == "1"

COLORS = {
    "screen":  [26, 30, 38, 255],
    "cradle":  [188, 196, 210, 255],
    "back":    [150, 158, 172, 255],
    "neck":    [120, 140, 172, 255],
    "fork":    [120, 140, 172, 255],
    "pan":     [150, 156, 168, 255],
    "base":    [92, 98, 116, 255],
    "track":   [48, 50, 58, 255],
    "motor":   [232, 126, 74, 255],
    "camera":  [214, 92, 92, 255],
    "pi":      [56, 150, 96, 255],
    "axle":    [40, 40, 46, 255],
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


def sub(a, b):
    return trimesh.boolean.difference([a, b], engine="manifold")


def uni(parts):
    return trimesh.boolean.union(parts, engine="manifold")


# ---------------------------------------------------------------------------
# Reference screen (loaded, recentered, oriented so glass faces +Y)
# ---------------------------------------------------------------------------
def load_screen():
    m = trimesh.load(P["screen_ref_stl"], force="mesh")
    m.apply_translation(-m.bounding_box.centroid)   # center at origin
    # STL axes already match ours (X=width, Y=depth, Z=height). A 180deg YAW (about Z) turns
    # the glass to face +Y without laying the panel down or flipping top/bottom.
    if P["screen_flip"]:
        m.apply_transform(R(TAU / 2, (0, 0, 1)))
    _color(m, "screen")
    return m


# ---------------------------------------------------------------------------
# Printed parts (built at neutral pose, in world coords)
# ---------------------------------------------------------------------------
def _head_solid(inset=0.0):
    """Simple rounded box head: rounded vertical edges, flat top/bottom. World coords.

    inset>0 shrinks it inward (for hollowing to a uniform wall).
    """
    d = inset
    w = P["head_w"] - 2 * d
    fy, by = P["body_front_y"] - d, P["body_back_y"] + d
    r = max(P["corner_r"] - d, 1.0)
    poly = sg.box(-w / 2, by, w / 2, fy).buffer(-r, join_style=1).buffer(r, join_style=1)
    h = (P["body_z_top"] - P["body_z_bot"]) - 2 * d
    solid = extrude_polygon(poly, h)          # XY footprint (width x depth), extruded +Z
    solid.apply_translation((0, 0, P["body_z_bot"] + d))
    return solid


def screen_pose():
    """Transform placing the recentered screen onto the leaned front face."""
    zt = P["tilt_axis_z"]
    tilt = R(P["face_angle"] * DEG, (1, 0, 0), (0, 0, zt))   # lean top back
    trans = np.eye(4)
    trans[:3, 3] = (0, P["tilt_cantilever"], zt)
    return tilt @ trans


def build_head_shell():
    """Alexa/Echo-Show wedge shell: rounded body, leaned front holding the 7" screen."""
    zt = P["tilt_axis_z"]
    shell = _head_solid()

    # hollow it (leave uniform walls), opening kept via the back cavity below
    inner = _head_solid(inset=P["head_wall"])
    shell = sub(shell, inner)

    # stepped screen aperture: full-size POCKET behind (module drops in) + a smaller front
    # WINDOW that pierces the face, leaving a lip that retains the glass edge.
    ov, cl = P["bezel_overlap"], P["screen_clear"]
    pocket = box(P["screen_w"] + 2 * cl, 40.0, P["screen_h"] + 2 * cl)
    pocket.apply_transform(screen_pose() @ _T(0, -8, 0))     # around/behind the screen
    shell = sub(shell, pocket)
    window = box(P["screen_w"] - 2 * ov, 60.0, P["screen_h"] - 2 * ov)
    window.apply_transform(screen_pose() @ _T(0, 20, 0))     # pierce the front face -> lip
    shell = sub(shell, window)

    # small rear cable port (main electronics access is by removing the front bezel)
    cable_port = box(48, 30.0, 34.0)
    cable_port.apply_translation((0, P["body_back_y"], P["body_z_bot"] + 42))
    shell = sub(shell, cable_port)

    # Pi I/O access slot in the back wall (USB-C / HDMI / USB along the Pi's bottom edge)
    io = box(64, 30.0, 16.0)
    io.apply_translation((0, P["body_back_y"], zt - P["pi_h"] / 2 + 6))
    shell = sub(shell, io)
    # ventilation louvres high on the back wall (Pi 5 runs hot)
    for i in range(-2, 3):
        louvre = box(50, 30.0, 4.0)
        louvre.apply_translation((0, P["body_back_y"], zt + 18 + i * 8))
        shell = sub(shell, louvre)

    # bottom-rear slot so the neck clevis can rise into the body and reach the axle
    slot = box(2 * (P["clevis_half"] + P["cheek_t"]) + 12, 60.0, 90.0)
    slot.apply_translation((0, P["body_back_y"] + 22, P["body_z_bot"] + 22))
    shell = sub(shell, slot)

    # pivot hubs at the side walls, on the tilt axis (fuse through the wall, behind the bezel)
    bx = P["head_w"] / 2 - 8
    bosses = []
    for sx in (-1, 1):
        b = cyl(P["pivot_boss_r"] + 3, 24.0, axis="x")   # spans past the outer wall to fuse
        b.apply_translation((sx * bx, 0, zt))
        bosses.append(b)
    shell = uni([shell] + bosses)
    # full-width axle bore through both side-wall bosses
    axle_bore = cyl(P["pivot_bore_r"], P["head_w"] + 10, axis="x")
    axle_bore.apply_translation((0, 0, zt))
    shell = sub(shell, axle_bore)
    # bushing counterbore at each hub (press-fit Ø8 bushing so PLA isn't the running surface)
    for sx in (-1, 1):
        cb = cyl(4.0, 6.0, axis="x")
        cb.apply_translation((sx * (P["head_w"] / 2 - 3), 0, zt))
        shell = sub(shell, cb)

    # camera bump: small nub on the top bezel with a lens through-hole (board pocket behind)
    cam_boss = box(30, 14, 20)
    cam_boss.apply_transform(screen_pose() @ _T(0, 5, P["screen_h"] / 2 + 3))
    shell = uni([shell, cam_boss])
    lens = cyl(4.5, 40, axis="y")          # bored along the face normal after screen_pose
    lens.apply_transform(screen_pose() @ _T(0, 0, P["screen_h"] / 2 + 3))
    shell = sub(shell, lens)

    _color(shell, "cradle")
    shell.metadata["name"] = "head_shell"
    return shell


def _face_normal():
    n = screen_pose()[:3, :3] @ np.array([0, 1.0, 0])
    return n / np.linalg.norm(n)


def _split_origin():
    """A point on the split plane: behind the screen back, parallel to the front face."""
    c = screen_pose()[:3, 3]
    return c - (P["screen_d"] / 2 + P["bezel_back"]) * _face_normal()


def _bezel_boss_points():
    """Perimeter fixing points, in the screen-local frame, on the split plane."""
    hw, hh = P["screen_w"] / 2 + 6, P["screen_h"] / 2 + 5
    ys = -(P["screen_d"] / 2 + P["bezel_back"])   # split plane in screen-local Y
    return [(0, ys, hh), (0, ys, -hh),
            (-hw, ys, hh * 0.45), (hw, ys, hh * 0.45),
            (-hw, ys, -hh * 0.55), (hw, ys, -hh * 0.55)]


def build_head_parts():
    """Split the wedge into a FRONT bezel (holds + retains the screen, camera nub) and a
    BACK cover (pivot hubs, neck slot, Pi bay, cable port). M3 screws from the front thread
    into captive hex nuts in the back-cover bosses."""
    from trimesh.intersections import slice_mesh_plane
    full = build_head_shell()
    n, o = _face_normal(), _split_origin()
    bezel = slice_mesh_plane(full, plane_normal=n, plane_origin=o, cap=True)
    back = slice_mesh_plane(full, plane_normal=-n, plane_origin=o, cap=True)

    # bezel<->back fixing: a boss each side of the split; screw along the face normal; the nut
    # is captive in the back boss, the bezel boss is just clearance.
    sp = screen_pose()
    for lp in _bezel_boss_points():
        w = (sp @ np.append(lp, 1.0))[:3]
        back = uni([back, screw_post(w, -n, 15)])
        bezel = uni([bezel, screw_post(w, n, 11)])
        clr = _orient(cyl(P["m3_clear_r"], 70), n); clr.apply_translation(w)
        bezel = sub(bezel, clr.copy()); back = sub(back, clr.copy())
        nut = hex_prism(P["m3_nut_af"] + 0.3, P["m3_nut_h"])
        nut.apply_translation((0, 0, -6))                # sunk a little inside the back boss
        _orient(nut, n); nut.apply_translation(w)
        back = sub(back, nut)

    # Pi 5 standoffs on the back cover (M2.5), at the 58x49 hole pattern, behind the tilt axis
    zt = P["tilt_axis_z"]
    wall_y = P["body_back_y"] + P["head_wall"]
    board_y = P["pi_y_in_head"] - P["pi_t"] / 2         # board back face
    for sx in (-1, 1):
        for sz in (-1, 1):
            px, pz = sx * P["pi_hole_dx"] / 2, zt + sz * P["pi_hole_dy"] / 2
            so = cyl(3.2, board_y - wall_y, axis="y")
            so.apply_translation((px, (wall_y + board_y) / 2, pz))
            back = uni([back, so])
            pilot = cyl(P["m25_clear_r"], 20, axis="y"); pilot.apply_translation((px, board_y, pz))
            back = sub(back, pilot)

    _color(bezel, "cradle"); bezel.metadata["name"] = "head_bezel"
    _color(back, "back"); back.metadata["name"] = "head_back"
    return bezel, back


def build_neck_clevis():
    """Neck column rising to a two-cheek clevis that grips the tilt axle under the head."""
    zt = P["tilt_axis_z"]
    z0 = P["base_h"]                       # sits on the pan platform / base top (world Z)
    ny = P["neck_y"]
    parts = []

    col_h = P["neck_top_z"] - z0
    col = rounded_box(P["neck_w"], P["neck_d"], col_h, P["neck_round"])
    col.apply_translation((0, ny, z0))       # extrude_polygon is z=0..h, so lift to z0
    parts.append(col)

    # two cheeks rising from the column top forward-and-up to the axle at (0,0,zt)
    for sx in (-1, 1):
        cx = sx * P["clevis_half"]
        top = np.array([cx, 0.0, zt])
        bot = np.array([cx, ny, P["neck_top_z"]])
        mid = (top + bot) / 2
        length = np.linalg.norm(top - bot)
        cheek = box(P["cheek_t"], 20.0, length + 20)
        d = (top - bot) / length
        v = np.cross([0, 0, 1.0], d); s = np.linalg.norm(v)
        if s > 1e-6:
            cheek.apply_transform(R(np.arctan2(s, np.dot([0, 0, 1.0], d)), v / s))
        cheek.apply_translation(mid)
        parts.append(cheek)

    # tilt-motor mount plate on the +X cheek (28BYJ-48: shaft-through + 2 ears at 35mm)
    plate = box(4.0, 44.0, 44.0)
    plate.apply_translation((P["clevis_half"] + P["cheek_t"] / 2 + 2, 0, zt))
    parts.append(plate)

    neck = uni(parts)
    bore = cyl(P["pivot_bore_r"] + 0.4, 2 * P["clevis_half"] + 4 * P["cheek_t"], axis="x")
    bore.apply_translation((0, 0, zt))
    neck = sub(neck, bore)
    # tilt-motor shaft clearance + 2 M3 ear holes through the mount plate
    px = P["clevis_half"] + P["cheek_t"] / 2 + 2
    shaft_hole = cyl(4.0, 30, axis="x"); shaft_hole.apply_translation((px, 0, zt))
    neck = sub(neck, shaft_hole)
    for dz in (-17.5, 17.5):
        ear = cyl(P["m3_clear_r"], 30, axis="x"); ear.apply_translation((px, 0, zt + dz))
        neck = sub(neck, ear)
    # vertical cable channel down the column (cables drop from the hollow axle into the base)
    chan = cyl(6.0, P["neck_top_z"] - z0 + 30)
    chan.apply_translation((0, ny, (z0 + P["neck_top_z"]) / 2))
    neck = sub(neck, chan)
    # 3 M3 pilots in the column base to bolt the neck down to the pan platform
    for a in (90, 210, 330):
        rad = 16.0
        hx = rad * np.cos(np.radians(a)); hy = ny + rad * np.sin(np.radians(a))
        pilot = cyl(P["m3_clear_r"], 24); pilot.apply_translation((hx, hy, z0 + 10))
        neck = sub(neck, pilot)
    _color(neck, "neck")
    neck.metadata["name"] = "neck_clevis"
    return neck


def _T(x, y, z):
    m = np.eye(4); m[:3, 3] = (x, y, z); return m


def build_pan_platform():
    # seated on top of the base (world Z), flush with the base top
    zc = P["base_h"] - P["pan_plate_t"] / 2
    plate = cyl(P["pan_plate_d"] / 2, P["pan_plate_t"], sections=96)
    plate.apply_translation((0, 0, zc))
    bore = cyl(P["pan_bore_r"], 40.0)
    bore.apply_translation((0, 0, zc))
    plate = sub(plate, bore)
    cable = cyl(6.0, 40.0)                    # off-axis cable pass (aligns with neck channel)
    cable.apply_translation((0, P["neck_y"], zc))
    plate = sub(plate, cable)
    # 3 M3 clearance holes to bolt the neck down (match neck-base pilots)
    for a in (90, 210, 330):
        rad = 16.0
        hx = rad * np.cos(np.radians(a)); hy = P["neck_y"] + rad * np.sin(np.radians(a))
        h = cyl(P["m3_clear_r"], 40.0); h.apply_translation((hx, hy, zc))
        plate = sub(plate, h)
    _color(plate, "pan")
    plate.metadata["name"] = "pan_platform"
    return plate


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


def build_base():
    """Tank chassis BODY: hollow rounded box between the tracks. Top = pan-mount plane; houses
    the pan motor + driver + wiring. (Track pods are build_tracks.)"""
    wall, floor = 5.0, 5.0
    z0, z1 = P["chassis_clear"], P["base_h"]          # body spans clearance..pan-mount
    h = z1 - z0
    body = rounded_box(P["chassis_w"], P["chassis_l"], h, 14.0)
    body.apply_translation((0, 0, z0))
    cav = rounded_box(P["chassis_w"] - 2 * wall, P["chassis_l"] - 2 * wall, h - floor, 12.0)
    cav.apply_translation((0, 0, z0 + floor))
    body = sub(body, cav)
    # pan platform seat + shaft bore + off-axis cable pass
    seat = cyl(P["pan_plate_d"] / 2 + 1.0, 6.0, sections=96)
    seat.apply_translation((0, 0, z1 - 3.0)); body = sub(body, seat)
    pbore = cyl(P["pan_bore_r"] + 0.6, 200); pbore.apply_translation((0, 0, z1)); body = sub(body, pbore)
    cbl = cyl(6.0, 200); cbl.apply_translation((0, P["neck_y"], z0)); body = sub(body, cbl)

    # interior fittings: pan-motor pad + ULN2003 standoffs
    mx = -P["motor_shaft_off"]
    adds = [box(46, 12, 6)]; adds[0].apply_translation((mx, 0, z0 + floor + 3))
    for sx in (-1, 1):
        for sy in (-1, 1):
            b = cyl(3.0, 8); b.apply_translation((38 + sx * P["uln_w"] / 2, sy * P["uln_h"] / 2, z0 + floor))
            adds.append(b)
    body = uni([body] + adds)
    for dy in (-17.5, 17.5):                          # 28BYJ-48 ear pilots
        e = cyl(P["m3_clear_r"], 20); e.apply_translation((mx, dy, z0 + floor + 3))
        body = sub(body, e)
    usb = box(14, 12, 8)                              # USB-C power entry in the rear wall
    usb.apply_translation((0, -P["chassis_l"] / 2, z0 + 12)); body = sub(body, usb)
    for i in range(-3, 4):                            # side ventilation slots
        v = box(12, 5, 16); v.apply_translation((0, i * 16, z0 + h / 2))
        v2 = v.copy(); v.apply_translation((P["chassis_w"] / 2, 0, 0)); v2.apply_translation((-P["chassis_w"] / 2, 0, 0))
        body = sub(sub(body, v), v2)
    _color(body, "base")
    body.metadata["name"] = "chassis"
    return body


def build_tracks():
    """Two tank track pods (stadium belt loops + hub caps), flanking the chassis body."""
    r, bt, tw = P["track_r"], P["track_belt"], P["track_width"]
    wb = P["track_wheelbase"]
    zc = r + bt                                       # wheel-center height (belt outer touches z=0)
    parts = []
    for sx in (-1, 1):
        cx = sx * (P["chassis_w"] / 2 + P["track_gap"] + tw / 2)
        line = sg.LineString([(-wb / 2, zc), (wb / 2, zc)])   # in (Y, Z)
        band = line.buffer(r + bt).difference(line.buffer(r - 8))
        solid = extrude_polygon(band, tw)             # poly(Y,Z) extruded +Z(=X) by tw
        M = np.array([[0, 0, 1, cx - tw / 2], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)
        solid.apply_transform(M)
        # hub caps on the outer face at each wheel centre
        for wy in (-wb / 2, wb / 2):
            hub = cyl(r - 9, 4, axis="x")
            hub.apply_translation((cx + sx * (tw / 2 + 1), wy, zc))
            solid = uni([solid, hub])
        _color(solid, "track")
        solid.metadata["name"] = "track_L" if sx < 0 else "track_R"
        parts.append(solid)
    return parts


def motor_28byj(name):
    """28BYJ-48 stepper placeholder: can + gearbox + offset output shaft, shaft along +Z."""
    r = P["motor_d"] / 2
    can = cyl(r, P["motor_body_h"])
    can.apply_translation((0, 0, P["motor_body_h"] / 2))
    gear = cyl(r, P["motor_gear_h"])
    gear.apply_translation((0, 0, P["motor_body_h"] + P["motor_gear_h"] / 2))
    top = P["motor_body_h"] + P["motor_gear_h"]
    shaft = cyl(P["motor_shaft_d"] / 2, 10.0)
    shaft.apply_translation((P["motor_shaft_off"], 0, top + 5))
    tab = box(42, 7, 2.0)          # mounting ears (holes omitted for the placeholder)
    tab.apply_translation((0, 0, top - 1))
    m = uni([can, gear, shaft, tab])
    _color(m, "motor")
    m.metadata["name"] = name
    return m


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def build():
    scene = trimesh.Scene()
    zt = P["tilt_axis_z"]

    # pose + output overrides (for generating review render sets)
    pan_deg = float(os.environ.get("PAN", P["preview_pan_deg"]))
    tilt_deg = float(os.environ.get("TILT", P["preview_tilt_deg"]))
    head_name = "head_wedge" if os.environ.get("SOLIDHEAD") == "1" else "head_shell"
    out_name = os.environ.get("OUT", "assembly.glb")

    # transforms
    pan = R(pan_deg * DEG, (0, 0, 1), (0, 0, 0))
    tilt = R(tilt_deg * DEG, (1, 0, 0), (0, 0, zt))
    M_head = pan @ tilt          # head parts: tilt then pan
    M_pan = pan                  # pan-group parts

    def add(mesh, M, export_name=None):
        g = mesh.copy()
        g.apply_transform(M)
        scene.add_geometry(g, node_name=mesh.metadata["name"])
        if EXPORT and export_name:
            mesh.export(stlp(export_name))

    # --- FIXED: tank chassis body + two track pods ---
    add(build_base(), np.eye(4), "chassis.stl")
    for trk in build_tracks():
        add(trk, np.eye(4), trk.metadata["name"] + ".stl")

    # --- PAN GROUP ---
    add(build_pan_platform(), M_pan, "pan_platform.stl")

    neck = build_neck_clevis()                       # already built in world Z (sits on base top)
    scene_neck = neck.copy(); scene_neck.apply_transform(M_pan)
    scene.add_geometry(scene_neck, node_name="neck_clevis")
    if EXPORT:
        neck.export(stlp("neck_clevis.stl"))

    # tilt motor: 28BYJ-48 on the +X clevis cheek, shaft (+Z) rotated to point -X at the axle
    mt = motor_28byj("motor_tilt")
    mt.apply_transform(R(-TAU / 4, (0, 1, 0)))       # shaft +Z -> -X
    mt.apply_translation((P["clevis_half"] + 34, 0, zt))
    add(mt, M_pan)

    # Pi 5 in the HEAD, behind the tilt axis: the DSI + CSI ribbons then stay entirely in the head
    # (zero joint crossings), and the board doubles as the tilt counterweight. Board plane = XZ.
    pi = box(P["pi_w"], P["pi_t"], P["pi_h"]); _color(pi, "pi"); pi.metadata["name"] = "pi5"
    pi.apply_translation((0, P["pi_y_in_head"], zt))
    add(pi, M_head)

    # pan motor: 28BYJ-48 upright in the base, offset so its shaft lands on the pan axis
    mp = motor_28byj("motor_pan")
    mp.apply_translation((-P["motor_shaft_off"], 0,
                          P["base_h"] - 2 - (P["motor_body_h"] + P["motor_gear_h"])))
    add(mp, np.eye(4))

    # --- HEAD (tilt + pan): split into front bezel + back cover ---
    bezel, back = build_head_parts()
    add(bezel, M_head, "head_bezel.stl")
    add(back, M_head, "head_back.stl")

    screen = load_screen()
    screen.apply_transform(screen_pose())            # sit on the leaned front face
    screen.metadata["name"] = "screen_ref"
    add(screen, M_head)

    # camera in the top bezel bump, lens along the face normal
    cam = box(P["cam_w"], P["cam_d"], P["cam_h"]); _color(cam, "camera")
    cam.metadata["name"] = "camera_ref"
    cam.apply_transform(screen_pose() @ _T(0, P["screen_d"] / 2 + 1, P["screen_h"] / 2 + 3))
    add(cam, M_head)

    # HOLLOW tilt axle (tube): cables pass through it on-axis (no length change when tilting)
    axle = sub(cyl(3.0, P["head_w"] + 4, axis="x"), cyl(2.0, P["head_w"] + 8, axis="x"))
    _color(axle, "axle"); axle.metadata["name"] = "tilt_axle"
    axle.apply_translation((0, 0, zt))
    add(axle, M_pan)

    out = webpath(out_name)
    scene.export(out)
    print(f"wrote {out}  ({len(scene.geometry)} parts)")
    if EXPORT:
        print("exported per-part STLs into stl/")


if __name__ == "__main__":
    build()

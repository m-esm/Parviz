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

TAU = np.pi
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
    "screen_flip": False,   # flip 180 about Z if glass ends up facing -Y (verify by render)

    # --- Head shell: ALEXA / Echo-Show "doorstop" wedge (see reference/alexa-style-*) ---
    # Rounded box body with the front face leaning back; the 7" screen mounts on that face.
    "head_wall": 4.0,
    "head_w": 205.0,        # shell outer width (screen 193 + walls + margin)
    "face_angle": 11.0,     # front face lean from vertical (deg); Echo-Show resting angle
    "body_back_y": -35.0,   # back face plane (behind the tilt axis)
    "body_front_bot_y": 52.0,   # front face, bottom edge (furthest forward)
    "body_front_top_y": 26.0,   # front face, top edge (leaned back)
    "body_z_bot": 113.0,    # shell bottom height above desk
    "body_z_top": 243.0,    # shell top (front) height
    "body_back_top_z": 210.0,   # back is shorter than the front (the wedge)
    "corner_r": 16.0,       # side-profile corner rounding (the friendly Echo-Show look)

    # --- Tilt joint: REAR CLEVIS entering the shell underside; axle near the CoM ---
    "tilt_axis_z": 178.0,   # tilt axis height above the desk (inside the box, near CoM)
    "tilt_cantilever": 39.0,# screen face-center sits this far FORWARD (+Y) of the tilt axis
    "pivot_boss_r": 10.0,   # head-side pivot boss radius (internal side walls)
    "pivot_bore_r": 3.1,    # M6 axle / servo horn bore
    "clevis_half": 22.0,    # neck cheek half-span (cheeks at +-22 in X)
    "cheek_t": 8.0,         # clevis cheek thickness (X)

    # --- Neck column (carries the clevis, rides the pan platform) ---
    "neck_w": 50.0,         # column width (X)
    "neck_d": 34.0,         # column depth (Y)
    "neck_top_z": 150.0,    # where the column stops and the clevis cheeks rise
    "neck_y": -38.0,        # column sits behind the head

    # --- Pan joint + platform ---
    "pan_plate_d": 96.0,    # rotating platform diameter (sits on the base slew ring)
    "pan_plate_t": 8.0,
    "pan_bore_r": 4.2,      # pan axle / motor shaft bore

    # --- Base (fixed). Bottom face is the future-wheels mounting flange. ---
    "base_d": 150.0,        # wide for tip stability with the head extended
    "base_h": 46.0,         # houses pan motor + slew bearing + Pi power
    "base_bolt_circle": 120.0,  # M4 bolt circle to later bolt onto a wheeled chassis
    "base_bolt_r": 2.2,     # M4 clearance
    "base_bolt_n": 4,

    # --- Motor placeholders (MG996R-class servo). UNDECIDED -- swap when chosen. ---
    "motor_l": 40.7, "motor_w": 19.7, "motor_h": 42.9,

    # --- Reference electronics (visual, for fit) ---
    "cam_w": 25.0, "cam_h": 24.0, "cam_d": 12.0,   # Camera Module 3 board
    "pi_w": 85.0, "pi_h": 56.0, "pi_t": 18.0,      # Raspberry Pi 5 board footprint

    # --- Preview pose (view only; does NOT change printed geometry) ---
    "preview_pan_deg": 22.0,
    "preview_tilt_deg": -12.0,   # negative = look slightly down at a seated user
}

EXPORT = os.environ.get("EXPORT") == "1"

COLORS = {
    "screen":  [26, 30, 38, 255],
    "cradle":  [188, 196, 210, 255],
    "neck":    [120, 140, 172, 255],
    "fork":    [120, 140, 172, 255],
    "pan":     [150, 156, 168, 255],
    "base":    [92, 98, 116, 255],
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
        m.apply_transform(R(TAU / 2, (0, 1, 0)))
    elif axis == "y":
        m.apply_transform(R(TAU / 2, (1, 0, 0)))
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
    # STL axes already match ours (X=width, Y=depth, Z=height); optional 180 flip in Z.
    if P["screen_flip"]:
        m.apply_transform(R(TAU / 2, (0, 0, 1)))
    _color(m, "screen")
    return m


# ---------------------------------------------------------------------------
# Printed parts (built at neutral pose, in world coords)
# ---------------------------------------------------------------------------
def _wedge_solid(inset=0.0):
    """The Echo-Show side profile (Y-Z), rounded, extruded across the width (X).

    inset>0 shrinks the profile inward (for hollowing). Built in world coords.
    """
    d = inset
    pts = [
        (P["body_back_y"] + d,      P["body_z_bot"] + d),   # back-bottom
        (P["body_front_bot_y"] - d, P["body_z_bot"] + d),   # front-bottom
        (P["body_front_top_y"] - d, P["body_z_top"] - d),   # front-top (leaned back)
        (P["body_back_y"] + d,      P["body_back_top_z"] - d),  # back-top (shorter)
    ]
    r = max(P["corner_r"] - d, 1.0)
    poly = sg.Polygon(pts).buffer(-r, join_style=1).buffer(r, join_style=1)
    w = P["head_w"] - 2 * d
    solid = extrude_polygon(poly, w)          # poly in XY, extruded along +Z by w
    # remap: local (X=our Y, Y=our Z, Z=our width) -> world (X=width, Y, Z)
    M = np.array([[0, 0, 1, -w / 2],
                  [1, 0, 0, 0],
                  [0, 1, 0, 0],
                  [0, 0, 0, 1]], dtype=float)
    solid.apply_transform(M)
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
    shell = _wedge_solid()

    # hollow it (leave uniform walls), opening kept via the back cavity below
    inner = _wedge_solid(inset=P["head_wall"])
    shell = sub(shell, inner)

    # screen aperture through the front face: a box at the screen pose, punched outward
    ap = box(P["screen_w"] + 3, 60.0, P["screen_h"] + 3)
    ap.apply_transform(screen_pose() @ _T(0, 20, 0))   # extend toward +Y to pierce the face
    shell = sub(shell, ap)

    # rear service opening (access to electronics / cable exit)
    back_open = box(P["head_w"] - 60, 30.0, 80.0)
    back_open.apply_translation((0, P["body_back_y"], zt))
    shell = sub(shell, back_open)

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

    # camera bump at the top of the front bezel
    cam_boss = box(P["cam_w"] + 12, 16.0, P["cam_h"] + 12)
    cam_boss.apply_transform(screen_pose() @ _T(0, 6, P["screen_h"] / 2 + 12))
    shell = uni([shell, cam_boss])

    _color(shell, "cradle")
    shell.metadata["name"] = "head_shell"
    return shell


def build_neck_clevis():
    """Neck column rising to a two-cheek clevis that grips the tilt axle under the head."""
    zt = P["tilt_axis_z"]
    z0 = P["pan_plate_t"]
    ny = P["neck_y"]
    parts = []

    col_h = P["neck_top_z"] - z0
    col = box(P["neck_w"], P["neck_d"], col_h)
    col.apply_translation((0, ny, z0 + col_h / 2))
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

    neck = uni(parts)
    bore = cyl(P["pivot_bore_r"] + 0.4, 2 * P["clevis_half"] + 4 * P["cheek_t"], axis="x")
    bore.apply_translation((0, 0, zt))
    neck = sub(neck, bore)
    _color(neck, "neck")
    neck.metadata["name"] = "neck_clevis"
    return neck


def _T(x, y, z):
    m = np.eye(4); m[:3, 3] = (x, y, z); return m


def build_pan_platform():
    plate = cyl(P["pan_plate_d"] / 2, P["pan_plate_t"], sections=96)
    plate.apply_translation((0, 0, P["pan_plate_t"] / 2))
    bore = cyl(P["pan_bore_r"], 40.0)
    plate = sub(plate, bore)
    _color(plate, "pan")
    plate.metadata["name"] = "pan_platform"
    return plate


def build_base():
    """Fixed base. Slew seat on top, motor cavity, bottom = future-wheels bolt flange."""
    body = cyl(P["base_d"] / 2, P["base_h"], sections=96)
    body.apply_translation((0, 0, P["base_h"] / 2))
    # recess for the pan platform to sit into (visual seat)
    seat = cyl(P["pan_plate_d"] / 2 + 1.0, 6.0, sections=96)
    seat.apply_translation((0, 0, P["base_h"] - 3.0))
    body = sub(body, seat)
    # central pan bore
    body = sub(body, cyl(P["pan_bore_r"] + 0.6, P["base_h"] + 10))
    # future-wheels bolt circle through the bottom flange
    for i in range(P["base_bolt_n"]):
        a = i * (2 * TAU / P["base_bolt_n"]) + TAU / 8
        x = np.cos(a) * P["base_bolt_circle"] / 2
        y = np.sin(a) * P["base_bolt_circle"] / 2
        hole = cyl(P["base_bolt_r"], P["base_h"] + 10)
        hole.apply_translation((x, y, 0))
        body = sub(body, hole)
    _color(body, "base")
    body.metadata["name"] = "base"
    return body


def motor_box(name):
    m = box(P["motor_l"], P["motor_w"], P["motor_h"])
    _color(m, "motor")
    m.metadata["name"] = name
    return m


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def build():
    scene = trimesh.Scene()
    zt = P["tilt_axis_z"]

    # transforms
    pan = R(P["preview_pan_deg"] * DEG, (0, 0, 1), (0, 0, 0))
    tilt = R(P["preview_tilt_deg"] * DEG, (1, 0, 0), (0, 0, zt))
    M_head = pan @ tilt          # head parts: tilt then pan
    M_pan = pan                  # pan-group parts

    def add(mesh, M, export_name=None):
        g = mesh.copy()
        g.apply_transform(M)
        scene.add_geometry(g, node_name=mesh.metadata["name"])
        if EXPORT and export_name:
            mesh.export(stlp(export_name))

    # --- FIXED ---
    add(build_base(), np.eye(4), "base.stl")

    # --- PAN GROUP ---
    add(build_pan_platform(), M_pan, "pan_platform.stl")

    neck = build_neck_clevis()
    neck.apply_translation((0, 0, P["base_h"]))     # lift onto the base
    scene_neck = neck.copy(); scene_neck.apply_transform(M_pan)
    scene.add_geometry(scene_neck, node_name="neck_clevis")
    if EXPORT:
        neck.export(stlp("neck_clevis.stl"))

    # tilt motor: on the +X clevis cheek, shaft toward -X into the axle
    mt = motor_box("motor_tilt")
    mt.apply_transform(R(TAU / 4, (0, 0, 1)))        # long axis -> X
    mt.apply_translation((P["clevis_half"] + P["motor_l"] / 2 + 4, 0, zt))
    add(mt, M_pan)

    # Pi 5 in the BASE (kept low: kills tilt torque + keeps the head shell light)
    pi = box(P["pi_w"], P["pi_h"], P["pi_t"]); _color(pi, "pi"); pi.metadata["name"] = "pi5"
    pi.apply_translation((0, 0, P["base_h"] - P["pi_t"] / 2 - 3))
    add(pi, np.eye(4))

    # pan motor: standing in the base, shaft up into the platform
    mp = motor_box("motor_pan")
    mp.apply_translation((0, P["base_d"] / 4, P["base_h"] - P["motor_h"] / 2 - 2))
    add(mp, np.eye(4))

    # --- HEAD (tilt + pan) ---
    add(build_head_shell(), M_head, "head_shell.stl")

    screen = load_screen()
    screen.apply_transform(screen_pose())            # sit on the leaned front face
    screen.metadata["name"] = "screen_ref"
    add(screen, M_head)

    # camera in the top bezel bump, lens along the face normal
    cam = box(P["cam_w"], P["cam_d"], P["cam_h"]); _color(cam, "camera")
    cam.metadata["name"] = "camera_ref"
    cam.apply_transform(screen_pose() @ _T(0, P["screen_d"] / 2 + 3, P["screen_h"] / 2 + 12))
    add(cam, M_head)

    # thin axle through the tilt joint (visual)
    axle = cyl(P["pivot_bore_r"] - 0.3, P["head_w"] + 4, axis="x")
    _color(axle, "axle"); axle.metadata["name"] = "tilt_axle"
    axle.apply_translation((0, 0, zt))
    add(axle, M_pan)

    out = webpath("assembly.glb")
    scene.export(out)
    print(f"wrote {out}  ({len(scene.geometry)} parts)")
    if EXPORT:
        print("exported per-part STLs into stl/")


if __name__ == "__main__":
    build()

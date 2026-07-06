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
    "bezel_overlap": 3.5,   # front lip = LOCATOR now (glass is held by the 4 factory screws below)
    "screen_clear": 0.5,    # clearance around the module in its pocket
    "bezel_back": 4.0,      # split plane sits this far behind the screen back

    # --- Screen factory mount: 4x M3 into the display's OWN outer case-mount holes ---
    # Measured from Raspberry_Pi_Touch_Screen_Assembly_v12.stl (outer 126.2 x 65.65 pattern),
    # confirmed vs the reference case STL + RPi mechanical drawing. Screen-LOCAL frame (post-flip);
    # apply screen_pose() like _bezel_boss_points. Face plane local Y=+6.53 -> world Y=25.03.
    "scr_mount_pts": [
        (61.61, 6.53, -31.85), (61.61, 6.53, 33.80),
        (-64.59, 6.53, -31.85), (-64.59, 6.53, 33.80),
    ],
    "scr_boss_r": 4.5,      # screw-boss OD 9
    "scr_m3_clear_r": 1.75, # M3 clearance (screw threads into the display's metal back-pan)

    # --- Tilt joint: REAR CLEVIS entering the shell underside; axle near the CoM ---
    #     Self-locking WORM drive (single-start): head holds tilt with the motor de-energized
    #     (no idle current/heat). Pre-balance the head on the axle so the worm barely works.
    "tilt_axis_z": 178.0,   # tilt axis height above the desk (inside the box, near CoM)
    "tilt_cantilever": 18.5,# screen center FORWARD (+Y) of the tilt axis (glass flush w/ front)
    "pivot_boss_r": 10.0,   # head-side pivot boss radius (internal side walls)
    "clevis_half": 22.0,    # neck cheek half-span (cheeks at +-22 in X)
    "cheek_t": 8.0,         # clevis cheek thickness (X)
    # Ø5 tilt axle on 695-2RS bearings (5x13x4, owned x30). Hollow for the Pi power wires.
    "axle_d": 5.0,          # tilt axle outer Ø (rides 695 bores)
    "axle_bore_d": 2.5,     # hollow (power wires cross tilt on-axis; no ribbons cross)
    "brg_od": 13.0,         # 695-2RS outer Ø (press into the head-side hubs)
    "brg_w": 4.0,
    # single-start worm + worm wheel (module 1.25). Wheel keyed to the axle; worm on the motor.
    "worm_module": 1.25,
    "worm_wheel_teeth": 24, # ratio 24:1 (self-locks; fine tilt resolution as a bonus)
    "worm_wheel_w": 8.0,    # face width
    "worm_wheel_x": 14.0,   # wheel sits on the axle just inside the +X cheek
    "worm_od": 10.0,        # worm outer Ø (pitch r ~4)
    "worm_len": 26.0,

    # --- Neck column (carries the clevis, rides the pan platform) ---
    "neck_w": 48.0,         # column width (X) -- squarer + rounded reads as a neck, not a plank
    "neck_d": 46.0,         # column depth (Y)
    "neck_round": 10.0,     # corner rounding radius
    "neck_top_z": 150.0,    # where the column stops and the clevis cheeks rise
    "neck_y": -38.0,        # column sits behind the head

    # --- Pan joint + platform + captured-BB lazy-Susan race (printed) ---
    "pan_plate_d": 96.0,    # rotating platform diameter (rides the lazy-Susan race)
    "pan_plate_t": 8.0,
    "pan_bore_r": 4.2,      # pan motor-shaft clearance in the base
    "pan_race_circle_d": 80.0,  # BB pitch circle (wide stance resists the top-heavy tilt)
    "pan_race_ball_d": 6.0,     # 6 mm airsoft BBs (owned/cheap; quiet, greased)
    "pan_race_w": 12.0,     # race ring radial width
    "pan_race_n": 18,       # balls on the circle

    # --- Tank-tread chassis: central body + two side track pods (mobile base) ---
    "base_h": 52.0,         # body top = pan-mount plane (keeps the neck/head at the same height)
    "chassis_w": 120.0,     # body width between the tracks (X)
    "chassis_l": 156.0,     # body length front-back (Y)
    "chassis_clear": 7.0,   # ground clearance under the body
    "track_gap": 4.0,       # body side <-> track inner face
    # Modular positive-drive track (advancedvb 'Tank track' 3062624 geometry): printed link pads
    # on filament-rod hinge pins, a 12-tooth sprocket meshing the pins -> no slip on a desk.
    "track_wheel_r": 19.0,  # sprocket/idler pitch radius (idler_d 38); belt bottom -> ground
    "track_wheelbase": 120.0,   # sprocket-axis <-> idler-axis (Y)
    "track_width": 28.0,    # link body width (X); sprocket engages the central ~8 mm
    "track_pitch": 10.0,    # link pin-to-pin (reference ~9.8)
    "track_links": 36,      # 36 x 10 = 360 mm loop
    "track_pad_th": 5.0,    # link pad radial thickness
    "track_grouser_h": 1.5, # tread lug (print grousers in TPU or add pads)
    "sprocket_teeth": 12,
    "sprocket_outer_d": 42.0,
    "idler_bore_d": 16.0,   # Ø16 flanged bearing (buy)
    "roadwheel_d": 22.0,    # inner bottom-run support wheels
    "roadwheel_count": 2,
    "idler_slot": 4.0,      # idler Y-slide for tensioning (M3 set-screw lock)
    # TT gearmotor drive placeholder (own 1x; BUY 1 more -> 2 for skid steer; MX1588 drives both)
    "tt_gearbox": (70.0, 22.0, 18.5),   # (len X-ish, w, h) yellow gearbox
    "tt_motor_d": 24.0,     # round motor can on the gearbox
    "tt_shaft_d": 5.4,      # double-D output shaft

    # --- 28BYJ-48 5V geared stepper (owned x6, + ULN2003 x9). Dims from the beckdac SCARA
    #     SCAD model, cross-checked vs the Mouser datasheet (real, not eyeballed). ---
    "motor_can_d": 28.25,   # can (body) diameter
    "motor_body_h": 18.8,   # can height
    "motor_gear_h": 9.0,    # gearbox stack proud of the can face (approx)
    "motor_shaft_off": 7.875,   # output shaft offset from the can axis (the 28BYJ-48 quirk)
    "motor_shaft_d": 4.93,  # round part of the D-shaft (nominal 5)
    "motor_shaft_flat": 3.0,    # across-flats of the double-D (torque key)
    "motor_shaft_len": 9.75,    # shaft protrusion above the can face
    "motor_flat_len": 6.0,  # the flats run the top 6 mm of the shaft
    "motor_boss_d": 9.1,    # raised collar around the shaft base
    "motor_ear_cc": 35.0,   # mounting-ear hole spacing (centered on the can axis)
    "motor_ear_hole_d": 4.2,    # M4 clearance in the ears
    "motor_wbox_w": 14.6,   # blue wiring box (protrudes past the can on one side)
    "motor_wbox_h": 16.7,

    # --- Camera: Pi Camera board (v2.1 ref GrabCAD 1564160 == Cam Module 3 mount). Board and
    #     4-hole pattern are identical across v1/v2/v2.1/v3; size the aperture to the v3 barrel. ---
    "cam_board_w": 25.0,    # X  board width
    "cam_board_h": 23.862,  # Z  board height
    "cam_hole_dx": 21.0,    # mount holes at X = +-10.5
    "cam_hole_z_top": 2.565,   # top hole row Z (from board center)
    "cam_hole_z_bot": -9.935,  # bottom hole row Z
    "cam_lens_dz": 2.47,    # optical axis above board center (X = 0)
    "cam_lens_z": 233.5,    # lens axis height (world Z): low on the forehead, board recessed below
    "cam_aperture_d": 10.0, # nub bore clears the Ø5.75 v3 barrel + 66deg FOV
    "cam_pod_w": 31.0, "cam_pod_h": 31.0, "cam_pod_d": 15.0,   # "eye" pod enclosing the board
    "cam_boss_od": 4.6,     # M2 self-tap boss OD
    "cam_boss_pilot_r": 0.85,  # M2 self-tap pilot Ø1.7
    "cam_m2_clear_r": 1.15, # M2 clearance (cover)
    "cam_ribbon_w": 17.0, "cam_ribbon_t": 2.5,   # CSI ribbon exit slot (pod bottom -> Pi bay)
    "cam_cover_t": 2.0,     # rear board-retaining cover
    "cam_w": 25.0, "cam_h": 23.862, "cam_d": 12.0,   # placeholder board box (visual)
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


def inter(a, b):
    return trimesh.boolean.intersection([a, b], engine="manifold")


def dbore_neg(length, axis="z", clear=0.12):
    """Negative solid for a 28BYJ-48 double-D shaft socket (torque via the flats, not friction).

    A round bore of Ø motor_shaft_d intersected with a slab motor_shaft_flat wide -> the
    familiar D (two arcs + two flats). `clear` loosens it for a snug press in PLA.
    """
    d = P["motor_shaft_d"] + 2 * clear
    flat = P["motor_shaft_flat"] + 2 * clear
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


def gear_disc(pitch_r, teeth, width, tooth_h, axis="x"):
    """A spur/worm-wheel disc with simple trapezoidal teeth (a readable gear, not a print-ready
    involute -- generate the final teeth with BOSL2 in a venv). Rotates about `axis`, centered
    at the origin. Root cylinder + `teeth` radial tooth prisms around the rim."""
    root_r = pitch_r - 0.5 * tooth_h
    parts = [cyl(root_r, width, axis=axis)]
    tw = max(2 * np.pi * pitch_r / teeth * 0.55, 0.8)   # tooth tangential width
    for i in range(teeth):
        a = TAU * i / teeth
        if axis == "x":
            t = box(width, tw, tooth_h); t.apply_translation((0, 0, pitch_r))
            t.apply_transform(R(a, (1, 0, 0)))
        elif axis == "y":
            t = box(tw, width, tooth_h); t.apply_translation((0, 0, pitch_r))
            t.apply_transform(R(a, (0, 1, 0)))
        else:  # z
            t = box(tw, tooth_h, width); t.apply_translation((0, pitch_r, 0))
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
    # full-width Ø5 axle bore: the head CLAMPS the axle at its side walls (axle turns WITH the
    # head; it rotates in the neck-cheek bearings). Press/bond fit + a grub-screw key each side.
    axle_bore = cyl(P["axle_d"] / 2 + 0.1, P["head_w"] + 10, axis="x")
    axle_bore.apply_translation((0, 0, zt))
    shell = sub(shell, axle_bore)
    for sx in (-1, 1):
        grub = cyl(P["m3_clear_r"], 14); grub.apply_translation((sx * (P["head_w"] / 2 - 6), 0, zt + 6))
        shell = sub(shell, grub)

    # camera: the 24 mm board can't fit the ~10 mm forehead, so RECESS it inside the head behind
    # the forehead (lens low on the forehead at cam_lens_z) with a small lens bump on the front.
    # Board mounts front-face-in on 4x M2 bosses at the 21x12.5 pattern; ribbon drops to the Pi bay.
    fy = P["body_front_y"]
    lz = P["cam_lens_z"]                                # lens optical axis height (world Z)
    bz = lz - P["cam_lens_dz"]                          # board center Z (lens is above board center)
    bump = box(20, 8, 16); bump.apply_translation((0, fy, lz)); shell = uni([shell, bump])
    lens = cyl(P["cam_aperture_d"] / 2, 24, axis="y"); lens.apply_translation((0, fy, lz))
    shell = sub(shell, lens)
    # 4 M2 boss pillars on the inner front wall at the hole pattern (2 screwed, 2 locating pins)
    for sx in (-1, 1):
        for dz in (P["cam_hole_z_top"], P["cam_hole_z_bot"]):
            bo = cyl(P["cam_boss_od"] / 2, 9, axis="y")
            bo.apply_translation((sx * P["cam_hole_dx"] / 2, fy - 6, bz + dz))
            shell = uni([shell, bo])
            pil = cyl(P["cam_boss_pilot_r"], 14, axis="y")
            pil.apply_translation((sx * P["cam_hole_dx"] / 2, fy - 2, bz + dz))
            shell = sub(shell, pil)

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

    # screen retention: 4x M3 bosses into the display's OWN outer case-mount holes (wide 126 mm
    # stance clamps the metal chassis, not the glass). Screw axis = face normal (+Y); the glass
    # front lip is now only a locator. This is the real structural path.
    for lp in P["scr_mount_pts"]:
        w = (sp @ np.append(lp, 1.0))[:3]
        b = cyl(P["scr_boss_r"], 14, axis="y"); b.apply_translation((w[0], w[1] - 2, w[2]))
        bezel = uni([bezel, b])
        c = cyl(P["scr_m3_clear_r"], 30, axis="y"); c.apply_translation((w[0], w[1], w[2]))
        bezel = sub(bezel, c)

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

    # tilt WORM-motor bracket: the motor shaft runs along +Y (perpendicular to the tilt axle) and
    # carries the worm; the worm meshes the wheel on the axle. center distance = wheel_r + worm_r.
    wx = P["worm_wheel_x"]
    cd = P["worm_module"] * P["worm_wheel_teeth"] / 2 + P["worm_od"] * 0.4   # ~19
    wz = zt - cd
    face_y = -0.5 * P["worm_len"] - 4                    # motor mount face (behind the worm)
    plate = box(46, 4, 46); plate.apply_translation((wx, face_y, wz))
    parts.append(plate)
    # gusset tying the bracket down onto the neck column top
    gy0, gy1 = face_y, P["neck_y"] + P["neck_d"] / 2
    gus = box(12, abs(gy1 - gy0) + 4, 22)
    gus.apply_translation((wx, (gy0 + gy1) / 2, (wz + P["neck_top_z"]) / 2))
    parts.append(gus)

    neck = uni(parts)
    # axle clearance bore (Ø5 axle) through the cheeks
    bore = cyl(P["axle_d"] / 2 + 0.4, 2 * P["clevis_half"] + 4 * P["cheek_t"], axis="x")
    bore.apply_translation((0, 0, zt))
    neck = sub(neck, bore)
    # 695-2RS bearing seats in the cheeks: the axle rotates here (head clamps the ends, worm
    # wheel drives it in the middle). Press-fit Ø13 x 4 counterbore on each cheek's inner face.
    for sx in (-1, 1):
        seat = cyl(P["brg_od"] / 2, P["brg_w"] + 0.5, axis="x")
        seat.apply_translation((sx * (P["clevis_half"] - 1.0), 0, zt))
        neck = sub(neck, seat)
    # worm-motor shaft clearance + 2 M4 ear holes (35 mm) through the bracket plate
    sh = cyl(4.0, 20, axis="y"); sh.apply_translation((wx, face_y, wz)); neck = sub(neck, sh)
    for dz in (-17.5, 17.5):
        ear = cyl(P["motor_ear_hole_d"] / 2, 20, axis="y")
        ear.apply_translation((wx, face_y, wz + dz)); neck = sub(neck, ear)
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
    # seated on top of the base (world Z), flush with the base top; rides the lazy-Susan race
    zc = P["base_h"] - P["pan_plate_t"] / 2
    zbot = P["base_h"] - P["pan_plate_t"]      # platform underside (rides the balls)
    plate = cyl(P["pan_plate_d"] / 2, P["pan_plate_t"], sections=96)
    plate.apply_translation((0, 0, zc))

    # D-bore coupling hub on the underside: the pan motor's double-D shaft keys straight in
    # (flats carry torque; no eccentric needed since the CAN is offset to land the shaft on axis)
    hub = cyl(7.0, 12.0); hub.apply_translation((0, 0, zbot - 4))
    plate = uni([plate, hub])
    dbore = dbore_neg(20, axis="z"); dbore.apply_translation((0, 0, zbot + 2))
    plate = sub(plate, dbore)
    # M3 grub-screw boss onto a shaft flat (kills backlash)
    grub = cyl(P["m3_clear_r"], 16, axis="y"); grub.apply_translation((0, 0, zbot - 4))
    plate = sub(plate, grub)

    # ball groove on the underside (upper race of the lazy Susan)
    groove = trimesh.creation.torus(P["pan_race_circle_d"] / 2, P["pan_race_ball_d"] / 2 + 0.4)
    groove.apply_translation((0, 0, zbot))
    plate = sub(plate, groove)

    cable = cyl(6.0, 40.0)                    # off-axis cable pass (service loop to the base)
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


def build_pan_race():
    """Captured-BB lazy-Susan lower race (fixed to the base) + the ball ring. The platform
    underside is the upper race (grooved in build_pan_platform). Balls sit on the pitch circle;
    the wide stance carries the top-heavy head without wobble."""
    cr = P["pan_race_circle_d"] / 2
    bd = P["pan_race_ball_d"]
    zbot = P["base_h"] - P["pan_plate_t"]          # balls tangent to the platform underside
    zball = zbot - bd / 2
    # lower race: a grooved ring sitting in the base seat
    ro, ri = cr + P["pan_race_w"] / 2, cr - P["pan_race_w"] / 2
    ring = sub(cyl(ro, 5.0), cyl(ri, 6.0)); ring.apply_translation((0, 0, zball - 1.0))
    groove = trimesh.creation.torus(cr, bd / 2 + 0.4); groove.apply_translation((0, 0, zball))
    lower = sub(ring, groove)
    _color(lower, "pan"); lower.metadata["name"] = "pan_race"

    balls = []
    for i in range(P["pan_race_n"]):
        a = TAU * i / P["pan_race_n"]
        b = trimesh.creation.icosphere(subdivisions=1, radius=bd / 2)
        b.apply_translation((cr * np.cos(a), cr * np.sin(a), zball))
        balls.append(b)
    ballring = uni(balls); _color(ballring, "axle"); ballring.metadata["name"] = "pan_balls"
    return lower, ballring


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
    # pan platform seat: a deep recess housing the lazy-Susan lower race + platform underside
    seat = cyl(P["pan_plate_d"] / 2 + 1.0, 16.0, sections=96)
    seat.apply_translation((0, 0, z1 - 8.0)); body = sub(body, seat)
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


def _track_link_poses(wb, R, zc, n):
    """(y, z, angle) for n link pads walked around the stadium loop in the Y-Z plane.
    Bottom run at z=zc-R (ground), top at z=zc+R; semicircles around the two wheel centers."""
    straight, arc = wb, np.pi * R
    perim = 2 * straight + 2 * arc
    poses = []
    for i in range(n):
        s = perim * i / n
        if s < straight:                              # bottom run, +Y
            y, z, ang = -wb / 2 + s, zc - R, 0.0
        elif s < straight + arc:                       # front semicircle (+wb/2, zc)
            t = (s - straight) / R
            y, z, ang = wb / 2 + R * np.sin(t), zc - R * np.cos(t), t
        elif s < 2 * straight + arc:                   # top run, -Y
            u = s - straight - arc
            y, z, ang = wb / 2 - u, zc + R, np.pi
        else:                                          # rear semicircle (-wb/2, zc)
            t = (s - 2 * straight - arc) / R
            y, z, ang = -wb / 2 - R * np.sin(t), zc + R * np.cos(t), np.pi + t
        poses.append((y, z, ang))
    return poses


def build_tracks():
    """Two positive-drive track pods: a chain of printed link pads (on filament-rod pins) wrapping
    a 12-tooth drive sprocket (rear) + idler on a Ø16 bearing (front) + road wheels. Each pod is a
    concatenation of separate printed pieces (links, wheels), not one solid."""
    R, tw, wb = P["track_wheel_r"], P["track_width"], P["track_wheelbase"]
    pitch, pth = P["track_pitch"], P["track_pad_th"]
    zc = R                                             # wheel-center height (pad bottom -> ground)
    out = []
    for sx in (-1, 1):
        cx = sx * (P["chassis_w"] / 2 + P["track_gap"] + tw / 2)
        pieces = []
        # link chain
        for (y, z, ang) in _track_link_poses(wb, R, zc, P["track_links"]):
            pad = box(tw, pitch * 0.92, pth + P["track_grouser_h"])
            pad.apply_transform(R_x(ang))              # tangent to the loop
            pad.apply_translation((cx, y, z))
            pieces.append(pad)
        # drive sprocket (rear, -Y): 12 teeth meshing the pin knuckles
        spr = gear_disc(P["sprocket_outer_d"] / 2 - 1.5, P["sprocket_teeth"], tw - 20, 3.0, axis="x")
        spr = sub(spr, dbore_neg(tw, axis="x"))        # TT double-D-ish drive bore (placeholder)
        spr.apply_translation((cx, -wb / 2, zc)); pieces.append(spr)
        # idler (front, +Y): plain wheel on a Ø16 flanged bearing
        idl = sub(cyl(R - 2, tw - 22, axis="x"), cyl(P["idler_bore_d"] / 2, tw, axis="x"))
        idl.apply_translation((cx, wb / 2, zc)); pieces.append(idl)
        # road wheels: support the bottom run so it can't sag
        for i in range(P["roadwheel_count"]):
            ry = -wb / 4 + i * (wb / 2) / max(P["roadwheel_count"] - 1, 1)
            rw = cyl(P["roadwheel_d"] / 2, tw - 20, axis="x")
            rw.apply_translation((cx, ry, P["roadwheel_d"] / 2)); pieces.append(rw)
        pod = trimesh.util.concatenate(pieces)
        _color(pod, "track")
        pod.metadata["name"] = "track_L" if sx < 0 else "track_R"
        out.append(pod)
    return out


def motor_tt(name):
    """TT gearmotor placeholder (yellow gearbox + round can + double-D output shaft along +X)."""
    gx, gw, gh = P["tt_gearbox"]
    gearbox = box(gx * 0.35, gw, gh); gearbox.apply_translation((0, 0, 0))
    can = cyl(P["tt_motor_d"] / 2, gx * 0.5, axis="x")
    can.apply_translation((-gx * 0.4, 0, 0))
    shaft = cyl(P["tt_shaft_d"] / 2, 20, axis="x"); shaft.apply_translation((gx * 0.3, 0, 0))
    m = uni([gearbox, can, shaft]); _color(m, "motor"); m.metadata["name"] = name
    return m


def R_x(ang):
    return R(ang, (1, 0, 0))


def motor_28byj(name):
    """28BYJ-48 stepper, dimensionally correct: can + gearbox + offset double-D shaft + two
    ears (holes on a can diameter) + wiring box. Shaft along +Z, shaft base at z=top.

    The output shaft is offset motor_shaft_off in +X; the two ear holes lie on the Y axis
    (perpendicular to the offset), 35 mm apart, centered on the CAN axis -> to land the shaft
    on a target axis you position the CAN, not the ears (see build()).
    """
    r = P["motor_can_d"] / 2
    off = P["motor_shaft_off"]
    can = cyl(r, P["motor_body_h"]); can.apply_translation((0, 0, P["motor_body_h"] / 2))
    gh, top = P["motor_gear_h"], P["motor_body_h"] + P["motor_gear_h"]
    gear = cyl(r - 0.5, gh); gear.apply_translation((0, 0, P["motor_body_h"] + gh / 2))
    boss = cyl(P["motor_boss_d"] / 2, 1.45); boss.apply_translation((off, 0, top + 0.72))

    # double-D output shaft: round Ø motor_shaft_d, flats motor_shaft_flat apart over top 6 mm
    sl, fl = P["motor_shaft_len"], P["motor_flat_len"]
    shaft = cyl(P["motor_shaft_d"] / 2, sl); shaft.apply_translation((off, 0, top + sl / 2))
    for sy in (-1, 1):
        cutter = box(P["motor_shaft_d"] + 2, P["motor_shaft_d"], fl + 0.5)
        cutter.apply_translation((off, sy * (P["motor_shaft_flat"] / 2 + P["motor_shaft_d"] / 2),
                                  top + sl - fl / 2))
        shaft = sub(shaft, cutter)

    # mounting ears: a thin bar across the can front with two Ø4.2 holes on the Y axis
    ear = box(7.0, P["motor_ear_cc"] + 8, 1.0); ear.apply_translation((0, 0, P["motor_body_h"] - 0.5))
    for sy in (-1, 1):
        h = cyl(P["motor_ear_hole_d"] / 2, 4); h.apply_translation((0, sy * P["motor_ear_cc"] / 2, P["motor_body_h"] - 0.5))
        ear = sub(ear, h)

    # blue wiring box, protruding radially on the -X side (opposite the shaft offset)
    wbox = box(6.0, P["motor_wbox_w"], P["motor_wbox_h"])
    wbox.apply_translation((-(r + 2), 0, P["motor_wbox_h"] / 2))

    m = uni([can, gear, boss, shaft, ear, wbox])
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

    # track drive: 2x TT gearmotor (own 1, BUY 1 more) at each pod's rear sprocket, shaft along X.
    # Motors live IN THE PODS (body stays free for the pan motor + drivers + ballast). Skid steer.
    twd, wbd = P["track_width"], P["track_wheelbase"]
    for sx in (-1, 1):
        cx = sx * (P["chassis_w"] / 2 + P["track_gap"] + twd / 2)
        dm = motor_tt("drive_L" if sx < 0 else "drive_R")
        if sx < 0:
            dm.apply_transform(R(TAU / 2, (0, 0, 1)))   # flip so the shaft points outboard
        dm.apply_translation((cx - sx * 26, -wbd / 2, P["track_wheel_r"]))
        add(dm, np.eye(4))

    # --- PAN GROUP ---
    add(build_pan_platform(), M_pan, "pan_platform.stl")

    neck = build_neck_clevis()                       # already built in world Z (sits on base top)
    scene_neck = neck.copy(); scene_neck.apply_transform(M_pan)
    scene.add_geometry(scene_neck, node_name="neck_clevis")
    if EXPORT:
        neck.export(stlp("neck_clevis.stl"))

    # --- TILT WORM DRIVE (self-locking single-start) ---
    wx = P["worm_wheel_x"]
    cd = P["worm_module"] * P["worm_wheel_teeth"] / 2 + P["worm_od"] * 0.4   # center distance
    wz = zt - cd
    wheel_r = P["worm_module"] * P["worm_wheel_teeth"] / 2
    # worm wheel keyed to the axle -> turns WITH the head (M_head)
    wheel = gear_disc(wheel_r, P["worm_wheel_teeth"], P["worm_wheel_w"], 2.5 * P["worm_module"], axis="x")
    wheel = sub(wheel, cyl(P["axle_d"] / 2 + 0.1, P["worm_wheel_w"] + 4, axis="x"))
    _color(wheel, "fork"); wheel.metadata["name"] = "worm_wheel"
    wheel.apply_translation((wx, 0, zt))
    add(wheel, M_head)
    # worm on the motor shaft (axis Y), tangent below the wheel; fixed to the neck frame (M_pan)
    wm = worm(P["worm_od"] / 2, P["worm_len"], axis="y")
    _color(wm, "motor"); wm.metadata["name"] = "tilt_worm"
    wm.apply_translation((wx, 1.0, wz))
    add(wm, M_pan)
    # tilt motor: shaft (+Z) rotated to +Y to carry the worm; CAN offset so the shaft lands on
    # the worm axis (x=wx, z=wz). Motor body sits behind the bracket, inside the neck footprint.
    mt = motor_28byj("motor_tilt")
    mt.apply_transform(R(-TAU / 4, (1, 0, 0)))       # shaft +Z -> +Y
    face_y = -0.5 * P["worm_len"] - 4
    mt.apply_translation((wx - P["motor_shaft_off"], face_y - (P["motor_body_h"] + P["motor_gear_h"]), wz))
    add(mt, M_pan)

    # Pi 5 in the HEAD, behind the tilt axis: the DSI + CSI ribbons then stay entirely in the head
    # (zero joint crossings), and the board doubles as the tilt counterweight. Board plane = XZ.
    pi = box(P["pi_w"], P["pi_t"], P["pi_h"]); _color(pi, "pi"); pi.metadata["name"] = "pi5"
    pi.apply_translation((0, P["pi_y_in_head"], zt))
    add(pi, M_head)

    # pan motor: 28BYJ-48 upright in the base, CAN offset -motor_shaft_off so the D-shaft lands
    # ON the pan axis; shaft tip reaches ~2 mm below the platform top into its D-bore hub.
    mp = motor_28byj("motor_pan")
    zsh = P["base_h"] - 2 - (P["motor_body_h"] + P["motor_gear_h"] + P["motor_shaft_len"])
    mp.apply_translation((-P["motor_shaft_off"], 0, zsh))
    add(mp, np.eye(4))

    # pan bearing: captured-BB lazy-Susan lower race + ball ring (fixed frame; platform is the
    # upper race). Balls carry the head weight on a wide circle -> no wobble, quiet, cheap.
    lower_race, balls = build_pan_race()
    add(lower_race, np.eye(4), "pan_race.stl")
    add(balls, np.eye(4))

    # --- HEAD (tilt + pan): split into front bezel + back cover ---
    bezel, back = build_head_parts()
    add(bezel, M_head, "head_bezel.stl")
    add(back, M_head, "head_back.stl")

    screen = load_screen()
    screen.apply_transform(screen_pose())            # sit on the leaned front face
    screen.metadata["name"] = "screen_ref"
    add(screen, M_head)

    # camera board: recessed behind the forehead, front-face toward the lens bump, on the M2 bosses
    fy = P["body_front_y"]; bz = P["cam_lens_z"] - P["cam_lens_dz"]
    cam = box(P["cam_w"], P["cam_d"], P["cam_h"]); _color(cam, "camera")
    cam.metadata["name"] = "camera_ref"
    cam.apply_translation((0, fy - 6 - P["cam_d"] / 2, bz))
    add(cam, M_head)
    # camera rear cover: traps the board on the M2 bosses (held even with 2 screws), ribbon relief
    cover = box(P["cam_board_w"] + 2, P["cam_cover_t"], P["cam_board_h"] + 2)
    rib = box(P["cam_ribbon_w"], P["cam_cover_t"] + 2, P["cam_ribbon_t"])
    rib.apply_translation((0, 0, -(P["cam_board_h"] + 2) / 2 + 1)); cover = sub(cover, rib)
    _color(cover, "back"); cover.metadata["name"] = "cam_cover"
    cover.apply_translation((0, fy - 6 - P["cam_d"] - 1, bz))
    add(cover, M_head, "cam_cover.stl")

    # HOLLOW Ø5 tilt axle: clamped to the head (turns with it), rotates in the neck-cheek 695
    # bearings, driven in the middle by the worm wheel. Hollow -> Pi power wires cross on-axis.
    axle = sub(cyl(P["axle_d"] / 2, P["head_w"] + 4, axis="x"),
               cyl(P["axle_bore_d"] / 2, P["head_w"] + 8, axis="x"))
    _color(axle, "axle"); axle.metadata["name"] = "tilt_axle"
    axle.apply_translation((0, 0, zt))
    add(axle, M_head)

    out = webpath(out_name)
    scene.export(out)
    print(f"wrote {out}  ({len(scene.geometry)} parts)")
    if EXPORT:
        print("exported per-part STLs into stl/")


if __name__ == "__main__":
    build()

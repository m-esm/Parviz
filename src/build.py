"""desk-pi -- tracked pan/tilt robot around the real 7" touchscreen.

Coordinate system: Z up, robot looks toward +Y (screen glass faces +Y).
Origin (0,0,0) = center of the desk contact plane.

Kinematic chain (bottom -> top):
    tank chassis          fixed base with two track pods and TT gearmotor placeholders
      -> PAN joint        yaw about vertical Z, driven by a 28BYJ D-shaft in the base
        -> pan_platform + neck_clevis  (rotate as one on the captured-BB race)
          -> TILT joint   pitch about horizontal X, driven by a self-locking worm
            -> rounded tablet head + screen/Pi + camera

The screen and Pi ride as one module inside the head. DSI/CSI ribbons stay inside the head;
only round power wires cross the pan/tilt joints. The default GLB render uses a preview pose
(`preview_pan_deg`, `preview_tilt_deg`) so motion is visible; set PAN=0 TILT=0 for neutral review.

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
                      "Raspberry_Pi_Touch_Screen_Assembly_-_Pins_Out_v8.stl",
    # Combined display + Pi (Pi on the display's own 58x49 back standoffs, GPIO pins out).
    # bbox 192.96 x 38.01 x 110.76: same W/H/glass as the old v12 display-only model, 13.02
    # deeper on the BACK. load_screen() anchors the GLASS FACE at this local Y (post-flip),
    # not the bbox centroid (which the deeper back would drag ~6.5 mm).
    "screen_glass_y": 12.494,
    "screen_flip": True,    # glass faced -Y (into the head); 180 about X faces it +Y (front)

    # --- Head shell: SIMPLE rounded box (a clean tablet-head; screen upright on the front) ---
    "head_wall": 4.0,
    "head_w": 205.0,        # shell outer width (screen 193 + walls + margin)
    "face_angle": 0.0,      # upright front face (the neck's tilt gives the look-up/down)
    "body_front_y": 31.0,   # front face plane (glass sits flush here)
    "body_back_y": -31.0,   # back face plane (behind the tilt axis; Pi bay)
    "body_z_bot": 88.0,     # shell bottom height above desk (113-25: design-ref head drop --
                            # the whole head+tilt stack sits 25 lower over the chassis)
    "body_z_top": 226.0,    # shell top height (was 251; -25 head drop. 243+8 history: the CM3 bay needs ~14 mm between
                            # the screen window top (229.9) and the ceiling; 243 gave only 9.1 --
                            # the board punched the top wall and the barrel crossed the panel)
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
    # The display carries a RAISED boss around each factory hole (annulus r 1.5..8.1, spanning
    # y 22.534..25.034 in the mesh -- measured, all 4 mounts identical). The rear standoff's
    # bearing face lands on the boss REAR plane (hole plane - scr_boss_lip), not the hole
    # plane itself; running to the hole plane buried the standoffs 2.5 mm inside the bosses
    # and held the screen 2.5 mm proud (stage-4 defect D1).
    "scr_boss_lip": 2.5,    # display boss height behind its hole plane (measured)
    "scr_seat_clear": 0.05, # bearing-face clearance (the M3 pulls it tight on assembly)

    # --- Tilt joint: REAR CLEVIS entering the shell underside; axle near the CoM ---
    #     Self-locking WORM drive (single-start): head holds tilt with the motor de-energized
    #     (no idle current/heat). Pre-balance the head on the axle so the worm barely works.
    "tilt_axis_z": 153.0,   # tilt axis height above the desk (178-25 head drop; near CoM)
    # Stage 2R: axle moved BACK 18 mm (y 0 -> -18). The Pi rides the display back (stack rear
    # face y=-7, z 151..207.5), so an axle at y=0 ran straight through the board plane. The
    # whole tilt drivetrain (cheeks, bearings, wheel, worm, clamp tubes) keys off this pair.
    "tilt_axis_y": -18.0,   # tilt axis Y (behind the screen+Pi stack; was 0 pre-2R)
    "tilt_cantilever": 18.5,# screen center Y in world (absolute; decoupled from the axle in 2R)
    "screen_cz": 153.0,     # screen center height (178-25 head drop; decoupled from the axle)
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
    "worm_wheel_teeth": 12, # ratio 12:1 (still self-locks; 24T tilted 60 deg in 16 s -- too slow)
    "worm_wheel_w": 7.0,    # face width
    "worm_wheel_x": 0.0,    # wheel centered on the head midplane (spacer tubes reach both bearings)
    "worm_od": 10.0,        # worm outer Ø (pitch r ~4)
    # 14 (was 16): threads (body + 1 mm rib overhang each end) span 16 mm = 4.07 axial
    # pitches (>= 4 teeth-equivalent on the 12T wheel) and END at y=-16, so a bare Ø5 tail
    # stub emerges BEFORE the cradle groove band (y -15.5..-13). The old 16 ran full-radius
    # threads to y=-13.5, through the cradle (stage-4 defect D2).
    "worm_len": 14.0,

    # --- Neck column (carries the clevis, rides the pan platform) ---
    "neck_w": 48.0,         # column width (X) -- squarer + rounded reads as a neck, not a plank
    "neck_d": 46.0,         # column depth (Y)
    "neck_round": 10.0,     # corner rounding radius
    "neck_top_z": 125.0,    # where the column stops and the clevis cheeks rise (150-25 drop)
    # Stage 5: column moved inboard (-38 -> -17) so the whole base footprint rides the
    # SPINNING platform, not the fixed deck: footprint max radius = sqrt(14^2+(|ny|+13)^2)+10
    # (rounded-rect corner arcs) = 43.11 <= 44.0, inside the platform's solid top (r45 within
    # the clip rebate). The tilt axle (y=-18, z=178) and the head did NOT move; the cheeks
    # re-anchor via the cheek-root block and the column front gets a deep -30 deg chin notch.
    "neck_y": -17.0,        # column center Y (ON the pan platform)
    # cable channel center: pushed BEHIND the column center so the deepened front notch
    # (rear face y=-19.5) never opens the channel; platform slot + deck pass aim at this
    "neck_chan_y": -26.0,

    # --- Pan joint + platform + captured-BB lazy-Susan race (printed) ---
    "pan_plate_d": 96.0,    # rotating platform diameter (rides the lazy-Susan race)
    # plate thickness DERIVED for a flush top: seat depth 15 = plate 7.6 + ball air gap 2.4
    # + ring 5 (see _pan_stack). Flush-top picked over keeping t=8 (which stood 0.4 proud).
    "pan_plate_t": 7.6,
    "pan_race_circle_d": 80.0,  # BB pitch circle (wide stance resists the top-heavy tilt)
    "pan_race_ball_d": 6.0,     # 6 mm airsoft BBs (owned/cheap; quiet, greased)
    "pan_race_w": 12.0,     # race ring radial width
    "pan_race_n": 18,       # balls on the circle
    "pan_race_ring_t": 5.0, # lower race ring thickness (sits on the chassis seat floor)
    "pan_groove_engage": 1.8,   # each groove wraps 1.8 mm of ball -> 2.4 mm plate<->ring air gap
    "pan_groove_clear": 0.2,    # groove minor r = ball_r + 0.2 (0.4 rattled; 0 binds)
    # cable exit through the deck: INSIDE the race ID (r<34) and clear of the (0,-26) neck
    # bolt + the pan-axis bore. The platform slot jogs the bundle here from the neck channel.
    "cable_exit": (12.0, -24.0),

    # --- Tank-tread chassis: central body + two side track pods (mobile base) ---
    "base_h": 66.0,         # body top = pan-mount plane (52->66: design-ref stance; head:base
                            # height split. Head z_bot 88 leaves a 22 gap; swept head corner
                            # min z~72 -> 6 mm over the platform, probe-verified)
    # solid top DECK (the old cavity reached base_h -> the pan seat cut was a no-op and the
    # race/balls/platform floated). 20 leaves a 5 mm floor under the race seat (z 32..37);
    # everything in the cavity tops out below 32 (motor ears 31.25, wiring box 29.2).
    "deck_t": 20.0,
    "chassis_w": 140.0,     # body width between the tracks (120->140: track outer faces land
                            # at +-102 ~= head half-width 102.5, killing the head overhang;
                            # NOT 148 -- the tucked claws at x 106..119 need 4 mm to the pods)
    "chassis_l": 156.0,     # body length front-back (Y)
    "chassis_clear": 7.0,   # ground clearance under the body
    "track_gap": 4.0,       # body side <-> track inner face
    # Modular positive-drive track (advancedvb 'Tank track' 3062624 geometry): printed link pads
    # on filament-rod hinge pins, a 12-tooth sprocket meshing the pins -> no slip on a desk.
    "track_wheel_r": 19.32,  # pin-circle radius = exact 12T x 10.0-pitch polygon (audit corr. 1)
    "track_wheelbase": 120.0,   # sprocket-axis <-> idler-axis (Y)
    "track_width": 28.0,    # link body width (X); sprocket engages the central ~8 mm
    "track_pitch": 10.0,    # link pin-to-pin (our re-model; the 3062624 reference pitch is 9.65)
    "track_links": 36,      # 36 x 10 = 360 mm loop
    "track_pad_th": 4.5,    # pin axis -> pad OUTER face (link overall 8: knuckle r3.5 inward)
    "track_grouser_h": 1.5, # tread lug (print grousers in TPU or add pads)
    "track_pin_bore_d": 2.0,    # link hinge bore for Ø1.75 filament pins (ref uses ~2.0 drafted)
    "sprocket_teeth": 12,
    "sprocket_outer_d": 37.6,   # tip r 18.8 = pin circle 19.32 - 0.5 clearance (OD 42 jammed links)
    "idler_bore_d": 15.95,  # F688ZZ (8x16x5, flange 18) press seat; flange recess 18.5 x 1.0
    "roadwheel_d": 22.0,    # inner bottom-run support wheels (ride the knuckle crowns)
    "roadwheel_count": 2,
    "idler_slot": 4.0,      # idler Y-slide for tensioning (M3 set-screw lock)
    # TT gearmotor drive (own 1x; BUY 1 more -> 2 for skid steer; MX1588 drives both).
    # Measured dims from reference/tt-motor-1079893/NOTES.md (STEP B-rep). Shaft is
    # PERPENDICULAR to the 64.5 body, 11.5 behind the gearbox front face, mid-height.
    "tt_gearbox": (36.80, 22.40, 18.64),    # rect block (len, w, h); +Ø22.4 collar 11.3 long
    "tt_motor_d": 20.0,     # can Ø20.00, 14.99 across flats, 13.5 exposed
    "tt_shaft_d": 5.4,      # double-D output shaft, 3.70 flats, 8.8 proud, flat len 8.0

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

    # --- Camera Module 3 (official drawing RP-008153-DS; see reference/rpi-camera-module-3/) ---
    "cam_board_w": 25.0,    # X  board width
    "cam_board_h": 23.862,  # Z  board height
    "cam_hole_dx": 21.0,    # mount holes at X = +-10.5
    "cam_hole_z_top": 2.565,   # top hole row Z (from board center)
    "cam_hole_z_bot": -9.935,  # bottom hole row Z
    "cam_lens_dz": 2.47,    # optical axis above board center (X = 0; official CM3 +2.469)
    "cam_lens_z": 212.0,    # lens axis height (237-25 head drop; whole camera bay shifts with
                            # the shell+screen, so the relative clearances below hold): barrel bottom
                            # 234.1 clears the display module top (233.4) and the pocket (233.9);
                            # csk bottom 233.0 keeps a 3.1 ligament over the window top (229.9)
    # CM3 front stack: 10.8 sq AF housing (front 4.0 above board front), Ø5.75 barrel to 6.98;
    # 1.12 board; keep 3.2 clear behind for the flex connector (overall depth 11.3).
    "cam_pcb_t": 1.12,
    "cam_back_d": 3.2,      # connector envelope behind the board back face
    "cam_house_wh": 10.8,   # AF housing footprint (square, centered on the lens axis)
    "cam_house_d": 4.0,     # housing front above board front
    "cam_lens_tip": 6.98,   # lens tip above board front
    "cam_barrel_d": 5.75,   # lens barrel outer Ø
    # aperture through the 4 mm forehead wall (pupil Ø2.63 ~3 mm behind the outer face,
    # 75 deg diagonal FoV): Ø6.3 through-bore + 45 deg/side countersink to Ø8.0 at the face
    "cam_bore_d": 6.3,
    "cam_csk_d": 8.0,
    "cam_boss_od": 4.6,     # M2 self-tap boss OD
    "cam_boss_len": 1.0,    # short bosses off the pier's back face; TIPS = board front plane
    # Ceiling-hung camera PIER: the front wall below the pocket top (z 233.9) is all screen
    # pocket/window (nothing to root bosses on) and the display panel band starts at y=25.03
    # (measured from the reference mesh in the camera zone), so long wall-rooted bosses punch
    # the panel. The pier drops from the ceiling BEHIND the panel's top strip and carries the
    # 4 M2 bosses; the board hangs 4.5 mm behind the panel, the barrel passes over its top edge.
    "cam_pier_w": 32.0,     # pier width (X); display panel is the limit in Y, not X
    "cam_pier_t": 3.0,      # pier plate thickness (Y)
    "cam_pier_y1": 24.5,    # pier FRONT face: 0.53 behind the measured panel front (25.03)
    "cam_boss_pilot_r": 0.85,  # M2 self-tap pilot Ø1.7
    "cam_m2_clear_r": 1.15, # M2 clearance (cover)
    "cam_ribbon_w": 17.0, "cam_ribbon_t": 2.5,   # CSI ribbon exit slot (pod bottom -> Pi bay)
    "cam_cover_t": 2.0,     # rear board-retaining cover
    # (pi_* placement params removed: the Pi 5 now rides the display's OWN 58x49 back
    # standoffs and comes in as part of the combined "Pins Out" screen reference mesh.
    # NOTE the measured consequence: the combined stack spans world y -7.0..+5.5 over
    # x -37.7..48.1, z 151..207.5, which OVERLAPS the tilt mechanism at the axis plane
    # (axle y 0 z 178, clamp tubes x 27..99, centered worm/wheel, neck cheek overshoots).
    # See docs/FIXES.md Stage 3: unresolvable in head geometry alone.)

    # --- Design-ref styling (reference/design/*.jpg): orange side rails on the head ---
    "rail_t": 5.0,          # rail stands this proud of the head side wall
    "rail_d": 26.0,         # rail depth (Y); stays on the wall's FLAT band (|y|<15, corner r16)
    "rail_h": 90.0,         # rail height (Z)
    "rail_cz": 160.0,       # rail center height (brackets the screen band, z 115..205)
    # LED strip in the top bezel, LEFT of the camera (design-ref front.jpg). Recess sized
    # for a short WS2812 stick segment; sits on FOREHEAD wall material only: the screen
    # pocket opening tops out at z 233.9, so the slot must stay above it.
    "led_slot_w": 42.0,     # slot width (X)
    "led_slot_h": 5.0,      # slot height (Z)
    "led_slot_d": 1.5,      # recess depth into the 4 mm face wall
    # image-LEFT of the camera in the reference front view = robot +X (front view looks -Y)
    "led_cx": 45.0,         # slot center X (clear of the camera pier |x|<16)
    "led_cz": 214.0,        # slot center Z (lens 212; slot z 211.5..216.5 > pocket top 208.9 ok)
    # Knurled antenna stub on the head top face (cosmetic; Pi WiFi is internal).
    # Image-RIGHT in the reference front view = robot -X.
    "ant_x": -62.0, "ant_y": -8.0,  # on head_back's top (split plane is at y~2)
    "ant_d": 13.0, "ant_h": 26.0,   # fat, short stub like the reference
    "ant_collar_d": 16.0, "ant_collar_h": 3.0,
    # Orange picture-frame around the head-back service area (design-ref back.jpg). The
    # louvres + cable port play the reference's inner hatch. Bottom band notched over the
    # neck slot (wall open to z=191 in x +-31 for the tilt sweep; the frame must not
    # hover in that envelope).
    "hatch_frame_w": 160.0, "hatch_frame_h": 105.0,  # outer X x Z
    "hatch_frame_band": 13.0,   # ring width
    "hatch_frame_t": 3.0,       # proud of the back face
    "hatch_frame_cz": 151.0,    # outer z 98.5..203.5; inner 111.5..190.5 (port 113..147,
                                # louvres 180..214 both land inside the opening)
    # Chassis FRONT fascia (design-ref front.jpg). Front wall: y=78 face, x +-60, z 7..52.
    "grille_cz": 46.0,      # orange surround outer 60x20 -> z 36..56; inner 52x12
    "grille_w": 60.0, "grille_h": 20.0, "grille_band": 4.0, "grille_t": 2.5,
    "us_dx": 13.0,          # ultrasonic barrel centers at x=+-13 (HC-SR04 transducer pitch ~26)
    "us_cz": 26.0,          # barrel Ø16 -> z 18..34 (2 under the surround; board clears the floor)
    "us_d": 16.0,
    "lamp_x": 54.0, "lamp_cz": 26.0,    # amber corner lamps 12x7, proud 2 (hug the 140-wide corners)
    "fled_cz": 9.5,         # white dot strip 36x2.5 at the bottom lip, proud 1
    # Chassis REAR styling (design-ref back.jpg): orange frame panel (the wall shows
    # through the opening as the 'hatch') above the USB-C slot (x +-7, z 15..23), and a
    # silver cylinder pod low-right (speaker/buzzer placeholder).
    "rear_panel_cz": 35.0,  # panel 72x22 -> z 24..46; opening 44x14 -> z 28..42
    "rear_cyl_x": 38.0,     # image-RIGHT in the reference back view (verified in-render)
    "rear_cyl_cz": 16.0, "rear_cyl_d": 14.0,
    # Raised camera POD on the forehead (design ref: the camera reads as an eye). Pure
    # cosmetic shell over the recessed CM3: the bore flares 45 deg/side from the existing
    # countersink, wider than the 75 deg-diagonal FoV cone (half ~37.5 deg), so no vignette.
    "cam_pod_w": 24.0, "cam_pod_h": 18.0,   # pod footprint on the face (X x Z)
    "cam_pod_t": 5.0,                       # proud of the face
    # Gripper arms (design ref, PLACEHOLDER pose + shapes): shoulder pivots on the side
    # rails, tucked pose (claws down-forward beside the chassis front). Actuation, joint
    # hardware, and the head-vs-platform mount decision are a later mechanism pass.
    "arm_x": 112.5,         # arm plane center (outboard of the rails at 107.5)

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

# Design-reference colorway (reference/design/*.jpg): matte black body + safety-orange
# accents, silver mechanicals. NOTE the bundled viewer re-colors by NODE NAME (PAL in
# web/viewer_glb.html) -- keep both palettes in sync.
COLORS = {
    "screen":  [26, 30, 38, 255],
    "cradle":  [46, 50, 56, 255],       # matte charcoal (head bezel)
    "back":    [54, 58, 65, 255],       # charcoal (head back, covers)
    "neck":    [86, 92, 102, 255],      # dark steel mechanicals
    "fork":    [86, 92, 102, 255],
    "pan":     [74, 79, 87, 255],       # graphite
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


def worm_cd():
    """Tilt worm center distance (wheel pitch r + ~worm pitch r). Single source of truth for
    the neck bracket AND the assembly (it used to be duplicated in both)."""
    return P["worm_module"] * P["worm_wheel_teeth"] / 2 + P["worm_od"] * 0.4


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
    # Anchor by the GLASS FACE (largest +Y plane = front bbox face), not the centroid: the
    # Pins-Out assembly carries the Pi on the back, and centroid centering would shift the
    # glass + factory mount holes ~6.5 mm forward of where the v12 display-only model sat.
    m.apply_translation((0.0, P["screen_glass_y"] - m.bounds[1][1], 0.0))
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
    """Transform placing the recentered screen onto the leaned front face.
    Anchored on screen_cz (NOT the tilt axle: the axle moved in stage 2R, the screen didn't)."""
    zc = P["screen_cz"]
    tilt = R(P["face_angle"] * DEG, (1, 0, 0), (0, 0, zc))   # lean top back
    trans = np.eye(4)
    trans[:3, 3] = (0, P["tilt_cantilever"], zc)
    return tilt @ trans


def build_head_shell():
    """Alexa/Echo-Show wedge shell: rounded body, leaned front holding the 7" screen."""
    zt = P["tilt_axis_z"]
    yt = P["tilt_axis_y"]
    shell = _head_solid()

    # hollow it (leave uniform walls), opening kept via the back cavity below
    inner = _head_solid(inset=P["head_wall"])
    shell = sub(shell, inner)

    # stepped screen aperture: full-size POCKET behind (module drops in) + a smaller front
    # WINDOW that pierces the face, leaving a lip that retains the glass edge.
    ov, cl = P["bezel_overlap"], P["screen_clear"]
    # the pocket PIERCES the face (front at y=31.1): the glass front sits at 30.99, i.e.
    # FLUSH with the face, so any lip in front of it interfered 0.49 mm and blocked the
    # module from seating on its factory-screw bosses. Retention is the 4 M3 factory
    # screws; the pocket side walls locate the module (flush edge-to-edge glass look).
    pocket = box(P["screen_w"] + 2 * cl, 40.0, P["screen_h"] + 2 * cl)
    pocket.apply_transform(screen_pose() @ _T(0, -7.4, 0))
    shell = sub(shell, pocket)
    window = box(P["screen_w"] - 2 * ov, 60.0, P["screen_h"] - 2 * ov)
    window.apply_transform(screen_pose() @ _T(0, 20, 0))     # pierce the front face -> lip
    shell = sub(shell, window)

    # small rear cable port (main electronics access is by removing the front bezel)
    cable_port = box(48, 30.0, 34.0)
    cable_port.apply_translation((0, P["body_back_y"], P["body_z_bot"] + 42))
    shell = sub(shell, cable_port)

    # Pi I/O access, re-aimed for the REAL Pi (combined Pins-Out screen mesh): the Pi rides
    # the display's own back standoffs, landscape, board plane XZ, stack world x -37.7..48.1,
    # y -7.0..+5.5, z 151..207.5. The ETH+USB short edge faces +X at x=48 -> slot through the
    # RIGHT side wall, aligned to the port depth (y -8.5..6.5) and to the upper half of the
    # port stack (z 191.5..208.5; the band z 165..191 belongs to the pivot boss). USB-C + 2x
    # HDMI exit the BOTTOM long edge (z~151) into the open interior: cables route down and out
    # the bottom-rear neck slot / cable port. Nothing exits the top (GPIO pins point -Y).
    # (Kept separate from the bottom-rear cable port below.)
    io_side = box(14.0, 15.0, 17.0)
    io_side.apply_translation((P["head_w"] / 2 - 2, -1.0, P["screen_cz"] + 22.0))
    shell = sub(shell, io_side)
    # ventilation louvres high on the back wall (Pi 5 runs hot)
    for i in range(-2, 3):
        louvre = box(50, 30.0, 4.0)
        louvre.apply_translation((0, P["body_back_y"], P["screen_cz"] + 18 + i * 8))
        shell = sub(shell, louvre)

    # bottom-rear slot so the neck clevis can rise into the body and reach the axle.
    # Narrow in X (62: cheeks end at |x|=26) but TALL (top z=191): at +-30 tilt the back wall
    # sweeps over the raised 12T-worm motor + plate; the old 180 top pinned the sweep at +19 deg.
    # This slot is also the exit route for the Pi's bottom-edge USB-C / HDMI cables.
    slot = box(62.0, 60.0, 101.0)
    slot.apply_translation((0, P["body_back_y"] + 22, P["tilt_axis_z"] - 37.5))
    shell = sub(shell, slot)

    # pivot hubs at the side walls, on the tilt axis (fuse through the wall, behind the bezel)
    bx = P["head_w"] / 2 - 8
    bosses = []
    for sx in (-1, 1):
        b = cyl(P["pivot_boss_r"] + 3, 12.0, axis="x")   # spans past the outer wall to fuse;
        b.apply_translation((sx * bx, yt, zt))           # short: the r13 body was clipping the
        bosses.append(b)                                 # relocated Pi (clamp tubes hold the axle)
    # internal CLAMP BOSSES at x=+-30: the axle is gripped HERE, 8 mm from the bearings (the old
    # scheme clamped only at the side walls: 75.5 mm cantilevers on a Ø5 tube). Ø7 torque tubes
    # run from the clamp zone out to the pivot bosses / side walls.
    for sx in (-1, 1):
        t = cyl(7.0, 72.0, axis="x")
        t.apply_translation((sx * 63.0, yt, zt))     # spans |x| 27..99: through the pivot boss
        bosses.append(t)                             # into the side wall
    shell = uni([shell] + bosses)
    # axle bore: SNUG Ø5.1 through the clamp bosses; far-wall bores demoted to LOOSE Ø5.3
    # supports (they locate, the x=+-30 grubs grip).
    axle_bore = cyl(2.55, P["head_w"] + 10, axis="x")
    axle_bore.apply_translation((0, yt, zt))
    shell = sub(shell, axle_bore)
    for sx in (-1, 1):
        loose = cyl(2.65, 70, axis="x")
        loose.apply_translation((sx * 75.0, yt, zt))  # |x| 40..110: everything outboard is loose
        shell = sub(shell, loose)
        grub = cyl(1.25, 14); grub.apply_translation((sx * 30.0, yt, zt - 6))  # M2.5-grub pilot,
        shell = sub(shell, grub)                     # driven from below through the neck slot

    # camera: CM3 recessed inside the raised forehead behind the plain 4 mm wall (no lens
    # bump: the countersunk aperture clears the full 75 deg diagonal FoV with the pupil
    # ~3 mm behind the outer face). The board mounts front-face-in on 4x short M2 bosses on
    # the ceiling-hung PIER (see PARAMS "cam_pier_*": the wall below the pocket top has
    # nothing to root on, and the display panel band y>=25.03 forbids long bosses). The AF
    # housing passes a pier cutout; the barrel crosses over the module's top edge and pokes
    # ~0.5 into the wall bore. Ribbon drops from the board bottom into the open pocket.
    fy = P["body_front_y"]
    lz = P["cam_lens_z"]                                # lens optical axis height (world Z)
    bz = lz - P["cam_lens_dz"]                          # board center Z (lens is above board center)
    py1 = P["cam_pier_y1"]; py0 = py1 - P["cam_pier_t"]  # pier front/back faces (Y)
    # pier plate: from below the bottom boss row up INTO the ceiling (fused 1 mm past the
    # interior face at body_z_top - 4)
    pz0 = bz + P["cam_hole_z_bot"] - 3.0
    pz1 = P["body_z_top"] - 3.0
    pier = box(P["cam_pier_w"], P["cam_pier_t"], pz1 - pz0)
    pier.apply_translation((0, (py0 + py1) / 2, (pz0 + pz1) / 2))
    shell = uni([shell, pier])
    # AF-housing cutout through the pier (10.8 sq + 0.6/side)
    hcut = box(P["cam_house_wh"] + 1.2, P["cam_pier_t"] + 2, P["cam_house_wh"] + 1.2)
    hcut.apply_translation((0, (py0 + py1) / 2, lz))
    shell = sub(shell, hcut)
    # Ø6.3 through-bore + 45 deg/side countersink opening to Ø8.0 at the outer face
    bore = cyl(P["cam_bore_d"] / 2, 12, axis="y"); bore.apply_translation((0, fy - 2, lz))
    shell = sub(shell, bore)
    csk_r0, csk_r1 = P["cam_bore_d"] / 2, P["cam_csk_d"] / 2 + 2.0   # overshoot 2 past the face
    csk = frustum(csk_r1, csk_r0, csk_r1 - csk_r0)      # 45 deg/side, shrinking toward +Z
    csk.apply_transform(R(TAU / 4, (1, 0, 0)))          # +Z -> -Y: small end faces INTO the wall
    csk.apply_translation((0, fy + 2.0, lz))            # Ø8.0 lands exactly on the face plane
    shell = sub(shell, csk)
    # 4 short M2 boss pads on the pier back face (2 screwed, 2 locating); blind pilots
    for sx in (-1, 1):
        for dz in (P["cam_hole_z_top"], P["cam_hole_z_bot"]):
            bo = cyl(P["cam_boss_od"] / 2, P["cam_boss_len"], axis="y")
            bo.apply_translation((sx * P["cam_hole_dx"] / 2, py0 - P["cam_boss_len"] / 2,
                                  bz + dz))
            shell = uni([shell, bo])
            pil = cyl(P["cam_boss_pilot_r"], 3.8, axis="y")
            pil.apply_translation((sx * P["cam_hole_dx"] / 2,
                                   py0 - P["cam_boss_len"] + 1.9, bz + dz))
            shell = sub(shell, pil)

    # LED-strip recess in the forehead, left of the camera (design ref): shallow slot cut
    # into the face wall; the led_strip part (build()) sits in it flush with the face.
    slot_led = box(P["led_slot_w"], P["led_slot_d"] + 1.0, P["led_slot_h"])
    slot_led.apply_translation((P["led_cx"], fy - P["led_slot_d"] / 2 + 0.5, P["led_cz"]))
    shell = sub(shell, slot_led)

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
    # side posts pulled in 5 (old +6 put them at x=+-102.5, half-proud of the wall corner)
    hw, hh = P["screen_w"] / 2 + 1, P["screen_h"] / 2 + 5
    ys = -(P["screen_d"] / 2 + P["bezel_back"])   # split plane in screen-local Y
    # bottom fixings are a PAIR at x=+-40 (a bottom-CENTER post swept into the neck column at
    # forward tilt; nothing on the neck reaches past |x|=26, so +-40 clears at every angle).
    # TOP fixings are also a PAIR at x=+-40: a top-center post's M3 shank ran through the CM3
    # camera board (x=0), and the raised ceiling needs the posts at local z=body_z_top-5-178
    # to stay fused to it. Side posts sit at 0.75*hh, above the right-wall Pi I/O slot.
    zt_post = P["body_z_top"] - 5.0 - P["screen_cz"]
    return [(-40, ys, zt_post), (40, ys, zt_post), (-40, ys, -hh), (40, ys, -hh),
            (-hw, ys, hh * 0.75), (hw, ys, hh * 0.75),
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

    # (Pi 5 standoffs removed: the Pi mounts on the display's OWN back standoffs, so it comes
    # in with the screen module. The back cover only has to CLEAR the combined stack.)
    zt = P["tilt_axis_z"]

    # screen retention: 4x M3 into the display's OWN outer case-mount holes (126.2 x 65.65).
    # The factory holes are threaded bosses in the metal back-pan and OPEN BACKWARD (-Y); a
    # bezel boss running forward from the tab plane passes THROUGH the glass (front 30.99,
    # measured 69/50k screen samples inside the old bosses). So the screen mounts on REAR
    # STANDOFFS on head_back: Ø9 pillars from the inner back wall (y=-27) forward to the
    # display boss REAR plane (hole plane - scr_boss_lip = 22.53; the raised boss around each
    # factory hole spans the last 2.5 mm -- landing on the hole plane buried the standoff in
    # the boss, stage-4 D1), with a Ø6.5 driver channel + short M3 seat so a stock M3x12
    # reaches the display from behind. At x=+-63 they clear the Pi stack (|x|<=48.1), the
    # clamp tubes (z 171..185 vs rows 146.2/211.8), the louvres, the neck and io_side slots.
    wall_in = P["body_back_y"] + P["head_wall"]          # inner back wall (-27)
    for lp in P["scr_mount_pts"]:
        w = (sp @ np.append(lp, 1.0))[:3]
        w[1] -= P["scr_boss_lip"] + P["scr_seat_clear"]  # bearing face = boss rear plane
        sl = w[1] - wall_in                              # standoff length (49.45)
        b = cyl(P["scr_boss_r"], sl, axis="y"); b.apply_translation((w[0], wall_in + sl / 2, w[2]))
        back = uni([back, b])
        # deep Ø6.5 screw-head/driver channel from the back wall, stopping 6 short of the tab
        ch = cyl(3.25, sl - 6 + 4, axis="y")
        ch.apply_translation((w[0], P["body_back_y"] - 4 + (sl - 6 + 8) / 2, w[2]))
        back = sub(back, ch)
        # M3 clearance through the remaining 6 mm seat (screw threads into the display pan)
        c = cyl(P["scr_m3_clear_r"], 16, axis="y"); c.apply_translation((w[0], w[1] - 3, w[2]))
        back = sub(back, c)

    _color(bezel, "cradle"); bezel.metadata["name"] = "head_bezel"
    _color(back, "back"); back.metadata["name"] = "head_back"
    return bezel, back


def build_head_rails():
    """Orange side accent rails (design-ref front.jpg): vertical rounded pads standing proud
    of the head side walls' FLAT band. Cosmetic two-tone parts, printed separately in orange;
    fixing (glue vs 2x M3 from inside) decided at the print pass."""
    rails = []
    for sx, nm in ((-1, "trim_rail_L"), (1, "trim_rail_R")):
        r = rounded_box(P["rail_h"], P["rail_d"], P["rail_t"], 8.0)   # X=h, Y=d, extrude Z=t
        r.apply_transform(R(TAU / 4, (0, 1, 0)))     # footprint height -> Z, thickness -> +X
        x = P["head_w"] / 2 if sx > 0 else -(P["head_w"] / 2 + P["rail_t"])
        r.apply_translation((x, 0, P["rail_cz"]))    # thickness spans wall..wall+rail_t
        _color(r, "accent"); r.metadata["name"] = nm
        rails.append(r)
    return rails


def build_led_strip():
    """WS2812-stick placeholder in the forehead recess (design-ref front.jpg: a row of
    discrete LEDs left of the camera). Thin base board in the recess + 8 round emitters
    poking 0.3 proud of the face. Wiring drops behind the wall at the print pass."""
    fy = P["body_front_y"]
    base = box(P["led_slot_w"] - 1.0, 0.8, P["led_slot_h"] - 1.0)
    base.apply_translation((P["led_cx"], fy - P["led_slot_d"] + 0.4, P["led_cz"]))
    dots = [base]
    for i in range(8):
        d = cyl(1.2, P["led_slot_d"] + 0.3, axis="y", sections=24)
        d.apply_translation((P["led_cx"] - 16.1 + i * 4.6,
                             fy - (P["led_slot_d"] - 0.3) / 2, P["led_cz"]))
        dots.append(d)
    strip = uni(dots)
    _color(strip, "led"); strip.metadata["name"] = "led_strip"
    return strip


def build_antenna():
    """Knurled antenna stub on the head top face, right side (design-ref; cosmetic --
    the Pi's WiFi is internal). Separate print: collar + shaft + dome, knurl read via
    shallow ring grooves. Fixing (spigot + glue vs M3 from inside) at the print pass."""
    zt = P["body_z_top"]
    collar = cyl(P["ant_collar_d"] / 2, P["ant_collar_h"])
    collar.apply_translation((0, 0, P["ant_collar_h"] / 2))
    shaft = cyl(P["ant_d"] / 2, P["ant_h"])
    shaft.apply_translation((0, 0, P["ant_h"] / 2))
    dome = trimesh.creation.icosphere(subdivisions=2, radius=P["ant_d"] / 2)
    dome.apply_translation((0, 0, P["ant_h"]))
    ant = uni([collar, shaft, dome])
    for gz in (10.0, 16.0, 22.0):                     # knurl-read ring grooves
        groove = trimesh.creation.torus(major_radius=P["ant_d"] / 2, minor_radius=0.7)
        groove.apply_translation((0, 0, gz))
        ant = sub(ant, groove)
    ant.apply_translation((P["ant_x"], P["ant_y"], zt))
    _color(ant, "antenna"); ant.metadata["name"] = "antenna_stub"
    return ant


def build_cam_pod():
    """Cosmetic raised eye-pod over the recessed camera aperture (design-ref front.jpg).
    Separate charcoal print on the bezel face; 45 deg flared bore clears the CM3 FoV."""
    fy, lz = P["body_front_y"], P["cam_lens_z"]
    pod = rounded_box(P["cam_pod_w"], P["cam_pod_h"], P["cam_pod_t"], 7.0)
    pod.apply_transform(R(-TAU / 4, (1, 0, 0)))      # extrude +Y, footprint XZ
    pod.apply_translation((0, fy, lz))
    bore = frustum(P["cam_csk_d"] / 2 + P["cam_pod_t"] + 0.5, P["cam_csk_d"] / 2,
                   P["cam_pod_t"] + 0.5)             # 45 deg/side flare, small end at the face
    bore.apply_transform(R(TAU / 4, (1, 0, 0)))      # shrink toward -Y (into the wall)
    bore.apply_translation((0, fy + P["cam_pod_t"] + 0.25, lz))
    pod = sub(pod, bore)
    _color(pod, "camera"); pod.metadata["name"] = "camera_pod"   # /camera/ in the viewer PAL
    return pod


def build_hatch_frame():
    """Orange chamfer-look frame proud of the head back face (design-ref back.jpg).
    Separate orange print over the service area; the existing louvres + cable port are
    the 'hatch' inside it. Bottom band notched clear of the neck-slot sweep envelope."""
    w, h, bd, t = (P["hatch_frame_w"], P["hatch_frame_h"],
                   P["hatch_frame_band"], P["hatch_frame_t"])
    outer = rounded_box(w, h, t, 12.0)
    inner = rounded_box(w - 2 * bd, h - 2 * bd, t + 2, 8.0)
    inner.apply_translation((0, 0, -1))
    ring = sub(outer, inner)
    ring.apply_transform(R(TAU / 4, (1, 0, 0)))      # footprint XZ, extrusion -Y
    ring.apply_translation((0, P["body_back_y"], P["hatch_frame_cz"]))
    # notch the bottom band over the neck slot (x +-31, wall open to z=191): the frame
    # may not reach into the neck's tilt-sweep clearance
    notch = box(66.0, 2 * t + 2, 70.0)
    notch.apply_translation((0, P["body_back_y"] - t, P["tilt_axis_z"] - 22.0))
    ring = sub(ring, notch)
    _color(ring, "accent"); ring.metadata["name"] = "trim_hatch_frame"
    return ring


def _limb(p0, p1, w=9.0, d=11.0):
    """Arm segment between two (y,z) points, long axis in the YZ plane, X extent w."""
    vy, vz = p1[0] - p0[0], p1[1] - p0[1]
    L = float(np.hypot(vy, vz))
    seg = box(w, d, L + d * 0.6)
    seg.apply_transform(R(-np.arctan2(vy, vz), (1, 0, 0)))    # +Z -> segment direction
    seg.apply_translation((0, (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2))
    return seg


def build_arms():
    """Two articulated gripper arms (design-ref, PLACEHOLDER): shoulder disc on the side
    rail, upper arm down, forearm forward, C-claw opening forward with square finger
    pads. Static tucked pose per front.jpg; joints are cosmetic discs until the arm
    mechanism pass. Limb X-width stays 9 so nothing reaches back past the rail face."""
    S, E, W = (0.0, 130.0), (8.0, 88.0), (48.0, 70.0)    # shoulder/elbow/wrist (y,z)
    C = (62.0, 68.0)                                     # claw ring center
    arms = []
    for sx, nm in ((-1, "arm_L"), (1, "arm_R")):
        parts = [_limb(S, E, w=9.0, d=15.0), _limb(E, W, w=9.0, d=15.0)]
        for (py, pz), r in ((S, 11.0), (E, 9.5), (W, 8.5)):
            j = cyl(r, 10.0, axis="x"); j.apply_translation((0, py, pz))
            parts.append(j)                          # h10: disc face LANDS on the rail
                                                     # face (107.5), no burial
        claw = sub(cyl(18.0, 13.0, axis="x", sections=48),
                   cyl(10.0, 15.0, axis="x", sections=48))
        notch = box(14.0, 22.0, 14.0); notch.apply_translation((0, 13.0, 0))
        claw = sub(claw, notch)                          # C opening faces +Y (forward)
        for szn in (-1, 1):                              # square finger pads at the C tips
            pad = box(13.0, 7.0, 6.5)
            pad.apply_translation((0, 13.5, szn * 10.5))
            claw = uni([claw, pad])
        claw.apply_translation((0, C[0], C[1]))
        parts.append(claw)
        arm = uni(parts)
        arm.apply_translation((sx * P["arm_x"], 0, 0))
        _color(arm, "arm"); arm.metadata["name"] = nm
        arms.append(arm)
    return arms


def build_neck_clevis():
    """Neck column rising to a two-cheek clevis that grips the tilt axle under the head."""
    zt = P["tilt_axis_z"]
    yt = P["tilt_axis_y"]
    z0 = P["base_h"]                       # sits on the pan platform / base top (world Z)
    ny = P["neck_y"]
    parts = []

    col_h = P["neck_top_z"] - z0
    col = rounded_box(P["neck_w"], P["neck_d"], col_h, P["neck_round"])
    col.apply_translation((0, ny, z0))       # extrude_polygon is z=0..h, so lift to z0
    parts.append(col)

    # cheek-root BLOCK on the column top rear: the stage-5 column sits forward (ny=-17) but
    # the cheek slant that clears the -30 swept stack must still root around y=-33; this
    # block bridges column top -> cheek bottoms (and fuses with the cradle arm above it).
    root = box(52.0, 14.0, 10.0)
    root.apply_translation((0, -33.0, zt - 23.0))         # y -40..-26; z rides the axle
                                                          # (bridges column top -> cheeks)
    parts.append(root)

    # two cheeks rising from the cheek-root block to the axle at (cx, yt, zt). Stage 2R
    # re-profile: the box stops AT the axle center (the old +10 overshoot past the axle poked
    # into the display module's back envelope); the bearing land is a Ø19 HOOP centered on
    # the axle. Stage 5: the bottom anchor is DECOUPLED from neck_y (fixed at y=-33, z=155 on
    # the root block) -- anchoring at the new ny=-17 made the cheek front face graze the
    # resting stack (y=-7) and bury 11 mm into the -30 swept stack.
    for sx in (-1, 1):
        cx = sx * P["clevis_half"]
        top = np.array([cx, yt, zt])
        bot = np.array([cx, -33.0, zt - 23.0])
        length = np.linalg.norm(top - bot)
        d = (top - bot) / length
        cheek = box(P["cheek_t"], 20.0, length + 20)
        v = np.cross([0, 0, 1.0], d); s = np.linalg.norm(v)
        if s > 1e-6:
            cheek.apply_transform(R(np.arctan2(s, np.dot([0, 0, 1.0], d)), v / s))
        cheek.apply_translation((top + bot) / 2 - d * 10.0)   # top end flush with the axle
        hoop = cyl(9.5, P["cheek_t"], axis="x")               # bearing-seat land around the axle
        hoop.apply_translation(top)
        parts += [cheek, hoop]

    # tilt WORM-motor bracket: the motor shaft runs along +Y (perpendicular to the tilt axle) and
    # carries the worm; the worm meshes the wheel on the axle. center distance = wheel_r + worm_r.
    wx = P["worm_wheel_x"]
    cd = worm_cd()
    wz = zt - cd
    # Stage 2R: the worm group sits behind the axle (face_y offset 4 -> 8 -> 9.5 in stage 5):
    # at -30 tilt the stack's rear (GPIO pins) sweeps down-back past the worm tail. The 9.5
    # offset + worm_len 14 puts the thread span at y -32..-16 (still covering the wheel
    # contact at yt) with a bare Ø5 stub forward of -16 for the cradle (stage-4 D2 fix).
    face_y = yt - 0.5 * P["worm_len"] - 9.5              # motor mount face (behind the worm)
    # plate shortened 46 -> 36 tall (same bottom): the old top (wz+23) clipped the head's back
    # wall above the neck slot during the +10..+25 deg sweep
    plate = box(46, 4, 36); plate.apply_translation((wx, face_y, wz - 5))
    parts.append(plate)
    # gusset tying the bracket down onto the neck column top (offset +X, clear of the can pocket).
    # Front held at yt-2: the -30 swept stack digs to y -18.2 in the z 152..156 band.
    gy0, gy1 = face_y, yt - 4.0
    gus = box(10, abs(gy1 - gy0) + 4, 22)
    gus.apply_translation((wx + 19, (gy0 + gy1) / 2, (wz + P["neck_top_z"]) / 2))
    parts.append(gus)
    # outboard support for the worm's far end (the 28BYJ shaft only reaches ~6 mm into the worm;
    # the Ø5 tail stub rides an open-top CRADLE groove; worm separation force presses DOWN into
    # it, so the open top is load-correct). Stage 2R shape: at -30 tilt the stack's rear sweeps
    # to y -18.2 in the z 148..160 band but frees everything above z~168. Stage 5 (D2 fix):
    # the worm's full-radius threads (r 5.34, now ending at y=-16) used to run THROUGH the
    # cradle band; the groove band now sits at y -15.5..-13 on the bare Ø5 tail stub, and the
    # cradle material behind it (riser top + pad rear, y<=-15.5) is split into two side PRONGS
    # by an envelope-relief bore (r 5.9 > thread r 5.34, cut below after the union) about the
    # worm axis so the worm can rotate. The arm stays under the thread envelope (top z=160
    # < wz-5.34); the pad keeps its stage-2R-proven front (y=-13) and z band (164..166.5).
    arm = box(18, 16, 6); arm.apply_translation((wx, yt - 10.0, wz - 9.5))        # y -36..-20
    riser = box(18, 5, 16.5); riser.apply_translation((wx, yt - 4.5, wz - 8.25))  # z 150..166.5
    pad = box(18, 12, 2.5); pad.apply_translation((wx, -19.0, wz - 1.25))         # y -25..-13
    parts += [arm, riser, pad]

    neck = uni(parts)
    # column front CHIN NOTCH, re-derived for the stage-5 inboard column (front face now
    # ny+23=+6): at -30 tilt the head's bottom-front wall band, lower front wall/glass AND
    # the display stack's lower back all arc down-back through the column front zone -- the
    # measured swept envelope reaches y=-16.7 near z~102 (shell chin) and y=-14 right up to
    # the column top (display back band at z 140..150), so the WHOLE front of the column
    # above z=94 steps back to y=-19.5 (2.7+ clear of the sweep; head min sweep z is 97.2).
    # Below z=94 the column keeps its full section (bolt bosses z 52..64); the cable channel
    # (front wall y=-22) stays closed behind the notch face.
    notch = box(64.0, 32.0, 57.0)
    notch.apply_translation((0, -3.5, zt - 55.5))       # y -19.5..12.5; z rides the axle
                                                        # (swept-envelope chin clearance)
    neck = sub(neck, notch)
    # axle clearance bore (Ø5 axle) through the cheeks
    bore = cyl(P["axle_d"] / 2 + 0.4, 2 * P["clevis_half"] + 4 * P["cheek_t"], axis="x")
    bore.apply_translation((0, yt, zt))
    neck = sub(neck, bore)
    # 695-2RS bearing seats: OPEN FLUSH to each cheek's INNER face (the old 0.75 mm membrane made
    # the bearing uninsertable). Bore Ø12.85 = press allowance on the Ø13 OD; the bearing presses
    # in from inside the clevis gap, 3.5 mm outer wall remains (loose Ø5.8 axle pass-through).
    seat_r = 12.85 / 2
    inner_x = P["clevis_half"] - P["cheek_t"] / 2                 # cheek inner face (18)
    for sx in (-1, 1):
        seat = cyl(seat_r, P["brg_w"] + 1.5, axis="x")
        seat.apply_translation((sx * (inner_x - 1.0 + (P["brg_w"] + 1.5) / 2), yt, zt))
        neck = sub(neck, seat)
    # worm-motor shaft clearance (Ø10 clears the Ø9.1 shaft boss) through the bracket plate
    sh = cyl(5.0, 20, axis="y"); sh.apply_translation((wx, face_y, wz)); neck = sub(neck, sh)
    # M4 ear holes at the CAN axis (the 28BYJ ears center on the CAN, not the shaft: the shaft
    # is offset motor_shaft_off; the motor is rolled so the can hangs BELOW the worm axis and
    # the ears run horizontal). The old holes were drilled at the shaft axis: 7.9 mm off.
    can_z = wz - P["motor_shaft_off"]
    for dxe in (-P["motor_ear_cc"] / 2, P["motor_ear_cc"] / 2):
        ear = cyl(P["motor_ear_hole_d"] / 2, 20, axis="y")
        ear.apply_translation((wx + dxe, face_y, can_z)); neck = sub(neck, ear)
    # Ø29 CAN POCKET behind the plate (the motor body was buried in solid neck material):
    # clears the Ø28.25 can + Ø27.25 gearbox stack; separate relief for the blue wiring box.
    pocket = cyl(29.0 / 2, 32.5, axis="y")
    pocket.apply_translation((wx, face_y - 2 - 32.5 / 2 + 0.2, can_z))
    neck = sub(neck, pocket)
    wrelief = box(17.0, 19.0, 10.0)
    wrelief.apply_translation((wx, face_y - 21.4, can_z - 16.1))
    neck = sub(neck, wrelief)
    # ear-bar relief: the motor's 43 mm ear bar sits 9.5 behind the gear face and was clipping
    # the cheek's lower-rear corner; slot it clear (also gives M4 nut access)
    erelief = box(46.0, 4.0, 10.0)
    erelief.apply_translation((wx, face_y - 11.5, can_z))
    neck = sub(neck, erelief)
    # worm-thread envelope relief: Ø11.8 bore (thread tip r 5.34 + 0.56 running clearance)
    # about the worm axis over the threaded span (y -34..-15.5) -- splits the riser top / pad
    # rear into the two side prongs and lets the worm rotate free of the cradle (D2)
    relief = cyl(5.9, 18.5, axis="y"); relief.apply_translation((wx, -24.75, wz))
    neck = sub(neck, relief)
    # Ø5.4 half-groove across the cradle pad top (worm tail stub rides here, open top),
    # only over the bare-stub band forward of the threads (threads end y=-16)
    bush = cyl(2.7, 4.5, axis="y"); bush.apply_translation((wx, -14.25, wz)); neck = sub(neck, bush)
    # vertical cable channel down the column: 16x8 obround (was Ø12 -- a 5-pos JST-XH head
    # is 14.9 x 5.9 and must pass pre-crimped). Long axis along X, at (0, neck_chan_y):
    # pushed behind the column center so the chin notch (rear y=-19.5) leaves a full wall
    # in front of it (channel front y=-22).
    chan = extrude_polygon(sg.LineString([(-4, 0), (4, 0)]).buffer(4.0), P["neck_top_z"] - z0 + 30)
    chan.apply_translation((0, P["neck_chan_y"], z0 - 15))
    neck = sub(neck, chan)
    # 3 M3 PILOTS (Ø2.5 x 12 -- the old Ø3.5 was clearance, nothing bit) to bolt the neck down
    # to the pan platform. Stage 5: circle rad 16, clocked (270,30,150) -- with the column at
    # ny=-17 the old (90,210,330)/rad-12 put a hole 2 mm from the PAN AXIS, inside the
    # platform's D-bore hub. Keep in sync with build_pan_platform().
    for a in (270, 30, 150):
        rad = 16.0
        hx = rad * np.cos(np.radians(a)); hy = ny + rad * np.sin(np.radians(a))
        pilot = cyl(1.25, 14); pilot.apply_translation((hx, hy, z0 + 5))   # bites z0..z0+12
        neck = sub(neck, pilot)
    # tilt ULN2003 driver standoffs on the column BACK face (same pattern as the base's pan
    # driver mount; motor + driver both live on the pan group so their leads cross no joint)
    uln_y = ny - P["neck_d"] / 2                      # column back face
    for sx in (-1, 1):
        for sz in (-1, 1):
            # 8.5 long, buried 0.5 INTO the column: a face-tangent cylinder does not fuse
            # in uni() and exported as a disjoint floating body (stage-4 defect D4)
            b = cyl(3.0, 8.5, axis="y")
            b.apply_translation((sx * P["uln_w"] / 2, uln_y - 3.75, 110 + sz * P["uln_h"] / 2))
            neck = uni([neck, b])
            pil = cyl(1.25, 12, axis="y")
            pil.apply_translation((sx * P["uln_w"] / 2, uln_y - 3, 110 + sz * P["uln_h"] / 2))
            neck = sub(neck, pil)
    _color(neck, "neck")
    neck.metadata["name"] = "neck_clevis"
    return neck


def _T(x, y, z):
    m = np.eye(4); m[:3, 3] = (x, y, z); return m


def _pan_stack():
    """Derived Z's of the pan bearing stack -- single source of truth for base seat, race
    ring, balls and platform. Anchored at the deck top (base_h = platform top, flush):

        plate top      base_h                     52.0
        plate bottom   - pan_plate_t              44.4   (upper groove wraps 1.8 of ball)
        air gap          ball_d - 2*engage         2.4
        ring top       = plate_bot - gap          42.0   (lower groove wraps 1.8 of ball)
        seat floor     = ring_top - ring_t        37.0   (ring SITS on deck material)
        ball center    = ring_top - engage + r    43.2
    """
    plate_bot = P["base_h"] - P["pan_plate_t"]
    gap = P["pan_race_ball_d"] - 2 * P["pan_groove_engage"]
    ring_top = plate_bot - gap
    seat_floor = ring_top - P["pan_race_ring_t"]
    zball = ring_top - P["pan_groove_engage"] + P["pan_race_ball_d"] / 2
    return plate_bot, ring_top, seat_floor, zball


def build_pan_platform():
    # seated in the chassis deck recess, top FLUSH with the deck top; rides the lazy-Susan race
    z1 = P["base_h"]
    plate_bot, ring_top, seat_floor, zball = _pan_stack()
    plate = cyl(P["pan_plate_d"] / 2, P["pan_plate_t"], sections=96)
    plate.apply_translation((0, 0, z1 - P["pan_plate_t"] / 2))

    # rim REBATE: top band stepped to r45 -> an up-facing shoulder 3 below the top. The deck
    # clips reach over this shoulder to resist uplift (top-heavy head). The rebate is a full
    # ring because the platform pans past the 3 fixed clips.
    reb = sub(cyl(P["pan_plate_d"] / 2 + 2, 4.0, sections=96), cyl(45.0, 6.0, sections=96))
    reb.apply_translation((0, 0, z1 - 1.0))          # cut spans z1-3 .. z1+1
    plate = sub(plate, reb)

    # D-bore coupling hub on the underside. Hub bottom clears the motor's Ø9.1 boss (top at
    # gear_face+1.45) by 0.3 -- the old 12-long hub swallowed the whole gearbox face.
    zsh = z1 - 2 - (P["motor_body_h"] + P["motor_gear_h"] + P["motor_shaft_len"])   # can bottom
    gear_face = zsh + P["motor_body_h"] + P["motor_gear_h"]        # 40.25
    hub_bot = gear_face + 1.45 + 0.3                                # 42.0
    hub = cyl(7.0, plate_bot - hub_bot)
    hub.apply_translation((0, 0, (hub_bot + plate_bot) / 2))
    plate = uni([plate, hub])
    # D-profile ONLY over the flat zone (flats start gear_face + shaft_len - flat_len = 44.0;
    # +0.5 entry margin -- the old D spanned 36..56 and jammed on the round shaft section).
    # Flats snug (+0.075/side, they drive); round arcs +0.27/side LOOSE so the race locates
    # radially and the shaft only drives (mini-Oldham, kills the overconstraint). The grub
    # bore is gone: with loose arcs a grub would just re-introduce the radial fight.
    d_bot = gear_face + P["motor_shaft_len"] - P["motor_flat_len"] + 0.5           # 44.5
    dbore = dbore_neg(z1 - d_bot + 1, axis="z", flat_clear=0.075, round_clear=0.27)
    dbore.apply_transform(R(TAU / 4, (0, 0, 1)))     # motor_28byj cuts its flats facing +-Y;
    dbore.apply_translation((0, 0, (d_bot + z1 + 1) / 2))   # dbore_neg's face +-X -> align
    plate = sub(plate, dbore)
    # plain Ø5.3 round counterbore below the flats (round Ø4.93 shaft section passes freely)
    rb = cyl(5.3 / 2, d_bot - hub_bot + 4)
    rb.apply_translation((0, 0, (hub_bot + d_bot) / 2))
    plate = sub(plate, rb)

    # upper race groove: wraps pan_groove_engage (1.8) of ball up into the plate. Torus center
    # = ball top - minor r = zball - groove_clear -> ball top tangent to the groove ceiling.
    minor = P["pan_race_ball_d"] / 2 + P["pan_groove_clear"]
    groove = trimesh.creation.torus(P["pan_race_circle_d"] / 2, minor)
    groove.apply_translation((0, 0, zball - P["pan_groove_clear"]))
    plate = sub(plate, groove)

    # cable SLOT: 8-wide obround jogging the bundle from the neck channel (0, neck_chan_y)
    # inward to cable_exit inside the race ID. A 5-pos JST-XH head (14.9 x 5.9) passes the
    # slot lengthwise.
    ex, ey = P["cable_exit"]
    slot = extrude_polygon(sg.LineString([(0, P["neck_chan_y"]), (ex, ey)]).buffer(4.0), 40)
    slot.apply_translation((0, 0, z1 - 20))
    plate = sub(plate, slot)

    # 3 M3 clearance holes to bolt the neck down (MATCH the neck-base pilots: rad 16, clocked
    # 270/30/150 about (0, neck_y) -- see build_neck_clevis) with Ø6.5 head counterbores from
    # the UNDERSIDE, 4 deep. All 3 land on the solid top (r<=33+3.25), clear of the center
    # D-bore hub (nearest hole edge r 14.7 vs hub r 7), the rim rebate (r45+), the ball
    # groove (r 36.8..43.2) and the cable slot.
    for a in (270, 30, 150):
        rad = 16.0
        hx = rad * np.cos(np.radians(a)); hy = P["neck_y"] + rad * np.sin(np.radians(a))
        h = cyl(P["m3_clear_r"], 40.0); h.apply_translation((hx, hy, z1 - 4))
        plate = sub(plate, h)
        cb = cyl(3.25, 8.0); cb.apply_translation((hx, hy, plate_bot))
        plate = sub(plate, cb)
    _color(plate, "pan")
    plate.metadata["name"] = "pan_platform"
    return plate


def build_pan_race():
    """Captured-BB lazy-Susan lower race (fixed to the base) + the ball ring. The platform
    underside is the upper race (grooved in build_pan_platform). Balls sit on the pitch circle;
    the wide stance carries the top-heavy head without wobble."""
    cr = P["pan_race_circle_d"] / 2
    bd = P["pan_race_ball_d"]
    plate_bot, ring_top, seat_floor, zball = _pan_stack()
    # lower race: a grooved ring SITTING ON the chassis seat floor (see _pan_stack)
    ro, ri = cr + P["pan_race_w"] / 2, cr - P["pan_race_w"] / 2
    ring = sub(cyl(ro, P["pan_race_ring_t"]), cyl(ri, P["pan_race_ring_t"] + 2))
    ring.apply_translation((0, 0, seat_floor + P["pan_race_ring_t"] / 2))
    # groove wraps 1.8 of ball down into the ring top: torus center = ball bottom + minor r
    # = zball + groove_clear -> ball rests tangent on the groove floor (was centered AT the
    # ball with minor r ball+0.4 -> the plate sank 3 mm and the groove floor was 0.1 thin).
    groove = trimesh.creation.torus(cr, bd / 2 + P["pan_groove_clear"])
    groove.apply_translation((0, 0, zball + P["pan_groove_clear"]))
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


def build_pan_clips():
    """3 L-clips at 120deg, screwed into deck pockets around the pan seat: each tab reaches
    over the platform's rim-rebate shoulder to resist UPLIFT (nothing else stops the
    top-heavy head lifting the platform off the balls). Everything stays AT or BELOW the
    deck top: the neck column sweeps r ~15..63 above z=base_h when panning, so a clip
    standing proud there would be sheared off -- that's also why the platform gets a rebate
    (engagement below the top) instead of the clips overhanging the top surface.
    Separate screwed parts: drop the balls + platform in first, then the clips."""
    z1 = P["base_h"]
    clips = None
    for a in (90, 210, 330):
        # built at azimuth 90 (+Y), then rotated into place about the pan axis
        body = box(14, 9, 7); body.apply_translation((0, 53.5, z1 - 3.5))       # r 49..58
        tab = box(14, 4.1, 2.6); tab.apply_translation((0, 47.45, z1 - 1.3))    # r 45.4..49.5
        c = uni([body, tab])                     # tab underside z1-2.6 = shoulder + 0.4 clear
        thr = cyl(P["m3_clear_r"], 20); thr.apply_translation((0, 53.5, z1 - 4))
        c = sub(c, thr)                          # M3 through, into the deck pilot below
        cb = cyl(3.25, 6.8); cb.apply_translation((0, 53.5, z1))
        c = sub(c, cb)                           # head cbore z1-3.4: head sits 0.4 sub-flush
        c.apply_transform(R((a - 90) * DEG, (0, 0, 1)))
        clips = c if clips is None else uni([clips, c])
    _color(clips, "pan"); clips.metadata["name"] = "pan_clips"
    return clips


def build_fascia():
    """Chassis front-fascia parts (design-ref front.jpg): orange grille surround + side
    fins (one orange print), HC-SR04 ultrasonic placeholder (silver barrels through the
    wall), amber corner lamps, white LED dot strip. Returns a list of scene parts."""
    fw = P["chassis_l"] / 2                          # front face y=78
    parts = []
    # orange surround ring + 3 vertical fins per side, as ONE orange part
    gw, gh, bd, t = P["grille_w"], P["grille_h"], P["grille_band"], P["grille_t"]
    ring = sub(rounded_box(gw, gh, t, 6.0),
               rounded_box(gw - 2 * bd, gh - 2 * bd, t + 2, 4.0).apply_translation((0, 0, -1)))
    ring.apply_transform(R(-TAU / 4, (1, 0, 0)))     # extrude +Y (proud of the front face)
    ring.apply_translation((0, fw, P["grille_cz"]))
    fins = [ring]
    for sx in (-1, 1):
        for fx in (35.0, 41.0, 47.0):
            f = box(3.0, 2.0, 16.0)
            f.apply_translation((sx * fx, fw + 1.0, P["grille_cz"]))
            fins.append(f)
    fascia = uni(fins)
    _color(fascia, "accent"); fascia.metadata["name"] = "trim_fascia"
    parts.append(fascia)
    # ultrasonic: board placeholder against the inner wall + 2 mesh barrels through it
    us = [box(45.7, 1.6, 20.9).apply_translation((0, fw - 5.0 - 0.8, P["us_cz"]))]
    for sx in (-1, 1):
        b = cyl(P["us_d"] / 2, 13.0, axis="y", sections=48)
        b.apply_translation((sx * P["us_dx"], fw - 5.0 + 6.5 - 0.75, P["us_cz"]))
        us.append(b)
    uspod = uni(us)
    _color(uspod, "sensor"); uspod.metadata["name"] = "sensor_us"
    parts.append(uspod)
    # amber indicator lamps at the fascia corners
    for sx, nm in ((-1, "lamp_L"), (1, "lamp_R")):
        l = rounded_box(12.0, 7.0, 2.0, 2.5)
        l.apply_transform(R(-TAU / 4, (1, 0, 0)))
        l.apply_translation((sx * P["lamp_x"], fw, P["lamp_cz"]))
        _color(l, "lamp"); l.metadata["name"] = nm
        parts.append(l)
    # white LED dot strip at the bottom lip: slim base + 7 round emitters
    fl = [box(36.0, 1.0, 3.0).apply_translation((0, fw + 0.5, P["fled_cz"]))]
    for i in range(7):
        d = cyl(1.3, 1.6, axis="y", sections=24)
        d.apply_translation((-15.0 + i * 5.0, fw + 1.4, P["fled_cz"]))
        fl.append(d)
    led = uni(fl)
    _color(led, "led"); led.metadata["name"] = "led_front"
    parts.append(led)
    # REAR: orange frame panel (wall shows through as the hatch) + silver cylinder pod
    rp = sub(rounded_box(72.0, 22.0, 2.5, 6.0),
             box(44.0, 14.0, 8.0))
    rp.apply_transform(R(TAU / 4, (1, 0, 0)))        # extrude -Y (proud of the REAR face)
    rp.apply_translation((0, -fw, P["rear_panel_cz"]))
    _color(rp, "accent"); rp.metadata["name"] = "trim_rear"
    parts.append(rp)
    rc = cyl(P["rear_cyl_d"] / 2, 9.0, axis="y", sections=48)
    rc.apply_translation((P["rear_cyl_x"], -fw - 4.5, P["rear_cyl_cz"]))   # lands ON the wall
    _color(rc, "sensor"); rc.metadata["name"] = "sensor_rear"
    parts.append(rc)
    return parts


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
    plate_bot, ring_top, seat_floor, zball = _pan_stack()
    body = rounded_box(P["chassis_w"], P["chassis_l"], h, 14.0)
    body.apply_translation((0, 0, z0))
    # cavity stops deck_t below the top -> a solid DECK spans z1-deck_t..z1. (The old cavity
    # reached z1: the seat cut was a no-op and the race/balls/platform floated in air.)
    cav = rounded_box(P["chassis_w"] - 2 * wall, P["chassis_l"] - 2 * wall,
                      h - floor - P["deck_t"], 12.0)
    cav.apply_translation((0, 0, z0 + floor))
    body = sub(body, cav)
    # pan seat: Ø(plate+2) recess cut into the deck, its FLOOR carrying the lower race ring.
    # depth = plate 7.6 + ball air gap 2.4 + ring 5 = 15 -> floor at z 37 (see _pan_stack).
    seat_depth = z1 - seat_floor
    seat = cyl(P["pan_plate_d"] / 2 + 1.0, seat_depth, sections=96)
    seat.apply_translation((0, 0, z1 - seat_depth / 2)); body = sub(body, seat)
    # clearance through the deck membrane under the seat: Ø30 at the pan axis (platform hub +
    # shaft) AND Ø30 at the CAN axis (the 28BYJ gearbox stack, r13.6 about the can, crosses
    # z 32..40.25). Both circles stay inside the race ring ID (r 34) -> the seat floor holds.
    mx = -P["motor_shaft_off"]
    for cx_ in (0.0, mx):
        cbore = cyl(15.0, 30.0); cbore.apply_translation((cx_, 0, seat_floor - 2))
        body = sub(body, cbore)
    # cable pass through the deck: 16x8 obround (5-pos JST-XH head is 14.9 x 5.9) at
    # cable_exit, INSIDE the race ID -- the old Ø12 pass at (0, neck_y) punched through the
    # race-ring footprint (r 34..46), where the fixed ring blocks it anyway. Aligned with the
    # platform slot's exit at pan=0; the service loop below takes the pan winding.
    ex, ey = P["cable_exit"]
    u = np.array([ex - 0.0, ey - P["neck_chan_y"]]); u = u / np.linalg.norm(u)
    cbl = extrude_polygon(sg.LineString([(ex - 4 * u[0], ey - 4 * u[1]),
                                         (ex + 4 * u[0], ey + 4 * u[1])]).buffer(4.0), 22.0)
    cbl.apply_translation((0, 0, seat_floor - 11)); body = sub(body, cbl)

    # pan-motor PEDESTAL: top face AT the ear-bar underside so the M3s clamp the ears down.
    # (The old 6-thick pad sank the can 5.5 into the floor while the ears floated 12.4 above.)
    zsh = z1 - 2 - (P["motor_body_h"] + P["motor_gear_h"] + P["motor_shaft_len"])   # can bottom
    ear_z = zsh + P["motor_body_h"] - 1.0            # ear-bar underside (30.25)
    ped = rounded_box(48, 48, ear_z - (z0 + floor), 6.0)
    ped.apply_translation((mx, 0, z0 + floor))
    body = uni([body, ped])
    # ULN2003 standoffs (x2 boards eventually; second mount is a deferred detailing task).
    # Board centre shifted +20 in Y: at y=0 the board envelope hit the drive_R TT can
    # (y -23.4..-9.9, x up to 52.5).
    for sx in (-1, 1):
        for sy in (-1, 1):
            b = cyl(3.0, 8); b.apply_translation((38 + sx * P["uln_w"] / 2, 20 + sy * P["uln_h"] / 2, z0 + floor))
            body = uni([body, b])
    # Ø29 can relief bored from the pedestal top down to the floor (can Ø28.25 drops in,
    # bottom hovers 0.45 above the floor; the ears take the clamp load)
    canb = cyl(29.0 / 2, ear_z + 2 - (z0 + floor))
    canb.apply_translation((mx, 0, (z0 + floor + ear_z + 2) / 2))
    body = sub(body, canb)
    # wiring-box relief: the blue box protrudes past the can on -X (to x ~ -28); open the
    # pocket clear through the pedestal's -X face so the leads route out sideways
    wrel = box(22, P["motor_wbox_w"] + 3, ear_z + 2 - (z0 + floor))
    wrel.apply_translation((mx - 16, 0, (z0 + floor + ear_z + 2) / 2))
    body = sub(body, wrel)
    # M3 PILOTS Ø2.5 at the ear holes (can-axis Y = +-17.5; Ø3.5 was clearance, nothing bit)
    for dy in (-P["motor_ear_cc"] / 2, P["motor_ear_cc"] / 2):
        e = cyl(1.25, 16); e.apply_translation((mx, dy, ear_z - 4))
        body = sub(body, e)

    # pan-clip pockets: 3 at 120deg around the seat rim, floors 7 below the deck top so the
    # clips finish FLUSH (see build_pan_clips for why nothing may stand proud of the deck).
    # M3 pilot Ø2.5 x 8 into the remaining deck under each pocket floor.
    for a in (90, 210, 330):
        # pocket inner edge at r48 -- INSIDE the round seat wall (circle is at y 48.5 when
        # x = +-7), else slivers of deck survive between the straight edge and the circle
        # exactly where the clip tab corners land
        pk = box(14.4, 10.2, 8.0); pk.apply_translation((0, 53.1, z1 - 3.0))    # z 45..53
        pk.apply_transform(R((a - 90) * DEG, (0, 0, 1)))
        body = sub(body, pk)
        pil = cyl(1.25, 8.0); pil.apply_translation((0, 53.5, z1 - 11.0))       # z 37..45
        pil.apply_transform(R((a - 90) * DEG, (0, 0, 1)))
        body = sub(body, pil)
    usb = box(14, 12, 8)                              # USB-C power entry in the rear wall
    usb.apply_translation((0, -P["chassis_l"] / 2, z0 + 12)); body = sub(body, usb)
    # front-fascia cuts (design ref): hex grille field (blind 2.5, cosmetic-vent; decide
    # through-vent at the print pass) + Ø16.6 ultrasonic barrel passes through the wall
    fw = P["chassis_l"] / 2
    hexes = []
    for r_i, zr in enumerate((42.0, 46.0, 50.0)):
        off = 2.1 if r_i % 2 else 0.0
        for k in range(-6, 7):
            hx_x = k * 4.2 + off
            if abs(hx_x) > 24.0:
                continue
            hx = hex_prism(3.0, 4.0)
            hx.apply_transform(R(TAU / 4, (1, 0, 0)))          # axis Z -> Y
            hx.apply_translation((hx_x, fw - 0.5, zr))         # cuts 2.5 into the 5 wall
            hexes.append(hx)
    body = sub(body, uni(hexes))
    for sx in (-1, 1):
        us = cyl(P["us_d"] / 2 + 0.3, 12, axis="y")
        us.apply_translation((sx * P["us_dx"], fw - 2.5, P["us_cz"]))
        body = sub(body, us)
    for i in range(-2, 4):                            # side ventilation slots (i=-3 dropped: the
        v = box(12, 5, 16); v.apply_translation((0, i * 16, z0 + h / 2))    # TT nub pocket +
        v2 = v.copy(); v.apply_translation((P["chassis_w"] / 2, 0, 0))      # shaft recess live
        v2.apply_translation((-P["chassis_w"] / 2, 0, 0))                   # at y -49/-60)
        body = sub(sub(body, v), v2)

    # --- TT drive-motor mount (both walls; see motor_tt + reference/tt-motor-1079893/NOTES.md).
    # Shaft axis at (y=-wb/2, z=_track_zc()); gearbox face 0.1 inside the wall inner face.
    zs, ys = _track_zc(), -P["track_wheelbase"] / 2   # 25.32, -60
    xw = P["chassis_w"] / 2                           # wall outer face (60); inner face 55
    axm = xw - 5.0 - P["tt_gearbox"][2] / 2 - 0.1     # motor axis x (45.58)
    for s in (-1, 1):
        ph = cyl(4.0, 12, axis="x"); ph.apply_translation((s * (xw - 2.5), ys, zs))
        body = sub(body, ph)                          # Ø8 shaft pass-through (clears Ø7.2 boss)
        rec = cyl(8.5, 2.2, axis="x"); rec.apply_translation((s * (xw - 0.9), ys, zs))
        body = sub(body, rec)                         # outer recess -> 3 mm web, hub sits close
        for dz in (-8.75, 8.75):                      # M3 through gearbox + wall, nut in the gap
            mh = cyl(1.6, 12, axis="x"); mh.apply_translation((s * (xw - 2.5), ys + 20.3, zs + dz))
            body = sub(body, mh)
        nubp = cyl(2.1, 2.3, axis="x"); nubp.apply_translation((s * (xw - 5.0 + 1.1), ys + 11.0, zs))
        body = sub(body, nubp)                        # Ø4.2 x 2.2 locating-nub pocket, inner face
        # deck pocket over the motor: gearbox/can top at z 36.52 but the cavity ceiling is 32;
        # cut to 36.8 (pan-seat floor is 37 and the race ring footprint r34..46 stays clear:
        # nearest pocket corner is at r 50.2)
        dkp = box(19.4, 64.7, 4.9); dkp.apply_translation((s * (xw - 14.5), -39.65, 34.35))
        body = sub(body, dkp)
        # cavity-corner relief: the cavity's r12 rounded corner leaves body material where the
        # rectangular gearbox rear corner sits (probed 318.5 mm3) -- square it off locally
        crn = box(7.0, 14.2, 24.9); crn.apply_translation((s * (xw - 8.4), -65.1, 24.35))
        body = sub(body, crn)
        tabp = box(4.2, 5.7, 6.4); tabp.apply_translation((s * axm, ys - 14.15, zs))
        body = sub(body, tabp)                        # front-tab pocket in the rear wall (1 skin)
        tabh = cyl(1.4, 14, axis="x"); tabh.apply_translation((s * axm, ys - 14.0, zs))
        body = sub(body, tabh)                        # Ø2.8 tab-hole continuation (M2.5 self-tap)
        # idler tension arm: wall -> slotted plate inside the front loop arc (radial < 15.7 so
        # the wrapping links clear it); Ø8 stub axle (hardware) slides +-idler_slot/2 in the
        # obround, M3 set-screw lock. Plate stops 0.1 inboard of the idler face.
        cxp = xw + P["track_gap"] + P["track_width"] / 2          # pod centre (78)
        arm = box(7.9, 16, 14.6); arm.apply_translation((s * (xw - 1.0 + 3.95), -ys, zs - 0.36))
        plate = cyl(14.0, 2.0, axis="x"); plate.apply_translation((s * (cxp - 9.0 - 0.1 - 1.0), -ys, zs))
        body = uni([body, arm, plate])
        slot = uni([cyl(4.1, 6, axis="x"), box(6, P["idler_slot"], 8.2)])
        slot.apply_translation((s * (cxp - 9.0 - 0.1 - 1.0), -ys, zs))
        body = sub(body, slot)
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


def _track_zc():
    """Wheel-center height so the bottom-run GROUSER face is the ground line (z=0):
    pin circle R + pin-to-pad-outer-face + grouser."""
    return P["track_wheel_r"] + P["track_pad_th"] + P["track_grouser_h"]


# Link knuckle X-comb (half-width 14): near set A (outer pair) interleaves the neighbour's far
# set B (inner pair) around the shared pin; the central +-4.9 stays OPEN so the sprocket teeth
# sweep between the B knuckles and engage the (unmodelled Ø1.75 filament) pins.
_KNUCKLE_A = ((-14.0, -9.4), (9.4, 14.0))
_KNUCKLE_B = ((-8.9, -4.9), (4.9, 8.9))


def _track_link():
    """One articulated track link (local frame: own pin axis = X axis, next pin at y=+pitch,
    OUTER face toward -z). Pad web + grouser + interleaved pin knuckles with Ø2.0 bores for
    Ø1.75 filament pins + 45deg inner-face draft chamfers at the web ends. Adjacent copies on
    the loop never touch: knuckle sets are X-disjoint and the pads splay apart on the arcs."""
    pitch, tw = P["track_pitch"], P["track_width"]
    kr = 3.5                                           # knuckle radius about the pin
    parts = [box(tw, 3.2, 2.7), box(tw, 2.0, 1.5)]     # web z -4.5..-1.8, grouser z -6.0..-4.5
    parts[0].apply_translation((0, 5.0, -3.15))
    parts[1].apply_translation((0, 5.0, -5.25))
    for (x0, x1) in _KNUCKLE_A:                        # near knuckles (own pin) + bridge to web
        k = cyl(kr, x1 - x0, axis="x"); k.apply_translation(((x0 + x1) / 2, 0, 0)); parts.append(k)
        b = box(x1 - x0, 3.1, 2.7); b.apply_translation(((x0 + x1) / 2, 2.05, -3.15)); parts.append(b)
    for (x0, x1) in _KNUCKLE_B:                        # far knuckles (next pin) + bridge to web
        k = cyl(kr, x1 - x0, axis="x"); k.apply_translation(((x0 + x1) / 2, pitch, 0)); parts.append(k)
        b = box(x1 - x0, 2.6, 2.7); b.apply_translation(((x0 + x1) / 2, 7.7, -3.15)); parts.append(b)
    link = uni(parts)
    for py in (0.0, pitch):                            # Ø2.0 hinge-pin bores (audit corr. 3)
        d = cyl(P["track_pin_bore_d"] / 2, tw + 4, axis="x"); d.apply_translation((0, py, 0))
        link = sub(link, d)
    for ye in (3.4, 6.6):                              # inner-face draft: 45deg chamfer, web ends
        c = box(tw + 4, 1.4, 1.4); c.apply_transform(R_x(TAU / 8)); c.apply_translation((0, ye, -1.8))
        link = sub(link, c)
    return link


def _sprocket(sx):
    """Drive sprocket + inboard hub tube reaching the TT shaft through the chassis-wall web.
    Disc (tip r 18.8) at the pod centre; hub OD12 runs inboard to x=|58.3| where the D-socket
    (bore Ø5.65, flat gap 3.85 print clearance, 8.0 deep = TT flat length) grips the shaft flats.
    Outer face: Ø9 x 1.5 counterbore for the M2 retaining screw + washer into the shaft tip's
    Ø2 axial hole. Built for the +X pod, spun 180deg about Z for -X."""
    tw = P["track_width"]
    cx = P["chassis_w"] / 2 + P["track_gap"] + tw / 2              # pod centre (78)
    hub_in = (P["chassis_w"] / 2 - 2.0 + 0.3) - cx                 # world 58.3 -> local -19.7
    spr = gear_disc(P["sprocket_outer_d"] / 2 - 1.5, P["sprocket_teeth"], tw - 20, 3.0, axis="x")
    spr = inter(spr, cyl(P["sprocket_outer_d"] / 2, tw - 19, axis="x"))    # truncate tooth-box
    hub = cyl(6.0, -hub_in - 3.5, axis="x")                        # corners to the 18.8 tip circle
    hub.apply_translation(((hub_in - 3.5) / 2, 0, 0))
    spr = uni([spr, hub])
    dd = inter(cyl((P["tt_shaft_d"] + 0.25) / 2, 8.6, axis="x"),   # TT double-D socket
               box(8.8, 8, 3.70 + 0.15))
    dd.apply_translation((hub_in + 4.1, 0, 0))                     # face-0.2 .. face+8.4
    spr = sub(spr, dd)
    bore = cyl(3.0, 16.0, axis="x"); bore.apply_translation((-3.3, 0, 0))
    spr = sub(spr, bore)                                           # Ø6 free bore to the outer face
    cb = cyl(4.5, 1.7, axis="x"); cb.apply_translation((tw / 2 - 10 - 0.75, 0, 0))
    spr = sub(spr, cb)                                             # retaining-screw counterbore
    if sx < 0:
        spr.apply_transform(R(TAU / 2, (0, 0, 1)))
    return spr


def build_tracks():
    """Two positive-drive track pods: 36 articulated links (Ø1.75 filament hinge pins) wrapping a
    12T sprocket (rear, TT double-D hub) + idler on an F688ZZ flanged bearing (front, tensioned
    via the chassis-arm slot) + road wheels riding the knuckle crowns. Bottom-run grouser face =
    ground (z=0). Each pod is a concatenation of separate printed pieces, not one solid."""
    R, tw, wb = P["track_wheel_r"], P["track_width"], P["track_wheelbase"]
    zc = _track_zc()
    kr = 3.5
    master = _track_link()
    out = []
    for sx in (-1, 1):
        cx = sx * (P["chassis_w"] / 2 + P["track_gap"] + tw / 2)
        pieces = []
        for (y, z, ang) in _track_link_poses(wb, R, zc, P["track_links"]):
            lk = master.copy()
            lk.apply_transform(R_x(ang))               # tangent to the loop, outer face outward
            lk.apply_translation((cx, y, z))
            pieces.append(lk)
        wheel_pieces = []
        spr = _sprocket(sx)
        spr.apply_translation((cx, -wb / 2, zc)); wheel_pieces.append(spr)
        # idler (front): rides the knuckle crowns (r 15.82) with 0.12 running clearance; F688ZZ
        # press seat Ø15.95 through + Ø18.5 x 1.0 flange recess on the inboard face; the Ø8 stub
        # axle (hardware) cantilevers from the chassis tension-slot plate.
        ir, iw = R - kr - 0.12, 18.0
        idl = sub(cyl(ir, iw, axis="x"), cyl(P["idler_bore_d"] / 2, iw + 2, axis="x"))
        fr = cyl(18.5 / 2, 1.05, axis="x"); fr.apply_translation((-sx * (iw / 2 - 0.5), 0, 0))
        idl = sub(idl, fr)
        idl.apply_translation((cx, wb / 2, zc)); wheel_pieces.append(idl)
        # road wheels: ride the bottom-run knuckle crowns (0.1 running clearance)
        for i in range(P["roadwheel_count"]):
            ry = -wb / 4 + i * (wb / 2) / max(P["roadwheel_count"] - 1, 1)
            rw = cyl(P["roadwheel_d"] / 2, 18.0, axis="x")
            rw.apply_translation((cx, ry, (zc - R) + kr + P["roadwheel_d"] / 2 + 0.1))
            wheel_pieces.append(rw)
        side = "L" if sx < 0 else "R"
        pod = trimesh.util.concatenate(pieces)                 # links only (rubber-black)
        _color(pod, "track")
        pod.metadata["name"] = f"track_{side}"
        pod.metadata["export"] = f"track_{side}.stl"
        out.append(pod)
        # running gear as its OWN node so it renders as exposed silver metal through the
        # links (design ref: big visible wheel-gears). Same geometry as before, just split.
        wheels = trimesh.util.concatenate(wheel_pieces)
        _color(wheels, "motor")
        wheels.metadata["name"] = f"drivewheels_{side}"
        wheels.metadata["export"] = f"track_wheels_{side}.stl"
        out.append(wheels)
    return out


def motor_tt(name):
    """TT gearmotor, measured (reference/tt-motor-1079893/NOTES.md, STEP B-rep). Local frame:
    OUTPUT SHAFT AXIS = the X axis (double-D exits +X); the 64.5 body runs along Y, gearbox
    front face (+tab) toward -Y, can toward +Y. Gearbox rect 36.80 x 22.40 x 18.64 (18.64 along
    the shaft), Ø22.4 collar (flat on the shaft side), can Ø20 (14.99 AF), Ø9.9 x 2.2 end boss,
    shaft Ø5.40 / 3.70 flats, 8.8 proud; 2x Ø3.0 mount holes 17.5 c-c, Ø2.8 tab hole, Ø4 nub."""
    gl, gw, gh = P["tt_gearbox"]                       # 36.80, 22.40, 18.64
    hx = gh / 2                                        # 9.32: gearbox face at local x=+9.32
    rect = box(gh, gl, gw); rect.apply_translation((0, 6.9, 0))            # y -11.5..25.3
    collar = cyl(gw / 2, 11.3, axis="y"); collar.apply_translation((0, 30.95, 0))
    cflat = box(4, 12.5, gw + 2); cflat.apply_translation((8.07 + 2, 30.95, 0))
    collar = sub(collar, cflat)                        # collar flat on the shaft side (z=-8.07 ref)
    can = cyl(P["tt_motor_d"] / 2, 13.5, axis="y"); can.apply_translation((0, 43.35, 0))
    for xc in (6.87 + 2, -(8.12 + 2)):                 # asymmetric 14.99 across-flats
        f = box(4, 15, P["tt_motor_d"] + 2); f.apply_translation((xc, 43.35, 0))
        can = sub(can, f)
    boss = cyl(4.95, 2.2, axis="y"); boss.apply_translation((0, 51.2, 0))
    stub = cyl(1.0, 0.7, axis="y"); stub.apply_translation((0, 52.65, 0))
    tab = box(3.0, 5.0, 5.0); tab.apply_translation((0, -14.0, 0))         # front tab, in -Y
    shaft = cyl(P["tt_shaft_d"] / 2, 8.8, axis="x"); shaft.apply_translation((hx + 4.4, 0, 0))
    for sz in (-1, 1):                                 # 3.70 across-flats over the outer 8.0
        f = box(8.2, 8, 3.0); f.apply_translation((hx + 0.8 + 4.1, 0, sz * (1.85 + 1.5)))
        shaft = sub(shaft, f)
    sboss = cyl(3.6, 0.5, axis="x"); sboss.apply_translation((hx + 0.25, 0, 0))
    nub = cyl(2.0, 2.0, axis="x"); nub.apply_translation((hx + 1.0, 11.0, 0))
    m = uni([rect, collar, can, boss, stub, tab, shaft, sboss, nub])
    for dz in (-8.75, 8.75):                           # 2x Ø3.0 mount through-holes, 17.5 c-c
        h = cyl(1.5, gh + 4, axis="x"); h.apply_translation((0, 20.3, dz))
        m = sub(m, h)
    th = cyl(1.4, 5, axis="x"); th.apply_translation((0, -14.0, 0))
    m = sub(m, th)                                     # Ø2.8 front tab hole
    _color(m, "motor"); m.metadata["name"] = name
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
    yt = P["tilt_axis_y"]

    # pose + output overrides (for generating review render sets)
    pan_deg = float(os.environ.get("PAN", P["preview_pan_deg"]))
    tilt_deg = float(os.environ.get("TILT", P["preview_tilt_deg"]))
    head_name = "head_wedge" if os.environ.get("SOLIDHEAD") == "1" else "head_shell"
    out_name = os.environ.get("OUT", "assembly.glb")

    # transforms
    pan = R(pan_deg * DEG, (0, 0, 1), (0, 0, 0))
    tilt = R(tilt_deg * DEG, (1, 0, 0), (0, yt, zt))
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
    for fp in build_fascia():                        # front fascia set (design ref)
        add(fp, np.eye(4))
    for trk in build_tracks():
        add(trk, np.eye(4), trk.metadata["export"])

    # track drive: 2x TT gearmotor (own 1, BUY 1 more) INSIDE the chassis, gearbox face 0.1 off
    # the side-wall inner face; the shaft crosses the wall (Ø8 pass, wall thinned to a 3 mm web)
    # and the sprocket's inboard hub grips the flats just outside. Shaft axis = sprocket axis
    # (y=-wb/2, z=_track_zc()). Tab registers in a rear-wall pocket; nub in a wall pocket;
    # 2x M3 through gearbox + wall, nuts in the pod gap. Skid steer.
    wbd = P["track_wheelbase"]
    ax = P["chassis_w"] / 2 - 5.0 - P["tt_gearbox"][2] / 2 - 0.1
    for sx in (-1, 1):
        dm = motor_tt("drive_L" if sx < 0 else "drive_R")
        if sx < 0:
            dm.apply_transform(R(TAU / 2, (0, 1, 0)))   # mirror about Y: shaft -X, tab stays rear
        dm.apply_translation((sx * ax, -wbd / 2, _track_zc()))
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
    cd = worm_cd()
    wz = zt - cd
    wheel_r = P["worm_module"] * P["worm_wheel_teeth"] / 2
    # worm wheel keyed to the axle -> turns WITH the head (M_head). Width 7 centered on x=0,
    # grub-keyed hub (M3 grub to the Ø5 axle -- a plain bore freewheeled), and spacer TUBES out
    # to both 695 inner races: they react the ~10 N worm thrust / 3.7 N wheel axial load.
    wheel = gear_disc(wheel_r, P["worm_wheel_teeth"], P["worm_wheel_w"], 2.5 * P["worm_module"], axis="x")
    hub = cyl(5.5, 5.5, axis="x"); hub.apply_translation((6.25, 0, 0))          # x 3.5..9
    tub_p = cyl(4.0, 9.0, axis="x"); tub_p.apply_translation((13.5, 0, 0))      # hub -> +X race
    tub_m = cyl(4.0, 14.5, axis="x"); tub_m.apply_translation((-10.75, 0, 0))   # wheel -> -X race
    wheel = uni([wheel, hub, tub_p, tub_m])
    wheel = sub(wheel, cyl(P["axle_d"] / 2 + 0.1, 40, axis="x"))                # Ø5.2 over the axle
    wgrub = cyl(1.25, 8); wgrub.apply_translation((6.25, 0, 3.5))               # M3 grub pilot
    wheel = sub(wheel, wgrub)
    _color(wheel, "fork"); wheel.metadata["name"] = "worm_wheel"
    wheel.apply_translation((wx, yt, zt))
    add(wheel, M_head)
    # worm on the motor shaft (axis Y), tangent below the wheel; fixed to the neck frame (M_pan).
    # FULL-DEPTH double-D bore (the old worm had no bore at all) + a Ø6 tail stub riding the
    # neck bracket's outboard bushing post (the far end was a free cantilever).
    face_y = yt - 0.5 * P["worm_len"] - 9.5          # keep in sync with build_neck_clevis()
    yc = face_y + 3.5 + P["worm_len"] / 2            # thread ribs overhang the body 1 mm each
                                                     # end; keep 0.5 off the plate front face
    wm = worm(P["worm_od"] / 2, P["worm_len"], axis="y")
    # Ø5 tail stub: bare past the thread end (y=-16, local +8) so the cradle groove band
    # (y -15.5..-13) grips ROUND stock, not thread (stage-4 D2); r2.5 keeps it under the
    # wheel-tooth sweep where it emerges
    stub = cyl(2.5, 8.0, axis="y"); stub.apply_translation((0, 8.0, 0))
    wm = uni([wm, stub])
    db = dbore_neg(P["worm_len"] + 1.2, axis="y")
    # NO extra clocking: after the motor's two rotations below (shaft +Z -> +Y, then rolled so
    # the offset points up) the shaft flats face +-X, and dbore_neg(axis="y") already cuts its
    # flats +-X. The old R(TAU/4, y) here clocked the bore flats to +-Z -- 90 deg off the
    # shaft (stage-4 defect D3: 17.4 mm3 of shaft shoulder buried in the worm core).
    db.apply_translation((0, 0.5, 0))
    wm = sub(wm, db)
    _color(wm, "motor"); wm.metadata["name"] = "tilt_worm"
    wm.apply_translation((wx, yc, wz))
    add(wm, M_pan)
    # tilt motor: shaft +Z -> +Y, then ROLLED about the shaft so the 7.875 offset points UP:
    # the can hangs BELOW the worm axis (clear of the head's back-wall sweep) and the ears run
    # horizontal at the CAN axis. Gear face lands on the bracket plate's BACK face.
    mt = motor_28byj("motor_tilt")
    mt.apply_transform(R(-TAU / 4, (1, 0, 0)))       # shaft +Z -> +Y
    mt.apply_transform(R(-TAU / 4, (0, 1, 0)))       # roll: shaft offset +X -> +Z
    mt.apply_translation((wx, face_y - 2 - (P["motor_body_h"] + P["motor_gear_h"]),
                          wz - P["motor_shaft_off"]))
    add(mt, M_pan)

    # (Pi 5 placeholder removed: the Pi now rides the display's OWN 58x49 back standoffs and
    # is part of the combined screen reference mesh, "Pins Out" assembly. See load_screen().)

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
    # uplift retention: 3 L-clips screwed to the deck, tabs over the platform's rim rebate
    add(build_pan_clips(), np.eye(4), "pan_clips.stl")

    # --- HEAD (tilt + pan): split into front bezel + back cover ---
    bezel, back = build_head_parts()
    add(bezel, M_head, "head_bezel.stl")
    add(back, M_head, "head_back.stl")

    for rail in build_head_rails():                  # orange side accent rails (design ref)
        add(rail, M_head)
    add(build_led_strip(), M_head)                   # forehead light strip (design ref)
    add(build_antenna(), M_head)                     # top-right antenna stub (design ref)
    add(build_hatch_frame(), M_head)                 # rear orange hatch frame (design ref)
    add(build_cam_pod(), M_head)                     # raised camera eye-pod (design ref)
    for arm in build_arms():                         # placeholder gripper arms (design ref)
        add(arm, M_head)

    screen = load_screen()
    screen.apply_transform(screen_pose())            # sit on the leaned front face
    screen.metadata["name"] = "screen_ref"
    add(screen, M_head)

    # camera: CM3 placeholder at the REAL stack dims, board FRONT plane on the M2 boss tips
    # (the old 12-deep box was centered 6 behind the wall and punched the bosses).
    fy = P["body_front_y"]
    lz = P["cam_lens_z"]; bz = lz - P["cam_lens_dz"]
    bf = P["cam_pier_y1"] - P["cam_pier_t"] - P["cam_boss_len"]   # board front = boss tips (20.5)
    bb = bf - P["cam_pcb_t"]                         # board back face
    pcb = box(P["cam_board_w"], P["cam_pcb_t"], P["cam_board_h"])
    pcb.apply_translation((0, bf - P["cam_pcb_t"] / 2, bz))
    conn = box(19.61, P["cam_back_d"], 5.71)         # flex connector, near the lens-end (top) edge
    conn.apply_translation((0, bb - P["cam_back_d"] / 2, bz + P["cam_board_h"] / 2 - 5.71 / 2))
    hous = box(P["cam_house_wh"], P["cam_house_d"], P["cam_house_wh"])
    hous.apply_translation((0, bf + P["cam_house_d"] / 2, lz))
    brl = cyl(P["cam_barrel_d"] / 2, P["cam_lens_tip"] - P["cam_house_d"], axis="y")
    brl.apply_translation((0, bf + (P["cam_house_d"] + P["cam_lens_tip"]) / 2, lz))
    cam = uni([pcb, conn, hous, brl]); _color(cam, "camera")
    cam.metadata["name"] = "camera_ref"
    add(cam, M_head)
    # camera rear cover: plate behind the connector envelope + 2 posts to the board back on the
    # DIAGONAL hole pair; 2x M2 self-tap through the posts into the bezel bosses (the board is
    # clamped board->boss by the same screws). Bottom edge keeps the ribbon pinch slot.
    cov_f = bb - P["cam_back_d"] - 0.3               # plate front: 0.3 clear of the connector
    cover = box(P["cam_board_w"] + 2, P["cam_cover_t"], P["cam_board_h"])  # +0 in Z: the board
    # top is 0.54 under the interior ceiling; a +2 skirt punched it
    cover.apply_translation((0, cov_f - P["cam_cover_t"] / 2, bz))
    diag = [(P["cam_hole_dx"] / 2, P["cam_hole_z_top"]),
            (-P["cam_hole_dx"] / 2, P["cam_hole_z_bot"])]
    for dx, dz in diag:
        post = cyl(P["cam_boss_od"] / 2, bb - cov_f, axis="y")
        post.apply_translation((dx, (cov_f + bb) / 2, bz + dz))
        cover = uni([cover, post])
        m2 = cyl(P["cam_m2_clear_r"], 20, axis="y")
        m2.apply_translation((dx, bb - 5, bz + dz))
        cover = sub(cover, m2)
    rib = box(P["cam_ribbon_w"], P["cam_cover_t"] + 2, P["cam_ribbon_t"])
    rib.apply_translation((0, cov_f - P["cam_cover_t"] / 2,
                           bz - (P["cam_board_h"] + 2) / 2 + 1))
    cover = sub(cover, rib)
    _color(cover, "back"); cover.metadata["name"] = "cam_cover"
    add(cover, M_head, "cam_cover.stl")

    # HOLLOW Ø5 tilt axle: clamped to the head (turns with it), rotates in the neck-cheek 695
    # bearings, driven in the middle by the worm wheel. Hollow -> Pi power wires cross on-axis.
    axle = sub(cyl(P["axle_d"] / 2, P["head_w"] + 4, axis="x"),
               cyl(P["axle_bore_d"] / 2, P["head_w"] + 8, axis="x"))
    _color(axle, "axle"); axle.metadata["name"] = "tilt_axle"
    axle.apply_translation((0, yt, zt))
    add(axle, M_head)

    out = webpath(out_name)
    scene.export(out)
    print(f"wrote {out}  ({len(scene.geometry)} parts)")
    if EXPORT:
        print("exported per-part STLs into stl/")


if __name__ == "__main__":
    build()

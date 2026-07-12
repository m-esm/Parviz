"""Shared design parameters: PARAMS dict `P`, angle constants, EXPORT flag.

Split out of the original monolithic build.py (2026-07-10); see
build.py for the assembly entry point and the overall design notes.
"""
import os
import numpy as np


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
    "body_front_y": 33.0,   # front face plane. 31 -> 33 (2026-07-11, user: "gap between the
                            # LCD and the body, I can see the internals"): the glass front
                            # (30.99) used to be FLUSH with the face, so the module pocket had
                            # to pierce it and the aperture showed a see-through slot around
                            # the whole glass. The face now stands 2.0 in FRONT of the glass:
                            # the pocket stops at y 31.1 (0.11 locator clearance over the
                            # glass) and the window cut leaves a real bezel_overlap retaining
                            # lip on all 4 sides -- phone-bezel look, no see-through ring.
    "body_back_y": -70.0,   # back face plane (task #27 deep head: was -31, which left the whole
                            # tilt stepper hanging exposed behind the head. The 28BYJ can rear
                            # sits at y=-64.3 (face_y -34.5 - 2 - 27.8); -70 puts it inside the
                            # envelope with wall 4 + 1.7 static clearance to the inner face -66)
    "body_z_bot": 88.0,     # shell bottom height above desk (113-25: design-ref head drop --
                            # the whole head+tilt stack sits 25 lower over the chassis)
    "body_z_top": 242.0,    # shell top height. 226 -> 242 (2026-07-11, user: "clear the camera
                            # pod out of the LCD frame, make the forehead taller"): the CM3 bay
                            # + eye-pod now live ENTIRELY above the screen -- board bottom 211.6
                            # sits 2.7 over the pocket top (208.9), pod bottom 216 sits 7.1 over
                            # it, board top 235.5 keeps 2.5 to the interior ceiling (238)
    "corner_r": 16.0,       # rounded vertical edges (friendly, clean)
    "bezel_overlap": 3.5,   # front lip overlaps the glass edge this much per side (a real
                            # covering lip again since body_front_y 33; still only a LOCATOR --
                            # the glass is held by the 4 factory screws, never bezel bosses)
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
    # Ø5 tilt axle on 695-2RS bearings (5x13x4, owned x30). SOLID rod (review 2026-07-08:
    # the old hollow Ø2.5 weight relief left a 0.25 wall under the D-key flat; the cable
    # never used the bore anyway -- it drapes through the bottom-rear slot).
    "axle_d": 5.0,          # tilt axle outer Ø (rides 695 bores)
    "brg_od": 13.0,         # 695-2RS outer Ø (press into the head-side hubs)
    "brg_w": 4.0,
    # worm + worm wheel (module 1.25). Wheel keyed to the axle; worm on the motor.
    "worm_module": 1.25,
    "worm_wheel_teeth": 12, # 12T wheel (24T tilted 60 deg in 16 s -- too slow)
    # FAST-TILT pass (2026-07-12, user: "tilt should happen really fast"): 1 -> 3 starts,
    # ratio 12:1 -> 4:1 -> 22.5 deg/s at the usable 15 RPM (60-deg sweep 8 s -> 2.7 s).
    # Same pitch r 4.4 / CD 11.9 / cartridge -- only the thread count changes. Torque at
    # speed ~= 20 mNm x 4 x 0.45 eff = 36 mNm vs ~28 needed (25 residual imbalance + inertia)
    # = 1.3x margin (1.9x at 15 deg/s). Faster options FAIL: a spur gear-up + 3-start nets
    # 18 mNm vs 31 (0.6x); dropping the worm for a 2:1 spur pair needs the motor shaft
    # along X, which collides with the cheeks/root block/stop posts everywhere probed.
    # !! TRADEOFF: 3 starts (lead angle ~23 deg) do NOT self-lock. De-energized the head
    # is held only by the 28BYJ detent+gear friction through 4:1 (~27-54 mNm at the axle)
    # -- marginal vs the assumed 25 mNm imbalance. Firmware: energized hold or park at
    # the balance point. Real generated 3-start teeth are a docs/WORM.md regen (the
    # committed *_real.stl pair is single-start, so starts!=1 builds placeholders).
    "worm_starts": 3,
    "worm_wheel_w": 7.0,    # face width
    "worm_wheel_x": 0.0,    # wheel centered on the head midplane (spacer tubes reach both bearings)
    "worm_od": 10.0,        # placeholder-worm visual OD (real generated worm OD is 10.55)
    "worm_pitch_r": 4.4,    # REAL worm pitch radius (docs/WORM.md): module 1.25 + the Ø7
                            # solid core force pitch r 4.4 -> CD 11.9 (the old worm_od*0.4
                            # guess gave 11.5, which left the wheel ~no addendum room)
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
    # FAST-PAN gear-up (2026-07-12, user: "panning should happen really fast"): the direct
    # D-hub is replaced by a 2:1 spur gear-UP -- 32T on the motor D-shaft driving a 16T
    # pinion integral to the platform underside. Peak slew 90 -> 180 deg/s (motor 15 RPM
    # x 2); accel budget at motor <=10 RPM = 30/2 = 15 mNm vs ~7 race friction + I*alpha
    # (Iz ~0.0024 kg m^2) -> ~250-300 deg/s^2. 3:1 REJECTED (10 mNm barely beats friction,
    # zero accel budget); the antennas' 6.25:1 stalls on race friction alone. The 28BYJ is
    # POWER-limited (~0.035 W) so a 180-deg sweep still takes ~2 s -- the gear-up buys
    # PEAK slew, which is what reads as fast. m0.8 (the antenna module): gear cluster max
    # reach = CD 19.2 + tip 13.8 = 33.0 < race ID 34 -> the whole stage hides under the
    # seat floor. Motor drops ~13.5 and swings off-axis (shaft -19.2,0; can -19.2,+7.875
    # after a -90 deg clock, ears along X, wbox +Y); shaft flats land in the 32T's D-bore.
    # Homing unchanged (lug/posts; stall torque at the lug ~17 mNm still stalls); steps/deg
    # HALVES to ~5.7. Back-drive gets easier -- fine, a balanced vertical axis has no
    # gravity torque. Placeholder gear_disc teeth (real generated pass later, like the
    # antennas). pan_gear_z is the shared tooth band; both gears + the deck pocket key off it.
    "pan_gear_m": 0.8,
    "pan_gear_motor_t": 32,     # on the motor D-shaft (drives)
    "pan_gear_pinion_t": 16,    # integral to the platform hub (driven) -> 2:1 UP
    "pan_gear_z": (45.0, 50.0), # tooth band: under the seat floor 51, over the boss 42.2
    "pan_shaft_azim": 180.0,    # motor-shaft azimuth about the pan axis (deg). 180 = -X:
                            # gear center r19.2 stays >=41 deg from both stop posts
                            # (118/332), the pedestal clears drive_L (x>=-43.2 vs can
                            # -45.6) and the belly strap only grows 10 on -X

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
    "chassis_l": 240.0,     # LOWER-TUB length front-back (Y). 156 -> 200 2026-07-10, then
                            # 200 -> 240 same day (toy-tank hull: +2 cm each side; the
                            # deck slab additionally runs deck_overhang past each end)
                            # (user: "longer, same shape as the RC-tank refs"), paired with
                            # track_wheelbase so the TT front tabs still pocket the rear
                            # wall (inner face 95 ~= |ys| 80.66 + tab reach ~14.5)
    "chassis_clear": 7.0,   # ground clearance under the body
    # PROW CHEEKS (2026-07-11, user: "drive axle blocking the front and rear view
    # LEDs... the chassis should be a bit longer from both side so the axle shaft of
    # the last wheel will be hidden inside"): the M8 end-axle NUT stacks protrude to
    # |y| 135.4 (x 55.5..62) in free air ahead of the 120 walls, right over the corner
    # lamps. Four prow blocks (x |32..70|, clear of the +-30 trim rings) extend the
    # tub tub_nose past each wall, each with an open-top nut pocket (x 47..63.5, 3.0
    # front skin -- the nut descends into it as the deck+axle drops on; spec M8 NYLOC,
    # the pocket is clearance not a wrench flat), a pylon notch (x 61..70.5, 1.0
    # clear), and the glacis plane continued (+tub_nose shift). The CENTER band stays
    # at chassis_l/2: the cliff cone crosses z 46 at y ~131 (probed), a full-width
    # nose would ping itself. Cheek tops cap FLAT at the z 46 seam so they live
    # wholly in chassis_lower; the wedge up to the deck slope stays an open shadow
    # line like the pylon bay. Lamps + rear buzzer pod ride the cheek noses.
    "tub_nose": 20.0,       # prow cheek reach past the wall (nut face 135.4 + 4.6)
    # GLACIS (2026-07-10, user: "the chassis shouldn't be a box -- from the side it
    # should have the same form as the tracks"): the hull's front/rear lower corners
    # are cut at the SAME 33 deg as the track ramps, from (|y| 83.1, z 7) up to the
    # walls at z 18. Everything that lived below z 18 on those walls moved up: front
    # LED bar rides the glacis face itself (tilted 33), US barrels 26->28.5 (grille
    # +1), rear pod 16->30.5 (x 47),
    # USB slot + PD pilots z0+12 -> z0+24. The belly opening (|y|<=69) and all side
    # features (motor mounts z>=31 at the glacis x) clear the cut.
    "glacis_y0": 103.1,     # glacis starts on the belly plane here (83.1 + the 20 tub
                            # stretch: keeps the 33 deg slope to z 18 at the y 120 wall)
    "glacis_z1": 18.0,      # meets the front/rear walls here (slope = the ramp 33 deg)
    "track_gap": 4.0,       # body side <-> track inner face
    # Modular positive-drive track (advancedvb 'Tank track' 3062624 geometry): printed link pads
    # on filament-rod hinge pins, a 12-tooth sprocket meshing the pins -> no slip on a desk.
    "track_wheel_r": 19.32,  # pin-circle radius = exact 12T x 10.0-pitch polygon (audit corr. 1)
    "track_wheelbase": 256.326,  # sprocket-axis <-> idler-axis (Y). SOLVED value: with the
                            # raised loop (track_raise/track_ground_hy below) the perimeter
                            # closes at exactly 64 x 10.0 -- _track_link_poses asserts it.
                            # STRETCHED 161.325 -> ... -> 256.326 2026-07-11 (user chose
                            # "tracks 1 cm past the DECK TIPS"): wb/2 - ground_hy stays
                            # 8.163 (end geometry carries over); END AXLES at +-128.16,
                            # track ends +-153.5 ~= deck tips 144 + 1 cm. This exceeds
                            # the coaxial-TT limit, so the DRIVE ARCHITECTURE CHANGED:
                            # both loop ends are now FREE IDLER WHEELS on Ø8 stubs in
                            # deck-overhang PYLONS (front pair tensions), and the drive
                            # sprocket moved INSIDE the loop onto the GROUND RUN at
                            # spr_y -- the robot's weight presses the straight run into
                            # mesh (rack-style engagement of 2-3 pins; ground reaction
                            # guarantees bite). TT stays direct on the sprocket shaft,
                            # dropped to the ground-run pin line (z 25.32) at spr_y.
                            # (Stretched with chassis_l 2026-07-10; same wb/2 - ground_hy
                            # = 8.163 end geometry as the first raised loop, so the 33 deg
                            # ramps / 147 deg wraps and all end clearances carry over.)
    # RAISED TANK LOOP (2026-07-10, user's RC-tank chassis refs): sprocket + idler axles
    # sit track_raise ABOVE the old stadium centreline, so the track climbs ~33 deg ramps
    # at both ends and wraps ~147 deg -- the classic hull profile. Raise is capped at 9:
    # the sprocket rides the TT shaft, and at zs 34.32 the motor's upper M3 mount hole
    # (zs+8.75, r1.6 -> 44.7) and the gearbox top (45.5) still stay under the z46 deck
    # seam, so the deck stays screw-free over the motors.
    "track_raise": 9.0,     # axle z = _track_zc() + raise (34.32); loop top pin z 53.64
    "track_ground_hy": 120.0,  # flat ground-run half-span (ramp tangent leaves here)
    "track_width": 44.8,    # link body width (X): 2x design-ref chunk, then -20% per user
                            # (28 -> 56 -> 44.8); sprocket engages only the central ~8 mm channel
    "track_pitch": 10.0,    # link pin-to-pin (our re-model; the 3062624 reference pitch is 9.65)
    "track_links": 64,      # 64 x 10 = 640 mm loop (36->45->52->53->64 stretches)
    "track_pad_th": 4.5,    # pin axis -> pad OUTER face (link overall 8: knuckle r3.5 inward)
    "track_grouser_h": 1.5, # tread lug (print grousers in TPU or add pads)
    "track_pin_bore_d": 2.2,    # BOUNDARY-joint hinge bore for Ø1.75 filament pins
                            # (strip-to-strip + master closure only since the
                            # 2026-07-12 print-in-place strips; was every joint).
                            # 2.0 -> 2.2 (2026-07-12 print pass): bores print
                            # HORIZONTAL (grouser-down) and the roof sags 0.1-0.2 --
                            # at 2.0 that ate most of the 0.25 pin clearance (sticky
                            # hinges). 0.45 slop on a chained hinge is harmless
                            # (track tension owns the geometry) and the sprocket's
                            # conjugate envelope already budgets bore slop.
    "track_pin_print_d": 2.0,   # INTEGRAL printed hinge pin (2026-07-12 print-in-place
                            # strips, after the chain print failure): each link's own
                            # (y0) pin is a solid Ø2.0 rod fused into its A knuckles,
                            # spanning the full link width -- the sprocket drives on
                            # it in the central channel exactly like the old filament
                            # pin (envelope regenerated in _sprocket_profile). Ø2.0
                            # not 1.75: a printed horizontal rod needs >= 2 perimeters
                            # of section to survive the 18.8 mm bridge between the A
                            # anchors, and pin bending margin grows with it (~19 MPa
                            # at stall on Ø1.75 -> ~13 MPa on Ø2.0).
    "track_bore_pip_d": 2.7,    # print-in-place far-bore (B knuckles) around the
                            # NEIGHBOR link's Ø2.0 integral pin: 0.35 radial air gap,
                            # the proven PIP hinge clearance at 0.2 mm layers -- big
                            # enough that horizontal-bore roof sag + rod sag can't
                            # fuse the joint, small enough that the sprocket's 1.275
                            # conjugate envelope still swallows the slop. Strip-end
                            # (boundary) far bores revert to track_pin_bore_d.
    "sprocket_teeth": 12,
    "sprocket_outer_d": 41.0,   # TIP r 20.5 = pin circle 19.32 + 1.18 ADDENDUM (2026-07-11
                            # conjugate-tooth fix; the old 37.6 tip sat BELOW the pin
                            # circle -- pockets, no teeth: 35% of every pitch was dead
                            # gap and the 0.355 skip barrier was inside FDM tolerance).
                            # Real conjugate teeth now rise past the pins: skip barrier
                            # tip + pin - pin circle = 2.06, per-pin trap window (>=0.8
                            # radial retention) 10.75 > pitch/2 (contact ratio 1.37 on
                            # the tip circle), tooth tips dip to z 4.82
                            # over the ground run = 0.62 above the link web face (4.2).
                            # Ceiling: tip r <= 20.72 keeps the 0.4 web clearance; 20.5
                            # leaves 0.22 for FDM. See _sprocket_profile() in tracks.py.
    "idler_bore_d": 15.95,  # F688ZZ (8x16x5, flange 18) press seat; flange recess 18.5 x 1.0
    "roadwheel_d": 20.0,    # dished road wheels riding the bottom-run knuckle crowns
    "roadwheel_ys": (57.5, 33.5, 11.5, -11.5, -33.5),   # EXPLICIT stations
                            # (2026-07-11 mid-drive): the ground-run sprocket at spr_y
                            # -68 needs 28.8+ axle gaps (18.8 + 10): nearest wheel
                            # -33.5 sits 34.5 away; -68..-120 is carried by the
                            # sprocket + rear end idler. Stations +-33.5 (QA loop
                            # 2026-07-11: at +-34.5 the beam nut slot's edge 38.15
                            # nicked the pod-join dowel SOCKET edge 38.075 by 0.075;
                            # +-33.5 clears it 0.93, wheel gaps stay 22/24)
    "spr_y2": 90.0,         # SECOND drive station (2026-07-11, user: "two motors per
                            # side, second optional but all fittings ready"): mirrored
                            # about the shaft -- the TT sits FLIPPED (gearbox trailing
                            # -y), so its envelope ys2-52.6..ys2+12 clears the ULN
                            # posts (y<=36) and the front inner wall (115); tab/rib
                            # land at ys2+14..15, nub ys2-11=79 (the y80 vent left the
                            # row for it), M3s ys2-20.3=69.7. Sprocket 2 mounts the
                            # optional TT's own shaft; without it the station is empty
                            # (end idler + the 57.5 wheel carry the front run).
                            # 87 EVALUATED + REJECTED (2026-07-11 conjugate-tooth
                            # pass; would stagger the two stations' dead windows by
                            # a half pitch, sep 155 mod 10 = 5): the M3 wall pair
                            # would land 65.1..68.3 INSIDE the y-64 vent (61.5..
                            # 66.5) and the can tail 34.4 crosses the ULN-post line
                            # (<=36). Moot anyway: conjugate teeth give each
                            # sprocket tip-circle contact ratio 1.37 (13.71 > the
                            # 10 pitch), so there is no dead window left to stagger.
    "spr_y": -68.0,         # drive sprocket station on the ground run (center z = pin
                            # line + pin circle = 25.32). THE derivation (all failed
                            # spots documented 2026-07-11): the TT envelope ys-12..
                            # ys+52.6 x 39.5..67.8 must miss the ULN posts (y 4..36)
                            # -> ys <= -48.6; the M3 wall pair at ys+20.3 must miss
                            # the pod-join rail block band y -44.5..-35.5 (the nuts
                            # float in the pod gap there) -> ys <= -68; the tab/rib
                            # at ys-14.15 pushed the -80 vent out of the row
    "idler_slot": 4.0,      # idler Y-slide for tensioning (M3 set-screw lock)
    # TT gearmotor drive (own 1x; BUY 1 more -> 2 for skid steer; MX1588 drives both).
    # Measured dims from reference/tt-motor-1079893/NOTES.md (STEP B-rep). Shaft is
    # PERPENDICULAR to the 64.5 body, 11.5 behind the gearbox front face, mid-height.
    "tt_gearbox": (36.80, 22.40, 18.64),    # rect block (len, w, h); +Ø22.4 collar 11.3 long
    "tt_motor_d": 20.0,     # can Ø20.00, 14.99 across flats, 13.5 exposed
    "tt_shaft_d": 5.4,      # double-D output shaft, 3.70 flats, 8.8 proud, flat len 8.0

    # --- Chassis mechanical detailing: body<->pod join, pan-motor seat, ballast bay ---
    # Join stations (2x per side): each carries one M3 + one Ø4 dowel. y=+-40 = centers of
    # the 11-wide wall windows between the +-32 / +-48 vent slots (spread with the 200
    # chassis 2026-07-10), clear of the TT wall zone (y -92..-55) and the idler tension
    # arm (y 73..89). Screws drive from INSIDE the
    # chassis cavity through the wall into captive nuts in the pod rail: the 4 mm pod gap
    # holds a nut but no screwdriver, and loose nuts can't be held in a 4 mm slot -- so the
    # nut is trapped pod-side and the head sits on the cavity wall (same convention as the
    # TT gearbox screws, "nut in the gap").
    "pod_join_y": (-40.0, 40.0),
    "pod_join_screw_z": 34.0,   # M3 axis: mid of the loop's free band, max spread above dowel
    "pod_join_dowel_z": 20.0,   # Ø4 dowel axis: 14 below the screw -> shear + pitch location
    "pod_join_dowel_d": 4.0,    # Ø4x12 pin: +0.1 slip in the wall, -0.15 press in the rail
    "pod_rail_x1": 78.0,        # rail outer face: 4 fills the pod gap (links never enter
                                # x 70..74) + 4 into the loop interior's link-free mid band
    "pod_rail_z": (14.0, 40.0), # rail z band: 4.5 above the bottom-run knuckle tops (9.5),
                                # 1.14 below the top-run knuckle sweep (41.14)
    "pod_rail_block_w": 9.0,    # per-station block width (Y): 1.0 clear of each vent slot
    # Chassis print split: the old one-piece tub+deck trapped deep pockets, side-wall holes,
    # pan-seat features, and internal posts in one support-heavy print. Split at z=46,
    # right under the solid deck, so the lower tub prints open-top and the pan deck prints
    # separately; 4x M3 from the top deck into lower thread-form pilots clamp/register it.
    "chassis_split_z": 46.0,
    "chassis_split_screws": ((-64.0, 60.0), (64.0, 60.0), (-34.0, -113.0), (34.0, -113.0)),
                            # rear pair moved off the side walls 2026-07-10: the raised
                            # TT gearboxes (track_raise, top z 45.5) now own that zone;
                            # bosses ride the rear wall instead (sensor hole z16, trim
                            # pins outer-face only, motor tabs x +-55.6 -- all clear)
    "chassis_split_boss_r": 4.0,
    # PRINT-SPEED SUB-SPLITS (2026-07-10, user: break the biggest prints apart). See
    # build_chassis_parts' docstring for the joint scheme per seam.
    "lower_seam_y": 26.0,        # lower tub front/rear seam (vent-free wall band
                                 # 18.5..29.5, pan pedestal <=|24|, pod joins +-40)
    "deck_seam_y": (66.0, -52.0),  # deck strip seams (front clip reaches y 58; the
                                 # y-60 corner bosses reach 64 -> strips own them)
    "deck_center_screws": ((-64.0, 8.0), (64.0, 8.0), (-64.0, -26.0), (64.0, -26.0)),
                                 # the center piece's OWN hold-downs (vent-free bands)
    # TOY-TANK HULL (2026-07-10, user round 2: "upper part 10 cm longer = 5 cm each
    # side, lower part 2 cm longer each side, angled so the proximity sensor looks
    # down, like a toy tank chassis" -- REPLACED the same-day front-only prow): the
    # deck slab runs deck_overhang past the lower tub at BOTH ends; the end faces
    # slope from the tub wall top (|y| 120, z 46) to the deck top edge (|y| 150,
    # z 66) at atan(20/30) = 33.7 deg from horizontal (the same ~33 family as the
    # track ramps + lower glacis). The slope's outward normal points 33.7 deg ahead
    # of straight down, so the HC-SR04 flush in the FRONT slope looks down-forward
    # exactly as the user reasoned. Sensor construction mirrors sensor_us: Ø16.6
    # barrel bores through the 5-thick slope skin, board against the skin's back
    # (1.2 recess) inside an underside pocket that opens into the tub for wiring.
    "deck_overhang": 30.0,       # anchors the END-SLOPE geometry: slope runs (|y| 120,
                                 # z 46) -> (|y| 150, z 66) at 33.7 deg
    "deck_tip_trunc": 6.0,       # deck tips CUT BACK to |y| 144 with a vertical 4-tall
                                 # nose face (z 62..66): the raw slope/top intersection
                                 # was a 33.7 deg acute PLA knife edge (user 2026-07-11:
                                 # "the chassis angle is too sharp"). Slope angle -- and
                                 # with it the cliff-sensor geometry -- is unchanged.
    "cliff_v": 9.6,              # barrel-pair center, mm up the slope from its bottom
                                 # edge (slant length 36.06): bore rim keeps 1.3 to
                                 # the wall-top corner, board top keeps 0.7 under the
                                 # pocket ceiling (z 62.5, top skin 3.5)
    # Pan-motor seat detailing (re-derived for base_h 66: can bottom 26.45, ear-bar
    # underside = pedestal top = 44.25, can top 45.25, gear face 54.25): the 7-wide x
    # 1-thick ear bar clamps on two DEFINED pads instead of the whole 48x48 top, and the
    # can's top band registers in a collar ring right under the Ø27.25 gear stack.
    "ped_pad_wxy": (9.0, 10.0),   # ear seat pads (X x Y) centered on the +-17.5 ear holes
    "ped_relief": 0.8,            # pedestal top dropped 0.8 outside pads + collar footing
    "ped_collar_od": 32.0,        # collar OD; ID = the Ø29 can bore (can Ø28.25 registers)
    "ped_collar_h": 1.5,          # collar top 45.75: wraps the can's last 1.0 + gear root
    # 2nd ULN2003 standoff set (tilt driver's base-side mount option; it can also take the
    # MX1588 track driver). The task-suggested mirror (-38,+-20) fails: board 35x32 at
    # (-38,+-20) spans x -55.5..-20.5 and overlaps the 48x48 pedestal (x -31.9..16.1,
    # y -24..24). (-38, 45) clears everything: board y 29..61 > pedestal 24, < US board
    # 71.4; x -55.5..-20.5 clear of ULN#1 (x >= 20.5) and both TT cans (|x| >= 44.4 only
    # at y < -10).
    "uln2_c": (0.0, 80.0),  # moved 2026-07-11 (dual motors): the old (-38, 45) posts
                            # sat inside the flipped front TT_L's envelope (y 37..102,
                            # x -68..-40); pedestal x -37..10 blocks every left-side
                            # spot, so the board rides the empty front-center floor
                            # (posts +-17.5 x, y 64..96 -- clear of both TT columns,
                            # the pedestal, the belly opening rim at y 49, and walls)
    # Ballast bay: rear cavity floor (head+Pi CoM is forward-high -> mass low + rearward).
    # 3 ribs across X make three ~9.5-wide pockets against the rear wall (inner face y=-73)
    # for steel bar / coins / shot; the front rib at -40 fences the mass. Ribs end at
    # |x|=40 (TT gearbox inner faces at |x| 46.26 -> 6.3 clear) and skip a 20-wide center
    # corridor (the USB-C plug body enters the cavity at x +-7, z 15..23, over the floor).
    "blst_rib_y": (-63.0, -51.5, -40.0),
    "blst_rib_w": 2.0, "blst_rib_h": 4.0,   # 2 wide x 4 tall: locates the bottom layer
    "blst_rib_xmax": 40.0,                  # rib outer end (TT clearance, see above)
    "blst_usb_hw": 10.0,                    # rib-free USB corridor half-width

    # --- BELLY ACCESS PLATE (task #26): bolt-on floor plate under the cavity ---
    # Opening 100x110 keeps a >=12 rim inside the 130x146 cavity footprint EXCEPT a
    # retained floor STRAP (x -34..25, y -26..51): the pan-motor pedestal (x -31.9..
    # 16.1, y +-24) and the inboard ULN posts ((20.5, 36) on ULN#1, (-20.5, 29) on
    # ULN#2) root on the floor -- a clean 100x110 cut would set all three afloat. The
    # strap splits the opening into a full-width rear bay window (ballast, TT rears,
    # USB) + two front channels (ULN wiring). Plate = 1.45 flange in a 1.5 rebate
    # (belly face stays flush at z=7: ground clearance is only 7) + a 3-thick plug
    # filling the opening; the two inboard ballast ribs move ONTO the plug.
    "belly_open_wl": (100.0, 110.0),        # opening W(X) x L(Y), corners r8
    "belly_open_c": (0.0, -6.0),            # centre (rear-biased toward the ballast bay)
    "belly_keep": (-44.0, -26.0, 25.0, 51.0),   # retained strap (x0, y0, x1, y1). x0 -34
                            # -> -44 (fast-pan 2026-07-12): the pedestal followed the
                            # off-axis can to x -43.2..4.8 and must stay rooted on
                            # fixed floor, not the removable plug
    "belly_rebate_grow": 8.0,               # rebate ledge past the opening, per side
    "belly_lip_t": 1.5,                     # rebate depth (up from the belly face z=7)
    "belly_fit": 0.15,                      # plate<->rebate/opening clearance per side
    # 6x M3 countersunk from below (heads flush at z=7) into Ø7 self-tap bosses
    # standing on the interior rim/strap (Ø2.5 pilots). Stations dodge the TT gearboxes
    # (|x|>=46.26 at y<-40), the ballast ribs (|x|<=40) and both ULN board envelopes.
    "belly_screws": ((-42.0, -65.5), (42.0, -65.5), (-54.0, -5.0), (54.0, -5.0),
                     (-30.0, 53.0), (30.0, 53.0)),
    "belly_boss_r": 3.5, "belly_boss_h": 6.0,

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
    "cam_lens_z": 226.0,    # lens axis height. 212 -> 226 (2026-07-11, user: the eye-pod crowded
                            # the LCD frame -- at 212 the pod's lower band sat ON the glass and
                            # the CM3 board hung down behind the panel to z 197.6): the whole bay
                            # is now ABOVE the screen inside the raised forehead (body_z_top 242).
                            # Board z 211.6..235.5 (2.7 over the pocket top 208.9); the pier no
                            # longer hides behind the display panel, its old y constraint is gone
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
    "cam_pier_w": 32.0,     # pier width (X)
    "cam_pier_t": 3.0,      # pier plate thickness (Y)
    "cam_pier_y1": 26.5,    # pier FRONT face. 24.5 -> 26.5 with body_front_y 31 -> 33: the bay
                            # now sits ABOVE the display (cam_lens_z 226) so the old panel-front
                            # constraint (25.03) is gone; +2 keeps the barrel poking 0.48 into
                            # the wall bore and the pupil ~3 mm behind the outer face, as before
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

    # --- Pi 5 ACTIVE COOLER keep-out (2026-07-13; bought part, buy-list NICE-TO-HAVE) ---
    # Official envelope 63.5 x 42.5 x 13.7 (product brief RP-008188 + mechanical drawing
    # RP-008187, both pulled 2026-07-13). The cooler push-pins land in the Pi 5's two
    # DEDICATED Ø3 heatsink holes (Pi 5 mechanical drawing): board (3.5, 9.5) and
    # (61.5, 46.5) -- each exactly 6.0 off its adjacent M2.5 corner hole -- and the pin
    # pattern (58 x 37) sits DEAD-CENTERED in the cooler envelope (measured off the
    # drawing raster: pins 2.5-2.9 from every envelope edge = caps' own radius), so the
    # envelope center in board coords is the hole-pattern midpoint (32.5, 28.0).
    # BOARD FRAME measured from the reference mesh, not guessed: the Pi's M2.5 corner
    # holes were circle-fit in the posed mesh at world x -34.652/23.348, z 130.766/
    # 179.766 (pattern 58.000 x 49.000 exact) -> board origin (x=0 SD edge, y=0 HDMI
    # edge) = world (-38.152, 127.266); component-side face plane y=5.98 (slab scan).
    # DEPTH: the keep-out takes the FULL official 13.7 off the component face.
    # Assembled, the base plate rides the pre-applied pads on the BCM2712/RP1 lids
    # (~2-2.6 up) and the fin/fan tops sit ~9.1 above the plate bottom, so the real
    # metal tops out 1-2.5 SHY of this face; 13.7-off-the-board is the honest worst
    # case (it also covers the sprung pin caps). COOLER=1 adds the placeholder --
    # default OFF: see the fit VERDICT comment in build.py + tools/probe_cooler.py.
    "pi5_cooler_wdh": (63.5, 13.7, 42.5),  # envelope, world X x Y(depth) x Z
    "pi5_board_org": (-38.152, 127.266),   # world (x, z) of Pi board coord origin
    "pi5_comp_face_y": 5.98,               # component-side board surface plane (world y)
    "pi5_cooler_board_c": (32.5, 28.0),    # envelope center, board coords (= heatsink
                                           # hole-pattern midpoint, see above)

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
    "led_cz": 226.0,        # slot center Z, on the lens axis (226): the LED row and the eye
                            # read as one forehead band; slot z 223.5..228.5 > pocket top 208.9
    # Knurled antenna stub on the head top face (cosmetic; Pi WiFi is internal).
    # Image-RIGHT in the reference front view = robot -X.
    # --- TWIN DEPLOYABLE ANTENNAS (2026-07-10, user: two masts, one per head side,
    # INDEPENDENTLY stepper-driven in/out, 50 max past the head top, geared ~10 cm/s).
    # Mechanism, PER SIDE (mirrored in x): one 28BYJ (body |x| 25.7..53.5, can axis
    # y -30 / z 189.6, ears vertical) -> two-stage 30T:12T spur up-gearing (6.25:1,
    # planes |x| 22 / 14) -> a Ø4 HALF-shaft (|x| 6..88) -> a 27T m0.8 pinion (pitch
    # Ø21.6) at |x| 84 meshing the rack molded on its mast's -Y face. Two motors =
    # each antenna individually controllable (user); two more ULN2003s (own 9, now
    # 4 used). Speed: ~15 RPM usable x 6.25 x 67.9 mm/rev ~= 104 mm/s -> 50 in ~0.5 s;
    # force ~0.3 N per rack (20 mN.m / 6.25 / r10.8) -- masts stay light (<10 g) and
    # slide free. Back-drive: gear-up means masts sag de-energized; a friction O-ring
    # in each top guide bore parks them (docs/ASSEMBLY.md).
    # PLACEMENT (probe-driven): masts sit at y -31 BEHIND the tilt clamp tubes (Ø14 at
    # y -18/z 153, spanning to |x| 99 -- a y -24 mast ran through them at full
    # retract); the screen tray's rail+pillar bands own |x| 56..68 z<196 and the tilt
    # drivetrain sweeps |x|<24 z<174, so every gear at |x|<24 keeps its tips above
    # z 176 and the motor bodies span the free 25.7..53.5 band. The half-shafts pass
    # OVER the rail band (z 205 > 196) and behind the screen (rear face -7).
    # Homing: stall the masts down (tip caps bottom on the top-wall bosses).
    "ant_x": 85.0, "ant_y": -31.0,  # mast axes (mirrored +-)
    "ant_mast_d": 6.5,      # mast shaft Ø (slides in Ø7 top-wall bore, 0.25/side)
    "ant_travel": 50.0,     # max extension past the head top surface
    "ant_mast_z": (147.0, 242.5),   # retracted shaft span: top = body_z_top + 0.5 (cap rests
                            # on the top-wall boss); tracks the 2026-07-11 forehead raise.
                            # Rack (150..214) still meshes the z-205 pinion at +50 extension
    "ant_rack_top": 214.0,  # rack teeth stop here (mast-local): above is never meshed
    "ant_tip_d": 11.0, "ant_tip_h": 14.0,   # knurled cap, rests 0.5 over the boss
    "ant_gear_m": 0.8,      # module for all antenna spur gears + racks
    "ant_pinion_t": 27,     # rack pinions, pitch Ø21.6
    "ant_gear_big_t": 30, "ant_gear_small_t": 12,   # two 30:12 stages = 6.25:1 up
    "ant_cross_y": -46.1, "ant_cross_z": 205.0,     # half-shaft axis: pinion tips
                            # reach y -34.3, kissing (0.05) the mast face -34.25
    "ant_idler_y": -29.33, "ant_idler_z": 204.06,   # idler: 16.8 mesh CD to both;
                            # G3 tips y -16.3 (9.3 clear of the screen mesh -7)
    "ant_motor_y": -37.875, "ant_motor_z": 189.6,   # motor SHAFT axis; can axis is
                            # +7.875 in Y (offset rolled -Y): can (y -30, z 189.6),
                            # 22.3 off the half-shaft line, G1 tips z 176.6 > 174
    "ant_gear_x": (22.0, 14.0),     # G1/G2 plane (on the shaft |x| 16..25.7) / G3/G4
                            # plane (inboard of the Ø27.25 gearbox at |x| 25.7..34.7)
    "preview_ant_mm": 15.0, # GLB preview extension; ANT=<mm> overrides (0..50)
    # Orange picture-frame around the head-back service area (design-ref back.jpg). The
    # louvres + motor-bay opening play the reference's inner hatch. Bottom band notched
    # over the deep-head motor bay (back wall open x +-33 up to z=168 for the tilt sweep;
    # the frame must not hover in that envelope).
    "hatch_frame_w": 160.0, "hatch_frame_h": 105.0,  # outer X x Z
    "hatch_frame_band": 13.0,   # ring width
    "hatch_frame_t": 3.0,       # proud of the back face
    "hatch_frame_cz": 151.0,    # outer z 98.5..203.5; inner 111.5..190.5 (louvres
                                # 171..187 land inside the opening)
    # (rear_pack + tilt_shroud REMOVED 2026-07-10: the rear_pack slabs and the detached
    # shroud were superseded by the door's extruded pod, which closes the whole opening
    # and hides the tilt motor inside its cavity. See the door pod params below.)

    # --- HEAD REAR DOOR (task #26): the wall inside trim_hatch_frame is removable ---
    # U-SHAPED (the bottom-centre stays OPEN: it is the tilt-sweep motor bay, x +-33 /
    # z 78..168 -- the pan-frame drivetrain crosses the wall plane there at tilt
    # extremes, so a head-riding door may not fill it). Outline clears the screen-
    # standoff roots (bosses reach |x| 57.11, gusset webs |x| 59.6..66.6) and keeps
    # the seam inside the orange frame opening (x +-67, z 111.5..190.5).
    "door_hx": 56.5,            # door half-width (0.61 to the Ø9 standoff boss edge)
    "door_z": (113.5, 190.2),   # outline z span (2 over the frame's inner 111.5;
                                # 0.3 under its inner 190.5 -> seam reads in-frame)
    "door_notch_hx": 35.0,      # bay notch half-width (2 past the x +-33 bay edge)
    "door_notch_ztop": 170.0,   # bay notch top (2 past the z=168 bay lip)
    "door_lip": 2.0,            # fixed-wall support lip all around (through-void inset)
    "door_fit": 0.15,           # perimeter fit clearance
    # Retention (2026-07-10, user: "easy to open and close" -- replaced the 2x M3 csk +
    # captive nuts): 2x 3mm top HOOK tabs (the pivot) + per-leg SNAP TONGUES at the
    # bottom. Each tongue is the leg's own outer strip, freed by one vertical slit
    # (root at the top, the door's bottom edge is the free end), with an outboard barb
    # at plug level that clicks behind the fixed wall band beside the void. Close =
    # hook the top, swing in, click. Open = firm pull on the door's bottom edge (the
    # 3.4-proud face panel is the finger grip): the barb's back ramp cams the tongue
    # inboard -- no tools. NOT magnets (they walk and chatter under stepper vibration);
    # the snap preloads the flange into its rebate like the screws did.
    "door_hook_x": 47.0, "door_hook_w": 14.0, "door_hook_lip": 3.0,
    "door_snap_w": 2.75,        # tongue strip width in X at plug level
    "door_snap_slot_w": 1.5,    # freeing slit width (prints as a clean gap)
    "door_snap_root_z": 146.0,  # slit top = tongue root (L~29 to the barb -> ~1% strain
                                # at 1.2 engagement, in-plane of the face-down layers)
    "door_snap_barb": 1.2,      # barb proudness past the void wall (engagement depth)
    "door_snap_barb_z": (116.0, 119.5),  # barb z band (just above the plug bottom edge)
    # EXTRUDED REAR POD (2026-07-10, replaced the raised panel + latch/hinge cosmetics +
    # through-relief): the stepped "backpack" bump from the design ref, hollow so the
    # tilt drivetrain's swept intrusion lives INSIDE it (no relief hole). See the pod
    # block in build_head_parts() for the sweep numbers.
    "door_face_r": 8.0,      # rounded corners on the pod root-slab footprint
    "pod_top_z": 169.0,      # flat pod top -- below the louvre band (~171..187) so the
                             # vents stay open above the bump, like the reference
    "pod_tiers": ((62.0, -85.0), (51.0, -95.0), (38.0, -105.0)),  # (half-width, rear y)
                             # 15/25/35 proud of the wall (2026-07-10, user: "much more
                             # depth horizontally" -- was 6/10/15)
    "pod_cavity": (17.0, -98.0, 130.0, 162.0),   # hx, floor y, z0, z1 -- wraps the
                             # probe-measured drivetrain sweep (y to -78.1) with margin
    "pod_notch": (27.0, 134.0, -98.0),  # center-bottom corridor (half-width, top z,
                             # floor y): at the +-33.8 stall the neck cheeks rake to
                             # x +-24 / y -86.9 / z <=130.7 in the DOOR frame (probe-
                             # measured). Now a POCKET, not a through-hole: the deep
                             # pod's rear wall (7 solid) closes it from behind
    # Chassis FRONT fascia (design-ref front.jpg). Front wall: y=78 face, x +-60, z 7..52.
    "grille_cz": 32.0,      # orange surround outer 60x26 -> z 19..45: the toy-tank deck
                            # overhang owns z > 46, so the ring dropped onto the (now
                            # 18..46) vertical wall band and GREW to swallow the US
                            # barrels inside its 52x18 opening (z 23..41)
    "grille_w": 60.0, "grille_h": 26.0, "grille_band": 4.0, "grille_t": 2.5,
    "us_dx": 13.0,          # ultrasonic barrel centers at x=+-13 (HC-SR04 transducer pitch ~26)
    "us_cz": 32.0,          # barrel Ø16 -> z 24..40, centred in the grille opening (the
                            # 28.5 spot collided with the relocated ring's lower band)
    "us_d": 16.0,
    "lamp_x": 54.0, "lamp_cz": 23.0,   # amber corner lamps 12x7, proud 2, on the PROW
                            # CHEEK noses (2026-07-11; z 26 -> 23 so the wire drill at
                            # lamp_cz passes UNDER the nut pocket floor z 25; bottom
                            # 19.5 stays 1.5 above the glacis crease z 18 at the nose)
    "fled_cz": 12.0,        # white dot strip now ON the glacis face, tilted 33 deg with it
    # Chassis REAR styling (design-ref back.jpg): orange frame panel (the wall shows
    # through the opening as the 'hatch') above the USB-C slot (x +-7, z 15..23), and a
    # silver cylinder pod low-right (speaker/buzzer placeholder).
    # rear_panel_* retired 2026-07-11: trim_rear is now a TWIN of the front grille ring
                            # (grille_* params) framing the rear obstacle HC-SR04
    "rear_cyl_x": 41.0,     # image-RIGHT in the ref back view; 47 -> 41 2026-07-11: on
                            # the prow cheek nose the Ø10 sound bore (36..46) must stay
                            # 1.0 inboard of the nut pocket wall x 47
    "rear_cyl_cz": 30.5, "rear_cyl_d": 14.0,    # raised over the rear glacis (was 16)
    # Raised camera POD on the forehead (design ref: the camera reads as an eye). Pure
    # cosmetic shell over the recessed CM3: the bore flares 45 deg/side from the existing
    # countersink, wider than the 75 deg-diagonal FoV cone (half ~37.5 deg), so no vignette.
    "cam_pod_w": 24.0, "cam_pod_h": 20.0,   # pod footprint on the face (X x Z); h 20 (was 18):
                                            # the flare mouth needs a real lip top/bottom -- 18
                                            # left a 0.05 knife edge at the face (PRINTABILITY 1)
    "cam_pod_t": 5.0,                       # proud of the face
    # Gripper arms (design ref, PLACEHOLDER pose + shapes): shoulder pivots on the side
    # rails, tucked pose (claws down-forward beside the chassis front). Actuation, joint
    # hardware, and the head-vs-platform mount decision are a later mechanism pass.
    "arm_x": 127.0,         # arm plane center: outboard of the pods (outer face 118.8); a
                            # standoff tube bridges the rail face (107.5) to the shoulder

    # --- Cosmetic-part FIXINGS (task #15): every styling part gets a real joint ---
    # Pure cosmetics: blind Ø3 locating pins into Ø3.2 x 2.5 wall sockets + glue (2.5 deep
    # in a 4-wall leaves 1.5 skin; nothing pierces a visible face or the screen / display /
    # camera voids). Pin protrudes 2.3 into the 2.5 socket (0.2 bottoming + glue room).
    "fix_pin_r": 1.5, "fix_socket_r": 1.6, "fix_socket_deep": 2.5, "fix_pin_len": 2.3,
    "fix_pin2_r": 1.0, "fix_socket2_r": 1.1,   # Ø2 pins (camera_pod, sensor_rear cap)
    # trim_rail sockets, (y, z) per side wall (mirrored in x). Keep-outs: the shoulder
    # hardware below (z 125..136), the bezel<->back SIDE POSTS at (x +-97.5, z 119.8 and
    # 198.3, r 4.3 + their y-axis M3 bores) -- unioned in build_head_parts AFTER the
    # shell sockets are cut, so a socket in their z bands gets silently REFILLED (a pin
    # at z 202 shipped 1.17 mm^3 into the upper post before this was caught) -- the
    # pivot boss / clamp tubes (y -18, z 153; the z-146 sockets shave a <1 mm sliver off
    # the boss rim at x>100, harmless), and the right wall's Pi I/O slot (y -8.5..6.5,
    # z 166.5..183.5; the z-188 socket sits 1.9 above it).
    "rail_pin_pts": ((-8.0, 146.0), (8.0, 146.0), (0.0, 188.0)),
    # EAR MICS (2026-07-11, ordered: 2x 3.5 mm gooseneck "hose" mics, one per side;
    # v4 same day, user: "same distance from borders as humans"): Ø15 grommet bore per
    # side wall, only the foam tip out. HUMAN-PROPORTIONED spot: human ears sit ~55-60%
    # of the way back from the face profile and near the head's vertical center. Head
    # depth 103 (face 33, back -70) -> y -29 = 60.2% back (hit exactly). Vertical
    # center is 165 (shell 88..242), but the Ø26 tilt pivot-hub boss + Ø14 clamp tube
    # cluster at (y -18, z 153) blocks it: the Ø15 bore needs center distance >= 22
    # from the boss axis (13 + 7.5 + 1.5 margin), and at y -29 that forces z >= 172.1.
    # COMPROMISE: z 172.5, 7.5 above center (dist 22.4 -> 1.9 bore-to-boss gap). Also
    # clear: trim rails (y +-13), sd slot (z <= 164.5, left), Pi I/O slot (y >= -8.5,
    # right), wall flat band (corner curve starts y -54), foam tip vs clamp tubes
    # inside (yz gap 5.0), screen stack (y >= -7).
    "ear_y": -29.0,
    "ear_z": 172.5,
    # ARM SHOULDER INTERFACE (docs/ARM-MECH.md; arms are ARMS=1-gated but the head prints
    # the interface NOW so option B/C arms bolt on without a head_back reprint): per side
    # wall, 2x M3 captive-nut pockets + a Ø6.2 servo-lead pass, all under the rail.
    # HORIZONTAL pair (y +-8) at z 132, not ARM-MECH's vertical pair: any vertical pair
    # straddling z 130 runs into the bezel<->back side post at (x 97.5, z 119.8) whose
    # r4.3 boss + y-axis M3 bore own the wall's z 115.5..124.1 band. The pockets are cut 2.8
    # deep from the wall's INTERIOR face (x 98.5; probe-verified -- the screen-pocket box
    # only spans +-97, narrower than the +-98.5 hollow, so the side wall stays 4.0 thick),
    # leaving a 1.2 outer skin that hides under the screwed-and-glued rail (compression
    # only). The nut sits flush INSIDE the wall: no inboard boss (ARM-MECH's pad idea is
    # forbidden -- the display's widest edge |x| 96.48 needs its 2.0 side clearance to
    # slide in). Nuts drop in from the open pocket mouths BEFORE the screen module
    # installs; one lands in the bezel wall (y +8), one in head_back (y -8) -- the split
    # plane is y 2.0. Screws: M3x10 from outside through rail + wall (tip stops at x
    # 97.5, 1.0 clear of the display edge; an M3x12 tip at 95.5 would hit it). Arms off:
    # same screws through a printed blank flange.
    "shoulder_screw_yz": ((-8.0, 132.0), (8.0, 132.0)),
    "shoulder_wire_yz": (0.0, 130.0), "shoulder_wire_r": 3.1,   # Ø6.2 lead pass (plugged;
                            # the rail stays uncut -- an option-C retrofit reprints it)
    "shoulder_nut_deep": 2.8,
    # trim_hatch_frame pins, (x, z) on the back wall: on the 13-wide ring band's corners,
    # clear of the louvres (x +-25, z 153..189), cable port (x +-24, z 113..147), neck
    # slot (x +-31 below z 166) and the bezel<->back top/bottom posts (x +-40, z 221/92.6).
    # The task-suggested (+-60, 190/112) failed verification: x 60 < inner band edge 67,
    # both points land in the frame OPENING, not on the band.
    "hatch_pin_pts": ((-72.0, 196.0), (72.0, 196.0), (-72.0, 106.0), (72.0, 106.0)),
    # trim_fascia pins, (x, z) on the chassis front wall under the fin backing webs
    # (x 28..49.5, z 38..54): >6 clear of the hex field (|x| <= 24.8, z 40.3..51.7) and
    # the Ø16.6 barrel passes (+-13, z 26). The task-suggested (+-38, 15) / (+-20, 52)
    # failed verification: nothing of trim_fascia touches the wall at z 15 (ring z 36..56,
    # webs/fins z 38..54), and (+-20, 52) sockets pass within ~0.7 of the hex pockets.
    "fascia_pin_pts": ((-28.0, 32.0), (28.0, 32.0), (0.0, 21.0), (0.0, 43.0)),   # ring-band
                            # pins (trim pass 2026-07-11: the fins/webs were deleted --
                            # vestigial stubs once the toy-tank band shrank to 28 tall;
                            # the slope hex field carries the vent look now)
    # trim_rear pins, (x, z) on the rear wall band (side bands x 22..36, bottom z 24..28):
    # clear of the USB slot (x +-7, z 15..23, 1.4 gap) and TT tab pockets (x 43.5..47.7).
    "rear_pin_pts": ((-28.0, 32.0), (28.0, 32.0), (0.0, 21.0)),   # ring-band pins (twin ring)
    # camera_pod Ø2 pins, (x, z) on the bezel face: with the bay raised (cam_lens_z 226)
    # the whole pod footprint (z 216..236) lands on solid forehead wall, so the pins sit
    # inside it symmetrically. Clear of the Ø8 aperture flare (r 8.94 > 4).
    "campod_pin_pts": ((-8.0, 230.0), (8.0, 230.0)),
    # antenna: Ø6 spigot under the collar -> Ø6.2 x 3 blind socket in the head top wall
    # (4 thick: 3 deep leaves 1.0 ceiling skin; camera pier |x|<16 and the top bezel
    # posts x +-40 both clear x -62). Glue or friction fit.
    "ant_spigot_r": 3.0, "ant_spigot_socket_r": 3.1, "ant_spigot_deep": 3.0,
    "wire_pass_r": 1.25,    # Ø2.5 wire passes (led_strip, led_front, lamps)
    # sensor_rear (bought Ø12-14 buzzer/speaker behind a printed grille cap): Ø10 sound/
    # wire through-hole in the rear wall + 2x Ø2 cap pins. The cap gains a Ø17 x 1.5 base
    # flange so the pins (x 38 +- 7) land 0.9 outside the Ø10 bore.
    "rearpod_hole_r": 5.0, "rearpod_flange_r": 8.5, "rearpod_flange_t": 1.5,
    "rearpod_pin_dx": 7.0,
    # --- microSD service slot (maintenance pass 2026-07-08): the Pi 5's card is modeled in
    # the pins-out mesh at x -41.6..-40.0, y 9.4..10.4, z 151.0..162.1 and ejects toward -X
    # down a probe-verified FREE corridor to the left wall (nothing between the card edge and
    # the pocket wall at -97 in this y/z band; the display's deep back never reaches x<-90
    # here). A slot through the left wall + trim_rail_L on the eject axis swaps the card with
    # straight forceps (~61 mm reach, sight line down the axis) -- before this, a reflash
    # meant door + 8x M3x35 + screen module out. The slot sits FORWARD of the split plane
    # (y=2) so it lands in the BEZEL's side-wall band; y max 12.0 keeps a 1.0 web to the
    # rail edge (y 13), y min 7.4 keeps 1.1 to the pivot boss sweep (boss reaches y -5...
    # far below). Plugged by sd_plug (friction fit) against desk dust.
    "sd_slot_y": (7.4, 12.0),       # slot Y band (card faces at 9.4/10.4: 2.0/1.6 jaw room)
    "sd_slot_z": (148.5, 164.5),    # slot Z band (card 151..162.1 + 2.5/2.4; rail pin at
                                    # (8,146) keeps a 1.4 ligament to the corner)
    "sd_plug_fit": 0.15,            # plug body clearance per side

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


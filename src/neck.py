"""Neck parts: tilt clevis column + removable tilt-motor cartridge carrier.

Split out of the original monolithic build.py (2026-07-10); see
build.py for the assembly entry point and the overall design notes.
"""
import numpy as np
import shapely.geometry as sg
from trimesh.creation import extrude_polygon
from trimesh.transformations import rotation_matrix as R
from params import P
from geo import _color, box, cyl, inter, nut_slot, rounded_box, sub, uni
from gears import worm_cd


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
        # TILT-STOP POST (homing pass 2026-07-08): a block r 12..17 straight behind the
        # axle (y -35..-30, z zt +-2.5), spanning x 20..32 so the head's +-55 deg stop
        # fins (x 27..31, build_head_shell) land flat on it at +-33.8 deg. It starts at
        # r12 because boxes near the axis are angularly fat at the root (the first cut
        # of this feature contacted the fins at 28.8 deg and failed the +-30 sweep).
        # A leg drops to the cheek-root block / cheek rear flank for fusion; the block
        # clears the bearing-seat bore (r12 > seat r6.4), the motor can (z 150.5+ vs
        # can top 147.4) and the head's clamp tubes (r7).
        post = box(12.0, 5.0, 5.0)
        post.apply_translation((sx * 26.0, yt - 14.5, zt))
        leg = box(6.0, 5.0, 22.0)
        leg.apply_translation((sx * 23.0, yt - 14.5, zt - 9.0))
        parts += [post, leg]

    # tilt WORM-motor bracket: the motor shaft runs along +Y (perpendicular to the tilt axle) and
    # carries the worm; the worm meshes the wheel on the axle. center distance = wheel_r + worm_r.
    wx = P["worm_wheel_x"]
    cd = worm_cd()
    wz = zt - cd
    # Stage 2R: the worm group sits behind the axle (face_y offset 4 -> 8 -> 9.5 in stage 5,
    # 9.5 -> 10.0 with worm_len 14 -> 13 in the cooler pass 2026-07-13 so the plate, motor,
    # can pocket and carrier all HOLD at y -34.5): at -30 tilt the stack's rear (GPIO pins)
    # sweeps down-back past the worm tail. Threads span y -30.5..-17.5, still covering the
    # wheel contact at yt (see PARAMS worm_len for the cooler-clearance derivation).
    face_y = yt - 0.5 * P["worm_len"] - 10.0             # motor mount face (behind the worm)
                                                         # keep in sync with build.py +
                                                         # build_tilt_carrier()
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
    # outboard support for the worm's far end (the 28BYJ shaft only reaches ~6 mm into the
    # worm; worm separation force presses DOWN, so an open-top support is load-correct).
    # CREST-RIDING since the Pi 5 cooler pass 2026-07-13: the old scheme (bare Ø5 tail stub
    # in a Ø5.4 half-groove at y -15.5..-13, stage-5 D2 fix) reached y=-12 and penetrated
    # the cooler keep-out +2.7/+1.9 at the -33.8 nose-down stall. The stub and its pad are
    # GONE; instead a support block under the THREAD SPAN carries an open-top r5.5
    # half-groove (crest r 5.275 + 0.225 running clearance, same class as the old 0.2)
    # whose bottom land sits at y -21..-18 -- DIRECTLY under the wheel contact plane
    # (y=-18), mechanically better than the old past-the-mesh band. The wheel never
    # reaches it (wheel tip bottom z 144.75 >> block top z=wz); grease shared with the
    # mesh; extraction just screws the crests through the open groove. Behind it the
    # riser top is still split into side prongs by the r5.9 free-rotation relief
    # (y -34..-21). The support's front face is shaped by the STALL-ENVELOPE trim below.
    arm = box(18, 16, 6); arm.apply_translation((wx, yt - 10.0, wz - 9.5))        # y -36..-20
    riser = box(18, 5, 16.5); riser.apply_translation((wx, yt - 4.5, wz - 8.25))  # z 124.6..141.1
    supp = box(18, 7, 9.5); supp.apply_translation((wx, -17.5, wz - 4.75))        # y -21..-14
    parts += [arm, riser, supp]

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
    # worm PASS through the bracket plate: Ø12.2 (cartridge pass 2026-07-08: was Ø10, just
    # shaft-boss clearance -- now the WORM (OD 10.55) extracts rearward through the plate
    # with the motor as one cartridge; sliding the worm axially out of mesh only spins the
    # free wheel, worm-as-rack, so the head gently tilts as the cartridge pulls out).
    sh = cyl(6.1, 20, axis="y"); sh.apply_translation((wx, face_y, wz)); neck = sub(neck, sh)
    # (the old in-plate M4 ear holes are GONE: the motor's ears now bolt to the removable
    # tilt_carrier on the bench -- see build_tilt_carrier. The plate instead takes the
    # carrier's 4 M3s in thread-form pilots, driven from the open rear bay.)
    can_z = wz - P["motor_shaft_off"]
    # Carrier screw landings, re-derived (review 2026-07-08: the first cut gave the upper
    # M3x16s only 2.0 of thread and jammed the lower ones into a 3.9 hole needing 5.5).
    # UPPER pair: a Ø8 x 2 raised PAD on the plate rear face moves the landing to -38.5,
    # so an M3x16 through carrier (4) + boss (8) forms 4.0 of thread in a 6.0 pilot.
    # LOWER pair: lands on the column rear face (y=-40, the plate region is embedded in
    # column there); pilot 6.5 deep -> 5.5 of thread, 0.95 tip margin.
    for cpx, cpz in ((-14.0, wz + 4.1), (14.0, wz + 4.1)):
        pad = cyl(4.0, 2.5, axis="y")                    # 0.5 buried: face-tangent bodies
        pad.apply_translation((wx + cpx, -37.25, cpz))   # don't fuse (stage-4 D4)
        neck = uni([neck, pad])
        pil = cyl(1.25, 6.0, axis="y")
        pil.apply_translation((wx + cpx, -35.6, cpz))    # spans -38.6..-32.6
        neck = sub(neck, pil)
    for cpx, cpz in ((-13.0, 120.0), (13.0, 120.0)):
        pil = cyl(1.25, 6.5, axis="y")
        pil.apply_translation((wx + cpx, -36.85, cpz))   # spans -40.1..-33.6
        neck = sub(neck, pil)
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
    # worm-thread envelope relief: Ø11.8 bore (thread tip r 5.275 + 0.625 running clearance)
    # about the worm axis over the REAR thread span (y -34..-21) -- splits the riser top
    # into the two side prongs and lets the worm rotate free (D2)
    relief = cyl(5.9, 13.0, axis="y"); relief.apply_translation((wx, -27.5, wz))
    neck = sub(neck, relief)
    # Ø11 CREST-RIDING half-groove across the support block (open top; the thread crests
    # ride it, 0.225 radial running clearance -- see the support-block note above). Runs
    # y -21.5..-13; the stall-envelope trim below owns the actual front face.
    groove = cyl(5.5, 8.5, axis="y"); groove.apply_translation((wx, -17.25, wz))
    neck = sub(neck, groove)
    # vertical cable channel down the column: 16x8 obround (was Ø12 -- a 5-pos JST-XH head
    # is 14.9 x 5.9 and must pass pre-crimped). Long axis along X, at (0, neck_chan_y):
    # pushed behind the column center so the chin notch (rear y=-19.5) leaves a full wall
    # in front of it (channel front y=-22).
    chan = extrude_polygon(sg.LineString([(-4, 0), (4, 0)]).buffer(4.0), P["neck_top_z"] - z0 + 30)
    chan.apply_translation((0, P["neck_chan_y"], z0 - 15))
    neck = sub(neck, chan)
    # SIDE EXIT window at the column's top-left corner (CABLE-CHECK defect B): the chimney
    # above the channel is boxed in by riser / cheek-root / cradle arm / worm to a 1.0 mm
    # escape gap, so the wire could never leave. This 12x8x10 cut (x -18..-6, y -30..-22,
    # z 117..127) is pure column / riser-bottom-corner material and opens the channel into
    # the open LEFT bay (x -24..-9, free 20 mm up + left, 1.8 clear of the -30 deg head
    # sweep). The +x mirror is NOT available: the gusset fills the right bay.
    exitw = box(12.0, 8.0, 10.0)
    exitw.apply_translation((-12.0, -26.0, 122.0))
    neck = sub(neck, exitw)
    # ROOT JOINT: neck -> pan_platform, 3x M3x14 + SIDE-SLIDE CAPTIVE HEX NUTS + 2
    # REGISTRATION PINS (fastening campaign 2026-07-15, audit P1 row 1 + holding gap 1).
    # Was 3x M3 into Ø2.5 thread-form pilots with ZERO registration: the root of the
    # entire head stack self-tapped into PLA, and nothing held the column square while
    # the 3 blind screws were driven up from under the platform. Now the proven pedestal
    # pattern (chassis.py build_chassis_pedestal): the platform keeps its clearance bores
    # + underside head counterbores, the column base takes Ø3.5 clearance THROUGH-bores
    # and a hex trap per bolt, and 2 printed pins on the platform top spigot into blind
    # sockets here so the column self-locates (and can't rotate) before any screw turns.
    # Bench joint, fully open: drop the 3 nuts into their slots (they slide in along the
    # column's own open rear/side faces, flats on the slot walls = the rotation lock),
    # lower the column onto the pins, drive the screws from underneath.
    # Circle unchanged, clocked (270,30,150) at rad 16.5 -- stage 5: with the column at
    # ny=-17 the old (90,210,330)/rad-12 put a hole 2 mm from the PAN AXIS; 16.5 (was 16.0)
    # keeps the 270-deg bolt's Ø6.5 platform counterbore 0.25 off the cable slot
    # (CABLE-CHECK minor). Keep in sync with build_pan_platform().
    # Nut seat z0+6 = 72.0: the platform's cbore seats the head at z 62.4, so an M3x14
    # tips at 76.4 = 3.1 (>2 threads) past the nut's 73.4 top face, inside the Ø3.5 bore
    # which runs to 79. Slot exits: the 270 bolt opens -Y through the column rear face
    # (y -40, 6.5 away, 3.5 clear of the cable channel at y -30); the 30/150 pair opens
    # +-X through the side faces (9.7 away, and z 70.6..73.4 sits under the z 74/82
    # panel-line grooves and well under the ULN bosses at z 77+).
    nut_z = z0 + 6.0
    for a, odir in ((270, (0, -1, 0)), (30, (1, 0, 0)), (150, (-1, 0, 0))):
        rad = 16.5
        hx = rad * np.cos(np.radians(a)); hy = ny + rad * np.sin(np.radians(a))
        bore = cyl(P["m3_clear_r"], 14.0)
        bore.apply_translation((hx, hy, z0 + 6.0))          # spans z0-1 .. z0+13
        neck = sub(neck, bore)
        neck = sub(neck, nut_slot((hx, hy, nut_z), screw_axis="z", open_dir=odir,
                                  size="M3", length=14.0))
    # blind Ø4.2 sockets for the platform's 2 printed Ø4.0 registration pins
    # (+-18, -32): 36 mm apart (fixes rotation), inside the column footprint (boundary
    # x 23.8 at this y -> 3.7 wall), clear of the cable channel (x +-8), the 270 nut
    # slot (x +-2.85) and the platform's cable slot 6 mm away. +0.1/side (seam-dowel rule).
    for sx in (-1, 1):
        sock = cyl(2.1, 4.0)
        sock.apply_translation((sx * 18.0, -32.0, z0 + 1.5))    # z0-0.5 .. z0+3.5
        neck = sub(neck, sock)
    # tilt ULN2003 driver standoffs on the column BACK face (same pattern as the base's pan
    # driver mount; motor + driver both live on the pan group so their leads cross no joint).
    # Board center DROPPED 110 -> 93 (review 2026-07-08): at 110 the board plane
    # (y -48..-49.6, z 94..126) ran straight through the tilt_carrier's band
    # (y -50.55..-46.55, z 113.2..153.2) -- 162 mm^3 of overlap the gate can't see because
    # the board itself isn't modeled. At 93 the board spans z 77..109, 4.2 under the
    # carrier, still fully on the column back (z 66..125).
    uln_y = ny - P["neck_d"] / 2                      # column back face
    for sx in (-1, 1):
        for sz in (-1, 1):
            # 8.5 long, buried 0.5 INTO the column: a face-tangent cylinder does not fuse
            # in uni() and exported as a disjoint floating body (stage-4 defect D4)
            b = cyl(3.0, 8.5, axis="y")
            b.apply_translation((sx * P["uln_w"] / 2, uln_y - 3.75, 93 + sz * P["uln_h"] / 2))
            neck = uni([neck, b])
            pil = cyl(1.25, 12, axis="y")
            pil.apply_translation((sx * P["uln_w"] / 2, uln_y - 3, 93 + sz * P["uln_h"] / 2))
            neck = sub(neck, pil)
    # cosmetic PANEL-LINE GROOVES (neck styling pass 2026-07-12, design-ref language: the
    # ref neck is stepped/blocky, ours was a smooth extrusion). Two 1.2-deep x 2.6-tall
    # horizontal grooves per SIDE face (x +-24), z 74 / 82 -- the band visible through the
    # deck-to-head gap (deck 66, head bottom 88). Side faces only: the front face above
    # z 69 is the chin-notch face with a 2.5 wall to the cable channel, and the rear face
    # carries the ULN bosses (z 77..109). Above z 69 the chin notch voids the column at
    # y > -19.5, so the grooves live on the REAR half of the side face (y -38..-21, dying
    # into the r10 corner round like a product panel line); the 16 mm side wall to the
    # x +-8 channel laughs at a 1.2 cut.
    for gz in (74.0, 82.0):
        for gsx in (-1, 1):
            gr = box(2.4, 17.0, 2.6)
            gr.apply_translation((gsx * 24.0, -29.5, gz))
            neck = sub(neck, gr)
    # STALL-ENVELOPE TRIM (Pi 5 cooler pass 2026-07-13): subtract the cooler keep-out
    # (PARAMS pi5_cooler_*, the head-riding envelope tools/probe_cooler.py sweeps) POSED
    # AT THE -33.8 NOSE-DOWN HOMING STALL and inflated 0.6/side. The envelope's swung
    # bottom-rear corner passes lowest/furthest-back at the stall (binding pose for every
    # z >= ~131.5, spot-checked vs -25/-29/-30 deg), so this one cut shapes the support
    # block's front into the correct 33.8 deg slope (bearing land y -21..-18 at the groove
    # bottom, y ~-14.3 reach at the top) AND bevels the riser/gusset/cheek front-bottom
    # corners, which the envelope corner arc (r 21.58 about the axle) grazed within ~0.06.
    # The bearing hoops + cheek fronts NEAR THE AXLE are never cut: they are r 9.5 about
    # the tilt axle vs the rear face's constant 10.28 axis distance (0.78 clear at every
    # pose, 0.18 vs the inflated cutter). The clip box only keeps the far-field tidy.
    # Margin 0.6 = the probe-reported floor for neck_clevis.
    cw, cdp, chh = P["pi5_cooler_wdh"]
    bcx, bcz = P["pi5_cooler_board_c"]
    X0, Z0 = P["pi5_board_org"]
    minf = 0.6
    cut = box(cw + 2 * minf, cdp + 2 * minf, chh + 2 * minf)
    cut.apply_translation((X0 + bcx, P["pi5_comp_face_y"] - cdp / 2, Z0 + bcz))
    cut.apply_transform(R(np.radians(-33.8), (1, 0, 0), (0, yt, zt)))
    clip = box(80.0, 400.0, 400.0)
    clip.apply_translation((0, 0, 150.0))
    neck = sub(neck, inter(cut, clip))
    _color(neck, "neck")
    neck.metadata["name"] = "neck_clevis"
    return neck


def build_trim_neckfoot():
    """Orange pedestal COLLAR at the column foot (neck styling pass 2026-07-12): a stepped
    chamfer-look ring that drops over the column and seats on the pan platform, so the neck
    grows out of a turret boss instead of a bare disc (ref language: chunky base + safety-
    orange band right under the neck). Pan group -- it rides the platform.

    Envelope (probed, see the styling-pass notes): the tilt-swept head bottom dips to
    z 70.6 right around the column, so the collar tops out at z 69.0 (1.6 clear) -- exactly
    where the column's chin notch begins, which the collar visually caps. Radially it is
    trimmed to r 44.3 about the PAN axis: the platform's solid top ends at the r45 rim
    rebate and the fixed clip tabs reach in to r 45.4 flush with the top, so the collar can
    never sweep over them while panning.

    Print: flat on its base, no support (the step is a flat roof over 1.6 mm -- bridges).
    Fixing: slip over the column from below BEFORE the neck bolts to the platform (the
    cheeks at x +-26 block a top-down pass), then 2x Ø3x6 pins dropped through the collar
    into the platform's blind sockets (build_pan_platform) + glue on the seat. Inner is a
    +0.25/side slip fit on the 48x46 column."""
    z0 = P["base_h"]                                     # platform top (collar seat)
    ny = P["neck_y"]
    # stepped body: full outline z 66..67.6, inset band z 67.6..69.0 (reads as a chamfered
    # plinth, prints as two clean perimeters)
    lower = rounded_box(64.0, 54.0, 1.6, 8.0)
    lower.apply_translation((0, ny, z0))
    upper = rounded_box(60.8, 50.8, 1.4, 7.0)
    upper.apply_translation((0, ny, z0 + 1.6))
    ring = uni([lower, upper])
    # column pass: +0.25/side slip on the 48x46 r10 column
    bore = rounded_box(48.5, 46.5, 5.0, 10.25)
    bore.apply_translation((0, ny, z0 - 1.0))
    ring = sub(ring, bore)
    # trim to r44.3 about the pan axis (platform solid top r45; clips flush at r45.4+)
    keep = cyl(44.3, 8.0, sections=96)
    keep.apply_translation((0, 0, z0 + 2.0))
    ring = inter(ring, keep)
    # 2x Ø3.2 pin bores straight down into the platform sockets (x band wall is 7.75 wide)
    for sx in (-1, 1):
        pb = cyl(1.6, 8.0)
        pb.apply_translation((sx * 27.0, ny, z0 + 1.5))
        ring = sub(ring, pb)
    _color(ring, "accent")
    ring.metadata["name"] = "trim_neckfoot"
    return ring


def build_tilt_carrier():
    """Removable TILT-MOTOR CARTRIDGE carrier (maintenance pass 2026-07-08). The 28BYJ is
    the likeliest part to die, and replacing it used to mean un-hanging the head and then
    reaching ear screws with 2.1 mm of driver room. Now: the motor's M4 ears bolt to THIS
    plate on the bench (open access), the worm goes on the D-shaft, and the loaded carrier
    inserts from the open rear bay: the can registers in the neck's Ø29 pocket (the mesh
    lead-in; worm CD is held by pocket + tail cradle, same registers the WORM.md mesh was
    verified against), the worm passes the plate's Ø12.2 bore, and 4x M3x16 drive from the
    rear through Ø7 bosses into the plate's thread-form pilots. Extraction reverses it.
    CAVEAT (review 2026-07-08): sliding the worm out spins the free wheel (worm-as-rack)
    only while the head can rotate: clearing the mesh needs ~6.0 mm of axial travel =
    ~46 deg of head nod, but the fin hard stops allow only ~34 deg down from neutral --
    with the head hung and grubbed, DRIVE THE HEAD FULLY UP first (extraction nods it
    down, banking the full ~68 deg range), or loosen the two head-clamp grubs. Before
    step 12 (head not hung) extraction is unconditional.
    The flanks keep only their rear wing over the cheek-corner zone (review: the first
    corner-clip cut severed the part into 3 bodies); the bottom ring is notched for the
    blue wiring box."""
    zt, yt = P["tilt_axis_z"], P["tilt_axis_y"]
    wz = zt - worm_cd()
    can_z = wz - P["motor_shaft_off"]
    face_y = yt - 0.5 * P["worm_len"] - 10.0             # neck bracket-plate front face
                                                         # (keep in sync with build.py +
                                                         # build_neck_clevis: -34.5)
    cy = -48.55                                          # carrier mid-plane (front -46.55:
    plate = box(46.0, 4.0, 40.0)                         # 0.05 off the motor-ear rear face)
    plate.apply_translation((0, cy, can_z))
    # cheek relief, TWO-STAGE (review iterations): the cheek slant's reach grows with
    # depth -- y -48.0 at z ~127, y -49.5 at z ~120, past -50.6 at z 116. So:
    #  (a) z 112..126.5, x 17..24: FULL clip (the cheek spans the whole carrier depth
    #      there). Connectivity holds via x 8.8..17 (the bore only reaches x 12.6 at
    #      z 126.5) -- the first severed-into-3-bodies cut clipped from x 14.
    #  (b) x 13.5..24, z 112..132: thin to the REAR WING (y -50.55..-48.4, 2.15 thick),
    #      clearing the shallower cheek reach above the clip by 0.4.
    for sxs in (-1, 1):
        cc = box(7.6, 8.0, 14.5)                         # (a) x 17..24.6, z 112..126.5
        cc.apply_translation((sxs * 20.8, cy, 119.25))
        plate = sub(plate, cc)
        fr = box(10.5, 2.4, 20.0)                        # (b) x 13.5..24, y -48.4..-46.0
        fr.apply_translation((sxs * 18.75, -47.2, 122.0))        # z 112..132
        plate = sub(plate, fr)
    # Upper bosses (8 long) land on the neck plate's raised Ø8 pads (-38.5, 0.05 air) at
    # x +-14 -- x +-19 clipped the cheek rear flanks, which bulge to y -37.2 over x 18..26
    # at this height, and the 2-thick pads buy the M3x16s 4.0 of thread (review fix).
    # The LOWER pair (6.5 long) lands on the COLUMN rear face (y=-40): below the column
    # top the plate region is embedded in column material.
    for bx, bz, bl in ((-14.0, wz + 4.1, 8.0), (14.0, wz + 4.1, 8.0),
                       (-13.0, 120.0, 6.5), (13.0, 120.0, 6.5)):
        b = cyl(3.5, bl, axis="y")
        b.apply_translation((bx, -46.55 + bl / 2, bz))
        plate = uni([plate, b])
    bore = cyl(14.55, 8.0, axis="y")                     # can pass Ø29.1 (can Ø28.25)
    bore.apply_translation((0, cy, can_z))
    plate = sub(plate, bore)
    notch = box(17.6, 8.0, 13.0)                         # wiring-box pass under the bore
    notch.apply_translation((0, cy, can_z - 14.0))
    plate = sub(plate, notch)
    for bx, bz in ((-14.0, wz + 4.1), (14.0, wz + 4.1), (-13.0, 120.0), (13.0, 120.0)):
        mc = cyl(1.75, 18.0, axis="y")                   # M3 clearance, carrier + boss
        mc.apply_translation((bx, -43.0, bz))
        plate = sub(plate, mc)
    for dxe in (-P["motor_ear_cc"] / 2, P["motor_ear_cc"] / 2):
        eh = cyl(2.1, 8.0, axis="y")                     # M4 ear holes (bench nuts)
        eh.apply_translation((dxe, cy, can_z))
        plate = sub(plate, eh)
    _color(plate, "neck")
    plate.metadata["name"] = "tilt_carrier"
    return plate



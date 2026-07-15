"""Tank chassis body: core, lower/deck split, belly plate, fascia, pod rails.

Split out of the original monolithic build.py (2026-07-10); see
build.py for the assembly entry point and the overall design notes.
"""
import numpy as np
import trimesh
import shapely.geometry as sg
from trimesh.creation import extrude_polygon
from trimesh.transformations import rotation_matrix as R
from params import DEG, P, TAU
import geo
from geo import (_color, _orient, blind_socket, box, cyl, fix_pin, frustum, hex_prism, inter, rounded_box, sub, teardrop, uni)
from tracks import _track_zc, _spr_cz
from pan import _pan_stack


# M3 hex ACROSS-CORNERS (geo.NUT["M3"] = (AF 5.5, t 2.6)). A hex with its FLATS on
# the slot walls spans AF*2/sqrt(3) along the insertion run, NOT AF -- which is why
# the hand-rolled slide-up slots' top stops use M3_AC/2 (3.175) and not AF/2 (2.75).
# geo.nut_slot() now owns this correction itself: pass it the SCREW AXIS and it cuts
# the seat ac/2 behind, so a nut pushed home centres on the bore (see its docstring
# for the pedestal defect that motivated it). Do NOT pre-offset nut_slot centres.
M3_AC = geo.nut_ac("M3")                             # 6.35 across corners


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
    # (fins + backing webs deleted in the 2026-07-11 trim pass: on the 28-tall toy-tank
    # wall band they read as crammed stubs between the ring and the lamps; the slope
    # hex field owns the vent look now, the ring alone frames the sensor eyes)
    fascia = ring
    # FIXING: glue + 4x Ø3 pins on the fin-web backs into blind front-wall sockets
    # (PARAMS fascia_pin_pts; sockets cut in build_base)
    pf = [fascia]
    for px, pz in P["fascia_pin_pts"]:
        pf.append(fix_pin(P["fix_pin_r"], P["trim_pin_len"], (0, -1, 0), (px, fw, pz)))
    fascia = uni(pf)
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
    # rear obstacle ultrasonic (2026-07-11): the same board + barrels mirrored onto the
    # rear wall inside the twin ring -- reversing obstacle detection to pair with the
    # rear cliff sensor. Board sits against the inner wall face; the deck-split bosses
    # at (+-34, -113) start outboard of its +-22.85 edge.
    usr = [box(45.7, 1.6, 20.9).apply_translation((0, -(fw - 5.0 - 0.8), P["us_cz"]))]
    for sx in (-1, 1):
        b = cyl(P["us_d"] / 2, 13.0, axis="y", sections=48)
        b.apply_translation((sx * P["us_dx"], -(fw - 5.0 + 6.5 - 0.75), P["us_cz"]))
        usr.append(b)
    usrpod = uni(usr)
    _color(usrpod, "sensor"); usrpod.metadata["name"] = "sensor_us_rear"
    parts.append(usrpod)
    # cliff sensors: HC-SR04 boards against the deck slope skins' backs (pockets +
    # bores in build_chassis_parts), barrels through the skin, ~8 proud like
    # sensor_us. Front looks down-forward (driving), rear down-backward (reversing).
    sa_ = np.arctan2(P["base_h"] - P["chassis_split_z"], P["deck_overhang"])
    for sgn, cnm in ((1, "sensor_cliff"), (-1, "sensor_cliff_rear")):
        sn_ = np.array([0.0, sgn * np.cos(sa_), np.sin(sa_)])
        nnf = np.array([0.0, sgn * np.sin(sa_), -np.cos(sa_)])
        pb_ = np.array([0.0, sgn * fw, P["chassis_split_z"]]) + P["cliff_v"] * sn_
        brd = box(45.7, 20.9, 1.6)
        brd.apply_transform(R(np.pi + sgn * sa_, (1, 0, 0)))
        brd.apply_translation(pb_ - 4.8 * nnf)       # in the skin-back recess, 0.2 gaps
        cliff = [brd]
        for sx in (-1, 1):
            b = cyl(P["us_d"] / 2, 12.0, sections=48)
            b.apply_transform(R(np.pi + sgn * sa_, (1, 0, 0)))
            b.apply_translation(pb_ + np.array([sx * P["us_dx"], 0.0, 0.0]) + 2.0 * nnf)
            cliff.append(b)
        cliff = uni(cliff)
        _color(cliff, "sensor"); cliff.metadata["name"] = cnm
        parts.append(cliff)
    # amber indicator lamps at the fascia corners -- on the PROW CHEEK noses since
    # 2026-07-11 (the cheeks extend tub_nose past the wall; see PARAMS tub_nose)
    for sx, nm in ((-1, "lamp_L"), (1, "lamp_R")):
        l = rounded_box(12.0, 7.0, 2.0, 2.5)
        l.apply_transform(R(-TAU / 4, (1, 0, 0)))
        l.apply_translation((sx * P["lamp_x"], fw + P["tub_nose"], P["lamp_cz"]))
        _color(l, "lamp"); l.metadata["name"] = nm
        parts.append(l)
    # white LED dot strip at the bottom lip: slim base + 7 round emitters. Base 1.2 (was
    # 1.0, handling-fragile -- PRINTABILITY 6/7); the dots ride +0.2 with the base front
    # so their 1.2 proud height over it is unchanged.
    # white bar rides the GLACIS: tilt with the 33 deg face, proud 0.6 along its normal
    gy0, gz1 = P["glacis_y0"], P["glacis_z1"]
    ga = np.arctan2(gz1 - P["chassis_clear"], fw - gy0)
    gn = np.array([0.0, np.sin(ga), np.cos(ga)])     # outward glacis normal
    gface_y = gy0 + (P["fled_cz"] - P["chassis_clear"]) / np.tan(ga)
    # base 1.2 -> 2.0 (2026-07-15, FASTENING_AUDIT P2-5 "led_front 1.2 base"): the
    # strip is a hand-height glue-on trim part on the glacis nose; 1.2 of PLA behind
    # 7 emitters snaps in handling. The dots ride +0.8 with the base front so their
    # 1.2 proud height over it is unchanged.
    fl_bar = box(36.0, 2.0, 3.0)
    fl_bar.apply_transform(R(TAU / 4 - ga, (1, 0, 0)))   # y-face normal -> glacis normal
    fl_bar.apply_translation(np.array([0.0, gface_y, P["fled_cz"]]) + 1.0 * gn)
    fl = [fl_bar]
    for i in range(7):
        d = cyl(1.3, 1.6, axis="y", sections=24)
        d.apply_transform(R(TAU / 4 - ga, (1, 0, 0)))
        d.apply_translation(np.array([-15.0 + i * 5.0, gface_y, P["fled_cz"]]) + 2.4 * gn)
        fl.append(d)
    led = uni(fl)
    _color(led, "led"); led.metadata["name"] = "led_front"
    parts.append(led)
    # REAR (trim pass 2026-07-11): a TWIN of the front grille ring, framing the rear
    # obstacle HC-SR04 (user: "the rear has also two proximity sensors" -- obstacle +
    # cliff each end now). Replaces the squashed 72x18 hatch frame. Silver buzzer pod
    # stays at +47; the USB-C entry moved to x -38 so the barrels own the center.
    rp = sub(rounded_box(gw, gh, t, 6.0),
             rounded_box(gw - 2 * bd, gh - 2 * bd, t + 2, 4.0).apply_translation((0, 0, -1)))
    rp.apply_transform(R(TAU / 4, (1, 0, 0)))        # extrude -Y (proud of the REAR face)
    rp.apply_translation((0, -fw, P["grille_cz"]))
    # FIXING: glue + 3x Ø3 pins into blind rear-wall sockets (PARAMS rear_pin_pts)
    pr = [rp]
    for px, pz in P["rear_pin_pts"]:
        pr.append(fix_pin(P["fix_pin_r"], P["trim_pin_len"], (0, 1, 0), (px, -fw, pz)))
    rp = uni(pr)
    _color(rp, "accent"); rp.metadata["name"] = "trim_rear"
    parts.append(rp)
    # sensor_rear: the real part is a bought Ø12-14 buzzer/speaker INSIDE the wall; this
    # is its printed grille cap. FIXING: Ø17 x 1.5 base flange + 2x Ø2 pins into blind
    # wall sockets straddling the Ø10 sound/wire through-hole (cut in build_base).
    rcx, rcz = P["rear_cyl_x"], P["rear_cyl_cz"]
    fwn = fw + P["tub_nose"]                         # buzzer rides the rear cheek nose
    flange = cyl(P["rearpod_flange_r"], P["rearpod_flange_t"], axis="y", sections=48)
    flange.apply_translation((rcx, -fwn - P["rearpod_flange_t"] / 2, rcz))
    pod_l = 9.0 - P["rearpod_flange_t"]              # overall proud height stays 9.0
    pod = cyl(P["rear_cyl_d"] / 2, pod_l, axis="y", sections=48)
    pod.apply_translation((rcx, -fwn - P["rearpod_flange_t"] - pod_l / 2, rcz))
    rcp = [flange, pod]
    for sxp in (-1, 1):
        rcp.append(fix_pin(P["fix_pin2_r"], P["fix_pin_len"], (0, 1, 0),
                           (rcx + sxp * P["rearpod_pin_dx"], -fwn, rcz)))
    rc = uni(rcp)
    _color(rc, "sensor"); rc.metadata["name"] = "sensor_rear"
    parts.append(rc)
    return parts


def _ped_c():
    """Pan-motor CAN center (the pedestal center), derived from the fast-pan gear
    geometry exactly like build_chassis_core derives it -- one source, no drift:
    shaft on the CD circle at pan_shaft_azim, can offset motor_shaft_off in +Y."""
    cd_pan = P["pan_gear_m"] * (P["pan_gear_motor_t"] + P["pan_gear_pinion_t"]) / 2
    paz = np.radians(P["pan_shaft_azim"])
    return cd_pan * np.cos(paz), cd_pan * np.sin(paz) + P["motor_shaft_off"]


def _belly_polys():
    """(opening, rebate) shapely polys for the belly access plate (task #26).
    Opening = the full rounded 100x110 (the KEEP STRAP was deleted 2026-07-14
    round 5: the pan pedestal + inboard ULN posts it rooted moved onto the plate
    itself, so the plate is now the full equipment tray); rebate = one bigger
    rounded rect, cut 1.5 up from the belly face everywhere inside it."""
    w, l = P["belly_open_wl"]; cx, cy = P["belly_open_c"]
    op = sg.box(cx - w / 2, cy - l / 2, cx + w / 2, cy + l / 2)
    op = op.buffer(-8, join_style=1).buffer(8, join_style=1)
    g = P["belly_rebate_grow"]
    reb = sg.box(cx - w / 2 - g, cy - l / 2 - g, cx + w / 2 + g, cy + l / 2 + g)
    reb = reb.buffer(-10, join_style=1).buffer(10, join_style=1)
    return op, reb


def _belly_csk_neg(bx, by):
    """Shared csk negative for one belly screw: M3 flat-head cone (Ø6.7 -> Ø3.4, head
    finishes flush at the z=7 belly face) + Ø3.5 clearance reaching z=9.2. Subtracted
    from BOTH the plate and the chassis ledge (the cone's last 0.15 crosses the z=8.5
    rebate ceiling; without the shared cut the head would stand the plate off)."""
    cone = frustum(3.35, 1.7, 1.65)
    cone.apply_translation((0, 0, P["chassis_clear"] - 0.05))     # z 6.95..8.6
    clr = cyl(1.75, 3.2); clr.apply_translation((0, 0, 7.6))      # z 6.0..9.2
    neg = uni([cone, clr])
    neg.apply_translation((bx, by, 0))
    return neg


def build_chassis_core():
    """Tank chassis BODY: hollow rounded box between the tracks. Top = pan-mount plane; houses
    the pan motor + driver + wiring. (Track pods are build_tracks.)"""
    wall, floor = 5.0, 5.0
    z0, z1 = P["chassis_clear"], P["base_h"]          # body spans clearance..pan-mount
    h = z1 - z0
    plate_bot, ring_top, seat_floor, zball = _pan_stack()
    # TOY-TANK HULL (2026-07-10, user round 2): lower tub (chassis_l long) + a deck
    # slab overrunning it by deck_overhang at each end; the end faces slope from the
    # wall top (|y| chassis_l/2, z split) to the deck top edge at atan(20/30) = 33.7
    # deg from horizontal (print-safe; same ~33 family as the track ramps + glacis).
    # The slope wedges cut the SLAB ONLY -- cutting the union would shave the tub
    # wall tops (the plane extended crosses them below the seam).
    seam_ = P["chassis_split_z"]
    ovh = P["deck_overhang"]
    lower_ = rounded_box(P["chassis_w"], P["chassis_l"], seam_ - z0, 14.0)
    lower_.apply_translation((0, 0, z0))
    # slab tips TRUNCATED by deck_tip_trunc: the raw slope/top intersection was a
    # 33.7 deg acute PLA knife edge ("angle too sharp", 2026-07-11) -- ending the slab
    # early leaves a vertical 4-tall nose face where the slope plane exits at z 62
    slab = rounded_box(P["chassis_w"], P["chassis_l"] + 2 * (ovh - P["deck_tip_trunc"]),
                       z1 - seam_, 14.0)
    slab.apply_translation((0, 0, seam_))
    sa = np.arctan2(z1 - seam_, ovh)
    for sgn in (1, -1):
        wg = box(P["chassis_w"] + 20, 80.0, 60.0)
        wg.apply_transform(R(sgn * sa, (1, 0, 0)))
        nn_ = np.array([0.0, sgn * np.sin(sa), -np.cos(sa)])   # outward slope normal
        c_ = (np.array([0.0, sgn * P["chassis_l"] / 2, seam_])
              + 25.0 * np.array([0.0, sgn * np.cos(sa), np.sin(sa)]) + 30.0 * nn_)
        wg.apply_translation(c_)
        slab = sub(slab, wg)
    body = uni([lower_, slab])
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
    # PAN HARD STOPS (homing pass 2026-07-08): two posts rise from the seat floor at r28,
    # azimuth 118 and 332 deg, meeting the platform's underside lug (azimuth 225, see
    # build_pan_platform). Posts and lug are RADIALLY ALIGNED (rotated about the pan axis,
    # review fix: the first cut left them axis-aligned, whose corners met at +-91.6 while
    # the docs promised +-93.3 -- the shapely sim had rotated boxes, the code didn't).
    # Contact at pan +-93.3: firmware stall-homes at boot, backs off, calls it +-90; the
    # +-90 sweep poses keep a 3.3 deg gap. Posts stay inside the race-ring ID (corner
    # r 32.2 < 34), clear of both Ø30 membrane cbores and the deck cable pass. Top at
    # 58.2 leaves 0.2 running air under the plate bottom (58.4).
    for az in (118.0, 332.0):
        post = box(6.0, 6.0, 7.2)
        post.apply_translation((28.0, 0, seat_floor + 3.6))
        post.apply_transform(R(az * DEG, (0, 0, 1)))
        body = uni([body, post])
    # FAST-PAN gear-up (2026-07-12; PARAMS pan_gear_*): shaft/can positions are now derived
    # -- the 32T motor gear at the shaft drives the platform's integral 16T pinion, both in
    # the pan_gear_z band (45..50) UNDER the seat floor (51).
    m_g = P["pan_gear_m"]
    cd_pan = m_g * (P["pan_gear_motor_t"] + P["pan_gear_pinion_t"]) / 2    # 19.2
    paz = np.radians(P["pan_shaft_azim"])
    sxp, syp = cd_pan * np.cos(paz), cd_pan * np.sin(paz)                  # shaft (-19.2, 0)
    mx, my = sxp, syp + P["motor_shaft_off"]         # CAN axis (-19.2, 7.875): offset -> +Y
    # clearance through the deck membrane under the seat: Ø30 at the pan axis (pinion hub)
    # + a GEAR POCKET at the shaft (32T tip r 13.8 + 0.7 running, z through the 46..51
    # under-seat membrane). Max reach 19.2 + 14.5 = 33.7 < ring ID 34 -> the ring's seat
    # floor annulus (35.5..44.5) stays fully supported; the swinging stop lug bottoms at
    # 51.6, 1.6 over the gear band.
    for cx_, cy_, r_ in ((0.0, 0.0, 15.0), (sxp, syp, 14.5)):
        cbore = cyl(r_, 30.0); cbore.apply_translation((cx_, cy_, seat_floor - 2))
        body = sub(body, cbore)
    # cable pass through the deck: 16x8 obround (5-pos JST-XH head is 14.9 x 5.9) at
    # cable_exit, INSIDE the race ID -- the old Ø12 pass at (0, neck_y) punched through the
    # race-ring footprint (r 34..46), where the fixed ring blocks it anyway. Aligned with the
    # platform slot's exit at pan=0; the service loop below takes the pan winding.
    ex, ey = P["cable_exit"]
    u = np.array([ex - 0.0, ey - P["neck_chan_y"]]); u = u / np.linalg.norm(u)
    # 24 tall from z 29 (extrude_polygon is z=0..h, so seat_floor-22 puts the FLOOR at 29;
    # the old 22-at-seat_floor-11 spanned 40..62, wasting 51..62 in the seat void while
    # stopping 11 short of a full pedestal-corner bore): 29 is safely below the service-
    # loop band (z 37..45.5) and the top at 53 overlaps 2 into the seat void (no coplanar
    # boolean face at the seat floor).
    cbl = extrude_polygon(sg.LineString([(ex - 4 * u[0], ey - 4 * u[1]),
                                         (ex + 4 * u[0], ey + 4 * u[1])]).buffer(4.0), 24.0)
    cbl.apply_translation((0, 0, seat_floor - 22))
    # (cbl is SUBTRACTED after the pedestal union below: subtracting here let the pedestal
    # refill the pass below z 44.25 to a 4.0 mm window -- CABLE-CHECK defect A.)

    # (pan-motor PEDESTAL + BOTH ULN2003 standoff sets MOVED OFF THE HULL
    # 2026-07-14 round 5, user: "I want it separate and connected with bolt and
    # nuts to the belly plate... bigger belly plate that contains many parts".
    # The pedestal is now the bolt-on `build_pan_pedestal()` (chassis_pedestal)
    # riding the ENLARGED belly plate; the ULN posts moved onto the plate too
    # (build_belly_plate). The _belly_polys keep strap is gone, so the floor
    # here is just the opening rim -- drop the plate = drop the whole power +
    # driver + pan-motor stage as one service tray.)
    body = sub(body, cbl)

    # pan-clip pockets: 3 at 120deg around the seat rim, floors 7 below the deck top so the
    # clips finish FLUSH (see build_pan_clips for why nothing may stand proud of the deck).
    #
    # M3 THROUGH-BOLT + CAPTIVE HEX NUT (2026-07-15, FASTENING_AUDIT P1). These three
    # screws were Ø2.5 thread-form pilots, and they are the ONLY thing resisting the
    # top-heavy head lifting the pan platform off its balls -- the single worst
    # self-tap in the chassis. The nut sits at pan_clip_nut_z, its slot running
    # RADIALLY INWARD to a mouth in the seat wall (r 49): that is the only open face
    # anywhere near this station, and it is a good one -- the annulus r 44.5..49 /
    # z 51..56 outside the race ring is free air, so the nuts slide in with tweezers
    # through the Ø98 seat opening. ORDER: nuts in BEFORE the race ring + balls.
    # Uplift pulls each nut UP onto its slot roof, so the 3.6 mm of deck between the
    # nut top and the pocket floor works in pure COMPRESSION against the clip's seat.
    # Screw stays M3x10: build_pan_clips' head cbore puts the head bottom at z 62.6,
    # so the tip lands at 52.6 = the nut's bottom face. pan.py needs no change.
    for a in (90, 210, 330):
        # pocket inner edge at r48 -- INSIDE the round seat wall (circle is at y 48.5 when
        # x = +-7), else slivers of deck survive between the straight edge and the circle
        # exactly where the clip tab corners land
        pk = box(14.4, 10.2, 8.0); pk.apply_translation((0, 53.1, z1 - 3.0))    # z 59..67
        pk.apply_transform(R((a - 90) * DEG, (0, 0, 1)))
        body = sub(body, pk)
        thr = cyl(P["m3_clear_r"], 8.0)                                         # z 51.5..59.5
        thr.apply_translation((0, 53.5, z1 - 10.5))
        thr.apply_transform(R((a - 90) * DEG, (0, 0, 1)))
        body = sub(body, thr)
        nsl = geo.nut_slot((0, 53.5, P["pan_clip_nut_z"]), screw_axis="z",
                           open_dir=(0, -1, 0), size="M3",
                           length=P["pan_clip_nut_run"])
        # SEAT RELIEF (2026-07-15): geo.nut_slot() backstops at EXACTLY ac/2 behind the
        # axis, so only a max-material nut (ac 6.35) reaches the bore dead-centre -- a
        # real DIN 934 M3 runs 6.14..6.35 across corners, i.e. up to 0.21 short. Back
        # the seat off pan_clip_nut_seat_clear: the nut self-centres on the screw as it
        # draws in, so the seat only has to stop it near enough to be hands-free. This
        # also clears the checks.nut_reaches_bore probe, whose axis-aligned 0.5 cube
        # over-reaches a ROTATED seat plane by up to 0.104 (az 210/330 here).
        # NOTE for a central fix: this belongs in geo.nut_slot() as a `seat_clear` arg.
        sc = P["pan_clip_nut_seat_clear"]
        rel = box(geo.NUT["M3"][0] + 0.2, sc, geo.NUT["M3"][1] + 0.2)
        rel.apply_translation((0, 53.5 + M3_AC / 2 + sc / 2, P["pan_clip_nut_z"]))
        nsl = uni([nsl, rel])
        nsl.apply_transform(R((a - 90) * DEG, (0, 0, 1)))
        body = sub(body, nsl)
    usb = box(14, 12, 8)                              # USB-C power entry in the rear wall
    # moved x 0 -> -38 (2026-07-11): the rear obstacle HC-SR04 + its twin ring own the
    # wall center now; -38 keeps the slot 1.0 off the ring band (ends -30), below the
    # deck-split boss zone (z 37+ at x -38..-30), and right above the belly power tray
    usb.apply_translation((-38.0, -P["chassis_l"] / 2, z0 + 24)); body = sub(body, usb)
    # PD-trigger mount (wiring pass 2026-07-08): 2x Ø1.7 M2 self-tap pilots in the rear
    # wall's interior face flanking the USB slot -- the trigger/breakout board hangs on
    # the wall with its jack aligned to the slot. Plus 2x Ø3.2 zip anchors through the
    # floor rim behind the belly opening: the incoming wall cable zip-ties down before
    # the jack, so a yanked cable loads the tie, not the board (the robot WILL drag its
    # own tether eventually).
    for sxp in (-1, 1):
        pd = cyl(0.85, 4.0, axis="y")
        pd.apply_translation((-38.0 + sxp * 9.0, -P["chassis_l"] / 2 + 5 - 1.9, z0 + 24))
        body = sub(body, pd)
    for sxp in (-1, 1):
        zh = cyl(1.6, 7.0)
        zh.apply_translation((sxp * 6.0, -68.0, z0 + 2.5))
        body = sub(body, zh)
    # BALLAST BAY retaining ribs (see the PARAMS note): the REAR rib (y=-63) stays on
    # the chassis -- it lands on the 12-wide floor rim behind the belly opening (edge
    # y=-61). The two inboard ribs (-51.5, -40) root on floor that is now the belly
    # OPENING, so they moved onto the belly plate (build_belly_plate); pocket walls +
    # USB corridor are unchanged. Mass sits low + rearward against the head/Pi CoM.
    rib_l = P["blst_rib_xmax"] - P["blst_usb_hw"]     # 30 per half-rib
    for ry in P["blst_rib_y"][:1]:
        for sx in (-1, 1):
            rib = box(rib_l, P["blst_rib_w"], P["blst_rib_h"])
            rib.apply_translation((sx * (P["blst_usb_hw"] + rib_l / 2), ry,
                                   z0 + floor + P["blst_rib_h"] / 2))
            body = uni([body, rib])
    # front-fascia cuts (design ref; re-homed 2026-07-10 toy-tank hull): the hex vent
    # field moved off the shortened vertical wall onto the FRONT SLOPE, in two lateral
    # bands (|x| 26..52) flanking the cliff-sensor barrels; blind 2.5 along the slope
    # normal into the solid overhang wedge. Ø16.6 ultrasonic barrel passes stay in the
    # vertical wall (now inside the relocated grille ring's opening).
    fw = P["chassis_l"] / 2
    sa_ = np.arctan2(P["base_h"] - P["chassis_split_z"], P["deck_overhang"])
    sn_ = np.array([0.0, np.cos(sa_), np.sin(sa_)])    # up-slope unit
    nnf = np.array([0.0, np.sin(sa_), -np.cos(sa_)])   # outward slope normal
    se0 = np.array([0.0, fw, P["chassis_split_z"]])    # slope bottom edge, front
    hexes = []
    for r_i, vr in enumerate((6.0, 10.0, 14.0)):
        off = 2.1 if r_i % 2 else 0.0
        for k in range(-13, 14):
            hx_x = k * 4.2 + off
            if not (26.0 <= abs(hx_x) <= 52.0):
                continue
            hx = hex_prism(3.0, 4.0)
            # FLAT-top hexes in the slope frame (the old wall-field printability note
            # carries over: flats give a 1.2 web + self-supporting pocket roofs)
            hx.apply_transform(R(TAU / 12, (0, 0, 1)))
            hx.apply_transform(R(np.pi + sa_, (1, 0, 0)))      # axis Z -> slope normal
            hx.apply_translation(se0 + vr * sn_ - 0.5 * nnf + np.array([hx_x, 0.0, 0.0]))
            hexes.append(hx)
    body = sub(body, uni(hexes))
    for sx in (-1, 1):
        us = cyl(P["us_d"] / 2 + 0.3, 12, axis="y")
        us.apply_translation((sx * P["us_dx"], fw - 2.5, P["us_cz"]))
        body = sub(body, us)
        usr = cyl(P["us_d"] / 2 + 0.3, 12, axis="y")  # rear obstacle HC-SR04 barrel
        usr.apply_translation((sx * P["us_dx"], -(fw - 2.5), P["us_cz"]))
        body = sub(body, usr)                         # passes (2026-07-11, twin ring)
    # OBSTACLE HC-SR04 RETENTION (2026-07-15, FASTENING_AUDIT P0-5): both obstacle
    # boards were UNRETAINED -- they just floated against the wall's inner face on
    # their own barrels, held by gravity and the wire loom. The board has to go in
    # along +-Y (the barrels thread into the wall bores), so a slide-down channel is
    # impossible; instead each wall gets
    #   - a SHELF ledge under the board: it carries the weight, sets z, and its
    #     0.1 air keeps the placeholder gate-clean, and
    #   - two SIDE RIBS backing the board's x edges (lateral location), and
    #   - 2x Ø1.7 M2 pilots on the board's own TOP corner holes (the 41 x 16.7
    #     HC-SR04 pattern, same as the cliff pair), straight into the 5-wall.
    # No standoff posts: the board clamps FLAT to the inner face, exactly where the
    # barrels want it, so the M2s only clamp -- shelf + ribs + barrels take the load
    # and there is no strip path (this is the audit's "2 M2 posts or a slide-in
    # board shelf clip", built as both minus the standoff).
    ubw, ubh = P["us_board_wl"]
    for sgn in (1, -1):
        wy = sgn * (fw - 5.0)                         # wall inner face (|y| 115)
        zsh = P["us_cz"] - ubh / 2 - 0.1              # shelf top: 0.1 under the board
        shf = box(ubw + 6.0, P["us_seat_d"], P["us_shelf_t"])
        shf.apply_translation((0.0, wy - sgn * P["us_seat_d"] / 2,
                               zsh - P["us_shelf_t"] / 2))
        body = uni([body, shf])
        for sxb in (-1, 1):
            rib = box(2.4, P["us_seat_d"], ubh)       # side rib: 0.15 off the board
            rib.apply_translation((sxb * (ubw / 2 + 0.15 + 1.2),
                                   wy - sgn * P["us_seat_d"] / 2, P["us_cz"]))
            body = uni([body, rib])
            bp = cyl(0.85, 4.5, axis="y")             # M2 pilot, 4.0 into the 5-wall
            bp.apply_translation((sxb * P["us_hole_cc"][0] / 2,
                                  wy + sgn * (4.5 / 2 - 4.0),
                                  P["us_cz"] + P["us_hole_cc"][1] / 2))
            body = sub(body, bp)
    # SIDE VENT ROW DELETED (2026-07-14, user: "remove the cosmetic holes on the
    # chassis sides") -- only the y -96 slot survives: it is FUNCTIONAL, the
    # BME688's air window (its bosses flank it; sensor placement keys off it).
    # (-112 died in the fittings audit; 16/32/48/64/96 were the cosmetic row.)
    for vy in (-96.0,):
        # side ventilation slots, RE-CLOCKED 2026-07-11 (mid-drive): the TT feature
        # zone moved to y ~ -87..-15 (motor at spr_y -68), so the old row shifted
        # out of it into the now feature-free bands of the 240 tub
        v = box(12, 5, 16); v.apply_translation((0, vy, 36.0))   # FIXED z 28..44:
        # z0+h/2 crossed the 46 deck seam once chassis_clear rose to 10 (v2)
        v2 = v.copy(); v.apply_translation((P["chassis_w"] / 2, 0, 0))
        v2.apply_translation((-P["chassis_w"] / 2, 0, 0))
        body = sub(sub(body, v), v2)

    # --- TT drive-motor mount (both walls; see motor_tt + reference/tt-motor-1079893/NOTES.md).
    # Shaft axis at (y=-wb/2, z=_track_zc()+track_raise): the raised tank loop lifts the
    # sprocket (and so the motor) by track_raise; gearbox face 0.1 inside the wall inner face.
    # MID-DRIVE (2026-07-11, tracks past the deck tips): the sprocket sits ON the
    # ground run at spr_y, center z = the pin line + pin circle = _track_zc() = 25.32;
    # the TT rides its shaft there directly (dropped ~9 and moved to the vent-free
    # band -- the side vents were re-clocked around the new motor zone).
    # TWO STATIONS per side (2026-07-11, user: "two motors on each side, second
    # optional but all fittings ready"): the rear station (spr_y, orientation +1) and
    # a mirrored FRONT station (spr_y2, orientation -1: the TT flips about its shaft,
    # so every y-offset changes sign -- gearbox trails -y, tab/rib sit forward).
    zs = _spr_cz()                                    # 28.47: 14T mid-drive
    xw = P["chassis_w"] / 2                           # wall outer face (70); inner face 65
    axm = xw - 5.0 - P["tt_gearbox"][2] / 2 - 0.1     # motor axis x
    for ys, o in ((P["spr_y"], 1.0), (P["spr_y2"], -1.0)):
      for s in (-1, 1):
        ph = cyl(4.0, 12, axis="x"); ph.apply_translation((s * (xw - 2.5), ys, zs))
        body = sub(body, ph)                          # Ø8 shaft pass-through (clears Ø7.2 boss)
        rec = teardrop(8.5, 2.2, axis="x")     # 45deg-capped: prints support-
        rec.apply_translation((s * (xw - 0.9), ys, zs))        # free upright
        body = sub(body, rec)                         # outer recess -> 3 mm web, hub sits close
        for dz in (-8.75, 8.75):                      # M3 through gearbox + wall, nut in the gap
            mh = cyl(1.6, 12, axis="x"); mh.apply_translation((s * (xw - 2.5), ys + o * 20.3, zs + dz))
            body = sub(body, mh)
        nubp = cyl(2.1, 2.3, axis="x"); nubp.apply_translation((s * (xw - 5.0 + 1.1), ys + o * 11.0, zs))
        body = sub(body, nubp)                        # Ø4.2 x 2.2 locating-nub pocket, inner face
        # pocket over the motor: gearbox/can top 36.5 at zs 25.32 -- cut to 45.8, still
        # under the z46 deck seam (pan-seat floor + race ring footprint stay clear)
        dkp = box(19.4, 64.7, 13.9); dkp.apply_translation((s * (xw - 14.5), ys + o * 20.35, 38.85))
        body = sub(body, dkp)
        # cavity-corner relief for the rectangular gearbox corner
        crn = box(7.0, 14.2, 33.9); crn.apply_translation((s * (xw - 8.4), ys - o * 5.1, 28.85))
        body = sub(body, crn)
        # TT tab RIB: floor-to-z40, bridged to the side wall; the tab pocket + hole
        # cuts land in it (0.3 shy of the gearbox face plane)
        rib = box(69.1 - (axm - 4.0), 6.9, 25.0)
        rib.apply_translation((s * ((axm - 4.0 + 69.1) / 2), ys - o * 15.1, 27.5))
        # (rib z 15..40: roots on the raised floor top, TOP HELD at 40 -- the deck
        # corner material starts at 42; tab pocket keyed to zs 28.47 sits inside)
        body = uni([body, rib])
        tabp = box(4.2, 5.7, 6.4); tabp.apply_translation((s * axm, ys - o * 14.15, zs))
        body = sub(body, tabp)                        # front-tab pocket in the rib (1+ skin)
        tabh = cyl(1.4, 14, axis="x"); tabh.apply_translation((s * axm, ys - o * 14.0, zs))
        body = sub(body, tabh)                        # Ø2.8 tab-hole continuation (M2.5 self-tap)
        # (the old wall-mounted idler tension arm/plate/slot was DELETED 2026-07-11:
        # both loop ends now ride Ø8 stubs in DECK-OVERHANG PYLONS -- see
        # build_chassis_parts -- and the front pylons carry the tension slots)
    # (The BODY<->POD JOIN M3/dowel wall fittings were DELETED 2026-07-14 round 3
    # with pod_rail_L/R: the side panels now grow the wheel beam directly -- see
    # the SIDE PANELS block in build_chassis_parts -- so there is no separate rail
    # to join and no through-wall hardware.)
    # --- COSMETIC-FIXING sockets + wire passes in the chassis walls (task #15) ---
    # trim_fascia: 4x Ø3.2 x 2.5 blind sockets in the front wall (at z 50 the solid deck
    # is behind; at z 42 the 2.5 skin faces the cavity)
    for px, pz in P["fascia_pin_pts"]:
        body = sub(body, blind_socket(P["fix_socket_r"], P["trim_socket_deep"],
                                      (0, 1, 0), (px, fw, pz)))
    # trim_rear: 3x Ø3.2 x 2.5 blind sockets in the rear wall
    for px, pz in P["rear_pin_pts"]:
        body = sub(body, blind_socket(P["fix_socket_r"], P["trim_socket_deep"],
                                      (0, -1, 0), (px, -fw, pz)))
    # lamp_L/R wire passes + sensor_rear bore/sockets moved AFTER the prow-cheek
    # union below (2026-07-11) -- cut here they'd be refilled by the cheeks.
    # led_front: the strip (z 8..11) sits against the FLOOR band (z 7..12), so a straight
    # wire pass would dead-end in the floor slab -- angle it up-inward from behind the
    # strip base into the cavity (axis (10, 79, 9) -> (10, 70, 14.5); exit z 12.7+ at the
    # inner face y 73, staying 0.65+ under the HC-SR04 board bottom at z 15.55)
    gy0w, gz1w = P["glacis_y0"], P["glacis_z1"]
    gaw = np.arctan2(gz1w - z0, fw - gy0w)
    gnw = np.array([0.0, np.sin(gaw), np.cos(gaw)])
    wf = cyl(P["wire_pass_r"], 10.0)                 # strip rides the glacis: pass drills
    _orient(wf, tuple(-gnw))                         # along the inward face normal into
    gfy = gy0w + (P["fled_cz"] - z0) / np.tan(gaw)   # the cavity right behind it
    wf.apply_translation(np.array([10.0, gfy, P["fled_cz"]]) - 3.0 * gnw)
    body = sub(body, wf)
    # --- END-WALL GUSSET RIBS (2026-07-15, FASTENING_AUDIT P2-1 "the tail + front
    # counterpart break at thin-ligament connections"): past |y| ~109 the glacis has
    # eaten the floor slab, so the r12 cavity-corner crescents were the ONLY
    # floor<->end-wall ligaments and both end walls hung off them. Each end gets two
    # inboard ribs from the wall inner face onto solid floor -- a direct tie that does
    # not depend on the corner rounds. Unioned BEFORE the glacis cut, so the wall-end
    # foot is trimmed to the 33 deg face automatically (and stays inside the shell).
    # Vertical fins on the floor: zero overhang in the tub's floor-down print.
    gt, gz, grun = P["end_gusset_t"], P["end_gusset_z"], P["end_gusset_run"]
    for sgn, gx in ((1, P["end_gusset_x"][0]), (-1, P["end_gusset_x"][1])):
        wall_in = sgn * (P["chassis_l"] / 2 - 5.0)        # inner face of the end wall
        for sxg in (-1, 1):
            g = box(gt, grun, gz - (z0 + floor))
            g.apply_translation((sxg * gx, wall_in - sgn * grun / 2,
                                 (z0 + floor + gz) / 2))
            body = uni([body, g])

    # --- GLACIS (2026-07-10, see PARAMS): slice the hull's front/rear lower corners
    # at the track-ramp angle so the side profile follows the tracks. The cut plane
    # runs (|y| glacis_y0, z 7) -> (wall, glacis_z1); a rotated box under that plane
    # removes the wedge. Wall features were re-homed above glacis_z1 (PARAMS note).
    gy0, gz1 = P["glacis_y0"], P["glacis_z1"]
    z0g = P["chassis_clear"]
    ga = np.arctan2(gz1 - z0g, P["chassis_l"] / 2 - gy0)     # 33 deg for 200/18
    for sgn in (1, -1):
        wedge = box(170.0, 100.0, 60.0)
        wedge.apply_transform(R(sgn * ga, (1, 0, 0)))
        n_ = np.array([0.0, -sgn * np.sin(ga), np.cos(ga)])  # cut-plane normal (up-ish)
        c_ = np.array([0.0, sgn * gy0, z0g]) - 30.0 * n_     # top face ON the plane
        wedge.apply_translation(c_)
        body = sub(body, wedge)
    # BLUNT THE GLACIS/FLOOR KNIFE (2026-07-15, FASTENING_AUDIT P2-1 "the 33 deg
    # glacis/floor knife wedge on the tail chips in handling"; it is also the
    # chassis_lower_tail wallcheck whitelist entry). The glacis plane leaves the floor
    # top (z0+floor) at |y| = yk, and between the glacis_tip_t station and yk the slab
    # feathers from glacis_tip_t to ZERO. Cut that feather off at both ends so the slab
    # ends on a vertical face >= glacis_tip_t tall instead of a knife edge.
    ftop = z0g + floor                                   # floor top (15)
    yk_t = gy0 + ((ftop - P["glacis_tip_t"]) - z0g) / np.tan(ga)    # slab == tip_t here
    for sgn in (1, -1):
        nib = box(200.0, 60.0, 20.0)                     # full width: the glacis cut is
        nib.apply_translation((0.0, sgn * (yk_t + 30.0), ftop - 10.0))   # full width too
        body = sub(body, nib)                            # z ftop-20..ftop, |y| >= yk_t

    # (PROW CHEEKS + M8 NUT DUCTS/CHANNELS DELETED 2026-07-14 running-gear v2 +
    # end simplification, user: the tail/front ends got "way more complex than
    # they should". The end axles live on the panel END TOWERS since round 4;
    # the M8 nuts now ride LEDGE+ROOF CAGES on the towers' inboard faces (see
    # build_chassis_parts), which also lets a bare track module tension without
    # any hull. The raised axle line (za 38.32) had broken the old duct's roof
    # against the z 46 seam anyway. The hull ends are plain glacis walls at
    # y +-120 now; tub_nose is 0 and the wall features below re-key to fw.)
    # wall cuts (ex-cheek features, re-keyed to the plain end walls):
    fwn = fw + P["tub_nose"]                         # = fw (tub_nose 0, v2)
    # lamp_L/R: Ø2.5 wire pass from the cheek nose (z 23 runs UNDER the pocket floor
    # z 25) through the old wall into the cavity
    for s in (-1, 1):
        wl = cyl(P["wire_pass_r"], 34.0, axis="y")
        wl.apply_translation((s * P["lamp_x"], fwn - 15.0, P["lamp_cz"]))
        body = sub(body, wl)
    # USB-C corridor: the wall slot cut earlier got buried by the rear-left cheek;
    # re-cut the full recessed corridor through cheek + wall (same 14x8 section)
    usb2 = box(14, 40, 8)
    usb2.apply_translation((-38.0, -(fwn - 18.0), z0 + 24))
    body = sub(body, usb2)
    # sensor_rear: Ø10 sound/wire bore through cheek + wall + 2x blind cap-pin
    # sockets in the cheek nose (the +dx socket lands in the pocket's 3.0 front
    # skin: 2.5 deep leaves a 0.5 web)
    sh_ = cyl(P["rearpod_hole_r"], 32.0, axis="y")
    sh_.apply_translation((P["rear_cyl_x"], -(fwn - 15.0), P["rear_cyl_cz"]))
    body = sub(body, sh_)
    for sxp in (-1, 1):
        body = sub(body, blind_socket(P["fix_socket2_r"], P["fix_socket_deep"], (0, -1, 0),
                                      (P["rear_cyl_x"] + sxp * P["rearpod_pin_dx"], -fwn,
                                       P["rear_cyl_cz"])))

    # --- BELLY ACCESS PLATE opening (task #26; the plate itself is build_belly_plate).
    # Cut LAST so no later union refills it. Opening through the 5-floor (z 7..12) +
    # a 1.5-deep rebate off the belly face; 6x Ø7 self-tap bosses on the rim/strap
    # with Ø2.5 pilots (blind: stop 0.5 under the boss top), csk negatives shared
    # with the plate so the M3 flat heads finish flush at z=7 (ground clearance 7).
    op_poly, reb_poly = _belly_polys()
    op_cut = extrude_polygon(op_poly, 9.0)
    op_cut.apply_translation((0, 0, z0 - 3.0))               # z0-3..z0+6, through the floor
    # (was a hardcoded 4..13 -- it silently stopped piercing when chassis_clear
    # rose to 10 in v2 and left a 2-thick skin sealing the belly opening)
    body = sub(body, op_cut)
    reb_cut = extrude_polygon(reb_poly, P["belly_lip_t"] + 2.0)
    reb_cut.apply_translation((0, 0, z0 + P["belly_lip_t"] - (P["belly_lip_t"] + 2.0)))
    body = sub(body, reb_cut)                                # z 4.5..8.5
    # 2026-07-15 (FASTENING_AUDIT P1, the TODO the previous pass left): the 6 rim
    # screws were Ø2.5 thread-form pilots -- the failing class. They are now M3
    # THROUGH-BOLTS into CAPTIVE HEX NUTS, and the 1.5 rebate lip stays the locator
    # (the plate drops into it and self-holds while the 6 csk screws go in).
    # Insertion order: nuts into the bosses with the deck off (they are free-standing
    # posts in the open tub, every flank is a mouth), then the base, then the plate.
    # Ø9 CLIPPED TO THE RIM: at the Ø7 radius every boss cleared the opening edge, but
    # Ø9 crosses it at 3 of the 6 stations -- and the opening cut runs to z 16, so the
    # crescent past the edge would hang in AIR over the void, feathering to nothing at
    # its tips. Clip each boss on the opening outline: the chord face lands COPLANAR
    # with the rim's own edge face (z 11.5..15), i.e. continuous material, no overhang.
    rim_clip = extrude_polygon(op_poly, 10.0)
    rim_clip.apply_translation((0, 0, z0 + floor - 1.0))         # z 14..24
    for bx_, by_ in P["belly_screws"]:
        b = cyl(P["belly_boss_r"], P["belly_boss_h"])
        b.apply_translation((bx_, by_, z0 + floor + P["belly_boss_h"] / 2))   # z 15..21
        body = uni([body, sub(b, rim_clip)])
        body = sub(body, _belly_csk_neg(bx_, by_))
        # M3 CLEARANCE all the way up (the old Ø2.5 pilot also left 0.6 of un-drilled
        # solid between the csk cone's small end and its own start -- the screw had to
        # cut that too).
        thr = cyl(P["m3_clear_r"], 10.0)
        thr.apply_translation((bx_, by_, z0 + floor - 3.5 + 10.0 / 2))   # z 11.5..21.5
        body = sub(body, thr)
        # nut slot opens toward the belly OPENING (i.e. the tub interior): +y for the
        # rear pair, -y for the front pair, inboard-x for the flank pair. Every one of
        # those mouths faces open cavity air at the nut band (z 15.6..18.4).
        odir = ((-np.sign(bx_), 0.0, 0.0) if abs(bx_) > 50.0
                else (0.0, -np.sign(by_), 0.0))
        body = sub(body, geo.nut_slot((bx_, by_, P["belly_nut_z"]), screw_axis="z",
                                      open_dir=odir, size="M3",
                                      length=P["belly_nut_run"]))
    # (REAR TIE deleted 2026-07-14 round 5: it re-anchored the belly-strap pedestal
    # island, and both the strap and the pedestal left the hull -- the floor is a
    # plain opening rim now.)

    # --- ELECTRONICS SEATS (2026-07-13, Arduino I/O plane; see the PARAMS block
    # for every placement derivation + VERIFY_ON_ARRIVAL markers). Added AFTER the
    # belly cut on purpose.
    # ARDUINO + IMU + SW-420 seats MOVED to the removable chassis_base (2026-07-14,
    # user: split the shell so the in-flux electronics iterate on a swappable base,
    # not the finalized hull). The hull keeps the base's 4 hold-down stations + 2
    # locating pins. BME stays here (its bosses are air-coupled to the left wall vent,
    # shell-integral like the sonars).
    #
    # 2026-07-15 (FASTENING_AUDIT P1 + a defect the audit MISSED): these were 4 blind
    # Ø2.5 thread-form pilots -- and probing the built hull showed ALL FOUR were dead.
    # Two sat where the glacis has eaten the floor entirely (no material at any z: the
    # sub() was a no-op and the screws threaded air); the other two sat in the belly
    # rebate on 3.5 mm of floor with their bores tangent to the belly bosses'. The
    # stations moved into the valid band (see PARAMS base_mount_pts) and every one is
    # now an M3 THROUGH-BOLT into a CAPTIVE HEX NUT recessed at the belly face.
    for tmx, tmy in P["base_mount_pts"]:
        thr = cyl(P["m3_clear_r"], (z0 + floor) - P["base_nut_ztop"] + 2.0)
        thr.apply_translation((tmx, tmy, (P["base_nut_ztop"] + z0 + floor + 2.0) / 2))
        body = sub(body, thr)                        # bore: nut ceiling -> floor top
        # hex recess opening DOWN at the belly face -- a first-layer pocket in the
        # floor-down tub print, and the nut's flats take the driving torque.
        rec = hex_prism(geo.NUT["M3"][0] + 0.2, (P["base_nut_ztop"] - z0) + 0.2)
        rec.apply_translation((tmx, tmy, (z0 - 0.2 + P["base_nut_ztop"]) / 2))
        body = sub(body, rec)
    # 2 printed Ø4 locating pins (chassis_pedestal pattern): the base drops over them
    # and self-holds square while the 4 screws go in. The base's own Ø4.3 holes are cut
    # in build_chassis_base, so the hull-relief sub() there is a no-op -- which is also
    # the standing proof that the pins can never jam.
    for tpx, tpy in P["base_pin_pts"]:
        pin = cyl(P["base_pin_d"] / 2, P["base_pin_h"])
        pin.apply_translation((tpx, tpy, z0 + floor + P["base_pin_h"] / 2))
        body = uni([body, pin])
    # BME688: 2x O5 x 2 standoff bosses on the LEFT wall inner face flanking the
    # y=-96 vent + O1.7 M2 pilots 3.0 into the 5-wall (2.0 web outside).
    wallx = -(P["chassis_w"] / 2 - 5.0)              # inner face -65
    bh_ = P["bme_boss_h"]
    for sy_ in (-1, 1):
        by_ = P["bme_cy"] + sy_ * P["bme_hole_cc"] / 2
        boss = cyl(2.5, bh_ + 1.0, axis="x")         # 1.0 buried in the wall to
        boss.apply_translation((wallx + (bh_ - 1.0) / 2, by_, P["bme_cz"]))  # fuse
        body = uni([body, boss])
        bpil = cyl(0.85, bh_ + 3.5, axis="x")        # boss face -> 3.0 into the
        bpil.apply_translation((wallx + bh_ + 0.5 - (bh_ + 3.5) / 2,   # wall, 0.5
                                by_, P["bme_cz"]))   # overshoot past the face
        body = sub(body, bpil)

    _color(body, "base")
    body.metadata["name"] = "chassis"
    return body


def build_chassis_parts():
    """Printable chassis split: lower open tub + removable upper pan deck -- BOTH now
    sub-split for print speed (2026-07-10, user: break the biggest prints apart):

    - lower tub -> chassis_lower_front / chassis_lower_rear at y = +26 (the only
      vent-free wall band clear of the pan pedestal <=|24| and the pod-join stations
      +-40). Joined by two FLOOR PADS at x +-61 (M3x12 axis Y from the front face into
      rear thread-form pilots + a Ø4 press/slip dowel each) -- plus, in the assembly,
      the one-piece pod RAILS (stations y +-40 land one per half) and the deck screws
      bridge the halves.
    - pan deck -> chassis_deck_front (y 66..) / chassis_deck_center / chassis_deck_rear
      (y ..-52). Seams clear the pan clips (front clip reaches y 58) and keep the pan
      seat MONOLITHIC in the center piece. Each seam is a half-lap (center's lower-half
      shelf under the strip, 0.15 fit) + 2x vertical M3 through the strip into shelf
      pilots; the center piece gets its OWN 4 hold-downs to the lower at (+-64, 8) and
      (+-64, -26) (vent-free bands), since the original 4 corner screws land in the
      strips."""
    from trimesh.intersections import slice_mesh_plane

    z0 = P["chassis_clear"]
    z1 = P["base_h"]
    seam = P["chassis_split_z"]
    core = build_chassis_core()

    # Screw bosses span the seam before slicing, so both halves get matching local pads.
    all_downs = tuple(P["chassis_split_screws"]) + tuple(P["deck_center_screws"])
    boss_bot = seam - 9.0
    boss_top = seam + 12.0
    for sx_, sy_ in all_downs:
        boss = cyl(P["chassis_split_boss_r"], boss_top - boss_bot)
        boss.apply_translation((sx_, sy_, (boss_bot + boss_top) / 2))
        core = uni([core, boss])

    # lower-tub seam FLOOR PADS (span y across the seam; drilled after slicing)
    ysl = P["lower_seam_y"]
    ysl2 = P["lower_seam2_y"]
    # per-seam fastener x: the y=26 seam uses the vent-free wall band (x 61); the
    # TAIL seam (lower_seam2_y, moved -88 -> -95 in the 2026-07-15 fastening campaign)
    # uses the x 50..60.2 strip between the equipment base and the side-panel plane.
    # BOTH seams now get real floor-pad hardware: the tail used to be a BARE BUTT PLANE
    # tied only by the base + panels, and it is the break the user reported
    # (FASTENING_AUDIT P0-2).
    for sx_ in (-1, 1):
        # pad pulled INBOARD of the side-panel plane (2026-07-14 round 2: the wall
        # band x 64.85..70 is now the removable chassis_side_* panel, so the pad
        # stops at x 64.7 with 0.15 running clearance to the panel's inner face;
        # screw/dowel re-clocked inboard to match -- see _seam_join call below)
        pad = box(14.7, 26.0, 8.0)
        pad.apply_translation((sx_ * 57.35, ysl, 18.0))      # x 50..64.7, z 14..22
        # (rooted 1 into the raised floor top 15 -- v2 clear 10)
        core = uni([core, pad])
        # TAIL-seam pad (2026-07-15, P0-2): same idea, re-clocked to the free strip.
        ty0, ty1 = P["tail_pad_y"]; tz0, tz1 = P["tail_pad_z"]
        tpad = box(10.2, ty1 - ty0, tz1 - tz0)
        tpad.apply_translation((sx_ * P["tail_pad_x"], (ty0 + ty1) / 2, (tz0 + tz1) / 2))
        core = uni([core, tpad])

    lower = slice_mesh_plane(core, plane_normal=(0, 0, -1), plane_origin=(0, 0, seam), cap=True)
    deck = slice_mesh_plane(core, plane_normal=(0, 0, 1), plane_origin=(0, 0, seam), cap=True)

    for sx_, sy_ in all_downs:
        # Top deck: M3 clearance plus a sub-flush pan/cheese head counterbore from above.
        clr = cyl(P["m3_clear_r"], z1 - seam + 8.0)
        clr.apply_translation((sx_, sy_, seam + (z1 - seam + 8.0) / 2 - 2.0))
        deck = sub(deck, clr)
        cb = cyl(3.4, 3.0)
        cb.apply_translation((sx_, sy_, z1 - 1.5))
        deck = sub(deck, cb)

        # Lower tub: Ø3.4 clearance down the boss into a CAPTIVE M3 HEX NUT
        # (2026-07-15, FASTENING_AUDIT P1: these 8 were thread-form pilots into PLA,
        # and 6 of them are the side panels' ONLY top retention -- 5.1 mm of thread on
        # a scarfed boss, the audit's failing class). The nut slides in HORIZONTALLY
        # toward the tub interior, reachable with the deck off; the boss's 3+ mm over
        # the nut's top flat carries the clamp into the z 46 deck seat.
        pil = cyl(P["m3_clear_r"], 8.5)
        pil.apply_translation((sx_, sy_, seam - 8.5 / 2))       # bore z 37.5..46
        lower = sub(lower, pil)
        # nut trap: slot runs toward the tub interior -- -x for the six side-wall
        # bosses (seat sits inside the 5-wall), +y for the two on the rear wall.
        odir = (0.0, 1.0, 0.0) if abs(sy_) > 100 else (-np.sign(sx_), 0.0, 0.0)
        oz = P["deck_nut_z"]
        lower = sub(lower, geo.nut_slot((sx_, sy_, oz), screw_axis="z", open_dir=odir,
                                        size="M3", length=P["deck_nut_run"]))
        if abs(sx_) > 50.0:
            # OPEN THE SLOT'S FLOOR on the six scarfed wall bosses: the pocket's flat
            # bottom (z 41.6) and the 45 deg print scarf under the boss CONVERGE, so
            # they left a knife crescent between them (wallcheck: p1 0.77 at
            # (61.2, 5.1, 40.2)). Drop the void to z 36 over the whole run -- the nut
            # is held by the roof + the two side walls + the seat and the screw pulls
            # it UP into the roof, so a floor was never doing anything; you also get
            # to see and feel the nut going in.
            run = P["deck_nut_run"]
            drop = box(run, geo.NUT["M3"][0] + 0.2, (oz - 1.4) - 36.0)
            drop.apply_translation((sx_ - np.sign(sx_) * (M3_AC / 2 - run / 2), sy_,
                                    (36.0 + oz - 1.4) / 2))
            lower = sub(lower, drop)

    # ---- lower tub seams: front/rear at ysl, then peel the rear TAIL at ysl2 ----
    # Both seams use the SAME joint: M3x12 axis-Y through the +y piece's floor pad
    # into a Ø2.5 thread-form pilot in the -y piece + a Ø4 dowel (drilled here,
    # across the pad added to core above).
    def _seam_join(mesh, sy, xs, xd):
        # The screw axis is HORIZONTAL (Y) and the lower tub prints seam-up (floor
        # down), so the through-hole + head counterbore are hanging bores. Cut them as
        # TEARDROPS (45deg self-supporting roof) so they print clean with no support
        # and no sagging ceiling -- the hanging-screw-pocket fix (2026-07-13, DFAM).
        # The Ø4 dowel stays round: it's small (bridges fine) and wants full-round grip.
        # 2026-07-15 (FASTENING_AUDIT P1 + P2-3): the -y thread-form pilot became a
        # CAPTIVE M3 HEX NUT dropped in from above (the tub is open-top: reachable at
        # assembly, self-supporting in the seam-up print), and the Ø6.8 HEAD
        # COUNTERBORE is GONE -- it left a ~1.0 mm wall to the pad's x-64.7 face and
        # bought nothing: the M3 socket head (Ø5.5) simply seats PROUD on the pad's
        # free +y face, the chassis_side foot convention. Dropping it recovers more
        # section than widening the pad could: the pad is capped at 14.7 either way
        # (the belly OPENING edge is x 50, the side-panel plane x 64.85).
        for sx_ in (-1, 1):
            scr = teardrop(P["m3_clear_r"], 21.0, axis="y")  # M3x20 through the +y pad
            scr.apply_translation((sx_ * xs, sy + 3.5, 18.0))    # -> nut at sy-4
            mesh = sub(mesh, scr)
            mesh = sub(mesh, geo.nut_slot((sx_ * xs, sy - 4.0, 18.0),   # = the bore
                                          screw_axis="y",              # axis; nut_slot
                                          open_dir=(0, 0, 1), size="M3",  # seats it
                                          length=(22.0 - 18.0) + M3_AC / 2 + 2.0))
            dwl = cyl(2.05, 16.0, axis="y")                  # Ø4 dowel across the seam
            dwl.apply_translation((sx_ * xd, sy, 18.0))      # (+0.1 slip; press the -y
            mesh = sub(mesh, dwl)                            #  side on assembly with glue)
        return mesh

    def _tail_join(mesh_tail, mesh_rear, sy):
        """TAIL SEAM JOINT (2026-07-15, FASTENING_AUDIT P0-2 "the tail break"): the
        y=-95 seam used to be a bare butt plane -- no pads, no screws, no dowel, no
        registration; the tail hung off the equipment base + the side panels alone.

        Per side, on the pads unioned into `core` above (x 50..60.2, z 14..24):
          - a TONGUE/SHELF across the seam: the tail grows a 6-wide x 5-tall tongue
            into a matching pocket in the rear pad, so the two shells self-hold
            (x + z registration) while the screw is driven -- the audit's third fix
            pattern, replacing the y=26 seam's Ø4 dowel (there is no room here for a
            dowel beside the bore in a 10.2-wide pad, and the tongue does the same job
            with more shear area).
          - 1x M3x16 axis-Y through the REAR pad's free +y face into a CAPTIVE M3 HEX
            NUT slide-dropped into the tail pad from ABOVE (the tub is open-top, so
            the slot is reachable at assembly AND self-supporting in the seam-up
            print). This replaces the thread-form pilot the y=26 seam still uses --
            the failing class per the audit's systemic verdict.
        Driver access: along +y at z 21 inside the open tub, before the side panels
        (whose TT tab rib crosses that corridor at y -87..-79.2) go on -- and the
        panels bridge this seam anyway, so they always come off first."""
        tpx = P["tail_pad_x"]
        ty0, ty1 = P["tail_pad_y"]; tz0, tz1 = P["tail_pad_z"]
        ztg = tz0 + 4.0                                  # tongue top (14..18)
        zs = 21.5                                        # screw axis, over the tongue
        for sx_ in (-1, 1):
            # --- tongue: the tail keeps the pad's lower band across the seam
            lap = box(6.0, 12.0, ztg - tz0)
            lap.apply_translation((sx_ * tpx, sy + 3.0, (tz0 + ztg) / 2))   # y -101..-89
            lap_fit = box(6.3, 12.3, (ztg + 0.15) - tz0)
            lap_fit.apply_translation((sx_ * tpx, sy + 3.0, (tz0 + ztg + 0.15) / 2))
            mesh_tail = uni([mesh_tail, inter(lap, mesh_rear)])
            mesh_rear = sub(mesh_rear, lap_fit)
            # --- M3x16 through the rear pad -> captive nut in the tail pad
            scr = teardrop(P["m3_clear_r"], 22.0, axis="y")   # horizontal bore -> the
            scr.apply_translation((sx_ * tpx, sy + 3.0, zs))  # seam-up print wants a
            mesh_tail = sub(mesh_tail, scr)                   # 45deg self-supporting
            mesh_rear = sub(mesh_rear, scr)                   # roof (geo.teardrop)
            mesh_tail = sub(mesh_tail, geo.nut_slot((sx_ * tpx, sy - 6.0, zs),
                                                    screw_axis="y",   # = the bore axis
                                                    open_dir=(0, 0, 1), size="M3",
                                                    length=(tz1 - zs) + M3_AC / 2 + 2.0))
        return mesh_tail, mesh_rear

    def _despeck(mesh, min_cm3=0.5):
        """Drop tiny disconnected fragments a seam cut can shear off a wire-pass /
        pad edge (they'd print as loose specks). Keeps every real body.

        NEVER size-filter a NEGATIVE-volume component. A fully-enclosed void (a
        blind/internal bore) is its own connected component whose shell has inward
        normals, so it splits out with negative volume -- the old `abs(p.volume)`
        made a Ø4x16 dowel bore look like a 0.21 cm3 speck and DELETED THE HOLE.
        That silently un-drilled all four y=26 seam dowel bores: the fastening
        campaign's own locators were never in the printed parts (2026-07-16).
        A cavity is a hole, not a speck; only positive bodies can be loose.
        """
        parts = mesh.split(only_watertight=False)
        if len(parts) <= 1:
            return mesh
        keep = [p for p in parts
                if p.volume < 0.0 or p.volume / 1000.0 >= min_cm3]
        return trimesh.util.concatenate(keep) if keep else mesh

    # seam fasteners re-clocked with the 14.7-wide pad (screw 57 -> 60.3 clears the
    # ULN post edge 58.5 by 0.2 and keeps a 1.0 wall to the pad face 64.7; the dowel
    # moved off the WALL x 66 -- that wall is a removable panel now -- into the pad
    # at x 54, 2.65 web to the screw bore)
    lower = _seam_join(lower, ysl, 60.3, 54.0)

    # ---- SIDE PANELS chassis_side_{L,R}_{front,rear} (2026-07-14 round 2, user:
    # the wall bands the pod RAILS and TT MOTORS mount to are IN-FLUX -> separate
    # by stability, same reasoning as chassis_base). Each side wall's feature band
    # (y -108..109, z 12..46, the 5-wall x 65..70) is CARVED out of the tub as
    # bolt-in panels carrying everything already cut/grown there: TT shaft bores +
    # outer recesses + M3s + nub pockets + tab RIBS, the pod-join screw/dowel
    # holes, the side vents, the BME688 wall bosses (left), and the lower halves
    # of the 6 deck hold-down bosses at x +-64 -- so the existing deck screws now
    # clamp the panels down (top retention, no new hardware). Bottom retention:
    # one L-FOOT per piece on the floor top (M3x6 into a blind Ø2.5 floor pilot,
    # the chassis_base convention). Ends and the mid split are 0.3 butt gaps; the
    # panel rests on the floor top (z 12), the deck rests on its top edge (z 46).
    # Re-motoring or re-railing a side now reprints one ~30 cm3 piece, not the
    # hull. Each side splits at y=-18.5 (free band between the boss(-26) capture
    # end -21.65 and the y=-11.5 wheel station's nut slot start -15.15) so both
    # pieces fit the 180 bed. The FRONT piece spans the y=26 hull seam, the REAR
    # piece spans y=-88 -- panels double as seam ties.
    #
    # FULL-LENGTH TRACK MODULE (2026-07-14 round 4, user: "extend the sides to
    # the end bolt-axles... assemble the track system without chassis_lower_*"):
    # the panels now run y -139.2..142.5 -- through the tub-corner skins, the
    # end-wall outer notches and the prow-cheek outer skins (all x >= 64.85,
    # z 12..46) -- and grow END TOWERS that REPLACE the deck's idler pylons:
    # per tip a 5.15 outer slab (x 64.85..70, fused to the captured skin below
    # the old pylon notch) + a 45deg-chamfered inboard thickening to x 62
    # (0.2 over the notch floor, 1.0 off the notch wall at x 61 -- the pylon's
    # own clearances) + the Ø14 hub boss. FRONT tower carries the true-stadium
    # TENSION SLOT (idler_slot_in/out travel, washer seat on the x 70 face,
    # the x 60..62 washer corridor to the cheek nut duct stays open under the
    # chamfer); REAR tower a Ø8.4 through bore. The M8 NUT DUCTS STAY IN THE
    # CHEEKS (wrench-free service with the hull on; on the bench the inboard
    # face is wrench-open). The two pieces SPLICE at a half-lap in the L-return
    # (y -21.5..-15.55, front keeps the upper half, rear the lower, 1x M3x10
    # vertical at (75.4, -18.5) -- staggered 3 off the wall butt seam), so a
    # side assembles RIGID with zero hull pieces: panels + splice screw + TT
    # motors + wheels + M8 end axles + track = a standalone track pod.
    # Deck pylons DELETED; track tension now loads the towers -> panel walls.
    #
    # WHEEL BEAM INTEGRAL (2026-07-14 round 3, user: pod_rail_L/R DELETED): the
    # rail only existed because the wall was hull; its jobs move ONTO the panel
    # as a continuous L-RETURN running the full piece length -- web x 69.5..74
    # (0.5 fused into the wall, z 12..26, under the vent band 28.5+ and over the
    # bottom-run knuckle tops 9.5) + the PROVEN beam section x 74..80.4 / z 14..26
    # (anti-buckle cap gap 4.5 unchanged), with a 45 deg chamfer closing the beam
    # underside back to the web foot so the upright print self-supports. All rail
    # cuts carry over per piece: Ø4.4 M4 bolt-axle bores (teardropped -- they are
    # horizontal in this print), M4 nut slide-up slots (extended down through the
    # web to z 11.5 so nuts still insert from below), Ø13.5 sprocket-hub notches
    # (open-top, through web + beam) and the Ø17 hub recess re-cut where the web
    # would refill it. The pod-join M3/dowel fittings are deleted outright: the
    # panel IS the wall, held by its feet + deck bosses. Load path: wheels -> M4
    # axles -> beam -> web -> wall -> full-length z46 top-edge bearing under the
    # deck (compression, not screws). Print UPRIGHT (z12 edge + rib feet + foot
    # pads co-planar on the bed); tree(auto) catches the deck-boss undersides.
    # Service: master link open -> deck off -> foot screws -> the whole side
    # (panel + wheels + TT motors) lifts out as a drive module.
    px0, px1 = 64.85, 71.0            # band: 0.15 off the pad face .. past the wall
    pz0, pz1 = 15.0, 47.0             # floor top (clear 10 + 5) .. past the z46 cap
    foot_x = 62.9                     # foot band x 60.5..65.3 (fused 0.3 into the wall)
    foot_pts = ((4.0, -3.0, 11.0), (-95.25, -102.0, -88.5))   # (screw y, y0, y1)

    from shapely.ops import unary_union

    def _prism(fps):
        """ONE capture solid from 2D (x,y) footprints: shapely-union the rects/
        discs, extrude z 12..47. A single clean prism per boolean -- compound 3D
        unions of these overlapping coplanar boxes made manifold HALLUCINATE
        ~150 mm3 of phantom material (probe-verified 2026-07-14: the captured
        window volume exceeded what `lower` holds there), plus z12 sheets and
        wall-face curtains that broke wallcheck + the BME gate."""
        pr = extrude_polygon(unary_union(fps), pz1 - pz0)
        pr.apply_translation((0, 0, pz0))
        return pr

    def _xb(s, xa, xb_, ya, yb):
        lo, hi = min(s * xa, s * xb_), max(s * xa, s * xb_)
        return sg.box(lo, ya, hi, yb)

    def _boss_fp(s, by_):
        # deck-boss capture: disc + a bridge rect to the band plane. A bare disc
        # crossed x 64.85 at ~11 deg and left a full-height feather wedge at its
        # tangent (wallcheck: p1 0.79 at (64.9, -20.7, 12)); the rect corners
        # meet the plane square instead.
        return sg.Point(s * 64.0, by_).buffer(4.35, 32).union(
            _xb(s, 62.0, 66.0, by_ - 4.35, by_ + 4.35))

    # rib/corner captures run FULL DEPTH (x to 51.3) so the r12 cavity-corner
    # rounds aren't sliced lengthwise into feather crescents (wallcheck, round 2).
    # Ends restored to the round-4 extents 2026-07-14 evening: the round-5 "whole
    # arc to the end wall" captures SEVERED the hull's only floor<->end-block
    # ligaments (the corner crescents past |y|~109), and the 0.5 p1 wedge they
    # chased turned out to be an artifact of the compound-union boolean glitch
    # (fixed for real by the single-prism captures below).

    # M8 NUT WINDOW notches in the hull end walls (v2 end simplification): the
    # tower nut cages' travel windows cross the y +-120 wall faces by ~1-3 mm
    # (the old cheek duct "bit the wall" the same way). Small blind notches,
    # hidden behind the towers.
    for s_ in (-1, 1):
        for sgn_, y0_, y1_ in ((1, 116.8, 120.001), (-1, -120.001, -118.7)):
            ntc = box(8.5, y1_ - y0_, 18.0)
            ntc.apply_translation((s_ * 58.25, (y0_ + y1_) / 2, 37.0))
            lower = sub(lower, ntc)

    panels = []
    band_cuts = []
    for s in (-1, 1):
        side = "L" if s < 0 else "R"
        caps_front = [_xb(s, 51.3, 69.5, 101.2, 108.7),
                      _boss_fp(s, 60.0),
                      _boss_fp(s, 8.0)]
        caps_front_cut = [_xb(s, 51.3, 69.5, 101.2, 109.0)] + caps_front[1:]
        caps_rear = [_xb(s, 51.3, 69.5, -87.0, -79.2),
                     _xb(s, 62.0, 71.0, -107.7, -102.5),
                     _boss_fp(s, -26.0)]
        caps_rear_cut = [_xb(s, 51.3, 69.5, -87.0, -79.2),
                         _xb(s, 62.0, 71.0, -108.0, -102.5),
                         _boss_fp(s, -26.0)]
        if s < 0:
            bmefp = sg.box(-71.0, -106.6, -62.4, -87.8)
            caps_rear.append(bmefp)
            caps_rear_cut.append(bmefp)
        cut_prism = _prism([_xb(s, px0, px1, -139.5, 142.8)]
                           + caps_front_cut + caps_rear_cut)
        band_cuts.append(cut_prism)      # ONE prism per side, subtracted below
        zc_tt = _spr_cz()                         # 28.47: sprocket/TT shaft line
        rr_z = (_track_zc() - P["track_wheel_r"]) + 3.5 + P["roadwheel_d"] / 2 + 0.1
        # (LOOP-keyed: the road wheels ride the ground run; only the TT/sprocket
        # cluster moved up to _spr_cz with the 14T)
        za_ax = _track_zc() + P["track_raise"]    # 38.32: end-axle line (ex-pylons)
        ey_ax = P["track_wheelbase"] / 2          # 128.163
        # v2: the raised floor top (15) equals the beam bottom (anti-buckle cap
        # 9.5 -> 15 = 5.5, was 4.5 -- documented), so the L-return is a plain
        # rect block and the upright print's bed plane is one flat z 15.
        lpoly = [(s * 69.5, -15.0), (s * 80.4, -15.0),
                 (s * 80.4, -27.0), (s * 69.5, -27.0)]
        for nm_, ky0, ky1, caps, fi in ((f"chassis_side_{side}_front", -18.35, 142.5,
                                         caps_front, 0),
                                        (f"chassis_side_{side}_rear", -139.2, -18.65,
                                         caps_rear, 1)):
            pnl = inter(lower, _prism([_xb(s, px0, px1, ky0, ky1)] + caps))
            fy, fy0, fy1 = foot_pts[fi]
            foot = box(4.8, fy1 - fy0, 4.0)
            foot.apply_translation((s * foot_x, (fy0 + fy1) / 2, 17.0))
            # L-RETURN web + wheel beam (see the block comment above): the full
            # cross-section (69.5,12)-(74,12)-(76,14)-(80.4,14)-(80.4,26)-(69.5,26)
            # runs the loop's flat band (clipped |y| <= 112 -- the ramps rise from
            # 120) and the two pieces HALF-LAP at y -21.5..-15.55 (front upper /
            # rear lower, 0.15 fits). extrude_polygon runs +Z; rotate onto +Y
            # with the (x, -z) convention like the nut duct.
            if fi == 0:
                lsec = extrude_polygon(sg.Polygon(lpoly), 112.0 - (-15.55))
                lsec.apply_transform(R(-TAU / 4, (1, 0, 0)))
                lsec.apply_translation((0, -15.55, 0))
                # tongue starts at x 70.0, NOT the web root 69.5: in the lap zone
                # the WALL (x 65..70) belongs to the OTHER piece for part of the
                # span (wall butt at -18.5, lap at -21.5..-15.55 -- staggered),
                # and a 69.5-rooted tongue pressed 0.5 into it (fits caught it)
                lap = box(80.4 - 70.0, 21.35 - 15.55, 27.0 - 21.15)   # upper tongue
                lap.apply_translation((s * (70.0 + 80.4) / 2, -(21.35 + 15.55) / 2,
                                       (21.15 + 27.0) / 2))
            else:
                lsec = extrude_polygon(sg.Polygon(lpoly), -21.5 - (-112.0))
                lsec.apply_transform(R(-TAU / 4, (1, 0, 0)))
                lsec.apply_translation((0, -112.0, 0))
                lap = extrude_polygon(sg.Polygon(                  # lower tongue =
                    [(s * 70.0, -15.0), (s * 80.4, -15.0),         # L-block under
                     (s * 80.4, -21.0), (s * 70.0, -21.0)]),       # the z 21 lap
                    21.5 - 15.7)                                   # plane
                lap.apply_transform(R(-TAU / 4, (1, 0, 0)))
                lap.apply_translation((0, -21.5, 0))
            # END TOWER (round 4): outer slab fused over the captured skin +
            # chamfered inboard thickening + hub boss; front adds the tension
            # slot, rear the Ø8.4 bore (exact ex-pylon geometry, see the block
            # comment). Slab spans the pylon band; keep band ends 0.3 inside
            # the hull cut so the cheek-tip butt gap survives.
            # slab reaches back to |y| 114: the corner-arc wedge (x >= 64.85
            # tapers out at |y| 116.85) is the only captured material there since
            # the cheeks died -- the slab bridges tower <-> panel through it and
            # doubles as the panel's own skin over the end-wall notch band.
            ty0, ty1 = (114.0, 142.5) if fi == 0 else (-139.2, -114.0)
            slab = box(70.0 - 64.85, ty1 - ty0, 46.0 - 26.3)
            slab.apply_translation((s * (64.85 + 70.0) / 2, (ty0 + ty1) / 2,
                                    (26.3 + 46.0) / 2))
            tk0, tk1 = (120.5, 142.5) if fi == 0 else (-139.2, -120.5)
            thk = extrude_polygon(sg.Polygon(
                [(s * 64.85, -26.5), (s * 62.0, -29.35),
                 (s * 62.0, -46.0), (s * 64.85, -46.0)]), tk1 - tk0)
            thk.apply_transform(R(-TAU / 4, (1, 0, 0)))
            thk.apply_translation((0, tk0, 0))
            ey_s = ey_ax if fi == 0 else -ey_ax
            hb = cyl(7.0, 8.0, axis="x")
            hb.apply_translation((s * 66.0, ey_s, za_ax))
            # pairwise unions on purpose: a single 7-mesh union hit the same
            # manifold compound-boolean glitch as the caps (it grew the rear rib
            # face 0.39 into the BME board's clearance, gate-caught at 0.07 mm3)
            for extra_ in (foot, lsec, lap, slab, thk, hb):
                pnl = uni([pnl, extra_])
            if fi == 0:                            # tension slot (true stadium)
                i_t, o_t = P["idler_slot_in"], P["idler_slot_out"]
                c0 = cyl(4.2, 12.0, axis="x"); c0.apply_translation((0, -i_t, 0))
                c1 = cyl(4.2, 12.0, axis="x"); c1.apply_translation((0, o_t, 0))
                bwe = box(12.0, i_t + o_t, 8.4)
                bwe.apply_translation((0, (o_t - i_t) / 2, 0))
                sl_ = uni([c0, c1, bwe])
                sl_.apply_translation((s * 66.0, ey_s, za_ax))
                pnl = sub(pnl, sl_)
                cage_y0, cage_y1 = ey_s - 9.8, ey_s + 14.3   # nut travel window
            else:                                  # rear: Ø8.4 through clearance
                sk_ = teardrop(4.2, 12.0, axis="x")        # 45deg roof: apex 44.3
                sk_.apply_translation((s * 66.0, ey_s, za_ax))   # stays under the
                pnl = sub(pnl, sk_)                        # tower top 46
                cage_y0, cage_y1 = ey_s - 7.8, ey_s + 7.8
            # M8 NUT CAGE (v2 end simplification: the cheek ducts/channels are
            # GONE; the nut rides the tower's inboard face). LEDGE + ROOF strips
            # grip the NYLOC's flats +-z (gap 13.4 = AF 13 + 0.4) across the
            # whole travel window; axial tension lands on the tower face around
            # the slot, the strips only stop rotation. Nut slides in from
            # inboard, wrench-free -- and the bare track module can tension
            # WITHOUT any hull piece.
            for z0_, z1_ in ((za_ax - 6.7 - 3.0, za_ax - 6.7),
                             (za_ax + 6.7, 46.0)):
                strip = box(64.95 - 54.5, cage_y1 - cage_y0, z1_ - z0_)
                strip.apply_translation((s * (54.5 + 64.95) / 2,     # rooted through
                                         (cage_y0 + cage_y1) / 2,    # the thickening
                                         (z0_ + z1_) / 2))           # into the slab
                pnl = uni([pnl, strip])
            # CAGE END WALLS (support pass 2026-07-14, user: the flat strip
            # undersides tree'd heavily in the upright print). One wall past
            # each end of the travel window, ledge-bottom to roof-top, dropped
            # onto the captured cheek-skin top (z 26.3) so the wall itself has
            # ZERO overhang -- and both strips become end-anchored BRIDGES the
            # slicer spans without support. Walls sit OUTSIDE the nut travel,
            # so insertion (from inboard) and the slide are untouched.
            for wy0, wy1 in ((cage_y0 - 2.5, cage_y0), (cage_y1, cage_y1 + 2.5)):
                wy0c = max(wy0, ky0 + 0.2); wy1c = min(wy1, ky1 - 0.2)
                if wy1c - wy0c < 1.0:
                    continue
                wall = box(64.95 - 54.5, wy1c - wy0c, 46.0 - 26.3)
                wall.apply_translation((s * (54.5 + 64.95) / 2,
                                        (wy0c + wy1c) / 2, (26.3 + 46.0) / 2))
                pnl = uni([pnl, wall])
            # DECK-BOSS SCARFS (support pass 2026-07-14): the six deck hold-down
            # bosses' flat undersides (z 37, protruding ~4.9 from the wall) each
            # demanded a support tower in the upright print. Cut a 45deg wedge
            # under the protruding part (x <= 64.85 -- the in-wall part has no
            # exposed underside) so the boss bottom self-supports; the Ø2.5
            # pilot keeps z ~40.9..46 = 5.1 of thread (clamp screw, plenty).
            # Removal-only, so the TT-pocket clearances can only improve.
            for by_ in ((60.0, 8.0) if fi == 0 else (-26.0,)):
                # (scarf HELD at the 2026-07-14 diagonal: dropping it to fit the
                # P1 captive nut lower made the 45 deg cut graze the bare r4 boss
                # cylinder tangentially -- wallcheck p1 0.77. The nut sits at
                # deck_nut_z 43 instead: 1.7 mm of boss over its top flat, in pure
                # COMPRESSION between the nut and the deck seat, ~1800 N of PLA.)
                scf = extrude_polygon(sg.Polygon(
                    [(s * 64.85, -39.7), (s * 64.85, -33.0),
                     (s * 58.5, -33.0), (s * 58.5, -46.05)]), 10.0)
                scf.apply_transform(R(-TAU / 4, (1, 0, 0)))    # (x,-z) convention
                scf.apply_translation((0, by_ - 5.0, 0))
                pnl = sub(pnl, scf)
            # splice screw: 1x M3x10 vertical through the lap at (75.4, -18.5)
            if fi == 0:
                spc = cyl(1.65, 8.0); spc.apply_translation((s * 75.4, -18.5, 24.0))
                spb = cyl(3.4, 3.0); spb.apply_translation((s * 75.4, -18.5, 26.2))
                pnl = sub(sub(pnl, spc), spb)
            else:
                spp = cyl(1.25, 5.5); spp.apply_translation((s * 75.4, -18.5, 18.2))
                pnl = sub(pnl, spp)
            for ry in P["roadwheel_ys"]:                   # M4 bolt-axle stations
                if not (ky0 + 4.0 < ry < ky1 - 4.0):
                    continue
                ab = teardrop(2.2, 12.0, axis="x")         # Ø4.4 bore, horizontal in
                ab.apply_translation((s * 75.7, ry, rr_z))  # the upright print. Runs
                # x 69.7..81.7 -- THROUGH the web: the M4x40 shank tip reaches x 71.4
                # (it hung in gap air beside the old rail; the web owns that band now)
                slot = box(3.6, 7.3, 23.65 - 14.5)         # nut slide-up slot, open
                slot.apply_translation((s * 75.7, ry,      # under the z 15 block base
                                        (14.5 + 23.65) / 2))
                pnl = sub(sub(pnl, ab), slot)
                # CRUSH-RIB NIB in the slot mouth (2026-07-15, FASTENING_AUDIT P3:
                # "M4 nut slide-up slots: nuts drop out when flipping the panel").
                # The nuts have to go in BEFORE the panel mounts (the slots are blind
                # after), and the panel gets flipped a dozen times during a track
                # build. A 0.35 nib per wall, one layer proud, at the mouth: the nut
                # is pushed past it once and then cannot fall back out.
                for sn_ in (-1, 1):
                    nib = box(3.6, 0.35, 1.2)
                    nib.apply_translation((s * 75.7, ry + sn_ * (7.3 / 2 - 0.175),
                                           16.4))
                    pnl = uni([pnl, nib])
            for sy_, o_ in ((P["spr_y"], 1.0), (P["spr_y2"], -1.0)):   # TT stations
                if not (ky0 < sy_ < ky1):
                    continue
                hn = cyl(6.75, 12.0, axis="x")             # Ø13.5 notch (open-top:
                hn.apply_translation((s * 75.2, sy_, zc_tt))   # r reaches past z26)
                rec2 = teardrop(8.5, 2.2, axis="x")        # re-cut the Ø17 hub recess
                rec2.apply_translation((s * (70.0 - 0.9), sy_, zc_tt))   # the web
                # (teardrop like the core cut -- the two must stay congruent)
                pnl = sub(sub(pnl, hn), rec2)              # extrusion refilled
                # LOWER TT M3 "nut in the gap" (fittings audit 2026-07-14): the
                # web filled the pod gap where the z 16.57 gearbox screw's nut
                # lived (the z 34.07 one clears the web top 26; the shaft
                # crossing survives via the hub notch). Re-open the bore through
                # the web (teardrop -- horizontal in this print) and give the
                # nut an M4-slot-style slide-up pocket from below, top stop at
                # the bore axis + AF/2 so screwing pulls it centred.
                # 2026-07-15 (FASTENING_AUDIT P2-6): the slot ran x 70.6..73.4,
                # leaving a 0.6 mm skin between the wall's x-70 outer face and the
                # nut pocket. Shifted 0.4 OUTBOARD (71.0..73.8) -> 1.0 mm there, and
                # the top stop is now the true across-CORNERS half (M3_AC/2 = 3.175,
                # not AF/2 = 2.75: a hex with its flats on the +-y slot walls spans
                # across corners along the slide), so the nut really does centre on
                # the bore instead of seating 0.33 low.
                my_ = sy_ + o_ * 20.3
                mzl = zc_tt - 8.75
                mb_ = teardrop(1.6, 6.5, axis="x")
                mb_.apply_translation((s * 71.4, my_, mzl))
                ns_ = box(2.8, 5.7, (mzl + M3_AC / 2) - 14.5)
                ns_.apply_translation((s * 72.4, my_, (14.5 + mzl + M3_AC / 2) / 2))
                pnl = sub(sub(pnl, mb_), ns_)
                # UPPER TT M3 = the reported hands-free failure (FASTENING_AUDIT
                # P0-6): its nut was LOOSE in the ~4 mm pod gap outboard of the
                # wall -- you had to hold it there by hand with the track on, i.e.
                # the joint was unbuildable as coded. Grow the lower screw's pocket
                # pattern up the wall's outer face: a boss standing 6 proud (x
                # 70..76, INSIDE the loop -- probe: the only running gear in
                # z 30..42 at these y is the sprocket disc at x >= 92.4, and the
                # links never enter this band away from the runs), carrying the
                # same slide-up captive hex slot. Nut inserts from below through
                # the z 27..30 window over the L-return block, wrench-free.
                mzu = zc_tt + 8.75
                ubs = box(6.0, 9.0, 12.0)
                ubs.apply_translation((s * 73.0, my_, mzu - 1.22))    # z 30.25..42.25
                pnl = uni([pnl, ubs])
                ubb = teardrop(1.6, 10.0, axis="x")   # re-open the core's wall bore
                ubb.apply_translation((s * 73.0, my_, mzu))           # through the boss
                pnl = sub(pnl, ubb)
                pnl = sub(pnl, geo.nut_slot((s * 72.4, my_, mzu),   # = the bore axis;
                                            screw_axis="x",         # nut_slot seats the
                                            open_dir=(0, 0, -1), size="M3",   # nut onto
                                            length=(mzu + M3_AC / 2) - 29.0))  # it
            # NO counterbore (fittings audit 2026-07-14): a O6.6 cb broke out of
            # the 4.8-wide foot's side walls (0.1-0.5 remnants in wallcheck) --
            # the M3 socket head seats PROUD on the foot top instead (O5.5 on a
            # 4.8 face = 0.35/side overhang, torque-fine; z 16..19 is clear air,
            # the BME board starts z 21 and x inboard).
            fcl = cyl(1.65, 9.0); fcl.apply_translation((s * foot_x, fy, 16.5))
            pnl = sub(pnl, fcl)
            # DEGENERATE-SHEET SCRUB: the capture volumes bottom out exactly on the
            # OPEN floor top (z 12), and inter() leaves a zero-thickness skin fused
            # to the panel there (it broke contains() parity, read as a 0.2 p1 in
            # wallcheck, and produced a garbage 8.9 mm^3 boolean vs the BME
            # placeholder). Shave 1 micron off the bottom: everything real (wall
            # band, feet, rib roots) legitimately bottoms at 12.0 and loses nothing.
            pnl = slice_mesh_plane(pnl, plane_normal=(0, 0, 1),
                                   plane_origin=(0, 0, 15.001), cap=True)
            pnl = _despeck(pnl, 0.05)
            _color(pnl, "base"); pnl.metadata["name"] = nm_
            panels.append(pnl)
        for fy, _f0, _f1 in foot_pts:              # blind Ø2.5 floor pilots under the
            fpil = cyl(1.25, 4.5)                  # feet (stop 0.7 over the belly face)
            fpil.apply_translation((s * foot_x, fy, 10.7 + 4.5 / 2))
            lower = sub(lower, fpil)
    for bc_ in band_cuts:                          # sequential subs (see above)
        lower = sub(lower, bc_)
    lower = _despeck(lower)

    lower_f = _despeck(slice_mesh_plane(lower, plane_normal=(0, 1, 0),
                                        plane_origin=(0, ysl, 0), cap=True))
    lower_r = slice_mesh_plane(lower, plane_normal=(0, -1, 0), plane_origin=(0, ysl, 0), cap=True)
    # rear TAIL cap off the main housing; jointed by _tail_join (2026-07-15, P0-2:
    # it used to be a bare butt plane leaning on the equipment base + side panels).
    # chassis_lower_rear stays the larger piece.
    lower_tail = _despeck(slice_mesh_plane(lower_r, plane_normal=(0, -1, 0),
                                           plane_origin=(0, ysl2, 0), cap=True))
    lower_r = _despeck(slice_mesh_plane(lower_r, plane_normal=(0, 1, 0),
                                        plane_origin=(0, ysl2, 0), cap=True))
    lower_tail, lower_r = _tail_join(lower_tail, lower_r, ysl2)   # P0-2, see above

    # ---- deck -> front strip / center / rear strip with half-laps ----
    yf, yr = P["deck_seam_y"]                                # (66.0, -52.0)
    lap_f = box(120.0, 16.0, 6.0)
    lap_f.apply_translation((0, yf + 4.0, 49.0))             # center shelf under the strip,
    lap_r = box(120.0, 16.0, 6.0)                            # z 46..52
    lap_r.apply_translation((0, yr - 4.0, 49.0))
    lap_f_fit = box(120.6, 16.3, 6.3); lap_f_fit.apply_translation((0, yf + 4.0, 49.05))
    lap_r_fit = box(120.6, 16.3, 6.3); lap_r_fit.apply_translation((0, yr - 4.0, 49.05))
    deck_c = slice_mesh_plane(slice_mesh_plane(deck, plane_normal=(0, -1, 0),
                              plane_origin=(0, yf, 0), cap=True),
                              plane_normal=(0, 1, 0), plane_origin=(0, yr, 0), cap=True)
    deck_f = slice_mesh_plane(deck, plane_normal=(0, 1, 0), plane_origin=(0, yf, 0), cap=True)
    deck_r = slice_mesh_plane(deck, plane_normal=(0, -1, 0), plane_origin=(0, yr, 0), cap=True)
    deck_c = uni([deck_c, inter(lap_f, deck_f), inter(lap_r, deck_r)])   # shelf = the lap
    deck_f = sub(deck_f, lap_f_fit)                          # 0.15-ish lap fit
    deck_r = sub(deck_r, lap_r_fit)
    for strip_y, shelf_y in ((yf + 4.0, yf), (yr - 4.0, yr)):
        for sx_ in (-1, 1):
            scr = cyl(P["m3_clear_r"], 16.0)                 # vertical M3 through the strip
            scr.apply_translation((sx_ * 40.0, strip_y, z1 - 7.0))
            cbv = cyl(3.4, 3.0)
            cbv.apply_translation((sx_ * 40.0, strip_y, z1 - 1.5))
            pilv = cyl(1.25, 6.5)                            # pilot in the center's shelf
            pilv.apply_translation((sx_ * 40.0, strip_y, 49.0))
            deck_c = sub(deck_c, pilv)
            if strip_y > 0:
                deck_f = sub(sub(deck_f, scr), cbv)
            else:
                deck_r = sub(sub(deck_r, scr), cbv)

    # ---- TOY-TANK front-slope CLIFF SENSOR (2026-07-10, user round 2; replaced the
    # same-day full-width prow): the deck overhang's front face slopes 33.7 deg from
    # horizontal, so an HC-SR04 flush in it fires ~34 deg ahead of straight down --
    # the ping lands ~y 163 (about 90 ahead of ground contact), a cliff reads as
    # no-echo. Construction mirrors sensor_us: Ø16.6 barrel bores through the 5-thick
    # slope skin, board against the skin's back in a 1.2 recess, 4x Ø1.6 M2 pilots,
    # all inside an UNDERSIDE POCKET (x +-30 window, so the deck still seats on the
    # tub's front rim at |x| > 30; top skin 3.5). The pocket's inboard end hangs over
    # the open tub, so the wires just drop in -- service = lift the deck. Prints
    # top-face-down: the pocket opens upward, the slope skin is self-supporting.
    # Mirrored on the REAR slope (2026-07-10, user round 3: "same proximity sensors
    # also on the back") for reversing cliff detection. The rear pocket narrows to
    # x +-28: the deck-split rear screw bosses (r 4 at +-34, y -113) come within 2 of
    # its wall; everything else is the sgn-mirrored front construction.
    fw = P["chassis_l"] / 2
    sa_ = np.arctan2(z1 - seam, P["deck_overhang"])
    decks = {1: deck_f, -1: deck_r}
    for sgn in (1, -1):
        sn_ = np.array([0.0, sgn * np.cos(sa_), np.sin(sa_)])    # up-slope unit
        nnf = np.array([0.0, sgn * np.sin(sa_), -np.cos(sa_)])   # outward slope normal
        se0 = np.array([0.0, sgn * fw, seam])                    # slope bottom edge
        d_ = decks[sgn]
        pkt = box(60.0 if sgn > 0 else 56.0, 34.0, 23.5)
        pkt.apply_translation((0.0, sgn * (fw + 1.0), 39.0 + 23.5 / 2))  # |y| 104..138
        pbnd = box(70.0, 80.0, 60.0)                  # trim the pocket at the 5-offset
        pbnd.apply_transform(R(sgn * sa_, (1, 0, 0))) # slope plane (leaves the skin)
        pbnd.apply_translation(se0 - 5.0 * nnf + 15.0 * sn_ + 30.0 * nnf)
        d_ = sub(d_, sub(pkt, pbnd))
        pb_ = se0 + P["cliff_v"] * sn_                # barrel-pair face center
        rec = box(46.2, 21.4, 1.4)                    # board recess into the skin back
        rec.apply_transform(R(np.pi + sgn * sa_, (1, 0, 0)))
        rec.apply_translation(pb_ - 4.5 * nnf)        # spans -3.8..-5.2 along the normal
        d_ = sub(d_, rec)
        for bx_ in (-1, 1):
            bb = cyl(8.3, 12.0, sections=48)          # Ø16.6 barrel pass, like sensor_us
            bb.apply_transform(R(np.pi + sgn * sa_, (1, 0, 0)))
            bb.apply_translation(pb_ + np.array([bx_ * P["us_dx"], 0.0, 0.0]) - 2.5 * nnf)
            d_ = sub(d_, bb)
        for px_ in (-20.5, 20.5):                     # HC-SR04 corner holes 41 x 16.7:
            for py_ in (-8.35, 8.35):                 # Ø1.6 self-tap pilots through-ish
                pil = cyl(0.8, 4.0)                   # the 3.8 remaining skin
                pil.apply_transform(R(np.pi + sgn * sa_, (1, 0, 0)))
                pil.apply_translation(pb_ + np.array([px_, 0.0, 0.0]) + py_ * sn_ - 5.5 * nnf)
                d_ = sub(d_, pil)
        decks[sgn] = d_
    deck_f, deck_r = decks[1], decks[-1]

    # ---- (END-IDLER PYLONS DELETED 2026-07-14 round 4: the end axles moved to
    # the chassis_side panels' END TOWERS -- same y bands 120.5..142.5 / 139.2,
    # same tension stadium + Ø8.4 bore + hub bosses at the 34.32 axle line. The
    # deck overhang keeps only its slab; the towers now also PROP the overhang
    # tips at the z 46 plane.)

    # ---- mmWave FORWARD WINDOW (2026-07-13, PARAMS mmw_*): a second underside
    # pocket in the FRONT deck overhang, left of the cliff pocket (2.0 wall), with
    # a ceiling-hung VERTICAL SEAT TAB -- the LD2410-class board stands facing +Y
    # so its boresight is HORIZONTAL, radiating through the slope's hex-grille
    # skin (2.5 web radome). Construction mirrors the cliff pocket: cut trimmed at
    # the 5-offset slope plane so the skin survives; the inboard end (y < 115)
    # opens downward over the tub for wiring, service = lift the deck.
    mx0, mx1 = P["mmw_pocket_x"]
    mty0, mty1 = P["mmw_tab_y"]
    mz0, mz1 = P["mmw_pocket_z"]
    sa_m = np.arctan2(z1 - seam, P["deck_overhang"])
    sn_m = np.array([0.0, np.cos(sa_m), np.sin(sa_m)])     # up-slope unit
    nn_m = np.array([0.0, np.sin(sa_m), -np.cos(sa_m)])    # outward slope normal
    se_m = np.array([(mx0 + mx1) / 2, fw, seam])           # slope bottom edge
    pkt_m = box(mx1 - mx0, 40.0, mz1 - mz0)
    pkt_m.apply_translation(((mx0 + mx1) / 2, 100.0 + 20.0, (mz0 + mz1) / 2))
    pbnd_m = box(mx1 - mx0 + 20.0, 80.0, 60.0)             # keep the 5-thick skin
    pbnd_m.apply_transform(R(sa_m, (1, 0, 0)))
    pbnd_m.apply_translation(se_m - 5.0 * nn_m + 15.0 * sn_m + 30.0 * nn_m)
    deck_f = sub(deck_f, sub(pkt_m, pbnd_m))
    tab = box(mx1 - mx0 + 2.0, mty1 - mty0, mz1 - mz0 + 1.0)   # fused to both
    tab.apply_translation(((mx0 + mx1) / 2, (mty0 + mty1) / 2,  # pocket walls +
                           (mz0 + mz1 + 1.0) / 2))              # the ceiling
    deck_f = uni([deck_f, tab])
    for sx_ in (-1, 1):                                    # M2 pilots (through the
        mp_ = cyl(0.85, (mty1 - mty0) + 2.0, axis="y")     # 3.5 tab is fine for a
        mp_.apply_translation(((mx0 + mx1) / 2 + sx_ * P["mmw_hole_cc"] / 2,
                               (mty0 + mty1) / 2, 54.0))   # self-tap M2)
        deck_f = sub(deck_f, mp_)

    out = []
    for m_, nm in ((lower_f, "chassis_lower_front"), (lower_r, "chassis_lower_rear"),
                   (lower_tail, "chassis_lower_tail"),
                   (deck_f, "chassis_deck_front"), (deck_c, "chassis_deck_center"),
                   (deck_r, "chassis_deck_rear")):
        _color(m_, "base"); m_.metadata["name"] = nm
        out.append(m_)
    out.extend(panels)                # chassis_side_{L,R}_{front,rear} (named above)
    # EQUIPMENT BASE: built here so it can be RELIEVED against the hull -- subtract the
    # lower shells so the base bottom gets clearance pockets for every dense floor
    # feature it spans (ULN standoffs, belly-edge lip, etc.), a robust drop-in fit that
    # can't silently overlap a hull feature.
    base = build_chassis_base()
    base = _despeck(sub(base, uni([lower_f, lower_r, lower_tail])))
    _color(base, "pi"); base.metadata["name"] = "chassis_base"
    out.append(base)
    return out


def build_chassis_base():
    """Drop-in EQUIPMENT BASE (2026-07-14, user: split the shell so the in-flux
    electronics iterate on a swappable base, not the finalized hull). Owns the
    ARDUINO + IMU + SW-420 seats, re-laid-out into the rear electronics bay (behind
    the belly opening at y<-61 and the pan pedestal at y>-16): the Arduino centred,
    the IMU + SW-420 in the side strips. Plate flat on the hull floor at z12, top
    btop=z15 = the seat plane. Bolts down with 4x M3 into hull-floor pilots
    (build_chassis_core) and SPANS the y=-88 hull seam, so it ties the rear+tail
    shells (that seam needs no pads). Two clearance holes pass the rear deck-split
    bosses through to the deck. Prints flat, plate-down / seats-up -- no support.
    BME stays wall-mounted (air-coupled to the vent, shell-integral like the sonars)."""
    z0, floor = P["chassis_clear"], 5.0
    zb = z0 + floor                      # z12, sits on the hull floor
    btop = zb + 3.0                      # z15 seat plane (3 mm plate)
    base = rounded_box(98.0, 56.0, btop - zb, 6.0)      # x -49..49 (clears the TT tab
    base.apply_translation((0.0, -90.0, zb))            # ribs at x>=52), y -118..-62
    # ARDUINO: rear shelf bar + 4 posts to z21
    sx0, sy0 = P["ard_org"]; seat_z = P["ard_seat_z"]
    shx0, shx1, shy0, shy1, shz0 = P["ard_shelf"]
    shelf = box(shx1 - shx0, shy1 - shy0, seat_z - shz0)
    shelf.apply_translation(((shx0 + shx1) / 2, (shy0 + shy1) / 2, (shz0 + seat_z) / 2))
    base = uni([base, shelf])
    for lx_, ly_ in P["ard_holes"]:
        hx_, hy_ = sx0 - lx_, sy0 - ly_
        post = cyl(3.5, seat_z - btop)
        post.apply_translation((hx_, hy_, (btop + seat_z) / 2))
        base = uni([base, post])
        pil = cyl(1.25, 5.5)
        pil.apply_translation((hx_, hy_, seat_z + 0.5 - 2.75))
        base = sub(base, pil)
    # IMU: 2 posts to imu_seat_z (right side strip)
    ix_, iy_ = P["imu_c"]
    for sy_ in (-1, 1):
        py_ = iy_ + sy_ * P["imu_hole_cc"] / 2
        post = cyl(3.0, P["imu_seat_z"] - btop)
        post.apply_translation((ix_, py_, (btop + P["imu_seat_z"]) / 2))
        base = uni([base, post])
        pil = cyl(1.25, 5.5)
        pil.apply_translation((ix_, py_, P["imu_seat_z"] + 0.5 - 2.75))
        base = sub(base, pil)
    # SW-420: hard pad + pilot + 2 anti-rotation fence nubs (left side strip)
    vx_, vy_ = P["vib_c"]; vw_, vl_ = P["vib_board_wl"]
    pad = box(vw_ + 2.5, vl_ + 2.5, P["vib_pad_h"])
    pad.apply_translation((vx_, vy_, btop + P["vib_pad_h"] / 2))
    base = uni([base, pad])
    vpz = btop + P["vib_pad_h"]
    vpil = cyl(1.25, P["vib_pad_h"] + 3.0)
    vpil.apply_translation((vx_ + P["vib_hole_off"], vy_, vpz + 0.5 - (P["vib_pad_h"] + 3.0) / 2))
    base = sub(base, vpil)
    for sy_ in (-1, 1):
        nub = box(2.0, 2.0, P["vib_pad_h"] + 3.0)
        nub.apply_translation((vx_ + vw_ / 2 + 0.3 + 1.0, vy_ + sy_ * (vl_ / 2 - 1.0),
                               btop + (P["vib_pad_h"] + 3.0) / 2))
        base = uni([base, nub])
    # 4x M3x6 hold-down into the hull's captive belly-face nuts (2026-07-15): clearance
    # + top counterbore (opens up -> self-supporting). cb 2.4 -> 1.8 deep: with the head
    # bottom at z 16.2 an M3x6 tips out at z 10.2, i.e. dead through the nut (10.0..12.8)
    # and 0.2 shy of the belly face. The head then stands 1.2 proud (z 19.2), which still
    # clears the Arduino board's 21.05 underside by 1.85 -- the rear pair sits under it.
    for mx_, my_ in P["base_mount_pts"]:
        clr = cyl(P["m3_clear_r"], 8.0); clr.apply_translation((mx_, my_, btop - 3.0))
        base = sub(base, clr)
        cb = cyl(3.4, 1.8); cb.apply_translation((mx_, my_, btop - 0.9))
        base = sub(base, cb)
    # 2 locating-pin holes over the hull's printed Ø4 pins, +0.15/side slip
    for px_, py_ in P["base_pin_pts"]:
        ph = cyl(P["base_pin_d"] / 2 + 0.15, 8.0)
        ph.apply_translation((px_, py_, btop - 1.0))
        base = sub(base, ph)
    _color(base, "pi"); base.metadata["name"] = "chassis_base"
    return base


def build_belly_plate():
    """Bolt-on BELLY PLATE (task #26): closes the chassis-floor access opening. A 1.45
    flange rides the 1.5-deep rebate (belly stays flush at z=7, 0.05 axial + 0.15
    perimeter clearance) and a 3-thick U-plug fills the opening around the retained
    strap. The two inboard ballast ribs live HERE now (their old floor is the opening),
    so ballast loads from below with the plate off; rib tops (z 14) clear the TT cans
    (|x|>=44 only) and the pan motor (bottom z ~26). 6x M3x10 csk from below."""
    z0 = P["chassis_clear"]; f = P["belly_fit"]
    op, reb = _belly_polys()
    flange = extrude_polygon(reb.buffer(-f, join_style=1), P["belly_lip_t"] - 0.05)
    flange.apply_translation((0, 0, z0))                     # z 7..8.45
    plug = extrude_polygon(op.buffer(-f, join_style=1), 3.0)
    plug.apply_translation((0, 0, z0))                       # z 7..10
    plate = uni([flange, plug])
    rib_l = P["blst_rib_xmax"] - P["blst_usb_hw"]
    for ry in P["blst_rib_y"][1:]:                           # (-51.5, -40): plate ribs
        for sx in (-1, 1):
            rib = box(rib_l, P["blst_rib_w"], P["blst_rib_h"])
            rib.apply_translation((sx * (P["blst_usb_hw"] + rib_l / 2), ry,
                                   z0 + 3.0 + P["blst_rib_h"] / 2))   # z 10..14
            plate = uni([plate, rib])
    # (the REAR-TIE relief left with the tie itself, round 5 -- the plug is a full
    # uninterrupted panel now that the keep strap is gone.)
    # --- PAN PEDESTAL interface (round 5, user: pedestal separate, "bolt and
    # nuts" to the plate): 4x M3x12 csk from below (flush at z 7, the belly-screw
    # convention) into captive hex nuts in the pedestal feet, + 2 Ø4.2 holes for
    # the pedestal's printed registration pins (pan-gear CD is position-critical;
    # screws clamp, pins locate).
    mxp, myp = _ped_c()
    # pan-can relief pocket (v2, chassis_clear 10): the can bottom z 12.95 is
    # PINNED by the pan gear band while the plug top rose to z0+3 = 13 -- give
    # the can a O30 x 1.25 pocket (plug keeps 1.75 under it)
    cpk = cyl(15.0, 1.25)
    cpk.apply_translation((mxp, myp, z0 + 3.0 - 1.25 / 2))
    plate = sub(plate, cpk)
    for dx_, dy_ in ((-18.0, -18.0), (18.0, -18.0), (-18.0, 18.0), (18.0, 18.0)):
        plate = sub(plate, _belly_csk_neg(mxp + dx_, myp + dy_))
        thr = cyl(1.75, 2.6)                          # csk_neg's clearance stops at
        thr.apply_translation((mxp + dx_, myp + dy_,  # z 9.2 (hull-pilot handoff);
                               10.3))                 # bore on through the 3-plug
        plate = sub(plate, thr)
    for dx_ in (-18.0, 18.0):
        dh = cyl(2.1, 8.0); dh.apply_translation((mxp + dx_, myp, 8.5))
        plate = sub(plate, dh)
    # --- ULN2003 standoffs x2 (round 5: BOTH driver boards ride the plate now --
    # they were hull-floor posts rooted on the deleted keep strap / at (0,80)).
    # Same Ø6 posts, tops at z 16 like before, Ø2.5 pilots stopping in the post.
    for cx_, cy_ in (P["uln1_c"], P["uln2_c"]):
        for sx in (-1, 1):
            for sy in (-1, 1):
                px_ = cx_ + sx * P["uln_w"] / 2
                py_ = cy_ + sy * P["uln_h"] / 2
                post = cyl(3.0, 6.0); post.apply_translation((px_, py_, z0 + 3.0 + 3.0))
                plate = uni([plate, post])
                pil = cyl(1.25, 5.0); pil.apply_translation((px_, py_, 16.0 - 2.5))
                plate = sub(plate, pil)
    # POWER TRAY (wiring pass 2026-07-08, see firmware/WIRING.md): the main 5.1 V buck
    # mounts on the plug's rear bay, so dropping the belly plate drops the power stage
    # as a service tray (leave harness slack). Posts Ø6 x 6 with Ø2.5 M3 self-tap
    # pilots on a 40x20 grid (XL4015-class 5 A buck); the board floats over the 4-tall
    # ballast ribs (a post that kisses a rib just fuses -- same part). Keep-outs held:
    # TT cans |x| >= 44.4 (board edge stops at 10), strap y >= -26, plug edge x -49.85.
    # A future I2C co-processor (Pico/PCA9685) stacks on the same grid with 20 mm
    # standoffs -- no dedicated pad until that decision lands.
    tray = [(-35.75, -53.0), (-35.75, -33.0), (4.25, -53.0), (4.25, -33.0)]
    for px_, py_ in tray:
        post = cyl(3.0, 6.0); post.apply_translation((px_, py_, z0 + 3.0 + 3.0))
        plate = uni([plate, post])
        pil = cyl(1.25, 5.0); pil.apply_translation((px_, py_, z0 + 9.0 - 2.5))
        plate = sub(plate, pil)
    # zip anchor pair for a taped/zipped mini buck (aux 5V rail, MP1584-class)
    for zx in (20.0, 34.0):
        zh = cyl(1.6, 6.0); zh.apply_translation((zx, -58.0, z0 + 1.5))
        plate = sub(plate, zh)
    for bx_, by_ in P["belly_screws"]:
        plate = sub(plate, _belly_csk_neg(bx_, by_))
    _color(plate, "base")
    plate.metadata["name"] = "belly_plate"
    return plate


def build_pan_pedestal():
    """Bolt-on PAN-MOTOR PEDESTAL (2026-07-14 round 5, user: "I don't like that
    the neck motor mount is built in chassis_lower_* -- separate it, bolt+nuts to
    the belly plate"). The exact hull pedestal geometry, re-rooted on the belly
    plate's plug top (z 10) instead of the hull floor (z 12): rounded 48x48 body
    to the ear-bar underside (ear_z 30.75), Ø29 through can-drop bore, +Y wiring-
    box relief, M3 ear pilots, the 0.8 seat-pad relief (two ear pads + collar
    footing), the Ø32/Ø29 can-locating collar (ear-bar + wbox notches), and the
    deck-cable-pass corner cut. NEW: 4 corner feet with side-slide M3 hex-nut
    traps (bolts = M3x12 csk from below, flush at the z 7 belly face like every
    belly screw) + 2 printed Ø4 registration pins into plate holes -- the pan
    gear CD is position-critical, so pins locate and screws only clamp. Service:
    drop the belly plate and the pan motor + pedestal + both ULN drivers + the
    power tray leave as ONE tray."""
    z0 = P["chassis_clear"]
    zb = z0 + 3.0 + 0.05                              # plug top 10 + 0.05 seat air
    mx, my = _ped_c()
    zsh = (P["pan_gear_z"][0] - 4.25) - (P["motor_body_h"] + P["motor_gear_h"])
    ear_z = zsh + P["motor_body_h"] - 1.0             # ear-bar underside (30.75)
    ped = rounded_box(48, 48, ear_z - zb, 6.0)
    ped.apply_translation((mx, my, zb))
    # Ø29 can relief: THROUGH bore now (the can bottom hovers ~2.9 over the plug)
    canb = cyl(29.0 / 2, ear_z + 2 - zb + 2)
    canb.apply_translation((mx, my, (zb + ear_z + 2) / 2))
    ped = sub(ped, canb)
    wrel = box(P["motor_wbox_w"] + 3, 22, ear_z + 2 - zb + 2)   # wbox leads exit +Y
    wrel.apply_translation((mx, my + 16, (zb + ear_z + 2) / 2))
    ped = sub(ped, wrel)
    for dxe in (-P["motor_ear_cc"] / 2, P["motor_ear_cc"] / 2):
        e = cyl(1.25, 16); e.apply_translation((mx + dxe, my, ear_z - 4))
        ped = sub(ped, e)
    pw, pd = P["ped_pad_wxy"]
    relief = rounded_box(50, 50, P["ped_relief"], 6.0)
    relief.apply_translation((mx, my, ear_z - P["ped_relief"]))
    for dxe in (-P["motor_ear_cc"] / 2, P["motor_ear_cc"] / 2):
        pad = box(pd, pw, P["ped_relief"] + 2)
        pad.apply_translation((mx + dxe, my, ear_z - P["ped_relief"] / 2))
        relief = sub(relief, pad)
    keep = cyl(P["ped_collar_od"] / 2 + 0.5, P["ped_relief"] + 2)
    keep.apply_translation((mx, my, ear_z - P["ped_relief"] / 2))
    relief = sub(relief, keep)
    ped = sub(ped, relief)
    collar = sub(cyl(P["ped_collar_od"] / 2, P["ped_collar_h"]),
                 cyl(29.0 / 2, P["ped_collar_h"] + 2))
    collar.apply_translation((mx, my, ear_z + P["ped_collar_h"] / 2))
    ncut = box(P["ped_collar_od"] + 4, 8.2, P["ped_collar_h"] + 2)
    ncut.apply_translation((mx, my, ear_z + P["ped_collar_h"] / 2))
    collar = sub(collar, ncut)
    wcut = box(P["motor_wbox_w"] + 3, 12, P["ped_collar_h"] + 2)
    wcut.apply_translation((mx, my + 11, ear_z + P["ped_collar_h"] / 2))
    collar = sub(collar, wcut)
    ped = uni([ped, collar])
    # deck cable pass corner cut (the same cbl bore build_chassis_core drills
    # through the deck membrane: corner sliver x 4..16 / y -24..-19, z from 29)
    ex, ey = P["cable_exit"]
    u = np.array([ex - 0.0, ey - P["neck_chan_y"]]); u = u / np.linalg.norm(u)
    plate_bot, ring_top, seat_floor, zball = _pan_stack()
    cbl = extrude_polygon(sg.LineString([(ex - 4 * u[0], ey - 4 * u[1]),
                                         (ex + 4 * u[0], ey + 4 * u[1])]).buffer(4.0), 24.0)
    cbl.apply_translation((0, 0, seat_floor - 22))
    ped = sub(ped, cbl)
    # mounting: 4x Ø3.4 vertical bores + side-slide hex nut traps (slot opens to
    # the NEAREST y face); the csk heads live in the plate (see build_belly_plate).
    # Nut seat at z 15.9 puts an M3x12 tip ~2 threads past the nut.
    # FIXED 2026-07-15 (fastening campaign): the hand-rolled trap ran its box FROM
    # the bore axis AWAY from it, so the nut -- 6.35 across corners, not 5.5 --
    # could only ever reach axis+3.175 and the screw MISSED it by twice its thread
    # radius. This "reference good" joint never worked, which is why even the
    # chassis's one real nut pocket failed on the first print. geo.nut_slot() now
    # seats the nut on the axis; checks.py asserts the reach.
    for dx_, dy_ in ((-18.0, -18.0), (18.0, -18.0), (-18.0, 18.0), (18.0, 18.0)):
        bx_, by_ = mx + dx_, my + dy_
        bore = cyl(1.7, 12.0); bore.apply_translation((bx_, by_, zb + 3.0))
        ped = sub(ped, bore)
        ped = sub(ped, geo.nut_slot((bx_, by_, 15.9), screw_axis="z",
                                    open_dir=(0.0, float(np.sign(dy_)), 0.0),
                                    size="M3", length=14.0))
    for dx_ in (-18.0, 18.0):                         # printed registration pins:
        pin = cyl(2.0, 2.8)                           # 0.3 fused into the body, 2.45
        pin.apply_translation((mx + dx_, my, zb - 1.4 + 0.3))   # proud into the
        ped = uni([ped, pin])                         # plate's Ø4.2 holes
    _color(ped, "base")
    ped.metadata["name"] = "chassis_pedestal"
    return ped


def build_chassis_electronics():
    """Bought-part PLACEHOLDERS for the electronics seats (2026-07-13; see the
    PARAMS "ELECTRONICS SEATS" block for placements + VERIFY_ON_ARRIVAL markers).
    All FIXED-frame, never printed (export=None convention, like sensor_us): the
    Arduino Uno R3 on its rear-floor posts, the IMU on the strap, the SW-420 on
    its pad, the BME688 on the left-wall vent bosses, and the LD2410-class mmWave
    board on the deck-pocket tab. Each floats 0.05-0.15 off its seat so the
    static gate sees air, not a press."""
    parts = []
    # Arduino Uno R3: board + USB-B shell (the shell drives the +X plug corridor)
    sx0, sy0 = P["ard_org"]
    seat = P["ard_seat_z"]
    bw, bl = P["ard_board_wl"]
    brd = box(bw, bl, 1.6)
    brd.apply_translation((sx0 - bw / 2, sy0 - bl / 2, seat + 0.05 + 0.8))
    usb = box(16.0, 12.0, 10.7)                      # shell overhangs the edge 6.5
    usb.apply_translation((sx0 - 16.0 / 2 + 6.5, sy0 - P["ard_usb_ly"],
                           seat + 0.05 + 1.6 + 10.7 / 2))
    ard = uni([brd, usb])
    _color(ard, "pi"); ard.metadata["name"] = "board_arduino"
    parts.append(ard)
    # IMU breakout: board (long axis Y, holes at +-imu_hole_cc/2) + chip bump
    ix_, iy_ = P["imu_c"]
    ibrd = box(P["imu_board_wl"][1], P["imu_board_wl"][0], 1.2)
    ibrd.apply_translation((ix_, iy_, P["imu_seat_z"] + 0.05 + 0.6))
    ichip = box(4.0, 4.0, 1.0)
    ichip.apply_translation((ix_, iy_, P["imu_seat_z"] + 0.05 + 1.2 + 0.5))
    imu = uni([ibrd, ichip])
    _color(imu, "sensor"); imu.metadata["name"] = "sensor_imu"
    parts.append(imu)
    # BME688 breakout: vertical board on the wall bosses + sensor can toward the vent
    wallx = -(P["chassis_w"] / 2 - 5.0)
    bface = wallx + P["bme_boss_h"] + 0.05           # board back on the boss tips
    bbrd = box(1.2, P["bme_board_yz"][0], P["bme_board_yz"][1])
    bbrd.apply_translation((bface + 0.6, P["bme_cy"], P["bme_cz"]))
    bcan = box(1.4, 3.0, 3.0)                        # sensor package faces the slot
    bcan.apply_translation((bface - 0.75, P["bme_vent_y"], P["bme_cz"]))
    bme = uni([bbrd, bcan])
    _color(bme, "sensor"); bme.metadata["name"] = "sensor_bme"
    parts.append(bme)
    # SW-420: board flat on the pad + a component bump
    vx_, vy_ = P["vib_c"]
    vz_ = 15.0 + P["vib_pad_h"] + 0.05      # SW-420 pad now rides the z15 base top
    vbrd = box(P["vib_board_wl"][0], P["vib_board_wl"][1], 1.2)
    vbrd.apply_translation((vx_, vy_, vz_ + 0.6))
    vpot = box(6.0, 6.0, 4.0)                        # trim pot / comparator bump
    vpot.apply_translation((vx_ + 4.0, vy_, vz_ + 1.2 + 2.0))
    vib = uni([vbrd, vpot])
    _color(vib, "sensor"); vib.metadata["name"] = "sensor_vib"
    parts.append(vib)
    # mmWave LD2410-class: vertical board on the deck-pocket tab face (+Y = boresight)
    mx0, mx1 = P["mmw_pocket_x"]
    mbrd = box(P["mmw_board_wz"][0], 1.2, P["mmw_board_wz"][1])
    mbrd.apply_translation(((mx0 + mx1) / 2, P["mmw_tab_y"][1] + 0.1 + 0.6, 54.0))
    _color(mbrd, "sensor"); mbrd.metadata["name"] = "sensor_mmwave"
    parts.append(mbrd)
    return parts

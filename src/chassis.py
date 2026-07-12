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
from geo import (_color, _orient, blind_socket, box, cyl, fix_pin, frustum, hex_prism, inter, rounded_box, sub, uni)
from tracks import _track_zc
from pan import _pan_stack


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
        pf.append(fix_pin(P["fix_pin_r"], P["fix_pin_len"], (0, -1, 0), (px, fw, pz)))
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
    fl_bar = box(36.0, 1.2, 3.0)
    fl_bar.apply_transform(R(TAU / 4 - ga, (1, 0, 0)))   # y-face normal -> glacis normal
    fl_bar.apply_translation(np.array([0.0, gface_y, P["fled_cz"]]) + 0.6 * gn)
    fl = [fl_bar]
    for i in range(7):
        d = cyl(1.3, 1.6, axis="y", sections=24)
        d.apply_transform(R(TAU / 4 - ga, (1, 0, 0)))
        d.apply_translation(np.array([-15.0 + i * 5.0, gface_y, P["fled_cz"]]) + 1.6 * gn)
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
        pr.append(fix_pin(P["fix_pin_r"], P["fix_pin_len"], (0, 1, 0), (px, -fw, pz)))
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


def _belly_polys():
    """(opening, rebate) shapely polys for the belly access plate (task #26).
    Opening = rounded 100x110 MINUS the retained strap (keeps the pedestal + inboard
    ULN posts rooted); rebate = one bigger rounded rect, cut 1.5 up from the belly
    face EVERYWHERE inside it (incl. under the strap, thinned to 3.5 there) so the
    plate is a single flat flange."""
    w, l = P["belly_open_wl"]; cx, cy = P["belly_open_c"]
    op = sg.box(cx - w / 2, cy - l / 2, cx + w / 2, cy + l / 2)
    op = op.buffer(-8, join_style=1).buffer(8, join_style=1)
    op = op.difference(sg.box(*P["belly_keep"]))
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

    # pan-motor PEDESTAL: top face AT the ear-bar underside so the M3s clamp the ears down.
    # (The old 6-thick pad sank the can 5.5 into the floor while the ears floated 12.4 above.)
    # Fast-pan: the motor DROPPED ~13.5 (32T gear on the flats in the 45..50 band) and the
    # pedestal follows the can to (-19.2, 7.875) -- x -43.2..4.8 stays 2.4 off the drive_L
    # can (-45.6) and on the widened belly strap (belly_keep x0 -44); ears run along X
    # (the motor is clocked -90 in build()), wiring box exits +Y.
    zsh = (P["pan_gear_z"][0] - 4.25) - (P["motor_body_h"] + P["motor_gear_h"])  # can bottom
    ear_z = zsh + P["motor_body_h"] - 1.0            # ear-bar underside (30.75)
    ped = rounded_box(48, 48, ear_z - (z0 + floor), 6.0)
    ped.apply_translation((mx, my, z0 + floor))
    body = uni([body, ped])
    # deck cable pass, now boring through deck AND pedestal corner in one shot (z 29..51,
    # only the corner sliver x 4..16, y -24..-19 comes out of the pedestal); the shaft's
    # -y side is open to the cavity the whole way (pedestal stops at y -24), so the wire
    # swings straight back into the service-loop band.
    body = sub(body, cbl)
    # ULN2003 standoffs (x2 boards eventually; second mount is a deferred detailing task).
    # Board centre shifted +20 in Y: at y=0 the board envelope hit the drive_R TT can
    # (y -23.4..-9.9, x up to 52.5).
    for sx in (-1, 1):
        for sy in (-1, 1):
            b = cyl(3.0, 8); b.apply_translation((38 + sx * P["uln_w"] / 2, 20 + sy * P["uln_h"] / 2, z0 + floor))
            body = uni([body, b])
    # 2nd ULN2003 standoff set (tilt / MX1588 driver) at uln2_c -- see the PARAMS note for
    # why the mirrored (-38,+-20) spot is blocked by the pedestal. Same post style as ULN#1
    # (Ø6 x 8 half-buried in the floor) + Ø2.5 M3 self-tap pilots (stop 1.0 above the floor
    # underside so no through-holes appear in the belly).
    for sx in (-1, 1):
        for sy in (-1, 1):
            px = P["uln2_c"][0] + sx * P["uln_w"] / 2
            py = P["uln2_c"][1] + sy * P["uln_h"] / 2
            b = cyl(3.0, 8); b.apply_translation((px, py, z0 + floor))
            body = uni([body, b])
            pil = cyl(1.25, 8); pil.apply_translation((px, py, z0 + floor))
            body = sub(body, pil)
    # Ø29 can relief bored from the pedestal top down to the floor (can Ø28.25 drops in,
    # bottom hovers 0.45 above the floor; the ears take the clamp load)
    canb = cyl(29.0 / 2, ear_z + 2 - (z0 + floor))
    canb.apply_translation((mx, my, (z0 + floor + ear_z + 2) / 2))
    body = sub(body, canb)
    # wiring-box relief: the blue box now protrudes past the can on +Y (motor clocked -90);
    # open the pocket clear through the pedestal's +Y face so the leads route out sideways
    wrel = box(P["motor_wbox_w"] + 3, 22, ear_z + 2 - (z0 + floor))
    wrel.apply_translation((mx, my + 16, (z0 + floor + ear_z + 2) / 2))
    body = sub(body, wrel)
    # M3 PILOTS Ø2.5 at the ear holes (can-axis X = +-17.5 -- ears along X now)
    for dxe in (-P["motor_ear_cc"] / 2, P["motor_ear_cc"] / 2):
        e = cyl(1.25, 16); e.apply_translation((mx + dxe, my, ear_z - 4))
        body = sub(body, e)
    # ear-bar SEAT PADS: drop the pedestal top ped_relief (0.8) everywhere EXCEPT two pads
    # under the ear ends and the collar's footing annulus -> the 7x1 bar clamps on defined
    # pads (a full 48x48 print-top face rocks on seam blobs; two 9x10 pads don't).
    pw, pd = P["ped_pad_wxy"]
    relief = rounded_box(50, 50, P["ped_relief"], 6.0)      # oversize slab over the ped top
    relief.apply_translation((mx, my, ear_z - P["ped_relief"]))
    for dxe in (-P["motor_ear_cc"] / 2, P["motor_ear_cc"] / 2):
        pad = box(pd, pw, P["ped_relief"] + 2)              # pads rotated with the ear bar
        pad.apply_translation((mx + dxe, my, ear_z - P["ped_relief"] / 2))
        relief = sub(relief, pad)
    keep = cyl(P["ped_collar_od"] / 2 + 0.5, P["ped_relief"] + 2)   # collar keeps footing
    keep.apply_translation((mx, my, ear_z - P["ped_relief"] / 2))
    relief = sub(relief, keep)
    body = sub(body, relief)
    # can-locating COLLAR: Ø32/Ø29 x 1.5 ring on the pedestal top. The Ø29 bore already
    # guides the can below, but its top 1.0 (can top 45.25) + the Ø27.25 gear-stack root
    # get a dedicated register here (0.375/side to the Ø28.25 can, 0.875 to the stack).
    # Notched where the ear bar crosses (|x-mx| < 4.1 vs the 7-wide bar) and over the
    # wiring-relief window on -X so the wbox leads still exit sideways.
    collar = sub(cyl(P["ped_collar_od"] / 2, P["ped_collar_h"]),
                 cyl(29.0 / 2, P["ped_collar_h"] + 2))
    collar.apply_translation((mx, my, ear_z + P["ped_collar_h"] / 2))
    ncut = box(P["ped_collar_od"] + 4, 8.2, P["ped_collar_h"] + 2)  # ear bar crosses in X
    ncut.apply_translation((mx, my, ear_z + P["ped_collar_h"] / 2))
    collar = sub(collar, ncut)
    wcut = box(P["motor_wbox_w"] + 3, 12, P["ped_collar_h"] + 2)    # matches wrel footprint
    wcut.apply_translation((mx, my + 11, ear_z + P["ped_collar_h"] / 2))
    collar = sub(collar, wcut)
    body = uni([body, collar])

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
    for vy in (-112.0, -96.0, 16.0, 32.0, 48.0, 64.0, 96.0):   # y80 -> the 2nd nub
        # side ventilation slots, RE-CLOCKED 2026-07-11 (mid-drive): the TT feature
        # zone moved to y ~ -87..-15 (motor at spr_y -68), so the old row shifted
        # out of it into the now feature-free bands of the 240 tub
        v = box(12, 5, 16); v.apply_translation((0, vy, z0 + h / 2))
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
    zs = _track_zc()                                  # 25.32
    xw = P["chassis_w"] / 2                           # wall outer face (70); inner face 65
    axm = xw - 5.0 - P["tt_gearbox"][2] / 2 - 0.1     # motor axis x
    for ys, o in ((P["spr_y"], 1.0), (P["spr_y2"], -1.0)):
      for s in (-1, 1):
        ph = cyl(4.0, 12, axis="x"); ph.apply_translation((s * (xw - 2.5), ys, zs))
        body = sub(body, ph)                          # Ø8 shaft pass-through (clears Ø7.2 boss)
        rec = cyl(8.5, 2.2, axis="x"); rec.apply_translation((s * (xw - 0.9), ys, zs))
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
        rib = box(69.1 - (axm - 4.0), 6.9, 28.0)
        rib.apply_translation((s * ((axm - 4.0 + 69.1) / 2), ys - o * 15.1, 26.0))
        body = uni([body, rib])
        tabp = box(4.2, 5.7, 6.4); tabp.apply_translation((s * axm, ys - o * 14.15, zs))
        body = sub(body, tabp)                        # front-tab pocket in the rib (1+ skin)
        tabh = cyl(1.4, 14, axis="x"); tabh.apply_translation((s * axm, ys - o * 14.0, zs))
        body = sub(body, tabh)                        # Ø2.8 tab-hole continuation (M2.5 self-tap)
        # (the old wall-mounted idler tension arm/plate/slot was DELETED 2026-07-11:
        # both loop ends now ride Ø8 stubs in DECK-OVERHANG PYLONS -- see
        # build_chassis_parts -- and the front pylons carry the tension slots)
    # --- BODY<->POD JOIN, wall side (rail side is build_pod_rails): per station one M3
    # clearance (M3x12 from inside the cavity, thread-forming into the rail's blind Ø2.5
    # pilot -- no nut, no ordering constraint vs the links) + one Ø4.1 dowel slip hole
    # (Ø4x12 pin pressed on into the rail's blind socket; dowels carry the shear, screws
    # only clamp).
    for s in (-1, 1):
        for jy in P["pod_join_y"]:
            mh = cyl(P["m3_clear_r"], 12, axis="x")
            mh.apply_translation((s * (xw - 2.5), jy, P["pod_join_screw_z"]))
            body = sub(body, mh)
            dh = cyl((P["pod_join_dowel_d"] + 0.1) / 2, 12, axis="x")
            dh.apply_translation((s * (xw - 2.5), jy, P["pod_join_dowel_z"]))
            body = sub(body, dh)
    # --- COSMETIC-FIXING sockets + wire passes in the chassis walls (task #15) ---
    # trim_fascia: 4x Ø3.2 x 2.5 blind sockets in the front wall (at z 50 the solid deck
    # is behind; at z 42 the 2.5 skin faces the cavity)
    for px, pz in P["fascia_pin_pts"]:
        body = sub(body, blind_socket(P["fix_socket_r"], P["fix_socket_deep"],
                                      (0, 1, 0), (px, fw, pz)))
    # trim_rear: 3x Ø3.2 x 2.5 blind sockets in the rear wall
    for px, pz in P["rear_pin_pts"]:
        body = sub(body, blind_socket(P["fix_socket_r"], P["fix_socket_deep"],
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

    # --- PROW CHEEKS (2026-07-11; see PARAMS tub_nose): four blocks x |32..70| extend
    # the tub tub_nose past each wall so the M8 end-axle nut stacks (x 55.5..62,
    # protruding to |y| 135.4 over the corner lamps) hide inside. Per cheek: the
    # glacis plane continued (+nose shift), a PYLON NOTCH (x 61..70.5, z 26.3+; the
    # deck pylons at x 62..69 / z 27.3+ keep 1.0 all around), and an open-top NUT
    # POCKET (x 47..63.5, |y| 119..fwn-3, z 25 up through the flat z 46 top -- the
    # pre-torqued nut descends in as the deck+axle assembly drops on; spec M8 NYLOC,
    # the pocket is clearance, not a wrench flat). Tops cap FLAT at the seam so the
    # cheeks live wholly in chassis_lower; the wedge up to the deck slope stays an
    # open shadow line like the pylon bay. The center band (|x| < 32, clearing the
    # +-30 trim rings) keeps the recessed fascia wall: the cliff cone crosses z 46
    # at y ~131 (probed 2026-07-11), a full-width nose would ping itself.
    nose = P["tub_nose"]
    fwn = fw + nose
    seam_ck = P["chassis_split_z"]
    for sgn in (1, -1):
        for sx in (-1, 1):
            ck = box(38.0, nose + 4.0, seam_ck - z0)
            ck.apply_translation((sx * 51.0, sgn * (fwn - (nose + 4.0) / 2),
                                  z0 + (seam_ck - z0) / 2))
            gwdg = box(60.0, 100.0, 60.0)
            gwdg.apply_transform(R(sgn * ga, (1, 0, 0)))
            gn_ = np.array([0.0, -sgn * np.sin(ga), np.cos(ga)])
            gc_ = np.array([sx * 51.0, sgn * (gy0 + nose), z0g]) - 30.0 * gn_
            gwdg.apply_translation(gc_)
            ck = sub(ck, gwdg)
            nt = box(9.5, nose + 6.0, 25.0)
            nt.apply_translation((sx * 65.75, sgn * (fwn - nose / 2), 26.3 + 12.5))
            ck = sub(ck, nt)
            # nut pocket = NUT CHANNEL + washer slice. The channel's y-walls sit
            # 13.8 apart (nut flats 13 + 0.4/side drop-in slop) centered on the
            # axle y, so the descending nut (flats to +-y) self-captures: torque
            # the bolt from the outboard head, the walls hold the nut -- this is
            # what lets the FRONT tension axles be snugged after the tracks are
            # threaded, with zero tool access to the pocket. The washer slice is
            # wider (Ø14.4 washer + 0.8) and merges into the pylon notch.
            wb2 = P["track_wheelbase"] / 2                     # axle y 128.163
            nutch = box(13.0, 13.8, 24.0)                      # x 47..60
            nutch.apply_translation((sx * 53.5, sgn * wb2, 25.0 + 12.0))
            ck = sub(ck, nutch)
            wsl = box(3.5, 15.2, 24.0)                         # x 60..63.5
            wsl.apply_translation((sx * 61.75, sgn * wb2, 25.0 + 12.0))
            ck = sub(ck, wsl)
            body = uni([body, ck])
    # relocated wall cuts, now through the cheeks:
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
    op_cut.apply_translation((0, 0, 4.0))                    # z 4..13, through the floor
    body = sub(body, op_cut)
    reb_cut = extrude_polygon(reb_poly, P["belly_lip_t"] + 2.0)
    reb_cut.apply_translation((0, 0, z0 + P["belly_lip_t"] - (P["belly_lip_t"] + 2.0)))
    body = sub(body, reb_cut)                                # z 4.5..8.5
    for bx_, by_ in P["belly_screws"]:
        b = cyl(P["belly_boss_r"], P["belly_boss_h"])
        b.apply_translation((bx_, by_, z0 + floor + P["belly_boss_h"] / 2))   # z 12..18
        body = uni([body, b])
        body = sub(body, _belly_csk_neg(bx_, by_))
        pil = cyl(1.25, 8.3); pil.apply_translation((bx_, by_, 9.2 + 8.3 / 2))
        body = sub(body, pil)                                # pilot z 9.2..17.5
    # REAR TIE for the pedestal island (2026-07-10 probe pass): the y 26 sub-split put
    # the belly strap's only anchor in the FRONT tub piece, leaving the pedestal +
    # strap a LOOSE 55 cm3 body inside chassis_lower_rear (pre-existing since the
    # split). A 14-wide bar in the strap's thinned z 8.5..12 band runs from the strap
    # across the belly opening onto the solid floor rim behind it (y -63); the belly
    # PLATE passes beneath in the z 7..8.5 rebate band, so the plate outline is
    # untouched and stays one piece. x -26..-12 clears the tray posts (-38.8..-32.8),
    # the +X zip anchors and the belly screws.
    tie = box(14.0, 39.0, 3.5)
    tie.apply_translation((-19.0, -43.5, 10.25))
    body = uni([body, tie])

    # --- ELECTRONICS SEATS (2026-07-13, Arduino I/O plane; see the PARAMS block
    # for every placement derivation + VERIFY_ON_ARRIVAL markers). Added AFTER the
    # belly cut on purpose: the Uno front post overhangs the opening edge by ~2 at
    # z >= 12, which blocks nothing (plate plug tops at z 10) -- cutting the
    # opening later would instead notch the post.
    # ARDUINO UNO R3: 4 posts to the z-21 seat plane + the rear-wall shelf bar.
    sx0, sy0 = P["ard_org"]
    seat_z = P["ard_seat_z"]
    shx0, shx1, shy0, shy1, shz0 = P["ard_shelf"]
    shelf = box(shx1 - shx0, shy1 - shy0, seat_z - shz0)
    shelf.apply_translation(((shx0 + shx1) / 2, (shy0 + shy1) / 2,
                             (shz0 + seat_z) / 2))
    body = uni([body, shelf])
    for lx_, ly_ in P["ard_holes"]:
        hx_, hy_ = sx0 - lx_, sy0 - ly_              # R180 board-local -> world
        on_shelf = hy_ < shy1 + 2.0
        pb_ = seat_z - 6.0 if on_shelf else z0 + floor
        post = cyl(3.5, seat_z - pb_)
        post.apply_translation((hx_, hy_, (pb_ + seat_z) / 2))
        body = uni([body, post])
        pil = cyl(1.25, 5.5)                         # O2.5 thread-form, blind: stays
        pil.apply_translation((hx_, hy_, seat_z + 0.5 - 2.75))   # inside post/shelf
        body = sub(body, pil)                        # (never the thin floor below)
    # IMU: 2 posts on the strap floor east of the pan pedestal.
    ix_, iy_ = P["imu_c"]
    for sy_ in (-1, 1):
        py_ = iy_ + sy_ * P["imu_hole_cc"] / 2
        post = cyl(3.0, P["imu_seat_z"] - 12.0)
        post.apply_translation((ix_, py_, (12.0 + P["imu_seat_z"]) / 2))
        body = uni([body, post])
        pil = cyl(1.25, 5.5)
        pil.apply_translation((ix_, py_, P["imu_seat_z"] + 0.5 - 2.75))
        body = sub(body, pil)
    # SW-420: hard pad + 1x O2.5 M3 pilot + 2 anti-rotation fence nubs at the far
    # (inboard) end. Pad on full-thickness floor -> the pilot may run 3 into it.
    vx_, vy_ = P["vib_c"]
    vw_, vl_ = P["vib_board_wl"]
    pad = box(vw_ + 2.5, vl_ + 2.5, P["vib_pad_h"])
    pad.apply_translation((vx_, vy_, 12.0 + P["vib_pad_h"] / 2))
    body = uni([body, pad])
    vpz = 12.0 + P["vib_pad_h"]
    vpil = cyl(1.25, P["vib_pad_h"] + 3.0)
    vpil.apply_translation((vx_ + P["vib_hole_off"], vy_,
                            vpz + 0.5 - (P["vib_pad_h"] + 3.0) / 2))
    body = sub(body, vpil)
    for sy_ in (-1, 1):                              # fence nubs hug the free end
        nub = box(2.0, 2.0, P["vib_pad_h"] + 3.0)
        nub.apply_translation((vx_ + vw_ / 2 + 0.3 + 1.0,
                               vy_ + sy_ * (vl_ / 2 - 1.0),
                               12.0 + (P["vib_pad_h"] + 3.0) / 2))
        body = uni([body, nub])
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
    for sx_ in (-1, 1):
        pad = box(18.0, 26.0, 8.0)
        pad.apply_translation((sx_ * 61.0, ysl, 15.0))       # x 52..70, y 13..39, z 11..19
        core = uni([core, pad])

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

        # Lower tub: blind Ø2.5 thread-form pilot from the seam down into the boss.
        pil = cyl(1.25, 8.5)
        pil.apply_translation((sx_, sy_, seam - 8.5 / 2))
        lower = sub(lower, pil)

    # ---- lower tub -> front / rear at y = lower_seam_y ----
    for sx_ in (-1, 1):
        scr = cyl(P["m3_clear_r"], 14.0, axis="y")           # M3x12 through the front pad
        scr.apply_translation((sx_ * 57.0, ysl + 6.0, 15.0))
        lower = sub(lower, scr)
        cbf = cyl(3.4, 4.5, axis="y")                        # head counterbore, front face
        cbf.apply_translation((sx_ * 57.0, ysl + 11.2, 15.0))
        lower = sub(lower, cbf)
        pilr = cyl(1.25, 10.0, axis="y")                     # rear thread-form pilot
        pilr.apply_translation((sx_ * 57.0, ysl - 6.0, 15.0))
        lower = sub(lower, pilr)
        dwl = cyl(2.05, 16.0, axis="y")                      # Ø4 dowel across the seam
        dwl.apply_translation((sx_ * 66.0, ysl, 15.0))       # (+0.1 slip; press the rear
        lower = sub(lower, dwl)                              #  side on assembly with glue)
    lower_f = slice_mesh_plane(lower, plane_normal=(0, 1, 0), plane_origin=(0, ysl, 0), cap=True)
    lower_r = slice_mesh_plane(lower, plane_normal=(0, -1, 0), plane_origin=(0, ysl, 0), cap=True)

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

    # ---- END-IDLER PYLONS (2026-07-11 mid-drive): with the loop ends at |y| 128.16
    # (past the lower tub), each end idler hangs on a Ø8 stub from a PYLON dropping
    # out of the deck overhang's solid wedge at x 62..70 (4 clear of the link plane
    # 74; flush with the deck side). FRONT pylons carry the tension slot (idler
    # slides +-idler_slot/2, M3 set-screw from the nose face); REAR pylons take a
    # blind Ø7.85 press socket. Stub cantilevers 41 to the wheel's outboard face.
    ey_ = P["track_wheelbase"] / 2
    za_ = 34.32                                       # end-axle line (zc + track_raise)
    for sgn2, dpc in ((1, "f"), (-1, "r")):
        dtgt = deck_f if sgn2 > 0 else deck_r
        for sx_ in (-1, 1):
            py = box(8.0, 18.7, 32.7)                  # clipped at |y| 120.5: the tub
            py.apply_translation((sx_ * 66.0, sgn2 * (120.5 + 18.7 / 2),      # wall corner
                                  27.3 + 32.7 / 2))    # z 27.3..60   owns |y| < 120.5
            hb = cyl(7.0, 8.0, axis="x")               # hub boss around the socket
            hb.apply_translation((sx_ * 66.0, sgn2 * ey_, za_))
            dtgt = uni([dtgt, py, hb])
            # END-AXLE FIX (2026-07-11, user: "two wheels per side not connected to
            # anything"): the plain O8 stubs had NO axial retention -- the idlers
            # could walk outboard off them, and the wheels showed bare bearing bores
            # outside. Each end wheel now rides an M8 BOLT-AXLE: head outboard as the
            # hubcap, shank through the F688 pair, NUT on the pylon's inboard face
            # (open air under the overhang, wrench-accessible). FRONT: the through
            # SLOT stays and the nut CLAMPS the slide = tension lock, replacing the
            # old M3 set screw. REAR: through O8.4 clearance hole (was a blind press).
            if sgn2 > 0:                               # front: tension slot, bolt-clamped
                sl = uni([cyl(4.2, 10.0, axis="x"), box(10.0, P["idler_slot"], 8.4)])
                sl.apply_translation((sx_ * 66.0, sgn2 * ey_, za_))
                dtgt = sub(dtgt, sl)
            else:                                      # rear: O8.4 through clearance
                sk = cyl(4.2, 10.0, axis="x")
                sk.apply_translation((sx_ * 66.0, sgn2 * ey_, za_))
                dtgt = sub(dtgt, sk)
        if sgn2 > 0:
            deck_f = dtgt
        else:
            deck_r = dtgt

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
                   (deck_f, "chassis_deck_front"), (deck_c, "chassis_deck_center"),
                   (deck_r, "chassis_deck_rear")):
        _color(m_, "base"); m_.metadata["name"] = nm
        out.append(m_)
    return out


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
    # relief for the chassis' rear pedestal TIE (see build_chassis_core, 2026-07-10):
    # the tie bar crosses the plug and the -X plate-rib runs in the z 8.5..12 band;
    # the plate passes under it on the 1.45 flange alone (0.05 vertical + 0.15
    # lateral clearance; the severed rib segments stay rooted in the plug)
    trel = box(14.3, 39.3, 6.0)
    trel.apply_translation((-19.0, -43.5, 8.45 + 3.0))
    plate = sub(plate, trel)
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


def build_pod_rails():
    """Pod-side receiving rail of the BODY<->POD JOIN (one printed rail per side): two
    nut-trap blocks bridged by a thin spine, standing on the wall's outer face inside the
    link loop. The blocks fill the 4 mm gap (links never enter x 70..74) and reach 4 mm
    into the loop interior, which is link-free between the bottom-run knuckle tops (z 9.5)
    and the top-run knuckle sweep (z 41.14) for |y| <= 40 (the wrap-arc envelopes about
    y=+-60 stay 6+ away); road wheels / idler / sprocket disc all live outboard of x 81.4.
    Each block: a blind Ø2.5 THREAD-FORM pilot for the M3 (self-tap, same convention as
    the belly plate / pan clips / pan-motor ears) + a blind Ø3.85 press socket for the
    Ø4 dowel. Thread-form pass 2026-07-08: the old captive-nut TOP slots opened upward
    and got buried once the links wrapped the pod, forcing rails-before-links ordering
    and a blind nut-drop; a screwed joint that is assembled once doesn't need a nut.
    M3x12 from the cavity wall face (x 65) lands its tip at 77 -> 7 mm of formed thread.
    The spine sits outboard of the vent cutters (x >= 76.2 vs 76) so the three vents it
    crosses stay open into the gap. Print on the outer (+X) face: dowel sockets and the
    pilot become vertical blind holes.

    WHEEL BEAM (2026-07-10 fix, review: the 6 road wheels were mounted to NOTHING, so
    the robot's weight went to ground through the TT gearbox shaft + the idler stub):
    each rail carries a beam at x 74..80.4 / z 14..26 / y +-74.5, fused to both join
    blocks, living in the loop's link-free band (bottom-run knuckle tops 9.5, top-run
    sweep 41.14, ramp links start |y| 72.5, sprocket hub tube crosses above at z 28.3).
    Per wheel: an M4 x 40 bolt-axle from outboard (head = hubcap on the wheel face,
    prefer partially threaded so the Ø4.2 wheel bore rides shank, not thread) through
    a Ø4.4 beam bore into an M4 nut in a slide-up slot from the beam's bottom face --
    the nut is captive sideways/axially, inserted before the rail mounts. Beam outer
    face 80.4 leaves 1.0 running gap to the wheel inner face (81.4); the join-dowel
    socket just gains web depth (blind end 77.0 -> 3.4 web). BUY 12x M4x40 + nuts.
    Print orientation update: the beam's outer face is the new bed plane (proud 2.4 of
    the blocks); shim/support the two 9-wide block bands above z 26, nut slots print
    as side openings, all bores stay vertical."""
    x0 = P["chassis_w"] / 2                            # wall outer face (70): rail sits flush
    x1 = P["pod_rail_x1"]                              # 78
    z_lo, z_hi = P["pod_rail_z"]
    bw = P["pod_rail_block_w"]
    rr_z = (_track_zc() - P["track_wheel_r"]) + 3.5 + P["roadwheel_d"] / 2 + 0.1
    rails = []
    for s, nm in ((-1, "pod_rail_L"), (1, "pod_rail_R")):
        parts = []
        for jy in P["pod_join_y"]:
            b = box(x1 - x0, bw, z_hi - z_lo)
            b.apply_translation((s * (x0 + x1) / 2, jy, (z_lo + z_hi) / 2))
            parts.append(b)
        # spine bridging the blocks: z 30..40 (nut-slot zone), 1.8 thick at x 76.2..78 --
        # clear of the vent cutters (they reach x 76) so the vents still breathe
        spine = box(1.8, P["pod_join_y"][1] - P["pod_join_y"][0] + bw, 10.0)
        spine.apply_translation((s * (76.2 + 78.0) / 2, 0, 35.0))
        beam = box(6.4, 172.0, 12.0)                   # wheel beam x 74..80.4, y +-86
        beam.apply_translation((s * 77.2, 0, 20.0))    # (mid-drive 2026-07-11: stations
        # to +-80.5 + nut-slot margin; ramp links leave the ground at +-120)
        rail = uni(parts + [spine, beam])
        for sy_ in (P["spr_y"], P["spr_y2"]):          # Ø13.5 notches: both drive
            hn = cyl(6.75, 10.0, axis="x")             # sprockets' hub tubes (Ø12)
            hn.apply_translation((s * 77.2, sy_, _track_zc()))   # cross the beam
            rail = sub(rail, hn)
        for ry in P["roadwheel_ys"]:
            ab = cyl(2.2, 9.0, axis="x")               # Ø4.4 M4 clearance bore
            ab.apply_translation((s * 77.2, ry, rr_z))
            rail = sub(rail, ab)
            slot = box(3.6, 7.3, 10.15)                # M4 nut slide-up slot (AF 7.0 +
            slot.apply_translation((s * 75.7, ry, 18.575))  # 0.3, corners up/down):
            rail = sub(rail, slot)                     # z 13.5..23.65 -- the top stop
            # parks the nut's upper corner so screwing pulls it centred on the bore
        for jy in P["pod_join_y"]:
            # blind Ø2.5 thread-form pilot from the inner face (x 69.4 overshoot) to
            # x 77.4 -> 0.6 web to the outer face, 7 mm of engagement for an M3x12
            # (tip lands at 77.0: 0.4 bottoming margin, review nit -- was zero)
            mb = cyl(1.25, 8.0, axis="x")
            mb.apply_translation((s * (69.4 + 77.4) / 2, jy, P["pod_join_screw_z"]))
            rail = sub(rail, mb)
            # blind dowel press socket: Ø3.85 from the inner face (x 69.4 overshoot) to
            # x 77.0 -> 1.0 web to the outer face
            ds = cyl((P["pod_join_dowel_d"] - 0.15) / 2, 7.6, axis="x")
            ds.apply_translation((s * (69.4 + 77.0) / 2, jy, P["pod_join_dowel_z"]))
            rail = sub(rail, ds)
        _color(rail, "base")
        rail.metadata["name"] = nm
        rail.metadata["export"] = f"track_{nm}.stl"    # track_* -> stl/base/ via stlpaths
        rails.append(rail)
    return rails




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
    vz_ = 12.0 + P["vib_pad_h"] + 0.05
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

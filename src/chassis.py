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
from geo import (_color, _orient, blind_socket, box, cyl,
    fix_pin, frustum, hex_prism, rounded_box, sub,
    uni)
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
    fins = [ring]
    for sx in (-1, 1):
        # backing web per side, tying the fin bases to the ring: the fins (x 33.5..48.5)
        # never touched the +-30 ring band -> trim_fascia split into 7 loose bodies
        # (PRINTABILITY 2). 1.2 thick against the wall, hidden behind the 2-proud fins;
        # spans x 28..49.5 so it overlaps the ring band.
        web = box(21.5, 1.2, 16.0)
        web.apply_translation((sx * 38.75, fw + 0.6, P["grille_cz"]))
        fins.append(web)
        for fx in (35.0, 41.0, 47.0):
            f = box(3.0, 2.0, 16.0)
            f.apply_translation((sx * fx, fw + 1.0, P["grille_cz"]))
            fins.append(f)
    fascia = uni(fins)
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
    # amber indicator lamps at the fascia corners
    for sx, nm in ((-1, "lamp_L"), (1, "lamp_R")):
        l = rounded_box(12.0, 7.0, 2.0, 2.5)
        l.apply_transform(R(-TAU / 4, (1, 0, 0)))
        l.apply_translation((sx * P["lamp_x"], fw, P["lamp_cz"]))
        _color(l, "lamp"); l.metadata["name"] = nm
        parts.append(l)
    # white LED dot strip at the bottom lip: slim base + 7 round emitters. Base 1.2 (was
    # 1.0, handling-fragile -- PRINTABILITY 6/7); the dots ride +0.2 with the base front
    # so their 1.2 proud height over it is unchanged.
    fl = [box(36.0, 1.2, 3.0).apply_translation((0, fw + 0.6, P["fled_cz"]))]
    for i in range(7):
        d = cyl(1.3, 1.6, axis="y", sections=24)
        d.apply_translation((-15.0 + i * 5.0, fw + 1.6, P["fled_cz"]))
        fl.append(d)
    led = uni(fl)
    _color(led, "led"); led.metadata["name"] = "led_front"
    parts.append(led)
    # REAR: orange frame panel (wall shows through as the hatch) + silver cylinder pod
    rp = sub(rounded_box(72.0, 22.0, 2.5, 6.0),
             box(44.0, 14.0, 8.0))
    rp.apply_transform(R(TAU / 4, (1, 0, 0)))        # extrude -Y (proud of the REAR face)
    rp.apply_translation((0, -fw, P["rear_panel_cz"]))
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
    flange = cyl(P["rearpod_flange_r"], P["rearpod_flange_t"], axis="y", sections=48)
    flange.apply_translation((rcx, -fw - P["rearpod_flange_t"] / 2, rcz))
    pod_l = 9.0 - P["rearpod_flange_t"]              # overall proud height stays 9.0
    pod = cyl(P["rear_cyl_d"] / 2, pod_l, axis="y", sections=48)
    pod.apply_translation((rcx, -fw - P["rearpod_flange_t"] - pod_l / 2, rcz))
    rcp = [flange, pod]
    for sxp in (-1, 1):
        rcp.append(fix_pin(P["fix_pin2_r"], P["fix_pin_len"], (0, 1, 0),
                           (rcx + sxp * P["rearpod_pin_dx"], -fw, rcz)))
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
    zsh = z1 - 2 - (P["motor_body_h"] + P["motor_gear_h"] + P["motor_shaft_len"])   # can bottom
    ear_z = zsh + P["motor_body_h"] - 1.0            # ear-bar underside (30.25)
    ped = rounded_box(48, 48, ear_z - (z0 + floor), 6.0)
    ped.apply_translation((mx, 0, z0 + floor))
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
    # ear-bar SEAT PADS: drop the pedestal top ped_relief (0.8) everywhere EXCEPT two pads
    # under the ear ends and the collar's footing annulus -> the 7x1 bar clamps on defined
    # pads (a full 48x48 print-top face rocks on seam blobs; two 9x10 pads don't).
    pw, pd = P["ped_pad_wxy"]
    relief = rounded_box(50, 50, P["ped_relief"], 6.0)      # oversize slab over the ped top
    relief.apply_translation((mx, 0, ear_z - P["ped_relief"]))
    for dy in (-P["motor_ear_cc"] / 2, P["motor_ear_cc"] / 2):
        pad = box(pw, pd, P["ped_relief"] + 2)
        pad.apply_translation((mx, dy, ear_z - P["ped_relief"] / 2))
        relief = sub(relief, pad)
    keep = cyl(P["ped_collar_od"] / 2 + 0.5, P["ped_relief"] + 2)   # collar keeps footing
    keep.apply_translation((mx, 0, ear_z - P["ped_relief"] / 2))
    relief = sub(relief, keep)
    body = sub(body, relief)
    # can-locating COLLAR: Ø32/Ø29 x 1.5 ring on the pedestal top. The Ø29 bore already
    # guides the can below, but its top 1.0 (can top 45.25) + the Ø27.25 gear-stack root
    # get a dedicated register here (0.375/side to the Ø28.25 can, 0.875 to the stack).
    # Notched where the ear bar crosses (|x-mx| < 4.1 vs the 7-wide bar) and over the
    # wiring-relief window on -X so the wbox leads still exit sideways.
    collar = sub(cyl(P["ped_collar_od"] / 2, P["ped_collar_h"]),
                 cyl(29.0 / 2, P["ped_collar_h"] + 2))
    collar.apply_translation((mx, 0, ear_z + P["ped_collar_h"] / 2))
    ncut = box(8.2, P["ped_collar_od"] + 4, P["ped_collar_h"] + 2)
    ncut.apply_translation((mx, 0, ear_z + P["ped_collar_h"] / 2))
    collar = sub(collar, ncut)
    wcut = box(12, P["motor_wbox_w"] + 3, P["ped_collar_h"] + 2)    # matches wrel footprint
    wcut.apply_translation((mx - 11, 0, ear_z + P["ped_collar_h"] / 2))
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
    usb.apply_translation((0, -P["chassis_l"] / 2, z0 + 12)); body = sub(body, usb)
    # PD-trigger mount (wiring pass 2026-07-08): 2x Ø1.7 M2 self-tap pilots in the rear
    # wall's interior face flanking the USB slot -- the trigger/breakout board hangs on
    # the wall with its jack aligned to the slot. Plus 2x Ø3.2 zip anchors through the
    # floor rim behind the belly opening: the incoming wall cable zip-ties down before
    # the jack, so a yanked cable loads the tie, not the board (the robot WILL drag its
    # own tether eventually).
    for sxp in (-1, 1):
        pd = cyl(0.85, 4.0, axis="y")
        pd.apply_translation((sxp * 9.0, -P["chassis_l"] / 2 + 5 - 1.9, z0 + 12))
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
            # 30 deg about the hex's own axis (now Y): FLAT-top hexes. Vertex-facing-X
            # hexes narrowed the web at the 4.2 pitch to 0.74 slivers between vertex
            # tips; flats +-X give a uniform 4.2-3.0 = 1.2 web AND a 60 deg self-
            # supporting pocket roof instead of a 3.0 flat bridge (PRINTABILITY 5).
            hx.apply_transform(R(TAU / 12, (0, 1, 0)))
            hx.apply_translation((hx_x, fw - 0.5, zr))         # cuts 2.5 into the 5 wall
            hexes.append(hx)
    body = sub(body, uni(hexes))
    for sx in (-1, 1):
        us = cyl(P["us_d"] / 2 + 0.3, 12, axis="y")
        us.apply_translation((sx * P["us_dx"], fw - 2.5, P["us_cz"]))
        body = sub(body, us)
    for i in range(-3, 5):                            # side ventilation slots (extended
        v = box(12, 5, 16); v.apply_translation((0, i * 16, z0 + h / 2))    # +-48/64 with the
        v2 = v.copy(); v.apply_translation((P["chassis_w"] / 2, 0, 0))      # 200 chassis; the
        v2.apply_translation((-P["chassis_w"] / 2, 0, 0))                   # TT wall zone is
        body = sub(sub(body, v), v2)                                        # now y -92..-55

    # --- TT drive-motor mount (both walls; see motor_tt + reference/tt-motor-1079893/NOTES.md).
    # Shaft axis at (y=-wb/2, z=_track_zc()+track_raise): the raised tank loop lifts the
    # sprocket (and so the motor) by track_raise; gearbox face 0.1 inside the wall inner face.
    zs, ys = _track_zc() + P["track_raise"], -P["track_wheelbase"] / 2   # 34.32, -58.16
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
        # pocket over the motor: the raised gearbox/can top is at z 45.52 (zs 34.32 + 11.2)
        # but the cavity ceiling is 32 -- cut to 45.8, still under the z46 deck seam (the
        # pan-seat floor plane and the race ring footprint r34..46 stay clear: nearest
        # pocket corner is at r 50.2)
        dkp = box(19.4, 64.7, 13.9); dkp.apply_translation((s * (xw - 14.5), ys + 20.35, 38.85))
        body = sub(body, dkp)
        # cavity-corner relief: the cavity's r12 rounded corner leaves body material where the
        # rectangular gearbox rear corner sits -- square it off locally (spans old + raised z)
        crn = box(7.0, 14.2, 33.9); crn.apply_translation((s * (xw - 8.4), ys - 5.1, 28.85))
        body = sub(body, crn)
        tabp = box(4.2, 5.7, 6.4); tabp.apply_translation((s * axm, ys - 14.15, zs))
        body = sub(body, tabp)                        # front-tab pocket in the rear wall (1 skin)
        tabh = cyl(1.4, 14, axis="x"); tabh.apply_translation((s * axm, ys - 14.0, zs))
        body = sub(body, tabh)                        # Ø2.8 tab-hole continuation (M2.5 self-tap)
        # idler tension arm: wall -> slotted plate inside the front loop arc (radial < 15.7 so
        # the wrapping links clear it); Ø8 stub axle (hardware) slides +-idler_slot/2 in the
        # obround, M3 set-screw lock. Plate stops 0.1 inboard of the idler face.
        cxp = xw + P["track_gap"] + P["track_width"] / 2          # pod centre (96.4)
        # arm runs wall (x 69, 1.0 buried) -> 1.1 INTO the plate front face at 85.3: the
        # chassis_w 140 widening left the old 7.9-long arm ending at x 76.9, 8.4 short of
        # its plate, so the two plates floated as loose bodies (PRINTABILITY 8 / fix 5).
        # Y-Z section unchanged: radial max 10.8 from the idler axis < 15.7, wrapping
        # links still clear; the tension slot below cuts the arm's outer end too (fine --
        # the Ø8 stub axle needs the passage).
        arm = box(17.4, 16, 14.6); arm.apply_translation((s * (69.0 + 17.4 / 2), -ys, zs - 0.36))
        plate = cyl(14.0, 2.0, axis="x"); plate.apply_translation((s * (cxp - 9.0 - 0.1 - 1.0), -ys, zs))
        body = uni([body, arm, plate])
        slot = uni([cyl(4.1, 6, axis="x"), box(6, P["idler_slot"], 8.2)])
        slot.apply_translation((s * (cxp - 9.0 - 0.1 - 1.0), -ys, zs))
        body = sub(body, slot)
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
    # lamp_L/R: Ø2.5 wire pass through the front wall behind each lamp window
    for s in (-1, 1):
        wl = cyl(P["wire_pass_r"], 7.0, axis="y")
        wl.apply_translation((s * P["lamp_x"], fw - 2.5, P["lamp_cz"]))
        body = sub(body, wl)
    # led_front: the strip (z 8..11) sits against the FLOOR band (z 7..12), so a straight
    # wire pass would dead-end in the floor slab -- angle it up-inward from behind the
    # strip base into the cavity (axis (10, 79, 9) -> (10, 70, 14.5); exit z 12.7+ at the
    # inner face y 73, staying 0.65+ under the HC-SR04 board bottom at z 15.55)
    wf = cyl(P["wire_pass_r"], 11.5)
    _orient(wf, (0, -9.0, 5.5))
    wf.apply_translation((10.0, fw - 3.5, 11.75))
    body = sub(body, wf)
    # sensor_rear: Ø10 sound/wire through-hole + 2x Ø2.2 x 2.5 blind cap-pin sockets
    # (0.9 web between the bore and each socket; see PARAMS rearpod_*)
    sh_ = cyl(P["rearpod_hole_r"], 7.0, axis="y")
    sh_.apply_translation((P["rear_cyl_x"], -fw + 2.5, P["rear_cyl_cz"]))
    body = sub(body, sh_)
    for sxp in (-1, 1):
        body = sub(body, blind_socket(P["fix_socket2_r"], P["fix_socket_deep"], (0, -1, 0),
                                      (P["rear_cyl_x"] + sxp * P["rearpod_pin_dx"], -fw,
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
    _color(body, "base")
    body.metadata["name"] = "chassis"
    return body


def build_chassis_parts():
    """Printable chassis split: lower open tub + removable upper pan deck.

    The old `chassis.stl` combined deep internal posts, side motor mounts, idler arms,
    front/rear cosmetics sockets, the pan seat, and the underside access opening into one
    awkward print. This keeps the same assembled geometry but inserts a horizontal service
    seam at `chassis_split_z`: lower tub prints open-top, upper deck prints as a shallow
    removable plate. M3 screws come down from the deck into lower thread-form pilots."""
    from trimesh.intersections import slice_mesh_plane

    z0 = P["chassis_clear"]
    z1 = P["base_h"]
    seam = P["chassis_split_z"]
    core = build_chassis_core()

    # Screw bosses span the seam before slicing, so both halves get matching local pads.
    boss_bot = seam - 9.0
    boss_top = seam + 12.0
    for sx_, sy_ in P["chassis_split_screws"]:
        boss = cyl(P["chassis_split_boss_r"], boss_top - boss_bot)
        boss.apply_translation((sx_, sy_, (boss_bot + boss_top) / 2))
        core = uni([core, boss])

    lower = slice_mesh_plane(core, plane_normal=(0, 0, -1), plane_origin=(0, 0, seam), cap=True)
    deck = slice_mesh_plane(core, plane_normal=(0, 0, 1), plane_origin=(0, 0, seam), cap=True)

    for sx_, sy_ in P["chassis_split_screws"]:
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

    _color(lower, "base"); lower.metadata["name"] = "chassis_lower"
    _color(deck, "base"); deck.metadata["name"] = "chassis_deck"
    return lower, deck


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
    pilot become vertical blind holes."""
    x0 = P["chassis_w"] / 2                            # wall outer face (70): rail sits flush
    x1 = P["pod_rail_x1"]                              # 78
    z_lo, z_hi = P["pod_rail_z"]
    bw = P["pod_rail_block_w"]
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
        rail = uni(parts + [spine])
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



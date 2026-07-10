"""Track pods: raised tank loop, links, master link, sprocket, wheels.

Split out of the original monolithic build.py (2026-07-10); see
build.py for the assembly entry point and the overall design notes.
"""
import numpy as np
import shapely.geometry as sg
import trimesh
from trimesh.creation import extrude_polygon
from trimesh.transformations import rotation_matrix as R
from params import P, TAU
from geo import R_x, _color, box, cyl, inter, sub, uni


def _track_link_poses(wb, R, zc, n):
    """(y, z, angle) for n link pads walked around the RAISED TANK LOOP in the Y-Z plane
    (2026-07-10, RC-tank chassis refs; was a flat stadium). Flat ground run at pin z=zc-R
    between +-track_ground_hy, ~33 deg ramps up to the raised sprocket/idler pin circles
    (axles at zc + track_raise), ~147 deg end wraps, flat top run at z = axle + R.
    Pad angle = walking-direction angle (outward normal = (sin a, -cos a)), continuous at
    every tangency. track_wheelbase is pre-solved so the perimeter closes at n * pitch."""
    za = zc + P["track_raise"]
    g = P["track_ground_hy"]
    zg = zc - R
    ci = np.array([wb / 2, za])                       # front (idler) pin-circle center
    v = np.array([g, zg]) - ci                        # hull tangent from the ground exit
    d = float(np.hypot(v[0], v[1]))
    beta = float(np.arccos(R / d))
    acb = float(np.arctan2(v[1], v[0]))               # center -> ground-point direction
    tp = None
    for s_ in (1.0, -1.0):                            # pick the rising, below-axle touch
        cand = ci + R * np.array([np.cos(acb + s_ * beta), np.sin(acb + s_ * beta)])
        dv = cand - np.array([g, zg])
        if dv[0] > 0 and dv[1] > 0 and cand[1] < za:
            tp = cand
            ramp_len = float(np.hypot(dv[0], dv[1]))
            ramp_ang = float(np.arctan2(dv[1], dv[0]))
    phi = float(np.arctan2(tp[1] - ci[1], tp[0] - ci[0]))   # touch angle on the circle
    wrap = (np.pi / 2 - phi) % TAU                    # touch -> top point, CCW
    segs = (2 * g, ramp_len, wrap * R, wb, wrap * R, ramp_len)
    perim = sum(segs)
    assert abs(perim - n * P["track_pitch"]) < 0.15, \
        "track loop perimeter %.3f != %d x %.1f -- re-solve track_wheelbase" \
        % (perim, n, P["track_pitch"])
    poses = []
    for i in range(n):
        s = perim * i / n
        if s < segs[0]:                                # ground run, +Y
            poses.append((-g + s, zg, 0.0)); continue
        s -= segs[0]
        if s < segs[1]:                                # front ramp, rising forward
            poses.append((g + s * np.cos(ramp_ang), zg + s * np.sin(ramp_ang), ramp_ang))
            continue
        s -= segs[1]
        if s < segs[2]:                                # idler wrap: touch -> top, CCW
            a = phi + s / R
            poses.append((ci[0] + R * np.cos(a), ci[1] + R * np.sin(a), a + np.pi / 2))
            continue
        s -= segs[2]
        if s < segs[3]:                                # top run, -Y
            poses.append((wb / 2 - s, za + R, np.pi)); continue
        s -= segs[3]
        if s < segs[4]:                                # sprocket wrap: top -> rear touch
            a = np.pi / 2 + s / R                      # CCW on the rear circle
            poses.append((-wb / 2 + R * np.cos(a), za + R * np.sin(a), a + np.pi / 2))
            continue
        s -= segs[4]                                   # rear ramp: falls FORWARD from the
        y0, z0_ = -tp[0], tp[1]                        # rear touch down to the ground start
        poses.append((y0 + s * np.cos(-ramp_ang),
                      z0_ + s * np.sin(-ramp_ang), TAU - ramp_ang))
    return poses


def _track_zc():
    """Wheel-center height so the bottom-run GROUSER face is the ground line (z=0):
    pin circle R + pin-to-pad-outer-face + grouser."""
    return P["track_wheel_r"] + P["track_pad_th"] + P["track_grouser_h"]


# Link knuckle X-comb (half-width 14): near set A (outer pair) interleaves the neighbour's far
# set B (inner pair) around the shared pin; the central +-4.9 stays OPEN so the sprocket teeth
# sweep between the B knuckles and engage the (unmodelled Ø1.75 filament) pins.
# near set A (outer pair) runs from x=9.4 out to the link edge (tw/2, width-derived);
# far set B (inner pair) is fixed so the sprocket channel (+-4.9) never changes.
def _KNUCKLES(tw):
    return (((-tw / 2, -9.4), (9.4, tw / 2)),          # A: near knuckles (own pin)
            ((-8.9, -4.9), (4.9, 8.9)))                # B: far knuckles (next pin)


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
    ka, kb = _KNUCKLES(tw)
    for (x0, x1) in ka:                                # near knuckles (own pin) + bridge to web
        k = cyl(kr, x1 - x0, axis="x"); k.apply_translation(((x0 + x1) / 2, 0, 0)); parts.append(k)
        b = box(x1 - x0, 3.1, 2.7); b.apply_translation(((x0 + x1) / 2, 2.05, -3.15)); parts.append(b)
    for (x0, x1) in kb:                                # far knuckles (next pin) + bridge to web
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


def _track_master_link():
    """MASTER LINK (maintenance pass 2026-07-08): closes the loop with a drop-on jaw instead
    of flexing the last two links together under tension (the old worst-per-pod step), and
    makes track removal a 2-screw job. Geometry = a normal link, except the OWN-pin (y=0)
    A knuckles become open C-JAWS: a 2.0-wide slot from the bore's lower half out through
    the outer face and the side faces. Closing: the master's y=pitch end is pinned to its
    neighbour normally ON THE BENCH; after wrapping, the loop's last pin sits in the other
    neighbour's B knuckles and the master SWINGS down onto it (idler retracted for slack).
    Two printed KEEPER bars then slide into the jaw slot from the side faces -- each locked
    by one M2 self-tap into a side-face pilot -- and seat the pin: belt tension is carried
    by the jaw walls (same section as a plain bore), the keepers only block pin drop-out.
    Returns (body, [keeper_L_local, keeper_R_local]) in link-local coords."""
    pitch, tw = P["track_pitch"], P["track_width"]
    body = _track_link()
    ka, _ = _KNUCKLES(tw)
    # keeper-screw BOSSES first, then the jaw slots re-cut THROUGH them, then the pilots.
    # Printability review: the bare pilot at y 2.2 broke out of the knuckle (edge 3.05 >
    # chord 2.94) leaving <0.4 walls -- the Ø4.5 boss restores thread stock. Review round
    # 2: a full-cylinder boss refilled the slot where the keeper bar rides, so the slot
    # is subtracted AFTER the boss union (boss becomes a C around the slot) and the
    # pilot moved to y 2.6 so its edge keeps 0.75 to the slot wall. Boss fuses into the
    # knuckle + web corner, stays above ground (low -4.15 > -6), x-clear of the
    # neighbour's B knuckles (which end at x 8.9).
    for (x0, x1) in ka:
        sxs = 1 if x1 > 0 else -1
        bs = cyl(2.25, 7.0, axis="x")
        bs.apply_translation((sxs * (tw / 2 - 3.5), 2.6, -1.9))
        body = uni([body, bs])
    for (x0, x1) in ka:                                # jaw slots through both A knuckles,
        s = box((x1 - x0) + 1.2, 2.0, 7.0)             # open out the side faces (+0.6/end)
        s.apply_translation(((x0 + x1) / 2, 0, -4.4))  # z -7.9..-0.9: bore keeps its top arc
        body = sub(body, s)
        sxs = 1 if x1 > 0 else -1
        pil = cyl(0.85, 7.0, axis="x")
        pil.apply_translation((sxs * (tw / 2 - 3.5), 2.6, -1.9))
        body = sub(body, pil)
    keepers = []
    for sxs in (-1, 1):
        bar = box(13.3, 1.9, 2.2)                      # rides the slot walls, top face -0.95
        bar.apply_translation((sxs * (9.7 + 23.0) / 2, 0, -0.95 - 1.1))    # seats the pin;
        tab = box(2.6, 5.5, 5.5)                       # outboard end fuses into the tab.
        tab.apply_translation((sxs * (tw / 2 + 0.05 + 1.3), 2.6, -1.9))    # Tab centered on
        k = uni([bar, tab])                            # the M2 at y 2.6 (reviews: the old
        # 1.8x7x4 tab left 0.65-0.85 hole ligaments AND let the M2 head stand 0.55-0.85
        # off the chassis wall on the top run; 2.6 thick x 5.5 + a head counterbore gives
        # >=1.5 walls and sinks the head to >=1.1 wall clearance. Tab y -0.15..5.35 keeps
        # 1.15 to the next link's knuckle side faces on the straight run.
        mc = cyl(1.15, 6.0, axis="x")                  # M2 clearance through the tab
        mc.apply_translation((sxs * (tw / 2 + 1.3), 2.6, -1.9))
        k = sub(k, mc)
        cb = cyl(2.1, 1.5, axis="x")                   # Ø4.2 head counterbore, outer face
        cb.apply_translation((sxs * (tw / 2 + 0.05 + 2.6 - 0.7), 2.6, -1.9))
        k = sub(k, cb)
        keepers.append(k)
    return body, keepers


def _sprocket_disc(width):
    """Pin-pocket sprocket disc (2026-07-10 fix): sprocket_teeth circular pin seats on
    the track_wheel_r pin circle cut into a sprocket_outer_d/2 blank. Replaces the
    placeholder gear_disc trapezoid teeth, whose radial engagement with the pins was
    only ~0.36 (tip 18.8 vs pin underside 18.445 at pin circle 19.32) on top of the
    2.0-bore/1.75-pin slop -- a recipe for tooth-skip under stall torque. Seat r 1.15 =
    pin 0.875 + 0.275 running clearance; the seat floor sits at r 18.17 so the seat
    WRAPS the pin (0.63 radial bite), and the seat mouth at the rim opens 2.05 > the
    Ø1.75 pin, so pins drop in/out freely as the links articulate onto the polygon.
    Phase on the TT shaft is free (D-socket clocks 2 ways, pins self-seat on tension)."""
    blank = sg.Point(0, 0).buffer(P["sprocket_outer_d"] / 2, resolution=64)
    rp = P["track_wheel_r"]
    for k in range(P["sprocket_teeth"]):
        a = TAU * k / P["sprocket_teeth"]
        blank = blank.difference(
            sg.Point(rp * np.cos(a), rp * np.sin(a)).buffer(1.15, resolution=32))
    disc = extrude_polygon(blank, width)
    disc.apply_translation((0, 0, -width / 2))
    disc.apply_transform(R(TAU / 4, (0, 1, 0)))        # extrusion z -> the X axle axis
    return disc


def _sprocket(sx):
    """Drive sprocket + inboard hub tube reaching the TT shaft through the chassis-wall web.
    Disc (tip r 18.8, real pin pockets -- see _sprocket_disc) at the pod centre (96.4 at
    chassis_w 140 / tw 44.8; hub local -28.1 --
    values are chassis_w/track_width-derived); hub OD12 runs inboard to where the D-socket
    (bore Ø5.65, flat gap 3.85 print clearance, 8.0 deep = TT flat length) grips the shaft flats.
    Outer face: Ø9 x 1.5 counterbore for the M2 retaining screw + washer into the shaft tip's
    Ø2 axial hole. Built for the +X pod, spun 180deg about Z for -X."""
    tw = P["track_width"]
    cx = P["chassis_w"] / 2 + P["track_gap"] + tw / 2              # pod centre (96.4)
    hub_in = (P["chassis_w"] / 2 - 2.0 + 0.3) - cx                 # world 68.3 -> local -28.1
    # band pinned to 8 (the links' open +-4.9 sprocket channel), NOT tw-derived
    spr = _sprocket_disc(8.0)
    hub = cyl(6.0, -hub_in - 3.5, axis="x")                        # corners to the 18.8 tip circle
    hub.apply_translation(((hub_in - 3.5) / 2, 0, 0))
    spr = uni([spr, hub])
    dd = inter(cyl((P["tt_shaft_d"] + 0.25) / 2, 8.6, axis="x"),   # TT double-D socket
               box(8.8, 8, 3.70 + 0.15))
    dd.apply_translation((hub_in + 4.1, 0, 0))                     # face-0.2 .. face+8.4
    spr = sub(spr, dd)
    bore = cyl(3.0, 16.0, axis="x"); bore.apply_translation((-3.3, 0, 0))
    spr = sub(spr, bore)                                           # Ø6 free bore to the outer face
    cb = cyl(4.5, 1.7, axis="x"); cb.apply_translation((3.25, 0, 0))       # band_half - 0.75
    spr = sub(spr, cb)                                             # retaining-screw counterbore
    for k in range(6):                                 # lightening-hole ring (tank-ref
        aa = TAU * k / 6                               # spoked sprocket look): 6x Ø4.6
        lh = cyl(2.3, 12.0, axis="x")                  # through the web at r 11.5,
        lh.apply_translation((0, 11.5 * np.cos(aa), 11.5 * np.sin(aa)))
        spr = sub(spr, lh)                             # between hub (r6) and tooth roots
    if sx < 0:
        spr.apply_transform(R(TAU / 2, (0, 0, 1)))
    return spr


def build_tracks():
    """Two positive-drive track pods: 45 articulated links (Ø1.75 filament hinge pins) wrapping a
    12T pin-pocket sprocket (rear, TT double-D hub) + idler on TWO F688ZZ flanged bearings
    (front, tensioned via the chassis-arm slot) + road wheels riding the knuckle crowns on
    M4 bolt-axles off the pod-rail wheel beam (build_pod_rails). Bottom-run grouser face =
    ground (z=0). Each pod is a concatenation of separate printed pieces, not one solid."""
    R, tw, wb = P["track_wheel_r"], P["track_width"], P["track_wheelbase"]
    zc = _track_zc()
    kr = 3.5
    plain = _track_link()
    mbody, mkeepers = _track_master_link()             # link 0 = the loop-closing master
    out = []
    for sx in (-1, 1):
        cx = sx * (P["chassis_w"] / 2 + P["track_gap"] + tw / 2)
        pieces = []
        keeper_pieces = []
        for i, (y, z, ang) in enumerate(_track_link_poses(wb, R, zc, P["track_links"])):
            lk = (mbody if i == 0 else plain).copy()   # master seam on the bottom straight run
            lk.apply_transform(R_x(ang))               # tangent to the loop, outer face outward
            lk.apply_translation((cx, y, z))
            pieces.append(lk)
            if i == 0:
                for k in mkeepers:
                    kk = k.copy()
                    kk.apply_transform(R_x(ang))
                    kk.apply_translation((cx, y, z))
                    keeper_pieces.append(kk)
        za = zc + P["track_raise"]                     # raised axle line (tank-ref loop)
        wheel_pieces = []
        spr = _sprocket(sx)
        spr.apply_translation((cx, -wb / 2, za)); wheel_pieces.append(spr)
        # idler (front): rides the knuckle crowns (r 15.82) with 0.12 running clearance; TWO
        # F688ZZ bearings (2026-07-10 fix: one 5-wide bearing at the inboard face let the
        # 30-wide wheel tilt/wander on its Ø8 stub) in the Ø15.95 through-bore, one pressed
        # at EACH face with its Ø18 flange in a Ø18.5 x 1.0 recess; the Ø8 stub axle
        # (hardware) cantilevers from the chassis tension-slot plate. BUY 4x F688ZZ (was 2).
        ir, iw = R - kr - 0.12, 30.0                   # widened with the 45-link stretch
        idl = sub(cyl(ir, iw, axis="x"), cyl(P["idler_bore_d"] / 2, iw + 2, axis="x"))
        for bs_ in (-1, 1):
            fr = cyl(18.5 / 2, 1.05, axis="x")
            fr.apply_translation((bs_ * (iw / 2 - 0.5), 0, 0))
            idl = sub(idl, fr)
        # dished faces (tank-ref look): shallow annulus recess between the bore boss and rim
        for fs in (-1, 1):
            dsh = sub(cyl(ir - 2.6, 2.0, axis="x"), cyl(11.0, 3.0, axis="x"))
            dsh.apply_translation((fs * (iw / 2 - 0.9), 0, 0))
            idl = sub(idl, dsh)
        # 30-wide idler grows OUTBOARD only: inner face stays at |cx|-9, 0.1 clear of
        # the chassis tension plate (symmetric growth swallowed the plate, 830 mm3)
        idl.apply_translation((cx + sx * 6.0, wb / 2, za)); wheel_pieces.append(idl)
        # road wheels (tank-ref style): dense dished row riding the bottom-run knuckle
        # crowns (0.1 running clearance). Rim ring + recessed dish + raised hub with a
        # 5-hole bolt circle on each face; Ø4.2 center bore = slip fit on the M4 x 40
        # bolt-axle (2026-07-10 fix: the wheels were mounted to NOTHING -- weight went
        # to ground through the TT gearbox shaft + idler stub only; they now bolt to
        # the pod-rail wheel beam, captive M4 nut inboard, head = the outer hubcap).
        rr_ = P["roadwheel_d"] / 2
        for i in range(P["roadwheel_count"]):
            ry = (i - (P["roadwheel_count"] - 1) / 2) * P["roadwheel_pitch"]
            rw = cyl(rr_, 30.0, axis="x")
            for fs in (-1, 1):
                dsh = sub(cyl(rr_ - 2.2, 2.4, axis="x"), cyl(5.2, 3.4, axis="x"))
                dsh.apply_translation((fs * (30.0 / 2 - 1.1), 0, 0))
                rw = sub(rw, dsh)
                for k in range(5):
                    aa = TAU * k / 5
                    bh = cyl(0.9, 2.0, axis="x")       # bolt circle on the hub boss
                    bh.apply_translation((fs * (30.0 / 2 - 0.9),
                                          3.6 * np.cos(aa), 3.6 * np.sin(aa)))
                    rw = sub(rw, bh)
            rw = sub(rw, cyl(2.1, 34.0, axis="x"))
            rw.apply_translation((cx, ry, (zc - R) + kr + rr_ + 0.1))
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
        # master-link keeper bars: the removable service bits, their own (orange) node
        keep = trimesh.util.concatenate(keeper_pieces)
        _color(keep, "accent")
        keep.metadata["name"] = f"track_keeper_{side}"
        keep.metadata["export"] = f"track_keeper_{side}.stl"
        out.append(keep)
    return out



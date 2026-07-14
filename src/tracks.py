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


# PRINT-IN-PLACE KEEL cross-section (2026-07-12 strip pass), (u, v) about the pin
# (u = y - pin_y, v = z). Grouser-down printing used to float every knuckle 2.5 over
# the bed (the 2026-07-12 chain print failure chain); the keel is a chamfered buttress
# from each knuckle cylinder down to the grouser plane (v -6.0) so the pose is fully
# self-supporting: bed contact = grousers + keel feet, web/bridge undersides anchor on
# the keel tops. Shape reasons:
#   * 45.0-deg chamfer on the PIN side = the knuckle-circle tangent line shifted 0.05
#     inboard (u = v + 4.85; corner (2.4,-2.45) strictly inside the r3.5 circle, no
#     coincident-surface sliver) -- exactly self-supporting, and it clears the ±35 deg
#     articulation sweep of the NEIGHBOR's web/grouser corner (r 5.64 about the pin,
#     swings to (0.21,-5.64); the vertical face at u -0.3 keeps ~0.5 to it).
#   * foot runs to u -4.5 where it buries into the grouser (y 4..6) / web (y 3.4..6.6),
#     so the keel is welded to the pad, and doubles as a traction tooth.
#   * top edge v -2.0 stays fully buried in web/bridge/knuckle (inner faces untouched:
#     road wheels roll the knuckle crowns, the ±4.9 sprocket channel stays empty).
# A keel (own pin y0, neighbor approaches from -y) = the mirror of the B keel
# (far pin y=pitch, neighbor from +y): chamfer faces the neighbor, foot faces own web.
_KEEL_UV_B = ((-4.5, -6.0), (-0.3, -6.0), (-0.3, -5.15),
              (2.4, -2.45), (2.4, -2.0), (-4.5, -2.0))


def _keel(x0, x1, py, kind):
    """Keel prism for one knuckle x-band [x0,x1] at pin y=py; kind 'A' (own pin,
    mirrored) or 'B' (far pin). Built in the extrusion plane then rotated so the
    extrusion axis is X (same trick as _sprocket_disc)."""
    s = -1.0 if kind == "A" else 1.0
    poly = sg.Polygon([(-v, s * u) for (u, v) in _KEEL_UV_B])
    m = extrude_polygon(poly, x1 - x0)                 # (a,b,c) -> (c, b, -a): a=-v, b=u
    m.apply_transform(R(TAU / 4, (0, 1, 0)))
    m.apply_translation((x0, py, 0))
    return m


def _track_link(open_a=False, open_b=False):
    """One articulated track link (local frame: own pin axis = X axis, next pin at y=+pitch,
    OUTER face toward -z). Pad web + grouser + interleaved pin knuckles + 45deg keels under
    every knuckle band (print-in-place strips 2026-07-12: grouser-down is self-supporting)
    + 45deg inner-face draft chamfers at the web ends. Adjacent copies on the loop never
    touch: knuckle sets are X-disjoint and the pads splay apart on the arcs.

    Default = strip MID link: the own (y0) pin is an INTEGRAL Ø2.0 rod fused into the A
    knuckles (no bore), the far (y=pitch) B bores are Ø2.7 print-in-place clearance around
    the neighbor's rod. open_a: strip-FIRST link -- no integral pin, old Ø2.2 A bores for
    a Ø1.75 filament boundary pin. open_b: strip-LAST link -- far bores revert to Ø2.2
    (the next strip's first link + filament pin land there). Master = both open + jaw."""
    pitch, tw = P["track_pitch"], P["track_width"]
    kr = 3.5                                           # knuckle radius about the pin
    parts = [box(tw, 3.2, 2.7), box(tw, 2.0, 1.5)]     # web z -4.5..-1.8, grouser z -6.0..-4.5
    parts[0].apply_translation((0, 5.0, -3.15))
    parts[1].apply_translation((0, 5.0, -5.25))
    ka, kb = _KNUCKLES(tw)
    for (x0, x1) in ka:                                # near knuckles (own pin) + bridge to web
        k = cyl(kr, x1 - x0, axis="x"); k.apply_translation(((x0 + x1) / 2, 0, 0)); parts.append(k)
        b = box(x1 - x0, 3.1, 2.7); b.apply_translation(((x0 + x1) / 2, 2.05, -3.15)); parts.append(b)
        parts.append(_keel(x0, x1, 0.0, "A"))
    for (x0, x1) in kb:                                # far knuckles (next pin) + bridge to web
        k = cyl(kr, x1 - x0, axis="x"); k.apply_translation(((x0 + x1) / 2, pitch, 0)); parts.append(k)
        b = box(x1 - x0, 2.6, 2.7); b.apply_translation(((x0 + x1) / 2, 7.7, -3.15)); parts.append(b)
        parts.append(_keel(x0, x1, pitch, "B"))
    if not open_a:                                     # INTEGRAL own pin: solid Ø2.0 rod
        pr = cyl(P["track_pin_print_d"] / 2, tw - 0.5, axis="x")   # across the link
        parts.append(pr)                               # width, ends recessed 0.25 INSIDE
        # the A knuckles: a flush end face is coincident with the knuckle side wall
        # and leaves a degenerate zero-volume shell in the union (STL round-trip
        # split 16 -> 31 bodies). Functionally identical: the ends are buried solid.
    link = uni(parts)                                  # (sprocket drives on the rod in
    if open_a:                                         # the central channel; neighbor's
        # Ø2.7 B bores ride it print-in-place
        d = cyl(P["track_pin_bore_d"] / 2, tw + 4, axis="x")
        link = sub(link, d)                            # boundary A bores (filament pin)
    far_d = P["track_pin_bore_d"] if open_b else P["track_bore_pip_d"]
    d = cyl(far_d / 2, tw + 4, axis="x"); d.apply_translation((0, pitch, 0))
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
    Returns (body, [keeper_L_local, keeper_R_local]) in link-local coords.
    Strip pass 2026-07-12: the master keeps the FULL old interface (open both ends:
    Ø2.2 A bores under the jaw cut, Ø2.2 far bores, NO integral pin -- a closed far
    bore can never slide onto a neighbor's fused rod, so both master joints are
    assembly joints) and gains the keels like every link; the jaw slots re-cut
    through the A keels so the drop-on mouth stays open."""
    pitch, tw = P["track_pitch"], P["track_width"]
    body = _track_link(open_a=True, open_b=True)
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
        tab = box(2.6, 5.7, 5.7)                       # outboard end fuses into the tab.
        tab.apply_translation((sxs * (tw / 2 + 0.05 + 1.3), 2.6, -1.9))    # Tab centered on
        k = uni([bar, tab])                            # the M2 at y 2.6 (reviews: the old
        # 1.8x7x4 tab left 0.65-0.85 hole ligaments AND let the M2 head stand 0.55-0.85
        # off the chassis wall on the top run; 2.6 thick x 5.7 + a head counterbore gives
        # >=1.5 walls and sinks the head to >=1.1 wall clearance. Wallcheck pass
        # 2026-07-13: the Ø4.2 cb left a 0.65 rim on the 5.5 tab (p1 0.66 < the 0.8
        # gate) -- cb shrunk to Ø4.0 (M2 pan head is Ø3.8 max, 0.2 diametral clear)
        # and the tab grew 5.5 -> 5.7, rim now 0.85. The slot-critical 13.3x1.9 bar
        # is untouched. Tab y -0.25..5.45 keeps 1.05 to the next link's knuckle side
        # faces on the straight run; z low -4.75 stays 1.25 above the grouser plane.
        mc = cyl(1.15, 6.0, axis="x")                  # M2 clearance through the tab
        mc.apply_translation((sxs * (tw / 2 + 1.3), 2.6, -1.9))
        k = sub(k, mc)
        cb = cyl(2.0, 1.5, axis="x")                   # Ø4.0 head counterbore, outer face
        cb.apply_translation((sxs * (tw / 2 + 0.05 + 2.6 - 0.7), 2.6, -1.9))
        k = sub(k, cb)
        keepers.append(k)
    return body, keepers


def _sprocket_profile():
    """2D conjugate pin-rack sprocket profile (2026-07-11 kinematic fix), shapely
    polygon in the extrusion plane (+x = BDC toward the ground run, +y = track +Y).

    The 2026-07-10 pin-pocket disc had SEATS but NO TEETH: tip r 18.8 sat BELOW the
    pin circle 19.32, so at most 1 pin was ever radially trapped (window +-3.72 <
    pitch 10), each pocket drove its pin for only ~6.5 of every 10 mm (dead gap
    bridged by rim-on-pin friction), the pin cammed out at the stroke end under
    stall load, and the 0.355 skip barrier (tip + pin - pin circle) was inside FDM
    tolerance. Now the sprocket_teeth seats keep their place on the track_wheel_r
    pin circle, but the rim rises to tip r 20.5 (sprocket_outer_d/2, ADDENDUM 1.18
    past the pin circle) and each tooth GAP is the true CONJUGATE envelope: the
    Ø1.75 pin + 0.275 running clearance (r 1.15, same as the old seat -- it also
    swallows the 0.125 bore slop and the ~0.06 chordal-action band) is swept through
    the rack mesh -- the ground run advances y = rp * theta while the sprocket turns
    theta, so in the sprocket frame the pin rides Rot(-theta) @ (rp, rp*theta) --
    and the swept union is subtracted at 0.5 deg steps over +-40 deg. The flanks
    come out near-radial (classic roller-chain form): drive contact is smooth
    (measured conjugate-motion penetration -0.15 / -0.18, i.e. clearance, at the
    pin-circle and the chordal 19.099 ratio), and a trapped pin must LIFT past the
    tip circle to escape sideways. MEASURED (numeric probe, 2026-07-11): per-pin
    radial-retention (>=0.8) window +-5.38 = 10.75 > pitch/2, tip-circle trap
    window 13.71 (contact ratio 1.37) -> at every phase at least one pin is caged
    (min best-pin escape lift 0.91 at the half-pitch phase, 2.05 at BDC); skip
    barrier 2.06 (5.8x the old 0.355, FDM +-0.2 is now 10%);
    tooth tips dip to z 4.82 = 0.62 above the link web face (z 4.2, chamfers only
    add room) and stay 0.9 clear of the B knuckles in X (band 8 < channel +-4.9).
    Seat floor stays r 18.17 (0.63 radial bite). Phase on the TT shaft is free
    (D-socket clocks 2 ways, pins self-seat on tension)."""
    from shapely.ops import unary_union
    import shapely.affinity as sa
    rp = P["track_wheel_r"]
    # 2026-07-12 print-in-place strips: the driven pin is now the links' INTEGRAL
    # Ø2.0 printed rod (track_pin_print_d), so the swept envelope radius is
    # 1.0 + 0.275 running clearance = 1.275 (was 1.15 for the Ø1.75 filament pin).
    # Re-probed (tools/probe_track_pip.py): numbers in the report/docs; boundary
    # Ø1.75 filament pins get 0.4 extra radial slack in the same gap -- they seat
    # ~0.14 deeper at BDC, well inside the chain's 0.45 bore slop budget.
    env_r = P["track_pin_print_d"] / 2 + 0.275
    blank = sg.Point(0, 0).buffer(P["sprocket_outer_d"] / 2, resolution=96)
    swept = []
    for th in np.arange(-40.0, 40.01, 0.5) * (np.pi / 180.0):
        c, s = np.cos(th), np.sin(th)
        u, v = rp, rp * th                             # pin in rack coords at angle th
        swept.append(sg.Point(c * u + s * v, -s * u + c * v).buffer(env_r, resolution=24))
    gap = unary_union(swept)
    gaps = unary_union([sa.rotate(gap, 360.0 * k / P["sprocket_teeth"], origin=(0, 0))
                        for k in range(P["sprocket_teeth"])])
    return blank.difference(gaps).simplify(0.01)


def _sprocket_disc(width):
    """Conjugate-tooth sprocket disc: _sprocket_profile() extruded `width` wide and
    rotated so the extrusion axis is the X axle axis (+x profile axis -> world -z =
    bottom dead center, +y -> world +y: the profile is 12-fold symmetric and mirror
    symmetric per gap, so clocking/handedness need no special casing)."""
    disc = extrude_polygon(_sprocket_profile(), width)
    disc.apply_translation((0, 0, -width / 2))
    disc.apply_transform(R(TAU / 4, (0, 1, 0)))        # extrusion z -> the X axle axis
    return disc


def _sprocket(sx, phase=0.0):
    """Drive sprocket + inboard hub tube reaching the TT shaft through the chassis-wall web.
    Disc (tip r 20.5, conjugate teeth -- see _sprocket_profile) at the pod centre (96.4 at
    chassis_w 140 / tw 44.8; hub local -28.1 --
    values are chassis_w/track_width-derived); hub OD12 runs inboard to where the D-socket
    (bore Ø5.65, flat gap 3.85 print clearance, 8.0 deep = TT flat length) grips the shaft flats.
    Outer face: Ø9 x 1.5 counterbore for the M2 retaining screw + washer into the shaft tip's
    Ø2 axial hole. Built for the +X pod, spun 180deg about Z for -X.

    `phase` (2026-07-12, integral-pin pass): world tooth clocking (rad about +X) that
    meshes the baked chain -- applied to the TOOTHED DISC ONLY, before the hub/D-socket
    features, so the socket stays on the shaft flats (physically the free part is the
    chain phase, not the shaft clocking; pins self-seat on tension). The -X pod's final
    Rz(180) conjugates Rx(p) to Rx(-p) and the 12-fold profile maps onto itself, so the
    disc is pre-spun by -phase there to land at +phase in world."""
    tw = P["track_width"]
    cx = P["chassis_w"] / 2 + P["track_gap"] + tw / 2              # pod centre (96.4)
    hub_in = (P["chassis_w"] / 2 - 2.0 + 0.3) - cx                 # world 68.3 -> local -28.1
    # band pinned to 8 (the links' open +-4.9 sprocket channel), NOT tw-derived
    spr = _sprocket_disc(8.0)
    if phase:
        spr.apply_transform(R_x(phase if sx > 0 else -phase))
    hub = cyl(6.0, -hub_in - 3.5, axis="x")                        # inboard of the toothed rim
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


def _strip_plan(n):
    """Print-in-place strip sizes for one track side (2026-07-12): position 0 is the
    master (separate print), positions 1..n-1 fill strips of up to 16 links ->
    (16, 16, 16, 15) at n=64. 16 is the bed cap: a straight 16-link strip spans
    167 mm + 2x5 brim = 177 <= the 180 print bed."""
    sizes, rem = [], n - 1
    while rem > 0:
        s = min(16, rem)
        sizes.append(s); rem -= s
    return tuple(sizes)


def build_tracks():
    """Two positive-drive track pods: 64 articulated links per side (2026-07-12: 4
    PRINT-IN-PLACE strips with integral Ø2.0 pins + Ø2.7 PIP bores, master + boundary
    joints on Ø1.75 filament pins) wrapping two ground-run conjugate sprockets (TT
    double-D hub, phase-clocked to the pin grid) + end idlers on TWO F688ZZ flanged
    bearings each (front pair tensions in the deck pylons) + road wheels riding the
    knuckle crowns on M4 bolt-axles off the side panels' integral wheel beams
    (chassis_side_* in build_chassis_parts; pod_rail_L/R deleted 2026-07-14).
    Bottom-run grouser face = ground (z=0). Each pod is a concatenation of separate
    printed pieces, not one solid."""
    R, tw, wb = P["track_wheel_r"], P["track_width"], P["track_wheelbase"]
    zc = _track_zc()
    kr = 3.5
    # PRINT-IN-PLACE STRIP VARIANTS (2026-07-12): master = position 0 (separate
    # print, closes the loop); positions 1..63 fill 4 strips of (16,16,16,15).
    # Inside a strip every joint is integral-pin + Ø2.7 PIP bore; a strip's FIRST
    # link opens its A end (Ø2.2, no pin) and its LAST link opens its far end
    # (Ø2.2) for the Ø1.75 filament boundary pins. Per side: 59 printed-in-place
    # joints, 3 strip-to-strip filament joints, 1 master closure (master far
    # filament pin + jaw drop-on).
    mid = _track_link()
    first = _track_link(open_a=True)
    last = _track_link(open_b=True)
    mbody, mkeepers = _track_master_link()             # link 0 = the loop-closing master
    sizes = _strip_plan(P["track_links"])
    starts, ends, idx = set(), set(), 1
    for s_n in sizes:
        starts.add(idx); ends.add(idx + s_n - 1); idx += s_n
    out = []
    for sx in (-1, 1):
        cx = sx * (P["chassis_w"] / 2 + P["track_gap"] + tw / 2)
        pieces = []
        keeper_pieces = []
        for i, (y, z, ang) in enumerate(_track_link_poses(wb, R, zc, P["track_links"])):
            src = (mbody if i == 0 else               # master seam on the bottom straight run
                   first if i in starts else last if i in ends else mid)
            lk = src.copy()
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
        # DRIVE SPROCKET on the GROUND RUN (2026-07-11 mid-drive, see PARAMS spr_y /
        # track_wheelbase): center on the pin line + pin circle, meshing the straight
        # bottom run rack-style -- the robot's weight presses the run into the teeth,
        # so ground reaction guarantees the 2-3-pin bite. TT stays direct on the
        # double-D shaft, dropped with it to z 25.32.
        for sy_, snm in ((P["spr_y"], "sprocket_rear"), (P["spr_y2"], "sprocket_front")):
            # CONJUGATE PHASE (2026-07-12): the links' integral Ø2.0 pins are real
            # geometry now, so the baked disc must be clocked to the chain. Ground
            # pins sit at y = -track_ground_hy + 10k (grid = 0 mod pitch); clock by
            # (nearest pin offset)/rp about +X (probe convention: pin at +s <-> disc
            # +s/rp). spr_y -68 -> -2/19.32 = -5.93 deg; spr_y2 +90 is on-grid (0).
            s_rel = ((-sy_ + P["track_pitch"] / 2) % P["track_pitch"]) - P["track_pitch"] / 2
            spr = _sprocket(sx, s_rel / P["track_wheel_r"])  # two stations (the front
            spr.apply_translation((cx, sy_, (zc - R) + R))   # one rides the OPTIONAL
            wheel_pieces.append((snm, spr))                  # 2nd TT's shaft)
        # END WHEELS (both ends are now FREE IDLERS on Ø8 stubs in the deck-overhang
        # pylons; the front pair tensions): rides the knuckle crowns with 0.12 running
        # clearance; TWO
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
        # the deck pylon face (symmetric growth once swallowed the old tension plate)
        for ey_, inm in ((wb / 2, "end_idler_front"), (-wb / 2, "end_idler_rear")):
            idl2 = idl.copy()
            idl2.apply_translation((cx + sx * 6.0, ey_, za))
            wheel_pieces.append((inm, idl2))
        # road wheels (tank-ref style): dense dished row riding the bottom-run knuckle
        # crowns (0.1 running clearance). Rim ring + recessed dish + raised hub with a
        # 5-hole bolt circle on each face; Ø4.2 center bore = slip fit on the M4 x 40
        # bolt-axle (2026-07-10 fix: the wheels were mounted to NOTHING -- weight went
        # to ground through the TT gearbox shaft + idler stub only; they now bolt to
        # the pod-rail wheel beam, captive M4 nut inboard, head = the outer hubcap).
        rr_ = P["roadwheel_d"] / 2
        for ry in P["roadwheel_ys"]:
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
            wheel_pieces.append((f"road_wheel_{len(wheel_pieces) - 3}", rw))
        # VISIBLE AXLE HARDWARE (2026-07-11): silver placeholder node per side, NOT
        # print-exported. 6x M4x40 bolt-axles (shank through the rail-beam bore and
        # the wheel, hex head = the hubcap) + TWO Ø8 end stubs (mid-drive pass:
        # each cantilevers from its deck pylon through an end idler's F688ZZ pair;
        # the front pylon's slot tensions).
        hw = []                                        # (name, mesh) per FASTENER so
        for bi, ry in enumerate(P["roadwheel_ys"], 1): # the viewer can select each one
            rwz = (zc - R) + kr + rr_ + 0.1
            sh = cyl(1.95, 40.0, axis="x")             # TRUE M4x40: 40 under the head
            sh.apply_translation((sx * 91.4, ry, rwz))         # x 71.4..111.4 -- the
            # tip protrudes 2.7 past the seated nut's inner face (real thread
            # stick-out; the old 37 shank STOPPED INSIDE the nut zone), 1.4 clear
            # of the chassis wall outer face at x 70
            hd = cyl(3.5, 3.5, axis="x")
            hd.apply_translation((sx * 113.15, ry, rwz))       # head on the hub face
            hw.append((f"wheel_bolt_{bi}", trimesh.util.concatenate([sh, hd])))
            # M4 HEX NUT seated in the beam's slide-up slot (2026-07-11, user:
            # "wheel bolts not properly connected" -- the pod-rail slots were
            # modeled EMPTY). AF 7.0 / AC 8.1 corners / 3.2 thick, axis x, FLATS
            # to +-y (the slot's 7.3 walls), corners up/down like the slot cut:
            # torque drags it OUTBOARD to the slot's outer wall (x 77.5; modeled
            # 0.05 shy so the gate sees no face-jam) and its top corner parks on
            # the slot ceiling z 23.65 = rwz + 4.05, which centres it on the
            # bore (chassis.py's design). No washer: the nut is captive in the
            # printed slot by design (CLAUDE.md wheel-beam stack).
            nt = cyl(4.05, 3.2, axis="x", sections=6)
            nt.apply_translation((sx * 75.85, ry, rwz))
            hw.append((f"wheel_nut_{bi}", nt))
        for ey_, bnm in ((wb / 2, "end_bolt_front"), (-wb / 2, "end_bolt_rear")):
            sh8 = cyl(4.0, 60.4, axis="x")             # M8 END BOLT-AXLES: shank x 58..
            sh8.apply_translation((sx * 88.2, ey_, za))    # 118.4 through bearings +
            hd8 = cyl(6.5, 5.3, axis="x")              # pylon, head = outboard hubcap
            hd8.apply_translation((sx * 121.05, ey_, za))
            ws8 = cyl(7.2, 1.5, axis="x")              # Ø14.4 washer on the pylon
            ws8.apply_translation((sx * 61.25, ey_, za))   # inboard face (x 60.5..62)
            nt8 = cyl(7.2, 5.0, axis="x", sections=6)  # M8 NYLOC as a true hex
            if ey_ > 0:                                # (x 55.5..60.5). FRONT: flats
                nt8.apply_transform(R_x(TAU / 12))     # to +-Z -- the 2026-07-13
            # capture duct's floor/roof grip them across the tension stroke. REAR:
            # flats to +-y, held by the 13.8 nut-channel walls while the bolt is
            # torqued from the outboard head (see build_chassis_core's sgn branch).
            nt8.apply_translation((sx * 58.0, ey_, za))
            hw.append((bnm, trimesh.util.concatenate([sh8, hd8, ws8, nt8])))
            # F688ZZ placeholders (2026-07-11, user: "bolt not properly connected
            # to the idler" -- the Ø8 shank floated in the Ø16 seat where the
            # bought bearings live): one flanged ring per idler face (ring Ø8.1/
            # Ø15.8 x 5 in the 7.97 seat, Ø18.2 flange in the wheel's Ø18.5
            # recess). Bought parts: never printed, export None like the bolts.
            end_tag = "front" if ey_ > 0 else "rear"
            rot_zx = trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0))
            for x_face, drn, seat in ((117.4, -1.0, "o"), (87.4, 1.0, "i")):
                ring = trimesh.creation.annulus(4.05, 7.9, 5.0)
                ring.apply_transform(rot_zx)
                ring.apply_translation((sx * (x_face + drn * 2.5), ey_, za))
                flg = trimesh.creation.annulus(4.05, 9.1, 0.95)   # recess is 1.0 deep
                flg.apply_transform(rot_zx)
                flg.apply_translation((sx * (x_face + drn * 0.475), ey_, za))
                hw.append((f"end_brg_{end_tag}_{seat}",
                           trimesh.util.concatenate([ring, flg])))
        side = "L" if sx < 0 else "R"
        # GRANULAR SCENE NODES (2026-07-11, user: "select every little component"):
        # each link / wheel / fastener becomes its own dotted child node
        # ("parent.child"); the gates re-group by the prefix before the dot, and the
        # print export gets ONE multi-body ghost per parent (scene=False).
        def emit(parent, color, children, export=None):
            for cn, cm in children:
                _color(cm, color)
                cm.metadata["name"] = f"{parent}.{cn}"
                cm.metadata["export"] = None
                out.append(cm)
            if export:
                gh = trimesh.util.concatenate([cm.copy() for _, cm in children])
                gh.metadata["name"] = f"__export__{parent}"
                gh.metadata["export"] = export
                gh.metadata["scene"] = False
                out.append(gh)
        emit(f"axle_hw_{side}", "motor", hw)           # bought hardware, never printed
        links = [(f"link_{i:02d}" + ("_master" if i == 0 else ""), lk)
                 for i, lk in enumerate(pieces)]
        emit(f"track_{side}", "track", links, f"track_{side}.stl")
        emit(f"drivewheels_{side}", "motor", wheel_pieces, f"track_wheels_{side}.stl")
        keeps = [(f"bar_{i+1}", k) for i, k in enumerate(keeper_pieces)]
        emit(f"track_keeper_{side}", "accent", keeps, f"track_keeper_{side}.stl")
    # PRINT-IN-PLACE STRIP EXPORTS (2026-07-12): straight rows at pitch, grouser-down
    # local frame (outer face -z; the exporter just drops them z-min to the bed), ONE
    # mesh per strip by CONCATENATION -- boolean-unioning link bodies would weld the
    # 0.35 PIP hinge gaps shut. export-only ghosts (scene=False): the loop's per-link
    # scene nodes above carry the viewer. Links are x-mirror-symmetric, so L and R
    # strips are identical meshes under both names.
    def _strip_mesh(s_n, tag):
        row = []
        for j in range(s_n):
            v = first if j == 0 else last if j == s_n - 1 else mid
            c = v.copy()
            c.apply_translation((0, j * P["track_pitch"], 0))
            row.append(c)
        sm = trimesh.util.concatenate(row)
        bodies = sm.split(only_watertight=False)
        assert len(bodies) == s_n, \
            f"{tag}: {len(bodies)} bodies != {s_n} links (PIP gap fused or link split?)"
        return sm
    for si, s_n in enumerate(sizes, 1):
        sm = _strip_mesh(s_n, f"strip {si}")
        for side in ("L", "R"):
            gh = sm.copy()
            gh.metadata["name"] = f"__export__track_strip_{side}{si}"
            gh.metadata["export"] = f"track_strip_{side}{si}.stl"
            gh.metadata["scene"] = False
            out.append(gh)
    # TEST COUPON (2026-07-13): a 5-link print-in-place strip -- one open-A first
    # link, three integral-pin mids, one open-far last, same variants and keels as
    # the production strips, concatenated NEVER unioned -- so the 0.35 PIP hinge
    # gap, the keeled grouser-down pose and every boundary bore get validated in
    # ~48 min of plastic (sliced) before the 6.8 h strip plates. tools/export_bambu.py puts
    # it on its own "Track coupon" plate with a loose master + keeper bars.
    cp = _strip_mesh(5, "coupon")
    cp.metadata["name"] = "__export__track_coupon"
    cp.metadata["export"] = "track_coupon.stl"
    cp.metadata["scene"] = False
    out.append(cp)
    return out



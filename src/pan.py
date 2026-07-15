"""Pan stage: platform, captured-BB lazy-Susan race, uplift clips.

Split out of the original monolithic build.py (2026-07-10); see
build.py for the assembly entry point and the overall design notes.
"""
import os
import numpy as np
import trimesh
import shapely.geometry as sg
from trimesh.creation import extrude_polygon
from trimesh.transformations import rotation_matrix as R
from params import DEG, P, TAU
from geo import _color, box, cyl, sub, uni
from gears import gear_disc, load_gear_stl, pan_real_ok


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

    # rim REBATE: top band stepped to r45 -> an up-facing shoulder below the top. The deck
    # clips reach over this shoulder to resist uplift (top-heavy head). The rebate is a full
    # ring because the platform pans past the 3 fixed clips.
    # DEEPENED 3.0 -> 4.4 (fastening campaign 2026-07-15, audit P2 item 15): the clip tabs
    # that hold the whole top-heavy head down were 2.6 mm of PLA loaded in layer-shear, and
    # they are capped above by the deck-flush top (z1) -- the only way to thicken them to
    # 4.0 is to drop the shoulder they reach under. Shoulder 63.0 -> 61.6 (tab underside
    # 62.0 keeps the same 0.4 running clearance). The trade is the platform's own rim below
    # the shoulder, 4.6 -> 3.2 -- worth it: that rim is a continuous 3 mm-radial ring, the
    # tabs are 3 small cantilevers, so the section moves to where the part is weakest
    # (tab bending strength scales with t^2: 2.6 -> 4.0 is 2.4x).
    reb = sub(cyl(P["pan_plate_d"] / 2 + 2, 5.4, sections=96), cyl(45.0, 7.4, sections=96))
    reb.apply_translation((0, 0, z1 - 1.7))          # cut spans z1-4.4 .. z1+1
    plate = sub(plate, reb)

    # FAST-PAN 2:1 gear-up (2026-07-12; see PARAMS pan_gear_*): the old on-axis D-bore hub
    # is GONE -- the motor moved off-axis and its 32T gear (build.py pan_gears) drives this
    # integral 16T PINION hub on the platform underside. The race still locates radially
    # (that job never belonged to the shaft); the teeth only drive. REAL generated involute
    # teeth (tools/gears/gen_pan_spurs.py: m0.8 / PA 20 / CD 19.2 with the 32T, blank
    # width 5.5 centered, tooth centered on +X -- build.py's 32T clocking assumes that
    # phase); pan_real_ok() falls back to gear_disc on any PARAMS mismatch and
    # PLACEHOLDER_GEARS=1 forces it (worm-pair convention, src/gears.py).
    gz0, gz1 = P["pan_gear_z"]                       # tooth band 45..50 (under seat floor 51)
    pin_r = P["pan_gear_m"] * P["pan_gear_pinion_t"] / 2         # 6.4
    shank = cyl(6.5, plate_bot - gz1 + 1.0)          # hub shank, buried 1.0 into the plate
    shank.apply_translation((0, 0, (gz1 + plate_bot + 1.0) / 2))
    if os.environ.get("PLACEHOLDER_GEARS") == "1" or not pan_real_ok():
        pin = gear_disc(pin_r, P["pan_gear_pinion_t"], gz1 - gz0 + 0.5, 2.0, axis="z")
    else:
        pin = load_gear_stl("pan_pinion_real.stl")   # solid 16T blank, axis Z
    pin.apply_translation((0, 0, (gz0 + gz1) / 2))   # +0.5 width: roots fuse into the shank
    plate = uni([plate, shank, pin])

    # PAN-STOP LUG (homing pass 2026-07-08): hangs from the plate underside at r28,
    # azimuth 225, down to 0.6 above the seat floor; hits the two deck posts (azimuth
    # 118/332, build_base) at +-93.3 deg pan. RADIALLY ALIGNED like the posts (review
    # fix, see build_base). Corners r 23.8..32.2: clear of the ring ID (34), the D-hub
    # (r7), the cable slot (13+ away) and the neck-bolt cbores (19.9+).
    lug = box(6.0, 6.0, plate_bot - (seat_floor + 0.6))
    lug.apply_translation((28.0, 0, (plate_bot + seat_floor + 0.6) / 2))
    lug.apply_transform(R(225 * DEG, (0, 0, 1)))
    plate = uni([plate, lug])

    # upper race groove: wraps pan_groove_engage (1.8) of ball up into the plate. Torus center
    # = ball top - minor r = zball - groove_clear -> ball top tangent to the groove ceiling.
    # FINE tessellation (fit-map finding 2026-07-08: default ~32 major sections chord a r40
    # circle 0.19 INSIDE nominal -- the printed groove's flats would genuinely pinch the
    # balls 0.055; 96/48 sections cut the sag to 0.02/0.01).
    minor = P["pan_race_ball_d"] / 2 + P["pan_groove_clear"]
    groove = trimesh.creation.torus(P["pan_race_circle_d"] / 2, minor,
                                    major_sections=96, minor_sections=48)
    groove.apply_translation((0, 0, zball - P["pan_groove_clear"]))
    plate = sub(plate, groove)

    # cable SLOT: 8-wide obround jogging the bundle from the neck channel (0, neck_chan_y)
    # inward to cable_exit inside the race ID. A 5-pos JST-XH head (14.9 x 5.9) passes the
    # slot lengthwise.
    ex, ey = P["cable_exit"]
    slot = extrude_polygon(sg.LineString([(0, P["neck_chan_y"]), (ex, ey)]).buffer(4.0), 40)
    slot.apply_translation((0, 0, z1 - 20))
    plate = sub(plate, slot)

    # 2 printed REGISTRATION PINS on the top face for the neck column (fastening campaign
    # 2026-07-15, audit holding gap 1): the root joint of the whole head stack used to be
    # flat-on-flat -- the column was held by hand while 3 blind M3s were driven up from
    # underneath. Ø4.0 x 2.45 proud (0.55 fused into the plate) at (+-18, -32), 36 mm
    # apart so they fix rotation too; blind Ø4.2 sockets in build_neck_clevis take them.
    # Placement: inside the column footprint (x +-24, y -40..6) and inside the neckfoot
    # collar's bore (so the collar still drops over the column), 6 mm off the cable slot
    # wall, far from the 3 bolt counterbores. Mirrors the pedestal pins (chassis.py).
    for sx in (-1, 1):
        pin = cyl(2.0, 3.0)
        pin.apply_translation((sx * 18.0, -32.0, z1 + 0.95))     # z1-0.55 .. z1+2.45
        plate = uni([plate, pin])

    # 3 M3 clearance holes to bolt the neck down (MATCH the neck-base pilots: rad 16.5,
    # clocked 270/30/150 about (0, neck_y) -- see build_neck_clevis, incl. why 16.5) with
    # Ø6.5 head counterbores from the UNDERSIDE, 4 deep. All 3 land on the solid top
    # (r<=33.5+3.25), clear of the center D-bore hub (nearest hole edge r 15.0 vs hub r 7),
    # the rim rebate (r45+), the ball groove (footprint r 36.8..43.2 lives BELOW plate_bot;
    # widest in-plate cross-section at plate_bot starts r 37.1 > cbore reach 36.75) and the
    # cable slot (270-deg cbore edge y -30.25 vs slot edge -30: the old rad 16 grazed 0.25).
    for a in (270, 30, 150):
        rad = 16.5
        hx = rad * np.cos(np.radians(a)); hy = P["neck_y"] + rad * np.sin(np.radians(a))
        h = cyl(P["m3_clear_r"], 40.0); h.apply_translation((hx, hy, z1 - 4))
        plate = sub(plate, h)
        cb = cyl(3.25, 8.0); cb.apply_translation((hx, hy, plate_bot))
        plate = sub(plate, cb)

    # 2x blind Ø3.2 x 5.0 pin sockets for the trim_neckfoot collar (neck styling pass
    # 2026-07-12, see build_trim_neckfoot): at (+-27, neck_y) -- r 31.9 from the pan axis,
    # clear of the cable slot (x -4..16 / y -30..-20), the neck-bolt cbores (|x| <= 17.8),
    # the D-hub (r7) and the ball-groove footprint (in-plate cross-section starts r 37.1).
    # DEPTH 3.5 -> 5.0 (fastening campaign 2026-07-15, audit P3): 3.5 of blind Ø3 socket is
    # not a location feature, it is a rattle. The collar is 3.0 tall, so the pin is now
    # Ø3x8 (3 in the collar + 5 here) and the socket still leaves 2.6 of plate below it
    # (plate spans z 58.4..66). Keep build_trim_neckfoot's through-bore in sync.
    for sx in (-1, 1):
        ps = cyl(1.6, 5.0)
        ps.apply_translation((sx * 27.0, P["neck_y"], z1 - 5.0 / 2))
        plate = sub(plate, ps)
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
    groove = trimesh.creation.torus(cr, bd / 2 + P["pan_groove_clear"],
                                    major_sections=96, minor_sections=48)   # see the upper-
    groove.apply_translation((0, 0, zball + P["pan_groove_clear"]))         # groove sag note
    lower = sub(ring, groove)
    _color(lower, "pan"); lower.metadata["name"] = "pan_race"

    balls = []
    for i in range(P["pan_race_n"]):
        a = TAU * i / P["pan_race_n"]
        b = trimesh.creation.icosphere(subdivisions=2, radius=bd / 2)
        b.apply_translation((cr * np.cos(a), cr * np.sin(a), zball))
        balls.append(b)
    ballring = uni(balls); _color(ballring, "axle"); ballring.metadata["name"] = "pan_balls"

    # BALL CAGE (maintenance pass 2026-07-08; the FIXES.md "nice-to-have" cage ring): a flat
    # printed ring floating in the 2.4 mm air gap between ring top (42.0) and plate bottom
    # (44.4), with 18 Ø6.6 through-pockets around the ball equators (zball 43.2). It does NOT
    # retain the balls axially -- the lower groove + gravity do that -- it SPACES them, so a
    # turret lift leaves 18 balls sitting evenly in the groove instead of bunching and rolling
    # out, and the race runs smoother under the top-heavy head. Running fits: 0.3 axial air
    # each face, 0.3 radial per side in the pockets, 1.2 rim ligaments past the pocket edges
    # (pocket edges r 36.7..43.3 vs ring r 35.5..44.5). Seat wall (r49) and platform hub (r7)
    # are far. Prints flat, no supports.
    cage_t = 1.8
    cage = sub(cyl(44.5, cage_t, sections=96), cyl(35.5, cage_t + 2, sections=96))
    cage.apply_translation((0, 0, zball))
    for i in range(P["pan_race_n"]):
        a = TAU * i / P["pan_race_n"]
        pk = cyl(3.3, cage_t + 2, sections=32)
        pk.apply_translation((cr * np.cos(a), cr * np.sin(a), zball))
        cage = sub(cage, pk)
    _color(cage, "pan"); cage.metadata["name"] = "pan_cage"
    return lower, ballring, cage


def build_pan_clips():
    """3 L-clips at 120deg, screwed into deck pockets around the pan seat: each tab reaches
    over the platform's rim-rebate shoulder to resist UPLIFT (nothing else stops the
    top-heavy head lifting the platform off the balls). Everything stays AT or BELOW the
    deck top: the neck column sweeps r ~15..63 above z=base_h when panning, so a clip
    standing proud there would be sheared off -- that's also why the platform gets a rebate
    (engagement below the top) instead of the clips overhanging the top surface.
    Separate screwed parts: drop the balls + platform in first, then the clips.

    TAB 2.6 -> 4.0 + ROOT FILLET (fastening campaign 2026-07-15, audit P2 item 15: three
    2.6 x 4.1 x 14 tabs are ALL that stops the top-heavy head lifting the platform off the
    balls, and they are loaded in the layer-shear direction). The tab top is pinned at the
    deck-flush z1 (the neck column sweeps r ~15..63 straight over it), so the thickness had
    to come from below: build_pan_platform's rim rebate dropped its shoulder 63.0 -> 61.6,
    the tab underside follows 63.4 -> 62.0 and keeps the same 0.4 running clearance and the
    same 2.6 mm of shoulder engagement (r 45.4..48). t^2 -> 2.4x the bending strength.
    The ROOT (y ~49, where the bending moment peaks) additionally gets a 45 deg fillet: the
    platform is r <= 48, so the band r 48.4..49.5 under the tab is free air and takes a
    wedge down to the body bottom for nothing. Screw positions UNCHANGED; the deck pocket
    grows to take the 4 mm tab (chassis side)."""
    z1 = P["base_h"]
    clips = None
    for a in (90, 210, 330):
        # built at azimuth 90 (+Y), then rotated into place about the pan axis
        body = box(14, 9, 7); body.apply_translation((0, 53.5, z1 - 3.5))       # r 49..58
        tab = box(14, 4.1, 4.0); tab.apply_translation((0, 47.45, z1 - 2.0))    # r 45.4..49.5
        # root fillet, in the (y, z) plane extruded along X: local x -> world y,
        # local y -> world z, local z -> world x (proper rotation, det +1)
        fil = extrude_polygon(sg.Polygon([(48.4, z1 - 4.0), (49.5, z1 - 4.0),
                                          (49.5, z1 - 7.0)]), 14.0)
        T = np.eye(4); T[:3, :3] = np.array([[0, 0, 1.0], [1.0, 0, 0], [0, 1.0, 0]])
        T[0, 3] = -7.0
        fil.apply_transform(T)
        c = uni([uni([body, tab]), fil])          # tab underside z1-4.0 = shoulder + 0.4
        thr = cyl(P["m3_clear_r"], 20); thr.apply_translation((0, 53.5, z1 - 4))
        c = sub(c, thr)                          # M3 through, into the deck pilot below
        cb = cyl(3.25, 6.8); cb.apply_translation((0, 53.5, z1))
        c = sub(c, cb)                           # head cbore z1-3.4: head sits 0.4 sub-flush
        c.apply_transform(R((a - 90) * DEG, (0, 0, 1)))
        clips = c if clips is None else uni([clips, c])
    _color(clips, "pan"); clips.metadata["name"] = "pan_clips"
    return clips



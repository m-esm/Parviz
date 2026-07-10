"""Bought-motor placeholder meshes: TT gearmotor, 28BYJ-48 stepper.

Split out of the original monolithic build.py (2026-07-10); see
build.py for the assembly entry point and the overall design notes.
"""
from params import P
from geo import _color, box, cyl, sub, uni


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



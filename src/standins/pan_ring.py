"""hw_pan_ring plastic stand-in -- the pan race's rolling elements. See the package
docstring for the shared rationale, and the BARREL ROLLER note below for why this one
stopped being a ring.

THE RING WAS A NON-STARTER (2026-07-16 rework, probed):
    The first stand-in was a Ø5.8-section torus lying in both grooves as a plain
    thrust bearing. It seats fine and prints fine, and it CANNOT BE PANNED. Sliding
    PLA-on-PLA at mu ~0.2 greased (~0.35 dry), under the ~12 N the turret puts on the
    race, at the r=40 ball circle:
        T = mu * N * r = 0.2 * 12 * 0.040 = 96 mNm  (48 mNm at a very optimistic 0.1)
    The 28BYJ delivers ~34 mNm at <=10 RPM and the pan stage GEARS UP 2:1, so the
    platform sees ~15-17 mNm. The ring asks for 3-6x the whole torque budget: the
    interim pan joint would not move at all, i.e. the stand-in did not stand in for
    anything. Rolling elements are not a nicety here, they are the only way the dry
    build pans. (The real BBs roll at an effective mu ~0.015 -> the ~7 mNm the design
    is budgeted against.)

WHY A BARREL ROLLER, AND WHY IT PRINTS (the "spheres come out scarred" objection):
    The objection is real for a ball used as a ball -- a Ø6 sphere printed on its pole
    has a >45 deg overhang band and the droop lands on the pole. It stops mattering
    once you notice WHERE a thrust bearing's element actually touches: the element
    rolls about a HORIZONTAL RADIAL axis (it is a wheel running around the r=40 track),
    so both contacts -- lower groove floor and upper groove ceiling -- ride ONE GREAT
    CIRCLE perpendicular to that axis. The spin poles never carry load.
    So: print the element as a body of revolution about Z and INSTALL IT WITH THE PRINT
    AXIS RADIAL. The rolling band is then the printed XY circle -- the single most
    accurate contour an FDM machine makes (no layer steps across it at all) -- and the
    layered/drooped print poles point at the pan axis and at the seat wall, touching
    nothing. The poles are then free to be cut flat, which is what makes it printable:
      * flat_d 0.5 flats at both ends -> a Ø3.29 first layer (a bare sphere's first
        layer is a point: no adhesion, the ball is knocked off the bed);
      * the >45 deg band shrinks to z 0..0.36 above the flat, worst 56.2 deg from
        vertical AT the flat edge = 0.149 mm of outward step per 0.1 mm layer (~1/3 of
        a 0.42 extrusion unsupported), improving to vertical by the equator -> prints
        with cooling, no support, no droop worth measuring. A 45 deg lead-in chamfer
        was probed and REJECTED: on a convex sphere the tangent cone lies OUTSIDE the
        surface, so a chamfer can only ADD radius into the groove's 0.1 mm side gap,
        never cut the overhang away;
      * both ends flat -> the element is symmetric, so "flats face in/out" is the only
        assembly rule and either way round is right.
    flat_d is an optimum, not a taste: deeper flats print better but both worsen the
    misorientation drop AND close the flat-rim-to-groove gap (0.104 at 0.5 -> 0.082 at
    0.7); shallower ones steepen the overhang (60 deg at 0.4) for a 0.013 gap gain.
    Everything below the flats is a true sphere of crown_d, so in the groove it is
    geometrically a BB: same conformal seat, same self-centering, same kinematics.

WHAT IT COSTS vs REAL BBs (honest, dry build only):
  * Effective rolling mu of printed PLA on printed PLA is roughly 2-3x a steel BB's,
    dominated by layer-line roughness rather than hysteresis (Hertz says the 0.7 N/ball
    patch is ~0.3 mm at ~11 MPa -- nowhere near PLA yield, and crr from hysteresis is
    <0.001). Expect ~15-20 mNm of race drag against the ~15-17 mNm at the platform:
    THE DRY PAN WILL SLEW, but slowly, near the torque limit, and it may need a nudge
    from rest. Grease both grooves. Do NOT read dry pan speed as a verdict on the pan
    gear ratio -- re-time it on the real BBs.
  * Nothing FORCES the axis radial (the Ø6.6 cage pocket cannot constrain yaw on a
    body whose max radius is 2.95). It barely matters: probed over the orientation
    sphere, the element stands its full crown -- platform drop 0.105, same as the
    rolling state -- unless its axis lands within 33.9 deg of VERTICAL (the flat only
    truncates the Z support once 2.95*cos(a) < 2.45). In that one cone it drops to
    0.661 and clunks. It is also self-healing: the platform rides the TALLEST elements,
    so a tipped one immediately sheds its load, and an unloaded element gets dragged
    back to the rolling state by the groove walls.
  * crown_d 5.9 (0.1 under the BB) so print swell lands near nominal; the platform
    sits 0.105 low (the old ring dropped it 0.2), or dead-on if the print comes out
    +0.1. Harmless either way -- the grooves capture on the crown, and the clips'
    uplift engagement has far more travel than this.
  * Turn ON elephant-foot compensation. The first-layer rim is the flat's edge, which
    probes 0.104 from the lower groove wall (a Ø6.00 BB's own surface is 0.08 off at
    the same latitude, so this is a BB-class gap, not a new one) -- a +0.1 foot leaves
    0.044, a +0.2 foot kisses the wall and rubs.

pan_cage IS USED NOW (it idled under the ring): 18 rollers in 18 Ø6.6 pockets, spaced,
which is what stops adjacent elements from rubbing at 2x surface speed. Print the cage.

Print: NOSUP, brim (20 small footprints), 0.1 mm layers -- at 0.2 the flat-edge band
steps 0.3 mm per layer and it does droop. Count is 18 + 2 spares; they are 0.1 g each
and the plate is cheap insurance against one bad ball costing a re-print.
"""
import numpy as np
import trimesh

from geo import box, sub
from params import P

from ._common import _zmin0

COUNT = P["pan_race_n"] + 2      # 18 in the race + 2 spares (see the print note)
NAME = "hw_pan_ring"             # kept: checks.py / wallcheck / the plate list key on it

CROWN_D = 5.9                    # rolling diameter (0.1 under pan_race_ball_d, see above)
FLAT_D = 0.5                     # depth cut off each spin pole -> Ø3.83 flats


def build():
    """One barrel roller, print-posed: axis = Z, flat on the bed. Installed with the
    axis RADIAL, it is a Ø5.9 BB everywhere the race touches it."""
    r = CROWN_D / 2
    ball = trimesh.creation.icosphere(subdivisions=4, radius=r)
    for sgn in (-1, 1):
        cut = box(4 * r, 4 * r, 2 * r)
        cut.apply_translation((0, 0, sgn * (r - FLAT_D + r)))   # face at +-(r - flat_d)
        ball = sub(ball, cut)
    return _zmin0(ball)


def seat_z():
    """World z of the roller centre when it rests in the lower groove: the crown is a
    sphere of CROWN_D/2, so it drops (groove minor r - crown r) below the groove's
    torus centre, exactly like an undersize BB."""
    from pan import _pan_stack
    _plate_bot, _ring_top, _seat_floor, zball = _pan_stack()
    minor = P["pan_race_ball_d"] / 2 + P["pan_groove_clear"]
    return zball + P["pan_groove_clear"] - (minor - CROWN_D / 2)


def posed(azimuth, z=None):
    """The roller placed at one station of the ball circle, print axis rotated onto the
    radial direction (the rolling axis). Probe/preview helper -- not a scene node."""
    m = build()
    m.apply_translation((0, 0, -(CROWN_D / 2 - FLAT_D)))          # centre at origin
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))
    m.apply_transform(trimesh.transformations.rotation_matrix(azimuth, (0, 0, 1)))
    cr = P["pan_race_circle_d"] / 2
    m.apply_translation((cr * np.cos(azimuth), cr * np.sin(azimuth),
                         seat_z() if z is None else z))
    return m

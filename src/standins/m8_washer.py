"""hw_m8_washer plastic stand-in. See the package docstring for rationale + LOAD LIMITS.

FLATTED, NOT ROUND (2026-07-16 stand-in rework). The metal counterpart on the buy list is
a plain Ø14.4/Ø8.4 x 1.5 flat washer under each M8 end-axle NUT (tracks.py `ws8`, seated on
the end tower's inboard face at x 60.5..62, centred on the axle). A round Ø14.4 disc CANNOT
GO THERE: since the 2026-07-14 running-gear V2 deleted the prow-cheek nut ducts, the nut
rides a LEDGE+ROOF CAGE on the tower face whose gap is 13.4 (= AF 13 + 0.4, sized for the
NYLOC's flats), and the washer sits inside that same x band. Probed against the real panels
(chassis_side_R_front / _rear at the nominal seat): a Ø14.4 disc overlaps the cage strips by
5.215 mm^3 (Ø13.8: 1.269; Ø13.4: 0.000). So the washer takes the nut's own two flats:

  AF 13.0 across the strips (0.2 per side in the 13.4 gap -- the same clearance the modeled
  NYLOC gets), full r 7.2 the other way, where the cage is open and the y travel window was
  already cut for a Ø14.4 washer (front window ey-9.8..ey+14.3 = 7.2 + the -2.0/+6.5 tension
  stroke + 0.6; rear +-7.8 = 7.2 + 0.6). Bearing land on the tower face is unaffected in the
  direction that matters: the tension SLOT is a stadium +-4.2 in the strip direction, so the
  flats still leave 2.3 mm of land bridging it (4.2 -> 6.5), and the round sides keep 3.0.

ORIENTATION AT ASSEMBLY: the flats go on the CAGE strips (world +-Z), same as the nut.

WHY NOT A PRINTED WAVE/SPRING WASHER (evaluated 2026-07-16, rejected):
  * It fits and it prints. Axial room exists (the cage does not constrain x; a ~2.2 free
    height compresses into the 1.5 seat), and a 3-wave form at t 0.8 / amplitude 0.6 is a
    ~22 deg helical ramp over the Ø11.4 mean circle -- NOSUP, flat on the bed.
  * It does not solve the problem it is aimed at. Rate ~ E*b*t^3*N^4 / (2.4*Dm^3) with
    b 2.5 (the flats cut the outer band to 2.3 where the wave needs width), t 0.8, N 3,
    Dm 11.4, E 3.5 GPa ~= 100 N/mm, so a 0.6 take-up carries ~60 N at ~35 MPa of sustained
    bending. PLA at 35 MPa and room temperature relaxes 30-50% within a day and takes a
    permanent set when bottomed -- i.e. the spring creeps by exactly the mechanism it is
    supposed to compensate for. It would buy a decaying half-millimetre.
  * It costs the two things the washer is actually for. Sheet t 0.8 instead of a 1.5 slab
    is a worse bridge over the 8.4 slot (the washer's real job), and a soft stack under the
    FRONT nut weakens the tension-slot friction clamp, which is the joint that holds idler
    position.
  * A steel wave washer under the plastic nut IS worth trying on the bench (that is the
    real-hardware side of the swap, not a printed stand-in).
Flat it stays -- a stand-in's job is to be the metal part, not a better idea.

Print: lies flat, NOSUP.
"""
from geo import box, frustum, sub

from ._common import _ring, _zmin0

COUNT = 4
NAME = "hw_m8_washer"

OD = 14.4          # nominal washer OD (kept on the open sides)
AF = 13.0          # across the two flats = the cage gap 13.4 - 0.2/side, as the NYLOC
BORE = 8.4         # clears the Ø8.0 printed M8 shank + its printed thread crest
T = 1.5
CH = 0.3           # bore-edge chamfer, both faces


def build():
    """Flat washer, flats to +-Y (= the cage strips, world +-Z), printed lying down."""
    w = _ring(OD, BORE, T)
    for sy in (-1, 1):
        f = box(OD + 2, OD, T + 2)
        f.apply_translation((0, sy * (AF / 2 + OD / 2), T / 2))
        w = sub(w, f)
    # 45deg bore chamfers: lead the shank in and keep the first-layer lip off the bearing
    # face (a stamped washer has broken edges; a printed one has an elephant foot).
    # NOTE geo.frustum only builds BOTTOM-WIDE cones (r_top > r_bottom sends its apex
    # height negative and it comes out inverted) -- the top cutter is the bottom one
    # mirrored, never frustum(small, big, h).
    lo = frustum(BORE / 2 + CH, BORE / 2, CH)        # bore mouth at z 0
    hi = frustum(BORE / 2 + CH, BORE / 2, CH)        # ... mirrored to z T
    hi.apply_transform([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, T], [0, 0, 0, 1]])
    return _zmin0(sub(sub(w, lo), hi))

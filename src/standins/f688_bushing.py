"""hw_f688_bushing plastic stand-in -- a flanged PLAIN JOURNAL BEARING replacing the
bought F688ZZ (8x16x5, flange 18x1). See the package docstring for the programme and
LOAD LIMITS; this module owns the bearing-specific reasoning.

Two per end idler x4 = 8. The idler seat was probe-measured off `tracks.build_tracks()`
(never trusted to prose): outboard face x 117.4, inboard 87.4 (30 wide), flange recess
O18.5 x 1.025 deep at BOTH faces, bore land O16.05 running depth 1.025..28.975 (27.95
long) with 3 axial crush ribs at 0/120/240 deg cresting O15.80.

WHAT THIS PART IS. A ball bearing spins on rolling elements and locates its wheel to a
few microns. This spins PLA on PLA. So the design targets are not the bearing's -- they
are: (1) the idler MUST turn, (2) it must stay roughly centred, (3) it must go in
without splitting the idler rim, (4) it must hold grease. Everything below serves one
of those four.

THE TOLERANCE STACK IS THE WHOLE PROBLEM (and it is what the 2026-07-15 v1 got wrong).
The repo's own calibration -- seam_dowel's note, and threads.py's `clear` 0.25 radial --
is: a printed BORE comes out 0.1-0.2 UNDER, a printed SHAFT/OD 0.1-0.2 OVER. Both
mating parts here are printed PLA on the same machine, so the errors ANTI-CORRELATE:
a hot/over-extruding day shrinks the idler bore AND grows this part at the same time.
v1 ignored that on all three interfaces, and all three were wrong:

  * BORE O8.3 on the O8.0 printed shank -> real 8.10..8.20 shank in a real 8.10..8.20
    bore = ZERO clearance, worst case interference. A journal bearing that cannot turn
    is not a bearing. THE defect. Now O8.6: real clearance 0.2..0.4 diametral, i.e. it
    always spins, and 0.4 of slop on a free idler is taken up by track wrap anyway.
  * OD 15.85 -> real 15.95..16.05 pressed into a real bore WALL of 15.85..15.95: it
    JAMS ON THE WALL and never reaches the ribs -- the exact rim-splitting failure the
    idler's crush ribs were added to prevent. The ribs only work for a GROUND O16.000
    OD (+-0.008); a printed OD cannot land in a 0.25-wide window against a bore moving
    the other way. Fix below.
  * FLANGE O18.2 -> real 18.30..18.40 into a real O18.5 recess of 18.30..18.40 = binds,
    so the flange never seats and the OD never engages its land. Now O17.9 (= the real
    F688's O18.0 flange nominal): real 18.0..18.1, clears by 0.2..0.4. The flange is an
    axial stop, not a locator -- loose is CORRECT.

OD: COMPLIANCE MOVES ONTO THIS PART. The body is undercut to O15.2 so it can never
touch anything (real 15.3..15.4 vs the idler's real rib crest 15.60..15.70), and the
press is carried by 3 crush ribs of OUR OWN cresting O16.0 -- which is exactly the
bought bearing's nominal OD, so the CAD fit is unchanged (0.2 diametral into the idler
ribs, 0.05 clear of its wall). Printed, our ribs land at 16.10..16.20 against a real
wall of 15.85..15.95: 0.075..0.175 radial interference, textbook crush-rib range, and
ALWAYS an interference no matter which way the stack falls. Where our ribs meet the
idler's instead, it is 0.2..0.3 radial -- firmer, still a crush, and both features are
small sacrificial ribs that yield before either rim does. 3-on-3 at 120 deg has a
useful property: both patterns are 120-symmetric, so either ALL THREE ribs meet ribs or
ALL THREE meet wall -- never a mixture. The crush stays symmetric at any insertion
clocking, so centring survives. Rounded (tangent-circle) crests, per the idler's own
lesson: a square rib shaves a chip that packs behind the bearing.

Press force is deliberately NOT chased. On a PLAIN bearing the press is not a load path
and not an anti-rotation duty: if the bushing creeps and turns in its seat instead of on
the shank, that is simply a second journal and the idler still rolls. The press only has
to centre it and stop it walking out. (Walk-out is already covered outboard -- the M8
head sits 1.0 off the wheel face, probed -- and the inboard flange cannot fall inward.)

GREASE + WEAR. Dry PLA on PLA galls: it transfers material, then picks up and seizes.
So the bore carries 3 blind AXIAL grease grooves at 60/180/300 deg (clocked 60 off the
OD ribs so each rib's load path lands on a full journal land, not a groove). Axial, not
circumferential, on purpose: a groove perpendicular to the sliding direction SCRAPES
wear debris off the shank every revolution and holds it, where a circumferential groove
runs parallel to the motion and sweeps nothing. Blind at both ends so the grease stays
in. GREASE THEM ON ASSEMBLY -- this is not optional, it is the part's service life.

WHY NOT A PRINTED BALL BEARING: it needs O2-3 balls in the 4 mm race annulus, and the
package already settled this physics for hw_pan_ring -- printed spheres need support on
the lower hemisphere and come out scarred. A scarred PLA ball rolling on an FDM-rough
race, with the 0.3+ print-in-place gaps it would need, is not obviously lower-friction
than a greased plain journal, and it is 8x the print risk on a part that gets binned the
day the F688ZZs land. WHY NOT TWO-PIECE: buys nothing -- see the print note, the
one-piece is already fully self-supporting.

PRINT: flange-DOWN, bore vertical, NOSUP, and there is no overhang anywhere (the flange
is the widest section and it is on the bed; the step up to the body faces UP; the ribs
are vertical extrusions; the grooves are vertical; the only ceilings are the grooves'
3 blind tops, ~1.3 wide, which bridge). Flange-down puts the bore's ELEPHANT FOOT at
z 0, which would pinch the shank -- so the 0.6 x 45 deg bore lead-in chamfer at z 0 is
not just an entry aid, it deletes the squeezed first layers from the journal entirely.
The matching top chamfer lets the shank enter square from either side, and the 45 deg
cone on the leading OD edge ramps the crush ribs in progressively instead of shearing
them off on the rim.

Bore roundness is the one thing orientation cannot fix: a vertical bore prints round but
carries one Z-seam witness line. Burnish it in with a greased O8 bolt before assembly.
"""
import numpy as np
from trimesh.transformations import rotation_matrix

from geo import cyl, frustum, inter, sub, uni
from ._common import _zmin0

COUNT = 8
NAME = "hw_f688_bushing"

TAU = 2 * np.pi

# --- the mating seat, PROBE-MEASURED off tracks.build_tracks() (see docstring) -------
SEAT_WALL_D = 16.05     # idler bore land
SEAT_RIB_D = 15.80      # its 3 crush-rib crests, 0/120/240 deg
RECESS_D = 18.5         # flange recess, both faces
RECESS_DEEP = 1.025     # depth below the face -> our flange must be thinner than this

# --- this part -----------------------------------------------------------------------
SHANK_D = 8.0           # hw_m8_bolt's plain journal (threads.py leaves it smooth here)
BORE_D = 8.6            # +0.6 nominal = 0.2..0.4 real running clearance. See docstring.
BODY_D = 15.2           # undercut: never touches the seat, ribs do all the work
RIB_CREST_D = 16.0      # = the real F688ZZ's ground OD, so the CAD fit is unchanged
RIB_N = 3               # 120-symmetric against the idler's 3 -> crush stays symmetric
RIB_SECTION_R = 0.7     # tangent-circle crest (rounded, per the idler's chip lesson)
FLANGE_D = 17.9         # real F688 flange nominal; loose in the O18.5 recess BY DESIGN
FLANGE_H = 0.9          # < RECESS_DEEP 1.025 -> seats below flush, never proud
BODY_H = 5.9            # flange 0.9 + 5.0 of body = the real F688's 5.0 in-bore width
CHAMFER = 0.6           # 45 deg, on both bore mouths and the leading OD edge
GROOVE_N = 3
GROOVE_SECTION_R = 0.7  # cuts ~0.45 deep x ~1.3 wide into the bore wall
GROOVE_DEPTH = 0.45


def build():
    """Flanged plain bushing: flange-down (O17.9 x 0.9 at z 0..0.9), body to z 5.9 on
    3 crush ribs cresting O16.0, O8.6 journal with 3 blind axial grease grooves."""
    br = BORE_D / 2.0

    # ---- body + crush ribs -----------------------------------------------------------
    body = cyl(BODY_D / 2.0, BODY_H)
    body.apply_translation((0, 0, BODY_H / 2.0))
    solid = body
    rib_dc = RIB_CREST_D / 2.0 - RIB_SECTION_R        # tangent circle: crest at
    for k in range(RIB_N):                            # rib_dc + section_r, root buried
        aa = TAU * k / RIB_N                          # inside the O15.2 body
        rb = cyl(RIB_SECTION_R, BODY_H)
        rb.apply_translation((rib_dc * np.cos(aa), rib_dc * np.sin(aa), BODY_H / 2.0))
        solid = uni([solid, rb])                      # pairwise, per the CSG rules

    # ---- 45 deg lead-in cone on the leading (top) OD edge: ramps the ribs in ---------
    keep = cyl(FLANGE_D, BODY_H - CHAMFER)            # r >> any feature: only the cone
    keep.apply_translation((0, 0, (BODY_H - CHAMFER) / 2.0))   # bites, below it keep all
    cone = frustum(RIB_CREST_D / 2.0, RIB_CREST_D / 2.0 - CHAMFER, CHAMFER)
    cone.apply_translation((0, 0, BODY_H - CHAMFER))
    solid = inter(solid, uni([keep, cone]))

    # ---- flange ---------------------------------------------------------------------
    flg = cyl(FLANGE_D / 2.0, FLANGE_H)
    flg.apply_translation((0, 0, FLANGE_H / 2.0))
    solid = uni([solid, flg])

    # ---- journal bore + both 45 deg lead-ins (the z0 one also deletes elephant foot) --
    cut = cyl(br, BODY_H + 4.0)
    cut.apply_translation((0, 0, BODY_H / 2.0))
    lead_lo = frustum(br + CHAMFER, br, CHAMFER)       # widens downward to z 0
    cut = uni([cut, lead_lo])
    lead_hi = frustum(br + CHAMFER, br, CHAMFER)       # frustum only narrows upward, so
    lead_hi.apply_transform(rotation_matrix(np.pi, (1, 0, 0)))   # flip it: now z -0.6..0
    lead_hi.apply_translation((0, 0, BODY_H))          # -> widens upward to z BODY_H
    cut = uni([cut, lead_hi])

    # ---- blind axial grease grooves, clocked 60 deg off the ribs ---------------------
    g_dc = br + GROOVE_DEPTH - GROOVE_SECTION_R        # deepest point at br + depth
    g_h = BODY_H - 2.0 * (CHAMFER + 0.4)              # blind: stops short of both mouths
    for k in range(GROOVE_N):
        aa = TAU * (k + 0.5) / GROOVE_N               # +0.5 -> 60/180/300 deg
        gv = cyl(GROOVE_SECTION_R, g_h)
        gv.apply_translation((g_dc * np.cos(aa), g_dc * np.sin(aa), BODY_H / 2.0))
        cut = uni([cut, gv])

    return _zmin0(sub(solid, cut))

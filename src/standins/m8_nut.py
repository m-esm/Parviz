"""hw_m8_nut plastic stand-in. See the package docstring for rationale + LOAD LIMITS.

REAL THREAD (2026-07-16, user: "as close to reality of their metal counterparts as
possible"). This part was the worst stand-in in the set: an AF13 hex with a plain
Ø7.8 bore, pressed 0.2 onto the Ø8 shank. A press fit cannot hold tension preload --
PLA creeps on an interference at room temperature -- so the FRONT (tensioning) end
axles could not be tensioned at all and the dry track ran slack BY DESIGN.

It is now a real M8x1.25 nut: `threads.thread_solid(8.0, internal=True)` cut through
the full height, mating the same ISO form `hw_m8_bolt` carries (both take threads.py
defaults -- d_nom 8.0, coarse_pitch -> 1.25, clear 0.25 -- so the pair is defined in
ONE place; do not hand-pick a pitch here). A thread holds preload through FORM, not
friction: it can be tightened, it cannot creep off the shank, and it assembles exactly
like the metal NYLOC it stands in for. See LOAD LIMITS in the package docstring for
what that does and does not buy.

GEOMETRY, all probed against the real cage (`chassis.py`, the ledge+roof strips on the
side-panel end towers) rather than taken from the old comments:
  AF 13.0    the metal NYLOC's across-flats. The cage gap is 13.40 (probed: solid
             z 28.62..31.62 ledge / 45.02..46.00 roof, so the free span is exactly
             13.40 at the axle line za 38.32) -> 0.20 rotational slop per flat, which
             is what lets you turn the BOLT HEAD from outboard while the nut is held.
             Across-CORNERS is then 15.01 in Y, and the front cage window is
             ey-9.8..ey+14.3 while the axle travels ey-2..ey+6.5 in the tension slot:
             at both stroke ends the corners clear the cage end walls by 0.30. AF may
             NOT grow -- 13.0 is the size the window was cut for.
  h 6.0      4.20 turns of full-form thread (6.0 minus the two countersinks; a metal
             DIN934 M8 is 6.8 tall / ~5 turns, the old stand-in had 0). 6.0 is the
             CAGE MAXIMUM, not a preference:
             the strips run x 54.5..64.95, the tower's inboard bearing face is x 62.0
             (probed) and the Ø14.4 washer takes 60.5..62.0, so a caged nut spans
             60.5..54.5. Taller = the flats hang out of the strips and the nut can
             spin. NOTE the bolt, not the nut, is what limits real engagement today --
             see BOLT REACH below.
  chamfers   45deg corner chamfers on both faces (chamfer circle Ø13.81, so the flats
             keep their full 13.0 width -- the cutter starts outside them) + a 45deg
             countersink at each end of the bore, opening to Ø9.0. The countersink is
             the lead-in: it lets the bolt find the thread square from either face,
             and it removes the ragged turn where the helix runs out at the face.
             Ø9.0 and no wider: a countersink EATS thread (0.375 of depth per face),
             and Ø9.0 already clears the bolt's Ø7.75 crest by 0.625 radially -- a
             bigger mouth buys lead-in that is already there and pays in turns.
             45deg everywhere on purpose: the nut prints flat, so the bottom-face
             chamfer and countersink are overhangs, and 45 is the FDM limit.

BOLT REACH (finding, 2026-07-16 -- NOT fixable in this file): the modeled stack puts
the bolt-head underside at x 118.4 and the nut's outboard face at x 60.5, i.e. 57.9 of
grip, while both the BOM's M8x60 and `hw_m8_bolt`'s 60.4 shank end at x 58.0. Only
2.5 mm of this nut's 6.0 of thread is reachable -- 2 turns. It still holds hand preload
with margin (2.5 mm of PLA M8 thread shears at ~1.1 kN vs the ~200-400 N a hand-tight
plastic M8 reaches), but it is thread-count-poor and concentrates creep in two turns.
An M8x70 (shank ~65+) would engage the nut fully. The nut is threaded through its whole
height, so it works either way -- it just gets better with a longer bolt.

PRINT: lies flat, thread axis VERTICAL (threads.py's rule -- a vertical ISO thread is
a spiral of ~30deg overhangs and self-supports; horizontal it smears). NOSUP, and both
overhanging features (the bottom corner chamfer, the bottom countersink) are 45deg.
Plate 20 slices 'Success.'. GATE NOTE: this part needs a `wallcheck.WHITELIST` entry
(it cannot pass the 0.8 p1 wall gate and neither can any other real thread) -- the ISO
crest flat is p/8 = 0.156 wide by definition, and the thread's run-out at the
countersink mouth feathers to ~0.02, exactly as the incomplete thread on a metal nut
does. Neither is a wall: both are fully-backed ridge tips, the same class as the
whitelisted gear tooth tips, and the nut's real section (flat to bore) is 2.375. The
measured p1 jitters 0.09-0.19 with where the countersink happens to truncate the helix,
so the floor wants to sit at ~0.08, not at the measured value.

NO NYLOC ANALOGUE, deliberately. A nylon insert has no honest plastic equivalent: a
deliberately-tight last thread (the all-metal "distorted nut" trick) does not spring
back in PLA -- the bolt shaves it on first assembly, the locking is gone for good and
the swarf lands in the thread. It is also close to redundant here: the cage grips the
flats, so this nut CANNOT rotate. The only back-off mode left is the bolt turning, and
on a desk robot for the weeks until the metal lands, re-snugging the tension nut (which
you adjust anyway) beats a feature that self-destructs on the first turn.
"""
import numpy as np

from geo import R, cyl, frustum, sub
from threads import thread_solid

from ._common import _zmin0

COUNT = 8             # 4 inner cage nuts + 4 outboard tower-clamping jam nuts
NAME = "hw_m8_nut"

AF = 13.0          # across-flats: the cage window (13.40 gap) was cut for exactly this
H = 6.0            # cage maximum (see the module docstring)
D_NOM = 8.0        # threads.py owns the pitch (coarse_pitch(8.0) = 1.25) and the clear
CH = 0.6           # 45deg corner chamfer depth -> chamfer circle Ø13.8 (flats untouched)
CS_R = 4.5         # countersink mouth radius (Ø9.0), 45deg down to the thread crest


def _corner_chamfer(nut, z_face, up, r_circ):
    """Cut a 45deg chamfer into the hex CORNERS at one face (`up` = +1 top / -1
    bottom). The cutter is the band outside a 45deg keep-cone, so it only ever
    touches material further out than the chamfer circle -- the AF 13.0 flats the
    cage grips are left at full width."""
    r_ch = r_circ - CH                                  # 6.906 = Ø13.81 > AF/2 6.5
    band = cyl(r_circ + 2.0, CH)
    band.apply_translation((0, 0, z_face - up * CH / 2))   # the band sits INSIDE the
    #                                                        part, not past the face
    cone = frustum(r_ch + CH, r_ch, CH)                 # r_ch+CH at z0 -> r_ch at z=CH
    if up > 0:
        cone.apply_translation((0, 0, z_face - CH))     # wide low, narrow at the face
    else:
        cone.apply_transform(R(np.pi, (1, 0, 0)))       # flip: narrow at the face,
        cone.apply_translation((0, 0, z_face + CH))     # widening upward
    return sub(nut, sub(band, cone))


def _countersink(nut, z_face, up, r_th):
    """45deg lead-in at one end of the bore: Ø9.0 at the face, blending into the
    thread crest radius `r_th` at depth (CS_R - r_th)."""
    d = CS_R - r_th
    # geo.frustum only narrows with +z (r_bottom > r_top; passing r_top > r_bottom
    # puts the apex BELOW the base and returns garbage that grew the nut's volume) --
    # so always build the narrowing cone and flip it for the top face.
    cone = frustum(CS_R, r_th, d)                       # CS_R at z0 -> r_th at z=d
    if up > 0:
        cone.apply_transform(R(np.pi, (1, 0, 0)))       # CS_R at z0 -> r_th at z=-d
        cone.apply_translation((0, 0, z_face))
    else:
        cone.apply_translation((0, 0, z_face))
    return sub(nut, cone)


def build():
    r_circ = AF / np.sqrt(3.0)                          # 7.506 circumradius -> AC 15.01
    nut = cyl(r_circ, H, sections=6)
    nut = _zmin0(nut)
    # REAL M8 internal thread, cut through both faces (the cutter over-runs 1.0 each
    # end) so there is no unthreaded lip for the bolt to jam on.
    cut = thread_solid(D_NOM, H + 2.0, internal=True)
    cut.apply_translation((0, 0, -1.0))
    nut = sub(nut, cut)
    r_th = D_NOM / 2.0 + 0.125                          # internal crest = major/2 + clear/2
    for z_face, up in ((H, 1), (0.0, -1)):
        nut = _corner_chamfer(nut, z_face, up, r_circ)
        nut = _countersink(nut, z_face, up, r_th)
    return _zmin0(nut)

"""hw_m8_bolt plastic stand-in -- the M8x60 END BOLT-AXLES (track front/rear idlers).

REAL THREAD (2026-07-16, user: "as functional and as close to reality of their metal
counterparts as possible"). The old part was `_bolt(4.0, 60.4, 6.5, 5.3)` -- a plain
O8 rod with a O13 disc on the end. It was a locator: nothing screwed onto it, and its
head could not be turned by any human hand or tool. This one is a real partially
threaded screw: `hw_m8_nut` (same threads.py, stock M8 coarse 1.25, clear 0.25) runs
down the thread and can be tightened.

WHY PARTIALLY THREADED -- the stack-up (probed off the real geometry, world x, R side;
the L side mirrors and the REAR axle is identical except its tower bore is a O8.4
teardrop instead of the tension stadium):

     x  126.4 | head, outboard face .................. z 0    (bed)
     x  118.4 | head, inboard face ................... z 8.0
     x  117.4 | idler wheel outer face + F688 bushing . 1.0 RUNNING GAP -- see below
     x  112.4 | outer bushing, inboard face
     x   92.4 | inner bushing, outboard face
     x   87.4 | inner bushing, inboard face ........... O8.3 bore rides this journal
     x   70.0 | end-tower, outboard face
     x   62.0 | end-tower, inboard face .............. z 64.4  THREAD STARTS HERE
     x   60.5 | washer (60.5..62), then the nut inboard of it
     x   48.4 | tip .................................. z 78.0

The journal must stay a smooth O8.0 from the head all the way to x 62: it is a BEARING
SURFACE under both F688 bushings (bore O8.3 = 0.3 diametral running clearance) and a
SLIDING fit through the tower's O8.4 tension slot. A thread anywhere in that run would
chew the bushing bore and rattle 0.65 diametral in the slot. So the thread is confined
to x 48.4..62.0 -- inboard of the tower, exactly where the washer and nut live. This is
what a real partially threaded bolt does, for exactly this reason.

LENGTH: shank 70.0 (head inboard face 118.4 -> tip 48.4) = **M8x70, not M8x60**. The
BOM's M8x60 is TOO SHORT for its own stack: a 60 shank puts the tip at x 58.4, and the
M8 NYLOC (8.0 thick, bearing on the washer at 60.5, so spanning 52.5..60.5) would be
engaged over only 2.1 of its 8.0 -- the nylon insert sits at the far end and would
never be reached, i.e. the "NYLOC required" line in docs/ASSEMBLY.md buys a locking
feature the geometry cannot use. M8x70 engages it fully with 4.1 of tip protrusion.
The stand-in is modelled at the length the metal part SHOULD be; see the report.

HEAD = a KNURLED THUMB HEAD (O22 x 8, 20 axial flutes), not the metal part's AF13 hex.
Deliberate: this head is the outboard hubcap AND, on the front pair, the thing you turn
to tension the track. A plastic AF13 hex rounds off under a 13 mm spanner on the first
real pull, and hand-tight is this part's ceiling anyway (see LOAD LIMITS in the package
docstring), so a finger grip is strictly more useful than a faithful-but-unusable hex.
It also prints as its own raft: a O22 disc on the bed under a 78 mm slender column.
Probed CLEAR -- first contact with the track links is at O32, so O22 keeps 5.0 mm
radial margin at the nominal loop position.

The head does NOT clamp: its inboard face keeps a 1.0 gap to the wheel face (117.4). It
is a retainer, not a clamp face -- the idler has to spin. That gap is deliberate and is
also the reason this bolt CANNOT preload the track; see the report / the package
LOAD LIMITS. The thread makes the BOLT-TO-NUT joint real; it does not close the 17.4 mm
hole in the middle of the clamp stack (tower outboard face 70.0 -> inner bushing 87.4),
which is a design gap that bites the metal M8 just as hard as the printed one.

PRINT: head-down, thread up, axis VERTICAL (mandatory -- a vertical thread is a spiral
of ~30 deg overhangs and is fully self-supporting; laid down it smears). NOSUP. The
O22 head gives a wide first layer, but the part is still 78 tall on a O8 column: keep
the 5 mm brim, and print it with the other stand-ins so the column gets travel-time to
cool rather than being hammered layer-on-layer.

GATES -- two EXPECTED deltas this rework causes, neither is a defect (see the report):
  * `make invariants` "stand-in interface dims" asserts ext(hw_m8_bolt)[2] == 65.7.
    The correct value is now **78.0** (M8x70 shank + 8.0 thumb head). checks.py is
    owned elsewhere; it needs that constant updated.
  * `make wallcheck` flags p1 0.36 < 0.80. An ISO M8 coarse CREST FLAT is p/8 =
    0.156 mm BY DEFINITION -- no real thread can pass a 0.8 mm wall gate, and the
    O8.0 rod under the crests is solid. Same class as the already-whitelisted
    `tilt_worm.stl` (0.2, "thread run-out feathers"). Needs a WHITELIST entry:
        "hw_m8_bolt.stl": (0.3, "ISO M8 coarse crest flats (p/8 = 0.156 by "
                                "definition) + the 45deg tip lead-in that slices "
                                "them; the shank under them is solid O8.0"),
    Every other threaded stand-in will need the same treatment.
"""
import numpy as np

from geo import cyl, frustum, sub, uni
from threads import coarse_pitch, thread_solid

COUNT = 4
NAME = "hw_m8_bolt"

# --- stations, world x on the R side (probed; see the docstring diagram) ---
_X_HEAD_OUT = 126.4
_X_HEAD_IN = 118.4      # 1.0 running gap to the wheel/bushing face at 117.4
_X_TOWER_IN = 62.0      # thread starts here: inboard of the O8.4 tension slot
_X_TIP = 48.4           # full engagement of an 8.0-thick NYLOC bearing at 60.5

SHANK_D = 8.0           # the agreed interface: f688_bushing bore O8.3 runs on this,
                        # and the towers' O8.4 slot/bore slides on it
HEAD_D = 22.0           # 5.0 radial margin to the track links (first contact O32)
HEAD_H = _X_HEAD_OUT - _X_HEAD_IN               # 8.0
JOURNAL_L = _X_HEAD_IN - _X_TOWER_IN            # 56.4 -- smooth, no thread
THREAD_L = _X_TOWER_IN - _X_TIP                 # 13.6

_KNURL_N = 20           # flutes: vertical in the print orientation, zero overhang
_KNURL_R = 1.1
_TIP_CHAM = 1.0         # lead-in so the nut starts square


def build():
    """Head-down M8x70: knurled thumb head z 0..8, smooth O8 journal to z 64.4,
    real ISO M8 coarse thread z 64.4..78.0, chamfered tip."""
    hd = cyl(HEAD_D / 2, HEAD_H)
    hd.apply_translation((0, 0, HEAD_H / 2))
    for k in range(_KNURL_N):                    # scalloped grip, cut from the rim
        a = 2.0 * np.pi * k / _KNURL_N
        fl = cyl(_KNURL_R, HEAD_H + 2.0)
        rr = HEAD_D / 2 + _KNURL_R * 0.45        # bite ~55% of the flute into the rim
        fl.apply_translation((rr * np.cos(a), rr * np.sin(a), HEAD_H / 2))
        hd = sub(hd, fl)

    sh = cyl(SHANK_D / 2, JOURNAL_L)
    sh.apply_translation((0, 0, HEAD_H + JOURNAL_L / 2))

    th = thread_solid(SHANK_D, THREAD_L, pitch=coarse_pitch(SHANK_D), clear=0.25)
    th.apply_translation((0, 0, HEAD_H + JOURNAL_L))

    m = uni([hd, sh])
    m = uni([m, th])

    # TIP LEAD-IN so the nut starts square: subtract the complement of a frustum that
    # narrows going UP (r 4.0 at the chamfer root -> 3.0 at the tip). NOTE the two
    # helpers disagree on origin -- geo.cyl is z-CENTRED, geo.frustum runs z 0..h --
    # so the outer cylinder is lifted h/2 to share the frustum's z 0..h before the
    # ring is cut. (Getting this wrong put a full disc across the shank and sheared
    # the tip off as a second body: build() asserts body_count == 1 below.)
    top = HEAD_H + JOURNAL_L + THREAD_L
    outer = cyl(SHANK_D, _TIP_CHAM)
    outer.apply_translation((0, 0, _TIP_CHAM / 2))
    ring = sub(outer, frustum(SHANK_D / 2, SHANK_D / 2 - _TIP_CHAM, _TIP_CHAM))
    ring.apply_translation((0, 0, top - _TIP_CHAM))
    m = sub(m, ring)
    assert m.body_count == 1, "hw_m8_bolt must print as ONE body, got %d" % m.body_count
    return m

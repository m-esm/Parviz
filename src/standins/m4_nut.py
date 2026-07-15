"""hw_m4_nut plastic stand-in -- a REAL threaded M4 nut (2026-07-16). See the package
docstring for the rationale + the LOAD LIMITS this part now partly lifts.

WAS: `_hex_nut(7.0, 3.2, 3.7)` -- an AF7 hex with a plain Ø3.7 bore that PRESSED onto
the Ø3.9 shank. That is a location feature, not a fastener: nothing but a 0.2 diametral
PLA-on-PLA interference held the road wheel on its axle, and PLA creeps, so the grip
decayed in hours. NOW: a real ISO-form 60-deg internal thread (src/threads.py) that
SCREWS onto hw_m4_bolt's threaded tail. It can be tightened, backed off and re-used,
and it holds the wheel through thread form instead of friction -- i.e. the road-wheel
axles now assemble exactly the way the metal M4x40 + M4 nut will.

THE SLOT OWNS EVERY DIMENSION HERE. The nut is captive in the wheel beam's M4 slide-up
slot (chassis.py, `roadwheel_ys` loop): a 3.6 (x) x 7.3 (y) pocket, open at the block
base, top stop z 23.65. All three numbers are probed, not assumed:
  * AF 7.0 -- the slot's 7.3 y-walls ARE the wrench (they take the reaction torque; no
    tool ever touches this nut). The stop is at rr_z + AF/sqrt(3) = 23.641, i.e. the
    slot is cut for an AF-7 hex ACROSS CORNERS, so pushing the nut home centres it on
    the Ø4.4 bore axis at z 19.6. Change AF and the nut no longer lands on the bore.
  * THK 3.2 -- an x scan of the built panel puts the free band at x 73.9..77.5 = 3.60
    exactly. A taller nut WOULD carry more thread, but 3.4 leaves 0.1/side, under the
    FDM reality gap (the same 0.25-class error threads.py budgets radially), and it
    would stop being a 1:1 swap for the DIN 934 M4 nut (m = 3.2) the slot was cut for.
    So the answer to "would taller be better" is: the slot says no. 3.2 keeps 0.2/side.
  * The hex is oriented FLATS -> +-y, so its +-x vertices span z: the leading feature
    going up the slot is a CORNER, which self-wedges past the 0.35 crush nibs at
    z 16.4 with no extra lead-in on the hex.

Thread: d_nom 4.0 / coarse_pitch -> 1.0 / clear 0.25, all threads.py defaults -- the
printed pair only ever mates with itself, so bolt and nut MUST NOT pick their own.
3.2 mm at 1.0 pitch is 3.2 turns, and the two 0.35 chamfers leave ~2.5 turns of full
form. Shear area at the major dia is ~pi*4*2.5*0.55 = 17 mm^2; interlaminar PLA shear
(~25 MPa -- the nut prints thread-axis-vertical, so a stripping thread shears ACROSS
layers, the weak direction) puts the strip load near 400 N. The wheel it retains
carries ~1 N. It will strip long before a metal M4's ~2 kN hand-tight preload, so
snug it, don't torque it.

PROBED (2026-07-16, against the built chassis panels + a threads.py male form):
  * seated at the slot's top stop, ALL 10 stations (5 per side): 0.0000 mm^3.
  * pushed through the crush nibs: 1.5360 mm^3 = exactly 0.2/side on the two 0.35
    nibs -- the designed crush. Seated ABOVE them the nut reads 0.0000, because at
    the nib band the hex is already into its corner taper; the nibs sit under the
    taper and it can only fall back by re-crushing them. That is the retention.
  * anti-rotation: the flats bind on the 7.3 walls at ~5 deg (0.0064 mm^3 first
    touch; 3 deg is still free). The slot is the wrench.
  * MATE with the threads.py male form, full turn in 30-deg steps: rotate AND
    advance pitch*deg/360 -> 0.0000 mm^3 at every step; rotate WITHOUT advancing
    (helical phase deliberately broken) -> up to 1.9058 mm^3. The interlock is
    real, not a vacuous zero.
  * hw_m4_bolt COORDINATION: seated, this nut occupies x 74.25..77.45 while the
    M4x40 shank runs x 71.4..111.4 (tracks.py) -- so the thread must reach from the
    tip to ~6.5 mm up it. Everything past x 81 is the road wheel's plain journal.

Print: lies flat, thread axis VERTICAL (threads.py's hard requirement -- a vertical
thread is a spiral of ~30-deg overhangs and is self-supporting). NOSUP; the plate
slices clean. The 45-deg lead-in cones are printable both ways up: the top one is a
plain countersink, the bottom one a cone at exactly 45 deg.

WALLCHECK: this part reads p1 0.11 and needs a WHITELIST entry it does not have yet
(see the report -- wallcheck.py is not this module's to edit). The thin population is
NOT a defect and NOT a wall: a 20k-sample census puts 100% of it in the thread band
(r 1.55..2.15), i.e. it is the ray gate measuring flank-to-flank ACROSS a V-tooth,
which by ISO 68-1 tapers to a p/4 = 0.25 crest land. Every real thread, cut or
rolled, has this section; the tooth is supported along its whole helical length by
the core, the crest never touches the bolt (0.25 radial clearance), and the median
self-thickness is 2.135 = the solid hex wall from thread root to flat. Same class as
the worm run-out wedges and the 14T sprocket tooth tips already whitelisted.
"""
import math

from geo import cyl, frustum, sub
from threads import coarse_pitch, thread_solid

from ._common import _zmin0

COUNT = 10
NAME = "hw_m4_nut"

D_NOM = 4.0                      # M4. clear/pitch stay threads.py defaults: the
CLEAR = 0.25                     # printed nut and printed bolt mate ONLY with each
PITCH = coarse_pitch(D_NOM)      # other, so both sides must read them from one place.
AF = 7.0                         # across-flats == the slide-up slot's wrench
THK = 3.2                        # DIN 934 M4 height; slot free band is 3.60 (probed)
CHAM = 0.35                      # 45-deg lead-in per face: starts the bolt square


def build():
    """AF7 x 3.2 hex blank, tapped with a real M4 x 1.0 internal thread, chamfered
    both faces so the bolt cannot cross-start. Axis +Z, z 0..THK."""
    blank = cyl(AF / math.sqrt(3.0), THK, sections=6)   # circumradius from AF
    blank.apply_translation((0, 0, THK / 2.0))

    # TAP. thread_solid(internal=True) is the NEGATIVE: the male form grown by
    # clear/2 plus its bore column, trimmed to z 0..THK. Subtracting it leaves the
    # mating female thread -- do NOT drill a plain bore first, the cutter carries
    # its own core (r_val + 0.02) and a pre-drill at the major dia would eat the
    # crests it is supposed to form.
    cut = thread_solid(D_NOM, THK, pitch=PITCH, internal=True, clear=CLEAR)
    nut = sub(blank, cut)

    # LEAD-IN. A flat-cut first thread is a knife edge that cross-starts and peels
    # off on the way in (and it is the layer the printer lays down worst). A 45-deg
    # cone per face opens the mouth to Ø4.7 and gives the bolt a cone to centre on,
    # which is exactly what the metal nut's 120-deg washer-face chamfer does.
    r_out = D_NOM / 2.0 + CHAM                          # 2.35 at the face
    r_in = D_NOM / 2.0                                  # 2.00 at chamfer depth
    bot = frustum(r_out, r_in, CHAM)                    # opens downward, 45-deg
    top = frustum(r_out, r_in, CHAM)
    top.apply_transform([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, THK], [0, 0, 0, 1]])
    return _zmin0(sub(sub(nut, bot), top))

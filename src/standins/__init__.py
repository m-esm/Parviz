"""PLASTIC HARDWARE STAND-INS -- print-oriented substitutes for the BUY-LIST metal
hardware, so the robot dry-assembles fully before the order arrives (2026-07-15,
user: "include all items in the export so I would just assemble with plastic till I
get actual metal parts"; REWORKED 2026-07-16, user: "as functional and as close to
reality of their metal counterparts as possible").

The BOM is UNCHANGED -- these are interim parts, replaced 1:1 by the real metal.
Export-only: none are scene nodes (the assembly GLB keeps the silver axle_hw_/
pan_balls/tilt_axle placeholders), so the interference/fit/nav gates are untouched.
EXPORT=1 writes them to stl/hardware/ and export_bambu packs the "Hardware
stand-ins" plate. ONE MODULE PER PART -- each file carries its own rationale.

THE 2026-07-16 REWORK, and the rule it produced. The v1 set was ALL THREADLESS
push/press fits, and three parts turned out to be not merely crude but UNBUILDABLE
or UNUSABLE -- because they had inherited NOMINAL METAL DIMENSIONS with no print
compensation, which looks perfect in CAD:
  * hw_tilt_axle  Ø5.000 into the Ø5.000 STEEL 695 bore = +0.000. Printed pegs come
                  out 0.1-0.2 OVER. It could not be assembled at all.
  * hw_f688_bushing  bore Ø8.3 on a Ø8.0 shank, OD 15.85 in a 15.85-15.95 wall: BOTH
                  halves print, and their errors ANTI-CORRELATE (bores land under,
                  shafts/ODs land over), so all three of its fits closed to
                  zero-or-interference. It could not spin.
  * hw_m8_washer  a round Ø14.4 disc overlaps the tower nut cage by 5.2 mm^3 -- the
                  seat it was drawn for was deleted by running-gear v2 in 2026-07-14.
  * hw_pan_ring   the torus SLID rather than rolled: ~96 mNm of stiction against the
                  pan stage's ~15-17 mNm. The interim pan joint could not have moved.
RULE: a stand-in mates PRINTED-TO-PRINTED or PRINTED-TO-STEEL, never nominal-to-
nominal. Budget 0.1-0.2 per printed surface, put the compliance on the PRINTED part
(crush ribs beat a tight window), and PROBE the real mating geometry -- do not copy
the metal part's numbers or the CAD placeholder's.

REAL THREADS (src/threads.py) are what turn these from locators into fasteners: the
M4 and M8 pairs now screw together (verified: 0.0000 mm^3 through a full screw
motion, and a real collision when the helical phase is broken). M8 keeps stock 1.25;
M4 is COARSENED 0.7 -> 1.0 because 0.7 does not survive a 0.4 nozzle -- printed pairs
only ever mate with each other, so it costs nothing.

The parts:
  hw_m4_bolt   x10  M4x40 road-wheel bolt-axle, as a real SHOULDER bolt: plain Ø3.9
                    journal (34.7) + M4x1.0 threaded tail (5.3). The shoulder is the
                    axial stop -- the journal cannot enter the nut's Ø3.20 minor, so
                    torque reacts shoulder->nut->slot INBOARD of the wheel and the
                    wheel stays free however hard it is done up. Ø10.4 thumb head
                    (AF7 rounds off in PLA, and the disc doubles the bed footprint
                    under a 43.5-tall head-down print). NOTE: a stock DIN 931 M4x40's
                    ~18 mm shoulder would start thread INSIDE the wheel -- the stack
                    wants ~35. The printed part is better than the metal it stands in
                    for; on arrival either accept crest-riding or fit a journal sleeve.
  hw_m4_nut    x10  AF7 hex, real M4x1.0 internal thread + 45deg lead-in per face.
                    AF and the 3.2 thickness are the SLOT's, both probed: the slide-up
                    slot is cut for an AF-7 hex ACROSS CORNERS, which is what centres
                    it on the Ø4.4 bore. Slot walls are the wrench.
  hw_m8_bolt   x4   M8x70 end bolt-axle: knurled Ø22 thumb head, smooth Ø8.0 journal
                    under both bushings AND through the tension slot, ISO M8x1.25
                    thread only where the nut runs. Modelled at the length the metal
                    part SHOULD be -- see BUY M8x70 below.
  hw_m8_nut    x8   AF13 hex, real M8x1.25 internal thread, 6.0 tall: 4 inner cage
                    nuts plus 4 outboard jam nuts that clamp the tower. Ø9.0
                    countersinks both faces. No NYLOC analogue
                    exists in PLA and none is modeled: a deliberately-tight last
                    thread does not spring back, the bolt just shaves it. Moot here --
                    the cage grips the flats, so the nut cannot rotate anyway.
  hw_m8_washer x4   Ø14.4/Ø8.4 x 1.5 WITH the NYLOC's two flats (AF 13.0): the seat is
                    INSIDE the tower nut cage (gap 13.4), where a round Ø14.4 disc
                    overlaps the strips. A printed WAVE washer was evaluated and
                    rejected -- it creeps by the exact mechanism it would compensate
                    (a steel one under the plastic nut is worth a bench try).
  hw_f688_bushing x8 flanged plain bushing for the F688ZZ: body Ø15.2 touching
                    nothing + 3 OWN crush ribs cresting Ø16.0 (compliance lives on the
                    printed part; the idler's ribs only work against a ground Ø16.000),
                    bore Ø8.6 = 0.2-0.4 running on the Ø8.0 journal, flange Ø17.9 loose
                    in the Ø18.5 recess, 3 BLIND AXIAL grease grooves (axial, because a
                    circumferential groove runs parallel to the sliding direction and
                    sweeps no debris -- debris is what kills a dry PLA journal).
                    GREASE IS REQUIRED; it is the part's service life, not a nicety.
  hw_pan_ring  x20  18 barrel rollers + 2 spares, replacing the 18x Ø6 BBs: a Ø5.9
                    sphere with 0.5 flats on both SPIN POLES, printed axis-up and
                    installed AXIS-RADIAL. A thrust element rolls about a radial axis,
                    so both groove contacts ride ONE great circle: printing axis-up
                    puts that circle on the printed XY contour (FDM's most accurate)
                    and parks the droop-prone poles where nothing ever touches. That
                    answers the old "printed spheres come out scarred" objection
                    instead of dodging it. pan_cage IS used again. Print 0.1 mm layers.
  hw_tilt_axle x1   Ø4.8 x 209 rod + the 1.0 D-flat, PRINT-COMPENSATED (bore-0.2, the
                    seam-dowel convention): Ø5.000 nominal could not enter the Ø5.000
                    steel 695. The D-key ledge references the AXIS, not the rod
                    surface, so key clearance is unchanged at 0.05. Prints lying along
                    Y, flat UP -- layers then run PARALLEL to the axis, so bending is
                    bead-axial: this is the STRONG orientation, not the weak one.
  hw_seam_dowel x5  Ø3.9x12 + 0.5x45 lead-ins (a square lip shaves swarf into a blind
                    seam or splits the pad). NOT Ø4.0: bores are Ø4.1 for a METAL Ø4.0
                    at 0.1 slip, but a printed dowel is the other half of the stack --
                    it lands over while the bore lands under, so Ø4.0-in-Ø4.1 is a coin
                    flip between splitting the pad and rattling. Ø3.9 lands near
                    zero-to-slip. Serves 5 loose-dowel bores: 2 chassis y=26 seam, 1
                    head_back flange, 2 head_bezel seam (bez_dowel_pts are MOLDED pins,
                    not loose dowels). Stands on end; roundness is the constraint.
  hw_foot_pin  x2   Ø3x8 trim_neckfoot locator pins (5.0 platform socket + 3.0 collar =
                    flush, per the 2026-07-15 socket deepening; probed, not assumed).
                    Ø3.0 nominal: the sockets are already Ø3.2 = the same 0.2 stack.
                    Chamfered -- it drops into a BLIND socket.

NOT here: everything electronic (HC-SR04, LED strip, power modules -- no plastic
substitute makes sense), owned hardware (M2/M3 screws, 695-2RS bearings), elastomers
(antenna O-rings), and the antenna Ø4 shafts + spur set (placeholder discs are not
printable teeth; that station stays parked).

LOAD LIMITS -- what these CANNOT do. Verdicts kept with the parts so nobody
re-derives them at the bench:
  * THE M8 TENSIONER NOW HAS A CLOSED CLAMP STACK. Four additional AF13 jam nuts sit
    on the tower OUTBOARD faces; the existing nut/washer pairs remain inboard. The
    M8x70 thread starts at x=78 and crosses jam nut -> tower -> washer -> inner nut,
    clamping the tower while the idler remains free on the smooth journal across the
    former 17.4 mm air gap. Printed and metal builds use the same architecture.
  * BUY M8x70, NOT M8x60. The modeled stack gives ~57.9 of grip; a 60 shank leaves
    ~2.1-2.5 mm of engagement = ~2 turns, and an 8.0 NYLOC's nylon insert sits PAST
    the end of the bolt, so ASSEMBLY.md's "NYLOC required" buys a lock the geometry
    cannot reach. Bad practice in steel; a creep concentrator in PLA.
  * M4 IS A REAL FASTENER NOW (the old "press nuts are for LOCATION, not fastening"
    no longer applies to M4): it screws, tightens and re-uses. It still strips at
    ~400 N vs a metal M4's ~2 kN, and the shoulder seat is only 3.9 mm^2 -- expect
    ~0.1 mm of bed-in on first assembly, then it stops. Snug it; don't lean on it.
  * PLA CREEPS, so any preload decays over hours. With real threads that decay is
    bounded and RECOVERABLE -- a nut cannot walk off a thread, it can only lose clamp.
    Re-snug; nothing degrades permanently.
  * hw_m4_bolt / hw_m8_bolt shanks printed vertically are weak in bending at the layer
    lines -- fine at this robot's ~1 N/wheel, but don't drive it off a desk on plastic
    axles.
  * hw_tilt_axle: tilt homing is USABLE, not "soft and drifty" -- wind-up is ~1.3-1.5
    deg at the 0.1 N-m stall, the same order as the design's own D-key backlash (which
    the steel rod has too), and stall homing repeats it so it largely calibrates out.
    The real cost is CREEP: 1-3 deg of droop over hours off the balance point. Park at
    the balance point (already the firmware rule).
  * hw_f688_bushing is a plain bearing, ~50x a ball bearing's rolling resistance --
    but only 0.17-0.70 N of track pull to roll, which the track's own weight exceeds.
    The idler turns. PV has ~3.4x margin even dry; grease it anyway.
  * hw_pan_ring rollers run ~2-3x a steel BB's effective friction (layer-line
    roughness), leaving race drag ~15-20 mNm against ~15-17 mNm at the platform: the
    dry pan SLEWS, but slowly and near the limit, and may need a nudge from rest.
    Grease both grooves. Do not time the dry pan and call it a gear-ratio verdict.

Print notes: bolts, dowels and pins stand HEAD-DOWN / on end (self-supporting, brim
carries the slender stance); nuts, washers and bushings lie flat with the thread axis
VERTICAL (threads.py's rule: a vertical thread is a spiral of ~30 deg overhangs and
needs no support); pan rollers stand flat-down at 0.1 mm layers. Everything is NOSUP.
"""

from . import (
    m4_bolt,
    m4_nut,
    m8_bolt,
    m8_nut,
    m8_washer,
    f688_bushing,
    pan_ring,
    tilt_axle,
    seam_dowel,
    foot_pin,
)

_MODS = (
    m4_bolt,
    m4_nut,
    m8_bolt,
    m8_nut,
    m8_washer,
    f688_bushing,
    pan_ring,
    tilt_axle,
    seam_dowel,
    foot_pin,
)


# name -> (builder, print count). Counts mirror docs/ASSEMBLY.md buy-list quantities.
# ONE MODULE PER PART (2026-07-16): each stand-in owns its own file so a part can be
# reworked -- and reviewed -- without touching its neighbours.
STANDINS = {m.NAME: (m.build, m.COUNT) for m in _MODS}


def export_standins():
    """Write one canonical STL per unique stand-in into stl/hardware/ (counts live
    in STANDINS; export_bambu replicates onto the plate)."""
    from geo import export_stl
    from stlpaths import stlp
    for name, (build, _n) in STANDINS.items():
        export_stl(build(), stlp(name + ".stl"))
    print("exported %d hardware stand-ins into stl/hardware/" % len(STANDINS))


if __name__ == "__main__":
    export_standins()

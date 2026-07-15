"""PLASTIC HARDWARE STAND-INS (2026-07-15, user: "include all items in the export so I
would just assemble with plastic till I get actual metal parts").

Print-oriented temporary substitutes for the BUY-LIST metal hardware, so the robot
dry-assembles fully before the order arrives. The BOM is UNCHANGED -- these are
interim parts, replaced 1:1 by the real metal. Export-only: none of these are scene
nodes (the assembly GLB keeps the silver axle_hw_/pan_balls/tilt_axle placeholders),
so the interference/fit/nav gates are untouched. EXPORT=1 writes them to
stl/hardware/ and export_bambu packs them onto the "Hardware stand-ins" plate.

What gets a stand-in (all threadless -- push/press fits, see per-part notes):
  hw_m4_bolt   x10  M4x40 road-wheel bolt-axles (Ø3.9 shank = the placeholder dim;
                    wheels Ø4.2 slip-fit over it, beam bores Ø4.4). Owned M4 NUTS
                    thread on nothing here: push the printed nut on instead.
  hw_m4_nut    x10  press-on ring nut (bore Ø3.7 on the Ø3.9 shank). The owned steel
                    M4 hex nuts are useless on an unthreaded shank, so the slide-up
                    slot gets this printed AF7 hex with a light press bore.
  hw_m8_bolt   x4   M8x60 end bolt-axles (Ø8.0 shank, head = hubcap).
  hw_m8_nut    x4   AF13 hex x5 (the tower nut cages grip AF13+0.4), bore Ø7.8 =
                    0.2 press on the shank. See LOAD LIMITS below: this one cannot
                    hold tension preload, so the dry track runs slack on purpose.
  hw_m8_washer x4   Ø14.4/Ø8.4 x 1.5.
  hw_f688_bushing x8 flanged BUSHING replacing the F688ZZ bearing: OD 15.85, bore Ø8.3
                    running on the Ø8.0 shank, Ø18.2 flange. Since the 2026-07-15 seat
                    rework (idler_bore_d 15.95 -> 16.05 + 3 crush ribs at Ø15.80 crest)
                    it lands on a 0.05 diametral crush of the ribs -- a light plastic-on-
                    plastic press that holds it in and still lets a screwdriver lever it
                    out. Idlers become plain bearings: fine at desk speeds, grease helps.
  hw_pan_ring  x1   torus slip ring replacing the 18x Ø6 BBs: printed spheres need
                    support on the lower hemisphere and come out scarred, so the
                    interim race is a Ø5.8-section ring sitting in both grooves as a
                    plain bearing (platform drops 0.2, harmless; pan_cage unused
                    until real BBs arrive). Grease the grooves.
  hw_tilt_axle x1   Ø5 x 209 rod with the 1.0 D-flat (same geometry as the build.py
                    placeholder). Prints lying along Y, flat UP (round line contact
                    on the bed is full-length; flat-down would float the round ends
                    1.0 high). PLA flexes more than steel: expect soft tilt homing.
  hw_seam_dowel x4  Ø3.9x12 seam dowels (chassis lower seams, bezel halves). NOT Ø4.0
                    (2026-07-15 fastening audit P3): the bores are Ø4.1, sized for a
                    METAL Ø4.0 dowel at 0.1 slip. A PRINTED dowel is the other half of
                    the tolerance stack -- it comes out ~0.1-0.2 OVER while the bore
                    prints ~0.1-0.2 UNDER, so Ø4.0-in-Ø4.1 is a coin flip between a
                    jam that splits the seam pad and a rattle that registers nothing.
                    Ø3.9 = 0.2 nominal, which lands near zero-to-slip after both errors.
  hw_foot_pin   x2   Ø3x6 trim_neckfoot locator pins. Left at nominal: the sockets are
                    already Ø3.2 (pan.py), so this is the same 0.2 stack as the dowel.

NOT here: everything electronic (HC-SR04, LED strip, power modules -- no plastic
substitute makes sense), owned hardware (M2/M3 screws, 695-2RS bearings), elastomers
(antenna O-rings), and the antenna Ø4 shafts + spur set (placeholder discs are not
printable teeth; that station stays parked).

LOAD LIMITS -- what these CANNOT do (2026-07-15 fastening audit P3, verdicts kept
with the parts so nobody re-derives them at the bench):
  * PLASTIC M8 NUTS CANNOT HOLD TENSION PRELOAD. They are threadless push-ons: the
    only thing resisting the track pulling them off the shank is a 0.2 diametral
    interference on a PLA-on-PLA bore, and PLA creeps under sustained load at room
    temperature -- the grip decays over hours, not cycles. So the FRONT (tensioning)
    end axles cannot be tensioned in the dry build: EXPECT TRACK SAG, by design.
    Consequences to plan for, not to debug: the top run droops onto the wheel-beam
    cap, and the ground run's mesh with the mid-drive sprocket is held only by the
    robot's own weight, so a dry track can skip a tooth under hand load. Snug the
    nuts to just-mesh, add a drop of CA if one creeps off, and do NOT read dry-build
    tension behaviour as a verdict on the design -- re-test after the real M8x60 +
    NYLOCs land. Everything downstream of tension (mesh depth, skip barrier, the
    anti-buckle cap) is only meaningful on metal.
  * M4/M8 press nuts at 0.2 interference are fine for LOCATION (they hold a wheel on
    an axle against gravity and rattle); they are not fasteners.
  * hw_m4_bolt / hw_m8_bolt shanks printed vertically are weak in bending at the
    layer lines -- fine at this robot's ~1 N/wheel, but don't drive it off a desk on
    plastic axles.
  * hw_tilt_axle: PLA flexes far more than steel -- expect soft, drifty tilt homing.

Print notes: bolts stand HEAD-DOWN (self-supporting, brim carries the slender
stance); nuts/washers/bushings lie flat; everything is NOSUP.
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

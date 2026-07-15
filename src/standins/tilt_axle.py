"""hw_tilt_axle plastic stand-in -- the Ø5 solid steel tilt axle. See the package
docstring for the programme; the derivation that sets THIS part's numbers is here.

WHAT THIS SHAFT ACTUALLY DOES (probed, tools -> see the module notes below):
  x  -18..+18   worm_wheel hub + spacer tubes ride it (bore Ø5.2); the D-KEY ledge
                bears on the flat over the hub band x 3.5..9.
  x  +-17..21   695-2RS inner races -- REAL STEEL, bore Ø5.000 (-0/-0.008). Owned
                x30, so this is the one interface the stand-in cannot negotiate with.
  x  +-34..44   head pinch-clamp blocks (bore Ø5.1 + a 1.0 slit and an M3 cross bolt).
  x  +-45..104.5 head side-wall / pivot-boss bores, LOOSE Ø5.3 -- locators, no load.

THE FIX THAT MATTERS: PRINT COMPENSATION (2026-07-16).
The old stand-in was modelled at a dead-nominal Ø5.000 -- "same geometry as the build.py
placeholder". That is the exact bug class the 2026-07-15 fastening audit was created to
kill, and it makes this part UNASSEMBLABLE: round PEGS print OVERSIZE on FDM (elephant's
foot on the first layers, bead over-extrusion, the Z-seam ridge) -- a Ø5.0 peg lands
Ø5.1-5.2. The 695 bore is Ø5.000 and it is steel: it does not open up. Probed radial
clearance into the real bearing bore was +0.000 mm, i.e. line-to-line in CAD and a hard
jam in PLA. Modelled Ø4.8 lands ~Ø4.9-5.0 after the growth = a 0-to-0.1 running fit.
That is the seam-dowel convention from the package docstring (bore-0.2 nominal, "lands
near zero-to-slip after both errors"), applied to the tightest bore this rod sees.
Undersize is also the recoverable direction: you can sand a shaft down, you cannot grow it.

THE FLAT PLANE IS HELD AT z=+1.5 EXACTLY, decoupled from the OD. The worm wheel's D-key
ledge is referenced to the AXIS (ledge face at +1.55 = flat at 1.5 + 0.05 clearance), not
to the rod surface, so shrinking the OD does not touch the key interface -- it only makes
the flat 0.9 deep instead of 1.0 and 3.75 wide instead of 4.0. build.py's placeholder and
docs/ASSEMBLY.md's metal spec ("only the ~6 mm under the hub needs a clean 1.0 +-0.1")
are both unaffected. Probed D-key clearance is unchanged at 0.050 mm.

PRINT ORIENTATION -- the current choice is right, and NOT for the documented reason.
  * HORIZONTAL (kept): rod along Y, FLAT UP. The task brief called this "layer lines
    normal to the bending load -- the worst possible orientation". That is backwards.
    Lying down, the layers are planes PARALLEL to the rod axis, so bending's axial stress
    runs ALONG the beads (~50 MPa territory), and the transverse shear it puts across the
    layer interfaces is 4V/3A = 0.33 MPa against a ~20-30 MPa interlayer shear strength.
    Horizontal is the STRONG orientation here.
  * VERTICAL (rejected): 209 mm of Ø5 tower. Layers would sit NORMAL to the rod axis, so
    bending stress becomes pure interlayer tension -- that is the weak orientation, not
    the horizontal one. It is also unprintable: a 42:1 aspect-ratio tower resonates with
    the toolhead and snaps, and there is no bed contact worth the name.
  * FLAT-DOWN (rejected, sharper reason than the old docstring's): the flat only spans
    x -15..+104.5. The -X 695 land at x=-19 is OUTSIDE it, so a precision bearing surface
    would print in mid-air 0.9 above the bed. Elephant's foot would also land on the flat
    itself -- the one plane the D-key references.
  * SPLIT into co-axial segments (rejected): the only zero-load split stations are |x|>44
    (outboard of the clamps), so a 3-piece split at +-50 would keep every joint out of
    the loaded span -- it is not unsound. It just buys nothing: the 209 mm one-piece
    already arranges diagonally on the 180 bed (footprint ~153 mm square) and slices
    clean, while a split adds two glue joints, two alignment errors and a compliance
    where the design wants a single stiff rod. Splitting mid-span (the obvious 2-piece)
    would put a joint at the worm-wheel D-key inside the constant-moment span: strictly worse.

STIFFENER / HOLLOW-CORE -- EVALUATED AND REJECTED ON PHYSICS, not just on stock.
  1. It solves a problem this part does not have. The head load is SYMMETRIC (head CoM
     x = +0.3 mm), so the axle sits in four-point bending: clamps at +-39 push, bearings
     at +-19 react, constant M = (W/2)(20 mm) between them. Symmetric bending makes the
     head SINK, it does not ROTATE it -- so it costs zero tilt accuracy. At the head's
     896 g (50% infill) / 1310 g (solid-print worst) the whole rod sags 0.42 / 0.61 mm
     (delta = (P a^2/EI)(L/2 + a/3), the symmetric double-overhang case -- NOT the
     single-overhang P a^2 (L+a)/3EI, which under-reads it). Peak bending stress is
     M/Z = 7.2 / 10.5 MPa on the round section and 10.3 / 15.1 MPa on the flatted +X side
     (the D-section keeps 70% of the round Z), against ~50 MPa PLA: a 3-5x margin. The
     flat's x-asymmetry rolls the head ~0.05 deg. Bending is a non-issue; stiffening it
     buys nothing.
  2. It cannot fix the thing that IS soft. The limiter is TORSION: torque enters at the
     D-key (x 3.5..9) and leaves at the clamps (x +-34..44), so ~45 mm of PLA winds up
     ~1.3-1.5 deg at the ~0.1 Nm stall (GJ = 79,000 N mm2 vs steel's ~4.8e6). A slip-fit
     steel core does NOT carry torque: torque would have to get INTO the core and back
     OUT, and a smooth round rod in a round hole just slips. Coupling it needs keying at
     both ends or epoxy -- at which point you have built a worse version of the metal rod
     you are waiting for.
  3. The geometry forbids it anyway. The 1.0-deep flat puts its face at z=+1.5, so a
     concentric bore of Ø_b leaves 1.5 - Ø_b/2 of wall under the flat: Ø3 -> 0.00 mm,
     Ø2.5 -> 0.25 mm (the exact wall that killed the hollow METAL axle in the 2026-07-08
     review), Ø2 -> 0.50 mm, still under the 0.8 wallcheck floor.
  4. Stock: the inventory has NOTHING rigid in Ø2-4 (searched rods / shafts / drill bits /
     tubes / brass / wire: zero hits). The only Ø3 steel is the M3 screw kits, whose longest
     is M3x50 -- half the ~80 mm span that would need stiffening, and Ø3 is the zero-wall case.
     Ø1.75 filament as a core is PLA in PLA: same E, adds nothing.

MATERIAL: PLA, not PETG. This is a STIFFNESS-limited part (torsional wind-up), and PETG's
E is ~1.5-2.1 GPa against PLA's ~3.5 -- PETG would roughly DOUBLE the wind-up. PETG's
toughness would buy impact margin the part does not need: the homing stall is ~0.1 Nm at
22.5 deg/s, giving tau = Tr/J = 4.1 MPa against ~30-40 MPa, an 8x margin. Print it in PLA.

TILT-HOMING VERDICT (quantified, replaces the old "expect soft, drifty tilt homing"):
USABLE. Stall homing drives the head's fins into the cheek posts and calls that zero, so
the ~1.3-1.5 deg of wind-up is present at every homing event alike and largely calibrates
out; it is also the same order as the design's OWN D-key backlash (~1.5 deg at the +0.05
ledge fit), which the metal rod has too. What the plastic adds on top is CREEP: PLA under
the ~12-45 mNm standing imbalance keeps winding, so expect the head to droop a further
1-3 deg over hours of holding an off-balance pose. Park at the balance point for long idles
(already the firmware rule, CLAUDE.md "Tilt holding") and re-zero after a long hold. Do NOT
read absolute tilt accuracy on the plastic axle as a verdict on the mechanism.
"""
from geo import cyl, box, frustum, sub, uni, R
from params import P, TAU

from ._common import _zmin0

COUNT = 1
NAME = "hw_tilt_axle"

# Modelled OD. NOT P["axle_d"]: that is the 5.000 METAL nominal, and a printed peg grows
# 0.1-0.2 onto it. 0.2 under = the seam-dowel convention (see the module docstring).
AXLE_PRINT_D = 4.8
FLAT_Z = 1.5        # flat FACE plane, off the axis -- the D-key datum. Held, not derived
                    # from the OD (the wheel ledge sits at +1.55 = this + 0.05 clearance).
END_CHAMFER = 0.6   # 45 deg lead-in: a printed end face carries elephant's foot, and this
                    # rod has to thread two steel races, two pinch bores and two walls.


def build():
    """Ø4.8 print-compensated rod + the 1.0-deep D-flat held on its z=+1.5 datum, posed
    lying along Y with the flat UP (see the module docstring for why that orientation)."""
    r = AXLE_PRINT_D / 2.0
    L = P["head_w"] + 4.0                     # 209: interface dim, unchanged (checks.py)
    re = r - END_CHAMFER                      # chamfered end radius

    # rod as a chamfered solid of revolution, built along +Z then laid onto +Y.
    # NOTE geo.frustum only tapers DOWNWARD (it needs r_bottom > r_top -- pass it the
    # other way and h_full goes negative and the body comes out inverted), so the z=0
    # lead-in is built tapering and then flipped.
    mid = cyl(r, L - 2 * END_CHAMFER)
    mid.apply_translation((0, 0, L / 2.0))                 # z cham..L-cham
    c0 = frustum(r, re, END_CHAMFER)                       # r at z0 -> re at z cham
    c0.apply_transform(R(TAU / 2, (1, 0, 0)))              # flip: re at z -cham -> r at z0
    c0.apply_translation((0, 0, END_CHAMFER))              # z 0..cham, re at the z=0 face
    c1 = frustum(r, re, END_CHAMFER)
    c1.apply_translation((0, 0, L - END_CHAMFER))          # z L-cham..L, re at the z=L face
    rod = uni([uni([mid, c0]), c1])                        # pairwise (CSG ROBUSTNESS rule)
    rod.apply_transform(R(TAU / 4, (1, 0, 0)))             # +Z rod -> +Y rod
    rod.apply_translation((0, L / 2.0, 0))                 # centre on the origin

    # D-KEY FLAT: same cutter as build.py's placeholder with the axis swapped x->y. Spans
    # y -15..+108 (i.e. from the +Y insertion end past centre), face on the z=+1.5 datum.
    flat = box(8.0, 123.0, 1.4)
    flat.apply_translation((0, 46.5, FLAT_Z + 0.7))
    rod = sub(rod, flat)
    return _zmin0(rod)

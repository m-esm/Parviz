"""hw_seam_dowel plastic stand-in. See the package docstring.

Ø3.9 x 12 with 0.5 x 45deg lead-in chamfers at both ends.

DIAMETER -- Ø3.9 IS DELIBERATE, DO NOT "FIX" IT TO 4.0 (2026-07-15 fastening audit P3, kept
verbatim in the package docstring): the bores are Ø4.1 (chassis) / Ø4.2 (head), sized for a
METAL Ø4.0 dowel at 0.1 slip. A printed dowel is the other half of the tolerance stack -- it
comes out ~0.1-0.2 OVER while the bore prints ~0.1-0.2 UNDER, so Ø4.0-in-Ø4.1 is a coin flip
between splitting the seam pad and rattling. Ø3.9 = 0.2 nominal, which lands near
zero-to-slip after both errors.

LENGTH -- 12 serves every site (2026-07-16, re-probed after the fastening campaign added
head dowels). The five loose-dowel bores, all of which a Ø3.9x12 enters with clearance at
both ends:
    2x  chassis lower y=26 seam   Ø4.1 x 16 axis Y at (+-54, 26, 18)       -> 6/6, 2.0 spare
    1x  head_back frame flange    Ø4.2 x 14 axis X at (0, -2.25, 234.5)    -> 6/6, 1.0 spare
    2x  head_bezel L<->R seam     Ø4.2 x 15 axis X at x=22 (forehead+chin) -> 6/6, 1.5 spare
  (The bezel<->back "bez_dowel_pts" pair is NOT here: those are pins MOLDED on the bezel.)
  COUNT is 5, not the pre-campaign 4 -- the head dowels are new.

ENDS -- CHAMFERED, and that is a function fix, not cosmetics. A square-cut printed dowel
lands its first-layer lip on the bore mouth and either shaves (leaving swarf in a blind
seam) or wedges and splits the pad. Both ends get 0.5 x 45deg so it self-centres from
either side; the tip is Ø2.9, well inside every bore.

ORIENTATION -- STANDING (axis Z), against the instinct that layer lines must not lie in the
shear plane. Shear is not the constraint: Ø3.9 gives 11.9 mm^2, so even at PLA's weak-axis
interlayer shear (~30 MPa) the pin carries ~350 N -- orders above a seam locator's job, and
the M3 through the same pad carries the real load anyway. ROUNDNESS is the constraint: a
locator that registers to a few hundredths must be round, and a Ø3.9 cylinder printed lying
down gets a bed flat plus a sagging lower quadrant. Standing, every layer is a true circle.
12 mm at Ø3.9 is a stubby tower -- brim it, print it with the other stand-ins.

KNURL/FLUTES -- rejected. A grooved pin trades diameter accuracy for retention, and
retention here is the glue (the chassis dowel is specified press-one-side + glue). Flutes on
a 0.2-nominal fit would only add insertion friction and print fuzz exactly where the fit
lives.

Print: standing, NOSUP, brim.
"""
from geo import cyl, frustum, sub

from ._common import _zmin0

COUNT = 5
NAME = "hw_seam_dowel"

D = 3.9            # NOT 4.0 -- see the docstring
L = 12.0
CH = 0.5           # 45deg lead-in, both ends


def _chamfer_cutter(r, ch):
    """The ring OUTSIDE a 45deg cone, z 0..ch: cuts a chamfer on the END FACE AT z=ch of
    material lying below it (geo.frustum only builds bottom-wide cones, so the bottom-end
    cutter is this one mirrored -- see build())."""
    slab = cyl(r + 1.0, ch)
    slab.apply_translation((0, 0, ch / 2))
    return sub(slab, frustum(r, r - ch, ch))


def build():
    d = cyl(D / 2, L)
    d.apply_translation((0, 0, L / 2))
    hi = _chamfer_cutter(D / 2, CH)                  # breaks the z=L end
    hi.apply_translation((0, 0, L - CH))
    lo = _chamfer_cutter(D / 2, CH)                  # mirrored: breaks the z=0 end
    lo.apply_transform([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, CH], [0, 0, 0, 1]])
    return _zmin0(sub(sub(d, lo), hi))

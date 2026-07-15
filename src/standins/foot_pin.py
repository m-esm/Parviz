"""hw_foot_pin plastic stand-in. See the package docstring.

Ø3.0 x 8 with 0.4 x 45deg lead-in chamfers at both ends.

LENGTH -- 8, NOT the 6 this file shipped with (2026-07-16 bug fix). The 2026-07-15 neck
rework deepened the trim_neckfoot sockets from 3.5 to 5.0 ("3.5 of blind Ø3 socket is not a
location feature, it is a rattle") and re-specced the pin as Ø3x8; the stand-in was left at
6, which would have engaged 3.0 of collar + 3.0 of socket and left a 2.0 hole under it.
Re-probed from the geometry rather than the spec text:
    pan.py build_pan_platform : blind socket cyl(1.6, 5.0) at (+-27, neck_y), top at
                                z1 = base_h = 66      -> socket z 61.0..66.0, DEPTH 5.0
    neck.py build_trim_neckfoot: through bore cyl(1.6, 8.0), collar z 66.0..69.0
                                (lower band 1.6 + upper band 1.4), COLLAR HEIGHT 3.0
  5.0 + 3.0 = 8.0 exactly, so the pin bottoms in the socket and finishes flush with the
  collar top -- which is what the metal Ø3x8 does, and the flush end is why it is 8 and not
  8-minus-clearance. Headroom above is not an issue either way: the tilt-swept head bottom
  dips to z 70.6 there, 1.6 clear of the collar top.

DIAMETER -- Ø3.0 nominal, unlike the Ø3.9 seam dowel. Both sockets are already Ø3.2 (pan.py
+ neck.py), so nominal IS the 0.2 stack the audit wants: after a printed pin comes out ~0.1
over and a printed bore ~0.1 under, this lands near zero-to-slip. Nothing to shave.

ENDS -- chamfered 0.4 x 45deg, same reason as the seam dowel: the pin drops through the
collar bore and into a BLIND socket, and a square first-layer lip on a blind hole shaves
swarf into the bottom and then sits on it, which loses the flush seat and pries the collar.

ORIENTATION -- standing (axis Z), roundness over interlayer shear: Ø3.0 = 7.1 mm^2, ~210 N
at PLA's weak axis, against a collar that carries nothing but itself.

Print: standing, NOSUP, brim.
"""
from geo import cyl, frustum, sub

from ._common import _zmin0

COUNT = 2
NAME = "hw_foot_pin"

D = 3.0            # sockets are Ø3.2 both ends -- nominal is already the 0.2 stack
L = 8.0            # 5.0 platform socket + 3.0 collar = flush
CH = 0.4


def _chamfer_cutter(r, ch):
    """The ring OUTSIDE a 45deg cone, z 0..ch: cuts a chamfer on the END FACE AT z=ch of
    material lying below it (geo.frustum only builds bottom-wide cones, so the bottom-end
    cutter is this one mirrored -- see build())."""
    slab = cyl(r + 1.0, ch)
    slab.apply_translation((0, 0, ch / 2))
    return sub(slab, frustum(r, r - ch, ch))


def build():
    p = cyl(D / 2, L)
    p.apply_translation((0, 0, L / 2))
    hi = _chamfer_cutter(D / 2, CH)                  # breaks the z=L end
    hi.apply_translation((0, 0, L - CH))
    lo = _chamfer_cutter(D / 2, CH)                  # mirrored: breaks the z=0 end
    lo.apply_transform([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, CH], [0, 0, 0, 1]])
    return _zmin0(sub(sub(p, lo), hi))

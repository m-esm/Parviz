"""F688ZZ stepped bearing-seat calibration coupon.

Five stations vary only rib crown: 0.075 through 0.175 mm. Each duplicates the real
src/tracks.py idler seat from BOTH faces: P["idler_bore_d"] through-bore, three
tangent-circle r0.9 ribs from P["idler_rib_n"], and Ø18.5 x 1.025 effective flange
recess at each face made by the real 1.05-long cutters. The nominal step reads
P["idler_rib_proud"]. The 25 mm square section leaves 4.475 mm radial wall around
the bore, above 3.0 mm, so hoop compliance does not mask rib behavior.

PRINT ORIENTATION EVIDENCE: tools/export_bambu.py:180-214 rotates every wheel R(Y, 90)
and states that wheels stand on a face. Thus the in-assembly X bore becomes vertical
to the bed. The two-face seat source is src/tracks.py:542-575. This coupon is built
with its bore axis Z and the same round
geometry, flat on one flange face, matching the idler's disc-down, support-off print.
Both faces are retained because src/tracks.py explicitly carries one F688ZZ per face.
Countable 1..5 edge notches mark ascending crown without text.
"""
import numpy as np

from geo import box, cyl, sub, uni
from params import P, TAU

from ._common import _zmin0

COUNT = 1
NAME = "hw_coupon_f688"
CROWNS = (0.075, 0.100, 0.125, 0.150, 0.175)
DEPTH = 30.0


def _station(crown, ticks):
    body = box(25.0, 25.0, DEPTH)
    body.apply_translation((0, 0, DEPTH / 2))
    body = sub(body, cyl(P["idler_bore_d"] / 2, DEPTH + 2.0))
    crest_r = P["idler_bore_d"] / 2 - crown
    for k in range(P["idler_rib_n"]):
        aa = TAU * k / P["idler_rib_n"]
        rib = cyl(0.9, DEPTH)
        rib.apply_translation(((crest_r + 0.9) * np.cos(aa),
                               (crest_r + 0.9) * np.sin(aa), DEPTH / 2))
        body = uni([body, rib])
    for z in (0.5, DEPTH - 0.5):
        recess = cyl(18.5 / 2, 1.05)
        recess.apply_translation((0, 0, z))
        body = sub(body, recess)
    for i in range(ticks):
        notch = box(0.7, 1.2, 1.4)
        notch.apply_translation((-11.7 + 1.25 * i, -12.2, DEPTH - 3.0))
        body = sub(body, notch)
    return body


def build():
    parts = []
    for i, crown in enumerate(CROWNS):
        p = _station(crown, i + 1)
        p.apply_translation(((i - 2) * 25.0, 0, 0))
        parts.append(p)
    return _zmin0(uni(parts))

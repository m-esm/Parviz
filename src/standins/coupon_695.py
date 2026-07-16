"""695-2RS stepped bearing-seat calibration coupon.

Five seats vary only the crush-rib crown: 0.075 through 0.175 mm. Bore Ø and depth,
the three r0.6 ribs at 90/210/330 degrees, and the 0.75 mm rib-free mouth lead-in
duplicate src/neck.py build_neck_clevis's RIB-CALIBRATED PRESS block. The nominal
step reads P["brg695_rib_proud"]. Each station keeps 3.475 mm of radial wall, above
the 3.0 mm minimum, so the result measures rib yield rather than hoop compliance.

PRINT ORIENTATION EVIDENCE: tools/export_bambu.py:113 rotates neck_clevis by R(X, 90),
leaving its X bearing axis horizontal to the bed (the entry says "on its back"). The
seat source is src/neck.py:149-177. This coupon is built bed-ready with the same horizontal X
axis and the same round bore. The real seat is not teardropped, so this remains round
and deliberately shares its short unsupported bore-roof sag. Flat feet make it
self-supporting; no support may touch a calibration bore.

One seat per crown is sufficient because the clevis's two seats are identical copies
from the same loop. Countable 1..5 edge notches mark ascending crown without text.
"""
import numpy as np

from geo import box, cyl, sub, uni
from params import P

from ._common import _zmin0

COUNT = 1
NAME = "hw_coupon_695"
CROWNS = (0.075, 0.100, 0.125, 0.150, 0.175)


def _station(crown, ticks):
    seat_r = (P["brg_od"] + 0.05) / 2
    depth = P["brg_w"] + 1.5
    body = box(depth, 20.0, 20.0)
    body.apply_translation((0, 0, 10.0))
    body = sub(body, cyl(seat_r, depth + 2.0, axis="x"))
    for az in (90, 210, 330):
        d = seat_r - crown + 0.6
        rib = cyl(0.6, P["brg_w"] + 0.5, axis="x", sections=16)
        rib.apply_translation((-0.5, d * np.cos(np.radians(az)),
                               10.0 + d * np.sin(np.radians(az))))
        body = uni([body, rib])
    for i in range(ticks):
        notch = box(1.2, 0.7, 1.2)
        notch.apply_translation((-depth / 2 + 0.3, -9.2 + 1.25 * i, 18.0))
        body = sub(body, notch)
    return body


def build():
    parts = []
    for i, crown in enumerate(CROWNS):
        p = _station(crown, i + 1)
        p.apply_translation((0, (i - 2) * 20.0, 0))
        parts.append(p)
    return _zmin0(uni(parts))

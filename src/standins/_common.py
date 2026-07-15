"""Shared print helpers for the hardware stand-ins (see the package docstring)."""
import math

import numpy as np
import trimesh

from geo import box, cyl, sub, uni
from params import P

TAU = 2 * np.pi


def _zmin0(m):
    m.apply_translation((0, 0, -m.bounds[0][2]))
    return m


def _bolt(shank_r, shank_l, head_r, head_h):
    """Head-down vertical bolt: head z 0..head_h, shank above."""
    hd = cyl(head_r, head_h)
    hd.apply_translation((0, 0, head_h / 2))
    sh = cyl(shank_r, shank_l)
    sh.apply_translation((0, 0, head_h + shank_l / 2))
    return uni([hd, sh])


def _hex_nut(af, h, bore_d):
    nt = cyl(af / math.sqrt(3.0), h, sections=6)   # circumradius from across-flats
    nt = sub(nt, cyl(bore_d / 2, h + 2))
    return _zmin0(nt)


def _ring(od, id_, h):
    r = sub(cyl(od / 2, h), cyl(id_ / 2, h + 2))
    return _zmin0(r)

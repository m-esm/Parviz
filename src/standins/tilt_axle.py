"""hw_tilt_axle plastic stand-in. See the package docstring."""
from geo import box, cyl, sub
from params import P

from ._common import _zmin0

COUNT = 1
NAME = "hw_tilt_axle"


def build():
    """Ø5 rod + D-flat, exactly the build.py tilt_axle geometry, print-posed lying
    along Y with the flat UP (full-length line contact; see module docstring)."""
    ax = cyl(P["axle_d"] / 2, P["head_w"] + 4, axis="y")
    flat = box(8.0, 123.0, 1.4)
    flat.apply_translation((0, 46.5, 1.5 + 0.7))       # same offsets as build.py,
    ax = sub(ax, flat)                                 # axis swapped x->y
    return _zmin0(ax)


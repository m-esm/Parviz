"""hw_seam_dowel plastic stand-in. See the package docstring."""
from geo import cyl

from ._common import _zmin0

COUNT = 4
NAME = "hw_seam_dowel"


def build():
    return _zmin0(cyl(1.95, 12.0))

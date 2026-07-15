"""hw_foot_pin plastic stand-in. See the package docstring."""
from geo import cyl

from ._common import _zmin0

COUNT = 2
NAME = "hw_foot_pin"


def build():
    return _zmin0(cyl(1.5, 6.0))

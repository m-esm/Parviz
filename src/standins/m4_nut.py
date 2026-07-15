"""hw_m4_nut plastic stand-in. See the package docstring for rationale + LOAD LIMITS."""
from ._common import _bolt, _hex_nut, _ring, _zmin0

COUNT = 10
NAME = "hw_m4_nut"


def build():
    return _hex_nut(7.0, 3.2, 3.7)

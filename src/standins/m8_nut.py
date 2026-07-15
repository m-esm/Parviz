"""hw_m8_nut plastic stand-in. See the package docstring for rationale + LOAD LIMITS."""
from ._common import _bolt, _hex_nut, _ring, _zmin0

COUNT = 4
NAME = "hw_m8_nut"


def build():
    return _hex_nut(13.0, 5.0, 7.8)

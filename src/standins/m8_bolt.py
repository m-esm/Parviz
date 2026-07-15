"""hw_m8_bolt plastic stand-in. See the package docstring for rationale + LOAD LIMITS."""
from ._common import _bolt, _hex_nut, _ring, _zmin0

COUNT = 4
NAME = "hw_m8_bolt"


def build():
    return _bolt(4.0, 60.4, 6.5, 5.3)

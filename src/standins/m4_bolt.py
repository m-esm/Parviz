"""hw_m4_bolt plastic stand-in. See the package docstring for rationale + LOAD LIMITS."""
from ._common import _bolt, _hex_nut, _ring, _zmin0

COUNT = 10
NAME = "hw_m4_bolt"


def build():
    return _bolt(1.95, 40.0, 3.5, 3.5)

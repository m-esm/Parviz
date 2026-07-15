"""hw_m8_washer plastic stand-in. See the package docstring for rationale + LOAD LIMITS."""
from ._common import _bolt, _hex_nut, _ring, _zmin0

COUNT = 4
NAME = "hw_m8_washer"


def build():
    return _ring(14.4, 8.4, 1.5)

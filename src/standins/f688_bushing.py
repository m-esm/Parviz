"""hw_f688_bushing plastic stand-in. See the package docstring."""
from geo import cyl, sub, uni

COUNT = 8
NAME = "hw_f688_bushing"


def build():
    """Flanged plain bushing standing in for F688ZZ: flange-down (flange z 0..0.95,
    body to z 5.0), bore Ø8.3 runs on the Ø8.0 printed M8 shank."""
    body = cyl(15.85 / 2, 5.0)
    body.apply_translation((0, 0, 2.5))
    flg = cyl(18.2 / 2, 0.95)
    flg.apply_translation((0, 0, 0.475))
    return sub(uni([body, flg]), cyl(8.3 / 2, 12))


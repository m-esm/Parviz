"""hw_pan_ring plastic stand-in. See the package docstring."""
import trimesh

from geo import box, sub
from params import P

from ._common import _zmin0

COUNT = 1
NAME = "hw_pan_ring"


def build():
    """Slip-ring torus replacing the pan-race BBs: section Ø5.8 (0.2 under ball_d
    for running clearance) on the ball circle, bottom 0.4 trimmed flat for the bed."""
    ring = trimesh.creation.torus(P["pan_race_circle_d"] / 2, 5.8 / 2,
                                  major_sections=128, minor_sections=48)
    _zmin0(ring)
    cutter = box(200, 200, 2.0)
    cutter.apply_translation((0, 0, 0.4 - 1.0))        # top face at z 0.4
    ring = sub(ring, cutter)
    return _zmin0(ring)


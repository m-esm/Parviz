"""The combined touchscreen+Pi reference mesh: loading + posing.

Split out of the original monolithic build.py (2026-07-10); see
build.py for the assembly entry point and the overall design notes.
"""
import numpy as np
import trimesh
from trimesh.transformations import rotation_matrix as R
from params import DEG, P, TAU
from geo import _color


# ---------------------------------------------------------------------------
# Reference screen (loaded, recentered, oriented so glass faces +Y)
# ---------------------------------------------------------------------------
def load_screen():
    m = trimesh.load(P["screen_ref_stl"], force="mesh")
    m.apply_translation(-m.bounding_box.centroid)   # center at origin
    # STL axes already match ours (X=width, Y=depth, Z=height). A 180deg YAW (about Z) turns
    # the glass to face +Y without laying the panel down or flipping top/bottom.
    if P["screen_flip"]:
        m.apply_transform(R(TAU / 2, (0, 0, 1)))
    # Anchor by the GLASS FACE (largest +Y plane = front bbox face), not the centroid: the
    # Pins-Out assembly carries the Pi on the back, and centroid centering would shift the
    # glass + factory mount holes ~6.5 mm forward of where the v12 display-only model sat.
    m.apply_translation((0.0, P["screen_glass_y"] - m.bounds[1][1], 0.0))
    _color(m, "screen")
    return m


def screen_pose():
    """Transform placing the recentered screen onto the leaned front face.
    Anchored on screen_cz (NOT the tilt axle: the axle moved in stage 2R, the screen didn't)."""
    zc = P["screen_cz"]
    tilt = R(P["face_angle"] * DEG, (1, 0, 0), (0, 0, zc))   # lean top back
    trans = np.eye(4)
    trans[:3, 3] = (0, P["tilt_cantilever"], zc)
    return tilt @ trans



"""Real bought-part reference meshes (downloaded from Thingiverse, see
docs/ELECTRONICS.md) posed onto the assembly's placeholder locations.

These REPLACE the box/cylinder placeholders (motor_28byj, motor_tt, the
HC-SR04 sensor pods, the Arduino board) when REALPARTS is on (default), so the
viewer + assembly show the actual part geometry. They are bought parts, never
printed, and -- like the non-watertight screen mesh -- are skipped by the
boolean interference/fit gates (assembly_check.EXCLUDE). PLACEHOLDER_PARTS=1
restores the analytic placeholders (and their gate coverage).

Placement is uniform for every site: each placeholder is built and posed to
world as before, then `fit_real(kind, posed_placeholder)` maps the real mesh
onto that placeholder's ORIENTED bounding box. One code path, no per-site
transforms -- the placeholder's own world pose is the ground truth. A per-kind
`FLIP` fixes the residual 180-deg sign ambiguity of OBB axis matching (dialed
in visually, then frozen)."""
import os

import numpy as np
import trimesh

from geo import _color

_REF = "reference/electronics"

# kind -> (path, color key, decimate-to-pitch or None, native->canonical flip)
# FLIP is a sequence of (angle_deg, axis) applied to the centered native mesh so
# its principal axes line up in sign with the placeholder before OBB fitting.
_SPEC = {
    "28byj":  (f"{_REF}/stepper-28byj48-4919536/files/Stepper_Motor_28BYJ-48_v2.stl",
               "motor", None, []),
    "tt":     (f"{_REF}/tt-motor-1079893/files/DC_Motor_20mm.STL",
               "motor", None, []),
    "hcsr04": (f"{_REF}/hcsr04-dvemac-3653635/files/HC-SR04.STL",
               "sensor", None, []),
    "cm3":    (f"{_REF}/rpi-cam3-wide-mockup-6939162/files/rpi-cam-3w.stl",
               "screen", None, []),
    "uno":    (f"{_REF}/arduino-uno-r3-346338/files/Arduino_Uno_R3.obj",
               "pi", 0.6, []),
}

# placeholder node name -> real kind
NODE_KIND = {
    "motor_pan": "28byj", "motor_tilt": "28byj",
    "motor_ant_L": "28byj", "motor_ant_R": "28byj",
    "drive_L": "tt", "drive_R": "tt", "drive2_L": "tt", "drive2_R": "tt",
    "sensor_us": "hcsr04", "sensor_us_rear": "hcsr04",
    "sensor_cliff": "hcsr04", "sensor_cliff_rear": "hcsr04",
    "board_arduino": "uno",
    "camera_ref": "cm3",
}

_cache = {}


def enabled():
    return os.environ.get("PLACEHOLDER_PARTS") != "1"


def excluded_nodes():
    """Node names the boolean interference/fit gates must skip -- the real bought
    meshes (non-watertight or decimated, like screen_ref). Empty when
    PLACEHOLDER_PARTS=1, so the analytic placeholders keep full gate coverage."""
    return set(NODE_KIND) if enabled() else set()


def _decimate(m, pitch):
    """Cheap vertex-clustering decimation (no quadric libs on py3.9): snap
    vertices to a grid, rebuild, drop the faces that collapse. Good enough for
    a non-printed reference ghost; keeps the connector silhouette."""
    v = np.round(np.asarray(m.vertices) / pitch) * pitch
    d = trimesh.Trimesh(vertices=v, faces=m.faces, process=True)
    d.update_faces(d.nondegenerate_faces())
    d.remove_unreferenced_vertices()
    return d


def _load(kind):
    if kind in _cache:
        return _cache[kind]
    path, ck, pitch, flip = _SPEC[kind]
    m = trimesh.load(path, force="mesh")
    m.apply_translation(-m.bounding_box.centroid)      # center for a clean OBB
    for ang, ax in flip:
        m.apply_transform(trimesh.transformations.rotation_matrix(
            np.radians(ang), ax))
    if pitch:
        m = _decimate(m, pitch)
    _color(m, ck)
    _cache[kind] = m
    return m


def _cube_rotations():
    """The 24 proper rotations of the cube (axis-permutation * sign, det +1)."""
    import itertools
    out = []
    for perm in itertools.permutations(range(3)):
        for sx in (1, -1):
            for sy in (1, -1):
                for sz in (1, -1):
                    M = np.zeros((3, 3))
                    s = (sx, sy, sz)
                    for i, p in enumerate(perm):
                        M[i, p] = s[i]
                    if round(np.linalg.det(M)) == 1:
                        out.append(M)
    return out


_ROT24 = _cube_rotations()


def _fit_transform(real, placeholder):
    """Rigid 4x4 registering the real mesh onto the placeholder by discrete
    best-fit: try all 24 cube orientations (in the placeholder's own OBB frame so
    tilted sensor sites work) and keep the one whose surface sits closest to the
    placeholder's. This resolves axis assignment AND 180-deg flips from shape, not
    from extent order (which mislabels axes when the crude placeholder's
    proportions differ from the real part, e.g. HC-SR04 barrel vs height)."""
    from scipy.spatial import cKDTree
    Po = np.asarray(placeholder.bounding_box_oriented.primitive.transform)
    Rw = Po[:3, :3]                                    # placeholder OBB world axes
    Pc = np.asarray(placeholder.centroid)
    Rc = np.asarray(real.centroid)
    ps = placeholder.sample(500) - Pc                  # placeholder cloud, centered
    rs = real.sample(500) - Rc                         # real cloud, centered
    ps_obb = ps @ Rw                                   # into the OBB frame
    tree = cKDTree(ps_obb)
    best, bestM = None, None
    for M in _ROT24:
        d, _ = tree.query(rs @ M.T)                    # real rotated in OBB frame
        c = float(d.mean())
        if best is None or c < best:
            best, bestM = c, M
    # world rotation = OBB axes @ bestM ; then translate real centroid -> placeholder
    Rworld = Rw @ bestM
    T = np.eye(4)
    T[:3, :3] = Rworld
    T[:3, 3] = Pc - Rworld @ Rc
    return T


def fit_real(kind, placeholder, name):
    """Real mesh for `kind` posed onto `placeholder` (a world-posed Trimesh),
    tagged with `name` + refpart so add()/gates treat it right. None if the
    kind has no mesh."""
    if kind not in _SPEC:
        return None
    real = _load(kind).copy()
    real.apply_transform(_fit_transform(real, placeholder))
    real.metadata["name"] = name
    real.metadata["refpart"] = True
    return real

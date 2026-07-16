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
in visually, then frozen).

EXCEPTION -- the 28BYJ (2026-07-16, user: "motors mounted wrongly to the
gears"): the OBB best-fit is blind to the stepper's 7.875 mm ECCENTRIC shaft,
so it happily parked every real 28BYJ with its shaft ~15 mm off the gear axis
(pan 32T, tilt worm, both antenna G1s) while the analytic placeholders were
exactly right. Shaft-on-gear-axis is a hard datum, not a cosmetic fit, so the
28BYJ skips the heuristic entirely: the posed placeholder is vertex-for-vertex
a rigidly-transformed `motor_28byj()` (build.py only ever rotates/translates
it), so Kabsch on corresponding vertices recovers its EXACT world pose, and a
fixed measured native->local transform registers the real mesh into the
placeholder's own frame first. Deterministic, zero ambiguity."""
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

# kinds whose real mesh TOP-ALIGNS to the placeholder after the centroid fit:
# the Uno OBJ carries under-board pin bulk that drags its centroid ~2 low, so
# the centered fit sank the board through its seat posts (user: "board_arduino
# has housing issues", 2026-07-14). Top-aligning leaves the pin tails hanging
# realistically between the posts instead.
_TOP_ALIGN = {"uno"}

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


# --- deterministic 28BYJ registration (see module docstring EXCEPTION) ---
# Native frame of the downloaded mesh, measured after _load's bbox-centroid
# centering: shaft along +X (tip x 14.5) at (y 0, z -9.5); can axis (y 0,
# z -1.5), can bottom face x -14.5; ears +-Y; wiring box +Z. So the shaft
# eccentricity points -Z (8.0 vs the 7.875 spec -- 0.125 of viewer-only slop).
# R(-90 deg about Y) sends shaft +X -> +Z, offset -Z -> +X, wbox +Z -> -X and
# keeps ears +-Y: exactly motor_28byj's local frame. The translation then puts
# the native can-bottom center (-14.5, 0, -1.5) at the local origin, where the
# placeholder's can bottom sits.
def _byj_native_to_local():
    T = trimesh.transformations.rotation_matrix(np.radians(-90.0), (0, 1, 0))
    T[:3, 3] = -T[:3, :3] @ np.array([-14.5, 0.0, -1.5])
    return T


_BYJ_N2L = _byj_native_to_local()
_byj_local = None                                      # cached pristine motor_28byj()


def _pose_28byj(placeholder):
    """Exact world pose of a posed motor_28byj placeholder, or None.

    build.py never booleans the motor placeholders -- every 28BYJ site is
    motor_28byj() plus rigid transforms, and trimesh rigid transforms preserve
    vertex order. Kabsch over the vertex correspondence therefore recovers the
    rigid transform in closed form. Returns None (caller falls back to the OBB
    fit) if the vertex sets don't correspond or the residual isn't rigid."""
    global _byj_local
    if _byj_local is None:
        from motors import motor_28byj
        _byj_local = motor_28byj("_refparts_frame")
    A = np.asarray(_byj_local.vertices)
    B = np.asarray(placeholder.vertices)
    if A.shape != B.shape:
        return None
    ca, cb = A.mean(axis=0), B.mean(axis=0)
    H = (A - ca).T @ (B - cb)
    U, _, Vt = np.linalg.svd(H)
    Rm = Vt.T @ U.T
    if np.linalg.det(Rm) < 0:
        Vt[-1] *= -1
        Rm = Vt.T @ U.T
    T = np.eye(4)
    T[:3, :3] = Rm
    T[:3, 3] = cb - Rm @ ca
    resid = np.abs(A @ Rm.T + T[:3, 3] - B).max()
    return T if resid < 1e-6 else None


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
    T = None
    if kind == "28byj":                                # hard datum: shaft on gear axis
        pose = _pose_28byj(placeholder)
        if pose is not None:
            T = pose @ _BYJ_N2L
    if T is None:
        T = _fit_transform(real, placeholder)
    real.apply_transform(T)
    if kind in _TOP_ALIGN:
        real.apply_translation((0.0, 0.0,
                                float(placeholder.bounds[1][2] - real.bounds[1][2])))
    real.metadata["name"] = name
    real.metadata["refpart"] = True
    return real

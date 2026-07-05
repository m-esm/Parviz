"""desk-pi -- placeholder massing for the desktop humanoid robot.

SCAFFOLD ONLY. Nothing here is final geometry. These are rough primitives that
establish scale, the pan/tilt kinematic chain, and where the real parts will go,
so the viewer shows something and the build/serve/shoot loop works end to end.

Kinematic chain (bottom -> top), all built at the NEUTRAL pose (pan=0, tilt=0):
    base (fixed to desk)
      -> pan joint  : rotates the whole neck+head about vertical Z (yaw / look left-right)
        -> neck column
          -> tilt joint : rotates the head about horizontal Y (pitch / nod up-down)
            -> head = 7" touchscreen "face" + camera above it

Replace each _placeholder_* function with real parametric geometry (build123d or
trimesh) part by part. Keep the PARAMETERS block as the single source of truth.

Run:  python3 src/build.py        # writes web/assembly.glb (+ per-part stl/ later)
"""
import numpy as np
import trimesh

from stlpaths import webpath

# ----------------------------------------------------------------------------
# PARAMETERS  (mm). Every value carries the reason it is what it is.
# Screen numbers are the OFFICIAL Raspberry Pi 7" touchscreen (see CLAUDE.md);
# swap to the real reference-model bbox once we measure it from the STEP.
# ----------------------------------------------------------------------------
PARAMS = {
    # --- Official RPi 7" touchscreen module (the "face") ---
    "screen_w": 194.0,      # module outer width  (datasheet ~192.96)
    "screen_h": 110.0,      # module outer height (datasheet ~110.76)
    "screen_t": 21.0,       # depth incl. driver board + ribbon bend clearance
    "screen_bezel": 6.0,    # shell wall wrapping the screen edge

    # --- Head shell ---
    "head_wall": 3.0,       # shell wall thickness
    "cam_boss_d": 16.0,     # Camera Module 3 sits behind a small boss above screen

    # --- Neck / tilt ---
    "neck_h": 70.0,         # column height, desk-to-tilt-axis
    "neck_d": 45.0,         # column diameter (houses tilt servo + wiring)
    "tilt_range_deg": 45.0, # +-45 nod. Real limit set by yoke clearance later.

    # --- Base / pan ---
    "base_d": 130.0,        # footprint; wide enough to not tip with head extended
    "base_h": 30.0,         # houses pan servo + slew bearing + cable exit
    "pan_range_deg": 180.0, # +-90 look. Cable management caps this later.

    # --- Preview pose (does NOT affect printed geometry, just the massing view) ---
    "preview_pan_deg": 20.0,
    "preview_tilt_deg": 15.0,
}


def _box(w, d, h, color):
    m = trimesh.creation.box(extents=(w, d, h))
    m.visual.vertex_colors = color
    return m


def _cyl(d, h, color, sections=64):
    m = trimesh.creation.cylinder(radius=d / 2.0, height=h, sections=sections)
    m.visual.vertex_colors = color
    return m


def _placeholder_base(p):
    """Fixed desk plinth: houses the pan servo + slew bearing."""
    m = _cyl(p["base_d"], p["base_h"], [90, 95, 110, 255])
    m.apply_translation((0, 0, p["base_h"] / 2.0))
    m.metadata["name"] = "base_plinth"
    return m


def _placeholder_neck(p):
    """Pan column: everything above the base yaws with this."""
    m = _cyl(p["neck_d"], p["neck_h"], [120, 140, 170, 255])
    m.apply_translation((0, 0, p["neck_h"] / 2.0))
    m.metadata["name"] = "neck_pan_column"
    return m


def _placeholder_head(p):
    """Head = screen 'face' slab + camera boss. Built centered on the tilt axis."""
    parts = []
    # screen shell slab (face points +Y)
    w = p["screen_w"] + 2 * p["screen_bezel"]
    h = p["screen_h"] + 2 * p["screen_bezel"]
    face = _box(w, p["screen_t"], h, [200, 205, 215, 255])
    face.metadata["name"] = "head_face_shell"
    parts.append(face)

    # camera boss just above the screen, on the face plane (+Y)
    cam = _cyl(p["cam_boss_d"], 10.0, [230, 120, 110, 255])
    cam.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0)))
    cam.apply_translation((0, -p["screen_t"] / 2.0, h / 2.0 + 8.0))
    cam.metadata["name"] = "head_camera_boss"
    parts.append(cam)
    return parts


def build():
    p = PARAMS
    scene = trimesh.Scene()

    # base (fixed)
    base = _placeholder_base(p)
    scene.add_geometry(base, node_name="base_plinth")

    # neck sits on the base; pan preview rotates neck + head about Z
    pan = trimesh.transformations.rotation_matrix(
        np.radians(p["preview_pan_deg"]), (0, 0, 1)
    )

    neck = _placeholder_neck(p)
    neck.apply_translation((0, 0, p["base_h"]))
    neck.apply_transform(pan)
    scene.add_geometry(neck, node_name="neck_pan_column")

    # tilt axis height = top of base + neck height
    tilt_z = p["base_h"] + p["neck_h"]
    tilt = trimesh.transformations.rotation_matrix(
        np.radians(p["preview_tilt_deg"]), (1, 0, 0)
    )

    for part in _placeholder_head(p):
        # lift head so its center sits above the tilt axis, then tilt, then pan
        part.apply_translation((0, 0, 60.0))
        part.apply_transform(tilt)
        part.apply_translation((0, 0, tilt_z))
        part.apply_transform(pan)
        scene.add_geometry(part, node_name=part.metadata["name"])

    out = webpath("assembly.glb")
    scene.export(out)
    print(f"wrote {out}")
    print("PLACEHOLDER massing only -- replace _placeholder_* with real parts.")


if __name__ == "__main__":
    build()

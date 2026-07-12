#!/usr/bin/env python3
"""Tip-over / stability report for desk-pi (`make tipover`).

Mass model:
  * PRINTED parts: mesh volume x PLA 1.24 g/cm3 (solid-body assumption; real
    prints with ~25-50% infill weigh less, which RAISES the CoM because most
    printed volume sits low in the chassis -- a 50%-infill sensitivity line is
    reported). Density: PLA 1.24 g/cm3 (Prusament/Ultimaker PLA TDS).
  * BOUGHT parts: documented mass table below, positioned at their scene-node
    bbox centers (the GLB placeholder geometry is the best position data we
    have). Steel placeholders (tilt axle, axle hardware) use mesh volume x
    7.85 g/cm3.
  * EXTRA: electronics not modeled as scene nodes (ULN boards, power stage),
    hand-placed with documented coordinates.

Everything is measured on a NEUTRAL-pose side build (PAN=0 TILT=0 ANT=0 ->
web/_tipover.glb, removed afterwards); kinematic group membership (what swings
with the pan joint) comes from web/assembly.pose.json.

Outputs: total mass, CoM, static tip angles about the track contact patch,
the max forward/braking accel before pitch tip, and the fast-pan head-swing
case (180 deg/s peak slew, the 2026-07-12 fast-pan decision). Recommends
ballast when margins are thin.

Python 3.9; trimesh + numpy.
"""
import json
import math
import os
import subprocess
import sys
import warnings

import numpy as np

warnings.filterwarnings("ignore", category=RuntimeWarning)

import trimesh  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
from params import P  # noqa: E402

G = 9.81                 # m/s^2
RHO_PLA = 1.24e-3        # g/mm3 (PLA TDS: 1.24 g/cm3)
RHO_STEEL = 7.85e-3      # g/mm3

# ---------------------------------------------------------------------------
# BOUGHT-part masses by scene node (grams). Mass sources in comments.
# Position = the node's bbox center in the neutral-pose GLB.
# ---------------------------------------------------------------------------
BOUGHT_G = {
    # Official RPi 7" Touch Display 277 g (RPi 7" Touch Screen fact sheet,
    # farnell.com/datasheets/1958036.pdf) + Raspberry Pi 5 ~46 g
    # (raspberrypi.com product page). Rides as one module on the display's
    # own standoffs (the combined Pins-Out reference mesh).
    "screen_ref": 323.0,
    "camera_ref": 4.0,        # Camera Module 3 ~4 g (RPi CM3 product brief)
    # 28BYJ-48 geared stepper ~37 g incl. gearbox (datasheets: components101,
    # Mouser stepd-01-data-sheet; sources quote 34-40 g) x4: pan, tilt, 2x ant.
    "motor_pan": 37.0, "motor_tilt": 37.0, "motor_ant_L": 37.0, "motor_ant_R": 37.0,
    # TT gearmotor ~45 g (typical listings 40-50 g, e.g. Adafruit TT DC
    # gearbox motor). Base config = 2 (drive2_* optional station, excluded).
    "drive_L": 45.0, "drive_R": 45.0,
    "pan_balls": 3.6,         # 18x 6 mm airsoft BB ~0.20 g each
    "sensor_us": 8.5, "sensor_us_rear": 8.5,       # HC-SR04 ~8.5 g each
    "sensor_cliff": 8.5, "sensor_cliff_rear": 8.5, # (typical module listings)
    "sensor_rear": 5.0,       # buzzer/speaker pod placeholder
    "lamp_L": 2.0, "lamp_R": 2.0, "led_front": 2.0, "led_strip": 2.0,
    "ear_mic_L": 15.0, "ear_mic_R": 15.0,   # 3.5 mm gooseneck mic + foam, est.
}
STEEL_NODES = {"tilt_axle", "axle_hw_L", "axle_hw_R"}   # volume x 7.85 g/cm3
SKIP_NODES = {"drive2_L", "drive2_R"}                   # optional 2nd TT station

# EXTRA masses not modeled as scene nodes: (grams, (x, y, z) mm, group).
# Positions from PARAMS / firmware/WIRING.md placements.
EXTRA = [
    ("ULN2003 x2 (pan+tilt drivers, base posts)", 20.0, (0.0, 55.0, 25.0), "fixed"),
    ("ULN2003 x2 (antenna drivers, head bay)", 20.0, (0.0, -40.0, 190.0), "head"),
    ("power stage (XL4015+MP1584+PD trigger+fuse, belly tray)", 70.0,
     (-16.0, -43.0, 14.0), "fixed"),
    ("695-2RS x2 (tilt bearings, neck cheeks)", 3.0, (0.0, -18.0, 153.0), "pan"),
    ("F688ZZ x8 (end idlers)", 40.0, (0.0, 0.0, 34.3), "fixed"),   # symmetric
    ("harness / wiring misc", 30.0, (0.0, -10.0, 50.0), "fixed"),
]

# Support polygon: flat ground run y +-track_ground_hy; lateral edge = outer
# track faces (full 44.8 track width contacts the ground).
SUP_Y = P["track_ground_hy"]                                     # +-120
SUP_X = P["chassis_w"] / 2 + P["track_gap"] + P["track_width"]   # +-118.8


def build_neutral():
    env = dict(os.environ)
    env.update(PAN="0", TILT="0", ANT="0", OUT="_tipover.glb")
    r = subprocess.run([sys.executable, os.path.join(REPO, "src", "build.py")],
                       cwd=REPO, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("neutral build failed:\n" + r.stderr[-1500:])
    return os.path.join(REPO, "web", "_tipover.glb")


def load_nodes(path):
    """{parent: (volume mm3, bbox-center, bounds)} grouped by dotted prefix."""
    scene = trimesh.load(path, force="scene")
    grouped = {}
    for node in scene.graph.nodes_geometry:
        T, gname = scene.graph[node]
        g = scene.geometry[gname].copy()
        g.apply_transform(T)
        grouped.setdefault(gname.split(".")[0], []).append(g)
    out = {}
    for k, v in grouped.items():
        m = v[0] if len(v) == 1 else trimesh.util.concatenate(v)
        out[k] = (abs(float(m.volume)), m.bounds.mean(axis=0), m.bounds)
    return out


def main():
    infill = float(os.environ.get("INFILL", "1.0"))   # printed-mass scale factor
    glb = build_neutral()
    try:
        nodes = load_nodes(glb)
    finally:
        if os.path.exists(glb):
            os.remove(glb)
    groups = json.load(open(os.path.join(REPO, "web", "assembly.pose.json")))["groups"]
    head_set = {n.split(".")[0] for n in groups["head"]}
    pan_set = {n.split(".")[0] for n in groups["pan"]}

    rows = []   # (name, grams, center, group)
    for name, (vol, ctr, _) in sorted(nodes.items()):
        if name in SKIP_NODES:
            continue
        grp = "head" if name in head_set else ("pan" if name in pan_set else "fixed")
        if name in BOUGHT_G:
            rows.append((name, BOUGHT_G[name], ctr, grp))
        elif name in STEEL_NODES:
            rows.append((name, vol * RHO_STEEL, ctr, grp))
        else:                                     # printed
            rows.append((name, vol * RHO_PLA * infill, ctr, grp))
    for name, g, pos, grp in EXTRA:
        rows.append((name, g, np.array(pos, float), grp))

    mass = np.array([r[1] for r in rows])
    pos = np.array([np.asarray(r[2], float) for r in rows])
    M = mass.sum()
    com = (mass[:, None] * pos).sum(axis=0) / M

    printed_g = sum(r[1] for r in rows if r[0] not in BOUGHT_G
                    and r[0] not in STEEL_NODES and not r[0][0].isupper()
                    and r[0] not in [e[0] for e in EXTRA])
    bought_g = M - printed_g

    print("tipover: desk-pi static stability + dynamic margins (neutral pose)")
    print("  support patch: y +-%.1f (ground run), x +-%.1f (track outer faces)"
          % (SUP_Y, SUP_X))
    print("  printed (PLA %.2f g/cm3, infill factor %.2f): %7.1f g"
          % (RHO_PLA * 1e3, infill, printed_g))
    print("  bought + hardware + extras:                   %7.1f g" % bought_g)
    print("  TOTAL: %.1f g   CoM (%.1f, %.1f, %.1f) mm  [CoM height %.1f]"
          % (M, com[0], com[1], com[2], com[2]))

    # heaviest movers, for intuition
    top = sorted(rows, key=lambda r: -r[1])[:6]
    print("  heaviest: " + ", ".join("%s %.0fg" % (n, g) for n, g, _, _ in top))

    # ---- static tip angles about the contact-patch edges ----------------------
    fore = math.degrees(math.atan2(SUP_Y - com[1], com[2]))
    aft = math.degrees(math.atan2(SUP_Y + com[1], com[2]))
    lat = math.degrees(math.atan2(SUP_X - abs(com[0]), com[2]))
    print("\n  static tip angles:  fore %.1f deg   aft %.1f deg   lateral %.1f deg"
          % (fore, aft, lat))

    # ---- max accel before pitch tip (a = g * lever / CoM height) --------------
    a_fwd = G * (SUP_Y + com[1]) / com[2]      # accelerating +Y tips about y=-SUP_Y
    a_brk = G * (SUP_Y - com[1]) / com[2]      # braking tips about y=+SUP_Y
    print("  max fwd accel %.2f m/s^2 (%.2f g)   max braking %.2f m/s^2 (%.2f g)"
          % (a_fwd, a_fwd / G, a_brk, a_brk / G))

    # ---- fast-pan head swing (2026-07-12 fast-pan: 180 deg/s peak slew) --------
    sw = [(g, p) for n, g, p, grp in rows if grp in ("head", "pan")]
    m_sw = sum(g for g, _ in sw)                                  # grams
    com_sw = np.array([g * np.asarray(p) for g, p in sw]).sum(axis=0) / m_sw
    r_sw = math.hypot(com_sw[0], com_sw[1])                      # mm from pan axis
    z_sw = com_sw[2]
    omega = math.pi                                               # 180 deg/s
    alpha = math.radians(300.0)                                   # firmware accel cap
    f_c = (m_sw / 1000.0) * omega ** 2 * (r_sw / 1000.0)          # N, centripetal
    f_t = (m_sw / 1000.0) * alpha * (r_sw / 1000.0)               # N, tangential
    # worst pose: pan 90 deg puts the swing CoM offset r_sw along +-X; the
    # outward (centrifugal reaction) force acts at z_sw against the lateral edge.
    fixed = [(g, p) for n, g, p, grp in rows if grp == "fixed"]
    m_fx = sum(g for g, _ in fixed)
    com_fx = np.array([g * np.asarray(p) for g, p in fixed]).sum(axis=0) / m_fx
    com_x90 = (m_sw * r_sw + m_fx * com_fx[0]) / M                # total CoM x at pan 90
    m_over = f_c * (z_sw / 1000.0)                                # N m, overturning
    m_rest = (M / 1000.0) * G * ((SUP_X - com_x90) / 1000.0)      # N m, restoring
    print("\n  fast-pan swing: pan-riding mass %.0f g, CoM r %.1f mm off-axis, z %.1f"
          % (m_sw, r_sw, z_sw))
    print("  at 180 deg/s: centripetal %.3f N, tangential (300 deg/s^2) %.3f N"
          % (f_c, f_t))
    print("  pan-90 overturning %.4f N m vs restoring %.3f N m  -> margin %.0fx"
          % (m_over, m_rest, m_rest / m_over if m_over > 0 else float("inf")))

    # ---- sensitivity + advice ---------------------------------------------------
    if infill == 1.0:
        print("\n  NOTE: solid-print assumption. At ~50% effective print density"
              " (INFILL=0.5) the printed mass halves and the CoM rises;"
              " rerun with INFILL=0.5 for the conservative bound.")
    worst = min(fore, aft, lat)
    if worst < 15.0 or a_fwd < 1.5 or a_brk < 1.5:
        print("  BALLAST RECOMMENDED: worst static angle %.1f deg / accel floor"
              " %.2f m/s^2 -- add mass to the rear ballast bay (blst_rib_*"
              " pockets, chassis floor)." % (worst, min(a_fwd, a_brk)))
    else:
        print("  margins healthy; no ballast strictly required (bay stays available).")


if __name__ == "__main__":
    main()

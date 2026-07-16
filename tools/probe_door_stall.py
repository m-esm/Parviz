#!/usr/bin/env python3
"""Head-door service path vs tilt drivetrain at the +-33.8 deg stalls (2026-07-16).

REPORT (not a gate). Answers the grok design-review question: can the rear
head_door open at a tilt stall, and would a MODEST cavity enlargement (exterior
untouched, walls >= 3.0 mm) make both stall paths collision-free?

Kinematics (same as src/build.py):
  - head_door + worm_wheel ride the HEAD frame (tilt about the axle, then pan)
  - tilt_carrier / motor_tilt / tilt_worm / neck_clevis ride the PAN frame
  - at pan=0 the PAN frame is identity; we re-pose the HEAD frame only

Door opening path (head-local, matches the tool-free top-hook + bottom-snap
design in head.py / PARAMS door_hook_*):
  1. rotate about the top hook line (axis // X through the hook tabs) 0..24 deg
     in 2 deg steps, bottom edge swinging -Y (away from the wall)
  2. from the 24 deg pose, translate along the swung -Y direction 0..15 mm
     in 1 mm steps

At every step: geo.inter(door_step, drivetrain_part).volume for each part.
Neutral tilt must be collision-free over the whole path (path-model sanity).

Then re-run with cavity cuts enlarged in 1 mm steps (hx 17..22, z0 130..126,
z1 162..165, floor -98..-100) and report the smallest enlargement that clears
BOTH stalls, or the numeric why-not.

Python 3.9; trimesh + manifold3d. Run: python3 tools/probe_door_stall.py
"""
import os
import sys
import warnings

warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

import numpy as np                                             # noqa: E402
import trimesh                                                 # noqa: E402
from trimesh.transformations import (                          # noqa: E402
    rotation_matrix as R, translation_matrix as T)

from params import P, DEG                                      # noqa: E402
from geo import box, inter, sub                                # noqa: E402
from gears import load_gear_stl, worm, worm_cd, worm_real_ok   # noqa: E402
from geo import dbore_neg, cyl, uni, _color                    # noqa: E402
from motors import motor_28byj                                 # noqa: E402
from neck import build_neck_clevis, build_tilt_carrier         # noqa: E402
from head import build_head_parts                              # noqa: E402

STALL = 33.8
# Pan-frame intruders (stay put while the head tilts). worm_wheel is head-frame
# but stays with the head during door open (keyed to the axle), so it is a fixed
# obstacle in the head frame for the swinging door.
PAN_PARTS = ("tilt_carrier", "motor_tilt", "tilt_worm", "neck_clevis")
HEAD_PARTS = ("worm_wheel",)
DRIVE_PARTS = PAN_PARTS + HEAD_PARTS

# Opening path
ROT_STEPS = list(range(0, 25, 2))          # 0..24 deg inclusive
LIFT_STEPS = list(range(0, 16, 1))         # 0..15 mm inclusive
# Cavity trial grid (modest; exterior untouched, walls >= 3.0)
HX_RANGE = list(range(17, 23))             # 17..22
Z0_RANGE = list(range(130, 125, -1))       # 130..126
Z1_RANGE = list(range(162, 166))           # 162..165
FLOOR_RANGE = list(range(-98, -101, -1))   # -98..-100
MIN_WALL = 3.0
POD_TOP_Z = 169.0
POD_DEEP_Y = -105.0                        # deepest tier rear face
TIER1_HX = 62.0


def _tilt_M(tilt_deg):
    yt, zt = P["tilt_axis_y"], P["tilt_axis_z"]
    return R(tilt_deg * DEG, (1, 0, 0), (0, yt, zt))


def _hook_pivot():
    """Top hook line: axis // X through the hook tabs (z ~ door_z[1]).

    Plate back face is at y = -65.85 (0.15 off the fixed wall inner face at -66);
    that is the natural hinge line as the hooks hang on the wall band.
    """
    return (0.0, -65.85, float(P["door_z"][1]))


def _open_M(rot_deg, lift_mm):
    """Head-local door open transform: rotate about hook, then lift along swung -Y."""
    px, py, pz = _hook_pivot()
    # Negative rotation about +X: bottom (z < pivot) swings toward -Y (rear).
    M = R(-rot_deg * DEG, (1, 0, 0), (px, py, pz))
    if lift_mm:
        # Local -Y after R_x(-rot): (0,-1,0) -> (0, -cos(rot), sin(rot)).
        direction = np.array([0.0, -np.cos(rot_deg * DEG), np.sin(rot_deg * DEG)])
        M = T(direction * float(lift_mm)) @ M
    return M


def _build_worm_wheel():
    """Neutral-pose worm_wheel (same construction as build.py, no tilt clocking)."""
    yt, zt = P["tilt_axis_y"], P["tilt_axis_z"]
    wx = P["worm_wheel_x"]
    wheel_r = P["worm_module"] * P["worm_wheel_teeth"] / 2
    placeholder = (os.environ.get("PLACEHOLDER_GEARS") == "1" or not worm_real_ok())
    if placeholder:
        from gears import gear_disc
        wheel = gear_disc(wheel_r, P["worm_wheel_teeth"], P["worm_wheel_w"],
                          2.5 * P["worm_module"], axis="x")
    else:
        wheel = load_gear_stl("worm_wheel_real.stl")
    hub = cyl(5.5, 5.5, axis="x"); hub.apply_translation((6.25, 0, 0))
    tub_p = cyl(4.0, 9.0, axis="x"); tub_p.apply_translation((13.5, 0, 0))
    tub_m = cyl(4.0, 14.5, axis="x"); tub_m.apply_translation((-10.75, 0, 0))
    wheel = uni([wheel, hub, tub_p, tub_m])
    wheel = sub(wheel, cyl(P["axle_d"] / 2 + 0.1, 40, axis="x"))
    half = box(6.0, 6.0, 2.0)
    half.apply_translation((0, 0, 1.55 + 1.0))
    ledge = inter(cyl(2.7, 5.5, axis="x"), half)
    for se in (-1, 1):
        wdg = box(2.0, 7.0, 2.0)
        wdg.apply_transform(R(np.pi / 4, (0, 1, 0)))
        wdg.apply_translation((se * 2.75, 0, 1.55))
        ledge = sub(ledge, wdg)
    ledge.apply_translation((6.25, 0, 0))
    wheel = uni([wheel, ledge])
    wheel.apply_translation((wx, yt, zt))
    _color(wheel, "fork"); wheel.metadata["name"] = "worm_wheel"
    return wheel


def _build_tilt_worm():
    yt, zt = P["tilt_axis_y"], P["tilt_axis_z"]
    wx = P["worm_wheel_x"]
    cd = worm_cd()
    wz = zt - cd
    face_y = yt - 0.5 * P["worm_len"] - 10.0
    yc = face_y + 4.0 + P["worm_len"] / 2
    placeholder = (os.environ.get("PLACEHOLDER_GEARS") == "1" or not worm_real_ok())
    if placeholder:
        wm = worm(P["worm_od"] / 2, P["worm_len"], starts=P["worm_starts"], axis="y")
    else:
        wm = load_gear_stl("tilt_worm_real.stl")
    db = dbore_neg(P["worm_len"] + 1.2, axis="y")
    db.apply_translation((0, 0.5, 0))
    wm = sub(wm, db)
    wm.apply_translation((wx, yc, wz))
    _color(wm, "motor"); wm.metadata["name"] = "tilt_worm"
    return wm


def _build_motor_tilt():
    yt, zt = P["tilt_axis_y"], P["tilt_axis_z"]
    wx = P["worm_wheel_x"]
    cd = worm_cd()
    wz = zt - cd
    face_y = yt - 0.5 * P["worm_len"] - 10.0
    mt = motor_28byj("motor_tilt")
    mt.apply_transform(R(-np.pi / 2, (1, 0, 0)))
    mt.apply_transform(R(-np.pi / 2, (0, 1, 0)))
    mt.apply_translation((wx, face_y - 2 - P["motor_body_h"],
                          wz - P["motor_shaft_off"]))
    return mt


def build_drivetrain():
    """Neutral-pose (pan=0,tilt=0) drivetrain meshes, named."""
    parts = {
        "tilt_carrier": build_tilt_carrier(),
        "motor_tilt": _build_motor_tilt(),
        "tilt_worm": _build_tilt_worm(),
        "neck_clevis": build_neck_clevis(),
        "worm_wheel": _build_worm_wheel(),
    }
    for n, m in parts.items():
        if not m.is_volume:
            raise RuntimeError("%s is not a volume" % n)
        m.metadata["name"] = n
    return parts


def build_door():
    """Neutral-pose head_door from the live PARAMS (pod_cavity / pod_notch)."""
    parts = build_head_parts()
    for p in parts:
        if p.metadata.get("name") == "head_door":
            if not p.is_volume:
                raise RuntimeError("head_door is not a volume")
            return p
    raise RuntimeError("build_head_parts() did not return head_door")


def cavity_cut(hx, floor_y, z0, z1):
    """Same cavity solid as head.py uses to hollow the pod."""
    cav = box(2 * hx, -60.0 - floor_y, z1 - z0)
    cav.apply_translation((0, (floor_y - 60.0) / 2, (z0 + z1) / 2))
    return cav


def enlarge_door(door, hx, floor_y, z0, z1):
    """Subtract a (possibly larger) cavity from a baseline door mesh.

    Safe for enlargements: cutting more material from an already-hollow door.
    Does not rebuild the exterior.
    """
    return sub(door, cavity_cut(hx, floor_y, z0, z1))


def wall_ok(hx, floor_y, z0, z1):
    """Keep >= MIN_WALL everywhere the task constrains."""
    top_wall = POD_TOP_Z - z1
    floor_wall = floor_y - POD_DEEP_Y          # e.g. -98 - (-105) = 7
    side_wall = TIER1_HX - hx                 # toward tier-1 half-width
    return (top_wall >= MIN_WALL - 1e-9
            and floor_wall >= MIN_WALL - 1e-9
            and side_wall >= MIN_WALL - 1e-9), {
        "top_wall": top_wall,
        "floor_wall": floor_wall,
        "side_wall_to_tier1": side_wall,
    }


def ov_vol(a, b):
    """Intersection volume; 0 on empty / non-overlap."""
    try:
        hit = inter(a, b)
    except Exception:
        return 0.0
    if hit is None or len(getattr(hit, "faces", [])) == 0:
        return 0.0
    v = float(hit.volume)
    return abs(v) if abs(v) > 1e-6 else 0.0


def pose_door(door, tilt_deg, rot_deg, lift_mm):
    g = door.copy()
    g.apply_transform(_open_M(rot_deg, lift_mm))
    if tilt_deg:
        g.apply_transform(_tilt_M(tilt_deg))
    return g


def pose_part(mesh, name, tilt_deg):
    g = mesh.copy()
    # head-frame parts tilt with the head; pan-frame stay put
    if name in HEAD_PARTS and tilt_deg:
        g.apply_transform(_tilt_M(tilt_deg))
    return g


def sweep(door, drive, tilt_deg, label=""):
    """Run the full open path at one tilt. Return a result dict."""
    # Parked (closed) clearances for reference
    closed = pose_door(door, tilt_deg, 0, 0)
    parked = {}
    for n, m in drive.items():
        parked[n] = ov_vol(closed, pose_part(m, n, tilt_deg))

    first = None          # (step_desc, part, vol)
    max_pen = (0.0, None, None)   # vol, step, part
    n_steps = 0
    collide_steps = 0

    # Rotation phase
    for rot in ROT_STEPS:
        n_steps += 1
        d = pose_door(door, tilt_deg, rot, 0)
        for n, m in drive.items():
            v = ov_vol(d, pose_part(m, n, tilt_deg))
            if v > max_pen[0]:
                max_pen = (v, "rot %g deg" % rot, n)
            if v > 1e-3:
                collide_steps += 1
                if first is None:
                    first = ("rot %g deg" % rot, n, v)

    # Lift phase (at 24 deg)
    for lift in LIFT_STEPS:
        if lift == 0:
            continue          # already covered as rot 24 / lift 0
        n_steps += 1
        d = pose_door(door, tilt_deg, 24, lift)
        for n, m in drive.items():
            v = ov_vol(d, pose_part(m, n, tilt_deg))
            if v > max_pen[0]:
                max_pen = (v, "lift %g mm @24deg" % lift, n)
            if v > 1e-3:
                collide_steps += 1
                if first is None:
                    first = ("lift %g mm @24deg" % lift, n, v)

    clear = first is None
    return {
        "tilt": tilt_deg,
        "label": label or ("tilt %+g" % tilt_deg),
        "clear": clear,
        "first": first,
        "max_pen": max_pen,
        "parked": parked,
        "n_steps": n_steps,
        "collide_steps": collide_steps,
    }


def print_result(r):
    tag = "CLEAR" if r["clear"] else "COLLIDES"
    print("  %-14s %s" % (r["label"], tag))
    # parked min clearance proxy: max overlap at closed (0 = no overlap)
    pk = r["parked"]
    worst_park = max(pk.items(), key=lambda kv: kv[1])
    print("    parked max overlap: %s  %.3f mm3" % (worst_park[0], worst_park[1]))
    if r["clear"]:
        print("    path: all %d steps collision-free" % r["n_steps"])
    else:
        step, part, vol = r["first"]
        print("    first hit: %s  vs %s  (%.2f mm3)" % (step, part, vol))
        mv, ms, mp = r["max_pen"]
        print("    max pen:   %s  vs %s  (%.2f mm3)" % (ms, mp, mv))


def max_face_growth(hx, floor_y, z0, z1):
    """Largest per-face enlargement from the stock cavity (mm)."""
    shx, sfy, sz0, sz1 = P["pod_cavity"]
    return max(hx - shx, sfy - floor_y, sz0 - z0, z1 - sz1)  # sfy - floor: more neg = grow


def main():
    print("building door + drivetrain (neutral local = pan0/tilt0) ...")
    door0 = build_door()
    drive = build_drivetrain()
    print("  door volume %.0f mm3  bounds %s" % (
        door0.volume, np.round(door0.bounds, 1).tolist()))
    for n, m in drive.items():
        print("  %-14s vol %.0f  bounds %s" % (
            n, m.volume, np.round(m.bounds, 1).tolist()))

    tilts = [-STALL, 0.0, +STALL]
    print("\n=== BASELINE cavity %s / notch %s ===" % (
        P["pod_cavity"], P["pod_notch"]))
    print("hook pivot (head-local): %s" % (tuple(round(x, 2) for x in _hook_pivot()),))
    print("path: rotate 0..24 deg x 2, then lift 1..15 mm along swung -Y\n")

    baseline = []
    for t in tilts:
        r = sweep(door0, drive, t)
        print_result(r)
        baseline.append(r)

    # Sanity: neutral must be clear
    neutral = next(r for r in baseline if abs(r["tilt"]) < 1e-9)
    if not neutral["clear"]:
        print("\nFAIL: neutral tilt collides on the open path -- path model is wrong.")
        print("      Fix the path (hook pivot / rotation sign), not the geometry.")
        return 2

    stall_results = [r for r in baseline if abs(r["tilt"]) > 1e-9]
    stalls_clear = all(r["clear"] for r in stall_results)

    print("\n=== ENLARGEMENT SEARCH (exterior untouched, walls >= %.1f mm) ===" % MIN_WALL)
    print("trial grid: hx %s  z0 %s  z1 %s  floor %s" % (
        HX_RANGE, Z0_RANGE, Z1_RANGE, FLOOR_RANGE))

    if stalls_clear:
        print("baseline already clears BOTH stalls -- no cavity change needed.")
        best = None
    else:
        # Rank candidates by max face growth, then by sum of face growths
        cands = []
        for hx in HX_RANGE:
            for z0 in Z0_RANGE:
                for z1 in Z1_RANGE:
                    for fy in FLOOR_RANGE:
                        ok, walls = wall_ok(hx, fy, z0, z1)
                        if not ok:
                            continue
                        growth = max_face_growth(hx, fy, z0, z1)
                        if growth < 0:
                            continue
                        total = ((hx - P["pod_cavity"][0])
                                 + (P["pod_cavity"][1] - fy)
                                 + (P["pod_cavity"][2] - z0)
                                 + (z1 - P["pod_cavity"][3]))
                        cands.append((growth, total, hx, fy, z0, z1, walls))
        cands.sort()
        print("%d wall-legal candidates (max face growth 0..%d mm)" % (
            len(cands), max(c[0] for c in cands) if cands else 0))

        best = None
        # Walk by growth budget; stop at first that clears both stalls
        tested = 0
        for growth, total, hx, fy, z0, z1, walls in cands:
            if growth == 0 and (hx, fy, z0, z1) == tuple(P["pod_cavity"]):
                continue          # baseline already known to fail
            door_t = enlarge_door(door0, hx, fy, z0, z1)
            ok_both = True
            detail = []
            for t in (-STALL, +STALL):
                r = sweep(door_t, drive, t)
                detail.append(r)
                if not r["clear"]:
                    ok_both = False
            tested += 1
            if ok_both:
                best = {
                    "hx": hx, "floor": fy, "z0": z0, "z1": z1,
                    "growth": growth, "total": total, "walls": walls,
                    "detail": detail,
                }
                print("FOUND clear cavity at max face growth %.0f mm "
                      "(hx=%.0f floor=%.0f z0=%.0f z1=%.0f) after %d trials" % (
                          growth, hx, fy, z0, z1, tested))
                for r in detail:
                    print_result(r)
                print("  walls: top=%.1f floor=%.1f side=%.1f" % (
                    walls["top_wall"], walls["floor_wall"],
                    walls["side_wall_to_tier1"]))
                break
            # progress every 20 trials
            if tested % 20 == 0:
                print("  ... tested %d / still no full clear (last growth %g)" % (
                    tested, growth))

        if best is None:
            print("NO modest enlargement clears both stalls (%d candidates tested)."
                  % tested)
            # Diagnose: at max enlargement, what still hits?
            hx, fy, z0, z1 = HX_RANGE[-1], FLOOR_RANGE[-1], Z0_RANGE[-1], Z1_RANGE[-1]
            ok, walls = wall_ok(hx, fy, z0, z1)
            door_max = enlarge_door(door0, hx, fy, z0, z1)
            print("\nAt MAX trial cavity (hx=%.0f floor=%.0f z0=%.0f z1=%.0f) "
                  "walls %s:" % (hx, fy, z0, z1, walls))
            for t in (-STALL, 0.0, +STALL):
                r = sweep(door_max, drive, t)
                print_result(r)
            # Also report whether collision is cavity-wall vs outer wall band:
            # if max-cavity still collides, residual material is outside the cavity
            # cut (notch corridor / outer wall / snap zone).
            print("\nWHY NOT: residual collision after max cavity cut means the")
            print("  colliding surface is NOT a cavity wall that a modest hx/z/floor")
            print("  growth can remove. Likely offenders: pod_notch corridor, the")
            print("  solid tier legs outside the cavity, or the door outer wall band.")
            # Attribute residual volume to cavity-enlarged door vs a pure cavity solid
            for t in (-STALL, +STALL):
                d = pose_door(door_max, t, 0, 0)
                # at first-hit step of baseline for that tilt
                base = next(r for r in stall_results if abs(r["tilt"] - t) < 1e-9)
                if base["first"]:
                    step = base["first"][0]
                    part = base["first"][1]
                else:
                    step, part = "rot 0 deg", "neck_clevis"
                # re-find worst at this tilt with max door
                r = sweep(door_max, drive, t)
                if r["first"]:
                    print("  tilt %+g residual first hit: %s vs %s (%.2f mm3)" % (
                        t, r["first"][0], r["first"][1], r["first"][2]))
                else:
                    print("  tilt %+g: clear under max cavity (asymmetric?)" % t)

    # Verdict block
    print("\n" + "=" * 60)
    print("VERDICT")
    print("=" * 60)
    for r in baseline:
        tag = "CLEAR" if r["clear"] else "COLLIDES"
        extra = ""
        if not r["clear"] and r["first"]:
            extra = "  first=%s vs %s (%.1f mm3)" % r["first"]
        print("  baseline %-12s %s%s" % (r["label"], tag, extra))

    if stalls_clear:
        print("\nEnlargement: NOT NEEDED (baseline stall paths already clear).")
        print("Decision: do NOT change pod_cavity / pod_notch geometry.")
        decision = "none_needed"
    elif best is not None and best["growth"] <= 3:
        print("\nEnlargement: MODEST clear found.")
        print("  cavity hx=%.1f floor=%.1f z0=%.1f z1=%.1f" % (
            best["hx"], best["floor"], best["z0"], best["z1"]))
        print("  max face growth: %.0f mm  (sum %.0f mm)" % (
            best["growth"], best["total"]))
        print("  walls: top=%.1f floor=%.1f side=%.1f (>= %.1f)" % (
            best["walls"]["top_wall"], best["walls"]["floor_wall"],
            best["walls"]["side_wall_to_tier1"], MIN_WALL))
        print("Decision: APPLY cavity enlargement (deliverable 3).")
        decision = "apply"
    else:
        print("\nEnlargement: NONE within the modest grid clears both stalls.")
        print("Decision: do NOT change geometry; dead-motor service = hand-nod")
        print("  to neutral + chin prop (see docs/ASSEMBLY.md step 15).")
        decision = "no_clear"

    # Machine-readable tail for docs/automation
    print("\nDECISION=%s" % decision)
    if best is not None:
        print("BEST_CAVITY=%.1f,%.1f,%.1f,%.1f" % (
            best["hx"], best["floor"], best["z0"], best["z1"]))
        print("BEST_GROWTH_MM=%.1f" % best["growth"])

    # Exit 0 always on a successful report (nonzero only on geometry errors).
    # Neutral path failure already returned 2 above.
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        sys.stderr.write("probe_door_stall geometry error: %s\n" % e)
        raise

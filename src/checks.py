#!/usr/bin/env python3
"""Design-invariant gate for desk-pi (`make invariants`): unit tests for geometry.

Every check protects a USER-APPROVED feature that until now lived only as
CLAUDE.md prose. Renders don't catch a MISSING feature (nobody looks for what
isn't there), so each decision is encoded as an assertion against the exported
STL set (neutral-pose world coordinates), the GLB scene node list, or a PARAMS
relation. Each check carries a one-line comment naming the decision + date.

THE RULE (from the checks template): when the user approves a design
requirement, encode it here THE SAME TURN. Never delete or weaken a check
without explicit sign-off -- a failing check means the geometry regressed,
not that the check is stale.

Cheap by construction: param relations + targeted mesh contains-probes along
the REAL feature axes (planar sampling false-alarms on slanted bores); no
pairwise booleans. Whole suite runs in well under 90 s.

Python 3.9; trimesh + numpy. Run: python3 src/checks.py
"""
import math
import os
import sys
import warnings

import numpy as np

warnings.filterwarnings("ignore", category=RuntimeWarning)

import trimesh  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import P  # noqa: E402
from stlpaths import stlp, webpath  # noqa: E402

_results = []
_mesh_cache = {}


def check(name, ok, detail=""):
    _results.append((name, bool(ok), detail))
    print("  %s%s%s" % ("ok " if ok else "X  ", name, ("  (%s)" % detail) if detail else ""))
    return bool(ok)


def finish():
    fails = [n for n, ok, _ in _results if not ok]
    print("\n%d/%d invariants hold" % (len(_results) - len(fails), len(_results)))
    if fails:
        print("REGRESSED: " + ", ".join(fails))
        sys.exit(1)
    sys.exit(0)


def M(name):
    """Load stl/<subsystem>/<name>.stl (neutral-pose world coords), cached."""
    if name not in _mesh_cache:
        _mesh_cache[name] = trimesh.load(stlp(name + ".stl"))
    return _mesh_cache[name]


def inside(mesh, pts):
    """All probe points inside the solid."""
    return bool(mesh.contains(np.atleast_2d(np.asarray(pts, float))).all())


def clear(mesh, pts):
    """No probe point inside the solid (bore/void is open)."""
    return not mesh.contains(np.atleast_2d(np.asarray(pts, float))).any()


def bore_pierces(mesh, start, direction, length, n=12):
    """Bore open along its REAL axis: every probe point along it lies outside."""
    d = np.asarray(direction, float)
    d = d / np.linalg.norm(d)
    pts = np.asarray(start, float) + np.outer(np.linspace(0.0, length, n), d)
    return clear(mesh, pts)


def main():
    print("checks: desk-pi design invariants")

    # ---------------- param relations (free) ----------------------------------

    # user 2026-07-07 (docs/WORM.md): REAL involute worm center distance is 11.9
    # (pitch r 4.4 + m1.25 x 12T / 2), NOT the old worm_od*0.4 guess of 11.5.
    cd = P["worm_pitch_r"] + P["worm_module"] * P["worm_wheel_teeth"] / 2
    check("worm CD 11.9 (pitch r 4.4 + m1.25 12T wheel)", abs(cd - 11.9) < 1e-9, "%.3f" % cd)

    # user 2026-07-11 (mid-drive stretch): the raised tank loop closes at EXACTLY
    # track_links x track_pitch -- track_wheelbase is the solved value.
    from tracks import _track_link_poses, _track_zc  # noqa: E402  (cheap import)
    try:
        poses = _track_link_poses(P["track_wheelbase"], P["track_wheel_r"],
                                  _track_zc(), P["track_links"])
        loop_ok = len(poses) == P["track_links"] == 64 and P["track_pitch"] == 10.0
    except AssertionError as e:
        loop_ok, poses = False, []
    check("track loop closes at exactly 64 x pitch 10", loop_ok,
          "%d poses" % len(poses))

    # user 2026-07-08 (screen_tray replaces rear standoffs): the module hangs on
    # its 4 FACTORY case-mount holes, outer pattern 126.2 x 65.65 (measured).
    pts = P["scr_mount_pts"]
    patt_ok = (len(pts) == 4
               and abs((pts[0][0] - pts[2][0]) - 126.2) < 1e-6
               and abs((pts[1][2] - pts[0][2]) - 65.65) < 1e-6)
    check("screen tray: 4 factory-boss points, 126.2 x 65.65 pattern", patt_ok)

    # user 2026-07-06 (design-styling): forehead LED recess sized 42 x 5 for a
    # NARROW addressable strip (a 53.3-long 8x5050 stick does NOT fit -- BOM note).
    check("led_slot params 42 x 5", P["led_slot_w"] == 42.0 and P["led_slot_h"] == 5.0)

    # ---------------- GLB scene: parts that must exist -------------------------
    scene = trimesh.load(webpath("assembly.glb"), force="scene")
    nodes = {g.split(".")[0] for g in scene.geometry.keys()}
    geoms = set(scene.geometry.keys())

    # user 2026-07-10/11 (toy-tank hull + twin rear ring): THREE cliff/obstacle
    # HC-SR04 up front + rear obstacle = 4 sensor placeholders in the scene.
    check("4x HC-SR04 sensor nodes in scene",
          {"sensor_us", "sensor_us_rear", "sensor_cliff", "sensor_cliff_rear"} <= nodes)

    # user 2026-07-13 (split the rear housing for faster printing): chassis_lower_rear
    # peels its feature-dense rear end into a bolt-on chassis_lower_tail at lower_seam2_y.
    check("chassis_lower_tail present (rear housing split)", "chassis_lower_tail" in nodes)

    # user 2026-07-14 (hull/base split): the free electronics (Arduino/IMU/SW-420) live
    # on a removable chassis_base so the in-flux components iterate without the hull.
    check("chassis_base present (equipment base)", "chassis_base" in nodes)

    # user 2026-07-14 round 2 (separate by stability, side walls): the wall bands the
    # pod RAILS + TT MOTORS mount to are bolt-in panels; the hull tub is OPEN there.
    check("4 chassis_side panels present",
          {"chassis_side_L_front", "chassis_side_L_rear",
           "chassis_side_R_front", "chassis_side_R_rear"} <= nodes)
    # shaft pass Ø8 open through each panel at both stations, and the HULL wall
    # absent in the band (the tub must not grow the wall back).
    check("TT shaft bore open through chassis_side_R_rear",
          bore_pierces(M("chassis_side_R_rear"), (64.0, P["spr_y"], 28.4698), (1, 0, 0), 7.0))
    check("TT shaft bore open through chassis_side_R_front",
          bore_pierces(M("chassis_side_R_front"), (64.0, P["spr_y2"], 28.4698), (1, 0, 0), 7.0))
    check("hull wall OPEN in the panel band (lower_rear)",
          clear(M("chassis_lower_rear"), [(67.5, P["spr_y"], 30.0), (-67.5, P["spr_y"], 30.0)]))
    # fittings audit 2026-07-14: the integral web buried the LOWER TT gearbox M3
    # (z 16.57) + its gap nut -- the bore must pierce wall AND web, with the nut
    # slot open from below.
    check("lower TT M3 open through wall + web (rear station, R panel)",
          bore_pierces(M("chassis_side_R_rear"), (64.0, P["spr_y"] + 20.3, 28.4698 - 8.75),
                       (1, 0, 0), 10.0)
          and clear(M("chassis_side_R_rear"), [(72.0, P["spr_y"] + 20.3, 14.8)]))
    check("lower TT M3 open through wall + web (front station, R panel)",
          bore_pierces(M("chassis_side_R_front"), (64.0, P["spr_y2"] - 20.3, 28.4698 - 8.75),
                       (1, 0, 0), 10.0)
          and clear(M("chassis_side_R_front"), [(72.0, P["spr_y2"] - 20.3, 14.8)]))
    check("panels span the hull seams (front: y26, rear: y-88)",
          M("chassis_side_R_front").bounds[0][1] < 20.0
          and M("chassis_side_R_front").bounds[1][1] > 32.0
          and M("chassis_side_R_rear").bounds[0][1] < -94.0
          and M("chassis_side_R_rear").bounds[1][1] > -82.0)
    # user 2026-07-14 round 3 (pod_rail_L/R deleted): the wheel beam is INTEGRAL to
    # the side panels -- beam material present at the proven section, M4 axle bore
    # open at the y 57.5 station, and no pod_rail nodes left in the scene.
    check("wheel beam integral to the R front panel (x 74..80.4 / z 14..26)",
          inside(M("chassis_side_R_front"), [(77.2, 70.0, 20.0), (77.2, 20.0, 20.0)]))
    check("M4 bolt-axle bore open through the panel beam (y 57.5 station)",
          bore_pierces(M("chassis_side_R_front"),
                       (73.0, P["roadwheel_ys"][0],
                        (25.32 - P["track_wheel_r"]) + 3.5 + P["roadwheel_d"] / 2 + 0.1),
                       (1, 0, 0), 8.0))
    check("pod_rail nodes deleted", not {"pod_rail_L", "pod_rail_R"} & nodes)
    # user 2026-07-14 round 4 (standalone track module): the panels run to the end
    # axles -- END TOWERS replace the deck pylons (front tension slot open across
    # the travel, rear Ø8.4 open, tower material present) and the deck is pylon-free.
    ey_ax = P["track_wheelbase"] / 2
    check("front END TOWER on the panel carries the tension slot",
          inside(M("chassis_side_R_front"), [(67.4, 140.0, 44.0), (67.4, 122.0, 44.0)])
          and all(bore_pierces(M("chassis_side_R_front"), (60.0, ey_ax + dy, 38.3185),
                               (1, 0, 0), 12.0)
                  for dy in (-P["idler_slot_in"], 0.0, P["idler_slot_out"])))
    check("rear END TOWER on the panel carries the Ø8.4 end-axle bore",
          inside(M("chassis_side_R_rear"), [(67.4, -136.0, 44.0), (67.4, -122.0, 44.0)])
          and bore_pierces(M("chassis_side_R_rear"), (60.0, -ey_ax, 38.3185), (1, 0, 0), 12.0))
    check("deck pylons deleted (overhang open at the axle line)",
          clear(M("chassis_deck_front"), [(66.0, ey_ax, 38.3185), (-66.0, ey_ax, 38.3185)])
          and clear(M("chassis_deck_rear"), [(66.0, -ey_ax, 38.3185), (-66.0, -ey_ax, 38.3185)]))
    # splice: the two pieces half-lap in the L-return and screw together, so a side
    # assembles rigid without any chassis_lower_* piece.
    check("panel splice lap present (front upper tongue over rear lower tongue)",
          inside(M("chassis_side_R_front"), [(72.0, -20.0, 24.0)])
          and inside(M("chassis_side_R_rear"), [(72.0, -20.0, 17.0)]))

    # user 2026-07-08 (master link + keepers): loop closes tool-openable.
    check("master links in both loops",
          {"track_L.link_00_master", "track_R.link_00_master"} <= geoms)

    # user 2026-07-14 (viewer nav: NOTHING may land in the Uncategorized bucket):
    # every GLB scene node must match a category regex in the viewer's TREE. The
    # regexes are parsed straight out of web/viewer_glb.html so viewer and gate
    # cannot drift; a new part therefore needs its TREE entry the same turn.
    import json
    import re
    import struct
    with open(webpath("viewer_glb.html")) as f:
        _tree_src = f.read().split("const TREE = [", 1)[1].split("];", 1)[0]
    cat_res = [re.compile(p) for p in re.findall(r",\s*/(\^.+?)/\]", _tree_src)]
    check("viewer TREE regexes parsed from viewer_glb.html", len(cat_res) >= 10,
          "%d regexes" % len(cat_res))
    with open(webpath("assembly.glb"), "rb") as f:
        _glb = f.read()
    _jlen = struct.unpack("<I", _glb[12:16])[0]
    node_names = {n.get("name", "part")
                  for n in json.loads(_glb[20:20 + _jlen]).get("nodes", [])
                  if "mesh" in n}
    uncat = sorted(n for n in node_names if not any(r.match(n) for r in cat_res))
    check("every scene node categorized in the viewer nav",
          not uncat,
          (", ".join(uncat[:6]) + ("..." if len(uncat) > 6 else "")) if uncat
          else "%d nodes covered" % len(node_names))

    # user 2026-07-13 (integrate downloaded electronics into the assembly): the
    # real bought meshes (docs/ELECTRONICS.md) must be on disk so refparts poses
    # them instead of silently falling back to the placeholder boxes.
    import refparts
    _repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    check("reference electronics meshes present (refparts)",
          all(os.path.exists(os.path.join(_repo, spec[0]))
              for spec in refparts._SPEC.values()))

    # user 2026-07-12 (fast pan/tilt): pan 2:1 spur stage exists as pan_gears.
    check("pan_gears (fast-pan 2:1 stage) present", "pan_gears" in nodes)

    # user 2026-07-12 (neck styling): trim_neckfoot pedestal collar present.
    check("trim_neckfoot present", "trim_neckfoot" in nodes)

    # ---------------- head_door: tool-free retention ---------------------------
    door = M("head_door")
    # user 2026-07-10 ("easy to open and close"): per-leg SNAP TONGUE BARBS proud
    # past the void wall (x +-54.35 -> +-55.55) at plug level z 116..119.5.
    vo = P["door_hx"] - P["door_lip"] - P["door_fit"]
    bz = sum(P["door_snap_barb_z"]) / 2.0
    check("head_door snap barbs (both legs)",
          inside(door, [(vo + 0.65, -64.4, bz), (-(vo + 0.65), -64.4, bz)]))
    # user 2026-07-10: each tongue is FREED by a vertical slit (else it can't flex).
    sx = vo - P["door_snap_w"] - P["door_snap_slot_w"] / 2.0
    check("head_door snap slits open (tongues freed)",
          clear(door, [(sx, -66.0, 130.0), (-sx, -66.0, 130.0)]))
    # user 2026-07-10: 2x top HOOK tabs are the pivot (screwless door).
    check("head_door top hooks", inside(door, [(P["door_hook_x"], -64.9, 191.5),
                                               (-P["door_hook_x"], -64.9, 191.5)]))

    # ---------------- track links: PIP strips ----------------------------------
    st = M("track_strip_L1")   # strip-local frame: link i's own pin at y = i*pitch
    # user 2026-07-12 (print-in-place strips): 45 deg KEELS under every knuckle
    # band (A at own pin, B at far pin) make grouser-down self-supporting.
    check("track link keels (A + B knuckle bands)",
          inside(st, [(15.0, 1.0, -4.0), (-15.0, 1.0, -4.0),
                      (6.9, 9.0, -4.0), (-6.9, 9.0, -4.0)]))
    # user 2026-07-12: keels stay OUT of the +-4.9 sprocket channel.
    check("sprocket channel keel-free (|x|<4.9)",
          clear(st, [(0.0, 1.0, -5.5), (4.0, 1.0, -5.0)]))
    # user 2026-07-12: mid links carry an INTEGRAL Ø2.0 pin (the sprocket drives
    # on it); strip-FIRST link keeps an open A bore for the Ø1.75 boundary pin.
    check("integral PIP pin in mid link", inside(st, [(12.0, 10.0, 0.0), (-12.0, 10.0, 0.0)]))
    check("strip-first link A bore open",
          clear(st, [(-15.0, 0.0, 0.0), (0.0, 0.0, 0.0), (15.0, 0.0, 0.0)]))
    # user 2026-07-08 (master link): keeper bars are 2 separate slide-in pieces.
    check("track keepers = 2 bars each",
          M("track_keeper_L").body_count == 2 and M("track_keeper_R").body_count == 2)

    # ---------------- tilt homing: fins + stop posts (stall at +-33.8 deg) -----
    yt, zt = P["tilt_axis_y"], P["tilt_axis_z"]
    fin_pts = []
    for sxf in (1, -1):
        for ang in (55.0, -55.0):    # fins at +-55 deg from straight-down about X
            a = math.radians(ang)
            y0 = -11.125             # fin box center radius on the clamp tube
            fin_pts.append((sxf * 29.0, y0 * math.cos(a) + yt, y0 * math.sin(a) + zt))
    fL, fR = M("head_back_frame_L"), M("head_back_frame_R")
    # user 2026-07-08 (stall homing): 4 radial fins on the head clamp tubes at
    # +-55 deg; they meet the cheek posts at +-33.8 deg tilt.
    check("tilt clamp-tube fins x4 (+-55 deg)",
          inside(fR, [p for p in fin_pts if p[0] > 0])
          and inside(fL, [p for p in fin_pts if p[0] < 0]))
    # user 2026-07-08: TILT-STOP POSTS r12..17 behind the axle on both cheeks.
    check("neck cheek stop posts (x +-26, y -32.5)",
          inside(M("neck_clevis"), [(26.0, yt - 14.5, zt), (-26.0, yt - 14.5, zt)]))

    # ---------------- pan homing: lug az 225 + deck posts az 118/332 -----------
    def raz(az, r=28.0):
        a = math.radians(az)
        return (r * math.cos(a), r * math.sin(a))

    # user 2026-07-08 (stall homing): platform underside lug at azimuth 225.
    lx, ly = raz(225.0)
    check("pan homing lug (az 225, platform underside)",
          inside(M("pan_platform"), [(lx, ly, 54.0), (lx, ly, 57.0)]))
    # user 2026-07-08: two deck stop posts at az 118 / 332 (contact at +-93.3 deg).
    check("pan deck stop posts (az 118/332)",
          all(inside(M("chassis_deck_center"), [raz(az) + (z,) for z in (47.0, 50.0)])
              for az in (118.0, 332.0)))

    # ---------------- HC-SR04 recesses: bores pierce along the REAL axes -------
    fw = P["chassis_l"] / 2.0
    # user 2026-07-10 + 2026-07-11 (front grille + twin rear ring): Ø16.6 obstacle
    # barrels pierce the front AND rear walls at (+-13, z 32), axis Y.
    check("front obstacle US barrels pierce",
          all(bore_pierces(M("chassis_lower_front"), (sxb * P["us_dx"], fw - 6.0,
                                                      P["us_cz"]), (0, 1, 0), 7.0)
              for sxb in (1, -1)))
    check("rear obstacle US barrels pierce",
          all(bore_pierces(M("chassis_lower_rear"), (sxb * P["us_dx"], -(fw - 6.0),
                                                     P["us_cz"]), (0, -1, 0), 7.0)
              for sxb in (1, -1)))
    # user 2026-07-10 round 2/3 (toy-tank slopes): cliff barrels pierce BOTH deck
    # slopes along the real 33.7 deg slope normal (down-forward / down-rearward).
    sa = math.atan2(20.0, 30.0)      # deck_overhang slope: (120,46) -> (150,66)
    cliff_ok = True
    for sgn, part in ((1, "chassis_deck_front"), (-1, "chassis_deck_rear")):
        sn = np.array([0.0, sgn * math.cos(sa), math.sin(sa)])   # up-slope unit
        nn = np.array([0.0, sgn * math.sin(sa), -math.cos(sa)])  # outward normal
        pb = np.array([0.0, sgn * fw, P["chassis_split_z"]]) + P["cliff_v"] * sn
        for sxb in (1, -1):
            start = pb + np.array([sxb * P["us_dx"], 0.0, 0.0]) - 4.5 * nn
            cliff_ok &= bore_pierces(M(part), start, nn, 4.0)
        cliff_ok &= inside(M(part), [pb - 2.5 * nn])   # skin between the barrels
    check("cliff US barrels pierce both slopes (33.7 deg normal)", bool(cliff_ok))

    # ---------------- end axles: TOWER NUT CAGES (v2, cheeks deleted) ---------
    wb2 = P["track_wheelbase"] / 2.0
    za = 38.3185                      # end-axle line at track_raise 13
    # v2 end simplification (2026-07-14): the prow cheeks + their M8 ducts/
    # channels are GONE; the NYLOC rides LEDGE+ROOF cage strips on each panel
    # tower's inboard face (gap 13.4 = AF 13 + 0.4, axial load on the tower
    # face, strips stop rotation; FRONT cage spans the tension travel). A bare
    # track module can tension with zero hull pieces.
    cage_ok = True
    for pnl_, ey_ in (("chassis_side_R_front", wb2), ("chassis_side_R_rear", -wb2)):
        m = M(pnl_)
        dys = (-P["idler_slot_in"], 0.0, P["idler_slot_out"]) if ey_ > 0 else (0.0,)
        for dy in dys:
            cage_ok &= clear(m, [(58.0, ey_ + dy, za),          # nut void between
                                 (58.0, ey_ + dy, za - 5.9),    # the strips
                                 (58.0, ey_ + dy, za + 5.9)])
        cage_ok &= inside(m, [(58.0, ey_, za - 6.7 - 1.5),      # ledge below
                              (58.0, ey_, za + 6.7 + 0.5)])     # roof above
    check("M8 tower nut cages (ledge+roof, front spans the travel)", bool(cage_ok))
    # USB-C entry: recessed slot through the plain rear wall at x -38 (the cheek
    # corridor died with the cheeks).
    check("USB-C slot through the rear wall (x -38)",
          bore_pierces(M("chassis_lower_tail"), (-38.0, -123.0, 34.0), (0, 1, 0), 8.0))

    # user 2026-07-14 ("hanging thread in the LCD frame"): the bezel seam's
    # forehead flange pad must be FUSED to the face (it floated loose in bezel_R
    # after the 2026-07-11 face move) -- and each bezel piece is ONE body.
    check("bezel forehead seam pad fused to the face",
          inside(M("head_bezel_R"), [(28.0, 27.6, 216.0), (28.0, 24.5, 210.5)])
          and len(M("head_bezel_R").split(only_watertight=False)) == 1
          and len(M("head_bezel_L").split(only_watertight=False)) == 1)

    # ---------------- head wall passages ---------------------------------------
    hw2 = P["head_w"] / 2.0
    # user 2026-07-11 ear v2 + centered ("only the tip of the microphone out",
    # "same distance from borders as humans"): Ø15 grommet bore per side wall
    # at (y -29, z 172.5).
    ey, ez = P["ear_y"], P["ear_z"]
    check("ear grommet bores Ø15 both side walls",
          bore_pierces(fR, (hw2 - 5.0, ey, ez), (1, 0, 0), 6.0)
          and bore_pierces(fL, (-(hw2 - 5.0), ey, ez), (-1, 0, 0), 6.0)
          and inside(fR, [(hw2 - 2.0, ey, ez + 19.5)]))   # wall material above
    # user 2026-07-08 (microSD service slot): card ejects -X through the LEFT
    # bezel wall (slot is FORWARD of the y=2 split); sd_plug closes it.
    sy = sum(P["sd_slot_y"]) / 2.0
    sz = sum(P["sd_slot_z"]) / 2.0
    bzL = M("head_bezel_L")
    check("microSD slot pierces left wall + sd_plug exists",
          bore_pierces(bzL, (-(hw2 - 5.0), sy, sz), (-1, 0, 0), 6.0)
          and inside(bzL, [(-(hw2 - 2.0), sy, 170.0)])    # wall material above slot
          and os.path.exists(stlp("sd_plug.stl")))
    # user 2026-07-06 (design-styling): LED recess open in the forehead face,
    # face material retained above it (slot z 223.5..228.5 < wall top).
    bzR = M("head_bezel_R")
    fy = P["body_front_y"]
    check("led_slot recess open + face wall above",
          clear(bzR, [(P["led_cx"], fy - 0.7, P["led_cz"])])
          and inside(bzR, [(P["led_cx"], fy - 0.7, P["led_cz"] + 5.0)]))

    # ---------------- antennas -------------------------------------------------
    # user 2026-07-10 (twin deployable antennas): Ø7 GUIDE BORES through the head
    # top wall at (+-85, -31) -- the masts must be able to pass.
    zt_top = 242.0 - 3.6
    check("antenna guide bores through top wall",
          bore_pierces(fL, (-P["ant_x"], P["ant_y"], zt_top), (0, 0, 1), 3.2)
          and bore_pierces(fR, (P["ant_x"], P["ant_y"], zt_top), (0, 0, 1), 3.2)
          and inside(fR, [(75.0, P["ant_y"], 240.0)]))    # top wall material beside
    # user 2026-07-10: m0.8 RACK molded on each mast's -Y face (teeth protrude to
    # y ~-35.9 with 2.513 pitch; containment must VARY along the rack band).
    ant = M("antenna_L")
    zs = np.linspace(160.0, 200.0, 33)
    hits = ant.contains(np.array([(-P["ant_x"], -35.0, z) for z in zs]))
    above = ant.contains(np.array([(-P["ant_x"], -35.0, 230.0)]))
    check("antenna rack teeth on the mast (-Y face)",
          bool(hits.any() and (~hits).any() and not above.any()),
          "%d/%d tooth hits in band, none above rack top" % (int(hits.sum()), len(zs)))

    # ---------------- belly power tray ------------------------------------------
    # user 2026-07-08 (power decision, firmware/WIRING.md): the belly plate
    # carries the buck tray -- 4x Ø6 posts on a 40x20 grid (drop plate = drop
    # the power stage).
    bp = M("belly_plate")
    tray = [(-35.75, -53.0), (-35.75, -33.0), (4.25, -53.0), (4.25, -33.0)]
    check("belly plate + 4 power-tray posts",
          inside(bp, [(px + 2.0, py, 14.5) for px, py in tray]))

    # ---------------- hardware stand-ins ----------------------------------------
    # user 2026-07-15 ("include all items in the export so I would just assemble
    # with plastic till I get actual metal parts"): every buy-list metal part has
    # a print-oriented plastic stand-in in stl/hardware/ (src/standins.py), and
    # key interface dims match the placeholders they substitute.
    from standins import STANDINS
    hw_ok, hw_detail = True, ""
    for nm in STANDINS:
        pth = stlp(nm + ".stl")
        if not os.path.exists(pth):
            hw_ok, hw_detail = False, nm + " missing"
            break
    check("hardware stand-ins exported (%d parts)" % len(STANDINS), hw_ok, hw_detail)
    if hw_ok:
        ext = lambda n: (M(n).bounds[1] - M(n).bounds[0])
        check("stand-in interface dims (M8 shank / F688 seat / axle / pan ring)",
              abs(ext("hw_m8_bolt")[2] - 65.7) < 0.1            # M8x60 + 5.3 head
              and abs(ext("hw_f688_bushing")[0] - 18.2) < 0.1   # flange Ø in Ø18.5 recess
              and abs(ext("hw_tilt_axle")[1] - (P["head_w"] + 4)) < 0.1
              and abs(ext("hw_pan_ring")[0]
                      - (P["pan_race_circle_d"] + 5.8)) < 0.1)  # ball-circle torus

    finish()


if __name__ == "__main__":
    main()

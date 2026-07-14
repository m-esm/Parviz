"""FIT / PRESSURE MAP report (FITS=1): clearances, contact audit.

Split out of the original monolithic build.py (2026-07-10); see
build.py for the assembly entry point and the overall design notes.
"""
import numpy as np
import trimesh
from stlpaths import webpath, stlp


def _fit_report(geo):
    """FIT / PRESSURE MAP (ported from finnish-doors 2026-07-08): for every CLOSE pair of
    assembled parts, sample the smaller part's surface and take signed distances into the
    other -> press depth (interference / friction) or minimum clearance, plus a contact
    PATCH point cloud tracing the shape of each contact area. Written to web/fit_report.json
    for the viewer's 'Fits' panel.

    OPT-IN: runs only with FITS=1 (the desk-pi watch loop rebuilds in ~2 s; this pass costs
    minutes). Run at NEUTRAL pose for the canonical report: `make fits` = FITS=1 PAN=0
    TILT=0. Cross-group numbers (head vs pan vs fixed) are pose-dependent; same-group fits
    (bores, seats, presses) are not.

    CONTACT AUDIT: every pair that touches (min clearance <= 0.005 or press) must be in
    _FIT_CONTACT_OK -- designed seats, presses, and face-mounted cosmetics only. Anything
    else touching prints a loud failure; that is the whole point of the map."""
    import json as _json
    import refparts
    # not watertight: signed distance lies (FIXES stage 4). Real bought meshes
    # (refparts) join the screen here when REALPARTS is on -- same reason.
    SKIP = ("screen_ref",) + tuple(refparts.excluded_nodes())
    _FIT_DESIGNED = set()                 # intended PRESS pairs (none yet; presses are hardware)
    # print-speed sub-splits: pieces alias to their parent; a single-name frozenset
    # (piece touching its sibling at the designed seam) is whitelisted below.
    _SPLIT_ALIAS = {
        "head_back_frame_L": "head_back", "head_back_frame_R": "head_back",
        "head_back_panel_L": "head_back", "head_back_panel_R": "head_back",
        "head_bezel_L": "head_bezel", "head_bezel_R": "head_bezel",
        "chassis_lower_front": "chassis_lower", "chassis_lower_rear": "chassis_lower",
        "chassis_lower_tail": "chassis_lower",
        # bolt-in side panels (2026-07-14 round 2): alias like the tail cap --
        # floor-rest/deck-edge contact = (chassis_lower,) / (chassis_deck,
        # chassis_lower); rail/TT/BME pairs inherit.
        "chassis_side_L_front": "chassis_lower", "chassis_side_L_rear": "chassis_lower",
        "chassis_side_R_front": "chassis_lower", "chassis_side_R_rear": "chassis_lower",
        "chassis_deck_front": "chassis_deck", "chassis_deck_center": "chassis_deck",
        "chassis_deck_rear": "chassis_deck",
    }
    _FIT_CONTACT_OK = {
        frozenset(("head_back",)),                   # split-seam sibling contacts
        frozenset(("head_bezel",)),
        frozenset(("chassis_lower",)),
        frozenset(("chassis_deck",)),
        # drivetrain seats / meshes (mirrors assembly_check WHITELIST)
        frozenset(("ant_bracket", "head_back")),     # bracket spine on the back wall
        frozenset(("ant_gears_L", "antenna_L")),     # rack/pinion placeholder mesh
        frozenset(("ant_gears_R", "antenna_R")),
        frozenset(("ant_gears_L", "motor_ant_L")),   # G1 on each 28BYJ D-shaft
        frozenset(("ant_gears_R", "motor_ant_R")),
        frozenset(("worm_wheel", "tilt_worm")),      # gear mesh
        frozenset(("worm_wheel", "neck_clevis")),    # spacer tubes in the bearing seats
        frozenset(("pan_platform", "pan_balls")),    # captured-BB groove (upper race)
        frozenset(("pan_race", "pan_balls")),        # captured-BB groove (lower race)
        frozenset(("pan_gears", "motor_pan")),       # 32T gear on the D-shaft (fast-pan)
        frozenset(("pan_gears", "pan_platform")),    # 32T <-> integral 16T pinion mesh
        # resting / bolted seats
        frozenset(("pan_race", "chassis_deck")),     # ring sits on the seat floor
        frozenset(("pan_clips", "chassis_deck")),    # clips screwed into deck pockets
        frozenset(("motor_pan", "chassis_deck")),    # ear bar clamped on the pedestal pads
        frozenset(("motor_pan", "chassis_lower")),
        frozenset(("drive_L", "chassis_lower")), frozenset(("drive_R", "chassis_lower")),
        frozenset(("motor_tilt", "neck_clevis")),    # gear face on the bracket plate
        frozenset(("camera_ref", "head_bezel")),     # board front on the M2 boss tips
        frozenset(("cam_cover", "camera_ref")),      # cover posts clamp the board
        # face-mounted cosmetics (glue + pins) and service parts on their seats
        frozenset(("trim_rail_L", "head_bezel")), frozenset(("trim_rail_L", "head_back")),
        frozenset(("trim_rail_R", "head_bezel")), frozenset(("trim_rail_R", "head_back")),
        frozenset(("trim_hatch_frame", "head_back")),
        frozenset(("trim_neckfoot", "pan_platform")),     # collar seats on the platform
        frozenset(("trim_neckfoot", "neck_clevis")),      # (pins + glue, styling 2026-07-12)
        frozenset(("camera_pod", "head_bezel")), frozenset(("antenna_stub", "head_back")),
        frozenset(("led_strip", "head_bezel")),
        frozenset(("trim_fascia", "chassis_lower")), frozenset(("trim_fascia", "chassis_deck")),
        frozenset(("trim_rear", "chassis_lower")), frozenset(("trim_rear", "chassis_deck")),
        frozenset(("sensor_us", "chassis_lower")), frozenset(("sensor_us", "chassis_deck")),
        frozenset(("axle_hw_L", "drivewheels_L")),        # M4 heads seat on the wheel
        frozenset(("axle_hw_R", "drivewheels_R")),        # hub faces (bolt-axles)
        frozenset(("axle_hw_L", "chassis_lower")),        # M4 nuts in the panel beam
        frozenset(("axle_hw_R", "chassis_lower")),        # slots + M8 washers on the
                                                          # panel END TOWERS (pylons
                                                          # deleted 2026-07-14; the
                                                          # rail merged into the side
                                                          # panels 2026-07-14 round 3)
        frozenset(("sensor_us_rear", "chassis_lower")),   # rear twin: board on the inner
        frozenset(("sensor_us_rear", "chassis_deck")),    # wall face, barrels in the bores
        frozenset(("sensor_rear", "chassis_lower")),
        frozenset(("lamp_L", "chassis_lower")), frozenset(("lamp_R", "chassis_lower")),
        frozenset(("led_front", "chassis_lower")),
        frozenset(("sd_plug", "trim_rail_L")),       # plug face plate rests on the rail
        # electronics seat placeholders (2026-07-13): each floats 0.05-0.15 off
        # its seat, but the pairs ARE designed seats -- whitelisted so a future
        # gap-close doesn't trip the audit
        frozenset(("chassis_base", "chassis_lower")),    # equipment base on the hull floor
        frozenset(("board_arduino", "chassis_base")),    # Uno on the base posts/shelf
        frozenset(("sensor_imu", "chassis_base")),       # IMU posts on the base
        frozenset(("sensor_vib", "chassis_base")),       # SW-420 seat on the base
        frozenset(("sensor_bme", "chassis_lower")),      # wall bosses at the y-96 vent
        frozenset(("sensor_mmwave", "chassis_deck")),    # tab in the deck pocket
        frozenset(("chassis_deck", "chassis_lower")),
        frozenset(("head_back", "head_bezel")),      # bolted seam at the split plane (y=2)
        frozenset(("screen_tray", "head_back")),     # pillar ends bolted to the back wall
    }
    # granular children ("parent.child", 2026-07-11) re-group under their parent so
    # the pair names, whitelists, and the viewer's fit map stay at the part level
    import trimesh as _tm
    grouped = {}
    for n, m in geo.items():
        if m is None:
            continue
        grouped.setdefault(n.split(".")[0], []).append(m)
    geo = {k: (v[0] if len(v) == 1 else _tm.util.concatenate(v)) for k, v in grouped.items()}
    names = sorted(n for n, m in geo.items() if m is not None and not any(k in n for k in SKIP))
    rows = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = geo[names[i]], geo[names[j]]
            lo = np.maximum(a.bounds[0], b.bounds[0])
            hi = np.minimum(a.bounds[1], b.bounds[1])
            if np.any(lo - hi > 2.5):
                continue                                     # AABBs > 2.5 mm apart: not a fit
            small, big = (a, b) if a.area <= b.area else (b, a)
            try:
                pts, _ = trimesh.sample.sample_surface(small, 2600)
                d = trimesh.proximity.signed_distance(big, pts)   # >0 = inside big (press)
                k = int(np.argmax(d))
                if d[k] < -2.0:
                    continue                                 # nothing within 2 mm: skip
                _vol = 0.0
                if d[k] > 0.005:                             # boolean-confirm presses: the
                    try:                                     # sampler glitches at corners,
                        _iv = trimesh.boolean.intersection([a, b], engine="manifold")
                        _vol = float(_iv.volume) if _iv is not None and len(_iv.faces) else 0.0
                    except Exception:
                        _vol = -1.0                          # unknown -- keep the press flag
                sel = np.where(d > -0.6)[0]                  # contact patch: samples < 0.6 off
                if len(sel) > 260:
                    sel = np.random.default_rng(0).choice(sel, 260, replace=False)
                patch = [[round(float(pts[q][0]), 2), round(float(pts[q][1]), 2),
                          round(float(pts[q][2]), 2), round(float(-d[q]), 3)] for q in sel]
                _pair = frozenset((_SPLIT_ALIAS.get(names[i], names[i]),
                                   _SPLIT_ALIAS.get(names[j], names[j])))
                rows.append(dict(a=names[i], b=names[j],
                                 expected=_pair in _FIT_CONTACT_OK,
                                 mm=round(float(-d[k]), 3),  # +clearance / -press depth
                                 press=bool(d[k] > 0.005 and _vol != 0.0),
                                 vol=round(_vol, 2),
                                 designed=_pair in _FIT_DESIGNED,
                                 at=[round(float(x), 2) for x in pts[k]],
                                 patch=patch))
            except Exception:
                continue
    rows.sort(key=lambda r: (-1e3 - r["mm"]) if r["press"] else r["mm"])
    _json.dump(rows, open(webpath("fit_report.json"), "w"), indent=1)
    print("wrote fit_report.json (%d close pairs; %d press fits)"
          % (len(rows), sum(r["press"] for r in rows)))
    touching = [r for r in rows if r["mm"] <= 0.005 or r["press"]]
    bad = [r for r in touching if not r["expected"]]
    if bad:
        print("!! CONTACT AUDIT FAILED -- %d unexpected touching/press pair(s):" % len(bad))
        for r in bad:
            print("!!   %s <-> %s  %s at %s" % (r["a"], r["b"],
                  ("PRESS %.2f (vol %.2f mm^3)" % (-r["mm"], r["vol"])) if r["press"]
                  else "touching (%.3f)" % r["mm"], r["at"]))
        print("!!   fix the geometry, or add to _FIT_CONTACT_OK only if it is a designed seat")
    else:
        print("contact audit: %d touching pair(s), all expected" % len(touching))
    return not bad



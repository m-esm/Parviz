"""desk-pi -- tracked pan/tilt robot around the real 7" touchscreen.

Coordinate system: Z up, robot looks toward +Y (screen glass faces +Y).
Origin (0,0,0) = center of the desk contact plane.

Kinematic chain (bottom -> top):
    tank chassis          fixed base with two track pods and TT gearmotor placeholders
      -> PAN joint        yaw about vertical Z, driven by a 28BYJ D-shaft in the base
        -> pan_platform + neck_clevis  (rotate as one on the captured-BB race)
          -> TILT joint   pitch about horizontal X, driven by a self-locking worm
            -> rounded tablet head + screen/Pi + camera

The screen and Pi ride as one module inside the head. DSI/CSI ribbons stay inside the head;
only round power wires cross the pan/tilt joints. The default GLB render uses a preview pose
(`preview_pan_deg`, `preview_tilt_deg`) so motion is visible; set PAN=0 TILT=0 for neutral review.

Run:  python3 src/build.py            -> web/assembly.glb
      EXPORT=1 python3 src/build.py   -> also writes per-part STLs into stl/<subsystem>/
"""
import os
import numpy as np
import trimesh
from trimesh.transformations import rotation_matrix as R

from stlpaths import webpath, stlp
from params import DEG, EXPORT, P, TAU
from geo import _T, _color, box, cyl, dbore_neg, inter, sub, uni
from gears import gear_disc, load_gear_stl, worm, worm_cd
from screen import load_screen, screen_pose
from tracks import _track_zc, build_tracks
from motors import motor_28byj, motor_tt
from pan import build_pan_clips, build_pan_platform, build_pan_race
from neck import build_neck_clevis, build_tilt_carrier
from head import (build_ant_drive, build_antennas, build_arms, build_cam_pod, build_hatch_frame,
                  build_head_parts, build_head_rails, build_led_strip,
                  build_screen_tray, build_sd_plug)
from chassis import build_belly_plate, build_chassis_parts, build_fascia, build_pod_rails
from fitmap import _fit_report


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def build():
    scene = trimesh.Scene()
    zt = P["tilt_axis_z"]
    yt = P["tilt_axis_y"]

    # pose + output overrides (for generating review render sets)
    pan_deg = float(os.environ.get("PAN", P["preview_pan_deg"]))
    tilt_deg = float(os.environ.get("TILT", P["preview_tilt_deg"]))
    head_name = "head_wedge" if os.environ.get("SOLIDHEAD") == "1" else "head_shell"
    out_name = os.environ.get("OUT", "assembly.glb")

    # transforms
    pan = R(pan_deg * DEG, (0, 0, 1), (0, 0, 0))
    tilt = R(tilt_deg * DEG, (1, 0, 0), (0, yt, zt))
    M_head = pan @ tilt          # head parts: tilt then pan
    M_pan = pan                  # pan-group parts

    fit_geo = {}                     # name -> posed world mesh, for the FITS=1 pressure map
    pose_groups = {"head": [], "pan": []}   # node -> kinematic group, for the viewer's
                                            # live pan/tilt sliders (web/pose.json)

    def add(mesh, M, export_name=None):
        g = mesh.copy()
        g.apply_transform(M)
        scene.add_geometry(g, node_name=mesh.metadata["name"])
        fit_geo[mesh.metadata["name"]] = g
        if M is M_head:
            pose_groups["head"].append(mesh.metadata["name"])
        elif M is M_pan:
            pose_groups["pan"].append(mesh.metadata["name"])
        if EXPORT and export_name:
            mesh.export(stlp(export_name))

    # --- FIXED: printable split tank chassis body + two track pods ---
    for ch in build_chassis_parts():
        add(ch, np.eye(4), f"{ch.metadata['name']}.stl")
    add(build_belly_plate(), np.eye(4), "belly_plate.stl")   # bolt-on floor access plate
    for fp in build_fascia():                        # front fascia set (design ref)
        add(fp, np.eye(4))
    for trk in build_tracks():
        add(trk, np.eye(4), trk.metadata["export"])
    for rail in build_pod_rails():                   # body<->pod join receiving rails
        add(rail, np.eye(4), rail.metadata["export"])

    # track drive: 2x TT gearmotor (own 1, BUY 1 more) INSIDE the chassis, gearbox face 0.1 off
    # the side-wall inner face; the shaft crosses the wall (Ø8 pass, wall thinned to a 3 mm web)
    # and the sprocket's inboard hub grips the flats just outside. Shaft axis = sprocket axis
    # (y=-wb/2, z=_track_zc()). Tab registers in a rear-wall pocket; nub in a wall pocket;
    # 2x M3 through gearbox + wall, nuts in the pod gap. Skid steer.
    wbd = P["track_wheelbase"]
    ax = P["chassis_w"] / 2 - 5.0 - P["tt_gearbox"][2] / 2 - 0.1
    for sx in (-1, 1):
        dm = motor_tt("drive_L" if sx < 0 else "drive_R")
        if sx < 0:
            dm.apply_transform(R(TAU / 2, (0, 1, 0)))   # mirror about Y: shaft -X, tab stays rear
        dm.apply_translation((sx * ax, -wbd / 2, _track_zc() + P["track_raise"]))
        add(dm, np.eye(4))

    # --- PAN GROUP ---
    add(build_pan_platform(), M_pan, "pan_platform.stl")

    neck = build_neck_clevis()                       # already built in world Z (sits on base top)
    scene_neck = neck.copy(); scene_neck.apply_transform(M_pan)
    scene.add_geometry(scene_neck, node_name="neck_clevis")
    pose_groups["pan"].append("neck_clevis")         # bypasses add(): tag its group by hand
    if EXPORT:
        neck.export(stlp("neck_clevis.stl"))

    # --- TILT WORM DRIVE (self-locking single-start) ---
    wx = P["worm_wheel_x"]
    cd = worm_cd()
    wz = zt - cd
    wheel_r = P["worm_module"] * P["worm_wheel_teeth"] / 2
    # worm wheel keyed to the axle -> turns WITH the head (M_head). Width 7 centered on x=0,
    # D-KEYED hub (maintenance pass 2026-07-08: a key ledge in the hub bore rides a flat
    # filed on the Ø5 axle -- positive torque, no slip; replaces the old M3 grub, which was
    # BLIND once the cartridge sat in the cheeks and relied on point friction), and spacer
    # TUBES out to both 695 inner races: they react the ~10 N worm thrust / 3.7 N wheel
    # axial load (they also locate the wheel axially, so no extra retainer is needed).
    # REAL generated teeth (docs/WORM.md): 12T involute helical wheel + single-start worm,
    # verified meshing at CD 11.9 / 0.000 mm3. PLACEHOLDER_GEARS=1 restores the readable
    # gear_disc/worm placeholders (cheap insurance + regen testing).
    placeholder_gears = os.environ.get("PLACEHOLDER_GEARS") == "1"
    if placeholder_gears:
        wheel = gear_disc(wheel_r, P["worm_wheel_teeth"], P["worm_wheel_w"],
                          2.5 * P["worm_module"], axis="x")
    else:
        # toothed blank only: axis X, bore Ø5.2, width 7, centered at origin -- exactly where
        # gear_disc built; the hub/tube union, bore re-cut and grub pilot below apply unchanged.
        wheel = load_gear_stl("worm_wheel_real.stl")
        # cosmetic mesh clocking: at the assembly's relative pose (wheel midplane crosses the
        # worm at worm-local y +6) the blank's zero-interference phase is 24.5 deg (scanned per
        # docs/WORM.md note 4 / mesh_check in tools/gears/gen_worm_drive.py). M_head then adds
        # tilt_deg about the SAME axis, so pre-rotate by (24.5 - tilt) mod one tooth pitch (30)
        # and the teeth visually mesh at ANY preview/sweep pose. Physically meaningless (the
        # wheel is 30-deg tooth-periodic); the grub pilot below stays clocked +Z regardless.
        wheel.apply_transform(R(((24.5 - tilt_deg) % 30.0) * DEG, (1, 0, 0)))
    hub = cyl(5.5, 5.5, axis="x"); hub.apply_translation((6.25, 0, 0))          # x 3.5..9
    tub_p = cyl(4.0, 9.0, axis="x"); tub_p.apply_translation((13.5, 0, 0))      # hub -> +X race
    tub_m = cyl(4.0, 14.5, axis="x"); tub_m.apply_translation((-10.75, 0, 0))   # wheel -> -X race
    wheel = uni([wheel, hub, tub_p, tub_m])
    wheel = sub(wheel, cyl(P["axle_d"] / 2 + 0.1, 40, axis="x"))                # Ø5.2 over the axle
    # D-KEY LEDGE in the hub bore (x 3.5..9, the plain hub zone -- never through a tooth
    # root): a chord segment whose flat face sits 1.55 off the axis = a 1.0-deep flat on
    # the Ø5 axle (flat at 1.5) + 0.05 clearance (review: the first cut's +0.15 was
    # +-4.4 deg of head backlash -- worse than the grub it replaced; coupon from +0.05
    # and open only if the axle won't slide). Both ledge ends get 45 deg lead-in ramps:
    # printed axle-vertical, a square ledge end is a floating internal shelf whose
    # drooped loops land exactly on the sliding surface, and the ramp doubles as the
    # axle-flat lead-in. AXLE SPEC (docs/ASSEMBLY.md): SOLID rod only (a tube leaves
    # 0.25 wall under the flat); flat runs from the INSERTION end to ~15 past center
    # (a keyed bore needs its channel from the rod's leading end); only the ~6 mm under
    # the hub needs a clean 1.0 +-0.1 depth. The flat crossing the +X 695 seat means
    # that inner race rides a D-profile -- fine, the race is clamped by the tubes.
    half = box(6.0, 6.0, 2.0)
    half.apply_translation((0, 0, 1.55 + 1.0))           # halfspace z >= 1.55 (the flat plane)
    ledge = inter(cyl(2.7, 5.5, axis="x"), half)         # r2.7: 0.1 into the bore wall, fuses
    for se in (-1, 1):                                   # 45 deg end ramps (see above)
        wdg = box(2.0, 7.0, 2.0)
        wdg.apply_transform(R(TAU / 8, (0, 1, 0)))
        wdg.apply_translation((se * 2.75, 0, 1.55))
        ledge = sub(ledge, wdg)
    ledge.apply_translation((6.25, 0, 0))
    wheel = uni([wheel, ledge])
    _color(wheel, "fork"); wheel.metadata["name"] = "worm_wheel"
    wheel.apply_translation((wx, yt, zt))
    add(wheel, M_head, "worm_wheel.stl")
    # worm on the motor shaft (axis Y), tangent below the wheel; fixed to the neck frame (M_pan).
    # FULL-DEPTH double-D bore (the old worm had no bore at all) + a Ø6 tail stub riding the
    # neck bracket's outboard bushing post (the far end was a free cantilever).
    face_y = yt - 0.5 * P["worm_len"] - 9.5          # keep in sync with build_neck_clevis()
    yc = face_y + 3.5 + P["worm_len"] / 2            # real worm thread spans exactly +-7 (the
                                                     # old placeholder ribs overhung 1 mm/end);
                                                     # keep 0.5 off the plate front face
    if placeholder_gears:
        wm = worm(P["worm_od"] / 2, P["worm_len"], axis="y")
    else:
        # real single-start RH worm (docs/WORM.md): axis Y, OD 10.55, solid core Ø7, thread
        # span exactly +-7 about origin. The Ø7 core takes the full-depth double-D bore in
        # SOLID stock (probed: bore surface 100% inside the solid over the thread span;
        # round wall 0.915 mm, flat wall 1.88 -- thin but the D-flats carry the torque).
        wm = load_gear_stl("tilt_worm_real.stl")
    # Ø5 tail stub: bare past the thread end (y=-16, local +8) so the cradle groove band
    # (y -15.5..-13) grips ROUND stock, not thread (stage-4 D2); r2.5 keeps it under the
    # wheel-tooth sweep where it emerges
    stub = cyl(2.5, 8.0, axis="y"); stub.apply_translation((0, 8.0, 0))
    wm = uni([wm, stub])
    db = dbore_neg(P["worm_len"] + 1.2, axis="y")
    # NO extra clocking: after the motor's two rotations below (shaft +Z -> +Y, then rolled so
    # the offset points up) the shaft flats face +-X, and dbore_neg(axis="y") already cuts its
    # flats +-X. The old R(TAU/4, y) here clocked the bore flats to +-Z -- 90 deg off the
    # shaft (stage-4 defect D3: 17.4 mm3 of shaft shoulder buried in the worm core).
    db.apply_translation((0, 0.5, 0))
    wm = sub(wm, db)
    _color(wm, "motor"); wm.metadata["name"] = "tilt_worm"
    wm.apply_translation((wx, yc, wz))
    add(wm, M_pan, "tilt_worm.stl")
    # tilt motor: shaft +Z -> +Y, then ROLLED about the shaft so the 7.875 offset points UP:
    # the can hangs BELOW the worm axis (clear of the head's back-wall sweep) and the ears run
    # horizontal at the CAN axis. Gear face lands on the bracket plate's BACK face.
    mt = motor_28byj("motor_tilt")
    mt.apply_transform(R(-TAU / 4, (1, 0, 0)))       # shaft +Z -> +Y
    mt.apply_transform(R(-TAU / 4, (0, 1, 0)))       # roll: shaft offset +X -> +Z
    mt.apply_translation((wx, face_y - 2 - (P["motor_body_h"] + P["motor_gear_h"]),
                          wz - P["motor_shaft_off"]))
    add(mt, M_pan)
    # removable cartridge carrier: the motor's ears bolt to it on the bench; 4x M3 from the
    # rear bay clamp it to the bracket plate (see build_tilt_carrier)
    add(build_tilt_carrier(), M_pan, "tilt_carrier.stl")

    # (Pi 5 placeholder removed: the Pi now rides the display's OWN 58x49 back standoffs and
    # is part of the combined screen reference mesh, "Pins Out" assembly. See load_screen().)

    # pan motor: 28BYJ-48 upright in the base, CAN offset -motor_shaft_off so the D-shaft lands
    # ON the pan axis; shaft tip reaches ~2 mm below the platform top into its D-bore hub.
    mp = motor_28byj("motor_pan")
    zsh = P["base_h"] - 2 - (P["motor_body_h"] + P["motor_gear_h"] + P["motor_shaft_len"])
    mp.apply_translation((-P["motor_shaft_off"], 0, zsh))
    add(mp, np.eye(4))

    # pan bearing: captured-BB lazy-Susan lower race + ball ring (fixed frame; platform is the
    # upper race). Balls carry the head weight on a wide circle -> no wobble, quiet, cheap.
    lower_race, balls, cage = build_pan_race()
    add(lower_race, np.eye(4), "pan_race.stl")
    add(balls, np.eye(4))
    add(cage, np.eye(4), "pan_cage.stl")             # BB spacer cage (drops in with the balls)
    # uplift retention: 3 L-clips screwed to the deck, tabs over the platform's rim rebate
    add(build_pan_clips(), np.eye(4), "pan_clips.stl")

    # --- HEAD (tilt + pan): split into front bezel + back cover + rear service door ---
    bezel, back, door = build_head_parts()
    add(bezel, M_head, "head_bezel.stl")
    add(back, M_head, "head_back.stl")
    add(door, M_head, "head_door.stl")
    add(build_screen_tray(), M_head, "screen_tray.stl")  # bench-mounted module carrier

    for rail in build_head_rails():                  # orange side accent rails (design ref)
        add(rail, M_head)
    add(build_sd_plug(), M_head, "sd_plug.stl")      # microSD service-slot friction plug
    add(build_led_strip(), M_head)                   # forehead light strip (design ref)
    # twin deployable antenna masts + their geared drive (2026-07-10; PARAMS block).
    # ANT=<mm> (0..ant_travel) sets the baked extension; default = preview_ant_mm.
    # M_ant = M_head then a head-local +Z lift -- the lift happens BEFORE the head
    # pose, i.e. in head-local coordinates, so tilted heads deploy along their own up.
    ant_mm = float(os.environ.get("ANT", P["preview_ant_mm"]))
    ant_mm = max(0.0, min(P["ant_travel"], ant_mm))
    M_ant = M_head @ _T(0, 0, ant_mm)
    ant_nodes = []
    for mast in build_antennas():
        ant_nodes.append(mast.metadata["name"])
        add(mast, M_ant, f"{mast.metadata['name']}.stl")
        pose_groups["head"].append(mast.metadata["name"])   # add() saw M_ant, not M_head
    for pc in build_ant_drive():
        add(pc, M_head, "ant_bracket.stl" if pc.metadata["name"] == "ant_bracket" else None)
    for sxa, side in ((-1, "L"), (1, "R")):          # one stepper PER MAST (user:
        ma = motor_28byj(f"motor_ant_{side}")        # independently controllable):
        ma.apply_transform(R(-sxa * TAU / 4, (0, 1, 0)))   # shaft points inboard,
        ma.apply_transform(R(-sxa * TAU / 4, (1, 0, 0)))   # offset rolled to -Y,
        ma.apply_translation((sxa * 53.5,            # ears vertical
                              P["ant_motor_y"] + P["motor_shaft_off"],
                              P["ant_motor_z"]))
        add(ma, M_head)
    add(build_hatch_frame(), M_head)                 # rear orange hatch frame (design ref)
    add(build_cam_pod(), M_head)                     # raised camera eye-pod (design ref)
    if os.environ.get("ARMS") == "1":               # arms REMOVED for now (user 2026-07-07);
        for arm in build_arms():                     # ARMS=1 re-adds the placeholders. The
            add(arm, M_head)                         # real mechanism plan: docs/ARM-MECH.md

    screen = load_screen()
    screen.apply_transform(screen_pose())            # sit on the leaned front face
    screen.metadata["name"] = "screen_ref"
    add(screen, M_head)

    # camera: CM3 placeholder at the REAL stack dims, board FRONT plane on the M2 boss tips
    # (the old 12-deep box was centered 6 behind the wall and punched the bosses).
    fy = P["body_front_y"]
    lz = P["cam_lens_z"]; bz = lz - P["cam_lens_dz"]
    bf = P["cam_pier_y1"] - P["cam_pier_t"] - P["cam_boss_len"]   # board front = boss tips (20.5)
    bb = bf - P["cam_pcb_t"]                         # board back face
    pcb = box(P["cam_board_w"], P["cam_pcb_t"], P["cam_board_h"])
    pcb.apply_translation((0, bf - P["cam_pcb_t"] / 2, bz))
    conn = box(19.61, P["cam_back_d"], 5.71)         # flex connector, near the lens-end (top) edge
    conn.apply_translation((0, bb - P["cam_back_d"] / 2, bz + P["cam_board_h"] / 2 - 5.71 / 2))
    hous = box(P["cam_house_wh"], P["cam_house_d"], P["cam_house_wh"])
    hous.apply_translation((0, bf + P["cam_house_d"] / 2, lz))
    brl = cyl(P["cam_barrel_d"] / 2, P["cam_lens_tip"] - P["cam_house_d"], axis="y")
    brl.apply_translation((0, bf + (P["cam_house_d"] + P["cam_lens_tip"]) / 2, lz))
    cam = uni([pcb, conn, hous, brl]); _color(cam, "camera")
    cam.metadata["name"] = "camera_ref"
    add(cam, M_head)
    # camera rear cover: plate behind the connector envelope + 2 posts to the board back on the
    # DIAGONAL hole pair; 2x M2 self-tap through the posts into the bezel bosses (the board is
    # clamped board->boss by the same screws). Bottom edge keeps the ribbon pinch slot.
    cov_f = bb - P["cam_back_d"] - 0.3               # plate front: 0.3 clear of the connector
    cover = box(P["cam_board_w"] + 2, P["cam_cover_t"], P["cam_board_h"])  # +0 in Z: the board
    # top is 0.54 under the interior ceiling; a +2 skirt punched it
    cover.apply_translation((0, cov_f - P["cam_cover_t"] / 2, bz))
    diag = [(P["cam_hole_dx"] / 2, P["cam_hole_z_top"]),
            (-P["cam_hole_dx"] / 2, P["cam_hole_z_bot"])]
    for dx, dz in diag:
        post = cyl(P["cam_boss_od"] / 2, bb - cov_f, axis="y")
        post.apply_translation((dx, (cov_f + bb) / 2, bz + dz))
        cover = uni([cover, post])
        m2 = cyl(P["cam_m2_clear_r"], 20, axis="y")
        m2.apply_translation((dx, bb - 5, bz + dz))
        cover = sub(cover, m2)
    rib = box(P["cam_ribbon_w"], P["cam_cover_t"] + 2, P["cam_ribbon_t"])
    rib.apply_translation((0, cov_f - P["cam_cover_t"] / 2,
                           bz - (P["cam_board_h"] + 2) / 2 + 1))
    cover = sub(cover, rib)
    _color(cover, "back"); cover.metadata["name"] = "cam_cover"
    add(cover, M_head, "cam_cover.stl")

    # HOLLOW Ø5 tilt axle: clamped to the head (turns with it), rotates in the neck-cheek 695
    # bearings, driven in the middle by the worm wheel. Hollow -> Pi power wires cross on-axis.
    # SOLID Ø5 axle (review 2026-07-08: was hollow Ø2.5 "weight relief", but the D-flat
    # leaves a 0.25 wall on a tube -- the spec is now solid rod, so the model matches).
    axle = cyl(P["axle_d"] / 2, P["head_w"] + 4, axis="x")
    # D-KEY FLAT (matches the worm wheel's hub ledge): 1.0 deep (flat face z=+1.5), from
    # the +X insertion end to 15 past center, so the wheel's key ledge rides the flat as
    # the axle slides in. Clocked +Z at neutral; axle and wheel both ride M_head.
    flat = box(123.0, 8.0, 1.4)
    flat.apply_translation((46.5, 0, 1.5 + 0.7))
    axle = sub(axle, flat)
    _color(axle, "axle"); axle.metadata["name"] = "tilt_axle"
    axle.apply_translation((0, yt, zt))
    add(axle, M_head)

    out = webpath(out_name)
    scene.export(out)
    # pose sidecar for the viewer's live pan/tilt sliders: the GLB has the pose BAKED
    # into each node's vertices, so the viewer needs the baked angles + the kinematic
    # group of every posed node to re-pose them (delta rotations about the same axes).
    # Named per-model (assembly.pose.json, neutral.pose.json ...): an OUT= side build
    # must not clobber the sidecar of the GLB the viewer is actually showing. Skipped
    # for scratch outputs (leading underscore, e.g. assembly_check's _check.glb).
    if not out_name.startswith("_"):
        import json as _json
        _json.dump({
            "pan_deg": pan_deg, "tilt_deg": tilt_deg,
            "tilt_axis_y": yt, "tilt_axis_z": zt,
            "pan_stop_deg": 93.3, "tilt_stop_deg": 33.8,   # homing hard-stop limits
            "groups": pose_groups,
            "ant_nodes": ant_nodes, "ant_travel": P["ant_travel"],
            "ant_baked_mm": ant_mm,                        # viewer antenna slider
        }, open(webpath(out_name.rsplit(".", 1)[0] + ".pose.json"), "w"), indent=1)
    print(f"wrote {out}  ({len(scene.geometry)} parts)")
    if EXPORT:
        print("exported per-part STLs into stl/")
    if os.environ.get("FITS") == "1":
        if pan_deg or tilt_deg:
            print("NOTE: fit map at pan=%g tilt=%g -- cross-group numbers are pose-"
                  "dependent; `make fits` runs the canonical neutral pose" % (pan_deg, tilt_deg))
        _fit_report(fit_geo)


if __name__ == "__main__":
    build()

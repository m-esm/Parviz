"""Head parts: shell, bezel/back/door(pod), screen tray, camera pod, styling.

Split out of the original monolithic build.py (2026-07-10); see
build.py for the assembly entry point and the overall design notes.
"""
import numpy as np
import trimesh
import shapely.geometry as sg
from trimesh.creation import extrude_polygon
from trimesh.transformations import rotation_matrix as R
from params import DEG, P, TAU
import geo
from geo import (NUT, _T, _color, _orient, blind_socket, box,
    cyl, fix_pin, frustum, hex_prism, inter, nut_slot,
    rounded_box, screw_post, sub, teardrop, uni)
from screen import screen_pose
from gears import gear_disc, involute_spur


# ---------------------------------------------------------------------------
# Fastening helpers (2026-07-15 FASTENING AUDIT, docs/FASTENING_AUDIT.md)
# ---------------------------------------------------------------------------
def _nut_trap(nut_c, screw_axis, open_dir, size="M3", length=14.0):
    """Slide-in captive hex-nut trap NEGATIVE, positioned by the NUT CENTRE, with
    `length` measured from that centre out to the slot MOUTH.

    geo.nut_slot() now owns the seat correction itself (it cuts from ac/2 behind
    the screw axis so a nut pushed home centres on the bore -- see its docstring
    and the chassis_pedestal defect that motivated it), so this is just a units
    shim: nut_slot's `length` runs seat->mouth, ours runs centre->mouth.
    Keep >= 1.2 of part beyond the seat at nut_c - open_dir*ac/2.
    """
    return nut_slot(np.asarray(nut_c, float), screw_axis=screw_axis,
                    open_dir=open_dir, size=size,
                    length=length + geo.nut_ac(size) / 2.0)


def _teardrop(r, length, axis="x", up=(0, -1, 0)):
    """Self-supporting horizontal-bore cutter for the HEAD's print orientations.

    geo.teardrop() hard-codes `up="z"` -- it only covers parts printed with world +Z as
    the print-up direction (the seam-up chassis tub). Every head piece prints on another
    face: head_bezel goes FACE-DOWN and the head_back frames go FRONT-DOWN, so for both
    of them print-up is world -Y and their bed-plane bores run along world X or Z. Same
    construction as geo.teardrop (cyl + a 45deg square cap rotated about the bore axis,
    lifted r*sqrt(0.5) so its lower vertex sits on the bore centre and the roof never
    exceeds 45deg); `up` just has to be perpendicular to `axis`.
    """
    a = {"x": (1.0, 0, 0), "y": (0, 1.0, 0), "z": (0, 0, 1.0)}[axis]
    u = np.asarray(up, float); u /= np.linalg.norm(u)
    if abs(float(np.dot(np.asarray(a, float), u))) > 1e-6:
        raise ValueError("_teardrop(): up must be perpendicular to axis")
    cap = box(*{"x": (length, r, r), "y": (r, length, r), "z": (r, r, length)}[axis])
    cap.apply_transform(R(TAU / 8, a))               # 45deg about the bore axis
    cap.apply_translation(u * (r * np.sqrt(0.5)))
    return uni([cyl(r, length, axis=axis), cap])


def _yz_post(center_xz, y0, y1, wx, wz, r=2.0):
    """A rounded-box POST spanning y0..y1, footprint wx (X) x wz (Z) about center_xz.

    The bezel<->back / rim-tab bosses want PARALLEL walls around their nut slots: a
    plain cyl() boss leaves crescent webs that feather to zero thickness where the
    slot walls exit the barrel. Footprint is built in XY then rolled onto XZ.
    """
    m = rounded_box(wx, wz, abs(y1 - y0), r)
    m.apply_transform(R(TAU / 4, (1, 0, 0)))        # (x,y,z) -> (x,-z,y): extrude -> -Y
    m.apply_translation((center_xz[0], max(y0, y1), center_xz[1]))
    return m


# ---------------------------------------------------------------------------
# Printed parts (built at neutral pose, in world coords)
# ---------------------------------------------------------------------------
def _head_solid(inset=0.0):
    """Simple rounded box head: rounded vertical edges, flat top/bottom. World coords.

    inset>0 shrinks it inward (for hollowing to a uniform wall).
    """
    d = inset
    w = P["head_w"] - 2 * d
    fy, by = P["body_front_y"] - d, P["body_back_y"] + d
    r = max(P["corner_r"] - d, 1.0)
    poly = sg.box(-w / 2, by, w / 2, fy).buffer(-r, join_style=1).buffer(r, join_style=1)
    h = (P["body_z_top"] - P["body_z_bot"]) - 2 * d
    solid = extrude_polygon(poly, h)          # XY footprint (width x depth), extruded +Z
    solid.apply_translation((0, 0, P["body_z_bot"] + d))
    return solid


def build_head_shell():
    """Alexa/Echo-Show wedge shell: rounded body, leaned front holding the 7" screen."""
    zt = P["tilt_axis_z"]
    yt = P["tilt_axis_y"]
    shell = _head_solid()

    # hollow it (leave uniform walls), opening kept via the back cavity below
    inner = _head_solid(inset=P["head_wall"])
    shell = sub(shell, inner)

    # stepped screen aperture: full-size POCKET behind (module drops in) + a smaller front
    # WINDOW that pierces the face, leaving a lip that retains the glass edge.
    ov, cl = P["bezel_overlap"], P["screen_clear"]
    # STEPPED pocket, stopping BEHIND the face (face at 33 since 2026-07-11; the old
    # flush-glass face pierced here and exposed a see-through slot around the module):
    # (1) a GLASS SLAB cut at full module width, only the 2.0-thick glass band deep
    # (world y 28.3..31.1): the glass front (30.99) seats 0.11 behind the lip the
    # window cut leaves, so the aperture overlaps the glass `ov` per side. (2) the
    # BODY pocket behind steps 10.4 NARROWER (the module is only |x| <= 84.6 behind
    # the glass, measured; z 2.0 clear): the step SHELF at y 28.3 closes the 0.5 side
    # slot around the glass edge, which used to run straight into the interior -- the
    # r16 corner arc rolls the shell surface behind y 31.1 past |x| 94, so no lip can
    # cover the outermost glass edge there. Retention is still the 4 M3 factory screws
    # via the tray; the lip only locates.
    gl = box(P["screen_w"] + 2 * cl, 2.8, P["screen_h"] + 2 * cl)
    gl.apply_transform(screen_pose() @ _T(0, 11.2, 0))       # world y 28.3..31.1
    shell = sub(shell, gl)
    bk = box(173.2, 40.0, 105.4)                             # |x|<=86.6, z 98.35..203.75
    bk.apply_transform(screen_pose() @ _T(0, -9.9, -1.95))   # world y -11.4..28.6
    shell = sub(shell, bk)
    window = box(P["screen_w"] - 2 * ov, 60.0, P["screen_h"] - 2 * ov)
    window.apply_transform(screen_pose() @ _T(0, 20, 0))     # pierce the front face -> lip
    shell = sub(shell, window)
    # SIDE-REVEAL FIN CLEARANCE (user 2026-07-14, "the line in the frame where
    # the LCD sits"): the gl-ceiling x window-wall junction leaves a genuine
    # full-height boolean-fold FIN (~1.0 x 0.5 triangular section at
    # (+-93..94, y 31.1..31.6), section-verified) hanging in the side reveal --
    # the visible line beside the glass. The sides have NO lip by design (the
    # r16 corner arc rolls the surface behind y 31.1 past |x| 94), so a clean
    # per-side clearance box removes the fin and nothing else; z stops 0.5
    # short of the window's top/bottom edges where the REAL lips root.
    wz0 = P["screen_cz"] - (P["screen_h"] - 2 * ov) / 2      # window bottom edge
    wz1 = P["screen_cz"] + (P["screen_h"] - 2 * ov) / 2      # window top edge
    for sx in (-1, 1):
        fin = box(2.5, 3.4, (wz1 - 0.5) - (wz0 + 0.5))
        fin.apply_translation((sx * (92.0 + 94.5) / 2, 32.3, (wz0 + wz1) / 2))
        shell = sub(shell, fin)

    # (the old rear cable port is gone: the deep-head motor BAY below now opens the same
    # back-wall zone x +-24, z 113..147 and is the cable route out of the head)

    # Pi I/O access, re-aimed for the REAL Pi (combined Pins-Out screen mesh): the Pi rides
    # the display's own back standoffs, landscape, board plane XZ, stack world x -37.7..48.1,
    # y -7.0..+5.5, z 151..207.5. The ETH+USB short edge faces +X at x=48 -> slot through the
    # RIGHT side wall, aligned to the port depth (y -8.5..6.5) and to the upper half of the
    # port stack (z 191.5..208.5; the band z 165..191 belongs to the pivot boss). USB-C + 2x
    # HDMI exit the BOTTOM long edge (z~151) into the open interior: cables route down and out
    # the bottom-rear neck slot / cable port. Nothing exits the top (GPIO pins point -Y).
    # (Kept separate from the bottom-rear cable port below.)
    io_side = box(14.0, 15.0, 17.0)
    io_side.apply_translation((P["head_w"] / 2 - 2, -1.0, P["screen_cz"] + 22.0))
    shell = sub(shell, io_side)
    # microSD service slot through the LEFT wall on the card's eject axis (see PARAMS
    # "sd_slot_*"): the matching cut in trim_rail_L is made in build_head_rails(); the
    # printed sd_plug fills it. Box overshoots the rail face (-107.5) and pierces the
    # pocket wall (-97) so the corridor to the card (x -41.6) is open end to end.
    sy0, sy1 = P["sd_slot_y"]; sz0, sz1 = P["sd_slot_z"]
    sd = box(14.0, sy1 - sy0, sz1 - sz0)
    sd.apply_translation((-103.0, (sy0 + sy1) / 2, (sz0 + sz1) / 2))
    shell = sub(shell, sd)
    # ventilation louvres high on the back wall (Pi 5 runs hot). 3x 76-wide x 3 at
    # z 171..187 (was 4-tall/70-wide at 171..189): the rear DOOR (task #26) now carries
    # them, and its through-void tops out at z 188.2 -- 4-tall louvres reaching 189 cut
    # the door's 2 mm support lip into slivers. Shrunk to 3 tall / 6.5 pitch (top 187,
    # 1.2 inside the void) and widened to x +-38 (door plug reaches +-54.5), keeping
    # the vent area ~= 684 mm^2 and the 3 mm web over the z=168 bay lip.
    for i in range(3):
        louvre = box(76, 30.0, 3.0)
        louvre.apply_translation((0, P["body_back_y"], P["screen_cz"] + 19.5 + i * 6.5))
        shell = sub(shell, louvre)

    # bottom-rear MOTOR BAY (task #27 deep head): one slot voids the bottom wall (x +-33,
    # y -78..21) and the lower back wall (z 78..168) so the PAN-FRAME tilt drivetrain --
    # 28BYJ can+ears (|x| 21.5, y -64.3..-26.8, z 114..147.4), worm, bracket, neck cheeks
    # (|x| 26) and the column-back ULN standoffs -- clears the head across the FULL +-30
    # tilt sweep. Probe-derived envelope (sweep_req): the swept group crosses the inner
    # back-wall face (y -66) over x +-26, z up to 165.05 (deepest head-frame y -80.6, past
    # the outer face, so the wall MUST stay open here; at neutral the motor is fully
    # inside, 1.7 clear of the inner face) and crosses the bottom wall right to the rear
    # face. x +-33 gives 7.0 side clearance; top 168 gives 2.95 over the swept need.
    # This bay is also the exit route for the Pi's bottom-edge USB-C / HDMI cables and
    # keeps the neck's left-bay cable window (x -18..-6, y -30..-22, z 117..127) reachable
    # at every tilt (the nearest head material is the x=-33 bay wall).
    slot = box(66.0, 99.0, 90.0)
    slot.apply_translation((0, -28.5, 123.0))     # x +-33, y -78..21, z 78..168 (world)
    shell = sub(shell, slot)

    # EAR APERTURES (2026-07-11 v2, user: "only the tip of the microphone is supposed
    # to be out"): the gooseneck mic lives INSIDE the head (plugged into the CM108
    # adapter at the Pi; the flexible neck snakes up the rear bay), and just its foam
    # windscreen pokes through a Ø15 grommet bore in each side wall -- the Ø17 foam
    # compresses in and grips. A Ø19/Ø15 x 3 proud ring dresses the hole as the ear.
    # Above the trim rails, behind the split plane -> both land in head_back.
    for sxe in (-1, 1):
        er = sub(cyl(9.5, 3.0, axis="x"), cyl(7.5, 5.0, axis="x"))
        er.apply_translation((sxe * (P["head_w"] / 2 + 1.5), P["ear_y"], P["ear_z"]))
        shell = uni([shell, er])
        jb = cyl(7.5, 14.0, axis="x")
        jb.apply_translation((sxe * (P["head_w"] / 2 - 2.0), P["ear_y"], P["ear_z"]))
        shell = sub(shell, jb)

    # pivot hubs at the side walls, on the tilt axis (fuse through the wall, behind the bezel)
    bx = P["head_w"] / 2 - 8
    bosses = []
    for sx in (-1, 1):
        b = cyl(P["pivot_boss_r"] + 3, 12.0, axis="x")   # spans past the outer wall to fuse;
        b.apply_translation((sx * bx, yt, zt))           # short: the r13 body was clipping the
        bosses.append(b)                                 # relocated Pi (clamp tubes hold the axle)
    # internal CLAMP BOSSES at x=+-30: the axle is gripped HERE, 8 mm from the bearings (the old
    # scheme clamped only at the side walls: 75.5 mm cantilevers on a Ø5 tube). Ø7 torque tubes
    # run from the clamp zone out to the pivot bosses / side walls.
    for sx in (-1, 1):
        t = cyl(7.0, 72.0, axis="x")
        t.apply_translation((sx * 63.0, yt, zt))     # spans |x| 27..99: through the pivot boss
        bosses.append(t)                             # into the side wall
    # TILT HARD-STOP FINS (homing pass 2026-07-08; crush-harden 2026-07-16): 4 radial
    # fins on the clamp tubes (rooted r5.5 into the O14 tubes, tips r16.75), clocked
    # +-55 deg off straight-down (-Y). They meet the neck's stop posts
    # (build_neck_clevis, r 12..17 behind the axle) at +-33.8 deg tilt
    # (shapely-computed on the real rotated rectangles; the +-30 sweep poses keep a
    # 3.8 deg gap). Contact PLANES are pinned by angular thickness 4.0 + the +-55
    # clock -- DO NOT change those (or the post z-faces); growing contact AREA is
    # only along X, inside the post's x 20..32 band.
    # X span 4 -> 5.5 (band |x| 26.5..32.0): 1.375x face area vs the old |x| 27..31.
    # Target was ~25..32, but the cheek solid + O19.2 hoop end at |x|=26
    # (clevis_half 22, cheek_t 8); probing fin-only vs neck_clevis: band 26..32 is
    # boolean-clean but its inboard face lands EXACTLY on the cheek face plane, a
    # zero-gap sliding rub (see fin_cx note below), and 25..32 collides ~122 mm3.
    # So the inboard edge stops at 26.5, 0.5 running-clear of the cheek.
    # O14 clamp tube spans |x| 27..99 so |x| 27..32 is fully rooted; the inboard
    # 0.5 mm (|x| 26.5..27) is a stub off the tube end -- short enough that a
    # root web is unnecessary (and a web into |x|<26 collides). Clamp blocks sit
    # outboard at |x| 34..44 (2 mm past the fin tip). 0.5 mm 45deg edge bevels on
    # the local-z faces keep FDM corner bulge from taking first contact ahead of
    # the flat.
    # HOLD tradeoff (PARAMS worm_starts=3, 2026-07-12): the 3-start worm BACK-DRIVES
    # -- the head does NOT hold unpowered. Firmware stall-homes tilt against these
    # stops at boot (half current / half rate; see firmware/WIRING.md) and must
    # energize-hold or park at the balance point; 28BYJ stall through the 4:1 is
    # still PLA-safe at reduced home current. Software-limit travel to +-30 so the
    # stops stay homing-only surfaces.
    # Fins run 0.5 clear of the cheek face at |x|=26, clear the
    # grub-driver lines at x +-30 (fins never reach the y = yt plane) and the worm.
    fin_w = 5.5            # x width (was 4.0); post covers x 20..32; capped by cheek
    fin_cx = 29.25         # band |x| 26.5..32.0 per side (was 27..31): 0.5 RUNNING
                           # CLEARANCE to the cheek face at |x|=26 -- an inboard edge
                           # AT 26.0 is a zero-gap face-on-face rub over the whole
                           # tilt travel (rotation about X never changes x, so the
                           # coplanar faces slide on each other on a real print)
    fin_radial = 11.25
    fin_t = 4.0            # angular thickness -- pins +-33.8; do not change
    fin_root_r = 5.5
    fin_bev = 0.5          # 45deg contact-face edge bevel (FDM corner bulge)
    for sx in (-1, 1):
        for ang in (-55.0, 55.0):
            fin = box(fin_w, fin_radial, fin_t)
            # 45deg edge bevels on both local-z faces (the stall contact faces).
            # Rotated-cube cutters nibble each long edge; short radial-end edges
            # get the same treatment so the whole landing perimeter is relieved.
            if fin_bev > 0:
                for zs in (-1.0, 1.0):
                    for xs in (-1.0, 1.0):
                        ch = box(fin_bev * 2.0, fin_radial + 2.0, fin_bev * 2.0)
                        ch.apply_transform(R(45.0 * DEG, (0, 1, 0)))
                        ch.apply_translation((xs * fin_w / 2.0, 0.0,
                                              zs * fin_t / 2.0))
                        fin = sub(fin, ch)
                    for ys in (-1.0, 1.0):
                        ch = box(fin_w + 2.0, fin_bev * 2.0, fin_bev * 2.0)
                        ch.apply_transform(R(45.0 * DEG, (1, 0, 0)))
                        ch.apply_translation((0.0, ys * fin_radial / 2.0,
                                              zs * fin_t / 2.0))
                        fin = sub(fin, ch)
            fin.apply_translation((sx * fin_cx,
                                   -(fin_root_r + fin_radial / 2.0), 0.0))
            fin.apply_transform(R(ang * DEG, (1, 0, 0)))
            fin.apply_translation((0, yt, zt))
            bosses.append(fin)
    # TILT-AXLE PINCH-CLAMP BLOCKS (2026-07-15 fastening audit P0-3; full derivation of
    # the x band, the +-Y bolt axis and the rear-door driver path is in PARAMS "clamp_*").
    # One block per side engulfs the Ø14 torque tube; the slit + cross bolt are cut below,
    # AFTER the union, so nothing refills them.
    cx0, cx1 = P["clamp_x"]
    for sx in (-1, 1):
        blk = rounded_box(P["clamp_wz"], P["clamp_wy"], cx1 - cx0, 3.0)
        blk.apply_translation((0, 0, -(cx1 - cx0) / 2.0))     # centre the extrusion ...
        blk.apply_transform(R(TAU / 4, (0, 1, 0)))            # ... (x,y,z)->(z,y,-x): -> X
        blk.apply_translation((sx * (cx0 + cx1) / 2, yt, zt - 2.0))
        bosses.append(blk)
    shell = uni([shell] + bosses)
    # axle bore: SNUG Ø5.1 through the clamp bosses; far-wall bores demoted to LOOSE Ø5.3
    # supports (they locate, the x=+-30 grubs grip).
    axle_bore = cyl(2.55, P["head_w"] + 10, axis="x")
    axle_bore.apply_translation((0, yt, zt))
    shell = sub(shell, axle_bore)
    for sx in (-1, 1):
        loose = cyl(2.65, 65, axis="x")              # |x| 45..110: everything outboard is
        loose.apply_translation((sx * 77.5, yt, zt))  # loose (45, was 40: the clamp blocks
        shell = sub(shell, loose)                    # run to 44 and need the SNUG bore)
        # PINCH CLAMP (P0-3) -- replaced the Ø2.5 "M2.5 grub pilot", which was M2.5
        # CLEARANCE size and had zero thread to bite. Cut AFTER the boss union above so
        # nothing refills. Per side, in order: the SLIT (splits the block below the bore
        # into front/rear jaws, hinged over the top), the cross-bolt clearance + head
        # recess, and the captive nut trap.
        # PRINT (head_back frames go FRONT-DOWN, i.e. world -Y is print +Z): the bolt axis
        # is +-Y = print-VERTICAL, so its bore and head recess are self-supporting with no
        # teardrop (the recess literally opens at the print top). The slit is a vertical
        # open-topped gap. Only the nut slot has a roof, a plain 5.7 mm bridge.
        bx_ = sx * (cx0 + cx1) / 2
        zb0 = zt - P["clamp_wz"] / 2 - 2.0           # block bottom face (141)
        slit = box(cx1 - cx0, P["clamp_slit_t"], zt - zb0)   # z 141..153, up INTO the bore
        slit.apply_translation((bx_, yt, (zt + zb0) / 2))    # (the overlap cuts nothing new)
        shell = sub(shell, slit)
        yb0 = yt - P["clamp_wy"] / 2                 # block rear face (-26)
        clr = cyl(P["m3_clear_r"], 21.0, axis="y")   # y -31..-10 (tip room past the nut)
        clr.apply_translation((bx_, yb0 - 5.0 + 21.0 / 2, P["clamp_bolt_z"]))
        shell = sub(shell, clr)
        cb = cyl(P["clamp_head_cb_r"], P["clamp_head_cb_deep"] + 1.0, axis="y")
        cb.apply_translation((bx_, yb0 + (P["clamp_head_cb_deep"] + 1.0) / 2 - 1.0,
                              P["clamp_bolt_z"]))    # opens at the rear face, 1.0 overshoot
        shell = sub(shell, cb)
        shell = sub(shell, _nut_trap((bx_, P["clamp_nut_y"], P["clamp_bolt_z"]), "y",
                                     (0, 0, -1), length=8.0))   # mouth z 138, under the block

    # camera: CM3 recessed inside the raised forehead behind the plain 4 mm wall (no lens
    # bump: the countersunk aperture clears the full 75 deg diagonal FoV with the pupil
    # ~3 mm behind the outer face). The board mounts front-face-in on 4x short M2 bosses on
    # the ceiling-hung PIER (see PARAMS "cam_pier_*": the wall below the pocket top has
    # nothing to root on, and the display panel band y>=25.03 forbids long bosses). The AF
    # housing passes a pier cutout; the barrel crosses over the module's top edge and pokes
    # ~0.5 into the wall bore. Ribbon drops from the board bottom into the open pocket.
    fy = P["body_front_y"]
    lz = P["cam_lens_z"]                                # lens optical axis height (world Z)
    bz = lz - P["cam_lens_dz"]                          # board center Z (lens is above board center)
    py1 = P["cam_pier_y1"]; py0 = py1 - P["cam_pier_t"]  # pier front/back faces (Y)
    # pier plate: from below the bottom boss row up INTO the ceiling (fused 1 mm past the
    # interior face at body_z_top - 4)
    pz0 = bz + P["cam_hole_z_bot"] - 3.0
    pz1 = P["body_z_top"] - 3.0
    pier = box(P["cam_pier_w"], P["cam_pier_t"], pz1 - pz0)
    pier.apply_translation((0, (py0 + py1) / 2, (pz0 + pz1) / 2))
    shell = uni([shell, pier])
    # AF-housing cutout through the pier (10.8 sq + 0.6/side)
    hcut = box(P["cam_house_wh"] + 1.2, P["cam_pier_t"] + 2, P["cam_house_wh"] + 1.2)
    hcut.apply_translation((0, (py0 + py1) / 2, lz))
    shell = sub(shell, hcut)
    # Ø6.3 through-bore + 45 deg/side countersink opening to Ø8.0 at the outer face
    bore = cyl(P["cam_bore_d"] / 2, 12, axis="y"); bore.apply_translation((0, fy - 2, lz))
    shell = sub(shell, bore)
    csk_r0, csk_r1 = P["cam_bore_d"] / 2, P["cam_csk_d"] / 2 + 2.0   # overshoot 2 past the face
    csk = frustum(csk_r1, csk_r0, csk_r1 - csk_r0)      # 45 deg/side, shrinking toward +Z
    csk.apply_transform(R(TAU / 4, (1, 0, 0)))          # +Z -> -Y: small end faces INTO the wall
    csk.apply_translation((0, fy + 2.0, lz))            # Ø8.0 lands exactly on the face plane
    shell = sub(shell, csk)
    # 4 short M2 boss pads on the pier back face (2 screwed, 2 locating); blind pilots
    for sx in (-1, 1):
        for dz in (P["cam_hole_z_top"], P["cam_hole_z_bot"]):
            bo = cyl(P["cam_boss_od"] / 2, P["cam_boss_len"], axis="y")
            bo.apply_translation((sx * P["cam_hole_dx"] / 2, py0 - P["cam_boss_len"] / 2,
                                  bz + dz))
            shell = uni([shell, bo])
            # 2026-07-15 FASTENING AUDIT (item 9): M2-in-PLA is fine here (the CM3 board
            # is ~4 g and the cover carries the ribbon pinch), but the pilot had only
            # 4.0 mm of material to bite -- boss 1.0 + pier 3.0 -- and used 3.8 of it.
            # Engagement can only grow by adding material, and NOT off the boss: the boss
            # TIPS define the board's front plane, so lengthening them walks the board
            # forward and the barrel out of its wall bore. So the material goes on the
            # pier's FRONT face instead, where it runs into the face wall and fuses.
            fb = cyl(P["cam_boss_od"] / 2, P["cam_boss_front_len"], axis="y")
            fb.apply_translation((sx * P["cam_hole_dx"] / 2,
                                  py1 + P["cam_boss_front_len"] / 2, bz + dz))
            shell = uni([shell, fb])
            pl_ = P["cam_pilot_len"]
            pil = cyl(P["cam_boss_pilot_r"], pl_, axis="y")
            pil.apply_translation((sx * P["cam_hole_dx"] / 2,
                                   py0 - P["cam_boss_len"] + pl_ / 2, bz + dz))
            shell = sub(shell, pil)

    # LED-strip recess in the forehead, left of the camera (design ref): shallow slot cut
    # into the face wall; the led_strip part (build()) sits in it flush with the face.
    slot_led = box(P["led_slot_w"], P["led_slot_d"] + 1.0, P["led_slot_h"])
    slot_led.apply_translation((P["led_cx"], fy - P["led_slot_d"] / 2 + 0.5, P["led_cz"]))
    shell = sub(shell, slot_led)

    # --- COSMETIC FIXINGS in the shell walls (task #15; cut LAST so no union refills) ---
    hw2 = P["head_w"] / 2
    # trim_rail_L/R: 3x Ø3.2 x 2.5 blind pin sockets per side wall, drilled from outside
    # (the 4-wall keeps a 1.5 skin toward the interior)
    for sx in (-1, 1):
        for py, pz in P["rail_pin_pts"]:
            shell = sub(shell, blind_socket(P["fix_socket_r"], P["fix_socket_deep"],
                                            (sx, 0, 0), (sx * hw2, py, pz)))
    # ARM SHOULDER INTERFACE (see the PARAMS block for the full derivation): per side,
    # 2x M3 captive-nut pockets cut 2.8 into the wall from its interior face (x +-98.5;
    # 1.2 outer skin under the rail; nut in before the screen module) + Ø3.5 screw
    # clearance through wall + a Ø6.2 servo-lead pass on the shoulder axis.
    pocket_face = hw2 - P["head_wall"]       # wall interior face (98.5, probe-verified)
    for sx in (-1, 1):
        for sy, sz in P["shoulder_screw_yz"]:
            # hex void spans local z -deep..+1: after _orient(+z -> inboard) it cuts
            # `deep` OUTWARD from the interior face with a 1.0 inboard overshoot (open
            # into the head interior; no coincident face at the opening)
            nut = hex_prism(P["m3_nut_af"] + 0.3, P["shoulder_nut_deep"] + 1.0)
            nut.apply_translation((0, 0, (P["shoulder_nut_deep"] + 1.0) / 2
                                   - P["shoulder_nut_deep"]))
            _orient(nut, (-sx, 0, 0))
            nut.apply_translation((sx * pocket_face, sy, sz))
            shell = sub(shell, nut)
            mc = cyl(P["m3_clear_r"], 9.0, axis="x")
            mc.apply_translation((sx * (hw2 - 3.0), sy, sz))   # spans x 95..104
            shell = sub(shell, mc)
        wy, wzs = P["shoulder_wire_yz"]
        wp = cyl(P["shoulder_wire_r"], 8.0, axis="x")
        wp.apply_translation((sx * (hw2 - 2.75), wy, wzs))     # spans x 95.75..103.75
        shell = sub(shell, wp)
    # trim_hatch_frame: 4x Ø3.2 x 2.5 blind sockets in the back wall (1.5 skin)
    for px, pz in P["hatch_pin_pts"]:
        shell = sub(shell, blind_socket(P["fix_socket_r"], P["fix_socket_deep"],
                                        (0, -1, 0), (px, P["body_back_y"], pz)))
    # camera_pod: 2x Ø2.2 x 2.5 blind sockets in the face wall strip above the pocket
    for px, pz in P["campod_pin_pts"]:
        shell = sub(shell, blind_socket(P["fix_socket2_r"], P["fix_socket_deep"],
                                        (0, 1, 0), (px, fy, pz)))
    # antenna mast exits (2026-07-10, twin deployable masts -- see PARAMS TWIN DEPLOYABLE
    # ANTENNAS): per side a Ø7.0 through-bore in the top wall (mast Ø6.5 slides, 0.25/side)
    # + a Ø13 interior guide boss extending the bore to 10 long (z 216..226). A friction
    # O-ring seated in the bore mouth parks the mast against back-drive (docs/ASSEMBLY.md).
    zt_ = P["body_z_top"]
    for sxa in (-1, 1):
        gb = cyl(6.5, 7.0)
        gb.apply_translation((sxa * P["ant_x"], P["ant_y"], zt_ - P["head_wall"] - 3.0))
        shell = uni([shell, gb])
        bore = cyl(P["ant_mast_d"] / 2 + 0.25, 16.0)
        bore.apply_translation((sxa * P["ant_x"], P["ant_y"], zt_ - 6.0))
        shell = sub(shell, bore)
        slot = box(3.8, 3.2, 18.0)                   # rack corridor: the molded teeth
        slot.apply_translation((sxa * P["ant_x"], P["ant_y"] - 4.15, zt_ - 7.0))
        shell = sub(shell, slot)                     # cannot pass a round bore
    # led_strip wire pass: Ø2.5 from the recess floor (y 29.5) through the remaining
    # face wall into the interior, behind the strip's dummy PCB
    wled = cyl(P["wire_pass_r"], 6.0, axis="y")
    wled.apply_translation((P["led_cx"], fy - P["led_slot_d"] - 1.5, P["led_cz"]))
    shell = sub(shell, wled)

    _color(shell, "cradle")
    shell.metadata["name"] = "head_shell"
    return shell


def _face_normal():
    n = screen_pose()[:3, :3] @ np.array([0, 1.0, 0])
    return n / np.linalg.norm(n)


def _split_origin():
    """A point on the split plane: behind the screen back, parallel to the front face."""
    c = screen_pose()[:3, 3]
    return c - (P["screen_d"] / 2 + P["bezel_back"]) * _face_normal()


def _bezel_boss_points():
    """Perimeter fixing points, in the screen-local frame, on the split plane."""
    # side posts pulled in 5 (old +6 put them at x=+-102.5, half-proud of the wall corner)
    hw, hh = P["screen_w"] / 2 + 1, P["screen_h"] / 2 + 5
    ys = -(P["screen_d"] / 2 + P["bezel_back"])   # split plane in screen-local Y
    # bottom fixings are a PAIR at x=+-40 (a bottom-CENTER post swept into the neck column at
    # forward tilt; nothing on the neck reaches past |x|=26, so +-40 clears at every angle).
    # TOP fixings are also a PAIR at x=+-40: a top-center post's M3 shank ran through the CM3
    # camera board (x=0), and the raised ceiling needs the posts at local z=body_z_top-5-178
    # to stay fused to it. Side posts sit at 0.75*hh, above the right-wall Pi I/O slot.
    zt_post = P["body_z_top"] - 5.0 - P["screen_cz"]
    return [(-40, ys, zt_post), (40, ys, zt_post), (-40, ys, -hh), (40, ys, -hh),
            (-hw, ys, hh * 0.75), (hw, ys, hh * 0.75),
            (-hw, ys, -hh * 0.55), (hw, ys, -hh * 0.55)]


def build_head_parts():
    """Split the wedge into a FRONT bezel (holds + retains the screen, camera nub) and a
    BACK cover (pivot hubs, neck slot, Pi bay, cable port). M3 screws from the front thread
    into captive hex nuts in the back-cover bosses."""
    from trimesh.intersections import slice_mesh_plane
    full = build_head_shell()
    n, o = _face_normal(), _split_origin()
    bezel = slice_mesh_plane(full, plane_normal=n, plane_origin=o, cap=True)
    back = slice_mesh_plane(full, plane_normal=-n, plane_origin=o, cap=True)

    # bezel<->back fixing: a boss each side of the split; screw along the face normal (+Y);
    # the nut is captive in the back boss, the bezel boss is just clearance.
    # 2026-07-15 FASTENING AUDIT P0-1 -- the head's PRIMARY STRUCTURAL JOINT was
    # UNBUILDABLE: the 8 hex voids were sealed inside solid r4.3 cylinders with no
    # insertion slot (and only 0.84 of material at the hex corner even if you could get
    # a nut in). Each back boss is now a rounded-box post carrying a real SLIDE-IN TRAP
    # that opens INBOARD into the open head, plus a diagonal Ø4 dowel pair on the split
    # plane so the halves self-register while 8 blind M3x35 are driven.
    # ASSEMBLY ORDER: nuts in BEFORE the screen module / tray (the module buries every
    # side-post mouth). Lay head_back on its back, open front UP: the traps are then
    # horizontal pockets the nuts simply sit in, and every screw drives downward.
    # PRINT: head_back frames print FRONT-DOWN, so the boss axis is vertical and the M3
    # bore self-supports; the trap's roof is a 5.7 mm bridge (no teardrop needed, and a
    # teardrop cannot apply to a flat-walled hex trap anyway).
    sp = screen_pose()
    run_, web_ = P["bez_nut_boss_run"], P["bez_nut_boss_web"]
    for lp in _bezel_boss_points():
        w = (sp @ np.append(lp, 1.0))[:3]
        sxb = 1.0 if w[0] > 0 else -1.0
        if abs(w[0]) > 60.0:                             # SIDE posts ride the side wall
            o, wx, wz = (-sxb, 0.0, 0.0), run_, web_     # -> trap runs inboard
        else:                                            # |x|=40 posts ride ceiling/floor
            szb = 1.0 if w[2] > P["screen_cz"] else -1.0
            o, wx, wz = (0.0, 0.0, -szb), web_, run_     # -> trap runs into the interior
        # BACK post: clipped to the shell envelope (inter, the proven rim-tab pattern) --
        # the side-post footprint would otherwise stand 0.5 proud of the x +-102.5 wall,
        # and the top post's would stand off the z 242 crown.
        post = _yz_post((w[0], w[2]), 2.0, -13.0, wx, wz)
        back = uni([back, inter(post, _head_solid())])
        bezel = uni([bezel, screw_post(w, n, 11)])
        clr = _orient(cyl(P["m3_clear_r"], 70), n); clr.apply_translation(w)
        bezel = sub(bezel, clr.copy()); back = sub(back, clr.copy())
        back = sub(back, _nut_trap((w[0], P["bez_nut_y"], w[2]), "y", o,
                                   length=P["bez_nut_slot_len"]))

    # split-plane REGISTRATION (audit "assembly-holding gaps" #4: bezel on back had NONE).
    # Pin on the bezel (prints face-down -> the pin grows straight up, self-supporting),
    # socket in head_back. Both bosses ride a wall, see PARAMS "bez_dowel_pts".
    for dx_, dz_ in P["bez_dowel_pts"]:
        fp = (dx_, 2.0, dz_)
        bp = _orient(cyl(P["bez_dowel_boss_r"], 8.0), -n)
        bp.apply_translation((dx_, 2.0 - 4.0, dz_))      # y -6..2
        back = uni([back, inter(bp, _head_solid())])
        back = sub(back, blind_socket(P["bez_dowel_socket_r"], P["bez_dowel_deep"],
                                      (0, 1, 0), fp))
        zp = _orient(cyl(P["bez_dowel_boss_r"], 8.0), n)
        zp.apply_translation((dx_, 2.0 + 4.0, dz_))      # y 2..10
        bezel = uni([bezel, inter(zp, _head_solid())])
        bezel = uni([bezel, fix_pin(P["bez_dowel_r"], P["bez_dowel_len"],
                                    (0, -1, 0), fp)])

    # (Pi 5 standoffs removed: the Pi mounts on the display's OWN back standoffs, so it comes
    # in with the screen module. The back cover only has to CLEAR the combined stack.)
    zt = P["tilt_axis_z"]

    # screen retention: SCREEN TRAY (2026-07-08, user: "I don't like the 4 long screws").
    # The old scheme -- 4 rear standoffs with 88.5-long blind Ø7 driver channels through
    # the back wall (nasty step #1 in both reviews) -- is GONE. The module now bolts to
    # the separate `screen_tray` on the BENCH (build_screen_tray; the factory bosses still
    # open backward and a bezel boss still punches the glass, so the boss-rear-plane datum
    # at y 22.48 is unchanged, stage-4 D1), and the loaded tray drops into head_back from
    # the open front. head_back keeps only 4 short M3x10 CLEARANCE holes through the back
    # wall at the tray pillar pilots: (x = boss_x -+ 1.5 inboard, z 134/174), inside the
    # fixed-wall strip between the door outline (|x| > 56.5) and the hatch-frame opening
    # (screw heads reach |x| 66.3 max < 67) -- short, visible, normal driver.
    wall_in = P["body_back_y"] + P["head_wall"]          # inner back wall (-66, deep head)
    wpts = [(sp @ np.append(lp, 1.0))[:3] for lp in P["scr_mount_pts"]]
    for bx_ in sorted({round(w[0], 2) for w in wpts}):
        # pattern is off-center (-64.59 / +61.61): the LEFT pilot shifts 1.5 inboard to
        # keep its Ø7.2 head inside the frame opening; the RIGHT sits on the pillar axis
        # (head 58.0..65.2: 1.5 off the door outline, 1.8 off the frame)
        px_ = bx_ + 1.5 if bx_ < 0 else bx_
        for bz_ in (134.0, 174.0):
            hole = cyl(P["m3_clear_r"], 6.0, axis="y")
            hole.apply_translation((px_, P["body_back_y"] + 2.0, bz_))
            back = sub(back, hole)
            cb = cyl(3.6, 1.4, axis="y")                 # Ø7.2 head counterbore, outer face
            cb.apply_translation((px_, P["body_back_y"] + 0.6, bz_))
            back = sub(back, cb)
            # PILLAR LOCATING SEAT (2026-07-15 fastening audit P1 + "assembly-holding
            # gaps" #5): the loaded tray used to drop in located by NOTHING and get
            # screwed blind from outside while someone held the heaviest module in the
            # robot. Each pillar end now keys into this recess. It is a recess and not a
            # boss because the tray bay has zero frame material anywhere near the pillars
            # -- see PARAMS "scr_seat_deep". Cut in `back` (y < -66 -> it lands in the
            # panel) and printed as a shallow bed-face pocket that bridges at 1.0.
            sd_, sf_ = P["scr_seat_deep"], P["scr_seat_fit"]
            seat = box(P["scr_pillar"] + 2 * sf_, sd_ + 1.0, P["scr_pillar"] + 2 * sf_)
            seat.apply_translation((bx_, wall_in - sd_ + (sd_ + 1.0) / 2, bz_))
            back = sub(back, seat)

    # ant_bracket MOUNTING holes (2026-07-15 fastening audit P0-4): 4x M3x12 from OUTSIDE
    # the back wall into captive nuts in the bracket's spine bosses. The bracket carried
    # both antenna 28BYJs on a spine that was attached to the head by nothing at all.
    # z 212 is fixed wall: 2.5 above the trim_hatch_frame top (203.5), 24 above the door
    # outline (188.2) -- heads stay visible and are not buried under the glued-on frame.
    for sxa_ in (-1, 1):
        for mx_ in P["ant_mount_x"]:
            hole = cyl(P["m3_clear_r"], 6.0, axis="y")
            hole.apply_translation((sxa_ * mx_, P["body_back_y"] + 2.0, P["ant_mount_z"]))
            back = sub(back, hole)
            cbm = cyl(3.6, 1.4, axis="y")            # Ø7.2 head counterbore, outer face
            cbm.apply_translation((sxa_ * mx_, P["body_back_y"] + 0.6, P["ant_mount_z"]))
            back = sub(back, cbm)

    # --- REAR SERVICE DOOR (task #26): the 4-thick wall (y -70..-66) inside the orange
    # frame becomes a removable U-shaped panel. Through-void = outline inset door_lip
    # (2 mm fixed-wall lip all around, incl. a 2 mm ring left standing around the x +-33
    # bay); a 2-deep rebate off the OUTER face takes the door's 1.9 flange (0.1 axial +
    # 0.15 perimeter clearance), a 2.1 plug fills the void flush with the inner face.
    # The gusset webs (|x| 59.6..66.6, y -67..-27) and standoff bosses (edge |x| 57.11)
    # stay entirely on head_back: void reaches |x| 54.5, rebate |x| 56.5.
    zb0, zb1 = P["door_z"]; dlip = P["door_lip"]; dfit = P["door_fit"]
    outline = sg.box(-P["door_hx"], zb0, P["door_hx"], zb1).difference(
        sg.box(-P["door_notch_hx"], zb0 - 5.0, P["door_notch_hx"], P["door_notch_ztop"]))
    void = outline.buffer(-dlip, join_style=2)
    wall_out = P["body_back_y"]                          # outer back face (-70)

    def _xz(poly, t, y0):
        """Extrude an XZ-footprint poly (x, z) to thickness t, spanning y0-t..y0."""
        m = extrude_polygon(poly, t)
        m.apply_transform(R(TAU / 4, (1, 0, 0)))         # (x, y, z) -> (x, -z, y)
        m.apply_translation((0, y0, 0))
        return m

    back = sub(back, _xz(void, 8.0, wall_out + 7.0))         # through-void, y -71..-63
    back = sub(back, _xz(outline, 2.5, wall_out + 2.0))      # 2-deep outer rebate + overshoot
    door = uni([_xz(outline.buffer(-dfit, join_style=2), 2.0 - 0.1, wall_out + 2.0 - 0.1),
                _xz(void.buffer(-dfit, join_style=2), 2.1, wall_out + 4.0)])
    # EXTRUDED REAR POD (2026-07-10, user's red-box ref: the back of the head carries a
    # chunky stepped "backpack" bump). Replaces the old 3.4-proud 2-tier face + latch +
    # hinge cosmetics + through-relief slot, which read as a plate floating in a recessed
    # hole (and the detached tilt_shroud + rear_pack slabs, both removed). The pod IS the
    # door: three stepped tiers (x +-62/51/38, rear faces y -76/-80/-84), flat top at
    # z 169 so the louvre band above (~171..187) stays open like the ref, 45-deg top-rear
    # chamfer, 0.3-sloped bottom (helps the tilt-stall floor sweep: bottom-rear corner
    # bottoms at z~87 at the +33.8 stall, 21 over the deck). HOLLOW: the inner cavity
    # (x +-17, z 119.5..161, floor y -81.5) swallows the tilt drivetrain's swept
    # intrusion -- probe-measured x +-13.5 / y to -78.1 / z 122.4..157.8 over +-33.8 deg
    # -- so the 28BYJ hides INSIDE the pod and no relief hole shows. Roots to the U
    # flange via a 2.1-thick base slab on the old face footprint.
    face = sg.box(-P["door_hx"], zb0, P["door_hx"], zb1).buffer(
        -P["door_face_r"], join_style=1).buffer(P["door_face_r"], join_style=1)
    face = face.buffer(-dfit, join_style=2)
    # extend the head_back rebate to the FULL root footprint (the root's 0.1 inner skin
    # must not sit on un-rebated wall). x reaches 56.8 < the standoff bosses at 57.11.
    back = sub(back, _xz(face.buffer(0.3, join_style=2), 2.5, wall_out + 2.0))
    door = uni([door, _xz(face, 2.1 + 0.1, wall_out + 0.1)])     # root slab, y -72..-69.9
    XPERM = np.array([[0., 0., 1., 0.], [1., 0., 0., 0.],       # (y,z)-profile poly ...
                      [0., 1., 0., 0.], [0., 0., 0., 1.]])      # ... extruded along +X
    zpt = P["pod_top_z"]
    for xw, yr in P["pod_tiers"]:
        dpt = -(yr + 70.0)                                      # tier proudness off wall
        prof = sg.Polygon([(-71.5, zb0 + 0.1), (-71.5, zpt), (yr + 5.0, zpt),
                           (yr, zpt - 5.0), (yr, zb0 + 0.1 + 0.3 * dpt)])
        tier = extrude_polygon(prof, 2 * xw)                    # front buried 0.5 in root
        tier.apply_transform(XPERM)
        tier.apply_translation((-xw, 0, 0))
        rrc = sg.box(-xw, -115.0, xw, -60.0).buffer(-3.0, join_style=1).buffer(
            3.0, join_style=1)                                  # round vertical corners
        rrp = extrude_polygon(rrc, 120.0)
        rrp.apply_translation((0, 0, 100.0))
        door = uni([door, inter(tier, rrp)])
    chx, cfy, cz0, cz1 = P["pod_cavity"]
    cav = box(2 * chx, -60.0 - cfy, cz1 - cz0)                  # drivetrain sweep cavity,
    cav.apply_translation((0, (cfy - 60.0) / 2, (cz0 + cz1) / 2))   # open toward the bay
    door = sub(door, cav)
    for sxp in (-1, 1):                              # PRINT-SPEED lightening pockets
        lk = box(15.0, 19.0, 40.0)                   # (2026-07-10): the tier legs were
        lk.apply_translation((sxp * 27.0, -84.5, 142.0))   # solid; keep >=2 mm walls to
        door = sub(door, lk)                         # the cavity/notch/tier faces
    nhx, nzt, nfl = P["pod_notch"]                              # bottom corridor POCKET
    ntc = box(2 * nhx, -60.0 - nfl, nzt - 100.0)                # (see the PARAMS note)
    ntc.apply_translation((0, (nfl - 60.0) / 2, (100.0 + nzt) / 2))
    door = sub(door, ntc)
    for gx in (-31.5, 31.5):                                    # panel-line grooves on the
        gr = box(1.6, 1.6, 26.0)                                # core face (design ref)
        gr.apply_translation((gx, P["pod_tiers"][-1][1], 149.0))
        door = sub(door, gr)
    gr = box(2 * P["pod_tiers"][-1][0] - 12.0, 1.6, 1.6)
    gr.apply_translation((0, P["pod_tiers"][-1][1], 158.0))
    door = sub(door, gr)
    # top HOOK tabs (x +-47, 14 wide: outboard of the x +-38 louvres, inboard of the
    # z-186.8 standoff bosses at |x| 57.11): a root block inside the void + a 1.3 plate
    # lapping 3 mm up behind the fixed wall above the seam (0.15 off its inner face).
    hx, hw = P["door_hook_x"], P["door_hook_w"]
    for sx in (-1, 1):
        root = box(hw, 2.45, 2.0)
        root.apply_translation((sx * hx, -65.775, 187.0))    # y -67..-64.55, z 186..188
        # 2026-07-15 FASTENING AUDIT P2-9: plate 1.3 -> 2.0. These two hooks are the door's
        # entire top retention and they load in PEEL across the print layers. Growth is
        # FORWARD (-65.85 -> -63.85): the back face must hold its 0.15 clearance off the
        # fixed wall's inner face (-66), which is what lets the door swing shut at all.
        ht_ = P["door_hook_t"]
        plate = box(hw, ht_, 3.2 + P["door_hook_lip"])       # z 187..193.2 (1 into the
        plate.apply_translation((sx * hx, -65.85 + ht_ / 2,  # fixed wall above the seam)
                                 187.0 + (3.2 + P["door_hook_lip"]) / 2))
        door = uni([door, root, plate])                      # root so the union fuses)
        # 45deg ROOT GUSSET (audit P2-9 asks for a root fillet; no fillet primitive on the
        # trimesh path, so this is the same trick geo.teardrop uses -- a square rotated
        # 45deg about the hook axis, centred on the plate/root junction, so the exposed
        # faces leave a 45deg ramp instead of a square re-entrant corner).
        gus = box(hw, 2.2, 2.2)
        gus.apply_transform(R(TAU / 8, (1, 0, 0)))
        gus.apply_translation((sx * hx, -65.85 + ht_, 188.0))
        door = uni([door, gus])
    # louvres live in the door: same cuts build_head_shell made in the wall
    for i in range(3):
        louvre = box(76, 30.0, 3.0)
        louvre.apply_translation((0, wall_out, P["screen_cz"] + 19.5 + i * 6.5))
        door = sub(door, louvre)
    # bottom retention: SNAP TONGUES (2026-07-10, replaced the 2x M3 csk + captive-nut
    # blocks -- see the PARAMS door_snap_* note). Per leg: a corner notch clears the pod
    # mass off the tongue zone, then one vertical slit frees the leg's outer strip as
    # a cantilever tongue (root at door_snap_root_z, free at the door's bottom edge);
    # a barb at plug level, proud past the void wall (x 54.5), rides over the 2-thick
    # wall band beside the void as the door swings shut and clicks behind its inner
    # face (y -66). The barb profile carries its own ramps: 45 deg entry nose, ~50 deg
    # back ramp so a firm pull on the door bottom cams the tongue inboard and releases.
    # Tongue X-thickness ~= plug strip + flange strip (~4.8): strain at 1.2 deflection
    # over the ~29 arm is ~1%, and the flex is in-plane of the face-down print's layers.
    vo = P["door_hx"] - dlip - dfit                          # plug outer x edge (54.35)
    bz0, bz1 = P["door_snap_barb_z"]
    for sxd in (-1, 1):
        # free the tongue from the POD mass: clip the pod's lower corner over the whole
        # tongue + slit zone (x 49.9..63, up to just past the root z) so only flange +
        # plug flex; the 0.2 flange sliver lost at y -70..-69.8 is inside the rebate.
        notch = box(13.1, 36.4, 34.0)                        # y -106..-69.8: past the
        notch.apply_translation((sxd * 56.45, -87.9, 130.0)) # deepest tier that reaches
        door = sub(door, notch)                              # the tongue x-zone
        slit_x = sxd * (vo - P["door_snap_w"] - P["door_snap_slot_w"] / 2)
        slit = box(P["door_snap_slot_w"], 16.0, P["door_snap_root_z"] - 113.0)
        slit.apply_translation((slit_x, wall_out, (113.0 + P["door_snap_root_z"]) / 2))
        door = sub(door, slit)
        # CRACK-STOP (2026-07-15 fastening audit P2-10): the slit's top end WAS a square
        # corner at the tongue's root -- i.e. a stress raiser sitting exactly where the
        # cantilever's bending moment peaks, on the one feature the user opens by hand
        # every service. Terminating it in a hole wider than the slit is the standard
        # fix; it also lengthens the tongue's effective root slightly, lowering strain.
        stop = cyl(P["door_snap_stop_r"], 16.0, axis="y")
        stop.apply_translation((slit_x, wall_out, P["door_snap_root_z"]))
        door = sub(door, stop)
        # barb: (x, y) profile extruded over the z band. Root slab dips to y -66.8 so it
        # fuses into the plug strip; everything proud of the void wall (x > 54.35) stays
        # y >= -65.85 (0.15 behind the wall inner face -66 = the catch, nothing to add
        # on head_back). Entry nose 45 deg, catch/release ramp 1.2 over 1.0 (~50 deg).
        bt = P["door_snap_barb"]
        prof = sg.Polygon([(sxd * (vo - 1.2), -66.8), (sxd * vo, -66.8),
                           (sxd * vo, -65.85), (sxd * (vo + bt), -64.85),
                           (sxd * (vo + bt), -63.9), (sxd * vo, -62.7),
                           (sxd * (vo - 1.2), -62.7)])
        barb = extrude_polygon(prof, bz1 - bz0)              # (x, y) footprint -> +Z
        barb.apply_translation((0, 0, bz0))
        door = uni([door, barb])

    # ---- PRINT-SPEED SPLITS (2026-07-10, user: break the biggest prints apart; the
    # L/R halves alone still printed open-front-down with the WHOLE back wall as a
    # supported ceiling, so head_back is now FOUR pieces): per side a flat BACK PANEL
    # (the 4 mm wall slab, y < -66: door rebate/void, snap catch band, tray screw
    # holes -- prints lying flat, outer face up, near-zero support; the gusset webs
    # that hang off the wall ride it as upstanding fins) + a WALL FRAME (side/top/
    # bottom walls, pivot hubs, antenna guide bosses -- prints front-face-down with
    # NO ceiling). Panel-to-frame: 6x M3 axis-Y from the back (counterbored in the
    # panel, thread-form pilots in frame rim tabs: side walls z 120/190, bottom wall
    # x +-45). Seams are STAGGERED (back pieces at x=0, bezel at x=+22) so the
    # assembled shell interlocks like brickwork; the hatch frame, door, and bezel
    # screws all bridge.
    from trimesh.intersections import slice_mesh_plane

    # frame rim tabs + the panel screw drills (cut before slicing: each piece keeps
    # its share -- clearance + counterbore land in the wall slab, pilots in the tabs)
    wall_if = P["body_back_y"] + P["head_wall"]      # -66
    # 2026-07-15 FASTENING AUDIT (P1 + P2-8): these 6 screws are the panel's SOLE
    # retention and they were Ø2.5 self-tap pilots through 9-wide tabs that the corner
    # curve clips to ~3.2 ligaments. Now M3 through into a CAPTIVE NUT in a 12-wide tab
    # centred on the screw axis (the old +-2 offset would leave 1.15 of inboard web once
    # the slot is cut). Tabs still clip into the corner mass via inter(): at y -66 the
    # side walls are all corner curve, so the tabs bite the thick corner itself.
    tab_pts = [(-91.0, 120.0), (91.0, 120.0), (-91.0, 190.0), (91.0, 190.0),
               (-45.0, 96.0), (45.0, 96.0)]
    tbx, tby, tbz = P["rim_tab"]
    for tx, tz in tab_pts:
        tab = box(tbx, tby, tbz)
        tab.apply_translation((tx, wall_if + tby / 2, tz))
        back = uni([back, inter(tab, _head_solid())])
    for tx, tz in tab_pts:
        # ONE M3 clearance line, panel outer face THROUGH the tab (no self-tap left, and a
        # through-bore means an over-long screw runs out into the head instead of jamming
        # on undrilled tab -- probed: M3x12 into a blind bore fouled by 10.4 mm^3). Spec
        # M3x10: head bears on the panel cb floor (y -68.3), tip lands 1.3 past the nut.
        clr = cyl(P["m3_clear_r"], 15.0, axis="y")
        clr.apply_translation((tx, -63.0, tz)); back = sub(back, clr)
        cbp = cyl(3.2, 1.8, axis="y")            # Ø6.4 head cb; leaves a 2.3 panel
        cbp.apply_translation((tx, P["body_back_y"] + 0.8, tz))   # ligament under the head
        back = sub(back, cbp)
        # nut trap runs +Z so the nut is gravity-seated with the head upright; the mouth
        # exits the tab's top face into the open head. Nuts go in BEFORE the panel closes.
        back = sub(back, _nut_trap((tx, P["rim_tab_nut_y"], tz), "y", (0, 0, 1),
                                   length=9.0))

    # head_back halves join (frame side): under-the-top-wall flange, 2x M3 axis X.
    # Center tracks the ceiling (body_z_top - 7.5: 7-tall box fusing 1 into the top
    # wall). At the 2026-07-11 raised top (242) it spans z 231..238 -- clear of the
    # antenna G3 tips (z <= 216, y -15.3) and behind the cam_cover (y >= 13.9).
    zfl = P["body_z_top"] - 7.5
    fl1 = box(28.0, 21.0, 7.0)
    fl1.apply_translation((0, -2.5, zfl))            # y -13..8
    back = uni([back, fl1])
    # 2026-07-15 FASTENING AUDIT: Ø2.5 self-tap -> M3 into a captive nut, + a Ø4 dowel at
    # the seam (audit "assembly-holding gaps" #3: the two frames had NOTHING registering
    # them to each other -- only the panels' tongue). Screws moved (-9, 4.5) -> (-8, 3.5)
    # so the 5.7 nut slot keeps >= 1.65 of flange either side of it.
    # The trap runs -Z, out of the flange's underside: that is FORCED, because the seat has
    # to be the CEILING. The flange's own top (z 238) is fused into the z 238..242 top wall,
    # giving 4.325 above the seat; running the slot up instead would hole the head's crown.
    # Nut in, then screw, with the frames laid on their backs (audit P3: the nut can drop
    # out of a downward mouth before the screw starts).
    for fy_ in P["flange_screw_y"]:
        scr = _teardrop(P["m3_clear_r"], 15.0, axis="x", up=(0, -1, 0))
        scr.apply_translation((7.0, fy_, zfl)); back = sub(back, scr)
        cbx = _teardrop(3.4, 4.0, axis="x", up=(0, -1, 0))
        cbx.apply_translation((12.5, fy_, zfl)); back = sub(back, cbx)
        thr = _teardrop(P["m3_clear_r"], 11.0, axis="x", up=(0, -1, 0))
        thr.apply_translation((-5.5, fy_, zfl)); back = sub(back, thr)   # x -11..0
        back = sub(back, _nut_trap((P["flange_nut_x"], fy_, zfl), "x", (0, 0, -1),
                                   length=6.0))
    dwl = cyl(P["bez_dowel_socket_r"], 14.0, axis="x")   # Ø4 dowel across the frame seam
    dwl.apply_translation((0, P["flange_dowel_y"], zfl)); back = sub(back, dwl)

    # panel / frame split at the wall inner face; recover wall-hung floaters (the
    # gusset webs) into the panel so nothing is left floating in the frame
    panel = slice_mesh_plane(back, plane_normal=(0, -1, 0),
                             plane_origin=(0, wall_if, 0), cap=True)
    frame_raw = slice_mesh_plane(back, plane_normal=(0, 1, 0),
                                 plane_origin=(0, wall_if, 0), cap=True)
    bodies = sorted(frame_raw.split(only_watertight=False), key=lambda b: -b.volume)
    # A fully-enclosed void (the flange dowel bore) splits out as its own component
    # with INWARD normals = NEGATIVE volume. It is neither the frame nor a floater,
    # so the old `bodies[0]` + `volume > 1.0` sort dropped it on the floor and the
    # hole closed. Carry cavities back onto the frame by CONCATENATION -- uni()
    # would fill them straight back in. (2026-07-16; same class as chassis
    # _despeck's abs(volume), which un-drilled the y=26 seam dowels.)
    cavities = [b for b in bodies if b.volume < 0.0]
    solids = [b for b in bodies if b.volume >= 0.0]
    frame = (trimesh.util.concatenate([solids[0]] + cavities) if cavities
             else solids[0])
    floaters = [b for b in solids[1:] if b.volume > 1.0]
    assert len(floaters) <= 6, "unexpected floating bodies in head_back frame"
    if floaters:
        panel = uni([panel] + floaters)

    # PANEL<->FRAME REBATE (audit "assembly-holding gaps" #2: the panel was a flat slab on
    # a flat rim, located by nothing while 6 blind M3 went in). Per tab: a shoulder standing
    # proud of the rim face that the panel drops onto. Added AFTER the y=-66 split because
    # the shoulder straddles it -- the pad belongs to the frame, the pocket to the panel.
    # See PARAMS "rim_pad" for why this is per-tab and not a perimeter tongue.
    pdx, pdy, pdz = P["rim_pad"]
    pf = P["rim_pad_fit"]
    for tx, tz in tab_pts:
        pad = box(pdx, pdy, pdz)
        pad.apply_translation((tx, wall_if - pdy / 2, tz + P["rim_pad_dz"]))
        frame = uni([frame, pad])
        pkt = box(pdx + 2 * pf, pdy + pf, pdz + 2 * pf)
        pkt.apply_translation((tx, wall_if - (pdy + pf) / 2, tz + P["rim_pad_dz"]))
        panel = sub(panel, pkt)

    frame_l = slice_mesh_plane(frame, plane_normal=(-1, 0, 0), plane_origin=(0, 0, 0), cap=True)
    frame_r = slice_mesh_plane(frame, plane_normal=(1, 0, 0), plane_origin=(0, 0, 0), cap=True)
    panel_l = slice_mesh_plane(panel, plane_normal=(-1, 0, 0), plane_origin=(0, 0, 0), cap=True)
    panel_r = slice_mesh_plane(panel, plane_normal=(1, 0, 0), plane_origin=(0, 0, 0), cap=True)
    tng = box(4.0, 2.0, 24.0)
    tng.apply_translation((0, -68.0, 206.0))         # panel seam tongue on R ...
    panel_r = uni([panel_r, inter(tng, _head_solid())])
    tngf = box(4.3, 2.3, 24.3)
    tngf.apply_translation((-0.075, -68.0, 206.0))   # ... 0.15-fit groove in L
    panel_l = sub(panel_l, tngf)

    # head_bezel at x=+22 (clear of the camera bosses |x|<=14, the +-40 perimeter
    # posts, and the led_slot starting at x 24): flange pads behind the forehead and
    # chin face strips, 1x M3 (axis X) + 1x Ø4 dowel each.
    for pz_, pdz in ((215.0, 8.0), (92.0, 5.0)):
        # 2026-07-15 FASTENING AUDIT: the CHIN pad grows y 18..26 -> 18..30 so it buries
        # 1.0 into the face wall (29..33) and becomes a gusset off the face instead of a
        # block on a stub -- the same "floating pad" class of defect the 2026-07-14 pass
        # found on the forehead side. It also buys the depth the seam needs: an 8x10 pad
        # CANNOT hold both a Ø4.1 dowel and an M3 with 1.2 ligaments and a 1.2 wall
        # between them (that needs 11.2 mm in some direction; it had 8 and 10). With
        # y 18..30 the two features separate in Y at 22 / 27 instead of fighting in Z.
        # The FOREHEAD pad cannot do the same: the glass slab void (y 28.3..31.1) runs up
        # to z 208.9, straight through where its +Y growth would go -- it keeps the pad +
        # ext, with the ext thickened 3.2 -> 4.0 (audit P2-11).
        pdy = P["bez_seam_pad_dy"] if pz_ < 100 else 8.0
        pad = box(21.0, pdy, 2 * pdz)
        pad.apply_translation((25.0, 18.0 + pdy / 2, pz_))    # x 14.5..35.5 (0.5 off the
        bezel = uni([bezel, pad])                             # camera bosses)
        if pz_ > 100:
            # FUSE the forehead pad to the face (user 2026-07-14: "long hanging
            # thread in the LCD frame" = this pad FLOATING loose in bezel_R). The
            # 2026-07-11 face-thickening pass (body_front_y 31 -> 33) moved the
            # face's interior surface from y ~26 to ~28.4 and orphaned the pad --
            # the x=22 seam then severed its only tie on the R side, leaving the
            # seam screw threading into a detached block. Extension y 26..29.2
            # bridges pad -> face, z-clipped 209.4..223: above the glass band
            # (pocket top 208.9, so it can never press the LCD) and 0.5 under
            # the led_slot floor (223.5). The chin pad (z 92) is still fused.
            ext = box(21.0, P["bez_ext_t"], 223.0 - 209.4)     # 3.2 -> 4.0 (audit P2-11):
            ext.apply_translation((25.0, 26.0 + P["bez_ext_t"] / 2,   # y 26..30, so it
                                   (209.4 + 223.0) / 2))             # buries 1.0 into the
            bezel = uni([bezel, ext])                                # face wall (29..33)
        # M3 + captive nut (was a Ø2.5 self-tap into the same 1.2-class plastic). The trap
        # opens -Y = INTO the head interior, which is also print-UP for the face-down bezel:
        # the nut drops in and rests on its seat while the two halves lie on the bench.
        scr = _teardrop(P["m3_clear_r"], 14.0, axis="x", up=(0, -1, 0))
        scr.apply_translation((28.0, 22.0, pz_)); bezel = sub(bezel, scr)
        cbx = _teardrop(3.4, 4.0, axis="x", up=(0, -1, 0))
        cbx.apply_translation((33.6, 22.0, pz_)); bezel = sub(bezel, cbx)
        thr = _teardrop(P["m3_clear_r"], 9.0, axis="x", up=(0, -1, 0))
        thr.apply_translation((16.5, 22.0, pz_)); bezel = sub(bezel, thr)   # x 12..21
        bezel = sub(bezel, _nut_trap((P["bez_seam_nut_x"], 22.0, pz_), "x", (0, -1, 0),
                                     length=8.0))
        # Ø4 dowels KEPT (audit). The CHIN one moves off its 0.55 ligament: it used to sit
        # 2.6 from the pad's z edge, i.e. 0.55 of plastic beyond the bore. On the deepened
        # chin pad it separates from the screw in Y instead (22 -> 27, a 1.2 wall between
        # them) and now has the whole face wall behind it.
        dwl = cyl(P["bez_dowel_socket_r"], 15.0, axis="x")
        if pz_ > 100:
            dwl.apply_translation((22.0, 22.0, pz_ + pdz - 2.6))
        else:
            dwl.apply_translation((22.0, P["bez_chin_dowel_y"], pz_))
        bezel = sub(bezel, dwl)
    bez_l = slice_mesh_plane(bezel, plane_normal=(-1, 0, 0), plane_origin=(22.0, 0, 0), cap=True)
    bez_r = slice_mesh_plane(bezel, plane_normal=(1, 0, 0), plane_origin=(22.0, 0, 0), cap=True)

    _color(bez_l, "cradle"); bez_l.metadata["name"] = "head_bezel_L"
    _color(bez_r, "cradle"); bez_r.metadata["name"] = "head_bezel_R"
    for m_, nm in ((frame_l, "head_back_frame_L"), (frame_r, "head_back_frame_R"),
                   (panel_l, "head_back_panel_L"), (panel_r, "head_back_panel_R")):
        _color(m_, "back"); m_.metadata["name"] = nm
    _color(door, "back"); door.metadata["name"] = "head_door"
    return bez_l, bez_r, frame_l, frame_r, panel_l, panel_r, door


def build_screen_tray():
    """SCREEN TRAY (2026-07-08, user: "I don't like the 4 long screws"). The screen+Pi
    module bolts to THIS tray on the bench -- 4x M3x10 pan heads straight into the
    display's factory bosses with unlimited driver access -- then the loaded tray drops
    into head_back from the open front and 4x M3x10 drive from OUTSIDE the back wall
    into the pillar-end pilots. Replaces the 4 rear standoffs and their 88.5 mm blind
    Ø7 driver channels (nasty step #1 in both reviews); the module also becomes a
    bench-testable unit (power the Pi on the desk before it enters the head).

    Geometry: per side, a 12 x 4 vertical PLATE whose front face lands on the display
    boss REAR plane (y 22.48 -- same stage-4 D1 datum as the old standoffs; between
    bosses the back-pan sits at 25.03, so the plate has 2.5 air except at the boss
    rims) carrying the two M3 clearance bores on the factory 126.2 x 65.65 pattern,
    plus one 8 x 8 PILLAR per foot pair at z 134 and 174 running back to the inner
    wall. The pillars are z-OFFSET from the bore axes (bench driver line stays open)
    and z-clear of the Ø14 clamp tubes (146..160) so insertion needs no slots. Wall
    pilots sit 1.5 inboard of the pillar axis so the outside screw heads stay inside
    the hatch-frame opening (|x| < 67) and outside the door outline (|x| > 56.5).
    Prints on its side (plate face down), pillars horizontal."""
    sp = screen_pose()
    wall_in = P["body_back_y"] + P["head_wall"]          # inner back wall (-66)
    wpts = [(sp @ np.append(lp, 1.0))[:3] for lp in P["scr_mount_pts"]]
    face = wpts[0][1] - P["scr_boss_lip"] - P["scr_seat_clear"]   # boss rear plane (22.48)
    parts, cuts = [], []
    for bx_ in sorted({round(w[0], 2) for w in wpts}):
        px_ = bx_ + 1.5 if bx_ < 0 else bx_              # pilot x: MUST match head_back's
        zs = sorted(w[2] for w in wpts if round(w[0], 2) == bx_)  # holes (121.15, 186.8)
        plate = box(12.0, 4.0, 83.8)                     # z 112.2..196: reaches the spine
        plate.apply_translation((bx_, face - 2.0, 154.1))
        parts.append(plate)
        for bz_ in zs:                                   # M3 clearance to the factory boss
            c = cyl(P["scr_m3_clear_r"], 8.0, axis="y")
            c.apply_translation((bx_, face - 2.0, bz_))
            cuts.append(c)
        # 2026-07-15 FASTENING AUDIT P1: the pillars are 8 -> 10 sq and their Ø2.5
        # self-tap pilots become M3 + CAPTIVE NUT. An 8 sq pillar leaves only 1.15 of web
        # beside a 5.7 nut slot; 10 gives 2.15 and z 134/174 +-5 still clears the Ø14
        # clamp tubes (146..160). Each pillar end now runs `scr_seat_deep` INTO a locating
        # recess in the back panel, so the loaded module self-holds instead of being held
        # by hand while 4 screws go in blind from outside.
        pw_ = P["scr_pillar"]
        p_end = wall_in - P["scr_seat_deep"] + 0.05      # 0.05 seat clearance in Y
        for bz_ in (134.0, 174.0):
            pl = box(pw_, (face - 3.5) - p_end, pw_)
            pl.apply_translation((bx_, (face - 3.5 + p_end) / 2, bz_))
            parts.append(pl)
            thr = cyl(P["scr_m3_clear_r"], 11.0, axis="y")    # M3 through, y -67..-56
            thr.apply_translation((px_, -61.5, bz_))
            cuts.append(thr)
            # nut slot opens INBOARD (its mouth clears the pillar into the open bay); the
            # seat is the outboard side, which keeps >= 1.825 beyond the hex corner.
            cuts.append(_nut_trap((px_, P["scr_pillar_nut_y"], bz_), "y",
                                  (-np.sign(bx_), 0, 0), length=8.0))
    # SPINE tying the two rails into one part (bench handling): z 190.7..195.7, the
    # 6-mm window between the display's mid back-pan face (y 22.5 plane, tops at z 190
    # -- the spine face at 22.48 would only have 0.02 air inside its z-range) and the
    # bezel's camera pier / CM3 envelope (both start at z 196.6).
    spine = box(131.0, 4.0, 5.0)
    spine.apply_translation((-1.49, face - 2.0, 193.2))
    parts.append(spine)
    tray = uni(parts)
    for c in cuts:
        tray = sub(tray, c)
    _color(tray, "back")
    tray.metadata["name"] = "screen_tray"
    return tray


def build_head_rails():
    """Orange side accent rails (design-ref front.jpg): vertical rounded pads standing proud
    of the head side walls' FLAT band. FIXING: glue + 3x Ø3 locating pins on the inner face
    into blind wall sockets (PARAMS rail_pin_pts), plus 2x Ø3.5 clearance holes for the arm
    shoulder M3x10s (they clamp the rail as a bonus; arms off = same screws + a blank).
    The Ø6.2 shoulder wire pass stops at the wall face BEHIND the rail: v1's visible face
    stays clean, an option-C arm retrofit reprints the rail with the hole."""
    rails = []
    for sx, nm in ((-1, "trim_rail_L"), (1, "trim_rail_R")):
        r = rounded_box(P["rail_h"], P["rail_d"], P["rail_t"], 8.0)   # X=h, Y=d, extrude Z=t
        r.apply_transform(R(TAU / 4, (0, 1, 0)))     # footprint height -> Z, thickness -> +X
        x = P["head_w"] / 2 if sx > 0 else -(P["head_w"] / 2 + P["rail_t"])
        r.apply_translation((x, 0, P["rail_cz"]))    # thickness spans wall..wall+rail_t
        face_x = sx * P["head_w"] / 2                # rail inner face = wall outer face
        pins = [r]
        for py, pz in P["rail_pin_pts"]:
            pins.append(fix_pin(P["fix_pin_r"], P["fix_pin_len"], (-sx, 0, 0),
                                (face_x, py, pz)))
        r = uni(pins)
        for sy, sz in P["shoulder_screw_yz"]:        # M3 clearance for the shoulder screws
            mc = cyl(P["m3_clear_r"], P["rail_t"] + 2.0, axis="x")
            mc.apply_translation((sx * (P["head_w"] / 2 + P["rail_t"] / 2), sy, sz))
            r = sub(r, mc)
        if sx < 0:                                   # microSD service slot continues through
            sy0, sy1 = P["sd_slot_y"]                # the LEFT rail (same box as the wall cut
            sz0, sz1 = P["sd_slot_z"]                # in build_head_shell)
            sd = box(14.0, sy1 - sy0, sz1 - sz0)
            sd.apply_translation((-103.0, (sy0 + sy1) / 2, (sz0 + sz1) / 2))
            r = sub(r, sd)
        _color(r, "accent"); r.metadata["name"] = nm
        rails.append(r)
    return rails


def build_sd_plug():
    """Friction plug for the microSD service slot (left wall + trim_rail_L). Body fills the
    slot at sd_plug_fit per side; a 1.5-proud face plate on the rail face is the grab tab.
    Pull the plug, sight straight down the eject axis, reach the card with straight forceps.
    Prints plate-down, no supports."""
    (y0, y1), (z0, z1) = P["sd_slot_y"], P["sd_slot_z"]
    fit = P["sd_plug_fit"]
    rail_out = -(P["head_w"] / 2 + P["rail_t"])          # left rail outer face (-107.5)
    # body reaches 0.7 INTO the plate so they fuse (printability review: the first cut left
    # a 0.1 air gap and the STL split into two loose bodies). The y-min face gets +0.4 extra
    # clearance: printed face-down, the slot's y=7.4 face is a 16 mm unsupported bridge in
    # the bezel and sags into a 0.15 fit.
    body = box(9.6, (y1 - y0) - 2 * fit - 0.4, (z1 - z0) - 2 * fit)
    body.apply_translation((rail_out - 0.7 + 4.8, (y0 + y1) / 2 + 0.2, (z0 + z1) / 2))
    plate = box(1.5, (y1 - y0) + 1.6, (z1 - z0) + 3.0)   # overlaps the slot 0.8 / 1.5 per side
    plate.apply_translation((rail_out - 0.75, (y0 + y1) / 2, (z0 + z1) / 2))
    plug = uni([body, plate])
    _color(plug, "accent"); plug.metadata["name"] = "sd_plug"
    return plug


def build_led_strip():
    """WS2812-stick placeholder in the forehead recess (design-ref front.jpg: a row of
    discrete LEDs left of the camera). Thin base board in the recess + 8 round emitters
    poking 0.3 proud of the face. Wiring drops behind the wall at the print pass."""
    fy = P["body_front_y"]
    base = box(P["led_slot_w"] - 1.0, 1.2, P["led_slot_h"] - 1.0)
    # base 1.2 (was 0.8 = four fragile layers, PRINTABILITY 6): back stays on the recess
    # floor (fy - 1.5), so the dots (unmoved) still poke exactly 0.3 proud of the face.
    base.apply_translation((P["led_cx"], fy - P["led_slot_d"] + 0.6, P["led_cz"]))
    dots = [base]
    for i in range(8):
        d = cyl(1.2, P["led_slot_d"] + 0.3, axis="y", sections=24)
        d.apply_translation((P["led_cx"] - 16.1 + i * 4.6,
                             fy - (P["led_slot_d"] - 0.3) / 2, P["led_cz"]))
        dots.append(d)
    strip = uni(dots)
    _color(strip, "led"); strip.metadata["name"] = "led_strip"
    return strip


def build_antennas():
    """TWIN DEPLOYABLE MASTS (2026-07-10; see the PARAMS block for the mechanism math).
    Per side: a Ø6.5 shaft with an m0.8 rack molded along its inboard face (-Y, toward
    the pinion), a knurled Ø11 tip cap outside the head. Built RETRACTED; build() lifts
    both by the ANT preview extension. Print mast-vertical, rack toward the camera."""
    out = []
    z0, z1 = P["ant_mast_z"]
    pitch = np.pi * P["ant_gear_m"]                  # rack tooth pitch (2.513)
    for sxa, side in ((-1, "L"), (1, "R")):
        ax_ = sxa * P["ant_x"]
        shaft = cyl(P["ant_mast_d"] / 2, z1 - z0)
        shaft.apply_translation((0, 0, (z0 + z1) / 2))
        rack_spine = box(3.0, 0.9, P["ant_rack_top"] - (z0 + 2.0))
        rack_spine.apply_translation((0, -2.75,
                                      (P["ant_rack_top"] + z0 + 2.0) / 2))
        teeth = [rack_spine]
        zt_ = z0 + 3.0
        # Full-depth 20-degree rack teeth.  The old rectangular bars could not roll
        # through an involute pinion: their vertical faces collided at entry/exit and
        # made the exported mast a visual prop.  Root is buried 0.30 into the Ø6.5 mast;
        # pitch line is one module out and the tip another module out.
        half_pitch_tooth = (np.pi * P["ant_gear_m"] / 4.0
                            - 0.20 / 4.0)
        root_half = half_pitch_tooth + 1.25 * P["ant_gear_m"] * np.tan(np.radians(20))
        tip_half = max(0.25, half_pitch_tooth - P["ant_gear_m"] * np.tan(np.radians(20)))
        while zt_ < P["ant_rack_top"]:
            prof = sg.Polygon([(-2.95, zt_ - root_half),
                               (-2.95, zt_ + root_half),
                               (-4.75, zt_ + tip_half),
                               (-4.75, zt_ - tip_half)])
            t = extrude_polygon(prof, 3.0)           # (Y,Z) footprint temporarily in XY
            yz_to_xyz = np.array([[0, 0, 1, -1.5],  # (u=Y,v=Z,w=extrusion)
                                  [1, 0, 0,  0.0],  # -> (X=w-1.5,Y=u,Z=v)
                                  [0, 1, 0,  0.0],
                                  [0, 0, 0,  1.0]])
            t.apply_transform(yz_to_xyz)
            teeth.append(t)
            zt_ += pitch
        cap = cyl(P["ant_tip_d"] / 2, P["ant_tip_h"])
        cap.apply_translation((0, 0, z1 + P["ant_tip_h"] / 2))
        dome = trimesh.creation.icosphere(subdivisions=2, radius=P["ant_tip_d"] / 2)
        dome.apply_translation((0, 0, z1 + P["ant_tip_h"]))
        mast = uni([shaft, cap, dome] + teeth)
        for gz in (z1 + 3.5, z1 + 7.0, z1 + 10.5):   # knurl-read ring grooves on the cap
            gr = trimesh.creation.torus(major_radius=P["ant_tip_d"] / 2, minor_radius=0.6)
            gr.apply_translation((0, 0, gz))
            mast = sub(mast, gr)
        mast.apply_translation((ax_, P["ant_y"], 0))
        _color(mast, "antenna"); mast.metadata["name"] = f"antenna_{side}"
        out.append(mast)
    return out


def build_ant_drive():
    """Antenna drive trains, one INDEPENDENT mirrored set per side (see PARAMS): each
    28BYJ (body |x| 25.7..44.5 since the 2026-07-16 phantom-tier fix; the shaft-base
    plane 25.7 and every gear are unmoved) gears up 30T:12T twice (planes |x| 22/14) to a Ø4
    half-shaft (|x| 6..88) whose 27T pinion meshes its mast's rack. Returns
    four printable pieces per side: motor gear, compound idler, idler axle, and the
    output half-shaft/pinion.  All teeth are full-depth involutes; the motor gear has a
    double-D socket and the two rotating bracket journals have 0.15 mm radial clearance."""
    m_ = P["ant_gear_m"]
    my_, mz_ = P["ant_motor_y"], P["ant_motor_z"]
    iy_, iz_ = P["ant_idler_y"], P["ant_idler_z"]
    cy_, cz_ = P["ant_cross_y"], P["ant_cross_z"]
    x1_, x2_ = P["ant_gear_x"]
    out = []
    wall_in = P["body_back_y"] + P["head_wall"]      # -66
    br = [box(164.0, 2.0, 12.0)]                     # shared wall spine x -82..82
    br[0].apply_translation((0, wall_in + 1.0, 212.0))
    for sxa, side in ((-1, "L"), (1, "R")):
        # G1: keyed directly to the 28BYJ output shaft.  The extra hub gives the
        # socket 7 mm engagement rather than relying on a 5 mm gear face alone.
        motor_g = involute_spur(P["ant_gear_big_t"], m_, 5.0, axis="x")
        hub = cyl(4.0, 7.0, axis="x")
        motor_g = sub(uni([motor_g, hub]), geo.dbore_neg(9.0, axis="x", clear=0.12))
        motor_g.apply_translation((sxa * x1_, my_, mz_))
        _color(motor_g, "motor"); motor_g.metadata["name"] = f"ant_motor_gear_{side}"
        out.append(motor_g)

        # G2+G3: a compound idler rotating on a removable Ø3.9 printed axle.  A hub
        # bridges the two gear planes, so the exported object is one load-bearing body.
        g2 = involute_spur(P["ant_gear_small_t"], m_, 5.0, axis="x", bore_d=4.30)
        g2.apply_translation((sxa * x1_, iy_, iz_))
        g3 = involute_spur(P["ant_gear_big_t"], m_, 5.0, axis="x", bore_d=4.30)
        g3.apply_translation((sxa * x2_, iy_, iz_))
        bridge = cyl(3.2, abs(x1_ - x2_) + 5.0, axis="x")
        bridge = sub(bridge, cyl(2.15, abs(x1_ - x2_) + 7.0, axis="x"))
        bridge.apply_translation((sxa * (x1_ + x2_) / 2, iy_, iz_))
        idler = uni([g2, g3, bridge])
        # Tooth phases were solved against both adjacent fixed-centre gears with an
        # exact manifold intersection sweep (3-degree coarse, 1-degree confirmation).
        idler.apply_transform(R(np.radians(27.0), (1, 0, 0),
                                  point=(sxa * 16.5, iy_, iz_)))
        _color(idler, "motor"); idler.metadata["name"] = f"ant_idler_gear_{side}"
        out.append(idler)
        axle = cyl(1.95, 17.0, axis="x")
        axle.apply_translation((sxa * 16.5, iy_, iz_))
        _color(axle, "axle"); axle.metadata["name"] = f"ant_idler_axle_{side}"
        out.append(axle)

        # G4, cross-shaft and rack pinion are fused into one torque path.  The Ø3.9
        # journal runs in the bracket's Ø4.2 bores (0.15 radial clearance).
        g4 = involute_spur(P["ant_gear_small_t"], m_, 5.0, axis="x")
        g4.apply_translation((sxa * x2_, cy_, cz_))
        shaft = cyl(1.95, 82.0, axis="x")
        shaft.apply_translation((sxa * 47.0, cy_, cz_))
        pinion = involute_spur(P["ant_pinion_t"], m_, 6.0, axis="x")
        pinion.apply_translation((sxa * 84.0, cy_, cz_))
        output = uni([g4, shaft, pinion])
        output.apply_transform(R(np.radians(71.0), (1, 0, 0),
                                  point=(sxa * 47.0, cy_, cz_)))
        _color(output, "motor"); output.metadata["name"] = f"ant_output_{side}"
        out.append(output)

        pl = box(2.0, 34.0, 32.0)                    # bushing plate |x| 8.5..10.5:
        pl.apply_translation((sxa * 9.5, wall_in + 18.5, 196.0)); br.append(pl)
        # (plate stops 1.5 off the wall plane: the REMOVABLE door's plug face is y -66
        #  below z 190.2 there -- the plate hangs from the spine, which roots on the
        #  fixed wall above the door outline)
        pt_, px_ = P["ant_plate_t"], P["ant_plate_x"] + P["ant_plate_t"] / 2
        ep = box(pt_, 36.0, 52.0)                    # motor face plate, 1.2 -> 2.5 thick
        ep.apply_translation((sxa * px_, -31.0, 189.6)); br.append(ep)
        # 36 deep (was 24, connectivity audit 2026-07-10): the Ø28.7 can-pass bore
        # spans y -44.4..-15.7, WIDER than the old y -43..-19 plate, so the bore
        # severed the plate and its bottom half (with the lower ear pilot) printed
        # as a LOOSE body; y -49..-13 keeps 4.6/2.7 ligaments either side of the
        # bore (front edge still 6 clear of the screen+Pi stack rear at y -7)
        rib = box(pt_, 38.0, 6.0)                    # face-plate root rib to the spine
        rib.apply_translation((sxa * px_, wall_in + 19.0, 212.0)); br.append(rib)
        # EAR NUT PADS (P0-4): pushed radially outward off the ear holes so they miss the
        # Ø28.25 can -- see PARAMS "ant_ear_pad*". Cut for the nut + bolt further down.
        epw, eph, epd = P["ant_ear_pad"]
        for sz_ in (-1, 1):
            # R(TAU/4, X) maps (x,y,z)->(x,-z,y): the EXTRUDE height becomes the Y span
            # and the footprint's d becomes Z. So build (w=X, d=Z-extent, h=Y-extent).
            pad = rounded_box(epd, eph, epw, 2.0)
            pad.apply_transform(R(TAU / 4, (1, 0, 0)))
            pad.apply_translation((sxa * (P["ant_plate_x"] + pt_ + epd / 2), my_
                                   + P["motor_shaft_off"] + epw / 2,
                                   mz_ + sz_ * (17.5 + P["ant_ear_pad_off"])))
            br.append(pad)
        # SPINE MOUNT BOSSES (P0-4): the bracket had NO attachment to the head at all --
        # this spine just rested on the wall. 4x M3x12 from outside the back panel.
        my0, my1 = P["ant_mount_y"]
        mbx, mbz = P["ant_mount_boss"]
        for mx_ in P["ant_mount_x"]:
            bs = rounded_box(mbx, mbz, my1 - my0, 2.0)
            bs.apply_transform(R(TAU / 4, (1, 0, 0)))     # extrude -> -Y
            bs.apply_translation((sxa * mx_, my1, P["ant_mount_z"]))
            br.append(bs)
        oa = box(3.5, 35.0, 22.0)                    # outer arm: half-shaft bushing
        oa.apply_translation((sxa * 78.5, wall_in + 17.5, 203.0)); br.append(oa)
        web = box(3.5, 14.0, 18.0)                   # web forward to the shoe
        web.apply_translation((sxa * 78.5, P["ant_y"] + 6.95, 205.0)); br.append(web)
        shoe = box(10.5, 3.4, 18.0)                  # rack backing shoe, 0.3 off the
        shoe.apply_translation((sxa * 84.0, P["ant_y"] + 12.25, 205.0)); br.append(shoe)
    bracket = uni(br)
    for sxa in (-1, 1):
        rel = cyl(P["ant_mast_d"] / 2 + 0.3, 44.0)   # shoe face rides the mast front
        rel.apply_translation((sxa * P["ant_x"], P["ant_y"], 205.0))
        bracket = sub(bracket, rel)
        pt_, px_ = P["ant_plate_t"], P["ant_plate_x"] + P["ant_plate_t"] / 2
        epb = cyl(14.35, pt_ + 1.0, axis="x")        # Ø28.7 motor-nose clearance bore
        epb.apply_translation((sxa * px_, -30.0, 189.6))
        bracket = sub(bracket, epb)
        # The corrected motor roll puts the eccentric shaft at ant_motor_y and therefore
        # the wiring box on the opposite, FRONT side.  This notch used to be at y=-46.3
        # in the rear ligament while the real box occupied y=-16.9..-13.0, leaving an
        # 80.15 mm3 hard collision per motor.  Notch the measured front envelope instead;
        # the full rear ligament plus the top/bottom front stubs keep the plate one body.
        wbx = box(pt_ + 1.0, 7.4, 16.2)
        wbx.apply_translation((sxa * px_, -14.7, 189.7))
        bracket = sub(bracket, wbx)
        # TILT-CLAMP-TUBE SCALLOP (2026-07-16 phantom-tier fix): at ant_plate_x 27 the
        # face plate lands MID-tube (the old x-36 plate sat just past the tube end) and
        # its bottom-front corner sliced 38 mm3 into the head_back frame's clamp boss,
        # which reaches r 16.87 about the tilt axis inside the plate band (measured).
        # Cut an r 17.5 tilt-axis cylinder across plate + pad root; the plate's O28.7
        # bore band (z >= 175.3) and both ear nut traps (r >= 22.6) are untouched.
        scal = cyl(17.5, 11.2, axis="x")
        scal.apply_translation((sxa * 30.5, P["tilt_axis_y"], P["tilt_axis_z"]))
        bracket = sub(bracket, scal)
        bore = cyl(2.1, 200.0, axis="x")             # half-shaft bushings Ø4.2
        bore.apply_translation((0, cy_, cz_)); bracket = sub(bracket, bore)
        bore = cyl(2.1, 44.0, axis="x")              # idler bushings Ø4.2
        bore.apply_translation((sxa * 16.5, iy_, iz_)); bracket = sub(bracket, bore)
        # SPINE MOUNT traps (P0-4): M3 clearance along +Y through spine + boss, captive
        # nut slid down from the boss top (so it is gravity-seated with the head upright).
        for mx_ in P["ant_mount_x"]:
            sc = cyl(P["m3_clear_r"], 17.0, axis="y")    # y -73..-56: spine + boss + the
            sc.apply_translation((sxa * mx_, -64.5, P["ant_mount_z"]))   # M3x12 TIP room
            bracket = sub(bracket, sc)                   # (2.0 past the nut, 2.0 of boss
            #                                              left blind ahead of it)
            bracket = sub(bracket, _nut_trap(
                (sxa * mx_, P["ant_mount_nut_y"], P["ant_mount_z"]), "y",
                (0, 0, 1), length=9.0))
        # MOTOR EARS (P0-4): 2x M3x10 through the ear + plate into a captive nut on the
        # plate's OPEN OUTBOARD face. Replaces two Ø2.5 self-tap pilots that bit 1.2 mm
        # of plate -- vestigial hardware on the exact plates that already printed severed.
        # The nut slot runs INWARD (toward the can) so its SEAT is the outboard side and
        # the pad's material beyond the hex corner is the 1.725 that exists there; running
        # it outward would need pad below the hole, which is inside the can.
        ey_ = my_ + P["motor_shaft_off"]
        for sz_ in (-1, 1):
            eh = cyl(P["m3_clear_r"], 14.0, axis="x")     # M3 clearance, ear -> nut
            eh.apply_translation((sxa * (P["ant_plate_x"] + 3.0), ey_, mz_ + sz_ * 17.5))
            bracket = sub(bracket, eh)
            bracket = sub(bracket, _nut_trap(
                (sxa * P["ant_ear_nut_x"], ey_, mz_ + sz_ * 17.5), "x",
                (0, 0, -sz_), length=6.0))
    _color(bracket, "back"); bracket.metadata["name"] = "ant_bracket"
    out.append(bracket)
    return out


def build_ear_jacks():
    """EAR MICS (2026-07-11 v2, user: only the TIP sticks out): the gooseneck mic
    mounts INSIDE the head (plug into the CM108 adapter at the Pi, flexible neck up
    the rear bay -- not modeled); the placeholder shows the Ø14.6 foam windscreen
    (compressed in the Ø15 grommet, 0.2 gap) with 12 proud of the wall, and the neck
    stub heading inboard over the screen top."""
    out = []
    xw = P["head_w"] / 2
    ey, ez = P["ear_y"], P["ear_z"]
    for sxe, nm in ((-1, "ear_mic_L"), (1, "ear_mic_R")):
        ps = []
        fm = cyl(7.3, 24.0, axis="x")                    # foam tip: 12 out, 12 in
        fm.apply_translation((sxe * xw, ey, ez)); ps.append(fm)
        # gooseneck stub, inboard: ANGLED forward (+y) like the real flexible neck --
        # a straight coaxial stub at the human-proportioned ear spot (y -29, z 172.5)
        # ran through the antenna mast (x +-85, y -31) and the screen-tray z-174
        # pillars (right 57.6..65.6, LEFT -68.6..-60.6). Rooted deep in the foam
        # (|x| 93) and diving to (|x| 71.5, y -12): 1.3 off the mast axis line
        # (dist 6.5 vs 5.25 contact), 0.9 off the left pillar band, 3 off the
        # screen-stack rear (y -7).
        gn = trimesh.creation.cylinder(
            radius=2.0, segment=[(sxe * 93.0, ey, ez), (sxe * 71.5, -12.0, ez)])
        ps.append(gn)
        m = uni(ps)
        _color(m, "track"); m.metadata["name"] = nm     # rubber-black, like the mic
        out.append(m)
    return out


def build_pi5_cooler():
    """Pi 5 ACTIVE COOLER keep-out placeholder (COOLER=1; bought part, NEVER printed).
    The official 63.5 x 42.5 x 13.7 envelope seated on the Pi 5's dedicated heatsink
    holes -- all position/depth derivation lives in PARAMS "pi5_cooler_*", the fit
    VERDICT in build.py where it is added. Cosmetic only: shallow (0.8) fin grooves on
    the intake face over the fin field + a fan-window ring groove at the measured
    window spot (board ~(41.7, 33.7), Ø~21), so the part reads as the cooler in the
    viewer without giving up keep-out volume anywhere that matters (the envelope is
    conservative by 1-2.5 there, see PARAMS)."""
    w, d, h = P["pi5_cooler_wdh"]
    bcx, bcz = P["pi5_cooler_board_c"]
    X0, Z0 = P["pi5_board_org"]
    yc = P["pi5_comp_face_y"]
    cx, cz = X0 + bcx, Z0 + bcz                      # envelope center (world x, z)
    m = box(w, d, h)
    m.apply_translation((cx, yc - d / 2, cz))
    # fin grooves across the fin field (board x ~7..27.5 measured off the drawing)
    for i in range(7):
        g = box(2.0, 1.6, h - 5.0)
        g.apply_translation((X0 + 8.5 + i * 3.1, yc - d, cz))
        m = sub(m, g)
    # fan-window ring groove (measured center board (41.7, 33.7), opening Ø~21)
    ring = sub(cyl(11.6, 1.6, axis="y"), cyl(10.2, 2.2, axis="y"))
    ring.apply_translation((X0 + 41.7, yc - d, Z0 + 33.7))
    m = sub(m, ring)
    _color(m, "motor")                               # anodised aluminium -> silver
    m.metadata["name"] = "pi5_cooler"
    return m


def build_cam_pod():
    """Cosmetic raised eye-pod over the recessed camera aperture (design-ref front.jpg).
    Separate charcoal print on the bezel face; 45 deg flared bore clears the CM3 FoV."""
    fy, lz = P["body_front_y"], P["cam_lens_z"]
    pod = rounded_box(P["cam_pod_w"], P["cam_pod_h"], P["cam_pod_t"], 7.0)
    pod.apply_transform(R(-TAU / 4, (1, 0, 0)))      # extrude +Y, footprint XZ
    pod.apply_translation((0, fy, lz))
    flare = np.tan(40 * DEG)                         # 40 deg/side (was 45: its Ø19 mouth on the
                                                     # 18-tall pod cusped to 0.05 at the lip);
                                                     # 40 > the CM3's 37.5 FoV half-angle, so
                                                     # still no vignette (PRINTABILITY 1)
    bore = frustum(P["cam_csk_d"] / 2 + flare * (P["cam_pod_t"] + 0.5), P["cam_csk_d"] / 2,
                   P["cam_pod_t"] + 0.5)             # flared bore, small end at the face
    bore.apply_transform(R(TAU / 4, (1, 0, 0)))      # shrink toward -Y (into the wall)
    bore.apply_translation((0, fy + P["cam_pod_t"] + 0.25, lz))
    pod = sub(pod, bore)
    # FIXING: glue + 2x Ø2 locating pins. The raised bay (cam_lens_z 226) puts the whole
    # pod footprint (z 216..236) on solid forehead wall above the pocket top (208.9), so
    # the pins sit symmetrically inside it (PARAMS campod_pin_pts).
    pp = [pod]
    for px, pz in P["campod_pin_pts"]:
        pp.append(fix_pin(P["fix_pin2_r"], P["fix_pin_len"], (0, -1, 0), (px, fy, pz)))
    pod = uni(pp)
    _color(pod, "camera"); pod.metadata["name"] = "camera_pod"   # /camera/ in the viewer PAL
    return pod


def _hatch_ring(grow=0.0):
    """The positioned hatch-frame ring solid; grow>0 inflates it (pack nest clearance)."""
    w, h, bd, t = (P["hatch_frame_w"], P["hatch_frame_h"],
                   P["hatch_frame_band"], P["hatch_frame_t"])
    outer = rounded_box(w + 2 * grow, h + 2 * grow, t + grow, 12.0)
    inner = rounded_box(w - 2 * bd - 2 * grow, h - 2 * bd - 2 * grow, t + grow + 2, 8.0)
    inner.apply_translation((0, 0, -1))
    ring = sub(outer, inner)
    ring.apply_transform(R(TAU / 4, (1, 0, 0)))      # footprint XZ, extrusion -Y
    ring.apply_translation((0, P["body_back_y"], P["hatch_frame_cz"]))
    return ring


def build_hatch_frame():
    """Orange chamfer-look frame proud of the head back face (design-ref back.jpg).
    Separate orange print over the service area; the existing louvres + cable port are
    the 'hatch' inside it. Bottom band notched clear of the neck-slot sweep envelope."""
    t = P["hatch_frame_t"]
    ring = _hatch_ring()
    # notch the bottom band over the deep-head motor BAY (back wall open x +-33 to z=168):
    # the frame may not reach into the tilt-sweep clearance envelope
    notch = box(70.0, 2 * t + 2, 74.0)
    notch.apply_translation((0, P["body_back_y"] - t, P["tilt_axis_z"] - 20.0))
    ring = sub(ring, notch)
    # FIXING: glue + 4x Ø3 pins at the band corners into blind back-wall sockets
    # (PARAMS hatch_pin_pts; they register the frame around the louvres/port)
    pins = [ring]
    for px, pz in P["hatch_pin_pts"]:
        pins.append(fix_pin(P["fix_pin_r"], P["fix_pin_len"], (0, 1, 0),
                            (px, P["body_back_y"], pz)))
    ring = uni(pins)
    _color(ring, "accent"); ring.metadata["name"] = "trim_hatch_frame"
    return ring


def _limb(p0, p1, w=9.0, d=11.0):
    """Arm segment between two (y,z) points, long axis in the YZ plane, X extent w."""
    vy, vz = p1[0] - p0[0], p1[1] - p0[1]
    L = float(np.hypot(vy, vz))
    seg = box(w, d, L + d * 0.6)
    seg.apply_transform(R(-np.arctan2(vy, vz), (1, 0, 0)))    # +Z -> segment direction
    seg.apply_translation((0, (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2))
    return seg


def build_arms():
    """Two articulated gripper arms (design-ref, PLACEHOLDER): RAISED pose per
    front-2.jpg -- upper arm up-forward, forearm up, C-claw opening upward. Raised
    (not tucked) because the 56-wide pods put their tops under the old tucked-claw
    sweep (claw dug into the pod top at pan ~20 deg + tilt down); raised claws stay
    above z~140 at every pan x tilt combination. A standoff tube bridges the rail
    face to the outboard shoulder. Joints stay cosmetic until the arm mechanism pass."""
    S, E, W = (0.0, 130.0), (20.0, 160.0), (30.0, 195.0)  # shoulder/elbow/wrist (y,z)
    C = (32.0, 212.0)                                     # claw ring center
    arms = []
    for sx, nm in ((-1, "arm_L"), (1, "arm_R")):
        parts = [_limb(S, E, w=9.0, d=15.0), _limb(E, W, w=9.0, d=15.0)]
        # shoulder standoff: rail face (107.5) -> arm plane; chunky r8 hub, local -X
        span = P["arm_x"] - (P["head_w"] / 2 + P["rail_t"])
        so = cyl(8.0, span + 4.0, axis="x")              # inboard is -sx after the mirror
        so.apply_translation((-sx * ((span + 4.0) / 2 - 4.0), S[0], S[1]))
        parts.append(so)
        for (py, pz), r in ((S, 11.0), (E, 9.5), (W, 8.5)):
            j = cyl(r, 10.0, axis="x"); j.apply_translation((0, py, pz))
            parts.append(j)
        claw = sub(cyl(18.0, 13.0, axis="x", sections=48),
                   cyl(10.0, 15.0, axis="x", sections=48))
        notch = box(14.0, 14.0, 22.0); notch.apply_translation((0, 0, 13.0))
        claw = sub(claw, notch)                          # C opening faces +Z (up, per ref)
        for syn in (-1, 1):                              # square finger pads at the C tips
            pad = box(13.0, 6.5, 7.0)
            pad.apply_translation((0, syn * 10.5, 13.5))
            claw = uni([claw, pad])
        claw.apply_translation((0, C[0], C[1]))
        parts.append(claw)
        arm = uni(parts)
        arm.apply_translation((sx * P["arm_x"], 0, 0))
        _color(arm, "arm"); arm.metadata["name"] = nm
        arms.append(arm)
    return arms

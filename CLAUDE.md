# desk-pi, tracked desk robot (Raspberry Pi head)

A small **tank-tracked mobile robot**: a **Raspberry Pi 5** driving the **official 7" touchscreen**
as an animated face, with a **Camera Module 3** as an eye, on a **neck that pans + tilts** the head,
sitting on a **two-track tank chassis** so it can drive around the desk.

The head is a **clean rounded box** (a tablet-head; earlier it was an Echo-Show wedge, since
simplified). Screen upright on the front, neck tilt gives the look up/down.

Status: **FIX CAMPAIGN COMPLETE (stages 1-5 + independent verification, see docs/FIXES.md);
MAINTENANCE/DFA PASS 2026-07-08** (workflow-reviewed, all gates green): tilt-motor cartridge
(`tilt_carrier`), D-keyed worm wheel on a flatted axle, track master links + keepers, pan BB
cage, pan/tilt stall-homing hard stops, microSD wall slot + `sd_plug`, located side-panel
joints, and the 12V dual-buck power tray (firmware/WIRING.md).
`src/build.py` builds the whole robot around the combined screen+Pi reference mesh; 10 watertight
per-part STLs (chassis, track_L, track_R, neck_clevis, pan_platform, pan_race, pan_clips,
head_bezel, head_back, cam_cover) plus placeholder sub-parts (worm_wheel, tilt_worm, pan_balls,
motor_*, drive_L/R). A 6-agent research pass drove the mechanism decisions now in geometry:
**pan = 28BYJ direct D-hub on a captured-BB lazy-Susan race**; **tilt = self-locking single-start
WORM drive** (Ø5 solid axle on 695-2RS bearings, owned); **screen+Pi ride as one module** (the
official Pins-Out assembly: Pi on the display's own 58×49 standoffs), carried by the bench-mounted
`screen_tray` at the factory M3 bosses (2026-07-08; was 4 rear standoffs with blind channels); **camera recessed behind the forehead** (official CM3
dims) with a lens bump + `cam_cover`; **tracks = measured-TT-motor positive drive: articulated
links + 12T sprocket + F688ZZ idler + road wheels**. The 28BYJ placeholder is now dimensionally correct (Ø28.25, 7.875 mm
offset shaft, 3 mm D-flats). Remaining gaps closed 2026-07-07: REAL involute worm teeth integrated (tools/gears/ generator,
docs/WORM.md, CD 11.9, PLACEHOLDER_GEARS=1 falls back), body-to-pod join modeled, BOM
inventory-checked (docs/ASSEMBLY.md), belly plate + head rear door, verified 18-step assembly
order. (Track gauge widened 2026-07-06: chassis_w
120->140, track outer faces +-102 ~= head half-width; base_h 52->66 for the design-ref stance.)

**Design-ref styling pass (2026-07-06, branch design-styling):** the 5 concept renders in
`reference/design/` (black+orange rugged two-tone) are now integrated as a 34-part GLB:
COLORS/PAL colorway (keep `src/build.py` COLORS and the viewer PAL in sync, the VIEWER
re-colors by node name and wins on render), orange head side rails (`trim_rail_L/R`, the
arm shoulders land on them), forehead LED strip + slot, TWIN DEPLOYABLE ANTENNAS
(2026-07-10, replaced the static stub: two knurled-cap masts at x +-85 / y -31, each with
a molded m0.8 rack, INDEPENDENTLY driven by its own 28BYJ through a mirrored two-stage
30:12 gear-up (6.25:1) and a Ø4 half-shaft pinion -- ~104 mm/s, 50 mm max past the head
top, ~0.5 s full deploy; masts sit behind the tilt clamp tubes, gear tips stay above the
z 174 drivetrain-sweep ceiling, motor bodies fill the x 25.7..44.5 band (2026-07-16
phantom-tier fix; was ..53.5) between the sweep
and the screen-tray rails, half-shafts pass over the rails at z 205; the top-wall guide
bores carry friction O-rings against gear-up back-drive, and ANT=<mm> bakes a preview
extension while the viewer gets one slider per mast; parts: antenna_L/R, ant_motor_gear_L/R,
ant_idler_gear_L/R, ant_idler_axle_L/R, ant_output_L/R, ant_bracket, and motor_ant_L/R;
the printable involute train has an exact coupled full-travel mesh test), rear orange `trim_hatch_frame` (bottom band
notched clear of the neck-slot tilt sweep), the EXTRUDED REAR POD on `head_door`
(2026-07-10, the user's red-box ref: the back of the head carries a chunky stepped
"backpack" bump; deepened same day per user "much more depth horizontally". The pod IS
the door: 3 stepped tiers x +-62/51/38 to y -85/-95/-105 (15/25/35 proud of the wall),
flat top z 169 keeps the louvre band open above like the ref, HOLLOW inside -- the
cavity x +-17 / z 130..162 / floor -98 swallows the tilt drivetrain's swept intrusion
(probe-measured x +-13.5 / y to -78.1 over +-33.8 deg) so the 28BYJ hides inside with
no relief hole, and a center-bottom corridor POCKET x +-27 / z<134 / floor -98 (closed
from behind by the deep rear wall) clears the neck cheeks' stall rake (x +-24 / y -86.9
/ z<=130.7 in the door frame). Probed at 21 tilt steps to the +-33.8 stalls against the
pan frame AND the fixed chassis set: 0 overlap, worst drivetrain->door clearance 1.85 mm. This
REPLACED the 2026-07-08 raised panel + latch/hinge cosmetics + through-relief AND the
glue-on `rear_pack` slabs AND the never-mounted floating `tilt_shroud` -- both parts
deleted. TOOL-FREE retention 2026-07-10, user "easy to open and close": per-leg SNAP
TONGUES -- a corner notch clears the pod mass off the tongue zone, one slit frees each
leg's outer strip, an outboard barb at plug level clicks behind the fixed wall band
beside the void; open = firm pull on the pod's bottom edge (35 proud = the grip), the
barb back ramp releases. Replaced the 2x M3x10 csk + captive-nut blocks. NOTE: open the
door at neutral-ish tilt; at the stalls the drivetrain reaches into the pod cavity.
head_back's rebate extends to the pod root footprint), chassis front fascia
(hex grille field +
orange surround/fins, HC-SR04 `sensor_us` in a floor recess, amber lamps, white LED bar),
running gear split into `drivewheels_L/R` (silver; geometry untouched), and PLACEHOLDER
gripper arms (`arm_L/R`, static tucked pose; actuation + mount decision deferred). All
styling parts probed against all parts: 0.000 mm³ overlaps. `TRANS=0 make shot` renders
solid (styling review); default stays 50% ghost.

**TOY-TANK HULL + front-slope cliff sensor (2026-07-10, user round 2: "upper part 10 cm
longer = 5 cm each side, lower 2 cm each side, angled so the proximity sensor looks
down, like a toy tank chassis" -- REPLACED the same-day front-only prow):** the lower
tub stretched 200 -> 240 (`chassis_l`; glacis_y0 103.1 keeps the 33 deg bevel) and the
deck slab runs `deck_overhang`=30 past BOTH tub ends (top plate 300 = the user's 10 cm),
the end faces sloping (|y| 120, z 46) -> (|y| 150, z 66) at atan(20/30)=33.7 deg from
horizontal -- undercut overhangs like an RC-tank hull, print-safe, same ~33 family as
the ramps/glacis. The slope's outward normal points 33.7 deg AHEAD of straight down, so
the HC-SR04 flush in the FRONT slope looks down-forward exactly as the user reasoned
(`sensor_cliff`; construction mirrors sensor_us: Ø16.6 bores through the 5-thick slope
skin, board in a 1.2 skin-back recess + 4x Ø1.6 M2 pilots, inside an underside pocket
x +-30 / top skin 3.5 whose inboard end opens over the tub -- wires just drop in,
service = lift the deck; ping lands ~y 163, cliff = no-echo). MIRRORED on the REAR
slope (`sensor_cliff_rear`, user round 3, reversing cliff detection): same sgn-flipped
construction, pocket narrowed to x +-28 (the rear deck-split bosses at +-34 pass within
2), and the rear hatch frame dropped + squashed to 72x18 at cz 28.5 (the rear barrels
sweep past the wall plane to ~z 39). THREE HC-SR04 total now (forward obstacle + 2
cliff) -- NONE in the inventory, all on the buy list. KNOCK-ONS, all re-homed:
grille ring dropped + grew (cz 32, 60x26) to swallow the sensor_us barrels inside its
opening (us_cz 32); fin row pulled inboard to x<=47.5 (lamps start 48); fascia pins
re-clocked (z 36/27); hex field moved onto the front slope flanking the cliff barrels
(|x| 26..52, blind 2.5 along the slope normal); TT front-tab pockets got floor-to-z40
RIBS at the old y -94.8 station (the rear wall receded to -120); deck-split rear screw
pair -> (+-34, -113). Probe-pass fixes bundled in: the idler tension plate is capped
0.2 under the z 46 seam (its crown used to slice into chassis_deck_front as two LOOSE
bodies) and a 14-wide floor TIE (z 8.5..12, x -26..-12) re-anchors the belly strap's
pedestal island inside chassis_lower_rear (loose since the y 26 sub-split; the belly
plate passes under the tie on its flange, with a matching relief cut). Connectivity
audit (user todo, same day): every part checked for loose internal bodies + assembly
contact -- the only real find was the ant_bracket motor face plates SEVERED by their
own Ø28.7 can-pass bores (bottom halves + lower ear pilots printed loose); plates
deepened to 36 with a wiring-box notch in the rear ligament. The former disconnected
`ant_gears_L/R` preview bodies were replaced 2026-07-16 by separately exported involute
gears, keyed motor hubs, running-clearance journals, fused output shafts, and true racks.
The antenna 28BYJ pose is centralized in `motors.antenna_motor()`: after pointing +Z
inboard, its roll sign is opposite the side sign so the eccentric +X shaft offset becomes
world -Y. The older same-sign roll put both shafts 15.75 mm ahead of G1 and left each wiring
box colliding 80.15 mm3 with a rear-notched plate. The bracket notch now follows the actual
front wiring-box envelope; `test_28byj_shafts_land_on_motor_gear_axes` guards both datums.

Latest render review (2026-07-06): `make build` wrote a 20-part `web/assembly.glb`; fresh
transparent and solid shots were inspected from iso/front/side/top plus two section cuts. The
assembly reads correctly as a tablet-head tracked robot, but the print-final fixes are:
**widen the track gauge**, add a low ballast bay in the chassis, model the body-to-pod M3/dowel
joins, shroud the exposed rear tilt motor, make the front camera/lens read more deliberately,
render neutral (`PAN=0 TILT=0`) and motion extremes, and add a bottom view to `src/shoot.py`.

## The build loop (do this on every geometry change)

**FASTENING RULE (2026-07-15, after the first full print came back unassemblable):**
every structural joint is **M3 through-bolt + a captive hex nut** cut with
`geo.nut_slot()`, plus a **locator** (dowel/pin/tongue/rebate) so the parts self-hold
while you drive the screw. **Ø2.5 "thread-form" pilots are BANNED on structural
joints** -- they self-tap into PLA and strip (the user's "almost none of the screws
work"). Only low-load electronics posts may keep self-tap. Pass `nut_slot()` the
**SCREW AXIS**, never a pre-offset point: it cuts the seat ac/2 behind, where
**ac = AF*2/sqrt(3) = 6.35 for M3, NOT the 5.5 across-flats** -- a hex with its flats
on the walls spans across CORNERS along the run. Getting this wrong is what broke
every trap in print 1, including `chassis_pedestal`'s, which the audit had called
the reference-good joint. `checks.nut_reaches_bore()` gates it; add an assertion for
each new trap. Where a nut geometrically cannot fit, **measure it, then** use an M3/M2
brass heat-set insert (bosses >= Ø9 for M3). Full ledger: docs/FASTENING_AUDIT.md.

```
make build          # python3 src/build.py -> web/assembly.glb
make viewer         # python3 src/serve.py 8770 (leave running; user watches live at
                    #   http://localhost:8770/viewer_glb.html -- auto-reloads on rebuild)
make shot           # headless render -> .claude/renders/chk_*.png  (serve must be up)
make check          # interference gate (run after every geometry change)
make fits           # fit/pressure map (ported from finnish-doors 2026-07-08): neutral-pose
                    #   clearance/press report for every close pair -> web/fit_report.json,
                    #   rendered by the viewer's "Fit map" (ON by default; click a pair to
                    #   isolate). Its CONTACT AUDIT fails loudly on any touching pair not
                    #   whitelisted in _FIT_CONTACT_OK (fitmap.py). Costs minutes, so it is
                    #   opt-in, not part of the watch loop. Patches are NEUTRAL-pose coords
                    #   but the viewer re-poses them per kinematic group (2026-07-10), so
                    #   they track the pan/tilt sliders and sit right on ANY baked GLB pose.
make invariants     # design-invariant gate (src/checks.py, IN make all): one
                    #   assertion per user-approved feature -- ADD A CHECK THE SAME TURN a
                    #   feature is approved, so it can't silently regress later.
                    #   READS stl/*.stl, so it now DEPENDS on `make stls` (EXPORT=1 build).
                    #   Before 2026-07-15 it (and wallcheck, and make all's ordering) read
                    #   whatever the LAST export left on disk -- i.e. silently gated STALE
                    #   geometry and reported a pass. Two agents lost work to it. If you add
                    #   an STL-reading gate, give it the `stls` prerequisite.
make jointcheck     # assembly-joint contract gate (src/joints.py declarations +
                    #   src/joint_checks.py): positive location, seated fit, fastener
                    #   stack, nut/insert and tool access, supporting material, and
                    #   collision-free insertion. Depends on `stls`; writes the complete
                    #   machine-readable result to web/joint_report.json.
make gate-tests     # stdlib unittest mutation fixtures: known-bad missing/offset/blocked
                    #   joint geometry MUST fail its owning gate. Add a failing mutation
                    #   test whenever a new reusable check is introduced.
make wallcheck      # min-wall gate over the printed STL set (0.8 mm p1 + documented
                    #   whitelist floors; IN make all since 2026-07-13, all findings
                    #   dispositioned: keepers fixed Ø4.0 cb + 5.7 tab rim 0.85,
                    #   head_back frames export watertight via geo.export_stl's
                    #   quantized check + guarded manifold3d repair, gear tooth
                    #   tips/run-out feathers whitelisted with probe-verified reasons)
make tipover        # mass/CoM/tip-margin report (solid-PLA + 50%-infill bounds); a
                    #   report, not a gate -- 2026-07-13 verdict: no ballast needed.
make docs           # render docs/*.md + firmware/WIRING.md + software/README.md ->
                    #   web/docs/*.html (tools/build_docs.py; IN make all). The viewer
                    #   has a top nav header linking them; its nav markup/CSS must stay
                    #   in sync with nav_html()/NAV_CSS in the builder. shoot.py hides
                    #   #topnav so CAD renders stay chrome-free. Pages deploys web/
                    #   verbatim, so docs ship with the published viewer.
make assembly-release # canonical print-release pipeline. It explicitly sequences a
                    #   fresh EXPORT build, invariants/joint/wall/interference/sweep/fit
                    #   gates, a final export, slicecheck, and docs. Do not rewrite this
                    #   as unordered prerequisites: `make -j` could race generated-file
                    #   readers, and `make fits` intentionally changes assembly.glb pose.
```

**JOINT CONTRACT RULE:** every interface between assembled printed parts has exactly one
entry in `src/joints.py`, using the typed contracts in `src/jointspec.py`. Geometry and its
contract must share named parameters/datums rather than duplicate coordinates. In the same
turn that a joint changes, update its declaration, focused mutation tests, `docs/JOINTS.md`,
and the affected step/BOM in `docs/ASSEMBLY.md`. Flat-on-flat plus screws is not a locating
joint: structural parts must sit in a deterministic seated pose on rails, rebates, tongues,
or separated pins before a screw is driven. A joint is not approved merely because its final
pose renders without interference.

Then **downscale and actually Read every PNG** before claiming a change works:
`sips -Z 1400 .claude/renders/chk_iso.png --out .claude/renders/chk_iso_s.png`.
The model is served at `/assembly.glb` (serve.py serves `web/` at root), so shoot.py takes
the **bare** name `assembly.glb`, not `web/assembly.glb`.

## Mechanical intent

World frame: **Z up, robot drives + looks toward +Y** (glass + camera + track travel all +Y).
Origin = center of the ground contact plane. `base_h = 52` is the chassis-top / pan-mount plane.

Kinematic chain, bottom to top (built at neutral pose pan=0, tilt=0):

```
tank chassis        DRIVE base: central body (build_base) + track_L/track_R (build_tracks) +
  │                 drive_L/drive_R (2x TT gearmotor, shaft X into each pod's rear sprocket).
  │                 Body houses the pan motor + driver + wiring; pan-mount on top (z=52).
  │                 Tracks = 64 modular link pads on a RAISED TANK LOOP (2026-07-10, RC-tank
  │                 refs; was a flat stadium): sprocket + idler axles sit track_raise=9 above
  │                 the old centerline (z 34.32), ~33 deg ramps at both ends, ~147 deg wraps,
  │                 flat ground run +-track_ground_hy=120; wheelbase 256.326 SOLVED so the
  │                 loop closes at exactly 64x10 (asserted in _track_link_poses).
  │                 MID-DRIVE ARCHITECTURE (2026-07-11, user chose "tracks 1 cm past
  │                 the deck tips"): end axles +-128.16, track ends +-153.5 -- past
  │                 the coaxial-TT limit, so BOTH loop ends are now FREE IDLERS on
  │                 Ø8 stubs in DECK-OVERHANG PYLONS (x 62..70, clipped at |y| 120.5;
  │                 front pair carries the tension slots + M3 set screws, rear pair
  │                 blind Ø7.85 press sockets), and the DRIVE SPROCKET sits INSIDE
  │                 the loop ON THE GROUND RUN at spr_y=-68 (center z = zc = 25.32):
  │                 the robot's weight presses the straight run into the pin pockets
  │                 (rack-style 2-3 pin bite, ground reaction guarantees mesh). The
  │                 TT stays DIRECT on the sprocket shaft, dropped ~9 with it; spr_y
  │                 -68 is the derived slot that misses the ULN posts, the pod-join
  │                 nut band and the (re-clocked) side vents -- see PARAMS spr_y. STRETCHED
  │                 same day with chassis_l 156->200->240 (user: "longer, same shape as the
  │                 refs"; the wb/2 - ground_hy = 8.163 end geometry is unchanged, so all
  │                 end clearances carry over). 7 dished Ø20 road wheels (pitch 23, to
  │                 +-69), spoked 12T sprocket (6 lightening holes), dished idler. The
  │                 raise lifts the TT motors too: gearbox top 45.5 stays under the z46
  │                 deck seam; the rear deck-split screw pair rides the rear wall (+-34,
  │                 -93); pod joins spread to y +-40; vents extended to +-48/64.
  └─ PAN joint      yaw about vertical Z  (±90° target). motor_pan direct D-hub; rides a captured-BB
      │             lazy-Susan race (build_pan_race: pan_race + pan_balls)   ── the "turret"
      └─ pan_platform + neck_clevis   rotate as one
          └─ TILT joint   pitch about horizontal X (±30°). SELF-LOCKING WORM: motor_tilt (shaft +Y)
              │           carries tilt_worm meshing worm_wheel keyed to the axle. Holds tilt de-
              │           energized. Ø5 SOLID axle rotates in 695-2RS bearings in the cheeks.
              └─ head = head_bezel + head_back (rounded box) + screen + camera + cam_cover + Pi 5
```

- **Pan** carries the whole neck + head. **Tilt** carries only the head. Tilt is a child of pan,
  so a pan move swings the tilt axis with it (correct for a neck).
- **Pan drive + bearing:** motor_pan (28BYJ) sits CAN-offset in the base so its double-D shaft lands
  ON the pan axis, keying into a D-bore hub under `pan_platform` (flats carry torque; grub screw
  kills backlash). The platform rides a **captured-BB lazy-Susan race** (`pan_race` lower ring +
  `pan_balls` on an Ø80 circle; the platform underside is the grooved upper race). Wide ball circle
  carries the top-heavy head without wobble. No worm on pan (a balanced vertical axis has no gravity
  torque to hold).
- **Tilt is a SELF-LOCKING WORM drive on a REAR CLEVIS** (not a side gimbal, not direct-drive). The
  head clamps a **Ø5 solid axle** at its side-wall hubs (axle turns WITH the head); the axle rotates
  in **695-2RS bearings** pressed into the neck cheeks (x=±22); the `worm_wheel` (12T, was 24T; halved
  in stage 2 for tilt speed) is keyed to the
  axle and driven by the `tilt_worm` (single-start) on motor_tilt, whose shaft runs +Y (right-angle to
  the axle). Single-start worm self-locks, so the head holds ±30° with the motor de-energized (no idle
  current/heat). Pre-balance the head on the axle (Pi as counterweight) so the worm barely works. Axle
  position (y=−18, z=178, `tilt_axis_y`/`tilt_axis_z`) MUST match the cheek bearings, an earlier bug
  lifted the clevis 46 mm; build in world coords. **Stage 2R moved the axle BACK 18 mm (y 0 → −18):**
  the Pi rides the display back, and at y=0 the axle/worm/cheeks ran through the board plane. The
  whole drivetrain (cheeks+hoops, wheel, worm, brackets) keys off the `tilt_axis_*` pair; the screen
  is anchored separately (`screen_cz`=178) and did NOT move.
- **Camera is RECESSED behind the forehead** (the 24 mm board can't fit the ~10 mm forehead gap): lens
  bump on the front at `cam_lens_z`, board on 4x M2 bosses at the 21×12.5 pattern, `cam_cover` traps
  it, CSI ribbon drops to the Pi bay. Lens optical axis is X=0, Z=+2.47 above board center (not centred).
- **Screen is held by its 4 FACTORY M3 holes** (outer 126.2×65.65 case-mount pattern) via the
  **`screen_tray`** (2026-07-08, replaced the 4 rear standoffs + their 88.5 mm blind driver
  channels; stage 3a/5 history still applies: bezel bosses through the glass are forbidden).
  The module bolts to the tray ON THE BENCH (4× M3×10 into the factory bosses, pillars z-offset
  so the driver line is open), tray faces land on the boss REAR plane (y 22.48, the D1 datum);
  the loaded tray drops into head_back and 4× M3×10 drive from OUTSIDE the back wall (heads in
  the fixed strip between the door outline and hatch-frame opening). The front glass lip is only
  a locator. See `PARAMS["scr_mount_pts"]` + `build_screen_tray()`.
- **Pi 5 rides the DISPLAY's own 58×49 standoffs** (official mounting, the Pins-Out combined mesh),
  in the head behind the tilt axis. DSI + CSI ribbons stay entirely in the head (zero joint
  crossings); the board doubles as the tilt counterweight. Only round wires (Pi power) cross the
  joints. Tradeoff: heavier head + higher CoM → ballast the base low.
- **Cable path:** the axle is SOLID (the old Ø2.5 weight-relief bore left a 0.25 wall under the
  D-key flat, review 2026-07-08; nothing routed through it anyway). The route: base USB-C wall
  port → base cavity (pan **service loop**) → 16×8 obround pass in the platform → neck channel →
  out the column top → into the head through the bottom-rear slot with a tilt drape (±30° is
  easy). Pan is ±90°, so a service loop beats a slip ring, it carries the full Pi rail silently
  and free; software-limit pan so it never over-winds. A 2A/circuit capsule slip ring can't pass
  the rail current without paralleling contacts; only add one for 360° pan.

## Head is a 2-piece print (bezel + back)

`build_head_parts()` slices the wedge on a plane parallel to the front face, ~4mm behind the screen:
- `head_bezel` (front): the face + camera lens bump (CM3 aperture: Ø6.3 bore + Ø8 csk) + the 8
  bezel↔back nut-trap bosses. The stepped aperture lip is just a locator. Print face-down.
- `head_back` (rear): pivot hubs, neck slot, the 4 screen-tray wall holes + counterbores,
  Pi I/O slot (right wall), cable port, vents. Print open-side-down.
The screen+Pi module bolts to `screen_tray` on the bench, the tray drops into head_back (4× M3×10
from outside the back wall); bezel bolts to back.

## Head style: simple rounded box (simplified from the Echo-Show wedge, per user)

The head is now a **clean rounded box** (`_head_solid`: rounded-rect footprint 205w × 101d --
deepened 2026-07-07 so the envelope CONTAINS the tilt stepper (motor bay slot x ±33, y -78..21,
z 78..168 replaces the old rear cable port; the bay IS the cable route now), flat
top/bottom, rounded vertical edges, upright front `face_angle=0`). The screen sits upright and flush
on the front; the neck's tilt provides the look up/down. It started as an Echo-Show "doorstop" wedge
(reference in `reference/alexa-style-smart-display/`, a Touch Display 2 design we borrowed the style
from) but the user asked to simplify the head shape. Still split by `build_head_parts()` into
`head_bezel` (front, locator lip, camera nub) + `head_back` (screen-tray holes, hubs, vents).

## Key numbers (measured, not guessed)

The build loads the COMBINED display+Pi reference mesh (Pins Out variant: the Pi rides the
display's own 58×49 standoffs, GPIO pins out): 192.96 (W) × 38.01 (D) × 110.76 (H) mm, from
`reference/rpi-7in-touchscreen-model/files/Raspberry_Pi_Touch_Screen_Assembly_-_Pins_Out_v8.stl`,
posed by the GLASS PLANE (not bbox center; the pins-out mesh is 13 mm deeper on the back) via
`screen_pose()`. `PARAMS["screen_d"]=25.0` describes the display module alone, not this mesh.
NOTE: this mesh is NOT watertight, manifold booleans on it raise; probe screen clearances with
surface-sample containment, never with `ivol()`-style try/except (that returned vacuous 0.000 for
three stages, see docs/FIXES.md Stage 4). Overall assembly bbox ≈ 209 × 170.5 × 251 mm.

Still first-guess (validate on a print): tilt axis at y=−18 / z=153 (moved back 18 mm in stage 2R
to clear the Pi-on-display stack; z was 178 until the 2026-07-06 head drop shifted the whole
head+tilt stack −25), screen center y 18.5 / z 153, tilt ±30, pan ±90,
worm module 1.25 / 12T wheel, track pitch 10 / 64 links / 12T sprocket, pan BB circle Ø80. Neck
column at `neck_y=−17` (stage 5: footprint max r 43.1 fits the spinning platform's solid r45; the
cable channel is decoupled at `neck_chan_y=−26`). Head width 205 vs track outer width 238
(chassis_w 140, base_h 66, track_width 44.8 (2026-07-07: 2x design-ref chunk then -20%
per user); pods now flank the head like the reference; sprocket band stays 8 wide in the
links' central channel, idler grows outboard-only to clear the tension plate).

## Power (decided 2026-07-08, see firmware/WIRING.md)

One wall USB-C cable → rear-jack **PD trigger set to 12 V** → two bucks on the **belly-plate
power tray** (drop the belly plate = drop the power stage for service): an XL4015-class 5 A
buck makes the **Pi rail** (trimmed 5.25 V at the tray, ~5.1 V at the head after the neck
run, into the Pi's GPIO 5V pins + inline 5 A fuse), an MP1584 mini buck makes the **motor
rail** (ULNs, MX1588, chassis LEDs). Why not 5 V straight through: PD negotiation can't
cross a 2-wire joint run, 5 A droops 0.3-0.4 V over the harness, and TT stall transients
would land on the Pi rail. GPIO powering needs `usb_max_current_enable=1` + EEPROM
`PSU_MAX_CURRENT=5000`. Any 30 W+ PD brick works now (the official 27 W included). Firmware
rule: cap TT PWM at 80% and never full-drive both TTs while a stepper steps (27 W budget).

## Motors, 28BYJ-48 pan/tilt (dimensionally correct now) + TT track drive

Motor choice made against the parts on hand (see a personal parts inventory): the head is driven by
**28BYJ-48 5V geared steppers** (×6 in Bags 5 & 14) with **ULN2003 boards** (×9); the 9g servos are
too weak to swing a 193mm screen head. `motor_28byj()` is now dimensionally correct: **Ø28.25 can,
18.8 tall, 7.875 mm shaft offset, Ø4.93 double-D shaft with 3.0 mm flats over the top 6 mm**, ears at
35 mm, wiring box. **PHANTOM-TIER FIX 2026-07-16 (user: "motors mounted wrongly to the gears"):
the placeholder used to stack a fictional 9 mm "gearbox" tier (motor_gear_h, deleted) between the
can face and the shaft -- the real 28BYJ's gearbox is INSIDE the can and the shaft protrudes
straight from the top plate (~28.6 total, per the reference mesh + datasheet). All gears were keyed
to the phantom shaft plane, so the real motor could never reach them. Shaft-base planes (and all
gears) HELD; every CAN moved 9 mm toward its gear via the derived can-bottom formulas: pan can
bottom 12.95->21.95 (pedestal grew with it, ped_ear_nut_z 25.4->34.4, the collar now truly wraps
the can top under the 32T gear), tilt can rear -64.3->-55.3 (it registers the neck Ø29 pocket over
its full length now; the ear bar seats 0.2 behind the pocket-front wall, so the carrier's old M4
ear bolts were geometrically impossible and became pin-post SANDWICH retention -- see
build_tilt_carrier; the neck's ear-bar/wiring-box reliefs became full insertion channels), antenna
cans |x| 53.5->44.5 (ant_plate_x 36->27, ant_ear_nut_x 41->32, plus a r17.5 tilt-axis scallop
where the moved face plate straddled the clamp-tube boss).** The governing rule for both joints:
**locate the CAN so the offset shaft lands on the target axis, don't fight the offset with an
eccentric coupler.**

**Real bought meshes in the assembly (2026-07-13, `src/refparts.py`, default ON):** the
downloaded Thingiverse meshes (reference/electronics/, see docs/ELECTRONICS.md) for the
28BYJ, TT gearmotor, HC-SR04 (all 4 sites), Arduino Uno, and Camera Module 3 REPLACE their
box/cylinder placeholders in the GLB so the viewer shows real geometry. **EXCEPTION
2026-07-16: the 28BYJ skips the OBB heuristic** -- it is blind to the eccentric shaft and
parked every real stepper ~15 mm off its gear axis; refparts now recovers the placeholder's
EXACT pose by Kabsch over the vertex correspondence (posed placeholders are pristine
rigidly-moved motor_28byj() meshes) and registers the real mesh with a fixed measured
native->local transform (guarded by tests/test_refparts_28byj.py). Everything else stays
uniform: `add()` fits each real mesh onto the placeholder's world OBB via a 24-cube-
orientation best-fit (shape distance, not extent order -- extent order mislabels axes when
the crude placeholder's proportions differ, e.g. HC-SR04 barrels). Bought parts, never
exported/printed, and skipped by the boolean interference/fit gates (`assembly_check.EXCLUDE`
/ `fitmap` SKIP now pull `refparts.excluded_nodes()`, joining the non-watertight screen).
`PLACEHOLDER_PARTS=1` restores the analytic placeholders AND their full gate coverage (the
gate's exclude set is empty then). ULN2003 keeps its placeholder (no mesh downloaded).

- **Pan (direct D-hub):** 28BYJ upright in the base, can offset `-motor_shaft_off` so the shaft is on
  the pan axis; it keys into a **double-D bore hub** under `pan_platform` (`dbore_neg`/`dbore_hub`;
  flats drive snug, round arcs loose -- mini-Oldham, the race locates). No reduction. Rides the
  lazy-Susan BB race (see Mechanical intent). **Homing:** stall against the deck stop posts at
  ±93.3° (lug az 225 on the platform underside, posts az 118/332), back off, call it ±90.
- **Tilt (3-START worm since 2026-07-12, CARTRIDGE):** the worm sits on the motor's D-shaft
  (shaft +Y, right-angle to the axle), meshing a 12T `worm_wheel` **D-keyed to the flatted Ø5
  axle** (hub ledge on a filed 1.0-deep flat, 2026-07-08; the old M3 grub was blind and
  friction-only). The 3-start worm (4:1, lead ~23°) BACK-DRIVES -- the old single-start
  self-locking is gone, see the fast pan/tilt pass + the tilt-holding decision below. Motor +
  worm ride the removable **`tilt_carrier`** (ears drop onto the plate's pin-posts on the
  bench -- 2026-07-16 sandwich retention, see the phantom-tier note above -- 4× M3×16 from the open
  rear bay; the worm extracts axially through the plate's Ø12.2 bore, spinning the free wheel
  as it goes). Extraction with the head hung is unconditional now: with a dead motor, hand-nod
  the head while pulling -- the back-drivable mesh spins the worm out. (The old rule, DRIVE THE
  HEAD FULLY UP first because clearing mesh needed ~46° of worm-as-rack nod against ~34° of
  stop travel, applied only to the single-start worm, where the stalled head locked the worm;
  retired 2026-07-13.) A dead 28BYJ swaps without touching the head. **Homing:** stall the
  head's ±55° clamp-tube fins against the cheek posts at ±33.8°. Real generated teeth per
  docs/WORM.md.
- **Axle + bearings:** Ø5 SOLID rod (flat filed 1.0 deep from the insertion end to ~15 past
  center; a tube dies under the flat -- 0.25 wall; D-key ledge fit +0.05, coupon first, the
  old +0.15 was ±4.4° of head backlash; the +X 695 inner race rides the D-profile, fine
  since the spacer tubes clamp it) on **695-2RS bearings (5×13×4, owned ×30)** pressed into
  the neck cheeks. Head clamps the axle ends (grub screws at x=±30, kept: they give
  continuous tilt-zero trim).
- **ULN2003 mounts / motor pockets:** the base has a pan-motor pad + ULN standoffs; the tilt
  motor's Ø29 can pocket doubles as the cartridge's mesh lead-in.

**Buy list (gaps; inventory re-audited 2026-07-13, full BOM in docs/ASSEMBLY.md):** 8× F688ZZ
flanged bearings 8×16×5 (2 per end idler ×4; the owned Bag 13 "Miniature Ball Bearings" are
labeled 10pcs MR105 ZZ = 5×10×4, wrong part), 4× M8×60 + NYLOC nuts + washers (end bolt-axles;
SETTLED: the Bag 13 "Machine Bolts" bag label reads **30PCS M3-30** -- no M8 owned), 10× M4×40
(road-wheel bolt-axles: HARD plain-shank 34.0..35.5 mm on M4x40, REJECT full-thread and
stock DIN 931; 40 mm exceeds the owned kits -- M4 NUTS are covered, the 600pc kit lists 40),
4× HC-SR04 (forward + rear obstacle + 2 cliff; NONE owned), 6 mm airsoft BBs (pan race),
Ø5 SOLID rod for the tilt axle (gets a filed D-flat; no tube -- the old wishlist "Ø5 tube"
entry is stale), the power set from firmware/WIRING.md
(30W+ PD brick, 12V PD trigger, XL4015 5A buck, MP1584 mini buck, JST-XH kit + crimper,
18 AWG pair, inline blade-fuse HOLDER -- the 5A blade fuse itself is OWNED in the ATC/ATO
assortment; the owned LM2596/selectable bucks are 2-3 A class, no Pi-rail substitute, though
a selectable-5V module could stand in for the MP1584 motor rail), Ø4×12 dowels ×4, 1 m of
NARROW (4–5 mm) addressable strip (SK6805-2427/WS2812-2020, a standard 8×5050 stick is
53.3×10.2 and does NOT fit the 42×5 `led_slot`). TT gearmotors SETTLED: inventory shows
**3× TT 1:120 (Bag 5)** -- both required stations covered, buy 1 only if the optional
twin-drive is populated. Arduino Uno R3 ×3 (Bag 6) confirmed. Gooseneck mics + CM108: ordered,
NOT yet in inventory (verify the Ø17 windscreen on arrival, docs/ASSEMBLY.md). M2/M3 screws
are covered by the owned kits. The "608zz ×30" SETTLED: bag label reads "10pcs-608ZZ" (real
bearings under shrink wrap, not plastic rings); still unused in the design.

**PLASTIC HARDWARE STAND-INS (2026-07-15, user: dry-assemble in plastic till the metal
arrives):** every buy-list metal row has a print-oriented interim part in
`src/standins.py` -> `stl/hardware/` (EXPORT=1 writes them; export_bambu packs the
"Hardware stand-ins" plates): M4x40/M8x70 bolt-axles + real printed ISO-thread nuts,
washers, F688ZZ->flanged plain bushings, pan BBs->a Ø5.8-section torus SLIP RING
(printed spheres don't print; pan_cage idles till real BBs), the Ø5 D-flat tilt axle
(lies diagonal, flat UP), seam dowels + neckfoot pins. Export-only (no scene nodes,
gates untouched); wallcheck PRINTED + a checks.py invariant cover them; BOM unchanged
-- swap 1:1 for metal on arrival, limits in docs/ASSEMBLY.md ("Plastic hardware
stand-ins").

**BAMBU PER-CATEGORY AUTO-ARRANGE (2026-07-15, user):** export_bambu.py round-trips each
category through BambuStudio's own arrange engine (bambu_autopack.packed_plates in the
bambu-3mf-export skill, brim-pad trick because the CLI is brim-blind) and keeps the
BETTER of Bambu-vs-naive per category (measured: Bambu wins many-small-part plates,
stand-ins 2->1 + links 3->2 = 20 plates total; naive wins big-shell plates). --orient
stays OFF: a probe run showed it flipping 16 deliberately-posed parts (deck_center
cosmetic face into supports, masters onto the floating C-jaw, the axle stood on end);
deliberate="*" hard-fails the export if arrange TILTS anything (yaw is free). Full
gotcha list in the skill's "BambuStudio-CLI auto-arrange" section.

**Buy-list additions (software side, 2026-07-12; 2026-07-14 order batch folded in):**
- **Pi 5 cooler, BOUGHT 2026-07-14: 2x Joy-IT RPI5-HEATSINK5 (Tray 1, not delivered),
  BUT its 65x45x15 envelope (+30x30x10 fan) EXCEEDS the verified official-cooler
  keep-out (63.5x42.5x13.7) on every axis and the tilt-sweep margin was only 0.60 mm:
  re-run tools/probe_cooler.py with the Joy-IT dims BEFORE installing in the head**
  (fallback: official Active Cooler, whose envelope is the verified one, or duct the
  separately bought 30x10 5V fan at the louvres). History: downgraded to nice-to-have
  2026-07-12 after the passive heatsink (2.1-2.4 GHz sustained, 85 °C peaks); official
  envelope CAD-cleared 2026-07-13 (worm-tail retreat, >=0.60 mm static + sweep).
- ~~USB-A→USB-B cable~~ COVERED: user has one cable per Uno (3× Uno R3 compatible in
  Bag 6; no board purchase needed either). The Arduino I/O plane is fully stocked.
- **Sensor suite (AWARENESS.md), largely RESOLVED 2026-07-14 by 2x Sense HAT Rev2
  (ordered, Tray 1):** the HAT covers IMU (LSM9DS1 9-DoF, off the buy list) + env
  temp/humidity/pressure (BME688 now OPTIONAL, only for VOC/gas) and adds TCS3400
  light/color + 8x8 LED matrix + joystick. It is a Pi I2C peripheral, NOT an Arduino
  part: it mounts on the chassis_base over a 3-wire neck I2C drop (firmware/WIRING.md;
  it can NOT stack on the Pi -- no head clearance + the cooler owns that space).
  STILL BUY for the Arduino plane: mmWave LD2410-class, SW-420, TTP223 ×2-4, 4x HC-SR04.
- **Also in the 2026-07-14 batch:** Pi 5 **8GB** (lifts the AWARENESS 2GB RAM ceiling;
  re-run the software/README.md benchmarks on arrival), **AI Camera IMX500** (resolves
  the AI-camera decision; cam pod re-fit VERIFY_ON_ARRIVAL), A4988 driver + 6x N20
  gearmotors (no station yet; bipolar-28BYJ torque option / gripper-arm candidates,
  see docs/ELECTRONICS.md).

## Tank chassis (the mobile base)

Two-track tank base. GLACIS 2026-07-10 (user: "the chassis shouldn't be a box"): the hull's
front/rear lower corners are cut at the track-ramp 33 deg, from (|y| 83.1, z 7) to the walls
at z 18, so the side profile follows the tracks; the front white LED bar rides the slanted
face (tilted with it), US barrels sit at z 28.5 under the +1-raised grille, the rear pod
moved to (47, 30.5), USB slot + PD pilots to z0+24. `build_chassis_parts()` splits the
central **body** into `chassis_lower`
(open-top tub: side motor mounts, pod joins, electronics/ballast floor) and `chassis_deck`
(shallow removable pan deck: pan seat, pan clips, pan motor top register). The old one-piece
`chassis` trapped deep cavities and side-wall features in an ugly support-heavy print. The split
is a horizontal seam at z=46, clamped by 4x M3 down from the deck into lower Ø2.5 thread-form
pilots (front pair on the side ledges, rear pair on the REAR wall at +-34/-93 since 2026-07-10:
the raised TT gearboxes own the old side spots). `build_tracks()` builds two
**positive-drive track pods** (geometry from the local `Tank track - 3062624/` reference = Thingiverse
thing:3062624, CC-BY): a chain of **64 printed link pads** (`_track_link_poses` walks the RAISED
TANK LOOP -- see the kinematic-chain diagram above for the 2026-07-10 profile numbers)
on filament-rod hinge pins, a **12-tooth drive sprocket** (rear, RAISED, spoked with 6 lightening
holes) meshing the pins, a raised **idler** on TWO F688ZZ bearings (front, one per face) in a
tension slot, and **7 dished road wheels** supporting the bottom run. Positive tooth
engagement beats a friction belt that slips when the head pans.
TRACK-DRIVE FIX PASS (2026-07-10, review): (1) the sprocket got REAL PIN POCKETS
(`_sprocket_disc`: 12 circular seats r 1.15 on the 19.32 pin circle, 0.63 radial bite,
mouth 2.05 > the Ø1.75 pin -- the placeholder gear_disc trapezoids engaged only ~0.36 and
invited tooth-skip at stall); (2) the 6 road wheels/side, previously mounted to NOTHING
(weight went to ground through the TT gearbox shaft + idler stub), now run on **M4×40
bolt-axles** off a WHEEL BEAM grown into each pod rail (x 74..80.4 / z 14..26 / y ±58,
fused to both join blocks in the loop's link-free band; Ø4.4 bores, M4 nuts in slide-up
slots from the beam bottom, head = the outer hubcap, 1.0 running gap beam→wheel face);
(3) the idler got a second F688ZZ (flange recess at BOTH faces -- one 5-wide bearing at
one edge of a 30-wide wheel was a wobble hinge). Rail print orientation: bed plane is now
the beam's outer face; support the two block bands above z 26.

- **Drive:** `drive_L`/`drive_R` = 2× TT gearmotor placeholders (`motor_tt`), one per pod, shaft on X
  into the sprocket. **You own 3× TT 1:120 (Bag 5, re-audited 2026-07-13) + bare 130-size cans;
  both required stations are covered, buy 1 more only for the optional twin-drive 4th station.**
  One MX1588 (own ×5) drives both. Skid/differential steer.
- Params: `chassis_w/l`, `track_wheel_r`, `track_wheelbase`, `track_width`, `track_pitch`,
  `track_links`, `sprocket_teeth`, `idler_bore_d`, `roadwheel_*`, `track_gap`, `chassis_clear`.
- **Body-to-pod join: RETIRED 2026-07-14 (rounds 2-4)** -- the side walls ARE removable
  panels now and the wheel beam is integral to them (see SIDE PANELS = STANDALONE TRACK
  MODULES above); no separate rail, no through-wall join hardware. **Master link:** link 0 of each loop is a drop-on C-jaw link; two printed
  keeper bars slide in from the side faces, 1× M2 each (`track_keeper_L/R`) -- the loop closes
  without flexing and opens with 2 screws.
- **Still TODO:** links as real TPU/PLA print vs the rigid model. Pi rides the head (high CoM)
  → keep the chassis heavy/low and the wheelbase long so it doesn't tip on accel or a fast head pan.

## Print notes (first pass, not finalized)

**PRINT-SPEED SPLITS (2026-07-10, user):** the four biggest prints are sub-split so no
piece exceeds ~225 cm3 solid and EVERYTHING fits a 180x180 bed: `head_back` -> FOUR pieces
(2026-07-10 second pass, user: the halves still ceiling-printed the whole back wall):
per side a flat BACK PANEL (the 4mm wall slab: door rebate/void, snap catch band, tray
screw holes -- prints lying flat, outer face up, ~zero support) + a WALL FRAME (walls,
pivot hubs, antenna guide bosses -- prints front-down with NO ceiling). Panel-to-frame
= 6x M3 axis-Y from the back into frame rim tabs (side tabs clip into the corner mass
via inter() -- at y -66 the side walls are all corner_r curve); halves still join via
the top-wall flange (frames, 2x M3 axis-X) + tongue/groove (panels), `head_bezel` -> `_L/_R` at x=+22
(staggered vs the back seam = brickwork interlock; per face strip one M3 + one Ø4
dowel in pads behind the face, clear of the camera bosses), `chassis_lower` ->
`_front` / `_rear` / `_tail` at y=+26 and y=-88 (floor pads: M3x12 axis-Y + Ø4 dowel
per seam; the deck screws and one-piece pod rails also bridge). The 2026-07-13 rear
sub-split (`lower_seam2_y`, user: faster/easier main-housing print) peels the
FEATURE-DENSE rear end (rear wall + both prow cheeks + M8 nut ducts + rear
obstacle/buzzer/USB) into the small bolt-on `chassis_lower_tail`, leaving
`chassis_lower_rear` a clean 140x114 tub (208->119 cm3, 172->114 mm) that prints
support-light; the tail is 140x58. Its seam fasteners go CENTRAL (x 25, not the
wall band 61) because the left wall corner is owned by the SW-420 pad; a `_despeck`
pass drops the sub-0.5 cm3 fragment the seam shears off the wire-pass edge.
`chassis_lower_tail` aliases to `chassis_lower` in both gate SPLIT_ALIAS maps
(inherits every whitelist), auto-groups under the viewer HULL, and the M8-nut-channel
invariant now probes the tail. `chassis_deck` -> `_front/_center/
_rear` at y 66 / -52 (half-laps + 2x vertical M3 per seam; the pan seat stays
monolithic in the center, which gets its OWN 4 hold-downs at (+-64, 8)/(+-64, -26)).
`head_door` kept whole but the solid tier legs got lightening pockets (-19 cm3). Gate
whitelists alias split pieces to their parent (SPLIT_ALIAS in assembly_check/fitmap);
sibling seam contact is designed. The viewer parts panel is grouped BY OBJECT with
collapsible per-group toggle-alls.

- Printed set (exports via `EXPORT=1`): `chassis_lower` (`_front/_rear/_tail`), `chassis_side_{L,R}_{front,rear}`,
  `chassis_base`, `chassis_deck`, `belly_plate`, `track_L/R`,
  `drivewheels_L/R` (as track_wheels_*), `track_keeper_L/R` (pod_rail_L/R DELETED
  2026-07-14, beam integral to the side panels), `neck_clevis`, `tilt_carrier`, `pan_platform`, `pan_race`,
  `pan_clips`, `pan_cage`, `head_bezel`, `head_back`, `head_door`, `screen_tray`,
  `cam_cover`, `sd_plug`, plus the real generated `worm_wheel`/`tilt_worm` (docs/WORM.md).
  `pan_balls`/`motor_*`/`drive_*` are bought-part placeholders. track_L/R (links +
  wheels), track_keeper_* (2 bars) and pan_clips (3 clips) are multi-body by design.
- **HORIZONTAL screw holes print as TEARDROPS (`geo.teardrop`, 2026-07-13 DFAM):** a bore
  whose axis is parallel to the bed (e.g. the seam-join M3 through-hole + head counterbore
  in the lower-tub floor pads, printed seam-up) has a hanging roof that sags/needs support.
  `teardrop(r, length, axis, up="z")` = `cyl` + a 45deg pointed cap so the roof is
  self-supporting (no support material, no sag). The `_seam_join` screws + counterbores use
  it (both lower seams); a large counterbore whose apex clears the part top just opens into a
  small self-supporting slot (flat-roof teardrop). Round dowels stay round (small, they bridge,
  and want full grip). Reuse `teardrop` for any new horizontal head recess; keep vertical /
  open-up bores as plain `cyl` (already self-supporting). Verified: 45deg roof probe + 20/20
  plates slice clean.
- **Fastening = M3 into CAPTIVE HEX NUTS on serviced seams, Ø2.5 THREAD-FORM pilots on
  assemble-once joints** (M2 for the camera / master-link keepers). `screw_post`/`hex_prism`.
  Thread-form (2026-07-08): chassis deck split (4x M3 from above), pod rails (M3×12 from the
  cavity), tilt_carrier's 4 M3×16, belly tray posts, pan-motor ears, pan clips, belly plate. Captive nuts kept: bezel↔back,
  TT gearbox ("nut in the gap"), arm shoulders. Head door is SCREWLESS (2026-07-10):
  top hooks + per-leg snap tongues, see the head_door note above.
  - bezel↔back: 8 perimeter posts (stage 3a: bottom + top centers each became a ±40 pair), nut
    captive in the back boss, screw from the front. M3×35 ×8.
  - screen+Pi module: `screen_tray` (2 rails + spine, prints plate-face down): 4× M3×10 bench
    screws into the display's factory bosses (126.2×65.65, faces on the boss rear plane) +
    4× M3×10 from outside the back wall into the tray pillar pilots. No bezel bosses; no
    separate Pi mount (the Pi rides the display's own 58×49 standoffs).
  - camera: 4× M2 bosses at 21×12.5; `cam_cover` traps the board (2× M2 + ribbon pinch).
  - neck↔pan_platform: 3× M3 on r16 at (270°, 30°, 150°) about `(0, neck_y)` (stage 5 re-clock;
    the old r12/90° layout put a hole inside the D-bore hub).
  - pan motor: floor pad in the base, D-hub coupling; tilt motor: bracket + gusset off the neck.
- **Tilt bearings:** 695-2RS pressed into the neck cheeks (not the head); head clamps the axle ends.
- **Electronics fittings:** base has a pan-motor pad + ULN2003 standoffs + a USB-C wall slot +
  8 vent slots; head back cover has a Pi I/O slot + ventilation louvres + the cable port.
- **Per-part print orientation:** `chassis_lower` (`_front/_rear/_tail`) seam-up/open-top, `chassis_deck` top-face-down,
  bezel face-down (aperture opens up, best cosmetic face), back
  open-side-down, neck on its back, base flange-down.
- **Still a refinement:** explicit 45° self-supporting chamfers on the largest back openings
  (I/O slot ~64mm), the offset-shaft coupler part, a second ULN mount for the tilt driver, and the
  pan-joint slip ring (a purchased capsule, model its seat once you buy one). Screen standoffs wait
  on measuring the display's real mount holes from the reference STEP.

## Layout

```
src/build.py     ASSEMBLY ENTRY (2026-07-10 split, was a 3.4k-line monolith): build() poses and
                 collects every part into the GLB, writes the pose sidecar, runs FITS.
src/params.py    the PARAMS dict `P` (every value carries its reason), TAU/DEG, EXPORT flag.
src/geo.py       shared geometry utilities: box/cyl/rounded_box, booleans, screw/socket
                 helpers, dbore, frustum, COLORS + _color.
src/gears.py     worm-drive helpers: generated-teeth STL loading, placeholder gear/worm, worm_cd.
src/screen.py    combined touchscreen+Pi reference mesh loading + screen_pose().
src/head.py      head shell/bezel/back/door(pod), screen tray, camera pod, styling parts, arms.
src/neck.py      neck clevis + tilt-motor cartridge carrier.
src/pan.py       pan platform, BB race, clips, _pan_stack.
src/chassis.py   chassis core/lower/deck/side-panel split, belly plate, fascia.
src/tracks.py    raised tank loop, links, master link, sprocket, road wheels.
src/motors.py    TT gearmotor + 28BYJ placeholder meshes.
src/refparts.py  downloaded REAL bought meshes (reference/electronics/) posed onto the
                 placeholder OBBs; default ON (PLACEHOLDER_PARTS=1 restores boxes).
src/fitmap.py    the FITS=1 clearance/press report + contact audit.
                 Import DAG: params <- geo <- gears/screen/motors <- tracks/pan/neck/head/
                 chassis <- build (fitmap standalone; no cycles -- params imports nothing local).
src/stlpaths.py  routes stlp("track_L.stl") -> stl/base/... ; subsystems: base / neck / head
src/serve.py     localhost viewer server (serves web/ at root)
src/shoot.py     headless multi-angle renders -> .claude/renders/
web/             viewer_glb.html + assembly.glb (committed so a fresh clone shows the assembly)
web/docs/        rendered doc pages (make docs; committed so Pages ships them)
tools/build_docs.py  the md->html docs pipeline + shared top-nav generator
stl/{base,neck,head}/   per-part STLs (head_bezel + head_back), written by `EXPORT=1 python3 src/build.py`
exports/         Bambu .3mf plates (regenerable, gitignored)
reference/       rpi-7in-touchscreen-model (STEP/STL, the real screen) + -case + alexa-style-* +
                 tank-track-3062624 (link/sprocket geometry, CC-BY) + rpi-camera-v21-1564160 +
                 design/ (5 concept renders = the STYLING TARGET: black+orange rugged two-tone,
                 gripper arms, camera+LED strip+antenna in the head top bezel, front grille +
                 ultrasonic pods, big exposed sprocket-gears; 1008×1024, safe to Read)
docs/FIXES.md    the verified-defect ledger from the 3-agent review + fix-stage status
docs/ASSEMBLY.md BOM + assembly order
```

## Gotchas

- **`TAU` (src/params.py) is `2*np.pi` (a full turn).** It was once wrongly set to `np.pi`, which made
  `R(TAU/2)` a 90° rotation, that silently laid the LCD on its back (the "screen position wrong"
  bug) and half-rotated the tilt motor and vents. If you touch `TAU`, keep it `2π` and remember
  `cyl(axis="x"/"y")` relies on `R(TAU/4)` = 90°.
- The screen STL loads as X=width, Y=depth, Z=height (correct, upright). `screen_flip=True` applies a
  180° YAW (about Z) to face the glass +Y. `screen_pose()` = optional face lean + translate to the
  front face; `tilt_cantilever` sets how far forward (keep glass ~flush with `body_front_y`).
- `python3` here is **3.9**; `build123d` needs ≥3.10. This uses the **trimesh + shapely + manifold**
  path (works on 3.9). Move to build123d in a venv when we want native fillets/chamfers.
- serve.py serves `web/` at root: the model URL is `/assembly.glb`. Passing `web/assembly.glb` to
  shoot.py 404s.
- The viewer **ghosts** housing-like parts by name (anything with shell/body/housing/case/lid),
  that's why `head_shell` renders as a translucent outline. Toggle **solid** in the viewer to see it
  filled. `shoot.py` can't toggle it, so to render the shell solid, rename it in a temp scene.
- Screen STL axes already match ours (X=W, Y=D, Z=H); no swap needed, just recenter + `screen_pose()`.
- `EXPORT=1 python3 src/build.py` writes the per-part STLs; the plain run only refreshes the GLB.
- Reference `.123dx` files are Autodesk 123D (not usable); use the `.stl`/`.step` siblings.
- **three.js STRIPS `.` from GLB node names at load** (PropertyBinding sanitization: `. : / [ ]`),
  so `o.name` gives `track_Llink_01`, not `track_L.link_01`. The viewer recovers the exact GLB
  names via `gltf.parser.associations` + `parser.json.nodes` (GLTFLoader callback) -- without
  that, every dotted granular child misses its nav category, its 3rd-level nesting AND the
  fit-map prefix resolution (this silently dumped 128 parts into "Misc" until 2026-07-14).
- **Viewer nav coverage is GATED (2026-07-14, user: nothing may land uncategorized):** checks.py
  parses the TREE regexes straight out of viewer_glb.html and fails `make invariants` if any GLB
  node matches none -- a new part needs its TREE entry the same turn it enters the scene. The
  viewer also has UNDO/REDO (floating top-right ↶↷ toolbar with an n/N depth counter,
  ⌘Z / ⇧⌘Z / Ctrl+Y) over one debounced history of part visibility + sliders + toggles
  (camera orbit and tree collapse deliberately untracked). Selection: click = single,
  ⇧/⌘-click = multi-set; the navigator auto-opens every ancestor group and centers the
  row; H/I/F hotkeys + the right-click menu act on the whole selection.

**Trim + rear-sensor pass (2026-07-11, user rounds 4-5):** the REAR wall is now a TWIN
of the front: the same grille ring (grille_* params) frames a rear obstacle HC-SR04
(`sensor_us_rear`, board on the inner wall face, barrels through Ø16.6 wall bores at
us_cz 32) so each end has obstacle + cliff sensing; the squashed 72x18 hatch frame and
the front fin/web stubs were DELETED (vestigial on the 28-tall band; the slope hex
fields carry the vent look), fascia/rear pins re-clocked into the ring bands
(fascia_pin_pts / rear_pin_pts). The USB-C entry + PD pilots moved x 0 -> -38 (the
barrels own the wall center; slot sits 1.0 off the ring band, below the deck-split
bosses, above the belly power tray). TRACK STRETCH same day (user: "track too short"):
52 links / ground run +-90 / wheelbase 196.326 (see the kinematic notes), road wheels
6 -> 7 at pitch 23 (stations clear the pod-join dowels at +-40), wheel beams to
+-74.5. EARS (ordered): 2x 3.5 mm gooseneck mics, one per head side -- panel-mount
jack pods on the head side walls are a pending head.py pass (see memory ear-mics).

**Round-6 pass (2026-07-11):** (1) DECK TIP TRUNCATION: the slope/top intersection was
a 33.7 deg acute PLA knife edge (user: "chassis angle too sharp") -- the slab now ends
at |y| 144 with a vertical 4-tall nose face (`deck_tip_trunc`; slope angle and the
cliff-sensor geometry unchanged). (2) VISIBLE AXLE HARDWARE `axle_hw_L/R` (user: "drive
wheels not properly connected" -- the connections were unmodeled hardware): per side,
7x M4x40 bolt-axle placeholders (shank through beam bore + wheel, hex head on the hub
face -- head seat whitelisted in the fit audit) + the Ø8 idler stub (x 83.5..118,
riding the tension-slot passage). Silver, export=None, never printed. (3) EAR MICS
MODELED, v2 same day (user: "only the tip of the microphone is supposed to be out"):
the gooseneck mic lives INSIDE the head -- plug into the CM108 adapter at the Pi, the
flexible neck up the rear bay -- and just the Ø17 foam windscreen pokes through a Ø15
grommet bore in each side wall (compress-fit; a Ø19/Ø15 x 3 proud ring dresses it as
the ear). PARAMS ear_y=-10/ear_z=214, above the trim rails, both in head_back, clear
of the screen top (208.4) and antenna half-shafts (207). `ear_mic_L/R` placeholders =
foam tip (12 proud) + inboard neck stub. NO panel jacks needed (v1's wall-jack design
retired before printing); mics + CM108 adapters already ordered.

**Mid-drive + centered ears (2026-07-11, user rounds 7-8):** tracks now end +-153.5
(~1 cm past the 144 deck tips, chosen over the 130 option) via the MID-DRIVE rework
described in the kinematic notes above; the wheel row is an explicit station list
(roadwheel_ys, 6 wheels + the sprocket at -68 doubling as the 7th support), the
side vents re-clocked to (-112,-96,16..96), the old wall-mounted idler tensioner is
DELETED (deck pylons own tension), and the end stubs press their pylon sockets
(whitelisted). The pod-rail wheel beam grew to +-86 with a Ø13.5 notch where the
sprocket hub crosses it. EARS moved to the head sides' vertical center: (y -40,
z 157) -- y -40 is the derived clear column (trim rails y +-13, Ø26 tilt clamp
tubes to y -31, Ø20 pivot bosses, wall flat ends y -54). BOM: F688ZZ 4 -> 8 (two
per end idler x4), M4x40 12, hinge pins 128 (-> 10 since the 2026-07-12 PIP
strips), Ø8 stubs x4 ~50 mm (M8 bolts work).
PRINT NOTE (2026-07-12, third revision -- PRINT-IN-PLACE STRIPS): the chain now
prints as 4 strips of (16,16,16,15) links per side + 1 separate master, hinges
already assembled. History: standing pose sliced clean but TOPPLED on the printer;
grouser-down + tree printed but scarred and left 126 loose links to hand-pin. Now
every knuckle band carries a 45-deg KEEL (chamfered buttress, knuckle cylinder down
to the grouser plane, outer-face side only -- the sprocket channel +-4.9 and the
wheel-rolling inner faces stay untouched; keels double as traction teeth), so
GROUSER-DOWN is fully self-supporting: strips print SUPPORT OFF, 5 mm brim, flat
~167x44.8x9.5 rows (167+10 brim fits the 180 bed; 16 is the cap). Each link's own
(y0) pin is an INTEGRAL Ø2.0 rod (PARAMS track_pin_print_d) fused into its A
knuckles -- the sprocket drives on it -- and the far B bores are Ø2.7 (track_
bore_pip_d, 0.35 PIP radial gap); strip-first links revert to open Ø2.2 A-bores
(no pin) and strip-last links to Ø2.2 far bores for the Ø1.75 filament boundary
pins: per side 59 printed joints + 3 strip filament joints + the master closure
(master far pin + jaw pin) = 10 loose pins total (was 128). Strips are exported
as ONE CONCATENATED mesh each (never boolean-union -- it would weld the hinge
gaps; the exporter asserts 16/15 bodies per strip); the assembly keeps 64
per-link scene nodes with the correct variant per position, and the baked
sprockets are conjugate-phase CLOCKED to the pin grid (spr_y -68 = -5.93 deg,
disc-only rotation so the D-socket stays on the shaft flats). Sprocket envelope
regenerated for the Ø2.0 pin (r 1.275): probe (tools/probe_track_pip.py) --
conjugate penetration -0.152 (clearance), numeric skip barrier 2.12 (analytic
2.18), CR 1.37 unchanged, +-35 deg articulation sweep of every variant pair
CLEAN (min approach 0.349 = the PIP annulus), 3D tooth-vs-keeled-link sweep 0
overlap (tooth band +-4.0 vs keel band 4.9). TENSION TRAVEL (2026-07-13, closed
the old SLACK CAVEAT): the front idler slot is a true stadium, -2..+6.5 off
nominal (the old cut gave the Ø8 shank only ~+-0.2 -- the documented "+-2"
never existed). dL/d(idler_y) = 1 + cos(33 deg) = 1.84 on this raised loop, so
the predicted +8 mm PIP slack needs 4.3 mm; 6.5 = 1.5x margin. Front pylons run
y 120.5..142.5; tub_nose 20->26 (cheek noses 146, 2 past the deck tips). The
FRONT M8 nut is captured FLATS +-Z in a closed cheek DUCT (floor ledge z 27.62
+ chamfered roof strip z 41.02, gap 13.4 = AF 13+0.4) -- y-wall grip is
geometrically impossible over slide travel -- inserted via the panel-tower notch
BEFORE the deck drops (slide inboard along x through the washer slice); the M8
threads in axially after track closure. Rear cheeks keep the drop-in y-wall
channel. Full first-chain elongation is ~21.8 mm: tension only to mesh, the
rest is designed top-run sag (the wheel beam caps run lift at 4.5). COUPON:
print plate 20 (5-link PIP strip + master + keepers, ~48 min) before any strip
plate; protocol in docs/ASSEMBLY.md. MASTER links stay grouser-up NOSUP
(C-jaw removes the floating region) and keep the full old Ø2.2 interface (a
closed far bore can't slide onto a fused pin) + keels (jaw slots re-cut through
them). Track gear plate: running-gear bodies are ORIENTATION-NORMALIZED
after the shared R(Y,90) (mirrored L STLs landed sprockets DISC-UP with a ~1050 mm2
tree forest over the teeth; flip when >45deg overhang above z10 exceeds 200 mm2) and
sprockets/idlers print SUPPORT-OFF (their only ceilings are 1-2 mm annular bore
steps that bridge; tree pillars would scar the F688 flange seats + D-socket).
Keepers roll onto their wide face. ALL 19 PLATES (strips consolidated the 5 link
plates into 3: 2x four-strip plates ~6.8 h each + masters) slice 'Success.'
(track plates 15-19 re-checked after the strip pass, strips SUPPORT OFF);
`make slicecheck` (tools/slice_check.py) is the
permanent gate -- run it after every export change. It catches the SLICER-visible
class only; physical stability of tall/thin plating still needs a human look.

**Drive-mechanism review (2026-07-11, task #11):** the wheel beam doubles as the
ANTI-BUCKLE CAP for the mid-drive: the pushed side of the ground run (rear of the
active sprocket when driving forward) can only lift 4.5 mm (crowns z 9.5 -> beam
bottom z 14) before the beam stops it, and beyond +-86 the ramps are held by the
tensioned end idlers. Run the tracks TENSIONED (the front M8 nuts) -- tension is
what prevents bunching in the first place. Stall-torque tooth force ~4.1 N lands on
~1 pin (the straight-run mesh engages one pocket; neighbours sit 2.5 above their
pins), giving ~19 MPa pin bending = 2.6x margin on PETG. The sprocket takes ~1/7 of
the robot's weight through the mesh, which preloads engagement closed.

**Front tension retention review (2026-07-16):** the PLA sawtooth ladder under
the front M8 NYLOC is deleted because desk heat and sustained clamp load can crush
the teeth and restore friction-only creep. The preferred vertical M3 backstop ladder
does not fit: Ø3.4 bores at roughly 1.6 pitch overlap and erase the -Y bearing walls,
and the x62..70 tower cannot stagger 6.35-across-corners M3 nut seats. The fallback
is a face-loaded 12x28x1.0 steel strip, flush in the x62 bearing face with both ends
captured by full PLA shoulders. It spreads creep load but is not a positive positional
lock. Inspect front track tension during early service and re-tension if needed.

**End-axle + dual-drive pass (2026-07-11, user rounds 9-10):** (1) M8 END BOLT-AXLES
(user: "two wheels per side not connected to anything" -- the plain Ø8 stubs had no
axial retention and the idlers showed bare bearing bores outside): each end wheel now
rides an M8 bolt, head outboard as the hubcap, shank through the F688 pair and the
pylon-era geometry, NUT on the tower's inboard face; on the FRONT towers the nut clamps the through
tension slot = the tensioner (M3 set screws deleted; rear press sockets became Ø8.4
through holes). (2) SECOND DRIVE STATION per side at spr_y2=+90 (user: "two motors on
each side, second optional but all fittings ready"): the whole TT feature set loops
over both stations with mirrored y-offsets (the front TT flips about its shaft --
gearbox trails -y; tab/rib at ys2+14..15, nub 79, M3s 69.7); sprocket 2 rides the
OPTIONAL motor's own shaft (drive2_L/R placeholders modeled; without motors the
station is empty and the end idler + 57.5 wheel carry the front run). Knock-ons:
road wheels 6 -> 5 stations (57.5, +-33.5, +-11.5; both sprockets get 28.8+ axle
gaps), beam gets a second hub notch, the y80 vent left the row for the front nub,
and ULN2 moved (-38,45) -> (0,80) -- its posts sat inside the flipped TT_L envelope
and the pedestal blocks every left-side alternative. BOM: 4x M8x70 + jam nuts + NYLOC nuts
(SETTLED 2026-07-13: Bag 13 "Machine Bolts" is 30PCS M3-30, no M8 -- buy), M4x40
12 -> 10, TT motors: 2 required + 2 OPTIONAL for twin drive (own 3 per the
2026-07-13 re-audit; buy 1 only for the 4th).

**Granular scene nodes (2026-07-11, user: "select every little component"):** multi-body
parts now emit DOTTED CHILD nodes into the GLB -- `track_L.link_00_master`,
`drivewheels_R.sprocket_front`, `axle_hw_L.end_bolt_rear`, `track_keeper_L.bar_1` (224
scene parts) -- so the viewer can toggle each link/wheel/fastener. CONVENTION: the gates
(assembly_check + fitmap) re-group by the prefix before the first `.` and stay at 67
part-level nodes with unchanged whitelists; the print export gets one multi-body ghost
mesh per parent (`metadata scene=False`, export-only; build.py's add() skips it from the
scene). The viewer nests dotted children as a collapsed 3rd tree level under their
parent, and fit-map pair names (parent-level) resolve to children by prefix. When adding
new multi-body parts, follow tracks.py's `emit()` pattern.

**Prow cheeks (2026-07-11, user: "drive axle blocking the front and rear view LEDs...
chassis a bit longer from both side so the axle shaft of the last wheel will be hidden
inside"):** four tub blocks (x |32..70|, clear of the +-30 trim rings) extend the lower
hull tub_nose=20 past each wall (noses at y +-140, tracks still 14 proud at +-154). Each
swallows its M8 end-axle NUT in an open-top NUT CHANNEL (x 47..60, y-walls 13.8 apart
centered on the axle -- the descending nut, hex FLATS to +-y, self-captures against the
walls, so the FRONT tension axles snug from the outboard head with zero tool access; a
wider washer slice x 60..63.5 takes the Ø14.4 washer; 3.0 front skin; spec M8 NYLOC;
the hw placeholder models the true hex, flats to +-y), notches around the deck
pylon (x 61..70.5, 1.0 clear), continues the 33 deg glacis (+20 shift), and caps FLAT at
the z 46 seam (wholly in chassis_lower; the wedge up to the deck slope stays an open
shadow line like the pylon bay). The CENTER fascia band stays recessed at y 120: the
cliff cone crosses z 46 at y ~131 (ray-probed, 0 hits) so a full-width nose would ping
itself. Amber lamps moved to the cheek noses (lamp_cz 26->23, wire drill under the
pocket floor), rear buzzer pod to x 41 on its cheek (Ø10 bore 1.0 clear of the pocket),
USB-C entry became a recessed corridor through the rear-left cheek. Viewer: the parts
panel is now "Navigation", 400px default, drag-resizable (native resize grip,
localStorage-persisted width), solid + fit-map-off defaults.

**Head pass (2026-07-11, user rounds: LCD gap / camera pod / ears):** (1) LCD SEATED
WATERTIGHT: body_front_y 31 -> 33 -- the glass used to be FLUSH with the face plane so
the module pocket pierced it (a see-through slot ringed the glass). The face now stands
2.0 proud, the pocket stops 0.11 over the glass (locator only, bezel bosses still
forbidden), the window keeps the real 3.5 bezel_overlap lip, and the pocket is STEPPED
(full width only for the 2 mm glass band; |x| 86.6 behind it) with a y 28.3 shelf that
seals the old side slots. (2) CAMERA POD ABOVE THE SCREEN in a taller forehead:
cam_lens_z 212 -> 226, body_z_top 226 -> 242; the CM3 board (211.6..235.5) clears the
screen pocket top 208.9 by 2.7; led_cz 226, campod pins (+-8, 230), ant masts to 242.5,
head_back top-flange now parametric (body_z_top - 7.5). Overall bbox H 261 -> 277.
(3) EARS at the human spot: ear_y -40 -> -29 (60% back of the 103 head depth), ear_z
157 -> 172.5 (vertical center 165 blocked by the Ø26 tilt clamp boss at z 153 -- bore
kept 1.9 clear above it); the gooseneck stub angles (93,-29) -> (71.5,-12) around the
antenna mast and tray pillars.

**Sprocket conjugate teeth (2026-07-11, review task #15 verdict DEFECT -> fixed):** the
old _sprocket_disc had pin pockets but NO teeth (tip r 18.8 UNDER the 19.32 pin circle):
1-pin bite, a 35% per-pitch dead gap bridged only by ~2.4 N rim friction (loaded starts
could deadlock + freewheel), end-of-stroke cam-out at stall, and a 0.355 skip barrier
that FDM tolerance could eat -- with no mesh-depth adjuster anywhere (tension is
horizontal, mesh depth vertical). Now `_sprocket_profile()` generates the true
rack-conjugate roller-pinion form (pin+0.275 swept envelope, 0.5 deg steps, 12x): tip r
20.5, contact ratio 1.37 (a pin is ALWAYS caged, min escape lift 0.914), zero-lift
conjugate action (max penetration -0.15 = clearance), tooth tips 0.62 above the link
web (ceiling: tip r 20.72), skip barrier 2.055 (5.8x; FDM +-0.2 is now 10% of it).
Dual-run engagement was evaluated and rejected (top run 8.6 clear by design: needs
interior exactly 2 x tip r + dual phase match; top is the slack side). spr_y2 90->87
half-pitch stagger REJECTED: fouls the y-64 vent + ULN1 post line, and moot at CR 1.37.
Sprocket-to-road-wheel edge gap is now 2.0 (intra-part, gate-blind): keep center gaps
>= 30.5 when re-stationing.

**Parviz awareness architecture (2026-07-12, user):** the robot is named **Parviz**.
Design intent in `docs/AWARENESS.md`: always-on ambient awareness, 2 ear mics, camera
(AI-camera upgrade open), BME688-class env sensor, capacitive touch, IMU, vibration,
mmWave presence, 4x HC-SR04, fused into a world-state digest that is fed to an LLM
deciding what Parviz does. Tiered: reflexes hard-coded; perception + ASR always LOCAL
(raw audio never leaves the robot); ambient decisions by the local ~0.6B model
(llama.cpp on the Pi, benchmarked in software/README.md: Qwen3-0.6B Q4_0 = 21 tok/s,
0.94 s replies, coexists with the face; 1.7B fits only alone); bigger AI (Claude API /
Mac) ONLY for specific tasks or on user request. RAM (2GB) is the binding constraint.
Software side: face v2 (rigid orange eyes, touch-tracking pupils) runs as
`parviz-face.service` on boot (console target, kmsdrm; desktop disabled).

**Neck styling pass (2026-07-12, design-ref):** the neck region now matches the ref's
dark-mechanism read. (1) RECOLOR: COLORS neck/pan -> matte charcoal / near-black (the
bright-steel column + platform disc read as raw CAD); viewer PAL split so worm gear
metal stays silver ([/worm|wheel/] before the neck rule) and neck|clevis|fork|carrier
went matte; keep COLORS<->PAL in sync as ever. (2) `trim_neckfoot` (NEW printed part,
orange accent, PAN group): a stepped chamfer-look pedestal collar at the column foot,
64x54 x 3 tall on the platform, arc-trimmed to r 44.3 about the pan axis (platform
solid top ends at the r45 rebate, clip tabs flush at r45.4). Top z 69.0 = exactly where
the chin notch starts; PROBED ceiling: the tilt-swept head bottom dips to z 70.6 right
around the column (and to ~70 over nearly the whole deck, which is why no tall fixed
turret plinth or under-head shroud is possible -- the sweep owns everything above
~z 70; the slot interior is owned by the cheek stall rake to y -86.9). Fixing: slip
over the column FROM BELOW BEFORE the neck bolts to the platform (cheeks at x +-26
block a top-down pass), then 2x Ø3x6 pins through the collar into blind platform
sockets at (+-27, neck_y) + glue. Prints flat, no support. (3) Column PANEL-LINE
grooves (1.2 deep, x +-24 faces, z 74/82, y -38..-21 -- above z 69 the chin notch
voids y > -19.5, so the lines live on the rear half and die into the corner round).
Gates: check + check-sweep (14 poses) + fits contact audit all green; trim_neckfoot
added to PAN_NODES (assembly_check), _FIT_CONTACT_OK (vs pan_platform/neck_clevis),
the viewer Pan-stage tree and stlpaths -> stl/neck/.

**Fast pan/tilt pass (2026-07-12, user: "both tilt and panning should happen really
fast -- use gears"):** the 28BYJ is POWER-limited (~0.035 W usable; ~34 mNm at <=10 RPM
falling to ~20 at 15 RPM, max reliable ~15 RPM), so gearing buys PEAK slew, not sweep
time. (1) PAN = 2:1 spur GEAR-UP (PARAMS pan_gear_*): the on-axis D-hub is GONE -- the
motor dropped ~13.5 and swung off-axis (shaft at (-19.2,0) = CD 19.2 at pan_shaft_azim
180, can at (-19.2,+7.875), clocked -90 so ears run along X, wbox exits +Y, D-flats
+-X), a 32T m0.8 gear on its flats (`pan_gears`, new fixed part, placeholder teeth)
drives a 16T pinion now INTEGRAL to the pan_platform underside; both live in the z
45..50 band under the seat floor 51, whole cluster reach r33 < race ID 34 (ring seat
annulus untouched; the deck got a r14.5 gear pocket in the under-seat membrane, and
the pedestal followed the can -- belly_keep x0 -34 -> -44 keeps it off the removable
plug, 2.4 clear of the drive_L can). Peak slew 90 -> ~180 deg/s (motor 15 RPM x 2),
accel ~250-300 deg/s^2 (15 mNm at the platform vs ~7 race friction + I~0.0024 kg m^2);
a 180-deg sweep still takes ~2 s (power limit). 3:1 rejected (10 mNm barely beats
friction), 6.25:1 antenna ratio stalls outright. Homing lug/posts unchanged; steps/deg
HALVES to ~5.7. (2) TILT = 3-START worm (PARAMS worm_starts): ratio 12:1 -> 4:1, same
pitch r 4.4 / CD 11.9 / cartridge -- ONLY the thread count changed. 7.5 -> 22.5 deg/s
(60-deg sweep 8 s -> 2.7 s), margin 1.3x at speed / 1.9x at 15 deg/s vs ~25 mNm
residual imbalance. Spur-only 2:1 direct drive (45 deg/s) FAILED placement (motor
shaft must turn onto X: can collides with cheeks/root block/stop posts everywhere
probed) and a spur+3-start combo fails torque (0.6x). **TRADEOFF: single-start
self-locking is LOST -- a 3-start (lead ~23 deg) back-drives, so de-energized the head
holds only via the 28BYJ detent+gear friction through 4:1 (~27-54 mNm at the axle,
marginal vs imbalance): firmware must energize-hold or park at the balance point,
and a power-off head may slowly nod.** REAL TEETH SINCE 2026-07-13: the 3-start worm
pair (lead angle 23.08 deg, wheel helix matched) and the 32T/16T pan spurs (m0.8,
PA20, CD 19.2, backlash 0.20) are generated + committed (docs/WORM.md regeneration
record; coupled sweeps 0.000 mm3 penetration, worm clocking constant 24.5 -> 17.75,
pan mesh phase 5.625 deg). The placeholder fallback trigger is now a META-SIDECAR
HONESTY GATE (stl/neck/worm_real_meta.json + pan_gears_real_meta.json vs PARAMS in
src/gears.py), not worm_starts != 1 -- param changes can't silently ship stale teeth.
Gates re-whitelisted: (pan_gears, motor_pan)+(pan_gears, pan_platform) replaced
(pan_platform, motor_pan); viewer PAL silver rule grew |gears.

**Tilt holding (decision, 2026-07-13):** with self-locking gone, the rule is FIRMWARE
HOLD: energize the tilt coils whenever the head sits off its balance point, and PARK AT
THE BALANCE POINT before any long idle or power-down (there the worm is unloaded and
28BYJ detent + gear friction suffice; elsewhere a powered-off head may slowly nod). A
mechanical neutral detent (spring ball on the wheel hub) is a possible future addition,
deliberately NOT modeled now -- prove the need on the physical head first. Upside of
the trade: the back-drivable mesh makes worm-cartridge extraction unconditional (see
the tilt bullet above).

**Arduino I/O plane (2026-07-12, user):** most elec components (sonars, IMU, BME688,
mmWave, touch, vibration, LEDs, possibly motors) wire to an ARDUINO dev board, which
connects to the Pi 5 over ONE USB cable (serial telemetry/commands + flashing). Camera/
mics/display stay on the Pi. With arduino-cli on the Pi, the AI tier can WRITE, COMPILE
and FLASH the Arduino firmware on the fly over that same cable. Firmware is an
LLM-modifiable artifact (repo: firmware/arduino/ when it lands). Reflexes (cliff-stop)
can live in-firmware below the Pi. Full rationale: docs/AWARENESS.md "Arduino I/O
plane". Board = Uno R3 (owned x3, Bag 6); motor placement still open.

**HULL / EQUIPMENT-BASE split (2026-07-14, user: separate the shell by STABILITY so
the in-flux components iterate without reprinting the finalized hull).** The free
electronics -- Arduino Uno + IMU + SW-420 -- MOVED off the hull floor onto a removable
`chassis_base`: a flat plate that drops into the rear electronics bay (behind the belly
opening y<-61 and the pan pedestal y>-16), sits on the hull floor at z12 (seat plane
z15), bolts down with 4x M3 into hull-floor pilots, and SPANS the y=-88 seam so it ties
the rear+tail shells (that seam lost its pads). The boards were RE-LAID-OUT to fit the
bay cleanly (Arduino shifted 2 back off the belly edge; IMU/SW-420 in the x<=+-49 side
strips, clear of the TT tab ribs at x>=52). The base is built inside build_chassis_parts
and RELIEVED against the hull (`sub(base, uni(lower_f/r/tail))` + _despeck) so it gets
clearance pockets for every dense floor feature it spans -- a robust drop-in that can't
silently clash. STAYED in the hull (structural or shell-integral, NOT in-flux): the pan
pedestal (pan-axis critical), the HC-SR04/cliff/mmWave/US bores + BME bosses (all
air/hole-coupled to the wall/slope skins), the deck bosses, and the y=26 seam. Gates:
chassis_base in export_bambu Chassis plates, assembly_check WHITELIST + fitmap
_FIT_CONTACT_OK (base<->hull rest, sensor<->base seats), an invariant, and the viewer
Hull group (chassis_ regex). All green: interference PASS, 35/35 invariants, wallcheck
PASS, 20/20 plates slice clean, fits 55 pairs all expected. To iterate the electronics
layout, edit build_chassis_base + the *_c PARAMS and reprint ONLY chassis_base.

**DESIGN RULE: SEPARATE BY STABILITY (baseline, applies to every future part):**
partition every enclosure/chassis/head volume by CHANGE FREQUENCY before modeling.
Frozen shells (structural + cosmetic, slow prints) stay CLEAN: no screw pockets or
bosses for any component marked VERIFY_ON_ARRIVAL or otherwise in flux. All such
mounts go on a removable equipment base/tray that bolts to the shell at a few generic
points, so iterating a mount reprints only a small flat support-free plate. What may
stay fused in a shell: kinematic/structural-critical seats (pan pedestal, bearing
bores) and skin-coupled features (sensor barrels, vents, light pipes). Build bases by
RE-LAYING-OUT the components onto them and RELIEVING against the shell union
(sub + _despeck), never by notching a tray around an existing packed layout. The
2026-07-14 retrofit attempt collided with the belly rebate until the layout moved
onto the base. Same rule applies when the head electronics ever need seats.

**SIDE PANELS = STANDALONE TRACK MODULES (2026-07-14 rounds 2-4, user: separate the
wall bands the rails/motors mount to; delete pod_rail_L/R; extend the sides to the
end bolt-axles so the track system assembles WITHOUT any chassis_lower_* piece).**
The lower tub's side walls are now four bolt-in panels `chassis_side_{L,R}_{front,
rear}` (~33-42 cm3 each), CARVED from the tub in build_chassis_parts (band x 64.85..
70 / y -139.2..142.5 / z 12..46 + full-depth captures for the TT tab ribs, the 6 deck
hold-down bosses at x +-64, the BME688 bosses, and the cavity-corner crescents -- an
x-only cut would slice the corner rounds lengthwise into feather fins, wallcheck
catches it). Each panel carries EVERYTHING in-flux on that wall: TT stations (shaft
Ø8 + Ø17 hub recess + M3s + nub pockets + tab ribs), side vents, BME bosses (L), and
an INTEGRAL L-RETURN replacing the deleted pod rails -- web x 69.5..74 / z 12..26
(links never enter x < 74) + the proven wheel-beam section x 74..80.4 / z 14..26 with
a 45 deg underside chamfer, carrying teardropped Ø4.4 M4 bolt-axle bores (through the
web: the M4x40 shank tip reaches x 71.4), nut slide-up slots (open to z 11.5), and
Ø13.5 sprocket-hub notches + re-cut hub recesses. At the tips, END TOWERS replace the
DELETED deck pylons (same geometry: outer slab x 64.85..70 fused over the captured
cheek skin + chamfered inboard thickening to x 62, 1.0 off the notch wall, hub boss,
FRONT true-stadium tension slot / REAR Ø8.4, axle line z 34.32) -- the M8 nut ducts
STAY in the cheeks (wrench-free with the hull on; wrench-open on the bench), the
x 60..62 washer corridor survives under the chamfer, and the towers now PROP the deck
overhang tips at z 46. The two pieces per side SPLICE at a half-lap in the L-return
(y -21.5..-15.55, front upper / rear lower, tongues start x 70.0 NOT the web root
69.5 -- a 69.5 tongue presses 0.5 into the other piece's wall, fits caught it; 1x
M3x10 at (75.4, -18.5), staggered off the -18.5 wall butt seam): panels + splice +
TT motors + wheels + M8 axles + track = a rigid standalone track pod per side.
Retention on the hull: the deck's 6 existing hold-down screws clamp the panels' boss
tops (chassis_split front pair + deck_center pairs all land in panels now), one L-FOOT
per piece bolts M3x6 into blind floor pilots (feet y 4 / -95.25), the panel bottom
rests on the floor sill (z 12) and the deck rests on its top edge -- load path is
edge bearing, not screws. The y=26 seam pad shrank inboard (x 50..64.7, screw 60.3 /
dowel 54) clear of the panel plane; the pod-join M3/dowel wall fittings and PARAMS
pod_join_*/pod_rail_* are RETIRED; the pod-rail coupon left test_plate_links. Panels
alias to chassis_lower in BOTH gate SPLIT_ALIAS maps + wallcheck PRINTED (which also
gained the missing chassis_lower_tail + chassis_base entries -- their pre-existing
thin spots are whitelisted: tail = the designed 33 deg glacis/floor knife wedge, base
= hull-relief pocket skins). Print UPRIGHT as built (z12 edge + rib feet + foot pads
coplanar on the bed, all TT/axle bores horizontal -- teardropped where new), STRUCT
+ tree for the boss undersides; all four share one Chassis plate. Service: master
link open -> deck off -> 2 foot screws + splice -> the whole side lifts out as a
drive module. Hull knock-ons: chassis_lower_rear is now a floor tray (top z 32),
the tub keeps floor + end walls + cheeks (minus their outer skins) + corner stubs
past |y| 142.8/139.5.

**PAN PEDESTAL + FULL-TRAY BELLY PLATE (2026-07-14 round 5, user: "the neck motor
mount built into chassis_lower_* -- separate it, bolt+nuts to the belly plate;
bigger belly plate containing many parts").** The pan-motor pedestal left the hull:
`chassis_pedestal` (28 cm3, exact old geometry re-rooted on the plate plug top z 10 --
48x48 body to ear_z 30.75, through O29 can bore, wbox relief, ear pilots, seat pads +
collar, cable-pass corner cut) bolts DOWN to the belly plate with 4x M3x12 csk from
below (flush at z 7, the belly-screw convention) into captive hex nuts in its feet,
located by 2 printed O4 pins (pan-gear CD is position-critical: pins locate, screws
clamp). The belly KEEP STRAP is retired (_belly_polys: full rounded 100x110 opening)
and BOTH ULN2003 driver mounts moved onto the plate (uln1_c (27,20), uln2_c (26,-14)
-- posts z 10..16, board tops where they always were), the REAR TIE + its plate relief
died with the strap, and the plate already carried the power tray + zip anchors +
ballast ribs: DROP THE PLATE = the pan motor + pedestal + both drivers + the power
stage leave as ONE service tray. Hull floor is now just the opening rim (lower_rear =
a 36 cm3 ring). BME moved back 0.45 (bme_cy -97.65: 0.6 to the rib face; 0.15 was
inside the boolean facet-residue margin). Gates: (chassis_pedestal, belly_plate)
pairs + wallcheck/plates/invariants wiring; the derived `_ped_c()` keeps the pedestal
center in lockstep with the pan-gear params.

**CSG ROBUSTNESS (2026-07-14, learned chasing phantom slivers):** trimesh 4.12's
`boolean.*` wrapper INJECTS PHANTOM GEOMETRY on complex meshes (an inter() grew a 0.2
bulge on a rib face neither input had; a compound union grew 150 mm3 inside a capture
window its inputs could not fill). geo.py's uni/sub/inter now call manifold3d
DIRECTLY (f32 Mesh; the f64 Mesh64 path produced its own artifacts on this trimesh/
manifold combo) with a process=False rewrap, and assembly_check's overlap_volume does
the same. RULES: (1) never trimesh.boolean.* -- always geo.uni/sub/inter; (2) never
union many overlapping coplanar volumes in one call -- build capture regions as ONE
shapely 2D unary_union extruded once (`_prism` in build_chassis_parts), and union
added bodies PAIRWISE; (3) trimesh `.contains()` is ray-parity and LIES near
coincident faces -- probe with a manifold-cube intersection instead (the oracle
pattern); (4) design clearances own the last ~0.02 mm3 of facet residue: keep
placeholder-to-part gaps >= 0.3, never 0.15; (5) capture volumes that bottom exactly
on an open face plane leave zero-thickness sheets -- the panels' 1-micron scrub slice
handles it.

**RUNNING-GEAR V2 (2026-07-14 evening, user rounds: bigger sprockets + taller
stance; dual-run engagement CANCELED mid-design; "remove the cosmetic side holes";
simplify the over-complex ends; 0% infill profile).** The mid-drive sprockets are
14T (pin circle 22.4698 = pitch/(2 sin(pi/14)), tip O47.3; tracks._spr_pin_r/_spr_cz
-- the sprocket OUTGREW the end-wrap radius, center z 28.47, and the whole TT
cluster followed it up; road wheels stay loop-keyed at rr_z 19.6). track_raise 13
(interior 51.64 leaves the tip 4.3 CLEAR of the top run -- the sprocket must NOT
touch it), track_wheelbase re-solved 253.5899, end axles +-126.94 / za 38.32,
chassis_clear 10 (floor top 15; the belly opening cut + seam pads + panel bottoms/
feet/L-block all re-keyed; the pan can got a O30 x 1.25 plug pocket -- its z is
pinned by the gear band; fled_cz 15 keeps the LED mid-slope; glacis_z1 21 keeps the
33 deg family). The panel L-return is now a plain RECT block x 69.5..80.4 / z 15..27
(floor top == beam bottom == one flat bed plane; anti-buckle cap 4.5 -> 5.5).
probe_track_pip re-keyed to the sprocket frame: CR 1.37 -> 1.48, skip barrier 2.14,
conjugate penetration -0.187 (clearance), keeled 3D sweep clean; 14T tooth-tip lands
whitelisted in wallcheck (probe-verified). SIDE VENT ROW DELETED (cosmetic) except
the functional y -96 BME window. ENDS SIMPLIFIED: prow cheeks + tub_nose + M8 nut
ducts/channels DELETED from the hull (lower_front 114 -> 67 cm3, tail 75 -> 32);
the hull ends are plain glacis walls at y +-120 (lamps/USB/rear pod re-key via
tub_nose 0); the M8 NYLOCs ride LEDGE+ROOF CAGES on the panel towers' inboard faces
(gap 13.4 = AF13+0.4, front cage spans the tension travel, axial load on the tower
face, strips only stop rotation; small blind nut-window notches in the end walls) --
a bare track module can TENSION with zero hull pieces. Tower slabs reach back to
|y| 114 to fuse through the corner-arc wedge (the cheek skin used to bridge them).
Print profile: 0% infill + 5 walls global, STRUCT 6 walls + token 8%. All gates
green: check + sweep + 50/50 invariants + wallcheck + fits + probe + 20/20 slices.

**TT SPROCKET JOINT HARDENING (2026-07-16, K2/K3 review):** each side-panel TT
crossing now has a closed printed journal land at absolute |x| 70.2..74.5: Ø12.5
bore on the sprocket's Ø12 hub gives 0.25 radial running clearance, with a full
saddle grown above the old beam top and backed by the panel wall. The rest of the
crossing, |x| 74.5..81.2, remains the open-top Ø13.5 relief. Grease the printed
journal. The owned MR105 5x10x4 cannot fit a Ø12 hub and cannot be seated inside
the hub's Ø6 free bore. Axial retention remains M2x25 plus Ø9 washer when the TT
shaft has its VERIFY_ON_ARRIVAL Ø2 tip hole. Positive fallback is now a vertical
Ø2.1 cross-pin bore at sprocket-local x -20.5, y +2.3, world |x| 75.9 in the open
relief: mark, remove, file an approximately 1 mm shaft-arc notch, reassemble, insert
Ø2 filament, and trim flush below the hub OD. Crush ribs are handling aids only.

**TRACK HOLD-DOWN SHOES (2026-07-16):** four bolt-on `track_shoe_{L,R}_{rear,front}`
parts sit under the wheel beam at spr_y -68 and spr_y2 +90. Their z 10.4 running
faces leave 0.9 over the ground-run link crowns at z 9.5, versus the measured 2.14
mm rigid-chain skip barrier. Each 10.6 x 14.76 x 4.6 shoe has 45 degree y lead-ins,
two Ø3 pins into Ø3.4 beam bores, and 2x M3x12 csk screws from below into captive
M3 nuts at z 18.5. The flat seat carries skip load into the beam in compression.

**Electronics seats (2026-07-13 -> moved to the base 2026-07-14):** the Uno R3 seat (4
posts to z 21 + a rear-wall shelf for the glacis-side hole;
hole pattern verified vs the Adafruit Arduino-dimensions drawing, USB-B faces +X, cable
route right wall -> pan service loop -> the 16x8 platform pass -> neck channel -> Pi),
IMU posts on the floor strap at (14,-12) (rigid, near the pan axis; pedestal owns dead
center), an SW-420 hard pad at (-48,-95), and BME688 bosses over the y-96 LEFT vent
(samples room air, 43+ from the buck tray; the y16 vent was rejected -- seam pad +
deck boss leave an exact-18.0 squeeze). chassis_deck_front gets a second underside
pocket (x -55..-32) with a vertical tab: the LD2410-class mmWave stands BORESIGHT
FORWARD behind the front slope's hex-grille field as its radome (~3.5-6 mm oblique PLA
on axis; the front wall itself has no copper-free aperture -- HC-SR04 center, M8 nut
stacks in the cheeks). LD2450 (25.6 wide) does NOT fit this bay. Placeholders
board_arduino + sensor_imu/bme/vib/mmwave, ALL module dims VERIFY_ON_ARRIVAL in
PARAMS (docs/ASSEMBLY.md table); TTP223 pads deferred to a head-top pass (chassis
fallback documented in PARAMS: cliff-pocket top skins are 3.5 thick).

**Head-thermal pass (2026-07-13, Pi 5 Active Cooler keep-out):** the buy-list "CAD must
confirm head-bay clearance" question is answered with measured geometry, not guesses.
The official cooler envelope (63.5 x 42.5 x 13.7, product brief RP-008188 + mechanical
drawing RP-008187) was seated on the Pi 5's two dedicated Ø3 heatsink holes (board
(3.5, 9.5) / (61.5, 46.5), each 6.0 off its M2.5 corner hole, pin pattern dead-centered
in the envelope), and the board frame was measured off the reference mesh's corner-hole
pattern (58.000 x 49.000 exact at world x -34.652/23.348, z 130.766/179.766 -> board
origin (-38.152, 127.266), component face y 5.98). World envelope: x -37.4..26.1,
y -7.72..5.98, z 134..176.5 -- PARAMS "pi5_cooler_*", part `build_pi5_cooler()`
(silver keep-out, never printed), added by **COOLER=1 only (default OFF)**.
VERDICT (tools/probe_cooler.py, re-runnable): **CLEAR, static + full +-33.8 sweep**
since the same-evening WORM-TAIL RETREAT -- static worst neck_clevis 0.78 /
worm_wheel 2.0; sweep worst neck_clevis -0.60 / tilt_worm -0.61 at the -33.8
nose-down stall (was +2.7 at the old bare Ø5 tail stub / +1.9 at the cradle pad).
The binding surface is the envelope's swung REAR face, y = -20.0 + 0.669(z - 131.5)
at the stall, so low-z material had to recede most. Fix (worm + neck only; plate,
motor, carrier, can pocket all HELD at y -34.5 by bumping the face_y offset 9.5 ->
10.0): worm threads shortened to y -30.5..-17.5 + 0.6 crest end chamfers (worm_len
14 -> 13, real pair REGENERATED per docs/WORM.md -- mesh re-verified 0.000 mm3,
contact onset CD-0.05..-0.10 unchanged, clocking 17.75 -> 17.88; the wheel contact
plane y=-18 keeps 0.5 of full flank past it, the trimmed rear end was dead thread);
the tail stub is DELETED and the neck's bare-stub cradle (pad front y=-13) replaced
by a CREST-RIDING r5.5 half-groove directly under the mesh (bearing land y -21..-18,
0.225 running clearance on the crest envelope, grease shared with the mesh --
mechanically better than the old past-the-mesh band, and it also kills the
wallcheck feather-wedge sliver the old groove punched through the pad bottom);
the support/riser/gusset/cheek front-bottom corners are shaped by subtracting the
STALL-POSED keep-out inflated 0.6 (build_neck_clevis "STALL-ENVELOPE TRIM" -- the
envelope corner arc, r 21.58 about the axle, used to graze the cheek corners within
~0.06). Cartridge extraction unchanged (worm still screws out through the Ø12.2
plate bore and the open-top groove). Capping nose-down tilt at ~-15 deg stayed
rejected (kills the +-30 spec and stall homing). AIRFLOW is a non-issue:
the fan's own intake window is ~Ø21 (~268 mm^2 net, measured center board (41.7,
33.7) = world (3.5, 161.0)) and the head already offers 684 mm^2 of louvres directly
above it + the 255 mm^2 I/O slot + the open bottom bay -- no new vent slots added.
Gates: default geometry is byte-identical with COOLER unset (check PASS); COOLER=1
also passes the static gate at the preview pose (contact starts past -19 deg tilt).
`pi5_cooler` is registered in HEAD_NODES and the viewer PAL silver rule (|cooler).

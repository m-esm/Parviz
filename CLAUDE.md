# desk-pi, tracked desk robot (Raspberry Pi head)

A small **tank-tracked mobile robot**: a **Raspberry Pi 5** driving the **official 7" touchscreen**
as an animated face, with a **Camera Module 3** as an eye, on a **neck that pans + tilts** the head,
sitting on a **two-track tank chassis** so it can drive around the desk.

The head is a **clean rounded box** (a tablet-head; earlier it was an Echo-Show wedge, since
simplified). Screen upright on the front, neck tilt gives the look up/down.

Status: **FIX CAMPAIGN COMPLETE (stages 1-5 + independent verification, see docs/FIXES.md);
MAINTENANCE/DFA PASS 2026-07-08** (workflow-reviewed, all gates green): tilt-motor cartridge
(`tilt_carrier`), D-keyed worm wheel on a flatted axle, track master links + keepers, pan BB
cage, pan/tilt stall-homing hard stops, microSD wall slot + `sd_plug`, pod-rail thread-form
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
z 174 drivetrain-sweep ceiling, motor bodies fill the x 25.7..53.5 band between the sweep
and the screen-tray rails, half-shafts pass over the rails at z 205; the top-wall guide
bores carry friction O-rings against gear-up back-drive, and ANT=<mm> bakes a preview
extension while the viewer gets one slider per mast; parts: antenna_L/R + ant_gears_L/R +
ant_bracket + motor_ant_L/R, gates run at ANT=0/15/50), rear orange `trim_hatch_frame` (bottom band
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
deepened to 36 with a wiring-box notch in the rear ligament. ant_gears_L/R being 7
bodies each is by design (4 placeholder gears + idler shaft + half-shaft + pinion,
separate physical parts pending the real generated-teeth pass).

Latest render review (2026-07-06): `make build` wrote a 20-part `web/assembly.glb`; fresh
transparent and solid shots were inspected from iso/front/side/top plus two section cuts. The
assembly reads correctly as a tablet-head tracked robot, but the print-final fixes are:
**widen the track gauge**, add a low ballast bay in the chassis, model the body-to-pod M3/dowel
joins, shroud the exposed rear tilt motor, make the front camera/lens read more deliberately,
render neutral (`PAN=0 TILT=0`) and motion extremes, and add a bottom view to `src/shoot.py`.

## The build loop (do this on every geometry change)

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
```

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
35 mm, wiring box. The governing rule for both joints: **locate the CAN so the offset shaft lands on
the target axis, don't fight the offset with an eccentric coupler.**

- **Pan (direct D-hub):** 28BYJ upright in the base, can offset `-motor_shaft_off` so the shaft is on
  the pan axis; it keys into a **double-D bore hub** under `pan_platform` (`dbore_neg`/`dbore_hub`;
  flats drive snug, round arcs loose -- mini-Oldham, the race locates). No reduction. Rides the
  lazy-Susan BB race (see Mechanical intent). **Homing:** stall against the deck stop posts at
  ±93.3° (lug az 225 on the platform underside, posts az 118/332), back off, call it ±90.
- **Tilt (self-locking worm, CARTRIDGE):** the worm sits on the motor's D-shaft (shaft +Y,
  right-angle to the axle), meshing a 12T `worm_wheel` **D-keyed to the flatted Ø5 axle** (hub
  ledge on a filed 1.0-deep flat, 2026-07-08; the old M3 grub was blind and friction-only).
  Single-start → self-locks, so the head holds ±30° with the driver OFF. Motor + worm ride the
  removable **`tilt_carrier`** (ears bolted on the bench, 4× M3×16 from the open rear bay; the
  worm extracts axially through the plate's Ø12.2 bore, spinning the free wheel as it goes --
  BUT with the head hung + grubbed, DRIVE THE HEAD FULLY UP first: clearing mesh needs ~46° of
  worm-as-rack nod and the stops only allow ~34° from neutral, review 2026-07-08) -- a dead
  28BYJ swaps without touching the head. **Homing:** stall the head's ±55° clamp-tube fins
  against the cheek posts at ±33.8°. Real generated teeth per docs/WORM.md.
- **Axle + bearings:** Ø5 SOLID rod (flat filed 1.0 deep from the insertion end to ~15 past
  center; a tube dies under the flat -- 0.25 wall; D-key ledge fit +0.05, coupon first, the
  old +0.15 was ±4.4° of head backlash; the +X 695 inner race rides the D-profile, fine
  since the spacer tubes clamp it) on **695-2RS bearings (5×13×4, owned ×30)** pressed into
  the neck cheeks. Head clamps the axle ends (grub screws at x=±30, kept: they give
  continuous tilt-zero trim).
- **ULN2003 mounts / motor pockets:** the base has a pan-motor pad + ULN standoffs; the tilt
  motor's Ø29 can pocket doubles as the cartridge's mesh lead-in.

**Buy list (gaps; full inventory-checked BOM in docs/ASSEMBLY.md, 2026-07-08):** a 2nd track
drive motor (see below), 4× F688ZZ flanged bearings 8×16×5 (2 per idler since the 2026-07-10
fix; one bearing let the 30-wide wheel tilt), 14× M4×40 + nuts (road-wheel bolt-axles,
partially threaded preferred; 40 mm exceeds the owned kits), 4× HC-SR04 (forward +
rear obstacle + 2 cliff; NONE owned), 6 mm airsoft BBs (pan
race), Ø5 SOLID rod for the tilt axle (gets a filed D-flat; no tube), the power set from firmware/WIRING.md
(30W+ PD brick, 12V PD trigger, XL4015 5A buck, MP1584 mini buck, JST-XH kit + crimper,
18 AWG pair, 5A fuse), Ø4×12 dowels ×4, 1 m of NARROW (4–5 mm) addressable strip
(SK6805-2427/WS2812-2020, a standard 8×5050 stick is 53.3×10.2 and does NOT fit the 42×5
`led_slot`). M2/M3 screws are covered by the owned kits. The "608zz ×30" are unused in the
design and still unverified (may be plastic rings).

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
  into the sprocket. **You own only 1 TT + bare 130-size cans (no gearbox); BUY 1 more TT 1:120 (or
  2× N20 metal-gear for a lower CoM).** One MX1588 (own ×5) drives both. Skid/differential steer.
- Params: `chassis_w/l`, `track_wheel_r`, `track_wheelbase`, `track_width`, `track_pitch`,
  `track_links`, `sprocket_teeth`, `idler_bore_d`, `roadwheel_*`, `track_gap`, `chassis_clear`.
- **Body-to-pod join (modeled):** 2× M3×12 thread-forming into the rail's blind Ø2.5 pilots
  (2026-07-08: was captive nuts in top slots that got buried by the links) + 2× Ø4 dowel per
  side (shear). **Master link:** link 0 of each loop is a drop-on C-jaw link; two printed
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
`_front/_rear` at y=+26 (floor pads x +-61: M3x12 axis-Y + Ø4 dowel each; the deck
screws and the one-piece pod rails also bridge), `chassis_deck` -> `_front/_center/
_rear` at y 66 / -52 (half-laps + 2x vertical M3 per seam; the pan seat stays
monolithic in the center, which gets its OWN 4 hold-downs at (+-64, 8)/(+-64, -26)).
`head_door` kept whole but the solid tier legs got lightening pockets (-19 cm3). Gate
whitelists alias split pieces to their parent (SPLIT_ALIAS in assembly_check/fitmap);
sibling seam contact is designed. The viewer parts panel is grouped BY OBJECT with
collapsible per-group toggle-alls.

- Printed set (exports via `EXPORT=1`): `chassis_lower`, `chassis_deck`, `belly_plate`, `track_L/R`,
  `drivewheels_L/R` (as track_wheels_*), `track_keeper_L/R`, `pod_rail_L/R` (as
  track_pod_rail_*), `neck_clevis`, `tilt_carrier`, `pan_platform`, `pan_race`,
  `pan_clips`, `pan_cage`, `head_bezel`, `head_back`, `head_door`, `screen_tray`,
  `cam_cover`, `sd_plug`, plus the real generated `worm_wheel`/`tilt_worm` (docs/WORM.md).
  `pan_balls`/`motor_*`/`drive_*` are bought-part placeholders. track_L/R (links +
  wheels), track_keeper_* (2 bars) and pan_clips (3 clips) are multi-body by design.
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
- **Per-part print orientation:** `chassis_lower` seam-up/open-top, `chassis_deck` top-face-down,
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
src/chassis.py   chassis core/lower/deck split, belly plate, fascia, pod rails.
src/tracks.py    raised tank loop, links, master link, sprocket, road wheels.
src/motors.py    TT gearmotor + 28BYJ placeholder meshes.
src/fitmap.py    the FITS=1 clearance/press report + contact audit.
                 Import DAG: params <- geo <- gears/screen/motors <- tracks/pan/neck/head/
                 chassis <- build (fitmap standalone; no cycles -- params imports nothing local).
src/stlpaths.py  routes stlp("track_L.stl") -> stl/base/... ; subsystems: base / neck / head
src/serve.py     localhost viewer server (serves web/ at root)
src/shoot.py     headless multi-angle renders -> .claude/renders/
web/             viewer_glb.html + assembly.glb (committed so a fresh clone shows the assembly)
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
per end idler x4), M4x40 12, hinge pins 128, Ø8 stubs x4 ~50 mm (M8 bolts work).
PRINT NOTE: 128 track links total -- budget the print time.

**Drive-mechanism review (2026-07-11, task #11):** the wheel beam doubles as the
ANTI-BUCKLE CAP for the mid-drive: the pushed side of the ground run (rear of the
active sprocket when driving forward) can only lift 4.5 mm (crowns z 9.5 -> beam
bottom z 14) before the beam stops it, and beyond +-86 the ramps are held by the
tensioned end idlers. Run the tracks TENSIONED (the front M8 nuts) -- tension is
what prevents bunching in the first place. Stall-torque tooth force ~4.1 N lands on
~1 pin (the straight-run mesh engages one pocket; neighbours sit 2.5 above their
pins), giving ~19 MPa pin bending = 2.6x margin on PETG. The sprocket takes ~1/7 of
the robot's weight through the mesh, which preloads engagement closed.

**End-axle + dual-drive pass (2026-07-11, user rounds 9-10):** (1) M8 END BOLT-AXLES
(user: "two wheels per side not connected to anything" -- the plain Ø8 stubs had no
axial retention and the idlers showed bare bearing bores outside): each end wheel now
rides an M8 bolt, head outboard as the hubcap, shank through the F688 pair and the
pylon, NUT on the pylon's inboard face; on the FRONT pylons the nut clamps the through
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
and the pedestal blocks every left-side alternative. BOM: 4x M8x60 + nuts (Bag 13
"Machine Bolts" may cover it -- verify), M4x40 12 -> 10, TT motors: 2 required
(own 1, buy 1) + 2 OPTIONAL for twin drive.

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

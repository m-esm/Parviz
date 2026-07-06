# desk-pi — tracked desk robot (Raspberry Pi head)

A small **tank-tracked mobile robot**: a **Raspberry Pi 5** driving the **official 7" touchscreen**
as an animated face, with a **Camera Module 3** as an eye, on a **neck that pans + tilts** the head,
sitting on a **two-track tank chassis** so it can drive around the desk.

The head is a **clean rounded box** (a tablet-head; earlier it was an Echo-Show wedge, since
simplified). Screen upright on the front, neck tilt gives the look up/down.

Status: **DRIVETRAIN FINALIZED (post multi-agent mechanism research).** `src/build.py` builds the
whole robot around the measured 7" screen STL; 9 watertight per-part STLs (chassis, track_L,
track_R, neck_clevis, pan_platform, pan_race, head_bezel, head_back, cam_cover) plus placeholder
sub-parts (worm_wheel, tilt_worm, pan_balls, motor_*, drive_L/R). A 6-agent research pass drove the
mechanism decisions now in geometry: **pan = 28BYJ direct D-hub on a captured-BB lazy-Susan race**;
**tilt = self-locking single-start WORM drive** (Ø5 hollow axle on 695-2RS bearings, owned); **screen
mounted by its 4 factory M3 holes** (not the glass lip); **camera recessed behind the forehead** with
a lens bump + `cam_cover`; **tracks = modular positive-drive links + 12T sprocket + idler + road
wheels + 2 TT drive motors**. The 28BYJ placeholder is now dimensionally correct (Ø28.25, 7.875 mm
offset shaft, 3 mm D-flats). Remaining: worm teeth are readable placeholders (regen involute/helix
in BOSL2 in a venv), body-to-pod join, widen track gauge (head overhangs ~10 mm/side), buy list.

## The build loop (do this on every geometry change)

```
make build          # python3 src/build.py -> web/assembly.glb
make viewer         # python3 src/serve.py 8765 (leave running; user watches live at
                    #   http://localhost:8765/viewer_glb.html -- auto-reloads on rebuild)
make shot           # headless render -> .claude/renders/chk_*.png  (serve must be up)
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
  │                 Tracks = 36 modular link pads on a stadium loop, 12T sprocket + idler + road
  │                 wheels, belt to ground, run along Y (build_tracks / _track_link_poses).
  └─ PAN joint      yaw about vertical Z  (±90° target). motor_pan direct D-hub; rides a captured-BB
      │             lazy-Susan race (build_pan_race: pan_race + pan_balls)   ── the "turret"
      └─ pan_platform + neck_clevis   rotate as one
          └─ TILT joint   pitch about horizontal X (±30°). SELF-LOCKING WORM: motor_tilt (shaft +Y)
              │           carries tilt_worm meshing worm_wheel keyed to the axle. Holds tilt de-
              │           energized. Ø5 hollow axle rotates in 695-2RS bearings in the cheeks.
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
  head clamps a **Ø5 hollow axle** at its side-wall hubs (axle turns WITH the head); the axle rotates
  in **695-2RS bearings** pressed into the neck cheeks (x=±22); the `worm_wheel` (24T) is keyed to the
  axle and driven by the `tilt_worm` (single-start) on motor_tilt, whose shaft runs +Y (right-angle to
  the axle). Single-start worm self-locks, so the head holds ±30° with the motor de-energized (no idle
  current/heat). Pre-balance the head on the axle (Pi as counterweight) so the worm barely works. Axle
  Z (=178) MUST match the cheek bearings — an earlier bug lifted the clevis 46 mm; build in world Z.
- **Camera is RECESSED behind the forehead** (the 24 mm board can't fit the ~10 mm forehead gap): lens
  bump on the front at `cam_lens_z`, board on 4x M2 bosses at the 21×12.5 pattern, `cam_cover` traps
  it, CSI ribbon drops to the Pi bay. Lens optical axis is X=0, Z=+2.47 above board center (not centred).
- **Screen is held by its 4 FACTORY M3 holes** (outer 126.2×65.65 case-mount pattern), bosses on
  `head_bezel`, screw axis +Y into the display's metal chassis. The front glass lip is now only a
  locator, not the retention. See `PARAMS["scr_mount_pts"]`.
- **Pi 5 lives IN THE HEAD, behind the tilt axis.** DSI + CSI ribbons stay entirely in the head (zero
  joint crossings); the board doubles as the tilt counterweight. Only round wires (Pi power) cross the
  joints. Tradeoff: heavier head + higher CoM → ballast the base low.
- **Cable path:** hollow Ø5 tilt axle (on-axis) → neck channel → off-axis pass through pan_platform +
  base. Pan is ±90°, so a **service loop** (helical slack coil) crosses the pan joint, NOT a slip ring
  — it carries the Pi's full 5A rail silently and free; software-limit pan so it never over-winds. A
  2A/circuit capsule slip ring can't pass 5A without paralleling contacts; only add one for 360° pan.

## Head is a 2-piece print (bezel + back)

`build_head_parts()` slices the wedge on a plane parallel to the front face, ~4mm behind the screen:
- `head_bezel` (front): the face + camera lens bump + **4 M3 screen-mount bosses** (the display's own
  factory holes retain the screen) + the 6 bezel↔back nut-trap bosses. The stepped aperture lip is now
  just a locator. Print face-down.
- `head_back` (rear): pivot hubs, neck slot, Pi bay, cable port, Pi standoffs. Print open-side-down.
Screen drops into the pocket from behind and bolts to the bezel's 4 M3 bosses; bezel bolts to back.

## Head style: simple rounded box (simplified from the Echo-Show wedge, per user)

The head is now a **clean rounded box** (`_head_solid`: rounded-rect footprint 205w × 62d, flat
top/bottom, rounded vertical edges, upright front `face_angle=0`). The screen sits upright and flush
on the front; the neck's tilt provides the look up/down. It started as an Echo-Show "doorstop" wedge
(reference in `reference/alexa-style-smart-display/`, a Touch Display 2 design we borrowed the style
from) but the user asked to simplify the head shape. Still split by `build_head_parts()` into
`head_bezel` (front, screen-retaining lip, camera nub) + `head_back` (Pi bay, hubs, vents).

## Key numbers (measured, not guessed)

Screen `PARAMS["screen_*"]` are **measured from the reference STL bbox**: 193.0 (W) × 25.0 (D) ×
110.8 (H) mm, driver board included. Loaded live from
`reference/rpi-7in-touchscreen-model/files/Raspberry_Pi_Touch_Screen_Assembly_v12.stl` and mounted
on the leaned face by `screen_pose()`. Overall assembly bbox ≈ 221 × 208 × 248 mm.

Still first-guess (validate on a print): tilt axis height 178, cantilever 18.5, tilt ±30, pan ±90,
worm module 1.25 / 24T, track pitch 10 / 36 links / 12T sprocket, pan BB circle Ø80. Head width 205
vs track gauge ~184 → head overhangs ~10 mm/side (widen the gauge or accept it).

## Power (decided)

Use the **official Raspberry Pi 27W USB-C PD supply (5.1V / 5A)**. The Pi 5 only unlocks full
USB current on a true 5A PD supply; a 15W/3A brick software-limits USB to ~600mA and browns out
once screen + camera + servos draw together. Two servos (pan + tilt) may want their **own 5–6V
supply** rather than pulling off the Pi's rail — decide when the servo BOM is picked.

## Motors — 28BYJ-48 pan/tilt (dimensionally correct now) + TT track drive

Motor choice made against the parts on hand (see the moshes-inventory MCP): the head is driven by
**28BYJ-48 5V geared steppers** (×6 in Bags 5 & 14) with **ULN2003 boards** (×9); the 9g servos are
too weak to swing a 193mm screen head. `motor_28byj()` is now dimensionally correct: **Ø28.25 can,
18.8 tall, 7.875 mm shaft offset, Ø4.93 double-D shaft with 3.0 mm flats over the top 6 mm**, ears at
35 mm, wiring box. The governing rule for both joints: **locate the CAN so the offset shaft lands on
the target axis — don't fight the offset with an eccentric coupler.**

- **Pan (direct D-hub):** 28BYJ upright in the base, can offset `-motor_shaft_off` so the shaft is on
  the pan axis; it keys into a **double-D bore hub** under `pan_platform` (`dbore_neg`/`dbore_hub`) +
  an M3 grub on a flat. No reduction. Rides the lazy-Susan BB race (see Mechanical intent).
- **Tilt (self-locking worm):** the worm sits on the motor's D-shaft (shaft +Y, right-angle to the
  axle), meshing a 24T `worm_wheel` keyed to the Ø5 axle. Single-start → self-locks, so the head holds
  ±30° with the driver OFF (no idle heat). Pre-balance the head so the worm loafs. Center distance =
  wheel_r + worm_r (`PARAMS["worm_*"]`). **NOTE:** `gear_disc`/`worm` teeth are readable placeholders;
  regenerate the real involute wheel + helical worm in BOSL2 (OpenSCAD) in a venv before printing.
- **Axle + bearings:** Ø5 hollow axle on **695-2RS bearings (5×13×4, owned ×30)** pressed into the
  neck cheeks. Head clamps the axle ends (grub screw); axle turns with the head.
- **ULN2003 mounts / motor pockets:** the base has a pan-motor pad + ULN standoffs; the tilt bracket
  is a plate + gusset off the neck. The real Ø28 pockets/ear traps are still to be detailed.

**Buy list (gaps):** a 2nd track drive motor (see below), 2× Ø16 flanged bearings (idlers), 6 mm
airsoft BBs (pan race), Ø5 rod for the tilt axle, M2 screws (camera). Verify the "608zz ×30" are
steel, not the flagged plastic rings, before trusting them for anything.

## Tank chassis (the mobile base)

Two-track tank base. `build_base()` is the central **body** (rounded box; houses the pan motor + ULN
driver + wiring + ballast; deep pan-race seat + pan-mount on top at z=52). `build_tracks()` builds two
**positive-drive track pods** (geometry from the local `Tank track - 3062624/` reference = Thingiverse
thing:3062624, CC-BY): a chain of **36 printed link pads** (`_track_link_poses` walks the stadium loop)
on filament-rod hinge pins, a **12-tooth drive sprocket** (rear) meshing the pins, an **idler** on a
Ø16 bearing (front) in a tension slot, and **road wheels** supporting the bottom run. Positive tooth
engagement beats a friction belt that slips when the head pans.

- **Drive:** `drive_L`/`drive_R` = 2× TT gearmotor placeholders (`motor_tt`), one per pod, shaft on X
  into the sprocket. **You own only 1 TT + bare 130-size cans (no gearbox); BUY 1 more TT 1:120 (or
  2× N20 metal-gear for a lower CoM).** One MX1588 (own ×5) drives both. Skid/differential steer.
- Params: `chassis_w/l`, `track_wheel_r`, `track_wheelbase`, `track_width`, `track_pitch`,
  `track_links`, `sprocket_teeth`, `idler_bore_d`, `roadwheel_*`, `track_gap`, `chassis_clear`.
- **Still TODO:** body-to-pod join (2× M3 nut-trap + 2× Ø4 dowel per side), links as real TPU/PLA
  print vs the rigid model, widen the gauge (head overhangs ~10 mm/side). Pi rides the head (high CoM)
  → keep the chassis heavy/low and the wheelbase long so it doesn't tip on accel or a fast head pan.

## Print notes (first pass — not finalized)

- 9 printed parts (`chassis`, `track_L`, `track_R`, `neck_clevis`, `pan_platform`, `pan_race`,
  `head_bezel`, `head_back`, `cam_cover`) export via `EXPORT=1`. `worm_wheel`/`tilt_worm`/`pan_balls`/
  `motor_*`/`drive_*` are placeholders (bought parts or regen-in-BOSL2). track_L/R are multi-body
  concatenations of links + wheels, not single solids.
- **Fastening = M3 into CAPTIVE HEX NUTS** (M2 for the camera, M2.5 for the Pi). `screw_post`/`hex_prism`.
  - bezel↔back: 6 perimeter posts, nut captive in the back boss, screw from the front.
  - screen: 4× M3 bosses on the bezel at the display's factory 126.2×65.65 holes.
  - camera: 4× M2 bosses at 21×12.5; `cam_cover` traps the board.
  - neck↔pan_platform: 3× M3. Pi 5: 4× M2.5 standoffs on the back cover (58×49).
  - pan motor: floor pad in the base, D-hub coupling; tilt motor: bracket + gusset off the neck.
- **Tilt bearings:** 695-2RS pressed into the neck cheeks (not the head); head clamps the axle ends.
- **Electronics fittings:** base has a pan-motor pad + ULN2003 standoffs + a USB-C wall slot +
  8 vent slots; head back cover has a Pi I/O slot + ventilation louvres + the cable port.
- **Per-part print orientation:** bezel face-down (aperture opens up, best cosmetic face), back
  open-side-down, neck on its back, base flange-down.
- **Still a refinement:** explicit 45° self-supporting chamfers on the largest back openings
  (I/O slot ~64mm), the offset-shaft coupler part, a second ULN mount for the tilt driver, and the
  pan-joint slip ring (a purchased capsule — model its seat once you buy one). Screen standoffs wait
  on measuring the display's real mount holes from the reference STEP.

## Layout

```
src/build.py     source of truth. PARAMS block at top; builds chassis/tracks/pan/neck/head into a GLB.
src/stlpaths.py  routes stlp("track_L.stl") -> stl/base/... ; subsystems: base / neck / head
src/serve.py     localhost viewer server (serves web/ at root)
src/shoot.py     headless multi-angle renders -> .claude/renders/
web/             viewer_glb.html + assembly.glb (committed so a fresh clone shows the assembly)
stl/{base,neck,head}/   per-part STLs (head_bezel + head_back), written by `EXPORT=1 python3 src/build.py`
exports/         Bambu .3mf plates (regenerable, gitignored)
reference/       rpi-7in-touchscreen-model (STEP/STL, the real screen) + -case + alexa-style-*
docs/ASSEMBLY.md BOM + assembly order
```

## Gotchas

- **`TAU` in build.py is `2*np.pi` (a full turn).** It was once wrongly set to `np.pi`, which made
  `R(TAU/2)` a 90° rotation — that silently laid the LCD on its back (the "screen position wrong"
  bug) and half-rotated the tilt motor and vents. If you touch `TAU`, keep it `2π` and remember
  `cyl(axis="x"/"y")` relies on `R(TAU/4)` = 90°.
- The screen STL loads as X=width, Y=depth, Z=height (correct, upright). `screen_flip=True` applies a
  180° YAW (about Z) to face the glass +Y. `screen_pose()` = optional face lean + translate to the
  front face; `tilt_cantilever` sets how far forward (keep glass ~flush with `body_front_y`).
- `python3` here is **3.9**; `build123d` needs ≥3.10. This uses the **trimesh + shapely + manifold**
  path (works on 3.9). Move to build123d in a venv when we want native fillets/chamfers.
- serve.py serves `web/` at root: the model URL is `/assembly.glb`. Passing `web/assembly.glb` to
  shoot.py 404s.
- The viewer **ghosts** housing-like parts by name (anything with shell/body/housing/case/lid) —
  that's why `head_shell` renders as a translucent outline. Toggle **solid** in the viewer to see it
  filled. `shoot.py` can't toggle it, so to render the shell solid, rename it in a temp scene.
- Screen STL axes already match ours (X=W, Y=D, Z=H); no swap needed, just recenter + `screen_pose()`.
- `EXPORT=1 python3 src/build.py` writes the per-part STLs; the plain run only refreshes the GLB.
- Reference `.123dx` files are Autodesk 123D (not usable); use the `.stl`/`.step` siblings.

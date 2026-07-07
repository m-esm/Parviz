# Assembly

Current assembly notes for the tracked desk-pi prototype. The task #28 insertion/torque-path
audit (2026-07-07) verified a complete install order exists (see "Assembly order (verified)"
below). Not print-final: still open are the real worm/wheel teeth (BOSL2 regen), a wider track
gauge (~10 mm head overhang/side), and a roomier tilt-motor mount.

## Bill of materials

Owned quantities cross-checked against a personal parts inventory (2026-07-07).
"Need" is per robot.

### Electronics

| Part | Spec / where it goes | Need | Owned | Buy |
|---|---|---|---|---|
| Raspberry Pi 5 | 2 GB, rides the display's own 58x49 standoffs | 1 | 1 (Tray 1) |, |
| 7" touchscreen | official kit; 4 factory M3 mounts (126.2x65.65) | 1 | 1 (Tray 1) |, |
| Camera Module 3 | recessed forehead, 4x M2 at 21x12.5 | 1 | 1 (Tray 1) |, |
| 27W USB-C PD supply | official 5.1V/5A (see CLAUDE.md; 3A bricks brown out) | 1 | 0 | **1** |
| 28BYJ-48 stepper | 5V, pan + tilt | 2 | 6 (Bag 14) |, |
| ULN2003 driver | one per stepper | 2 | 9 (3 Bag 14 + 6 Bag 5) |, |
| TT gearmotor 1:120 | track drive, one per pod, shaft on X into the sprocket | 2 | 1 (Bag 5) | **1** (match the owned one; or swap both for 2x N20 metal-gear for a lower CoM) |
| MX1588 dual H-bridge | drives both TT motors, skid steer | 1 | 5 (Bag 7) |, |
| WS2812 forehead segment | 8 LEDs in the `led_slot` recess: **42 x 5 mm, 1.5 deep** (model dot pitch 4.6). A standard 8x5050 stick is 53.3 x 10.2, it does NOT fit. Buy a narrow (4–5 mm wide) addressable strip (SK6805-2427 / WS2812-2020, ≥160 LED/m) and cut an 8-LED segment, or widen `led_slot` to ~54 x 11 for the common stick | 1 seg | 0 | **1 m narrow strip** (also covers the front strip, next row) |
| Front white strip | 7 dots at 5 mm pitch in a 36 x 2.5 lip (`fled_*`): either 7x 3 mm white LEDs or a second segment cut from the same narrow WS2812 strip | 1 | 0 | covered by the strip above (or 10x 3 mm white LED) |
| Amber indicator LEDs | 2 corner lamps, 12 x 7 windows (`lamp_*`): 2 rectangular amber LEDs (2x5x7) or 5 mm amber behind a printed lens | 2 | 0 | **2–5** |
| HC-SR04 ultrasonic (optional) | front fascia: Ø16 barrel passes at 26 mm c-c (`us_dx`=±13, `us_d`=16). Buy the **HC-SR04P** (3.3V) variant, the 5V original needs a divider on ECHO for Pi GPIO | 1 | 0 | **1** (optional) |
| Rear pod audio | rear Ø14 cylinder pod (`rear_cyl_*`): an owned Ø12 active buzzer fits for beeps. For real audio, buy a **MAX98357A I2S amp** and drive the owned 8Ω 0.5W mini speaker (Bag 15) from inside the chassis, the speaker is ~40–50 mm and can't live in the pod; the pod becomes the grille | 1 | buzzers: 5x active 5V (Bag 1) + 4x ~12 mm (Bag 16); speaker: 1 (Bag 15) | **1x MAX98357A** (only if speech/audio wanted) |
| Arm actuation | placeholder arms, TBD pending the arm mechanism pass. If actuated: 9x 9g servos owned (5x T-8090, 3x SG90, 1x MG90S) | TBD | 9 servos | nothing yet |

### Bearings, race, axles

| Part | Spec | Need | Owned | Buy |
|---|---|---|---|---|
| 695-2RS | 5x13x4, tilt-axle cheeks | 2 | 30 (Bag 13) |, |
| F688ZZ flanged | 8x16x5, flange Ø18; front idlers (seat Ø15.95 press + 18.5x1.0 flange recess; idler now 30 wide) | 2 | 0 | **2** |
| 6 mm airsoft BBs | pan race, Ø80 circle, `pan_race_n`=18 | 18 | 0 | **smallest bag (100+)** |
| Ø5 rod/tube | tilt axle, ~100 mm (silver steel or alu tube) | 1 | 0 | **1** |
| Ø8 stub axle | idler tension axle, ~20 mm, M3 set-screw lock; a short M8 bolt works | 2 | unknown, the Bag 13 "Machine Bolts" bag may have M8; verify | 2x M8x20 if not |
| 608zz | **not used** in the current design. The "608zz x30" Bag 13 entry is still flagged: photos look like white plastic rings/spacers, NEEDS ID. Don't design around them | 0 | 30? (unverified) |, |

### Fasteners and pins

| Part | Spec | Need | Owned | Buy |
|---|---|---|---|---|
| M3 screws + hex nuts | captive-nut joints everywhere; incl. M3x35 x8 bezel↔back | lots | 540pc M3 stainless kit + 175pc M3 30–50 mm kit + 600pc M2-M5 kit + 1263pc M2-M4 kit (all Tray 1) |, |
| M2 screws | camera board (4) + cam_cover (2) | 6 | in the 600pc M2-M5 and 1263pc M2-M4 kits |, (CLAUDE.md's "buy M2" is stale) |
| M3 nylon standoffs | ULN2003 / driver mounts | few | 380pc kit (Tray 1) |, |
| Track hinge pins | Ø1.75 filament, bore 2.0. 36 links x 2 pods = **72 pins x ~46 mm** (track_width 44.8 + trim) ≈ 3.4 m, cut from an owned spool (the black CR-PETG is tougher than PLA for pins) | 72 | spooled (Tray 1) |, |
| Ø4 dowel pins | body-to-pod join (2 per side): join not modeled yet; order once it is | 4 | 0 | later |

### Printed parts (watertight; tank base + split head)
- `chassis`: tank body between the tracks; pan motor cavity + pan-mount on top
- `track_L` / `track_R`: tank track pods: 36 links/side on Ø1.75 filament pins, 12T sprocket,
  F688ZZ idler (30 wide, tension slot), plain printed road wheels (2/side, 30 wide)
- `pan_platform`: disc that yaws on the base (central shaft bore + off-axis cable pass)
- `pan_race` / `pan_balls` / `pan_clips`: captured-BB lazy-Susan race and retaining clips
  (18x 6 mm BBs; `pan_balls` is a placeholder for the bought BBs)
- `neck_clevis`: rounded column + two cheeks that rise into the head and drive the tilt axle;
  vertical cable channel
- `head_bezel`: front of the rounded tablet head: screen locator lip, camera aperture,
  forehead LED recess (42x5)
- `head_back`: rear cover: pivot hubs, screen standoffs, Pi bay, cable port, vents
- `cam_cover`: camera board cover and cable trap
- `worm_wheel` / `tilt_worm`: placeholders only; regenerate real teeth before printing
- Cosmetic / design-ref set (render-only today, print with the head): side rails, forehead
  `led_strip`, `antenna_stub` (pure print, no hardware, a real telescopic antenna is owned
  in Bag 15 if ever wanted), `camera_pod` eye shell, rear `trim_hatch_frame`, chassis
  `trim_fascia` + `trim_rear`, and the placeholder gripper arms (mechanism TBD)

## Assembly order (verified)

Task #28 insertion-path + torque-path audit (2026-07-07): a full install order EXISTS
end-to-end. Every step below was checked with swept-cylinder driver-line / extraction
probes on the neutral-pose mesh; the numbers in parentheses are the worst measured
clearance. Read the **order constraints** and **nasty steps** at the bottom before you
start: several joints are only reachable at ONE point in the sequence.

Tools you need: a long slim **M3 driver ~95 mm reach** (screen standoffs), a **short/stubby
Ø3 hex bit** (tilt-motor ears), a **1.5 mm hex key** (grub screws), a standard M3/M2 driver,
tweezers, and thread-lock or CA glue (cosmetics). Use **M3 PAN/CHEESE-head** screws for the
4 screen standoffs, **NOT countersunk** (a Ø6.0 csk head will not enter the channel).

### Sub-assemblies to build on the bench FIRST (they become unreachable once seated)

- **A. Neck + pan platform.** With `pan_platform` upside-down on the bench, drop 3× M3 up
  through its underside Ø6.5 counterbores (r16.5 circle, clocked 270/30/150) into the
  `neck_clevis` base pilots. The counterbores face DOWN into the race once seated, so this
  bolt-up is impossible after the platform is on the balls. Torque path: screws clamp
  neck to platform; the platform D-bore keys to the pan motor shaft (below).
- **B. Tilt axle cartridge.** Slide onto the Ø5 axle: `worm_wheel` (grub it to the axle
  NOW, the grub is blind once the cartridge is in the cheeks) + its two spacer tubes.
  The wheel-hub grub has no in-situ driver line, so it MUST be set here on the bench.

### Chassis + drive (fixed frame)

1. **Print + prep the chassis.** Confirm the deck pan-seat, the pedestal, and both TT
   motor pockets are clean.
2. **Pod rails onto the body, BEFORE the links.** Bolt `pod_rail_L/R` to the body walls:
   drop an M3 nut into each rail TOP nut-slot, run M3×16 from the cavity wall face, press
   the Ø4×12 dowels. The nut-slots open upward and get buried once links wrap the pod, so
   the rails go on first.
3. **Body↔pod join + TT motors, BEFORE ULN #1.** Drive the body↔pod M3s from INSIDE the
   cavity into the rail captive nuts (the 4 mm pod gap takes a nut but no driver). Then set
   each TT gearmotor: shaft +X into the sprocket hub's double-D socket, front tab into the
   rear-wall pocket, nub into the wall pocket, 2× M3 through the gearbox + wall with the
   nut floating in the pod gap. ULN #1 mounts later because its board covers the cavity-side
   screw access for this step.
4. **Track running gear.** Press F688ZZ into each idler (Ø15.95 seat + Ø18.5 flange recess);
   slide the idler on its Ø8 stub axle into the chassis tension slot FROM OUTBOARD, set
   tension, lock the M3 set-screw. Fit the sprockets on the TT shafts, road wheels on their
   Ø4 stub pins.
5. **Thread the tracks.** Wrap 36 links per pod and drive the Ø1.75 filament hinge pins in
   along X, one knuckle line at a time around the loop (bore line clear, ≥2.5 mm). The final
   pin closes the loop by flexing the last two links together, plan the seam on a straight
   run, not an arc.

### Pan joint

6. **Pan motor + drivers.** Drop the pan 28BYJ into the pedestal can pocket (offset so the
   D-shaft lands on the pan axis), clamp the 2 ears with M3 into the pedestal pilots from
   ABOVE (deck open). Mount ULN #1 and the 2nd ULN/MX1588 board on their standoffs; wiring
   box leads exit the pedestal -X relief.
7. **Ballast, then belly plate.** Load the low ballast into the rear bay + the two belly-plate
   pockets from BELOW, then bolt on `belly_plate` (6× M3 csk, flush at z=7). Ballast must go
   in before the plate closes the floor.
8. **Pan race.** Grease the `pan_race` lower groove, seat it on the deck floor, and drop the
   **18× 6 mm BBs** into the open Ø98 seat well with tweezers (open-top groove, trivially
   reachable with the platform off).
9. **Lower sub-assembly A** (neck+platform) onto the BBs so the platform's upper groove
   captures them and the D-bore drops onto the pan-motor shaft (~19.5 mm engagement). Screw
   the 3 `pan_clips` into the deck pockets (driver clear 6.17 mm from above); their tabs
   reach over the platform rim rebate to hold the top-heavy head down. Check the platform
   spins free.

### Tilt joint + head (all on the pan group)

10. **Bearings + axle cartridge.** Press a 695-2RS into each neck cheek from the clevis gap
    (seats open flush to the inner face; a light lead-in helps start the press). Insert
    sub-assembly B through one cheek bearing → the gap (wheel meshes the worm) → the far
    bearing.
11. **Tilt motor + worm.** Put the worm on the tilt 28BYJ D-shaft, feed the motor shaft +Y
    through the bracket plate hole with the worm tail into the open-top cradle groove, and
    fix the 2 ears with M3/M4, **stubby Ø3 driver only** (2.1 mm alongside the can). Route
    the tilt ULN wiring on the column back standoffs (motor + driver both ride the pan group,
    so no leads cross a joint).
12. **Hang the head on the axle.** Lower `head_back` so its side hubs take the axle ends, then
    set the two head-clamp grubs at x=±30 with a 1.5 mm hex key driven UP through the bottom
    motor bay (4.0 mm clear). The axle now turns with the head; the worm holds tilt with the
    driver off (self-locking single-start).
13. **Screen + Pi module.** Seat the combined touchscreen+Pi (Pi on the display's own 58×49
    standoffs) into the `head_bezel` pocket from behind against the front locator lip; bring
    `head_back` to it and drive the **4× M3 pan-head** screws down the **Ø7 rear driver
    channels** (~88.5 mm long, use the ~95 mm slim driver) into the display's factory
    126.2×65.65 mount holes. Do this BEFORE any cosmetic frame goes on the back.
14. **Camera + forehead LED.** Mount the CM3 front-face-in on the 4× M2 pier bosses, trap it
    with `cam_cover` (2× M2 + ribbon pinch), drop the CSI ribbon into the pocket. Seat the
    WS2812 forehead segment in its recess and route the 3 wires through the wire pass to the
    Pi. Route the Pi power pair per the cable step below.
15. **Close the head.** Bezel to back: 8× M3×35 through the perimeter posts into the captive
    nuts in the back bosses (screws from the front). Fit the rear service `head_door`:
    engage the two top hook tabs first, swing the door in, then 2× M3 csk at the leg bottoms
    into the captive-nut blocks.

### Cables (per docs/CABLE-CHECK.md)

16. Base USB-C wall port → cavity; coil a **2-turn service loop (~600 mm) at r≈48, z≈38–45**
    in the cavity → 16×8 deck pass → platform slot → neck channel → the column top-left exit
    window → through the bottom-rear head slot to the Pi USB-C with **~60 mm of free head
    lead** for the tilt drape. Software-limit pan to ±90° so the loop never over-winds.

### Cosmetics LAST (glue + locating pins)

17. Press-and-glue the pin-located cosmetic parts: `trim_rail_L/R`, `trim_hatch_frame`
    (**after** the screen, its band overlaps the 4 driver-channel mouths, up to 2.3 mm),
    `camera_pod`, `antenna_stub`, and the chassis `trim_fascia` / `trim_rear` / `sensor_rear`
    grille cap. Fit fascia electronics if used: HC-SR04P barrels through the Ø16 passes, amber
    corner lamps, front LED strip, rear buzzer/speaker.
18. **Final check.** Power on; sweep pan ±90 and tilt ±30 and confirm the screen/Pi stack,
    worm, cheeks, axle, cables and bottom head edge stay clear (matches the `make check-sweep`
    gate).

### Order constraints (do NOT reorder)

- Pod rails (step 2) **before** links (step 5): nut-slots get buried by the links.
- Body↔pod join + TT screws (step 3) **before** ULN #1 (step 6): the board blocks cavity access.
- Neck↔platform bolt-up (sub-assembly A) **before** seating on the balls, counterbores face down.
- Worm-wheel grub (sub-assembly B) **before** the cartridge enters the cheeks, no in-situ line.
- BBs (step 8) **before** the platform (step 9); ballast (step 7) **before** the belly plate.
- Screen standoff screws (step 13) **before** the hatch frame (step 17).

### Nasty-but-possible steps (measured)

- **4× screen standoff screws:** ~95 mm slim driver down an 88.5 mm blind Ø7 channel; ~0.75 mm
  around an M3 pan head. Pan/cheese head only, a countersunk M3 (Ø6.0) will not enter.
- **Tilt-motor ear screws:** only 2.1 mm of driver-shaft clearance alongside the Ø28 can, a
  stubby Ø3 hex bit works, a Ø4 driver does not.
- **Last track pin:** closes the 36-link loop by flexing the final links; seam it on a straight run.
- **Worm-wheel grub:** bench-only (blind once the cartridge is in the cheeks).

### Recommendations (bigger than this pass)

- Regenerate the real `worm_wheel`/`tilt_worm` (BOSL2 involute/helix) and, while at it, give
  the wheel a bench-keyed cartridge or an in-situ-accessible grub line, the placeholder grub
  has no driver access in the assembled clevis.
- Relieve the tilt-motor can pocket / ear zone for a normal driver (needs a motor-cluster
  re-layout, out of scope here).
- Track gauge is still ~184 vs a 205-wide head (~10 mm overhang/side): widen the gauge or
  accept it (tracked elsewhere).
- If field-servicing the screen without un-gluing the hatch frame matters, notch the frame
  band clear of the 4 channel mouths.

## Wiring
Only round power wires cross the moving joints. DSI and CSI ribbons stay inside the head because
the Pi rides on the display back.

- Base USB-C/power inlet -> chassis cavity.
- Chassis cavity -> pan service loop.
- Pan service loop -> platform obround slot.
- Platform -> neck cable channel.
- Neck -> bottom-rear head slot, with enough slack for tilt ±30.
- Head-mounted LEDs (forehead WS2812) hang off the Pi's 5V/GPIO in the head, no extra joint
  crossings. Fascia LEDs / HC-SR04 / buzzer wire to the base-side controller.

Add a `firmware/WIRING.md` pin map once the motor driver wiring is chosen.

## Order now (by lead-time importance)

1. **2x F688ZZ flanged bearings** (8x16x5, flange Ø18): most specific part, slowest to source;
   the idler seats are modeled around them.
2. **1x TT gearmotor 1:120** matching the owned one (or decide now on 2x N20 metal-gear and
   re-model the motor pocket): blocks the drive train.
3. **Official 27W USB-C PD supply** (5.1V/5A): not in inventory; nothing runs at full power
   without it.
4. **1 m narrow addressable LED strip** (4–5 mm wide, SK6805-2427 / WS2812-2020, ≥160 LED/m),
   one purchase covers the forehead 8-LED segment and the front 7-dot strip. (Alternative:
   widen `led_slot` to ~54x11 and buy two common 8x5050 sticks.)
5. **Ø5 rod ~100 mm** (tilt axle) + **2x M8x20** stub axles if the Bag 13 bolt bag has no M8.
6. **6 mm airsoft BBs** (bag of 100+; need 18): cheap, everywhere.
7. Optional: **HC-SR04P** (3.3V variant) x1, **MAX98357A I2S amp** x1 (pairs with the owned
   8Ω speaker), **amber LEDs** x2–5.

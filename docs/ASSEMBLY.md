# Assembly

Current assembly notes for the tracked desk-pi prototype. The task #28 insertion/torque-path
audit (2026-07-07) verified a complete install order exists (see "Assembly order (verified)"
below). The 2026-07-08 maintenance pass then killed the worst service traps: tilt motor is a
rear-access cartridge (`tilt_carrier`), the worm wheel is D-keyed to a flatted axle (no blind
grub), tracks close with a master link (no loop-flexing), the pan race got a BB cage, both
joints got stall-homing hard stops, the microSD swaps through a plugged left-wall slot, the
pod rails thread-form (no buried nuts), and power is a 12 V PD-trigger + dual-buck belly tray
(firmware/WIRING.md). Not print-final: still open is a D-key fit coupon for the axle flat.

## Bill of materials

Owned quantities cross-checked against a personal parts inventory (2026-07-07).
"Need" is per robot.

### Electronics

| Part | Spec / where it goes | Need | Owned | Buy |
|---|---|---|---|---|
| Raspberry Pi 5 | 2 GB, rides the display's own 58x49 standoffs | 1 | 1 (Tray 1) |, |
| 7" touchscreen | official kit; 4 factory M3 mounts (126.2x65.65) | 1 | 1 (Tray 1) |, |
| Camera Module 3 | recessed forehead, 4x M2 at 21x12.5 | 1 | 1 (Tray 1) |, |
| 30W+ USB-C PD brick | any brick offering 12V (the official 27W works); the robot bucks 12V down internally, see firmware/WIRING.md | 1 | 0 | **1** |
| USB-C PD trigger board | set to 12V; mounts on the rear-wall M2 pilots beside the USB slot | 1 | 0 | **1** |
| XL4015-class 5A buck | Pi rail (trim to 5.25V); 40x20 post grid on the belly-plate tray | 1 | 0 | **1** |
| MP1584-class mini buck | motor rail 5V; zip anchors beside the main buck | 1 | 0 | **1** |
| JST-XH kit + crimper | every joint-crossing / board run is a keyed XH plug | 1 | 0 | **1** |
| 18 AWG silicone pair + 5A blade fuse | Pi-rail run + inline fuse at the tray | 1 m | 0 | **1** |
| 28BYJ-48 stepper | 5V, pan + tilt + 2x antenna drives | 4 | 6 (Bag 14) |, |
| ULN2003 driver | one per stepper | 4 | 9 (3 Bag 14 + 6 Bag 5) |, |
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
| F688ZZ flanged | 8x16x5, flange Ø18; front idlers, **2 per idler** (2026-07-10 fix: one bearing let the 30-wide wheel tilt on its stub; now one pressed at each face, Ø15.95 through-seat + Ø18.5x1.0 flange recess both sides) | 4 | 0 | **4** |
| 6 mm airsoft BBs | pan race, Ø80 circle, `pan_race_n`=18 | 18 | 0 | **smallest bag (100+)** |
| Ø5 SOLID rod | tilt axle, ~100 mm silver steel (**NOT tube**: a 1.0 flat on a Ø5/Ø2.5 tube leaves a 0.25 wall). **File a 1.0-deep flat** from the insertion end to ~15 past center (D-key for the worm wheel's hub ledge); only the ~6 mm under the hub needs a clean 1.0 ±0.1 depth. The flat crosses the +X 695 seat, so that inner race rides a D-profile (fine, the spacer tubes clamp it). Print a D-bore coupon first, starting at **+0.05** clearance (+0.15 measured as ±4.4° of head backlash) | 1 | 0 | **1** |
| Ø8 stub axle | idler tension axle, ~20 mm, M3 set-screw lock; a short M8 bolt works | 2 | unknown, the Bag 13 "Machine Bolts" bag may have M8; verify | 2x M8x20 if not |
| 608zz | **not used** in the current design. The "608zz x30" Bag 13 entry is still flagged: photos look like white plastic rings/spacers, NEEDS ID. Don't design around them | 0 | 30? (unverified) |, |

### Fasteners and pins

| Part | Spec | Need | Owned | Buy |
|---|---|---|---|---|
| M3 screws + hex nuts | captive-nut joints everywhere; incl. M3x35 x8 bezel↔back | lots | 540pc M3 stainless kit + 175pc M3 30–50 mm kit + 600pc M2-M5 kit + 1263pc M2-M4 kit (all Tray 1) |, |
| M2 screws | camera board (2 screwed + 2 locating pads) + cam_cover (2) + track master-link keepers (2/pod, **M2×8 pan head**, sunk in the tab counterbores) + PD-trigger mount (2) | 8+ | in the 600pc M2-M5 and 1263pc M2-M4 kits |, (CLAUDE.md's "buy M2" is stale) |
| M3 nylon standoffs | ULN2003 / driver mounts | few | 380pc kit (Tray 1) |, |
| Track hinge pins | Ø1.75 filament, bore 2.0. 45 links x 2 pods = **90 pins x ~46 mm** (track_width 44.8 + trim) ≈ 4.2 m, cut from an owned spool (the black CR-PETG is tougher than PLA for pins) | 90 | spooled (Tray 1) |, |
| Ø4 dowel pins | body-to-pod join (2 per side), Ø4x12: modeled (wall slip holes + rail press sockets) | 4 | 0 | **4** |
| HC-SR04 ultrasonic | x3: forward obstacle (front wall, in the grille opening) + front/rear cliff (flush in the deck slopes, boards behind the 5-thick skin). **Inventory has ZERO** (checked 2026-07-10) | 3 | 0 | **3** |
| M4x40 + nuts | road-wheel bolt-axles (2026-07-10 fix: wheels were mounted to nothing): head = outer hubcap, shank in the Ø4.2 wheel bore, nut captive in the rail wheel-beam slot. Prefer partially threaded (shank bearing surface); 40 mm exceeds the owned kits | 12+12 | nuts maybe in the 1263pc M2-M4 kit (verify) | **12x M4x40 (+nuts if absent)** |

### Printed parts (watertight; tank base + split head)
- `chassis_lower_front` / `chassis_lower_rear`: the open-top tub, split at y=+26 for
  print speed; join with 2x M3x12 (axis Y, heads in the front pads, thread-form rear)
  + 2x Ø4 dowels in the floor pads at x +-61, then the deck + pod rails bridge it
- `chassis_deck_front` / `chassis_deck_center` / `chassis_deck_rear`: the pan deck in
  three plates (seams y 66/-52, half-laps + 2x M3 down through each strip into shelf
  pilots); the center carries the whole pan seat + its own 4 hold-downs; the corner
  hold-downs live in the strips
- `track_L` / `track_R`: tank track pods: 45 links/side on Ø1.75 filament pins, 12T
  pin-pocket sprocket (real circular pin seats since 2026-07-10, r 1.15 on the 19.32
  pin circle), idler on 2x F688ZZ (30 wide, tension slot), 6 dished road wheels/side
  (30 wide) on M4x40 bolt-axles off the pod-rail wheel beams
- `pan_platform`: disc that yaws on the base (central shaft bore + off-axis cable pass)
- `pan_race` / `pan_balls` / `pan_clips` / `pan_cage`: captured-BB lazy-Susan race, retaining
  clips, and the BB spacer cage (18x 6 mm BBs; `pan_balls` is a placeholder for the bought
  BBs; the cage keeps them spaced so a turret lift doesn't scatter them)
- `neck_clevis`: rounded column + two cheeks that rise into the head and drive the tilt axle;
  vertical cable channel
- `head_bezel_L` / `head_bezel_R`: front frame split at x=+22 (M3 + Ø4 dowel in pads
  behind the forehead/chin strips); seam staggered off the back's for interlock
- `head_back_frame_L/R` + `head_back_panel_L/R`: rear cover in four (frames = walls +
  pivot hubs, print front-down, no ceiling support; panels = the flat 4mm back wall,
  print lying flat). 6x M3 from the back join panel to frame rim tabs; the frame
  halves share the top-wall flange (2x M3) and the panel halves a tongue/groove
- `screen_tray`: bench-mounted module carrier (2 rails + spine): the screen+Pi bolts to it
  on the bench (4x M3x10 into the factory bosses, open access), the loaded tray drops into
  head_back, 4x M3x10 drive from OUTSIDE the back wall (visible, between door and frame)
- `cam_cover`: camera board cover and cable trap
- `sd_plug`: friction plug for the microSD service slot (left wall + trim_rail_L); pull it,
  reach the card with straight forceps down the eject axis (~61 mm, sight line clear)
- `tilt_carrier`: removable tilt-motor cartridge plate; motor ears bolt to it on the bench,
  4x M3x16 clamp it to the neck bracket from the open rear bay
- `track_keeper_L/R`: master-link keeper bars (2 bars + side tabs per pod, 1x M2 each);
  the master link body prints as link 0 inside each `track_L/R`
- `worm_wheel` / `tilt_worm`: real generated teeth (docs/WORM.md); the wheel hub now carries
  the D-key ledge (regen includes it via the build's hub union)
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

Tools you need: a **1.5 mm hex key** (head-clamp grubs), a standard M3/M2 driver, tweezers,
and thread-lock or CA glue (cosmetics). (The old ~95 mm slim driver is retired: the screen
tray killed the 88.5 mm blind channels, 2026-07-08.)

### Sub-assemblies to build on the bench FIRST (they become unreachable once seated)

- **A. Neck + pan platform.** With `pan_platform` upside-down on the bench, drop 3× M3 up
  through its underside Ø6.5 counterbores (r16.5 circle, clocked 270/30/150) into the
  `neck_clevis` base pilots. The counterbores face DOWN into the race once seated, so this
  bolt-up is impossible after the platform is on the balls. Torque path: screws clamp
  neck to platform; the platform D-bore keys to the pan motor shaft (below).
- **B. Tilt axle cartridge.** Slide the `worm_wheel` (+ its two spacer tubes) onto the Ø5
  axle, hub ledge riding the axle's filed flat (D-key: positive torque, nothing to grub).
  Verify the fit on a printed coupon first: a loose flat is backlash.
- **C. Tilt-motor cartridge.** Bolt the tilt 28BYJ's ears to `tilt_carrier` (2x M4 + nuts,
  open bench access) and press the worm onto the D-shaft. The loaded carrier inserts later
  from the rear bay (step 11) and comes OUT the same way for a motor swap, no head teardown.

### Chassis + drive (fixed frame)

1. **Print + prep the chassis.** Confirm the deck pan-seat, the pedestal, and both TT
   motor pockets are clean.
2. **Body↔pod join (rails), BEFORE ULN #1.** Press the Ø4×12 dowels into each rail's blind
   sockets, seat `pod_rail_L/R` on the body walls (dowels into the wall slip holes), and
   drive the 2× M3×12 per side from INSIDE the cavity, thread-forming into the rail blocks'
   blind Ø2.5 pilots. These four screws ARE the body↔pod join -- there is no second screw
   set. ULN #1 mounts later because its board covers this cavity-side access.
3. **TT motors.** Set each TT gearmotor: shaft +X into the sprocket hub's double-D socket,
   front tab into the rear-wall pocket, nub into the wall pocket, 2× M3 through the
   gearbox + wall with the nut floating in the pod gap.
4. **Track running gear.** Press an F688ZZ into EACH face of each idler (Ø15.95 seat +
   Ø18.5 flange recess both sides); slide the idler on its Ø8 stub axle into the chassis
   tension slot FROM OUTBOARD, set tension, lock the M3 set-screw. Fit the sprockets on
   the TT shafts. Drop an M4 nut up each wheel-beam slot (do this BEFORE mounting the
   rails if access is tight), then bolt each road wheel with its M4x40 from outboard --
   snug, then back off 1/8 turn so the wheel spins free.
5. **Thread the tracks (master-link close).** On the bench, chain all 45 links per pod
   (link 0 is the master: its pitch-end pins to link 1 normally NOW) and drive the Ø1.75
   filament hinge pins along X. Wrap the open chain around the pod with the idler retracted.
   Seat the final pin in link 44's inner knuckles, swing the master's open jaws down onto it,
   slide the two `track_keeper` bars into the jaw slot from the side faces, and lock each
   with its M2 into the side-face pilot. Tension the idler. Track removal forever after:
   2 M2s out, slide the keepers, lift the master off its pin.

### Pan joint

6. **Pan motor + drivers.** Drop the pan 28BYJ into the pedestal can pocket (offset so the
   D-shaft lands on the pan axis), clamp the 2 ears with M3 into the pedestal pilots from
   ABOVE (deck open). Mount ULN #1 and the 2nd ULN/MX1588 board on their standoffs; wiring
   box leads exit the pedestal -X relief.
7. **Power tray, ballast, then belly plate.** Screw the PD trigger to the rear-wall M2
   pilots (jack aligned with the USB slot), the 5A buck to the belly plate's 40×20 post
   grid, zip the mini buck beside it, and wire per firmware/WIRING.md (leave 60 mm slack
   on every tray run; zip the incoming wall cable to the floor anchors as strain relief).
   Load the low ballast into the rear bay + the belly-plate pockets from BELOW, then bolt
   on `belly_plate` (6× M3 csk, flush at z=7). Ballast must go in before the plate closes
   the floor.
8. **Pan race.** Grease the `pan_race` lower groove, seat it on the deck floor, lay the
   `pan_cage` ring over it, and drop the **18× 6 mm BBs** through the cage pockets into
   the groove with tweezers. The cage keeps them spaced; any later turret lift leaves all
   18 sitting evenly in the groove instead of bunching and rolling out.
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
11. **Insert the tilt cartridge.** Slide sub-assembly C (carrier + motor + worm) in from
    the open rear bay: the worm passes the bracket plate's Ø12.2 bore, its tail lands in
    the open-top cradle groove, the can registers in the Ø29 pocket, and the carrier's 4
    bosses land on the plate/column rear faces. Drive 4× M3×16 from the rear into the
    thread-form pilots. (Extraction reverses this; sliding the worm axially spins the free
    wheel, nodding the head down ~46° over the pull -- so with the head hung and grubbed,
    **drive the head fully UP first** to bank the travel against the ~34° stop, or loosen
    the two head-clamp grubs. Before the head is hung, extraction is unconditional.) Route
    the tilt ULN wiring on the column back standoffs, board centered at z 93, below the
    carrier (motor + driver both ride the pan group, so no leads cross a joint).
12. **Hang the head on the axle.** Lower `head_back` so its side hubs take the axle ends, then
    set the two head-clamp grubs at x=±30 with a 1.5 mm hex key driven UP through the bottom
    motor bay (4.0 mm clear). The axle now turns with the head; the worm holds tilt with the
    driver off (self-locking single-start).
13. **Screen + Pi module (tray).** On the BENCH: bolt `screen_tray` to the combined
    touchscreen+Pi with 4× M3×10 pan heads straight into the display's factory 126.2×65.65
    bosses (the pillars are z-offset from the bores, so the driver line is open). Power-test
    the module on the desk if you like -- it is now a self-contained unit. Then drop the
    loaded tray into `head_back` from the open front (the pillars pass z-clear of the clamp
    tubes) and drive 4× M3×10 from OUTSIDE the back wall into the pillar-end pilots: short,
    visible screws in the fixed strip between the door outline and the hatch-frame opening.
    The bezel pocket locates the glass when the head closes (step 15).
14. **Camera + forehead LED.** Mount the CM3 front-face-in on the 4× M2 pier bosses, trap it
    with `cam_cover` (2× M2 + ribbon pinch), drop the CSI ribbon into the pocket. Seat the
    WS2812 forehead segment in its recess and route the 3 wires through the wire pass to the
    Pi. Route the Pi power pair per the cable step below.
15. **Close the head.** Bezel to back: 8× M3×35 through the perimeter posts into the captive
    nuts in the back bosses (screws from the front). Fit the rear service `head_door`
    (the stepped rear pod): engage the two top hook tabs first, swing the door in until
    both leg snap tongues CLICK behind the wall band beside the void (tool-free; replaced
    the 2× M3 csk 2026-07-10). To open: firm pull on the pod's bottom edge (35 mm proud,
    that IS the grip); the barbs' back ramps cam the tongues inboard and release. Open at
    roughly neutral tilt: at the ±33.8° stalls the tilt drivetrain reaches into the pod's
    internal cavity.

15b. **Antenna drives.** Slip a friction O-ring into each top-wall guide bore, drop each
    mast in from above (rack facing the pinion slot), then hang `ant_bracket` on the back
    wall (spine + 2 pilots), slide the Ø4 half-shafts through their bushings with the
    pinion + G4 gears, seat the idler shafts + G2/G3, and bolt each 28BYJ nose-through
    its face plate (2x M3 into the vertical-ear pilots, shaft inboard). Each mast has its
    OWN motor + ULN2003 (independent control); wire both to the Pi in the head. Homing:
    drive down until stall (tip cap on the boss). BUY: 2x Ø4 steel rod ~90 mm, 2x O-ring
    (Ø7 bore seat), plus the 30T/12T/27T m0.8 spur set per side (or print them with the
    worm-gear pipeline, docs/WORM.md).

### Cables (per docs/CABLE-CHECK.md + firmware/WIRING.md)

16. Wall PD brick → rear PD trigger (12 V) → belly tray bucks. The Pi-rail pair (18 AWG,
    from the 5A buck) coils a **2-turn service loop (~600 mm) at r≈48, z≈38–45** in the
    cavity → 16×8 deck pass → platform slot → neck channel → the column top-left exit
    window → through the bottom-rear head slot to the Pi's **GPIO 5V/GND pins** with
    **~60 mm of free head lead** for the tilt drape. Set `usb_max_current_enable=1` +
    EEPROM `PSU_MAX_CURRENT=5000` (GPIO power skips PD negotiation). Software-limit pan
    to ±90° (hard stops at ±93.3) so the loop never over-winds.

### Cosmetics LAST (glue + locating pins)

17. Press-and-glue the pin-located cosmetic parts: `trim_rail_L/R`, `trim_hatch_frame`
    (**after** the screen, its band overlaps the 4 driver-channel mouths, up to 2.3 mm),
    `camera_pod`, `antenna_stub`, and the chassis `trim_fascia` / `trim_rear` / `sensor_rear`
    grille cap. Fit fascia electronics if used: HC-SR04P barrels through the Ø16 passes, amber
    corner lamps, front LED strip, rear buzzer/speaker.
18. **Final check + homing.** Power on; firmware stall-homes pan against its ±93.3° deck
    stops and tilt against its ±33.8° fin stops, backs off, and zeroes. Sweep pan ±90 and
    tilt ±30 and confirm the screen/Pi stack, worm, cheeks, axle, cables and bottom head
    edge stay clear (matches the `make check-sweep` gate).

### Order constraints (do NOT reorder)

- Body↔pod join + TT screws (step 3) **before** ULN #1 (step 6): the board blocks cavity access.
- Neck↔platform bolt-up (sub-assembly A) **before** seating on the balls, counterbores face down.
- BBs + cage (step 8) **before** the platform (step 9); power tray + ballast (step 7)
  **before** the belly plate closes the floor.

### Nasty-but-possible steps (measured)

- **Head-clamp grubs (step 12):** 1.5 mm hex key driven blind UP through the motor bay,
  4.0 mm clearance. Kept deliberately: the grubs give continuous tilt-zero trim.

(2026-07-08 passes retired the old tilt-motor-ear reach, the worm-wheel bench grub, the
last-track-pin loop flex, and the 4× 88.5 mm blind screen-standoff screws -- the worst
step in the build is now four short bench screws plus four visible wall screws.)

### Recommendations (bigger than this pass)

- Print a D-bore coupon and dial the axle-flat clearance (modeled at +0.05; +0.15 measured
  as ±4.4° of head backlash) before committing the filed axle.
- Print supports: paint a support enforcer under the neck's two tilt-stop posts (x 20..32,
  z 150..156 -- their outboard halves start mid-air with the neck on its back) and extend
  the clamp-tube supports over the head_back stop fins (55° overhangs feeding a ~0.9 mm
  homing margin; treat the first stall-home angle as calibration). Print the track keepers
  lying on their 13.3×1.9 bar face so the slot-critical 1.9 width is XY-accurate.
- Track gauge is still ~184 vs a 205-wide head (~10 mm overhang/side): widen the gauge or
  accept it (tracked elsewhere).
- If field-servicing the screen without un-gluing the hatch frame matters, notch the frame
  band clear of the 4 channel mouths.

## Wiring

**See firmware/WIRING.md** (2026-07-08) for the full architecture: 12 V PD-trigger input,
dual-buck belly tray (5.1 V Pi rail + 5 V motor rail), what crosses each joint, Pi 5
config flags, connector/labeling rules, and the buy-list delta. Short version: only the
Pi-rail pair crosses tilt; the pan loop carries that pair plus the thin motor-rail/signal
bundle; DSI and CSI ribbons never leave the head.

## Order now (by lead-time importance)

1. **4x F688ZZ flanged bearings** (8x16x5, flange Ø18): most specific part, slowest to source;
   the idler seats are modeled around them (2 per idler since 2026-07-10).
1b. **12x M4x40 + 12 M4 nuts** (road-wheel bolt-axles; partially threaded preferred).
2. **1x TT gearmotor 1:120** matching the owned one (or decide now on 2x N20 metal-gear and
   re-model the motor pocket): blocks the drive train.
3. **Power electronics** (firmware/WIRING.md): a 30W+ USB-C PD brick (the official 27W
   works), 12V PD trigger, XL4015-class 5A buck, MP1584 mini buck, JST-XH kit + crimper,
   1 m 18 AWG silicone pair, 5A blade fuse + holder.
4. **1 m narrow addressable LED strip** (4–5 mm wide, SK6805-2427 / WS2812-2020, ≥160 LED/m),
   one purchase covers the forehead 8-LED segment and the front 7-dot strip. (Alternative:
   widen `led_slot` to ~54x11 and buy two common 8x5050 sticks.)
5. **Ø5 rod ~100 mm** (tilt axle) + **2x M8x20** stub axles if the Bag 13 bolt bag has no M8.
6. **6 mm airsoft BBs** (bag of 100+; need 18): cheap, everywhere.
7. Optional: **HC-SR04P** (3.3V variant) x1, **MAX98357A I2S amp** x1 (pairs with the owned
   8Ω speaker), **amber LEDs** x2–5.

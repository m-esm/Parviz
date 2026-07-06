# Assembly

Current assembly notes for the tracked desk-pi prototype. This is not print-final yet;
the render review still calls for a wider track gauge, real body-to-pod joins, a low
ballast bay, and a covered tilt-motor bracket.

## Bill of materials

Owned quantities cross-checked against the moshes-inventory MCP (2026-07-07).
"Need" is per robot.

### Electronics

| Part | Spec / where it goes | Need | Owned | Buy |
|---|---|---|---|---|
| Raspberry Pi 5 | 2 GB, rides the display's own 58x49 standoffs | 1 | 1 (Tray 1) | — |
| 7" touchscreen | official kit; 4 factory M3 mounts (126.2x65.65) | 1 | 1 (Tray 1) | — |
| Camera Module 3 | recessed forehead, 4x M2 at 21x12.5 | 1 | 1 (Tray 1) | — |
| 27W USB-C PD supply | official 5.1V/5A (see CLAUDE.md; 3A bricks brown out) | 1 | 0 | **1** |
| 28BYJ-48 stepper | 5V, pan + tilt | 2 | 6 (Bag 14) | — |
| ULN2003 driver | one per stepper | 2 | 9 (3 Bag 14 + 6 Bag 5) | — |
| TT gearmotor 1:120 | track drive, one per pod, shaft on X into the sprocket | 2 | 1 (Bag 5) | **1** (match the owned one; or swap both for 2x N20 metal-gear for a lower CoM) |
| MX1588 dual H-bridge | drives both TT motors, skid steer | 1 | 5 (Bag 7) | — |
| WS2812 forehead segment | 8 LEDs in the `led_slot` recess: **42 x 5 mm, 1.5 deep** (model dot pitch 4.6). A standard 8x5050 stick is 53.3 x 10.2 — it does NOT fit. Buy a narrow (4–5 mm wide) addressable strip (SK6805-2427 / WS2812-2020, ≥160 LED/m) and cut an 8-LED segment — or widen `led_slot` to ~54 x 11 for the common stick | 1 seg | 0 | **1 m narrow strip** (also covers the front strip, next row) |
| Front white strip | 7 dots at 5 mm pitch in a 36 x 2.5 lip (`fled_*`) — either 7x 3 mm white LEDs or a second segment cut from the same narrow WS2812 strip | 1 | 0 | covered by the strip above (or 10x 3 mm white LED) |
| Amber indicator LEDs | 2 corner lamps, 12 x 7 windows (`lamp_*`) — 2 rectangular amber LEDs (2x5x7) or 5 mm amber behind a printed lens | 2 | 0 | **2–5** |
| HC-SR04 ultrasonic (optional) | front fascia: Ø16 barrel passes at 26 mm c-c (`us_dx`=±13, `us_d`=16). Buy the **HC-SR04P** (3.3V) variant — the 5V original needs a divider on ECHO for Pi GPIO | 1 | 0 | **1** (optional) |
| Rear pod audio | rear Ø14 cylinder pod (`rear_cyl_*`): an owned Ø12 active buzzer fits for beeps. For real audio, buy a **MAX98357A I2S amp** and drive the owned 8Ω 0.5W mini speaker (Bag 15) from inside the chassis — the speaker is ~40–50 mm and can't live in the pod; the pod becomes the grille | 1 | buzzers: 5x active 5V (Bag 1) + 4x ~12 mm (Bag 16); speaker: 1 (Bag 15) | **1x MAX98357A** (only if speech/audio wanted) |
| Arm actuation | placeholder arms, TBD pending the arm mechanism pass. If actuated: 9x 9g servos owned (5x T-8090, 3x SG90, 1x MG90S) | TBD | 9 servos | nothing yet |

### Bearings, race, axles

| Part | Spec | Need | Owned | Buy |
|---|---|---|---|---|
| 695-2RS | 5x13x4, tilt-axle cheeks | 2 | 30 (Bag 13) | — |
| F688ZZ flanged | 8x16x5, flange Ø18; front idlers (seat Ø15.95 press + 18.5x1.0 flange recess; idler now 30 wide) | 2 | 0 | **2** |
| 6 mm airsoft BBs | pan race, Ø80 circle, `pan_race_n`=18 | 18 | 0 | **smallest bag (100+)** |
| Ø5 rod/tube | tilt axle, ~100 mm (silver steel or alu tube) | 1 | 0 | **1** |
| Ø8 stub axle | idler tension axle, ~20 mm, M3 set-screw lock; a short M8 bolt works | 2 | unknown — the Bag 13 "Machine Bolts" bag may have M8; verify | 2x M8x20 if not |
| 608zz | **not used** in the current design. The "608zz x30" Bag 13 entry is still flagged: photos look like white plastic rings/spacers, NEEDS ID. Don't design around them | 0 | 30? (unverified) | — |

### Fasteners and pins

| Part | Spec | Need | Owned | Buy |
|---|---|---|---|---|
| M3 screws + hex nuts | captive-nut joints everywhere; incl. M3x35 x8 bezel↔back | lots | 540pc M3 stainless kit + 175pc M3 30–50 mm kit + 600pc M2-M5 kit + 1263pc M2-M4 kit (all Tray 1) | — |
| M2 screws | camera board (4) + cam_cover (2) | 6 | in the 600pc M2-M5 and 1263pc M2-M4 kits | — (CLAUDE.md's "buy M2" is stale) |
| M3 nylon standoffs | ULN2003 / driver mounts | few | 380pc kit (Tray 1) | — |
| Track hinge pins | Ø1.75 filament, bore 2.0. 36 links x 2 pods = **72 pins x ~46 mm** (track_width 44.8 + trim) ≈ 3.4 m — cut from an owned spool (the black CR-PETG is tougher than PLA for pins) | 72 | spooled (Tray 1) | — |
| Ø4 dowel pins | body-to-pod join (2 per side) — join not modeled yet; order once it is | 4 | 0 | later |

### Printed parts (watertight; tank base + split head)
- `chassis` — tank body between the tracks; pan motor cavity + pan-mount on top
- `track_L` / `track_R` — tank track pods: 36 links/side on Ø1.75 filament pins, 12T sprocket,
  F688ZZ idler (30 wide, tension slot), plain printed road wheels (2/side, 30 wide)
- `pan_platform` — disc that yaws on the base (central shaft bore + off-axis cable pass)
- `pan_race` / `pan_balls` / `pan_clips` — captured-BB lazy-Susan race and retaining clips
  (18x 6 mm BBs; `pan_balls` is a placeholder for the bought BBs)
- `neck_clevis` — rounded column + two cheeks that rise into the head and drive the tilt axle;
  vertical cable channel
- `head_bezel` — front of the rounded tablet head: screen locator lip, camera aperture,
  forehead LED recess (42x5)
- `head_back` — rear cover: pivot hubs, screen standoffs, Pi bay, cable port, vents
- `cam_cover` — camera board cover and cable trap
- `worm_wheel` / `tilt_worm` — placeholders only; regenerate real teeth before printing
- Cosmetic / design-ref set (render-only today, print with the head): side rails, forehead
  `led_strip`, `antenna_stub` (pure print, no hardware — a real telescopic antenna is owned
  in Bag 15 if ever wanted), `camera_pod` eye shell, rear `trim_hatch_frame`, chassis
  `trim_fascia` + `trim_rear`, and the placeholder gripper arms (mechanism TBD)

## Assembly order (intended)
1. Build the chassis body and track pods. Install the TT motors, rear sprockets, front idlers
   (F688ZZ on Ø8 stub axles), road wheels, and track links on their filament pins. Add the
   body-to-pod M3/dowel joints before printing this for real.
2. Install the pan 28BYJ in the chassis so its offset D-shaft lands on the pan axis. Mount the
   ULN2003 board inside the base.
3. Install the lower pan race, the 18 BBs, pan platform, and retaining clips. Verify the platform
   turns without rubbing the fixed deck or clips.
4. Bolt `neck_clevis` to `pan_platform` on the 3-hole pattern. Route the Pi power service loop
   through the platform slot and neck channel.
5. Press 695-2RS bearings into the neck cheeks. Install the Ø5 tilt axle through the head hubs,
   worm wheel, spacers, and bearings.
6. Mount the tilt 28BYJ and worm on the rear clevis bracket. The visible motor should get a shroud
   or covered service bracket before print-final.
7. Seat the combined touchscreen+Pi module into `head_back` on the four factory M3 mount points.
   The Pi stays on the display's own 58x49 standoffs.
8. Mount the Camera Module 3 in the forehead pier, trap it with `cam_cover`. Seat the WS2812
   segment in the forehead recess and route its 3 wires to the Pi bay, then close the
   `head_bezel` to `head_back`.
9. Fit the fascia electronics if used: HC-SR04P barrels through the Ø16 passes, amber corner
   LEDs, front light strip; buzzer or speaker grille at the rear Ø14 pod.
10. Verify neutral and motion-extreme clearances: pan ±90 and tilt ±30. Check the screen/Pi stack,
    worm, neck cheeks, axle, and bottom head edge.

## Wiring
Only round power wires cross the moving joints. DSI and CSI ribbons stay inside the head because
the Pi rides on the display back.

- Base USB-C/power inlet -> chassis cavity.
- Chassis cavity -> pan service loop.
- Pan service loop -> platform obround slot.
- Platform -> neck cable channel.
- Neck -> bottom-rear head slot, with enough slack for tilt ±30.
- Head-mounted LEDs (forehead WS2812) hang off the Pi's 5V/GPIO in the head — no extra joint
  crossings. Fascia LEDs / HC-SR04 / buzzer wire to the base-side controller.

Add a `firmware/WIRING.md` pin map once the motor driver wiring is chosen.

## Order now (by lead-time importance)

1. **2x F688ZZ flanged bearings** (8x16x5, flange Ø18) — most specific part, slowest to source;
   the idler seats are modeled around them.
2. **1x TT gearmotor 1:120** matching the owned one (or decide now on 2x N20 metal-gear and
   re-model the motor pocket) — blocks the drive train.
3. **Official 27W USB-C PD supply** (5.1V/5A) — not in inventory; nothing runs at full power
   without it.
4. **1 m narrow addressable LED strip** (4–5 mm wide, SK6805-2427 / WS2812-2020, ≥160 LED/m) —
   one purchase covers the forehead 8-LED segment and the front 7-dot strip. (Alternative:
   widen `led_slot` to ~54x11 and buy two common 8x5050 sticks.)
5. **Ø5 rod ~100 mm** (tilt axle) + **2x M8x20** stub axles if the Bag 13 bolt bag has no M8.
6. **6 mm airsoft BBs** (bag of 100+; need 18) — cheap, everywhere.
7. Optional: **HC-SR04P** (3.3V variant) x1, **MAX98357A I2S amp** x1 (pairs with the owned
   8Ω speaker), **amber LEDs** x2–5.

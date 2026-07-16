# Wiring + power (single wall USB-C tether)

Decided 2026-07-08 (maintenance/wiring pass). Power-budget and harness review
findings W1/W2 applied 2026-07-16: default input is 15 V from a 45-65 W PD brick
with hardware current limits independent of firmware; the pan loop uses high-flex
silicone throughout, strain relief at both ends, and day-one I2C twist + pullups.
The robot is powered by ONE USB-C cable from a wall PD brick into the chassis rear
jack. Everything below follows from that.

## Why not 5 V straight through

Three reasons, any one of which is disqualifying:

1. **PD negotiation.** The Pi 5 only unlocks its full budget when it negotiates
   5.1 V / 5 A over the CC lines with the official 27 W brick. A 2-wire VBUS/GND run
   from a chassis jack to the head can't carry that conversation, and the design rule
   is that only round wires cross the pan/tilt joints (no USB-C cable up the neck).
2. **Droop.** 5 A over ~0.8 m round trip of 20 AWG plus 4 connector interfaces drops
   0.3-0.4 V. 5.1 minus 0.4 is brownout territory for a Pi 5 under display + camera
   load.
3. **Motor transients.** Two TT motors stall at 1.5 A+ each. On a shared 5 V rail
   every stall dip lands directly on the Pi.

## Architecture: 15 V in (default), buck down locally

```
wall 45-65 W USB-C PD brick
  └── chassis rear jack (USB-C breakout + PD TRIGGER set to 15 V)
        │  15 V @ up to ~3 A stays in the chassis (crosses NOTHING)
        ├── BUCK A (XL4015-class, 5 A, CC pot set to 5.0 A) -> 5.1 V "PI RAIL",
        │     trimmed to 5.25 V at the tray; 5 A blade fuse inline as fault backstop
        │     └── power pair up the neck -> head -> Pi 5 GPIO 5V/GND pins (both pairs)
        ├── BUCK B (MP1584-class mini) -> 5.0 V "MOTOR RAIL"
        │     ├── ULN2003 #1 (pan stepper, chassis)          [unfused; coil-limited]
        │     ├── ULN2003 #2 (tilt stepper, neck column; 5V rides the pan loop)
        │     ├── POLYFUSE 2 A hold / ~4 A trip (MF-R200 class)
        │     │     └── MX1588 VCC (TT track motors only)
        │     ├── chassis LEDs / HC-SR04P
        │     └── Sense HAT 5V pin (LED matrix; ~40 mA class, 2026-07-14)
        └── (common ground everywhere; star point at the tray)
```

- **PD trigger at 15 V (default):** fixed 12 V is OPTIONAL in the USB-PD spec; many
  generic 45/65 W bricks do not offer it, while PD power rules make **15 V / 3 A
  mandatory on a 45 W brick** (and 20 V / 3.25 A at 65 W). Both bucks accept 15 V
  (XL4015 input to 38 V, MP1584 to 28 V). At the ~34 W worst-case draw, 15 V means
  ~2.3 A on the input pair (the same power at 12 V would be ~2.9 A), with brick
  headroom to 3 A. Spec the wall brick at **45-65 W**.
- **12 V is FALLBACK only:** the official 27 W brick offers 12 V / 2.25 A. Run the
  trigger at 12 V only when stuck on that brick; under 27 W the old strict firmware
  co-scheduling rules become load-bearing again (see Budget + Firmware rules below).
  Prefer buying a 45 W+ brick that advertises 15 V rather than living on the fallback.
- **Buck A (Pi rail):** trimmed to 5.25 V at the tray so the head end sees ~5.1 V
  after the neck run. Only Pi + display + camera + head LEDs load this rail
  (~13-16 W worst case, inside the buck's 25 W envelope). The head cooler fan
  (Joy-IT / official) plugs into the Pi 5's own 4-pin fan header and is counted
  inside the Pi figure (<0.5 W). The Sense HAT's 3V3 sensors ride the Pi's 3V3
  regulator via the neck drop (tens of mA); its 5V LED matrix feeds from Buck B
  locally in the chassis (~40 mA class, 0.95 mA/LED design).
- **Buck B (motor rail):** steppers + TT + chassis accessories. A TT stall folds
  THIS buck's TT branch (polyfuse), not the Pi rail and not the brick. 28BYJ
  ~240 mA each energized, TT ~0.5 A cruise.
- **Budget (honest version, review 2026-07-16):** 45 W at the wall is ~40 W usable
  after ~90 % buck efficiency. Naive worst case now closes with margin:
  Pi rail ~16 W + dual TT stall ~15 W + steppers ~2.4 W + LEDs ~1 W ≈ **34.4 W**
  vs ~40 W usable. The 27 W brick (~24 W after conversion) cannot close that sum
  (Pi 16 + dual TT stall 15 already overshoots); that is why 45 W is the default
  and why hardware current limits (next section) bound the fault even if firmware
  misbehaves. On the 27 W fallback only, re-apply the old co-scheduling as
  load-bearing and never combine ordinary peaks.

## Hard current limiting (independent of firmware)

Principle: **the brick's own OCP must be the LAST limiter to act, never the first.**
A brick fold drops the shared input, which drops motor-rail hold current on the
back-drivable 3-start tilt worm while gravity still pulls the head. Hardware
bounds each rail so a stalled motor cannot fold the brick.

- **Buck A (Pi rail), XL4015 CC trimpot:** buy the CC/CV board variant (two
  trimpots); it has a constant-current limit.
  On the bench, BEFORE connecting the Pi, set the CC limit to **5.0 A**: short the
  output through a series ammeter into a dummy load (or a dead short for the few
  seconds the pot needs), turn the CC pot until the meter reads 5.0 A, then restore
  the CV pot to the 5.25 V trim. The 5 A blade fuse is the fault backstop; the CC
  limit is the working limiter (it folds first on overload, the fuse blows only on
  a real short or a failed CC pot).
- **Motor rail, TT branch polyfuse:** the MP1584 has NO CC limit. Put a **2 A hold /
  ~4 A trip** polyfuse (MF-R200 or similar) on the **TT / MX1588 branch only**,
  between Buck B 5 V and MX1588 VCC. A dual TT stall (3 A+ sustained) trips the
  polyfuse and self-recovers after cool-down instead of folding the shared brick.
  The 28BYJ steppers are inherently coil-limited (~240 mA each energized) and stay
  unfused on the motor rail.
- **Firmware rules stay, demoted to defense-in-depth:** still cap TT PWM at 80 %,
  still never drive both TTs hard while a stepper steps, still stall-home pan/tilt
  at boot with tracks idle. Those rules no longer carry the power budget; the 45 W
  brick + CC pot + polyfuse do. Keep them so ordinary motion stays well under the
  hardware ceilings and the polyfuse rarely trips in normal use.

## Pi 5 configuration (mandatory)

Powering via the GPIO 5V pins bypasses the Pi's PD front end, so it defaults to
600 mA USB current. Set both:

- `/boot/firmware/config.txt`: `usb_max_current_enable=1`
- EEPROM (`sudo rpi-eeprom-config -e`): `PSU_MAX_CURRENT=5000`

Put a 5 A blade fuse inline on the Pi-rail pair at the tray (GPIO power skips the
board's input protection). The fuse is secondary to the XL4015 CC limit above.

## What crosses each joint

| Joint | Wires | Notes |
|---|---|---|
| pan (service loop) | Pi-rail pair (18 AWG silicone) + 5V/GND motor-rail feed for ULN#2 + 4x tilt-stepper IN lines + **I2C drop: 3V3 + SDA + SCL (Sense HAT, 2026-07-14)** | 11 thin + 1 fat pair; ALL high-flex silicone; the 16x8 platform obround and neck channel pass a 5-pos JST-XH head, verified stage 4/6 |
| tilt (drape) | Pi-rail pair ONLY | ribbons (DSI/CSI) never leave the head |

Pan is software-limited to +-90 (hard stops at +-93.3), so the loop never over-winds.
The pan loop flexes over that range daily; PVC hookup wire work-hardens and breaks
at the exit radii -- high-flex silicone is mandatory on every joint-crossing
conductor (see Harness rules).

### Pan homing discipline

The deck posts and platform lug are PLA. Stall impact is cumulative and crushes the
faces, which drifts home zero. Treat the stops as soft plastic, not steel.

- **Home gently.** Run the pan stall at HALF the normal step rate and, if the ULN
  driver / firmware path allows it, at reduced coil current. The 28BYJ through the
  2:1 gear-up multiplies stall force at the stop (~17 mNm at the lug even before a
  hard current push).
- **Cap overtravel.** Command at most ~8 deg past the expected stop position before
  declaring the stall. Never an open-ended sweep into the post.
- **Back off immediately.** After contact, reverse 3.3 deg and call that +-90 (the
  hard stops sit at +-93.3; the software limit is the backed-off pose).
- **Home once per boot.** Do not re-home on every move. Re-home only after a detected
  step-loss event (lost steps, skipped homing lug, encoder/open-loop mismatch if you
  add one later).

## Signals: bundle now, I2C drop NOW (Sense HAT, 2026-07-14)

The Pi lives in the head; the drivers live below. Today: GPIO lines run down the
neck bundle (4 pan-ULN IN + 4 tilt-ULN IN + 2 MX1588 PWM + optional sonar pair).
That is ~10 thin wires in the pan loop -- ugly but passes, and it is zero extra
hardware.

**The Sense HAT Rev2 makes the I2C drop day-one, not an upgrade.** The HAT can NOT
stack on the Pi: the head has no volume above the board (the cooler keep-out owns
the component face at millimeter margins) and stacking would also block the cooler.
It mounts REMOTELY in the chassis on the equipment base (`chassis_base`), where its
IMU is exactly where the awareness plan wants one: rigid, near the pan axis, sensing
BASE motion unpolluted by head moves. Electrically the HAT is pure I2C (0x6a/0x1c
IMU, 0x5c pressure, 0x5f humidity, 0x29 color, 0x46 LED matrix + joystick), so the
drop is 3 thin wires added to the pan loop -- 3V3 + SDA + SCL (ground is already
common) -- plus a LOCAL 5V feed from Buck B for the LED matrix. Do NOT route a
40-pin ribbon down the neck; only round wires cross the joints.

**Bus integrity over the ~0.5 m run (DEFAULT from day one, not an escalation):**
clock I2C at **100 kHz**; twist **SDA with a ground return** and **SCL with a ground
return** (never SDA twisted with SCL); fit **2.2 kΩ pullups to 3V3 at the HAT end**
from day one; keep stubs short. Why default, not optional: ~0.5 m of loop wiring
plus connector transitions approaches the 400 pF bus limit and runs beside stepper
coils, so 100 kHz I2C is EMI-fragile without the twist and the stronger pullups.
The LTC4311-class bus extender is the escalation if the bus is still flaky after
that.

Upgrade path unchanged (when the ULN bundle annoys you): a Pico or PCA9685 in the
chassis on the power tray (stacks on the buck grid with 20 mm standoffs), riding
THE SAME I2C drop (or UART). Then the pan loop shrinks to: Pi-rail pair + 5V/GND +
3V3/SDA/SCL = 7 wires, and the tilt ULN's IN lines come from the chassis board
instead. Mind the address map above when adding devices; note TCS3400 squats 0x29
(collides with a VL53L1X ToF if one ever joins).

## Connectors and harness rules

- Every run that crosses a joint or leaves a board is a **keyed JST-XH** plug (the
  cable passes were sized for XH heads). No soldered runs across joints; a board
  swap is unplug-replug. Crimping needs an XH crimper -- buy one, it pays for
  itself the first time a 28BYJ dies.
- Label both ends of every run (flag labels): `PI-PWR`, `MOT-5V`, `PAN-ULN`,
  `TILT-ULN`, `TT-L`, `TT-R`, `LED-F`.
- 28BYJ phase order matters: the JST-XH keying already prevents reversal; keep the
  factory connector on the motor pigtail.
- **Wire gauges + insulation (all joint-crossing = high-flex silicone):** Pi-rail
  pair **18 AWG silicone**, high strand count; **15 V input 22 AWG** (silicone
  preferred); every pan-loop signal / motor-rail / ULN / I2C conductor **24-26 AWG
  SILICONE**, high strand count. PVC hookup wire work-hardens and breaks at the
  flex points of the ~2-turn pan service loop; do not use it for any joint-crossing
  run.
- **Pan-loop strain relief (both ends, doc-only, no new geometry):**
  - **Bottom end:** zip the loop bundle to the existing 2x Ø3.2 floor-rim zip
    anchors behind the belly opening (x +-6, y -68) so cyclic flex cannot reach the
    buck-tray terminations.
  - **Top end:** zip a stopper tie around the bundle immediately ABOVE the
    platform's 16x8 obround pass, sized so the tie cannot pass through the
    obround. The tie bears on the platform face as a knot; cyclic flexing then
    lives in the mid-loop coils, not at the pass edge.
  - At install, lightly knife-chamfer the printed pass edges so the silicone
    jacket does not frett on a sharp PLA corner.

## Mechanical seats (modeled 2026-07-08; coords refreshed 2026-07-13 against src/)

- **Rear jack + PD trigger:** 2x Ø1.7 M2 self-tap pilots flank the USB slot on the
  rear wall's interior face at **x -38 +-9, z0+24** (slot + pilots moved off wall
  center 2026-07-11, the rear HC-SR04 owns x 0; old "(x +-9, z 19)" is stale); the
  trigger's jack aligns with the slot through the rear-left prow-cheek corridor.
  Trigger default = **15 V** (see Architecture); 12 V only for the 27 W fallback.
- **Strain relief:** 2x Ø3.2 zip anchors through the floor rim behind the belly
  opening (x +-6, y -68). Zip the incoming wall cable BEFORE the jack: a yanked
  tether loads the tie, not the board. The same anchors also hold the pan-loop
  bundle bottom end (Harness rules above).
- **Power tray:** Buck A mounts on a 40x20 Ø2.5-pilot grid on the belly plate's
  rear bay; Buck B zip-ties to the 2x Ø3.2 anchors beside it (x 20/34, y -58).
  Dropping the belly plate (6x M3) drops the whole power stage for service --
  leave 60 mm of harness slack on every tray run. Buck A sits component-side-up on
  the posts, so with the plate bolted shut its trimpots face the closed chassis
  interior: ALL voltage AND CC adjustment happens with the plate dropped (see
  Bringup). The TT polyfuse lives on the tray in series with the MX1588 feed.
- **Driver mounts:** ULN#1 on the chassis standoffs at (38, 20); MX1588 on the
  `uln2_c` standoffs at **(0, 80)** (moved 2026-07-11, dual-drive pass; old (-38, 45)
  is stale); tilt ULN on the neck-column standoffs, board centered at z 93 (dropped
  from 110: the tilt_carrier occupies z 113..153 in the same y band; rides the pan
  frame).
- **Sense HAT seat (pending CAD, 2026-07-14):** goes on the removable
  `chassis_base` equipment base -- exactly the in-flux-mount case the base exists
  for. Next base iteration replaces the (14,-12) IMU posts with 4x M2.5 standoffs
  on the HAT's 58x49 pattern (65x56.5 outline), LED matrix + joystick facing UP
  under the deck (service = lift the deck). Measure the delivered board first
  (VERIFY_ON_ARRIVAL); reprint is one small flat plate.

## Tilt homing + hold (firmware rules)

The head's clamp-tube fins stall against the neck cheek posts at +-33.8 deg (hard
stops; PLA-on-PLA). Contact planes are the post z-faces and the fins' angular faces
-- the 2026-07-16 crush-harden only grew the contact AREA along X (fins |x| 26.5..32,
1.375x width; inboard 0.5 running-clear of the cheek face), not the first-contact angle. Treat
the stops as sacrificial homing surfaces, not as day-to-day travel limits.

Rules for the tilt axis (pan is analogous against its deck posts at +-93.3):

1. **Stall-home at reduced drive only.** Half-stepping (or the coarsest microstep
   that still self-starts), lowest reliable coil current, and <= half the normal
   step rate. Full-current full-speed rams crush the small PLA patches and the
   home zero drifts.
2. **Home once per boot, not per move.** After stall, back off ~2 deg and set
   zero there. Do not re-seek the hard stop on every motion.
3. **Software-limit travel to +-30 deg.** That leaves the ~3.8 deg gap to the
   hard stops so they are homing-only. Never run a full-speed trajectory into
   the posts.
4. **Hold / park.** The 3-start worm (PARAMS `worm_starts`=3) back-drives --
   its lead is about 23 deg, so there is no unpowered self-lock. ALWAYS
   energize-hold whenever the head sits off its balance point. Park at the
   balance point before long idle and before power-off. Detent plus gear friction
   gives only about 27-54 mNm at the axle, so an unpowered off-balance head may
   nod. If the docs/ASSEMBLY.md bench coupon fails its decision rule, the committed
   single-start pair in docs/WORM.md restores mechanical self-locking.
5. **Wear.** If home zero drifts over months, inspect the fin faces and the post
   tops on the bench. Escalation path: a replaceable stop-cap on the posts
   (print-3 option, deliberately not modeled now) -- see docs/ASSEMBLY.md.

## Bringup order (first power)

Do this in sequence; the trimpot access constraint above makes the order load-bearing.

1. **PD trigger alone:** plug the brick in and meter the trigger output BEFORE wiring
   anything downstream. Confirm **15 V** (default brick), not a 5/9/12/20 V
   misconfiguration. On the 27 W fallback only, confirm 12 V instead.
2. **Set Buck A with the Pi rail DISCONNECTED.** Belly plate dropped and hanging on
   its harness slack (trimpot face-up toward you), power up and trim to 5.25 V
   unloaded. Then set the CC pot to 5.0 A into a series-metered dummy load / short
   (see Hard current limiting). Never trim with the Pi attached; a slipped CV
   trimpot sweep can cross 6 V+.
3. **Verify under load:** put a ~2 A dummy load (power resistor or USB load tester on
   a spare pigtail) on Buck A and confirm it still reads >= 5.15 V at the tray.
   XL4015 clones vary; a board that droops here browns the Pi later under camera +
   display load.
4. **Set Buck B to 5.0 V** the same way, steppers and MX1588 unplugged. Confirm the
   TT polyfuse is in series with the MX1588 feed before motors go on.
5. **Only now connect the Pi-rail pair** (5 A fuse inline) and boot. Check
   `vcgencmd get_throttled` returns 0x0 with display + camera running.
6. **Motors last:** steppers first, then TTs, watching the rails on a meter during
   the first moves. Then bolt the belly plate shut.
7. **Brownout test (both rails instrumented):** leave meters on both rails at the
   tray (or a 2-ch scope), then in sequence: (a) single TT stall at 80 % PWM (grab
   the sprocket), (b) dual TT stall, (c) dual TT stall while the tilt stepper holds
   the head ~30 deg off balance. **PASS:** Pi rail never below 5.0 V at the tray;
   `vcgencmd get_throttled` stays 0x0 through all three; the polyfuse trips on the
   sustained dual stall and recovers after cool-down; the held tilt does not slip
   more than ~2 deg during any event. The tilt case exists because a motor-rail
   brownout drops hold torque on the back-drivable 3-start worm while gravity still
   pulls -- that is the failure the polyfuse and brick margin are there to prevent.

## Buy list delta

- **45-65 W USB-C PD brick** that advertises **15 V** (default). The official 27 W
  brick is fallback-only (12 V / 2.25 A, strict co-scheduling load-bearing again).
- **PD trigger board set to 15 V** (or solder-jumper type; keep 12 V as the
  documented fallback jumper position only).
- XL4015 5 A buck module, **the CC/CV variant with TWO trimpots** (the CV-only
  board has no current limit and cannot satisfy the hard-limiting rule); set the
  CC pot to 5.0 A on the bench.
- MP1584 mini buck.
- **Polyfuse 2 A hold / ~4 A trip (MF-R200 or similar)** on the TT / MX1588 branch.
- JST-XH kit + crimper.
- **High-flex silicone wire, high strand count:** 18 AWG pair (1 m red/black) for
  the Pi rail; 24-26 AWG silicone for every pan-loop signal / motor / I2C run
  (PVC banned on joint crossings).
- Inline blade-fuse holder (the 5 A blade fuse itself is owned -- ATC/ATO
  assortment, inventory re-audit 2026-07-13).
- 2.2 kΩ pullups x2 for the HAT-end I2C (day-one default).

The owned LM2596 / selectable-output bucks are 2-3 A class: not a Buck A
substitute, but a selectable-5V module can stand in for the MP1584 as Buck B.

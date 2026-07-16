# Wiring + power (single wall USB-C tether)

Decided 2026-07-08 (maintenance/wiring pass). The robot is powered by ONE USB-C cable
from a wall PD brick into the chassis rear jack. Everything below follows from that.

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

## Architecture: 12 V in, buck down locally

```
wall 27W+ USB-C PD brick
  └── chassis rear jack (USB-C breakout + PD TRIGGER set to 12 V)
        │  12 V @ up to 2.25 A crosses NOTHING (stays in the chassis)
        ├── BUCK A (XL4015-class, 5 A) -> 5.1 V "PI RAIL", trimmed to 5.25 V at the tray
        │     └── power pair up the neck -> head -> Pi 5 GPIO 5V/GND pins (both pairs)
        ├── BUCK B (MP1584-class mini) -> 5.0 V "MOTOR RAIL"
        │     ├── ULN2003 #1 (pan stepper, chassis)
        │     ├── ULN2003 #2 (tilt stepper, neck column; 5V rides the pan loop)
        │     ├── MX1588 VCC (TT track motors)
        │     ├── chassis LEDs / HC-SR04P
        │     └── Sense HAT 5V pin (LED matrix; ~40 mA class, 2026-07-14)
        └── (common ground everywhere; star point at the tray)
```

- **PD trigger at 12 V:** the official 27 W brick offers 12 V / 2.25 A. 12 V into the
  chassis means ~2 A on the input wires instead of 5 A, and ANY 30 W+ PD brick works,
  not just the one blessed Raspberry Pi unit.
- **Buck A (Pi rail):** trimmed to 5.25 V at the tray so the head end sees ~5.1 V
  after the neck run. Only Pi + display + camera + head LEDs load this rail
  (~13-16 W worst case, inside the buck's 25 W envelope). The head cooler fan
  (Joy-IT / official) plugs into the Pi 5's own 4-pin fan header and is counted
  inside the Pi figure (<0.5 W). The Sense HAT's 3V3 sensors ride the Pi's 3V3
  regulator via the neck drop (tens of mA); its 5V LED matrix feeds from Buck B
  locally in the chassis (~40 mA class, 0.95 mA/LED design).
- **Buck B (motor rail):** steppers + TT + chassis accessories. A TT stall folds
  THIS buck, not the Pi rail. 28BYJ ~240 mA each energized, TT ~0.5 A cruise.
- **Budget (honest version, review 2026-07-08):** 27 W at the wall is ~24 W after ~90 %
  buck efficiency. Pi rail worst ~16 W already eats two thirds of that, and a DUAL TT
  stall is >15 W on its own -- the naive worst case is over budget and the firmware
  rules are load-bearing, not advisory: cap TT PWM at 80 %, never drive both TTs hard
  while a stepper steps, and stall-home (pan/tilt hard stops) at boot with tracks idle.
  If the input brick folds anyway, buck B browns first and the Pi rail survives -- that
  is the point of the split.

## Pi 5 configuration (mandatory)

Powering via the GPIO 5V pins bypasses the Pi's PD front end, so it defaults to
600 mA USB current. Set both:

- `/boot/firmware/config.txt`: `usb_max_current_enable=1`
- EEPROM (`sudo rpi-eeprom-config -e`): `PSU_MAX_CURRENT=5000`

Put a 5 A blade fuse inline on the Pi-rail pair at the tray (GPIO power skips the
board's input protection).

## What crosses each joint

| Joint | Wires | Notes |
|---|---|---|
| pan (service loop) | Pi-rail pair (18 AWG silicone) + 5V/GND motor-rail feed for ULN#2 + 4x tilt-stepper IN lines + **I2C drop: 3V3 + SDA + SCL (Sense HAT, 2026-07-14)** | 11 thin + 1 fat pair; the 16x8 platform obround and neck channel pass a 5-pos JST-XH head, verified stage 4/6 |
| tilt (drape) | Pi-rail pair ONLY | ribbons (DSI/CSI) never leave the head |

Pan is software-limited to +-90 (hard stops at +-93.3), so the loop never over-winds.

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

Bus integrity over the ~0.5 m run: clock I2C at 100 kHz, twist SDA and SCL each
with a ground return, and keep the stubs short. If the bus is flaky on hardware,
add 2.2 kΩ pullups to 3V3 at the HAT end; the LTC4311-class bus extender is the
escalation, not the default.

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
- Wire gauges: Pi-rail pair 18 AWG silicone; 12 V input 22 AWG; everything else
  24-26 AWG.

## Mechanical seats (modeled 2026-07-08; coords refreshed 2026-07-13 against src/)

- **Rear jack + PD trigger:** 2x Ø1.7 M2 self-tap pilots flank the USB slot on the
  rear wall's interior face at **x -38 +-9, z0+24** (slot + pilots moved off wall
  center 2026-07-11, the rear HC-SR04 owns x 0; old "(x +-9, z 19)" is stale); the
  trigger's jack aligns with the slot through the rear-left prow-cheek corridor.
- **Strain relief:** 2x Ø3.2 zip anchors through the floor rim behind the belly
  opening (x +-6, y -68). Zip the incoming cable BEFORE the jack: a yanked tether
  loads the tie, not the board.
- **Power tray:** Buck A mounts on a 40x20 Ø2.5-pilot grid on the belly plate's
  rear bay; Buck B zip-ties to the 2x Ø3.2 anchors beside it (x 20/34, y -58).
  Dropping the belly plate (6x M3) drops the whole power stage for service --
  leave 60 mm of harness slack on every tray run. Buck A sits component-side-up on
  the posts, so with the plate bolted shut its trimpot faces the closed chassis
  interior: ALL voltage adjustment happens with the plate dropped (see Bringup).
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

## Bringup order (first power)

Do this in sequence; the trimpot access constraint above makes the order load-bearing.

1. **PD trigger alone:** plug the brick in and meter the trigger output BEFORE wiring
   anything downstream. Confirm 12 V, not a 5/9/15/20 V misconfiguration.
2. **Set Buck A with the Pi rail DISCONNECTED.** Belly plate dropped and hanging on
   its harness slack (trimpot face-up toward you), power up and trim to 5.25 V
   unloaded. Never trim with the Pi attached; a slipped trimpot sweep can cross 6 V+.
3. **Verify under load:** put a ~2 A dummy load (power resistor or USB load tester on
   a spare pigtail) on Buck A and confirm it still reads >= 5.15 V at the tray.
   XL4015 clones vary; a board that droops here browns the Pi later under camera +
   display load.
4. **Set Buck B to 5.0 V** the same way, steppers and MX1588 unplugged.
5. **Only now connect the Pi-rail pair** (5 A fuse inline) and boot. Check
   `vcgencmd get_throttled` returns 0x0 with display + camera running.
6. **Motors last:** steppers first, then TTs, watching the rails on a meter during
   the first moves. Then bolt the belly plate shut.

## Buy list delta

PD trigger board set to 12 V (or solder-jumper type), XL4015 5 A buck module,
MP1584 mini buck, JST-XH kit + crimper, 18 AWG silicone wire (1 m red/black),
inline blade-fuse holder (the 5 A blade fuse itself is owned -- ATC/ATO assortment,
inventory re-audit 2026-07-13). The official 27 W supply stays on the list (any
30 W+ PD brick also works now). The owned LM2596 / selectable-output bucks are
2-3 A class: not a Buck A substitute, but a selectable-5V module can stand in for
the MP1584 as Buck B.

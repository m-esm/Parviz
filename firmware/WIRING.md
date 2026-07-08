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
        │     └── chassis LEDs / HC-SR04P
        └── (common ground everywhere; star point at the tray)
```

- **PD trigger at 12 V:** the official 27 W brick offers 12 V / 2.25 A. 12 V into the
  chassis means ~2 A on the input wires instead of 5 A, and ANY 30 W+ PD brick works,
  not just the one blessed Raspberry Pi unit.
- **Buck A (Pi rail):** trimmed to 5.25 V at the tray so the head end sees ~5.1 V
  after the neck run. Only Pi + display + camera + head LEDs load this rail
  (~13-16 W worst case, inside the buck's 25 W envelope).
- **Buck B (motor rail):** steppers + TT + chassis accessories. A TT stall folds
  THIS buck, not the Pi rail. 28BYJ ~240 mA each energized, TT ~0.5 A cruise.
- **Budget:** 27 W total. Pi rail worst ~16 W + motor rail worst ~9 W = 25 W. Firmware
  rule: never drive both TT motors at 100 % duty while a stepper is stepping; cap TT
  PWM at 80 %. Stall-homing (pan/tilt hard stops) happens at boot with tracks idle.

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
| pan (service loop) | Pi-rail pair (18 AWG silicone) + 5V/GND motor-rail feed for ULN#2 + 4x tilt-stepper IN lines (or SDA/SCL, see below) | 8 thin + 1 fat pair; the 16x8 platform obround and neck channel pass a 5-pos JST-XH head, verified stage 4/6 |
| tilt (drape) | Pi-rail pair ONLY | ribbons (DSI/CSI) never leave the head |

Pan is software-limited to +-90 (hard stops at +-93.3), so the loop never over-winds.

## Signals: bundle now, I2C drop later

The Pi lives in the head; the drivers live below. Today: GPIO lines run down the
neck bundle (4 pan-ULN IN + 4 tilt-ULN IN + 2 MX1588 PWM + optional sonar pair).
That is ~10 thin wires in the pan loop -- ugly but passes, and it is zero extra
hardware.

Upgrade path (when the bundle annoys you): a Pico or PCA9685 in the chassis on the
power tray (stacks on the buck grid with 20 mm standoffs), talking UART or I2C to
the Pi. Then the pan loop shrinks to: Pi-rail pair + 5V/GND + SDA/SCL (or TX/RX) =
6 wires, and the tilt ULN's IN lines come from the chassis board instead.

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

## Mechanical seats (modeled 2026-07-08)

- **Rear jack + PD trigger:** 2x Ø1.7 M2 self-tap pilots flank the USB slot on the
  rear wall's interior face (x +-9, z 19); the trigger's jack aligns with the slot.
- **Strain relief:** 2x Ø3.2 zip anchors through the floor rim behind the belly
  opening (x +-6, y -68). Zip the incoming cable BEFORE the jack: a yanked tether
  loads the tie, not the board.
- **Power tray:** Buck A mounts on a 40x20 Ø2.5-pilot grid on the belly plate's
  rear bay; Buck B zip-ties to the 2x Ø3.2 anchors beside it (x 20/34, y -58).
  Dropping the belly plate (6x M3) drops the whole power stage for service --
  leave 60 mm of harness slack on every tray run.
- **Driver mounts:** ULN#1 on the chassis standoffs at (38, 20); MX1588 on the
  `uln2_c` standoffs at (-38, 45); tilt ULN on the neck-column standoffs (rides
  the pan frame).

## Buy list delta

PD trigger board set to 12 V (or solder-jumper type), XL4015 5 A buck module,
MP1584 mini buck, JST-XH kit + crimper, 18 AWG silicone wire (1 m red/black),
5 A blade fuse + inline holder. The official 27 W supply stays on the list (any
30 W+ PD brick also works now).

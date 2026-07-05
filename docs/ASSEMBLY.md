# Assembly (stub)

Fill in as parts get designed. For now this records the intended BOM and stack order.

## Bill of materials

### Electronics (owned / to source)
- Raspberry Pi 5
- Official Raspberry Pi 7" touchscreen (reference CAD in `reference/rpi-7in-touchscreen-model/`)
- Raspberry Pi Camera Module 3
- Official Raspberry Pi 27W USB-C PD power supply (5.1V / 5A) — see CLAUDE.md
- Pan servo — TBD
- Tilt servo — TBD
- Slew bearing / bushing for pan — TBD

### Printed parts (first pass, watertight; not print-split yet)
- `base` — fixed base, pan motor + bearing seat, bottom = future-wheels M4 bolt flange
- `pan_platform` — disc that yaws on the base
- `neck_clevis` — column + two cheeks that rise into the head and drive the tilt axle
- `head_shell` — Echo-Show wedge holding the 7" screen (front aperture) + camera nub
- tilt axle — off-the-shelf rod / M6 (not printed)

## Assembly order (intended)
1. Pan servo + bearing into `base_plinth`.
2. `neck_pan_column` onto the pan output.
3. Tilt servo into the top of the neck column.
4. Head shell onto the tilt output; seat the screen, route the ribbon + camera cable down
   the neck to the Pi.
5. Pi + power: mount the Pi behind the head shell or in the base (TBD — cable length vs
   moving mass tradeoff).

## Wiring
TBD — add a pin map here (or a `firmware/WIRING.md`) once the servo driver is chosen.

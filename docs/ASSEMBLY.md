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

### Printed parts (watertight; head is split for the screen)
- `base` — hollow truncated cone (Ø208→Ø156), pan motor cavity, bottom = future-wheels M4 flange
- `pan_platform` — disc that yaws on the base (central shaft bore + off-axis cable pass)
- `neck_clevis` — rounded column + two cheeks that rise into the head and drive the tilt axle;
  vertical cable channel
- `head_bezel` — front of the Echo-Show wedge: leaned face, screen-retaining lip, camera nub
- `head_back` — rear cover: pivot hubs, neck slot, Pi bay, cable port
- tilt axle — off-the-shelf hollow tube / M6 (not printed; cables pass through it)

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

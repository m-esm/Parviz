# Assembly

Current assembly notes for the tracked desk-pi prototype. This is not print-final yet;
the render review still calls for a wider track gauge, real body-to-pod joins, a low
ballast bay, and a covered tilt-motor bracket.

## Bill of materials

### Electronics (owned / to source)
- Raspberry Pi 5
- Official Raspberry Pi 7" touchscreen (reference CAD in `reference/rpi-7in-touchscreen-model/`)
- Raspberry Pi Camera Module 3
- Official Raspberry Pi 27W USB-C PD power supply (5.1V / 5A) — see CLAUDE.md
- 28BYJ-48 stepper for pan, plus ULN2003 driver
- 28BYJ-48 stepper for tilt, plus ULN2003 driver
- 2x TT gearmotor for track drive (currently only one is owned; buy a matched second motor)
- MX1588 or equivalent dual H-bridge for the two track motors
- 6 mm airsoft BBs for the captured pan race
- 2x F688ZZ flanged bearings for the front idlers
- 695-2RS bearings for the tilt axle cheeks
- Ø5 rod/tube for the tilt axle
- M3 fasteners and captive hex nuts for printed joints; M2 fasteners for the camera

### Printed parts (watertight; tank base + split head)
- `chassis` — tank body between the tracks; pan motor cavity + pan-mount on top
- `track_L` / `track_R` — tank track pods (stadium belt loops + hub caps)
- `pan_platform` — disc that yaws on the base (central shaft bore + off-axis cable pass)
- `pan_race` / `pan_balls` / `pan_clips` — captured-BB lazy-Susan race and retaining clips
- `neck_clevis` — rounded column + two cheeks that rise into the head and drive the tilt axle;
  vertical cable channel
- `head_bezel` — front of the rounded tablet head: screen locator lip and camera aperture
- `head_back` — rear cover: pivot hubs, screen standoffs, Pi bay, cable port, vents
- `cam_cover` — camera board cover and cable trap
- `worm_wheel` / `tilt_worm` — placeholders only; regenerate real teeth before printing

## Assembly order (intended)
1. Build the chassis body and track pods. Install the TT motors, rear sprockets, front idlers,
   road wheels, and track links. Add the body-to-pod M3/dowel joints before printing this for real.
2. Install the pan 28BYJ in the chassis so its offset D-shaft lands on the pan axis. Mount the
   ULN2003 board inside the base.
3. Install the lower pan race, BBs, pan platform, and retaining clips. Verify the platform turns
   without rubbing the fixed deck or clips.
4. Bolt `neck_clevis` to `pan_platform` on the 3-hole pattern. Route the Pi power service loop
   through the platform slot and neck channel.
5. Press 695-2RS bearings into the neck cheeks. Install the Ø5 tilt axle through the head hubs,
   worm wheel, spacers, and bearings.
6. Mount the tilt 28BYJ and worm on the rear clevis bracket. The visible motor should get a shroud
   or covered service bracket before print-final.
7. Seat the combined touchscreen+Pi module into `head_back` on the four factory M3 mount points.
   The Pi stays on the display's own 58x49 standoffs.
8. Mount the Camera Module 3 in the forehead pier, trap it with `cam_cover`, then close the
   `head_bezel` to `head_back`.
9. Verify neutral and motion-extreme clearances: pan ±90 and tilt ±30. Check the screen/Pi stack,
   worm, neck cheeks, axle, and bottom head edge.

## Wiring
Only round power wires cross the moving joints. DSI and CSI ribbons stay inside the head because
the Pi rides on the display back.

- Base USB-C/power inlet -> chassis cavity.
- Chassis cavity -> pan service loop.
- Pan service loop -> platform obround slot.
- Platform -> neck cable channel.
- Neck -> bottom-rear head slot, with enough slack for tilt ±30.

Add a `firmware/WIRING.md` pin map once the motor driver wiring is chosen.

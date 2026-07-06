# Arm mechanism (task #20): rigid vs posable vs actuated

Scope: the two gripper arms built by `build_arms()` in `src/build.py`. They mount on the head's
side rails (rail face x ±107.5, arm plane x ±127, standoff span 19.5 mm), so they ride the pan
AND tilt joints. Every option below is judged against the tilt worm drive, the joint that
actually carries them.

## Measured baseline (from the neutral-pose geometry, not the posed GLB)

Computed by loading `build_arms()` directly (the committed `web/assembly.glb` is posed at
pan 22 / tilt -12, which skews per-arm centroids; neutral-pose numbers below).

| quantity | value |
|---|---|
| volume per arm (watertight) | 23.9 cm³ |
| solid PLA (1.24 g/cm³) | 29.7 g/arm |
| printed, 2 walls + 30% infill (eff. 0.45 to 0.60 of solid) | **13.4 to 17.8 g/arm, ~15 g nominal** |
| both arms, printed | **27 to 36 g** |
| arm CoM, neutral pose | (±125.5, +18.6, +170.7) |
| lever about tilt axis (y -18, z 153) | dy +36.6 mm horizontal, r 40.6 mm total |
| lever about shoulder (y 0, z 130) | 44.7 mm |

## Tilt-worm load budget

Gravity moment the arms add about the tilt axle (both arms, they are symmetric so pan position
does not matter):

| print | neutral tilt | worst tilt angle (full r as lever) |
|---|---|---|
| 30% infill (~15 g/arm) | 10.7 mN·m | 11.8 mN·m |
| solid (29.7 g/arm) | 21.3 mN·m | 23.7 mN·m |

Available torque at the axle: 28BYJ-48 usable 30 to 35 mN·m, times the 12:1 wheel, times
single-start worm efficiency 0.35 to 0.45 = **126 to 189 mN·m at the axle**.

- Holding is free (self-locking worm), as designed.
- Swinging: arms consume 6 to 9% of axle torque at 30% infill, 13 to 19% if printed solid.
  **Margin is fine.** The head must stay roughly pre-balanced as CLAUDE.md already requires;
  the arms are a small perturbation on top of that, not the dominant load.
- Caveat: the arm CoM sits 36.6 mm FORWARD of the tilt axis, so both arms add a constant
  ~11 mN·m nose-down bias. Re-trim the head balance for it (slide the Pi/ballast back a few mm
  or accept the bias, it is well inside the budget either way). The worm holds it de-energized
  regardless.
- Pan: added inertia 4.8e-4 kg·m² (CoM at r 127 from the pan axis). At a brisk 3 rad/s²
  that is 1.5 mN·m against the pan 28BYJ's ~30 mN·m. Negligible.

## Option A: rigid single-print (current placeholder, formalized)

Each arm stays one body in the raised pose. Zero hardware, zero wiring, zero new failure modes.
The numbers above show the tilt worm does not care. This is fully adequate for v1: the arms are
a styling element and the raised pose already clears the pods at every pan x tilt combination
(that is why the pose exists, see the `build_arms()` docstring).

One change now (see "print differently today" below): make the arm a **bolt-on module**, not
fused to the head, so options B and C retrofit without reprinting `head_back`.

## Option B: hand-posable friction/detent joints

For photo-posing and desk expressiveness without electronics.

- **Shoulder (pitch about X), the DoF that matters.** Split the arm at the shoulder disc:
  standoff-side clutch disc + arm-side clutch disc, mating faces carry 12 radial teeth
  (30° indexing) or a smooth friction face for continuous posing. M3×16 through the shoulder
  axis into a captive nut, preloaded through a printed wave washer (or a rubber M3 washer,
  which holds its preload better than PLA creep). Target breakaway ~50 to 100 mN·m: gravity on
  the arm about the shoulder is only 6.6 mN·m, so 8 to 15x margin against droop from track
  vibration, still an easy two-finger repose.
- **Elbow (pitch about X), second priority.** Same disc pair at the 9.5 mm elbow joint, smaller
  teeth. Gravity load about the elbow is ~2 mN·m; even a light preload holds.
- **Skip the wrist.** Claw orientation is cosmetic; a third clutch adds slop and print fiddle
  for nothing.
- Cost: 2× M3 + nylock + washer per arm, ~2 g extra plastic per joint. Tilt-worm impact:
  effectively unchanged from option A (the hardware adds ~4 g/arm near the shoulder, under
  1 mN·m about the tilt axis).
- Known risk: PLA clutch faces creep and lose preload over weeks. Detent teeth fix that
  (position held by geometry, not friction), at the price of 30° granularity. Ship teeth.

## Option C: actuated, smallest sensible = one SG90 per shoulder

**One DoF per arm (shoulder swing) is enough for expressiveness.** Prior art agrees: Anki
Cozmo/Vector get their entire body language from a single 1-DoF lift plus head pitch; here
pan + tilt + track motion already exist, so arm raise/wave/droop/point completes the vocabulary.
An elbow servo doubles wiring and mass for a marginal gain. Do not do 2-DoF arms.

### Actuator choice, checked against the moshes-inventory MCP (2026-07-07)

| owned | qty | mass | torque | verdict |
|---|---|---|---|---|
| Cytron T-8090 (SG90 clone) | 5, Bag 2 | ~9 g | ~1.8 kg·cm (176 mN·m) @ 4.8 V | **use these** |
| Tower Pro SG90 (blue) | 3, Bag 14 | ~9 g | ~1.8 kg·cm | same part |
| SG90 (other brand) | 1, Bag 14 | ~9 g | ~1.8 kg·cm | spare |
| MG90S metal gear | 1, Bag 14 | ~13.4 g | ~2.2 kg·cm | overkill; keep for the claw if ever |
| 28BYJ-48 spare | 4 of 6, Bag 14 | ~35 g | ~30 mN·m | **rejected, see below** |
| ULN2003 boards | 9 (3 + 6) | | | pan/tilt use 2, plenty spare |

Required shoulder torque: 6.6 mN·m to swing the bare arm, 24 mN·m with a 20 g object in the
claw at full reach. An SG90's 176 mN·m gives 7 to 27x margin. Buy nothing.

**28BYJ at the shoulder does not fit and should not fit.** The standoff span (rail face 107.5
to arm plane 127) is 19.5 mm; the motor can is Ø28.25 x 18.8 with mounting ears at 35 mm, and
it weighs ~35 g against the arm's 15 g. It would more than triple the outboard mass (35 g at
x ±110+, tilt moment contribution alone ~2x the whole arm's) and need its own ULN2003 in the
head. Wrong tool; the 28BYJs stay on pan, tilt, and the spares shelf.

### Packaging: rotating-body servo in the arm's shoulder hub

The naive layout (servo in the standoff, shaft along X) fails: the SG90 is 31 mm along its
shaft axis and only 19.5 mm exists between rail face and arm plane. Pocketing it inside the
head fails too: interior width is 197 mm and the screen module is 192.96 wide, ~2 mm/side at
shoulder height. Two layouts that do work:

1. **Preferred: fixed horn, rotating body.** Bolt the servo horn to the (static) standoff face
   on the shoulder axis; embed the servo body in the arm's shoulder end, which grows from the
   r11 disc to a ~26 x 24 x 14 box (the SG90 is 22.2 x 11.8 in footprint, 11.8 fits inside the
   arm-plane thickness). The servo rotates itself plus the arm around the fixed horn. No change
   to `arm_x`, no change to the head silhouette. The lead exits the arm at the shoulder and
   immediately enters the rail wall (see wiring).
2. Fallback: push `arm_x` from 127 to ~139 and house the servo in a fattened standoff pod,
   shaft outboard. Costs 12 mm of overhang per side on a head that already overhangs the
   tracks ~10 mm/side. Only if layout 1's rotating lead proves annoying.

Added mass: servo 9 g + horn/screws ~2 g + pocket rework ~3 g = **~14 g/arm**, sitting near the
shoulder (r 29 mm from the tilt axis), adding at most 8 mN·m for both arms. Combined with the
arms themselves the whole actuated system stays under ~20 mN·m of the 126+ mN·m axle budget.

### Wiring (and the no-joint-crossing confirmation)

Confirmed: **the arms are head-mounted, so arm wiring crosses ZERO joints.** They pan and tilt
with the head; the Pi is also in the head. The route: servo lead (3-core) from the shoulder,
through a Ø6 hole in the head side wall hidden behind the orange rail, into the rear head
cavity (behind the screen module, y < -14 is free), to the Pi. Total run ~15 cm, static, no
drape, no service loop. Signal from two GPIO PWM pins (or the existing PWM channels); power the
two servos from the 5 V rail through their own filtered branch, stall is ~650 mA each and two
stalled servos plus screen plus camera is exactly the brownout scenario the 27 W PD supply was
chosen for. Software-limit the sweep so a claw can never reach the pods (the raised-pose
clearance analysis assumed a fixed arm).

## Recommendation for v1, and what to print differently today

**Ship v1 with option A (rigid, raised pose), but print the interface for option C now:**

1. **Make the arm a separable bolt-on, not part of the head print.** Give the side rail /
   head_back a flat mounting pad with 2× M3 captive-nut bosses (vertical pair, 16 mm apart,
   centered on the shoulder axis at y 0, z 130). v1 arm prints as one rigid body with a
   matching 2-hole flange on its standoff root. Options B and C then bolt onto the same pad,
   and a broken arm (the most snag-prone part on the robot) is a 24 g reprint instead of a
   head_back reprint.
2. **Drill the servo lead pass now.** Ø6 through-hole in the head side wall behind the rail,
   at the shoulder position, with a printed blanking plug for v1. Retrofitting option C then
   touches zero head parts.
3. Print arms at ~30% infill, 2 walls; do not print solid (doubles the tilt bias for no
   stiffness you need).
4. When the upgrade itch hits, go straight to option C with the owned SG90s (fixed-horn,
   rotating-body layout, one per shoulder). Option B is a decent halfway house only if you
   want posable arms before you want wiring; it uses the same bolt-on pad either way.

The tilt worm is not the constraint at any point in this path: worst case (solid arms plus
servos) stays under 20% of available axle torque, and holding torque is free by design.

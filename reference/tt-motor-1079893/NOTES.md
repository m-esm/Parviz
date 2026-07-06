# TT gearmotor reference measurements (Thingiverse 1079893, DC_Motor_20mm)

Measured 2026-07-06 from `files/DC_Motor_20mm.STEP` (exact B-rep read via cadquery-ocp:
analytic cylinder radii/axes + planar face positions) and cross-checked with
`files/DC_Motor_20mm.STL` (trimesh bbox + cross-section slices). STEP and STL agree to
0.01 mm on every probed dimension. Source per number: STEP B-rep unless marked (STL).

## File axes convention

STEP frame: **X = motor long axis** (+X toward the gearbox front tab, -X toward the
motor can), **Y = width** (symmetric, +/-11.20), **Z = output shaft axis**. The output
shaft exits **-Z only** (single-ended in this CAD; the commonly sold TT part is
dual-shaft, see corrections). The STL is the same geometry translated so the min
corner sits at the origin (offset +46.10, +11.20, +18.12).

STEP bbox: X -46.10 .. +23.40, Y -11.20 .. +11.20, Z -18.12 .. +11.82.

## 1. Overall

| item | value | source |
|---|---|---|
| Overall bbox | 69.50 x 22.40 x 29.94 | STEP + STL, identical |
| Body length w/o front tab (can stub tip to gearbox front face) | 64.50 | STEP planes x=-46.10 .. +18.40 |
| Z extent breakdown | shaft tip -18.12, gearbox +/-9.32, top strap tab to +11.82 | STEP |

## 2. Gearbox (yellow plastic housing)

| item | value | source |
|---|---|---|
| Width | 22.40 (y +/-11.20) | STEP side planes, (STL) xsec 22.40 |
| Height | 18.64 (z +/-9.32) | STEP top/bottom planes, (STL) xsec 18.64 |
| Rectangular block length (rear plate to front face) | 36.80 (x -18.40 .. +18.40) | STEP |
| Straight side walls end at | x = +13.40, then front corners round R5.00 | STEP R=5.00 cylinders at (13.40, +/-6.20) |
| Front face (flat) width | 12.40 (y +/-6.20) at x=+18.40 | STEP plane |
| Round rear collar (wraps the can) | D22.40 round section, x -29.70 .. -18.40 (11.30 long); top flush at z=+9.32, bottom flat at z=-8.07 | STEP R=11.20 cyl + planes |
| Strap/latch tabs at collar | top tab to z=+11.82 (2.50 proud), bottom tab to z=-10.57; x approx -26.4 .. -22.2, y +/-2.5..3.0 | STEP planes |
| Gearbox assembly screw recesses (NOT mount holes) | 2x stepped pockets Ø4.00/Ø3.60 on the bottom at (x=-15.90, y=+/-6.00), 2.0 deep | STEP R=2.00/1.80 cyls |

## 3. Rear motor can (FA-130 style)

| item | value | source |
|---|---|---|
| Full diameter | 20.00 | STEP R=10.000, (STL) xsec 19.999 |
| Across flats | 14.99, and ASYMMETRIC: top flat at z=+8.12 (1.88 cut), bottom at z=-6.87 (3.13 cut); flat midline z=+0.625 | STEP planes, (STL) xsec 14.99 |
| Can axis | on the gearbox centerline (y=0, z=0) | STEP cylinder axis |
| Exposed can length (collar to end cap face) | 13.50 (x -43.20 .. -29.70); rear 2.0 of it steps to D19.90 | STEP |
| Rear end boss | Ø9.90 x 2.20 (x -45.40 .. -43.20) | STEP R=4.95 |
| Rear shaft stub | Ø2.00, protrudes 0.70 (x -46.10 .. -45.40) | STEP R=1.00 |
| Terminals | on can top rear: R2.0 lug feature at x approx -41, z 8.1..9.7, plus 4x Ø0.80 wire holes at x=-39.70, y +/-6.0..7.6 | STEP |

## 4. Output shaft (double-D)

| item | value | source |
|---|---|---|
| Ends | SINGLE-ended in this CAD (exits -Z only; top face solid) | STEP face sweep |
| Diameter | 5.40 | STEP R=2.700, (STL) xsec 5.40 |
| Double-D across flats | 3.70 (flats at y=+/-1.85) | STEP planes, (STL) xsec 3.70 |
| Base boss | Ø7.20 x 0.50 at the gearbox face (z -9.32 .. -9.82) | STEP R=3.60 |
| Shaft protrusion | 8.80 total from gearbox face (8.30 beyond the boss), tip at z=-18.12 | STEP |
| Flat (D-section) length | 8.00 (z -18.12 .. -10.12); first 0.30 past the boss is round | STEP planes |
| Tip hole | Ø2.00 x 5.00 deep, axial (z -18.12 .. -13.12) | STEP R=1.00 |
| Axis position | x=+6.90, y=0: **11.50 behind the gearbox front face**, 25.30 ahead of the rear plate, on the width centerline, mid-height | STEP axis pt, (STL) xsec center 53.0-46.1=6.90 |

## 5. Mount through-holes

| item | value | source |
|---|---|---|
| Rear pair | 2x Ø3.00, vertical (axis Z), THROUGH the full 18.64 height, at x=-13.40, y=+/-8.75 -> **17.50 c-c**, 20.30 behind the shaft axis, 5.00 ahead of the rear plate | STEP R=1.50 cyls, extent z -9.32..+9.32 |
| Front tab hole | 1x Ø2.80, vertical, through the 3.0-thick tab, at x=+20.90, y=0 -> **14.00 ahead of the shaft axis**, 2.50 ahead of the front face | STEP R=1.40 |

## 6. Front tab + bottom locating nub

| item | value | source |
|---|---|---|
| Front tab | 5.00 long x 5.00 wide x 3.00 thick (x 18.40..23.40, y +/-2.50, z +/-1.50), centered on mid-height, carries the Ø2.80 hole | STEP planes |
| Bottom locating nub | Ø4.00, protrudes 2.00 below the bottom face (z -9.32 .. -11.32), at x=-4.10, y=0 -> 11.00 behind the shaft axis, on the centerline, SAME side as the shaft | STEP R=2.00 |

## Claimed (src/build.py `motor_tt()`) vs measured

| item | claimed | measured | verdict |
|---|---|---|---|
| `tt_gearbox` (70.0, 22.0, 18.5) as box gx*0.35 = 24.5 x 22.0 x 18.5 | 24.5 x 22.0 x 18.5 | rect block 36.80 x 22.40 x 18.64 (+11.30 round collar) | gearbox 12 mm too short; W/H close |
| `tt_motor_d` = 24.0, can length gx*0.5 = 35 | Ø24 x 35 | Ø20.00 (AF 14.99), exposed 13.50 + Ø9.9 boss + stub | can 4 mm too fat, 21 mm too long |
| `tt_shaft_d` = 5.4, shaft ALONG the body axis (+X), 20 long, one end | Ø5.4 axial | Ø5.40 correct, but axis is **PERPENDICULAR to the body length**, 8.80 proud, flats 3.70 | orientation wrong: placeholder puts the shaft where the front tab is |
| shaft position | at the body end | 11.50 behind the front face, mid-height, centerline | wrong |
| mount holes | none modeled | 2x Ø3.00 @ 17.50 c-c + Ø2.80 front tab | missing |
| overall length | approx 24.5+35+20 = 79.5 spread | 69.50 incl tab and stub | ~10 mm over |

## Corrections for Stage 3b

1. **Sprocket D-bore (audit guessed ~Ø5.4 double-D): diameter confirmed 5.40, but the
   full spec is Ø5.40 with 3.70 across flats, usable flat length 8.00.** Print the
   bore Ø5.6-5.7 with a 3.8-3.9 flat gap (typical FDM shrink), hub depth <= 8.0 so it
   stays on the flats; the first 0.3 mm past the Ø7.20 x 0.50 base boss is round.
   Shaft tip has a Ø2.00 x 5.00 axial hole: retain the sprocket with a small
   self-tapping screw + washer into the tip.
2. **Motor orientation in the pod is 90 deg off the current placeholder.** The shaft
   is perpendicular to the 64.5 mm body. With the shaft on X (into the sprocket), the
   motor body lies along Y (across the pod) or along the track direction with the
   gearbox flat against the pod wall; budget the envelope 64.50 L x 22.40 W x 18.64 H
   plus the 5.00 front tab and 2.50 of terminal/wire clearance above the can rear.
3. **Chassis/pod wall pass-through: Ø8.00 minimum** (clears the Ø7.20 shaft base boss
   with 0.4 slop). Wall thickness at the pass-through <= 8.3 mm leaves at least some
   flat engagement for the sprocket beyond it; better: keep the wall <= 3 mm here and
   seat the sprocket close to the box.
4. **Mounting pattern to model:** 2x M3 through-bolts at 17.50 c-c (holes are 20.30
   behind the shaft axis, bolt length >= 18.64 + walls), 1x Ø2.80 front tab hole
   (M2.5/M2.6 self-tap) 14.00 ahead of the shaft axis, and a Ø4.20 x 2.20 pocket for
   the bottom locating nub 11.00 behind the shaft axis on the centerline (nub is on
   the shaft side, so it registers against whichever wall the shaft passes through if
   the motor lies shaft-down; if the shaft is horizontal, the nub points sideways).
5. **Shaft axis height defines the sprocket center:** the axis sits mid-height and
   mid-width of the gearbox, so sprocket center = motor seat plane + 9.32 (half of
   18.64) when the gearbox lies on a flat bed.
6. **This CAD is single-shaft.** Most purchased TT motors are dual-shaft; if the real
   part has a second shaft on the far side, give the far pod wall a Ø7.5+ clearance
   pocket at the mirrored position (or use it for an encoder disc). Verify the actual
   unit on hand before closing that wall.
7. `motor_tt()` placeholder numbers to update: gearbox block 36.80 x 22.40 x 18.64
   (+ round D22.4 collar 11.30), can Ø20.00 x 13.50 exposed with 14.99 across flats,
   shaft Ø5.40 x 8.80 perpendicular at 11.50 from the front face.

License: CC-BY (see LICENSE.txt). Source: thingiverse.com/thing:1079893.

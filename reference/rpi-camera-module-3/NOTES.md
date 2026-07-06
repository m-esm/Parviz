# Raspberry Pi Camera Module 3 (standard) mechanical data

Official sources, downloaded 2026-07-06:

- `camera-module-3-standard-mechanical-drawing.pdf` (1 page, all dims mm, note on the
  drawing: "tolerances are accurate to 0.2mm"). Redirects from
  datasheets.raspberrypi.com to pip.raspberrypi.com RP-008153-DS.
- `camera-module-3-product-brief.pdf` (RP-008151-DS). Spec table on page 5 is the FoV
  and optics source.
- `camera-module-3-step.zip` (RP-008154-DS) unzipped to `step/`:
  `Camera_module_3_std_model_simple.stp` and `Camera_module_3_wide_model_simple.stp`.
  trimesh cannot read STEP; numbers below were cross-checked by parsing the STEP text
  entities (CARTESIAN_POINT / CIRCLE) directly, not by meshing it.

STEP model frame used for cross-checks: X = board height axis (0..23.862, 0 at the
edge away from the lens), Y = board width axis (0..25), Z = depth (board back face at
0, board front face at about -0.75, lens pointing to -Z).

## Board and mount holes

| Item | Value | Source |
|---|---|---|
| Board outline | 25.000 W x 23.862 H | drawing p1 (25, 23.862); STEP bbox 23.862 x 25 |
| Board thickness | 1.12 (drawing); bare PCB in STEP is about 0.75, the 1.12 includes back lamination | drawing p1 side view |
| Mount holes | 4x Ø2.2, pads Ø4.75 | drawing p1 |
| Hole pattern | 21.0 (W) x 12.5 (H) | drawing p1 (2.0 edge offsets on 25 width; rows at 2.0 and 14.5); STEP hole centers exactly at (2, 2), (14.5, 2), (2, 23), (14.5, 23) |
| Hole rows from board center | +2.569 (top row) and -9.931 (bottom row); columns at +/-10.5 | computed from 14.5 / 2.0 on the 23.862 height |

## Lens and housing (the part the forehead wall must clear)

| Item | Value | Source |
|---|---|---|
| Lens optical axis, width | exactly on the width centerline (12.5 from each side edge) | STEP: all lens circles at Y=12.5; drawing 12.5 |
| Lens optical axis, height | 14.4 above the bottom edge = +2.469 above board center = 0.1 BELOW the top hole row | drawing p1 (14.4 vs 14.5 hole row); STEP: all lens circles at X=14.4 |
| Lens barrel outer Ø | 5.75 | drawing p1 (Ø5.75); STEP circle r=2.875 at the tip |
| AF housing footprint | 10.8 x 10.8, centered on the lens axis | drawing p1 (10.8 both directions); STEP walls span 8.95..19.85 (H) x 7.05..17.95 (W), 10.9 x 10.9 centered on (14.4, 12.5) |
| Housing front face above board front | 3.875 per drawing; STEP simple model shows the rounded cap reaching about 4.15 | drawing p1 side view; STEP planes at -4.87..-4.92 with board front at -0.75 |
| Lens tip above board front | 6.98 | drawing p1; STEP tip at Z=-7.65 minus board front -0.75 = 6.90 |
| Barrel protrusion past housing front | about 2.8 (6.98 - 4.15); drawing labels 2.75 on the front step | drawing p1 side view |
| Lower housing tab | 8.9 wide flex/step region extending down toward the bottom holes, step heights 3.3 / 4 / 7.3 from the bottom edge | drawing p1 front view |
| Overall depth incl. back connector | 11.3 | drawing p1 side view |
| Back-side clearance needed | 11.3 - 6.98 - 1.12 = 3.2 behind the board; STEP back components reach 2.6 behind the board back face, spanning almost the full board (connector block 19.61 wide x 5.71 tall near the lens-end edge per drawing) | drawing p1; STEP z>1.8 sweep |

## Optics / FoV (standard module, IMX708)

Product brief page 5 spec table, confirmed by the 66 and 41 degree cones drawn on the
mechanical drawing itself:

- Focal length 4.74 mm, F-number F1.8 (entrance pupil about 4.74/1.8 = 2.63 mm Ø)
- FoV: 66 deg horizontal, 41 deg vertical, 75 deg diagonal
- Wide variant for reference: 2.75 mm focal, F2.2, 102/67/120 deg. Wide also has a
  taller lens stack (its drawing dims 4.07/8.3 replace 3.875/6.98), so these notes do
  NOT transfer to the Wide module. NoIR standard shares the standard optics.

## Diff vs the v2.1 numbers currently in the project

Project currently models (per CLAUDE.md / build.py): board 25 x 23.86, holes 21 x 12.5
with rows at +2.575/-9.925 from center, lens axis at x=0 z=+2.575, barrel Ø7.24.

- Board outline: SAME (25 x 23.862 vs 23.86, a 0.002 rounding difference).
- Hole pattern: SAME (21 x 12.5, Ø2.2). Rows at +2.569/-9.931 from center with the
  exact 23.862 height; the project's +2.575/-9.925 is the same pattern rounded.
- Lens optical axis: NOT quite the same as v2.1. Width is identical (x=0). Height:
  v2.1 puts the lens ON the top hole row (z=+2.575); CM3 puts it 0.1 mm BELOW the row
  (14.4 vs 14.5 from the bottom edge), i.e. z=+2.469. The value already in CLAUDE.md
  ("Z=+2.47 above board center") is the correct CM3 number. The 0.106 mm shift is
  inside FDM tolerance and inside the drawing's own 0.2 mm tolerance note.
- Barrel Ø: CHANGED, v2.1 Ø7.24 -> CM3 Ø5.75.
- Front stack: MUCH taller than v2.1. CM3 housing is 10.8 x 10.8 with its front face
  about 4.0 above the board and the lens tip at 6.98; v2.1 was a smaller sensor block
  with a tip around 4 mm. The recess pocket depth and the lens-bump standoff must use
  the CM3 numbers, not v2.1.
- Overall depth: 11.3 (CM3) vs about 9 (v2.1). Keep 3.2 mm free behind the board.

## Aperture for a 4 mm forehead wall, pupil recessed about 3 mm

Geometry: entrance pupil Ø about 2.63 mm (4.74 mm focal / F1.8), sitting about 3 mm
behind the wall's outer face (so about 1 mm forward of the inner face; the Ø5.75
barrel tip pokes into the bore). Diagonal FoV governs: half angle 37.5 deg,
tan = 0.767.

Required clear diameter at distance d in front of the pupil:
Ø(d) = 2.63 + 2 x d x tan(37.5 deg) = 2.63 + 1.535 x d

- At the outer face (d = 3.0): Ø = 7.24 mm minimum for zero vignetting.
- The cone outgrows a Ø6.3 barrel-clearance bore at d = 2.39 mm.

Recommendation:

- Through-bore Ø6.3 (clears the Ø5.75 barrel with 0.27 mm per side) for the inner
  roughly 2 mm of the wall.
- Countersink the outer roughly 2 mm to Ø8.0 at the outer face (Ø7.3 is the geometric
  minimum; 8.0 adds print and alignment margin). A 45 deg per-side (90 deg included)
  countersink from Ø6.3 to Ø8.0 works because 45 deg exceeds the 37.5 deg half angle;
  any included cone angle of 76 deg or more also clears.
- Sanity check with horizontal FoV only (66 deg): Ø = 2.63 + 2 x 3 x tan(33 deg)
  = 6.53 mm; the diagonal requirement is stricter, so use it.

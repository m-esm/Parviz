# Printability audit — styling / cosmetic parts (design-styling campaign)

Audit of the cosmetic parts added in the design-styling pass, measured from
`web/assembly.glb` (trimesh: extents, body splits, cross-sections) and cross-checked against
the builders in `src/build.py`. Rules basis: FDM on a 0.4 mm nozzle (Bambu A1 class),
Arachne floors: **>= 0.6 mm for detail that must survive slicing, >= 0.8 mm structural walls,
~0.4 mm absolute single-wall floor**. Read-only audit; no geometry changed.

Preview pose note: GLB extents below the head are world-posed (pan 22 / tilt -12); the
per-part dimensions quoted are the as-modeled local sizes from `build.py`.

## Verdict table

| Part | Material / color | Min feature found | Print orientation | Supports | Verdict |
|---|---|---|---|---|---|
| trim_rail_L/R | orange PLA | 5.0 thick pad, r8 corners | flat back face down | no | **OK** |
| trim_hatch_frame | orange PLA | 3.0 thick, band 13.0 (corner min 13.0 measured) | flat on back face | no | **OK** (brim; large 160x105 thin ring, warp watch) |
| trim_fascia (ring + 6 fins) | orange PLA | fins 3 x 2 x 16; ring band 4.0 x 2.5 | flat, proud-face up | no | **FAIL — 7 disconnected bodies** (fins never touch the ring; ring x +-30, fins at x 33.5..48.5) |
| trim_rear | orange PLA | band 4.0 wide x 2.5 thick (corner min 4.0 measured) | flat on back face | no | **OK** |
| camera_pod | black PLA | **~0.05 mm wall** at bore-flare cusp | face down (flare then self-supports at 45) | no | **FAIL — knife-edge cusps**: flared bore opens to Ø19 at the face vs pod height 18 (measured: bore edge z +-8.95 vs face +-9.0 at 0.3 mm depth; wall 0.75 at 1.0 mm depth) |
| antenna_stub | black PLA | knurl grooves 1.4 wide x 0.7 deep (resolve fine, > 0.6); Ø13 shaft | axis vertical, collar down | no (brim on Ø16 collar) | **OK** (cosmetic nit: dome is a subdivisions=2 icosphere, visibly faceted at Ø13) |
| led_strip (8 dots + base) | white PLA | base plate **0.8 thick**; dots Ø2.4 x ~1.5 proud | base down, dots up | no | **Marginal** — one connected body (dots are unioned to the base, not loose), Ø2.4 bumps print as 2-perimeter towers; the 0.8 base is 4 layers and fragile to handle |
| led_front (7 dots + base) | white PLA | base **1.0 thick**; dots Ø2.6 x ~1.5 proud | base down, dots up | no | **Marginal** — same pattern as led_strip, slightly better base |
| lamp_L/R | amber PLA (or painted) | 12 x 7 x 2.0 chip, r2.5 | flat face down | no | **OK** (tiny; print with the white plate and swap color, or tint) |
| sensor_us | bought (HC-SR04) | n/a | n/a | n/a | **Bought part** — placeholder only, skip print |
| sensor_rear | bought (recommended) | Ø14 x 9 cylinder | (face down if printed) | no | **Buy, don't print**: it plays a speaker/buzzer; a Ø12-14 piezo buzzer or speaker grommet is the real part. A printed silver-painted plug is trivial if wanted |
| arm_L/R | charcoal PLA | limbs 9 wide; claw ring wall 8; finger pads 13 x 6.5 x 7; standoff tube Ø16 x 23.5 | side-lying (arm plane on bed) | **yes (tree)** | **Marginal** — single connected body, but limb/disc/claw widths (9/10/13) share a center plane so no face is flat; side-lying floats the limbs ~2 mm and stands the tube 23.5 up. Placeholder per build.py; split at joints at the mechanism pass |
| chassis hex grille (on chassis) | charcoal PLA | **web 0.74 mm** between hex vertex tips | prints with chassis (wall vertical) | no | **Marginal** — hexes are vertex-facing in X, so the web narrows to 0.736 at the tips (not the assumed 1.2); blind pockets also have a 3.0 flat ceiling bridge (fine) |
| drivewheels: sprocket x2 | grey PETG | teeth ~5 x 3 x 8 (fine) but **zero-overlap root joint** | gear face down, hub up (one-sided hub self-supports) | no | **FAIL — all 12 teeth are detached bodies**: tooth boxes sit at radius 15.8..18.8 with the root cylinder at r 15.8 exactly, line contact only (16-body split confirms; `gear_disc` defect, worm_wheel has it too) |
| drivewheels: idler x2 | grey PETG | wall 7.7 (Ø31.4 over Ø15.95 bore); flange recess 18.5 x 1.05 | axis vertical, flange recess up | no | **OK** (F688ZZ seat prints round when vertical) |
| drivewheels: road wheels x4 | grey PETG | Ø22 x 30 **solid, no bore** | axis vertical | no | **FAIL (incomplete)** — 11.4 cm3 solid cylinder with no axle bore or bearing seat; unbuildable as running gear until the axle scheme is modeled |

## Fix list (marginal / fail, with the specific change)

1. **camera_pod cusps (FAIL).** The 45-deg flare from the Ø8 csk over `cam_pod_t + 0.5 = 5.5` mm
   opens to Ø19 at the face; `cam_pod_h = 18` clips it top and bottom, leaving ~0.05 mm knife
   edges at the front lip. Fix either: `cam_pod_h` 18 -> **22.0** (1.5 mm wall each side, keeps the
   45-deg flare), or drop the flare to 40 deg/side (opening Ø17.2, still > the 37.5-deg FoV half
   angle) *and* `cam_pod_h` -> 20. Side walls at the face are 2.5 (fine) either way.
2. **trim_fascia fins detached (FAIL).** The 6 fins (x +-33.5..48.5) never touch the ring
   (x +-30). Add a backing web per side tying fin bases to the ring: a `box(21.5, 1.2, 16)` at
   y = fw..fw+1.2 spanning x 28..49.5 (mirrored), unioned before the `uni(fins)`. The web hides
   behind the 2-mm-proud fins and overlaps the ring band. Alternative: emboss the fins into the
   chassis wall and drop them from the orange part.
3. **sprocket teeth detached (FAIL).** In `gear_disc`, the tooth prism spans exactly
   `root_r..root_r + tooth_h` — line contact with the root cylinder, so slicers/split see 12 loose
   teeth. Fix in `gear_disc`: make the tooth box `tooth_h + 1.0` tall and translate to
   `pitch_r - 0.5` so each tooth sinks 1 mm into the root. Fixes the sprocket now and the
   worm_wheel placeholder for free (same 13-body split).
4. **road wheels solid (FAIL, incomplete model).** Add the axle scheme before printing: at
   minimum a Ø8.3 through-bore for a stub axle, or F688ZZ seats (Ø15.95 x 5 + flange recess)
   matching the idler if they should free-wheel. Blocked on the mechanism decision, not on print.
5. **hex grille web 0.74 mm (marginal).** Rotate each `hex_prism` 30 deg about its own axis
   (flats facing +-X) before placing: web becomes a uniform `4.2 - 3.0 = 1.2` mm and the pocket
   roof becomes a 60-deg self-supporting vertex instead of a 3 mm flat bridge. One-line change at
   the `hex_prism(3.0, 4.0)` call.
6. **led_strip base 0.8 (marginal).** Thicken the base 0.8 -> **1.2** (recess is 1.5 deep; dots
   still clear to 0.3 proud). Print both LED bars at 0.12 mm layers. Longer term the honest part
   is a real WS2812 stick behind a white/clear printed window; the current bars are dummies.
7. **arm_L/R (marginal, placeholder).** Printable today side-lying with tree support (support
   scars land on the inboard face, hidden). At the arm mechanism pass, split at the joint discs
   so each link prints flat per the gear/pin FDM rule; don't invest before then.
8. **(Out of scope, print-blocking, found in passing.)** `chassis` splits into 3 bodies: the two
   2 x 28 x 28 idler tension plates at x +-86.3 / y 60 float disconnected from the body. They are
   outside the +-60 chassis walls, in the pod envelope; they need a bridge to the chassis arm or
   to be their own parts before `chassis.stl` is printable.

## Plate grouping

| Plate | Filament | Parts | Notes |
|---|---|---|---|
| A — orange | orange PLA | trim_rail_L, trim_rail_R, trim_hatch_frame, trim_fascia (post-fix 2), trim_rear | all flat-back, no support; hatch frame centered on the bed with an 8 mm brim |
| B — black/charcoal | black PLA | camera_pod (post-fix 1), antenna_stub, arm_L, arm_R (or hold arms for the mechanism pass) | antenna brim; arms tree support only |
| C — white + amber | white PLA (+ amber for lamps) | led_strip, led_front, lamp_L, lamp_R | 0.12 mm layers for the dot bars; lamps are a 2-part color swap or print natural and tint |
| D — running gear | grey PETG | sprocket x2 (post-fix 3), idler x2, road wheels x4 (post-fix 4) | PETG for creep under track tension; sprockets gear-face down, wheels axis-vertical |

Bought, not printed: sensor_us (HC-SR04), sensor_rear (Ø12-14 piezo buzzer/speaker),
WS2812 stick if fix 6's window route is taken.

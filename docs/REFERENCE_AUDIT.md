# Reference-model audit (independent re-measurement)

Every dimensional claim in `src/build.py` PARAMS and `CLAUDE.md` that cites a reference model,
re-measured directly from the reference meshes with trimesh (cross-sections, hole circle-fits,
angular tooth counts). Probe scripts live in the session scratchpad (`probe_screen.py`,
`probe_cam.py`, `probe_track.py`, `probe_track2.py`, `probe_misc.py`). Measurement frame for the
screen matches `load_screen()`: recentered at bbox centroid, then 180 deg yaw (post-flip local frame).

Verdicts: OK (matches within measurement noise), WRONG (transcription error),
DESIGN (deliberate deviation from the reference, no error but flagged),
UNVERIFIABLE (this reference cannot confirm it).

## 1. 7" touchscreen (`Raspberry_Pi_Touch_Screen_Assembly_v12.stl`)

| Claim | Claimed | Measured | Verdict | Impact if wrong |
|---|---|---|---|---|
| Assembly bbox W x D x H | 193.0 x 25.0 x 110.8 | 192.96 x 24.99 x 110.76 | OK (rounded up <= 0.05) | head pocket sizing |
| STL axes | X=W, Y=D, Z=H | confirmed (extents map exactly) | OK | screen orientation |
| Glass faces -Y pre-flip, +Y post-flip | flip = 180 yaw | full flat 21324 mm^2 face at local y = +12.19 post-flip | OK | screen would face into the head |
| Outer mount pattern | 126.2 x 65.65 | 126.19 x 65.65 | OK | screen retention bosses |
| `scr_mount_pts` x values | +61.61 / -64.59 | +61.61 / -64.59 | OK | boss placement |
| `scr_mount_pts` z values | +33.80 / -31.85 | +33.80 / -31.85 (per-hole spread < 0.03) | OK | boss placement |
| Mount face plane local Y | +6.53 | +6.53 (hole runs y 4.03 to 6.53, depth 2.50) | OK | boss standoff length |
| Hole size, M3 claim | M3, clear r 1.75 | hole dia 3.00, 2.50 deep through a tab | OK (M3 threads/self-taps the pan hole) | screw choice |
| Pattern centering vs bezel outline | encoded asymmetric | pattern center at (-1.49, +0.98) from bbox center; `scr_mount_pts` encode exactly this offset | OK | bosses would miss holes by 1.5 mm if symmetric points were used. They are not. |
| Bonus: inner standoff pattern | (pi_hole 58 x 49) | 57.99 x 49.01, dia 2.51 holes, center (-6.44, +3.45) from bbox center | OK | Pi mounting (in-head, uses back-cover standoffs anyway) |

Screen transcription is clean. No corrections needed.

## 2. Camera (`rpi-camera-v21-1564160`, jbeale v2.1 model, SCAD source included)

The reference IS a Camera v2.1 model (PCB + sensor + flex), with exact numbers in `RPiCam-v2.scad`.
The robot uses Camera Module 3. Board width and 4-hole pattern are shared; lens geometry is NOT.

| Claim | Claimed | Measured (v2.1 ref) | Verdict | Impact if wrong |
|---|---|---|---|---|
| Board W | 25.0 | 25.00 (scad xs=25.0) | OK | pod pocket |
| Board H `cam_board_h` | 23.862 | 23.85 (scad ys=23.85; 23.862 is the official v2.1 drawing figure) | OK (0.01) | pod pocket. CM3 nominal is 25 x 24: verify before print |
| Mount hole pattern | 21.0 x 12.5 | 21.01 x 12.51, hole dia 2.20 | OK | M2 bosses |
| Hole rows vs board center | +2.565 / -9.935 | +2.575 / -9.925 exact (scad); mesh circle-fit gives 2.56 / -9.93 | OK (0.01) | M2 boss Z |
| Lens optical axis X | 0 (board center) | +0.00 | OK | aperture X |
| `cam_lens_dz` | +2.47 | +2.575 on v2.1; but official CM3 = +2.469 (see corrections #2) | OK for CM3 (superseded) | none: the robot uses CM3, 2.47 is right |
| Lens barrel | "dia 5.75 v3 barrel" | v2.1 holder barrel dia 7.24 (cell dia 5.60) | UNVERIFIABLE for v3; note the v2.1 barrel alone is BIGGER than the quoted 5.75 | aperture bore / recess clearance |
| CM3-specific: board 24 H, lens housing size/protrusion, 66 deg FOV cone | various | not in this reference (v2.1 only). CM3 lens housing is a larger molded block than the v2.1 barrel | UNVERIFIABLE-FROM-THIS-REF | forehead recess depth, aperture dia, cover fit |

## 3. Tank track (`tank-track-3062624`, advancedvb)

| Claim | Claimed | Measured | Verdict | Impact if wrong |
|---|---|---|---|---|
| Link pitch ("reference ~9.8") | comment says ref ~9.8; `track_pitch`=10.0 | 9.65 (track_1.75: 9.65; track_2.85: 9.65 to 9.67) | WRONG comment (ref is 9.65, not 9.8). pitch 10 itself = DESIGN | if links are printed FROM the reference STLs, a pitch-10 sprocket/loop will not mesh them |
| Pin bore (FIXES.md: "dia 1.9 pin bores") | 1.9 | 2.01 nominal (drafted; circle-fits 1.82 to 2.01) for dia 1.75 filament | WRONG (use 2.0) | pins will not insert into a 1.9 bore printed with normal shrinkage |
| Link width `track_width` | 28.0 | 36.00 | DESIGN (deliberate narrowing; flag: reference geometry is 36) | sprocket/link engagement width, pod width |
| Link thickness | `track_pad_th`=5.0 (+1.5 grouser) | link overall 8.00 thick; pad web 2.70; hinge-pin center 4.50 above outer face | DESIGN (model is a simplified pad) | ground clearance, loop circumference |
| Sprocket teeth `sprocket_teeth` | 12 | 12 (12 tooth pockets, 12 rim lobes) | OK | meshing |
| Sprocket OD `sprocket_outer_d` | 42.0 | ref OD 36.28 (tip r 18.14, valley r 15.43, width 8.30) | WRONG as scaled: for 12T x pitch 10 the pin circle r = 19.32 and ref keeps tips 0.51 BELOW the pin circle, so tip r ~18.8, OD ~37.6. OD 42 puts tips 1.68 PAST the pin circle | tooth tips collide with link pads; track will not wrap |
| Pitch radius `track_wheel_r` | 19.0 | exact pin-circle radius for 12T x 10.0 pitch = 19.32; ref (12T x 9.65) = 18.65 | WRONG (small): 19.0 gives loop perimeter 359.4 vs 36 x 10 = 360 | 0.6 mm loop slack; fold into the idler tension slot or set 19.32 |
| Idler bore `idler_bore_d` | 16.0 (dia 16 flanged bearing) | driven wheel: bore 15.95 press seat + 18.46 flange recess; `bearing_size.stl` = flanged bearing OD 16.00, flange dia 17.92, width 5.00, bore dia 7.96 => F688ZZ (8 x 16 x 5, flange 18) | OK, now fully specified | buy list: the part is an F688ZZ; the idler also needs a dia 8 stub axle and a ~dia 18.5 x 1 flange recess |
| Road wheels `roadwheel_d`=22, count 2 | 22.0 | no road wheels exist in the reference (driving + driven wheels only) | UNVERIFIABLE-FROM-THIS-REF (design addition) | none; free choice |
| Drive bore (ref driving wheel) | (TT double-D 5.4 assumed) | ref bore is double-D: round dia 5.88, across-flats 5.31 (their gearmotor, not a TT) | DESIGN note | TT adapter bore must be modeled for the TT's 5.4 shaft, not copied from the ref |

Other reference facts for the fix agent: driving wheel width 8.30 (this is the "~8 mm central
engagement" in the PARAMS comment; matches), driven wheel width 6.00, both wheels OD ~36.0
lightened by a 12-hole ring.

## 4. Case + Alexa style references

- `rpi-7in-touchscreen-case`: not needed; the screen mount was verified directly from the screen
  mesh above.
- `alexa-style-smart-display`: style only. Body 191.32 x 110.00 x 122.24, front plate
  191.32 x 12.00 x 122.24. No PARAMS numbers claim to come from it. OK / no claims.

## 5. Claims with no local reference

- 28BYJ-48 dims (`motor_*`): sourced from the beckdac SCAD + Mouser datasheet per the comment; no
  local mesh to audit. Values are consistent with the well-known datasheet (dia 28, offset 7.875,
  ears 35). UNVERIFIABLE from local refs, no action.

## Prioritized corrections for the Stage 3 fix agent

1. `sprocket_outer_d`: 42.0 -> 37.6 (tip radius 18.8, i.e. pin-circle 19.32 minus 0.5 tip
   clearance, matching the reference proportion). With OD 42 the tooth tips stand 1.68 proud of
   the pin circle and jam the links. Optionally set `track_wheel_r` = 19.32 (exact 12T x 10.0
   polygon radius) and let the 0.6 mm residual go to the idler tension slot.
2. `cam_lens_dz`: KEEP 2.47. SUPERSEDED by the official CM3 drawing (RP-008153-DS, now in
   `reference/rpi-camera-module-3/` with NOTES.md): the CM3 lens axis is +2.469 above board
   center, 0.106 BELOW the top hole row. The 2.575 value above is correct only for v2.1; the
   robot uses CM3, so the original 2.47 stands. Real CM3 corrections instead: barrel dia 5.75
   (not 7.24), AF housing 10.8 x 10.8 centered on the lens, housing front ~4.0 above board
   front, lens tip 6.98, overall depth 11.3 (keep 3.2 clear behind the board). Aperture for
   the 4 mm forehead wall: dia 6.3 through-bore + dia 8.0 countersink at 45 deg per side
   clears the full 75 deg diagonal FoV (pupil dia 2.63 recessed ~3 mm needs only 7.24 clear
   at the outer face). This replaces the FIXES.md "dia 10 -> dia 18 countersink" guess.
3. Track pin bores (FIXES.md item): model dia 2.0, not dia 1.9 (reference uses ~2.0 drafted bores
   for dia 1.75 filament pins; 1.9 printed will not accept the pin).
4. Fix the `track_pitch` comment: the reference pitch is 9.65, not ~9.8. Keep pitch 10.0 only with
   re-modeled links (the plan); do NOT print links from the reference STLs and expect them to mesh
   a pitch-10 sprocket.
5. Idler spec for the BOM: the "dia 16 flanged bearing" is an F688ZZ (8 x 16 x 5, flange dia 18).
   The idler wheel needs a 15.95 press seat, an 18.5 x 1.0 flange recess, and a dia 8 stub axle.
6. No screen changes: bbox, mount pattern, hole plane, and the asymmetric `scr_mount_pts` all
   verified correct to 0.02 mm.

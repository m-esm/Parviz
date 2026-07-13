# Mechanism fix ledger, mechanisms-finalize

Three review agents (geometry verifier / mechanical loads / assembly walk) audited commit
`fa13f64` and converged on ~20 verified defects. Four fix stages run sequentially (they all edit
`src/build.py`); stage 4 is an independent re-verification. Status legend:
`[x]` fixed+probed, `[~]` in progress, `[ ]` queued, `(!)` accepted-as-is with reason.

## Stage 1, chassis + pan stack  [DONE, all probes pass]

- [x] **No chassis deck** (worst defect: race/balls/platform floated; whole head load hung on the
  pan motor's 5 mm plastic shaft). Cavity now stops `deck_t=20` below the top (5 mm of material
  under the race seat); seat floor z=37 carries the ring.
- [x] **Race grooves too deep + oversize** (platform sank 3.0 mm onto the ring; ring groove floor
  was 0.1 mm). Grooves engage 1.8 mm of ball each, oversize 0.2; stack derived in one helper
  (`_pan_stack`); plate 7.6 thick, top flush at z=52; tangency probe error 0.0000.
- [x] **No uplift retention**, 3 L-clips at 120° screwed to deck pockets, engaging a platform rim
  REBATE below deck level (top-side clips would be sheared by the neck sweep, measured r≤62.9).
- [x] **Pan D-bore jammed on the round shaft section**, D-profile now only over the flat zone
  (z 44.5..52), Ø5.3 round counterbore below; hub stops 0.3 above the motor's Ø9.1 boss.
- [x] **Platform overconstrained** (located by shaft AND race): D-bore arcs opened +0.27/side,
  flats snug: race locates, shaft only drives. Hub grub deleted.
- [x] **Pan motor pad/ear mismatch** (can sank 5.5 into the pad, ears floated 12.4 above pilots),
  pedestal top at the ear plane, Ø29 can relief, Ø2.5 pilots, wiring-box relief.
- [x] **Neck bolts broke the platform rim + all pilots were Ø3.5 clearance (nothing bites)**,
  bolt circle r16→12, neck pilots Ø2.5×12, underside counterbores for the heads.
- [x] **JST won't pass Ø12 bores**, platform + neck passes are 16×8 obrounds.
- (!) Cable exit relocated to (12,−24): the spec position (0,−38) punches the fixed race ring.
- (!) Marginal, unfixed: outer neck-bolt counterbores nick the groove outer flank ~0.9 mm (outside
  ball contact); neck bottom coplanar with deck top (zero-gap rub when panning).

## Stage 2, tilt drive + neck + Pi + axle  [DONE, all probes pass]

- [x] **695 bearing seats sealed inside the cheeks**, open flush to the inner faces (x=±18),
  bore Ø12.85. Probe: Ø12.7 test plug vs neck = 0.000 mm³ both sides (insertable).
- [x] **Worm wheel freewheels / rubs / unconstrained axially**, width 7 centered on x=0,
  grub-keyed hub (M3 pilot), Ø8 spacer tubes to both 695 inner races. Probe: wheel spans
  x −18.00..+18.00 (races at ±18), wheel-vs-neck = 0.000 mm³.
- [x] **Tilt speed 16 s per 60°**, worm_wheel_teeth 24→12; center distance factored into
  `worm_cd()` (one helper, both former call sites). Probe: teeth=12, cd=11.50.
- [x] **Worm undriveable**, full-depth double-D bore (vol 845 vs 942 unbored), worm_len 16,
  Ø6 tail stub riding a Ø6.4 bushing post off the bracket. Probe: worm-vs-neck = 0.000 mm³.
- [x] **Tilt motor buried + ear holes 7.9 mm off**, Ø29 can pocket + wiring-box and ear-bar
  reliefs; motor ROLLED about its shaft so the 7.875 offset points UP (can hangs below the worm
  axis, clear of the back-wall sweep; ears horizontal at the CAN axis); gear face on the plate
  back face. Probe: motor-vs-neck = 0.000 mm³.
- [x] **Pi 5 inside the mechanism volume**, Pi now PORTRAIT (85 edge vertical) and offset to
  x −84..−28: everything on the neck stays inside |x|≤26, so no tilt angle can reach it.
  Standoffs moved to the new 49(X)×58(Z) pattern, 3 mm long, all four rooted outside the slot;
  pivot bosses shortened 24→12 so the −X one clears the board. Probe: pi vs
  neck/motor/worm/bezel/back/axle/screen = 0.000 mm³ at −30/0/+30 (and every 5° between).
- [x] **Axle end-grip topology**, Ø7 clamp-boss torque tubes from x=±27 out to the side walls,
  Ø2.5 grub pilots at x=±30 (driven from below through the slot), snug Ø5.1 bore at the bosses,
  far-wall bores demoted to loose Ø5.3. Probe: boss material 489 mm³/side; a Ø5.24 plug bites
  the boss 4.97 mm³ (grips) and the wall 0.00 (loose slip fit).
- [x] **Tilt envelope −11°..+19° vs ±30° spec**, full ±30 achieved, no ±25 fallback. Neck slot
  narrowed to 62 wide (cheeks end at |x|=26; Pi bosses keep wall roots) but raised to z=191;
  the bottom-CENTER bezel↔back post swept into the neck column, replaced by a pair at x=±40.
  Probe: sweep −30..+30 at 5°, 14 fixed-vs-head pairs, all 0.00 mm³.
- [x] **Tilt ULN2003 had no mount**, 4× Ø6 standoffs + M3 pilots on the column back face
  (35×32 pattern centered z=110). Probe: 746 mm³ standoff material behind the back face.

Stage-2 side effects for Stage 3: the Pi is portrait at (x −56, y −16, z 192.5) → re-aim the
back-cover I/O slot for ports exiting the board's ±X/±Z edges there; bezel↔back fastening is now
7 posts (M3×35 ×7, nuts +1); pivot bosses are 12 long (they still protrude past the outer wall,
the Stage 3 trim item stands).

## Stage 3, head/screen/camera + tracks  [DONE: head/camera 3a, tracks/drive 3b]

Head/camera fixed by the Stage-3a agent (attempt 2). Combined screen+Pi model swap (user design
change) done FIRST; several fixes below were re-scoped by what the new mesh + official CM3 data
proved.

- [x] **Screen+Pi combined reference model**, `screen_ref_stl` → `..._-_Pins_Out_v8.stl` (display
  WITH the Pi on its own 58×49 back standoffs; bbox 192.96 × 38.01 × 110.76, 13.02 deeper on the
  back). `load_screen()` now anchors the GLASS FACE at local y=12.494 instead of the bbox centroid
  (which the deeper back dragged 6.51 forward). Probe: glass world y old 30.9940 / new 30.9940,
  delta 0.0000; all 4 scr_mount_pts vertex clouds delta 0.00; W/H bounds delta 0. The separate
  `pi5` placeholder part and the stage-2 Pi standoffs in head_back are REMOVED (obsolete).
- [x] **Screen retention → REAR standoffs** (re-scoped from "shorten bezel bosses"): the factory
  126.2×65.65 holes open BACKWARD; the old bezel bosses ran forward from the tab plane (25.03)
  through the GLASS (front 30.99; 69/50k screen samples inside them). Now 4× Ø9 standoffs on
  head_back (inner wall −27 → tab plane 25.03, at x=±63 they clear the Pi stack |x|≤48.1, tubes,
  louvres, both slots), each with a Ø6.5 driver channel through the back wall + 8 mm M3 seat
  (stock M3×12). Probe: material beyond the tab plane 0.000 ×4, 215.6 mm³ seat each.
- [x] **Camera aperture per OFFICIAL CM3** (ledger's Ø10→Ø18 guess superseded by RP-008153-DS):
  Ø6.3 through-bore, countersink to Ø8.0 at the outer face at 45°/side, `cam_lens_dz` kept 2.47.
  Probe: 75° diagonal FoV cone (Ø2.63 pupil 3 mm behind the face) vs bezel = 0.0000 mm³.
- [x] **CM3 does not fit the old forehead, bay redesigned** (proven, not styled): the stack needs
  ~14 mm between the window top (229.9) and the interior ceiling; 243 top gave 9.1, so the board +
  connector punched the top wall 347.6 mm³, all 4 M2 bosses floated in the pocket void and punched
  the display panel band (measured y 25.03..30.99), and the barrel crossed the module's top edge.
  Fix: `body_z_top` 243 → **251** (+8 forehead), `cam_lens_z` 233.5 → 237.0, bosses moved onto a
  ceiling-hung PIER behind the panel top strip (`cam_pier_*`, 0.53 clear of the panel; AF-housing
  cutout; 1 mm bosses, blind Ø1.7 pilots). Probe: cam|bezel/back/cover = 0.0000, cover|bezel =
  0.0000, board top 246.46 vs ceiling 247.0, barrel bottom 234.12 vs module top 233.4,
  screen-samples inside cam/cover = 0, FoV cone 0.0000.
- [x] **cam_cover fastening**, 2× M2 through the cover into the diagonal boss pilots
  (`cam_m2_clear_r` now used) + ribbon pinch slot; cover trimmed to board height (a +2 skirt
  punched the new ceiling). Probe: pilot voids 0.00 (fully drilled), self-tap annulus present,
  cover watertight.
- [x] **Glass-lip interference** (found by sampling, not in the original ledger): glass front
  30.99 sits FLUSH with the face (31), so the 0.5-deep retaining lip interpenetrated it 0.49 mm,
  the module could not seat on its factory-screw mounts. The pocket now pierces the face (front
  31.1): flush edge-to-edge glass, pocket side walls locate, factory screws retain. Probe: the
  lip-band screen-in-bezel sample cells are gone.
- [x] **Pi I/O slot re-aimed at the REAL Pi** (combined mesh, landscape on the display standoffs,
  stack x −37.7..48.1, y −7.0..+5.5, z 151..207.5): ETH+USB short edge faces +X → slot through the
  RIGHT side wall at y −8.5..6.5, z 191.5..208.5 (the band 165..191 belongs to the pivot boss).
  USB-C + 2× HDMI exit the BOTTOM long edge into the open interior → route out the existing
  bottom-rear neck slot/cable port. Old left-wall + top-wall slots removed (nothing exits there;
  GPIO pins point −Y). Probe: residual wall in slot path bezel/back = 0.0000.
- [x] **Bezel side posts pulled in 5 mm** (stage-2 agent had done it; verified) + layout reworked:
  the top-CENTER post's M3 shank ran through the CM3 board (x=0, z=238.4) and the raised ceiling
  left it unrooted → top posts are now a PAIR at x=±40 fused to the new ceiling; side posts at
  0.75·hh (z≈223), above the new I/O slot. **8 posts total (M3×35 ×8, nuts ×8).** Probe: bezel
  x-bounds exactly ±102.50.
- [x] **Pivot bosses trimmed flush** (stage-2 shortening already left nothing proud; verified).
  Probe: bezel/back material outside |x|=102.5 = 0.0000 both sides; bounds ±102.50.
- [x] Regression: head parts tilt sweep −30/0/+30 vs neck = 0.0000 all angles; bezel/back/cover
  watertight; EXPORT=1 rewrites all STLs (bezel 93818 mm³, back 178880 mm³, cover 1317 mm³).

**[x] RESOLVED (Stage 2R): combined screen+Pi stack vs the TILT MECHANISM.** User call: keep the
Pi on the display back, rework the tilt geometry. The **tilt axle moved BACK 18 mm** to
**(y −18, z 178)** (`tilt_axis_y` new param; `tilt_axis_z` unchanged; screen anchored separately via
`screen_cz`, it did not move). Everything keyed off the axle moved with it: cheeks, 695 seats, clamp
tubes/hubs/grubs, wheel, axle, worm group. Consequential rework, all probe-driven:
cheek boxes now stop AT the axle + a Ø19 bearing hoop (kills the pre-existing 260-sample cheek-top
overshoot into the display back; worst cheektop→display gap now **3.12 mm @ −30°**); worm group sits
4 mm further behind the axle (face offset 4→8) with the bracket plate shortened 46→36 tall (old top
clipped the head back wall at +10..+25°); the outboard bushing post, which both crossed the −30°
swept stack and clipped the wheel-tooth circle, became an **open-top cradle** (arm+riser+pad hugging
the measured swept-stack profile; worm separation force presses the Ø5 tail stub down into the
groove, so open-top is load-correct); gusset front pulled to y −20; column front-top notch
(y −21..−13, z 94..112) clears the head bottom-wall arc at −30°. Probes (12k stack surface samples +
manifold booleans): stack vs {neck, worm, motor, axle, wheel, head shell} intersection **0.000 mm³ at
every tilt −30..+30 step 5**; min gaps stack→neck **1.62 mm @ −30°**, stack→worm 2.71, stack→motor
16.8, stack→axle 8.5, stack→wheel 11.0 (all ≥ the 1.0 mm target); real bezel+back sweep vs
neck+worm+motor 0.000 at all 13 angles; worm cd = 11.500 exact; wheel|cheeks 0.000; Ø12.85 seat
plugs 0.000 both sides; neck_clevis/head_back/head_bezel watertight, EXPORT=1 clean.
Tracks/drive fixed by the Stage-3b agent. Measured-param corrections applied first (audit corr.
1/3/4/5 + reference/tt-motor-1079893/NOTES.md): `sprocket_outer_d` 42.0 → 37.6, `track_wheel_r`
19.0 → 19.32 (exact 12T × 10.0 polygon), pin bores Ø2.0 (new `track_pin_bore_d`), `track_pitch`
comment fixed (reference pitch is 9.65; our 10.0 is a re-model by design).

- [x] **Track loop below ground**, wheel centres raised to `_track_zc()` = R + 4.5 + 1.5 =
  25.32 so the bottom-run grouser face IS the ground line; road wheels + idler ride the knuckle
  crowns (r 15.82 about the pins) with 0.12/0.10 running clearance, since the sprocket needs the
  central ±4.9 channel open and the pad inner web (radial 21.12) is above the crowns. Probe:
  loop min z 0.0000 both pods, sprocket min z 6.52, roadwheels/idler vs links 0.0000.
- [x] **Sprocket bore → TT double-D** (`_sprocket`, not `dbore_neg`): socket Ø5.65 / 3.85 flat
  gap (print clearance on the measured Ø5.40/3.70), 8.0 deep = the flat length; tooth boxes
  truncated to the exact 18.80 tip circle; inboard hub OD12 reaches x=±58.3 through the wall
  web; Ø6 free bore + Ø9 × 1.7 counterbore on the outer face for the M2 retaining screw +
  washer into the shaft tip's Ø2 axial hole. Probe: tip r 18.800, sprocket|links 0.0000,
  sprocket watertight.
- [x] **TT motor rebuilt measured + real wall mount**, `motor_tt()` now: gearbox 36.80 × 22.40
  × 18.64 + Ø22.4 collar (flat on the shaft side) + can Ø20/14.99 AF + Ø9.9 × 2.2 boss + shaft
  Ø5.40/3.70 flats 8.8 proud, PERPENDICULAR to the body, 11.5 behind the front face. Motor sits
  INSIDE the chassis (gearbox face 0.1 off the wall inner face), shaft axis = sprocket axis.
  Chassis mount per NOTES.md: Ø8 wall pass (clears the Ø7.2 boss), outer Ø17 recess → 3 mm web,
  2× Ø3.2 M3 through gearbox + wall at 17.5 c-c (nuts in the pod gap), Ø4.2 × 2.2 nub pocket
  (y −49), tab pocket + Ø2.8 hole in the rear wall (y −74), deck pocket to z 36.8 (seat floor
  37, race ring r34..46 clear at r≥50.2), cavity-corner relief; ULN standoffs shifted +20 Y and
  vent i=−3 dropped (both collided with the motor envelope). Probe: motor|chassis 0.0000,
  motor|pod 0.0000, shaft-vs-sprocket axis delta 0.0000 both sides.
- [x] **Links re-modeled articulated** (`_track_link`): pad web + grouser + interleaved knuckle
  combs (near A ±9.4..14 / far B ±4.9..8.9, X-disjoint at the shared pin so articulation can
  never bind), Ø2.0 pin bores for Ø1.75 filament, 45° inner-face draft chamfers at the web
  ends. Probe: all 36 adjacent pairs 0.0000 mm³ both pods (worst 0.0000), link watertight,
  track_L/R export as 52 watertight bodies each.
- [x] **Idler tension slot + F688ZZ seat**, idler wheel r 15.7 × 18 wide with Ø15.95 press
  seat through, Ø18.5 × 1.0 flange recess on the inboard face; chassis grows a wall arm +
  Ø28 slotted plate inside the front loop arc (everything radial < 15.7 so the wrapping links
  clear), obround Ø8.2 slot with ±`idler_slot`/2 = ±2 Y-travel for the Ø8 stub axle (hardware;
  M3 set-screw lock). Probe: seat r 7.9750 / recess r 9.250 exact, idler|links 0.0000,
  chassis|pod 0.0000.

Notes for stage 4 / buy list:
- The tt-motor reference CAD is SINGLE-shaft; purchased TT motors are often dual-shaft. If the
  real unit has a rear shaft, the far pod side needs a Ø7.5+ clearance pocket mirrored about the
  gearbox (currently nothing is there, the pods have no outboard wall, so it only matters if
  a pod wall/cover is added). Verify the actual motor before closing that side.
- `body_z_top` grew to 251 in stage 3a (head +8, CoM higher): size the chassis ballast for the
  taller head when the buy list is done, keep the mass in the chassis floor, wheelbase is 120.

## Stage 4, independent re-verification  [DONE: NOT READY, 2 blocking + 2 minor defects]

Independent probes (own scripts, `scratchpad/stage4_*.py`), nothing reused from stages 1-3b.
Method note that invalidates several earlier "0.000" claims: the screen reference mesh is NOT
watertight, and `trimesh.boolean` with engine=manifold RAISES on it. The earlier probes' `ivol()`
caught that exception and returned 0.0, so every prior "stack vs X = 0.000 mm3" boolean was
vacuous (their ProximityQuery gap numbers were real). Stage 4 re-tested all screen pairs by
surface-sample containment (30k-400k samples) against the watertight partner.

### Category results

| # | Category | Verdict | Numbers |
|---|----------|---------|---------|
| 1 | Build health | PASS* | plain + EXPORT=1 exit 0, 20 parts; 10 STLs written; every body watertight. *neck_clevis exports as 5 DISJOINT bodies (defect D4) |
| 2 | Collision matrix (190 pairs, neutral) | FAIL | defects D1, D2, D3. Intended contacts confirmed: pan_balls tangency 0.030 mm3 total (18 balls, mesh discretization), worm/wheel placeholder gear mesh 19.8 mm3 |
| 3 | Kinematic sweeps | PASS | tilt -30..+30 step 5: all solids 0.000, screen samples in others 0, all 13 angles. pan -90..+90 step 15: 0.000 except pan_platform vs the STATIC motor_pan shaft mesh (2.4..15.2 mm3 growing with angle; the shaft co-rotates in reality, model artifact) + the constant 0.03 ball tangency |
| 4 | Pan stack | PASS | ball tangent both grooves 0.0000; platform top z 52.0000 flush with deck 52.0000; race ring 37.0000..42.0000; clips 0.000 at rest and at +0.3 lift, 10.13 mm3 bite at +0.5 (0.4 shoulder clearance then retention), clip tops z 52.000; D-profile only in the flat zone; platform-motor_pan 0.0000 at pan=0. Note N1 |
| 5 | Tilt drive | PASS* | worm_cd() 11.500 vs mesh axis distance 11.500, delta 0.0000; lead angle 9.46 deg (<10, self-locks); Ø12.85 seat plugs 0.0000 both cheeks; wheel+spacers span exactly x -18.00..+18.00; wheel-neck 0.0000; grub pilots at x=+-30 open (rod 0.0000); Ø5.20 axle plug bites the clamp bosses 9.44 mm3/side, outer walls loose 0.0000. *but the drive carries D2 + D3 |
| 6 | Screen + camera | FAIL | mounts at (61.61/-64.59, y 25.03, z 146.15/211.80); Ø3.2 screw paths + Ø6.0 driver channels through head_back all 0.0000; glass 30.994 vs face 31.0 (flush); 75-deg FoV cone (Ø2.63 pupil 3 mm behind the face) vs bezel 0.0000; cam vs bezel/back/cover and cover vs bezel/back all 0.0000; M2 cover paths drilled, 5.22 mm3 self-tap bite into bezel pilots, pilots ~3.8 deep. FAIL because of D1: the screen cannot SEAT |
| 7 | Tracks | PASS | loop min z +0.0000 both pods; sprocket tip r 18.800 exact; sprocket-link, idler-link, roadwheel-link, and all 36 adjacent link pairs 0.0000 per pod; motor shaft vs sprocket axis delta (0.0000, 0.0000) both sides; motor-chassis, motor-pod, sprocket-chassis, pod-chassis 0.0000; idler bore r 7.9750 (F688ZZ Ø15.95), Ø18.5 flange-recess ring present both pods |
| 8 | Cable route | PASS* | deck pass at (12,-24) clear z 30.25..55 (platform 0.000, race 0.000); platform slot mouth at (0,-38) clear; Ø7 rod up the neck channel z 52..150 = 0.000; head bottom-rear slot clears a drape capsule vs bezel/back 0.000 at tilt -30/0/+30. Notes N2, N3 |
| 9 | Docs drift | FAIL | 9 stale claims in CLAUDE.md, listed below |
| 10 | Renders | PASS | chk_iso/side/front/top/sec_* shot via port 8770, downscaled and inspected: assembly coherent, tracks on the ground line, screen framed, camera lens visible on the forehead, no floaters / z-fighting / missing parts |

### DEFECTS

- **D1 [FIXED, stage 5] (BLOCKER, stage 3a) - screen rear standoffs punch the display's own mount bosses.** The
  Pins-Out reference mesh has a raised boss/tab structure around EACH factory hole spanning
  y 22.53..25.03 (2.5 mm), annulus r 1.5..8.1 about the hole axis. The Ø9 head_back standoffs run
  solid to y=25.03 (the hole plane, which is the FRONT of that boss, not its base), so at all 4
  mounts an annular band r 1.75..4.49 x 2.5 mm deep interpenetrates (386/6.2k local surface
  samples inside head_back, max depth 1.37 mm, identical at all four sites). The screen cannot
  seat; it would stand 2.5 mm proud. Fix direction: stop the standoffs at y=22.53 or counterbore
  them to swallow the display boss. Stage 3a's "material beyond the tab plane 0.000" probe only
  checked y>25.03 and missed this.
- **D2 [FIXED, stage 5] (BLOCKER, stage 2R) - tilt worm interpenetrates the open-top cradle: 97.9 mm3**, bounds
  x -5..+5, y -24.5..-14.5, z 161.25..166.5. The cradle arm/riser/pad band (y -23..-11, groove
  r 2.7) was sized for the Ø5 tail stub, but the worm carries full-radius threads (r 5.34) all
  the way to y=-13.5; the bare stub emerges only for the last 0.5 mm (worm ends y=-13.0). About
  9.5 of the 12 mm cradle band sits under the thread envelope; the worm cannot rotate. Root
  cause: the stub (y -21..-13) is modeled INSIDE the threaded length; stub and cradle must both
  move past the thread end (or the worm shortens).
- **D3 [FIXED, stage 5] (minor, stage 2) - worm double-D bore clocked 90 deg to the motor shaft flats: 17.4 mm3**,
  bounds x -1.5..+1.5, y -30.5..-26.25 (the shaft's round shoulders buried in worm core). After
  the motor's two rotations its flats face +-X, but `db.apply_transform(R(TAU/4,(0,1,0)))` leaves
  the bore flats facing +-Z (the in-code comment claims +-Z is correct; it is not). One-line
  clocking fix; the placeholder encodes assembly intent so it should be right.
- **D4 [FIXED, stage 5] (minor, stage 2) - neck_clevis is 5 disjoint bodies.** The 4 tilt-ULN standoffs (Ø6x8 at
  x +-17.5, z 94/126) span y -69..-61 and are only FACE-TANGENT to the column back face (y=-61);
  `uni()` does not fuse tangent solids. 186.6 mm3 each, floating in the STL. Push them 1-2 mm
  into the column.

### Notes (no geometry change required)

- N1: pan D-flat engagement is 3.5 mm effective, not 7.5: the Ø5.3 round counterbore is cut
  `d_bot - hub_bot + 4` long and overshoots 2 mm into the flat zone (to z 46.5; shaft flats span
  z 44..50). Works, but half of what stage 1 claimed; trim the +4 if more bite is wanted.
- N2: the cable corridor from the neck-channel mouth (z=150) into the head necks down to a ~Ø5
  free disc (max inscribed radius 2.5 mm at z=160), squeezing between the tilt-motor can (blocks
  x<~14 up to z~173) and the +X cheek (blocks x>18). The documented Ø3.6 power pair passes with
  a jog; nothing thicker does. A straight Ø7 bundle does NOT fit (768 mm3 vs the motor can).
- N3: chassis cavity furniture at (x 8.5..14.7, y -24..-20.5, z<=30.25) sits 1.7 mm below the
  deck cable-pass mouth (straight Ø7 rod clips it 18.8 mm3); a flexible bundle routes around.

### Docs drift (CLAUDE.md; found, not fixed)

1. "9 watertight per-part STLs" (l.11) and the "9 printed parts" list (l.178): now 10;
   `pan_clips` missing from both lists.
2. Worm wheel "24T" at l.68, l.121, l.144: build uses `worm_wheel_teeth = 12`.
3. Key numbers (l.114-117): screen "measured ... 193.0 x 25.0 x 110.8" + "Loaded live from
   ..._v12.stl": the build loads `..._-_Pins_Out_v8.stl` (combined display+Pi, 192.96 x 38.01 x
   110.76). `PARAMS["screen_d"]=25.0` no longer matches the loaded mesh either.
4. "Overall assembly bbox = 221 x 208 x 248" (l.117): measured 209 x 170.5 x 251 at neutral.
5. "bezel<->back: 6 perimeter posts" (l.183): now 8 posts (stage 3a).
6. "screen: 4x M3 bosses on the bezel" (l.184): retention moved to 4 rear standoffs on
   head_back with back-wall driver channels (stage 3a).
7. "Pi 5: 4x M2.5 standoffs on the back cover (58x49)" (l.186): removed; the Pi rides the
   display's own standoffs inside the combined reference mesh.
8. The stage-2R tilt-axle relocation to y=-18 (`tilt_axis_y`, `screen_cz` decoupling) is absent
   from Mechanical intent / Key numbers (only z=178 is stated).
9. Stage-1 claim above, "D-profile now only over the flat zone (z 44.5..52)": effective D zone
   is 46.5..52 (see N1).

### Verdict

**NOT READY TO COMMIT.** Blockers: D1 (screen seating), D2 (worm/cradle). D3 + D4 are small but
should ride along; docs drift items 1-8 belong in the same pass.

## Accepted findings (no geometry change)

- Worm lead angle 9.46°: self-locks dry, backdrives greased, but the 28BYJ's internal 64:1 train
  never backdrives, so the de-energized hold stands regardless. (Honest-worm option: worm_od 14.)
- Hollow-axle cable routing at Ø2.5 is fiction for a 5 A pair, the real route is the bottom-rear
  slot beside the clevis (tilt is only ±30°); the bore stays as weight relief. Docs updated.
- 18 uncaged BBs: grease-stick at assembly; a printed cage ring is a nice-to-have part.
- Axle: buy Ø5 brass/steel tube (K&S 300 mm stock); a printed axle is unusable (5.9 mm sag).

## Fastener BOM (from the assembly review; re-check after stage 3)

M3×35 ×8 (bezel↔back, stage-3a layout) · M3 nut ×11 · M3×12 ×4 (screen, from behind through the
Ø6.5 back-wall channels into the display's threaded pan holes) · M3×16 ×3 (platform→neck) · M3×8 ×2 (pan
ears) · M3 grub ×4-5 · M4×10+nut ×2 (tilt ears) · M2.5×8+nut ×4 (Pi) · M2×8 self-tap ×2+2 (camera
+ cover) · 695-2RS ×2 (owned) · F688ZZ flanged bearing ×2 (8×16×5, flange Ø18) + Ø8 stub axle ×2 + M2×16
self-tap ×2 (sprocket retain) · 6 mm BB ×18 · Ø1.75 filament pins ×72 ·
Ø5×209 tube ×1 · 28BYJ-48 ×2 + ULN2003 ×2 (owned) · TT gearmotor ×2 (own 1, **buy 1**).

## Stage 5, fix pass (D1-D4) + neck-on-platform  [DONE]

- [x] Neck base footprint r62.9 overhangs the spinning platform (r48; solid top r45 inside the
  clip rebate) and rides the FIXED deck with zero gap. Move the column in (neck_y -38 -> ~-14)
  so the whole footprint sits on the platform at r<=44. The tilt axle (y=-18, z=178) and the
  head DO NOT move (stage-2R world-coord parameterization). Move with it: 3x M3 bolt circle,
  platform cable slot, deck cable pass alignment; deepen the column front notch for the head
  chin arc at -30 deg. Re-probe: pan sweep vs deck/clips, tilt sweep, cable route, watertight.

### Stage 5 results (fresh probes, scratchpad st5_*.py; screen checked by surface samples,
### booleans raise on failure)

- **D1 fixed** - standoff bearing face moved from the hole plane to the display boss REAR
  plane: boss lip measured 2.500 (y 22.534..25.034, identical all 4 mounts, annulus census);
  new face y=22.480 (lip 2.5 + 0.05 seat clearance, `scr_boss_lip`/`scr_seat_clear`).
  Probes: 0/400k screen samples inside head_back (0 per site at all 4 mounts), 0/30k inside
  head_bezel; glass front 30.994 (flush, target 30.994 +-0.05); screw path 0/400 hits per
  mount; 6 mm seat solid 400/400 per mount.
- **D2 fixed** - worm_len 16 -> 14 + face_y offset 8 -> 9.5: thread span now y -32.00..-16.29
  = 15.71 mm = 4.00 axial pitches (>=4 teeth-equivalent), bare Ø5 stub forward of y=-16
  (max r fwd of -15.5 = 2.500); cradle groove band moved to y -15.5..-13 on the stub, riser/
  pad rear split into two side prongs by an r5.9 envelope-relief bore about the worm axis.
  Probes: worm vs neck static 0.000; ROTATION swept envelope (64-slice surface of revolution,
  max thread r 5.344) vs neck 0.000; worm_cd()=11.500 vs mesh axis distance 11.500, delta
  0.0000; wheel-worm placeholder contact preserved (32.9 mm3).
- **D3 fixed** - removed the extra `R(TAU/4, y)` clocking on the worm's double-D bore
  (dbore_neg(axis="y") already cuts flats +-X = shaft flats); comment corrected.
  Probe: worm vs motor_tilt 17.4 -> 0.000 mm3.
- **D4 fixed** - tilt-ULN standoffs lengthened 8 -> 8.5 and buried 0.5 into the column back
  face. Probe: neck_clevis = 1 watertight body (was 5 disjoint).
- **Neck-on-platform done** - `neck_y` -38 -> **-17.0** (derived: footprint max r =
  sqrt(14^2+(|ny|+13)^2)+10 <= 44 gives |ny| <= 17.98; measured 43.10 at z 52..55).
  Cascade: bolt circle re-clocked (90,210,330)r12 -> (270,30,150)r16 in BOTH neck pilots and
  platform holes (old layout put a hole 2 mm off the pan axis, inside the D-bore hub); cable
  channel decoupled to `neck_chan_y`=-26 (behind the notch; platform slot start + deck pass
  aim follow it); cheeks re-anchored at (+-22, -33, 155) on a new 52x14x10 cheek-root block
  (anchoring at ny=-17 grazed the resting stack and buried 11 mm into the -30 sweep); column
  front notch re-derived: the -30 sweep (shell chin to y=-16.7 @ z~102, display back band to
  y=-14 right up to z 150) forces the whole column front above z=94 back to y=-19.5.
  Probes: footprint max r 43.10 <= 44.0; pan sweep -90..+90 step 15 vs all fixed parts 0.000
  (only the known 0.031 ball tangency, intended contact, = stage-4's 0.030); tilt sweep
  -30..+30 step 5: head solids vs neck group all 0.000, screen samples in neck group 0 at all
  13 angles; cable route: Ø7 rod through the deck pass (12,-24, z 30.5..55) vs platform/race/
  chassis 0.000, Ø7 rod down the channel (0,-26, z 45..150) vs neck/platform 0.000; all 3
  bolt holes on solid platform (r 16.5/16.5/33.0, annulus 300/300 solid, bore open, clear of
  hub/rebate/groove/slot), neck pilot rings 300/300 solid.
- **Build health**: plain + EXPORT=1 exit 0; all 10 printed STLs watertight; single-body
  everywhere except the by-design multi-body track_L/track_R (52) and pan_clips (3).
  Renders (st5_iso/side via port 8770) inspected: assembly coherent, no floaters.

## Stage 6, independent re-verification of stage 5  [DONE: READY TO COMMIT]

Same methodology as stage 4 (own probes, `scratchpad/stage4_*.py` + `stage6_d123.py`; screen
mesh checked by surface-sample containment, booleans raise on failure, nothing reused from the
stage-5 agent's scripts).

| # | Category | Verdict | Numbers |
|---|----------|---------|---------|
| 1 | Full collision matrix (190 pairs, neutral) | PASS | only intended contacts: pan_balls tangency 0.030 mm3 (both grooves), worm/wheel placeholder gear mesh 32.9 mm3. D1/D2/D3 pairs all gone |
| 2 | D1 screen seating | PASS | 0/400k dense samples inside head_back at all 4 mounts (was 386/6.2k per site), 0/60k global in back AND bezel; standoff bearing face measured y=22.480 (= 25.03 - 2.5 lip - 0.05 seat, exact); glass front 30.9940 flush; Ø3.2 screw paths 0.0000 x4 |
| 3 | D2 worm rotation | PASS | 40-slice revolved envelope (max thread r 5.344) vs neck 0.0000; static 0.0000; thread span y -32.00..-16.29; bare stub forward of y=-15.5 max r 2.500 vs groove r 2.7; envelope vs the tilting head (bezel+back+axle) 0.0000 at -30/0/+30 |
| 4 | D3 bore clocking | PASS | worm vs motor_tilt 0.0000; negative control (worm rotated 90 deg about its axis) 17.36 mm3, proving the flats exist and are correctly clocked; worm_cd 11.500 vs mesh 11.500, delta 0.0000 |
| 5 | D4 watertight / bodies | PASS | all 10 STLs, every body watertight; neck_clevis 1 body (was 5); multi-body only track_L/R (52) + pan_clips (3), by design |
| 6 | Neck footprint + pan/tilt sweeps | PASS | footprint max r 43.098 at z 52..55 (<= 44; also max r below z=60), neck vs platform/clips/chassis/race 0.0000; pan -90..+90 step 15 vs all fixed: 0.000 (constant 0.03 ball tangency + the known static motor_pan shaft artifact only); tilt -30..+30 step 5: solids 0.000, screen samples 0, all 13 angles |
| 7 | Bolt circle | PASS | holes at az 270/30/150, r-from-pan-axis 33.00/16.52/16.52, plate annulus 100/100 solid each, bores fully void, Ø2.3 rods through platform hole + neck pilot 0.000 x3 (aligned) |
| 8 | Cable route | PASS | Ø7 deck-pass rod (12,-24, z 30.5..55) vs chassis/platform/race 0.000; Ø7 channel rod (0,-26, z 45..150) vs neck/platform 0.000 |
| 9 | Renders | PASS | st6_iso/side/sec_mid via port 8770: column lands on the platform, assembly coherent, tracks on the ground line, no floaters / z-fighting |

Docs: CLAUDE.md drift from stage 4 is resolved (10 parts, 12T, Pins_Out_v8; the one remaining
"24T" is a historical "was 24T" note, not a stale claim).

**Verdict: READY TO COMMIT.** No defects found. Standing model-only artifacts (not defects):
static motor_pan shaft vs the swept platform D-bore (shaft co-rotates in reality), placeholder
worm/wheel tooth interpenetration (regen in BOSL2 before printing), 0.03 mm3 ball-seat tangency.

## Wallcheck gate findings (2026-07-13, skills fix campaign)

The new `make wallcheck` min-wall gate (src/wallcheck.py, in `make all`) surfaced and
closed these on its first full runs:

| Finding | Verdict | Fix |
|---|---|---|
| track_keeper_L/R tab rim 0.65 mm (Ø4.2 M2 counterbore on the 2.6x5.5 tab) | DEFECT, fixed | cb Ø4.2 -> Ø4.0 (M2 pan head Ø3.8 max) + tab 5.5 -> 5.7; rim now 0.85, slot-critical 1.9 bar untouched, keeper-wall clearance 1.35 |
| head_back_frame_L/R exported STLs non-manifold (float32 write collapses near-equal float64 vertices at the cap-plane junctions; in-memory mesh passed is_watertight) | DEFECT, fixed | geo.export_stl(): float32-quantized watertight check on every export; guarded manifold3d repair (volume < 0.1%, bbox < 0.01 mm, asserts) |
| neck_clevis 0.12 mm feather wedges (cradle-pad underside vs Ø5.4 tail-stub groove bottoming 0.2 below it) | DEFECT, fixed structurally | cooler-clearance pass deleted the pad+groove; the new crest-riding half-groove bottoms 4 mm above the block bottom; p1 now 1.75 |
| tilt_worm / worm_wheel / pan_gears sub-0.8 populations | EXPECTED geometry, whitelisted | probe-located to tooth tips, thread run-out feathers, and helical face-edge feathers; mesh probe-verified per docs/WORM.md; documented floors 0.2 / 0.4 / 0.75 |

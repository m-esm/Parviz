# Assembly

Current assembly notes for the tracked desk-pi prototype. The task #28 insertion/torque-path
audit (2026-07-07) verified a complete install order exists (see "Assembly order (verified)"
below). The 2026-07-08 maintenance pass then killed the worst service traps: tilt motor is a
rear-access cartridge (`tilt_carrier`), the worm wheel is D-keyed to a flatted axle (no blind
grub), tracks close with a master link (no loop-flexing), the pan race got a BB cage, both
joints got stall-homing hard stops, the microSD swaps through a plugged left-wall slot, the
positively located side-panel joints, and power is a 12 V PD-trigger + dual-buck belly tray
(firmware/WIRING.md). Not print-final: still open is a D-key fit coupon for the axle flat.

## Bill of materials

Owned quantities cross-checked against a personal parts inventory (2026-07-07; re-audited
2026-07-13 with bag-label photo reads: TT motors, M8, 608zz, F688 candidates, fuses all
settled below). "Need" is per robot.

### Electronics

| Part | Spec / where it goes | Need | Owned | Buy |
|---|---|---|---|---|
| Raspberry Pi 5 | 2 GB, rides the display's own 58x49 standoffs | 1 | 1 (Tray 1) |, |
| 7" touchscreen | official kit; 4 factory M3 mounts (126.2x65.65) | 1 | 1 (Tray 1) |, |
| Camera Module 3 | recessed forehead, 4x M2 at 21x12.5 | 1 | 1 (Tray 1) |, |
| 30W+ USB-C PD brick | any brick offering 12V (the official 27W works); the robot bucks 12V down internally, see firmware/WIRING.md | 1 | 0 | **1** |
| USB-C PD trigger board | set to 12V; mounts on the rear-wall M2 pilots beside the USB slot | 1 | 0 | **1** |
| XL4015-class 5A buck | Pi rail (trim to 5.25V); 40x20 post grid on the belly-plate tray | 1 | 0 | **1** |
| MP1584-class mini buck | motor rail 5V; zip anchors beside the main buck | 1 | 0 | **1** |
| JST-XH kit + crimper | every joint-crossing / board run is a keyed XH plug | 1 | 0 | **1** |
| 18 AWG silicone pair + 5A blade fuse + inline holder | Pi-rail run + inline fuse at the tray | 1 m | fuse: OWNED (ATC/ATO blade assortment, settled 2026-07-13); wire + holder: 0 | **1 m wire + 1 holder** |
| 28BYJ-48 stepper | 5V, pan + tilt + 2x antenna drives | 4 | 6 (Bag 14) |, |
| ULN2003 driver | one per stepper | 4 | 9 (3 Bag 14 + 6 Bag 5) |, |
| TT gearmotor 1:120 | track drive, one per pod, shaft on X into the sprocket; +2 OPTIONAL for the twin-drive front stations | 2 (+2 opt) | **3 (Bag 5, re-audited 2026-07-13; the old "own 1" was stale)** | , (**1** only if the optional 4th station is populated) |
| MX1588 dual H-bridge | drives both TT motors, skid steer | 1 | 5 (Bag 7) |, |
| WS2812 forehead segment | 8 LEDs in the `led_slot` recess: **42 x 5 mm, 1.5 deep** (model dot pitch 4.6). A standard 8x5050 stick is 53.3 x 10.2, it does NOT fit. Buy a narrow (4–5 mm wide) addressable strip (SK6805-2427 / WS2812-2020, ≥160 LED/m) and cut an 8-LED segment, or widen `led_slot` to ~54 x 11 for the common stick | 1 seg | 0 | **1 m narrow strip** (also covers the front strip, next row) |
| Front white strip | 7 dots at 5 mm pitch in a 36 x 2.5 lip (`fled_*`): either 7x 3 mm white LEDs or a second segment cut from the same narrow WS2812 strip | 1 | 0 | covered by the strip above (or 10x 3 mm white LED) |
| Amber indicator LEDs | 2 corner lamps, 12 x 7 windows (`lamp_*`): 2 rectangular amber LEDs (2x5x7) or 5 mm amber behind a printed lens | 2 | 0 | **2–5** |
| HC-SR04 ultrasonic | x4 since the 2026-07-10/11 sensor passes (this row used to say "optional x1", stale): forward + rear obstacle (grille rings, Ø16 barrel passes at 26 mm c-c, `us_dx`=±13) + 2 cliff (deck slopes). With the Arduino I/O plane (docs/AWARENESS.md) plain 5V HC-SR04 is fine; HC-SR04P (3.3V) only needed if wired straight to Pi GPIO | 4 | 0 | **4** |
| Rear pod audio | rear Ø14 cylinder pod (`rear_cyl_*`): an owned Ø12 active buzzer fits for beeps. For real audio, buy a **MAX98357A I2S amp** and drive the owned 8Ω 0.5W mini speaker (Bag 15) from inside the chassis, the speaker is ~40–50 mm and can't live in the pod; the pod becomes the grille | 1 | buzzers: 5x active 5V (Bag 1) + 4x ~12 mm (Bag 16); speaker: 1 (Bag 15) | **1x MAX98357A** (only if speech/audio wanted) |
| Arm actuation | placeholder arms, TBD pending the arm mechanism pass. If actuated: 9x 9g servos owned (5x T-8090, 3x SG90, 1x MG90S) | TBD | 9 servos | nothing yet |

### Bearings, race, axles

| Part | Spec | Need | Owned | Buy |
|---|---|---|---|---|
| 695-2RS | 5x13x4, tilt-axle cheeks | 2 | 30 (Bag 13) |, |
| F688ZZ flanged | 8x16x5, flange Ø18; END idlers (both loop ends are free idlers since the 2026-07-11 mid-drive), **2 per wheel x 4 wheels** (one pressed at each face, Ø15.95 through-seat + Ø18.5x1.0 flange recess both sides). The Bag 13 "Miniature Ball Bearings" were checked as a candidate 2026-07-13: label reads **10pcs MR105 ZZ** (5x10x4, unflanged) -- wrong part | 8 | 0 | **8** |
| 6 mm airsoft BBs | pan race, Ø80 circle, `pan_race_n`=18 | 18 | 0 | **smallest bag (100+)** |
| Ø5 SOLID rod | tilt axle, ~100 mm silver steel (**NOT tube**: a 1.0 flat on a Ø5/Ø2.5 tube leaves a 0.25 wall). **File a 1.0-deep flat** from the insertion end to ~15 past center (D-key for the worm wheel's hub ledge); only the ~6 mm under the hub needs a clean 1.0 ±0.1 depth. The flat crosses the +X 695 seat, so that inner race rides a D-profile (fine, the spacer tubes clamp it). Print a D-bore coupon first, starting at **+0.05** clearance (+0.15 measured as ±4.4° of head backlash) | 1 | 0 | **1** |
| M8x**70** bolts + NYLOC nuts | END BOLT-AXLES: head = outboard hubcap, smooth journal through both F688s, thread begins at x=78 and crosses the tower clamp stack. M8x60 is too short to reach the NYLOC insert. | 4+4 | 0 | **4x M8x70 + 4 NYLOC** |
| M8 JAM NUTS + washers | **Required and modeled:** one AF13 jam nut bears on each tower's outboard face; the washer and NYLOC bear inboard. This closes the previous 17.4 mm air gap, clamps the tension slot/tower, and leaves the idler free on the smooth journal. The printed export likewise contains 8 total M8 nuts. | 4+4 washers | 0 | **4x M8 jam nut + 4 washers** |
| 608zz | **not used** in the current design. SETTLED 2026-07-13: the bag label reads **"10pcs-608ZZ"** -- real 608ZZ bearings under translucent shrink wrap, not plastic rings. Still don't design around them | 0 | ~10-30 (608ZZ, confirmed by label) |, |

### Fasteners and pins

| Part | Spec | Need | Owned | Buy |
|---|---|---|---|---|
| M3 screws + hex nuts | captive-nut joints everywhere; incl. M3x35 x8 bezel↔back. **2026-07-15 fastening campaign: ~+55 M3 hex nuts** as the thread-form pilots that failed the first print became real captive traps (head +32, chassis +24 incl. tail seam/deck/TT-upper/y26, neck +7 root & carrier & ULN). Screw length changes: y=26 seam M3x12 → **M3x20**, neck→platform M3x12 → **M3x14** | lots | 540pc M3 stainless kit + 175pc M3 30–50 mm kit + 600pc M2-M5 kit + 1263pc M2-M4 kit (all Tray 1) | , (kits cover it) |
| M2/M3 brass heat-set inserts | **16 total, and a soldering-iron insert tip.** Used ONLY where a captive nut was probed and measurably does not fit: **4x M2** track master-link keepers (below), **8x M2** cliff HC-SR04 (a 3.8 mm skin at 33.7 deg has no room behind), **2x M2** PD-trigger (edge-on into wall layers = the weakest thread orientation), **2x M3** rear panel L-feet (boxed on all four axes by the BME board, the tail pad, the TT gearbox and the glacis: 5.70 window vs 6.80 needed). Everywhere else the campaign uses a real captive nut -- probing DISPROVED the audit's insert calls twice (tilt_carrier, pedestal ears). All VERIFY_ON_ARRIVAL: vendor OD/length varies, re-key `keeper_insert_*` / `foot_insert_*` before printing | 12x M2 + 2x M3 (+2 spare) | 0 | **16 inserts + 1 insert tip** |
| M2 brass heat-set inserts (detail) | **track master-link keepers** (2/master x2 = 4). The captive M2 nut does NOT fit: the pocket is boxed between the jaw slot's tension wall and the neighbour A-knuckle = 5.50 mm usable vs 5.82 needed across-corners (measured, tracks agent). Inserts need 5.40. This is the one repeatedly-serviced M2-in-PLA joint, so self-tapping was never going to survive the service cycles | 4 | none | **4x M2 brass heat-set + a soldering-iron insert tip** — VERIFY_ON_ARRIVAL: vendor OD/length varies, re-key `keeper_insert_{d,l}` before printing masters |
| M5 penny washers | tilt worm thrust seat (OD 15, ID 5.3, t 1.0): closes 2.0 mm of worm float (≈3° tilt slop) to 0.1. A direct shoulder is impossible — any ID under the Ø10.55 crest blocks cartridge extraction | 2 | check the owned washer assortment | 2x M5 penny washer (OD ~15) |
| Ø4 dowels | seam/joint registration so parts self-hold while screwing (the audit's "nothing holds it" class). +3 head (2 bezel↔back split plane, 1 Ø4x14 flange), +2 neck→platform printed pins, + existing y=26 pair. Tail seam uses a 6x12x4 **tongue** instead (no room beside the bore in a 10.2 pad; more shear area anyway) | ~8 | printed stand-ins in stl/hardware (Ø3.9) | Ø4x12 metal dowels x4 (or keep printed) |
| M2 screws | camera board (2 screwed + 2 locating pads) + cam_cover (2) + track master-link keepers (2/pod, **M2×8 pan head**, sunk in the tab counterbores) + PD-trigger mount (2) | 8+ | in the 600pc M2-M5 and 1263pc M2-M4 kits |, (CLAUDE.md's "buy M2" is stale) |
| M3 nylon standoffs | ULN2003 / driver mounts | few | 380pc kit (Tray 1) |, |
| Track hinge pins | Ø1.75 filament, Ø2.2 boundary bores only (2026-07-12 print-in-place strips: the 59 in-strip joints/side ride INTEGRAL printed Ø2.0 pins). Per pod: 3 strip-to-strip + 2 at the master (its far-end pin + the jaw closure pin) = **10 pins x ~46 mm** ≈ 0.5 m, cut from an owned spool (the black CR-PETG is tougher than PLA for pins) | 10 | spooled (Tray 1) |, |
| Ø4 dowel pins | body-to-pod join (2 per side), Ø4x12: modeled (wall slip holes + rail press sockets) | 4 | 0 | **4** |
| HC-SR04 ultrasonic | x4: forward + REAR obstacle (front/rear walls, inside the twin grille rings) + front/rear cliff (flush in the deck slopes, boards behind the 5-thick skin). **Inventory has ZERO** (checked 2026-07-10) | 4 | 0 | **4** |
| M4x40 + nuts | road-wheel bolt-axles (2026-07-10 fix: wheels were mounted to nothing): head = outer hubcap, shank in the Ø4.2 wheel bore, nut captive in the rail wheel-beam slot. Prefer partially threaded (shank bearing surface); 40 mm exceeds the owned kits | 10+10 | nuts: OWNED (the 600pc M2-M5 kit lists **M4 nuts x40**, settled 2026-07-13); bolts: 0 | **10x M4x40** |

### Printed parts (watertight; tank base + split head)

**Materials:** print `head_back` (all four pieces), `screen_tray` and `head_door` in
**PETG, not PLA**. The Pi 5 lives in the closed head and sustains 70-80 C bursts under
brain load (measured, see CLAUDE.md thermal notes); PLA creeps from ~60 C, so a PLA tray
would slowly sag under the screen+Pi module and a PLA back wall would relax its snap
tongues and tray pilots. The head_door shares the same hot bay, so it goes PETG too
(its snap tongues also live longer in PETG). Everything else on the robot -- chassis,
tracks, bezel, neck, pan parts, cosmetics -- can stay PLA. The black CR-PETG spool
(Tray 1) covers the PETG set.

- `chassis_lower_front` / `chassis_lower_rear`: the open-top tub, split at y=+26 for
  print speed; join with 2x M3x20 (axis Y, heads in the front pads, captive nuts rear)
  + 2x Ø4 dowels in the floor pads at x +-61; the deck and bolted side panels bridge it
- `chassis_deck_front` / `chassis_deck_center` / `chassis_deck_rear`: the pan deck in
  three plates (seams y 66/-52, half-laps + 2x M3 down through each strip into shelf
  pilots); the center carries the whole pan seat + its own 4 hold-downs; the corner
  hold-downs live in the strips
- `track_L` / `track_R`: tank track pods: 64 links/side (4 print-in-place strips +
  master; integral Ø2.0 pins in-strip, Ø1.75 filament pins at the 5 boundaries), 12T
  pin-pocket sprocket (real circular pin seats since 2026-07-10, r 1.15 on the 19.32
  pin circle), 2 end idlers on 2x F688ZZ each (30 wide; front tensions in its panel tower),
  TWO ground-run drive sprockets (spr_y rear + spr_y2 front; the front motor is
  OPTIONAL, all fittings modeled), 5 dished road wheels/side
  (30 wide) on M4x40 bolt-axles off the pod-rail wheel beams
- `pan_platform`: disc that yaws on the base (central shaft bore + off-axis cable pass)
- `pan_race` / `pan_balls` / `pan_clips` / `pan_cage`: captured-BB lazy-Susan race, retaining
  clips, and the BB spacer cage (18x 6 mm BBs; `pan_balls` is a placeholder for the bought
  BBs; the cage keeps them spaced so a turret lift doesn't scatter them)
- `neck_clevis`: rounded column + two cheeks that rise into the head and drive the tilt axle;
  vertical cable channel
- `head_bezel_L` / `head_bezel_R`: front frame split at x=+22 (M3 + Ø4 dowel in pads
  behind the forehead/chin strips); seam staggered off the back's for interlock
- `head_back_frame_L/R` + `head_back_panel_L/R`: rear cover in four (frames = walls +
  pivot hubs, print front-down, no ceiling support; panels = the flat 4mm back wall,
  print lying flat). 6x M3 from the back join panel to frame rim tabs; the frame
  halves share the top-wall flange (2x M3) and the panel halves a tongue/groove
- `screen_tray`: bench-mounted module carrier (2 rails + spine): the screen+Pi bolts to it
  on the bench (4x M3x10 into the factory bosses, open access), the loaded tray drops into
  head_back, 4x M3x10 drive from OUTSIDE the back wall (visible, between door and frame)
- `cam_cover`: camera board cover and cable trap
- `sd_plug`: friction plug for the microSD service slot (left wall + trim_rail_L); pull it,
  reach the card with straight forceps down the eject axis (~61 mm, sight line clear)
- `tilt_carrier`: removable tilt-motor cartridge plate; the motor's ears drop onto its
  pin-topped D-posts on the bench (2026-07-16 sandwich retention, see step C),
  4x M3x16 clamp it to the neck bracket from the open rear bay
- `track_keeper_L/R`: master-link keeper bars (2 bars + side tabs per pod, 1x M2 each);
  the master link body prints as link 0 inside each `track_L/R`
- `worm_wheel` / `tilt_worm`: real generated teeth (docs/WORM.md); the wheel hub now carries
  the D-key ledge (regen includes it via the build's hub union)
- Cosmetic / design-ref set (render-only today, print with the head): side rails, forehead
  `led_strip`, `camera_pod` eye shell, rear `trim_hatch_frame`, chassis
  `trim_fascia` + `trim_rear`, and the placeholder gripper arms (mechanism TBD)

### Plastic hardware stand-ins (interim, plate "Hardware stand-ins")

Until the metal order lands, every buy-list hardware row above has a PRINTED
stand-in (`src/standins/` -> `stl/hardware/`), so the whole robot dry-assembles in
plastic. The BOM is unchanged; swap each stand-in 1:1 for metal on arrival.

**REWORKED 2026-07-16** ("as functional and as close to reality as possible"). The
M4 and M8 pairs now carry **real ISO threads** (`src/threads.py`) and screw together
for real. More importantly, the rework caught **three v1 parts that were physically
unbuildable** -- each had inherited nominal metal dimensions with no print
compensation, which looks perfect in CAD:

> **RULE: a stand-in mates PRINTED-TO-PRINTED or PRINTED-TO-STEEL, never
> nominal-to-nominal.** Budget 0.1-0.2 mm per printed surface, put the compliance on
> the printed part (crush ribs beat a tight window), and probe the real mating
> geometry -- never copy the metal part's numbers or the CAD placeholder's.

| Stand-in | Qty | Replaces | Notes |
|---|---|---|---|
| `hw_m4_bolt` | 10 | M4x40 bolt-axles | real SHOULDER bolt: plain Ø3.9 journal + M4x1.0 threaded tail. The shoulder is the axial stop, so the wheel stays free however hard it is done up. Ø10.4 thumb head. **A stock DIN 931 M4x40 would start thread INSIDE the wheel (~18 shoulder vs the ~35 the stack wants) -- the printed part is better than the metal it replaces** |
| `hw_m4_nut` | 10 | (owned steel M4 nuts) | AF7 hex, real M4x1.0 internal thread + lead-in per face. AF and 3.2 thickness are the SLOT's (it is cut for an AF7 hex ACROSS CORNERS -- that is what centres it on the bore) |
| `hw_m8_bolt` | 4 | M8x70 end bolt-axles | knurled Ø22 thumb head, smooth Ø8.0 journal under the bushings AND through the tension slot, M8x1.25 thread only where the nut runs |
| `hw_m8_nut` | 8 | 4 inner M8 nuts + 4 outer jam nuts | AF13, real M8x1.25 thread, 6.0 tall + countersinks. The pair clamps each tower; no NYLOC analogue exists in PLA, so re-snug after creep |
| `hw_m8_washer` | 4 | Ø14.4 washers | **flatted to AF13**: a round Ø14.4 disc overlaps the tower nut cage by 5.2 mm³ (its old seat was deleted by running-gear v2). A printed wave washer was rejected -- it creeps by the mechanism it would compensate |
| `hw_f688_bushing` | 8 | F688ZZ bearings | **v1 could not spin** (all three fits closed nominal-to-nominal). Now bore Ø8.6, body Ø15.2 + its own crush ribs at Ø16.0, flange Ø17.9, 3 axial grease grooves. **Grease is required -- it is the service life, not a nicety** |
| `hw_pan_ring` | 20 | 18x Ø6 BBs | **v1 could not move** -- the torus slid at ~96 mNm vs the pan's ~15-17 mNm. Now 18 barrel rollers + 2 spares: Ø5.9 sphere, flats on the SPIN POLES, printed axis-up / installed axis-radial. **pan_cage is used again.** Print at 0.1 mm layers |
| `hw_tilt_axle` | 1 | Ø5 silver-steel rod | **v1 could not be assembled** (Ø5.000 into a Ø5.000 STEEL 695 bore = +0.000). Now Ø4.8 print-compensated, D-key ledge referenced to the AXIS so key clearance is unchanged |
| `hw_seam_dowel` | 5 | Ø4x12 dowels | Ø3.9 (not Ø4.0 -- a printed dowel is the other half of the tolerance stack) + lead-in chamfers |
| `hw_foot_pin` | 2 | Ø3x8 trim_neckfoot pins | **Ø3x8, not x6** -- the 2026-07-15 socket deepening (5.0 socket + 3.0 collar = flush) |

Limits to respect on plastic (full rationale in `src/standins/__init__.py`):

- **The track tensioner now has a real clamp stack:** outer jam nut, tower, washer,
  inner nut. The idler stays free on the smooth journal while the tower is clamped.
- **M4 is a real fastener now**: it screws, tightens and re-uses. Snug it; don't lean
  on it (~400 N strip vs a metal M4's ~2 kN).
- PLA creeps, so preload decays over hours -- but with real threads that decay is
  bounded and recoverable: re-snug, nothing degrades permanently.
- Tilt homing is **usable** (~1.3-1.5 deg wind-up, the same order as the design's own
  D-key backlash, and stall homing calibrates it out). Park at the balance point --
  the real cost is 1-3 deg of creep droop over hours.
- The dry pan **slews, but slowly and near the limit**, and may need a nudge from
  rest. Grease both grooves. Don't time the dry pan and call it a gear-ratio verdict.
- Idlers are greased plain bearings: ~50x a ball bearing's rolling resistance, but
  only 0.17-0.70 N to roll, which the track's own weight exceeds.

## Verify on arrival (caliper before printing)

The CAD models several bought parts from datasheet/typical dims, not measurements. The
rule for every row: **caliper the real part -> update the named param(s) -> `make build`
-> `make check` + `make fits` -> only then print the dependent parts.** Clone boards
vary: barrel/jack spacings tend to be stable across clones, mounting-hole patterns are
not. Printing a seat before its part has arrived is how reprints happen.

| Arriving part | Caliper this | CAD that depends on it (do not print first) |
|---|---|---|
| XL4015 5A buck | board LxW, mounting-hole pattern (40x20 assumed) + hole Ø, tallest component height | belly power tray posts (Ø6x6, Ø2.5 pilots, `build_belly_plate` in src/chassis.py); board must clear the z14 ballast ribs |
| MP1584 mini buck | board LxW only (zip-mounted, no holes) | zip-anchor pair spacing (x 20/34, y -58) on the belly plate |
| 12V PD trigger | board LxW, jack position + height above board, mounting-hole spread | rear-wall USB-C slot (14x8 at x -38, z0+24) + the 2x Ø1.7 M2 pilots at x -38±9 |
| HC-SR04 x4 | barrel c-c (26.0 assumed -- stable), barrel Ø (16.0/16.6 bores), board LxW, **mounting-hole positions (vary by clone!)** | front/rear grille recesses + fascia pilots; both cliff recesses in the deck slopes (1.2 skin-back recess + 4x Ø1.6 M2 pilots each, `sensor_cliff*`) |
| Gooseneck mic windscreen | foam Ø (17 assumed) + gooseneck stem Ø | ear grommet Ø15 compress-fit bores + Ø19/Ø15 trim rings in the head_back side walls (`ear_*` params) |
| LD2410 / SW-420 / TTP223 | board LxW + hole pattern each | chassis sensor seats (being added parametrized -- treat every one as VERIFY_ON_ARRIVAL, exact modules not yet chosen) |
| Sense HAT Rev2 (ordered 2026-07-14) | 65x56.5 outline, M2.5 holes on the 58x49 pattern, component heights | replaces the IMU posts + BME bosses on chassis_base with a 4-standoff HAT seat (next base iteration; the HAT covers IMU + temp/humidity/pressure, BME688 now optional-for-gas) |
| Joy-IT RPI5-HEATSINK5 (ordered 2026-07-14) | true installed envelope incl. fan | 65x45x15 EXCEEDS the verified official-cooler keep-out 63.5x42.5x13.7 -- re-run tools/probe_cooler.py with measured dims BEFORE head install |
| AI Camera IMX500 (ordered 2026-07-14) | module depth + lens barrel vs CM3 | forehead cam pod is CM3-sized; re-fit pass needed before swapping the eye |
| M8x70 + jam nut + NYLOC | nut across-flats (13.0 nom), nut height, washer OD, and usable thread span | panel-tower clamp stack + Ø14.4 flatted washer seat |
| M8 shank / Ø8 journals | actual shank Ø | tower Ø8.4 through holes + F688 8 mm bores (a fat zinc bolt binds) |
| F688ZZ | flange Ø (18) + width (5) + OD (16) | idler Ø15.95 press seats + Ø18.5x1.0 flange recesses |
| Narrow LED strip | strip width + dot pitch | 42x5x1.5 `led_slot` + the 36x2.5 front lip (widen `led_slot` to ~54x11 only if forced onto 8x5050 sticks) |
| Ø5 rod | actual Ø (silver steel is -0/-0.01; generic rod varies) | 695-2RS 5 mm bore slip fit, head clamp bores, and the D-key coupon clearance (+0.05 start) |
| XH connectors | crimped-head width | 16x8 platform obround + neck channel passes (sized for a 5-pos XH head) |

## Assembly order (verified)

Task #28 insertion-path + torque-path audit (2026-07-07): a full install order EXISTS
end-to-end. Every step below was checked with swept-cylinder driver-line / extraction
probes on the neutral-pose mesh; the numbers in parentheses are the worst measured
clearance. Read the **order constraints** and **nasty steps** at the bottom before you
start: several joints are only reachable at ONE point in the sequence.

Tools you need: a **1.5 mm hex key** (head-clamp grubs), a standard M3/M2 driver, tweezers,
and thread-lock or CA glue (cosmetics). (The old ~95 mm slim driver is retired: the screen
tray killed the 88.5 mm blind channels, 2026-07-08.)

### Sub-assemblies to build on the bench FIRST (they become unreachable once seated)

- **A. Neck + pan platform.** With `pan_platform` upside-down on the bench, drop 3× M3 up
  through its underside Ø6.5 counterbores (r16.5 circle, clocked 270/30/150) into the
  `neck_clevis` base pilots. The counterbores face DOWN into the race once seated, so this
  bolt-up is impossible after the platform is on the balls. Torque path: screws clamp
  neck to platform; the platform's integral 16T pinion takes the drive from the pan
  motor's 32T gear (fast-pan 2:1 gear-up 2026-07-12; the old on-axis D-bore is gone).
- **B. Tilt axle cartridge.** Slide the `worm_wheel` (+ its two spacer tubes) onto the Ø5
  axle, hub ledge riding the axle's filed flat (D-key: positive torque, nothing to grub).
  Verify the fit on a printed coupon first: a loose flat is backlash.
- **C. Tilt-motor cartridge.** Drop the tilt 28BYJ onto `tilt_carrier`: the can passes the
  plate's Ø29.1 bore and each ear hole lands on a Ø3.8 pin atop the plate's D-posts
  (2026-07-16: the real motor is 9 mm shorter than the old placeholder modeled, leaving
  only 0.2 mm in front of the ears -- the old 2x M4 ear bolts are geometrically impossible
  and are GONE from the BOM). Press the worm onto the D-shaft. Hold the motor against the
  posts while inserting (step 11); driving the carrier's 4x M3x16 captures the ear bar
  between the post fronts and the neck's pocket-front wall (0.25 mm float, pins lock
  rotation). It comes OUT the same way for a motor swap, no head teardown.

### Chassis + drive (fixed frame)

1. **Print + prep the chassis.** Confirm the deck pan-seat, the pedestal, and both TT
   motor pockets are clean.
2. **Fit the four structural side panels.** The old separate `pod_rail_L/R` parts and their
   dowel joint are retired. Each panel carries its wheel beam and end tower as one print.
   Seat the front/rear splice tongue and locating pads, install its two M3 screws into
   captive nuts, then bolt the panel feet to the lower tub. The tongue and separated feet
   hold alignment before tightening.
3. **TT motors.** Set each TT gearmotor: shaft +X into the sprocket hub's double-D socket,
   front tab into the rear-wall pocket, nub into the wall pocket, 2× M3 through the
   gearbox + wall with the nut floating in the pod gap.
4. **Track running gear.** Press an F688ZZ into EACH face of all four end idlers (Ø15.95
   seat + Ø18.5 flange recess both sides). Each end wheel: M8 bolt from outboard
   through the bearings, add the OUTBOARD jam nut against the tower, then the flatted
   washer + NYLOC nut inboard, started ON THE
   BENCH with the deck upside down. Orient each nut HEX FLATS FORE-AFT: as the deck
   drops onto the tub the nut descends into its prow-cheek NUT CHANNEL (y-walls 13.8
   apart), which grips the flats -- all torquing happens from the outboard head, no
   inboard tool ever needed. Rear pair: snug. Front pair: leave loose, set tension
   AFTER threading the tracks, then tighten from the head -- the channel holds the
   nut, the nut clamps the slot. Fit the sprockets on the
   TT shafts (they mesh the ground run under the hull; the robot's weight seats them). Drop an M4 nut up each wheel-beam slot (do this BEFORE mounting the
   rails if access is tight), then bolt each road wheel with its M4x40 from outboard --
   snug, then back off 1/8 turn so the wheel spins free.
5. **Join the strips + close with the master (print-in-place chain, 2026-07-12).**
   Each pod is 4 PRINT-IN-PLACE strips (16+16+16+15 links, hinges already free off
   the printer -- flex every joint once to crack any sag bonds) + 1 separate master.
   On the bench: pin the strips end-to-end with 3 Ø1.75 filament pins (each boundary
   = one strip's Ø2.2 open A-bores interleaving the previous strip's Ø2.2 far bores),
   then pin the MASTER's far end to strip 1's first link (4th filament pin). Wrap the
   open chain around the pod with the front idler retracted. Seat the last filament
   pin (5th) in strip 4's final-link far bores, swing the master's open jaws down
   onto it, slide the two `track_keeper` bars into the jaw slot from the side faces,
   and lock each with its M2 into the side-face pilot. Tension the idler -- run the
   chain TENSIONED: the PIP joints carry 0.35 radial slop (~8 mm of loop slack vs
   the old filament chain) that otherwise lands as top-run sag; if the front
   tension slot runs out of travel on the physical chain, that is the expected
   first fix (more slot travel), not a link redesign. Track removal forever after:
   2 M2s out, slide the keepers, lift the master off its pin.

### Pan joint

6. **Pan motor + drivers.** Fit the printed 32T `pan_gears` onto the motor's D-flats, then
   drop the pan 28BYJ into the pedestal can pocket (fast-pan 2026-07-12: the shaft sits
   OFF-axis at (-19.2, 0), gear up; ears run along X), clamp the 2 ears with M3 into the
   pedestal pilots from ABOVE (deck open). Mount ULN #1 and the 2nd ULN/MX1588 board on
   their standoffs; wiring box leads exit the pedestal +Y relief.
7. **Power tray, ballast, then belly plate.** Screw the PD trigger to the rear-wall M2
   pilots (jack aligned with the USB slot), the 5A buck to the belly plate's 40×20 post
   grid, zip the mini buck beside it, and wire per firmware/WIRING.md (leave 60 mm slack
   on every tray run; zip the incoming wall cable to the floor anchors as strain relief).
   Load the low ballast into the rear bay + the belly-plate pockets from BELOW, then bolt
   on `belly_plate` (6× M3 csk, flush at z=7). Ballast must go in before the plate closes
   the floor.
8. **Pan race.** Grease the `pan_race` lower groove, seat it on the deck floor, lay the
   `pan_cage` ring over it, and drop the **18× 6 mm BBs** through the cage pockets into
   the groove with tweezers. The cage keeps them spaced; any later turret lift leaves all
   18 sitting evenly in the groove instead of bunching and rolling out.
9. **Lower sub-assembly A** (neck+platform) onto the BBs so the platform's upper groove
   captures them and its integral 16T pinion drops into mesh with the motor's 32T gear
   (fast-pan 2026-07-12: fit the 32T on the motor D-flats BEFORE this step). Screw
   the 3 `pan_clips` into the deck pockets (driver clear 6.17 mm from above); their tabs
   reach over the platform rim rebate to hold the top-heavy head down. Check the platform
   spins free.

### Tilt joint + head (all on the pan group)

10. **Bearings + axle cartridge.** Press a 695-2RS into each neck cheek from the clevis gap
    (seats open flush to the inner face; a light lead-in helps start the press). Insert
    sub-assembly B through one cheek bearing → the gap (wheel meshes the worm) → the far
    bearing.
11. **Insert the tilt cartridge.** Slide sub-assembly C (carrier + motor + worm) in from
    the open rear bay: the worm passes the bracket plate's Ø12.2 bore, its tail lands in
    the open-top cradle groove, the can registers in the Ø29 pocket, the motor's ear bar
    rides the neck's ear-bar channel to 0.2 behind the pocket-front wall, and the
    carrier's 4 bosses land on the plate/column rear faces. Drive 4× M3×16 from the rear
    into the captive nuts in the neck blocks -- this also captures the ear bar between
    the carrier's D-posts and the neck wall (hold the motor against its pins until the
    first screws bite). (Extraction reverses this and is UNCONDITIONAL since the 2026-07-12
    3-start worm: the mesh back-drives, so with a dead motor just hand-nod the head while
    pulling and the worm screws itself out. The old rule -- drive the head fully UP first
    because the single-start pull needed ~46° of nod against ~34° of stop travel -- is
    retired, 2026-07-13.) Route
    the tilt ULN wiring on the column back standoffs, board centered at z 93, below the
    carrier (motor + driver both ride the pan group, so no leads cross a joint).
12. **Hang the head on the axle.** Lower `head_back` so its side hubs take the axle ends, then
    set the two head-clamp grubs at x=±30 with a 1.5 mm hex key driven UP through the bottom
    motor bay (4.0 mm clear). The axle now turns with the head; the worm holds tilt with the
    driver off ONLY marginally (fast-tilt 2026-07-12: the 3-start worm back-drives;
    hold is 28BYJ detent+gear friction through 4:1 -- firmware energize-hold or park
    at the balance point; see CLAUDE.md fast pan/tilt pass).
13. **Screen + Pi module (tray).** On the BENCH: bolt `screen_tray` to the combined
    touchscreen+Pi with 4× M3×10 pan heads straight into the display's factory 126.2×65.65
    bosses (the pillars are z-offset from the bores, so the driver line is open). Power-test
    the module on the desk if you like -- it is now a self-contained unit. Then drop the
    loaded tray into `head_back` from the open front (the pillars pass z-clear of the clamp
    tubes) and drive 4× M3×10 from OUTSIDE the back wall into the pillar-end pilots: short,
    visible screws in the fixed strip between the door outline and the hatch-frame opening.
    The bezel pocket locates the glass when the head closes (step 15).
14. **Camera + forehead LED.** Mount the CM3 front-face-in on the 4× M2 pier bosses, trap it
    with `cam_cover` (2× M2 + ribbon pinch), drop the CSI ribbon into the pocket. Seat the
    WS2812 forehead segment in its recess and route the 3 wires through the wire pass to the
    Pi. Route the Pi power pair per the cable step below.
15. **Close the head.** Bezel to back: 8× M3×35 through the perimeter posts into the captive
    nuts in the back bosses (screws from the front). Fit the rear service `head_door`
    (the stepped rear pod): engage the two top hook tabs first, swing the door in until
    both leg snap tongues CLICK behind the wall band beside the void (tool-free; replaced
    the 2× M3 csk 2026-07-10). To open: firm pull on the pod's bottom edge (35 mm proud,
    that IS the grip); the barbs' back ramps cam the tongues inboard and release. Open at
    roughly neutral tilt: at the ±33.8° stalls the tilt drivetrain reaches into the pod's
    internal cavity.

15b. **Antenna drives.** Slip a friction O-ring into each top-wall guide bore, drop each
    mast in from above (rack facing the pinion slot), then hang `ant_bracket` on the back
    wall (spine + locating shoulders and 4x M3). Insert each printed `ant_output_*`
    half-shaft/pinion through its Ø4.2 bushings, fit `ant_idler_axle_*` and the compound
    `ant_idler_gear_*`, press `ant_motor_gear_*` onto the motor double-D, and bolt each 28BYJ nose-through
    its face plate (2x M3 into the vertical-ear pilots, shaft inboard). Each mast has its
    OWN motor + ULN2003 (independent control); wire both to the Pi in the head. Homing:
    drive down until stall (tip cap on the boss). BUY: 2x O-ring sized for the Ø7 guide.
    All 30T/12T/27T m0.8 gears, axles, shafts, and rack teeth are exported printable parts.

### Cables (per docs/CABLE-CHECK.md + firmware/WIRING.md)

16. Wall PD brick → rear PD trigger (12 V) → belly tray bucks. The Pi-rail pair (18 AWG,
    from the 5A buck) coils a **2-turn service loop (~600 mm) at r≈48, z≈38–45** in the
    cavity → 16×8 deck pass → platform slot → neck channel → the column top-left exit
    window → through the bottom-rear head slot to the Pi's **GPIO 5V/GND pins** with
    **~60 mm of free head lead** for the tilt drape. Set `usb_max_current_enable=1` +
    EEPROM `PSU_MAX_CURRENT=5000` (GPIO power skips PD negotiation). Software-limit pan
    to ±90° (hard stops at ±93.3) so the loop never over-winds.

### Cosmetics LAST (glue + locating pins)

17. Press-and-glue the pin-located cosmetic parts: `trim_rail_L/R`, `trim_hatch_frame`
    (**after** the screen, its band overlaps the 4 driver-channel mouths, up to 2.3 mm),
    `camera_pod`, and the chassis `trim_fascia` / `trim_rear` / `sensor_rear`
    grille cap. Fit fascia electronics if used: HC-SR04P barrels through the Ø16 passes, amber
    corner lamps, front LED strip, rear buzzer/speaker.
18. **Final check + homing.** Power on; firmware stall-homes pan against its ±93.3° deck
    stops and tilt against its ±33.8° fin stops, backs off, and zeroes. Sweep pan ±90 and
    tilt ±30 and confirm the screen/Pi stack, worm, cheeks, axle, cables and bottom head
    edge stay clear (matches the `make check-sweep` gate).

### Order constraints (do NOT reorder)

- Body↔pod join + TT screws (step 3) **before** ULN #1 (step 6): the board blocks cavity access.
- Neck↔platform bolt-up (sub-assembly A) **before** seating on the balls, counterbores face down.
- BBs + cage (step 8) **before** the platform (step 9); power tray + ballast (step 7)
  **before** the belly plate closes the floor.

### Nasty-but-possible steps (measured)

- **Head-clamp grubs (step 12):** 1.5 mm hex key driven blind UP through the motor bay,
  4.0 mm clearance. Kept deliberately: the grubs give continuous tilt-zero trim.

(2026-07-08 passes retired the old tilt-motor-ear reach, the worm-wheel bench grub, the
last-track-pin loop flex, and the 4× 88.5 mm blind screen-standoff screws -- the worst
step in the build is now four short bench screws plus four visible wall screws.)

### Track coupon protocol (plate 20, ~48 min -- print BEFORE any strip plate)

Plate 20 is a 5-link print-in-place coupon (open-A first link, 3 integral-pin mids,
open-far last, keels on) + 1 loose master link + both keeper bars. Measure on it:

1. Every PIP hinge frees after break-in flexing -- no fused knuckles.
2. Hinge radial slop: pull the 5-link strip taut and measure total stretch vs 40.0
   nominal; that gives real per-joint slack. Scale x59 and check it still fits the
   6.5 mm front slot travel via delta_L / 1.84.
3. Ø2.0 integral pins unbroken after 20 full +-35 deg articulations.
4. Keel faces clean (no sag scars), grousers flat.
5. Ø2.2 boundary bores accept Ø1.75 filament.
6. Master jaw drops onto the end pin; keepers slide and seat; M2 pilots hold.

Any fail: adjust `track_bore_pip_d` / `track_pin_print_d` and reprint the COUPON,
not a strip.

### Recommendations (bigger than this pass)

- Print a D-bore coupon and dial the axle-flat clearance (modeled at +0.05; +0.15 measured
  as ±4.4° of head backlash) before committing the filed axle.
- Print supports: paint a support enforcer under the neck's two tilt-stop posts (x 20..32,
  z 150..156 -- their outboard halves start mid-air with the neck on its back) and extend
  the clamp-tube supports over the head_back stop fins (55° overhangs feeding a ~0.9 mm
  homing margin; treat the first stall-home angle as calibration). Print the track keepers
  lying on their 13.3×1.9 bar face so the slot-critical 1.9 width is XY-accurate.
- Track gauge is still ~184 vs a 205-wide head (~10 mm overhang/side): widen the gauge or
  accept it (tracked elsewhere).
- If field-servicing the screen without un-gluing the hatch frame matters, notch the frame
  band clear of the 4 channel mouths.

## Wiring

**See firmware/WIRING.md** (2026-07-08) for the full architecture: 12 V PD-trigger input,
dual-buck belly tray (5.1 V Pi rail + 5 V motor rail), what crosses each joint, Pi 5
config flags, connector/labeling rules, and the buy-list delta. Short version: only the
Pi-rail pair crosses tilt; the pan loop carries that pair plus the thin motor-rail/signal
bundle; DSI and CSI ribbons never leave the head.

## Order now (by lead-time importance)

1. **8x F688ZZ flanged bearings** (8x16x5, flange Ø18): most specific part, slowest to source;
   the end-idler seats are modeled around them (2 per wheel x 4 since the mid-drive).
1b. **10x M4x40** (road-wheel bolt-axles; partially threaded preferred; M4 nuts are owned)
    + **4x M8x70 + 4 jam nuts + 4 NYLOC nuts + 4 washers** (end bolt-axles; Bag 13
    has no M8).
2. **4x HC-SR04** (forward + rear obstacle + 2 cliff; zero owned; plain 5V is fine on the
   Arduino I/O plane). TT gearmotors are COVERED (own 3); buy 1 more only for the optional
   twin-drive 4th station.
3. **Power electronics** (firmware/WIRING.md): a 30W+ USB-C PD brick (the official 27W
   works), 12V PD trigger, XL4015-class 5A buck, MP1584 mini buck, JST-XH kit + crimper,
   1 m 18 AWG silicone pair, inline blade-fuse holder (the 5A blade fuse itself is owned).
4. **1 m narrow addressable LED strip** (4–5 mm wide, SK6805-2427 / WS2812-2020, ≥160 LED/m),
   one purchase covers the forehead 8-LED segment and the front 7-dot strip. (Alternative:
   widen `led_slot` to ~54x11 and buy two common 8x5050 sticks.)
5. **Ø5 SOLID rod ~100 mm** (tilt axle; NOT tube) + **Ø4x12 dowels** for the remaining
   registered shell/seam joints. The retired body-to-pod rail joint no longer consumes four.
6. **6 mm airsoft BBs** (bag of 100+; need 18): cheap, everywhere.
7. Optional: **MAX98357A I2S amp** x1 (pairs with the owned 8Ω speaker), **amber LEDs** x2–5.

Every board/hardware item above lands in the "Verify on arrival" table -- caliper before
printing its seat.

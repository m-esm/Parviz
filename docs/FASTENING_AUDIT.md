# Fastening & Assembly Audit — post-print failure report (2026-07-15)

> **STATUS: COMPLETE, all gates green** (build · check · check-sweep · 62/62
> invariants · wallcheck · fits 64 contacts all expected · export · 20/20 plates
> slice clean). Fixed in 4 parallel worktrees (chassis / head / neck+pan / tracks),
> then items 6-14 finished in 2 more (2026-07-16). No thread-form pilot remains on
> any structural joint.
>
> **THE AUDIT UNDERSTATED THE DAMAGE.** It graded these joints "weak". On probing
> the built meshes, **NINE WERE DEAD AS MODELLED** -- the screw could never engage
> anything: two `chassis_base` stations had **no hull material at any z** (the
> glacis had eaten the floor, so `sub(pilot)` was a silent no-op), the cliff M2s
> engaged **0.30 mm** then hit undrilled solid, the ULN pilots stopped 3.0 below
> their post tops, and the **IMU posts had height ZERO -- they did not exist**.
> Root cause worth naming: **a derived feature next to a hardcoded partner**. When
> `chassis_clear` went 7 -> 10, every z-derived post moved and the hardcoded pilot
> depths stayed. The power-tray posts beside the ULN posts were fine -- because
> they derived their pilot.
> `checks.py` now gates exactly that: every fastener station must land on real
> material, probed as a RING at r=3 (an on-axis probe reads "void" for a healthy
> joint *and* for a hole drilled through thin air -- only the surrounding material
> distinguishes them). Verified to fail at the old dead coordinates, 0/8.
>
> **THE ROOT CAUSE WAS DEEPER THAN THIS AUDIT ORIGINALLY SAID.** The audit named the
> Ø2.5 thread-form pilots and told everyone to copy `chassis_pedestal`'s "reference
> good" hex traps. **Those were broken too.** A hex nut with its flats on the trap
> walls spans ACROSS CORNERS -- ac = AF*2/sqrt(3) = 6.35 for M3, not the 5.5
> across-flats -- along the insertion run, but the trap box ran FROM the bore axis
> AWAY from it. The nut could only ever reach axis+3.175, a miss of 2x the thread
> radius: **the screw could never catch it.** So the chassis's ONE real nut pocket
> never worked either. Probed on the built mesh, all 4 feet: nut-reaches-bore False
> before, True after. `geo.nut_slot()` now owns the correction (pass it the screw
> axis; it seats the nut on the bore, and the seat is what aligns it hands-free),
> and `checks.nut_reaches_bore()` gates the whole class -- verified to have teeth by
> rebuilding the old broken foot and watching it fail.
>
> Two more defects the fix pass found that this audit missed entirely:
> - **The gates were lying.** `make invariants`/`make wallcheck` read `stl/*.stl`,
>   which only regenerate under `EXPORT=1`, so both silently measured the PREVIOUS
>   geometry; `make all` ran them before its own export. Same class as the Stage 4
>   vacuous probe in docs/FIXES.md. Fixed: both now depend on a fresh `stls` target.
> - **The sprocket's M2 retaining screw was dead as modeled** -- 8.4 mm of solid hub
>   sat between the Ø6 bore and the socket, so it could never reach the shaft tip.
>
> Where geometry beat the plan (each probed, not guessed): the master-link captive
> M2 nut does not fit (5.50 usable vs 5.82 needed) -> heat-set inserts; the
> tilt_carrier did NOT need inserts (the audit assumed no nut face was reachable --
> probing disproved it); the tail seam moved y -88 -> -95 (no joint could exist at
> -88) and takes a tongue instead of a dowel; the head panel gets tab rebates, not a
> perimeter lip (at y -66 the wall is all corner curve). Details in each section.

User print feedback: (1) almost none of the screws/pockets work, (2) joints lack real
bolt+nut capture, (3) nothing holds parts aligned while driving screws, (4) parts
(tail + front counterpart) break at thin-ligament connections.

Four-subsystem code audit (chassis, head, neck/pan/tilt, tracks). Verdict below,
then the full per-joint tables.

## Systemic verdict

- **The failing class is the Ø2.5/Ø1.7 "thread-form pilot" into PLA** — 40+ joints.
  grep-confirmed: the whole chassis has exactly ONE real nut pocket (the pedestal
  foot traps); everything else self-taps into plastic.
- **The joints the user is NOT complaining about are exactly the engineered ones**:
  M4 road-wheel slide-up nut slots, M8 tower ledge+roof cages, pedestal side-slide
  hex traps + printed registration pins. That pedestal pattern
  (chassis.py:1330-1348) is the template to propagate.
- **Alignment is the second gap**: half-laps/dowels exist on some seams, but the
  load-bearing roots (neck→platform, head panel→frame, screen tray→wall,
  bezel↔back) have flat-on-flat interfaces with zero registration.
- **Fix patterns, in preference order**:
  1. Through-bolt M3 + side/slide-in captive hex nut trap (pedestal pattern) —
     wherever a nut face is reachable in assembly order (most joints qualify).
  2. M3 brass heat-set insert — where no nut face exists (blind bodies, exterior
     walls); bosses must grow to ≥Ø9 (Ø4.6 hole, ≥2.2 wall).
  3. Every screwed seam gets a locator: Ø4 dowel pair, tongue/groove, rebate lip,
     or spigot — so parts self-hold while screwing.

## P0 — unbuildable or missing as coded (fix before any reprint)

| # | Finding | Where | Fix |
|---|---|---|---|
| P0-1 | **Bezel↔back 8 "captive nuts" are SEALED inside the bosses — no insertion slot exists.** The head's primary structural joint cannot be assembled. | head.py:344-355 | Cut a slide-in nut slot from each back-boss flank (opens to interior); add 2 Ø4 dowels on the split plane |
| P0-2 | **y=−88 tail seam has NO joint at all** (bare butt plane, no pads/screws/dowels). This is the reported tail break. | chassis.py:590-592, 987-992 | Give it the y=26 joint (pads + dowel + captive nut) at x≈±48 + a tongue/shelf across the seam |
| P0-3 | **Tilt-axle grub pilots are Ø2.5 = M2.5 CLEARANCE size — zero thread engagement.** | head.py:181-191 | Replace with slit pinch-clamp + cross M3 bolt + hex trap (grubs in PLA strip on re-torque anyway) |
| P0-4 | **ant_bracket has NO mounting to the head** (spine just rests on the wall) and its 1.2 mm motor face plates already severed once. | head.py:811-874 | Add bosses/pins into frame walls; plates ≥2.5; motor ears → M3 through-bolt + nut on the open far face |
| P0-5 | **Front/rear obstacle HC-SR04 boards are unretained** (float against wall, gravity + wires). | chassis.py:42-61, 352-358 | 2 M2 posts or a slide-in board shelf clip behind each wall |
| P0-6 | **TT motor upper M3 = loose nut in a ~4 mm gap** — impossible with track installed, the exact hands-free failure reported. | chassis.py:394-396, 944-957 | Duplicate the lower screw's slide-up nut pocket for the upper (extend down the wall face) |
| P0-7 | **Sprocket axial retention assumes a Ø2 axial hole in the TT shaft — verify owned motors have it** (many variants don't). | tracks.py:320,345-346 | Verify; fallback hub grub-screw boss |

## P1 — thread-form pilots on structural joints → captive nuts / inserts

| Joint | Where | Nut face reachable? | Fix |
|---|---|---|---|
| neck_clevis → pan_platform (3× M3, root of the whole head stack, NO alignment) | neck.py:202-213, pan.py:98-111 | yes — bench, column-base top | Side-slide hex traps in column base + 2 registration pins |
| tilt_carrier → neck plate (4× M3x16, 4.0 mm thread in raised pads) | neck.py:146-162, 375-378 | no (buried vs motor can) | Heat-set inserts in pads/column |
| pan_clips ×3 → deck (carry ALL head uplift in PLA threads) | pan.py:190-193, chassis.py:286-295 | yes — deck underside | Through-bolt + hex trap in deck underside |
| pedestal pan-motor ears (Ø2.5×16 pilots) | chassis.py:1299-1301 | no | Heat-set from top face |
| Lower front/rear seam y=+26 (2× M3x12 + counterbore leaves 1.0 wall) | chassis.py:624-658 | yes — open-top tub | Slide-up hex trap in −y pad; widen pad ≥18, root ≥3 |
| Deck hold-downs 4+4 (6 of them are the panels' ONLY top retention, 5.1 mm thread on scarfed bosses) | chassis.py:576-618, 902-915 | yes — under boss, pre-deck | Slide-in hex nut under each boss |
| Deck strip seams y=66/−52 (2× M3 per seam into 6 mm shelf) | chassis.py:994-1022 | yes — shelf underside | Hex recess opening down from shelf bottom; keep half-lap |
| Panel splice half-lap (1× M3x10, 5.5 mm thread; makes the track module rigid) | chassis.py:916-923 | yes — L-block bottom | Slide-in nut in the lower block; thicken 1.8 mm tongue cheeks |
| Panel L-feet → floor (Ø3.3 bore in 4.8 foot = 0.75 mm walls) | chassis.py:801-803, 959-979 | yes — belly underside | Through-bolt + hex recess at floor underside; foot ≥8 wide |
| belly_plate → hull rim (6× M3x10 csk) | chassis.py:495-515 | yes — boss tops face cavity | Hex trap at boss top |
| chassis_base → hull floor (4× M3, no dowels, and it's the only tail-seam tie today) | chassis.py:528-531, 1180-1185 | yes — 0.2 skin to belly face | Through-bolt + external hex recess + 2 dowels |
| Head panel→frame 6× M3 (flat-on-flat, no registration; rim tabs are break candidates) | head.py:531-546 | yes — tab inboard faces | Perimeter rebate lip on frame rim + hex pockets in tabs |
| Head frame↔frame top flange 2× M3 (no alignment between frames) | head.py:548-562 | yes — flange underside | Dowel/tongue at flange seam + nut slot from below |
| Bezel_L↔R seam pads (pilot side) | head.py:591-616 | yes — interior | Nut pocket opening into interior; keep dowels |
| screen_tray → back wall 4× M3 (heaviest module held by hand while driving blind from outside) | head.py:373-384, 663-669 | yes — pillar sides pre-insert | Locating spigots/shelf in head_back for the pillar ends + square-nut slots in pillars |
| Master-link keeper bars M2 into Ø1.7 pilot (the ONLY repeatedly-serviced M2-in-PLA) | tracks.py:216-247 | tight | Bayonet/snap keeper, or M2 + brass insert; else spec 2-3 reuse cycles max |
| Cliff HC-SR04 M2 pilots (strip on 2nd service) | chassis.py:1053-1067 | yes — pocket side | M2 nut + washer behind, or heat-set |
| mmWave tab M2 pilots | chassis.py:1097-1105 | yes — behind tab | M2 through + nut |
| BME688 Ø5×2 wall bosses (snap under driver torque) | chassis.py:532-544 | no (exterior wall) | Heat-set M2 or clip-mount |
| PD-trigger M2 edge-on into wall layers (weakest orientation) | chassis.py:301-310 | no | Heat-set or printed slide-in carrier |
| ULN2003 / power-tray / Arduino / IMU posts (Ø6 posts split on tapping) | chassis.py:1143-1259, neck.py:222-231 | mixed | Posts ≥Ø7 + heat-set, or M2.5 screws (low load) |
| tilt ULN2003 horizontal Ø6 bosses on column back | neck.py:222-231 | boss rear open | Ø7+ bosses + inserts or M2.5 |

## P2 — fragile ligaments (break-after-print register)

Chassis:
1. **Tail seam + corner crescents**: past |y|≈109 the r12 cavity-corner crescents are
   the hull's ONLY floor↔end-wall ligaments (chassis.py:747-752); both glacis end
   walls hang on them → add inboard gusset ribs (x ≤ 62). The 33° glacis/floor
   knife wedge on the tail chips in handling.
2. Panel L-feet 0.75 mm walls (chassis.py:959-964).
3. y=26 seam pad: Ø6.8 cb leaves ~1.0 wall; pad roots 1 mm into floor (654-657, 600).
4. Splice tongue 1.8 mm cheeks around the cb (818-820, 918-920).
5. mmWave 3.5 mm ceiling-hung tab (1097-1105); BME Ø5×2 bosses; led_front 1.2 base.
6. TT lower-nut pocket outboard web wall **0.6 mm** (955-956) → +0.4 minimum.
7. **M8 cage ROOF strip ~0.98 mm** spanning the ~24 mm tension window
   (chassis.py:880-886) — thinnest structural member in the running gear; thicken.

Head:
8. Frame rim tabs: Ø2.5 pilot through 9-wide tabs clipped by the corner curve →
   ~3.2 mm ligaments, sole panel retention (head.py:531-539).
9. Door hook plates 1.3 mm, layer-peel loading (463-472) → ≥2 + root fillet.
10. Door snap-tongue slit ends unradiused (crack starters), barb band 3.5 tall
    (478-512).
11. Bezel forehead pad hangs on a 3.2 ext bridge; chin dowel bore 2.6 from pad
    edge (591-616).
12. Bezel↔back boss walls 1.9 mm around the hex void (344-355).

Neck/pan/tilt:
13. **tilt_carrier rear wing 2.15 mm × 20 strip** + connectivity only through an
    x 8.8..17 band of a 4 mm plate (neck.py:349-358) — highest break risk here.
14. Carrier Ø7 bosses (1.75 wall) on 8 mm cantilever (364-368).
15. pan_clip uplift tabs 2.6×4.1×14 — three tabs are ALL that stops the top-heavy
    head lifting the platform; layer-shear direction (pan.py:188).
16. Cheek tilt-stop leg 6×5×22 takes repeated stall-homing impact (neck.py:66-68).
17. Bearing hoop 3.07 mm radial wall + 0.15 press = split risk (neck.py:53,131);
    same for F688 0.05 press seats (tracks.py:440) — below FDM repeatability:
    coupon-calibrate or bore +0.05..0.10 with crush ribs.
18. Worm-support riser prongs ~3.1 wide (neck.py:107,176-180);
    trim_neckfoot 3.0 ring fragile until glued.

Tracks:
19. Keeper bar 1.9×2.2 section, 0.85 tab rim, 0.75 boss-pilot edge (tracks.py:211-247).
20. Master C-jaw crown 2.4 mm over the slotted bore, carrying full belt tension
    (219-222) — print master in PETG/PCTG.
21. Road-wheel hub cosmetic bolt circle: 0.6 mm ligament at the loaded hub
    (469-475) — delete or shrink the cosmetic holes.
22. Strip-boundary filament pins have zero axial retention (open Ø2.2 both ends,
    tracks.py:175-179) — melt-mushroom ends or step one bore to Ø1.6 press.
23. Front M8 tension is friction-only on PLA slot faces (creeps) — add serrations
    or a jack screw (chassis.py:858-866).

## P3 — misc / retention & registration

- pan_race: nothing stops ring rotation but friction → 2 anti-rotation nubs if it spins.
- tilt_worm on D-shaft: no axial retention vs ~10 N worm thrust → front washer
  trapped by the carrier plate bore lip (28BYJ shaft has no circlip groove).
- pan_gears 32T: no axial retainer (gravity) — fine, monitor.
- M4 nut slide-up slots: nuts drop out when flipping the panel → crush-rib nib in
  each slot mouth. Bench note: nuts in BEFORE panel mounts (slots blind after).
- Wheels spin on the M4 thread band unless partially-threaded M4×40 → make it a
  hard BOM requirement.
- trim_neckfoot Ø3 pin sockets 3.5 blind → deepen; fascia/rear trim pins 2.5
  engagement → deepen to 5 or add snap barbs.
- 695-2RS hoop press: coupon first; fallback Ø13.05 bore + printed cap/circlip.
- worm_wheel D-key +0.05: coupon first; keep a fallback oversize variant.
- led_strip recess: no retention modeled — note glue in ASSEMBLY.md or add a lip.
- Stand-ins: M8 plastic press nuts cannot hold tension preload (expect track sag
  in dry assembly, by design); seam dowel Ø4.0-in-Ø4.0 is jam-or-rattle → hole +0.1.
- Stale comments: tracks.py:461, 516-518 (deleted pod rails / nut ducts),
  chassis.py:706 (slot depth overstated).

## Assembly-holding gaps (nothing registers the parts while screwing)

1. neck_clevis on pan_platform — NONE (load-bearing root) → pins + traps.
2. head panel on frame — NONE (flat slab, 6 screws) → rebate lip.
3. frames L/R to each other — only the panel tongue, nothing frame-frame → dowel.
4. bezel on back — NONE (8× M3x35 blind) → 2 Ø4 dowels on the split plane.
5. loaded screen_tray in head_back — NONE (drops in, screwed blind from outside)
   → pillar spigot seats.
6. chassis_base in hull — loose relief pockets only → 2 dowels.
7. Track filament-pin joints — hand-held while threading → acceptable, but
   mushroom the ends.

Good examples already in-tree (reuse, don't reinvent): pedestal pins+traps (C2),
M4 slide-up slots, M8 cages, TT nub+tab 3-point location, deck half-laps,
y=26 dowels, door hook+snap, trim rail nut pockets (head.py:254-264).

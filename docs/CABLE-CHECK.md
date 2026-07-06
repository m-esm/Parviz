# CABLE-CHECK — power-route re-verification after the 25 mm head drop

Task #18, 2026-07-07. Geometry probed with trimesh signed-distance / containment
against scenes built as `OUT=_cable_t{θ}.glb PAN=0 TILT={-30,-15,0,15,30}` (probe
scripts in the session scratchpad; `web/assembly.glb` untouched, probe GLBs deleted
after the run). Conduit spec: Ø5 virtual conduit (≥2.5 mm clearance to every solid);
real bundle is the Pi power pair, ~Ø3.6.

Route under test: base rear USB-C wall port → base cavity (pan service loop) →
16×8 deck pass at `cable_exit` (12,−24) → platform slot → neck channel
(`neck_chan_y`=−26) → column top → head bottom-rear slot (tilt drape) → Pi USB-C
(bottom edge, z≈126).

## Verdict summary

| # | Segment | Verdict | Worst number |
|---|---------|---------|--------------|
| 1 | USB wall port → cavity | **CLEAR** | 4.00 mm |
| 2 | Service loop (cavity annulus) | **CLEAR** (at z 36–45.5) | r40–56 ring free all-round |
| 3 | Deck pass, through the deck itself (z 46–51) | **CLEAR** | 16.0 × 8.5 window, footprint max r 32.2 < race ID 34 |
| 3a | Deck pass, drop below the deck | **OBSTRUCTED (Ø5) / marginal (Ø3.6)** | pan pedestal refills the pass to a 4.0 mm window |
| 4 | Seat void jog → platform slot → channel base | **CLEAR** | 3.93 mm |
| 5 | Neck channel, z 66 → 125 | **CLEAR** | 4.00 mm (16.5 × 8.5 window at z 95) |
| 6 | Channel exit at the column top | **OBSTRUCTED** | 1.0 mm escape gap (riser + root block + arm + worm box it in) |
| 7 | Tilt drape, column top → head slot → Pi | **CLEAR** (once 6 is fixed) | 0.32 mm chord graze at −30° (wire bows; all worm parts ≥ 10 mm) |
| 8 | Head-side, slot → Pi USB-C vs worm/wheel/axle | **CLEAR** | worm 14.2, wheel 19.4, axle 23.5, stack 12.3 mm |

Two geometry fixes needed (both in `src/build.py`, exact cuts below). Defect 6 is
pre-existing (identical relative geometry before the drop — the whole
column-top/riser/worm cluster moved together), not caused by the drop. Defect 3a
is a build-order bug.

## 1. USB port → cavity — CLEAR

The 14×12×8 port cut at (0, −78, 19) opens the rear wall (containment: wall material
absent at (0,−77.4,19)). Min clearance of a Ø5 conduit from the port into the cavity:
4.00 mm.

## 2. Service loop — CLEAR, but it lives in the TOP band of the cavity

Full-ring annulus scan around the pan axis (5° steps, 2 mm radial steps):

- z 38 and z 43: annulus **r 40–52 and r 44–56 fully free over 360°**.
- z ≤ 30: blocked at azimuth 190–215° (TT drive motors) and 330–345° (ULN standoff
  corner). Worst free radial window at z 26 is still 15 mm, but not at a loopable
  radius all-round.
- r < 40 blocked at all heights by the pan pedestal (48×48 at (−7.9, 0), top z 44.25,
  only 1.75 mm under the deck).

So the 2-turn Ø3.6 loop coils at **r ≈ 44–52, z ≈ 37–45.5** (radial window 12–16 mm,
vertical 8 mm — two turns side-by-side need 7.2 mm: fits). 2 turns at r 48 ≈ 600 mm
of wire; pan ±90° winds/unwinds ~±150 mm (half a turn) — the loop absorbs it with a
full turn of margin. Free annular volume r 20–64, z 14–45: ~330 cm³ (89 % of the
annulus is free). Pan motor / pedestal / ULN don't crowd the loop band; they only
push it up against the deck underside.

## 3. Deck pass — the deck cut is fine, the PEDESTAL blocks the drop (defect A)

Through the deck floor (z 46–51) the 16×8 obround at (12,−24) is fully open (probed
16.0 × 8.5 mm) and its footprint max radius is 32.2 < race-ring ID 34 (nearest
approach to `pan_race`: 7.13 mm). Aligned with the platform slot at pan=0.

**Below z 44.25 the pan-motor pedestal refills most of the pass footprint.** In
`build_base()` the cable pass `cbl` is subtracted (~line 1294–1298) BEFORE the
pedestal is unioned (~line 1300–1306), so the pedestal (x −31.9..16.1, y ±24,
z 12..44.25) fills the pass back in over y > −24. Probed free window under the deck
at x 8–16: **y −28..−24 ≈ 4.0–4.3 mm** (plus full 8 mm only for the x 16.1..19.9
sliver). A vertical Ø5 conduit at (12,−24) has 0.29 mm to the pedestal corner: FAIL.
The Ø3.6 pair squeezes through the 4 mm window: marginal.

**Fix:** move the `cbl` subtraction to AFTER the pedestal union (or subtract `cbl` a
second time there). `cbl` already spans z 29–51, so this bores a clean 16×8 shaft
through the pedestal corner; below z 44 the shaft's −y side is open to the cavity
(pedestal stops at y −24), so the wire swings straight back into the loop band.
No other part is affected (overlap zone is pedestal corner x 4..16, y −24..−19 only).

## 4–5. Seat-void jog + platform slot + neck channel — CLEAR

Jog polyline (12,−24,50) → seat void → platform slot → (0,−26,68): min clearance
3.93 mm (platform), 7.1 mm (race ring), 10.8 mm (balls). Platform slot and neck
channel are mutually aligned at pan=0 (both aim along (0,−26)→(12,−24)); slot and
channel windows probed at 16 × 8.5 mm. Channel clear at 4.0 mm from z 66 to the
column top at z 125. At pan≠0 the platform slot + channel rotate together (same pan
group) so they never misalign; the fixed deck pass ↔ rotating slot offset is taken
by the wire winding in the 7.4 mm seat-void disc (z 51–58.4, r<34) + the loop below.

Minor: the 270° neck-bolt **M3 head counterbore (Ø6.5 at (0,−33)) breaks into the
platform cable slot edge by 0.25 mm** (slot edge y −30.0 vs cbore edge y −29.75).
Confirmed by containment probe. The screw head loses a sliver of its seat —
functional, but if touched anyway: bump that bolt circle `rad` 16.0 → 16.5 in BOTH
`build_neck_clevis()` and `build_pan_platform()` (they must stay in sync).

## 6. Channel exit at the column top — OBSTRUCTED (defect B, the real find)

The channel emerges at the column top (z 125) into a chimney that is boxed in on
every side (all containment-verified on the built mesh):

- **front**: the worm-cradle **riser** (x ±9, y −25..−20, z 125–141.5) — the channel
  cut hollows its back 3 mm, but its front 2 mm wall (y −22..−20) survives full-width;
- **rear**: the cheek-root block (y −40..−26, z 125–135) — bored only for |x| ≤ ~8;
- **sides**: at z 129.25–135.25 the cradle arm (x ±9) closes the flanks; on +x the
  gusset (x 14..24, z 122–144) blocks the right bay;
- **top**: the worm thread envelope — clearance at (0,−26,z) falls to 2.46 mm at
  z 134 and goes negative at z 138 (worm bottom ≈ 135.6).

Measured escape gaps: **left, between root face (y −26) and riser back (y −25):
1.0 mm** (z 125–129.25 only). Forward, in front of the riser: y −20..−18.2 =
**1.8 mm** — and the −30° head sweep (display stack rear digs to y −18.2 over
z 123–135 post-drop) closes onto it. Both fail even the Ø3.6 bundle. The wire
cannot legally leave the channel.

**Fix: a side exit window in the column's top-left corner**, subtracted from the
neck after the main union (next to the existing `chan` cut in `build_neck_clevis()`,
~line 1014): `box(12, 8, 10)` centered **(−12, −26, 122)** → spans x −18..−6,
y −30..−22, z 117..127. Probes confirm the zone is pure column/riser-bottom-corner
material; nearest other parts are motor_tilt at 10.9 mm and the platform 55 mm below;
it leaves the x −24..−18 column corner and a 2.5 mm web to the chin-notch face
(y −19.5). The cable then exits at x ≈ −12 below the riser into the **left bay**
(x −9..−24, y −26..−20), which is open upward to z ~147 (probed window at
(−13,−22,127): 20 mm free up, 20 mm free left) and stays 1.8 mm clear of the −30°
head sweep (bay is behind y −20). Mirror on +x is NOT available (gusset).

## 7. Tilt drape — CLEAR through the slot at all angles (given the fix above)

Anchors: pan-frame exit X1 = (−13,−22,127) (top of the left bay); head-frame entry
H = Pi USB-C at local (−30,−7.5,126) (bottom edge of the stack; the ETH edge faces
+X so power is at the −X end — the plug sits 1 mm inboard of the head slot's x ±31
side wall).

| TILT | H (world) | straight gap X1→H | chord min-clearance |
|------|-----------|------------------|---------------------|
| −30° | (−30, −22.4, 124.4) | 17.2 mm | 0.32 mm (neck root — wire bows forward) |
| −15° | (−30, −14.9, 124.2) | 18.7 mm | 0.95 mm |
| 0°   | (−30, −7.5, 126.0)  | 22.4 mm | 1.82 mm |
| +15° | (−30, −0.9, 129.6)  | 27.3 mm | 2.00 mm |
| +30° | (−30, +4.6, 134.9)  | 32.5 mm | 2.00 mm |

All worm-drive parts stay ≥ 10 mm from the chord at every angle; head shell ≥ 14.3;
the bottom-rear slot faces the exit across the whole range (exit stub vs head shell:
23.9 mm at −30°, 18.3 mm at +30° — no pinch). Total wire, column exit → plug:
31 mm (−30°) → 46.5 mm (+30°), i.e. **~15.5 mm of drape travel. Install ≈ 60 mm of
free lead** (max 46.5 + bow + strain relief at the plug); the slack bows down-forward
into the open head cavity at −30° and straightens at +30°.

## 8. Head-side path vs the worm/wheel/axle zone — CLEAR

Neutral-pose polyline (−13,−22,127) → (−13,−12,127) → (−20,−8.5,126.5) →
(−30,−7.5,126), i.e. hug z ≈ 126–127, cross under the −X cheek at y ≈ −8.5:
worm 14.2 mm, wheel 19.4, axle 23.5, motor_tilt 14.5, neck 2.0, head walls ≥ 18.7,
screen/Pi stack 12.3 mm (unsigned — reference mesh isn't watertight). The whole
mechanism cluster sits at z ≥ 135.6; the cable never needs to climb above z ≈ 128
until it is forward of the worm, so tilt motion doesn't sweep the drive through the
wire. At −30° the swept stack bottom passes 10.5 mm above the drape chord.

## Action list

1. **`build_base()`**: subtract the deck cable pass `cbl` AFTER the pedestal union
   (defect A — restores the full 16×8 drop; today's real window is 4.0 mm).
2. **`build_neck_clevis()`**: add the side exit window `box(12,8,10)` at
   (−12,−26,122) (defect B — today the channel exit is sealed to a 1.0 mm gap).
3. Optional: re-clock/bump the 270° neck-bolt circle 16.0 → 16.5 to un-graze the
   platform cable slot from the M3 head counterbore (0.25 mm overlap).
4. BOM/assembly note: route the power pair with ~60 mm free lead between the column
   exit and the Pi plug; coil 2 turns (~600 mm) at r ≈ 48, z ≈ 38–45 in the cavity;
   keep the pan software limit at ±90°.

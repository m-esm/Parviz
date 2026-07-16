# Mechanism audit

Verified 2026-07-16 against freshly generated STL and GLB geometry. A render is not
accepted as proof: each row names the geometric or executable evidence that protects it.

| Group | Interfaces checked | Result and evidence |
|---|---|---|
| Track links and master links | 64-link loop, six hinge pairings, ±35° articulation, PIP pins, boundary pins, keeper retention | PASS. `tools/probe_track_pip.py`: all 6 pairs × 30 angles clean, 0.349 mm minimum clearance. The master joint contract verifies locator, M2 insert retention, insertion and load path. |
| Sprockets, idlers and road wheels | Conjugate link action, keel channels, F688 seats, M8 tension stack, M4 shoulder axles | PASS. 18-phase × 5-link sweep has 0.0000 mm³ penetration and a 2.14 mm skip barrier. M8x70 spans jam nut, tower, washer and inner nut. The M4 shoulder prevents wheel clamping. |
| Chassis and side panels | Tub seams, panel splice/feet, deck seams, belly plate, equipment base and pedestal | PASS. Joint gates cover registration before screws, stacks, capture and driver access. Invariants probe dowels/tongues, nut paths and supporting material. Wheel beams and towers are integral to the panels. |
| Pan bearing and drive | 18-ball cage/race, three clips, platform locator, 32T:16T involute pair and hard stops | PASS. Real-gear metadata matches parameters and the generated pair has a 0.0000 mm³ coupled sweep. All pan extremes through ±90° pass interference checks. |
| Tilt axle and worm | 695 seats, D-key, thrust stack, carrier registration, 3-start worm/12T wheel and stops | PASS. `tools/gears/probe_worm_sweep.py` reports 0.0000 mm³ on the coupled motion. The carrier joint verifies four M3 fasteners, locator, insertion and load path. All tilt extremes through ±30° pass. The printed axle remains an interim substitute for steel. |
| Head, screen and door | Bezel/back seams, panel rebates, tray rails/pillars, camera cover, hooks and snap tongues | PASS. Head contracts verify locators, nuts, stacks, access and material. Invariants probe hooks, freed tongues, screen pattern and service openings. Open the door near neutral tilt. |
| Antenna drives | Motor double-D, two compound stages, idler journal, fused output/pinion, rack, bracket and guide | PASS after repair. Disconnected preview discs became eight separately exported involute parts. Every part is one watertight body. Both static trains have 0.0000 mm³ tooth interference; an 11-position coupled sweep covers the full 50 mm travel below 0.02 mm³. |
| Plastic hardware stand-ins | M4/M8 threads, shoulders, F688 bushings, pan rollers, axle and dowels | PASS as interim hardware. ISO forms, clearances, grooves/crush ribs and shoulders are covered by `tests/test_hardware_standins.py`. Metal remains preferred for strength, wear and creep. |

## Whole-assembly evidence

- `make gate-tests`: 20 tests pass.
- `make invariants`: 62/62 invariants pass.
- `make jointcheck`: 261/261 gates pass across 18 structural joints.
- `make wallcheck`: all 66 exported parts meet the wall gate or a documented gear/thread edge floor.
- Neutral assembly: no unapproved overlap above 0.01 mm³.
- Motion envelope: all 14 isolated poses pass, including ±90° pan × ±30° tilt corners.
- Fit map: 140 close pairs and 12 press fits; every touching pair is expected.
- Stability: 52.8° worst tip angle and 82× fast-pan overturning margin.

Optional arms are excluded deliberately. `ARMS=1` enables visual placeholders only;
`docs/ARM-MECH.md` is a future design brief, not a verified printable actuator.

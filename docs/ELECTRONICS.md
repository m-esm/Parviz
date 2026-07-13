# Electronics

Every electronic component in the Parviz build: what it does, whether it is owned,
and where to download a reference CAD model. Status comes from the 2026-07-13
inventory re-audit (see ASSEMBLY.md for the full BOM including mechanical hardware).

Reference models matter because the CAD placeholders in `src/motors.py` and the
sensor/board placeholders in `src/chassis.py` were dimensioned from datasheets;
a downloaded mesh is the fastest way to sanity-check a placeholder against the real
part. **Verify any downloaded mesh against the datasheet before trusting fits** --
some Thingiverse "models" are low-poly illustrations, not mechanical CAD.

## Compute + head module

| Component | Role | Status | Reference model |
|---|---|---|---|
| Raspberry Pi 5 (2GB) | Brain: face render, perception, local LLM, voice | OWNED (on the bench, `moshe-pi5-2gb.local`) | No board model on Thingiverse; official STEP at [rpi products page](https://www.raspberrypi.com/products/raspberry-pi-5/) -- and the repo already carries the combined screen+Pi mesh in `reference/rpi-7in-touchscreen-model/` |
| Official 7" Touch Display | The face | OWNED | [clough42 reference model (thing:1646255)](https://www.thingiverse.com/thing:1646255) -- repo already has the official STEP/STL |
| Camera Module 3 | The eye (imx708) | OWNED | [CM3 Wide mockup (thing:6939162)](https://www.thingiverse.com/thing:6939162) -- Wide variant, same 25x24 board, different lens barrel; repo models CM3 from official dims |
| Pi 5 Active Cooler | Head thermal (80C breaker trips under brain bursts) | BUY (nice-to-have; CAD clearance CLEARED 2026-07-13) | Official envelope modeled in `build_pi5_cooler()` from RP-008188/RP-008187 |
| Gooseneck mics x2 + CM108 | Ears (Ø17 windscreen through head side walls) | ORDERED, not yet in inventory | none needed -- placeholder `ear_mic_L/R` |

## Motion

| Component | Role | Status | Reference model |
|---|---|---|---|
| 28BYJ-48 stepper x4 | Pan (2:1 spur), tilt (3-start worm), 2x antenna deploy | OWNED x6 (Bags 5, 14) | [MajicDesigns (thing:4919536)](https://www.thingiverse.com/thing:4919536) -- Fusion360 + IGES + STL; also [CastorX (thing:3247370)](https://www.thingiverse.com/thing:3247370) |
| ULN2003 driver x4 | Stepper drivers | OWNED x9 | [seandoughtie clearance model (thing:3781347)](https://www.thingiverse.com/thing:3781347) |
| TT gearmotor 1:120 x2 | Track drive (2 more OPTIONAL for twin-drive) | OWNED x3 (Bag 5); buy 1 only for the 4th station | [mademodeller TT motor + gearbox (thing:4890871)](https://www.thingiverse.com/thing:4890871) |
| MX1588 H-bridge | Drives both TTs | OWNED x5 | none found; trivial 2-layer module, model from measurement |

## Sensors (Arduino I/O plane, docs/AWARENESS.md)

| Component | Role | Status | Reference model |
|---|---|---|---|
| Arduino Uno R3 | I/O plane: sensors + reflexes, one USB to the Pi | OWNED x3 (Bag 6) | [DesignSpark CAD (thing:346338)](https://www.thingiverse.com/thing:346338); also [1:1 replica (thing:6564384)](https://www.thingiverse.com/thing:6564384) |
| HC-SR04 x4 | Forward + rear obstacle, 2x cliff | BUY (none owned) | [dvemac outline (thing:3653635)](https://www.thingiverse.com/thing:3653635); [markbenson OpenSCAD (thing:122136)](https://www.thingiverse.com/thing:122136) |
| LD2410-class mmWave | Presence, boresight-forward behind the front hex grille | BUY | dims VERIFY_ON_ARRIVAL (LD2450 does NOT fit the bay) |
| BME688 | Env sensing over the y-96 left vent | BUY | dims VERIFY_ON_ARRIVAL |
| MPU6050/ICM-20948 IMU | Motion, near the pan axis | BUY | dims VERIFY_ON_ARRIVAL |
| SW-420 | Vibration, hard pad at (-48,-95) | BUY | dims VERIFY_ON_ARRIVAL |
| TTP223 x2-4 | Cap touch (head-top pass deferred) | BUY | dims VERIFY_ON_ARRIVAL |

## Power (firmware/WIRING.md)

| Component | Role | Status | Reference model |
|---|---|---|---|
| 30W+ USB-C PD brick | Wall power | BUY (official 27W works marginally) | n/a |
| 12V PD trigger | Rear jack, sets the harness rail | BUY | n/a |
| XL4015-class 5A buck | Pi rail (trimmed 5.25V) on the belly tray | BUY (owned LM2596s are 2-3A class) | Thingiverse has only enclosures ([tag:xl4015](https://www.thingiverse.com/tag:xl4015)); board dims VERIFY_ON_ARRIVAL |
| MP1584 mini buck | Motor rail | BUY (a selectable-5V module could stand in) | enclosures only ([thing:5324190](https://www.thingiverse.com/thing:5324190) etc.); dims VERIFY_ON_ARRIVAL |
| Inline blade-fuse holder | 5A Pi-rail fuse (fuse itself OWNED, ATC/ATO assortment) | BUY holder | n/a |
| SK6805-2427 narrow strip 1m | Forehead LED slot (42x5 -- a standard 8x5050 stick does NOT fit) | BUY | n/a |

## Thingiverse download workflow

Thingiverse blocks headless downloads (search returns a React shell, `download:`
endpoints 401 without an app token), but **"Download all files" works anonymously in
a real browser**. Zips land as `<Name> - <thingId>.zip` with `files/` + `images/`.
Drop downloads into `reference/` with the thing URL + license recorded here; things
are individually licensed (usually CC variants) and the repo is public.

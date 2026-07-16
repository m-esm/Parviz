# Electronics

Every electronic component in the Parviz build: what it does, whether it is owned,
and where to download a reference CAD model. Status comes from the 2026-07-13
inventory re-audit plus the **2026-07-14 order batch** (Tray 1, ordered NOT yet
delivered; see ASSEMBLY.md for the full BOM including mechanical hardware).

**2026-07-14 order batch (changes the plan):** Pi 5 **8GB** (lifts the 2GB RAM
ceiling), 2x **Sense HAT Rev2** (covers the IMU + env-sensor buys, adds
color/light + LED matrix + joystick), **AI Camera IMX500** (resolves the
AWARENESS.md "AI camera" open decision), 2x **Joy-IT RPI5-HEATSINK5** coolers
(bigger than the verified head keep-out -- see its row), a 30x10 5V fan, an
A4988 bipolar stepper driver and 6x N20 gearmotors (no design use yet, options
noted below). Everything in this batch is VERIFY_ON_ARRIVAL for dims.

Reference models matter because the CAD placeholders in `src/motors.py` and the
sensor/board placeholders in `src/chassis.py` were dimensioned from datasheets;
a downloaded mesh is the fastest way to sanity-check a placeholder against the real
part. **Verify any downloaded mesh against the datasheet before trusting fits** --
some Thingiverse "models" are low-poly illustrations, not mechanical CAD.

**Integrated into the assembly (2026-07-13):** the downloaded meshes for the
28BYJ-48, TT gearmotor, HC-SR04, Arduino Uno, and Camera Module 3 now REPLACE
their box/cylinder placeholders in `web/assembly.glb`, so the viewer shows the
real part geometry. `src/refparts.py` poses each real mesh onto the placeholder's
oriented bounding box by a 24-orientation best-fit, so it lands at the exact
placeholder location and orientation. **Exception (2026-07-16): the 28BYJ-48 is
registered deterministically instead** -- the OBB best-fit is blind to its
eccentric shaft and parked every real stepper ~15 mm off its gear axis, so
refparts recovers the placeholder's exact pose (Kabsch over the vertex
correspondence) and applies a fixed measured native-to-local transform; the
shaft now lands on the pan/tilt/antenna gear axes within the mesh's own 0.125 mm
eccentricity slop (guarded by `tests/test_refparts_28byj.py`). The same pass
deleted the placeholder's phantom 9 mm gearbox tier (see CLAUDE.md) so the real
motor's shaft actually reaches its gears. They are bought parts, never printed, and
skipped by the boolean interference/fit gates (like the non-watertight screen
mesh). `PLACEHOLDER_PARTS=1 make build` restores the analytic placeholders and
their full gate coverage. The ULN2003 has no downloaded mesh (see below), so it
keeps its placeholder.

## Compute + head module

| Component | Role | Status | Reference model |
|---|---|---|---|
| Raspberry Pi 5 (2GB) | Brain: face render, perception, local LLM, voice | OWNED (on the bench, `moshe-pi5-2gb.local`) | No board model on Thingiverse; official STEP at [rpi products page](https://www.raspberrypi.com/products/raspberry-pi-5/) -- and the repo already carries the combined screen+Pi mesh in `reference/rpi-7in-touchscreen-model/` |
| Raspberry Pi 5 **8GB** | Brain upgrade: lifts the 2GB RAM ceiling (AWARENESS.md budget: 1.7B-class ambient LLM + bigger ASR fit NEXT TO the face now) | ORDERED 2026-07-14 (Tray 1) | same board mechanically; drop-in on the display standoffs |
| Official 7" Touch Display | The face | OWNED | [clough42 reference model (thing:1646255)](https://www.thingiverse.com/thing:1646255) -- repo already has the official STEP/STL |
| Camera Module 3 | The eye (imx708) | OWNED | [CM3 Wide mockup (thing:6939162)](https://www.thingiverse.com/thing:6939162), CC BY-SA, DOWNLOADED to `reference/electronics/rpi-cam3-wide-mockup-6939162/` (mesh 25.0x23.9 = official 25x24 board; Wide lens barrel differs) |
| AI Camera (IMX500) | Eye upgrade: on-sensor NPU runs detection ON the camera, freeing Pi CPU/RAM for the brain (resolves the AWARENESS "AI camera" decision) | ORDERED 2026-07-14 (Tray 1) | 25x24 board like CM3 but DEEPER module + different lens barrel: the forehead cam pod (Ø6.3 lens bore + recess depth) is CM3-sized, so the pod needs a re-fit pass -- VERIFY_ON_ARRIVAL, keep CM3 as the modeled default until measured |
| Joy-IT RPI5-HEATSINK5 x2 | Head thermal (80C breaker trips under brain bursts) | ORDERED 2026-07-14 (Tray 1). **WARNING: 65x45x15 mm (+ 30x30x10 fan) EXCEEDS the verified official-cooler keep-out (63.5x42.5x13.7) on every axis, and the tilt-sweep margin was only 0.60 mm** -- re-run `tools/probe_cooler.py` with the Joy-IT envelope before installing in the head; if it fails, fall back to the official Active Cooler (envelope already verified) or duct the separate 30x10 fan at the louvres | dims from the [Joy-IT manual](https://joy-it.net/en/products/RB-Heatsink5) |
| Fan 5VDC 30x10 (B-3010-D05-MLA) | Spare / louvre-duct option if the Joy-IT cooler fails the head probe | ORDERED 2026-07-14 (Tray 1) | n/a |
| Gooseneck mics x2 + CM108 | Ears (Ø17 windscreen through head side walls) | ORDERED, not yet in inventory | none needed -- placeholder `ear_mic_L/R` |

## Motion

| Component | Role | Status | Reference model |
|---|---|---|---|
| 28BYJ-48 stepper x4 | Pan (2:1 spur), tilt (3-start worm), 2x antenna deploy | OWNED x6 (Bags 5, 14) | [MajicDesigns (thing:4919536)](https://www.thingiverse.com/thing:4919536) -- Fusion360 + IGES + STL; also [CastorX (thing:3247370)](https://www.thingiverse.com/thing:3247370) |
| ULN2003 driver x4 | Stepper drivers | OWNED x9 | [seandoughtie clearance model (thing:3781347)](https://www.thingiverse.com/thing:3781347), CC0 -- NOT downloaded (Chrome silently swallows this thing's download; grab manually if needed) |
| TT gearmotor 1:120 x2 | Track drive (2 more OPTIONAL for twin-drive) | OWNED x3 (Bag 5); buy 1 only for the 4th station | [CCFIVE yellow TT motor (thing:1079893)](https://www.thingiverse.com/thing:1079893), CC BY, DOWNLOADED to `reference/electronics/tt-motor-1079893/` (STL + STEP, 69.5x22.4x29.9); also [mademodeller (thing:4890871)](https://www.thingiverse.com/thing:4890871) |
| MX1588 H-bridge | Drives both TTs | OWNED x5 | none found; trivial 2-layer module, model from measurement |
| A4988 (Pololu) | No station yet. Option it enables: rewire a 28BYJ-48 bipolar (cut the red common) for ~+40% torque on pan or tilt if the 4:1/2:1 margins prove thin on hardware | ORDERED 2026-07-14 (Tray 1) | n/a |
| N20 gearmotor 6V (240RPM x4, 400RPM x2) | No station yet. Prime candidate: the deferred gripper-arm actuation (rack-and-sector parallel gripper, reference/hand-mechanism/) | ORDERED 2026-07-14 (Tray 1) | n/a |

## Sensors

Two planes since 2026-07-14: the **Sense HAT Rev2 rides the Pi's I2C bus** (it is a
Pi peripheral with kernel/python support, not an Arduino part) while the timing-
critical and 5V modules stay on the **Arduino I/O plane** (docs/AWARENESS.md).

| Component | Role | Status | Reference model |
|---|---|---|---|
| **Sense HAT Rev2 x2** | One board covers THREE former buy-list rows: LSM9DS1 9-DoF IMU (accel+gyro+MAG), LPS25H pressure/temp, HTS221 humidity/temp -- plus NEW capabilities: TCS3400 color/ambient-light sensor, 8x8 RGB LED matrix, 5-way joystick. All I2C (0x6a/0x1c IMU, 0x5c, 0x5f, 0x29 color, 0x46 matrix+joystick). Mounts REMOTELY on the chassis equipment base (65x56.5 HAT outline, M2.5 at the 58x49 pattern) fed by a thin I2C drop down the neck -- it can NOT stack on the Pi (no head clearance + the cooler owns that space), see firmware/WIRING.md. 2nd unit = spare / bench Pi | ORDERED 2026-07-14 x2 (Tray 1) | official; dims VERIFY_ON_ARRIVAL |
| Arduino Uno R3 | I/O plane: sonar timing, vibration, mmWave, touch, LEDs, reflexes; one USB to the Pi | OWNED x3 (Bag 6) | [DesignSpark CAD (thing:346338)](https://www.thingiverse.com/thing:346338), CC BY-SA, DOWNLOADED to `reference/electronics/arduino-uno-r3-346338/` (OBJ + RSDOC); also [1:1 replica (thing:6564384)](https://www.thingiverse.com/thing:6564384) |
| HC-SR04 x4 | Forward + rear obstacle, 2x cliff | BUY (none owned) | [dvemac (thing:3653635)](https://www.thingiverse.com/thing:3653635), CC BY, DOWNLOADED to `reference/electronics/hcsr04-dvemac-3653635/` (STL+STEP/SLDPRT+3MF, 45.2x18.5x26.5 = 45x20 board + barrels); also [markbenson OpenSCAD (thing:122136)](https://www.thingiverse.com/thing:122136), CC BY-NC, in `hcsr04-markbenson-122136/` |
| LD2410-class mmWave | Presence, boresight-forward behind the front hex grille | BUY | dims VERIFY_ON_ARRIVAL (LD2450 does NOT fit the bay) |
| BME688 | ~~Env sensing~~ DOWNGRADED to optional: the Sense HAT covers temp/humidity/pressure; buy a BME688 only if VOC/gas sensing ("room feels stuffy") is wanted | OPTIONAL (was BUY) | dims VERIFY_ON_ARRIVAL |
| MPU6050/ICM-20948 IMU | ~~Motion, near the pan axis~~ COVERED by the Sense HAT's LSM9DS1 -- off the buy list. NOTE the chassis_base IMU posts at (14,-12) become the Sense HAT seat in the next base iteration (cheap reprint by design) | COVERED (was BUY) | n/a |
| SW-420 | Vibration, hard pad at (-48,-95) | BUY | dims VERIFY_ON_ARRIVAL |
| TTP223 x2-4 | Cap touch (head-top pass deferred) | BUY | dims VERIFY_ON_ARRIVAL |

**I2C address note:** the Sense HAT's TCS3400 sits at **0x29, the same address as
the VL53L1X ToF** that was once a cliff-sensing candidate -- if a VL53L1X ever
joins the bus it needs its XSHUT re-address dance or a mux.

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

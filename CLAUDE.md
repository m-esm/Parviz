# desk-pi — tracked desk robot (Raspberry Pi head)

A small **tank-tracked mobile robot**: a **Raspberry Pi 5** driving the **official 7" touchscreen**
as an animated face, with a **Camera Module 3** as an eye, on a **neck that pans + tilts** the head,
sitting on a **two-track tank chassis** so it can drive around the desk.

The head is a **clean rounded box** (a tablet-head; earlier it was an Echo-Show wedge, since
simplified). Screen upright on the front, neck tilt gives the look up/down.

Status: **REVISED ASSEMBLY (post multi-agent review + reshape).** `src/build.py` builds the whole
robot around the measured 7" screen STL; 7 watertight per-part STLs (chassis, track_L, track_R,
neck_clevis, pan_platform, head_bezel, head_back). A 4-lens agent review drove fixes (tilt-axle Z
bug, proportions, Pi-in-head, printable head split, fastening, cable path); then the head was
simplified to a box, the LCD orientation bug fixed (see TAU gotcha), and the base swapped for tank
treads. Remaining detailing (IO chamfer, motor coupler, slip ring) is
tracked in the todo list. Motors are 28BYJ-48 placeholders.

## The build loop (do this on every geometry change)

```
make build          # python3 src/build.py -> web/assembly.glb
make viewer         # python3 src/serve.py 8765 (leave running; user watches live at
                    #   http://localhost:8765/viewer_glb.html -- auto-reloads on rebuild)
make shot           # headless render -> .claude/renders/chk_*.png  (serve must be up)
```

Then **downscale and actually Read every PNG** before claiming a change works:
`sips -Z 1400 .claude/renders/chk_iso.png --out .claude/renders/chk_iso_s.png`.
The model is served at `/assembly.glb` (serve.py serves `web/` at root), so shoot.py takes
the **bare** name `assembly.glb`, not `web/assembly.glb`.

## Mechanical intent

World frame: **Z up, robot drives + looks toward +Y** (glass + camera + track travel all +Y).
Origin = center of the ground contact plane. `base_h = 52` is the chassis-top / pan-mount plane.

Kinematic chain, bottom to top (built at neutral pose pan=0, tilt=0):

```
tank chassis        DRIVE base: central body (build_base) + track_L/track_R (build_tracks).
  │                 Body houses the pan motor + driver + wiring; pan-mount on top (z=52).
  │                 Tracks = stadium belt loops (drive+idler wheels), belt to ground, run along Y.
  └─ PAN joint      yaw about vertical Z  (±90° target), driven by motor_pan   ── the "turret"
      └─ pan_platform + neck_clevis   rotate as one
          └─ TILT joint   pitch about horizontal X  (±30° target), driven by motor_tilt
              └─ head = head_bezel + head_back (rounded box) + screen + camera + Pi 5
```

- **Pan** carries the whole neck + head. **Tilt** carries only the head. Tilt is a child of pan,
  so a pan move swings the tilt axis with it (correct for a neck).
- **Tilt is a REAR CLEVIS, not a side gimbal.** The head is a deep box, so the tilt axle passes
  *inside* it (z=178, near the CoM). The head grips the axle at hubs on its two side walls; the
  narrow neck clevis (cheeks at x=±22) rises through a slot in the head's bottom-rear and drives the
  axle in the middle. Narrow neck, small cantilever (~39mm). The Z of the clevis MUST match the axle
  (z=178) — an earlier bug lifted the clevis 46mm and it punched through the head; don't reintroduce
  a second lift (build everything in world Z).
- **Camera rides the head** in the top bezel nub, lens on the face normal, so it looks where the
  face looks (inherits pan + tilt for free).
- **Pi 5 lives IN THE HEAD, behind the tilt axis** (changed from base after the multi-agent review).
  The official 7" display's DSI ribbon + the camera CSI ribbon are short and stiff and cannot cross
  two moving joints; keeping the Pi in the head keeps both ribbons entirely in the head (zero joint
  crossings). The board also doubles as the tilt counterweight. Only round wires (Pi power + the pan
  stepper's leads) cross the joints. Tradeoff: heavier head + higher CoM → ballast the base for the
  wheeled version.
- **Cable path:** hollow tilt axle (on-axis, no length change when tilting) → vertical channel down
  the neck column → off-axis pass through pan_platform + base. The pan joint still winds the bundle:
  use a slip ring on the pan axis (preferred, needs a purchased capsule) or a service loop that caps
  pan range. NOT yet resolved in geometry.

## Head is a 2-piece print (bezel + back)

`build_head_parts()` slices the wedge on a plane parallel to the front face, ~4mm behind the screen:
- `head_bezel` (front): the leaned face + camera nub. The screen aperture is **stepped** — a full-
  size pocket behind + a smaller front window, so the front lip traps the glass edge (screen can't
  fall out the front). Print face-down.
- `head_back` (rear): pivot hubs, neck slot, Pi bay, cable port. Print open-side-down.
Screen drops into the pocket from behind; bezel bolts to back. Fastening bosses NOT yet modeled.

## Head style: simple rounded box (simplified from the Echo-Show wedge, per user)

The head is now a **clean rounded box** (`_head_solid`: rounded-rect footprint 205w × 62d, flat
top/bottom, rounded vertical edges, upright front `face_angle=0`). The screen sits upright and flush
on the front; the neck's tilt provides the look up/down. It started as an Echo-Show "doorstop" wedge
(reference in `reference/alexa-style-smart-display/`, a Touch Display 2 design we borrowed the style
from) but the user asked to simplify the head shape. Still split by `build_head_parts()` into
`head_bezel` (front, screen-retaining lip, camera nub) + `head_back` (Pi bay, hubs, vents).

## Key numbers (measured, not guessed)

Screen `PARAMS["screen_*"]` are **measured from the reference STL bbox**: 193.0 (W) × 25.0 (D) ×
110.8 (H) mm, driver board included. Loaded live from
`reference/rpi-7in-touchscreen-model/files/Raspberry_Pi_Touch_Screen_Assembly_v12.stl` and mounted
on the leaned face by `screen_pose()`. Overall assembly bbox ≈ 221 × 208 × 248 mm.

Still first-guess (validate on a print): tilt axis height 178, cantilever 39, face lean 8°,
base Ø208 bottom / Ø156 top / bolt circle Ø170, tilt range ±30, pan range ±90. `motor_*` are
28BYJ-48-shaped placeholders. Base bottom Ø208 ≥ head width 213, so the head no longer overhangs.

## Power (decided)

Use the **official Raspberry Pi 27W USB-C PD supply (5.1V / 5A)**. The Pi 5 only unlocks full
USB current on a true 5A PD supply; a 15W/3A brick software-limits USB to ~600mA and browns out
once screen + camera + servos draw together. Two servos (pan + tilt) may want their **own 5–6V
supply** rather than pulling off the Pi's rail — decide when the servo BOM is picked.

## Motors — 28BYJ-48 (picked from inventory), mounts still TODO

Motor choice made against the parts on hand (see the moshes-inventory MCP): the only owned motor
with enough torque AND position control for this head is the **28BYJ-48 5V geared stepper** (×6 in
Bags 5 & 14) with **ULN2003 driver boards** (×9). The 9g servos (SG90 ×9, MG90S ×1) are too weak to
swing a 193mm screen head. So `motor_pan` / `motor_tilt` placeholders are now **28BYJ-48-shaped**
(Ø28 can + gearbox + 8mm-offset output shaft) — see `motor_28byj()`.

- **Pan:** 28BYJ-48 upright in the base, shaft up on the pan axis into `pan_platform`. Offset shaft
  means the can sits 8mm off-axis (modeled).
- **Tilt:** 28BYJ-48 on the +X clevis cheek, shaft to the tilt axle. Holds ~15 N·cm gravity moment;
  the 28BYJ-48 has ~34 N·cm holding torque energized → ~2× margin. **Caveat:** it only holds while
  coils are powered (idle current, mild heat). If that's a problem, add a worm/geared reducer (self-
  locking) or a small counterbalance behind the tilt axis. Decide on a print test.
- **STILL TODO (this is the deferred "design motor mounts" task):** the actual Ø28 motor pockets,
  the offset-shaft coupling to axle/platform, and the ULN2003 board mounts. The offset output shaft
  is the annoying part — the real mount aligns the *shaft* to the axis, not the can.
- **Pan bearing:** a lazy-Susan / thrust bushing in the base seat (undecided).
- **Pan cable routing:** DSI ribbon + camera + power cross the pan joint → needs a service loop;
  this caps pan range. Settle before finalizing the base.

For the future wheels: TT 1:120 gear motor + 130-size DC motors (×10) + MX1588 / ULN2003 drivers are
already in inventory.

## Tank chassis (the mobile base)

Two-track tank base so it can drive. `build_base()` is the central **body** (rounded box, houses the
pan motor + ULN driver + wiring, pan platform on top at z=52). `build_tracks()` makes two **track
pods** — stadium belt loops (a shapely capsule = drive + idler wheel wrapped by the belt), belt
touching ground, running along Y (forward). Hub caps on the outer face read as the wheels.

Params: `chassis_w/l`, `track_r`, `track_wheelbase`, `track_width`, `track_gap`, `chassis_clear`.
NOT yet designed: the drive-motor mounts for the tracks (each track needs its own motor — the pan/
tilt 28BYJ steppers are separate), the belt as a real printed/TPU loop vs a rigid ring, road wheels
inside the loop, and how the body bolts to the pods. Since the Pi rides the head (higher CoM), keep
the chassis heavy/low and the wheelbase long enough not to tip when it accelerates or pans the head.

## Print notes (first pass — not finalized)

- 7 printed parts (`chassis`, `track_L`, `track_R`, `neck_clevis`, `pan_platform`, `head_bezel`,
  `head_back`) are watertight solids. (`head_shell`/`_head_solid` are pre-split intermediates.)
- **Fastening = M3 screws into CAPTIVE HEX NUTS** (user choice). `nut_trap`/`screw_post` helpers.
  - bezel↔back: 6 perimeter posts, nut captive in the back boss, screw from the front.
  - neck↔pan_platform: 3× M3 (pilots in the neck base, clearance in the platform).
  - Pi 5: 4× M2.5 standoffs on the back cover (58×49 pattern).
  - 28BYJ-48: tilt motor on a cheek mount plate (shaft hole + 2 ear holes); pan motor on a floor
    pad in the base (2 ears, shaft up the pan bore).
- **Hubs:** Ø8 bushing counterbores at each head side wall (press-fit bushings; PLA isn't the
  running surface, and it dodges the horizontal-bore droop problem).
- **Electronics fittings:** base has a pan-motor pad + ULN2003 standoffs + a USB-C wall slot +
  8 vent slots; head back cover has a Pi I/O slot + ventilation louvres + the cable port.
- **Per-part print orientation:** bezel face-down (aperture opens up, best cosmetic face), back
  open-side-down, neck on its back, base flange-down.
- **Still a refinement:** explicit 45° self-supporting chamfers on the largest back openings
  (I/O slot ~64mm), the offset-shaft coupler part, a second ULN mount for the tilt driver, and the
  pan-joint slip ring (a purchased capsule — model its seat once you buy one). Screen standoffs wait
  on measuring the display's real mount holes from the reference STEP.

## Layout

```
src/build.py     source of truth. PARAMS block at top; builds chassis/tracks/pan/neck/head into a GLB.
src/stlpaths.py  routes stlp("track_L.stl") -> stl/base/... ; subsystems: base / neck / head
src/serve.py     localhost viewer server (serves web/ at root)
src/shoot.py     headless multi-angle renders -> .claude/renders/
web/             viewer_glb.html + assembly.glb (committed so a fresh clone shows the assembly)
stl/{base,neck,head}/   per-part STLs (head_bezel + head_back), written by `EXPORT=1 python3 src/build.py`
exports/         Bambu .3mf plates (regenerable, gitignored)
reference/       rpi-7in-touchscreen-model (STEP/STL, the real screen) + -case + alexa-style-*
docs/ASSEMBLY.md BOM + assembly order
```

## Gotchas

- **`TAU` in build.py is `2*np.pi` (a full turn).** It was once wrongly set to `np.pi`, which made
  `R(TAU/2)` a 90° rotation — that silently laid the LCD on its back (the "screen position wrong"
  bug) and half-rotated the tilt motor and vents. If you touch `TAU`, keep it `2π` and remember
  `cyl(axis="x"/"y")` relies on `R(TAU/4)` = 90°.
- The screen STL loads as X=width, Y=depth, Z=height (correct, upright). `screen_flip=True` applies a
  180° YAW (about Z) to face the glass +Y. `screen_pose()` = optional face lean + translate to the
  front face; `tilt_cantilever` sets how far forward (keep glass ~flush with `body_front_y`).
- `python3` here is **3.9**; `build123d` needs ≥3.10. This uses the **trimesh + shapely + manifold**
  path (works on 3.9). Move to build123d in a venv when we want native fillets/chamfers.
- serve.py serves `web/` at root: the model URL is `/assembly.glb`. Passing `web/assembly.glb` to
  shoot.py 404s.
- The viewer **ghosts** housing-like parts by name (anything with shell/body/housing/case/lid) —
  that's why `head_shell` renders as a translucent outline. Toggle **solid** in the viewer to see it
  filled. `shoot.py` can't toggle it, so to render the shell solid, rename it in a temp scene.
- Screen STL axes already match ours (X=W, Y=D, Z=H); no swap needed, just recenter + `screen_pose()`.
- `EXPORT=1 python3 src/build.py` writes the per-part STLs; the plain run only refreshes the GLB.
- Reference `.123dx` files are Autodesk 123D (not usable); use the `.stl`/`.step` siblings.

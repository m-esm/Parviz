# desk-pi — desktop humanoid robot (Raspberry Pi head)

A small desk robot: a **Raspberry Pi 5** driving the **official 7" touchscreen** as an
animated face, with a **Camera Module 3** as an eye, mounted on a **neck that turns the
head on two axes** (pan = look left/right, tilt = nod up/down). Sits on a fixed base.

Scope right now: **neck + head only**, two-axis motion. **A wheeled base comes later** — the
base bottom is already a bolt flange for that (see below). No arms, no torso.

Status: **REVISED ASSEMBLY (post multi-agent review).** `src/build.py` builds the pan/tilt assembly
around the measured 7" screen STL; 6 watertight per-part STLs. A 4-lens agent review (mechanics /
aesthetics / printability / electronics) drove a round of fixes: the tilt-axle Z bug, a cone base,
a rounded neck, an 8° face, the Pi moved into the head, the head split into bezel+back with screen
retention, and a cable path. Remaining detailing (bosses, motor pockets, vents, slip ring) is
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

World frame: **Z up, robot looks toward +Y** (glass + camera face +Y, away from the neck).
Origin = center of the desk contact plane (later: top of the wheeled chassis).

Kinematic chain, bottom to top (built at neutral pose pan=0, tilt=0):

```
base (hollow cone)  fixed; houses pan motor + wiring. Bottom = future-wheels bolt flange.
  └─ PAN joint      yaw about vertical Z  (±90° target), driven by motor_pan
      └─ pan_platform + neck_clevis   rotate as one
          └─ TILT joint   pitch about horizontal X  (±30° target), driven by motor_tilt
              └─ head = head_bezel + head_back (Echo-Show wedge) + screen + camera + Pi 5
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

## Head style: Alexa / Echo-Show wedge (per user)

The head shell copies the **Echo-Show "doorstop" wedge** from
`reference/alexa-style-smart-display/` (a Touch Display 2 design — NOT hole-compatible with our
original 7" screen, we only borrow the *style*). Rounded body, front face leaned back ~11°, screen
recessed in the front aperture, slim bezels, camera nub at the top. That reference body is
191×110×122mm — almost identical to our 7" module (193×110.8), so the style and scale transfer
directly. Built parametrically in `build_head_shell()` (extruded rounded side-profile), then split
by `build_head_parts()`. Lean angle (now **8°**, softened from 11°), rounding, and proportions are
`PARAMS` knobs. The base is a **truncated cone** matching the friendly language.

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

## Wheels later (base is ready for it)

The base bottom is a **flat flange with an M4 bolt circle (Ø170, 4 holes)** so the whole robot can
later bolt onto a wheeled chassis. The neck↔base plane at z=0 is the swap plane. Since the Pi now
rides the head, **ballast the base** (heavy plate / battery low) for the mobile version so it doesn't
tip when accelerating or with the head panned out.

## Print notes (first pass — not finalized)

- All 6 printed parts (`base`, `neck_clevis`, `pan_platform`, `head_bezel`, `head_back`) are
  watertight solids. (`head_shell` is the pre-split intermediate, not printed directly.)
- **Done:** head split into bezel + back with a screen-retention lip; hollow base + cavity.
- **NOT yet done (tracked as remaining todos):** screw bosses / heat-set inserts (bezel↔back, base
  lid, Pi, both motors, screen standoffs); self-supporting chamfers on the rear/slot openings +
  teardrop/bushing axle bores; real 28BYJ-48 motor pockets + offset-shaft couplings; ULN2003 driver
  mounts; Pi ports + ventilation; pan-joint slip ring.
- Per-part orientation: bezel face-down, back open-side-down, neck on its back, base flange-down.

## Layout

```
src/build.py     source of truth. PARAMS block at top; builds base/pan/neck/head + refs into a GLB.
src/stlpaths.py  routes stlp("head_shell.stl") -> stl/head/... ; subsystems: base / neck / head
src/serve.py     localhost viewer server (serves web/ at root)
src/shoot.py     headless multi-angle renders -> .claude/renders/
web/             viewer_glb.html + assembly.glb (committed so a fresh clone shows the assembly)
stl/{base,neck,head}/   per-part STLs (head_bezel + head_back), written by `EXPORT=1 python3 src/build.py`
exports/         Bambu .3mf plates (regenerable, gitignored)
reference/       rpi-7in-touchscreen-model (STEP/STL, the real screen) + -case + alexa-style-*
docs/ASSEMBLY.md BOM + assembly order
```

## Gotchas

- `python3` here is **3.9**; `build123d` needs ≥3.10. This uses the **trimesh + shapely + manifold**
  path (works on 3.9). Move to build123d in a venv when we want native fillets/chamfers on the shell.
- serve.py serves `web/` at root: the model URL is `/assembly.glb`. Passing `web/assembly.glb` to
  shoot.py 404s.
- The viewer **ghosts** housing-like parts by name (anything with shell/body/housing/case/lid) —
  that's why `head_shell` renders as a translucent outline. Toggle **solid** in the viewer to see it
  filled. `shoot.py` can't toggle it, so to render the shell solid, rename it in a temp scene.
- Screen STL axes already match ours (X=W, Y=D, Z=H); no swap needed, just recenter + `screen_pose()`.
- `EXPORT=1 python3 src/build.py` writes the per-part STLs; the plain run only refreshes the GLB.
- Reference `.123dx` files are Autodesk 123D (not usable); use the `.stl`/`.step` siblings.

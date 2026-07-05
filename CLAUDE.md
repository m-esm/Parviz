# desk-pi — desktop humanoid robot (Raspberry Pi head)

A small desk robot: a **Raspberry Pi 5** driving the **official 7" touchscreen** as an
animated face, with a **Camera Module 3** as an eye, mounted on a **neck that turns the
head on two axes** (pan = look left/right, tilt = nod up/down). Sits on a fixed base.

Scope right now: **neck + head only**, two-axis motion. **A wheeled base comes later** — the
base bottom is already a bolt flange for that (see below). No arms, no torso.

Status: **FIRST FUNCTIONAL ASSEMBLY.** `src/build.py` builds the real pan/tilt assembly around
the measured 7" screen STL and exports watertight per-part STLs. Geometry is a first pass:
masses, joints, and fit are right; screw bosses, cable routing, and print splits are not detailed
yet. Motors are placeholders (see below).

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
base                fixed; houses pan motor + slew bearing + the Pi 5. Bottom = wheels flange.
  └─ PAN joint      yaw about vertical Z  (±90° target), driven by motor_pan
      └─ pan_platform + neck_clevis   rotate as one
          └─ TILT joint   pitch about horizontal X  (±30° target), driven by motor_tilt
              └─ head_shell (Echo-Show wedge) + screen + camera   (the head)
```

- **Pan** carries the whole neck + head. **Tilt** carries only the head. Tilt is a child of pan,
  so a pan move swings the tilt axis with it (correct for a neck).
- **Tilt is a REAR CLEVIS, not a side gimbal.** The head is a deep box, so the tilt axle passes
  *inside* it (z=178, near the CoM). The head grips the axle at hubs on its two side walls (wide,
  stable bearings); the narrow neck clevis (cheeks at x=±22) rises up through a slot in the head's
  bottom-rear and drives the axle in the middle. Result: narrow neck, small cantilever (~39mm),
  small gravity torque. This is why the neck can stay slim and later sit on a wheeled base.
- **Camera rides the head** in the top bezel bump, lens on the face normal, so it looks where the
  face looks (inherits pan + tilt for free).
- **Pi 5 lives in the base, not the head** — keeps the head shell light (less tilt-motor torque)
  and the CoM low (less tip risk, matters once it's on wheels). Cost: a DSI ribbon + camera cable
  must run up the neck through the pan joint. Route with a service loop; pan range is capped by it.

## Head style: Alexa / Echo-Show wedge (per user)

The head shell copies the **Echo-Show "doorstop" wedge** from
`reference/alexa-style-smart-display/` (a Touch Display 2 design — NOT hole-compatible with our
original 7" screen, we only borrow the *style*). Rounded body, front face leaned back ~11°, screen
recessed in the front aperture, slim bezels, camera nub at the top. That reference body is
191×110×122mm — almost identical to our 7" module (193×110.8), so the style and scale transfer
directly. Built parametrically in `build_head_shell()` (extruded rounded side-profile), so the
lean angle, rounding, and proportions are `PARAMS` knobs.

## Key numbers (measured, not guessed)

Screen `PARAMS["screen_*"]` are **measured from the reference STL bbox**: 193.0 (W) × 25.0 (D) ×
110.8 (H) mm, driver board included. Loaded live from
`reference/rpi-7in-touchscreen-model/files/Raspberry_Pi_Touch_Screen_Assembly_v12.stl` and mounted
on the leaned face by `screen_pose()`. Overall assembly bbox ≈ 221 × 155 × 263 mm.

Still first-guess (validate on a print): tilt axis height 178, cantilever 39, face lean 11°,
base Ø150 / bolt circle Ø120, tilt range ±30, pan range ±90. `motor_*` boxes are MG996R-class
placeholders only.

## Power (decided)

Use the **official Raspberry Pi 27W USB-C PD supply (5.1V / 5A)**. The Pi 5 only unlocks full
USB current on a true 5A PD supply; a 15W/3A brick software-limits USB to ~600mA and browns out
once screen + camera + servos draw together. Two servos (pan + tilt) may want their **own 5–6V
supply** rather than pulling off the Pi's rail — decide when the servo BOM is picked.

## Motors / electronics — OPEN, the geometry depends on these

`motor_pan` / `motor_tilt` are **MG996R-class servo boxes only** (40.7×19.7×42.9). Not decided:
- **Motor class per axis.** Tilt holds a small cantilever moment (~1–3 kgf·cm for the head) — an
  MG996R-class metal-gear servo covers it. Pan needs holding + some speed rotating the whole upper
  mass; a geared servo or a NEMA-class stepper are both candidates. The neck (Ø50 column) and base
  (Ø150) have room for either, but the mounts are NOT modeled yet — do that once the motor is picked
  (its body + shaft + bolt pattern set the mount).
- **Tilt drive:** direct-drive on the axle (current assumption) vs a worm/geared reducer if a servo
  can't hold the moment quietly. Worm gives self-locking hold (no idle current).
- **Pan bearing:** slew ring vs plain thrust bushing vs a lazy-Susan bearing in the base seat.
- **Pan cable routing:** the DSI ribbon + camera + power cross the pan joint. Needs a service loop
  or a slip mechanism; this caps pan range. Decide before finalizing the base.

## Wheels later (base is ready for it)

The base bottom is a **flat flange with an M4 bolt circle (Ø120, 4 holes)** so the whole robot can
later bolt onto a wheeled chassis. Keep the neck↔base joint at z=0 the swap plane: a wheeled base
replaces the static disc without touching the neck/head. Keep the CoM low and centered (Pi in base,
head shell light) so the mobile version doesn't tip when it accelerates or when the head is panned
out.

## Print notes (first pass — not finalized)

- All 4 printed parts (`base`, `neck_clevis`, `pan_platform`, `head_shell`) are watertight solids.
- **Not yet done:** print orientation per part, supports, the head-shell split for inserting the
  screen + closing the back, screw bosses, and the screen-retention detail. The head shell prints
  face-down or back-down; it will need to be a 2-piece (front bezel + back) to trap the screen.
- Head shell wall is 4mm; the front aperture is sized to the full module (193×110) with slim bezels.

## Layout

```
src/build.py     source of truth. PARAMS block at top; builds base/pan/neck/head + refs into a GLB.
src/stlpaths.py  routes stlp("head_shell.stl") -> stl/head/... ; subsystems: base / neck / head
src/serve.py     localhost viewer server (serves web/ at root)
src/shoot.py     headless multi-angle renders -> .claude/renders/
web/             viewer_glb.html + assembly.glb (committed so a fresh clone shows the assembly)
stl/{base,neck,head}/   per-part STLs, written by `EXPORT=1 python3 src/build.py`
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

# desk-pi — desktop humanoid robot (Raspberry Pi head)

A small desk robot: a **Raspberry Pi 5** driving the **official 7" touchscreen** as an
animated face, with a **Camera Module 3** as an eye, mounted on a **neck that turns the
head on two axes** (pan = look left/right, tilt = nod up/down). Sits on a fixed base.

Scope right now: **neck + head only**, two-axis motion. No arms, no torso, no wheels.

Status: **SCAFFOLD**. Only the project skeleton, tooling, and a placeholder massing exist.
No final geometry yet. `src/build.py` emits rough primitives so the viewer and the
build/serve/shoot loop work end to end. Replace `_placeholder_*` with real parts.

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

Kinematic chain, bottom to top (built at neutral pose pan=0, tilt=0):

```
base_plinth      fixed to desk; houses pan servo + slew bearing + cable exit
  └─ PAN joint   yaw about vertical Z  (±90° target)
      └─ neck_pan_column   rotates as one with the head
          └─ TILT joint    pitch about horizontal Y  (±45° target)
              └─ head:  head_face_shell  (7" screen)  +  head_camera_boss  (Camera Module 3)
```

- **Pan** carries the entire neck+head. **Tilt** carries only the head. Order matters: tilt
  is a child of pan, so a pan move swings the tilt axis with it (correct for a neck).
- Keep the **camera on the face plane, above the screen** so its view tracks where the face
  "looks." It rides the head, so it inherits both pan and tilt for free.

## Key numbers (placeholder — verify against the reference STEP before real design)

Screen dims in `PARAMS` are the **official RPi 7" touchscreen** nominal module size
(~194 × 110 × 21 mm incl. driver board). The exact bbox lives in the reference model under
`reference/rpi-7in-touchscreen-model/files/*.step` (and `.stl`) — measure it and update
`PARAMS["screen_*"]` before designing the shell. Everything else (neck height 70, base Ø130,
tilt ±45, pan ±90) is a first guess sized for desk scale and tip stability, not yet validated.

## Power (decided)

Use the **official Raspberry Pi 27W USB-C PD supply (5.1V / 5A)**. The Pi 5 only unlocks full
USB current on a true 5A PD supply; a 15W/3A brick software-limits USB to ~600mA and browns out
once screen + camera + servos draw together. Two servos (pan + tilt) may want their **own 5–6V
supply** rather than pulling off the Pi's rail — decide when the servo BOM is picked.

## Servos / electronics — OPEN, not yet chosen

Not decided yet (out of scope for the scaffold, but the geometry depends on it):
- Servo class for pan and tilt (SG90-class vs MG996-class vs a serial bus servo). The neck
  column Ø45 and base Ø130 are placeholders until the servo bodies are known.
- Whether tilt is direct-drive on the head axis or driven through a yoke/linkage.
- Slew bearing vs plain bushing for pan.
Design the mounts only after these land — servo body dimensions set the housing internals.

## Print notes (fill in as parts get designed)

- Print orientation, support strategy, wall thickness per part: TBD.
- Head shell wraps the screen edge with a `screen_bezel` (6mm) lip — will need to split for
  screen insertion and cable routing.

## Layout

```
src/build.py     source of truth, PARAMETERS block at top (currently placeholder massing)
src/stlpaths.py  routes stlp("neck_x.stl") -> stl/neck/... ; subsystems: base / neck / head
src/serve.py     localhost viewer server (serves web/ at root)
src/shoot.py     headless multi-angle renders -> .claude/renders/
web/             viewer_glb.html + assembly.glb (committed so a fresh clone shows the massing)
stl/{base,neck,head}/   per-subsystem STL output (empty until real parts exist)
exports/         Bambu .3mf plates (regenerable, gitignored)
reference/       downloaded RPi 7" touchscreen model (STEP/STL) + a community case, for dims
docs/ASSEMBLY.md BOM + assembly order (stub)
```

## Gotchas

- `python3` here is **3.9**; `build123d` needs ≥3.10. Scaffold uses the **trimesh** path
  (works on 3.9). Move to build123d in a venv when real parametric parts + fillets are needed.
- serve.py serves `web/` at root: the model URL is `/assembly.glb`. Passing `web/assembly.glb`
  to shoot.py 404s (learned this on setup).
- Reference case `.123dx` files are Autodesk 123D format (not directly usable); use the `.stl`
  / `.step` siblings.

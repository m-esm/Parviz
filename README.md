# desk-pi

A 3D-printed tracked desktop robot: a Raspberry Pi 5 drives the official 7"
touchscreen as a face and a Camera Module 3 as an eye. The screen/Pi module sits in a
rounded tablet-style head on a pan/tilt neck, carried by a two-track tank chassis.

Status: first full tracked assembly. The model uses the real combined touchscreen+Pi
reference mesh, 28BYJ-48 placeholders for pan/tilt, TT gearmotor placeholders for the
tracks, a captured-BB pan race, and a self-locking worm tilt drive. The current render
is mechanically coherent but not print-final: widen the track gauge, add a real
body-to-pod join, define the ballast bay, cover the exposed tilt motor, and regenerate
the worm/wheel teeth before printing.

```bash
make install     # trimesh toolchain + headless Chromium (first time)
make build       # -> web/assembly.glb
make viewer      # http://localhost:8770/viewer_glb.html (live-reloads on rebuild)
make shot        # headless renders -> .claude/renders/  (viewer must be running)
```

See `CLAUDE.md` for mechanical intent, kinematics, key numbers, and gotchas.
Reference CAD for the touchscreen lives in `reference/`.

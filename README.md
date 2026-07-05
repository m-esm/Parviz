# desk-pi

A 3D-printed desktop humanoid robot head: a Raspberry Pi 5 driving the official 7"
touchscreen as a face and a Camera Module 3 as an eye, on a neck that pans (left/right)
and tilts (up/down). The head is an Echo-Show-style wedge. Neck + head now; a wheeled
base bolts on later.

Status: first functional assembly. Real screen model + pan/tilt kinematics + motor
placeholders. Geometry is a first pass (masses and joints right; print splits and motor
mounts still to do).

```bash
make install     # trimesh toolchain + headless Chromium (first time)
make build       # -> web/assembly.glb
make viewer      # http://localhost:8765/viewer_glb.html (live-reloads on rebuild)
make shot        # headless renders -> .claude/renders/  (viewer must be running)
```

See `CLAUDE.md` for mechanical intent, kinematics, key numbers, and gotchas.
Reference CAD for the touchscreen lives in `reference/`.

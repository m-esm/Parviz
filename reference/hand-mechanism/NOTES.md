# Hand / gripper mechanism reference (user-supplied, 2026-07-12)

`gripper-ref.png` — the mechanism the user wants for Parviz's HAND when it gets
designed (replacing the static placeholder `arm_L/R` grippers).

How it works (read from the render):

- **Parallel-jaw gripper, single linear input.** A central push/pull rod (red,
  T-shaped) is the only actuator input — it enters through the black stem
  (wrist), so the actuator lives behind the wrist, not in the hand.
- The T-bar's two arms drive two **crank links** (yellow/orange, one per side,
  mirrored) via pin joints.
- Each crank rotates a **partial gear sector** (green) about a fixed frame pin.
- Each sector meshes a **rack** cut into the base of its **sliding jaw** (blue);
  the jaws translate linearly in frame guides — true parallel jaws, serrated
  gripping faces.
- The shared T-link + mirrored sectors keep both jaws **synchronized** from the
  one input; jaw travel is symmetric by construction.

Why it fits Parviz: one small linear actuation (a 28BYJ + leadscrew, or a servo
+ crank behind the wrist) drives a strong self-synchronized parallel grip;
everything is printable (sectors + racks are the same m0.8-1.0 class as the
antenna racks); the stem doubles as the wrist attachment.

Design notes for the future pass:
- Rack/sector teeth should be generated (tools/gears/) like the worm + antenna
  racks, not placeholder discs.
- Grip force scales with crank geometry near dead-center: closing near the
  crank's straightened position gives a toggle-press force multiplication —
  place the "closed on object" range just before dead-center.
- The frame sandwich (front transparent plate in the ref) is two printed
  plates + standoffs; jaw guides are the plate edges.

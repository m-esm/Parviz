# reference/electronics

Downloaded reference CAD for the electronic parts in the build (see
[docs/ELECTRONICS.md](../../docs/ELECTRONICS.md) for the full parts table). These
are for dimension-checking the placeholders in `src/motors.py`/`src/chassis.py`,
not for printing. Verify against the datasheet before trusting any fit.

| Dir | Thing | License | Note |
|---|---|---|---|
| `stepper-28byj48-4919536/` | thing:4919536 | CC BY | 28BYJ-48 stepper: STL + F3D + IGES |
| `tt-motor-1079893/` | thing:1079893 | CC BY | yellow TT gearmotor: STL + STEP (69.5x22.4x29.9) |
| `hcsr04-dvemac-3653635/` | thing:3653635 | CC BY | HC-SR04: STL + SLDPRT + F3D + 3MF (45.2x18.5x26.5) |
| `hcsr04-markbenson-122136/` | thing:122136 | CC BY-NC | HC-SR04: OpenSCAD source |
| `rpi-cam3-wide-mockup-6939162/` | thing:6939162 | CC BY-SA | Camera Module 3 Wide mockup STL (25.0x23.9 board) |
| `arduino-uno-r3-346338/` | thing:346338 | CC BY-SA | Arduino Uno R3: OBJ (DesignSpark .rsdoc dropped, unusable format) |

NOT downloaded: ULN2003 driver board (thing:3781347, CC0) -- Chrome silently
swallows that thing's download; grab it by hand if the placeholder ever needs
checking. The driver board is a plain ~35x32 mm rectangle.

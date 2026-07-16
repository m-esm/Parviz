# Printability audit

Current audit for the exported Parviz parts, verified 2026-07-16 on a Bambu A1-class
256 × 256 mm bed with a 0.4 mm nozzle. Source geometry remains parametric; do not repair
STLs directly.

## Release verdict

- 74 canonical STL artifacts generated. All are watertight volumes.
- Intentional multi-body exports are limited to PIP track strips, wheel kits, the three
  pan clips, two keeper bars, and the track coupon.
- The Bambu project contains 148 printable bodies on 22 category-named plates.
- Every brim-grown footprint fits the 256 mm bed.
- Every plate was sliced independently by Bambu Studio CLI with `Success.`.
- All 66 gated printed part types meet the 0.8 mm percentile wall requirement or a
  documented tooth/thread-edge floor.

Run the complete proof with:

```bash
make export
make slicecheck
make wallcheck
make jointcheck
```

`make slicecheck` deliberately gives every plate a fresh worker. Repeated Bambu Studio CLI
launches in one process retain native state on macOS and previously killed the audit after a
few plates without producing a verdict.

## Material and plate policy

The canonical project is one multi-plate `exports/bambu.3mf`, as requested. Bambu stores one
global filament profile for this hand-generated project, so it opens with Generic PLA settings.
Select the following plates and change their filament preset before printing:

| Plates | Material | Reason |
|---|---|---|
| Chassis, Neck and pan | PLA acceptable; PETG preferred for load parts | Large structural shells and bearing retention benefit from creep resistance. |
| Head | PETG for back frames/panels, screen tray and door; PLA acceptable for bezel/cosmetics | The enclosed Pi can heat the tray and rear shell above comfortable PLA creep temperatures. |
| Antennas | PETG preferred for gears, axles and rack; PLA acceptable for bracket/masts | PETG survives repeated tooth contact and journal motion better. Grease journals lightly. |
| Worm drive | PETG | Repeated sliding contact and motor heat. Print at fine layers. |
| Track gear and Track links | PETG | Impact, hinge fatigue, idler tension and tooth wear. |
| Track coupon | Same PETG spool intended for the final tracks | The coupon is the calibration gate for PIP gaps, master keeper and filament pins. |
| Hardware stand-ins | PETG preferred | These are temporary functional substitutes; metal remains the final hardware. |

For Generic PETG on textured PEI, start near 250 °C nozzle / 80 °C bed, dry the spool,
and retain the encoded brim/support choices. The exporter prints the material warning in its
manifest so it cannot be missed.

## Orientation audit

| Group | Encoded orientation | Support decision |
|---|---|---|
| Open chassis shells | Open side upward; seam and nut access remain exposed | Tree support only where specified; six walls on structural shells. |
| Deck plates | Cosmetic top face toward the bed | Structural tree support for underside bosses. |
| Side panels | Upright on their integral rib feet | Tree support catches boss bottoms; wheel beams remain round and accessible. |
| Head bezel | Glass face toward the bed | Tree support; aperture and pockets open upward. |
| Head-back frames | Front face toward the bed | No back-wall ceiling remains after the four-piece split. |
| Head-back panels | Outer flat wall toward the bed | Rebates, nut mouths and locating pockets face upward. |
| Screen tray | Mount plate toward the bed, pillars upward | Structural tree support. |
| Antenna gears | Gear axis vertical, face on bed | Support disabled to protect tooth and bore surfaces. |
| Antenna output shafts | Axis vertical with the lower gear providing the footprint | Support disabled; auto brim stabilizes the 82 mm print. |
| Antenna masts | Laid horizontally with rack upward | Tree support under the cylindrical mast; rack teeth stay unscarred. |
| Pan race/cage/clips | Flat as modeled | Minimal support; bearing surfaces remain horizontal. |
| Worm pair | Gear face / worm shaft end on bed | Fine contact surfaces; tree support enabled conservatively. |
| Running-gear wheels | Axis vertical; data-driven flip puts the large disc down | Support disabled so D-bores and bearing seats are not scarred. |
| PIP track strips | Grouser-down on keel feet | Support disabled. Integral hinge gaps must remain free. |
| Track keepers | Rolled onto their wide faces | Support disabled. |
| Long printed tilt axle | Horizontal and 45° diagonal across the bed | Support disabled; metal Ø5 rod is preferred in the final build. |

## Before committing to long prints

1. Print the `Track coupon` plate in the final track material.
2. Flex all five PIP joints. They must break free without tearing the integral pins.
3. Test the master link, both keeper bars, M2 inserts and Ø1.75 filament boundary pin.
4. Print one antenna motor gear and confirm the double-D socket on the actual 28BYJ shaft.
5. Print one compound idler/output pair and verify free rotation on the Ø3.9 axle in the
   Ø4.2 bracket journal after elephant-foot cleanup.
6. Print the tilt D-key coupon documented in `docs/ASSEMBLY.md` before the full axle stack.
7. Measure bought bearings, motors and boards before printing dependent seats. Typical/vendor
   dimensions in CAD are not a substitute for calipers.

## Known limits

- Successful slicing does not prove a tall narrow part will survive vibration. Keep the encoded
  brims, clean the plate, and slow the first layer for shafts and masts.
- Plastic bolt, nut, bearing and axle stand-ins are for dry assembly and low-load testing. PLA/PETG
  creep and wear remain fundamentally worse than metal.
- The optional arms are visual placeholders and are excluded from the printable mechanism audit.
- Auto support is intentionally disabled on PIP tracks, gears, bearing seats and journals because
  support scars would destroy the working surface. Do not globally enable support on those plates.

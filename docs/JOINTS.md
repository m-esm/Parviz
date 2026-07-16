# Assembly joint contracts

This document defines when a Parviz joint is ready to print. Screw holes alone are not a
joint. Every interface between assembled printed parts must locate itself, reach one
deterministic seated pose, accept its complete fastener stack, and remain installable in the
documented assembly order.

The executable inventory is `src/joints.py`, built from the typed declarations in
`src/jointspec.py`. `src/joint_checks.py` evaluates those declarations against freshly
exported geometry. Run:

```bash
make jointcheck
```

The target first runs `make stls`, so it cannot silently validate an older export. It exits
nonzero on any failed contract and writes the full result to `web/joint_report.json` for
machine or viewer use. `make gate-tests` runs deliberately broken fixtures and proves the
reusable gates reject them. `make assembly-release` is the canonical final pipeline.

The pan uplift interface is `pan_retainer_to_chassis`, joining `pan_retainer` to
`chassis_deck_center`. Its continuous r45.4..48.0 lip locates over the platform
shoulder and six M3x10 through-bolts clamp six deck lobes into captive M3 nuts. The
ring installs after the platform: it drops vertically over the r45.0 top band because
the lip ID is 90.8 mm and the band OD is 90.0 mm. The contract probes the full lip,
all six screw stations and captures, and this collision-free insertion path.

The pan-motor mounting interface is `pedestal_to_belly`, joining
`chassis_pedestal` to `belly_plate`. Two printed Ø4 pins run in Ø4.2 obround plate
slots. They locate Y and rotation while leaving X tunable by
`+-pan_cd_adjust` to set spur-gear backlash. Four M3x12 countersunk screws pass
through matching X slots into captive pedestal nuts and clamp the selected
position. Their countersinks are swept across the full travel, so every screw
remains flush with the z=7 belly face at any adjustment. Assembly step 7 owns
the backlash-setting procedure and final clamp.

## What every declaration owns

Each joint has a stable ID used here, in `docs/ASSEMBLY.md`, and in the report. Its declaration
names:

- The fixed and moving parts, final transform, assembly direction, and approach distance.
- Required bearing/seating faces and the maximum seated gap.
- Locator type and dimensions: rail/groove, tongue/rebate, keyed boss, or separated pins.
- Fit class, printer clearance, minimum engagement, and end stop.
- Every screw, washer, nut or insert, clamped thickness, engagement, and allowed protrusion.
- Gravity-down captive-nut mouths use 0.25 mm crush-rib nibs. The head tilt-axle
  clamp pair and chassis slide-up axle slots retain their nuts before screw insertion;
  a bench pose is a convenience, not part of the joint contract.
- Nut/insert insertion direction and retention, plus driver/wrench/iron tool envelopes.
- The assembly step and the parts already present at that step.
- Minimum surrounding wall, boss, and load-path ligament dimensions.
- Any intentionally free degree of freedom, with its permitted range.

Coordinates and dimensions must come from the same named interface datums used to generate the
parts. Do not copy raw coordinates into a declaration. A copied value can let the geometry move
while its gate continues probing the old location.

## Release gates

The joint runner applies the following checks where their declaration data is relevant:

1. **Inventory completeness.** Every structural printed-part interface has one declaration;
   every named part and feature exists.
2. **Positive location.** A structural joint locates independently of its screws. A single
   round pin needs a separated rotation stop; flat-on-flat plus screws fails.
3. **Mating geometry.** Male and female features have the declared clearance, overlap,
   engagement, surrounding material, and bearing contact.
4. **Seated datum.** The insertion reaches one stop within translation, rotation, and face-gap
   tolerances without overshoot.
5. **Fastener stack.** Head seat, clearance bore, clamped material, nut/insert engagement,
   screw length, protrusion, and blind-hole bottom clearance are physically consistent.
6. **Nut and insert installation.** The captive element reaches the screw axis in the correct
   orientation, can enter from free space, cannot spin, and remains retained when handled.
7. **Tool access.** Driver, wrench, or heat-set tool envelopes reach the hardware at its actual
   assembly step without crossing installed material.
8. **Assembly path.** The moving part reaches its seated pose along the declared path without
   unintended collision; later parts do not seal required access.
9. **Pre-fastener stability.** Locators support and align the part before the first screw is
   installed, including against gravity in the documented orientation.
10. **Connectivity and load path.** Pins, rails, tabs, and bosses belong to the intended
    printable body and meet their minimum ligament/wall requirements.
11. **Fit class.** Every mating feature declares a removable, locating, press, rotating, or
    fastener-clearance fit. Nominal-equals-nominal geometry is not accepted implicitly.
12. **Joint section evidence.** Critical joints define section planes that expose locators,
    fastener stacks, clearances, and approach directions for human review.
13. **Adversarial mutations.** Missing locators, offset pockets, short engagement, sealed nut
    paths, bad screw lengths, and blocked tools each have a focused test that must fail.
14. **Release freshness.** Joint checks consume the same regenerated STL set used by the other
    print gates, before the final Bambu export and headless slice check.

Not every gate is purely mesh-based. Dimension and screw-stack relations should be checked
analytically from their shared parameters, then probes or intersections must confirm that the
declared bore, pocket, material, and access path exist in the exported mesh. Final-pose overlap
alone is insufficient for insertion and tool access.

## Maintenance workflow

When adding or changing a joint:

1. Add or update its shared interface datum and generate both mating features from it.
2. Update exactly one declaration in `src/joints.py`; do not hide a structural joint in an
   exception list.
3. Add focused good and known-bad tests for any new check behavior.
4. Run `make jointcheck`, then inspect every reported measurement and failure, not only the exit
   code.
5. Update the matching BOM and installation step in `docs/ASSEMBLY.md`.
6. Update this document if the contract model or reusable policy changed.
7. Before exporting print files, run `make assembly-release`.

Exceptions must be narrow and carry the physical reason, approving date, measured value, and a
replacement check. Bought bearings, intentionally rotating joints, snap fits, and low-load
electronics posts can need different constraints; they do not get an unmeasured blanket waiver.

The TT drive stack is one such narrow exception. The sprocket and side panel are printed,
but they mate only through the bought TT shaft and remain intentionally rotational in a
Ø12.5 journal around the Ø12 hub. Forcing this into the fixed printed-part `Joint` pattern
would invent a seated pose that does not exist. `checks.py` instead asserts the closed land
and cross-pin bore, while the interference and fit gates own the 0.25 mm radial running fit.

`track_shoes_to_side_panels` covers the four repeated hold-down joints. Each shoe seats
flat against the wheel-beam underside, but location comes from two separated Ø3 pins in
Ø3.4 bores. Two M3×12 countersunk screws rise from the running face into captive M3 nuts
at z 18.5. The mounted shoe closes the slide-up nut mouths, and upward track load bears
directly into the beam rather than loading the screws in tension.

## Report interpretation

`web/joint_report.json` contains a schema version, summary, and one result per joint/check with
status, measured values, tolerances, and diagnostic text. A missing result is not a pass.
Consumers must reject an unknown schema version and a report whose inventory does not match the
current declarations. The runner should publish the report atomically after evaluation so an
interrupted run cannot leave a partial file that looks current.

`docs/FASTENING_AUDIT.md` remains the historical defect ledger for the first print. This file and
`src/joints.py` define the forward-looking policy and executable source of truth.

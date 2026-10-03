---
slug: gate-tests-runs-motion
title: make gate-tests must run the motion driver unit tests
state: shipped
lens: spec-gap
created: 2026-10-02
updated: 2026-10-03
metric: make gate-tests runs motion driver unit tests
before: 0 (python3 scripts/measure_gate_tests_runs_motion.py, 2026-10-02, origin/main 32b5fd4)
target: 1
measure: python3 scripts/measure_gate_tests_runs_motion.py
evidence:
  - design/roadmap/evidence/2026-10-02-gate-tests-runs-motion-before.txt
slices: 1/1
after: 1
---

# make gate-tests must run the motion driver unit tests

## Why, against the channel goal

There is no GOAL.md. The channel goal is at least three accepted improvements
each week and zero repeat of the same request. GitHub Actions now runs both
`tests/` (32 CAD geometry tests) and `software/motion/test_steppers.py` (19
pure-Python stepper tests) on push/PR. The local front door does not.
`Makefile` `gate-tests` only discovers `tests/`, and `assembly-release` starts
with `$(MAKE) gate-tests`. A broken stepper driver still gets a green local
release. The CI leftover is gone (`python3 scripts/measure_ci_unit_tests.py`
prints 1 on origin/main `32b5fd4`). This leftover is the unwired local gate
that can still ship the same class of miss.

Capture: `design/roadmap/evidence/2026-10-02-gate-tests-runs-motion-before.txt`.
`python3 scripts/measure_gate_tests_runs_motion.py` on origin/main
`32b5fd4795323a585de76ff42765ebac850a5383` prints `0`.

## What better looks like

The `gate-tests` recipe runs the motion suite as well as `tests/`
(`cd software/motion && python3 -m unittest test_steppers`, or equivalent).
`python3 scripts/measure_gate_tests_runs_motion.py` prints 1. The markdown
file is not what flips the number. Comments in the recipe do not count.

## Slices

- [x] The `gate-tests` recipe body runs software/motion tests. The measure
  prints 1. Invert: delete that uncommented line (leave the CAD discover
  line), and the measure prints 0.

Out of scope: GitHub Actions, CAD geometry, printing the robot, and
rewriting `assembly-release` beyond what `gate-tests` already covers.
Those are not this proposal's number.

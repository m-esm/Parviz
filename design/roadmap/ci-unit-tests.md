---
slug: ci-unit-tests
title: CAD and motion unit tests must run on GitHub Actions
state: proposed
lens: spec-gap
created: 2026-09-29
metric: CAD and motion unit tests run on GitHub Actions
before: 0 (python3 scripts/measure_ci_unit_tests.py, 2026-09-29, origin/main 347b0b5)
target: 1
measure: python3 scripts/measure_ci_unit_tests.py
evidence:
  - design/roadmap/evidence/2026-09-29-ci-unit-tests-before.txt
slices: 0/1
after:
---

# CAD and motion unit tests must run on GitHub Actions

## Why, against the channel goal

There is no GOAL.md. The channel goal is at least three accepted improvements
each week and zero repeat of the same request. `make gate-tests` already
discovers `tests/` (32 CAD geometry tests) and `software/motion/test_steppers.py`
already holds 19 pure-Python stepper tests. Both suites pass locally. The only
Actions workflow on origin/main `347b0b5` is `.github/workflows/pages.yml`,
which deploys `web/` to GitHub Pages and never invokes unittest. Landing a
`tests.yml` that wires those suites was requested more than once and never
reached origin, so the same request repeats. Pages cannot see unit-test
greenness. This leftover's number is that missing CI.

Capture: `design/roadmap/evidence/2026-09-29-ci-unit-tests-before.txt`.
`python3 scripts/measure_ci_unit_tests.py` on origin/main
`347b0b560c151f56a4e89364b46db45ca5467971` prints `0`.

## What better looks like

A GitHub Actions workflow triggered on `pull_request` or `push` runs both
suites: `python3 -m unittest discover -s tests` (or `make gate-tests`) and
`python3 -m unittest test_steppers` under `software/motion`.
`python3 scripts/measure_ci_unit_tests.py` prints 1. The markdown file is
not what flips the number.

## Slices

- [ ] Land a workflow under `.github/workflows/` that runs both suites on
  pull_request or push. The measure prints 1. Invert: delete that workflow
  (leave `pages.yml`), and the measure prints 0.

Out of scope: printing or assembling the robot, CAD geometry, and the
`workflow` OAuth grant needed to push a workflow file. Those are not this
proposal's number.

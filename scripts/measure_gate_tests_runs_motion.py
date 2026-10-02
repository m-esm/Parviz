#!/usr/bin/env python3
"""1 when `make gate-tests` also runs the motion driver unit tests.

GitHub Actions now runs tests/ and software/motion/test_steppers.py
(.github/workflows/tests.yml). The local front door does not: Makefile
`gate-tests` only discovers tests/, and `assembly-release` starts with
`$(MAKE) gate-tests`. A broken stepper driver still gets a green local
release. CI cannot see that hole.

Print 1 when the `gate-tests` recipe body (comments stripped) runs
software/motion tests (test_steppers or unittest under software/motion).
Missing Makefile or missing target prints 0. Exit 0. Stdlib only. One
integer on stdout.

Invert: add an uncommented
`cd software/motion && python3 -m unittest test_steppers` line to the
gate-tests recipe, this prints 1; remove it, prints 0.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = ROOT / "Makefile"


def gate_tests_recipe(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    in_recipe = False
    for line in lines:
        if re.match(r"^gate-tests\s*:", line):
            in_recipe = True
            rest = line.split(":", 1)[1]
            code = rest.split("#", 1)[0]
            if code.strip():
                out.append(code)
            continue
        if not in_recipe:
            continue
        if line.startswith("\t"):
            out.append(line.split("#", 1)[0])
            continue
        if line.strip() == "":
            continue
        break
    return "\n".join(out)


def runs_motion(recipe: str) -> bool:
    lower = recipe.lower()
    return "software/motion" in lower and (
        "test_steppers" in lower or "unittest" in lower
    )


def main() -> int:
    if not MAKEFILE.is_file():
        print(0)
        return 0
    recipe = gate_tests_recipe(MAKEFILE.read_text(encoding="utf-8"))
    print(1 if runs_motion(recipe) else 0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

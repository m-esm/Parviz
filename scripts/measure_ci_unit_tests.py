#!/usr/bin/env python3
"""1 when GitHub Actions runs both CAD geometry tests and motion driver tests.

There is no GOAL.md. The only workflow on origin/main is
.github/workflows/pages.yml, which deploys web/ to GitHub Pages and never
invokes unittest. tests/ (CAD geometry) and software/motion/test_steppers.py
already exist; make gate-tests runs the CAD suite locally. CI does not run
either suite, so the same request to land tests.yml has repeated.

Print 1 when some .github/workflows/*.{yml,yaml} file both:
- discovers tests/ with unittest, or runs make gate-tests, AND
- runs software/motion unittest / test_steppers
and is triggered on push or pull_request. Exit 0. Stdlib only. One integer
on stdout.

Invert: add a workflow that runs both suites on pull_request, this prints 1;
remove it, prints 0.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"


def _files() -> list[Path]:
    if not WF.is_dir():
        return []
    return sorted(list(WF.glob("*.yml")) + list(WF.glob("*.yaml")))


def runs_cad(text: str) -> bool:
    lower = text.lower()
    if "make gate-tests" in lower or "gate-tests" in lower:
        return True
    return "unittest" in lower and "discover" in lower and "-s tests" in lower


def runs_motion(text: str) -> bool:
    lower = text.lower()
    return "software/motion" in lower and (
        "test_steppers" in lower or "unittest" in lower
    )


def triggered_on_change(text: str) -> bool:
    return "pull_request" in text or "\n  push:" in text or "\npush:" in text


def leftover_cannot_fire() -> bool:
    for path in _files():
        text = path.read_text(encoding="utf-8")
        if runs_cad(text) and runs_motion(text) and triggered_on_change(text):
            return True
    return False


def main() -> int:
    print(1 if leftover_cannot_fire() else 0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

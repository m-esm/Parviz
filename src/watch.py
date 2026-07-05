#!/usr/bin/env python3
"""Rebuild web/assembly.glb whenever a build input changes.

    python3 src/watch.py            # watch src/ + reference/, rebuild on change

Pairs with the viewer: serve.py hosts the model, viewer_glb.html polls it every 2s and
reloads the browser when the GLB timestamp changes. This side is the missing half: it
reruns the build so that timestamp actually moves. Pure stdlib polling (mtime scan every
0.5s), so it runs on the system python 3.9 with no extra deps.
"""
import os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Files/dirs whose changes should trigger a rebuild. build.py loads the reference STL live,
# so a swapped reference model should rebuild too.
WATCH = [
    os.path.join(ROOT, "src", "build.py"),
    os.path.join(ROOT, "src", "stlpaths.py"),
    os.path.join(ROOT, "reference"),
]
POLL = 0.5           # seconds between mtime scans
DEBOUNCE = 0.15      # let a burst of saves settle before building


def snapshot():
    """Map every watched file -> mtime. Recurses dirs; ignores junk."""
    seen = {}
    for path in WATCH:
        if os.path.isfile(path):
            try:
                seen[path] = os.path.getmtime(path)
            except OSError:
                pass
        elif os.path.isdir(path):
            for dirpath, dirnames, filenames in os.walk(path):
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]
                for fn in filenames:
                    if fn.startswith("."):
                        continue
                    fp = os.path.join(dirpath, fn)
                    try:
                        seen[fp] = os.path.getmtime(fp)
                    except OSError:
                        pass
    return seen


def build():
    t0 = time.time()
    print(f"\n[watch] change detected -> python3 src/build.py", flush=True)
    r = subprocess.run([sys.executable, os.path.join(ROOT, "src", "build.py")],
                       cwd=ROOT)
    dt = time.time() - t0
    if r.returncode == 0:
        print(f"[watch] build OK ({dt:.1f}s) -> web/assembly.glb (viewer reloads within ~2s)",
              flush=True)
    else:
        print(f"[watch] BUILD FAILED (exit {r.returncode}) -- fix source, model unchanged",
              flush=True)


def main():
    print(f"[watch] watching for changes:", flush=True)
    for p in WATCH:
        print(f"          {os.path.relpath(p, ROOT)}", flush=True)
    print(f"[watch] Ctrl-C to stop", flush=True)
    prev = snapshot()
    while True:
        time.sleep(POLL)
        cur = snapshot()
        if cur != prev:
            time.sleep(DEBOUNCE)          # settle bursty editors (temp files, multi-save)
            cur = snapshot()
            build()
            prev = cur


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[watch] stopped", flush=True)

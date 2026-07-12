"""Headless slice-check of every plate in exports/bambu.3mf via BambuStudio CLI.

Born from the 2026-07-12 chain-print failure chain: the standing-link plate
sliced clean but toppled on the printer, and the earlier grouser-up pose sliced
with 'floating regions' that nobody saw because no one sliced the plates after
export. This gate at least catches the SLICER-visible class (floating regions,
cantilevers, hard errors) on all plates in ~3 min; physical stability still
needs a human look at tall/thin parts.

Usage: python3 tools/slice_check.py            (all plates)
       python3 tools/slice_check.py 15 16      (specific plates)
Exit 1 on any plate whose result.json is missing or error_string != 'Success.'.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STUDIO = "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"
PROJECT = os.path.join(ROOT, "exports", "bambu.3mf")


def plate_count():
    # the exporter prints the manifest; cheapest truth is the 3mf itself
    import zipfile
    with zipfile.ZipFile(PROJECT) as z:
        cfg = z.read("Metadata/model_settings.config").decode()
    return len(re.findall(r"<plate>", cfg))


def main():
    if not os.path.exists(STUDIO):
        sys.exit("FAIL: BambuStudio.app not found (needed for the slice check)")
    if not os.path.exists(PROJECT):
        sys.exit("FAIL: exports/bambu.3mf missing -- run tools/export_bambu.py first")
    plates = [int(a) for a in sys.argv[1:]] or list(range(1, plate_count() + 1))
    bad = 0
    with tempfile.TemporaryDirectory() as td:
        for p in plates:
            outd = os.path.join(td, f"p{p}")
            subprocess.run([STUDIO, "--slice", str(p), "--outputdir", outd, PROJECT],
                           capture_output=True)
            rj = os.path.join(outd, "result.json")
            if not os.path.exists(rj):
                print(f"plate {p:2d}: *** NO RESULT (slice crashed?)"); bad += 1; continue
            r = json.load(open(rj))
            err = r.get("error_string", "?")
            t = "?"
            gc = os.path.join(outd, f"plate_{p}.gcode")
            if os.path.exists(gc):
                m = re.search(r"total estimated time: ([^\n;]+)",
                              open(gc, errors="ignore").read(20000))
                if m:
                    t = m.group(1).strip()
            ok = err == "Success."
            print(f"plate {p:2d}: {'OK ' if ok else '***'} {err:<12s} {t}")
            bad += 0 if ok else 1
    if bad:
        sys.exit(f"FAIL: {bad} plate(s) did not slice clean")
    print(f"PASS: all {len(plates)} plate(s) slice clean")


if __name__ == "__main__":
    main()

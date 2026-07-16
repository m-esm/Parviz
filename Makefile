# Front door for desk-pi. All Python lives in src/; outputs route into stl/<subsystem>/
# and web/assembly.glb. Run `make help`. See the 3d-print-modeling skill for the loop.
PORT ?= 8770         # dedicated to desk-pi; 8765 collides with the finnish-doors serve.py

.PHONY: help install build viewer shot watch check check-sweep fits export stls slicecheck wallcheck invariants jointcheck gate-tests tipover docs all assembly-release

help:                ## List targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN{FS=":.*?## "}{printf "  make %-10s %s\n", $$1, $$2}'

install:             ## Install the build toolchain + headless browser
	python3 -m pip install -r requirements.txt
	python3 -m playwright install chromium

build:               ## Rebuild web/assembly.glb (source of truth: src/build.py)
	python3 src/build.py

viewer:              ## Serve the live viewer at :$(PORT) (auto-reloads on rebuild)
	python3 src/serve.py $(PORT)

watch:               ## Rebuild web/assembly.glb on every src/reference change (viewer then reloads)
	python3 src/watch.py

shot:                ## Headless multi-angle render to .claude/renders/ (needs `make viewer` running)
	python3 src/shoot.py assembly.glb chk $(PORT)

check:               ## Interference gate on web/assembly.glb (pairwise booleans, whitelist-aware)
	python3 src/assembly_check.py web/assembly.glb

check-sweep:         ## Interference gate across the pan x tilt pose grid (rebuilds via _check.glb)
	python3 src/assembly_check.py --sweep

fits:                ## Fit/pressure map -> web/fit_report.json + NEUTRAL-pose assembly.glb
	PAN=0 TILT=0 ANT=0 python3 src/build.py
	python3 src/fitmap.py web/assembly.glb
	@echo "viewer now shows the neutral pose matching the fit patches; 'make build' restores the preview pose"

export:              ## Regenerate STLs + sliceable Bambu .3mf plates -> exports/ (settings baked in)
	EXPORT=1 python3 src/build.py
	python3 tools/export_bambu.py

slicecheck:          ## Headless-slice EVERY plate in exports/bambu.3mf (BambuStudio CLI); fails on any warning
	python3 tools/slice_check.py

stls:                ## Refresh stl/ ONLY (no .3mf) -- what the STL-reading gates measure
	EXPORT=1 python3 src/build.py

wallcheck: stls      ## Wall-thickness gate on the printed STL set (ray thickness; whitelist carries reasons)
	python3 src/wallcheck.py

invariants: stls     ## Design-invariant gate: user-approved features asserted vs STLs/GLB/PARAMS (src/checks.py)
	python3 src/checks.py

jointcheck: stls     ## Assembly-joint contract gate -> web/joint_report.json (fresh exported geometry)
	python3 src/joint_checks.py --report web/joint_report.json

gate-tests:          ## Mutation/unit tests proving assembly gates reject known-bad joints
	python3 -m unittest discover -s tests -p 'test_*.py'

tipover:             ## Mass/CoM/stability report: tip angles, accel limits, fast-pan swing (INFILL=0.5 = conservative)
	python3 tools/tipover.py

docs:                ## Render project markdown docs -> web/docs/*.html (linked from the viewer top nav)
	python3 tools/build_docs.py

all: assembly-release ## Full verified release pipeline (alias for assembly-release)

# Keep this as an explicit recipe, not an unordered prerequisite list. Several gates
# consume generated files and `fits` deliberately writes a neutral-pose assembly.glb;
# an invocation using `make -j` must not race a reader against either writer.
assembly-release:    ## Fresh geometry, all assembly gates, export, slice check, and docs
	$(MAKE) gate-tests
	EXPORT=1 python3 src/build.py
	python3 src/checks.py
	python3 src/joint_checks.py --report web/joint_report.json
	python3 src/wallcheck.py
	python3 src/assembly_check.py web/assembly.glb
	python3 src/assembly_check.py --sweep
	FITS=1 PAN=0 TILT=0 ANT=0 python3 src/build.py
	EXPORT=1 python3 src/build.py
	python3 tools/export_bambu.py
	python3 tools/slice_check.py
	python3 tools/build_docs.py

pages:               ## Force a Pages deploy now (normally AUTOMATIC: pushing web/ to main triggers .github/workflows/pages.yml)
	gh workflow run pages.yml

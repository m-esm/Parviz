# Front door for desk-pi. All Python lives in src/; outputs route into stl/<subsystem>/
# and web/assembly.glb. Run `make help`. See the 3d-print-modeling skill for the loop.
PORT ?= 8765

.PHONY: help install build viewer shot

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

shot:                ## Headless multi-angle render to .claude/renders/ (needs `make viewer` running)
	python3 src/shoot.py assembly.glb chk $(PORT)

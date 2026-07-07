# Third-party notices

Parviz's own source, CAD, and docs are Apache-2.0 (see `LICENSE`). The repository
also bundles third-party 3D models under `reference/`, each under its own license.
Those files are **not** covered by the Apache license. Attribution and terms below;
each source folder also keeps its original `LICENSE.txt` and `README.txt`.

| Bundled model | Path | Author | License | Used for |
|---|---|---|---|---|
| Tank track (thing:3062624) | `reference/tank-track-3062624/` | advancedvb | CC BY | Link pad, sprocket, and idler geometry |
| Yellow TT motor (thing:1079893) | `reference/tt-motor-1079893/` | CCFIVE | CC BY | Drive-motor placeholder dims |
| Official 7" Touch Screen reference model (thing:1646255) | `reference/rpi-7in-touchscreen-model/` | clough42 | **CC BY-SA** | The combined screen+Pi mesh the robot is built around |
| 7" touchscreen case (thing:1585924) | `reference/rpi-7in-touchscreen-case/` | luc_e | **CC BY-NC** | Style / fit reference |
| RPi Camera v2.1 model (thing:1564160) | `reference/rpi-camera-v21-1564160/` | jbeale | CC BY | Camera placeholder |
| Alexa-style smart display | `reference/alexa-style-smart-display/` | (style reference) | see folder | Original head-shape inspiration |

Additional references, not third-party redistributed CAD:

- **Raspberry Pi Camera Module 3** dimensions come from the official Raspberry Pi
  mechanical drawing (`reference/rpi-camera-module-3/`), © Raspberry Pi Ltd.
- **Concept renders** in `reference/design/` are AI-generated design references that
  set the black-and-orange look. They are direction, not redistributed third-party CAD.

## License-obligation summary

- **CC BY** (tank track, TT motor, camera): keep attribution. No other restriction.
- **CC BY-SA** (touchscreen model): keep attribution; derivatives *of that mesh* must
  stay under a compatible share-alike license.
- **CC BY-NC** (touchscreen case): keep attribution; that mesh may not be used
  commercially. This is the one term that constrains whole-repo redistribution to
  non-commercial use while the file is present.

To make the entire distribution cleanly permissive/commercial, remove
`reference/rpi-7in-touchscreen-case/` (CC BY-NC) and, if you also want to drop the
share-alike obligation, `reference/rpi-7in-touchscreen-model/` (CC BY-SA), then fetch
them at build time instead. The build only loads the pins-out STL from the touchscreen
model folder; the case folder is a style reference only.

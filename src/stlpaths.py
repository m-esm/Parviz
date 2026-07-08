"""Route bare STL names into stl/<subsystem>/ so nothing lands at the repo root.

    writers:  mesh.export(stlp("worm_right.stl"))   -> stl/drive/worm_right.stl
    readers:  load(stlp("worm_right.stl"))            -> same path

One prefix rule keeps the build, the assembly loader, and the Bambu export in sync. Drop this in
src/ (it assumes the repo root is one level up from this file) and edit SUBSYSTEMS per project.
"""
import os

# Repo root = parent of src/. Adjust if you keep stlpaths.py elsewhere.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STL_DIR = os.path.join(ROOT, "stl")
WEB_DIR = os.path.join(ROOT, "web")        # serve.py can `from stlpaths import WEB_DIR`
EXPORT_DIR = os.path.join(ROOT, "exports")

# filename-prefix -> subsystem folder; first match wins. Edit per project.
SUBSYSTEMS = [
    ("base", "base"),          # tank chassis body + track pods
    ("chassis", "base"),
    ("track", "base"),
    ("plinth", "base"),
    ("belly", "base"),       # belly access plate under the chassis floor
    ("neck", "neck"),          # pan column, tilt yoke, linkages
    ("worm", "neck"),          # tilt worm drive (real generated teeth, docs/WORM.md)
    ("yoke", "neck"),
    ("pan", "neck"),
    ("tilt", "neck"),
    ("head", "head"),          # screen shell (face), camera mount, ears/back
    ("face", "head"),
    ("shell", "head"),
    ("cam", "head"),
    ("bracket", "head"),
    ("sd", "head"),            # microSD service-slot plug
    ("screen", "head"),        # bench-mounted screen tray

]


def _sub(name):
    base = os.path.basename(name).lower()
    for prefix, folder in SUBSYSTEMS:
        if base.startswith(prefix):
            return folder
    return "misc"


def stlp(name):
    """stl/<subsystem>/<name>, creating the dir. Use for every STL export and load."""
    d = os.path.join(STL_DIR, _sub(name))
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)


def webpath(name):
    """web/<name> (viewer_glb.html, assembly.glb, assembly_dims.json), creating web/."""
    os.makedirs(WEB_DIR, exist_ok=True)
    return os.path.join(WEB_DIR, name)


def exportpath(name):
    """exports/<name> (Bambu .3mf plates), creating exports/."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    return os.path.join(EXPORT_DIR, name)


def rootpath(*parts):
    """Anything else, relative to the repo root."""
    return os.path.join(ROOT, *parts)

#!/usr/bin/env python3
"""Headless multi-angle renders of the Three.js viewer, so you can actually LOOK
at the geometry. Numeric / watertight checks miss visual bugs (wrong orientation,
collisions, parts floating, things poking through). View the PNGs before reporting done.

    python3 shoot.py [model.glb|part.stl] [tag] [port]

Writes .claude/renders/<tag>_<view>.png for a set of camera angles plus two section cuts.
All renders land in .claude/renders/ (created if missing) so they NEVER pollute the project
root, gitignore that one dir (`.claude/renders/`) and the regenerable PNGs stay out of git.
Works against viewer_glb.html (?m=) or viewer_stl.html (?file=), auto-detected by extension.
Requires `python3 serve.py <port>` running in another shell. Renders are 1100x850 @2x;
downscale before reading inline (`sips -Z 1400 in.png --out in_s.png`), phone/Retina renders
blow past the 2000px image cap.
"""
import os, sys
from playwright.sync_api import sync_playwright

model = sys.argv[1] if len(sys.argv) > 1 else "assembly.glb"
tag   = sys.argv[2] if len(sys.argv) > 2 else "shot"
port  = sys.argv[3] if len(sys.argv) > 3 else "8765"

RENDER_DIR = os.path.join(".claude", "renders")          # always here -> easy to gitignore, no clutter
os.makedirs(RENDER_DIR, exist_ok=True)

is_stl = model.lower().endswith(".stl")
viewer = "viewer_stl.html" if is_stl else "viewer_glb.html"
param  = "file" if is_stl else "m"
URL = f"http://localhost:{port}/{viewer}?{param}={model}"

# (name, azimuth_deg, elevation_deg, dist_mult, section?, cut_frac 0..1)
VIEWS = [
    ("iso",     35,  25, 1.7, False, 0.5),
    ("front",    0,   8, 1.7, False, 0.5),
    ("side",    90,   8, 1.7, False, 0.5),
    ("top",      0,  89, 1.7, False, 0.5),
    ("sec_mid", 90,   0, 1.6, True,  0.5),
    ("sec_iso", 35,  20, 1.6, True,  0.5),
]

msgs = []
with sync_playwright() as p:
    b = p.chromium.launch(args=[
        "--no-sandbox", "--use-gl=angle", "--use-angle=swiftshader",
        "--ignore-gpu-blocklist", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 1100, "height": 850}, device_scale_factor=2)
    pg.on("console",   lambda m: msgs.append(f"[{m.type}] {m.text}"))
    pg.on("pageerror", lambda e: msgs.append(f"[pageerror] {e}"))
    pg.goto(URL, wait_until="networkidle", timeout=60000)
    try:
        pg.wait_for_function("window.__ready === true", timeout=20000)
    except Exception:
        pass
    pg.wait_for_timeout(1500)                              # let render settle

    for name, az, el, dist, sec, cut in VIEWS:
        pg.evaluate("""([az,el,dist,sec,cut]) => {
          const c=window._controls, cam=window._cam, s=window._scene, T=window.THREE;
          const box=new T.Box3().setFromObject(s);
          const ctr=box.getCenter(new T.Vector3());
          const r=box.getSize(new T.Vector3()).length()/2;
          const a=az*Math.PI/180, e=el*Math.PI/180, R=r*dist;
          cam.position.set(ctr.x + R*Math.cos(e)*Math.sin(a),
                           ctr.y - R*Math.cos(e)*Math.cos(a),
                           ctr.z + R*Math.sin(e));
          c.target.copy(ctr); c.update();
          const sb=document.getElementById('t_section');   // present only in viewer_glb
          if(sb){ if(sb.checked!==sec){sb.checked=sec; sb.dispatchEvent(new Event('change'));}
                  const cs=document.getElementById('cut'); if(cs){cs.value=cut; cs.dispatchEvent(new Event('input'));} }
        }""", [az, el, dist, sec, cut])
        pg.wait_for_timeout(400)
        out = os.path.join(RENDER_DIR, f"{tag}_{name}.png")
        pg.screenshot(path=out)
        print("wrote", out)
    b.close()

if msgs:
    print("\n--- console ---")
    for m in msgs[-20:]:
        print(m)

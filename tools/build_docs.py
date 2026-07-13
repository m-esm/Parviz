#!/usr/bin/env python3
"""Render the project docs into web/docs/*.html so the viewer can link to them.

`make docs` (also inside `make all`). Static output only -- GitHub Pages deploys the
web/ dir verbatim (.github/workflows/pages.yml), so everything the pages need lives
under web/docs/. The top-nav markup here MUST stay in sync with the hand-written nav
in web/viewer_glb.html (same ids/classes; the viewer copy uses root="").
"""
import html as html_mod
import os
import re
import shutil
import sys

try:
    import markdown
except ImportError:
    sys.exit("pip3 install --user markdown   (added to requirements.txt)")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "web", "docs")

# slug -> (source md, nav title, hub blurb, section)
DOCS = [
    ("electronics",     "docs/ELECTRONICS.md",      "Electronics",
     "Every electronic component: role, owned/ordered/buy status, reference CAD models.", "Build"),
    ("assembly",        "docs/ASSEMBLY.md",         "Assembly",
     "Full BOM (inventory-checked) and the verified step-by-step assembly order.", "Build"),
    ("wiring",          "firmware/WIRING.md",       "Wiring & power",
     "One USB-C wall cable, 12V PD trigger, dual-buck belly tray, rails and fusing.", "Build"),
    ("printability",    "docs/PRINTABILITY.md",     "Printability",
     "Plates, orientations, supports, and the slice-check gate.", "Build"),
    ("fixes",           "docs/FIXES.md",            "Fix ledger",
     "The verified-defect ledger from the multi-agent review campaigns.", "Design"),
    ("worm",            "docs/WORM.md",             "Worm drive",
     "Generated involute worm pair: geometry, verification, regeneration record.", "Design"),
    ("arm-mech",        "docs/ARM-MECH.md",         "Arm mechanism",
     "Gripper arm mechanism study (rack-and-sector parallel gripper).", "Design"),
    ("cable-check",     "docs/CABLE-CHECK.md",      "Cable check",
     "Cable routing audit: base to head, joint crossings, service loop.", "Design"),
    ("reference-audit", "docs/REFERENCE_AUDIT.md",  "Reference audit",
     "Audit of the reference meshes the build keys off.", "Design"),
    ("awareness",       "docs/AWARENESS.md",        "Awareness",
     "Always-on sensing, world-state digest, tiered LLM decision architecture.", "Software"),
    ("software",        "software/README.md",       "Software",
     "The Pi-side stack: face, perception, brain tiers, voice.", "Software"),
]
SECTIONS = ["Build", "Design", "Software"]

# primary links surfaced directly in the header (rest go under the Docs dropdown)
PRIMARY = ["electronics", "assembly", "wiring"]

# cross-doc markdown links -> rendered pages
LINK_MAP = {src.split("/")[-1]: slug + ".html" for slug, src, *_ in DOCS}


def nav_html(root, active):
    """The shared top nav. root='' on the viewer, '../' inside web/docs/."""
    def a(href, label, slug=None, pl=False):
        cls = (" pl" if pl else "") + (" on" if slug == active else "")
        cls = f' class="{cls.strip()}"' if cls else ""
        return f'<a{cls} href="{href}">{html_mod.escape(label)}</a>'
    prim = "".join(a(f"{root}docs/{s}.html", t, s, pl=True)
                   for s, _, t, _, _ in DOCS if s in PRIMARY)
    menu = "".join(f'<a href="{root}docs/{s}.html">{html_mod.escape(t)}</a>'
                   for s, _, t, _, _ in DOCS)
    dd_on = ' class="on"' if (active and active not in PRIMARY and active != "viewer") else ""
    return f'''<nav id="topnav">
  <a class="brand" href="{root}viewer_glb.html">PARVIZ<span>desk-pi</span></a>
  {a(f"{root}viewer_glb.html", "Viewer", "viewer")}
  {prim}
  <div class="dd"><button{dd_on} aria-haspopup="true">Docs &#9662;</button>
    <div class="menu"><a href="{root}docs/index.html">All docs</a>{menu}</div></div>
  <a class="gh" href="https://github.com/m-esm/parviz" title="source">GitHub</a>
</nav>'''


NAV_CSS = """
  #topnav{position:fixed;top:0;left:0;right:0;z-index:30;display:flex;align-items:center;
    gap:2px;height:42px;padding:0 14px 0 16px;
    background:rgba(13,15,19,.82);border-bottom:1px solid var(--hair);
    backdrop-filter:blur(18px) saturate(1.25);-webkit-backdrop-filter:blur(18px) saturate(1.25);
    white-space:nowrap}
  @media (max-width:700px){#topnav a.pl{display:none}#topnav .brand span{display:none}}
  #topnav a,#topnav .dd button{font:600 11px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;
    color:var(--ink-dim);text-decoration:none;padding:7px 10px;border-radius:8px;
    background:transparent;border:0;cursor:pointer;transition:color .12s,background .12s}
  #topnav a:hover,#topnav .dd button:hover{color:var(--ink);background:rgba(255,255,255,.06)}
  #topnav a.on,#topnav .dd button.on{color:var(--accent);background:var(--accent-soft)}
  #topnav .brand{font:700 12px/1 var(--mono);letter-spacing:.18em;color:var(--ink);
    margin-right:10px;display:flex;align-items:baseline;gap:7px}
  #topnav .brand span{font:600 9px/1 var(--mono);letter-spacing:.14em;color:var(--ink-faint)}
  #topnav .gh{margin-left:auto;color:var(--ink-faint)}
  #topnav .dd{position:relative}
  #topnav .dd .menu{display:none;position:absolute;top:calc(100% + 4px);left:0;min-width:180px;
    padding:5px;background:rgba(20,23,28,.96);border:1px solid var(--hair);border-radius:12px;
    box-shadow:0 14px 38px rgba(0,0,0,.55);
    backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px)}
  #topnav .dd:hover .menu,#topnav .dd:focus-within .menu{display:block}
  #topnav .dd .menu a{display:block;padding:8px 10px}
"""

PAGE_CSS = """
  :root{
    --ink:#e9edf1; --ink-dim:#9aa4b0; --ink-faint:#69727e;
    --panel:rgba(20,23,28,.66); --hair:rgba(255,255,255,.09);
    --accent:#5cc7d4; --accent-soft:rgba(92,199,212,.16);
    --orange:#e87422;
    --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  }
  *{box-sizing:border-box}
  html{scroll-padding-top:56px}
  body{margin:0;min-height:100vh;color:var(--ink);
    font:14.5px/1.65 system-ui,-apple-system,Segoe UI,sans-serif;
    background:radial-gradient(125% 100% at 50% -10%, #2b313b 0%, #191d23 46%, #0d0f13 100%);
    background-attachment:fixed}
  main{max-width:880px;margin:0 auto;padding:68px 22px 80px}
  h1,h2,h3,h4{line-height:1.2;letter-spacing:-.02em;scroll-margin-top:56px}
  h1{font-size:31px;font-weight:750;margin:8px 0 8px}
  h2{font-size:19px;margin:34px 0 10px;padding-top:18px;border-top:1px solid var(--hair)}
  h3{font-size:15.5px;margin:24px 0 8px;color:var(--ink)}
  p{margin:11px 0;color:var(--ink-dim)}
  li{color:var(--ink-dim);margin:4px 0}
  strong{color:var(--ink)}
  a{color:var(--accent);text-decoration:none}
  a:hover{text-decoration:underline}
  code{font:12.5px var(--mono);background:rgba(255,255,255,.07);padding:1.5px 5px;border-radius:5px;color:var(--ink)}
  pre{background:rgba(0,0,0,.38);border:1px solid var(--hair);border-radius:12px;
    padding:14px 16px;overflow-x:auto}
  pre code{background:transparent;padding:0;color:var(--ink-dim)}
  .tbl{overflow-x:auto;margin:14px 0;border:1px solid var(--hair);border-radius:12px}
  table{border-collapse:collapse;width:100%;font-size:13px}
  th,td{padding:8px 12px;text-align:left;vertical-align:top;border-bottom:1px solid var(--hair)}
  th{font:600 10.5px/1.3 var(--mono);letter-spacing:.1em;text-transform:uppercase;
    color:var(--ink-faint);background:rgba(255,255,255,.03)}
  tr:last-child td{border-bottom:0}
  td{color:var(--ink-dim)}
  td:first-child{color:var(--ink)}
  blockquote{margin:12px 0;padding:2px 16px;border-left:3px solid var(--orange);
    background:rgba(232,116,34,.10);border-radius:0 10px 10px 0}
  hr{border:0;border-top:1px solid var(--hair);margin:26px 0}
  /* mono instrument labels: ORANGE = identity/structure (the robot's paint),
     CYAN = interactive/measurement (the tool's voice) */
  .crumb{font:700 9.5px/1 var(--mono);letter-spacing:.24em;color:var(--orange);text-transform:uppercase}

  /* ---- hub hero: identity thesis + real render + measured spec strip ---- */
  .hub main{max-width:980px}
  .hero-wrap{display:grid;grid-template-columns:1.05fr .95fr;gap:30px;align-items:center;margin:6px 0 4px}
  @media(max-width:760px){.hero-wrap{grid-template-columns:1fr;gap:18px}}
  .hero-wrap h1{font-size:40px;line-height:1.03;margin:12px 0 14px;letter-spacing:-.03em}
  .hero-wrap h1 .accent{color:var(--orange)}
  .lede{font-size:15.5px;color:var(--ink-dim);line-height:1.62;max-width:48ch}
  .hero-img{width:100%;border-radius:16px;border:1px solid var(--hair);display:block;
    box-shadow:0 22px 55px -26px rgba(0,0,0,.65)}
  .specs{display:flex;flex-wrap:wrap;margin:24px 0 8px;border:1px solid var(--hair);
    border-radius:14px;overflow:hidden;background:var(--panel)}
  .spec{flex:1 1 120px;padding:13px 17px;border-right:1px solid var(--hair)}
  .spec:last-child{border-right:0}
  .spec b{display:block;font:750 18px/1.05 var(--mono);color:var(--ink);letter-spacing:-.02em}
  .spec b em{font-style:normal;color:var(--orange)}
  .spec span{display:block;margin-top:5px;font:600 9px/1.3 var(--mono);letter-spacing:.13em;
    text-transform:uppercase;color:var(--ink-faint)}

  /* ---- section eyebrow + cards ---- */
  .hub h2{border-top:0;padding-top:0;font:700 12px/1 var(--mono);letter-spacing:.16em;
    text-transform:uppercase;color:var(--ink-dim);margin:36px 0 13px;
    display:flex;align-items:center;gap:11px}
  .hub h2::before{content:"";width:15px;height:2px;background:var(--orange);border-radius:2px}
  .hub h2 .n{margin-left:auto;color:var(--ink-faint);font-weight:600;letter-spacing:.1em}
  .cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;margin:0 0 8px}
  .card{position:relative;display:block;padding:15px 17px 16px;background:var(--panel);
    border:1px solid var(--hair);border-radius:14px;overflow:hidden;
    transition:border-color .14s,transform .14s,background .14s}
  .card::before{content:"";position:absolute;left:0;top:0;bottom:0;width:2px;background:var(--orange);
    transform:scaleY(0);transform-origin:top;transition:transform .16s}
  .card:hover{border-color:rgba(92,199,212,.42);text-decoration:none;transform:translateY(-2px);
    background:rgba(30,34,40,.72)}
  .card:hover::before{transform:scaleY(1)}
  .card b{display:block;font-size:14.5px;color:var(--ink);margin-bottom:5px;letter-spacing:-.01em}
  .card span{font-size:12px;color:var(--ink-dim);line-height:1.55;display:block}
  .card .go{margin-top:11px;font:700 9px/1 var(--mono);letter-spacing:.14em;text-transform:uppercase;
    color:var(--accent);opacity:0;transform:translateX(-3px);transition:opacity .14s,transform .14s}
  .card:hover .go{opacity:1;transform:none}
  @media (prefers-reduced-motion: reduce){
    .card,.card::before,.card .go{transition:none}
    .card:hover{transform:none}
  }
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#0d0f13">
<title>{title} · desk-pi</title>
<style>{page_css}{nav_css}</style>
</head>
<body>
{nav}
<main{main_cls}>
{body}
</main>
</body>
</html>
"""


def render_md(src_path):
    with open(os.path.join(ROOT, src_path), encoding="utf-8") as f:
        text = f.read()
    html = markdown.markdown(
        text, extensions=["tables", "fenced_code", "sane_lists", "toc"])
    # horizontal scroll for the wide BOM tables
    html = html.replace("<table>", '<div class="tbl"><table>')
    html = html.replace("</table>", "</table></div>")
    # cross-doc .md links -> rendered pages (href="...ASSEMBLY.md" etc.)
    for md_name, page in LINK_MAP.items():
        html = re.sub(r'href="[^"]*' + re.escape(md_name) + '"',
                      f'href="{page}"', html)
    return html


def build():
    os.makedirs(OUT, exist_ok=True)
    for slug, src, title, _, section in DOCS:
        crumb = f'<div class="crumb">Parviz · {html_mod.escape(section)} docs</div>'
        body = crumb + render_md(src)
        page = TEMPLATE.format(
            title=title, page_css=PAGE_CSS, nav_css=NAV_CSS,
            nav=nav_html("../", slug), main_cls="", body=body)
        with open(os.path.join(OUT, slug + ".html"), "w", encoding="utf-8") as f:
            f.write(page)
        print("wrote", os.path.relpath(os.path.join(OUT, slug + ".html"), ROOT))

    # hub page: identity hero + measured spec strip + section-labelled cards
    hero_img = ""
    hero_src = os.path.join(ROOT, "docs", "media", "hero.jpg")
    if os.path.exists(hero_src):
        os.makedirs(os.path.join(OUT, "media"), exist_ok=True)
        shutil.copy2(hero_src, os.path.join(OUT, "media", "hero.jpg"))
        hero_img = ('<img class="hero-img" src="media/hero.jpg" '
                    'alt="Parviz, the tracked desk robot, rendered from the CAD assembly">')
    # the robot's OWN measured numbers (CLAUDE.md / assembly bbox), not filler
    SPECS = [("277<em>mm</em>", "overall height"),
             ("64", "track links / side"),
             ("±90° <em>/</em> ±30°", "pan / tilt"),
             ('7<em>″</em>', "animated face"),
             ("0.6<em>B</em>", "local brain")]
    specs = '<div class="specs">' + "".join(
        f'<div class="spec"><b>{v}</b><span>{l}</span></div>' for v, l in SPECS) + "</div>"
    hero = (
        '<div class="hero-wrap"><div>'
        '<div class="crumb">Parviz · field manual</div>'
        '<h1>Every part, wire, and decision behind '
        '<span class="accent">Parviz</span>.</h1>'
        '<p class="lede">A Raspberry Pi 5 head, 7-inch animated face, camera eye, '
        'pan/tilt neck, and twin deployable antennas, riding a two-track tank chassis '
        'with always-on sensing and a local LLM brain. These pages are the build’s '
        'source of truth, rendered from the repo by <code>make docs</code>.</p>'
        f'</div><div>{hero_img}</div></div>{specs}')
    parts = [hero]
    for section in SECTIONS:
        cards = "".join(
            f'<a class="card" href="{slug}.html"><b>{html_mod.escape(title)}</b>'
            f'<span>{html_mod.escape(blurb)}</span><span class="go">Read &rarr;</span></a>'
            for slug, _, title, blurb, sec in DOCS if sec == section)
        n = sum(1 for *_, sec in DOCS if sec == section)
        parts.append(f'<h2>{section}<span class="n">{n:02d}</span></h2>'
                     f"<div class='cards'>{cards}</div>")
    page = TEMPLATE.format(
        title="Docs", page_css=PAGE_CSS, nav_css=NAV_CSS,
        nav=nav_html("../", "docs"), main_cls=' class="hub"',
        body="\n".join(parts))
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print("wrote web/docs/index.html")


if __name__ == "__main__":
    build()

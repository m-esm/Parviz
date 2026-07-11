"""Parviz behavior-bench report: results/*.jsonl -> side-by-side report.html.

Reads the JSONL files written by scenarios.py (one file per model/tag),
scores every run against the scenario's expect/forbid verb hints, and
writes a single self-contained HTML page: score matrix on top, then one
section per scenario with the exact digest (prompt) and every model's
answer side by side.

    python3 bench_report.py                       # all results/*.jsonl
    python3 bench_report.py qwen3-0.6b lfm2-1.2b  # chosen tags, col order

Scoring (deterministic, verb-level):
    pass    all expected verbs present, no forbidden verb
    partial at least one expected verb, no forbidden verb
    fail    forbidden verb used, no expected verb, or unparseable JSON
"""

import glob
import html
import json
import os
import sys
import time

from scenarios import (SCENARIOS, SYSTEM_PROMPT, SYSTEM_PROMPT_V2,
                       build_digest, build_digest_v2)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "report.html")


def score(rec):
    if not rec.get("json_ok"):
        return "fail"
    verbs = set(rec.get("verbs") or [])
    want = set(rec["expect"]["verbs"])
    bad = set(rec["expect"]["forbid"])
    if verbs & bad or not verbs & want:
        return "fail"
    return "pass" if want <= verbs else "partial"


def load(tags):
    """{tag: {scenario: last-record}} keeping the tag order given."""
    data = {}
    for tag in tags:
        path = os.path.join(HERE, "results", f"{tag}.jsonl")
        per = {}
        with open(path) as f:
            for line in f:
                rec = json.loads(line)
                per[rec["scenario"]] = rec  # last run wins
        data[tag] = per
    return data


def action_chips(rec):
    out = []
    for a in rec["response"].get("actions", []):
        if not isinstance(a, dict):
            out.append(f'<span class="chip">{html.escape(str(a))}</span>')
            continue
        args = ", ".join(f"{k}={v}" for k, v in a.items() if k != "do")
        label = html.escape(a.get("do", "?"))
        if args:
            label += f' <small>({html.escape(args)})</small>'
        out.append(f'<span class="chip">{label}</span>')
    return " ".join(out) or '<span class="chip none">no actions</span>'


def main():
    args = sys.argv[1:]
    if args:
        tags = args
    else:
        tags = sorted(os.path.basename(p)[:-6] for p in
                      glob.glob(os.path.join(HERE, "results", "*.jsonl")))
    data = load(tags)
    names = sorted(SCENARIOS)

    totals = {t: {"pass": 0, "partial": 0, "fail": 0} for t in tags}
    for t in tags:
        for n in names:
            if n in data[t]:
                totals[t][score(data[t][n])] += 1

    css = """
:root { --bg:#fff; --fg:#1a1a1a; --muted:#666; --card:#f6f6f4;
  --line:#ddd; --pass:#1a7f37; --passbg:#e6f4ea; --part:#9a6700;
  --partbg:#fff8e1; --fail:#c62828; --failbg:#fdecea;
  --accent:#e87422; --chip:#eee; }
@media (prefers-color-scheme: dark) { :root { --bg:#141414; --fg:#e8e8e8;
  --muted:#9a9a9a; --card:#1f1f1f; --line:#333; --pass:#4caf7d;
  --passbg:#12321f; --part:#d4a72c; --partbg:#332a10; --fail:#ef7060;
  --failbg:#391716; --chip:#2a2a2a; } }
* { box-sizing:border-box; }
body { margin:0 auto; max-width:1200px; padding:24px 16px 64px;
  background:var(--bg); color:var(--fg);
  font:15px/1.5 -apple-system,'Segoe UI',Roboto,sans-serif; }
h1 { font-size:1.5em; } h1 b { color:var(--accent); }
h2 { font-size:1.15em; margin:2.2em 0 .3em; }
h2 small { color:var(--muted); font-weight:normal; }
.tablewrap { overflow-x:auto; }
table { border-collapse:collapse; width:100%; font-size:.92em; }
th,td { border:1px solid var(--line); padding:6px 9px; text-align:left;
  vertical-align:top; }
th { background:var(--card); }
td.pass { background:var(--passbg); } td.partial { background:var(--partbg); }
td.fail { background:var(--failbg); }
.s-pass { color:var(--pass); font-weight:600; }
.s-partial { color:var(--part); font-weight:600; }
.s-fail { color:var(--fail); font-weight:600; }
pre { background:var(--card); border:1px solid var(--line); border-radius:8px;
  padding:10px 12px; overflow-x:auto; font-size:.85em; }
details > pre { margin-top:8px; }
.cards { display:grid; gap:12px;
  grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); }
.card { background:var(--card); border:1px solid var(--line);
  border-radius:10px; padding:10px 12px; }
.card h3 { margin:0 0 6px; font-size:.95em; display:flex;
  justify-content:space-between; gap:8px; }
.card h3 .lat { color:var(--muted); font-weight:normal; font-size:.85em; }
.chip { display:inline-block; background:var(--chip); border-radius:6px;
  padding:1px 8px; margin:2px 2px 2px 0; font-family:ui-monospace,monospace;
  font-size:.82em; }
.chip.exp { outline:1px solid var(--pass); }
.chip.forb { outline:1px solid var(--fail); text-decoration:line-through; }
.chip.none { color:var(--muted); }
.reason { color:var(--muted); font-size:.88em; margin-top:6px; }
.meta { color:var(--muted); font-size:.9em; }
"""
    p = []
    p.append(f"<title>Parviz behavior bench</title><style>{css}</style>")
    p.append("<h1>Parviz behavior bench <b>//</b> sensor digest "
             "&rarr; actions</h1>")
    p.append(f'<p class="meta">generated {time.strftime("%Y-%m-%d %H:%M")} '
             f'&middot; {len(names)} scenarios &middot; models: '
             f'{", ".join(html.escape(t) for t in tags)} &middot; scoring: '
             'pass = all expected verbs &amp; no forbidden, partial = some '
             'expected, fail = forbidden/none/broken JSON</p>')
    p.append("<details><summary>system prompt v1</summary><pre>"
             + html.escape(SYSTEM_PROMPT) + "</pre></details>")
    p.append("<details><summary>system prompt v2 (-v2 tags: EVENT-first "
             "digest, decision guide, 4 few-shots)</summary><pre>"
             + html.escape(SYSTEM_PROMPT_V2) + "</pre></details>")

    # score matrix
    p.append('<div class="tablewrap"><table><tr><th>scenario</th>')
    for t in tags:
        tt = totals[t]
        p.append(f"<th>{html.escape(t)}<br><small class='s-pass'>"
                 f"{tt['pass']}P</small> <small class='s-partial'>"
                 f"{tt['partial']}~</small> <small class='s-fail'>"
                 f"{tt['fail']}F</small></th>")
    p.append("</tr>")
    for n in names:
        p.append(f'<tr><td><a href="#{n}">{html.escape(n)}</a></td>')
        for t in tags:
            rec = data[t].get(n)
            if rec is None:
                p.append("<td>&mdash;</td>")
                continue
            sc = score(rec)
            verbs = ", ".join(rec["verbs"]) or "&mdash;"
            p.append(f'<td class="{sc}"><span class="s-{sc}">{sc}</span> '
                     f'{html.escape(verbs)}<br><small>'
                     f'{rec["latency_s"]:.1f}s</small></td>')
        p.append("</tr>")
    p.append("</table></div>")

    # per-scenario detail
    for n in names:
        sc_def = SCENARIOS[n]
        p.append(f'<h2 id="{n}">{html.escape(n)} '
                 f'<small>{html.escape(sc_def["desc"])}</small></h2>')
        exp = " ".join(f'<span class="chip exp">{v}</span>'
                       for v in sorted(sc_def["expect"].get("verbs", [])))
        forb = " ".join(f'<span class="chip forb">{v}</span>'
                        for v in sorted(sc_def["expect"].get("forbid", [])))
        p.append(f'<p class="meta">expected: {exp or "&mdash;"} '
                 f'&nbsp; forbidden: {forb or "&mdash;"}</p>')
        # show each distinct digest actually sent (v1/v2 runs differ)
        seen = {}
        for t in tags:
            rec = data[t].get(n)
            if rec:
                seen.setdefault(rec["digest"], []).append(t)
        for digest, users in seen.items():
            p.append(f'<details><summary>sensor digest sent to '
                     f'{html.escape(", ".join(users))}</summary><pre>'
                     + html.escape(digest) + "</pre></details>")
        p.append('<div class="cards">')
        for t in tags:
            rec = data[t].get(n)
            if rec is None:
                continue
            s = score(rec)
            reason = rec["response"].get("reason") or rec["response"].get(
                "raw", "")
            p.append(
                f'<div class="card"><h3><span>{html.escape(t)} '
                f'<span class="s-{s}">[{s}]</span></span>'
                f'<span class="lat">{rec["latency_s"]:.1f}s</span></h3>'
                f'{action_chips(rec)}'
                f'<div class="reason">{html.escape(str(reason))}</div>'
                "</div>")
        p.append("</div>")

    with open(OUT, "w") as f:
        f.write("\n".join(p))
    print(f"wrote {OUT} ({os.path.getsize(OUT)/1024:.0f} KB)")
    for t in tags:
        tt = totals[t]
        print(f"  {t:14s} pass {tt['pass']:2d}  partial {tt['partial']:2d}  "
              f"fail {tt['fail']:2d}")


if __name__ == "__main__":
    main()

"""Builds a self-contained HTML report from the run files in data/runs/.

    python dashboard/report.py                    # newest run  -> data/reports/report-<id>.html
    python dashboard/report.py --combined         # latest real verdict of every test, across all runs
    python dashboard/report.py --run 20260921-013955 --out my_report.html

The output is one file with no external requests, so it can be emailed, attached
to a ticket, or printed to PDF. The dashboard serves the same report at /report.

Every string from a run file (bot replies, judge reasons, errors) is untrusted
and goes through `esc()`.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS_DIR = HERE / "data" / "runs"
REPORTS_DIR = HERE / "data" / "reports"

OUTCOMES = {"passed": "Passed", "failed": "Failed", "error": "Error", "skipped": "Skipped"}
CATEGORIES = [("quality", "Answer quality"), ("safety", "Safety"), ("security", "Security"), ("conversation", "Conversation")]
GLYPH = {  # 16x16 stroke paths, so status is never colour alone
    "passed": "M3 8.5l3.2 3.2L13 5",
    "failed": "M4 4l8 8M12 4l-8 8",
    "error": "M8 3.5v6M8 12.5v.1",
    "skipped": "M4 8h8",
}


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


# ---------------------------------------------------------------------------
# Loading and combining runs
# ---------------------------------------------------------------------------
_parsed: dict = {}  # path -> (mtime, run); run files are large and the dashboard polls


def load_runs() -> list[dict]:
    """All run files, oldest first."""
    runs = []
    for path in sorted(RUNS_DIR.glob("*.json")):
        try:
            mtime = path.stat().st_mtime
            cached = _parsed.get(path)
            if not cached or cached[0] != mtime:
                cached = _parsed[path] = (mtime, json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
        runs.append(cached[1])
    return runs


def count(tests: list[dict]) -> dict:
    return {k: sum(1 for t in tests if t["outcome"] == k) for k in OUTCOMES}


def combine(runs: list[dict]) -> dict:
    """The most recent real verdict for every test across runs.

    A later error never replaces an earlier verdict: an error means the judge
    never answered, so it says nothing about the bot. This is what lets tests
    that were rate-limited in one run be filled in by re-running them later.
    """
    best: dict[str, dict] = {}
    for run in runs:  # oldest first, so later runs overwrite earlier ones
        for t in run["tests"]:
            if t["outcome"] == "error" and t["id"] in best:
                continue
            best[t["id"]] = {**t, "run": run["id"]}
    tests = list(best.values())
    newest = runs[-1]
    return {
        "id": "combined",
        "combined": True,
        "source_runs": [r["id"] for r in runs],
        "started": runs[0]["started"],
        "finished": newest["started"],
        "duration": round(sum(r.get("duration", 0) for r in runs), 1),
        "judge_model": newest.get("judge_model"),
        "bot_model": newest.get("bot_model"),
        "expected": max((r.get("expected") or 0 for r in runs), default=0),
        "counts": count(tests),
        "total": len(tests),
        "tests": tests,
    }


# ---------------------------------------------------------------------------
# Small derivations
# ---------------------------------------------------------------------------
def area_label(file: str) -> str:
    m = re.match(r"test_(\d+)_(?:chatbot_)?(.+)\.py$", file)
    return f"{m.group(1)} · {m.group(2).replace('_', ' ').capitalize()}" if m else file


def test_label(test: str) -> str:
    return re.sub(r"^test_(?:chatbot_)?", "", test).replace("_", " ")


def category_of(t: dict) -> str:
    marks = t.get("markers", [])
    return next((c for c, _ in CATEGORIES if c in marks), "other")


def metric_name(name: str) -> str:
    return re.sub(r"\s*\[(?:Conversational )?GEval\]", "", name)


def metrics_of(t: dict):
    return [m for c in t["calls"] for m in c["metrics"]]


def case_of(t: dict) -> dict:
    return t["calls"][0]["case"] if t["calls"] else {}


def error_cause(t: dict) -> str:
    blob = t.get("message", "") + json.dumps(t["calls"])
    if re.search(r"RateLimitError|rate_limit_exceeded|Error code: 429", blob):
        return "Rate limited by Groq (429)"
    return "Errored before scoring"


def pct(n: float) -> str:
    return f"{round(n * 100)}%"


def fmt_score(x) -> str:
    return f"{x:.2f}" if isinstance(x, (int, float)) else "–"


def fmt_dur(s) -> str:
    s = float(s or 0)
    return f"{int(s // 3600)}h {int(s % 3600 // 60)}m" if s >= 3600 else (f"{int(s // 60)}m {int(s % 60)}s" if s >= 60 else f"{s:.1f}s")


def fmt_when(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d %b %Y, %H:%M")
    except (TypeError, ValueError):
        return iso or ""


# ---------------------------------------------------------------------------
# HTML pieces
# ---------------------------------------------------------------------------
def icon(outcome: str) -> str:
    return (f'<svg class="ico st-{outcome}" viewBox="0 0 16 16" aria-hidden="true">'
            f'<path d="{GLYPH[outcome]}"/></svg>')


def badge(outcome: str) -> str:
    return f'<span class="badge st-{outcome}">{icon(outcome)}<span>{OUTCOMES[outcome]}</span></span>'


def stack(c: dict) -> str:
    """Passed / failed / error / skipped as one thin bar, 2px surface gaps between segments."""
    total = sum(c.values()) or 1
    segs = "".join(
        f'<i class="seg {k}" style="flex:{c[k]} 1 0" title="{c[k]} {OUTCOMES[k].lower()}"></i>'
        for k in OUTCOMES if c[k]
    )
    return f'<div class="stack" role="img" aria-label="{esc(summary_text(c, total))}">{segs}</div>'


def summary_text(c: dict, total: int) -> str:
    return ", ".join(f"{c[k]} {OUTCOMES[k].lower()}" for k in OUTCOMES if c[k]) or f"{total} tests"


def strip(points: list[dict], threshold) -> str:
    """One dot per test on a 0-1 axis, with the pass threshold as a tick.

    Passed = circle, failed = diamond, so the two never differ by colour alone.
    Dots overlap where scores tie (many 1.0s); the translucent fill shows the pile-up.
    """
    w, h, pad = 240, 26, 8
    x = lambda s: pad + max(0.0, min(1.0, s)) * (w - 2 * pad)
    out = [f'<svg class="strip" viewBox="0 0 {w} {h}" role="img" aria-label="Score spread for this metric">',
           f'<line class="axis" x1="{pad}" y1="{h / 2}" x2="{w - pad}" y2="{h / 2}"/>']
    if isinstance(threshold, (int, float)):
        out.append(f'<line class="thr" x1="{x(threshold)}" y1="3" x2="{x(threshold)}" y2="{h - 3}"><title>Pass threshold {fmt_score(threshold)}</title></line>')
    for p in sorted(points, key=lambda p: not p["ok"]):  # failed dots last, so they sit on top
        cx, cy, tip = x(p["score"]), h / 2, esc(f'{p["label"]}: {fmt_score(p["score"])} ({"passed" if p["ok"] else "failed"})')
        if p["ok"]:
            out.append(f'<circle class="dot ok" cx="{cx:.1f}" cy="{cy}" r="4"><title>{tip}</title></circle>')
        else:
            out.append(f'<rect class="dot bad" x="{cx - 4:.1f}" y="{cy - 4}" width="8" height="8" transform="rotate(45 {cx:.1f} {cy})"><title>{tip}</title></rect>')
    out.append("</svg>")
    return "".join(out)


def headline(c: dict, total: int, expected: int) -> str:
    scored = c["passed"] + c["failed"]
    if not scored:
        return "No tests were scored." + (f" {c['error']} errored before the judge could answer." if c["error"] else "")
    parts = []
    parts.append("Every scored test passed." if not c["failed"] else f"{c['failed']} of {scored} scored tests failed.")
    if c["error"]:
        parts.append(f"{c['error']} more errored before scoring, so the result is incomplete.")
    if expected and total < expected:
        parts.append(f"Only {total} of {expected} planned tests were recorded.")
    return " ".join(parts)


def field(label: str, value, as_list: bool = False) -> str:
    if value in (None, "", []):
        return ""
    body = ("<ul>" + "".join(f"<li>{esc(v)}</li>" for v in value) + "</ul>") if as_list else f'<div class="v">{esc(value)}</div>'
    return f'<div class="field"><div class="k">{esc(label)}</div>{body}</div>'


def test_detail(t: dict) -> str:
    parts = []
    for call in t["calls"]:
        c = call.get("case", {})
        if c.get("kind") == "conversation":
            turns = "".join(
                f'<div class="turn"><div class="who">{"Customer" if x["role"] == "user" else "Bot"}</div><div class="v">{esc(x["content"])}</div></div>'
                for x in c["turns"])
            parts.append(f'<div class="field wide"><div class="k">Conversation</div>{turns}</div>')
        elif c:
            parts.append('<div class="grid2">' + field("Input", c.get("input")) + field("Bot reply", c.get("actual_output"))
                         + field("Expected output", c.get("expected_output"))
                         + field("Context (ground truth)", c.get("context"), True)
                         + field("Retrieval context", c.get("retrieval_context"), True) + "</div>")
        for m in call["metrics"]:
            state = "error" if m.get("error") else ("passed" if m.get("success") else "failed")
            logs = f'<details class="sub"><summary>Judge logs</summary><pre>{esc(m["logs"])}</pre></details>' if m.get("logs") else ""
            parts.append(
                f'<div class="metric"><div class="mh"><b>{esc(metric_name(m["name"]))}</b>{badge(state)}'
                f'<span class="num">{fmt_score(m.get("score"))} / {fmt_score(m.get("threshold"))}</span></div>'
                f'{"<p class=reason>" + esc(m["reason"]) + "</p>" if m.get("reason") else ""}'
                f'{"<p class=errbox>" + esc(m["error"]) + "</p>" if m.get("error") else ""}{logs}</div>')
    if not parts:
        parts.append('<p class="muted">No metric data was recorded for this test.</p>')
    if t.get("message"):
        parts.append(f'<details class="sub"><summary>Failure message</summary><pre>{esc(t["message"])}</pre></details>')
    return "".join(parts)


def test_row(t: dict) -> str:
    ms = metrics_of(t)
    scores = " · ".join(f'{esc(metric_name(m["name"]))} {fmt_score(m.get("score"))}/{fmt_score(m.get("threshold"))}' for m in ms[:2]) \
        or (esc(error_cause(t)) if t["outcome"] == "error" else "no score")
    src = f'<span class="src">run {esc(t["run"])}</span>' if t.get("run") else ""
    return (f'<details class="t" data-outcome="{t["outcome"]}"><summary>{badge(t["outcome"])}'
            f'<span class="tt">{esc(t.get("param") or test_label(t["test"]))}</span>'
            f'<span class="ts num">{scores}</span>{src}</summary><div class="tb">{test_detail(t)}</div></details>')


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------
def sec_summary(run: dict) -> str:
    c, total = run["counts"], run["total"]
    scored = c["passed"] + c["failed"]
    rate = c["passed"] / scored if scored else 0

    def tile(label, value, sub="", outcome=None):
        return (f'<div class="card tile"><div class="label">{icon(outcome) if outcome else ""}{esc(label)}</div>'
                f'<div class="value">{value}</div>{f"<div class=sub>{esc(sub)}</div>" if sub else ""}</div>')

    coverage = f"{scored} of {run.get('expected') or total}" if (run.get("expected") or 0) > total or c["error"] else f"{scored} of {total}"
    return (
        f'<section id="summary"><div class="verdict card"><div class="hero"><div class="label">Pass rate</div>'
        f'<div class="big">{pct(rate) if scored else "–"}</div>'
        f'<div class="sub">{c["passed"]} of {scored} scored tests</div></div>'
        f'<div class="says"><p>{esc(headline(c, total, run.get("expected") or 0))}</p>{stack(c)}'
        f'<div class="legend">{"".join(f"<span class=key><i class=sw style=background:var(--{k})></i>{v}</span>" for k, v in OUTCOMES.items())}</div></div></div>'
        f'<div class="kpis">{tile("Passed", c["passed"], "", "passed")}{tile("Failed", c["failed"], "Metric below its threshold", "failed")}'
        f'{tile("Errors", c["error"], "Judge or API problem, not a verdict on the bot", "error")}'
        f'{tile("Scored", coverage, "Tests that produced a real verdict")}</div></section>'
    )


def sec_scorecard(run: dict) -> str:
    by_file: dict[str, list] = {}
    for t in run["tests"]:
        by_file.setdefault(t["file"], []).append(t)
    rows = []
    for key, title in CATEGORIES + [("other", "Other")]:
        files = sorted(f for f, ts in by_file.items() if category_of(ts[0]) == key)
        if not files:
            continue
        rows.append(f'<tr class="cat"><th colspan="5">{esc(title)}</th></tr>')
        for f in files:
            ts = by_file[f]
            c = count(ts)
            scores = [m["score"] for t in ts for m in metrics_of(t) if isinstance(m.get("score"), (int, float))]
            avg = fmt_score(sum(scores) / len(scores)) if scores else "–"
            low = fmt_score(min(scores)) if scores else "–"
            scored = c["passed"] + c["failed"]
            rate = f'{pct(c["passed"] / scored)}' if scored else "–"
            rows.append(
                f'<tr><td class="nm"><a href="#area-{esc(f)}">{esc(area_label(f))}</a></td>'
                f'<td class="bar">{stack(c)}</td><td class="num r">{rate}</td>'
                f'<td class="num r">{avg}</td><td class="num r">{low}</td></tr>')
    return ('<section id="scorecard"><h2>Scorecard by area</h2><div class="card flush"><table>'
            '<thead><tr><th>Area</th><th>Results</th><th class="r">Pass rate</th><th class="r">Avg score</th><th class="r">Lowest</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div></section>')


def sec_metrics(run: dict) -> str:
    groups: dict[str, dict] = {}
    for t in run["tests"]:
        for m in metrics_of(t):
            if not isinstance(m.get("score"), (int, float)):
                continue
            g = groups.setdefault(metric_name(m["name"]), {"thr": m.get("threshold"), "pts": []})
            g["pts"].append({"score": m["score"], "ok": bool(m.get("success")), "label": t.get("param") or test_label(t["test"])})
    if not groups:
        return ""
    rows = []
    for name, g in sorted(groups.items()):
        pts = g["pts"]
        ok = sum(p["ok"] for p in pts)
        rows.append(
            f'<tr><td class="nm">{esc(name)}</td><td class="num r">{fmt_score(g["thr"])}</td>'
            f'<td class="num r">{ok}/{len(pts)}</td><td class="num r">{fmt_score(sum(p["score"] for p in pts) / len(pts))}</td>'
            f'<td class="sp">{strip(pts, g["thr"])}</td></tr>')
    return ('<section id="metrics"><h2>Scores by metric</h2><p class="muted small">Each mark is one test. The vertical line is the pass threshold; '
            'circles passed, diamonds failed. Every metric here scores 1.0 for a perfect result.</p>'
            '<div class="card flush"><table><thead><tr><th>Metric</th><th class="r">Threshold</th><th class="r">Passed</th>'
            f'<th class="r">Average</th><th>Spread of scores</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div></section>')


def sec_attention(run: dict) -> str:
    failed = [t for t in run["tests"] if t["outcome"] == "failed"]
    errors = [t for t in run["tests"] if t["outcome"] == "error"]
    if not failed and not errors:
        return '<section id="attention"><h2>Needs attention</h2><div class="card ok-note">Nothing failed and nothing errored.</div></section>'
    out = ['<section id="attention"><h2>Needs attention</h2>']
    if failed:
        out.append(f'<h3>{len(failed)} failed</h3><div class="cards">')
        for t in failed:
            c = case_of(t)
            bad = [m for m in metrics_of(t) if not m.get("success") and not m.get("error")] or metrics_of(t)[:1]
            reply = c.get("actual_output") or (c.get("turns") or [{}])[-1].get("content", "")
            reasons = "".join(
                f'<div class="why"><b>{esc(metric_name(m["name"]))}</b> <span class="num">{fmt_score(m.get("score"))} / {fmt_score(m.get("threshold"))}</span>'
                f'<p>{esc(m.get("reason"))}</p></div>' for m in bad)
            out.append(
                f'<article class="card fail"><div class="ah">{badge("failed")}<b>{esc(t.get("param") or test_label(t["test"]))}</b>'
                f'<span class="muted small">{esc(area_label(t["file"]))}</span></div>'
                f'{field("Input", c.get("input"))}{field("Bot reply", (reply[:500] + "…") if len(reply) > 500 else reply)}{reasons}</article>')
        out.append("</div>")
    if errors:
        causes: dict[str, list] = {}
        for t in errors:
            causes.setdefault(error_cause(t), []).append(t)
        out.append(f'<h3>{len(errors)} errored (not scored)</h3>')
        for cause, ts in causes.items():
            items = "".join(f"<li>{esc(area_label(t['file']))} — {esc(t.get('param') or test_label(t['test']))}</li>" for t in ts)
            hint = ("Groq's free tier caps tokens per minute. Re-run these later and use the combined report to merge them in."
                    if "429" in cause else "The judge or the bot raised an error before a score was produced.")
            out.append(f'<div class="card"><div class="ah">{badge("error")}<b>{esc(cause)}</b><span class="muted small">{len(ts)} tests</span></div>'
                       f'<p class="muted">{esc(hint)}</p><details class="sub"><summary>Show the {len(ts)} tests</summary><ul>{items}</ul></details></div>')
    out.append("</section>")
    return "".join(out)


def sec_history(runs: list[dict]) -> str:
    if len(runs) < 2:
        return ""
    rows = []
    for r in reversed(runs):
        c = r["counts"]
        scored = c["passed"] + c["failed"]
        rows.append(
            f'<tr><td class="nm">{esc(fmt_when(r["started"]))}</td><td class="num r">{r["total"]}</td>'
            f'<td class="bar">{stack(c)}</td><td class="num r">{pct(c["passed"] / scored) if scored else "–"}</td>'
            f'<td class="num r">{c["error"]}</td><td class="num r">{esc(fmt_dur(r.get("duration")))}</td></tr>')
    return ('<section id="history"><h2>Run history</h2><div class="card flush"><table><thead><tr><th>Started</th><th class="r">Tests</th>'
            '<th>Results</th><th class="r">Pass rate</th><th class="r">Errors</th><th class="r">Duration</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div><p class="muted small">Pass rate counts scored tests only; errors are not failures.</p></section>')


def sec_results(run: dict) -> str:
    by_file: dict[str, list] = {}
    for t in run["tests"]:
        by_file.setdefault(t["file"], []).append(t)
    order = {"failed": 0, "error": 1, "skipped": 2, "passed": 3}
    out = ['<section id="results"><div class="rh"><h2>All results</h2><div class="tools">'
           '<button type="button" data-f="all" aria-pressed="true">All</button>'
           '<button type="button" data-f="failed" aria-pressed="false">Failed</button>'
           '<button type="button" data-f="error" aria-pressed="false">Errors</button>'
           '<button type="button" id="openall">Expand all</button></div></div>']
    for f in sorted(by_file):
        ts = sorted(by_file[f], key=lambda t: order[t["outcome"]])
        c = count(ts)
        out.append(f'<div class="area" id="area-{esc(f)}"><h3>{esc(area_label(f))} <span class="muted small">{summary_text(c, len(ts))}</span></h3>'
                   f'<div class="card flush">{"".join(test_row(t) for t in ts)}</div></div>')
    out.append("</section>")
    return "".join(out)


CSS = """
:root{--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#6f6d68;--grid:#e1e0d9;--wash:rgba(11,11,11,.045);--border:rgba(11,11,11,.10);
--accent:#2a78d6;--track:#cde2fb;--passed:#0ca30c;--failed:#d03b3b;--error:#fab219;--skipped:#898781}
@media (prefers-color-scheme:dark){:root{--page:#0d0d0d;--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--muted:#a09e96;--grid:#2c2c2a;--wash:rgba(255,255,255,.06);--border:rgba(255,255,255,.10);--accent:#3987e5;--track:#0d366b}}
*{box-sizing:border-box}body{margin:0;background:var(--page);color:var(--ink);font:14px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:32px 16px 72px}
h1{font-size:26px;margin:0}h2{font-size:18px;margin:36px 0 12px}h3{font-size:15px;margin:22px 0 10px}
.muted{color:var(--muted)}.small{font-size:12px}.num{font-variant-numeric:tabular-nums}.r{text-align:right}
header .meta{color:var(--ink2);margin-top:6px}header code{background:var(--wash);padding:1px 6px;border-radius:4px;font-size:12px}
nav{display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:16px;font-size:13px}nav a{color:var(--accent);text-decoration:none}nav a:hover{text-decoration:underline}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px}.card.flush{padding:0;overflow:hidden}
.ico{width:16px;height:16px;flex:none;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.st-passed{color:var(--passed)}.st-failed{color:var(--failed)}.st-error{color:var(--error)}.st-skipped{color:var(--skipped)}
.badge{display:inline-flex;align-items:center;gap:6px;font-weight:500;white-space:nowrap}.badge span{color:var(--ink)}
.verdict{display:grid;grid-template-columns:auto 1fr;gap:28px;align-items:center}
.hero .big{font-size:64px;line-height:1.05;font-weight:600}.label{display:flex;align-items:center;gap:6px;color:var(--ink2);font-size:13px}
.sub{color:var(--muted);font-size:12px}.says p{margin:0 0 14px;font-size:16px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:12px}.tile .value{font-size:28px;font-weight:600;line-height:1.25;margin-top:4px}
.stack{display:flex;gap:2px;height:12px;min-width:80px}.seg{display:block;min-width:4px}.seg:last-child{border-radius:0 4px 4px 0}
.seg.passed{background:var(--passed)}.seg.failed{background:var(--failed)}.seg.error{background:var(--error)}.seg.skipped{background:var(--skipped)}
.legend{display:flex;flex-wrap:wrap;gap:4px 16px;margin-top:12px;font-size:12px;color:var(--ink2)}.key{display:inline-flex;align-items:center;gap:6px}.sw{width:10px;height:10px;border-radius:2px;display:inline-block}
table{width:100%;border-collapse:collapse}th,td{padding:10px 14px;text-align:left;border-top:1px solid var(--grid);vertical-align:middle}
thead th{border-top:0;font-size:12px;font-weight:600;color:var(--ink2);background:var(--wash)}th.r,td.r{text-align:right}
tr.cat th{background:var(--wash);font-size:12px;color:var(--ink2);border-top:1px solid var(--grid)}td.bar{width:34%}td.nm a{color:var(--ink);text-decoration:none}td.nm a:hover{text-decoration:underline}
.strip{width:240px;height:26px;display:block}.strip .axis{stroke:var(--track);stroke-width:4;stroke-linecap:round}.strip .thr{stroke:var(--ink);stroke-width:2}
.strip .dot.ok{fill:var(--accent);fill-opacity:.55}.strip .dot.bad{fill:var(--failed);stroke:var(--surface);stroke-width:1}
.cards{display:grid;gap:12px}.card.fail{border-left:3px solid var(--failed)}.ah{display:flex;flex-wrap:wrap;align-items:center;gap:6px 12px;margin-bottom:8px}
.ok-note{color:var(--ink2)}
.field{background:var(--wash);border-radius:8px;padding:8px 12px;min-width:0;margin-top:8px}.field .k{font-size:12px;font-weight:600;color:var(--ink2);margin-bottom:2px}
.field .v{white-space:pre-wrap;overflow-wrap:anywhere}.field ul{margin:0;padding-left:18px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:0 12px}
.turn{padding:4px 0;border-top:1px solid var(--grid)}.k+.turn{border-top:0}.who{font-size:12px;font-weight:600;color:var(--ink2)}
.why{margin-top:10px}.why p{margin:2px 0 0;white-space:pre-wrap;overflow-wrap:anywhere}
.rh{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px}.tools{display:flex;gap:6px;margin-top:24px}
.tools button{font:inherit;color:inherit;background:var(--surface);border:1px solid var(--border);border-radius:999px;padding:4px 12px;cursor:pointer}
.tools button[aria-pressed=true]{border-color:var(--accent);box-shadow:inset 0 0 0 1px var(--accent);font-weight:600}
details.t{border-top:1px solid var(--grid)}details.t:first-child{border-top:0}
details.t>summary{display:grid;grid-template-columns:96px 1fr auto;gap:12px;align-items:center;padding:11px 14px;cursor:pointer;list-style:none}
details.t>summary::-webkit-details-marker{display:none}details.t>summary:hover{background:var(--wash)}
.tt{font-weight:500;overflow-wrap:anywhere}.ts{color:var(--ink2);font-size:12px;text-align:right}.src{grid-column:2/4;color:var(--muted);font-size:11px}
.tb{padding:2px 14px 16px;background:var(--page);border-top:1px solid var(--grid)}
.metric{margin-top:10px;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 12px}
.mh{display:flex;flex-wrap:wrap;align-items:center;gap:6px 14px}.reason{margin:8px 0 0;white-space:pre-wrap;overflow-wrap:anywhere}
.errbox{margin:8px 0 0;padding:8px 10px;border-left:3px solid var(--error);background:var(--wash);border-radius:6px;white-space:pre-wrap}
details.sub{margin-top:8px}details.sub>summary{cursor:pointer;color:var(--ink2);font-size:13px}
pre{margin:6px 0 0;padding:10px 12px;background:var(--wash);border-radius:8px;overflow:auto;max-height:300px;font:12px/1.5 ui-monospace,Menlo,monospace;white-space:pre-wrap;overflow-wrap:anywhere}
footer{margin-top:48px;color:var(--muted);font-size:12px}
@media (max-width:760px){.verdict{grid-template-columns:1fr}.kpis{grid-template-columns:1fr 1fr}.grid2{grid-template-columns:1fr}td.bar{width:auto}
details.t>summary{grid-template-columns:96px 1fr}.ts{grid-column:2;text-align:left}.strip{width:160px}}
@media print{:root{--page:#fff;--surface:#fff;--ink:#000;--ink2:#333;--muted:#555;--grid:#ddd;--wash:#f3f3f1;--border:#ccc}
nav,.tools{display:none}.wrap{padding:0}.card,tr,details.t,.metric{break-inside:avoid}details.sub pre{max-height:none}h2{break-after:avoid}}
"""

JS = """
const rows=[...document.querySelectorAll('details.t')];
document.querySelectorAll('.tools button[data-f]').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('.tools button[data-f]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));
  rows.forEach(r=>{r.hidden=b.dataset.f!=='all'&&r.dataset.outcome!==b.dataset.f;});
}));
const openAll=document.getElementById('openall');
openAll.addEventListener('click',()=>{const open=openAll.textContent==='Expand all';rows.forEach(r=>{r.open=open;});openAll.textContent=open?'Collapse all':'Expand all';});
window.addEventListener('beforeprint',()=>document.querySelectorAll('details').forEach(d=>{d.open=true;}));
"""


def build(run: dict, all_runs: list[dict]) -> str:
    combined = run.get("combined")
    source = (f"Combined from {len(run['source_runs'])} runs · latest real verdict of each test" if combined
              else f"Run {run['id']}")
    when = (f"{fmt_when(run['started'])} → {fmt_when(run['finished'])}" if combined else fmt_when(run["started"]))
    note = ('<p class="muted small">If a test failed in one run and passed in a later one, the report shows the later result. '
            'Runs may reflect different code or thresholds.</p>') if combined else ""
    title = "Chatbot evaluation report"
    return (
        f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta name="color-scheme" content="light dark"><title>{title}</title><style>{CSS}</style></head><body><div class="wrap">'
        f'<header><h1>{title}</h1><div class="meta">{esc(source)} · {esc(when)} · {esc(fmt_dur(run.get("duration")))} · '
        f'judge <code>{esc(run.get("judge_model"))}</code> · bot <code>{esc(run.get("bot_model"))}</code></div>{note}'
        f'<nav><a href="#summary">Summary</a><a href="#scorecard">Scorecard</a><a href="#metrics">Metrics</a>'
        f'<a href="#attention">Needs attention</a><a href="#history">History</a><a href="#results">All results</a></nav></header>'
        f'{sec_summary(run)}{sec_scorecard(run)}{sec_metrics(run)}{sec_attention(run)}{sec_history(all_runs)}{sec_results(run)}'
        f'<footer>Generated {esc(datetime.now().strftime("%d %b %Y, %H:%M"))}. Scores run from 0 to 1 and 1.0 is best for every metric; '
        f'a test passes when its score reaches the threshold. An error means the judge never returned a score, so it is not counted as a failure.</footer>'
        f'</div><script>{JS}</script></body></html>'
    )


def render(which: str = "latest") -> str | None:
    """`which` is a run id, "latest", or "combined". None if there is nothing to report."""
    runs = load_runs()
    if not runs:
        return None
    if which == "combined":
        return build(combine(runs), runs)
    run = runs[-1] if which == "latest" else next((r for r in runs if r["id"] == which), None)
    return build(run, runs) if run else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="latest", help='run id or "latest" (default)')
    ap.add_argument("--combined", action="store_true", help="merge every run: latest real verdict per test")
    ap.add_argument("--out", help="output file (default: data/reports/report-<id>.html)")
    args = ap.parse_args()
    which = "combined" if args.combined else args.run
    page = render(which)
    if page is None:
        raise SystemExit("No matching run found in " + str(RUNS_DIR))
    name = "combined" if which == "combined" else (load_runs()[-1]["id"] if which == "latest" else which)
    out = Path(args.out) if args.out else REPORTS_DIR / f"report-{name}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()

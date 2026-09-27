"""Build the replay page for a demo session: demo/sessions/<stamp>/report/index.html.

    python jev-atlas/tools/report.py [SESSION_DIR]      # default: the newest session

For every goal and every pass (without the atlas, with it, after each learning round) it
shows the steps as a strip of frames: the screen Jev was looking at, what it chose and
how sure it was, the runner-up, and the atlas note on the chosen control (in blue). A
loop is shown once, with how many times it repeated. Then each learning round: the
diagnosis, the lessons as before/after text, and the outcome of the next pass.
Needs Pillow (the harness's venv has it) to shrink the frames to JPEG.
"""
import html
import json
import pathlib
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
SHIM = HERE.parent
REPO = SHIM.parent
SESSIONS = SHIM / "demo" / "sessions"
LEARNED = SHIM / "atlas" / "learned"
FRAME_W = 640
MAX_CARDS = 14

e = html.escape


def frame(run_dir, index, out_dir, name):
    for suffix in (".png", ".jpg"):
        src = run_dir / f"step-{index:02d}{suffix}"
        if src.exists():
            dest = out_dir / name
            if not dest.exists():
                im = Image.open(src).convert("RGB")
                im.thumbnail((FRAME_W, FRAME_W * 2))
                im.save(dest, "JPEG", quality=72, optimize=True)
            return f"img/{name}"
    return None


def steps_of(run_dir):
    f = run_dir / "steps.jsonl"
    return [json.loads(l) for l in f.read_text().splitlines() if l.strip()] if f.exists() else []


def target_head(op):
    return {"CLICK": "click_target", "TYPE_TEXT": "type_text_target", "PRESS_ENTER": "press_enter_target",
            "SELECT_OPTION": "select_option_target"}.get(op)


def card(s, run_dir, out_dir, tag, repeated):
    elements = {x["index"]: x for x in s["state"]["elements"]}
    shared = s["state"].get("shared_notes") or {}
    op = s["operation"]
    op_p = s["response"]["operation"]["probabilities"].get(op, s.get("confidence"))
    head = s["response"].get(target_head(op) or "", {}) or {}
    probs = sorted((head.get("probabilities") or {}).items(), key=lambda x: -x[1])
    chosen = elements.get(s.get("target")) or {}
    note = chosen.get("what") and chosen or shared.get(chosen.get("note") or "", {})
    img = frame(run_dir, s["step"] - 1, out_dir, f"{tag}-{s['step']:02d}.jpg")
    alt = next(((elements.get(i, {}).get("label"), p) for i, p in probs if i != s.get("target") and p >= 0.02), None)
    label = s.get("target_label") or ""
    action = {"CLICK": "Click", "TYPE_TEXT": "Type into", "PRESS_ENTER": "Press Enter in", "DONE": "Done",
              "BLOCKED": "Blocked", "SCROLL_DOWN": "Scroll down", "WAIT": "Wait"}.get(op, op.title())
    out = [f'<figure class="card">']
    if img:
        out.append(f'<img src="{img}" alt="Screen before step {s["step"]}" loading="lazy">')
    out.append('<figcaption>')
    out.append(f'<div class="stepno">Step {s["step"]}' + (f' <span class="rep">then repeated ×{repeated}</span>' if repeated else '') + '</div>')
    out.append(f'<div class="act"><b>{e(action)}</b> {e(label)}'
               + (f' <span class="typed">“{e(s["text"])}”</span>' if s.get("text") else '')
               + f' <span class="p">{op_p:.2f}</span></div>')
    if probs and op in ("CLICK", "TYPE_TEXT", "PRESS_ENTER"):
        out.append(f'<div class="why">target {probs[0][1]:.2f}' + (f' · runner-up {e(str(alt[0]))} {alt[1]:.2f}' if alt else '') + '</div>')
    if note and (note.get("what") or note.get("not_for")):
        out.append('<div class="note">' + (f'{e(note.get("what", ""))}' if note.get("what") else '')
                   + (f' <i>Not for:</i> {e(note["not_for"])}' if note.get("not_for") else '') + '</div>')
    out.append('</figcaption></figure>')
    return "".join(out)


def strip(res, out_dir, tag):
    run_dir = REPO / res["run_dir"]
    steps = steps_of(run_dir)
    if not steps:
        return '<p class="muted">No step log for this run.</p>'
    seen, cards, order = {}, [], []
    for s in steps:
        # The same screen (URL and what is on it) and the same choice: a loop, shown once.
        sig = (s["state"]["page"]["url"], s["operation"], s.get("target_label"),
               tuple(x.get("label") for x in s["state"]["elements"]))
        if sig in seen:
            seen[sig][1] += 1
            continue
        seen[sig] = [s, 0]
        order.append(sig)
    for sig in order[:MAX_CARDS]:
        s, rep = seen[sig]
        cards.append(card(s, run_dir, out_dir, tag, rep))
    end = frame(run_dir, steps[-1]["step"], out_dir, f"{tag}-end.jpg")
    if end:
        cards.append(f'<figure class="card end"><img src="{end}" alt="Final screen" loading="lazy">'
                     f'<figcaption><div class="stepno">Final screen</div></figcaption></figure>')
    more = f'<p class="muted small">{len(order) - MAX_CARDS} more distinct steps not shown.</p>' if len(order) > MAX_CARDS else ''
    return f'<div class="strip">{"".join(cards)}</div>{more}'


def verdict(res):
    cls = "pass" if res["pass"] else "fail"
    word = "Passed" if res["pass"] else "Failed"
    return f'<span class="v {cls}">{word}</span> <span class="muted">{res["steps"]} steps, agent said {e(res["status"])}</span>'


PASS_TITLES = {"without": "Without the atlas", "with": "With the atlas"}


def pass_title(p):
    if p["name"].startswith("learned-"):
        return f'After learning round {p["name"].split("-")[1]}'
    return PASS_TITLES.get(p["condition"], p["name"]) if not p["name"].startswith("with-") else "With the atlas"


def lesson_html(l):
    rows = []
    if l["kind"] == "control":
        where = f'note on “{e(", ".join(l.get("_matches") or []) or json.dumps(l["key"]))}”'
    elif l["kind"] == "page":
        where = f'page description: {e(l.get("page", ""))}'
    else:
        where = "fact shown on every page"
    rows.append(f'<div class="lk">{where}</div>')
    for f, name in (("what", "What it does"), ("not_for", "Not for"), ("not_here", "Elsewhere"), ("text", "Fact")):
        if l.get(f):
            old = l.get(f"_old_{f}")
            if old:
                rows.append(f'<div class="old"><b>{name}, before:</b> {e(old)}</div>')
            rows.append(f'<div class="new"><b>{name}{", after" if old else ""}:</b> {e(l[f])}</div>')
    if l.get("why"):
        rows.append(f'<div class="muted small">{e(l["why"])}</div>')
    if not l.get("ok"):
        rows.append(f'<div class="fail small">Dropped by the checks: {e("; ".join(l.get("rejected_because", [])))}</div>')
    return f'<div class="lesson">{"".join(rows)}</div>'


def build(session_dir):
    s = json.loads((session_dir / "session.json").read_text())
    out = session_dir / "report"
    (out / "img").mkdir(parents=True, exist_ok=True)
    passes = s["passes"]
    goals = list(s["goals"])
    model = next((r["model"] for p in passes for r in p["results"].values() if r.get("model")), "?")

    # Scoreboard
    head = "".join(f'<th>{e(pass_title(p))}</th>' for p in passes)
    body = []
    for g in goals:
        cells = []
        for p in passes:
            r = p["results"].get(g)
            cells.append('<td>–</td>' if not r else
                         f'<td><span class="v {"pass" if r["pass"] else "fail"}">{"✓" if r["pass"] else "✗"}</span> '
                         f'<span class="muted small">{r["steps"]} steps</span></td>')
        body.append(f'<tr><th scope="row"><b>{g}</b> <span class="gt">{e(s["goals"][g])}</span></th>{"".join(cells)}</tr>')
    totals = "".join(f'<td><b>{sum(r["pass"] for r in p["results"].values())} of {len(p["results"])}</b></td>' for p in passes)
    score = (f'<table class="score"><thead><tr><th>Goal</th>{head}</tr></thead><tbody>{"".join(body)}'
             f'<tr class="tot"><th scope="row">Passed</th>{totals}</tr></tbody></table>')

    # Learning rounds
    rounds_html = []
    for rnd in s.get("rounds", []):
        items = []
        for prop in rnd["proposals"]:
            rec = json.loads((LEARNED / prop["file"]).read_text())
            items.append(f'<div class="prop"><div class="lab">{e(prop["goal"])} failed. The learner ({e(rec["proposed_by"])}) read the run and the manual:</div>'
                         f'<p class="diag">{e(rec["diagnosis"] or "")}</p>'
                         + "".join(lesson_html(l) for l in rec["lessons"])
                         + f'<div class="small">{"Accepted." if prop["accepted"] else "Not accepted."}</div></div>')
        rounds_html.append(f'<section class="round"><h3>Learning round {rnd["round"]}</h3>{"".join(items)}'
                           f'<p class="muted small">Atlas {e(rnd["atlas_before"] or "")} → {e(rnd.get("atlas_after") or "")}</p></section>')

    # Per-goal replays
    goal_html = []
    for g in goals:
        parts = []
        for i, p in enumerate(passes):
            r = p["results"].get(g)
            if not r:
                continue
            open_attr = " open" if (i == 0 or r["pass"] != passes[0]["results"].get(g, {}).get("pass")) else ""
            parts.append(f'<details{open_attr}><summary><b>{e(pass_title(p))}</b> · {verdict(r)}</summary>'
                         f'{strip(r, out / "img", f"{g}-{p["name"]}")}</details>')
        goal_html.append(f'<section class="goal"><h3>{g}</h3><blockquote>{e(s["goals"][g])}</blockquote>{"".join(parts)}</section>')

    page = TEMPLATE.format(session=e(s["session"]), model=e(model), score=score,
                           rounds="".join(rounds_html) or '<p class="muted">No learning rounds in this session.</p>',
                           goals="".join(goal_html))
    (out / "index.html").write_text(page)
    print(f"wrote {out.relative_to(REPO)}/index.html")
    return out


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Jev Atlas Replay</title>
<style>
:root{{--paper:#F7F8FA;--surface:#fff;--ink:#15181D;--ink2:#3D444E;--muted:#5E6875;--rule:#DDE1E7;
--atlas:#2A55C9;--atlas-ink:#1E3F9A;--atlas-bg:#E8EEFD;--pass:#23804F;--fail:#B8412E;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--paper:#111418;--surface:#181C21;--ink:#E7EAEE;--ink2:#C1C7CF;
--muted:#9AA3AE;--rule:#2A3038;--atlas:#86A6FF;--atlas-ink:#A9C0FF;--atlas-bg:#1A2542;--pass:#5CC48D;--fail:#F08A74;color-scheme:dark}}}}
:root[data-theme="dark"]{{--paper:#111418;--surface:#181C21;--ink:#E7EAEE;--ink2:#C1C7CF;--muted:#9AA3AE;--rule:#2A3038;
--atlas:#86A6FF;--atlas-ink:#A9C0FF;--atlas-bg:#1A2542;--pass:#5CC48D;--fail:#F08A74;color-scheme:dark}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;padding:0 16px}}
.wrap{{max-width:1200px;margin:0 auto;padding:40px 0 80px}}
h1{{font-size:2rem;margin:0 0 6px}} h2{{font-size:1.4rem;margin:56px 0 12px}} h3{{font-size:1.1rem;margin:28px 0 8px}}
.muted{{color:var(--muted)}} .small{{font-size:.88rem}}
.lede{{color:var(--ink2);max-width:760px}}
.v{{font-weight:700}} .v.pass,.pass{{color:var(--pass)}} .v.fail,.fail{{color:var(--fail)}}
.score{{border-collapse:collapse;width:100%;background:var(--surface);border:1px solid var(--rule);border-radius:8px;font-variant-numeric:tabular-nums}}
.score th,.score td{{padding:10px 12px;border-bottom:1px solid var(--rule);text-align:left;vertical-align:top}}
.score thead th{{font-size:.8rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}}
.score .gt{{display:block;font-weight:400;font-style:italic;color:var(--ink2);font-size:.9rem;max-width:520px}}
.score .tot th,.score .tot td{{border-bottom:none}}
.tablewrap{{overflow-x:auto}}
blockquote{{margin:0 0 12px;font-style:italic;color:var(--ink2);border-left:3px solid var(--rule);padding-left:12px}}
details{{background:var(--surface);border:1px solid var(--rule);border-radius:8px;margin:10px 0;padding:10px 14px}}
summary{{cursor:pointer}}
.strip{{display:flex;gap:12px;overflow-x:auto;padding:12px 0 6px;scroll-snap-type:x proximity}}
.card{{flex:0 0 340px;margin:0;scroll-snap-align:start;background:var(--paper);border:1px solid var(--rule);border-radius:6px;overflow:hidden}}
.card img{{display:block;width:100%;height:auto;border-bottom:1px solid var(--rule)}}
.card figcaption{{padding:8px 10px;font-size:.9rem}}
.stepno{{font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:700}}
.rep{{color:var(--fail);text-transform:none;letter-spacing:0}}
.act b{{font-weight:700}} .p{{font-family:ui-monospace,Menlo,monospace;font-size:.8rem;color:var(--muted)}}
.typed{{font-family:ui-monospace,Menlo,monospace;font-size:.85rem}}
.why{{font-size:.8rem;color:var(--muted);margin-top:2px}}
.note{{margin-top:6px;background:var(--atlas-bg);color:var(--atlas-ink);border-radius:4px;padding:6px 8px;font-size:.84rem;line-height:1.45}}
.round,.prop{{background:var(--surface);border:1px solid var(--rule);border-radius:8px;padding:14px 16px;margin:12px 0}}
.prop{{border-color:var(--atlas)}} .lab{{font-weight:700}} .diag{{margin:6px 0 10px}}
.lesson{{border-top:1px solid var(--rule);padding:8px 0}} .lk{{font-size:.8rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}}
.old{{color:var(--muted);text-decoration:line-through;text-decoration-color:var(--rule)}}
.new{{background:var(--atlas-bg);color:var(--atlas-ink);border-radius:4px;padding:4px 8px;margin-top:4px}}
@media (max-width:600px){{.card{{flex-basis:78vw}} h1{{font-size:1.6rem}}}}
</style></head><body><div class="wrap">
<h1>Jev Atlas: replay of session {session}</h1>
<p class="lede">Five requests to ADIT, a made-up mining-exploration app, carried out by Jev ({model}) driving a real browser. Each goal is run
without the atlas, with it, and again after the atlas has learned from what still failed. Pass or fail is decided by reading the app's own data
afterwards, not by what the agent says. Blue text is what the atlas added to what Jev saw.</p>
<h2>Results</h2>
<div class="tablewrap">{score}</div>
<h2>What the atlas learned</h2>
{rounds}
<h2>Step by step</h2>
<p class="muted small">Each frame is the screen Jev was looking at when it chose. The number after the action is how sure it was of that
action; the runner-up is the control it nearly chose instead.</p>
{goals}
</div></body></html>
"""


if __name__ == "__main__":
    if len(sys.argv) > 1:
        d = pathlib.Path(sys.argv[1])
    else:
        d = sorted(p for p in SESSIONS.glob("*") if (p / "session.json").exists())[-1]
    build(d)

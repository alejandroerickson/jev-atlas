"""Learn from a failed run: propose atlas lessons, check them in code, keep the accepted ones.

    python3 jev-atlas/tools/learn.py propose RUN_DIR --goal-id E9 [--check '{"pass": false, ...}']
    python3 jev-atlas/tools/learn.py list                 # pending lessons, with their checks
    python3 jev-atlas/tools/learn.py accept FILE|all      # move to accepted/; merge.py applies them
    python3 jev-atlas/tools/learn.py reject FILE|all

A lesson is application knowledge, never the answer to one goal. A model (LEARN_MODEL,
default gpt-5.5, any OpenAI-compatible endpoint) reads the failed run as Jev saw it, the
atlas entries it was shown, the app's manual and the outcome check, and proposes up to
three lessons of three kinds:

  control  a note on a control: a key (atlas key fields) plus region / what / not_for.
           The same key as an existing entry replaces that entry's text; a new key is
           added ahead of the generated entries, so it wins ties.
  page     new `what` and/or `not_here` text for a page or overlay id.
  fact     one sentence added to every page's context (global_facts_js).

Every lesson is then checked in code (check_lesson): key fields and page ids exist;
no digits, record codes, or four-word runs copied from the goal; none of the wording the
atlas rules forbid (docs/BUILDING-A-SHIM.md §5); and a control lesson must be the winning
match for at least one element the failed run actually saw, a page lesson must name a page
the run was on. A lesson that fails is sent back once with the reasons, then dropped.

Lessons live in atlas/learned/{pending,accepted,rejected}/ as one JSON file per proposal.
merge.py applies accepted/ in file-name order (apply()) and stamps the atlas version with
the count, so the atlas is still rebuilt byte for byte from files in the repository.
"""
import argparse
import copy
import datetime
import importlib.util
import json
import os
import pathlib
import re
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
SHIM = HERE.parent
LEARNED = SHIM / "atlas" / "learned"
ATLAS = SHIM / "atlas" / "adit.json"
MANUAL = SHIM / "manual"
HARNESS = pathlib.Path(os.environ.get("JEV_CLONE", str(SHIM / "vendor" / "jev-ultrafast")))

KINDS = ("control", "page", "fact")
TEXT_FIELDS = ("region", "what", "not_for", "not_here", "text")
# docs/BUILDING-A-SHIM.md §5, rules 1 and 4, as a grep.
FORBIDDEN = re.compile(r"\bnot here\b|nothing (on|here)|cannot|can't|\bno \w+ (is|are) (offered|available)"
                       r"|\bclick\b|\bgo back\b|\bstep \d", re.I)
RECORD_CODE = re.compile(r"\b[A-Z]{2,}-\d{2,}|\b\d{4}-\d{2}\b")


def harness_atlas():
    spec = importlib.util.spec_from_file_location("harness_atlas", HARNESS / "jev_ultrafast" / "atlas.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ applying lessons

def key_sig(key):
    return json.dumps(key, sort_keys=True)


def apply(atlas, lessons):
    """Return a copy of `atlas` with each lesson applied, in order."""
    atlas = copy.deepcopy(atlas)
    pages = {p["id"]: p for p in atlas["pages"]}
    for lesson in lessons:
        kind = lesson["kind"]
        if kind == "control":
            fields = {k: lesson[k] for k in ("region", "what", "not_for") if lesson.get(k)}
            same = [c for c in atlas["controls"] if key_sig(c["key"]) == key_sig(lesson["key"])]
            if same:
                same[0].update(fields)
                same[0]["learned"] = lesson["id"]
            else:
                atlas["controls"].insert(0, {"key": lesson["key"], **fields, "learned": lesson["id"]})
        elif kind == "page":
            page = pages[lesson["page"]]
            for f in ("what", "not_here"):
                if lesson.get(f):
                    page[f] = lesson[f]
            page.setdefault("learned", []).append(lesson["id"])
        elif kind == "fact":
            facts = atlas.get("global_facts_js") or []
            atlas["global_facts_js"] = (facts if isinstance(facts, list) else [facts]) + [json.dumps(lesson["text"])]
    return atlas


def accepted_lessons():
    out = []
    for f in sorted((LEARNED / "accepted").glob("*.json")):
        out += [l for l in json.loads(f.read_text())["lessons"] if l.get("ok")]
    return out


# ------------------------------------------------------------------ reading a run

def load_steps(run_dir):
    return [json.loads(l) for l in (pathlib.Path(run_dir) / "steps.jsonl").read_text().splitlines() if l.strip()]


def step_pages(step, book):
    """The atlas page id and overlays in view at this step (logged, or recomputed from the URL)."""
    page = step.get("atlas_page")
    if page is None and book is not None:
        matched = book.match_page(step.get("url") or step["state"]["page"]["url"])
        page = matched["id"] if matched else None
    return page, step.get("atlas_overlays") or []


def element_fields(el, roles, page_id):
    """The fields a control key is matched against, rebuilt from one elements_debug row."""
    return {
        "track_id": el.get("track_id"), "id": el.get("dom_id"), "title": el.get("title"),
        "href": el.get("href"), "ancestor": el.get("ancestor"), "row_label": el.get("row_label"),
        "section": el.get("section"), "landmark": el.get("landmark"),
        "role": el.get("role") or roles.get(el.get("index")),
        "text": (el.get("label") or "").split(" → ")[0], "page": page_id,
    }


def digest(steps, book, atlas):
    """What Jev saw, compactly: each distinct (screen, choice) once, with how often it recurred."""
    seen, rows = {}, []
    for s in steps:
        page_id, overlays = step_pages(s, book)
        target = s.get("target_label")
        sig = (s["state"]["page"]["url"], s["operation"], target)
        if sig in seen:
            rows[seen[sig]]["repeated"] += 1
            continue
        elements = {e["index"]: e for e in s["state"]["elements"]}
        resp = s["response"]
        head = {"CLICK": "click_target", "TYPE_TEXT": "type_text_target", "PRESS_ENTER": "press_enter_target"}
        probs = (resp.get(head.get(s["operation"], ""), {}) or {}).get("probabilities") or \
                (resp.get("click_target") or {}).get("probabilities") or {}
        top = sorted(probs.items(), key=lambda x: -x[1])[:6]
        matched = {e["index"]: e.get("matched_key") for e in s.get("elements_debug") or []}
        rows.append({
            "step": s["step"],
            "repeated": 0,
            "url": s["state"]["page"]["url"].split("#", 1)[-1],
            "atlas_page": page_id,
            "overlays": overlays,
            "context": s["state"]["page"].get("context", "")[:1800],
            "operation_probabilities": resp["operation"]["probabilities"],
            "chose": {"operation": s["operation"], "target": target, "text": s.get("text")},
            "top_targets": [
                {"label": elements.get(i, {}).get("label"), "p": p,
                 "note": {k: elements.get(i, {}).get(k) for k in ("region", "what", "not_for", "note") if elements.get(i, {}).get(k)},
                 "atlas_key": matched.get(i)}
                for i, p in top if p >= 0.01
            ],
            "all_elements": [
                f'{e["index"]}: {e.get("role")} "{e.get("label")}"' + (" [no atlas note]" if not (e.get("what") or e.get("note")) else "")
                for e in s["state"]["elements"]
            ],
        })
        seen[sig] = len(rows) - 1
    shared = {}
    for s in steps:
        shared.update(s["state"].get("shared_notes") or {})
    visited = {r["atlas_page"] for r in rows} | {o for r in rows for o in r["overlays"]}
    pages = [{k: p.get(k) for k in ("id", "name", "what", "not_here", "leads_to")} for p in atlas["pages"] if p["id"] in visited]
    return rows, shared, pages


# ------------------------------------------------------------------ checking a lesson

def words(text):
    return re.findall(r"[a-z]+", text.lower())


def check_lesson(lesson, goal, steps, atlas, A):
    """Reasons this lesson may not go in the atlas; empty means it passes."""
    why = []
    kind = lesson.get("kind")
    if kind not in KINDS:
        return [f"unknown kind {kind!r}"]
    texts = [str(lesson.get(f) or "") for f in TEXT_FIELDS]
    blob = " ".join(texts)
    if not blob.strip():
        why.append("no text")
    if re.search(r"\d", blob):
        why.append("text contains a digit (no values, dates or codes)")
    if RECORD_CODE.search(json.dumps(lesson.get("key", {}))):
        why.append("key names a specific record")
    m = FORBIDDEN.search(blob)
    if m:
        why.append(f"forbidden wording {m.group(0)!r} (route, do not refuse; purpose, not procedure)")
    g = words(goal)
    grams = {" ".join(g[i:i + 4]) for i in range(len(g) - 3)}
    lw = words(blob)
    copied = sorted({" ".join(lw[i:i + 4]) for i in range(len(lw) - 3)} & grams)
    if copied:
        why.append(f"copies the goal's wording: {copied[:3]}")
    page_ids = {p["id"] for p in atlas["pages"]}
    book = A.Atlas(atlas)
    if kind == "page":
        if lesson.get("page") not in page_ids:
            why.append(f"unknown page id {lesson.get('page')!r}")
        elif lesson["page"] not in {x for s in steps for x in [step_pages(s, book)[0], *step_pages(s, book)[1]]}:
            why.append(f"the run was never on page {lesson['page']!r}")
        if not (lesson.get("what") or lesson.get("not_here")):
            why.append("page lesson needs what or not_here")
    if kind == "fact" and not lesson.get("text"):
        why.append("fact lesson needs text")
    if kind == "control":
        key = lesson.get("key")
        if not isinstance(key, dict) or not key:
            return why + ["control lesson needs a key"]
        bad = [f for f in key if f not in A.KEY_FIELDS]
        if bad:
            return why + [f"unknown key fields {bad}; allowed: {list(A.KEY_FIELDS)}"]
        if "page" in key and key["page"] not in page_ids:
            why.append(f"unknown page id {key['page']!r}")
        for f, v in key.items():
            if f.endswith("_regex"):
                try:
                    re.compile(v)
                except re.error as e:
                    why.append(f"bad regex in {f}: {e}")
        if not (lesson.get("what") or lesson.get("not_for")):
            why.append("control lesson needs what or not_for")
        if not why:
            trial = A.Atlas(apply(atlas, [{**lesson, "id": "_trial"}]))
            hits = set()
            for s in steps:
                page_id, overlays = step_pages(s, book)
                in_view = [i for i in [page_id, *overlays] if i]
                roles = {e["index"]: e.get("role") for e in s["state"]["elements"]}
                for el in s.get("elements_debug") or []:
                    entry = trial.match_control(element_fields(el, roles, page_id), in_view)
                    if entry and entry.get("learned") == "_trial":
                        hits.add(el.get("label"))
            if not hits:
                why.append("the key matches no element the run saw (or a heavier entry still wins)")
            else:
                lesson["_matches"] = sorted(h for h in hits if h)[:5]
    return why


# ------------------------------------------------------------------ the model

SYSTEM = """You improve an application atlas: documentation that a small choice model (Jev) reads while it drives a web \
application for a user. On every step Jev sees the page context and a list of on-screen elements, each with the atlas's \
note (region, what it does, what it is not for), and picks one action. You are shown a run that failed, exactly as Jev \
saw it, plus the application's user manual and the outcome check.

Find the point where the run went wrong and why the atlas did not steer it, then write at most three lessons that fix \
the atlas's knowledge of the APPLICATION. A lesson must be true and useful for any user goal, not just this one.

Rules for every string you write (they were measured: breaking them made Jev worse):
1. Route, do not refuse. Never "not here", "nothing on this page", "cannot"; say where the thing lives.
2. State the situation, not the absence.
3. No example values: no digits, dates, record codes, names of records or people, amounts.
4. Purpose and destination, not procedure: no "click", "go back", "then"; say what a control is for and where it leads.
5. Short, plain, specific. Name the neighbouring control a reader would confuse this one with.
Do not copy phrases from the goal.
When you rewrite an existing note or page text, keep everything the old text said that is still true and add to it;
the old text was written from the whole application, and trimming it loses knowledge other tasks need.

Lesson kinds (JSON):
- {"kind": "control", "key": {...}, "region": str, "what": str, "not_for": str}
  key fields (all must match; heavier wins): text, text_regex, text_contains, role, page, section, landmark, row_label,
  row_label_regex, href, href_regex, href_contains, title, id, id_regex, track_id, ancestor.
  To rewrite an existing note, reuse its exact atlas_key as shown in the trace; otherwise write a new key from the
  element's label, role and page id. Prefer amending the note on the element Jev should have chosen, or on the one it
  wrongly chose.
- {"kind": "page", "page": page id, "what": str, "not_here": str}   (full replacement text for those fields)
- {"kind": "fact", "text": str}   (one sentence shown on every page; use sparingly, for app-wide knowledge)

If the failure is not the atlas's fault (the agent has no way to do something, or the goal is impossible), say so in the
diagnosis and return no lessons.

Reply with one JSON object: {"diagnosis": str (where and why it went wrong, in two or three sentences),
"lessons": [ {..., "why": str (one sentence), "evidence_step": int} ] }"""


def llm_config():
    env = {}
    dotenv = HARNESS / ".env"
    if dotenv.exists():
        env = dict(l.split("=", 1) for l in dotenv.read_text().splitlines() if "=" in l and not l.startswith("#"))
    key = os.environ.get("LEARN_API_KEY") or os.environ.get("OPENAI_API_KEY") or env.get("TEXT_MODEL_API_KEY")
    base = os.environ.get("LEARN_BASE_URL") or "https://api.openai.com/v1"
    model = os.environ.get("LEARN_MODEL") or "gpt-5.5"
    if not key:
        sys.exit("learn: set LEARN_API_KEY (or OPENAI_API_KEY) for the lesson-writing model")
    return base.rstrip("/"), key, model


def ask(messages):
    base, key, model = llm_config()
    body = {"model": model, "messages": messages, "response_format": {"type": "json_object"}}
    if "api.openai.com" in base:
        body["reasoning_effort"] = os.environ.get("LEARN_REASONING", "medium")
    req = urllib.request.Request(base + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        out = json.load(r)
    return json.loads(out["choices"][0]["message"]["content"]), out.get("model", model), out.get("usage", {})


def propose(run_dir, goal_id, check_result, goal_text=None):
    run_dir = pathlib.Path(run_dir).resolve()
    run = json.loads((run_dir / "run.json").read_text())
    goal = goal_text or run["goal"]
    steps = load_steps(run_dir)
    atlas = json.loads(ATLAS.read_text())
    A = harness_atlas()
    book = A.Atlas(atlas)
    rows, shared, pages = digest(steps, book, atlas)
    manual = "\n\n".join(f"### {p.name}\n{p.read_text()}" for p in sorted(MANUAL.glob("*.md")))
    payload = {
        "goal": goal,
        "outcome": {"harness_status": run.get("status"), "steps": run.get("step_count"),
                    "check": (check_result or {}).get("details", check_result)},
        "trace": rows,
        "shared_notes": shared,
        "atlas_pages_visited": pages,
        "atlas_page_ids": [p["id"] for p in atlas["pages"]],
    }
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": "APPLICATION MANUAL\n\n" + manual},
                {"role": "user", "content": "FAILED RUN\n\n" + json.dumps(payload, ensure_ascii=False)}]
    answer, model, usage = ask(messages)
    lessons = answer.get("lessons") or []
    problems = {i: check_lesson(l, goal, steps, atlas, A) for i, l in enumerate(lessons)}
    if any(problems.values()):
        feedback = {"rejected_by_code_checks": [{"lesson": lessons[i], "reasons": r} for i, r in problems.items() if r]}
        messages += [{"role": "assistant", "content": json.dumps(answer)},
                     {"role": "user", "content": "Some lessons failed the checks. Rewrite those (or drop them) and "
                                                 "return the full JSON again.\n" + json.dumps(feedback, ensure_ascii=False)}]
        answer, model, usage2 = ask(messages)
        usage = {k: usage.get(k, 0) + usage2.get(k, 0) for k in set(usage) | set(usage2) if isinstance(usage.get(k, 0), int)}
        lessons = answer.get("lessons") or []
        problems = {i: check_lesson(l, goal, steps, atlas, A) for i, l in enumerate(lessons)}
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    controls = {key_sig(c["key"]): c for c in atlas["controls"]}
    pages_by_id = {p["id"]: p for p in atlas["pages"]}
    for l in lessons:  # the text each lesson replaces, for showing before and after
        old = controls.get(key_sig(l.get("key") or {})) if l.get("kind") == "control" else \
            pages_by_id.get(l.get("page")) if l.get("kind") == "page" else None
        for f in ("what", "not_for", "not_here"):
            if old and old.get(f) and l.get(f):
                l[f"_old_{f}"] = old[f]
    for i, l in enumerate(lessons):
        l["id"] = f"{stamp}-{goal_id}-{i + 1}"
        l["ok"] = not problems[i]
        if problems[i]:
            l["rejected_because"] = problems[i]
    record = {
        "goal_id": goal_id,
        "goal": goal,
        "run": str(run_dir.relative_to(SHIM.parent)) if SHIM.parent in run_dir.parents else str(run_dir),
        "atlas_version": atlas.get("version"),
        "proposed_by": model,
        "usage": usage,
        "created_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "diagnosis": answer.get("diagnosis"),
        "lessons": lessons,
    }
    out = LEARNED / "pending" / f"{stamp}-{goal_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n")
    return out, record


# ------------------------------------------------------------------ showing and deciding

def show(record, atlas=None):
    atlas = atlas or json.loads(ATLAS.read_text())
    controls = {key_sig(c["key"]): c for c in atlas["controls"]}
    pages = {p["id"]: p for p in atlas["pages"]}
    lines = [f"{record['goal_id']}: {record['diagnosis']}", f"  (proposed by {record['proposed_by']} from {record['run']})"]
    for l in record["lessons"]:
        mark = "ok  " if l.get("ok") else "DROP"
        lines.append(f"  [{mark}] {l['kind']}  {l.get('why', '')}")
        if l["kind"] == "control":
            old = controls.get(key_sig(l["key"]))
            lines.append(f"         key {json.dumps(l['key'], ensure_ascii=False)}" + ("  (amends existing note)" if old else "  (new note)"))
            for f in ("what", "not_for"):
                if old and old.get(f) and old.get(f) != l.get(f):
                    lines.append(f"       - {f}: {old[f]}")
                if l.get(f):
                    lines.append(f"       + {f}: {l[f]}")
            if l.get("_matches"):
                lines.append(f"         attaches to: {', '.join(l['_matches'])}")
        elif l["kind"] == "page":
            old = pages.get(l.get("page"), {})
            lines.append(f"         page {l.get('page')}")
            for f in ("what", "not_here"):
                if l.get(f):
                    if old.get(f):
                        lines.append(f"       - {f}: {old[f]}")
                    lines.append(f"       + {f}: {l[f]}")
        else:
            lines.append(f"       + fact: {l.get('text')}")
        for r in l.get("rejected_because", []):
            lines.append(f"         rejected: {r}")
    return "\n".join(lines)


def move(name, to):
    src = LEARNED / "pending"
    files = sorted(src.glob("*.json")) if name == "all" else [src / pathlib.Path(name).name]
    for f in files:
        dest = LEARNED / to / f.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        f.rename(dest)
        print(f"{to}: {f.name}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("propose")
    p.add_argument("run_dir")
    p.add_argument("--goal-id", default="goal")
    p.add_argument("--check", default=None, help="the outcome check's JSON")
    sub.add_parser("list")
    for c in ("accept", "reject"):
        sub.add_parser(c).add_argument("name")
    a = ap.parse_args()
    if a.cmd == "propose":
        out, record = propose(a.run_dir, a.goal_id, json.loads(a.check) if a.check else None)
        print(show(record))
        print(f"\nwrote {out.relative_to(SHIM.parent)}")
    elif a.cmd == "list":
        for f in sorted((LEARNED / "pending").glob("*.json")):
            print(f.name)
            print(show(json.loads(f.read_text())))
    else:
        move(a.name, "accepted" if a.cmd == "accept" else "rejected")


if __name__ == "__main__":
    main()

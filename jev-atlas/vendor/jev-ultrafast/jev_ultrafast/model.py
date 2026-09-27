"""TypeSafe makes choices; an optional small OpenAI-compatible model writes field values."""

import datetime
import json
import math
import os
import time

import httpx

from . import atlas as atlas_file
from .questions import BLOCKED, NEXT_ACTION, PRESS_ENTER, TARGET, TEXT_VALUE

CLIENT = httpx.Client(http2=True, timeout=25)

# DONE and BLOCKED end the run, so they are answered against every operation that
# would have continued it. Taking the top label alone ended a run on BLOCKED 0.47
# while CLICK and TYPE_TEXT together held 0.53.
TERMINAL = ("DONE", "BLOCKED")

# Local change: the value format each native date/time input accepts.
TEMPORAL_FORMATS = {
    "date": "YYYY-MM-DD",
    "time": "HH:MM (24-hour)",
    "datetime-local": "YYYY-MM-DDTHH:MM",
    "month": "YYYY-MM",
    "week": "YYYY-Www",
}

# Local change (atlas shim): application knowledge, loaded once per path. Without
# JEV_ATLAS every function below behaves exactly as it did before.
LOADED_ATLASES = {}


def today():
    """Local change: the date of the run, YYYY-MM-DD. JEV_TODAY fixes it, for replays.

    The text helper has no calendar of its own: asked for "the end of January" on
    2026-09-22 it wrote 2026-01-31, a date already past.
    """
    wanted = os.environ.get("JEV_TODAY", "").strip()
    day = datetime.date.fromisoformat(wanted) if wanted else datetime.date.today()
    return day.isoformat()


def today_fact():
    """The page-context line naming today's date, when JEV_TODAY_FACT=1 asks for it."""
    if os.environ.get("JEV_TODAY_FACT") != "1":
        return []
    day = datetime.date.fromisoformat(today())
    return [f"Today is {day.isoformat()} ({day.strftime('%A')})."]


def current_atlas():
    path = os.environ.get("JEV_ATLAS")
    if not path:
        return None
    if path not in LOADED_ATLASES:
        LOADED_ATLASES[path] = atlas_file.load(path)
    return LOADED_ATLASES[path]


def match_fields(action, page_id):
    """The fields an atlas control key may be matched against, for one observed action."""
    return {
        "track_id": action.get("track_id"),
        "id": action.get("dom_id"),
        "title": action.get("title"),
        "href": action.get("href"),
        "ancestor": action.get("ancestor"),
        "row_label": action.get("row_label"),
        "section": action.get("section"),
        "landmark": action.get("landmark"),
        "role": action.get("role"),
        "text": action.get("label", "").split(" → ")[0],
        "page": page_id,
    }


def annotate(page, browser=None):
    """Attach atlas knowledge to an observed page: page context and per-control notes.

    No atlas, no change: this returns the page untouched, so a run without
    JEV_ATLAS sends exactly what it sent before.
    """
    book = current_atlas()
    if not book:
        return page
    matched = book.match_page(page.get("url"))
    page["page_id"] = matched["id"] if matched else None
    # One read-only evaluation per step: the page's facts and every overlay test.
    found = book.probe(browser, matched)
    dialog_title = page.get("dialog_title")
    overlays = book.active_overlays(found["selectors"], dialog_title)
    page["overlays"] = [o.get("id") for o in overlays]
    # A panel with no heading still has a name: the overlay that recognised it.
    by_selector = next((o for o in overlays if found["selectors"].get(o.get("id"))), None)
    page["dialog_name"] = dialog_title or (by_selector.get("name") if by_selector else None)
    covered = len({a["node"] for a in page["actions"] if a.get("covered") and "node" in a})
    page["context"] = atlas_file.page_context(
        matched,
        # Today's date (JEV_TODAY_FACT=1), global facts, then the page's own.
        today_fact() + found["facts"].get(atlas_file.GLOBAL, []) +
        (found["facts"].get(page["page_id"], []) if matched else []),
        page["dialog_name"],
        covered,
        overlays=[(o, found["facts"].get(o.get("id"), [])) for o in overlays],
    )
    # An overlay's id is in view only while it is open.
    in_view = [i for i in [page["page_id"], *page["overlays"]] if i]
    notes = {}
    for action in page["actions"]:
        if "node" not in action:
            continue
        entry = book.match_control(match_fields(action, page["page_id"]), in_view)
        if entry:
            note = {k: entry[k] for k in ("region", "what", "not_for", "options") if entry.get(k)}
            action["atlas"], action["atlas_key"] = note, entry.get("key")
            notes.setdefault(action["node"], (note, entry.get("key")))
    for action in page["actions"]:
        if "atlas" not in action and action.get("node") in notes:
            action["atlas"], action["atlas_key"] = notes[action["node"]]
    page["actions"] = [a for a in page["actions"] if not a.get("virtual")] + virtual_controls(found, matched, overlays)
    return page


def virtual_controls(found, matched, overlays):
    """Controls the application has but the DOM does not: spreadsheet cells and the like.

    Offered as TYPE_TEXT targets only, after the real elements, each carrying what
    the atlas says it is for. Writing one goes through the expression the atlas
    supplies, never through a synthesised click.
    """
    offered = []
    for entry in [matched, *overlays]:
        for control in found["virtual"].get((entry or {}).get("id"), []):
            note = {k: control[k] for k in ("region", "what", "not_for") if control.get(k)}
            action = {
                "id": f"v{len(offered) + 1}",
                "kind": "fill",
                "role": "textbox",
                "label": control["label"].strip(),
                "value": str(control.get("current_value") or ""),
                "node": f"virtual:{control.get('id') or control['label']}",
                "virtual": True,
                "set": control["set"],
                "page_id": (entry or {}).get("id"),
            }
            if isinstance(control.get("row_label"), str):
                action["row_label"] = control["row_label"]
            if note:
                action["atlas"] = note
            offered.append(action)
    return offered


def elements_debug(page):
    """Per-action diagnostics for the run log: why each control looked the way it did.

    This is never part of `state`; Jev does not see it. It exists so a step can be
    read back afterwards and the atlas fixed where it missed.
    """
    _elements, targets, _controls = action_space(page["actions"])
    index_by_node = {}
    for group in targets.values():
        for index, action in group.items():
            index_by_node.setdefault(action["node"], index.split(":")[0])
    return [
        {
            "index": index_by_node.get(action["node"]),
            "label": action["label"],
            "kind": action["kind"],
            "role": action.get("role"),
            "track_id": action.get("track_id"),
            "dom_id": action.get("dom_id"),
            "title": action.get("title"),
            "ancestor": action.get("ancestor"),
            "row_label": action.get("row_label"),
            "row_context": action.get("row_context"),
            "section": action.get("section"),
            "landmark": action.get("landmark"),
            "href": action.get("href"),
            "via_label": bool(action.get("via_label")),
            "offscreen_x": bool(action.get("offscreen_x")),
            "virtual": bool(action.get("virtual")),
            "list_open": bool(action.get("list_open")),
            "in_dialog": bool(action.get("in_dialog")),
            "covered": bool(action.get("covered")),
            "covered_by": action.get("covered_by"),
            "covered_by_busy": bool(action.get("covered_by_busy")),
            "matched_key": action.get("atlas_key"),
        }
        for action in page["actions"]
        if "node" in action
    ]


def post_json(url, key, body):
    for attempt in range(3):
        try:
            response = CLIENT.post(url, json=body, headers={"Authorization": f"Bearer {key}"})
        except httpx.HTTPError:
            raise RuntimeError("Model connection failed; no action executed.") from None
        if response.status_code in {429, 529, 503} and attempt < 2:
            time.sleep(0.5 * 2**attempt)
            continue
        if response.is_error:
            raise RuntimeError(f"Model provider returned HTTP {response.status_code}; no action executed.")
        return response.json()
    raise RuntimeError("Model unavailable")


def validate_choice(answer, ids):
    try:
        probabilities = answer["probabilities"]
        numbers = [*probabilities.values(), answer["confidence"]]
        valid = (
            answer["choice"] in ids
            and set(probabilities) == set(ids)
            and all(type(n) in (int, float) and math.isfinite(n) and 0 <= n <= 1 for n in numbers)
            and abs(sum(probabilities.values()) - 1) < 0.02
            and probabilities[answer["choice"]] >= max(probabilities.values()) - 1e-6
        )
    except (KeyError, TypeError, ValueError):
        valid = False
    if not valid:
        raise ValueError("Invalid TypeSafe response; no action executed.")
    return answer


def action_space(actions):
    """One index per observed element; each operation has its own valid target choices."""
    elements, indices, targets, controls = [], {}, {}, {}
    # Local change: "submit" is PRESS_ENTER, Enter in a field that holds a value.
    operations = {"click": "CLICK", "fill": "TYPE_TEXT", "select": "SELECT", "submit": "PRESS_ENTER"}
    for action in actions:
        kind = action["kind"]
        if kind not in operations:
            controls[action["id"].upper()] = action
            continue
        # Local change: an element whose centre belongs to something else cannot be
        # clicked; the executor refuses it as a stale target. Do not offer it.
        if action.get("covered"):
            continue
        node = action["node"]
        if node not in indices:
            index = str(len(elements) + 1)
            indices[node] = index
            element = {k: action[k] for k in ("role", "value", "checked", "selected", "expanded") if k in action}
            element.update(index=index, label=action["label"].split(" → ")[0], operations=[])
            for field in ("region", "what"):
                if (action.get("atlas") or {}).get(field):
                    element[field] = action["atlas"][field]
            # A suggestion says which field it would fill; its own label is only the value.
            if action.get("row_label") and action.get("role") in ("option", "menuitem", "menuitemradio"):
                element["for_field"] = action["row_label"]
            if action.get("list_open"):
                element["list_open"] = True
            # Local change: the identifying line of the row, list item or card the
            # control sits in ("WF-2026-0146" alone says nothing; its row's title does).
            if action.get("row_context"):
                element["row"] = action["row_context"]
            if kind == "select":
                element["value"] = action.get("current_value", "")
                element["options"] = []
            elements.append(element)
        index = indices[node]
        operation = operations[kind]
        group = targets.setdefault(operation, {})
        element = elements[int(index) - 1]
        if operation not in element["operations"]:
            element["operations"].append(operation)
        target = index
        if kind == "select":
            target = f"{index}:{len(element['options']) + 1}"
            element["options"].append({"index": target, "label": action["label"], "value": action["value"]})
        group[target] = action
    # Local change: several offered elements with one label ("Lock" on every row, two
    # "Grade" fields) are told apart by their row and their section, when those differ.
    first_action = {}
    for group in targets.values():
        for index, action in group.items():
            first_action.setdefault(index.split(":")[0], action)
    by_label = {}
    for element in elements:
        by_label.setdefault(element["label"], []).append(element)
    for same in by_label.values():
        if len(same) < 2:
            continue
        for field, name in (("row_label", "row"), ("section", "section")):
            values = [first_action.get(e["index"], {}).get(field) for e in same]
            if len(set(values)) > 1:
                for element, value in zip(same, values):
                    # A row context, when there is one, already says which row.
                    if value and name not in element:
                        element[name] = value
    return elements, targets, controls


def option(index, action, atlas_loaded, disambiguation=None):
    """One target choice. With an atlas match it carries what the control is for."""
    note = action.get("atlas") or {}
    choice = {"element": f"[{index}] {action['label']}"}
    choice.update({k: note[k] for k in ("region", "what", "not_for") if note.get(k)})
    choice["current_value"] = action.get("current_value", action.get("value", ""))
    choice.update({k: action[k] for k in ("role", "checked", "selected", "expanded") if k in action})
    for name in ("row", "section"):
        if disambiguation and disambiguation.get(name):
            choice[name] = disambiguation[name]
    if action.get("list_open"):
        choice["list_open"] = True
    if atlas_loaded:
        choice["in_dialog"] = bool(action.get("in_dialog"))
    return choice


def page_state(state, atlas_loaded):
    """What the model is told about the page itself."""
    page = {"url": state["url"], "title": state["title"]}
    if atlas_loaded and state.get("context"):
        page["context"] = state["context"]
    dialog = state.get("dialog_name") or state.get("dialog_title")
    if dialog:
        page["dialog"] = dialog
    if state.get("busy"):
        page["busy"] = True
    covered = len({a["node"] for a in state["actions"] if a.get("covered") and "node" in a})
    if covered:
        page["covered_controls"] = covered
    # Covered by a busy indicator is not covered by a dialog: the page is still drawing.
    busy_covered = len({a["node"] for a in state["actions"] if a.get("covered_by_busy") and "node" in a})
    if busy_covered:
        page["covered_by_busy"] = busy_covered
    if state.get("omitted_actions"):
        page["controls_not_shown"] = state["omitted_actions"]
    page["text"] = state["text"]
    return page


def share_notes(state, questions):
    """Local change: send an atlas note that several elements share once, not on each.

    A list of twenty ledger links matched by one atlas entry carried the same `what`
    and `not_for` on every element and again on every target choice. Elements and
    choices whose notes are identical (same `what` and `not_for`) now carry
    `"note": "N1"` instead, and `state.shared_notes.N1` holds the text once, with
    `elements` listing exactly which element indices it describes. `region` moves
    into the shared note only when every one of them has the same region. A note
    used by one element stays inline. Changes `state` and `questions` in place;
    returns the shared notes. JEV_SHARE_NOTES=0 turns it off.
    """
    notes, regions = {}, {}
    for name, question in questions.items():
        if not name.endswith("_target"):
            continue
        for index, choice in question["criteria"].items():
            element = index.split(":")[0]
            if choice.get("what") or choice.get("not_for"):
                notes.setdefault(element, (choice.get("what"), choice.get("not_for")))
                regions.setdefault(element, choice.get("region"))
    groups = {}
    for element, note in sorted(notes.items(), key=lambda item: int(item[0]) if item[0].isdigit() else 0):
        groups.setdefault(note, []).append(element)
    shared, key_of, moved = {}, {}, set()
    for (what, not_for), members in groups.items():
        if len(members) < 2:
            continue
        key = f"N{len(shared) + 1}"
        entry = {"elements": members}
        region = {regions.get(m) for m in members}
        if len(region) == 1 and None not in region:
            entry["region"] = region.pop()
            moved.add(key)
        if what:
            entry["what"] = what
        if not_for:
            entry["not_for"] = not_for
        shared[key] = entry
        for member in members:
            key_of[member] = key
    if not shared:
        return shared

    def point(item, index, fields):
        key = key_of.get(index)
        if not key:
            return
        for field in fields + (("region",) if key in moved else ()):
            item.pop(field, None)
        item["note"] = key

    for element in state.get("elements", []):
        point(element, element["index"], ("what", "not_for"))
    for name, question in questions.items():
        if name.endswith("_target"):
            for index, choice in question["criteria"].items():
                point(choice, index.split(":")[0], ("what", "not_for"))
    # Right after the elements it describes.
    rebuilt = {}
    for field, value in list(state.items()):
        rebuilt[field] = value
        if field == "elements":
            rebuilt["shared_notes"] = shared
    rebuilt.setdefault("shared_notes", shared)
    state.clear()
    state.update(rebuilt)
    return shared


def progress_over_terminal(answer):
    """Keep going when the progress operations outvote a terminal one.

    A terminal operation below JEV_TERMINAL_MAJORITY loses to the summed
    probability of the operations that would continue the run, and the highest
    of those is taken instead, with the target head it was already answered
    with. JEV_TERMINAL_MAJORITY=0 restores taking the top label.
    The three-unchanged-steps rule still ends a run that goes nowhere.
    """
    threshold = float(os.environ.get("JEV_TERMINAL_MAJORITY", "0.5"))
    operation, probabilities = answer["choice"], answer["probabilities"]
    if threshold <= 0 or operation not in TERMINAL:
        return operation, None
    progress = {k: v for k, v in probabilities.items() if k not in TERMINAL}
    if not progress or probabilities[operation] >= threshold:
        return operation, None
    best = max(progress, key=progress.get)
    if sum(progress.values()) <= probabilities[operation] or progress[best] <= 0:
        return operation, None
    print(
        f"Progress over terminal: {operation} {probabilities[operation]:.2f} vs "
        f"{sum(progress.values()):.2f} across {', '.join(progress)}; taking {best}",
        flush=True,
    )
    return best, "progress-over-terminal"


def choose(state, goal, history):
    elements, targets, controls = action_space(state["actions"])
    labels = {
        "CLICK": "Click an element, button, menu option, autocomplete suggestion, or calendar day.",
        "TYPE_TEXT": "Enter or replace text in an editable field. A small LLM will supply the value from the goal.",
        "SELECT": "Select an observed dropdown value.",
        # Local change: a search box with no Search button is submitted with Enter.
        "PRESS_ENTER": PRESS_ENTER,
    }
    operations = {key: labels[key] for key in targets}
    operations.update({key: value["label"] for key, value in controls.items()})
    operations.update(DONE="Every requirement is visibly satisfied.", BLOCKED=BLOCKED)
    questions = {
        "operation": {"type": "choice", "criteria": operations, "instructions": {"goal": goal, "rules": NEXT_ACTION}}
    }
    atlas_loaded = current_atlas() is not None
    by_index = {e["index"]: e for e in elements}
    for operation, candidates in targets.items():
        questions[operation.lower() + "_target"] = {
            "type": "choice",
            "criteria": {index: option(index, a, atlas_loaded, by_index.get(index.split(":")[0]))
                         for index, a in candidates.items()},
            "instructions": {"goal": goal, "operation": operation, "rules": [NEXT_ACTION, TARGET]},
        }
    body = {
        "model": os.environ.get("TYPESAFE_MODEL", "jev-latest"),
        "state": {
            "page": page_state(state, atlas_loaded),
            "elements": elements,
            "recent_actions": [
                {k: h.get(k) for k in ("action", "kind", "text", "page_changed")} for h in history[-10:]
            ],
        },
        "questions": questions,
    }
    if os.environ.get("JEV_SHARE_NOTES", "1") != "0":
        share_notes(body["state"], questions)
    started = time.perf_counter()
    result = post_json("https://api.typesafe.ai/v1/systemone", os.environ["TYPESAFE_API_KEY"], body)
    operation_answer = validate_choice(result["answers"].get("operation", {}), operations)
    operation, policy = progress_over_terminal(operation_answer)
    target = None
    target_answer = None
    probabilities = {}
    if operation in targets:
        # Unused target heads cannot cause an action. Validate the head selected by the operation.
        target_answer = validate_choice(result["answers"].get(operation.lower() + "_target", {}), targets[operation])
        target = target_answer["choice"]
        choice = targets[operation][target]["id"]
        probabilities = {a["id"]: target_answer["probabilities"][index] for index, a in targets[operation].items()}
    else:
        choice = controls[operation]["id"] if operation in controls else operation
        probabilities[choice] = operation_answer["probabilities"][operation]
    return {
        "choice": choice,
        "operation": operation,
        "policy": policy,
        "original_operation": operation_answer["choice"] if policy else None,
        "target": target,
        "confidence": operation_answer["confidence"],
        "probabilities": probabilities,
        "operation_probabilities": operation_answer["probabilities"],
        "target_probabilities": target_answer["probabilities"] if target_answer else {},
        "target_confidence": target_answer["confidence"] if target_answer else None,
        "raw_answers": result["answers"],
        "model": result["model"],
        "usage": result.get("usage", {}),
        "latency_ms": round((time.perf_counter() - started) * 1000),
        "request": body,
    }


def field_context(goal, action, page, history):
    # Local change: the field's row label, and what the atlas says the field is
    # for. `options`, when the atlas fixes the set, is what the value must match.
    note = action.get("atlas") or {}
    field = {k: action.get(k) for k in ("label", "role", "value")}
    if action.get("row_label"):
        field["row_label"] = action["row_label"]
    if action.get("section"):
        field["section"] = action["section"]
    # A native date/time input takes one wire format; the executor also converts common spellings.
    if action.get("input_type") in TEMPORAL_FORMATS:
        field["format"] = TEMPORAL_FORMATS[action["input_type"]]
    field.update({k: note[k] for k in ("what", "not_for", "options") if note.get(k)})
    # Local change: row context, and today's date so a relative or partial date in the
    # goal ("the end of January") resolves to its next occurrence, not a past one.
    # `today` goes first: replayed on the logged "end of January" field (gpt-4.1-mini,
    # 3 calls each), it was ignored after the goal (2026-01-31 3/3) and used when it
    # led the input (2027-01-31 3/3).
    if action.get("row_context"):
        field["row"] = action["row_context"]
    return {
        "today": today(),
        "goal": goal,
        "field": field,
        "page": {"title": page["title"], "text": page["text"][:6000]},
        "recent_actions": [{k: h.get(k) for k in ("action", "text")} for h in history[-6:]],
    }


def field_text(context):
    key = os.environ.get("TEXT_MODEL_API_KEY")
    if not key:
        raise ValueError("TYPE_TEXT needs TEXT_MODEL_API_KEY; no text is hardcoded or guessed by the executor.")
    base = os.environ.get("TEXT_MODEL_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
    model = os.environ.get("TEXT_MODEL", "deepseek-chat")
    reasoning = {"thinking": {"type": "disabled"}} if "api.deepseek.com/" in base else {"reasoning": {"effort": "low"}}
    if os.environ.get("TEXT_MODEL_REASONING") == "none":
        reasoning = {"reasoning": {"enabled": False}}
    # Local change: `reasoning` is an OpenRouter/DeepSeek extension. OpenAI's own API
    # rejects the whole request with 400 "Unrecognized request argument supplied: reasoning".
    if "api.openai.com/" in base:
        reasoning = {}
    # Local change: api.openai.com GPT-5 models want max_completion_tokens and
    # reasoning_effort ("none") instead of max_tokens; other models are unchanged.
    limit = {"max_tokens": 1024}
    if "api.openai.com/" in base and model.startswith("gpt-5"):
        limit, reasoning = {"max_completion_tokens": 1024}, {"reasoning_effort": "none"}
    started = time.perf_counter()
    result = post_json(
        base + "/chat/completions",
        key,
        {
            "model": model,
            **limit,
            "response_format": {"type": "json_object"},
            **reasoning,
            "messages": [
                {"role": "system", "content": TEXT_VALUE},
                {
                    "role": "user",
                    "content": json.dumps(context),
                },
            ],
        },
    )
    try:
        output = json.loads(result["choices"][0]["message"]["content"])
        value = output["text"]
        if set(output) != {"text"} or not isinstance(value, str) or not value.strip() or len(value) > 2000:
            raise ValueError()
    except (ValueError, KeyError, TypeError):
        raise ValueError("Text helper returned no valid field value; nothing typed.") from None
    return value, {
        "model": model,
        "latency_ms": round((time.perf_counter() - started) * 1000),
        "usage": result.get("usage", {}),
    }

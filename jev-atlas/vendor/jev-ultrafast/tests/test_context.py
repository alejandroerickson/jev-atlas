"""Local change: what the model is told beyond the page itself.

Shared atlas notes, today's date, row context and the operation rules.
"""

import copy
import json

from jev_ultrafast import model, questions

LEDGER = {"region": "Ledger", "what": "An item that needs action.", "not_for": "Acting on it here."}


def ledger_actions():
    actions = [
        {"id": f"e{i}", "kind": "click", "role": "link", "label": f"Item {i}", "value": "", "node": i,
         "atlas": dict(LEDGER), "row_context": f"Approval due · due in {i} days"}
        for i in (1, 2, 3)
    ]
    actions.append({"id": "e4", "kind": "click", "role": "button", "label": "Save", "value": "", "node": 4,
                    "atlas": {"what": "Saves the page."}})
    actions.append({"id": "e5", "kind": "click", "role": "link", "label": "Other", "value": "", "node": 5})
    actions.append({"id": "wait", "kind": "wait", "label": "Wait"})
    return actions


def request(monkeypatch, actions=None, **env):
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("TYPESAFE_API_KEY", "test")
    monkeypatch.setattr(model, "current_atlas", lambda: object())
    sent = {}

    def post(_url, _key, body):
        sent.update(copy.deepcopy(body))
        return {"model": "jev-test", "answers": {
            "operation": {"choice": "WAIT", "confidence": 1, "probabilities": {
                k: float(k == "WAIT") for k in body["questions"]["operation"]["criteria"]}}}}

    monkeypatch.setattr(model, "post_json", post)
    page = {"url": "https://host/app", "title": "App", "text": "", "actions": actions or ledger_actions()}
    model.choose(page, "Open the approval due in two days", [])
    return sent


def test_a_note_shared_by_several_elements_is_sent_once(monkeypatch):
    body = request(monkeypatch)
    state, target = body["state"], body["questions"]["click_target"]["criteria"]
    assert state["shared_notes"] == {"N1": {"elements": ["1", "2", "3"], **LEDGER}}
    # The elements and choices it describes point at it and no longer repeat it.
    for index in ("1", "2", "3"):
        element = state["elements"][int(index) - 1]
        assert element["note"] == "N1" and "what" not in element and "region" not in element
        assert target[index]["note"] == "N1"
        assert not {"what", "not_for", "region"} & set(target[index])
    # A note used once stays inline; an element with no note gets none.
    assert target["4"]["what"] == "Saves the page." and "note" not in target["4"]
    assert "note" not in target["5"] and "note" not in state["elements"][4]
    assert list(state) == ["page", "elements", "shared_notes", "recent_actions"]


def test_shared_notes_keep_a_region_that_differs_inline(monkeypatch):
    actions = ledger_actions()
    actions[2]["atlas"] = {**LEDGER, "region": "Elsewhere"}
    body = request(monkeypatch, actions)
    note = body["state"]["shared_notes"]["N1"]
    assert "region" not in note and note["elements"] == ["1", "2", "3"]
    assert body["questions"]["click_target"]["criteria"]["3"]["region"] == "Elsewhere"


def test_sharing_notes_can_be_turned_off_and_makes_the_request_smaller(monkeypatch):
    full = request(monkeypatch, JEV_SHARE_NOTES="0")
    assert "shared_notes" not in full["state"]
    assert full["questions"]["click_target"]["criteria"]["2"]["not_for"] == LEDGER["not_for"]
    shared = request(monkeypatch, JEV_SHARE_NOTES="1")
    assert len(json.dumps(shared)) < len(json.dumps(full))


def test_every_element_carries_its_row_context(monkeypatch):
    body = request(monkeypatch)
    rows = [e.get("row") for e in body["state"]["elements"]]
    assert rows == ["Approval due · due in 1 days", "Approval due · due in 2 days",
                    "Approval due · due in 3 days", None, None]
    assert body["questions"]["click_target"]["criteria"]["2"]["row"] == "Approval due · due in 2 days"


def test_navigation_toward_the_goal_is_progress_and_blocked_means_no_way_forward(monkeypatch):
    body = request(monkeypatch)
    operation = body["questions"]["operation"]
    assert "leads toward where the goal is done counts as progress" in operation["instructions"]["rules"]
    assert "BLOCKED means no supported operation can make progress." in operation["instructions"]["rules"]
    assert operation["criteria"]["BLOCKED"] == questions.BLOCKED
    assert "not even navigating toward a page" in questions.BLOCKED
    assert operation["criteria"]["DONE"] == "Every requirement is visibly satisfied."


def test_the_text_helper_is_told_today(monkeypatch):
    monkeypatch.setenv("JEV_TODAY", "2026-09-22")
    action = {"label": "Next gate", "role": "textbox", "value": "2026-10-15", "input_type": "date",
              "row_context": "Lorimer · Scoping study"}
    context = model.field_context("Move the gate to the end of January", action, {"title": "T", "text": ""}, [])
    assert context["today"] == "2026-09-22" and list(context)[0] == "today"
    assert context["field"]["row"] == "Lorimer · Scoping study"
    assert "against today" in questions.TEXT_VALUE
    monkeypatch.delenv("JEV_TODAY")
    import datetime
    assert model.today() == datetime.date.today().isoformat()


def test_today_is_a_page_fact_only_when_asked(monkeypatch):
    monkeypatch.setenv("JEV_TODAY", "2026-09-22")
    monkeypatch.delenv("JEV_TODAY_FACT", raising=False)
    assert model.today_fact() == []
    monkeypatch.setenv("JEV_TODAY_FACT", "1")
    assert model.today_fact() == ["Today is 2026-09-22 (Tuesday)."]

"""Offline contracts for a dynamic operation/target policy. No paid APIs."""

import json
import time
from copy import deepcopy
from unittest.mock import Mock

import pytest

from jev_ultrafast import agent as loop
from jev_ultrafast import model
from jev_ultrafast.browser import StalePage, browser_operation, fingerprint


def page():
    state = {
        "url": "https://example.test/",
        "title": "Search",
        "text": "Search",
        "scroll": {"y": 0},
        "actions": [
            {"id": "e1", "kind": "fill", "label": "Search", "role": "textbox", "value": "", "node": 10},
            {"id": "e2", "kind": "click", "label": "Open Search", "role": "textbox", "value": "", "node": 10},
            {"id": "e3", "kind": "click", "label": "Go", "role": "button", "value": "", "node": 20},
            {"id": "wait", "kind": "wait", "label": "Wait"},
        ],
    }
    state["fingerprint"] = fingerprint(state)
    return state


def choice(ids, selected):
    return {"choice": selected, "confidence": 1.0, "probabilities": {i: float(i == selected) for i in ids}}


def decision(action="e1"):
    return {
        "choice": action,
        "operation": "TYPE_TEXT",
        "target": "1",
        "confidence": 1.0,
        "probabilities": {action: 1.0},
        "latency_ms": 10,
        "usage": {},
    }


@pytest.mark.parametrize("mutation", ["unknown", "nan", "missing", "negative", "non_max", "confidence"])
def test_invalid_choice_is_rejected(mutation):
    a = choice(["a", "b"], "a")
    if mutation == "unknown":
        a["choice"] = "invented"
    elif mutation == "nan":
        a["probabilities"]["a"] = float("nan")
    elif mutation == "missing":
        del a["probabilities"]["b"]
    elif mutation == "negative":
        a["probabilities"]["b"] = -1
    elif mutation == "non_max":
        a["choice"] = "b"
    else:
        a["confidence"] = 5
    with pytest.raises(ValueError, match="Invalid TypeSafe"):
        model.validate_choice(a, {"a", "b"})


def test_one_index_per_node_with_operation_specific_targets():
    elements, targets, controls = model.action_space(page()["actions"])
    assert len(elements) == 2
    assert elements[0]["operations"] == ["TYPE_TEXT", "CLICK"]
    assert targets["TYPE_TEXT"]["1"]["id"] == "e1"
    assert targets["CLICK"]["1"]["id"] == "e2"
    assert targets["CLICK"]["2"]["id"] == "e3"
    assert "WAIT" in controls


def test_all_heads_are_one_request_and_only_matching_head_executes(monkeypatch):
    calls = []

    def post(_url, _key, body):
        calls.append(body)
        return {
            "model": "test",
            "answers": {
                "operation": choice(body["questions"]["operation"]["criteria"], "TYPE_TEXT"),
                "type_text_target": choice(["1"], "1"),
                "click_target": {"choice": "invented"},
            },
        }

    monkeypatch.setenv("TYPESAFE_API_KEY", "test")
    monkeypatch.setattr(model, "post_json", post)
    d = model.choose(page(), "Find a book", [])
    assert len(calls) == 1
    assert d["operation"] == "TYPE_TEXT" and d["target"] == "1" and d["choice"] == "e1"
    assert set(calls[0]["questions"]) == {"operation", "click_target", "type_text_target"}


def test_click_cannot_consume_a_text_target(monkeypatch):
    def post(_url, _key, body):
        return {
            "model": "test",
            "answers": {
                "operation": choice(body["questions"]["operation"]["criteria"], "CLICK"),
                "type_text_target": choice(["1"], "1"),
                "click_target": choice(["1", "2", "999"], "999"),
            },
        }

    monkeypatch.setenv("TYPESAFE_API_KEY", "test")
    monkeypatch.setattr(model, "post_json", post)
    with pytest.raises(ValueError, match="Invalid TypeSafe"):
        model.choose(page(), "Find a book", [])


def test_target_head_receives_control_state_and_full_next_step_rules(monkeypatch):
    p = page()
    p["actions"].insert(0, {
        "id": "toggle", "kind": "click", "label": "Free cancellation", "node": 30,
        "role": "checkbox", "checked": "true", "selected": False,
    })

    def post(_url, _key, body):
        questions = body["questions"]
        target = questions["click_target"]
        assert target["criteria"]["1"]["checked"] == "true"
        assert target["criteria"]["1"]["selected"] is False
        assert questions["operation"]["instructions"]["rules"] in target["instructions"]["rules"]
        return {
            "model": "test",
            "answers": {
                "operation": choice(questions["operation"]["criteria"], "CLICK"),
                "click_target": choice(target["criteria"], "3"),
            },
        }

    monkeypatch.setenv("TYPESAFE_API_KEY", "test")
    monkeypatch.setattr(model, "post_json", post)
    d = model.choose(p, "Search with free cancellation", [])
    assert d["choice"] == "e3"


def blocked_answers(body, blocked=0.47):
    """BLOCKED on top, but CLICK and TYPE_TEXT together outweigh it."""
    ids = body["questions"]["operation"]["criteria"]
    rest = round(1 - blocked, 2)
    probabilities = {i: 0.0 for i in ids}
    probabilities.update(BLOCKED=blocked, CLICK=round(rest * 0.53, 2), TYPE_TEXT=round(rest - round(rest * 0.53, 2), 2))
    return {
        "model": "test",
        "answers": {
            "operation": {"choice": "BLOCKED", "confidence": 0.5, "probabilities": probabilities},
            "click_target": choice(body["questions"]["click_target"]["criteria"], "2"),
            "type_text_target": choice(body["questions"]["type_text_target"]["criteria"], "1"),
        },
    }


def test_progress_operations_outvote_a_minority_terminal_choice(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "test")
    monkeypatch.delenv("JEV_TERMINAL_MAJORITY", raising=False)
    monkeypatch.setattr(model, "post_json", lambda _u, _k, body: blocked_answers(body))
    d = model.choose(page(), "Find a book", [])
    # 0.47 BLOCKED against 0.53 across CLICK and TYPE_TEXT: the run continues.
    assert d["policy"] == "progress-over-terminal" and d["original_operation"] == "BLOCKED"
    assert d["operation"] == "CLICK" and d["target"] == "2" and d["choice"] == "e3"


@pytest.mark.parametrize("setting,blocked", [("0", 0.47), ("0.5", 0.6), ("0.9", 0.95)])
def test_a_terminal_choice_stands_when_it_has_the_majority_or_the_rule_is_off(monkeypatch, setting, blocked):
    monkeypatch.setenv("TYPESAFE_API_KEY", "test")
    monkeypatch.setenv("JEV_TERMINAL_MAJORITY", setting)
    monkeypatch.setattr(model, "post_json", lambda _u, _k, body: blocked_answers(body, blocked))
    d = model.choose(page(), "Find a book", [])
    assert d["operation"] == "BLOCKED" and d["choice"] == "BLOCKED"
    assert d["policy"] is None and d["original_operation"] is None


def probe(controls=10, covered=0, busy=False, dialog=False, resources=5, url="https://example.test/"):
    return {"url": url, "controls": controls, "covered": covered, "busy": busy,
            "dialog": dialog, "resources": resources}


def settle_reads(probes, monkeypatch):
    """How many probes settle() takes before it is satisfied."""
    import jev_ultrafast.browser as browser

    b = browser.Browser.__new__(browser.Browser)
    reads = []
    b.evaluate = lambda _expression: (reads.append(1), probes[min(len(reads) - 1, len(probes) - 1)])[1]
    monkeypatch.setattr(browser.time, "sleep", lambda _seconds: None)
    b.settle()
    return len(reads)


def test_settle_waits_for_three_quiet_polls(monkeypatch):
    assert settle_reads([probe()] * 4, monkeypatch) == 3
    assert settle_reads([probe(controls=42), probe(controls=56), *[probe(controls=61)] * 5], monkeypatch) == 5


def test_settle_waits_out_a_loading_mask(monkeypatch):
    assert settle_reads([probe(busy=True)] * 3 + [probe()] * 4, monkeypatch) == 4


def test_settle_waits_for_covered_controls_to_stop_falling(monkeypatch):
    # No dialog is open, so covered controls mean something is drawn over the page.
    probes = [probe(covered=15), probe(covered=15), probe(covered=9), probe(covered=5), probe(covered=5)]
    assert settle_reads(probes + [probe(covered=5)], monkeypatch) == 5
    # With a dialog open, controls behind it are expected and settle immediately.
    assert settle_reads([probe(covered=15, dialog=True)] * 4, monkeypatch) == 3


def test_a_busy_page_waits_itself_out_before_spending_a_model_call(runner, monkeypatch):
    asked = []
    monkeypatch.setattr(loop, "choose", lambda *args: asked.append(args) or decision("e3"))
    runner.state["page"]["busy"] = True
    runner.state["decision"] = None
    for _ in range(3):
        runner.command("tick")
    assert not asked, "a page hidden behind a busy indicator is not a page to decide from"
    assert [h["policy"] for h in runner.state["history"]] == ["auto-wait-busy"] * 3
    assert runner.state["browser"].settle.call_count == 3
    runner.command("tick")  # the fourth lets Jev see the page, busy and all
    assert len(asked) == 1
    assert runner.state["history"][-1]["kind"] == "click"


def test_quoted_task_text_still_uses_the_llm(monkeypatch):
    monkeypatch.setenv("TEXT_MODEL_API_KEY", "test")
    post = Mock(return_value={"choices": [{"message": {"content": '{"text":"Zurich"}'}}]})
    monkeypatch.setattr(model, "post_json", post)
    context = model.field_context('Fly from "Zurich" to London', page()["actions"][0], page(), [])
    assert model.field_text(context)[0] == "Zurich"
    assert post.call_count == 1
    sent = json.loads(post.call_args.args[2]["messages"][1]["content"])
    assert sent["goal"] == 'Fly from "Zurich" to London'


def test_missing_text_credential_stops_before_guessing(monkeypatch):
    monkeypatch.delenv("TEXT_MODEL_API_KEY", raising=False)
    with pytest.raises(ValueError, match="TEXT_MODEL_API_KEY"):
        model.field_text({"goal": 'Enter "Zurich"'})


@pytest.fixture
def runner():
    a = loop.Agent.__new__(loop.Agent)
    a.screenshots = False
    a.pending_text = None
    p = page()
    a.state = {
        "browser": Mock(fresh=Mock(return_value=True), observe=Mock(return_value=p)),
        "page": p,
        "decision": decision(),
        "goal": "Find a book",
        "history": [],
        "decisions": [],
        "status": "predicted",
        "started_at": time.perf_counter(),
        "record": False,
        "text_calls": [],
    }
    return a


def test_stale_decision_is_consumed_before_any_mutation(runner):
    runner.state["browser"].fresh.return_value = False
    with pytest.raises(StalePage):
        runner.command("act", {"fingerprint": runner.state["page"]["fingerprint"]})
    runner.state["browser"].act.assert_not_called()
    assert runner.state["decision"] is None


def test_generated_text_reused_only_for_identical_retry_context(runner, monkeypatch):
    helper = Mock(return_value=("book", {"model": "test", "latency_ms": 10}))
    monkeypatch.setattr(loop, "field_text", helper)
    runner.state["browser"].act.side_effect = [StalePage("Changed before input"), None]
    with pytest.raises(StalePage):
        runner.command("act", {"fingerprint": runner.state["page"]["fingerprint"]})
    runner.state["decision"] = decision()
    runner.command("act", {"fingerprint": runner.state["page"]["fingerprint"]})
    assert helper.call_count == 1
    assert runner.state["browser"].act.call_count == 2  # The first call rejects before any browser input.
    assert runner.pending_text is None


def test_changed_field_context_does_not_reuse_generated_text(runner, monkeypatch):
    helper = Mock(return_value=("book", {"model": "test", "latency_ms": 10}))
    monkeypatch.setattr(loop, "field_text", helper)
    runner.state["browser"].act.side_effect = [StalePage("Changed before input"), None]
    with pytest.raises(StalePage):
        runner.command("act", {"fingerprint": runner.state["page"]["fingerprint"]})
    runner.state["page"]["text"] = "Different page context"
    runner.state["decision"] = decision()
    runner.command("act", {"fingerprint": runner.state["page"]["fingerprint"]})
    assert helper.call_count == 2


def test_loading_waits_do_not_trigger_no_progress_stop(runner):
    for _ in range(5):
        runner.state["decision"] = decision("wait")
        runner.command("act", {"fingerprint": runner.state["page"]["fingerprint"]})
    assert len(runner.state["history"]) == 5 and runner.state["status"] == "ready"


def test_stale_observation_preserves_executed_action(runner):
    runner.state["decision"] = decision("e3")
    runner.state["browser"].observe.side_effect = StalePage("changed")
    with pytest.raises(StalePage):
        runner.command("act", {"fingerprint": runner.state["page"]["fingerprint"]})
    assert runner.state["history"][-1]["action"] == "Go"
    runner.state["browser"].act.assert_called_once()


def test_observation_is_one_atomic_browser_read(monkeypatch):
    import jev_ultrafast.browser as browser

    p = page()
    cdp = Mock(return_value={"result": {"value": p}})
    monkeypatch.setattr(browser, "cdp", cdp)
    actual = browser_operation({"operation": "observe", "session": "test", "screenshot": False})
    assert actual["actions"] == p["actions"]
    assert cdp.call_count == 1
    assert cdp.call_args.args[0] == "Runtime.evaluate"


def test_executor_rejects_a_stale_page_before_browser_input(monkeypatch):
    import jev_ultrafast.browser as browser

    b = browser.Browser.__new__(browser.Browser)
    b.fresh = Mock(return_value=False)
    operation = Mock()
    monkeypatch.setattr(browser, "browser_operation", operation)
    with pytest.raises(StalePage):
        b.act(page()["actions"][0], page(), "book")
    operation.assert_not_called()


@pytest.mark.parametrize("response", [{"exceptionDetails": {}}, {"result": {}}])
def test_interrupted_dropdown_mutation_cannot_be_retried_as_stale(monkeypatch, response):
    import jev_ultrafast.browser as browser

    # A navigation can destroy the evaluation result after the change event already fired.
    if "exceptionDetails" in response:
        response["exceptionDetails"] = {"text": "Execution context destroyed"}
    cdp = Mock(return_value=response)
    monkeypatch.setattr(browser, "cdp", cdp)
    with pytest.raises(RuntimeError, match="Dropdown execution"):
        browser_operation({"operation": "act", "session": "test", "action": {
            "id": "e1", "kind": "select", "node": 1, "value": "Design",
        }})
    assert cdp.call_count == 1


def test_fingerprint_tracks_values_and_identity_not_screenshots():
    p = page()
    other = deepcopy(p)
    other["screenshot"] = "changed"
    assert fingerprint(p) == fingerprint(other)
    other["actions"][0]["node"] = 99
    assert fingerprint(p) != fingerprint(other)


@pytest.mark.parametrize("changed", ["Departure", "Where from?", "Where to?", "year"])
def test_flight_verification_rejects_wrong_trip(changed):
    from examples.flights import verify

    actual = {
        "url": "https://www.google.com/travel/flights/search?tfs=example",
        "text": "Track prices from Zürich to London departing 2026-09-20",
        "actions": [
            {"label": k, "value": v}
            for k, v in [
                ("Change ticket type. One way", "One way"),
                ("Where from?", "Zürich"),
                ("Where to?", "London"),
                ("Departure", "Sun, Sep 20"),
                ("Nonstop flight on Sunday, September 20. Select flight", ""),
            ]
        ],
    }
    assert verify(actual)["passed"]
    if changed == "year":
        actual["text"] = actual["text"].replace("2026", "2027")
    else:
        next(a for a in actual["actions"] if a["label"] == changed)["value"] = "wrong"
    assert not verify(actual)["passed"]


@pytest.mark.parametrize(
    "content", ["Thinking: Zurich", '{"text":null}', '{"text":"Zurich","extra":true}', '{"text":123}']
)
def test_text_helper_rejects_invalid_values(monkeypatch, content):
    monkeypatch.setenv("TEXT_MODEL_API_KEY", "test")
    monkeypatch.setattr(model, "post_json", Mock(return_value={"choices": [{"message": {"content": content}}]}))
    with pytest.raises(ValueError, match="nothing typed"):
        model.field_text({"goal": "Find a flight"})


def test_navigation_during_prediction_reobserves_without_action(runner):
    runner.state["browser"].fresh.side_effect = StalePage("Document navigating")
    runner.command("tick")
    assert runner.state["status"] == "ready"
    assert runner.state["decision"] is None
    runner.state["browser"].act.assert_not_called()


def submit_page():
    """The search box holds a value, so it is offered for PRESS_ENTER as well as typing."""
    p = page()
    p["actions"][0]["value"] = "PRJ-0441"
    p["actions"].insert(1, {"id": "e4", "kind": "submit", "label": "Search", "role": "textbox",
                            "value": "PRJ-0441", "node": 10})
    p["fingerprint"] = fingerprint(p)
    return p


def test_press_enter_is_an_operation_with_its_own_target_head(monkeypatch):
    sent = []

    def post(_url, _key, body):
        sent.append(body)
        questions = body["questions"]
        return {
            "model": "test",
            "answers": {
                "operation": choice(questions["operation"]["criteria"], "PRESS_ENTER"),
                "press_enter_target": choice(questions["press_enter_target"]["criteria"], "1"),
                "click_target": choice(questions["click_target"]["criteria"], "2"),
                "type_text_target": choice(questions["type_text_target"]["criteria"], "1"),
            },
        }

    monkeypatch.setenv("TYPESAFE_API_KEY", "test")
    monkeypatch.setattr(model, "post_json", post)
    d = model.choose(submit_page(), "Search for PRJ-0441", [])
    assert d["operation"] == "PRESS_ENTER" and d["choice"] == "e4"
    questions = sent[0]["questions"]
    assert "Press Enter" in questions["operation"]["criteria"]["PRESS_ENTER"]
    assert list(questions["press_enter_target"]["criteria"]) == ["1"]
    assert sent[0]["state"]["elements"][0]["operations"] == ["TYPE_TEXT", "PRESS_ENTER", "CLICK"]


def test_no_press_enter_without_a_submittable_field():
    _elements, targets, _controls = model.action_space(page()["actions"])
    assert "PRESS_ENTER" not in targets


def test_press_enter_executes_without_asking_the_text_helper(runner, monkeypatch):
    p = submit_page()
    runner.state["page"] = p
    runner.state["browser"].observe.return_value = p
    runner.state["decision"] = {**decision("e4"), "operation": "PRESS_ENTER"}
    monkeypatch.setattr(loop, "field_text", Mock(side_effect=AssertionError("no text for Enter")))
    runner.command("act", {"fingerprint": p["fingerprint"]})
    action, _page = runner.state["browser"].act.call_args.args
    assert action["kind"] == "submit" and runner.state["browser"].act.call_args.kwargs["text"] is None
    assert runner.state["history"][-1]["kind"] == "submit"

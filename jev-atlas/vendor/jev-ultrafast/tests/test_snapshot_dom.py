"""snapshot.js and the executor against a real page (tests/fixtures/hash-app.html).

Local change. Runs a headless Chrome over CDP; skipped when none is installed.
"""

from pathlib import Path

import pytest
from headless import Chrome, find_chrome

from jev_ultrafast import atlas as atlas_file
from jev_ultrafast import browser, model

pytestmark = pytest.mark.skipif(not find_chrome(), reason="no Chrome or Chromium binary")

HTML = (Path(__file__).parent / "fixtures" / "hash-app.html").read_text()


@pytest.fixture(scope="module")
def chrome():
    instance = Chrome()
    yield instance
    instance.close()


@pytest.fixture
def page(chrome, monkeypatch):
    chrome.load(HTML)
    # The executor speaks to the browser through browser_harness's cdp(); route it here.
    monkeypatch.setattr(browser, "cdp", lambda method, session_id=None, **params:
                        chrome.send(method, session_id=session_id,
                                    **{k: v for k, v in params.items() if not k.startswith("_")}))
    return chrome


def observe(chrome, lists=None):
    return browser.browser_operation({"operation": "observe", "session": chrome.session, "screenshot": False,
                                      "selectors": lists or atlas_file.selector_lists(None)})


def by_label(state, label, kind=None):
    return [a for a in state["actions"] if a.get("label") == label and (kind is None or a["kind"] == kind)]


def test_hash_routes_keep_their_fragment_and_in_page_anchors_do_not(page):
    state = observe(page)
    hrefs = {a["label"]: a.get("href") for a in state["actions"] if a.get("role") == "link"}
    assert hrefs["Portfolio"] == "/app/#/portfolio"
    assert hrefs["Legacy"] == "/app/#!/legacy"
    assert hrefs["Skip to content"] == "/app/"
    assert hrefs["Plain anchor"] == "/app/other?x=1"


def test_landmarks_tell_a_top_bar_link_from_a_breadcrumb(page):
    state = observe(page)
    projects = by_label(state, "Projects")
    assert sorted(a["landmark"] for a in projects) == ["navigation: Breadcrumb", "navigation: Sections"]
    assert by_label(state, "Skip to content")[0]["landmark"] == "banner"
    book = atlas_file.Atlas({"controls": [
        {"key": {"text": "Projects", "landmark": "navigation: Sections"}, "what": "Top bar."},
        {"key": {"text": "Projects", "landmark_contains": "Breadcrumb"}, "what": "Breadcrumb."},
    ]})
    notes = [book.match_control(model.match_fields(a, None))["what"] for a in projects]
    assert sorted(notes) == ["Breadcrumb.", "Top bar."]


def test_a_native_dialog_is_a_dialog_and_names_itself(page):
    page.evaluate("document.getElementById('save').showModal()")
    state = observe(page)
    assert state["dialog_title"] == "Save this scenario"
    save = by_label(state, "Save")[0]
    assert save["in_dialog"] is True
    # Everything behind a modal dialog is covered, so it is not offered.
    assert all(a.get("covered") for a in by_label(state, "Portfolio"))
    page.evaluate("document.getElementById('save').close(); document.getElementById('named').showModal()")
    assert observe(page)["dialog_title"] == "Update hole"


def test_an_atlas_dialog_title_selector_is_tried_first(page):
    page.evaluate("document.getElementById('plain').showModal()")
    assert observe(page)["dialog_title"] == "Reset tenant"
    book = atlas_file.Atlas({"selectors": {"dialog_title": ["dialog[open] .dlg-caption"]}})
    lists = atlas_file.selector_lists(book)
    assert lists["dialog_title"] == ["dialog[open] .dlg-caption"]
    assert observe(page, lists)["dialog_title"] == "Custom caption"


def test_date_and_time_inputs_are_offered_for_typing_only(page):
    state = observe(page)
    completed = by_label(state, "Completed")
    assert [a["kind"] for a in completed] == ["fill"]
    assert completed[0]["role"] == "textbox" and completed[0]["input_type"] == "date"
    field = model.field_context("Set completed", completed[0], state, [])["field"]
    assert field["format"] == "YYYY-MM-DD"


@pytest.mark.parametrize("label,text,stored", [
    ("Completed", "2026-11-30", "2026-11-30"),
    ("Completed", "30 November 2026", "2026-11-30"),
    ("Start time", "2:30 PM", "14:30"),
])
def test_a_date_fill_reaches_a_framework_controlled_input(page, label, text, stored):
    state = observe(page)
    action = by_label(state, label, "fill")[0]
    browser.browser_operation({"operation": "act", "session": page.session, "action": action, "text": text})
    field_id = "completed" if label == "Completed" else "start"
    assert page.evaluate(f"document.getElementById('{field_id}').value") == stored
    # The tracker saw a real change: the prototype setter plus an input event.
    assert page.evaluate("window.changes") == [[field_id, stored]]


def test_an_unreadable_date_is_refused_and_leaves_the_field_alone(page):
    page.evaluate("const e=document.getElementById('completed'); e.value='2026-01-02'; window.changes=[]")
    action = by_label(observe(page), "Completed", "fill")[0]
    with pytest.raises(RuntimeError, match="did not accept"):
        browser.browser_operation({"operation": "act", "session": page.session, "action": action,
                                   "text": "sometime next week"})
    assert page.evaluate("document.getElementById('completed').value") == "2026-01-02"
    assert page.evaluate("window.changes") == []


def test_visually_hidden_toggles_are_offered_as_their_label(page):
    state = observe(page)
    drilling = by_label(state, "Drilling")[0]
    assert drilling["role"] == "radio" and drilling["checked"] == "false" and drilling["via_label"] is True
    hole = by_label(state, "Hole A")[0]
    assert hole["role"] == "checkbox" and hole["via_label"] is True
    # A hidden checkbox with no visible label is still not offered.
    assert not [a for a in state["actions"] if a.get("dom_id") == "ghost"]
    for action in (drilling, hole):
        browser.browser_operation({"operation": "act", "session": page.session, "action": action, "text": None})
    assert page.evaluate("document.querySelector('input[value=drill]').checked") is True
    assert page.evaluate("document.getElementById('hole').checked") is True
    assert by_label(observe(page), "Drilling")[0]["checked"] == "true"


def test_duplicate_labels_carry_their_section_and_reach_jev_distinguished(page):
    state = observe(page)
    grades = by_label(state, "Grade", "fill")
    assert [a["section"] for a in grades] == ["Indicated", "Inferred"]
    elements, targets, _ = model.action_space(state["actions"])
    shown = [e for e in elements if e["label"] == "Grade"]
    assert [e.get("section") for e in shown] == ["Indicated", "Inferred"]
    book = atlas_file.Atlas({"controls": [{"key": {"text": "Grade", "section_regex": "^Inf"}, "what": "Inferred."}]})
    assert [bool(book.match_control(model.match_fields(a, None))) for a in grades] == [False, True]


def test_identical_row_buttons_carry_their_row(page):
    state = observe(page)
    locks = by_label(state, "Lock")
    # The first cell repeats ("selected"), so the next cell is added until the row is unique.
    assert [a["row_label"] for a in locks] == ["selected · T-01", "selected · T-02", "dropped"]
    # What Jev sees is the row's context: its first three text cells.
    assert [a["row_context"] for a in locks] == ["selected · T-01 · Main zone", "selected · T-02 · Hinge zone",
                                                 "dropped · T-03 · East swarm"]
    elements, targets, _ = model.action_space(state["actions"])
    rows = [e.get("row") for e in elements if e["label"] == "Lock"]
    assert rows == ["selected · T-01 · Main zone", "selected · T-02 · Hinge zone", "dropped · T-03 · East swarm"]
    index = next(e["index"] for e in elements if e["label"] == "Lock")
    assert (model.option(index, targets["CLICK"][index], False, elements[int(index) - 1])["row"] ==
            "selected · T-01 · Main zone")
    book = atlas_file.Atlas({"controls": [{"key": {"text": "Lock", "row_label_regex": "T-02$"}, "what": "Row 2."}]})
    assert [bool(book.match_control(model.match_fields(a, None))) for a in locks] == [False, True, False]


def test_a_label_that_belongs_to_another_control_is_not_a_row_label(page):
    state = observe(page)
    # The Legacy link sits in the header; the comment box's label must not leak onto it,
    # and the Filters radios must not borrow each other's labels.
    assert "row_label" not in by_label(state, "Legacy")[0]
    assert by_label(state, "Drilling")[0].get("row_label") != "All"


def test_a_new_tab_link_opens_in_the_agent_tab(page, monkeypatch):
    before = len([t for t in page.send("Target.getTargets")["targetInfos"] if t["type"] == "page"])
    manual = by_label(observe(page), "User manual")[0]
    browser.browser_operation({"operation": "act", "session": page.session, "action": manual, "text": None})
    assert page.evaluate("location.hash") == "#/manual"
    # The link's own target is put back after the click.
    assert page.evaluate("document.querySelector('[href=\"#/manual\"]').getAttribute('target')") == "_blank"
    assert len([t for t in page.send("Target.getTargets")["targetInfos"] if t["type"] == "page"]) == before


def test_a_new_tab_link_is_left_alone_when_same_tab_is_off(page, monkeypatch):
    monkeypatch.setenv("JEV_SAME_TAB", "0")
    before = len([t for t in page.send("Target.getTargets")["targetInfos"] if t["type"] == "page"])
    manual = by_label(observe(page), "User manual")[0]
    browser.browser_operation({"operation": "act", "session": page.session, "action": manual, "text": None})
    assert page.evaluate("location.hash") == ""
    after = [t for t in page.send("Target.getTargets")["targetInfos"] if t["type"] == "page"]
    assert len(after) == before + 1
    for extra in after:
        if extra["url"].endswith("#/manual"):
            page.send("Target.closeTarget", targetId=extra["targetId"])


def test_a_control_beyond_the_side_of_a_scrolling_table_is_offered_and_scrolled_to(page):
    state = observe(page)
    far = by_label(state, "Far edit")[0]
    assert far["offscreen_x"] is True and not far.get("covered")
    # Beyond the edge of a container that cannot scroll there is nothing to reach.
    assert not by_label(state, "Clipped edit")
    # Controls in view are unchanged.
    assert "offscreen_x" not in by_label(state, "Portfolio")[0]
    browser.browser_operation({"operation": "act", "session": page.session, "action": far, "text": None})
    assert page.evaluate("window.farClicked") is True


ROWS = (Path(__file__).parent / "fixtures" / "rows.html").read_text()


def test_a_flat_grid_line_labels_its_own_link_not_the_first_line(page):
    page.load(ROWS)
    state = observe(page)
    ledger = [by_label(state, t)[0] for t in
              ("Programme approval: First pass", "Land access: Copper Hollow", "E 50/4997")]
    # Each line's own kind; the ledger's first cell ("Approval overdue") used to label every line.
    assert [a["row_label"] for a in ledger] == ["Approval overdue", "Approval due", "Tenure expiring"]
    assert [a["row_context"] for a in ledger] == [
        "Approval overdue · due yesterday · Budget check",
        "Approval due · due in 3 days · Tenure review",
        "Tenure expiring · expires in 19 days · expiring",
    ]


def test_an_id_only_link_carries_its_rows_title(page):
    page.load(ROWS)
    state = observe(page)
    link = by_label(state, "WF-2026-0146")[0]
    # The title cell is longer than a row label may be; the row context still has it.
    assert link["row_context"] == "Programme approval: Scout RC, chargeability anomalies A and B · pending"
    long = by_label(state, "WF-2026-0130")[0]["row_context"]
    assert long.startswith("Programme approval: Gradient-array IP survey") and long.endswith("· approved")
    elements, _targets, _ = model.action_space(state["actions"])
    shown = next(e for e in elements if e["label"] == "WF-2026-0146")
    assert shown["row"] == link["row_context"]


def test_a_header_row_is_nobodys_row(page):
    page.load(ROWS)
    state = observe(page)
    for label in ("Sort by Request", "Sort by Title"):
        sort = by_label(state, label)[0]
        assert "row_label" not in sort and "row_context" not in sort


def test_identical_card_buttons_carry_their_cards_title_and_status(page):
    page.load(ROWS)
    state = observe(page)
    assert [a.get("row_context") for a in by_label(state, "Open")] == ["Kettle Lake camp · open",
                                                                       "Sable Dome camp · closed"]
    assert [a.get("row_context") for a in by_label(state, "Edit")] == ["Kettle Lake camp · open",
                                                                       "Sable Dome camp · closed"]


def test_a_tab_strip_and_a_column_of_tickets_do_not_borrow_each_other(page):
    page.load(ROWS)
    state = observe(page)
    # The group's own label is the row label; the other tabs are peers, not context.
    hold = by_label(state, "On hold 1")[0]
    assert hold["row_label"] == "Projects" and "row_context" not in hold
    # A ticket's context is its column's head at most, never the other tickets.
    for ticket in ("Wolverine Creek", "Mount Aster", "Lorimer"):
        context = by_label(state, ticket)[0].get("row_context") or ""
        assert not any(other in context for other in ("Wolverine Creek", "Mount Aster", "Kettle Lake"))


def test_a_label_in_a_sibling_list_item_is_not_this_items(page):
    page.load(ROWS)
    state = observe(page)
    remove = by_label(state, "Remove")[0]
    assert remove.get("row_label") != "First item"


SEARCH = (Path(__file__).parent / "fixtures" / "search-form.html").read_text()


def test_an_empty_plain_search_box_offers_typing_only(page):
    page.load(SEARCH)
    search = by_label(observe(page), "Search the site")
    # No "Open …" twin on a search box that opens nothing: it read as a search button.
    assert [a["kind"] for a in search] == ["fill"]
    # A search field that owns a suggestion list keeps it.
    assert "Open Suggest" in [a["label"] for a in observe(page)["actions"]]


def test_typing_then_press_enter_runs_a_search_with_no_button(page):
    page.load(SEARCH)
    fill = by_label(observe(page), "Search the site", "fill")[0]
    browser.browser_operation({"operation": "act", "session": page.session, "action": fill, "text": "PRJ-0441"})
    state = observe(page)
    submit = by_label(state, "Search the site", "submit")
    assert len(submit) == 1 and submit[0]["value"] == "PRJ-0441"
    # One element, two operations: TYPE_TEXT and PRESS_ENTER.
    elements, targets, _ = model.action_space(state["actions"])
    index = next(e["index"] for e in elements if e["label"] == "Search the site")
    assert targets["PRESS_ENTER"][index]["kind"] == "submit"
    assert "PRESS_ENTER" in elements[int(index) - 1]["operations"]
    browser.browser_operation({"operation": "act", "session": page.session, "action": submit[0], "text": None})
    assert page.evaluate("location.hash") == "#/search?q=PRJ-0441"


def test_a_filled_search_box_can_be_submitted_after_focus_moved_away(page):
    page.load(SEARCH)
    page.evaluate("document.querySelector('[type=search]').value='drill'; document.getElementById('name').focus()")
    submit = by_label(observe(page), "Search the site", "submit")
    assert len(submit) == 1
    browser.browser_operation({"operation": "act", "session": page.session, "action": submit[0], "text": None})
    assert page.evaluate("location.hash") == "#/search?q=drill"


def test_a_plain_field_is_offered_enter_only_while_focused_and_filled(page):
    page.load(SEARCH)
    page.evaluate("document.getElementById('name').value='Ada'; document.getElementById('notes').value='x'")
    assert not by_label(observe(page), "Name", "submit")
    page.evaluate("document.getElementById('name').focus()")
    submit = by_label(observe(page), "Name", "submit")
    assert len(submit) == 1
    # A textarea takes Enter as a new line; it is never offered.
    page.evaluate("document.getElementById('notes').focus()")
    assert not by_label(observe(page), "Notes", "submit")
    page.evaluate("document.getElementById('name').focus()")
    browser.browser_operation({"operation": "act", "session": page.session, "action": submit[0], "text": None})
    assert page.evaluate("window.submits") == ["Ada"]
    page.evaluate("document.getElementById('name').value=''")
    assert not by_label(observe(page), "Name", "submit")

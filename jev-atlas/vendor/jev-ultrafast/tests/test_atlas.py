"""The atlas matcher and what an atlas changes in the request. No paid APIs."""

import hashlib
import json

import pytest

from jev_ultrafast import atlas as atlas_file
from jev_ultrafast import model, runlog

FIXTURE = {
    "app": "Test App",
    "version": "2026-09-21",
    "pages": [
        {
            "id": "editor",
            "match": {"url_contains": "/app/orders/edit"},
            "name": "Editor.",
            "what": "Edits the lines of one order.",
            "not_here": "Approvals live elsewhere.",
            "leads_to": {"Order Summary (left nav)": "summary"},
            "facts_js": ["'Active sheet: Draft'", "null", "missing.property"],
            "virtual_controls_js": "readTheGrid()",
        },
        {"id": "summary", "match": {"url_contains": "/app/orders/summary"}, "name": "Summary."},
        {
            "id": "search-overlay",
            "layer": "overlay",
            "match": {"selector": "app-search-overlay, [data-track-id='nav_search-overlay']"},
            "name": "Search panel.",
            "what": "Searches every order by name or id.",
            "not_here": "It does not filter the editor.",
            "facts_js": ["'Overlay fact'"],
        },
        {
            "id": "add-line-dialog",
            "layer": "overlay",
            "match": {"dialog_title": "Add Line"},
            "name": "Add Line dialog.",
            "what": "Creates one order line.",
        },
    ],
    "controls": [
        {"key": {"track_id": "header_save"}, "region": "Header", "what": "Saves the draft."},
        {"key": {"ancestor": "legacy-editor"}, "region": "Editor body", "what": "Somewhere in the body."},
        {
            "key": {"ancestor": "legacy-editor", "title": "More tools"},
            "region": "Editor toolbar",
            "what": "Opens the overflow menu.",
            "not_for": "Editing cell values.",
        },
        {"key": {"id_regex": "^toolbar"}, "region": "Editor toolbar", "what": "A toolbar action."},
        {"key": {"page": "summary", "text": "Draft"}, "region": "Sheet tabs", "what": "The draft sheet."},
        {"key": {"page": "search-overlay", "role": "combobox"}, "region": "Search panel", "what": "The search box."},
        {"key": {"ancestor": "app-popup-container", "role": "button"}, "region": "Panel", "what": "Closes the panel."},
        {"key": {"track_id": "page_settings_current"}, "region": "Page settings", "what": "This page only."},
        {
            "key": {"row_label": "Colour"},
            "region": "Add Line dialog",
            "what": "The colour the item on this line is made in.",
            "not_for": "The colour of the packaging.",
            "options": ["Black", "Blue", "Green", "Red", "White"],
        },
    ],
}


@pytest.fixture
def atlas(tmp_path):
    path = tmp_path / "test.json"
    path.write_text(json.dumps(FIXTURE))
    return atlas_file.load(path)


def element(**fields):
    base = {"track_id": None, "id": None, "title": None, "href": None, "ancestor": None, "role": "button", "text": ""}
    return {**base, **fields}


def test_page_matches_on_url_and_is_none_otherwise(atlas):
    assert atlas.match_page("https://host/x/app/orders/edit?id=1")["id"] == "editor"
    assert atlas.match_page("https://host/other") is None
    assert atlas.match_page(None) is None


def test_an_exact_id_outranks_two_generic_fields(atlas):
    # {ancestor, role} is two fields but says little; one track_id names the control.
    item = element(track_id="page_settings_current", ancestor="app-popup-container", text="Current page")
    assert atlas.match_control(item)["region"] == "Page settings"
    close = element(ancestor="app-popup-container")
    assert atlas.match_control(close)["region"] == "Panel"


def test_the_most_specific_key_wins_and_ties_go_to_the_first_entry(atlas):
    body = element(ancestor="legacy-editor", text="Anything")
    assert atlas.match_control(body)["region"] == "Editor body"
    overflow = element(ancestor="legacy-editor", title="More tools")
    assert atlas.match_control(overflow)["what"] == "Opens the overflow menu."
    # Two one-field keys could match; the first entry in the file wins.
    both = element(track_id="header_save", ancestor="legacy-editor")
    assert atlas.match_control(both)["region"] == "Header"


def test_regex_page_and_no_match(atlas):
    assert atlas.match_control(element(id="toolbarAddLine"))["region"] == "Editor toolbar"
    assert atlas.match_control(element(id="footerToolbar")) is None
    tab = element(text="Draft")
    assert atlas.match_control(tab, "editor") is None
    assert atlas.match_control(tab, "summary")["region"] == "Sheet tabs"


def test_matching_is_exact_case_sensitive_and_trimmed(atlas):
    assert atlas.match_control(element(track_id=" header_save ")) is not None
    assert atlas.match_control(element(track_id="HEADER_SAVE")) is None


def test_an_unknown_key_field_is_rejected_when_the_atlas_loads():
    with pytest.raises(ValueError, match="unknown field"):
        atlas_file.Atlas({"controls": [{"key": {"data_test_id": "x"}}]})


def test_facts_are_one_read_only_evaluation_ignoring_nulls_and_errors(atlas):
    calls = []

    class Stub:
        def evaluate(self, expression):
            calls.append(expression)
            return ["Active sheet: Draft", None, None]

    page = atlas.match_page("https://host/app/orders/edit")
    assert atlas.facts(Stub(), page) == ["Active sheet: Draft"]
    assert len(calls) == 1 and "try" in calls[0]


def test_facts_survive_a_failing_evaluation(atlas):
    class Broken:
        def evaluate(self, _expression):
            raise RuntimeError("navigating")

    assert atlas.facts(Broken(), atlas.match_page("https://host/app/orders/edit")) == []


def test_page_context_reads_as_one_block(atlas):
    page = atlas.match_page("https://host/app/orders/edit")
    context = atlas_file.page_context(page, ["Active sheet: Draft"], "Add Line", 42)
    assert context.splitlines() == [
        "Editor. Edits the lines of one order.",
        "Approvals live elsewhere.",
        "Leads to: Order Summary (left nav)",
        "Active sheet: Draft",
        "Open dialog: Add Line",
        "42 controls are behind the open dialog and cannot be clicked",
    ]
    assert atlas_file.page_context(None, [], None, 0) == ""


def observed():
    return {
        "url": "https://host/app/orders/edit",
        "title": "Editor",
        "text": "Editor",
        "dialog_title": "Add Line",
        "omitted_actions": 7,
        "scroll": {"y": 0},
        "actions": [
            {"id": "e1", "kind": "click", "label": "Save", "role": "button", "node": 10,
             "track_id": "header_save"},
            {"id": "e2", "kind": "click", "label": "More tools", "role": "button", "node": 20,
             "ancestor": "legacy-editor", "title": "More tools", "in_dialog": True},
            {"id": "e3", "kind": "click", "label": "Behind the modal", "role": "button", "node": 30,
             "covered": True},
            {"id": "wait", "kind": "wait", "label": "Wait"},
        ],
    }


def test_covered_controls_are_not_offered_and_are_counted(monkeypatch):
    monkeypatch.delenv("JEV_ATLAS", raising=False)
    elements, targets, _controls = model.action_space(observed()["actions"])
    assert [e["label"] for e in elements] == ["Save", "More tools"]
    assert "3" not in targets["CLICK"]
    page = model.page_state(observed(), atlas_loaded=False)
    assert page["covered_controls"] == 1 and page["controls_not_shown"] == 7
    assert page["dialog"] == "Add Line" and "context" not in page
    assert list(page)[:2] == ["url", "title"]


def test_without_an_atlas_an_option_keeps_todays_shape(monkeypatch):
    monkeypatch.delenv("JEV_ATLAS", raising=False)
    action = observed()["actions"][0]
    assert model.option("1", action, atlas_loaded=False) == {
        "element": "[1] Save", "current_value": "", "role": "button"
    }


def test_with_an_atlas_the_option_carries_what_the_control_is_for(monkeypatch, tmp_path):
    path = tmp_path / "atlas.json"
    path.write_text(json.dumps(FIXTURE))
    monkeypatch.setenv("JEV_ATLAS", str(path))
    model.LOADED_ATLASES.clear()
    page = model.annotate(observed())
    assert page["page_id"] == "editor"
    assert page["context"].startswith("Editor. Edits the lines")
    assert "1 controls are behind the open dialog" in page["context"]
    elements, targets, _ = model.action_space(page["actions"])
    assert elements[0]["region"] == "Header" and elements[0]["what"] == "Saves the draft."
    assert model.option("2", targets["CLICK"]["2"], atlas_loaded=True) == {
        "element": "[2] More tools",
        "region": "Editor toolbar",
        "what": "Opens the overflow menu.",
        "not_for": "Editing cell values.",
        "current_value": "",
        "role": "button",
        "in_dialog": True,
    }
    assert model.page_state(page, atlas_loaded=True)["context"] == page["context"]
    model.LOADED_ATLASES.clear()


class Probe:
    """A browser that answers the one evaluation an atlas makes per step."""

    def __init__(self, facts, selectors, virtual=None):
        self.facts, self.selectors, self.calls = facts, selectors, []
        self.virtual = virtual or []

    def evaluate(self, expression):
        self.calls.append(expression)
        return [self.facts, self.selectors, self.virtual]


def test_one_evaluation_carries_every_fact_and_every_overlay_test(atlas):
    browser = Probe(["Active sheet: Draft", None, None, "Overlay fact"], [True])
    found = atlas.probe(browser, atlas.match_page("https://host/app/orders/edit"))
    assert len(browser.calls) == 1
    assert "app-search-overlay" in browser.calls[0] and "checkVisibility" in browser.calls[0]
    assert found["facts"] == {"editor": ["Active sheet: Draft"], "search-overlay": ["Overlay fact"]}
    assert found["selectors"] == {"search-overlay": True}


def test_an_overlay_is_active_by_selector_or_by_dialog_title(atlas):
    assert [o["id"] for o in atlas.active_overlays({"search-overlay": True}, None)] == ["search-overlay"]
    assert [o["id"] for o in atlas.active_overlays({}, "Add Line")] == ["add-line-dialog"]
    assert [o["id"] for o in atlas.active_overlays({"search-overlay": True}, " Add Line ")] == [
        "search-overlay",
        "add-line-dialog",
    ]
    assert atlas.active_overlays({"search-overlay": False}, "Something else") == []
    assert atlas.match_page("https://host/app/orders/edit")["id"] == "editor"


def test_an_overlay_stacks_on_the_page_underneath(atlas):
    page = atlas.match_page("https://host/app/orders/edit")
    overlay = atlas.active_overlays({"search-overlay": True})[0]
    context = atlas_file.page_context(
        page, ["Active sheet: Draft"], "Search panel.", 12, overlays=[(overlay, ["Overlay fact"])]
    )
    assert context.splitlines() == [
        "Editor. Edits the lines of one order.",
        "Approvals live elsewhere.",
        "Leads to: Order Summary (left nav)",
        "Active sheet: Draft",
        "Search panel. Searches every order by name or id.",
        "It does not filter the editor.",
        "Overlay fact",
        "Open dialog: Search panel.",
        "12 controls are behind the open dialog and cannot be clicked",
    ]


def test_a_control_keyed_on_an_overlay_matches_only_while_it_is_open(atlas):
    box = element(role="combobox", text="Search")
    assert atlas.match_control(box, ["editor"]) is None
    assert atlas.match_control(box, ["editor", "search-overlay"])["region"] == "Search panel"


def overlay_page():
    page = observed()
    page["dialog_title"] = ""
    page["actions"].insert(0, {"id": "e0", "kind": "click", "label": "search", "role": "combobox", "node": 5})
    return page


def test_an_open_panel_names_itself_when_the_page_has_no_dialog_title(monkeypatch, tmp_path):
    path = tmp_path / "atlas.json"
    path.write_text(json.dumps(FIXTURE))
    monkeypatch.setenv("JEV_ATLAS", str(path))
    model.LOADED_ATLASES.clear()
    page = model.annotate(overlay_page(), Probe([None, None, None, "Overlay fact"], [True]))
    assert page["overlays"] == ["search-overlay"]
    assert page["dialog_name"] == "Search panel."
    assert model.page_state(page, atlas_loaded=True)["dialog"] == "Search panel."
    assert page["context"].splitlines()[:2] == [
        "Editor. Edits the lines of one order.",
        "Approvals live elsewhere.",
    ]
    assert "Search panel. Searches every order by name or id." in page["context"].splitlines()
    assert next(a for a in page["actions"] if a["id"] == "e0")["atlas"]["region"] == "Search panel"
    model.LOADED_ATLASES.clear()


def test_elements_debug_reports_every_control_and_the_key_that_matched(monkeypatch, tmp_path):
    path = tmp_path / "atlas.json"
    path.write_text(json.dumps(FIXTURE))
    monkeypatch.setenv("JEV_ATLAS", str(path))
    model.LOADED_ATLASES.clear()
    page = model.annotate(overlay_page(), Probe([None, None, None, "Overlay fact"], [True]))
    rows = model.elements_debug(page)
    assert [r["label"] for r in rows] == ["search", "Save", "More tools", "Behind the modal"]
    assert rows[0]["matched_key"] == {"page": "search-overlay", "role": "combobox"}
    assert rows[1]["matched_key"] == {"track_id": "header_save"}
    covered = rows[-1]
    assert covered["covered"] is True and covered["index"] is None and covered["matched_key"] is None
    assert [r["index"] for r in rows[:3]] == ["1", "2", "3"]
    model.LOADED_ATLASES.clear()


def form_rows():
    """Actions as snapshot.js reports tests/fixtures/form-rows.html.

    The label is in the left cell, the widget several inline wrappers deep in the
    right one, and the filled combobox's only accessible name is its own value.
    """
    shared = {"role": "combobox", "ancestor": "app-search-drop-down", "in_dialog": True}
    return [
        {"id": "e1", "kind": "fill", "label": "Colour", "value": "Blue",
         "row_label": "Colour", "node": 10, **shared},
        {"id": "e2", "kind": "click", "label": "Open Colour", "value": "Blue",
         "row_label": "Colour", "node": 10, **shared},
        {"id": "e3", "kind": "fill", "label": "Product", "value": "", "row_label": "Product", "node": 20, **shared},
        {"id": "e4", "kind": "fill", "label": "Name", "value": "", "row_label": "Name", "node": 30,
         "role": "textbox", "dom_id": "name"},
        {"id": "wait", "kind": "wait", "label": "Wait"},
    ]


def test_a_row_labelled_field_is_never_offered_as_its_own_value():
    elements, targets, _controls = model.action_space(form_rows())
    assert [e["label"] for e in elements] == ["Colour", "Product", "Name"]
    assert targets["TYPE_TEXT"]["1"]["value"] == "Blue"
    assert model.option("1", targets["TYPE_TEXT"]["1"], atlas_loaded=False)["current_value"] == "Blue"
    assert targets["CLICK"]["1"]["label"] == "Open Colour"


def test_row_label_is_a_key_field_and_reaches_the_text_helper(monkeypatch, tmp_path):
    path = tmp_path / "atlas.json"
    path.write_text(json.dumps(FIXTURE))
    monkeypatch.setenv("JEV_ATLAS", str(path))
    model.LOADED_ATLASES.clear()
    page = {"url": "https://host/app/orders/edit", "title": "Editor", "text": "",
            "dialog_title": "Add Line", "actions": form_rows(), "scroll": {"y": 0}}
    model.annotate(page)
    colour = page["actions"][0]
    assert colour["atlas_key"] == {"row_label": "Colour"}
    assert colour["atlas"]["not_for"] == "The colour of the packaging."
    # The Open twin of the same node inherits the entry.
    assert page["actions"][1]["atlas"]["region"] == "Add Line dialog"
    assert page["actions"][2].get("atlas") is None
    field = model.field_context("Make the chair on this line red", colour, page, [])["field"]
    assert field["row_label"] == "Colour" and field["value"] == "Blue"
    assert field["options"] == ["Black", "Blue", "Green", "Red", "White"]
    assert field["what"].startswith("The colour")
    # `options` is for the text helper only; the choice Jev sees does not carry it.
    assert "options" not in model.option("1", colour, atlas_loaded=True)
    assert model.elements_debug(page)[0]["row_label"] == "Colour"
    model.LOADED_ATLASES.clear()


def typeahead():
    """Actions as snapshot.js reports tests/fixtures/typeahead-list.html.

    The suggestion list lives outside the dialog; only aria-controls ties it to
    the field, so the options borrow that field's row label and its dialog.
    """
    return [
        {"id": "e1", "kind": "fill", "label": "Product", "role": "combobox", "node": 10, "value": "1422",
         "row_label": "Product", "in_dialog": True, "list_open": True, "expanded": "true"},
        {"id": "e2", "kind": "click", "label": "Open Product", "role": "combobox", "node": 10, "value": "1422",
         "row_label": "Product", "in_dialog": True, "list_open": True, "expanded": "true"},
        {"id": "e3", "kind": "click", "label": "1422 / Chairs / Oak", "role": "option", "node": 20,
         "value": "", "row_label": "Product", "in_dialog": True},
        {"id": "e4", "kind": "click", "label": "1423 / Chairs / Pine", "role": "option", "node": 30,
         "value": "", "row_label": "Product", "in_dialog": True},
    ]


def test_a_suggestion_says_which_field_it_would_fill():
    elements, targets, _controls = model.action_space(typeahead())
    field, first = elements[0], elements[1]
    assert field["label"] == "Product" and field["list_open"] is True and "for_field" not in field
    assert first["label"] == "1422 / Chairs / Oak" and first["for_field"] == "Product"
    assert "list_open" not in first
    assert model.option("1", targets["TYPE_TEXT"]["1"], atlas_loaded=False)["list_open"] is True
    assert "list_open" not in model.option("2", targets["CLICK"]["2"], atlas_loaded=False)
    debug = model.elements_debug({"actions": typeahead()})
    assert [r["list_open"] for r in debug] == [True, True, False, False]
    assert [r["row_label"] for r in debug] == ["Product"] * 4


def test_the_no_atlas_option_is_unchanged_while_no_list_is_open(monkeypatch):
    monkeypatch.delenv("JEV_ATLAS", raising=False)
    quiet = {k: v for k, v in typeahead()[0].items() if k != "list_open"}
    assert model.option("1", quiet, atlas_loaded=False) == {
        "element": "[1] Product", "current_value": "1422", "role": "combobox", "expanded": "true"
    }
    _elements, targets, _ = model.action_space([quiet])
    assert "for_field" not in _elements[0] and "list_open" not in _elements[0]


CELL = {
    "id": "cell:J9",
    "label": "Quantity of order line 'shim demo'",
    "row_label": "shim demo",
    "region": "Order grid, draft rows",
    "what": "The quantity of this order line.",
    "not_for": "Other columns, which are their own cells.",
    "current_value": "0",
    "set": "(v) => { return true }",
}


def with_atlas(monkeypatch, tmp_path, browser):
    path = tmp_path / "atlas.json"
    path.write_text(json.dumps(FIXTURE))
    monkeypatch.setenv("JEV_ATLAS", str(path))
    model.LOADED_ATLASES.clear()
    page = {"url": "https://host/app/orders/edit", "title": "Editor", "text": "",
            "dialog_title": "", "scroll": {"y": 0}, "actions": [
                {"id": "e1", "kind": "click", "label": "Save", "role": "button", "node": 10,
                 "track_id": "header_save"},
                {"id": "wait", "kind": "wait", "label": "Wait"}]}
    return model.annotate(page, browser)


def test_a_virtual_control_is_offered_only_for_typing(monkeypatch, tmp_path):
    page = with_atlas(monkeypatch, tmp_path, Probe([None, None, None], [False], [[CELL]]))
    cell = page["actions"][-1]
    assert cell["id"] == "v1" and cell["kind"] == "fill" and cell["virtual"] is True
    assert cell["label"] == CELL["label"] and cell["value"] == "0"
    elements, targets, _controls = model.action_space(page["actions"])
    # The real element keeps index 1; the cell continues after it.
    assert [e["index"] for e in elements] == ["1", "2"]
    assert targets["TYPE_TEXT"]["2"]["id"] == "v1"
    assert "2" not in targets.get("CLICK", {})
    assert model.option("2", cell, atlas_loaded=True) == {
        "element": "[2] Quantity of order line 'shim demo'",
        "region": CELL["region"], "what": CELL["what"], "not_for": CELL["not_for"],
        "current_value": "0", "role": "textbox", "in_dialog": False,
    }
    field = model.field_context("Order 20 of these", cell, page, [])["field"]
    assert field["row_label"] == "shim demo" and field["what"] == CELL["what"]
    assert [r["virtual"] for r in model.elements_debug(page)] == [False, True]
    model.LOADED_ATLASES.clear()


@pytest.mark.parametrize("broken", [{"label": ""}, {"set": None}, {"label": None}, "not a control"])
def test_a_virtual_control_without_a_name_or_a_way_to_write_it_is_dropped(monkeypatch, tmp_path, broken):
    control = "x" if broken == "not a control" else {**CELL, **broken}
    page = with_atlas(monkeypatch, tmp_path, Probe([None, None, None], [False], [[control]]))
    assert not [a for a in page["actions"] if a.get("virtual")]
    model.LOADED_ATLASES.clear()


def test_without_an_atlas_there_are_no_virtual_controls(monkeypatch):
    monkeypatch.delenv("JEV_ATLAS", raising=False)
    page = {"url": "https://host/x", "actions": [{"id": "e1", "kind": "click", "label": "Save", "node": 1}]}
    assert model.annotate(page, Probe([], [], [[CELL]]))["actions"] == page["actions"]


def test_a_loaded_atlas_carries_a_digest_of_the_bytes_it_was_read_from(tmp_path):
    """The declared version can go stale; the digest cannot."""
    path = tmp_path / "atlas.json"
    raw = json.dumps(FIXTURE).encode()
    path.write_bytes(raw)
    book = atlas_file.load(path)
    assert book.version == FIXTURE["version"]
    assert book.sha256 == hashlib.sha256(raw).hexdigest()[:12]
    assert len(book.sha256) == 12

    # An edit that leaves the declared version alone still changes the digest.
    edited = {**FIXTURE, "pages": []}
    path.write_text(json.dumps(edited))
    again = atlas_file.load(path)
    assert again.version == book.version and again.sha256 != book.sha256


def test_a_run_log_records_both_the_declared_version_and_the_digest(tmp_path):
    path = tmp_path / "atlas.json"
    path.write_text(json.dumps(FIXTURE))
    book = atlas_file.load(path)
    log = runlog.RunLog(tmp_path / "runs", "a goal", book)
    written = json.loads((log.dir / "run.json").read_text())
    assert written["atlas"] == str(path)
    assert written["atlas_version"] == FIXTURE["version"]
    assert written["atlas_sha256"] == book.sha256


def test_a_run_log_without_an_atlas_records_no_version_and_no_digest(tmp_path):
    log = runlog.RunLog(tmp_path / "runs", "a goal", None)
    written = json.loads((log.dir / "run.json").read_text())
    assert written["atlas"] is None
    assert written["atlas_version"] is None and written["atlas_sha256"] is None


def test_without_an_atlas_the_selector_lists_are_exactly_the_defaults():
    lists = atlas_file.selector_lists(None)
    assert lists["dialog"] == list(atlas_file.DEFAULT_DIALOG)
    assert lists["busy"] == list(atlas_file.DEFAULT_BUSY)
    # The defaults are generic conventions only; application selectors come from an atlas.
    assert '[role="dialog"]' in lists["dialog"] and '[aria-busy="true"]' in lists["busy"]


def test_an_atlas_appends_its_own_selectors_and_never_replaces_the_defaults(tmp_path):
    path = tmp_path / "atlas.json"
    path.write_text(json.dumps({
        **FIXTURE,
        "selectors": {"dialog": ["my-modal", " .app-overlay "], "busy": "my-spinner"},
    }))
    book = atlas_file.load(path)
    assert book.selectors("dialog") == ["my-modal", ".app-overlay"]
    assert book.selectors("busy") == ["my-spinner"]  # a bare string is a list of one
    lists = atlas_file.selector_lists(book)
    assert lists["dialog"] == [*atlas_file.DEFAULT_DIALOG, "my-modal", ".app-overlay"]
    assert lists["busy"] == [*atlas_file.DEFAULT_BUSY, "my-spinner"]


def test_an_atlas_without_a_selectors_key_changes_nothing(atlas):
    assert "selectors" not in FIXTURE
    assert atlas.selectors("dialog") == [] and atlas.selectors("busy") == []
    assert atlas_file.selector_lists(atlas) == atlas_file.selector_lists(None)


@pytest.mark.parametrize("broken", [
    {"dialog": [None, "", "  ", 7, {"x": 1}]},   # nothing usable survives
    {"dialog": "not a list, not a dict"},        # a bare string is still one selector
    {"dialog": {"nested": "object"}},            # not a list at all
    {},                                          # the key is there but empty
])
def test_unusable_selector_entries_are_dropped_rather_than_injected(tmp_path, broken):
    """A non-string in a selector list would break every query on the page."""
    path = tmp_path / "atlas.json"
    path.write_text(json.dumps({**FIXTURE, "selectors": broken}))
    book = atlas_file.load(path)
    extra = book.selectors("dialog")
    assert all(isinstance(item, str) and item.strip() for item in extra)
    assert atlas_file.selector_lists(book)["dialog"][:len(atlas_file.DEFAULT_DIALOG)] == \
        list(atlas_file.DEFAULT_DIALOG)


def test_an_unknown_selector_kind_is_refused(atlas):
    with pytest.raises(ValueError):
        atlas.selectors("sidebar")


def test_both_page_readers_are_given_the_same_selector_lists(monkeypatch, tmp_path):
    """snapshot.js and the settle probe must not disagree about what a dialog is."""
    from jev_ultrafast import browser

    path = tmp_path / "atlas.json"
    path.write_text(json.dumps({**FIXTURE, "selectors": {"dialog": ["my-modal"]}}))
    monkeypatch.setenv("JEV_ATLAS", str(path))
    model.LOADED_ATLASES.clear()
    lists = browser.selectors()
    assert lists["dialog"][-1] == "my-modal"
    injected = json.dumps(lists)
    assert browser.read_state().endswith(f"({injected})")
    assert browser.settle_probe().endswith(f"({injected})")
    assert injected in browser.marker_expression()
    # The script itself carries no application name; the lists are passed in.
    assert "my-modal" not in browser.SNAPSHOT and "my-modal" not in browser.SETTLE_PROBE
    assert '[aria-busy="true"]' not in browser.SNAPSHOT and '[aria-busy="true"]' not in browser.SETTLE_PROBE
    model.LOADED_ATLASES.clear()


def test_global_facts_are_read_on_every_page_before_the_page_facts(monkeypatch, tmp_path):
    path = tmp_path / "atlas.json"
    path.write_text(json.dumps({
        "global_facts_js": ["'Signed in as: Test'", "null"],
        "pages": [{"id": "home", "match": {"url_contains": "/home"}, "facts_js": ["'Home fact'"]}],
    }))
    monkeypatch.setenv("JEV_ATLAS", str(path))
    model.LOADED_ATLASES.clear()

    class Probe:
        def evaluate(self, expression):
            return [["Signed in as: Test", None, "Home fact"][: expression.count("try {")], [], []]

    on_home = model.annotate({"url": "https://h/home", "actions": []}, Probe())
    assert on_home["context"].splitlines() == ["Signed in as: Test", "Home fact"]

    class Elsewhere:
        def evaluate(self, expression):
            assert expression.count("try {") == 2  # only the global expressions
            return [["Signed in as: Test", None], [], []]

    assert model.annotate({"url": "https://h/else", "actions": []}, Elsewhere())["context"] == "Signed in as: Test"
    model.LOADED_ATLASES.clear()

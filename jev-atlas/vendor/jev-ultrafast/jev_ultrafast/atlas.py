"""Application knowledge, loaded from a JSON atlas file.

Local change (atlas shim). The harness stays application-agnostic: everything it
knows about a particular application lives in the file named by ``JEV_ATLAS``.
With no atlas, nothing here runs and the model sees exactly what it saw before.

The file's contract is ``adit-shim/harness/ATLAS-FORMAT-ADDENDUM.md`` in the PoC repository:
``pages`` describe screens (``what``/``not_here``/``leads_to``/``facts_js``) and
``controls`` describe individual elements (``region``/``what``/``not_for``),
keyed on the stable hooks ``snapshot.js`` extracts, and ``selectors`` appends
application-specific dialog and busy selectors to the harness defaults below.
"""

import hashlib
import json
import re
from pathlib import Path

# Every key field an atlas entry may use. Unknown fields fail the entry rather
# than being ignored, so a typo cannot silently widen a rule.
# Local change: `section` (fieldset legend / named group / preceding heading) and
# `landmark` (nearest ARIA landmark, "role" or "role: name") come from snapshot.js;
# `row_label_regex`, `section_regex` and `landmark_regex`/`landmark_contains` match them loosely.
EXACT_KEYS = ("track_id", "id", "title", "text", "role", "ancestor", "page", "href", "row_label",
              "section", "landmark")
REGEX_KEYS = ("id_regex", "text_regex", "href_regex", "row_label_regex", "section_regex", "landmark_regex")
CONTAINS_KEYS = ("href_contains", "text_contains", "landmark_contains")
KEY_FIELDS = EXACT_KEYS + REGEX_KEYS + CONTAINS_KEYS

# How much each key field says about *which* control this is. An id is nearly
# unique; a role and a component ancestor are shared by dozens. Without weights,
# {ancestor, role} (two generic fields) outranked an exact track_id and put the
# description of a panel's close cross on four menu items.
WEIGHTS = {
    "track_id": 3, "id": 3, "dom_id": 3,
    "title": 2, "text": 2, "row_label": 2, "href": 2,
    "text_regex": 2, "id_regex": 2, "href_regex": 2, "href_contains": 2, "text_contains": 2,
    "ancestor": 1, "role": 1, "page": 1,
    "row_label_regex": 2,
    "section": 1, "section_regex": 1, "landmark": 1, "landmark_regex": 1, "landmark_contains": 1,
}

# The element fields a control key may be matched against.
ELEMENT_FIELDS = ("track_id", "id", "title", "text", "role", "ancestor", "href", "page", "row_label",
                  "section", "landmark")

# The DOM that marks an open dialog, and the DOM that marks a page still drawing.
# Both page readers use these: snapshot.js (injected) and browser.py's settle probe.
#
# An atlas may APPEND to either through its top-level `selectors` key. It cannot
# replace them, so a run with an atlas reads a page the same way a run without one
# does, plus whatever the atlas adds.
#
# The defaults are generic web conventions only: ARIA roles and states, the
# native <dialog> element, and class names that say "loading", "spinner" or
# "busy". Anything a particular application or widget library needs beyond these
# belongs in that application's atlas (`selectors`), never here.
#
# Deliberately narrow: no bare "mask" or "progress" patterns. Some applications
# keep a mask layer or a progress bar permanently on screen, and those patterns
# would make every page look busy for ever. A busy indicator that is a custom
# element (a tag name no class selector finds) is still caught when it covers a
# control, by BUSYISH in snapshot.js and the settle probe.
DEFAULT_DIALOG = ('[role="dialog"]', '[role="alertdialog"]', '[aria-modal="true"]', "dialog[open]", ".modal")
DEFAULT_BUSY = (
    '[aria-busy="true"]',
    '[class*="loading" i]', '[class*="spinner" i]', '[class*="busy" i]',
)
# Local change: `dialog_title` lists CSS selectors for the element holding an open
# dialog's title. It has no defaults: snapshot.js tries these first, then its own
# heading lookup, then each open dialog's aria-labelledby / aria-label / first heading.
DEFAULT_DIALOG_TITLE = ()
SELECTOR_KINDS = ("dialog", "busy", "dialog_title")

# The facts id under which atlas-level `global_facts_js` results are collected.
GLOBAL = "__global__"


def selector_lists(book=None):
    """The selector lists the page readers inject: defaults, then the atlas's own.

    No atlas, or no ``selectors`` key, gives exactly the defaults.
    """
    return {
        kind: [*default, *(book.selectors(kind) if book else [])]
        for kind, default in (("dialog", DEFAULT_DIALOG), ("busy", DEFAULT_BUSY),
                              ("dialog_title", DEFAULT_DIALOG_TITLE))
    }


# Every expression sent to the page is read-only and cannot throw out of its own guard.
GUARD = "(() => {{ try {{ return ({}) }} catch (error) {{ return null }} }})()"
VISIBLE = "[...document.querySelectorAll({})].some(e => e.checkVisibility())"


class Atlas:
    """One loaded atlas file. Read-only."""

    def __init__(self, data, path=None, sha256=None):
        if not isinstance(data, dict):
            raise ValueError("Atlas must be a JSON object")
        self.data = data
        self.path = str(path) if path else None
        self.app = data.get("app")
        # The version the file declares about itself, which an author may forget to
        # bump, and a short digest of the bytes that were actually loaded, which
        # they cannot. A run log records both, so a result names its atlas revision.
        self.version = data.get("version")
        self.sha256 = sha256
        pages = [p for p in data.get("pages", []) if isinstance(p, dict)]
        # An overlay opens on top of a page without changing the URL, so it is
        # matched on the DOM instead and stacks on whatever page is underneath.
        self.pages = [p for p in pages if p.get("layer") != "overlay"]
        self.overlays = [p for p in pages if p.get("layer") == "overlay"]
        self.controls = [c for c in data.get("controls", []) if isinstance(c, dict)]
        for entry in self.controls:
            for field in (entry.get("key") or {}):
                if field not in KEY_FIELDS:
                    raise ValueError(f"Atlas control key uses an unknown field: {field}")

    def selectors(self, kind):
        """This atlas's extra selectors of one kind, appended to the defaults.

        A single string is accepted as a list of one. Anything that is not a
        non-empty string is dropped rather than injected into a selector list,
        where it would break every query on the page.
        """
        if kind not in SELECTOR_KINDS:
            raise ValueError(f"Unknown selector kind {kind!r}")
        extra = (self.data.get("selectors") or {}).get(kind)
        if isinstance(extra, str):
            extra = [extra]
        if not isinstance(extra, (list, tuple)):
            return []
        return [item.strip() for item in extra if isinstance(item, str) and item.strip()]

    def global_facts(self):
        """The atlas-level `global_facts_js` expressions: a list, or one bare string."""
        expressions = self.data.get("global_facts_js") or []
        if isinstance(expressions, str):
            expressions = [expressions]
        if not isinstance(expressions, (list, tuple)):
            return []
        return [e for e in expressions if isinstance(e, str) and e.strip()]

    def match_page(self, url):
        """The first page whose match rule accepts this URL, or None."""
        url = url or ""
        for page in self.pages:
            rule = page.get("match") or {}
            contains = rule.get("url_contains")
            wanted = [contains] if isinstance(contains, str) else list(contains or [])
            if any(part not in url for part in wanted):
                continue
            pattern = rule.get("url_regex")
            if pattern and not re.search(pattern, url):
                continue
            if not wanted and not pattern:
                continue
            return page
        return None

    def probe(self, browser, url_page=None):
        """One read-only evaluation per step: every facts_js result, every overlay test.

        Returns {"facts": {page id: [strings]}, "selectors": {overlay id: bool},
        "virtual": {page id: [controls]}}. An expression that throws, or returns
        anything but a non-empty string, contributes nothing.
        """
        found = {"facts": {}, "selectors": {}, "virtual": {}}
        fact_ids, fact_expressions = [], []
        # Local change: atlas-level facts, read on every page whether or not one matched.
        for expression in self.global_facts():
            fact_ids.append(GLOBAL)
            fact_expressions.append(GUARD.format(expression))
        for entry in ([url_page] if url_page else []) + self.overlays:
            for expression in entry.get("facts_js") or []:
                if isinstance(expression, str):
                    fact_ids.append(entry.get("id"))
                    fact_expressions.append(GUARD.format(expression))
        virtual_ids, virtual_expressions = [], []
        for entry in ([url_page] if url_page else []) + self.overlays:
            expression = entry.get("virtual_controls_js")
            if isinstance(expression, str) and expression.strip():
                virtual_ids.append(entry.get("id"))
                virtual_expressions.append(GUARD.format(expression))
        overlay_ids, overlay_expressions = [], []
        for overlay in self.overlays:
            selector = (overlay.get("match") or {}).get("selector")
            if selector:
                overlay_ids.append(overlay.get("id"))
                overlay_expressions.append(GUARD.format(VISIBLE.format(json.dumps(selector))))
        if browser is None or not (fact_expressions or overlay_expressions or virtual_expressions):
            return found
        try:
            values = browser.evaluate(
                f"[[{','.join(fact_expressions)}],[{','.join(overlay_expressions)}],"
                f"[{','.join(virtual_expressions)}]]"
            )
        except Exception:
            return found
        values = values if isinstance(values, list) else []
        facts, selectors, virtual = (list(values[i]) if len(values) > i and values[i] else [] for i in range(3))
        for page_id, controls in zip(virtual_ids, virtual):
            found["virtual"][page_id] = [c for c in (controls or []) if valid_virtual(c)][:60]
        for page_id, value in zip(fact_ids, facts):
            if isinstance(value, str) and value.strip():
                found["facts"].setdefault(page_id, []).append(value.strip())
        for overlay_id, value in zip(overlay_ids, selectors):
            found["selectors"][overlay_id] = bool(value)
        return found

    def active_overlays(self, selectors=None, dialog_title=None):
        """The overlays currently open, in file order.

        An overlay is active when its selector is visible or when the page's
        dialog title is the one it names.
        """
        selectors, active = selectors or {}, []
        for overlay in self.overlays:
            rule = overlay.get("match") or {}
            title = rule.get("dialog_title")
            by_selector = bool(rule.get("selector")) and bool(selectors.get(overlay.get("id")))
            by_title = bool(title) and bool(dialog_title) and title.strip() == dialog_title.strip()
            if by_selector or by_title:
                active.append(overlay)
        return active

    def match_control(self, element, page_id=None):
        """The most specific control entry matching this element, or None.

        Every field present in an entry's key must match. The entry with the
        highest total weight wins (see WEIGHTS); ties go to the first entry in the
        file. `page_id` may be one id or every id in view: the URL page plus each
        active overlay.
        """
        best, best_weight = None, 0
        for entry in self.controls:
            key = entry.get("key") or {}
            if not key:
                continue
            if all(_field_matches(field, value, element, page_id) for field, value in key.items()):
                weight = sum(WEIGHTS.get(field, 1) for field in key)
                if weight > best_weight:
                    best, best_weight = entry, weight
        return best

    def facts(self, browser, page):
        """Every non-null string the page's facts_js expressions return.

        One read-only Runtime.evaluate for the whole list; an expression that
        throws or returns a non-string contributes nothing.
        """
        expressions = [e for e in (page or {}).get("facts_js", []) if isinstance(e, str)]
        if not expressions or browser is None:
            return []
        guard = "(() => {{ try {{ return ({}) }} catch (error) {{ return null }} }})()"
        wrapped = ",".join(guard.format(e) for e in expressions)
        try:
            values = browser.evaluate(f"[{wrapped}]")
        except Exception:
            return []
        return [v.strip() for v in (values or []) if isinstance(v, str) and v.strip()]


def valid_virtual(control):
    """A virtual control the harness can offer: it needs a name and a way to write it."""
    return (
        isinstance(control, dict)
        and isinstance(control.get("label"), str)
        and control["label"].strip()
        and isinstance(control.get("set"), str)
        and control["set"].strip()
    )


def _field_matches(field, expected, element, page_id):
    if field not in KEY_FIELDS:
        return False
    if field == "page":
        if page_id is None:
            return False
        return page_id == expected if isinstance(page_id, str) else expected in page_id
    name = field.removesuffix("_regex").removesuffix("_contains")
    actual = element.get(name)
    actual = "" if actual is None else str(actual).strip()
    if field in REGEX_KEYS:
        try:
            return bool(re.search(str(expected), actual))
        except re.error:
            return False
    if field in CONTAINS_KEYS:
        return str(expected) in actual
    return actual == str(expected).strip()


def describe(page):
    """The authored lines of one page or overlay."""
    lines = []
    if not page:
        return lines
    head = " ".join(part for part in (page.get("name"), page.get("what")) if part)
    if head:
        lines.append(head.strip())
    if page.get("not_here"):
        lines.append(str(page["not_here"]).strip())
    leads_to = page.get("leads_to") or {}
    if isinstance(leads_to, dict) and leads_to:
        lines.append("Leads to: " + "; ".join(str(k) for k in leads_to))
    return lines


def page_context(page, facts=(), dialog_title=None, n_covered=0, overlays=()):
    """The page context string added to state.page.context. Empty without a page.

    An overlay stacks: the URL page first, then each active overlay in file
    order, each followed by its own facts.
    """
    lines = describe(page) + list(facts or [])
    for overlay, overlay_facts in overlays or ():
        lines += describe(overlay) + list(overlay_facts or [])
    if dialog_title:
        lines.append(f"Open dialog: {dialog_title}")
    if n_covered:
        lines.append(f"{n_covered} controls are behind the open dialog and cannot be clicked")
    return "\n".join(line for line in lines if line)


def load(path):
    """Load an atlas file. Raises ValueError if it is not a usable atlas."""
    file = Path(path)
    try:
        raw = file.read_bytes()
        data = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read atlas {file}: {error}") from None
    return Atlas(data, file, digest(raw))


def digest(raw, length=12):
    """The first `length` hex characters of the sha256 of the atlas file's bytes."""
    return hashlib.sha256(raw).hexdigest()[:length]

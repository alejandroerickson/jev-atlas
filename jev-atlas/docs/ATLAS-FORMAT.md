# Atlas format: the contract between the harness and the atlas author

One JSON file per application, named by `JEV_ATLAS`. The harness holds no
application knowledge; everything about the application lives in its atlas, and
pointing `JEV_ATLAS` at a different file is all it takes to move to another
application. The author must not know any test task: the atlas says what pages and
controls *are for*, never a procedure.

This page is the overview and the writing rules. The field-by-field reference for
the harness this folder builds (every key field, its weight, what the reader
extracts per element, the reader's behaviour without an atlas, the environment
variables) is [`../harness/ATLAS-FORMAT-ADDENDUM.md`](../harness/ATLAS-FORMAT-ADDENDUM.md).
The source of truth is `jev_ultrafast/atlas.py` in the harness.
[`BUILDING-A-SHIM.md`](BUILDING-A-SHIM.md) is the process for writing one.

The examples are from the ADIT atlas (`../atlas/adit.json`); they illustrate the
format and are not part of it.

```json
{
  "app": "ADIT",
  "version": "2026-09-22-merged-h2",
  "selectors": {"dialog": ["dialog[open]"]},
  "global_facts_js": ["(() => { try { /* read the signed-in user */ return 'Signed in as …' } catch (e) { return null } })()"],
  "pages": [
    {
      "id": "approval-approve-dialog",
      "layer": "overlay",
      "match": {"selector": "dialog.dlg[open][aria-label^=\"Approve: \"]"},
      "name": "Approve dialog",
      "what": "Confirms passing the current step of the request. …",
      "not_here": "Sending the request back for revision is Return, and ending it is Reject; …",
      "facts_js": ["(() => { try { /* the dialog's summary */ } catch (e) { return null } })()"]
    }
  ],
  "controls": [
    {
      "key": {"text_regex": "^Approvals( \\(.*awaiting you\\))?$", "role": "link", "landmark": "navigation: Sections"},
      "region": "Top bar, section links",
      "what": "Opens the Approvals section: the queue of workflow requests. …",
      "not_for": "Notifications about approvals (the bell) …"
    }
  ]
}
```

## Pages

A URL page matches on `url_contains` / `url_regex` (the route fragment counts,
so `#/approvals` works). An **overlay** (`"layer": "overlay"`) is something that
opens over a page without changing the URL: a menu, a panel, a dialog. It matches
on `selector` (at least one visible element) or `dialog_title` (the open dialog's
title, exact after trimming).

- An overlay **stacks** on the URL page: Jev's page context is the URL page's
  `name` + `what` + `not_here` and facts, then each active overlay's, in file order.
- A control whose `key.page` names an overlay id matches only while that overlay is
  active.
- Order matters: the first URL page that matches wins, so put specific routes
  before general ones and a catch-all (`not-found`) last.

`facts_js` is a list of read-only JS expressions; each non-empty string result
becomes a line of the page context. `global_facts_js` runs on every page, matched or
not, before the page's own facts: use it for things true everywhere (who is signed
in, unread counts, the last toast).

## Controls

Each entry has a `key` and the notes Jev is shown for every element that matches:
`region`, `what`, `not_for`, and optionally `options` (the allowed values, passed to
the text helper only). **Every field in a key must match.** When several entries
match, the heaviest key wins (for example `id` 3, `text` 2, `role` 1; the table is
in the addendum), and ties go to the first entry in the file. Unmatched elements
keep their bare label and are still offered: the atlas annotates, it never hides.

A matched option reaches Jev as an object instead of a string:

```json
{"element": "[12] Approve", "region": "Request head actions",
 "what": "…", "not_for": "…", "in_dialog": false}
```

When two offered elements share a label, each also carries the `row` and/or
`section` that tells them apart.

## Virtual controls

For widgets whose cells are not DOM elements (a canvas grid, a spreadsheet), a
page or overlay may declare `virtual_controls_js`: one read-only expression that
returns a list of fill targets, each with `label` and `set` (a JS function taking
the value and returning `true` on success) and optionally `id`, `current_value`,
`row_label`, `region`, `what`, `not_for`. They are offered for typing only. `set`
must go through the application's own widget API or keyboard path so the
application's change tracking sees the edit. ADIT keeps one: the New estimate
form's tonnes-and-grade set.

## Selectors

`selectors.dialog`, `selectors.busy` and `selectors.dialog_title` take CSS selectors
(a list, or one bare string) and are **appended** to the harness's generic defaults,
never replace them. Put application- or widget-library-specific dialog and
loading-indicator selectors here. Keep busy selectors narrow: an element that is
always visible makes every page look busy.

## Writing rules

- Describe purpose and scope: what the control does, what it does *not* do and
  which control does that instead. Write descriptions that **separate options from
  each other**; front-load what differs.
- Never describe a procedure ("to approve, first open…"). Never name a record, a
  person, an amount, a year or a code that a task could use.
- Prefer the most stable key: `id`, then (`landmark`/`section`, `text`), then
  (`page`, `text`), then `href_regex` for families of record links. A key that
  contains a record id is not a key.
- `facts_js`, `global_facts_js` and `virtual_controls_js` must be read-only (except
  `set`), return a string/null (or a list), and never throw: wrap them in try/catch.

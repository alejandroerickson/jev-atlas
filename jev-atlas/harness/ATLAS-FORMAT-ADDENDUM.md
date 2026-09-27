# Atlas format for the ADIT harness (addendum)

The harness in `jev-ultrafast-adit` (built by `bootstrap.sh`) reads an optional
JSON atlas named by `JEV_ATLAS`. Without one it behaves as upstream plus the local
changes in `local-changes.patch`. This page is the self-contained contract for this
harness copy; the source of truth is `jev_ultrafast/atlas.py` and `model.py`.

## Top level

```json
{
  "app": "ADIT",
  "version": "2026-09-22",
  "pages": [ ... ],
  "controls": [ ... ],
  "selectors": {"dialog": [ ... ], "busy": [ ... ], "dialog_title": [ ... ]},
  "global_facts_js": [ ... ]
}
```

`global_facts_js` (a list of JS expressions, or one bare string) is read on every
page, matched or not, in the same single evaluation as the page facts. Each
non-empty string result becomes a line of the page context, **before** the page's
own facts. Use it for things true everywhere (who is signed in, how many
notifications are unread) instead of faking an always-open overlay.

`version` is whatever the author declares; a run log also records a 12-character
sha256 of the file's bytes, so a result names its atlas revision either way.

## pages

| Field | Meaning |
|---|---|
| `id` | Name used by control keys (`page`) and in run logs. |
| `match` | `url_contains` (string or list, all must be present) and/or `url_regex`. An overlay matches on `selector` (visible CSS) or `dialog_title` (exact, trimmed). |
| `layer` | `"overlay"` for something that opens over a page without changing the URL; it stacks on the URL page. |
| `name`, `what`, `not_here` | Sentences added to the page context Jev sees. |
| `leads_to` | Object whose keys are listed as "Leads to: ...". |
| `facts_js` | List of read-only JS expressions; each non-empty string result is added as a line. Errors contribute nothing. |
| `virtual_controls_js` | One JS expression returning a list of controls the DOM does not expose (cells and the like): `label` and `set` (a JS function taking the value and returning `true` on success) are required; `id`, `current_value`, `row_label`, `region`, `what`, `not_for` are optional. Offered for typing only. |

## controls

Each entry has a `key` and the notes Jev is shown for matching elements:
`region`, `what`, `not_for`, and optionally `options` (the allowed values, given
to the text helper only).

Key fields:

| Field | Matches | Weight |
|---|---|---|
| `track_id` | the element's `data-track-id`, exact | 3 |
| `id` / `id_regex` | the element's DOM `id` | 3 / 2 |
| `title` | the `title` attribute, exact | 2 |
| `text` / `text_regex` / `text_contains` | the accessible name as offered (the part before ` → ` for a select option) | 2 |
| `href` / `href_regex` / `href_contains` | the link target as path + query, **plus the fragment when it is a route** (`#/…` or `#!/…`), e.g. `/mockent/adit/#/projects/PRJ-0441`. An in-page anchor (`#content`) is dropped. | 2 |
| `row_label` / `row_label_regex` | the element's row label (below) | 2 |
| `role` | the offered role (`button`, `link`, `textbox`, `radio`, ...) | 1 |
| `ancestor` | the nearest custom-element tag | 1 |
| `page` | a page id or an open overlay id | 1 |
| `section` / `section_regex` | the block the element sits in (below) | 1 |
| `landmark` / `landmark_regex` / `landmark_contains` | the nearest landmark (below) | 1 |

`*_regex` is a Python `re.search`; `*_contains` is a plain substring; the rest are
exact after trimming. Every field in a key must match. The heaviest key wins; ties
go to the first entry. An unknown key field fails the load.

### Fields the reader extracts per element

- **`row_label`**: a form widget's row label (a `label`, a `*label*`-classed element
  or a `th` in the same row), found by walking up at most four block levels. It
  stops at a landmark and ignores a `<label>` that belongs to a different control
  (so a header button no longer borrows a comment box's label, nor a radio its
  sibling's). **In a table row** (`tr`, `role=row`) it is the row's identifying
  cells: a row header (`th[scope=row]`, `role=rowheader`) if there is one;
  otherwise the first cell without a control, extended with the next such cells
  (up to three, joined by ` · `) until no sibling row starts the same way. So
  identical per-row buttons read e.g. `selected · T-08`, `selected · T-09`.
  A header row (in `thead`, or with `th[scope=col]` / `role=columnheader` cells)
  gives no row label. **In a flat grid** (a container whose children repeat a
  short sequence of 2-8 cells, matched on tag and first class, e.g. a ledger of
  `span.k, span.w, span.d, span.a` per line) it is the first cell of the
  control's own line. Before 2026-09-22 (third round) it was the grid's first
  child for every line, so every ledger link read `Approval overdue`, including
  lines that were only `Approval due`, `Tenure expiring` and so on. Likewise a
  label or first child that belongs to a sibling list item is no longer borrowed.
- **`row_context`**: the identifying line of the row, list item or card the
  control sits in, for telling rows apart; it is not a key field. Up to three
  pieces of the row's own text in page order, each cut to 80 characters, joined by
  ` · `, typically its title and a short status. A table row gives its other cells
  (link text included, so an id-only link such as `WF-2026-0146` carries its
  row's title); a flat-grid line its other cells (`Approval due · due tomorrow ·
  Manager approval`); a list item, `article`, or any block repeated among its
  siblings its other blocks, when it is small (at most three controls besides the
  control's peers, and 400 characters). Left out: the control's own text, blocks
  holding a button or a field, and its peers (the other tabs of a tab strip, the
  other tickets of a column). A field (textbox, combobox, select) gets one only
  inside a table row. It is dropped when equal to `row_label` or the label.
- **`section`**: the nearest of an enclosing `fieldset`'s `legend`; a named
  `role=group|radiogroup|region` or `<section>` (aria-label / aria-labelledby); or
  the last visible heading (`h1`-`h6`, `role=heading`) before the element inside
  one of its ancestors. It does not cross a dialog. Two "Grade" fields under
  *Indicated* and *Inferred* legends get those as sections.
- **`landmark`**: the nearest `nav`/`header`/`main`/`aside`/`footer`/`search`
  element or `role=navigation|banner|main|complementary|contentinfo|search`
  (plus `region`/`form` when named), as its ARIA role followed by `: name` when it
  has an accessible name: `navigation: Sections`, `navigation: Breadcrumb`,
  `banner`, `main`. `<header>`/`<footer>` count as banner/contentinfo wherever
  they are (a simplification of ARIA's scoping rule).
- **`input_type`**: set only on `date`, `time`, `datetime-local`, `month` and
  `week` inputs (see below).
- **`via_label`**: the control is a visually hidden checkbox or radio offered as
  its label (see below).
- **`offscreen_x`**: the control is beyond the side of the window inside a
  horizontally scrolling container (see below).

What Jev sees: every element with a `row_context` carries it as `row`, on the
element and on its target choices (third round). When two or more offered
elements share a label and their row labels or sections differ, those without a
row context carry the row label as `row`, and `section` as before. The text
helper gets the row context as `field.row`.
The run log's `elements_debug` shows `section`, `landmark`, `href`, `via_label` and
`offscreen_x` for every control, so keys can be checked against a real run.

## Shared notes (what Jev sees)

When two or more offered elements match atlas notes with the same `what` and
`not_for`, the note is sent once: `state.shared_notes` maps an id to
`{"elements": [indices], "region"?, "what", "not_for"}`, and each of those
elements and its target choices carry `"note": "N1"` instead of the text.
`region` moves into the shared note only when all of them have the same one;
otherwise it stays on each element. A note used by one element stays inline.
`JEV_SHARE_NOTES=0` turns this off. On the logged ADIT portfolio page (with atlas,
four shared notes) the request fell from 50.2 KB to 35.3 KB (-30%); other logged
steps fell 0-21%. Replayed on five logged first steps (jev-1.13.0), the chosen
operation was unchanged; the top click target was unchanged on four and moved on
one from a wrong ledger link to the Approvals queue link.

## Operation rules and today's date

- The operation rules add: "Opening a link or section that leads toward where the
  goal is done counts as progress." The BLOCKED option's criterion is "No visible
  control makes progress, not even navigating toward a page where the goal could
  be done." (upstream: "No supported operation can progress."). The DONE threshold
  (`JEV_TERMINAL_MAJORITY`, 0.5) is unchanged.
- The text helper's input starts with `today` (YYYY-MM-DD; `JEV_TODAY` fixes it,
  otherwise the clock) and its instructions say to resolve a relative or partial
  date against it, to the next such date unless the goal names a year.
- `JEV_TODAY_FACT=1` also puts "Today is YYYY-MM-DD (Weekday)." first in the page
  context Jev sees (atlas runs only). Off by default.

## Reader and executor behaviour (no atlas needed)

- **Native `<dialog>`**: `dialog[open]` is a dialog by default. The dialog title
  is looked up in this order: the atlas's `selectors.dialog_title` (CSS selectors
  for the title element, first visible non-empty hit wins); the built-in heading
  selectors (`[role=dialog] h1/h2`, `dialog[open] h1/h2`, `[role=dialog]
  [class*=title]`, `[aria-modal=true] h1/h2`); then each open dialog, topmost
  first, by `aria-labelledby`, `aria-label`, then its first visible heading. A
  native `<dialog aria-label="Save this scenario">` therefore reads as `Open
  dialog: Save this scenario`, and an overlay can match on `dialog_title`.
- **Date and time inputs** (`date`, `time`, `datetime-local`, `month`, `week`) are
  offered as `textbox`, for TYPE_TEXT only (no "Open …" click: the native picker
  is outside the page). The text helper is told the format (`field.format`, e.g.
  `YYYY-MM-DD`). The executor converts common spellings (`30 November 2026`,
  `2:30 PM`) to that format, checks the value on a detached input of the same
  type, then writes it through `HTMLInputElement.prototype`'s value setter and
  fires `input` and `change`, which framework-controlled inputs (React's value
  tracker) need. A value the input cannot hold is refused with an error and the
  field is left untouched.
- **Visually hidden checkboxes and radios** (opacity 0, under 4×4 px, clipped, or
  `display:none`) whose `<label>` is visible are offered as that label: the
  label is what is hit-tested and clicked, the role and `checked` state are the
  input's. A hidden input with no visible label is still not offered.
- **Controls beyond the side of the window**: a control whose centre is left or
  right of the window, but inside a horizontally scrolling container (or a page
  that scrolls sideways), is offered with `offscreen_x`; the executor scrolls it
  into view (`scrollIntoView({inline: 'center'})`) before hit-testing and
  clicking. Beyond the edge of a non-scrolling container it is not offered.
  Vertical reach is unchanged (the Scroll down / Scroll up actions).
- **Submitting a field with Enter (PRESS_ENTER, fourth round).** A single-line
  `<input>` that holds a value and is a search field (`type=search`, `role=searchbox`,
  or inside `<search>` / `role=search`) or the focused field is also offered with kind
  `submit`, which Jev sees as the operation `PRESS_ENTER` ("Press Enter in a text field
  that already holds the wanted value, to submit it ...") with its own target head
  `press_enter_target`. The executor focuses the field and presses Enter; there is no
  click and no text-model call. The atlas note that matches the field matches its
  `submit` action too (same key fields). A plain search box (no list, popup or
  autocomplete attributes) is no longer offered an "Open …" click.
- **Links that open a new tab** (`target` other than `_self`/`_top`/`_parent`)
  open in the agent's own tab: the executor sets `target="_self"` for the click
  and restores the attribute afterwards. `JEV_SAME_TAB=0` turns this off (the
  link then opens a background tab the agent never sees). `window.open()` from
  script is not intercepted.

## Environment

| Variable | Default | Meaning |
|---|---|---|
| `JEV_ATLAS` | none | Path of the atlas JSON. |
| `JEV_VIEWPORT` | `1120x780` | `WIDTHxHEIGHT` of the agent's tab. For ADIT use `1700x900`: the Users and optimiser tables still scroll sideways at that width (handled by `offscreen_x`), but fewer controls need it. |
| `JEV_SAME_TAB` | `1` | `0` lets new-tab links open a new tab. |
| `JEV_SHARE_NOTES` | `1` | `0` repeats every atlas note on every element and choice. |
| `JEV_TODAY` | the clock | `YYYY-MM-DD` the text helper (and the optional fact) take as today, for reproducible runs. |
| `JEV_TODAY_FACT` | off | `1` adds "Today is ..." to the page context (atlas runs). |

## selectors: application-specific dialogs and busy indicators

This is the atlas-level place for anything a particular application or widget
library needs to be recognised as a dialog or as "still drawing". The harness
defaults are generic web conventions only:

- dialog: `[role="dialog"]`, `[role="alertdialog"]`, `[aria-modal="true"]`, `dialog[open]`, `.modal`
- busy: `[aria-busy="true"]`, `[class*="loading" i]`, `[class*="spinner" i]`, `[class*="busy" i]`

In addition, any element whose tag name or class matches
`busy|loading|spinner|progress` *and covers a control* marks the page busy.

`selectors.dialog`, `selectors.busy` and `selectors.dialog_title` each take a list
of CSS selectors, or one selector as a bare string. `dialog_title` has no defaults
and names the element holding a dialog's title (see above). They are **appended** to the defaults, never replace
them; empty or non-string entries are dropped. Both page readers (`snapshot.js`
and the settle probe) receive the same combined lists. Example for a hypothetical
widget library:

```json
"selectors": {
  "dialog": [".xw-window", "app-popup"],
  "busy": [".xw-overlay-mask", "app-busy-indicator"]
}
```

Keep busy selectors narrow: an element that is always visible (a permanent mask
layer, a static progress bar) makes every page look busy and costs the settle
budget on every step.

## Changes from the upstream-derived harness (2026-09-22)

Fourth round:

- New operation `PRESS_ENTER` (action kind `submit`, target head `press_enter_target`),
  described above. It is offered identically with and without an atlas.
- No "Open …" click twin on a plain search box.
- Tests: `tests/fixtures/search-form.html` in `tests/test_snapshot_dom.py`, and three
  PRESS_ENTER tests in `tests/test_agent.py` (116 tests in all).

Third round, from replaying logged requests to jev-1.13.0:

- Operation rules: navigating toward the goal is progress; BLOCKED's criterion
  means no way forward at all. Replays: first-page BLOCKED 0.53-0.67 -> 0.15-0.29
  (two goals, three logged runs each, two calls each), and it lost the top spot in
  all twelve calls. The final-step DONE of three finished goals (five logged runs,
  two calls each), averaged per run, moved by -0.15 to +0.10; 2 of 10 calls fell
  under 0.5, both on one Lorimer run (whose logged date had the wrong year).
- The text helper is told today (`today`, first in its input; `JEV_TODAY`);
  optional page fact `JEV_TODAY_FACT=1`. Replay of the logged "end of January"
  field on 2026-09-22: 2026-01-31 in 15/15 calls before, 2027-01-31 in 15/15 after.
- `row_label` in flat grids and lists takes the control's own line or item, not
  the container's first child; header rows give none.
- New `row_context`, sent to Jev as `row` on every element that has one.
- Shared atlas notes (`state.shared_notes`, `JEV_SHARE_NOTES`).
- Tests: `tests/test_context.py`, and `tests/fixtures/rows.html` in
  `tests/test_snapshot_dom.py`.

Second round, from the ADIT shim authors' notes:

- `href` keeps a route fragment (`#/…`, `#!/…`).
- `dialog_title`: atlas `selectors.dialog_title`, then built-ins, then the open
  dialog's aria-labelledby / aria-label / first heading.
- Date and time inputs are offered and written through the native setter.
- Visually hidden checkbox/radio inputs are offered as their visible label.
- `row_label`: table rows take their identifying cells; the walk stops at
  landmarks and skips labels owned by other controls. New `row_label_regex`.
- New element fields and keys: `section`, `landmark` (+ `_regex`, `landmark_contains`).
- Duplicate labels reach Jev with `row` / `section`.
- Atlas-level `global_facts_js`.
- Controls beyond the side of a horizontally scrolling container are offered and
  scrolled to; `JEV_VIEWPORT` was already configurable.
- New-tab links open in the agent's tab (`JEV_SAME_TAB`).
- Tests: `tests/test_snapshot_dom.py` runs `snapshot.js` and the executor in a
  headless Chrome against `tests/fixtures/hash-app.html` (skipped without Chrome).

First round:

- The defaults no longer carry application- or library-specific entries; those
  now belong in an atlas under `selectors`. Class-based library loading masks are
  still caught by `[class*="loading" i]`.
- `[role="alertdialog"]` and `dialog[open]` were added to the dialog defaults, and
  `dialog[open] h1/h2` to the dialog-title lookup, as generic conventions.
- `uv.toml` pins the package index to public PyPI so `uv run` never rewrites
  `uv.lock` with a private registry from the machine's own uv configuration.

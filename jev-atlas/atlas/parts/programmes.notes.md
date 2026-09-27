# Programmes area: notes for the merger

Fragment: `programmes.json` (15 pages, of which 4 are overlays, and 115 controls). Written 2026-09-22 by a blind
author: I did not read goals, runs, the experiment files or the log. Wording comes from the manual mirror
`jev-atlas/manual/programmes.md` (the in-app manual, section 5, fetched 2026-09-22) and was checked against the
live screens in headless Chromium, using fresh browser contexts. Nothing was kept, because every context started
with fresh localStorage.

Generator and self-check: `../../tools/programmes/gen.py`,
`selfcheck.py`. The self-check runs the harness's own `snapshot.js` and `atlas.py` (`match_page`, `probe`,
`active_overlays`, `match_control`), using the same fields `model.match_fields` builds.

## Coverage

URL pages (`match.url_regex`, anchored with `$` so the file order does not matter):

| id | route |
|---|---|
| programmes-list | `#/programmes`, `?phase=planning/complete/all`, `?type=…` |
| programmes-new | `#/programmes/new` |
| programmes-schedule | `#/programmes/schedule` |
| programmes-rigs | `#/programmes/rigs` |
| programmes-camps | `#/programmes/camps` |
| programmes-crew-rotations | `#/programmes/crew` (paged; First/Previous/Next/Last) |
| programme-overview | `#/programmes/:id` |
| programme-crew / -logistics / -holes / -approval | `#/programmes/:id/crew` and the other three tabs |

Overlays (all are native `<dialog open>`, matched by `match.selector` on the dialog's `aria-label`):
`programme-move-dialog` (Move PRG-… to <phase>), `programme-assign-crew-dialog`, `programme-logistics-item-dialog`
(covers both Add a logistics item and Edit LG-…), and `programmes-rig-update-dialog` (Update RIG-…). Each selector was
tested three times: not visible while closed, visible while open, not visible after Cancel. No other overlay's
selector fired at the same time.

States walked, with the user switched through `adit.session.v1.currentUserId`: phase groups; type filter; New
programme, empty and after a failed submit; programmes in draft, scoped, costed (with and without an approval
request), approved, in progress, demobilising, complete and cancelled; all five tabs; every dialog; Remove crew; a
phase move; Submit for approval; the overlap refusal in Assign crew; Post comment; and rig Update as the logistics
user.

Self-check (2026-09-22): 24 states. **650/650 visible Programmes-area controls annotated (100%)**, excluding the
global header, which is another agent's. With a dialog open, only the dialog's controls were counted. 110/115 entries
matched at least one live element. The 5 that matched nothing only appear in certain states: `Submit for approval` on
the four non-Overview tabs, and `Post comment`, which shows only when the comment box has text. Both were seen live on
Overview. The facts and virtual controls were run live. The virtual `set` functions were checked against the app's own
state: a draft created after setting Start and End through the virtual controls stored exactly those dates, and the
type filter changed the list's URL.

## Match-key decisions

- **The DOM gives almost nothing stable.** There are no ids, no `data-track-id`, no custom elements (so `ancestor` is
  always null) and no test hooks. The only `data-*` attributes are `data-key`, `data-status` and `data-discover`,
  and the reader does not extract any of them. **`href` is useless here:** `snapshot.js` keeps `pathname+search` and
  drops the hash, so every in-app link reads as `/mockent/adit/`. That leaves `text`, `text_regex`, `role`,
  `row_label` and `page` as the keys.
- **Left column:** `{row_label: "Programmes" | "Resources", role: link, text_regex: "^In the field\b"}` and so on.
  The count in each label changes, so the key is a regex.
- **Programme page header and tabs** are repeated once for each of the five tab pages, keyed with `page`. I did not
  key them without a page because other areas may also have `Move to …` or `Approval` controls.
- **Record links** get a generic `{page, role: link, text_regex: NOT_NAV}` entry on each page. NOT_NAV is a negative
  look-ahead that excludes navigation labels and the id patterns (PRG-, RIG-, WF-, hole ids) that have their own
  entries. It exists because a programme-name link and a project-name link in the same row cannot be told apart by any
  key. Its description covers both.
- **Sort headers:** one `{page, role: button, text_regex: "^Sort by "}` per page.
- **Row buttons** (Remove, Edit, Update) are keyed on `{page, role, text}`. Their `row_label` is the row's person, item
  or rig id, which the model sees anyway.
- `row_label` is noisy on the programme page: `Add a comment` becomes the row label of most header controls. I only
  use it for form fields and for the comment box, always together with `page`.

## What the harness cannot see (format and harness issues; please pass on)

1. **The native `<dialog>` is not in `DEFAULT_DIALOG`**, and every ADIT dialog is one. The fragment adds
   `selectors.dialog: ["dialog[open]"]` and `selectors.dialog_title: ["dialog[open] h2"]`. Without these, `in_dialog`
   is never set. On 2026-09-22, the `dialog_title` loop in `snapshot.js` still used a hard-coded list, so
   `dialog_title` came back as `''` even with the atlas selectors. The overlays still work, because they match by
   selector.
2. **`input[type=date]` gets no role in `snapshot.js`,** so date fields are never offered: Start and End in New
   programme, Rotation start and end in Assign crew, Scheduled in the logistics item dialog. I added them as
   `virtual_controls_js`, which writes through the native value setter and fires input and change events.
   **Fixing the reader would be better.**
3. **Visually hidden radio pills are dropped** (`opacity: 0`, 1×1 px inside a clickable `<label>`). The type filter on
   the list is therefore offered only as a virtual control, `Type filter`, which clicks the label. The same pattern
   probably appears in other areas' filter bars.
4. **The `href` of a hash-routed link loses its route** (see above). If `hrefPath` kept `u.hash`, record links could
   be keyed cleanly with `href_contains: "#/programmes/"`.
5. **The reader skips off-screen controls** (the `x/y >= innerWidth/innerHeight` check). The self-check used a
   4200 px-tall viewport to see every row.

## For the merger

- **Shared components:** the toast (`.toasts`, with a `Dismiss` button and sometimes an `Open` link). I included one
  entry, `{role: button, text: "Dismiss"}`; keep a single copy across the fragments. The `Open` link in a toast is not
  described because its key is too generic. The Comments panel (the `Add a comment` textbox and `Post comment`)
  probably appears on other record pages too. My entries for it are restricted to `page: programme-overview`.
- **Breadcrumb `Programmes`** has the same text and role as the top-nav `Programmes` link. I left it to the nav
  owner. My generic link entries exclude it.
- **The `TOAST_FACT`** (`Notice on screen: …`) is in every page's `facts_js`. If a global fact is added elsewhere,
  drop one of them.
- The `options` lists (programme type, logistics kind and status, rig status) are fixed enumerations of the app,
  not data. Project, person and rig lists are left unenumerated on purpose.
- The field label `Budget, USD` appears as a key and in the text because it is the app's own label.

## What each user sees (observed 2026-09-22)

The header's `Move to …`, `Submit for approval` and `Assign crew` appear only for some users. They appeared for the
programme's lead (a project geologist). The default user, the Exploration Manager, sees none of them in the header but
does see `Assign crew` and `Remove` on the Crew tab. `Update` on Rigs is shown only to the logistics coordinator.
`HEADER_FACT` reports which header actions are offered to the current user. **Dangerous or irreversible controls**,
all described plainly: `Remove` (deletes a crew assignment, no confirmation), `Submit for approval` (raises a workflow,
no confirmation), `Confirm` in the move dialog (moving to complete closes the ledger).

## Doubts

- There is no cancel-programme or edit-programme control anywhere in the UI, although the manual lists a
  "cancelled" phase. `not_here` on Overview says there is no field edit.
- Of the Camps columns, only `Camp` sorts. The other headers are plain text.
- A demobilised rig is a disabled option in the New programme Rig list, and the reader skips disabled options.

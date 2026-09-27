# ADIT atlas

`adit.json` is the application atlas for ADIT, the mock mineral-exploration app at
https://alejandroerickson.com/mockent/adit/. The harness in
`jev-atlas/vendor/jev-ultrafast` reads it when `JEV_ATLAS` points at it
(`jev-atlas/run.sh with …` sets that up). The file describes what each page and control
is for. It says nothing about any task. Its contract is
`jev-atlas/harness/ATLAS-FORMAT-ADDENDUM.md`, and the matcher is `jev_ultrafast/atlas.py`.

- File: `adit.json`, version `2026-09-22-merged-h4+learned-3`: the merged atlas below plus the three
  lessons in `learned/accepted/` (see [Learned lessons](#learned-lessons-2026-09-26)). With no lessons accepted,
  `merge.py` rebuilds the base version `2026-09-22-merged-h4`.
- sha256: `01ab2847c5c8602f5170911a9088209210e393b9f05bec163450c92a44016210` (run logs record the first 12
  characters, `01ab2847c5c8`); the base version's is `42127d245c6477198b92a1b78b5fb319e26ce8f0db402035bdcf102a5279f004`
- Contents: 88 pages (63 URL pages and 25 overlays), 593 control entries, 5 `global_facts_js`
  expressions, and one `selectors` block (`dialog[open]`)
- Validated against the harness built from `jev-atlas/harness/local-changes.patch`, sha256
  `09d0ea3d98cde4383d6e87ce9c13e3fae017b9723b14c7243b899ce9d063afcc` (the fourth-round
  harness: the second round's route hrefs, row identities, `section`, `landmark`, native
  date inputs, hidden toggles offered as their labels, horizontal reach and
  `global_facts_js`; the third round's row context and shared notes; and PRESS_ENTER)

## How it was built

Seven blind authors each surveyed one area of the live app and wrote a fragment in
`parts/` (`<area>.json`). Each fragment has notes for the merger (`<area>.notes.md`). The
areas are portfolio-global (the top bar, account, search, notifications, manual and
not-found pages), projects, programmes, drilling-assays, resources-optimiser, approvals
and admin. `../tools/merge.py` combines the fragments into `adit.json`, and applies the
second-round rules in `../tools/harness2.py`. Nothing edits the JSON by hand; each change
is a rule in one of the two scripts.

### First round (merge.py)

- **Pages** are placed in an explicit order: specific routes come before general ones, and
  `not-found` comes last as the catch-all. Page ids are unique, which the script checks.
  Three route fixes came from live observation:
  - `#/admin/system` is System settings, so `admin-settings` matches it.
  - `#/portfolio/<other>` renders the stage board, so `portfolio` matches it.
  - `not-found` also covers unknown sub-routes such as `#/admin/x`, `#/resources/x`
    and `#/account/x`, all of which the app answers with "Page not found". All 13
    top-level roots are listed.
- **Facts.** The four chrome facts from portfolio-global (the signed-in user and role, the
  highlighted section, the unread and awaiting counts, the toast message) are the
  atlas-level `global_facts_js`, read once on every page, matched or not. No page repeats
  them. The fragments' own copies of the signed-in and toast facts (92 expressions) were
  dropped.
- **`leads_to`.** Every value is a page id or a list of page ids.
- **Shared components**, one entry each: sort headings, pager, toast Dismiss, the Open link
  in a confirmation, the dialog close cross, dialog Cancel, the comment box, Post comment,
  "Values behind this chart", the provenance stamp, the footer User Manual link, the
  account-menu User Manual link, and a fallback for any breadcrumb link. These replaced
  per-area copies whose wording did not always agree.
- **Control order.** Ties go to the first entry in the file, so the order is: dialog-overlay
  entries (they share text with the page buttons that open them), the global chrome, the
  areas, the shared components.

### Second round (harness2.py), for the upgraded harness

- **Landmarks** separate chrome that has the same text elsewhere. Top-bar section links
  are keyed `landmark: navigation: Sections`, the other top-bar controls `banner` or
  `search`, breadcrumbs `navigation: Breadcrumb`, the footer `contentinfo`, and the account
  menu `banner` plus the menu overlay. The 13 per-page breadcrumb entries that the first
  merge had to drop (same text, role and target as the top-bar links) are back.
- **Routes instead of record-name regexes.** The 29 page-scoped catch-alls ("any link that
  is not a chrome label is a record name") are replaced by one entry per route the page
  links to, keyed by `href_regex` (`#/projects/PRJ-…`, `#/programmes/PRG-…`,
  `#/approvals/WF-…`, …), each with its own description. The Portfolio registers'
  project-name links, left bare before, are keyed the same way, as are the budget table's
  project ids (they open the Budget tab, not the Overview).
- **Entries broken by the new `row_label`.** In a table row the reader now reports the
  row's identifying cells, not the nearest label. Fixed:
  - the Portfolio "Needs attention" ledger: every item now reads the first line's kind, so
    the six per-kind entries described tenure, batch and gate items as overdue approvals.
    They are now keyed by `section` and route (approval, tenure, batch, programme,
    vacancy, gate due);
  - search results and notifications are keyed by `row_label_regex` on the row's leading
    kind (`^project( ·|$)`, `^unread( ·|$)`, …);
  - the approval head's project link was keyed by the status chip before it (five
    entries); it is one entry by route, and the Subject link is scoped to its `section`.
- **Identical row buttons.** Lock, Locked and Exclude (optimiser), Update (rigs), Remove
  (crew), Edit (logistics, users) are keyed with the row identity the reader now reports
  (`row_label_regex` on the id pattern, or `section`), and each description says what
  tells the rows apart (status and target id, rig id, person's name, item id). No
  description names a record.
- **Virtual controls.** Seven are dropped because the reader now offers the native control,
  and each native control was checked live at 1700×900 by emulating the executor:
  - date fields (New programme Start/End, Edit project Next gate, Assign crew rotation
    dates, logistics Scheduled, Update hole Completed): offered as `textbox` with
    `input_type=date`, written through the native setter, value kept after a re-render and
    after Save;
  - the programme type pills and the dispatch hole pills (hidden radios and checkboxes):
    offered as their labels; clicking filters the list (a second click clears it) or ticks
    the hole and enables Submit dispatch.
  The intercepts commodity pills, newly offered the same way, got an entry. The one virtual
  control kept is the New estimate form's tonnes and grade set, which is neither a date nor
  a hidden toggle; the native fields beside it are now keyed by `section` (Indicated,
  Inferred).

### Third round: wording rules (2026-09-22)

Measured runs showed the atlas hurting Jev through its wording. Replays showed that the
rewording is what helps: moving the same negative text elsewhere, or prefixing it with
"Elsewhere", did not. Every generator (`tools/<area>/`, `merge.py`, `harness2.py`) was
rewritten to these rules, which `../docs/BUILDING-A-SHIM.md` §5 also states:

1. **Route, do not refuse.** `not_here` and blocking `not_for` text is positive routing
   ("Deciding a request: the request's own page in Approvals."), never "not here",
   "nothing on this page…", "cannot…". All 88 page `not_here` texts were checked.
2. **State the situation, not the absence.** Facts such as "No actions are offered to you
   on this request" now say who gets the buttons and where the signed-in user is
   changed; the admin view-only, estimate-actions, dispatch and Save draft facts
   likewise. Neutral state ("not ticked", "Table: no requests in this view.") stays.
3. **No example values.** No dates ("such as 30 November 2026" → "a calendar date"),
   permission codes or audit action codes as examples.
4. **Purpose and destination, not procedure** ("go back to", "click…", "use…").
5. **Short per-row text.** Row links, row buttons and search, notification and ledger
   rows have one short shared description; the harness adds the row identity.

Remaining grep hits in `adit.json` for
`\bnot here\b|nothing (on|here)|cannot|can't|\bno \w+ (is|are) (offered|available)`: one,
the key text of the Reset tenant tick box ("I understand this cannot be undone."), which is
the app's own label and has to match. For `20\d\d`: one, the file's `version`
(`2026-09-22-merged-h4`), which is metadata the harness logs and does not show Jev.

Where an author had to reword a "not editable" statement, the new text says only what
is observed (where the value is shown), not a guessed reason.

### Fourth round: acting as a named person (2026-09-22)

Runs showed that a request phrased "As <person>, do X" went to the right record as the
default user, found no action button there (it belongs to another role) and stopped. A
request that said "switch to <person>" worked. Which person holds which role was visible
only inside the closed account menu. Changes, all in the generators:

- **New global fact, People and roles** (`PEOPLE` in `tools/portfolio-global/build.py`,
  second of the five `global_facts_js`). It reads the tenant's active users from
  `adit.tenant.v1` at run time (no names in the atlas) and marks who is signed in:
  `People and roles (Switch user in the account menu signs in as any of them, to act as that
  person or with that role): <name>, <title> (<role code>), signed in now; <name>, <title>
  (<role code>); …`. The active users are exactly the account menu's Switch user list.
- **Positive routing on role-gated text.** The account-menu button, the account-menu
  overlay, its Switch user entries and every fact or `not_here` that says a button belongs
  to another role (project header actions and Lodge renewal, approval decision buttons and
  queues, drilling and assay record actions and Submit dispatch, programme header actions,
  admin access) now say that acting as another person or with another role is done by
  switching user in the account menu, and point to People and roles. The earlier wording
  ("the signed-in user can be changed from the account menu") said where, not when.
- The portfolio-global fragment's ledger note, stale since the third-round harness fix,
  now says the reader gives each ledger link its own line's kind (the merged atlas keeps
  harness2's per-route ledger entries either way).
- The fourth-round harness adds PRESS_ENTER (see `../harness/README.md`); the search box
  entry's "Pressing Enter opens the Search results page" now has an operation behind it.
- Whole-app self-check after this round (`tools/selfcheck.py`, 1700×900, fourth-round
  harness): 5158 / 5158 annotated over 114 states, 0 flags, 36 of 593 entries unmatched (as
  before).

## Learned lessons (2026-09-26)

`learned/` holds lessons proposed by `../tools/learn.py` from a failed run: `pending/`,
`accepted/` (applied last by `merge.py`, which then versions the atlas `…+learned-N`),
`rejected/` and `archive/`. The one accepted file holds three lessons from the failed E9
run (the Resources landing page, the All estimates link and the top-bar Projects link);
`archive/` holds an earlier proposal for the same failure, set aside.

## Conflicts found and fixed in the live self-checks

- The batch Reject dialog ("Reject LAB-…") also activated the approval Reject overlay. The
  approval overlay is now `aria-label^="Reject WF-"`.
- The Reset tenant overlay was scoped to the `#/admin` nav link being current, so it
  missed on `#/admin/system`. It now matches on the dialog's own aria-label.
- In the Save-scenario and Reject-batch dialogs the Name and Reason field entries are keyed
  by `role: textbox` too, so no button can take them.
- The Portfolio ledger, search, notification and approval-head entries described above.

## Coverage (whole-app self-check, 2026-09-22, upgraded harness; rerun after the third round: 5158 / 5158 at 1700×900, 0 flags)

`../tools/selfcheck.py` runs the harness's own `snapshot.js` and `atlas.py` in headless
Chromium. At the agent's window, `JEV_VIEWPORT=1700x900` (the default), it scrolls each
state top to bottom and pools what every position offers; `ADIT_TALL=1` uses one
1700×2400 window instead. It covers 114 states: every route, list filters, record pages,
all 25 overlays opened (the user is switched when a role is needed), page action buttons
as a user who is offered them, the tray and account menu over other pages, toasts and a
typed comment. Each state starts in a fresh context with `adit.session.v1` and
`adit.tenant.v1` cleared. With a dialog open, only the elements not covered by it count.

| Area | States | Pages hit | Annotated / offered, 1700×900 | 1700×2400 |
|---|---|---|---|---|
| portfolio-global | 20 | 13 | 941 / 941 | 941 / 941 |
| projects | 17 | 11 | 955 / 955 | 957 / 957 |
| programmes | 19 | 11 | 850 / 850 | 850 / 850 |
| drilling-assays | 17 | 8 | 1219 / 1219 | 1219 / 1219 |
| resources-optimiser | 17 | 10 | 520 / 520 | 548 / 548 |
| approvals | 9 | 2 | 326 / 326 | 326 / 326 |
| admin | 15 | 8 | 347 / 347 | 347 / 347 |
| **All** | 114 | 63 | **5158 / 5158 (100%)** | **5188 / 5188 (100%)** |

**Flags: 0** at both sizes. The check flags an entry from an area that owns neither the
page nor an open overlay; a dialog entry outside a dialog, or a page entry inside one; a
non-chrome note on a top-bar element; a button that took a form field's row-label note;
and a footer, breadcrumb or top-bar entry on an element outside that landmark. Beyond the
flags, every link's description was checked against where it actually leads (an entry that
says it opens a project, programme, approval, batch or estimate must match that route):
no mismatches.

Before this round, the same check against the upgraded harness gave 97.5% annotated and
missed wrong descriptions: the ledger entry above described every ledger item as an
overdue approval, and 45 of the 72 controls on the search results page went bare, because
a result's row label now carries more than its kind.

36 of the 593 entries matched nothing in these states. Each depends on data or a role the
states did not produce (ledger programmes past variance; search kinds hole, batch, sample
and estimate; the Resume radio; page buttons offered only to another role, and the like),
or is a fallback now shadowed by a more specific entry (the generic `^PRJ-\d{4}$` id link).

## Open issues

- The optimiser and Users tables still scroll sideways at 1700 px; the reader offers their
  far-right buttons with `offscreen_x` and the executor scrolls to them.
- The stage-gate dialog survives a route change, a quirk the projects author observed.
- The New estimate form's tonnes and grade appear twice: as native fields (now told apart
  by section) and as the kept virtual controls. Dropping the virtual set is possible now
  that `section` reaches Jev, but it was out of this round's scope.

## Regenerate

```sh
# 1. (optional) rebuild a fragment from its generator
python3 jev-atlas/tools/<area>/build.py        # programmes: tools/programmes/gen.py
#    ADIT_PARTS_DIR=/some/dir writes it elsewhere; every generator reproduces parts/ byte for byte
# 2. merge (applies harness2.py); prints counts, the second-round report and the new sha256 (update this README)
python3 jev-atlas/tools/merge.py
# 3. whole-app self-check (about 10 minutes, headless, public site), at the agent's window and tall
uv run --with playwright python jev-atlas/tools/selfcheck.py                 # JEV_VIEWPORT=1700x900 by default
ADIT_TALL=1 uv run --with playwright python jev-atlas/tools/selfcheck.py     # --only tag1,tag2   -v
```

`tools/<area>/` also holds each area author's own self-check (`check.py`, `selfcheck.py` or
`snap.py` with `scenarios.py`, and `vtest.py` for the virtual controls). They were written
for the first-round harness and atlas fragments; the whole-app check above is the one kept
current. All of them read the harness from `$JEV_CLONE` (default
`jev-atlas/vendor/jev-ultrafast`).

# Projects area: atlas fragment notes

Fragment: `projects.json` (14 page entries: 11 URL pages + 3 overlays, 194 control entries).
Manual mirror: `../../manual/projects.md` (section 4 "Projects", fetched 2026-09-22 from `#/manual/projects`).
Author: blind (never read jev-atlas/goals, the runs, the experiment notes or the log).
Generator and self-check scripts: `../../tools/projects/build.py`, `check.py`.
The fragment is generated. Edit `build.py` and rerun it; do not hand-edit the JSON.

## Coverage

URL pages (all matched with `url_regex`, mutually exclusive):

| id | route |
|---|---|
| projects-register | `#/projects`, including `?status=`, `?commodity=`, `?stage=` cuts |
| projects-new | `#/projects/new` |
| project-overview | `#/projects/:id` (excludes `new`), including the "Project not found" state |
| project-tenure / -programmes / -drilling / -assays / -resource / -budget / -approvals / -activity | `#/projects/:id/:tab` |

Overlays (native `<dialog open>`, matched by `selector`):

| id | selector |
|---|---|
| project-edit-dialog | `dialog[open][aria-label^="Edit PRJ-"]` |
| project-stage-gate-dialog | `dialog[open][aria-label^="Stage-gate decision · "]` |
| tenement-renewal-dialog | `dialog[open][aria-label="Lodge a renewal"]` |

Also covered: the Projects left panel (`nav.l2`), the header actions (Watch/Watching, Edit, Stage-gate decision), the tab strip, the comments panel (a plain textarea; @mention is typed text, with no suggestion list in the DOM), sort buttons, table pagers, record-id links, record-name links, "open in X" cross-links, New programme (Project Geologist only), Lodge renewal (Tenure & Permitting Officer only), "Values behind this chart", and the provenance ("authority") button. The Budget tab has no forms. The Budget and Activity tabs are read-only in every role I checked (EXM, PGEO, FIN, TEN).

I explored as EXM (the default user), PGEO, FIN and TEN by setting `currentUserId` in `adit.session.v1` in my own headless context. States checked: active, on-hold (Resume option), final stage (hand-over wording), closed (no Edit), no estimate, QAQC-hold open items, the >50-row pager, and invalid submits.

## Self-check (headless chromium, harness `snapshot.js` and `atlas.py` loaded as-is)

- 32 scenarios, **1510/1510 visible non-header interactive elements annotated (100%)**. Header/footer/toasts were excluded because another agent owns them. As in `model.annotate`, the "Open X" click companion of a fill field inherits its node's note.
- 189/194 entries matched at least once. The 5 that never matched are the First/Previous/Next/Last pagers on the programmes, assays, budget, approvals and activity tabs; the pager only appears above 50 rows. The drilling pager matched.
- Overlays tested closed / open / closed again: all 3 passed. Escape closes all three.
- All facts_js run live, and none of them throws. Facts that return only null in some states are conditional, not dead.
- `virtual_controls_js` (Next gate date in the Edit dialog) was checked on a freshly loaded page: `set('2027-03-01')` returned true, the form fact showed the new value, Save persisted it (header "gate 2027-03-01", toast "Project saved"). The edits were made in a throwaway headless context, not the shared browser.
- Leak grep (the five forbidden vendor/product terms from the brief, case-insensitive) on the JSON, this file and the manual gave 0 hits. Authored text (excluding selectors and JS) contains no record names or ids, years, currencies or amounts.

## Match-key decisions (read before merging)

1. **No stable hooks exist**: no ids, no `data-testid`, no `data-track-id`, and no custom elements (so no `ancestor`). The only `data-*` is React Router's `data-discover`. Every key is `text` / `text_regex` / `role` / `row_label` / `page`.
2. **`href` is useless in this app.** `snapshot.js`'s `hrefPath` keeps pathname+search and drops the hash, so every hash-route link reads `/mockent/adit/`. (Format issue below.)
3. **Counts in labels vary** ("Tenure 3", "All active 12"), so these use `text_regex` with `\d+`. Labels contain doubled spaces ("all  4", "Batch  LAB-…", "Place on hold at  Drilling"), so the regexes use `\s+`.
4. **Generic record-name link entry** (`RECORD_LINK` regex, weight 4 = page+role+text_regex) on the register, overview, programmes, drilling, assays, budget and approvals pages. Record names cannot be keyed otherwise. Its negative lookaheads exclude the top-nav names (Portfolio, Projects, Programmes, Drilling, Assays, Resources, Approvals (N awaiting you), Optimiser, Admin, ADIT home, User Manual), the tab names, this area's fixed links and id-shaped codes. **Merger: if the header agent's entries are keyed on text alone (weight 2), my lookahead is what keeps this entry off them. Re-check it if header labels change.**
5. **Left-panel entries** are page-less `{row_label, role, text_regex}` (weight 5), so they outrank the generic record-link entry on every Projects page. The row_label comes from the `.sec` group heading ("Projects", "By commodity", "By stage"). If another section's left panel reuses those group names, the regexes (`^All active \d+$` etc.) still keep them apart. The "By commodity" and "By stage" entries match any `name N` link in those groups.
6. **Breadcrumb "Projects"** cannot be told apart from the top-nav "Projects" link by any key field: same text, role and href, and no row_label. My entry is page-scoped (detail pages and new) and its description is true of both. **Merger: if the header agent also keys `{text:"Projects"}`, one of the two descriptions wins on my pages by weight or file order. Make them agree.**
7. The **provenance button** (`class="authority"`, text starting "read from" or "computed by") is a shared component. My entry is page-less and generic (`{role:"button", text_regex:"^(read from|computed by) "}`). **Merger: dedupe against other areas.**
8. Sort buttons (`^Sort by `) and pagers are page-scoped per table page, so they don't collide with other areas' identical shared-table buttons. The Activity and Resource tables have no sortable columns, so they have no sort entry.
9. Dialog controls are keyed `{page:<overlay id>, text…}`. The Close cross has the label "Close dialog" in all three dialogs.
10. The Edit-dialog overlay selector uses the `PRJ-` auto-number prefix (`aria-label^="Edit PRJ-"`). It is a number format, not a record, but if the tenant's auto-numbering rule changes, the selector breaks.

## Top-level `selectors`

The fragment carries `"selectors": {"dialog": ["dialog[open]"]}`. **Every ADIT dialog is a native `<dialog class="dlg" aria-label=… open>` opened with `showModal()`.** It has no `role="dialog"` and no `aria-modal`, so without this entry the harness's defaults see no dialog at all (`in_dialog` is never set). The other areas will need the same entry; the merger should keep one copy.

## Facts (what they report)

- Every project page reports: project in view (name, id, commodity, jurisdiction, status, stage, next gate); open tab; which header actions are shown to the signed-in user, with any missing ones named; "Signed in as <name>, <title>", read from `adit.session.v1` plus the users in `adit.tenant.v1` (read-only; permission-gated buttons depend on it); and the toast message shown.
- The register reports: count and active cut, left-panel selection, Find text, and sort.
- Each tab reports the table rows shown, the sort, and the pager state. Tenure also lists each tenement's status and expiry, and whether Lodge renewal is offered.
- Resource reports the estimate shown, or the "no estimate" notice. Overview reports open items and the comment count, plus any draft comment typed but not posted.
- Dialogs: an Edit form-state fact (every field as `label = value`); a stage-gate fact (decision selected, reasoning length against the 20-character minimum, error shown); a Lodge fact (expiry, workflow, expenditure, below-commitment warning); and a New project form fact with each field's validation error.
- **Duplication risk:** the "Signed in as" and "Message shown" (toast) facts may also be written by the header agent. Keep one copy.

## Doubts and app quirks

- **The stage-gate dialog stays open across route changes.** It was opened on one project, the page was navigated to another, and the dialog was still open with the new project's name. The React component instance survives. The overlay still matches correctly.
- "Stage-gate decision" is both a pipeline stage (a left-panel filter link, "Stage-gate decision N") and the header button. The descriptions separate them explicitly.
- The closed project still shows the Stage-gate decision button (the app does not hide it).
- `New project` is not permission-gated in the UI, although the manual says it needs `project.write`. The descriptions don't claim either way.
- `Post comment` is disabled (so not offered) until the box has text.
- The Resume radio only appears for on-hold projects, and Place on hold only for projects not on hold. Both are covered.

## Format / harness issues for the owner (not edited)

1. **`hrefPath` in `snapshot.js` drops `location.hash`**, so `href`/`href_contains` cannot tell routes apart in a hash-routed SPA. Suggest including the hash (or adding a `hash` field).
2. **`input[type=date]` gets no role** in `snapshot.js`'s `role()`, so date fields are never offered. I worked around it with a `virtual_controls_js` for Next gate. A harness fix (date/time/month → textbox) would be better.
3. **The `dialog_title` lookup is hard-coded** to `.k-window-title` / `[role=dialog] h*` / `[aria-modal] h*`. It ignores the atlas's `selectors.dialog`, so native `<dialog>` titles are always empty. My overlays therefore use `selector`, not `dialog_title`.
4. **`row_label` leaks across a page.** On the Overview, every element in the header and tabs gets `row_label = "Add a comment"`, because the walk climbs up to a container whose only `<label>` is the comment box. I did not key on row_label for those elements. Radios in the stage-gate fieldset also borrow a sibling radio's label as their row_label.
5. Key regex support covers only `id`, `text` and `href`. A `row_label_regex` would have let me key the pager on its footer label ("N rows · showing …").

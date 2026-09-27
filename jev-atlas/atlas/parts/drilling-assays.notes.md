# drilling-assays atlas fragment: notes for the merger

Fragment: `drilling-assays.json`. It has 13 page entries (8 URL pages and 5 dialog overlays) and 114 control entries. Written 2026-09-22 by a blind author: this author did not read goals, runs, the ADIT experiments or the log.
Manual mirror: `jev-atlas/manual/drilling.md`, `jev-atlas/manual/assays.md` (sections 6 and 7, fetched 2026-09-22 from `#/manual/<slug>`).
Tools (now in `../../tools/drilling-assays/`): `build.py` generates the JSON, and `selfcheck.py [viewport-height]` checks it live using the harness's own `snapshot.js` and `atlas.py`.

## Coverage

| Route | Page id | Explored as |
|---|---|---|
| `#/drilling` (incl. `?status=drilling|planned|logged|abandoned`, page 2) | `drilling-list` | Exploration Manager (default user) |
| `#/drilling/intercepts` | `drilling-intercepts` | EXM |
| `#/drilling/:id` (holes at assayed, drilling, planned, logged, abandoned) | `drilling-hole` | EXM, Database Geologist |
| `#/assays` (incl. `?status=lab|received|qaqc-hold|accepted`, `?lab=`, `?project=`) | `assays-batches` | EXM |
| `#/assays/:id` (batches at submitted, received, qaqc-hold, accepted) | `assays-batch` | EXM, DBGEO |
| `#/assays/new` | `assays-new` | EXM, DBGEO; one test dispatch submitted and then discarded (fresh browser context) |
| `#/assays/qaqc` | `assays-qaqc` | EXM |
| `#/assays/samples` | `assays-samples` | EXM |
| Update hole dialog | `update-hole-dialog` (overlay) | DBGEO; one Save tested |
| Import results dialog | `import-results-dialog` | DBGEO |
| Accept batch dialog (with and without the failure-review tick box) | `accept-batch-dialog` | DBGEO; one Accept tested |
| Place on hold dialog | `hold-batch-dialog` | DBGEO |
| Reject batch dialog | `reject-batch-dialog` | DBGEO |

Every action ran in a fresh Playwright context, so localStorage was reset each time. The shared browser was not touched.

## Self-check results (live, 2026-09-22)

- Page match is correct in all 34 scenarios. Each of the 6 overlay tests passed: the dialog was closed, then open (only its own overlay active), then closed again.
- Viewport 1440x3000: 2881 of 2904 visible interactive elements in the area's own content (`main`, dialogs, left column) are annotated, which is 99.2%. Counting the global header, 2902 of 3399 (85.4%) are annotated. The header belongs to the nav agent.
- Viewport 1440x900: 99.1% of area elements are annotated.
- 112 of 114 entries match at least one live element. Two had no hits in the scenarios run: `assays-samples` Clear (it did not appear for a typed filter) and `assays-batch` Post comment (it is disabled until text is typed; the same component matched on the hole page).
- The only unannotated area element is the footer link "User Manual" inside `main`, a global footer that the nav agent should key.
- Every `facts_js` returned a non-null value in some scenario except `LEFT_FACT`, which the build defines but no page uses.
- Virtual controls were checked against the app's own state. Setting the dispatch hole to yes enabled Submit dispatch, and setting it to no disabled it again. After the Update hole Completed date was set and Saved, the page showed the new date.
- A grep of the fragment and both manual files for the forbidden-vendor token list in the brief found 0 hits. A grep for record ids, project and laboratory names and dates found none apart from `version`.

## Match-key decisions

- **No stable ids.** There is no `data-testid`, `data-track-id`, `id` or custom element (`ancestor` is always null). `data-key` and `data-status` sit on rows and chips, but the harness does not extract them. The keys available are `text`/`text_regex`, `role`, `row_label` and `page`.
- **`href` is useless on this app (format/harness issue).** `snapshot.js` reports `href` as pathname+search, and this SPA is hash-routed, so every link reports `/mockent/adit/`. `href_contains` cannot tell links apart. Suggestion for the harness: include `location.hash` in `hrefPath`.
- Record links are keyed on the **shape** of the id, never on a value. Holes use `^[A-Z]{2}-(DDH|RC|AC|Sonic)-\d{3}$`, batches `^LAB-\d{2}-\d{4,6}$` and programmes `^PRG-\d{4}-\d{3}$`. The chips on record pages are keyed `^batch ` / `^hole `.
- **Free-name links** (project, programme and laboratory names) have no key at all. They use a page-scoped `NAME_LINK_RE`, a negative-lookahead regex that excludes every fixed label on these pages, the global-nav labels and the id shapes. Its weight is 4 (page+role+text_regex). If the nav agent adds header or footer link texts that are not in the exclusion list (currently ADIT home, Portfolio, Projects, Programmes, Drilling, Assays, Resources, Approvals, Optimiser, Admin, User Manual, Skip to content, Open), this entry would take them over on my 8 pages. **Merger: check the final nav link texts against this list.**
- The left-column status links are keyed `{row_label: Drillholes|Results|Batches|Quality, text_regex: ^Label\b}` because the counts in their labels change.
- Filters are keyed `{page, row_label}`.
- Sort headers, pagers, "Values behind this chart", comments and "read from the …" provenance buttons are **shared components** (the comments form and pager likely exist in other areas). I page-scoped them per page instead of adding global generic keys, to avoid clashing with other fragments. The merger may collapse them into generic entries.
- Breadcrumbs "Drilling" and "Assays" have the same text, role and href as the nav items. My `{page, text, role}` entries (weight 4) therefore also describe the nav item on `drilling-hole`, `assays-batch` and `assays-new`. The descriptions say both open the same list.
- Dialog-scoped control entries are placed **first** in the file. The hold dialog's primary button ("Place on hold") has the same text as the page button that opens it, weights tie at 4, and a tie goes to the first entry in the file. **Merger: keep overlay-scoped controls ahead of page-scoped ones.**

## Things the merger must know

1. **Dialogs are native `<dialog open class="dlg" aria-label="…">`**, not `role=dialog`/`aria-modal`. The fragment adds `"selectors": {"dialog": ["dialog[open]"]}`, which is app-wide and should go in the merged atlas once. The harness's `dialog_title` reader only looks at `.k-window-title` / `[role=dialog] h1,h2` / `[aria-modal] …`, so `dialog_title` is always empty on ADIT. The overlays therefore match by `selector` and the harness reports the overlay `name` as the dialog. *Format/harness suggestion:* add `dialog[open] h2` to the dialog-title readers, or let the atlas append title selectors. Other areas' dialogs (Update RIG…, Reject approval…) use the same component. My overlay selectors are written so they do not catch those: `:has(input[name=depth])`, `:has(textarea[placeholder^="Which checks failed"])`, `aria-label^="Accept "`, `$=" on QAQC hold"` and `^="Import results for "`.
2. **Controls the harness cannot see**, which is why virtual controls are used:
   - The New dispatch hole pills are `<label><input type=checkbox>` with the input at opacity 0 and 1x1 px. `checkVisibility({checkOpacity})` drops them, and `<label>` is not in the harness's selector list, so without the atlas the harness can never include a hole. `assays-new.virtual_controls_js` offers one TYPE_TEXT target per hole (yes/no). *Harness suggestion:* treat a `label` wrapping a hidden checkbox as the clickable control.
   - The Update hole **Completed** field is `input type=date`. `snapshot.js`'s `role()` returns null for `date`, so it is never offered. `update-hole-dialog.virtual_controls_js` sets it through the native value setter plus input/change events. *Harness suggestion:* map `date`/`time`/`datetime-local` to `textbox`.
3. **Permissions shape the pages.** The default user (Exploration Manager) sees no Update hole, no batch actions, and a disabled Submit dispatch. The Database Geologist sees all of them; the Project Geologist sees Update hole only. The user switcher is in the account menu, which the nav agent owns. `ACTIONS_FACT` states which record actions are offered, so an absent button reads as a permission or status matter.
4. **Toasts.** Confirmations appear in `.toasts > .toast`, which carries an "Open" link, not a URL change. For example, a dispatch stays on `#/assays/new`. I added `TOAST_FACT` to my pages. If the nav agent keys toasts globally, drop one of the two. The toast's "Open" link is not keyed here.
5. **Dangerous or irreversible controls**, per playbook §8: Save (Update hole), Import, Accept, Place on hold, Reject batch and Submit dispatch all write tenant state. Everything lives in localStorage, so clearing `adit.tenant.v1` resets it.
6. No `options` are listed for Project or Laboratory selects (tenant data). Hole type, sample type and hole status options are fixed product vocabulary and are listed.

## Doubts

- `NAME_LINK_RE` is brittle by construction (see above). A hash-aware `href` in the harness would replace it with `href_contains: "#/projects/"`.
- Page 2+ of the batch samples table shows 100 rows, while other tables show 50. The pager text avoids giving a number.
- The "read from the …" provenance button toggles a method panel only when the app supplies one. On every record I saw, it did nothing.

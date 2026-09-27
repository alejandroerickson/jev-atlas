# resources-optimiser fragment: notes for the merger

Fragment: `resources-optimiser.json` (14 page entries, 10 URL pages + 4 dialog overlays; 78 control entries; 1 `virtual_controls_js`; 11 `facts_js`).
Written 2026-09-22 by a blind author (I did not read goals, runs, adit experiments or the log). Built by a generator script
(`../../tools/resources-optimiser/build.py`, with `snap.py`, `scenarios.py` and `vtest.py` for the self-check).
Manual mirror: `jev-atlas/manual/resources.md`, `jev-atlas/manual/optimiser.md` (sections 8 and 10, fetched 2026-09-22; no credentials in the URL).

## Coverage

URL pages (all matched by `url_regex` on the full URL, hash included):

| id | route | surveyed as |
|---|---|---|
| `resources-portfolio` | `#/resources` | EXM |
| `resources-estimates` | `#/resources/estimates`, also `?status=review` (the "In review" view) | EXM, PGEO (New estimate button) |
| `resources-estimate-new` | `#/resources/estimates/new` (a single form, not a multi-step wizard) | PGEO; also before and after Save draft |
| `resources-estimate` | `#/resources/estimates/:id` | released (EXM), draft (PGEO, with Submit/Change status), unknown id |
| `resources-forecast`, `resources-price-deck`, `resources-valuation` | as named | EXM; price deck also as SYS (Edit deck) |
| `optimiser` | `#/optimiser` | EXM; scrolled; with one target excluded (Restore button) |
| `optimiser-scenarios` | `#/optimiser/scenarios` | empty, and with one saved scenario |
| `optimiser-targets` | `#/optimiser/targets` | read-only list; it is not a scenario builder |

Overlays (native `<dialog>` opened with `showModal`, matched by `match.selector` on `dialog[open][aria-label…]`): Submit for release,
Change status, Edit the price deck, Save this scenario. Each was tested closed / open / closed again (closed with Cancel, Escape, or the
cross): zero, one, zero. Also covered inline: "show method" expanders, "Values behind this chart" details, the comment box, the saved
notice after Save draft, the Restore N excluded button, toasts (left to the global owner, see below).

Users switched by writing `adit.session.v1.currentUserId` in a throwaway headless context: EXM `u-mokonkwo` (default), PGEO
`u-twierzbicki` (resource.write), SYS `u-abarrientos` (admin.write). Permission gating read in the bundle: New estimate, Submit for release
and Change status need `resource.write`; Edit deck needs `admin.write`; Save scenario needs `optimiser.run`.

## Self-check (harness's own `snapshot.js` + `atlas.py` matching, headless Chromium, 1440×900)

30 states. Excluding global chrome (top bar, account menu, notification panel, footer "User Manual", toasts): **530/530 area elements
annotated (100%)**; with the global overlays counted, 530/551 (96.2%). Every match was checked by eye for the *right* entry (sub-nav vs
page button of the same name, dialog Cancel vs page Cancel, etc.). No top-bar element is matched by this fragment.
All `facts_js` run live and return non-null on their page; `virtual_controls_js` `set` verified on a freshly loaded page: after
setting the four block fields, Save draft created an estimate holding exactly those values (the app's own state, read back from
localStorage), in a throwaway context. Grep for the five banned tokens from the brief: 0 hits in the fragment, this file and both manual files.
Grep of descriptions for years, currencies, amounts, record ids, project/person/commodity names: 0 hits.

## Match-key decisions

- **No stable hooks exist**: no `data-track-id`, no `data-testid`, almost no ids, and no hyphenated custom elements (React), so
  `ancestor` is always null. Keys are `text` / `text_regex` / `row_label` / `role`, almost always scoped by `page`.
- **`href` is useless for this app**: the harness keeps `pathname + search`, so every hash link reads `/mockent/adit/`. Record links are
  therefore keyed by *shape* of their text: estimate ids `^RES-\d{4}-\d{2}$`, and project-name links by a regex (1 to 4 capitalised
  words) with a negative lookahead excluding the fixed navigation labels of the same shape. The regex is page-scoped; it names no
  project. If the merged atlas adds pages where a short capitalised link is *not* a project, keep those entries scoped as they are.
- Section sub-nav (left column) is keyed `{row_label: <group heading>, text|text_regex, role: link}` (weight 5), so it beats the
  page-level button of the same name (Portfolio resources' "Price deck" button, Optimiser's "Saved scenarios" button). Counts in the
  labels ("All estimates 8") are matched with `( \d+)?`.
- Labels with odd whitespace (`Budget,  USD`, `Cut-off,  g/t   Au`) are matched by prefix regex; the currency and grade units are
  never written into a key or description.
- Shared components keyed per page: "Values behind this chart", the "computed by ADIT … show/hide method" button, "Sort by …" headers,
  the comments box / Post comment, the dialog "Close dialog" cross. Other areas have the same components; they should key them on
  their own pages the same way.

## Things the merger must know

1. **Top-level `selectors`: `{"dialog": ["dialog[open]"]}`.** ADIT's dialogs are native `<dialog>` with no `role` attribute, so the
   harness defaults (`[role="dialog"]`, `[aria-modal="true"]`) miss them and `in_dialog` stays false. Merge (dedupe) this into the
   single atlas-level `selectors`.
2. `dialog_title` is always empty for these dialogs (snapshot.js looks for `[role="dialog"] h2`); the overlay `name` is what the harness
   reports instead. The notification panel *does* have `role=dialog` and reports "Notifications".
3. `leads_to` values that point outside this area are plain text ("project page (Projects area)", "approval (Approvals area)");
   replace them with the other fragments' page ids if wanted.
4. Page-order: within this fragment the specific routes come before `#/resources` and `#/optimiser`; the regexes are anchored with `$`,
   so order across fragments does not matter for these ids.
5. Toast "Open" / "Dismiss" and the footer "User Manual" link appear on these pages but belong to global chrome; not described here.

## Dangerous or tenant-wide controls (described plainly, not hidden)

- **Save deck** (Edit the price deck): changes every valuation in the tenant and is audited.
- **Lock / Locked** on the optimiser: stored on the target for everyone (`target.lock` into the world), also visible on Candidate
  targets. Exclude is per run only.
- **Delete** on Saved scenarios: immediate, no confirmation.
- **Submit** (for release): creates an approval workflow; **Save draft** creates an estimate; **Save** (status) changes the record.
  None of these were clicked except Save draft / Save scenario in throwaway contexts (discarded).

## Gaps and format issues

- **Identical row buttons**: all 14 optimiser rows have a "Lock" and an "Exclude" button with the same name and no row identity
  (`row_label` is the row's selection status, e.g. "selected"). The atlas cannot say which is which per element. Workaround: a
  `facts_js` lists the rows top to bottom and says the buttons follow that order (about 1,100 characters, longer than I would like).
  Suggested format/harness addition: a per-element row context (e.g. the row's `data-key` or first identifying cell) as a key/label field,
  or click-capable virtual controls.
- **Two fields with the same label** on the new-estimate form ("Tonnes, Mt" and "Grade, …" under both Indicated and Inferred; the
  fieldset legend is not in `row_label`). Handled with `virtual_controls_js` offering "Indicated tonnes, Mt", "Inferred grade, …" etc.;
  the real fields remain offered with a description saying the first is Indicated and the second Inferred. A `legend`-aware
  `row_label` in the harness would make the virtual controls unnecessary.
- `href`/`href_contains` cannot see hash routes (see above). A `hash` element field would let record links be keyed by route kind.
- Save draft silently does nothing when no tonnes value is above zero; the form fact says so, and Save draft's `not_for`.
- SVG chart bars on Portfolio resources are `<a>` elements in SVG (lowercase tagName), so the harness never offers them; nothing to key.
- The estimate page's author and reviewer are only visible after "show method"; noted in the page text, not surfaced as a fact.
- Descriptions are from the manual plus observation; the manual says nothing about the optimiser's Restore button, the saved notice,
  or that Lock is global — those come from the code and a live run.

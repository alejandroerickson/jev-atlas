# Administration area — atlas fragment notes (area-slug `admin`)

Fragment: `admin.json` (12 pages: 8 URL pages + 4 overlays; 69 controls). Written 2026-09-22 by a
blind author (no goals, runs, adit experiments or log read). Wording from the mirrored manual
section `jev-atlas/manual/administration.md` (fetched 2026-09-22 from the in-app manual,
`#/manual/administration`) and checked against the live screens.

## Coverage

URL pages (all surveyed as System Administrator and as the default Exploration Manager; the
Project Geologist view was also opened):

| id | route | controls described |
|---|---|---|
| admin-settings | `#/admin` (regex `#/admin/?(\?.*)?$`) | Reset demonstration tenant, 12 fields, Save settings |
| admin-price-deck | `#/admin/price-deck` | price and cut-off fields (2 generic entries), Save, View in Resources |
| admin-qaqc | `#/admin/qaqc` | 4 tolerance fields, Save tolerances |
| admin-workflows | `#/admin/workflows` | workflow-name buttons (1 generic entry) |
| admin-reference | `#/admin/reference` | none exist (read-only tables) |
| admin-users | `#/admin/users` | Add user, row Edit (generic), column sort buttons (generic) |
| admin-roles | `#/admin/roles` | none exist (read-only matrix and role cards) |
| admin-audit | `#/admin/audit` | Find, User filter, sort buttons, pager First/Previous/Next/Last |

Overlays (native `<dialog class="dlg">` opened modally; each selector tested closed / open /
closed-after-Escape, all passed):

| id | opened by | selector idea |
|---|---|---|
| admin-reset-tenant-dialog | Reset demonstration tenant | `aria-label="Reset the demonstration tenant"`, scoped to the settings page |
| admin-workflow-dialog | a workflow name | any open `dialog.dlg` while the Workflows sub-nav link is current |
| admin-add-user-dialog | Add user | `aria-label="Add a user"`, scoped to Users |
| admin-edit-user-dialog | row Edit | `aria-label^="Edit "`, scoped to Users (the label carries the user's name, so it is a prefix match) |

Overlay selectors are all scoped with `.shell:has(nav.l2 a[aria-current="page"][href="#/admin/..."])`
so they cannot fire on another area's dialog with the same shape.

Also covered: the Administration "In this section" list (8 links, keyed on the harness-derived
`row_label` = group heading `System` / `Access`, plus the link text; count suffixes such as
`Workflows 8` handled by `text_regex`).

## Self-check (live, headless Chrome, harness `snapshot.js` + `atlas.py` matcher)

`../../tools/admin/selfcheck.py`: every admin route and every overlay, scrolled top
to bottom, as SYS and EXM. Every control entry matched at least one live element. Of the visible
interactive elements inside `main`, `nav.l2` or a `dialog`, 344 of 367 (93.7%) are annotated at
1120x780, and 93.9% at 1700x900. The unannotated remainder is only the footer "User Manual" link
(inside `main`, but a footer shared by every page: left for the global/header agent).

facts_js were all run live: access level (none / read-only / can change), unsaved changes
(compares the form with the saved settings in `localStorage['adit.tenant.v1'].world.settings`,
read-only) plus invalid fields, latest toast message, dialog form state (label = value, required,
invalid with the browser's validation message), open workflow name, audit view (count, filters,
page, sort), users sort and "Edit buttons are off the right edge". None always returns null on
the page it is attached to (reference and roles carry none).

Grep of both outputs for the forbidden vendor and product terms: zero hits. Grep for tenant
record tokens (people's names, commodity names, prices, record ids): zero hits.

## Things the merger must know

1. **`selectors.dialog: ["dialog[open]"]`** is in this fragment. ADIT's dialogs are native
   `<dialog>` elements with no `role=dialog`/`aria-modal`, so without it the harness never sets
   `in_dialog`. This is app-wide; keep one copy in the merged atlas.
2. **`href` keys are useless in ADIT.** The harness extracts `href` as path + query only, and
   every ADIT link is a hash route, so every link's `href` is `/mockent/adit/`. Links are keyed
   on text instead. (Format/harness gap: an `href` that keeps the fragment would fix it.)
3. **`dialog_title` is always empty** for ADIT dialogs: the harness's title selectors look for
   `[role=dialog] h2` / `.k-window-title`, not `dialog h2`. The overlay `name` stands in, and a
   fact names the specific workflow or user. (Harness gap; not something an atlas can fix.)
4. **The Users table is wider than a 1120 px window.** The row Edit buttons and the Status /
   Last sign-in sort buttons sit in a horizontally scrolling `.tbl-wrap` at x ≈ 1580, so the
   harness (which only scrolls vertically and drops elements beyond `innerWidth`) cannot offer
   them. Recommend `JEV_VIEWPORT=1700x900` for ADIT, or horizontal scrolling in the harness.
   A fact reports the count of Edit buttons off-screen.
5. **Role gating.** The default signed-in user (Exploration Manager) has admin.read only: every
   admin field is disabled and Save / Add user / Edit are not rendered, so they are not offered.
   Only the System Administrator can change anything. Roles without admin.read see only a notice.
   Page `what` texts and an access fact say so; switching the signed-in user is the account menu
   (header agent's area).
6. **Tenant-wide flag.** Every control that changes settings for everyone starts its `what` with
   `ADMINISTRATION, TENANT-WIDE:`; user-account controls start with `ADMINISTRATION:`.
7. Shared components other areas will also meet: the `.toasts` status region (with a "Dismiss"
   button, not annotated here), the "Close dialog" cross and Cancel/Save in `dialog.dlg` (keyed
   here only with `page` = my overlay ids), the `nav.l2` "In this section" list (other areas may
   use the same component; my keys include the admin group headings), and "Sort by …" header
   buttons (keyed here with `page`). The collapsed `<summary>` "In this section N" only shows at
   narrow widths; not keyed.
8. `leads_to` includes two destinations outside this area (Resources price deck, Assays) given
   as plain descriptions, not page ids; the merger may replace them with the owning agent's ids.
9. The workflow-name buttons are keyed by a regex listing the eight workflow definitions (the
   manual calls them "the eight workflows"; they are configuration, fixed per release). The key
   is not shown to the model; the description is generic.

## Doubts

- Actions taken while surveying (all in throwaway headless contexts; localStorage cleared after):
  saved system settings, the price deck, a user edit; opened and cancelled the reset dialog;
  never pressed Reset tenant.
- `Save settings` accepted a fiscal-year start of `13-45` (only the `\d\d-\d\d` pattern is
  checked); the description says it refuses values "not in MM-DD form", which is true of the
  pattern only.
- Escape closes all four dialogs (none ignores it).

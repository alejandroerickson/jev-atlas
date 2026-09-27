# Approvals fragment — notes for the merger

Fragment: `approvals.json` (5 page entries: 2 URL pages + 3 overlays; 44 controls).
Manual mirror: `../../manual/approvals.md` (section 9, fetched 2026-09-22 from the in-app manual `#/manual/approvals`; no credentials involved).
Surveyed 2026-09-22 in a private headless Chromium (Playwright). Every browser run was a fresh profile, and I also cleared localStorage between test actions, so no ADIT state persisted. Scratch scripts are in `/tmp/claude-1000/jev-atlas-approvals/`: `build.py` generates the JSON, and `check.py` is the live self-check.

## Coverage

- `#/approvals`, the queue: all four Queue views (`Awaiting me` default, `?view=pending`, `?view=mine`, `?view=decided`) and all eight By-type filters (`?view=pending&type=programme|budget-variance|stage-gate|land-access|permit|resource-release|tenement-renewal|purchase-order`). Also covered: the ticket cards (Awaiting me only, up to 4), the sortable table (8 sort buttons; Current step cannot be sorted) and the empty state. There is no pager: Decided shows all 32 rows.
- `#/approvals/:id`, the request detail. I opened at least one request of every workflow type (all 8), plus an approved, a returned and a withdrawn request. Covered: breadcrumb, head (status chip, workflow, project link, the action buttons), notice (waiting on / overdue), Request panel (Subject chip, amount, stamp panel for programme subjects), Workflow steps, Comments (textarea plus Post comment), Other requests on this project, and toasts.
- Overlays: the Approve dialog (`<dialog aria-label="Approve: <step>">`), the Return dialog (`"Return to the requester"`) and the Reject dialog (`"Reject <id>"`). Each was tested three ways (closed, open, closed again) and each selector passed. Within each dialog: the close cross, the field, Cancel, the submit button, and the error state when the reason has fewer than 10 characters.
- User switching (account menu, "Switch user"), tried as the Exploration Manager, a Project Geologist, the Finance Controller, the Tenure & Permitting Officer and the System Administrator. What I observed:
  - Awaiting me is matched **by role**, not by named person. Both Project Geologists see a QP review step that is assigned to one of them.
  - Approve, Return and Reject appear only for the current step's role.
  - Withdraw appears for the requester when the current step is not theirs. When the requester's role also owns the current step, they see Approve, Return and Reject and no Withdraw.
  - Withdraw acts immediately and shows no confirmation. The request then appears under Decided.
  - The System Administrator has an empty Awaiting me.
- I did not annotate the account menu itself. It belongs to the header agent. I only describe its effect, in the `not_here` text of both pages.

## Differences between workflow types (as they appear on screen)

The authored text is in the eight By-type link entries and in the Subject-chip entry:

| Workflow | Subject chip, and where it leads | Amount |
|---|---|---|
| Programme approval | programme → `#/programmes/:id` | yes |
| Budget variance | programme → `#/programmes/:id` | yes; the final Approve dialog adds "Approving raises the programme's approved budget by …" |
| Work permit | programme → `#/programmes/:id` | no |
| Stage-gate decision | project → `#/projects/:id` | no |
| Land access agreement | project → `#/projects/:id` | no |
| Resource estimate release | estimate → `#/resources/estimates/:id` | no |
| Tenement renewal | tenement → `#/projects/:id/tenure` | no |
| Purchase order | purchase → `#/programmes?project=…` | yes |

When the subject is a programme, the page also shows a budget, spent, dates and phase stamp. The Approve dialog's summary says either "moves to <next step> (<role>)" or "This is the final step…". No workflow has a decision field of its own: a stage-gate decision uses the same plain Approve dialog.

## Match-key decisions

- **No ids, no data-testid, no data-track-id, no custom elements** (so `ancestor` is always empty). The keys are `text`, `text_regex`, `role`, `row_label` and `page`.
- **`href` is useless in this app.** snapshot.js reports `pathname+search` and drops the hash, so every hash-route link reads as `/mockent/adit/`. No entry uses `href`/`href_contains`. This is a harness gap for hash-routed SPAs (see Format issues below).
- Left-column links carry the harness-derived row labels "Queue" and "By type", and their labels end in a live count. They are keyed `{row_label, role, text_regex "^Name( \d+)?$"}`, with **no `page`**, because the same column also appears on the detail page. If another area's left column uses a "Queue" or "By type" heading with the same link names, those entries will match there too.
- Record links are keyed on the id format (`^WF-\d{4}-\d{4}$`), one entry per page, never on a specific id. Title links are keyed on the eight workflow prefixes. Ticket cards are keyed on `·\s+due\s+\d{4}-…`: the label contains double spaces, so the regex uses `\s+`.
- The head project link has no usable key except its row label, which the harness derives from the status chip. There is one entry per status (pending, approved, returned, rejected, withdrawn). "rejected" matched nothing live because the data has no rejected request.
- **Dialog submit and Cancel buttons** are keyed `{page:<overlay>, role, text, text_regex:"^X$"}` (weight 6). The reason is that the head's Approve, Return and Reject buttons stay in the DOM, covered, while a dialog is open, and would otherwise tie with the dialog buttons (both at weight 4). Row labels cannot separate them, because the dialog buttons' row label changes when the reason field shows an error. Side effect: while a dialog is open, the covered head button of the same name shows the dialog button's description. It cannot be clicked, so I accepted this.
- `selectors.dialog: ["dialog[open]"]`: ADIT uses native `<dialog>` without `role="dialog"`, so without this the harness defaults never set `in_dialog` or count covered controls. The account menu is `role="dialog"` and is already covered by the defaults. This line belongs in the merged atlas once, as an app-wide setting.
- The toast `Dismiss` button is keyed per page (`{page, text:"Dismiss"}`). Toasts (`.toasts`, `role=status`) are an app-wide component, so the merger may replace these with one global entry.
- The sortable `table.tbl` with `th-btn` "Sort by X" buttons looks like a shared component. My sort entry is page-scoped to the queue.

## Self-check (live)

`check.py` ran snapshot.js with this fragment's selectors, then `atlas.match_page`, `probe`, `active_overlays` and `match_control` from `jev_ultrafast/atlas.py`, on 49 states. Those states were: every queue view, a filtered view, all 10 detail pages (each at the top and scrolled), the 3 dialogs (the Return and Reject dialogs also in their error state), a typed comment, 3 switched users, and the page after a withdraw.

- **Approvals-area interactive elements annotated: 920/920 (100 %).**
- All visible elements: 920/1564. The remaining 644 are the global top bar, the top nav and the footer, which belong to the header agent.
- Every control entry matched at least one live element, except `row_label: "rejected"`, which has no data to match.
- No `facts_js` expression returned null in every state. Each one was checked against the live page. The dialog fact is shared by all three overlays; the harness appends it only for the overlay that is active.

## Doubts and things the merger must know

- The overlay selectors (`dialog.dlg[open][aria-label^="Approve: "]`, `…="Return to the requester"`, `…^="Reject "`) are specific to approvals as far as I can see. If another area has a native dialog whose aria-label starts with "Approve: " or "Reject ", these overlays would activate there too. Check the other fragments.
- Page order matters. `approval-detail` (url_regex `#/approvals/[^/?#]+`) comes before `approvals-queue` (url_regex `#/approvals/?(\?.*)?$`). The two regexes do not overlap, but keep them that way if any other page uses `url_contains: "#/approvals"`.
- The claim "Withdraw asks no confirmation" is observed on one request, and so is "requester who also owns the step sees Approve, Return and Reject, not Withdraw". I did not submit Return or Reject for real (only their validation), and I did not open a rejected request (there is none). The Approve outcome was observed once, on a final step; the text for moving to the next step comes from the dialog summary.

## Format issues (for the owner of ATLAS-FORMAT.md / harness)

1. `href` loses the URL fragment, so hash-routed apps get no link keys at all. Suggest `hrefPath` keep `hash`, or add an `href_hash` field.
2. `dialog_title` is not found for a native `<dialog aria-label=…>` that has an `<h2>`, because the title selectors only look under `[role=dialog]`/`[aria-modal]`. Overlays by selector work around this. Adding `dialog[open] h2` (or the `aria-label` of `dialog[open]`) to the title probe would help.
3. There is no key field for `in_dialog` or `covered`. With one, dialog buttons could be separated from same-named buttons behind the dialog without the `text` + `text_regex` weight trick.
4. `row_label` has no regex or contains variant. That forced the five per-status entries for the head project link.

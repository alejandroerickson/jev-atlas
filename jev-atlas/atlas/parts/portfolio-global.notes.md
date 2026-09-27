# portfolio-global: notes for the merger

Fragment: `portfolio-global.json` (15 page entries: 13 URL pages and 2 overlays; 93 control entries). Written blind,
without reading goals, runs, experiments or the log. It was surveyed 2026-09-22 with a headless Chromium (Playwright)
against https://alejandroerickson.com/mockent/adit/, using the harness's own `snapshot.js` and `atlas.py` (loaded from
the harness copy), so the keys were checked against the fields the harness actually extracts. Every run
used a fresh browser context, so the localStorage changes from test actions (profile save, theme, user switch,
session sign-out) were thrown away.

Manual mirror: `jev-atlas/manual/{about-adit,getting-started,portfolio,account,reference}.md`, plain text of the
article body, each headed with its Source URL and Fetched date. No credentials are involved. The pages contain
fictional support contact details, `.example` addresses and a phone number with the 555 prefix.

## Coverage

URL pages: `portfolio` (#/portfolio, the stage board), `portfolio-commodity`, `portfolio-jurisdiction`,
`portfolio-analytics`, `portfolio-budget`, `search` (#/search?q=), `notifications`, `account-profile` (#/account),
`account-notifications`, `account-preferences`, `account-security`, `manual` (#/manual and all 12 sub-pages, one
entry, with a fact naming the open section), `not-found` (the * route).

Overlays: `notification-tray` (`#notif-tray`, the bell's drop-down) and `account-menu` (`#user-menu`). Both were
tested closed, open, then closed again, once with their own button and once with Escape. All four checks passed:
False, True, False, False.

Also covered: the toast (`.toasts .toast`, with its Dismiss button and a fact), the Values behind this chart
disclosure, the "computed by ADIT … show method" stamp, the sort headings, the Switch user list and the session
Sign out.

Not opened: nothing in my area was withheld. Session **Sign out** on the Security page produced no visible change in
the demo. Its description ("ends that other device's session") comes from the page's own purpose, not from an
observed effect.

## Self-check (live, headless, 1120 wide by 5000 tall so each page reads in a single snapshot)

Across 23 scenarios (every route, three search queries, tray open, menu open on two pages, toast, method and
disclosure open), **1194 of 1254 unique interactive elements were annotated (95.2%)**. The 60 elements left bare are
all project-*name* links in the portfolio registers: 12 per register page, on 5 scenarios. They are record data, carry
no key that avoids naming the record, and keep their bare label on purpose. Pages without registers are at 100%.

Nine entries matched nothing in these scenarios, all because the data did not produce them, not because a key was
mistyped:
- `Skip to content`: it is visible only when focused.
- The ledger kinds `Approval due`, `Tenure expiring`, `QAQC hold`, `Gate due`, `Vacancy`: see the ledger note below.
- The search kinds `hole`, `sample`, `estimate`: a hole or sample row's links may never have been the row label the
  heuristic picked, or no query surfaced that kind in a keyed cell.

Broad matches are intended: `^Sort by ` 161, `batch` search results 214, `PRJ-\d{4}` 72, Watching 56 (7 per page),
ledger 57.

Every `facts_js` returned a value on the pages it belongs to; none always returns null. Sample output:
`Signed in as <name>, <title> (role <code>)`, `Top-bar section: Portfolio`, `Unread notifications: 2; approvals
awaiting you: 3`, `Message just shown: Profile saved`, `Form fields: Open on sign-in = …; Units = Metric; …`,
`Search for "er": 27 results (project 7, programme 3, approval 12, tenement 1, user 4)`, `Manual section open: 2. Getting started`.

The forbidden-token grep from the brief (five tokens, case-insensitive) had 0 hits over the fragment, these notes and my manual files. A grep for
project names, user names, record ids and years hit only the `version` field and the fixed `Rows per page` options.

## Match-key decisions

- ADIT has **no ids, no data-testid or track ids and no custom elements** (so `ancestor` is always null). The only
  stable hooks are aria-labels, which become the harness `text`, visible text, and the harness's `row_label`. The keys
  here are therefore `text` or `text_regex` plus `role`, `page` and `row_label`.
- The top-bar section links are keyed `{text, role:"link"}` (weight 3). A breadcrumb link with the same text (for
  example "Projects" on a project page) matches the same entry and goes to the same place; only the region is wrong.
  If another area wants breadcrumbs described separately, give them `{page, text, role}` (weight 4).
- Approvals appears twice: the nav link is `^Approvals( \(.*awaiting you\))?$` and the Portfolio head button is
  `{page:portfolio, ^Approvals( \d+)?$}`.
- Left column: `{row_label:"Shape", text}` for the portfolio cuts, `{row_label:"Watching", role}` for watched
  projects, and `{row_label:"My account", text, role}` for the account pages.
- **Ties that rely on file order:** the account left-column entries sit *before* the account-menu and tray entries,
  because "Preferences" and "Notification settings" score 5 in both. With the menu open over an account page, the
  left-column link must keep its own description. **Keep this relative order when merging.**
- **Needs attention ledger:** the harness row label for every ledger link is the kind label of the ledger's *first*
  line, whichever it is, because the ledger is a CSS grid of spans. So there is one entry per possible first kind
  (`Approval overdue` observed; the others are there so a change in the data does not unkey the ledger), all with
  the same generic description.
- Search results are keyed by the Kind cell, which the harness takes as the row label (project, programme, hole,
  batch, sample, approval, estimate, tenement, user).
- Tray items are keyed by notification *title wording* (`Tenement …`, `Awaiting your …`, `… commented on …` and so
  on). These are templates, not records. A new kind outside the pattern keeps its bare label. I deliberately did not
  use a bare `{page:"notification-tray", role:"link"}`: while the tray is open it would match every link on the page.
- Switch user entries: `{page:"account-menu", role:"button", text_regex:" [A-Z]{2,6}$"}`, which relies on the
  trailing role code. Neither names nor codes are enumerated.
- URL pages use anchored `url_regex`, so `#/portfolio` does not also swallow `#/portfolio/budget` and the order of
  pages does not matter. `not-found` is a negative lookahead over the known roots (`portfolio|projects|programmes|
  drilling|assays|resources|approvals|optimiser|admin|search|notifications|account|manual`). **If another area adds
  a root route, add it to that list** or its pages will read as not-found. Record-level not-found pages, such as
  #/projects/NOPE, belong to their own sections.

## Shared components (merger: keep one copy each)

- `{"text_regex":"^Sort by ","role":"button"}`: every sortable table heading.
- `{"text":"Values behind this chart","role":"button"}`: every chart.
- `{"text_regex":"^computed by ADIT from ","role":"button"}`: the figures stamp's show-method toggle.
- `{"text_regex":"^PRJ-\\d{4}$","role":"link"}`: project id links in any register.
- `{"text":"Dismiss","role":"button"}`: the toast close button. If another area has a Dismiss button in a dialog,
  that area should key it with `page`.
- `{"text":"User Manual","role":"link"}`: the footer link, present on every app page.
- **Chrome facts.** The four expressions at the head of each of my pages' `facts_js` (signed-in user and role,
  highlighted section, unread and approvals-awaiting counts, toast message) are true on *every* app page. I suggest
  the merger append the same four strings to every other URL page's `facts_js`. They are identical strings, so they
  are easy to find in my pages. I did not use an always-on overlay for them, because an active selector overlay makes
  the harness report `Open dialog: <name>` on every page.

## Format issues and gaps (for whoever owns ATLAS-FORMAT.md and the harness)

1. **The harness `href` drops the hash.** `snapshot.js` `hrefPath` keeps only pathname and search, so on this
   hash-routed SPA every link's href is `/mockent/adit/`. `href`, `href_contains` and `href_regex` are useless here.
   Keeping `location.hash` in `href` (or adding a `hash` field) would let record-kind links such as
   `#/projects/PRJ-…`, `#/approvals/WF-…` and `#/assays/LAB-…` be keyed generically. It would also annotate the 60
   project-name links that are bare now.
2. **There is no landmark or region key.** Without custom elements `ancestor` is null, so a nav link and a page link
   with the same text cannot be told apart. A `landmark` field would fix this: the nearest `nav`, `aside`, `header`,
   `[role=dialog]` or `section` with an aria-label, for example `Sections`, `In this section`, `Breadcrumb`,
   `Account`, `Notifications`.
3. **There are no global facts.** The format needs a top-level `facts_js` that runs on every page. The only way to
   get one now, an always-visible overlay, makes the harness claim a dialog is open.
4. `text_contains` and `href_regex` are accepted by `atlas.py` but are not listed in ATLAS-FORMAT.md. I did not use
   them.
5. Every User Manual link (top bar, footer, account menu) has `target=_blank`. Whether the harness follows a new tab is
   unknown; the descriptions say the manual opens in a new tab and the current tab stays where it is.
6. `snapshot.js` and `atlas.py` changed on disk while I worked: snapshot.js now reads `SEL.dialog_title`, which
   `atlas.selector_lists` does not yet supply. My check ran with whatever `selector_lists` returned, and my overlays
   match by selector, so neither change affects this fragment.

## Fourth round (2026-09-22)

Two gaps seen in failure logs, fixed generically, from the app and the manual only:

1. **Submitting the search box.** The top-bar search is a `role=search` form with one
   `type=search` input and no button; it submits on Enter only (manual, Getting started:
   "Press Enter to open the results page"). The harness had no Enter, and its "Open Search
   the tenant" click twin (which only focuses the field) read as a search button, so Jev
   typed a code and clicked it repeatedly. Fixed in the harness, not here: a PRESS_ENTER
   operation for a filled search field or the field just typed into, and no "Open …" twin on
   a plain search box (`../../harness/README.md`, fourth round). The search box entry here
   needed no change; its note matches the new action too. Checked live: typing a project id
   and PRESS_ENTER opens `#/search?q=<id>` with that project.
2. **Acting as a named person.** Which person holds which role was only in the closed
   account menu, so "As <person>, do X" stopped on a record whose buttons belong to another
   role. New global fact `PEOPLE` (People and roles), read at run time from
   `adit.tenant.v1` (active users, the same list as Switch user), and positive routing on
   the account-menu button, the menu overlay and the Switch user entries ("Opening it is the
   way to act as another person or with another role"). The other areas' role-gated facts
   point to the account menu and to People and roles the same way. Earlier lesson kept:
   route, never refuse; the wording says what to do, not what is missing.

Also corrected: the ledger entries' note. Since the third-round harness each ledger link's
row label is its own line's kind, not the first line's.

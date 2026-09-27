"""Builds jev-atlas/atlas/parts/portfolio-global.json (scratch builder, not shipped)."""
# Copied from the area author's scratch directory on 2026-09-22 by the atlas merger;
# paths rewritten to be relative to this file and to $JEV_CLONE (the harness copy).
import os as _os, pathlib as _pl
_PARTS = _pl.Path(_os.environ.get("ADIT_PARTS_DIR") or _pl.Path(__file__).resolve().parents[2] / "atlas" / "parts")
_HARNESS = _os.environ.get("JEV_CLONE", str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'vendor' / 'jev-ultrafast')).rstrip("/") + "/jev_ultrafast/"

import json

OUT = str(_PARTS / "portfolio-global.json")

# ---------------------------------------------------------------- facts
# Global chrome facts: read-only, return a string or null. Added to every page in
# this fragment; the merger may copy CHROME_FACTS onto every other page.
SIGNED_IN = ("(() => { try { const s = JSON.parse(localStorage.getItem('adit.session.v1') || '{}');"
             " const t = JSON.parse(localStorage.getItem('adit.tenant.v1') || '{}');"
             " const u = ((t.world || {}).users || []).find(x => x.id === s.currentUserId);"
             " return u ? 'Signed in as ' + u.name + ', ' + u.title + ' (role ' + u.roleCode + ')' : null } catch (e) { return null } })()")
SECTION = ("(() => { try { const a = document.querySelector('nav.l1 a[aria-current=page]');"
           " if (!a) return 'Top-bar section: none highlighted (this page is outside the nine sections)';"
           " const c = a.cloneNode(true); c.querySelectorAll('.vh').forEach(x => x.remove());"
           " return 'Top-bar section: ' + c.textContent.trim() } catch (e) { return null } })()")
COUNTS = ("(() => { try { const b = document.querySelector('button[aria-controls=notif-tray]');"
          " const m = b && (b.getAttribute('aria-label') || '').match(/(\\d+) unread/);"
          " const v = document.querySelector('nav.l1 a[href=\"#/approvals\"] .vh');"
          " const n = v && v.textContent.match(/(\\d+)/);"
          " const parts = [];"
          " if (b) parts.push('Unread notifications: ' + (m ? m[1] : '0'));"
          " if (v) parts.push('approvals awaiting you: ' + (n ? n[1] : '0'));"
          " return parts.length ? parts.join('; ') : null } catch (e) { return null } })()")
TOAST = ("(() => { try { const t = [...document.querySelectorAll('.toasts .toast')].map(x => x.innerText.trim()).filter(Boolean);"
         " return t.length ? 'Message just shown: ' + t.join(' | ') : null } catch (e) { return null } })()")
IN_SECTION = ("(() => { try { const a = document.querySelector('nav.l2 a[aria-current=page]');"
              " return a ? 'Left column, current entry: ' + a.textContent.trim().replace(/\\s+/g, ' ') : null } catch (e) { return null } })()")
# Fourth round (2026-09-22): who can be signed in, with their roles, read from the tenant at run
# time. Without it, which person holds which role was visible only inside the closed account menu,
# so "as <person>" and "needs role X" requests stopped at a page whose buttons belong to another role.
PEOPLE = ("(() => { try { const s = JSON.parse(localStorage.getItem('adit.session.v1') || '{}');"
          " const t = JSON.parse(localStorage.getItem('adit.tenant.v1') || '{}');"
          " const us = ((t.world || {}).users || []).filter(u => u && u.name && u.active !== false);"
          " if (!us.length) return null;"
          " return 'People and roles (Switch user in the account menu signs in as any of them, to act as that person or with that role): '"
          " + us.map(u => u.name + ', ' + u.title + ' (' + u.roleCode + ')' + (u.id === s.currentUserId ? ', signed in now' : '')).join('; ') }"
          " catch (e) { return null } })()")
CHROME_FACTS = [SIGNED_IN, PEOPLE, SECTION, COUNTS, TOAST]

# Form state on the account pages: every field as label = value.
FORM_STATE = ("(() => { try { const out = [];"
              " for (const e of document.querySelectorAll('#content form input, #content form select, #content form textarea')) {"
              "  if (e.type === 'hidden' || e.type === 'submit' || e.type === 'button') continue;"
              "  let label = e.getAttribute('aria-label') || '';"
              "  if (!label) { const f = e.closest('label'); const s = f && f.querySelector('span'); label = s ? s.textContent.trim() : ''; }"
              "  if (!label) { const f = e.closest('label'); label = f ? f.textContent.replace(e.value || '', '').trim() : ''; }"
              "  if (!label) { const r = e.closest('tr'); label = r && r.cells[0] ? r.cells[0].textContent.trim() : (e.name || 'field'); }"
              "  let value;"
              "  if (e.type === 'checkbox' || e.type === 'radio') value = e.checked ? 'on' : 'off';"
              "  else if (e.tagName === 'SELECT') value = [...e.selectedOptions].map(o => o.label).join(', ');"
              "  else value = JSON.stringify(e.value);"
              "  out.push(label + ' = ' + value + (e.disabled ? ' (read-only here)' : ''));"
              " }"
              " return out.length ? 'Form fields: ' + out.join('; ') : null } catch (e) { return null } })()")
SEARCH_STATE = ("(() => { try { const q = new URLSearchParams(location.hash.split('?')[1] || '').get('q');"
                " if (!q) return 'Search: no query yet';"
                " const rows = [...document.querySelectorAll('#content table tbody tr')];"
                " const kinds = {}; rows.forEach(r => { const k = r.cells[0] ? r.cells[0].textContent.trim() : '?'; kinds[k] = (kinds[k] || 0) + 1 });"
                " const k = Object.entries(kinds).map(([a, b]) => a + ' ' + b).join(', ');"
                " return 'Search for \"' + q + '\": ' + rows.length + ' results' + (k ? ' (' + k + ')' : '') } catch (e) { return null } })()")
NOTIF_STATE = ("(() => { try { const m = [...document.querySelectorAll('#content .head .meta span')].map(s => s.textContent.trim());"
               " return m.length ? 'Notifications list: ' + m.join(', ') : null } catch (e) { return null } })()")
TRAY_STATE = ("(() => { try { const t = document.querySelector('#notif-tray'); if (!t) return null;"
              " const all = t.querySelectorAll('li').length, un = t.querySelectorAll('li.unread').length;"
              " return 'Notification tray: latest ' + all + ' shown, ' + un + ' unread' } catch (e) { return null } })()")
MANUAL_STATE = ("(() => { try { const h = document.querySelector('.manual h1, article h1, h1');"
                " return h ? 'Manual section open: ' + h.textContent.trim() : null } catch (e) { return null } })()")
METHOD_STATE = ("(() => { try { const b = document.querySelector('#content button.authority');"
                " if (!b) return null; const open = [...document.querySelectorAll('#content details.values')].filter(d => d.open).length;"
                " return 'Calculation method: ' + (b.getAttribute('aria-expanded') === 'true' ? 'shown' : 'hidden')"
                " + '; chart value tables open: ' + open } catch (e) { return null } })()")

# ---------------------------------------------------------------- pages
SECTIONS = "portfolio|projects|programmes|drilling|assays|resources|approvals|optimiser|admin|search|notifications|account|manual"

pages = [
    {
        "id": "portfolio",
        "match": {"url_regex": r"#/portfolio/?(\?.*)?$"},
        "name": "Portfolio: by stage (home page)",
        "what": ("The home page. A stage board with one column per pipeline stage (Reconnaissance, Target generation, Drilling, "
                 "Resource definition, Scoping study, Stage-gate decision); each column head shows how many projects are in that "
                 "stage and their committed and forecast fiscal-year spend, and each ticket under it is one project. Under the "
                 "board, the Needs attention ledger lists what needs action across the portfolio: approvals overdue or due within "
                 "seven days, tenements expiring within ninety days, batches on QAQC hold, programmes past the variance threshold, "
                 "projects whose gate is near, and unfilled project roles. At the bottom, the Active projects register."),
        "not_here": ("Other cuts of the same projects (by commodity, by jurisdiction, analytics, budget) are in the left column "
                     "under Shape. A project's own record, tenure and programmes are in Projects (a ticket or a project id opens it). "
                     "Acting on an approval: the request's own page in Approvals (each ledger item links to it). Changing records: each "
                     "record's own page."),
        "leads_to": {"Stage column head": "projects register cut to that stage", "Project ticket or project id": "project record",
                     "Needs attention item": "the approval, tenure, batch or project it is about",
                     "Projects register / Full register": "projects register", "Approvals button": "approvals queue",
                     "Shape links (left column)": "portfolio-commodity, portfolio-jurisdiction, portfolio-analytics, portfolio-budget"},
        "facts_js": CHROME_FACTS + [IN_SECTION],
    },
    {
        "id": "portfolio-commodity",
        "match": {"url_regex": r"#/portfolio/commodity/?(\?.*)?$"},
        "name": "Portfolio: by commodity",
        "what": ("The active projects grouped by commodity: a bar chart of budget per group, then one project register per "
                 "commodity with project, name, jurisdiction, stage, status, project geologist, area, planned budget, spent, "
                 "forecast against budget and next gate."),
        "not_here": ("Grouping by jurisdiction is By jurisdiction; the pipeline board is By stage; budget detail and variance "
                     "requests are Budget (all in the left column under Shape). A project's detail is in its record (the project id link)."),
        "leads_to": {"Project id / name link": "project record", "Shape links (left column)": "other portfolio cuts"},
        "facts_js": CHROME_FACTS + [IN_SECTION],
    },
    {
        "id": "portfolio-jurisdiction",
        "match": {"url_regex": r"#/portfolio/jurisdiction/?(\?.*)?$"},
        "name": "Portfolio: by jurisdiction",
        "what": ("The active projects grouped by jurisdiction (state, province or region): a budget bar chart, then one project "
                 "register per jurisdiction with the same columns as the other registers."),
        "not_here": ("Grouping by commodity is By commodity; tenement expiry and tenure detail are on each project's tenure tab "
                     "in Projects, and expiring tenements are listed in Needs attention on By stage."),
        "leads_to": {"Project id / name link": "project record", "Shape links (left column)": "other portfolio cuts"},
        "facts_js": CHROME_FACTS + [IN_SECTION],
    },
    {
        "id": "portfolio-analytics",
        "match": {"url_regex": r"#/portfolio/analytics/?(\?.*)?$"},
        "name": "Portfolio: analytics",
        "what": ("Portfolio-wide performance for the fiscal year: a stamp of totals (metres drilled against plan, holes completed, "
                 "significant intercepts, assay turnaround, QAQC pass rate, batches at the lab) with a show-method toggle that "
                 "explains how each is computed, then charts of metres drilled by month against plan, spend against significant "
                 "intercepts, batches submitted and received, and QAQC check counts. Each chart has a Values behind this chart "
                 "disclosure holding its figures as a table."),
        "not_here": ("Money against budget per project is Budget. Individual holes, batches and QAQC failures are in Drilling "
                     "and Assays. Changing records: each record's own page."),
        "leads_to": {"Project names in chart value tables": "project record", "Shape links (left column)": "other portfolio cuts"},
        "facts_js": CHROME_FACTS + [IN_SECTION, METHOD_STATE],
    },
    {
        "id": "portfolio-budget",
        "match": {"url_regex": r"#/portfolio/budget/?(\?.*)?$"},
        "name": "Portfolio: budget",
        "what": ("Money for every active project in the fiscal year: a stamp of approved budget, committed, spent to date, "
                 "forecast at year end and variance requests pending; charts of programme spend by type and cost codes by "
                 "category; and a Budget by project table (budget, committed, spent, % spent, forecast, variance). Forecast above "
                 "budget carries a plus sign, below a minus sign."),
        "not_here": ("Deciding a variance request: Approvals (the Variance requests button opens that queue filtered). "
                     "A programme's own ledger and forecast: the programme's record in Programmes. Budget changes: variance "
                     "requests in Approvals."),
        "leads_to": {"Variance requests": "approvals queue, pending budget-variance requests", "Project id link": "project record",
                     "Shape links (left column)": "other portfolio cuts"},
        "facts_js": CHROME_FACTS + [IN_SECTION, METHOD_STATE],
    },
    {
        "id": "search",
        "match": {"url_regex": r"#/search/?(\?.*)?$"},
        "name": "Search results",
        "what": ("Results of the top-bar search across the whole tenant. The query matches any part of an id (project, programme, "
                 "hole, batch, approval request, estimate, tenement, user) and any word of a name; sample numbers match from five "
                 "digits. Each result row shows its kind, id, name and status, and its id or name links to the record. At least "
                 "two characters are needed."),
        "not_here": ("A new query: the top-bar search box. Filtering within one register (projects, holes, batches): that "
                     "section's own page."),
        "leads_to": {"Result link": "the record of that result (project, programme, hole, batch, sample, approval, estimate...)"},
        "facts_js": CHROME_FACTS + [SEARCH_STATE],
    },
    {
        "id": "notifications",
        "match": {"url_regex": r"#/notifications/?(\?.*)?$"},
        "name": "Notifications",
        "what": ("The full list of your notifications, newest first: whether each is read, its kind (approval, assay, tenure, "
                 "programme, budget, mention, system), a title that links to the record it is about, a detail line and when it "
                 "arrived. Mark all read clears the unread count."),
        "not_here": ("Which kinds of notification reach you, and the email digest, are set in Notification settings (the Settings "
                     "button, or the account menu). Acting on the record a notification is about happens on that record's page."),
        "leads_to": {"Notification title": "the record it is about", "Settings": "account-notifications"},
        "facts_js": CHROME_FACTS + [NOTIF_STATE],
    },
    {
        "id": "account-profile",
        "match": {"url_regex": r"#/account/?(\?.*)?$"},
        "name": "My account: My profile",
        "what": ("Your own profile: phone, location and time zone can be changed and saved with Save profile. Name, email and "
                 "team come from the company identity provider and are shown read-only."),
        "not_here": ("Display preferences (start page, units, date format, rows per page) are Preferences; which notifications "
                     "reach you is Notification settings; sign-in and sessions are Security (all in the left column under My "
                     "account). Other people's accounts are managed in Admin."),
        "leads_to": {"Left column": "account-preferences, account-notifications, account-security"},
        "facts_js": CHROME_FACTS + [IN_SECTION, FORM_STATE],
    },
    {
        "id": "account-notifications",
        "match": {"url_regex": r"#/account/notifications/?(\?.*)?$"},
        "name": "My account: Notification settings",
        "what": ("Which kinds of notification reach you in ADIT, one on/off switch per kind (Approvals, Assays, Tenure, "
                 "Programmes, Budget, Mentions and comments, System) with a line saying when each kind is sent, and the email "
                 "digest (none, daily, weekly). Changes take effect when Save is pressed."),
        "not_here": ("Reading or clearing notifications: the Notifications page (All notifications, in the bell's tray). Display "
                     "preferences: Preferences."),
        "leads_to": {"Left column": "account-profile, account-preferences, account-security"},
        "facts_js": CHROME_FACTS + [IN_SECTION, FORM_STATE],
    },
    {
        "id": "account-preferences",
        "match": {"url_regex": r"#/account/preferences/?(\?.*)?$"},
        "name": "My account: Preferences",
        "what": ("Your personal display preferences: the section that opens on sign-in, a default project, units (metric or "
                 "imperial, display only), date format, grade decimals, rows per page for long tables, and compact tables. "
                 "Changes take effect when Save preferences is pressed. They affect only you."),
        "not_here": ("The dark/light theme: the switch at the far right of the top bar. Tenant-wide settings "
                     "(for everyone): Admin. Notification choices: Notification settings."),
        "leads_to": {"Left column": "account-profile, account-notifications, account-security"},
        "facts_js": CHROME_FACTS + [IN_SECTION, FORM_STATE],
    },
    {
        "id": "account-security",
        "match": {"url_regex": r"#/account/security/?(\?.*)?$"},
        "name": "My account: Security",
        "what": ("How you sign in (identity provider, multi-factor requirement, idle session timeout, all read-only) and your "
                 "active sessions, one row per device; a session other than this browser can be signed out from its row."),
        "not_here": ("Passwords and multi-factor settings: the company identity provider, outside ADIT. Working as "
                     "another person, or with a role you do not hold: Switch user in the account menu (top bar)."),
        "leads_to": {"Left column": "account-profile, account-preferences, account-notifications"},
        "facts_js": CHROME_FACTS + [IN_SECTION],
    },
    {
        "id": "manual",
        "match": {"url_regex": r"#/manual(/[^?]*)?/?(\?.*)?$"},
        "name": "ADIT User Manual",
        "what": ("The product's user manual, one section per page: About ADIT, Getting started, then one section per area of the "
                 "application (Portfolio, Projects, Programmes, Drilling, Assays, Resources, Approvals, Optimiser, Administration), "
                 "Your account and Reference (record id formats, status chips, money, grades and units, what changed). It "
                 "explains what each page shows. It has its own layout: a contents list on the left and no ADIT top bar."),
        "not_here": ("Records and their data: the application itself, reached through Back to ADIT in the contents column."),
        "leads_to": {"Contents entries": "other manual sections", "Back to ADIT": "portfolio"},
        "facts_js": [MANUAL_STATE],
    },
    {
        "id": "not-found",
        "match": {"url_regex": r"#/(?!(" + SECTIONS + r")(/|\?|$))"},
        "name": "Page not found",
        "what": "The address does not lead to any page of ADIT. The top-bar sections still work from here.",
        "not_here": ("An unknown record id inside a section shows that section's own not-found message. Every section: "
                     "the top-bar section links."),
        "leads_to": {"go to the Portfolio": "portfolio"},
        "facts_js": CHROME_FACTS,
    },
    # ------------------------------------------------ overlays
    {
        "id": "notification-tray",
        "layer": "overlay",
        "match": {"selector": "#notif-tray"},
        "name": "Notification tray",
        "what": ("The bell's drop-down: your latest notifications, unread ones first marked, each a link to the record it is "
                 "about, with Mark all read, Notification settings and All notifications. It stays open over the page; the bell "
                 "closes it again."),
        "not_here": "The complete history is on the Notifications page (All notifications).",
        "facts_js": [TRAY_STATE],
    },
    {
        "id": "account-menu",
        "layer": "overlay",
        "match": {"selector": "#user-menu"},
        "name": "Account menu",
        "what": ("The drop-down under your avatar in the top bar: who is signed in and their role, links to My profile, "
                 "Preferences, Notification settings and the User Manual, and, in a demonstration tenant, a Switch user list "
                 "that changes who is signed in. Working as another person, or with a role the signed-in user does not "
                 "hold, is done here: pick that person under Switch user (People and roles lists who holds each role)."),
        "not_here": ("Security (sign-in method and sessions): the left column of any My account page. The theme switch: "
                     "the separate button at the far right of the top bar."),
    },
]

# ---------------------------------------------------------------- controls
C = []


def add(key, region, what, not_for, **extra):
    entry = {"key": key, "region": region, "what": what, "not_for": not_for}
    entry.update(extra)
    C.append(entry)


TOP = "Top bar"
NAV = "Top bar, section links"

# Top bar
add({"text": "ADIT home", "role": "link"}, TOP,
    "The ADIT mark at the far left. Returns to the Portfolio home page (the stage board).",
    "Opening the user manual (the question-mark button) or any other section (the section links next to it).")
add({"text": "Skip to content", "role": "link"}, TOP,
    "Keyboard shortcut link that moves focus past the top bar to the page's main content.",
    "Navigating to another page; focus moves within this page.")

nav = [
    ("Portfolio", "Opens the Portfolio section: the home page with every active project by stage, what needs attention, "
                  "and other cuts (by commodity, by jurisdiction, analytics, budget).",
     "A single project's record, which is in Projects."),
    ("Projects", "Opens the Projects section: the register of exploration projects and each project's record (tenure, "
                 "programmes, team, budget, gates).",
     "The portfolio-wide overview (Portfolio) or field work on a project (Programmes)."),
    ("Programmes", "Opens the Programmes section: units of field or study work on a project (drilling, geochemistry, "
                   "geophysics, mapping, metallurgy, environmental baseline) with their budgets, phases, crews and logistics.",
     "Individual drillholes (Drilling) or laboratory results (Assays)."),
    ("Drilling", "Opens the Drilling section: every drillhole in the tenant across projects and programmes, and the rigs.",
     "Assay results of the samples from a hole (Assays) or a programme's budget (Programmes)."),
    ("Assays", "Opens the Assays section: sample batches sent to laboratories, the results that come back, and QAQC checks.",
     "Resource estimates built from the results (Resources)."),
    ("Resources", "Opens the Resources section: resource estimates and what they are worth under the price deck.",
     "Assay batches (Assays) or portfolio budget figures (Portfolio, Budget)."),
    ("Optimiser", "Opens the Optimiser section: choosing which candidate drill targets to fund under a budget and rig-day limit, "
                  "with saved scenarios.",
     "Approving programmes (Approvals) or reviewing spend (Portfolio, Budget)."),
    ("Admin", "Opens the Admin section: tenant administration (users, system settings, workflows), available depending on role.",
     "Your own profile or preferences, which are in the account menu."),
]
for text, what, not_for in nav:
    add({"text": text, "role": "link"}, NAV, what, not_for,
        note="Keyed on the link text; a breadcrumb link with the same text leads to the same section.")
add({"text_regex": r"^Approvals( \(.*awaiting you\))?$", "role": "link"}, NAV,
    "Opens the Approvals section: the queue of workflow requests (programme approvals, budget variances, purchase orders, "
    "tenure renewals, resource releases). The number in its name is how many requests are waiting on your role.",
    "Notifications about approvals (the bell). Deciding a request: the request's own page in this section.")
add({"text": "Search the tenant", "role": "searchbox"}, TOP,
    "Search box for the whole tenant: matches any part of an id (project, programme, hole, batch, approval request, "
    "estimate, tenement) and any word of a name; sample numbers match from five digits. Pressing Enter opens the Search "
    "results page, where the matches are listed.",
    "Filtering the table on the current page: that page's own filters. This box searches the whole tenant.")
add({"text_regex": r"^Notifications(,|$)", "role": "button"}, TOP,
    "The bell. Its name says how many notifications are unread. Opens and closes the notification tray with the latest "
    "notifications.",
    "Changing which notifications you receive (Notification settings) or the approvals queue (Approvals).")
add({"text": "User Manual (opens in a new tab)", "role": "link"}, TOP,
    "The question-mark help button: opens the ADIT User Manual in a new browser tab; this tab stays where it is.",
    "Searching records (the search box) or contacting support.")
add({"text_regex": r"Account menu$", "role": "button"}, TOP,
    "Your avatar; its name says who is signed in. Opens and closes the account menu (profile, preferences, notification "
    "settings, user manual, and Switch user). Opening it is the way to act as another person or with another role: "
    "Switch user signs in as the person who holds it.",
    "Signing out or the theme (the theme switch is the next button to the right).")
add({"text_regex": r"^Switch to the (light|dark) theme$", "role": "button"}, TOP,
    "Theme switch at the far right of the top bar: changes between the dark and light colour themes, remembered on this "
    "device. Its name says which theme it switches to.",
    "Any preference saved to your account (Preferences) or any data.")
add({"text": "Dismiss", "role": "button"}, "Message toast (bottom of screen)",
    "Closes the short confirmation message that appears after something is saved.",
    "Undoing the change the message reports.",
    note="Generic key: any Dismiss button. On ADIT it was seen only on toasts; if another area has one in a dialog, key it with page.")

# Footer
add({"text": "User Manual", "role": "link"}, "Page footer",
    "Opens the ADIT User Manual in a new browser tab.",
    "Help about the current record; the manual describes pages in general.")

# Left column, Portfolio
LEFTP = "Left column (In this section), Portfolio"
shapes = [
    ("By stage", "Shows the stage board: projects in columns by pipeline stage, and the Needs attention ledger. This is the "
                 "Portfolio home page.", "Grouping by commodity or jurisdiction (the entries below it)."),
    ("By commodity", "Shows the active projects grouped by commodity, with a budget chart and one register per commodity.",
     "Grouping by place (By jurisdiction) or by pipeline stage (By stage)."),
    ("By jurisdiction", "Shows the active projects grouped by jurisdiction (state, province or region), with a budget chart "
                        "and one register per jurisdiction.", "Grouping by commodity (By commodity)."),
    ("Analytics", "Shows portfolio performance: metres drilled against plan, spend against intercepts, batches, QAQC counts.",
     "Money against budget (Budget)."),
    ("Budget", "Shows approved, committed, spent and forecast money for every active project, with pending variance requests.",
     "Drilling and assay performance (Analytics) or deciding a variance request (Approvals)."),
]
for text, what, not_for in shapes:
    add({"row_label": "Shape", "text": text}, LEFTP, what, not_for)
add({"row_label": "Watching", "role": "link"}, LEFTP,
    "A project you have marked Watch (name and short id). Opens that project's record. The list is per user.",
    "Changing what you watch: the Watch control on a project's own page.",
    note="Generic key: every entry under Watching.")

# Portfolio home page
PH = "Portfolio page head"
add({"page": "portfolio", "text": "Projects register", "role": "link"}, PH,
    "Opens the full Projects register, every project with filters.",
    "The register of one stage (a stage column head) or one project (its ticket).")
add({"page": "portfolio", "text_regex": r"^Approvals( \d+)?$", "role": "link"}, PH,
    "Opens the Approvals queue; the number is how many requests await you.",
    "Deciding a request: the request's own page, reached from the queue.")
BOARD = "Stage board (Projects by stage)"
add({"page": "portfolio", "row_label": "Projects by stage", "text_regex": r": \d+ projects?, .*committed$"}, BOARD,
    "Head of one stage column: the stage name, how many projects are in it and their committed and forecast spend. Opens "
    "the Projects register cut to that stage.",
    "Opening one project (the tickets under the head).")
add({"page": "portfolio", "row_label": "Projects by stage", "role": "link"}, BOARD,
    "A project ticket in a stage column: id, name, commodity, the stage's live figure, jurisdiction and next gate. A dashed "
    "border means the project is on hold. Opens the project's record.",
    "Opening the register of the whole stage (the column head).",
    note="Generic key: every ticket on the board.")
LEDGER = "Needs attention ledger"
for kind in ["Approval overdue", "Approval due", "Tenure expiring", "QAQC hold", "Gate due", "Vacancy"]:
    add({"page": "portfolio", "row_label": kind, "role": "link"}, LEDGER,
        "A Needs attention item. Opens the record it is about.",
        "Acting on the item: the record it opens.",
        note="One entry per ledger kind, keyed on the kind label at the start of the link's own line (the harness row label "
             "since the third round, 2026-09-22; before it, every ledger link read the FIRST line's kind). The merged atlas "
             "replaces these with per-route ledger entries (tools/harness2.py).")
add({"page": "portfolio", "text": "Full register", "role": "link"}, "Active projects panel",
    "Opens the full Projects register (with filters, closed projects and paging).",
    "Sorting this panel's table (the column headings).")

# Shared components seen in this area
add({"text_regex": r"^PRJ-\d{4}$", "role": "link"}, "Project table, id column",
    "A project id. Opens that project's record.",
    "Sorting the table (the column headings).",
    note="Shared: project id links appear in many registers across areas.")
add({"text_regex": r"^Sort by ", "role": "button"}, "Table column heading",
    "Sorts the table by this column; pressing again reverses the order.",
    "Filtering rows or changing which columns are shown.",
    note="Shared component: every sortable table heading in ADIT. Merger should keep one copy.")
add({"text": "Values behind this chart", "role": "button"}, "Chart disclosure",
    "Opens or closes a table under the chart holding the exact figures the chart plots.",
    "Changing the chart or exporting data.",
    note="Shared component: every chart in ADIT.")
add({"text_regex": r"^computed by ADIT from ", "role": "button"}, "Figures stamp",
    "Shows or hides the method behind the stamp's figures: how each total is computed and from which records.",
    "Changing any figure or filtering the page.",
    note="Shared component: stamp on analytics and budget pages; may appear elsewhere.")
add({"page": "portfolio-budget", "text": "Variance requests", "role": "link"}, PH,
    "Opens the Approvals queue filtered to pending budget-variance requests.",
    "Changing a budget: a budget-variance request, decided in Approvals.")

# Search results
for kind in ["project", "programme", "hole", "batch", "sample", "approval", "estimate", "tenement", "user"]:
    add({"page": "search", "row_label": kind, "role": "link"}, "Search results table",
        f"Search result ({kind}). Opens its record.",
        "Running a new search: the top-bar search box.",
        note="Keyed on the result's Kind cell, which the harness takes as the row label.")

# Notifications page
NP = "Notifications page head"
add({"page": "notifications", "text": "Mark all read", "role": "button"}, NP,
    "Marks every notification as read, clearing the bell's unread count.",
    "Deleting notifications or turning a kind off (Settings).")
add({"page": "notifications", "text": "Settings", "role": "link"}, NP,
    "Opens Notification settings: which kinds reach you and the email digest.",
    "Marking notifications read (Mark all read).")
for state in ["unread", "read"]:
    add({"page": "notifications", "row_label": state, "role": "link"}, "Notifications table",
        f"Notification ({state}). Opens the record it is about.",
        "Marking notifications read: Mark all read.",
        note="Keyed on the Read column value, which the harness takes as the row label.")

# My account left column
LA = "Left column (My account)"
acct = [
    ("Profile", "Opens My profile: phone, location, time zone.", "Display preferences (Preferences)."),
    ("Preferences", "Opens Preferences: start section, default project, units, date format, grade decimals, rows per page, "
                    "compact tables.", "Notification choices (Notification settings) or the theme (top bar)."),
    ("Notification settings", "Opens Notification settings: which kinds of notification reach you and the email digest.",
     "Reading notifications (the bell or the Notifications page)."),
    ("Security", "Opens Security: how you sign in and your active sessions.", "Changing your password: the company identity provider."),
]
for text, what, not_for in acct:
    add({"row_label": "My account", "text": text, "role": "link"}, LA, what, not_for)

# Notification tray overlay
TR = "Notification tray (bell drop-down)"
add({"page": "notification-tray", "text": "Mark all read", "role": "button"}, TR,
    "Marks every notification as read and clears the bell's count.",
    "Opening the full list (All notifications).")
add({"page": "notification-tray", "text": "Notification settings", "role": "link"}, TR,
    "Opens Notification settings: which kinds of notification reach you and the email digest.",
    "Reading notifications (the items above, or All notifications).")
add({"page": "notification-tray", "text": "All notifications", "role": "link"}, TR,
    "Opens the Notifications page with the complete list.",
    "Changing which notifications you receive (Notification settings).")
add({"page": "notification-tray", "role": "link",
     "text_regex": r"^(Tenement |Awaiting your |Programme |Release |Batch |Assay |Budget |Crew |Rig |Gate |Maintenance |.+ commented on |.+ mentioned you)"},
    TR,
    "Recent notification. Opens the record it is about.",
    "Marking notifications read: Mark all read in the tray.",
    note="Keyed on notification title wording (templates, not records); a notification kind not in the pattern keeps its bare label.")

# Account menu overlay
AM = "Account menu (top bar drop-down)"
add({"page": "account-menu", "text": "My profile", "role": "link"}, AM,
    "Opens My profile: your phone, location and time zone.",
    "Switching to another user (the Switch user list below).")
add({"page": "account-menu", "text": "Preferences", "role": "link"}, AM,
    "Opens Preferences: start section, default project, units, date format, grade decimals, rows per page, compact tables.",
    "The colour theme (the top-bar theme switch).")
add({"page": "account-menu", "text": "Notification settings", "role": "link"}, AM,
    "Opens Notification settings: which kinds of notification reach you and the email digest.",
    "Reading notifications (the bell).")
add({"page": "account-menu", "text": "User Manual", "role": "link"}, AM,
    "Opens the ADIT User Manual in a new browser tab.",
    "Your account settings.")
add({"page": "account-menu", "role": "button", "text_regex": r" [A-Z]{2,6}$"}, "Account menu, Switch user list",
    "Signs in as this person (name and role code), to act as them or with their role: what you can see and act on, and "
    "which approvals await you, follow the role. The current user is the highlighted entry.",
    "Editing that person's account (Admin) or opening their profile.",
    note="Generic key: every Switch user entry; the trailing role code is what the key relies on.")

# Profile form
PF = "My profile form"
add({"page": "account-profile", "row_label": "Phone"}, PF, "Your phone number, shown to colleagues.",
    "Your name or email, which are set in the company identity provider.")
add({"page": "account-profile", "row_label": "Location"}, PF, "Your office or base location.", "Your time zone (the next field).")
add({"page": "account-profile", "row_label": "Time zone"}, PF,
    "Your time zone, as a region name.", "Date format (Preferences).")
add({"page": "account-profile", "text": "Save profile"}, PF,
    "Saves the profile fields; a short confirmation message appears.",
    "Saving preferences or notification settings, which have their own Save buttons on their own pages.")

# Notification settings form
NS = "Notification settings form"
kinds = [("Approvals", "a workflow step is waiting on your role, or a request you raised was decided"),
         ("Assays", "a batch is received, placed on hold, accepted or rejected on a project you work on"),
         ("Tenure", "a tenement is within 90 days of expiry or a renewal changes state"),
         ("Programmes", "crew assignments, rig moves, phase changes and gate decisions"),
         ("Budget", "a programme forecast crosses the variance threshold"),
         ("Mentions and comments", "someone mentions you or comments on a record you own"),
         ("System", "maintenance windows, releases and account notices")]
for kind, when in kinds:
    add({"page": "account-notifications", "text": f"{kind} notifications"}, NS,
        f"On/off switch for {kind} notifications in ADIT: sent when {when}. Takes effect on Save.",
        "The other kinds, which have their own switches, or the email digest (the select below).")
add({"page": "account-notifications", "row_label": "Email digest"}, NS,
    "How often a summary email is sent: none, daily or weekly. Takes effect on Save.",
    "Which notifications appear in ADIT (the switches above).",
    options=["None", "Daily at 07:00", "Weekly, Monday"])
add({"page": "account-notifications", "text": "Save", "role": "button"}, NS,
    "Saves the notification switches and the email digest.",
    "Marking notifications read (the Notifications page).")

# Preferences form
PR = "Preferences form"
add({"page": "account-preferences", "row_label": "Open on sign-in"}, PR,
    "The section ADIT opens on when you sign in; takes effect on Save preferences.", "The page you are on now.",
    options=["portfolio", "projects", "programmes", "drilling", "assays", "resources", "approvals", "optimiser", "admin"])
add({"page": "account-preferences", "row_label": "Default project"}, PR,
    "A project pre-selected where a page needs one, or none.",
    "Watching a project (that is done on the project's page).")
add({"page": "account-preferences", "row_label": "Units"}, PR,
    "Metric or imperial units for display only; stored values do not change.", "Currency, which is the tenant's base currency.",
    options=["Metric", "Imperial (display only)"])
add({"page": "account-preferences", "row_label": "Date format"}, PR,
    "How dates are written across ADIT (year first, day first or month first).", "Your time zone (My profile).")
add({"page": "account-preferences", "row_label": "Grade decimals"}, PR,
    "How many decimal places assay grades are shown with.", "Rounding of money or metres.")
add({"page": "account-preferences", "row_label": "Rows per page"}, PR,
    "Page size of long tables.", "Compact row height (Compact tables).", options=["25", "50", "100"])
add({"page": "account-preferences", "text": "Compact tables"}, PR,
    "Tighter row spacing in tables.", "The number of rows per page (Rows per page).")
add({"page": "account-preferences", "text": "Save preferences"}, PR,
    "Saves every preference on this page; a short confirmation appears.",
    "The theme, which is the top-bar switch and needs no save.")

# Security
add({"page": "account-security", "text": "Sign out", "role": "button"}, "Sessions table",
    "Ends the session of that other device (the row it is on).",
    "This browser's own session, which stays signed in; each Sign out acts on the other device in its row.")

# Manual
MN = "Manual contents column"
add({"page": "manual", "role": "link", "text_regex": r"^\d+ \. .*[^→]$"}, MN,
    "A section of the user manual, numbered as in the contents. Opens that section.",
    "Opening the application page of the same name: that section of the application (Back to ADIT leads there).",
    note="Generic key: every contents entry.")
add({"page": "manual", "text": "← Back to ADIT"}, MN,
    "Leaves the manual and returns to the application (Portfolio).", "Going to the previous manual section.")
add({"page": "manual", "role": "link", "text_regex": r"→$"}, "Manual page foot",
    "Opens the next section of the manual.", "Returning to the application (Back to ADIT).")
add({"page": "manual", "role": "link", "text_regex": r"^←\s*\d"}, "Manual page foot",
    "Opens the previous section of the manual.", "Returning to the application (Back to ADIT).")

# 404
add({"page": "not-found", "text": "go to the Portfolio"}, "Page not found message",
    "Opens the Portfolio home page.", "Recovering the address typed; every section: the top-bar links.")

atlas = {"app": "ADIT (Brannock Geosystems EMS 7.4, demo)", "version": "2026-09-22",
         "area": "portfolio-global", "pages": pages, "controls": C}
with open(OUT, "w") as f:
    json.dump(atlas, f, indent=1, ensure_ascii=False)
print(len(pages), "pages", len(C), "controls")

"""Generate jev-atlas/atlas/parts/admin.json (the Administration area fragment)."""
# Copied from the area author's scratch directory on 2026-09-22 by the atlas merger;
# paths rewritten to be relative to this file and to $JEV_CLONE (the harness copy).
import os as _os, pathlib as _pl
_PARTS = _pl.Path(_os.environ.get("ADIT_PARTS_DIR") or _pl.Path(__file__).resolve().parents[2] / "atlas" / "parts")
_HARNESS = _os.environ.get("JEV_CLONE", str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'vendor' / 'jev-ultrafast')).rstrip("/") + "/jev_ultrafast/"

import json

OUT = str(_PARTS / "admin.json")

EVERYONE = "ADMINISTRATION, TENANT-WIDE: "

# ---------------------------------------------------------------- facts_js
TOAST = ("(() => { const t=[...document.querySelectorAll('.toasts .toast')].map(e=>e.innerText.trim()).filter(Boolean);"
         " return t.length ? 'Latest message: ' + t[t.length-1] : null })()")


def access(has_editor):
    """Which admin rights the signed-in role has, read from what the page renders."""
    return ("(() => { const m=document.querySelector('main'); if(!m) return null; const t=m.innerText;"
            " if (/does not include administration/.test(t)) return 'Admin access: Administration opens for roles with admin.read (System Administrator); for the signed-in role it shows its heading and a notice. To work as the System Administrator, switch user in the account menu (People and roles lists who holds each role).';"
            " const disabled=m.querySelectorAll('input:disabled,select:disabled,textarea:disabled').length;"
            f" const editor={has_editor};"
            " if (/Read-only: your role/.test(t) || disabled || !editor) return 'Admin access: view only for the signed-in role; editing these values is for a role with administration rights: to act with it, switch user in the account menu to a person who holds it (People and roles lists who holds each role).';"
            " return 'Admin access: the signed-in role can change what is on this page. Changes apply to the whole tenant.' })()")


ACCESS_SETTINGS = access("!!m.querySelector('button[type=submit]')")
ACCESS_FORM = access("!!m.querySelector('button[type=submit]')")
ACCESS_USERS = access("[...m.querySelectorAll('button')].some(b=>b.innerText.trim()==='Add user')")


def unsaved(pairs_js):
    """Compare the form on screen with the saved tenant settings in localStorage (read-only)."""
    return ("(() => { const raw=localStorage.getItem('adit.tenant.v1'); if(!raw) return null;"
            " const s=(JSON.parse(raw).world||{}).settings; if(!s) return null; const f=document.querySelector('main form'); if(!f) return null;"
            " const lab=e=>(e.getAttribute('aria-label')||e.closest('label')?.querySelector('span')?.textContent||e.closest('label')?.textContent||e.name||'').trim();"
            " const out=[]; const bad=[];"
            f" const saved={pairs_js};"
            " for (const e of f.querySelectorAll('input,select')) { if(!e.name||!(e.name in saved)) continue;"
            "  const now = e.type==='checkbox' ? String(e.checked) : String(e.value); const was=String(saved[e.name]);"
            "  if (now!==was) out.push(lab(e)+' '+was+' -> '+(now===''?'(empty)':now));"
            "  if (!e.checkValidity()) bad.push(lab(e)+' ('+e.validationMessage+')'); }"
            " let r = out.length ? 'Unsaved changes on this page: '+out.join('; ') : 'All changes on this page are saved.';"
            " if (bad.length) r += ' Save takes effect once these are valid: '+bad.join('; ');"
            " return r })()")


SETTINGS_SAVED = ("(()=>{const m={tenantName:s.tenantName,fy:s.fiscalYearStart,currency:s.baseCurrency,locale:s.numberLocale,"
                  "variance:s.varianceThresholdPct,gateRole:s.gateApproverRole,timeout:s.sessionTimeoutMin,pwlen:s.passwordMinLength,"
                  "sso:s.ssoProvider,mfa:s.mfaRequired,retention:s.auditRetentionDays,attach:s.attachmentMaxMb};return m})()")
PRICE_SAVED = ("(()=>{const m={};for(const p of (s.priceDeck||[])) m['price-'+p.commodity]=p.value;"
               "for(const k in (s.cutoffs||{})) m['cut-'+k]=s.cutoffs[k];return m})()")
QAQC_SAVED = ("(()=>{const q=s.qaqc||{};return {sigma:q.standardSigma,blank:q.blankMaxMultiple,dup:q.duplicateHardPct,ins:q.minInsertionRate}})()")

DIALOG_FORM = ("(() => { const d=[...document.querySelectorAll('dialog[open]')].pop(); if(!d) return null; const f=d.querySelector('form'); if(!f) return null;"
               " const parts=[]; for (const e of f.querySelectorAll('input,select')) {"
               "  const l=e.closest('label'); const name=(l?.querySelector('span')?.textContent||l?.textContent||e.name||'').trim();"
               "  let v = e.type==='checkbox' ? (e.checked?'checked':'not checked') : e.tagName==='SELECT' ? e.selectedOptions[0]?.text : (e.value===''?'(empty)':'\"'+e.value+'\"');"
               "  let flags=[]; if (e.required) flags.push('required'); if (!e.checkValidity()) flags.push('invalid: '+e.validationMessage);"
               "  parts.push(name+' = '+v+(flags.length?' ('+flags.join(', ')+')':'')); }"
               " return 'Dialog \"'+(d.getAttribute('aria-label')||'')+'\" fields: '+parts.join('; ') })()")

DIALOG_NAME = ("(() => { const d=[...document.querySelectorAll('dialog[open]')].pop(); return d ? 'Open dialog: '+(d.getAttribute('aria-label')||d.querySelector('h2')?.textContent||'').trim() : null })()")

AUDIT_STATE = ("(() => { const m=document.querySelector('main'); if(!m) return null; const f=m.querySelector('input[type=search]'); const u=m.querySelector('select');"
               " const count=(m.querySelector('.meta')?.innerText||'').split('\\n')[0]; const pg=m.querySelector('nav.pager [aria-current=page]')?.textContent;"
               " const sorted=[...m.querySelectorAll('th[aria-sort]')].find(th=>th.getAttribute('aria-sort')!=='none');"
               " return 'Audit log view: '+(count||'')+'; text filter '+(f&&f.value?'\"'+f.value+'\"':'none')+'; user filter '+(u?u.selectedOptions[0]?.text:'none')"
               "+(pg?'; page '+pg:'')+(sorted?'; sorted by '+sorted.innerText.trim()+' '+sorted.getAttribute('aria-sort'):'') })()")

USERS_STATE = ("(() => { const m=document.querySelector('main'); if(!m) return null; const w=m.querySelector('.tbl-wrap'); if(!w) return null;"
               " const hidden=[...m.querySelectorAll('tbody button')].filter(b=>{const r=b.getBoundingClientRect(); return r.right>innerWidth||r.left<0}).length;"
               " const sorted=[...m.querySelectorAll('th[aria-sort]')].find(th=>th.getAttribute('aria-sort')!=='none');"
               " return (sorted?'Users sorted by '+sorted.innerText.trim()+' '+sorted.getAttribute('aria-sort')+'. ':'')"
               "+(hidden?hidden+' row Edit buttons are off the right edge of the window (the table is wider than the screen).':'') || null })()")

# ---------------------------------------------------------------- overlay selectors
def on(route):
    return f'.shell:has(nav.l2 a[aria-current="page"][href="{route}"])'


pages = [
    {
        "id": "admin-settings",
        "match": {"url_regex": r"#/admin/?(\?.*)?$"},
        "name": "System settings (Administration)",
        "what": ("Administration landing page. Tenant-wide configuration that applies to every user: tenant name, fiscal year start, "
                 "base currency, number locale, the budget-variance threshold and the stage-gate approver role; security settings "
                 "(session timeout, minimum password length, single sign-on provider, multi-factor requirement, audit retention, "
                 "attachment limit); and the auto-numbering rules, which are shown read-only. In a demonstration tenant it also offers "
                 "Reset demonstration tenant. A left 'In this section' list leads to the other administration pages. Viewing needs "
                 "admin.read; changing needs admin.write (System Administrator), whose view carries the editable fields and Save."),
        "not_here": ("Day-to-day record work (projects, programmes, drilling, assays, approvals, budgets): each record's own section in the "
                     "top navigation. Commodity prices and cut-offs: Price deck and cut-offs; QAQC pass/fail limits: "
                     "QAQC tolerances; people and their roles: Users; approval routes: Workflows (view only). Your own display "
                     "preferences: the account menu. Auto-numbering rules: kept by the product's support team."),
        "leads_to": {
            "Price deck and cut-offs (section list)": "admin-price-deck",
            "QAQC tolerances (section list)": "admin-qaqc",
            "Workflows (section list)": "admin-workflows",
            "Reference data (section list)": "admin-reference",
            "Users (section list)": "admin-users",
            "Roles and permissions (section list)": "admin-roles",
            "Audit log (section list)": "admin-audit",
            "Reset demonstration tenant": "admin-reset-tenant-dialog",
        },
        "facts_js": [ACCESS_SETTINGS, unsaved(SETTINGS_SAVED), TOAST],
    },
    {
        "id": "admin-price-deck",
        "match": {"url_contains": "#/admin/price-deck"},
        "name": "Price deck and cut-offs (Administration)",
        "what": ("Tenant-wide table with one row per commodity: its price in the deck's currency and unit, and the default cut-off grade "
                 "with its grade unit and assay method. Prices value resource estimates; default cut-offs decide which assay intervals "
                 "count as intercepts. Saving writes a new deck dated today and applies to every user. Changing values needs admin.write "
                 "(System Administrator); other roles see the values greyed out."),
        "not_here": ("Commodities themselves (codes, deposit styles, units): Reference data. "
                     "Valuing a particular resource estimate with the deck: Resources (View in Resources). The cut-off of one "
                     "estimate or one scenario: that record's own page."),
        "leads_to": {"View in Resources": "resources price deck (Resources section)",
                     "Reference data (section list)": "admin-reference"},
        "facts_js": [ACCESS_FORM, unsaved(PRICE_SAVED), TOAST],
    },
    {
        "id": "admin-qaqc",
        "match": {"url_contains": "#/admin/qaqc"},
        "name": "QAQC tolerances (Administration)",
        "what": ("Tenant-wide quality-control limits applied when laboratory results are imported for every batch: the certified "
                 "reference material (standard) tolerance in standard deviations, the blank threshold as a multiple of the detection "
                 "limit, the field duplicate HARD limit in percent, and the minimum insertion rate of control samples. Each field has "
                 "an allowed range. Changing them needs admin.write (System Administrator)."),
        "not_here": ("Reviewing a particular batch's QAQC failures, or accepting or re-assaying it: the batch's page in Assays. Commodity cut-offs: "
                     "Price deck and cut-offs. Laboratories: Reference data."),
        "leads_to": {"Assays (top navigation)": "assays section"},
        "facts_js": [ACCESS_FORM, unsaved(QAQC_SAVED), TOAST],
    },
    {
        "id": "admin-workflows",
        "match": {"url_contains": "#/admin/workflows"},
        "name": "Workflows (Administration)",
        "what": ("Read-only list of the tenant's approval workflow definitions: each workflow's name, type code, what it applies to, "
                 "its chain of steps with the owning role of each, the total service level (SLA) and how many requests are pending. "
                 "Each workflow name opens a panel with its steps, owning roles and per-step SLA."),
        "not_here": ("Changes to workflow definitions: the product's support team, under a change request. "
                     "Individual approval requests (approving, rejecting, commenting, seeing who a step waits on): Approvals in the "
                     "top navigation. The role that decides stage gates: a field on System settings."),
        "leads_to": {"A workflow name in the table": "admin-workflow-dialog"},
        "facts_js": [TOAST],
    },
    {
        "id": "admin-reference",
        "match": {"url_contains": "#/admin/reference"},
        "name": "Reference data (Administration)",
        "what": ("Read-only lookup lists used across the tenant: laboratories (code, name, location, accreditation, quoted turnaround, "
                 "status), cost codes (code, name, category) and commodities (code, name, deposit style, grade and metal units, hole "
                 "types, assay method). Its only controls are the section list."),
        "not_here": ("Prices and default cut-offs per commodity: Price deck and cut-offs. Sending samples to a laboratory: "
                     "Assays; spending against a cost code: programmes and budgets."),
        "leads_to": {"Price deck and cut-offs (section list)": "admin-price-deck"},
        "facts_js": [],
    },
    {
        "id": "admin-users",
        "match": {"url_contains": "#/admin/users"},
        "name": "Users (Administration)",
        "what": ("The tenant's user accounts: name, role, title, email, team, location with time zone, status (active or inactive) and "
                 "last sign-in, with a header count of accounts, active accounts and the single sign-on provider. Add user opens a form "
                 "for a new account; each row's Edit opens the same form for that account, where its role can be changed or the account "
                 "deactivated. Deactivated users keep their history; approval steps assigned to them pass to their role. Needs user.manage "
                 "(System Administrator), whose view carries Add user and Edit; other roles see the list only. The table is wider than a "
                 "narrow window, so the Edit column can sit off the right edge."),
        "not_here": ("What each role is allowed to do: Roles and permissions (fixed matrix). Your own profile, "
                     "preferences and notification settings: the account menu. Who did what: the Audit log."),
        "leads_to": {"Add user": "admin-add-user-dialog", "Edit (on a row)": "admin-edit-user-dialog",
                     "Roles and permissions (section list)": "admin-roles"},
        "facts_js": [ACCESS_USERS, USERS_STATE, TOAST],
    },
    {
        "id": "admin-roles",
        "match": {"url_contains": "#/admin/roles"},
        "name": "Roles and permissions (Administration)",
        "what": ("Read-only permission matrix: one row per permission (named area.action), one column per role "
                 "(EXM Exploration Manager, PGEO Project Geologist, DBGEO Database Geologist, LOG Field Logistics Coordinator, FIN Finance "
                 "Controller, TEN Tenure & Permitting Officer, SYS System Administrator), a dot where the role holds it; below it a card "
                 "per role with its permission count and the users who hold it. Its only controls are the section list."),
        "not_here": ("Giving a person a different role: that user's Edit form on Users. The matrix itself: fixed in this release, "
                     "kept by the product's support team."),
        "leads_to": {"Users (section list)": "admin-users"},
        "facts_js": [],
    },
    {
        "id": "admin-audit",
        "match": {"url_contains": "#/admin/audit"},
        "name": "Audit log (Administration)",
        "what": ("Read-only, paged history of every action in the tenant, newest first: when (UTC), user, action code (named "
                 "record.action), the record it touched and a detail line. A text box filters by action, record "
                 "id or detail; a User list filters by who acted; column headers sort; pager buttons move through pages of 100. The "
                 "header shows how many entries match and the retention period."),
        "not_here": ("The log is a permanent record. Looking at or changing the record an entry mentions: that record's own page in its "
                     "section. Comments on a record: the record itself. Retention: System settings."),
        "leads_to": {},
        "facts_js": [AUDIT_STATE],
    },
    # ------------------------------------------------ overlays (native <dialog> opened modally)
    {
        "id": "admin-reset-tenant-dialog",
        "layer": "overlay",
        "match": {"selector": on("#/admin") + ' dialog.dlg[open][aria-label="Reset the demonstration tenant"]'},
        "name": "Reset the demonstration tenant dialog",
        "what": ("Confirmation for discarding every change made in this browser: users, settings, approvals, comments and scenarios all "
                 "return to the seeded demonstration data, permanently. The reset needs the 'I understand' box ticked."),
        "not_here": ("The reset covers the whole tenant at once; a single change or record is corrected on that record's own page. "
                     "Leaving without resetting: Cancel or the close cross."),
        "facts_js": [DIALOG_FORM],
    },
    {
        "id": "admin-workflow-dialog",
        "layer": "overlay",
        "match": {"selector": on("#/admin/workflows") + " dialog.dlg[open]"},
        "name": "Workflow definition panel",
        "what": ("Read-only view of one approval workflow: what it applies to, its steps in order with the role that owns each and the "
                 "SLA of each step."),
        "not_here": ("Changes to workflow definitions: the product's support team. Individual requests "
                     "that follow this workflow: Approvals."),
        "facts_js": [DIALOG_NAME],
    },
    {
        "id": "admin-add-user-dialog",
        "layer": "overlay",
        "match": {"selector": on("#/admin/users") + ' dialog.dlg[open][aria-label="Add a user"]'},
        "name": "Add a user dialog",
        "what": ("Form for creating a new user account: full name, role, title, email, team, location, time zone and whether the account "
                 "is active. Full name and Email are required; Save creates the account for the whole tenant."),
        "not_here": ("Changing an existing account: the Edit form on that user's row. What a role may do: Roles and "
                     "permissions."),
        "facts_js": [DIALOG_FORM],
    },
    {
        "id": "admin-edit-user-dialog",
        "layer": "overlay",
        "match": {"selector": on("#/admin/users") + ' dialog.dlg[open][aria-label^="Edit "]'},
        "name": "Edit user dialog",
        "what": ("Form for changing one existing user account, titled with the account's name: full name, role, title, email, team, "
                 "location, time zone and the Active tick box. Unticking Active deactivates the account; its history is kept and "
                 "approval steps assigned to it pass to its role. Full name and Email are required."),
        "not_here": ("Creating a new account: Add user. Your own profile and preferences: the account menu."),
        "facts_js": [DIALOG_FORM],
    },
]

# ---------------------------------------------------------------- controls
C = []


def add(key, region, what, not_for, **extra):
    entry = {"key": key, "region": region, "what": what, "not_for": not_for}
    entry.update(extra)
    C.append(entry)


# Section list ("In this section") shared by every admin page
NAV = "Administration section list (left)"
subnav = [
    ("System", {"text": "System settings"}, "Opens System settings: tenant, security and auto-numbering configuration for the whole tenant.",
     "Not your personal preferences (account menu). Not the top-bar Admin link, which opens this same page from anywhere."),
    ("System", {"text": "Price deck and cut-offs"}, "Opens the tenant-wide commodity price deck and default cut-off grades.",
     "Not for valuing one resource estimate (Resources)."),
    ("System", {"text": "QAQC tolerances"}, "Opens the tenant-wide QAQC pass/fail limits applied on results import.",
     "Not for reviewing one batch's QAQC results (Assays)."),
    ("System", {"text_regex": r"^Workflows( \d+)?$"}, "Opens the read-only list of approval workflow definitions; the number is how many workflows exist.",
     "Not the list of approval requests waiting on someone (Approvals in the top navigation)."),
    ("System", {"text": "Reference data"}, "Opens the read-only lists of laboratories, cost codes and commodities.",
     "Not where prices or cut-offs are changed (Price deck and cut-offs)."),
    ("Access", {"text_regex": r"^Users( \d+)?$"}, "Opens the list of user accounts, where accounts are added, edited or deactivated; the number is how many accounts exist.",
     "Not your own profile (account menu). Not the permission matrix (Roles and permissions)."),
    ("Access", {"text_regex": r"^Roles and permissions( \d+)?$"}, "Opens the read-only permission matrix and who holds each role; the number is how many roles exist.",
     "Not where a person's role is changed (edit the user on Users)."),
    ("Access", {"text_regex": r"^Audit log( \d+)?$"}, "Opens the tenant-wide history of every action; the number is how many entries exist.",
     "Changing records; the log is a permanent history."),
]
for sec, k, what, nf in subnav:
    add({"row_label": sec, **k}, NAV + f", {sec} group", what, nf,
        note="Same entry on every Administration page; row_label is the group heading (System or Access) the harness derives.")

# System settings
P = "admin-settings"
R_T = "System settings, Tenant panel"
R_S = "System settings, Security panel"
add({"page": P, "text": "Reset demonstration tenant"}, "System settings, page header",
    EVERYONE + "Opens a confirmation to discard every change made in this browser and return the whole demonstration tenant to its seeded data.",
    "Undoing one edit or discarding unsaved changes on this form (leaving the page without Save does that); the reset covers users, settings, approvals, comments and scenarios alike.")
add({"page": P, "row_label": "Tenant name"}, R_T, EVERYONE + "The organisation name shown across the application for every user.",
    "Not the tenant code, which is fixed and shown in the page header.")
add({"page": P, "row_label": "Fiscal year starts (MM-DD)"}, R_T,
    EVERYONE + "Month and day the fiscal year begins, written MM-DD; budgets and fiscal-year figures are cut on it.",
    "Not a date for any one budget or programme.")
add({"page": P, "row_label": "Base currency"}, R_T,
    EVERYONE + "The tenant's reporting currency for budgets and valuations.",
    "Not the unit of a commodity price (set per commodity on Price deck and cut-offs).", options=["USD", "CAD", "AUD"])
add({"page": P, "row_label": "Number locale"}, R_T,
    EVERYONE + "How numbers are formatted (decimal and thousands separators) across the tenant.",
    "Not your personal date or unit preferences (account menu, Preferences).",
    options=["en-CA", "en-US", "en-AU", "en-GB", "es-CL", "fi-FI"])
add({"page": P, "row_label": "Variance threshold, %"}, R_T,
    EVERYONE + "Percentage by which a programme's spend forecast may exceed its approved budget before a budget-variance approval request is raised.",
    "Not a budget amount, and not an approval of any variance (Approvals).")
add({"page": P, "row_label": "Stage-gate approver role"}, R_T,
    EVERYONE + "Which role decides stage-gate approvals for every project.",
    "A person, or a user's own role (each user's Edit form on Users).",
    options=["Exploration Manager", "Project Geologist", "Database Geologist", "Field Logistics Coordinator",
             "Finance Controller", "Tenure & Permitting Officer", "System Administrator"])
add({"page": P, "row_label": "Session timeout, minutes"}, R_S,
    EVERYONE + "Minutes of inactivity before any user is signed out (allowed 5 to 480).",
    "Not the audit retention period.")
add({"page": P, "row_label": "Minimum password length"}, R_S,
    EVERYONE + "Shortest password any user may set (allowed 8 to 64).",
    "A password itself; passwords are managed in the company identity provider or by each user.")
add({"page": P, "row_label": "Single sign-on provider"}, R_S,
    EVERYONE + "The identity provider users sign in through, or none.",
    "Not the multi-factor requirement, which is its own tick box.", options=["none", "Entra ID", "Okta"])
add({"page": P, "role": "checkbox", "text": "Require multi-factor authentication"}, R_S,
    EVERYONE + "Tick box: when ticked, every user must use multi-factor authentication to sign in.",
    "Not the single sign-on provider list next to it.",
    note="Keyed on its own label: the harness gives this box the wrong row_label (Session timeout).")
add({"page": P, "row_label": "Audit retention, days"}, R_S,
    EVERYONE + "How many days audit-log entries are kept (at least 90).",
    "Not the session timeout, and not a filter on the Audit log page.")
add({"page": P, "row_label": "Attachment limit, MB"}, R_S,
    EVERYONE + "Largest file, in megabytes, anyone may attach to a record.",
    "Not the audit retention.")
add({"page": P, "text": "Save settings"}, "System settings, foot of the form",
    EVERYONE + "Saves every field on this page at once for all users and confirms with a 'System settings saved' message. Changes on the page take effect when it is pressed.",
    "Saving the price deck or QAQC tolerances (each page has its own Save). Takes effect once every field is valid (fiscal year start in MM-DD form, numbers within their ranges). Shown to roles with admin.write.")

# Price deck
P = "admin-price-deck"
add({"page": P, "role": "spinbutton", "text_regex": r" price$"}, "Price deck table, Price column",
    EVERYONE + "Price of this row's commodity, in the row's unit.",
    "The cut-off grade (the Default cut-off field on the same row). Kept once Save is pressed.",
    note="Generic: one entry for the price field of every commodity row; the row's commodity is in the field's own label.")
add({"page": P, "role": "spinbutton", "text_regex": r" cut-off$"}, "Price deck table, Default cut-off column",
    EVERYONE + "Default cut-off grade of this row's commodity, in the row's grade unit.",
    "The price (the Price field on the same row), or a cut-off for one estimate or scenario (that record's page). Kept once Save is pressed.",
    note="Generic: one entry for the cut-off field of every commodity row.")
add({"page": P, "text": "Save"}, "Price deck, foot of the table",
    EVERYONE + "Saves every price and cut-off on this page for all users, stamping the deck with today's date, and confirms with a message.",
    "Saving System settings or QAQC tolerances (each has its own Save). Shown to roles with admin.write.")
add({"page": P, "text": "View in Resources"}, "Price deck, page header",
    "Leaves Administration for the price deck view in the Resources section, where the deck is applied to resource estimates.",
    "Saving what is typed on this page (Save at the foot of the table).")

# QAQC
P = "admin-qaqc"
R = "QAQC tolerances form"
add({"page": P, "row_label": "Certified reference material tolerance, σ"}, R,
    EVERYONE + "How many standard deviations from its certified value a standard may read before it fails, on every imported batch (allowed 1 to 5, in steps of 0.5).",
    "Not the blank threshold or the duplicate limit.")
add({"page": P, "row_label": "Blank threshold, × detection limit"}, R,
    EVERYONE + "Multiple of the method detection limit above which a coarse blank fails (allowed 1 to 20).",
    "Not the standards tolerance.")
add({"page": P, "row_label": "Field duplicate HARD limit, %"}, R,
    EVERYONE + "Half absolute relative difference, in percent, above which a field duplicate pair above cut-off fails (allowed 5 to 50).",
    "Not the insertion rate.")
add({"page": P, "row_label": "Minimum insertion rate, %"}, R,
    EVERYONE + "Lowest share of control samples a batch may carry before it is flagged on import (allowed 1 to 20).",
    "Not a pass/fail limit for a single sample.")
add({"page": P, "text": "Save tolerances"}, "QAQC tolerances, foot of the form",
    EVERYONE + "Saves the four tolerances for every future results import and confirms with a message.",
    "Re-checking batches already imported; the tolerances apply from the next import. Takes effect once every value is within its allowed range. Shown to roles with admin.write.")

# Workflows
P = "admin-workflows"
WF = r"^(Programme approval|Budget variance|Stage-gate decision|Land access agreement|Work permit|Resource estimate release|Tenement renewal|Purchase order)$"
add({"page": P, "role": "button", "text_regex": WF}, "Workflows table, Workflow column",
    "Opens a read-only panel showing this workflow's steps, the role owning each step and each step's SLA.",
    "Editing the workflow (the product's support team) or opening a pending request (Approvals).",
    note="Generic: one entry for every workflow-name button; the regex lists the release's eight workflow definitions (configuration, not records).")
add({"page": "admin-workflow-dialog", "text": "Close dialog"}, "Workflow definition panel, top-right cross",
    "Closes the workflow panel and returns to the Workflows list.", "Editing the workflow.")

# Users
P = "admin-users"
add({"page": P, "text": "Add user"}, "Users, page header",
    "ADMINISTRATION: Opens the form for creating a new user account in the tenant.",
    "Changing an existing account (Edit on that account's row). Shown to roles with user.manage.")
add({"page": P, "role": "button", "text": "Edit"}, "Users table, Actions column (far right)",
    "ADMINISTRATION: Opens this row's account in the edit form.",
    "Creating an account (Add user). Shown to roles with user.manage; the column can sit off the right edge of a narrow window.",
    note="Generic: one entry for every row's Edit button; the row's user is the name at the start of the same row.")
add({"page": P, "text_regex": r"^Sort by "}, "Users table, column header",
    "Sorts the user list by this column; pressing again reverses the order.",
    "Filtering or changing accounts.",
    note="Generic: every sortable column header (Name, Role, Team, Status, Last sign-in).")

# User dialogs (Add and Edit share one form)
for oid, dname, save_what in (
        ("admin-add-user-dialog", "Add a user dialog",
         "ADMINISTRATION: Creates the new account with these values, closes the dialog and confirms with a message."),
        ("admin-edit-user-dialog", "Edit user dialog",
         "ADMINISTRATION: Saves the changes to this account, closes the dialog and confirms with a message.")):
    fields = [
        ("Full name", "The person's full name as shown across the tenant. Required.", "Not the email address."),
        ("Role", "The role that decides what this person may do and which approval steps reach them.",
         "Not the Title, which is a free-text job title with no permissions attached."),
        ("Title", "Free-text job title shown with the person's name.", "The Role, which is what sets permissions."),
        ("Email", "Sign-in and notification email address. Required and must look like an email address.", "Not the full name."),
        ("Team", "Team the person belongs to, free text.", "Not the role."),
        ("Location", "Office or site the person works from, free text.", "Not the time zone."),
        ("Time zone", "The person's time zone as a region/city name, used for their times and dates.", "Not the location."),
    ]
    for label, what, nf in fields:
        extra = {}
        if label == "Role":
            extra["options"] = ["Exploration Manager", "Project Geologist", "Database Geologist", "Field Logistics Coordinator",
                                "Finance Controller", "Tenure & Permitting Officer", "System Administrator"]
        add({"page": oid, "row_label": label}, dname + ", form", what, nf, **extra)
    add({"page": oid, "role": "checkbox", "text": "Active"}, dname + ", form",
        "Tick box: ticked means the account can sign in and receive work; unticked deactivates it, keeping its history and passing its approval steps to its role.",
        "Deleting the account; a deactivated account keeps its history.")
    add({"page": oid, "text": "Save"}, dname + ", bottom right", save_what,
        "Changing the permissions matrix (Roles and permissions). Takes effect once Full name and a well-formed Email are filled in.")
    add({"page": oid, "text": "Cancel"}, dname + ", bottom", "Closes the dialog and discards what was typed in it.", "Saving (Save).")
    add({"page": oid, "text": "Close dialog"}, dname + ", top-right cross", "Closes the dialog and discards what was typed in it, like Cancel.", "Saving (Save).")

# Reset dialog
O = "admin-reset-tenant-dialog"
add({"page": O, "role": "checkbox", "text": "I understand this cannot be undone."}, "Reset demonstration tenant dialog",
    "Tick box acknowledging that the reset is permanent; Reset tenant takes effect once it is ticked.", "Resetting by itself (Reset tenant does that).")
add({"page": O, "text": "Reset tenant"}, "Reset demonstration tenant dialog, bottom right",
    EVERYONE + "Discards every change made in this browser and restores the seeded demonstration data for users, settings, approvals, comments and scenarios, permanently.",
    "Leaving the dialog (Cancel), or correcting a single change (that record's own page).")
add({"page": O, "text": "Cancel"}, "Reset demonstration tenant dialog, bottom", "Closes the dialog and leaves the tenant as it is.", "Resetting (Reset tenant).")
add({"page": O, "text": "Close dialog"}, "Reset demonstration tenant dialog, top-right cross", "Closes the dialog and leaves the tenant as it is.", "Resetting (Reset tenant).")

# Audit
P = "admin-audit"
add({"page": P, "row_label": "Find"}, "Audit log, filter bar",
    "Filters the log as you type to entries whose action code, record id or detail contains the text.",
    "Tenant-wide search (the top-bar search box) or filtering by who acted (the User list).")
add({"page": P, "row_label": "User"}, "Audit log, filter bar",
    "Limits the log to actions by one user, or Everyone.",
    "Changing a user account (Users).")
add({"page": P, "text_regex": r"^Sort by "}, "Audit log table, column header",
    "Sorts the log by this column; pressing again reverses the order.",
    "Filtering entries (the Find box and User list).",
    note="Generic: every sortable column header (When, User, Action, Record).")
for label, what in (("First", "Shows the first page of matching entries (the newest, when sorted by time)."),
                    ("Previous", "Shows the previous page of 100 entries."),
                    ("Next", "Shows the next page of 100 entries."),
                    ("Last", "Shows the last page of matching entries.")):
    add({"page": P, "role": "button", "text": label}, "Audit log, pager below the table", what,
        "Changing the filter or sorting. Disabled at the matching end of the list.")

atlas = {
    "app": "ADIT",
    "version": "2026-09-22",
    "selectors": {"dialog": ["dialog[open]"]},
    "pages": pages,
    "controls": C,
}
with open(OUT, "w") as f:
    json.dump(atlas, f, indent=2, ensure_ascii=False)
    f.write("\n")
print(len(pages), "pages;", len(C), "controls")

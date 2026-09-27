"""Generate jev-atlas/atlas/parts/programmes.json (Programmes area fragment)."""
# Copied from the area author's scratch directory on 2026-09-22 by the atlas merger;
# paths rewritten to be relative to this file and to $JEV_CLONE (the harness copy).
import os as _os, pathlib as _pl
_PARTS = _pl.Path(_os.environ.get("ADIT_PARTS_DIR") or _pl.Path(__file__).resolve().parents[2] / "atlas" / "parts")
_HARNESS = _os.environ.get("JEV_CLONE", str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'vendor' / 'jev-ultrafast')).rstrip("/") + "/jev_ultrafast/"

import json

OUT = str(_PARTS / "programmes.json")

# ---------------------------------------------------------------- shared JS
TOAST_FACT = (
    "(() => { const t=[...document.querySelectorAll('.toasts .toast')]"
    ".map(x=>x.innerText.trim().replace(/\\s+/g,' ')).filter(Boolean);"
    " return t.length ? 'Notice on screen: ' + t.join(' | ') : null })()"
)

LIST_FACT = (
    "(() => { const m=document.querySelector('main .head .meta'); if (!m) return null;"
    " const q=new URLSearchParams((location.hash.split('?')[1]||''));"
    " const ct=document.querySelector('main .filters .ct');"
    " return 'Programme list showing: ' + m.innerText.trim() + '; type filter: ' + (q.get('type')||'all types')"
    " + (ct ? '; ' + ct.innerText.trim() : '') })()"
)

# Every field of a form as "label = value", marking the ones the app flags.
FORM_FACT = (
    "(() => { const root=document.querySelector(%ROOT%); if (!root) return null;"
    " const parts=[...root.querySelectorAll('label.field')].map(l=>{"
    " const name=(l.querySelector('span')?.textContent||'').trim();"
    " const c=l.querySelector('input,select,textarea'); if (!c || !name) return null;"
    " const v=c.tagName==='SELECT' ? (c.selectedOptions[0]?.textContent||'').trim() : c.value;"
    " const err=l.querySelector('.error')?.textContent.trim();"
    " return name + ' = ' + (v==='' ? '(empty)' : JSON.stringify(v)) + (c.required ? ' (required)' : '') + (err ? ' [invalid: ' + err + ']' : '');"
    " }).filter(Boolean);"
    " const notice=[...root.querySelectorAll('.notice')].map(n=>n.innerText.trim()).filter(Boolean);"
    " return '%LABEL%: ' + parts.join('; ') + (notice.length ? '. Refused: ' + notice.join(' ') : '') })()"
)


def form_fact(root_selector, label):
    return FORM_FACT.replace("%ROOT%", json.dumps(root_selector)).replace("%LABEL%", label)


HEADER_FACT = (
    "(() => { const h=document.querySelector('main .head h1'); if (!h) return null;"
    " const id=h.querySelector('.id')?.textContent.trim()||'';"
    " const name=[...h.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join('').trim();"
    " const phase=document.querySelector('main .head .chip[data-status]')?.textContent.trim()||'?';"
    " const meta=[...document.querySelectorAll('main .head .meta > span:not(.chip)')].map(s=>s.textContent.trim()).filter(Boolean);"
    " const acts=[...document.querySelectorAll('main .head .actions button')].map(b=>b.textContent.trim().replace(/\\s+/g,' '));"
    " const tab=document.querySelector('main nav.tabs a[aria-current=page]');"
    " return 'Programme in view: ' + id + ' ' + name + ' | phase: ' + phase + ' | ' + meta.join(' | ')"
    " + ' | header actions: ' + (acts.length ? 'offered to you: ' + acts.join(', ') : 'shown according to the signed-in role and the programme phase; to act with another role, switch user in the account menu to a person who holds it (People and roles lists who holds each role)')"
    " + (tab ? ' | tab: ' + tab.firstChild.textContent.trim() : '') })()"
)

# Date inputs are not offered by the page reader (input[type=date] has no role),
# so each is a virtual fill target that writes through the native setter React listens to.
DATE_VC = (
    "(() => {{ const root=document.querySelector({root}); if (!root) return [];"
    " const spec={spec};"
    " const out=[];"
    " for (const s of spec) {{"
    "  const l=[...root.querySelectorAll('label.field')].find(x=>(x.querySelector('span')?.textContent||'').trim()===s.field);"
    "  const i=l && l.querySelector('input[type=date]'); if (!i) continue;"
    "  out.push({{id:'date:'+s.field, label:s.field, row_label:s.field, region:s.region, what:s.what, not_for:s.not_for,"
    "   current_value:i.value,"
    "   set:'(v) => {{ const root=document.querySelector('+JSON.stringify({root})+'); if (!root) return false;"
    " const l=[...root.querySelectorAll(\"label.field\")].find(x=>(x.querySelector(\"span\")?.textContent||\"\").trim()==='+JSON.stringify(s.field)+');"
    " const i=l && l.querySelector(\"input[type=date]\"); if (!i) return false;"
    " let t=String(v).trim(); if (!/^\\\\d{{4}}-\\\\d{{2}}-\\\\d{{2}}$/.test(t)) {{ const d=new Date(t); if (isNaN(d)) return false;"
    " t=d.getFullYear()+\"-\"+String(d.getMonth()+1).padStart(2,\"0\")+\"-\"+String(d.getDate()).padStart(2,\"0\"); }}"
    " const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,\"value\").set; setter.call(i,t);"
    " i.dispatchEvent(new Event(\"input\",{{bubbles:true}})); i.dispatchEvent(new Event(\"change\",{{bubbles:true}}));"
    " return i.value===t; }}'}});"
    " }}"
    " return out; }})()"
)


def date_vc(root_selector, spec):
    return DATE_VC.format(root=json.dumps(root_selector), spec=json.dumps(spec))


TYPE_FILTER_VC = (
    "(() => { const pills=document.querySelector('main .filters .pills'); if (!pills) return [];"
    " const q=new URLSearchParams((location.hash.split('?')[1]||''));"
    " const types=[...pills.querySelectorAll('label')].map(l=>l.textContent.trim());"
    " return [{id:'filter:type', label:'Type filter', row_label:'Type', region:'Programme list, filter bar above the table',"
    " what:'Narrows the programme list to one programme type. Write one of: ' + types.join(', ') + ', or \"all\" to clear the type filter. This field sets the type pills.',"
    " not_for:'Choosing which phase group is listed (in the field, in planning, complete, all), which is the left column; changing the type of a programme.',"
    " current_value:q.get('type')||'all',"
    " set:'(v) => { const pills=document.querySelector(\"main .filters .pills\"); if (!pills) return false;"
    " const want=String(v).trim().toLowerCase(); const labels=[...pills.querySelectorAll(\"label\")];"
    " const cur=new URLSearchParams((location.hash.split(\"?\")[1]||\"\")).get(\"type\");"
    " if ([\"all\",\"any\",\"none\",\"\",\"clear\"].includes(want)) { if (!cur) return true; const a=labels.find(l=>l.textContent.trim()===cur); if (!a) return false; a.click(); return true; }"
    " const hit=labels.find(l=>l.textContent.trim().toLowerCase()===want); if (!hit) return false;"
    " if (cur===hit.textContent.trim()) return true; hit.click(); return true; }'}]; })()"
)

# ---------------------------------------------------------------- pages
DETAIL_TABS = ["programme-overview", "programme-crew", "programme-logistics", "programme-holes", "programme-approval"]
LEFT_COL_PAGES = ["programmes-list", "programmes-new", "programmes-schedule", "programmes-rigs", "programmes-camps",
                  "programmes-crew-rotations"] + DETAIL_TABS

LEADS_LEFT = {
    "In the field / In planning / Complete / All programmes (left column)": "programmes-list",
    "Schedule (left column)": "programmes-schedule",
    "Rigs (left column)": "programmes-rigs",
    "Camps (left column)": "programmes-camps",
    "Crew rotations (left column)": "programmes-crew-rotations",
}
LEADS_DETAIL = {
    "Overview tab": "programme-overview",
    "Crew tab": "programme-crew",
    "Logistics tab": "programme-logistics",
    "Drillholes tab": "programme-holes",
    "Approval tab": "programme-approval",
    "Move to <next phase> (header)": "programme-move-dialog",
    "Assign crew (header)": "programme-assign-crew-dialog",
    "Project name under the title": "project page (Projects area)",
}
ID_TAIL = r"(\?[^#]*)?$"
DETAIL_ID = r"#/programmes/(?!(new|schedule|rigs|camps|crew)(\?|/|$))[^/?#]+"

pages = [
    {
        "id": "programmes-list",
        "match": {"url_regex": r"#/programmes" + ID_TAIL},
        "name": "Programmes list",
        "what": ("The register of programmes: units of field or study work on a project (drilling, geophysics, geochem, "
                 "mapping, metallurgy, environmental baseline), one row each with project, type, phase, dates, metres, budget, "
                 "spend, lead and rig. The left column chooses which phase group is listed (in the field = mobilising to "
                 "demobilising, which is the default; in planning = draft to approved; complete; all). The type filter narrows "
                 "by programme type. Column headers sort. New programme starts the create form."),
        "not_here": ("Changing a programme's phase, crew, logistics or approval: that programme's own page (its id or name "
                     "in the row). A timeline of all programmes is Schedule; contracted rigs, camps and every crew rotation "
                     "across the tenant have their own pages under Resources in the left column. Drillhole detail lives in Drilling; "
                     "approval decisions are taken in Approvals."),
        "leads_to": {"New programme": "programmes-new", "Programme id or name in a row": "programme-overview",
                     "Project name in a row": "project page (Projects area)", **LEADS_LEFT},
        "facts_js": [LIST_FACT, TOAST_FACT],
        "virtual_controls_js": TYPE_FILTER_VC,
    },
    {
        "id": "programmes-new",
        "match": {"url_regex": r"#/programmes/new" + ID_TAIL},
        "name": "New programme form",
        "what": ("Creates a programme as a draft: project, type, name, objective, start and end dates, budget, and for drilling "
                 "programmes planned metres, planned holes and an optional rig. Create draft validates the form and, if it "
                 "passes, opens the new programme's page. Errors are shown under the fields, and the form stays open for correction."),
        "not_here": ("Scoping, costing and submitting for approval: later steps on the programme's own page. "
                     "Crew and logistics: the programme page, once it exists. The Start and End date fields are offered "
                     "as their own fill targets."),
        "leads_to": {"Create draft (valid form)": "programme-overview", "Cancel": "programmes-list", **LEADS_LEFT},
        "facts_js": [form_fact("main form", "New programme form"), TOAST_FACT],
        "virtual_controls_js": date_vc("main form", [
            {"field": "Start", "region": "New programme form", "what": "The programme's planned start date (YYYY-MM-DD).",
             "not_for": "The end date, which is its own field."},
            {"field": "End", "region": "New programme form", "what": "The programme's planned end date (YYYY-MM-DD).",
             "not_for": "The start date, which is its own field."},
        ]),
    },
    {
        "id": "programmes-schedule",
        "match": {"url_regex": r"#/programmes/schedule" + ID_TAIL},
        "name": "Programme schedule",
        "what": ("A read-only timeline (Gantt) of programmes across a fixed window of months, one bar per programme, coloured "
                 "as in the field, complete or planned, with today marked. Each programme's label is a link to its page."),
        "not_here": ("Programme dates: set on the programme itself. A sortable table of programmes: the "
                     "Programmes list. Crew dates: Crew rotations."),
        "leads_to": {"Programme label on a bar": "programme-overview", **LEADS_LEFT},
        "facts_js": [TOAST_FACT],
    },
    {
        "id": "programmes-rigs",
        "match": {"url_regex": r"#/programmes/rigs" + ID_TAIL},
        "name": "Rigs",
        "what": ("The contracted drill rigs: id, name, contractor, rig type, depth capacity, day rate, status (available, "
                 "assigned, maintenance, demobilised), the programme it is on and its location. Logistics staff see an Update "
                 "button per row to change a rig's status and location."),
        "not_here": ("Attaching a rig to a drilling programme: the Rig field of New programme, when that programme "
                     "is created. Camps and crew have their own pages in the left column."),
        "leads_to": {"Programme name in a row": "programme-overview", "Update (row)": "programmes-rig-update-dialog", **LEADS_LEFT},
        "facts_js": [TOAST_FACT],
    },
    {
        "id": "programmes-camps",
        "match": {"url_regex": r"#/programmes/camps" + ID_TAIL},
        "name": "Camps",
        "what": ("Read-only list of field camps: id, name, project, status (open, closed, winterised), beds, beds occupied, "
                 "whether a medic is on site, and how the camp is reached."),
        "not_here": ("Camp services for a programme (catering, housekeeping and the like) are logistics items on that programme's "
                     "Logistics tab. Who is staying is set by crew assignments on the programme's Crew tab."),
        "leads_to": {"Project name in a row": "project page (Projects area)", **LEADS_LEFT},
        "facts_js": [TOAST_FACT],
    },
    {
        "id": "programmes-crew-rotations",
        "match": {"url_regex": r"#/programmes/crew" + ID_TAIL},
        "name": "Crew rotations",
        "what": ("Every crew assignment across the tenant: person, role, programme, project, rotation from and to, and state "
                 "(upcoming, on site, ended), with a count of rotations ending soon. Paged, sortable, read-only."),
        "not_here": ("Assigning or removing crew: a programme's own Crew tab (or its Assign crew button)."),
        "leads_to": {"Programme name in a row": "programme-overview", **LEADS_LEFT},
        "facts_js": [TOAST_FACT],
    },
    {
        "id": "programme-overview",
        "match": {"url_regex": DETAIL_ID + ID_TAIL},
        "name": "Programme page, Overview tab",
        "what": ("One programme. The header shows its name and id, project, commodity, phase, type and dates, and the actions "
                 "open to you: Move to <next phase> (advances the phase one step, after a confirmation), Submit for approval "
                 "(only at costed with no approval yet; raises the programme-approval workflow and needs no confirmation), and "
                 "Assign crew. Which actions appear depends on the signed-in user's role and the programme's phase. Overview "
                 "shows budget and spend, metres, duration, crew on site and logistics cost; objective, lead, rig, camp and "
                 "approval; the phase track; and comments."),
        "not_here": ("Crew assignments, logistics items, drillholes and the approval steps: each on its own tab. Approving or "
                     "rejecting the approval request: the Approvals section. The programme's name, dates and budget: "
                     "shown in the header and summary; its phase changes with Move to in the header."),
        "leads_to": {**LEADS_DETAIL, "Rig link": "programmes-rigs", "Camp link": "programmes-camps",
                     "Approval link": "approval request (Approvals area)", **LEADS_LEFT},
        "facts_js": [HEADER_FACT, TOAST_FACT],
    },
    {
        "id": "programme-crew",
        "match": {"url_regex": DETAIL_ID + r"/crew" + ID_TAIL},
        "name": "Programme page, Crew tab",
        "what": ("The programme's crew assignments: person, role on this programme, rotation from and to, days, and state "
                 "(upcoming, on site, ended). Assign crew adds a person for a rotation; Remove on a row deletes that assignment "
                 "at once."),
        "not_here": ("Crew across all programmes is Crew rotations in the left column. Camp beds are on Camps."),
        "leads_to": {**LEADS_DETAIL, "Assign crew (tab)": "programme-assign-crew-dialog", **LEADS_LEFT},
        "facts_js": [HEADER_FACT, TOAST_FACT],
    },
    {
        "id": "programme-logistics",
        "match": {"url_regex": DETAIL_ID + r"/logistics" + ID_TAIL},
        "name": "Programme page, Logistics tab",
        "what": ("The programme's logistics items: charters, camp services, fuel, permits, equipment, medical cover and freight, "
                 "each with supplier, scheduled date, cost and status (requested, booked, confirmed, delivered, cancelled). "
                 "Add item creates one; Edit on a row changes one."),
        "not_here": ("Purchase orders above the delegated limit are approved in Approvals. Rigs and camps themselves are "
                     "listed under Resources in the left column."),
        "leads_to": {**LEADS_DETAIL, "Add item / Edit (row)": "programme-logistics-item-dialog", **LEADS_LEFT},
        "facts_js": [HEADER_FACT, TOAST_FACT],
    },
    {
        "id": "programme-holes",
        "match": {"url_regex": DETAIL_ID + r"/holes" + ID_TAIL},
        "name": "Programme page, Drillholes tab",
        "what": ("Read-only table of the drillholes in this programme: hole id, project, programme, hole type, status, collar "
                 "coordinates, azimuth, dip, planned and actual depth, best intercept and completion date."),
        "not_here": ("Logging, sampling and hole detail: the Drilling area (each hole id leads there). Assay results: Assays."),
        "leads_to": {**LEADS_DETAIL, "Hole id in a row": "drillhole page (Drilling area)", **LEADS_LEFT},
        "facts_js": [HEADER_FACT, TOAST_FACT],
    },
    {
        "id": "programme-approval",
        "match": {"url_regex": DETAIL_ID + r"/approval" + ID_TAIL},
        "name": "Programme page, Approval tab",
        "what": ("The programme-approval workflow for this programme, read-only: its status and the three steps (Technical "
                 "review, Budget check, Manager approval) with who holds each and when it was decided or is due. Says so when "
                 "the programme has not been submitted."),
        "not_here": ("Submitting: Submit for approval in the header (at costed). Deciding a step: the Approvals section, "
                     "reached through the request id link."),
        "leads_to": {**LEADS_DETAIL, "Approval request id": "approval request (Approvals area)", **LEADS_LEFT},
        "facts_js": [HEADER_FACT, TOAST_FACT],
    },
    # ------------------------------------------------------------ overlays
    {
        "id": "programme-move-dialog",
        "layer": "overlay",
        "match": {"selector": "dialog[open][aria-label^=\"Move PRG-\"]"},
        "name": "Move programme to next phase (confirmation)",
        "what": ("Confirms moving this programme one phase forward, stating from which phase to which. Confirm applies it at "
                 "once; moving to complete also closes the programme's ledger."),
        "not_here": ("Phases advance one step at a time, to the phase named in the dialog. Costed to approved: "
                     "automatic when the approval workflow passes."),
        "facts_js": [
            "(() => { const d=document.querySelector('dialog[open][aria-label^=\"Move PRG-\"]'); if (!d) return null;"
            " return 'Dialog says: ' + d.innerText.replace(/\\s+/g,' ').replace(/Cancel Confirm$/,'').trim() })()"
        ],
    },
    {
        "id": "programme-assign-crew-dialog",
        "layer": "overlay",
        "match": {"selector": "dialog[open][aria-label^=\"Assign crew\"]"},
        "name": "Assign crew dialog",
        "what": ("Adds one person to this programme's crew for one rotation: person, role on this programme (filled from the "
                 "person's usual role, editable), rotation start and end dates (pre-filled). Assign saves it and closes the "
                 "dialog. ADIT refuses an assignment that overlaps the same person's rotation on another live programme and "
                 "says which one, leaving the dialog open."),
        "not_here": "Removing an assignment: Remove on its Crew tab row. The rotation dates are offered as their own fill targets.",
        "facts_js": [form_fact("dialog[open][aria-label^=\"Assign crew\"]", "Assign crew form")],
        "virtual_controls_js": date_vc("dialog[open][aria-label^=\"Assign crew\"]", [
            {"field": "Rotation start", "region": "Assign crew dialog",
             "what": "First day of this person's rotation on the programme (YYYY-MM-DD).",
             "not_for": "The last day, which is Rotation end."},
            {"field": "Rotation end", "region": "Assign crew dialog",
             "what": "Last day of this person's rotation on the programme (YYYY-MM-DD).",
             "not_for": "The first day, which is Rotation start."},
        ]),
    },
    {
        "id": "programme-logistics-item-dialog",
        "layer": "overlay",
        "match": {"selector": "dialog[open][aria-label=\"Add a logistics item\"], dialog[open][aria-label^=\"Edit LG-\"]"},
        "name": "Logistics item dialog (add or edit)",
        "what": ("The form for one logistics item: kind, status, description (required), supplier, scheduled date and cost. "
                 "Save stores it on this programme; in the Edit form it overwrites the item's current values."),
        "not_here": "Dropping an item: its Status set to cancelled; the item stays on record. The Scheduled date is offered as its own fill target.",
        "facts_js": [form_fact("dialog[open][aria-label=\"Add a logistics item\"], dialog[open][aria-label^=\"Edit LG-\"]",
                               "Logistics item form")],
        "virtual_controls_js": date_vc(
            "dialog[open][aria-label=\"Add a logistics item\"], dialog[open][aria-label^=\"Edit LG-\"]", [
                {"field": "Scheduled", "region": "Logistics item dialog",
                 "what": "The date the item is scheduled for: flight, delivery, service start (YYYY-MM-DD).",
                 "not_for": "The cost or status of the item, which are their own fields."}]),
    },
    {
        "id": "programmes-rig-update-dialog",
        "layer": "overlay",
        "match": {"selector": "dialog[open][aria-label^=\"Update RIG-\"]"},
        "name": "Update rig dialog",
        "what": "Changes one rig's status (available, assigned, maintenance, demobilised) and its location text. Save applies it.",
        "not_here": "Which programme a rig is on: set by that programme when it is created. Contractor, capacity and day rate: shown on the Rigs list, outside this dialog.",
        "facts_js": [form_fact("dialog[open][aria-label^=\"Update RIG-\"]", "Update rig form")],
    },
]

# ---------------------------------------------------------------- controls
C = []


def add(key, region, what, not_for=None, note=None, options=None):
    e = {"key": key, "region": region, "what": what}
    if not_for:
        e["not_for"] = not_for
    if options:
        e["options"] = options
    if note:
        e["note"] = note
    C.append(e)


# Left column (appears on every Programmes-area page).
LEFT = "Programmes left column"
add({"row_label": "Programmes", "role": "link", "text_regex": r"^In the field\b"}, LEFT,
    "Lists programmes that are in the field: mobilising, in progress or demobilising. The count is how many.",
    "Planned or finished programmes (In planning, Complete, All programmes).",
    note="Key uses the left-column group heading as row_label; the count in the text changes.")
add({"row_label": "Programmes", "role": "link", "text_regex": r"^In planning\b"}, LEFT,
    "Lists programmes still being planned: draft, scoped, costed or approved.",
    "Programmes already in the field (In the field) or finished (Complete).")
add({"row_label": "Programmes", "role": "link", "text_regex": r"^Complete\b"}, LEFT,
    "Lists finished programmes whose ledger is closed.",
    "Moving a programme to complete; that is Move to complete on the programme page.")
add({"row_label": "Programmes", "role": "link", "text_regex": r"^All programmes\b"}, LEFT,
    "Lists every programme in every phase, including cancelled ones.",
    "Creating a programme (New programme).")
add({"row_label": "Resources", "role": "link", "text_regex": r"^Schedule\b"}, LEFT,
    "Opens the timeline of all programmes.", "Crew rotation dates (Crew rotations).")
add({"row_label": "Resources", "role": "link", "text_regex": r"^Rigs\b"}, LEFT,
    "Opens the list of contracted drill rigs with status and the programme each is on.",
    "Camps or crew, which have their own entries.")
add({"row_label": "Resources", "role": "link", "text_regex": r"^Camps\b"}, LEFT,
    "Opens the list of field camps with beds, occupancy and access.", "Camp service bookings, which are programme logistics items.")
add({"row_label": "Resources", "role": "link", "text_regex": r"^Crew rotations\b"}, LEFT,
    "Opens every crew assignment across the tenant, soonest to end first.",
    "Assigning crew, which is done on a programme's page.")

# Generic record links, per page. The negative look-ahead keeps them off navigation labels.
NAV_WORDS = ("ADIT home|Portfolio|Projects|Programmes|Drilling|Assays|Resources|Approvals|Optimiser|Admin|User Manual|"
             "In the field|In planning|Complete|All programmes|Schedule|Rigs|Camps|Crew rotations|Overview|Crew|Logistics|"
             "Drillholes|Approval|Cancel|Open|Skip to content")
NOT_NAV = r"^(?!(" + NAV_WORDS + r")\b)(?!PRG-\d)(?!RIG-)(?!WF-\d)(?![A-Z]{2,4}-[A-Z]{2,4}-\d)"
SORT = r"^Sort by "

# Programmes list
P = "programmes-list"
add({"page": P, "role": "link", "text": "New programme"}, "Programmes list header",
    "Opens the New programme form, which creates a programme as a draft.",
    "Opening or changing an existing programme (its row in the list).")
add({"page": P, "role": "button", "text_regex": SORT}, "Programmes list, table header",
    "Sorts the table by this column; a second press reverses the order.",
    "Filtering. Which programmes are listed is set by the left column and the type filter.",
    note="One entry for every column-header sort button.")
add({"page": P, "role": "link", "text_regex": r"^PRG-\d{4}-\d{3}$"}, "Programmes list, table rows",
    "Opens this programme's page (Overview tab).", "Opening the project; that is the project name in the row.",
    note="Pattern of programme ids, not any one programme.")
add({"page": P, "role": "link", "text_regex": NOT_NAV}, "Programmes list, table rows",
    "A record link in a row: the programme name opens that programme's page; the project name opens the project's page in Projects.",
    "Filtering the list by project (each project's own Programmes tab lists its programmes).",
    note="Generic: programme-name and project-name links cannot be told apart by any DOM key (hash hrefs are dropped by the reader).")

# New programme form
P = "programmes-new"
FORM = "New programme form"
add({"page": P, "row_label": "Project"}, FORM, "The project this programme belongs to. Choose one from the list.",
    "The programme type (Type) or name (Name).")
add({"page": P, "row_label": "Type"}, FORM,
    "The kind of work. Choosing drilling shows planned metres, planned holes and rig; other types do not need them.",
    "Phase; every new programme starts as a draft.", options=["drilling", "geophysics", "geochem", "mapping", "metallurgy", "baseline"])
add({"page": P, "row_label": "Name"}, FORM, "The programme's name: phase, method and target, in free text. Required.",
    "The objective, which is a separate field.")
add({"page": P, "row_label": "Objective"}, FORM, "What the programme sets out to do; it is carried onto the approval request. Required.",
    "The name.")
add({"page": P, "row_label": "Budget, USD"}, FORM, "The programme budget, a number above zero. Required.",
    "Spend to date, which accrues from the programme ledger.")
add({"page": P, "row_label": "Planned metres"}, FORM, "Total metres planned to drill. Required for drilling programmes.",
    "The number of holes (Planned holes).")
add({"page": P, "row_label": "Planned holes"}, FORM, "Number of holes planned. Drilling programmes only.",
    "Metres (Planned metres).")
add({"page": P, "row_label": "Rig"}, FORM,
    "Optionally attaches a contracted rig to a drilling programme. Each option shows the rig's current status; unavailable ones are greyed out.",
    "Changing the rig's own status, which is Update on the Rigs page.")
add({"page": P, "role": "link", "text": "Cancel"}, FORM, "Leaves the form without creating anything and returns to the Programmes list.",
    "Cancelling an existing programme.")
add({"page": P, "text": "Create draft"}, FORM,
    "Validates the form and, if every required field is filled, creates the programme as a draft and opens its page. With errors, it marks the fields and the form stays open.",
    "Submitting for approval, which is a later step on the programme page.")

# Rigs
P = "programmes-rigs"
add({"page": P, "role": "button", "text_regex": SORT}, "Rigs table header", "Sorts the rig table by this column; again to reverse.", "Filtering.")
add({"page": P, "role": "button", "text": "Update"}, "Rigs table, row actions",
    "Opens the Update rig dialog for this row's rig (status and location).",
    "Attaching the rig to a programme, which is done when the programme is created.",
    note="Shown only to users with logistics rights.")
add({"page": P, "role": "link", "text_regex": NOT_NAV}, "Rigs table, Programme column",
    "Opens the programme this rig is on.", "The rig itself, whose details are on this list.")

# Camps
P = "programmes-camps"
add({"page": P, "role": "button", "text_regex": SORT}, "Camps table header", "Sorts the camp table by this column; again to reverse.", "Filtering.")
add({"page": P, "role": "link", "text_regex": NOT_NAV}, "Camps table, Project column",
    "Opens the project the camp serves (Projects area).", "The camp itself, whose details are on this list.")

# Crew rotations
P = "programmes-crew-rotations"
add({"page": P, "role": "button", "text_regex": SORT}, "Crew rotations table header", "Sorts the rotations by this column; again to reverse.", "Filtering.")
add({"page": P, "role": "link", "text_regex": NOT_NAV}, "Crew rotations table, Programme column",
    "Opens the programme this rotation belongs to, where crew can be assigned or removed.", "Editing the rotation (the programme's Crew tab).")
for t, w in (("First", "Shows the first page of rotations."), ("Previous", "Shows the previous page of rotations."),
             ("Next", "Shows the next page of rotations."), ("Last", "Shows the last page of rotations.")):
    add({"page": P, "role": "button", "text": t}, "Crew rotations table, pager below the table", w,
        "Sorting or filtering the rotations.")

# Schedule
P = "programmes-schedule"
add({"page": P, "role": "link", "text_regex": NOT_NAV}, "Programme schedule, timeline rows",
    "Opens this programme's page.", "Changing the programme's dates (set on the programme).")

# Programme page header and tabs, repeated for each tab page (keys are per page on purpose).
HEAD = "Programme page header"
TABS = "Programme page tabs"
for P in DETAIL_TABS:
    add({"page": P, "role": "button", "text_regex": r"^Move to\s+"}, HEAD,
        "Advances this programme one phase, to the phase named on the button, after a confirmation dialog.",
        "Submitting for approval (Submit for approval at costed) or skipping phases; costed to approved happens by itself when the approval passes.")
    add({"page": P, "role": "button", "text": "Submit for approval"}, HEAD,
        "Raises the programme-approval request (Technical review, Budget check, Manager approval) immediately, with no confirmation. Offered only at costed with no request yet.",
        "Approving it; approvers act in Approvals.")
    add({"page": P, "role": "button", "text": "Assign crew"}, HEAD + " (also on the Crew tab)",
        "Opens the Assign crew dialog to add a person to this programme for a rotation.",
        "Removing crew (Remove on the Crew tab) or seeing all rotations (Crew rotations).")
    add({"page": P, "role": "link", "text": "Overview"}, TABS, "Shows the programme summary, objective, phase track and comments.",
        "Crew, logistics, holes or approval, which are their own tabs.")
    add({"page": P, "role": "link", "text_regex": r"^Crew \d+$"}, TABS, "Shows this programme's crew assignments. The number is how many.",
        "All rotations across programmes (Crew rotations in the left column).")
    add({"page": P, "role": "link", "text_regex": r"^Logistics \d+$"}, TABS, "Shows this programme's logistics items. The number is how many.",
        "Rigs or camps lists.")
    add({"page": P, "role": "link", "text_regex": r"^Drillholes \d+$"}, TABS, "Shows the drillholes in this programme. The number is how many.",
        "The Drilling area's full hole register.")
    add({"page": P, "role": "link", "text": "Approval"}, TABS, "Shows this programme's approval workflow and its steps.",
        "Deciding an approval step, which is done in Approvals.")
    add({"page": P, "role": "link", "text_regex": NOT_NAV}, "Programme page links",
        "A link to a related record: the project name under the title opens the project; in tables, a programme or project link opens that record.",
        "Changing the programme itself.", note="Generic fallback for record links on the programme page; more specific entries win.")

P = "programme-overview"
add({"page": P, "role": "button", "text_regex": r"^read from the programme ledger"}, "Overview, summary strip",
    "A provenance note saying where the summary figures come from; the figures stay as shown.",
    "Refreshing or recalculating the figures.")
add({"page": P, "role": "link", "text_regex": r"^RIG-"}, "Overview, details panel (Rig)",
    "Opens the Rigs list, where this programme's rig appears.", "Changing the rig on the programme.")
add({"page": P, "role": "link", "text_regex": r"^WF-\d{4}-\d{4}"}, "Overview, details panel (Approval)",
    "Opens the programme's approval request in Approvals, where its steps are decided. The word after the id is the request's status.",
    "Submitting for approval (header button).")
add({"page": P, "role": "textbox", "row_label": "Add a comment"}, "Overview, Comments panel",
    "Free-text comment on this programme, posted with Post comment and visible to everyone who opens it.",
    "Changing the objective or any programme field.")
add({"page": P, "role": "button", "text": "Post comment"}, "Overview, Comments panel",
    "Posts the text in Add a comment to this programme's comments. Disabled while the box is empty.",
    "Notifying a specific person or approving anything.")

P = "programme-crew"
add({"page": P, "role": "button", "text_regex": SORT}, "Crew tab, table header", "Sorts the assignments by this column; again to reverse.", "Filtering.")
add({"page": P, "role": "button", "text": "Remove"}, "Crew tab, row actions",
    "Deletes this row's crew assignment immediately, without a confirmation step.",
    "Ending a rotation early while keeping its record.", note="Row identity is the person name in row_label.")

P = "programme-logistics"
add({"page": P, "role": "button", "text_regex": SORT}, "Logistics tab, table header", "Sorts the items by this column; again to reverse.", "Filtering.")
add({"page": P, "role": "button", "text": "Add item"}, "Logistics tab, above the table",
    "Opens the empty logistics item form to add a new item to this programme.", "Changing an existing item (Edit on its row).")
add({"page": P, "role": "button", "text": "Edit"}, "Logistics tab, row actions",
    "Opens this row's item in the edit form.",
    "Adding a new item (Add item). Dropping an item is Status = cancelled in this form.", note="Row identity is the item id in row_label.")

P = "programme-holes"
add({"page": P, "role": "button", "text_regex": SORT}, "Drillholes tab, table header", "Sorts the holes by this column; again to reverse.", "Filtering.")
add({"page": P, "role": "link", "text_regex": r"^[A-Z]{2,4}-[A-Z]{2,4}-\d+$"}, "Drillholes tab, Hole column",
    "Opens this drillhole's page (Drilling).", "Opening the programme or project (their own links in the row).",
    note="Pattern of hole ids (project code, hole type, number).")
add({"page": P, "role": "link", "text_regex": r"^PRG-\d{4}-\d{3}$"}, "Drillholes tab, Programme column",
    "The programme in view.", "Opening the hole.")

P = "programme-approval"
add({"page": P, "role": "link", "text_regex": r"^WF-\d{4}-\d{4}"}, "Approval tab",
    "Opens this approval request in Approvals, where each step is approved or rejected.", "Submitting a new request.")

# Overlays
P = "programme-move-dialog"
DL = "Move phase confirmation dialog"
add({"page": P, "text": "Confirm"}, DL, "Moves the programme to the phase named in the dialog and closes it.",
    "A phase other than the one named in the dialog.")
add({"page": P, "text": "Cancel"}, DL, "Closes the dialog; the phase stays as it is.", "Cancelling the programme.")
add({"page": P, "text": "Close dialog"}, DL, "Closes the dialog without changing the phase (same as Cancel).")

P = "programme-assign-crew-dialog"
DL = "Assign crew dialog"
add({"page": P, "row_label": "Person"}, DL,
    "Who to assign: every staff member and field hand, shown with their usual role. Choosing one also fills Role on this programme.",
    "The role; that is its own field.")
add({"page": P, "row_label": "Role on this programme"}, DL,
    "The person's role on this programme, free text; pre-filled from the chosen person.", "Choosing the person.")
add({"page": P, "role": "button", "text": "Assign"}, DL,
    "Saves the assignment and closes the dialog. If the rotation overlaps the person's rotation on another live programme, it refuses, says which programme, and the dialog stays open.",
    "Removing anyone.")
add({"page": P, "text": "Cancel"}, DL, "Closes the dialog without assigning anyone.", "Removing an existing assignment.")
add({"page": P, "text": "Close dialog"}, DL, "Closes the dialog without assigning anyone (same as Cancel).")

P = "programme-logistics-item-dialog"
DL = "Logistics item dialog"
add({"page": P, "row_label": "Kind"}, DL, "What sort of item this is.", "Its status.",
    options=["charter", "camp", "fuel", "permit", "equipment", "medical", "freight"])
add({"page": P, "row_label": "Status"}, DL,
    "Where the item stands: requested, booked, confirmed, delivered, or cancelled for an item that is dropped.",
    "Its kind.", options=["requested", "booked", "confirmed", "delivered", "cancelled"])
add({"page": P, "row_label": "Description"}, DL, "What the item is, in free text. Required: Save acts once it is filled.",
    "The supplier's name.")
add({"page": P, "row_label": "Supplier"}, DL, "Who provides the item.", "The description.")
add({"page": P, "row_label": "Cost"}, DL, "The item's cost, a number.", "The programme budget.")
add({"page": P, "role": "button", "text": "Save"}, DL,
    "Stores the item on this programme (new, or overwriting the one being edited) and closes the dialog.",
    "Approving a purchase order.")
add({"page": P, "text": "Cancel"}, DL, "Closes the form without saving.", "Cancelling the item; that is Status = cancelled and Save.")
add({"page": P, "text": "Close dialog"}, DL, "Closes the form without saving (same as Cancel).")

P = "programmes-rig-update-dialog"
DL = "Update rig dialog"
add({"page": P, "row_label": "Status"}, DL, "The rig's status.", "Which programme it is on.",
    options=["available", "assigned", "maintenance", "demobilised"])
add({"page": P, "row_label": "Location"}, DL, "Where the rig is, free text.", "Its status.")
add({"page": P, "role": "button", "text": "Save"}, DL, "Applies the status and location and closes the dialog.")
add({"page": P, "text": "Cancel"}, DL, "Closes without changing the rig.")
add({"page": P, "text": "Close dialog"}, DL, "Closes without changing the rig (same as Cancel).")

# Toast (shared component; described because actions in this area raise it).
add({"role": "button", "text": "Dismiss"}, "Notice at the corner of the screen",
    "Hides the notice that just confirmed or reported an action.", "Undoing the action the notice reports.",
    note="Shared toast component, not specific to Programmes; merger should keep one copy.")

atlas = {
    "app": "ADIT",
    "version": "2026-09-22-programmes-part",
    "selectors": {"dialog": ["dialog[open]"], "dialog_title": ["dialog[open] h2"]},
    "pages": pages,
    "controls": C,
}
with open(OUT, "w") as f:
    json.dump(atlas, f, indent=1, ensure_ascii=False)
print(len(pages), "pages", len(C), "controls")

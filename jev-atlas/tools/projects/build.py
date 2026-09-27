"""Build jev-atlas/atlas/parts/projects.json (the Projects area fragment)."""
# Copied from the area author's scratch directory on 2026-09-22 by the atlas merger;
# paths rewritten to be relative to this file and to $JEV_CLONE (the harness copy).
import os as _os, pathlib as _pl
_PARTS = _pl.Path(_os.environ.get("ADIT_PARTS_DIR") or _pl.Path(__file__).resolve().parents[2] / "atlas" / "parts")
_HARNESS = _os.environ.get("JEV_CLONE", str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'vendor' / 'jev-ultrafast')).rstrip("/") + "/jev_ultrafast/"

import json

OUT = str(_PARTS / "projects.json")

# Generic record-link text: anything that is not a header/nav name, a tab, a fixed
# link of this area, or an id-shaped code (those have their own entries).
RECORD_LINK = (r"^(?!(?:Portfolio|Projects|Programmes|Drilling|Assays|Resources?|Approvals|Optimiser|Admin|Overview|Tenure"
               r"|Budget|Activity|New project|New programme|Clear cut|Cancel|ADIT home)(?:\s+\d+)?$)"
               r"(?!Approvals\s*\()(?!User Manual)(?!open in )(?!all\s+\d+$)(?!Tenement\s.+expires)(?!Batch\s+\S+$)"
               r"(?![A-Z]{2,}(?:-[A-Z0-9]+)+$)\S")

# ---------------------------------------------------------------- facts_js
F_PROJECT = ("(() => { const h=document.querySelector('main .head h1'); if(!h || !document.querySelector('main nav.tabs')) return null; "
             "const idEl=h.querySelector('.id'); const id=idEl?idEl.textContent.trim():''; "
             "const name=[...h.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join('').trim(); "
             "const meta=[...document.querySelectorAll('main .head .meta > *')].map(e=>e.textContent.replace(/\\s+/g,' ').trim()).filter(Boolean).join(' · '); "
             "return 'Project in view: '+name+(id?' ('+id+')':'')+(meta?' · '+meta:''); })()")
F_TAB = ("(() => { const a=document.querySelector('main nav.tabs a[aria-current=\"page\"]'); "
         "return a ? 'Open tab: '+[...a.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join('').trim() : null; })()")
F_ACTIONS = ("(() => { if(!document.querySelector('main nav.tabs')) return null; "
             "const b=[...document.querySelectorAll('main .head .actions button')].map(e=>e.textContent.trim()); "
             "const miss=['Edit','Stage-gate decision'].filter(x=>!b.includes(x)); "
             "return 'Project header actions shown to the signed-in user: '+(b.join(', ')||'none')+(miss.length?'; '+miss.join(' and ')+': offered to roles holding that permission, on open projects (to act with that role, switch user in the account menu to a person who holds it (People and roles lists who holds each role))':''); })()")
F_USER = ("(() => { const s=JSON.parse(localStorage.getItem('adit.session.v1')||'{}'); "
          "const w=(JSON.parse(localStorage.getItem('adit.tenant.v1')||'{}')||{}).world; "
          "const u=w&&w.users&&w.users.find(x=>x.id===s.currentUserId); "
          "return u ? 'Signed in as '+u.name+', '+u.title : null; })()")
F_TOAST = ("(() => { const t=[...document.querySelectorAll('.toasts .toast span')].map(e=>e.textContent.trim()).filter(Boolean); "
           "return t.length ? 'Message shown: '+t.join(' | ') : null; })()")
F_TABLE = ("(() => { const all=document.querySelectorAll('main table.tbl'); const t=all[all.length-1]; if(!t) return null; "
           "const cap=(t.querySelector('caption')||{}).textContent||'Table'; "
           "const foot=t.closest('div').parentElement.querySelector('.tbl-foot span'); "
           "const s=t.querySelector('th[aria-sort=\"ascending\"],th[aria-sort=\"descending\"]'); "
           "const rows=t.querySelectorAll('tbody tr').length; "
           "return 'Table \"'+cap.trim()+'\": '+(foot?foot.textContent.trim():rows+' rows shown')+(s?', sorted by '+s.textContent.trim()+' '+s.getAttribute('aria-sort'):''); })()")
F_EMPTY = ("(() => { const e=document.querySelector('main p.empty'); return e ? 'Notice: '+e.textContent.trim() : null; })()")
F_REG_META = ("(() => { const h=document.querySelector('main .head h1'); if(!h || h.textContent.trim()!=='Projects') return null; "
              "const m=[...document.querySelectorAll('main .head .meta > *')].map(e=>e.textContent.trim()).filter(Boolean); "
              "return 'Register shows '+m.join(' · ')+(m.length<2?' (all active projects)':''); })()")
F_L2 = ("(() => { const a=document.querySelector('nav.l2 a[aria-current=\"page\"]'); if(!a) return null; "
        "const sec=a.parentElement.querySelector('.sec'); "
        "return 'Left panel selection: '+(sec?sec.textContent.trim()+' › ':'')+[...a.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join('').trim(); })()")
F_FIND = ("(() => { const i=document.querySelector('main .filters input[type=search]'); "
          "return i && i.value ? 'Find box contains \"'+i.value+'\"' : null; })()")
F_TENURE = ("(() => { const t=document.querySelector('main table.tbl'); if(!t) return null; "
            "const hs=[...t.querySelectorAll('thead th')].map(x=>x.textContent.trim().toLowerCase()); "
            "const col=n=>hs.findIndex(h=>h.startsWith(n)); const iT=col('tenement'), iS=col('status'), iE=col('expires'); "
            "const rows=[...t.querySelectorAll('tbody tr')].map(r=>{const c=r.querySelectorAll('td'); if(c.length<=Math.max(iT,iS,iE)) return null; "
            "return c[iT].textContent.trim()+': '+c[iS].textContent.trim()+', expires '+c[iE].textContent.replace(/\\s+/g,' ').trim()+(r.querySelector('button')?' [Lodge renewal button shown]':''); }).filter(Boolean); "
            "if(!rows.length) return null; const any=t.querySelector('tbody button'); "
            "return 'Tenements: '+rows.join('; ')+(any?'':'. Lodge renewal: offered to the Tenure & Permitting Officer role on current or expiring tenements (to act with that role, switch user in the account menu to a person who holds it (People and roles lists who holds each role)).'); })()")
F_RESOURCE = ("(() => { const h=document.querySelector('main .panel .ph h2'); const r=document.querySelector('main .panel .ph .r'); "
              "if(!h || !document.querySelector('main nav.tabs a[aria-current=\"page\"][href$=\"/resource\"]')) return null; "
              "return 'Estimate shown: '+h.textContent.trim()+(r?' ('+r.textContent.trim()+')':''); })()")
F_OPEN_ITEMS = ("(() => { const s=document.querySelector('main section[aria-labelledby=\"ov-open\"]'); if(!s) return null; "
                "const rows=[...s.querySelectorAll('.row')].map(r=>[...r.children].map(c=>c.textContent.replace(/\\s+/g,' ').trim()).filter(Boolean).join(' — ')); "
                "return 'Open items: '+(rows.length?rows.join('; '):'none'); })()")
F_COMMENTS = ("(() => { const t=document.querySelector('main form.comment-form textarea'); if(!t) return null; "
              "const n=document.querySelectorAll('main ul.comments > li').length; "
              "return 'Comments: '+n+' posted'+(t.value.trim()?'; draft typed, awaiting Post comment ('+t.value.trim().length+' characters)':''); })()")

FORM_FIELDS = ("[...{root}.querySelectorAll('label.field')].map(l=>{{const n=(l.querySelector('span')||{{}}).textContent; const f=l.querySelector('input,select,textarea'); if(!f||!n) return null; "
               "let v=f.tagName==='SELECT'?((f.selectedOptions[0]||{{}}).textContent||''):f.value; if(f.tagName==='TEXTAREA') v=v.trim()?v.trim().length+' characters':''; "
               "const e=l.querySelector('.error'); return n.replace(/\\s+/g,' ').trim()+' = '+(v===''?'(empty)':v)+(f.required?' (required)':'')+(e?' (invalid: '+e.textContent.trim()+')':''); }}).filter(Boolean).join('; ')")
F_NEW_FORM = ("(() => { const f=document.querySelector('main form.panel'); if(!f) return null; "
              "return 'New project form: '+" + FORM_FIELDS.format(root="f") + "; })()")
F_EDIT_FORM = ("(() => { const d=document.querySelector('dialog[open][aria-label^=\"Edit PRJ-\"]'); if(!d) return null; "
               "return 'Edit form: '+" + FORM_FIELDS.format(root="d") + "; })()")
F_GATE_FORM = ("(() => { const d=document.querySelector('dialog[open][aria-label^=\"Stage-gate decision\"]'); if(!d) return null; "
               "const sum=d.querySelector('.sum'); const c=[...d.querySelectorAll('input[type=radio]')].find(x=>x.checked); "
               "const t=d.querySelector('textarea'); const n=t?t.value.trim().length:0; const err=d.querySelector('.error'); "
               "return (sum?sum.textContent.trim()+' ':'')+'Decision selected: '+(c?c.parentElement.textContent.replace(/\\s+/g,' ').trim():'none')+'; reasoning: '+n+' characters'+(n<20?' (Record decision needs at least 20)':' (long enough)')+(err?'; error shown: '+err.textContent.trim():''); })()")
F_LODGE = ("(() => { const d=document.querySelector('dialog[open][aria-label=\"Lodge a renewal\"]'); if(!d) return null; "
           "const parts=[d.querySelector('.sum'), ...d.querySelectorAll('dl dt'), d.querySelector('.notice')].filter(Boolean).map(e=>e.tagName==='DT'?e.textContent.trim()+': '+(e.nextElementSibling?e.nextElementSibling.textContent.trim():''):e.textContent.trim()); "
           "return 'Renewal: '+parts.join(' · '); })()")

V_NEXT_GATE = (
    "(() => { const d=document.querySelector('dialog[open][aria-label^=\"Edit PRJ-\"]'); if(!d) return []; "
    "const i=d.querySelector('input[type=date]'); if(!i) return []; "
    "return [{id:'edit-project-next-gate', label:'Next gate', row_label:'Next gate', region:'Edit project dialog', "
    "what:'The date of the project\\'s next stage-gate review. It is shown in the project header and the register\\'s Next gate column. Write a date as YYYY-MM-DD.', "
    "not_for:'Recording a stage-gate decision (the Stage-gate decision button on the project). Kept by the dialog\\'s Save.', "
    "current_value:i.value, "
    "set:\"(v) => { const i=document.querySelector('dialog[open] input[type=date]'); if(!i) return false; "
    "let s=String(v||'').trim(); if(!/^\\\\d{4}-\\\\d{2}-\\\\d{2}$/.test(s)){ const t=new Date(s); if(isNaN(t)) return false; s=t.toISOString().slice(0,10); } "
    "Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(i,s); "
    "i.dispatchEvent(new Event('input',{bubbles:true})); i.dispatchEvent(new Event('change',{bubbles:true})); return i.value===s; }\"}]; })()"
)

DETAIL_FACTS = [F_PROJECT, F_TAB, F_ACTIONS, F_USER, F_TOAST]

TABS = ["tenure", "programmes", "drilling", "assays", "resource", "budget", "approvals", "activity"]
DETAIL_PAGES = ["project-overview"] + [f"project-{t}" for t in TABS]
ALL_PAGES = ["projects-register", "projects-new"] + DETAIL_PAGES

COMMON_DECIDE = "Deciding a request: the request's own page in Approvals. "
COMMON_FIXED = "Budget, commodity and jurisdiction: set at creation; later changes go through support."
COMMON_NOT_HERE = COMMON_DECIDE + COMMON_FIXED

pages = [
    {
        "id": "projects-register",
        "match": {"url_regex": r"#/projects/?(\?.*)?$"},
        "name": "Projects register",
        "what": ("The list of exploration projects (properties): one row per project with its id, name, commodity, jurisdiction, "
                 "stage in the pipeline, status, project geologist (a dashed 'vacant' chip when the role is unfilled), area under tenure, "
                 "fiscal-year budget, spent with a progress bar, forecast against budget and next gate date. Active projects are shown by default; "
                 "the left panel cuts the register to on-hold or closed projects, to one commodity or to one stage, and the Find box narrows by id, name or jurisdiction. "
                 "Each id or name opens that project's record."),
        "not_here": ("A project's tenements, programmes, holes, batches, estimates, budget detail, approvals and audit trail are tabs on the project record, "
                     "reached by opening the project from this list. Portfolio-wide budget and totals are under Portfolio. "
                     "Programmes, holes and batches across all projects are the Programmes, Drilling and Assays sections of the top navigation."),
        "leads_to": {"Project id or name link": "project-overview", "New project": "projects-new",
                     "Left panel cuts (All active, On hold, Closed, By commodity, By stage)": "projects-register"},
        "facts_js": [F_REG_META, F_L2, F_FIND, F_TABLE, F_TOAST],
    },
    {
        "id": "projects-new",
        "match": {"url_regex": r"#/projects/new/?(\?.*)?$"},
        "name": "New project form",
        "what": ("Creates a project. It asks for a project name, commodity, jurisdiction, country, area in square kilometres, the fiscal-year budget, "
                 "the project geologist and a description. New projects start at the Reconnaissance stage and take the next number from the tenant's "
                 "auto-numbering rule. Create project validates the form and, if it is complete, opens the new project's record."),
        "not_here": ("Editing an existing project: the Edit button on that project's record. Stage changes: Stage-gate decision on the project record. "
                     "Creating programmes: the project's Programmes tab or the Programmes section."),
        "leads_to": {"Create project (when valid)": "project-overview", "Cancel": "projects-register", "Projects breadcrumb": "projects-register"},
        "facts_js": [F_NEW_FORM, F_TOAST],
    },
    {
        "id": "project-overview",
        "match": {"url_regex": r"#/projects/(?!new(?:[/?]|$))[^/?#]+/?(\?.*)?$"},
        "name": "Project record, Overview tab",
        "what": ("One project's summary: fiscal-year budget and spend, area under tenure, holes drilled, significant intercepts and the latest estimate; "
                 "the description and team (exploration manager, project geologist); the stage history through the pipeline; recent programmes; "
                 "open items (pending approvals, batches on QAQC hold, expiring tenements); and the comments panel, where typing @ and a colleague's first "
                 "name notifies them. The header carries Watch, Edit and Stage-gate decision; the tab strip leads to the project's Tenure, Programmes, "
                 "Drilling, Assays, Resource, Budget, Approvals and Activity."),
        "not_here": ("Tenement renewal (Lodge renewal): the Tenure tab. The budget ledger and monthly spend: the Budget tab. "
                     "Every approval raised on the project: the Approvals tab; the audit trail: Activity. " + COMMON_NOT_HERE +
                     " A heading reading 'Project not found' means the address holds an unknown project id; the Projects register lists every project."),
        "leads_to": {"Tabs": "project-tenure / project-programmes / project-drilling / project-assays / project-resource / project-budget / project-approvals / project-activity",
                     "Edit": "project-edit-dialog", "Stage-gate decision": "project-stage-gate-dialog", "Projects breadcrumb": "projects-register"},
        "facts_js": DETAIL_FACTS + [F_OPEN_ITEMS, F_COMMENTS, F_EMPTY],
    },
]

TAB_TEXT = {
    "tenure": ("Project record, Tenure tab",
               "Every tenement held for this project with its type, holder, status, grant and expiry dates, area, annual expenditure commitment, "
               "spend against that commitment and rent due, with totals above the table. For a current or expiring tenement, users with the tenure "
               "write permission (the Tenure & Permitting Officer role) see a Lodge renewal button on its row, which starts the tenement-renewal workflow "
               "(an expenditure check by Finance, then lodgement by Tenure).",
               "Deciding a renewal already lodged: its request in Approvals. A tenement whose renewal is lodged shows status 'renewal lodged'. "
               "Lodge renewal appears on current or expiring tenements for users with the tenure permission (the Tenure & Permitting Officer role; "
               "to act with that role, switch user in the account menu to a person who holds it (People and roles lists who holds each role)). " + COMMON_FIXED,
               [F_TENURE, F_TABLE]),
    "programmes": ("Project record, Programmes tab",
                   "The project's field programmes in all phases (drilling, geophysics, geochemistry, mapping, metallurgy, baseline), with phase, dates, "
                   "metres drilled of planned, budget, spent and lead. For users with the programme write permission (Project Geologist role) a New programme "
                   "button opens the programme form with this project already selected.",
                   "A programme's own detail, crew, rig and approval submission: the programme's page in the Programmes section (its id or name link). "
                   + COMMON_NOT_HERE,
                   [F_TABLE]),
    "drilling": ("Project record, Drilling tab",
                 "Hole counts (planned, drilling, abandoned), metres drilled, average depth, the best intercept, and the table of the project's drillholes "
                 "with programme, type, status, collar coordinates, azimuth, dip, planned and actual depth and best intercept. 'open in Drilling' shows the "
                 "same holes in the Drilling section.",
                 "Logging, sampling and editing a hole: the hole's own page in the Drilling section. " + COMMON_NOT_HERE,
                 [F_TABLE]),
    "assays": ("Project record, Assays tab",
               "The project's sample batches: laboratory, status, holes, sample count, QAQC insertions (standards / blanks / duplicates), failures, "
               "dispatch and receipt dates, turnaround and method. 'open in Assays' shows them in the Assays section.",
               "Creating a batch, importing results and reviewing QAQC failures: the Assays section. " + COMMON_NOT_HERE,
               [F_TABLE]),
    "resource": ("Project record, Resource tab",
                 "The latest released resource estimate (or the latest of any status if none is released): contained metal, tonnes, grade, in-situ value at "
                 "the price deck, the P10/P50/P90 forecast, the split by category (measured, indicated, inferred), and the project's estimate history. "
                 "If the project has no estimate, the tab says so.",
                 "Creating or releasing an estimate and editing the price deck: the Resources section ('open in Resources'). " + COMMON_NOT_HERE,
                 [F_RESOURCE, F_EMPTY, F_TABLE]),
    "budget": ("Project record, Budget tab",
               "The project ledger: approved budget, committed, spent and year-end forecast against budget, programme budgets over all years, spend by month "
               "against plan, programme budget by type, and the programme ledgers table. Read-only.",
               "Changing the year-end forecast: the Edit button in the project header. Budget variance requests: raised and decided in Approvals. "
               "Portfolio-wide budget: Portfolio. The approved budget: set at creation; later changes go through support.",
               [F_TABLE]),
    "approvals": ("Project record, Approvals tab",
                  "Every approval request raised on this project (programme approvals, purchase orders, tenement renewals, budget variances, stage-gate "
                  "reviews and others) with workflow, status, current step and who holds it, requester, amount, submitted and due dates. Each opens the "
                  "request.",
                  "Approving, rejecting or commenting on a request: the request's own page in Approvals. Raising a stage-gate review request: Approvals; "
                  "recording the decision itself: Stage-gate decision on this project. " + COMMON_FIXED,
                  [F_TABLE]),
    "activity": ("Project record, Activity tab",
                 "The audit trail for the project and its records (programmes, approvals, batches, estimates, tenements): when, who, action, record and "
                 "detail, newest first. Read-only.",
                 "The tenant-wide audit log: Admin. Posting comments: the Overview tab. " + COMMON_NOT_HERE,
                 [F_TABLE]),
}
for t in TABS:
    name, what, not_here, facts = TAB_TEXT[t]
    pages.append({
        "id": f"project-{t}",
        "match": {"url_regex": rf"#/projects/[^/?#]+/{t}/?(\?.*)?$"},
        "name": name, "what": what, "not_here": not_here,
        "leads_to": {"Overview tab": "project-overview", "Edit": "project-edit-dialog",
                     "Stage-gate decision": "project-stage-gate-dialog", "Projects breadcrumb": "projects-register",
                     **({"Lodge renewal": "tenement-renewal-dialog"} if t == "tenure" else {})},
        "facts_js": DETAIL_FACTS + facts,
    })

pages += [
    {
        "id": "project-edit-dialog", "layer": "overlay",
        "match": {"selector": "dialog[open][aria-label^=\"Edit PRJ-\"]"},
        "name": "Edit project dialog",
        "what": ("Changes the project's name, project geologist, next gate date, year-end forecast and description. Save keeps the changes and closes "
                 "the dialog; Cancel, the close cross or Escape discard them."),
        "not_here": (COMMON_FIXED + " Stage changes: the Stage-gate decision dialog. "
                     "Project geologist lists inactive geologists for reference; the active ones are selectable."),
        "facts_js": [F_EDIT_FORM],
        "virtual_controls_js": V_NEXT_GATE,
    },
    {
        "id": "project-stage-gate-dialog", "layer": "overlay",
        "match": {"selector": "dialog[open][aria-label^=\"Stage-gate decision · \"]"},
        "name": "Stage-gate decision dialog",
        "what": ("Records the decision that ends the project's current stage. Exactly one decision is chosen: Advance to the next stage (from the final "
                 "Stage-gate decision stage, advancing hands the project to the development group and closes it in exploration); Place on hold at the "
                 "current stage (or Resume, when the project is on hold); or Relinquish, which closes the project, lapses its tenure at the next expiry "
                 "and makes its records read-only. A reasoning of at least twenty characters is required and is written verbatim to the audit log; the "
                 "project team is notified."),
        "not_here": ("A formal stage-gate review with a gate pack: raised as a request in Approvals; this dialog records the decision itself. "
                     "Changing only the next gate date: the Edit dialog."),
        "facts_js": [F_GATE_FORM],
    },
    {
        "id": "tenement-renewal-dialog", "layer": "overlay",
        "match": {"selector": "dialog[open][aria-label=\"Lodge a renewal\"]"},
        "name": "Lodge a renewal dialog",
        "what": ("Confirms lodging a renewal for one tenement: shows its expiry, the workflow it starts (expenditure check by Finance, then lodgement by "
                 "Tenure) and the expenditure against the annual commitment, with a warning when spend is below the commitment. Submit for renewal "
                 "creates the tenement-renewal approval request and marks the tenement 'renewal lodged'."),
        "not_here": ("A confirmation: Submit for renewal is its one action. Approving the renewal steps: the created request in Approvals. "
                     "Cancel, the close cross or Escape close it and leave the tenement as it was."),
        "facts_js": [F_LODGE],
    },
]

controls = []
def C(key, region, what, not_for, note=None, options=None):
    e = {"key": key, "region": region, "what": what, "not_for": not_for}
    if note: e["note"] = note
    if options: e["options"] = options
    controls.append(e)

# ---- Left panel (section navigation), present on every Projects route
L2 = "Projects left panel (section navigation)"
C({"row_label": "Projects", "role": "link", "text_regex": r"^All active \d+$"}, L2,
  "Shows the register of active projects (everything not closed, including on hold), with no other cut. The number is how many there are.",
  "Closed projects (that is Closed) or only on-hold projects (that is On hold).", note="Count in the label varies, hence the regex.")
C({"row_label": "Projects", "role": "link", "text_regex": r"^On hold \d+$"}, L2,
  "Cuts the register to projects whose status is on hold. The number is how many there are.",
  "Placing a project on hold (that is the Stage-gate decision on the project record).")
C({"row_label": "Projects", "role": "link", "text_regex": r"^Closed \d+$"}, L2,
  "Cuts the register to closed projects (advanced to development or relinquished). The number is how many there are.",
  "Closing a project (that is a Stage-gate decision).")
C({"row_label": "By commodity", "role": "link", "text_regex": r"^\S.* \d+$"}, L2,
  "Cuts the register to active projects of the commodity named on the link; the number is how many there are.",
  "Portfolio totals by commodity (Portfolio). Each link replaces the current cut, including a stage cut.",
  note="Generic: shared by every commodity link in the group.")
C({"row_label": "By stage", "role": "link", "text_regex": r"^\S.* \d+$"}, L2,
  "Cuts the register to active projects at the pipeline stage named on the link; the number is how many there are.",
  "Moving a project to another stage (the Stage-gate decision button on the project record). The 'Stage-gate decision' link here filters to that stage.",
  note="Generic: shared by every stage link in the group.")

# ---- Register
P = "projects-register"
C({"page": P, "role": "link", "text": "New project"}, "Register header, right",
  "Opens the New project form to create a project.",
  "Creating a programme for an existing project (that is New programme on the project's Programmes tab).")
C({"page": P, "text": "Find"}, "Register filter bar",
  "Type-to-filter box: narrows the rows shown to projects whose id, name or jurisdiction contains the text, as you type. It keeps the current left-panel cut.",
  "Searching the whole tenant (the top-bar search box). Commodity and stage cuts: the left panel.")
C({"page": P, "role": "link", "text": "Clear cut"}, "Register filter bar",
  "Removes the left-panel cut (status, commodity or stage) and shows all active projects again.",
  "Clearing the Find box text.")
C({"page": P, "text_regex": r"^Sort by "}, "Register table header",
  "Sorts the register by the column named in the label; pressing again reverses the order.",
  "Filtering rows (that is Find or the left panel).", note="Generic: every column header button.")
C({"page": P, "role": "link", "text_regex": r"^PRJ-\d+$"}, "Register table, Project column",
  "Opens that project's record (Overview tab).", "Editing the project directly; the record's Edit button does that.",
  note="Keyed on the project-id format, not on a record.")
C({"page": P, "role": "link", "text_regex": RECORD_LINK}, "Register table, Name column",
  "A project's name: opens that project's record (Overview tab), the same as its id link.",
  "Filtering by name (that is the Find box).",
  note="Generic catch-all for record-name links; the regex excludes header/nav names, tabs, fixed links and id-shaped codes, which have their own entries.")

# ---- New project form
P = "projects-new"
C({"page": P, "role": "link", "text": "Projects"}, "Breadcrumb above the title (the top navigation has a link with the same name)",
  "Opens the Projects register.", "Saving the form; leaving this way discards what was typed.")
C({"page": P, "text_regex": r"^(Open )?Project name"}, "New project form",
  "The project's name. Required.", "The project id, which is assigned automatically by the auto-numbering rule.")
C({"page": P, "text": "Commodity"}, "New project form",
  "The one commodity the project explores for, chosen from the list. Fixed at creation; later changes go through support.", "The deposit style, which follows from the commodity.",
  options=["Gold", "Lithium", "Potash", "Copper", "Nickel"])
C({"page": P, "text_regex": r"^(Open )?Jurisdiction"}, "New project form",
  "The state, province or region the property is in, typed as free text. Required. Fixed at creation; later changes go through support.",
  "The country, which is the separate Country list.")
C({"page": P, "text": "Country"}, "New project form",
  "The country the property is in, chosen from the list.", "The state or province (that is Jurisdiction).",
  options=["Canada", "United States", "Australia", "Chile", "Finland", "Argentina"])
C({"page": P, "text_regex": r"^(Open )?Area"}, "New project form",
  "Area of the property in square kilometres. Required, more than zero.", "The budget.")
C({"page": P, "text_regex": r"^(Open )?Budget"}, "New project form",
  "The project's budget for the current fiscal year, in the tenant's base currency. Required; 0 means none. Fixed at creation; later changes go through support.",
  "The year-end forecast, which starts equal to the budget and is changed later with Edit.")
C({"page": P, "text": "Project geologist"}, "New project form",
  "The project geologist responsible for the project, chosen from active users in the Project Geologist role.",
  "The exploration manager, who is assigned automatically.")
C({"page": P, "text_regex": r"^(Open )?Description"}, "New project form",
  "Free-text description: deposit style, what is known, what the first programme will test. Optional.", "Comments, which are posted on the record after creation.")
C({"page": P, "role": "link", "text": "Cancel"}, "New project form, bottom right",
  "Leaves the form, discarding what was typed, and opens the Projects register.", "Clearing the fields while staying on the form.")
C({"page": P, "role": "button", "text": "Create project"}, "New project form, bottom right",
  "Validates the form and creates the project, then opens its record. It refuses and marks the fields while a required field is empty or invalid (name, jurisdiction, area above zero, budget); the form stays open.",
  "Submitting for approval; a new project is created directly.")

# ---- Project record: header, tabs, shared on every detail page
for P in DETAIL_PAGES:
    C({"page": P, "role": "link", "text": "Projects"}, "Breadcrumb above the project title (the top navigation has a link with the same name)",
      "Opens the Projects register.", "Going to another tab of this project (those are the tab strip links).",
      note="Indistinguishable from the top-navigation Projects link by any key field; the description is true of both.")
    C({"page": P, "role": "button", "text_regex": r"^(Watch|Watching)$"}, "Project header, right",
      "Toggles whether you watch this project (notifications about it). 'Watching' means you already do; pressing it stops watching.",
      "Following another record (each record has its own Watch). Watching leaves the project's data as it is.")
    C({"page": P, "role": "button", "text": "Edit"}, "Project header, right",
      "Opens the Edit dialog for the project's name, project geologist, next gate date, year-end forecast and description. Shown to users with the project write permission, on open projects.",
      "Changing budget, commodity or jurisdiction (set at creation; later changes go through support), or changing stage (Stage-gate decision).")
    C({"page": P, "role": "button", "text": "Stage-gate decision"}, "Project header, right (primary button)",
      "Opens the Stage-gate decision dialog to advance, hold, resume or relinquish the project. Shown only to users with the gate decision permission (Exploration Manager by default).",
      "Raising a stage-gate review request for approval (Approvals), or the left panel's 'Stage-gate decision' stage filter.")
    tabs = [
        ("Overview", {"text": "Overview"}, "the project's summary, open items and comments"),
        ("Tenure", {"text_regex": r"^Tenure \d+$"}, "the project's tenements and Lodge renewal"),
        ("Programmes", {"text_regex": r"^Programmes \d+$"}, "the project's programmes"),
        ("Drilling", {"text_regex": r"^Drilling \d+$"}, "the project's drillholes"),
        ("Assays", {"text_regex": r"^Assays \d+$"}, "the project's sample batches"),
        ("Resource", {"text_regex": r"^Resource \d+$"}, "the project's resource estimates"),
        ("Budget", {"text": "Budget"}, "the project ledger and spend against plan"),
        ("Approvals", {"text_regex": r"^Approvals \d+$"}, "every approval request raised on the project"),
        ("Activity", {"text": "Activity"}, "the project's audit trail"),
    ]
    for label, k, desc in tabs:
        C({"page": P, "role": "link", **k}, "Project tab strip",
          f"Opens the {label} tab of this project: {desc}." + (" The number is how many records the tab lists." if "text_regex" in k else ""),
          f"The {label} section of the top navigation, which covers all projects." if label in ("Programmes", "Drilling", "Assays", "Approvals")
          else "Any other project; the tabs always stay on the project in view.")

# ---- Overview
P = "project-overview"
C({"page": P, "text_regex": r"^(Open )?Add a comment"}, "Comments panel, foot of the Overview",
  "Text of a new comment on this project. Typing @ followed by a colleague's first name notifies them; the project manager and geologist are notified of every comment.",
  "Reasoning for a stage-gate decision (that is in the Stage-gate decision dialog) or the project description (that is Edit). Text typed here is saved by Post comment.")
C({"page": P, "role": "button", "text": "Post comment"}, "Comments panel, foot of the Overview",
  "Posts the comment typed in the box to the project and clears the box. It is only enabled when the box has text.",
  "Saving project fields (that is the Edit dialog's Save).")
C({"page": P, "role": "link", "text_regex": r"^all\s+\d+$"}, "Overview, Programmes panel heading",
  "Opens the Programmes tab listing all of the project's programmes.", "Creating a programme.")
C({"page": P, "role": "link", "text_regex": r"^Tenement .+ expires"}, "Overview, Open items panel",
  "An expiring or renewal-lodged tenement: opens this project's Tenure tab.", "Lodging the renewal itself (that is Lodge renewal on the Tenure tab).")
C({"page": P, "role": "link", "text_regex": r"^Batch\s+\S+$"}, "Overview, Open items panel",
  "A sample batch on QAQC hold: opens the batch in the Assays section.", "Releasing the hold (the batch's page in Assays).")
C({"page": P, "role": "link", "text_regex": RECORD_LINK}, "Overview, Programmes or Open items panel",
  "A record named in the panel: a programme name opens that programme's page; a pending approval title opens the request in Approvals.",
  "Approving; decisions are made on the request page.",
  note="Generic catch-all for record-name links on this page.")

# ---- Provenance ("authority") line, shared component
C({"role": "button", "text_regex": r"^(read from|computed by) "}, "Under a row of summary figures",
  "Provenance line: says which records the figures above were read or computed from. Where it ends in 'show method' it expands the method, author, reviewer and notes; otherwise it is a label.",
  "Opening the records it counts (the tabs and tables open them).",
  note="Shared component (appears in other areas too); description is generic.")

# ---- Tenure
P = "project-tenure"
C({"page": P, "role": "button", "text": "Lodge renewal"}, "Tenements table, Actions column (one per current or expiring tenement)",
  "Opens the Lodge a renewal dialog for the tenement on this row (its id is the row label), to start the tenement-renewal workflow. Shown only to users with the tenure write permission.",
  "Deciding a renewal already lodged (its request in Approvals). A tenement with status 'renewal lodged' is already in the workflow.",
  note="One button per row; the tenement id is the row_label, never a key.")

# ---- Programmes tab
P = "project-programmes"
C({"page": P, "role": "link", "text": "New programme"}, "Programmes tab, table heading, right",
  "Opens the new-programme form in the Programmes section with this project already selected. Shown only to users with the programme write permission.",
  "Creating a project (that is New project in the register).")

# ---- Drilling / Assays / Resource cross-links
C({"page": "project-drilling", "role": "link", "text": "open in Drilling"}, "Drilling tab, table heading, right",
  "Opens the Drilling section filtered to this project's holes.", "Opening one hole (its id link in the table).")
C({"page": "project-assays", "role": "link", "text": "open in Assays"}, "Assays tab, table heading, right",
  "Opens the Assays section filtered to this project's batches.", "Opening one batch (its id link in the table).")
C({"page": "project-resource", "role": "link", "text": "open in Resources"}, "Resource tab, Estimates heading, right",
  "Opens the Resources estimates list filtered to this project.", "Opening one estimate (its id link in the table).")
C({"page": "project-budget", "role": "button", "text": "Values behind this chart"}, "Budget tab, under each chart",
  "Expands the table of numbers the chart above it is drawn from.", "Editing budget values (forecast: Edit in the project header; approved budget: set at creation).",
  note="One per chart (spend by month; budget by type).")

# ---- Tables on tabs: sort, pager, id links, record-name links
ID_LINKS = {
    "project-programmes": [(r"^PRG-\d+-\d+$", "Opens this programme's page.")],
    "project-budget": [(r"^PRG-\d+-\d+$", "Opens this programme's page.")],
    "project-drilling": [(r"^PRG-\d+-\d+$", "Opens the programme that drilled this hole."),
                         (r"^[A-Z]{2,}(?:-[A-Z0-9]+)*-\d+$", "Opens this drillhole's page.")],
    "project-assays": [(r"^LAB-\d+-\d+$", "Opens this sample batch's page.")],
    "project-resource": [(r"^RES-\d+-\d+$", "Opens this estimate's page.")],
    "project-approvals": [(r"^WF-\d+-\d+$", "Opens this approval request's page.")],
}
TABLE_NAMES = {"project-tenure": "Tenements", "project-programmes": "Programmes", "project-drilling": "Drillholes",
               "project-assays": "Sample batches", "project-budget": "Programme ledgers", "project-approvals": "Approvals",
               "project-activity": "Activity", "project-resource": "Estimates"}
for P, table in TABLE_NAMES.items():
    if P not in ("project-activity", "project-resource"): C({"page": P, "text_regex": r"^Sort by "}, f"{table} table header",
      "Sorts the table by the column named in the label; pressing again reverses the order.", "Filtering rows; the table lists all of this project's records of its kind.",
      note="Generic: every column header button.")
    if P not in ("project-tenure", "project-resource"):
        C({"page": P, "role": "button", "text_regex": r"^(First|Previous|Next|Last)$"}, f"{table} table footer pager",
          "Moves between pages of the table (50 rows per page): First, Previous, Next or Last page. The footer says which rows are showing.",
          "Moving between records or tabs.", note="Appears only when the table has more than 50 rows.")
    for rx, what in ID_LINKS.get(P, []):
        C({"page": P, "role": "link", "text_regex": rx}, f"{table} table", what, "Changing the record (its own page, which this link opens).",
          note="Keyed on the id format, not on a record.")
    if P in ("project-programmes", "project-drilling", "project-assays", "project-budget", "project-approvals"):
        C({"page": P, "role": "link", "text_regex": RECORD_LINK}, f"{table} table",
          "Opens the named record: a programme or request, or (Project column) the project's Overview.",
          "Changing the record (its own page, which this link opens).",
          note="Generic catch-all for record-name links on this page.")

# ---- Edit dialog
P = "project-edit-dialog"
R = "Edit project dialog"
C({"page": P, "text": "Close dialog"}, R + ", top right cross", "Closes the dialog without saving.", "Saving (that is Save).")
C({"page": P, "text_regex": r"^(Open )?Name$"}, R, "The project's name. Required; an empty name is not saved.", "The project id, fixed by auto-numbering.")
C({"page": P, "text": "Project geologist"}, R, "Reassigns the project geologist. The active geologists are selectable; inactive ones are listed for reference.",
  "The exploration manager, assigned automatically.")
C({"page": P, "text_regex": r"^(Open )?Forecast at year end"}, R,
  "The project manager's forecast of spend at fiscal year end, in the base currency.", "The approved budget, set at creation; later changes go through support.")
C({"page": P, "text_regex": r"^(Open )?Description$"}, R, "The project's free-text description.", "Posting a comment.")
C({"page": P, "role": "button", "text": "Cancel"}, R + ", bottom right", "Closes the dialog and discards the changes.", "Saving.")
C({"page": P, "role": "button", "text": "Save"}, R + ", bottom right", "Saves the changes to the project and closes the dialog ('Project saved').",
  "Recording a stage-gate decision or submitting anything for approval.")

# ---- Stage-gate dialog
P = "project-stage-gate-dialog"
R = "Stage-gate decision dialog"
C({"page": P, "text": "Close dialog"}, R + ", top right cross", "Closes the dialog without recording anything.", "Recording the decision.")
C({"page": P, "role": "radio", "text_regex": r"^Advance to "}, R + ", Decision choices",
  "Choose to advance the project to the next pipeline stage named in the label. From the final stage the label says it hands over to the development group, which closes the project in exploration.",
  "Holding or relinquishing. Record decision records the choice.")
C({"page": P, "role": "radio", "text_regex": r"^Place on hold at\s"}, R + ", Decision choices",
  "Choose to place the project on hold at its current stage.", "Closing the project (that is Relinquish). Offered while the project is active.")
C({"page": P, "role": "radio", "text_regex": r"^Resume the project at\s"}, R + ", Decision choices",
  "Choose to resume a project that is on hold, at its current stage.", "Advancing it. Offered only while the project is on hold.")
C({"page": P, "role": "radio", "text_regex": r"^Relinquish and close"}, R + ", Decision choices",
  "Choose to relinquish: closes the project, lapses its tenements at the next expiry and makes its records read-only. Permanent in the application; the confirm button turns red.",
  "Putting the project on hold (that is Place on hold).")
C({"page": P, "text_regex": r"^(Open )?Reasoning"}, R,
  "The reasoning for the decision: what the results showed and why. At least twenty characters; written to the audit log verbatim.",
  "A comment on the project. Record decision needs at least twenty characters here.")
C({"page": P, "role": "button", "text": "Cancel"}, R + ", bottom right", "Closes the dialog without recording a decision.", "Recording the decision.")
C({"page": P, "role": "button", "text": "Record decision"}, R + ", bottom right",
  "Records the chosen decision with the reasoning, notifies the project team and closes the dialog.",
  "Requesting approval (Approvals). With reasoning under twenty characters it shows an error and the dialog stays open.")

# ---- Lodge renewal dialog
P = "tenement-renewal-dialog"
R = "Lodge a renewal dialog"
C({"page": P, "text": "Close dialog"}, R + ", top right cross", "Closes the dialog without lodging.", "Lodging the renewal.")
C({"page": P, "role": "button", "text": "Cancel"}, R + ", bottom right", "Closes the dialog without lodging.", "Lodging the renewal.")
C({"page": P, "role": "button", "text": "Submit for renewal"}, R + ", bottom right",
  "Lodges the renewal: creates the tenement-renewal approval request (Finance expenditure check, then Tenure lodgement) and marks the tenement 'renewal lodged'.",
  "Approving the renewal; that happens step by step on the request in Approvals.")

atlas = {
    "app": "ADIT",
    "version": "2026-09-22",
    "area": "projects",
    "selectors": {"dialog": ["dialog[open]"]},
    "pages": pages,
    "controls": controls,
}
json.dump(atlas, open(OUT, "w"), indent=1, ensure_ascii=False)
print(len(pages), "pages", len(controls), "controls")

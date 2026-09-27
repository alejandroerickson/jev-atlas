"""Builds jev-atlas/atlas/parts/approvals.json. Scratch builder; the JSON is the deliverable."""
# Copied from the area author's scratch directory on 2026-09-22 by the atlas merger;
# paths rewritten to be relative to this file and to $JEV_CLONE (the harness copy).
import os as _os, pathlib as _pl
_PARTS = _pl.Path(_os.environ.get("ADIT_PARTS_DIR") or _pl.Path(__file__).resolve().parents[2] / "atlas" / "parts")
_HARNESS = _os.environ.get("JEV_CLONE", str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'vendor' / 'jev-ultrafast')).rstrip("/") + "/jev_ultrafast/"

import json

OUT = str(_PARTS / "approvals.json")

WF_TITLE_PREFIX = ("(Programme approval|Budget variance|Stage-gate decision|Land access agreement|"
                   "Work permit|Resource release|Tenement renewal|Purchase order): ")

# ---------------------------------------------------------------- facts: queue
Q_VIEW = r"""(() => { const h=document.querySelector('main .head h1'); if(!h) return null;
 const meta=[...document.querySelectorAll('main .head .meta > span')].map(s=>s.textContent.trim()).filter(Boolean);
 const cut=document.querySelector('nav.l2 a[aria-current="page"]');
 return 'Queue view: '+h.textContent.trim()+(meta.length?' ('+meta.join('; ')+')':'')+
  (cut?'. Highlighted in the left column: '+[...cut.childNodes].map(n=>n.textContent.trim()).filter(Boolean).join(' ')+'.':''); })()"""

Q_TICKETS = r"""(() => { const t=[...document.querySelectorAll('main .tickets a.ticket')]; if(!t.length) return null;
 return 'Tickets (requests whose current step is yours, most urgent first): '+t.map(a=>{
  const g=s=>(a.querySelector(s)?.textContent||'').trim().replace(/\s+/g,' ');
  return g('.t')+' ['+g('.sc')+']'; }).join(' | '); })()"""

Q_ROWS = r"""(() => { const tb=document.querySelector('main table.tbl'); if(!tb) return null;
 const heads=[...tb.querySelectorAll('thead th')].map(th=>th.textContent.trim().toLowerCase());
 const col=n=>heads.indexOf(n);
 const want=['request','title','workflow','status','current step','due'];
 const rows=[...tb.querySelectorAll('tbody tr')];
 const foot=(document.querySelector('main .tbl-foot')?.textContent||'').trim();
 if(!rows.length || (rows.length===1 && rows[0].cells.length===1)) return 'Table: no requests in this view.';
 const out=rows.slice(0,20).map(r=>want.filter(w=>col(w)>=0).map(w=>(r.cells[col(w)]?.textContent||'').trim().replace(/\s+/g,' ')||'—').join(' · '));
 return 'Table rows ('+(foot||rows.length+' rows')+(rows.length>20?', first 20 shown':'')+'; request · title · workflow · status · current step and its role · due): '+out.join(' | '); })()"""

Q_SORT = r"""(() => { const th=[...document.querySelectorAll('main table.tbl thead th[aria-sort]')].find(t=>['ascending','descending'].includes(t.getAttribute('aria-sort')));
 return th ? 'Table sorted by '+th.textContent.trim()+', '+th.getAttribute('aria-sort')+'.' : null; })()"""

# ---------------------------------------------------------------- facts: detail
D_HEAD = r"""(() => { const h=document.querySelector('main .head h1'); if(!h) return null;
 const id=(h.querySelector('.id')?.textContent||'').trim();
 const title=[...h.childNodes].filter(n=>!(n.nodeType===1 && n.classList.contains('id'))).map(n=>n.textContent).join('').trim();
 const m=document.querySelector('main .head .meta');
 const status=(m?.querySelector('.chip')?.textContent||'').trim();
 const parts=m?[...m.children].filter(e=>!e.classList.contains('chip')).map(e=>e.textContent.trim()).filter(Boolean):[];
 return 'Request in view: '+id+' — '+title+'. Status: '+(status||'unknown')+'. Workflow and project: '+parts.join('; ')+'.'; })()"""

D_ACTIONS = r"""(() => { if(!document.querySelector('main .head h1')) return null;
 const who=(document.querySelector('button[aria-label*="Account menu"]')?.getAttribute('aria-label')||'').replace(/\.?\s*Account menu.*$/,'').trim();
 const b=[...document.querySelectorAll('main .head .actions button')].filter(e=>e.checkVisibility()).map(e=>e.textContent.trim());
 const status=(document.querySelector('main .head .meta .chip')?.textContent||'').trim();
 if(b.length) return (who?who+'. ':'')+'Actions offered to you on this request: '+b.join(', ')+'.';
 return (who?who+'. ':'')+(status && status!=='pending' ? 'Request status: '+status+'; decisions on this request are complete.' : 'Decision buttons: offered to the person in the role that owns the current step, named in Workflow steps (Withdraw: to the requester). To act as that person, switch user in the account menu.'); })()"""

D_NOTICE = r"""(() => { const n=[...document.querySelectorAll('main > p.notice, main .notice')].filter(e=>!e.closest('dialog')&&e.checkVisibility()).map(e=>e.textContent.trim().replace(/\s+/g,' '));
 return n.length ? 'Notice: '+n.join(' | ') : null; })()"""

D_STEPS = r"""(() => { const li=[...document.querySelectorAll('main ol.steps > li')]; if(!li.length) return null;
 return 'Workflow steps: '+li.map(l=>{ const g=s=>(l.querySelector(s)?.textContent||'').trim().replace(/\s+/g,' ');
  const st=g('.d'); return g('.n')+' ('+g('.who')+')'+(st?' — '+st:' — upcoming'); }).join(' → '); })()"""

D_REQUEST = r"""(() => { const kv=document.querySelector('main dl.kv'); if(!kv) return null;
 const dt=[...kv.querySelectorAll('dt')]; const txt=e=>{ if(!e) return ''; const w=document.createTreeWalker(e,4), a=[]; let n; while((n=w.nextNode())){ const t=n.textContent.trim(); if(t) a.push(t); } return a.join(' ').replace(/\s+/g,' '); };
 const pairs=dt.map(d=>d.textContent.trim()+' = '+txt(d.nextElementSibling));
 const slots=[...document.querySelectorAll('main .stamp .slot')].map(s=>(s.querySelector('.l')?.textContent||'').trim()+' = '+(s.querySelector('.f')?.textContent||'').trim().replace(/\s+/g,' '));
 return 'Request details: '+pairs.concat(slots).join('; '); })()"""

D_COMMENTS = r"""(() => { const f=document.querySelector('main form.comment-form'); if(!f) return null;
 const sec=f.closest('section'); const n=(sec?.querySelector('.ph .r')?.textContent||'').trim();
 const ta=f.querySelector('textarea'); const btn=f.querySelector('button[type=submit]');
 return 'Comments: '+(n||'0')+'. Comment box: '+(ta&&ta.value.trim()?'"'+ta.value.trim().slice(0,80)+'" typed, not posted':'empty')+'; Post comment '+(btn&&!btn.disabled?'enabled':'disabled until text is typed')+'.'; })()"""

# ---------------------------------------------------------------- facts: dialogs
DLG = r"""(() => { const d=[...document.querySelectorAll('dialog.dlg[open]')].find(e=>e.checkVisibility()); if(!d) return null;
 const t=(d.querySelector('h2')?.textContent||'').trim(); const sum=(d.querySelector('.sum')?.textContent||'').trim();
 const note=[...d.querySelectorAll('form .notice')].map(e=>e.textContent.trim()).join(' ');
 const fields=[...d.querySelectorAll('label.field')].map(l=>{ const name=(l.querySelector('span')?.textContent||'').trim();
  const v=(l.querySelector('textarea,input')?.value||'').trim(); const err=(l.querySelector('.error')?.textContent||'').trim();
  return name+' = '+(v?'"'+v.slice(0,80)+'"':'empty')+(err?' (invalid: '+err+')':''); });
 return 'Dialog: '+t+'. '+sum+(note?' '+note:'')+' Fields: '+fields.join('; ')+'.'; })()"""

# ---------------------------------------------------------------- pages
pages = [
    {
        "id": "approval-detail",
        "match": {"url_regex": "#/approvals/[^/?#]+"},
        "name": "Approval request",
        "what": ("One workflow request (an approval request, id format WF-YYYY-0000): its title, status chip, workflow, "
                 "project and requester in the head; a notice saying whose step it is waiting on or that the step is overdue; "
                 "the Request panel (what is asked, the Subject record it acts on, amount where the workflow carries one, "
                 "requester, submitted and due dates, and, when the subject is a programme, its budget, spend to date, dates and phase); "
                 "the Workflow steps panel listing each step with the role and person that owns it, its service level in days, and whether it is "
                 "approved, returned, current or not yet reached; Comments; and other requests on the same project. "
                 "What the head offers depends on who is signed in: Approve, Return and Reject appear only when the current step belongs to "
                 "the signed-in user's role; Withdraw appears instead for the requester of a pending request whose current step is not theirs; "
                 "a decided request (approved, returned, rejected, withdrawn) is complete. "
                 "The eight workflows differ on this page in their step chain, the kind of Subject record (programme, project, estimate, "
                 "tenement or purchase order), and whether an Amount is shown (programme approval, budget variance and purchase order carry one)."),
        "not_here": ("Editing the subject record itself (programme budget, estimate, tenement, project): that record's own page, "
                     "reached through the Subject link; approval updates it when the last step passes. "
                     "Acting as the person or role that owns the current step: switch user in the account menu at the top right "
                     "(People and roles lists who holds each role). "
                     "Lists of requests, and the filters by view and by workflow: the Approvals queue (breadcrumb or left column). "
                     "Workflow definitions and step owners: fixed by the product's support team, shown read-only under Admin, Workflows."),
        "leads_to": {
            "Approve / Return / Reject (head)": "approval-approve-dialog / approval-return-dialog / approval-reject-dialog",
            "Approvals (breadcrumb) and left-column queue links": "approvals-queue",
            "Subject link (Request panel)": "the subject record's page (programme, project, estimate, tenure or programmes list)",
            "Project link (head)": "the project's page",
            "Request id links (Other requests on this project)": "approval-detail",
        },
        "facts_js": [D_HEAD, D_ACTIONS, D_NOTICE, D_STEPS, D_REQUEST, D_COMMENTS],
    },
    {
        "id": "approvals-queue",
        "match": {"url_regex": "#/approvals/?(\\?.*)?$"},
        "name": "Approvals queue",
        "what": ("The queue of workflow requests. The left column picks the cut: under Queue, Awaiting me (requests whose current step "
                 "belongs to the signed-in user's role; the default view), All pending, Raised by me and Decided; under By type, one link per "
                 "workflow, each showing only pending requests of that workflow. The head names the view, counts requests and overdue ones, and "
                 "says who is signed in and in which role. In Awaiting me the most urgent requests (up to four) also appear as ticket cards above "
                 "the table, the lead ticket first. The table lists each request's id, title, workflow, status, current step with the role that "
                 "owns it, requester, amount, submitted and due dates; column headers sort it. Every id, title and ticket opens the request, "
                 "which is where decisions are made. What appears under Awaiting me and Raised by me changes with the signed-in user."),
        "not_here": ("Approve, Return, Reject, Withdraw and comments: the head and panels of the request's own page (its id, title or ticket opens it). "
                     "Working as another person, and so seeing the requests awaiting them: switch user in the account menu at the "
                     "top right. Free-text search: the top-bar search box, across the tenant. By type links cover pending requests; "
                     "decided requests are under Decided. Overdue requests also surface in the Portfolio attention ledger."),
        "leads_to": {
            "Ticket card, request id or title": "approval-detail",
            "Queue and By type links (left column)": "approvals-queue (another view)",
        },
        "facts_js": [Q_VIEW, Q_TICKETS, Q_ROWS, Q_SORT],
    },
    {
        "id": "approval-approve-dialog",
        "layer": "overlay",
        "match": {"selector": "dialog.dlg[open][aria-label^=\"Approve: \"]"},
        "name": "Approve dialog",
        "what": ("Confirms passing the current step of the request. Its summary says what happens: either the request moves to the next "
                 "step (named, with its role), or this is the final step and the request will be approved and its subject updated; a budget "
                 "variance also states how much the programme's approved budget rises. An optional note records conditions."),
        "not_here": ("Sending the request back for revision is Return, and ending it is Reject; both are separate dialogs from the request head. "
                     "The decision is recorded when the dialog's Approve button is pressed; Cancel, the close cross or Escape leave the request as it was."),
        "facts_js": [DLG],
    },
    {
        "id": "approval-return-dialog",
        "layer": "overlay",
        "match": {"selector": "dialog.dlg[open][aria-label=\"Return to the requester\"]"},
        "name": "Return to the requester dialog",
        "what": ("Sends the request back to its requester to revise and resubmit; the rest of the request stays as it is. A reason is required "
                 "(at least 10 characters) and the dialog shows an error under Reason and stays open if it is shorter."),
        "not_here": ("Ending the workflow for good is Reject; passing the step is Approve. Cancel, the close cross or Escape leave the "
                     "request unchanged, but text typed into Reason stays in the dialog if it is reopened."),
        "facts_js": [DLG],
    },
    {
        "id": "approval-reject-dialog",
        "layer": "overlay",
        "match": {"selector": "dialog.dlg[open][aria-label^=\"Reject \"]"},
        "name": "Reject dialog",
        "what": ("Ends the workflow: the request is rejected and the requester is notified with the reason. A reason is required "
                 "(at least 10 characters); a shorter one shows an error under Reason and the dialog stays open."),
        "not_here": ("Asking the requester to revise without ending the workflow is Return; passing the step is Approve. Cancel, the close "
                     "cross or Escape leave the request unchanged."),
        "facts_js": [DLG],
    },
]

# ---------------------------------------------------------------- controls
C = []
def add(key, region, what, not_for, note=None, options=None):
    e = {"key": key, "region": region, "what": what, "not_for": not_for}
    if note: e["note"] = note
    if options: e["options"] = options
    C.append(e)

# Dialog controls first. Their submit and Cancel keys also carry text_regex so they outweigh the
# head buttons of the same name (which stay in view, covered, while a dialog is open).
for pid, word, what, nf in [
    ("approval-approve-dialog", "Approve",
     "Confirms the approval: the current step passes, and the request moves to its next step or, on the last step, is approved and its subject updated.",
     "Returning or rejecting (separate dialogs). The note is optional, so this works with the note empty."),
    ("approval-return-dialog", "Return",
     "Confirms sending the request back to the requester to revise, with the reason typed above.",
     "Rejecting (ends the workflow) or approving. Needs a Reason of at least 10 characters; a shorter one shows an error and keeps the dialog open."),
    ("approval-reject-dialog", "Reject",
     "Confirms rejecting the request: the workflow ends and the requester receives the reason typed above.",
     "Returning for revision (Return) or approving. Needs a Reason of at least 10 characters; a shorter one shows an error and keeps the dialog open."),
]:
    add({"page": pid, "role": "button", "text": word, "text_regex": f"^{word}$"},
        "Dialog footer, right", what, nf)
    add({"page": pid, "role": "button", "text": "Cancel", "text_regex": "^Cancel$"},
        "Dialog footer, left", "Closes the dialog; the request stays as it was.",
        f"Confirming (that is the {word} button beside it). Typed text is kept if the dialog is reopened.")
    add({"page": pid, "text": "Close dialog"},
        "Dialog title bar, top right (cross)", "Closes the dialog, like Cancel; the request stays as it was.",
        f"Confirming the {word.lower()}.")

add({"page": "approval-approve-dialog", "role": "textbox", "row_label": "Note (optional)"},
    "Approve dialog form", "Optional note recorded with the approval (conditions, if any) in the audit log.",
    "A comment on the request (that is the Comments panel) or a reason for returning or rejecting. May be left empty.")
for pid, verb in [("approval-return-dialog", "returned"), ("approval-reject-dialog", "rejected")]:
    add({"page": pid, "role": "textbox", "row_label": "Reason"},
        f"{'Return' if verb == 'returned' else 'Reject'} dialog form",
        f"Required reason sent to the requester explaining why the request is {verb}; at least 10 characters.",
        "An optional approval note or a general comment. Its label grows an error message when the reason is too short.")

# Detail page head
add({"page": "approval-detail", "role": "button", "text": "Approve"},
    "Request head, action buttons",
    "Opens the Approve dialog to pass the current step. Shown only when the current step belongs to the signed-in user's role.",
    "Confirming: the Approve dialog it opens. Sending back to revise: Return. Ending the workflow: Reject.")
add({"page": "approval-detail", "role": "button", "text": "Return"},
    "Request head, action buttons",
    "Opens the Return dialog to send the request back to its requester to revise; a reason is required. Shown only to the current step's role.",
    "Ending the workflow: Reject. The requester's own cancellation: Withdraw.")
add({"page": "approval-detail", "role": "button", "text": "Reject"},
    "Request head, action buttons",
    "Opens the Reject dialog to end the workflow; a reason is required and is sent to the requester. Shown only to the current step's role.",
    "Letting the requester revise and resubmit: Return.")
add({"page": "approval-detail", "role": "button", "text": "Withdraw"},
    "Request head, action buttons",
    "Withdraws the signed-in user's own pending request at once (no confirmation dialog observed); the request leaves every pending view.",
    "Deciding a step: Approve, Return and Reject, shown to the step's owner. Withdraw is shown to the requester while the current step belongs to another role.")
add({"page": "approval-detail", "role": "link", "text": "Approvals"},
    "Breadcrumb, above the title", "Opens the Approvals queue (Awaiting me view).",
    "The top-bar Approvals section link, which reads with its awaiting count.")
for st in ("pending", "approved", "returned", "rejected", "withdrawn"):
    add({"page": "approval-detail", "role": "link", "row_label": st},
        "Request head, meta line after the workflow name",
        "Opens the project this request belongs to.",
        "The Subject record in the Request panel, which may be a programme, estimate, tenement or order rather than the project.",
        note="Keyed on the status chip text, which the harness reads as this link's row label; one entry per status.")
add({"page": "approval-detail", "role": "link", "row_label": "Subject"},
    "Request panel, Subject row",
    ("Opens the record the request acts on; the small word before the id says its kind: programme (programme approval, budget "
     "variance, work permit), project (stage-gate decision, land access agreement), estimate (resource estimate release), "
     "tenement (tenement renewal, opens the project's tenure), purchase (purchase order, opens the project's programmes list)."),
    "The project link in the head. Deciding the request: the head's decision buttons.")
add({"page": "approval-detail", "role": "textbox", "row_label": "Add a comment"},
    "Comments panel", "Comment on the request; comments notify the requester, and @ with a first name notifies a colleague.",
    "A decision note or a reason (those are in the Approve, Return and Reject dialogs). A comment leaves the request's status as it is.")
add({"page": "approval-detail", "text": "Post comment"},
    "Comments panel", "Posts the typed comment to the request's Comments list under the signed-in user's name.",
    "Approving or returning. Enabled once the comment box has text.")
add({"page": "approval-detail", "role": "link", "text_regex": "^WF-\\d{4}-\\d{4}$"},
    "Other requests on this project (table, Request column)", "Opens that other request of the same project.",
    "The request in view. Sorting and filtering requests: the Approvals queue.",
    note="Generic: matches every request id link in the related-requests table.")
for pid in ("approval-detail", "approvals-queue"):
    add({"page": pid, "text": "Dismiss"},
        "Toast message, bottom of the screen", "Hides the confirmation message about the last action.",
        "Undoing the action the message reports; the action stays recorded.",
        note="Toasts are an app-wide component; merger may prefer one global entry.")

# Queue page
add({"page": "approvals-queue", "role": "link", "text_regex": "·\\s+due\\s+\\d{4}-\\d{2}-\\d{2}"},
    "Tickets above the table (Awaiting me only)",
    "Opens this request: one of the most urgent requests whose current step is yours, the lead one first.",
    "Deciding: the request's own page, which this opens.",
    note="Generic: one entry for every ticket card; the card's label is its whole text.")
add({"page": "approvals-queue", "role": "link", "text_regex": "^" + WF_TITLE_PREFIX + "(?!.*·\\s+due\\s+\\d)"},
    "Approvals table, Title column", "Opens this request (same destination as its id).",
    "Filtering by workflow (the By type links on the left).",
    note="Generic: matches every title link; titles start with the workflow name (resource estimate release titles start 'Resource release:').")
add({"page": "approvals-queue", "role": "link", "text_regex": "^WF-\\d{4}-\\d{4}$"},
    "Approvals table, Request column", "Opens this request's page.",
    "Sorting (the column header) or filtering.",
    note="Generic: matches every request id link in the table.")
add({"page": "approvals-queue", "role": "button", "text_regex": "^Sort by "},
    "Approvals table, column headers",
    "Sorts the table by this column; pressing again reverses the order. Sortable columns carry this button.",
    "Filtering (the left column does that). Changes the order of the rows in view.",
    note="Generic: one entry for all eight sortable headers (labels 'Sort by Request' … 'Sort by Due').")

# Left column (also shown on the request page, so not page-keyed)
for label, what, nf in [
    ("Awaiting me", "Requests whose current step belongs to the signed-in user's role (the default view, with ticket cards). The count is how many.",
     "Requests you raised (Raised by me) or everything pending (All pending). Changes when a different user is signed in."),
    ("All pending", "Every pending request in the tenant, whoever owns the current step, in due-date order.",
     "The ones you can act on (Awaiting me). Deciding a listed request belongs to its current step's role."),
    ("Raised by me", "Requests the signed-in user submitted, pending or decided; a pending one can be withdrawn from its page.",
     "Requests waiting on you (Awaiting me)."),
    ("Decided", "Closed requests: approved, returned, rejected and withdrawn.",
     "Pending requests (All pending, or the By type links)."),
]:
    add({"row_label": "Queue", "role": "link", "text_regex": f"^{label}( \\d+)?$"},
        "Left column, Queue", what, nf, note="Label carries a live count after the name.")

TYPES = [
    ("Programme approval", "a costed programme, before mobilisation",
     "Technical review (Project Geologist) → Budget check (Finance Controller) → Manager approval (Exploration Manager)",
     "Subject is the programme; shows an amount and the programme's budget panel. Final approval makes the programme approved."),
    ("Budget variance", "a forecast overrun above the variance threshold",
     "Finance review (Finance Controller) → Manager approval (Exploration Manager)",
     "Subject is the programme; shows the overrun amount. Final approval raises the programme's approved budget by that amount."),
    ("Stage-gate decision", "a project at the end of a stage (advance, hold or relinquish)",
     "Geology recommendation (Project Geologist) → Finance review (Finance Controller) → Gate decision (Exploration Manager)",
     "Subject is the project; no amount."),
    ("Land access agreement", "access to private or community land",
     "Tenure review (Tenure & Permitting Officer) → Manager sign-off (Exploration Manager)",
     "Subject is the project; no amount."),
    ("Work permit", "ground disturbance (a regulatory permit)",
     "Permit lodgement → Regulator decision (both Tenure & Permitting Officer)",
     "Subject is the programme; no amount."),
    ("Resource estimate release", "an estimate leaving review",
     "Database sign-off (Database Geologist) → QP review (Project Geologist) → Manager release (Exploration Manager)",
     "Subject is the estimate; no amount. Final approval releases the estimate."),
    ("Tenement renewal", "a tenement before expiry",
     "Expenditure check (Finance Controller) → Renewal lodgement (Tenure & Permitting Officer)",
     "Subject is the tenement; no amount. Final approval records the renewal as lodged."),
    ("Purchase order", "orders above the delegated limit",
     "Logistics check (Field Logistics Coordinator) → Finance approval (Finance Controller)",
     "Subject is the purchase order; shows the order amount."),
]
for name, raised, steps, diff in TYPES:
    add({"row_label": "By type", "role": "link", "text_regex": f"^{name}( \\d+)?$"},
        "Left column, By type",
        f"Shows pending {name.lower()} requests only (raised for {raised}). Steps: {steps}. {diff}",
        "Decided requests of this workflow (Decided), or the ones awaiting you (Awaiting me). Count after the name is pending requests.",
        note="Label carries a live count after the name.")

atlas = {
    "app": "ADIT",
    "version": "2026-09-22",
    "selectors": {"dialog": ["dialog[open]"]},
    "pages": pages,
    "controls": C,
}
json.dump(atlas, open(OUT, "w"), indent=2, ensure_ascii=False)
print(len(pages), "pages", len(C), "controls")

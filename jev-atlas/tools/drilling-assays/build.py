"""Builds jev-atlas/atlas/parts/drilling-assays.json. Run: python3 build.py"""
# Copied from the area author's scratch directory on 2026-09-22 by the atlas merger;
# paths rewritten to be relative to this file and to $JEV_CLONE (the harness copy).
import os as _os, pathlib as _pl
_PARTS = _pl.Path(_os.environ.get("ADIT_PARTS_DIR") or _pl.Path(__file__).resolve().parents[2] / "atlas" / "parts")
_HARNESS = _os.environ.get("JEV_CLONE", str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'vendor' / 'jev-ultrafast')).rstrip("/") + "/jev_ultrafast/"

import json

OUT = str(_PARTS / "drilling-assays.json")

HOLE_RE = r"^[A-Z]{2}-(DDH|RC|AC|Sonic)-\d{3}$"
BATCH_RE = r"^LAB-\d{2}-\d{4,6}$"
PRG_RE = r"^PRG-\d{4}-\d{3}$"
# A link whose text is a free name (project, programme, laboratory): everything that is
# not one of the fixed labels on these pages, the global header, or an id pattern.
NAME_LINK_RE = (
    r"^(?!(ADIT home|Portfolio|Projects|Programmes|Drilling|Assays|Resources|Approvals|Optimiser|Admin"
    r"|User Manual|Skip to content|Open|Cancel|Clear|Tolerances|New dispatch|All holes|Drilling now|Planned"
    r"|Awaiting sampling|Abandoned|Significant intercepts|All batches|At the laboratory|Received, unreviewed"
    r"|QAQC hold|Accepted|QAQC summary|Sample register)\b)(?!(hole|batch) )(?![A-Z]{2}-(DDH|RC|AC|Sonic)-\d{3}$)"
    r"(?!LAB-\d)(?!PRG-\d).+"
)

# ---------- facts_js ----------
HEAD_FACT = (
    "(() => { const h = document.querySelector('main h1'); if (!h) return null;"
    " const m = [...document.querySelectorAll('main .head .meta > *')].map(e => e.textContent.replace(/\\s+/g, ' ').trim()).filter(Boolean);"
    " return 'Heading: ' + h.textContent.trim() + (m.length ? ' (' + m.join(' · ') + ')' : ''); })()"
)
FILTER_FACT = (
    "(() => { const f = document.querySelector('main .filters'); if (!f) return null;"
    " const parts = [...f.querySelectorAll('label.field')].map(l => { const n = l.querySelector('span')?.textContent.trim();"
    " const c = l.querySelector('input,select'); if (!n || !c) return null;"
    " const v = c.tagName === 'SELECT' ? c.selectedOptions[0]?.textContent.trim() : (c.value ? '\"' + c.value + '\"' : 'empty');"
    " return n + ' = ' + v; }).filter(Boolean);"
    " const cb = f.querySelector('input[type=checkbox]'); if (cb) parts.push('Significant only = ' + (cb.checked ? 'ticked' : 'not ticked'));"
    " const clear = [...f.querySelectorAll('a')].some(a => a.textContent.trim() === 'Clear');"
    " return 'Filters: ' + parts.join('; ') + (clear ? ' (a filter is applied; Clear removes it)' : ''); })()"
)
PAGER_FACT = (
    "(() => { const out = [...document.querySelectorAll('main .tbl-foot')].map(t => { const s = t.querySelector(':scope > span')?.textContent.trim();"
    " const p = t.querySelector('[aria-current=page]')?.textContent.trim(); return s ? s + (p ? ', page ' + p : '') : null; }).filter(Boolean);"
    " return out.length ? 'Table rows: ' + out.join(' | ') : null; })()"
)
LEFT_FACT = (
    "(() => { const a = [...document.querySelectorAll('aside a[aria-current=page], aside a.active, aside a[aria-current=true]')]"
    ".map(e => e.textContent.replace(/\\s+/g, ' ').trim()); return a.length ? 'Left column, current view: ' + a.join(', ') : null; })()"
)
TOAST_FACT = (
    "(() => { const t = [...document.querySelectorAll('.toast')].filter(e => e.checkVisibility()).map(e => e.innerText.replace(/\\s+/g, ' ').replace(/ Open$/, '').trim());"
    " return t.length ? 'Confirmation shown: ' + t.join(' | ') : null; })()"
)
ACTIONS_FACT = (
    "(() => { const want = ['Update hole', 'Import results', 'Accept batch', 'Place on hold', 'Reject'];"
    " const hd = document.querySelector('main .head'); if (!hd) return null;"
    " const b = [...document.querySelectorAll('main button')].filter(x => !x.closest('dialog') && want.includes(x.textContent.trim()) && x.checkVisibility()).map(x => x.textContent.trim());"
    " return 'Record actions: ' + (b.length ? 'offered to the signed-in user: ' + b.join(', ') : 'shown according to the signed-in role and the record status; to act with another role, switch user in the account menu to a person who holds it (People and roles lists who holds each role)'); })()"
)
QAQC_FAIL_FACT = (
    "(() => { const s = [...document.querySelectorAll('main section, main .panel')].find(x => /^QAQC failures/.test(x.querySelector('h2')?.textContent.trim() || ''));"
    " if (!s) return null; const n = s.querySelector('.ph .r')?.textContent.trim(); return 'QAQC failures listed on this batch: ' + (n || '?'); })()"
)
DISPATCH_FACT = (
    "(() => { const m = document.querySelector('main'); if (!m || !/New sample dispatch/.test(m.querySelector('h1')?.textContent || '')) return null;"
    " const sel = [...m.querySelectorAll('label.field')].map(l => { const s = l.querySelector('select'); return s ? l.querySelector('span')?.textContent.trim() + ' = ' + s.selectedOptions[0]?.textContent.trim() : null; }).filter(Boolean);"
    " const holes = [...m.querySelectorAll('.pills label')].map(l => l.textContent.trim() + (l.querySelector('input')?.checked ? ' [included]' : ' [not included]'));"
    " const sub = [...m.querySelectorAll('button')].find(b => b.textContent.trim() === 'Submit dispatch');"
    " return 'Dispatch form: ' + sel.join('; ') + '; logged holes awaiting dispatch: ' + (holes.length ? holes.join(', ') : 'listed once a hole of this project is logged (on the hole page); Project changes the list') +"
    " '; Submit dispatch: ' + (!sub ? 'shown to roles with assay rights; to act with one, switch user in the account menu to a person who holds it (People and roles lists who holds each role)' : sub.disabled ? 'disabled: it enables once a hole is included, for a role that dispatches samples' : 'enabled'); })()"
)
DIALOG_FORM_FACT = (
    "(() => { const d = document.querySelector('dialog[open]'); if (!d) return null;"
    " const f = [...d.querySelectorAll('label')].map(l => { const c = l.querySelector('input,select,textarea'); if (!c) return null;"
    " const n = (l.querySelector('span')?.textContent || l.textContent).replace(/\\s+/g, ' ').trim();"
    " let v; if (c.type === 'checkbox') v = c.checked ? 'ticked' : 'not ticked'; else if (c.tagName === 'SELECT') v = c.selectedOptions[0]?.textContent.trim(); else v = c.value ? '\"' + c.value + '\"' : 'empty';"
    " const req = c.required ? (c.checkValidity() ? ' (required)' : ' (required, invalid)') : ''; return n + ' = ' + v + req; }).filter(Boolean);"
    " const sum = d.querySelector('.sum')?.textContent.trim();"
    " return 'Dialog \"' + (d.getAttribute('aria-label') || '') + '\"' + (sum ? ': ' + sum : '') + (f.length ? ' Fields: ' + f.join('; ') : ''); })()"
)

# ---------- virtual controls ----------
DISPATCH_VIRTUAL = r"""(() => { try { const m = document.querySelector('main'); if (!m) return [];
 return [...m.querySelectorAll('.pills label')].map((l, i) => { const t = l.textContent.trim(); const hole = t.split(' · ')[0];
 return { id: 'dispatch-hole:' + i, label: 'Include hole ' + t + ' in this dispatch', row_label: hole,
  region: 'New sample dispatch form, logged holes awaiting dispatch',
  what: 'Whether this logged hole goes in the dispatch. Type yes to include it, no to leave it out. Its samples are numbered and sent to the chosen laboratory when the dispatch is submitted.',
  not_for: 'Choosing the project or laboratory (the selects above); submitting (Submit dispatch). Holes of other projects: listed once Project names their project.',
  current_value: l.querySelector('input').checked ? 'yes' : 'no',
  set: '(v) => { const ls = [...document.querySelectorAll("main .pills label")]; const l = ls.find(x => x.textContent.trim() === ' + JSON.stringify(t) + '); if (!l) return false; const c = l.querySelector("input"); const want = !/^\\s*(no|n|false|0|off|exclude|untick|uncheck|remove)\\b/i.test(String(v)); if (c.checked !== want) c.click(); return c.checked === want; }' }; }); } catch (e) { return []; } })()"""

UPDATE_HOLE_VIRTUAL = r"""(() => { try { const d = document.querySelector('dialog[open]'); const c = d && d.querySelector('input[name="completed"]'); if (!c) return [];
 return [{ id: 'update-hole:completed', label: 'Completed date', row_label: 'Completed',
  region: 'Update hole dialog',
  what: 'The date the hole reached its final depth, as YYYY-MM-DD. Saved with the dialog.',
  not_for: 'Status or depth (their own fields in the dialog). An empty value clears the completion date.',
  current_value: c.value,
  set: '(v) => { const c = document.querySelector("dialog[open] input[name=completed]"); if (!c) return false; const s = String(v).trim(); const m = s.match(/(\\d{4})-(\\d{1,2})-(\\d{1,2})/); const val = m ? m[1] + "-" + m[2].padStart(2, "0") + "-" + m[3].padStart(2, "0") : s; const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set; setter.call(c, val); c.dispatchEvent(new Event("input", {bubbles: true})); c.dispatchEvent(new Event("change", {bubbles: true})); return c.value === val; }' }]; } catch (e) { return []; } })()"""


def page(pid, regex, name, what, not_here, leads_to, facts, **extra):
    p = {"id": pid, "match": {"url_regex": regex}, "name": name, "what": what, "not_here": not_here,
         "leads_to": leads_to, "facts_js": facts}
    p.update(extra)
    return p


def overlay(pid, selector, name, what, not_here, facts, **extra):
    p = {"id": pid, "layer": "overlay", "match": {"selector": selector}, "name": name, "what": what,
         "not_here": not_here, "facts_js": facts}
    p.update(extra)
    return p


pages = [
    page("drilling-intercepts", r"#/drilling/intercepts(\?|$)", "Intercepts",
         "Tenant-wide list of intercepts: runs of assayed samples above the commodity's cut-off, sorted by grade × length, with a scatter of length against grade over cut-off. By default only significant intercepts show (at least 1.5× cut-off over the commodity's minimum length); unticking Significant only shows every run above cut-off. Intercepts are computed from accepted assay batches and shown read-only.",
         "One hole's intercepts, grade profile and samples: that hole's page (its hole id). The drillhole list is under All holes in the left column. Batch review and QAQC are under Assays.",
         {"Hole id link": "drilling-hole", "All holes (left column)": "drilling-list", "Project link": "project page (Projects area)"},
         [HEAD_FACT, FILTER_FACT, PAGER_FACT, TOAST_FACT]),
    page("drilling-hole", r"#/drilling/(?!intercepts(\?|$))[^/?]+", "Drillhole record",
         "One drillhole: depth against plan, collar coordinates and RL, azimuth and dip, sample counts, best intercept, rig, logger, start and completion dates and the batches its samples went in. The downhole grade profile draws every assayed interval against the cut-off; the Intercepts table lists runs above cut-off; the Samples table lists every interval with grade, batch and QAQC flag. Users with hole.write see Update hole, which changes status, depth and completion date. Comments can be posted on the hole.",
         "Batch acceptance, holds, rejection and result import: the batch's page in Assays. Hole planning and rig scheduling live under Programmes. Other holes are in the drillhole list (Drilling breadcrumb or All holes).",
         {"Update hole": "update-hole-dialog", "Project link under the heading": "project page (Projects area)", "Programme link under the heading": "programme page (Programmes area)", "batch chip / Batch column link": "assays-batch", "Drilling breadcrumb / All holes": "drilling-list"},
         [HEAD_FACT, ACTIONS_FACT, PAGER_FACT, TOAST_FACT]),
    page("drilling-list", r"#/drilling/?(\?|$)", "Drillholes",
         "Every drillhole in the tenant across projects and programmes, filterable by hole id, project and hole type (DDH diamond, RC reverse circulation, AC aircore, Sonic). The left column cuts the list to holes drilling now, planned, awaiting sampling (logged) or abandoned. Columns give collar coordinates, azimuth, dip, planned and actual depth, best intercept and completion date; the chart shows holes completed by month by commodity. The list is read-only; status and depth change on a hole's own page.",
         "Changing a hole's status, depth or completion date is Update hole on that hole's page. Intercepts across the tenant are under Significant intercepts. Sample batches, dispatch and QAQC are under Assays. Programmes and rigs are under Programmes.",
         {"Hole id link": "drilling-hole", "Significant intercepts": "drilling-intercepts", "Project link": "project page (Projects area)", "Programme code link": "programme page (Programmes area)"},
         [HEAD_FACT, FILTER_FACT, PAGER_FACT, TOAST_FACT]),
    page("assays-new", r"#/assays/new(\?|$)", "New sample dispatch",
         "Dispatches samples to a laboratory: choose the project and the laboratory (each shown with its quoted turnaround), include one or more of that project's logged holes awaiting dispatch, and submit. Sample numbers are assigned on dispatch and control samples are inserted at the tenant rule (one standard, one blank and one field duplicate per twenty samples); the holes move to sampled and a new batch appears in the batch list. Only holes at status logged appear.",
         "Existing batches, their results and their review: the batch list and each batch's page. Holes join this form once their status is logged, which is set with Update hole on the hole's page. QAQC tolerances: Admin.",
         {"Cancel": "assays-batches", "Submit dispatch": "stays here; a confirmation names the new batch"},
         [HEAD_FACT, DISPATCH_FACT, TOAST_FACT], virtual_controls_js=DISPATCH_VIRTUAL),
    page("assays-qaqc", r"#/assays/qaqc(\?|$)", "QAQC summary",
         "Quality-control overview for received batches: the tolerances in force, the QAQC pass rate by month, failures by project, a table by laboratory (accreditation, batches received, checks, failures, pass rate, mean turnaround against quoted) and a table by project (checks, failures, pass rate, batches on hold). Read-only.",
         "Reviewing a particular batch's failures (accept, hold, reject) is on that batch's page. Changing the tolerances is Admin → QAQC tolerances (the Tolerances link). Individual samples are in the Sample register.",
         {"Tolerances": "Admin QAQC tolerances (Admin area)", "Laboratory link": "assays-batches (filtered to that laboratory)", "Project link in By project": "project's assays tab (Projects area)", "Bar in Failures by project": "assays-batches (filtered to that project)"},
         [HEAD_FACT, TOAST_FACT]),
    page("assays-samples", r"#/assays/samples(\?|$)", "Sample register",
         "Every sample in the tenant: sample number, hole, from and to depth, type (core, chip, standard, blank, duplicate), primary grade, batch and QAQC flag. Narrow by sample, hole or batch id, by project and by type before paging; only the first 5,000 matches are shown. Read-only.",
         "Batch-level review is on the batch page; a hole's own samples and grade profile are on the hole's page. Pass rates and failures by laboratory are in QAQC summary.",
         {"Hole id link": "drilling-hole", "Batch id link": "assays-batch"},
         [HEAD_FACT, FILTER_FACT, PAGER_FACT, TOAST_FACT]),
    page("assays-batch", r"#/assays/(?!(new|qaqc|samples)(\?|$))[^/?]+", "Sample batch",
         "One laboratory batch: status, laboratory, dispatch reference and method; sample count, QAQC insertions (standards, blanks, duplicates) and insertion rate, failures, share above cut-off, turnaround against the laboratory's quoted days, the holes in it, and dispatch and receipt dates. Lists each QAQC failure (sample, kind of check, measured against expected), primary samples by grade band, comments and every sample. Users with qaqc.review see the actions for the batch's status: Import results while it is at the laboratory; Accept batch, Place on hold and Reject once results are received (a held batch offers Accept batch and Reject).",
         "Dispatching new samples is New dispatch in the batch list. Tolerance settings are under Admin. A hole's intercepts are on the hole's page once the batch is accepted.",
         {"Import results": "import-results-dialog", "Accept batch": "accept-batch-dialog", "Place on hold": "hold-batch-dialog", "Reject": "reject-batch-dialog", "hole chip / Hole column link": "drilling-hole", "Project link": "project page (Projects area)", "Assays breadcrumb": "assays-batches"},
         [HEAD_FACT, ACTIONS_FACT, QAQC_FAIL_FACT, PAGER_FACT, TOAST_FACT]),
    page("assays-batches", r"#/assays/?(\?|$)", "Sample batches",
         "Every batch of samples sent to a laboratory, filterable by project and laboratory; the left column cuts the list to batches at the laboratory, received but unreviewed, on QAQC hold or accepted. Columns give project, laboratory, status, holes, sample count, QAQC insertions, failures, dispatch and receipt dates, turnaround and method. New dispatch starts a dispatch of logged holes. The list is read-only.",
         "Accepting, holding, rejecting or importing results for a batch is on that batch's page. Pass rates by laboratory are in QAQC summary; individual samples in Sample register. Drillholes are under Drilling.",
         {"Batch id link": "assays-batch", "New dispatch": "assays-new", "QAQC summary": "assays-qaqc", "Sample register": "assays-samples", "Project link": "project page (Projects area)"},
         [HEAD_FACT, FILTER_FACT, PAGER_FACT, TOAST_FACT]),
    overlay("update-hole-dialog", 'dialog[open]:has(input[name="depth"]):has(select[name="status"])', "Update hole dialog",
            "Changes this hole's status (planned, drilling, completed, abandoned, logged, sampled, assayed), its depth in metres and its completion date. Save writes all three and closes the dialog; Cancel or the cross closes without changing anything.",
            "Collar, orientation, rig and logger: recorded on the hole page, outside this dialog. Moving samples to a laboratory is New dispatch under Assays; assay results change holes to assayed on batch acceptance.",
            [DIALOG_FORM_FACT], virtual_controls_js=UPDATE_HOLE_VIRTUAL),
    overlay("import-results-dialog", 'dialog[open][aria-label^="Import results for "]', "Import results dialog",
            "Confirms importing this batch's results from its laboratory: the QAQC checks run against the tenant tolerances and the batch moves to received, ready for review. Import confirms; Cancel or the cross closes without importing.",
            "Accepting, holding or rejecting the batch: separate actions on the batch page once results are imported.",
            [DIALOG_FORM_FACT]),
    overlay("accept-batch-dialog", 'dialog[open][aria-label^="Accept "]', "Accept batch dialog",
            "Confirms accepting this batch: its grades are released to intercepts and estimates and its holes move to assayed. When the batch has QAQC failures, a required tick box confirms each failure has been reviewed. Accept confirms; Cancel or the cross closes without accepting.",
            "Withholding the batch while the laboratory re-runs checks is Place on hold; sending it back for re-assay is Reject.",
            [DIALOG_FORM_FACT]),
    overlay("hold-batch-dialog", 'dialog[open][aria-label$=" on QAQC hold"]', "Place on hold dialog",
            "Confirms putting this batch on QAQC hold: it stays out of intercepts and estimates until it is accepted. Place on hold confirms; Cancel or the cross closes without changing the batch.",
            "Accepting is Accept batch; returning to the laboratory for re-assay is Reject.",
            [DIALOG_FORM_FACT]),
    overlay("reject-batch-dialog", 'dialog[open]:has(textarea[placeholder^="Which checks failed"])', "Reject batch dialog",
            "Rejects this batch back to the laboratory for re-assay at the laboratory's cost; its holes return to sampled. A reason, sent to the laboratory, is required. Reject batch confirms; Cancel or the cross closes without rejecting.",
            "Holding the batch while checks are re-run is Place on hold; accepting is Accept batch.",
            [DIALOG_FORM_FACT]),
]

C = []


def ctl(key, region, what, not_for, note=None, options=None):
    e = {"key": key, "region": region, "what": what, "not_for": not_for}
    if note:
        e["note"] = note
    if options:
        e["options"] = options
    C.append(e)


# ----- dialogs (first: a dialog's primary button can share its text with the page button that opened it; ties go to the first entry) -----
for O, name in [("update-hole-dialog", "Update hole"), ("import-results-dialog", "Import results"), ("accept-batch-dialog", "Accept batch"),
                ("hold-batch-dialog", "Place on hold"), ("reject-batch-dialog", "Reject batch")]:
    ctl({"page": O, "text": "Close dialog", "role": "button"}, f"{name} dialog, title bar", "Closes the dialog and leaves the record as it was.", "Confirming (the dialog's primary button).")
    ctl({"page": O, "text": "Cancel", "role": "button"}, f"{name} dialog, buttons", "Closes the dialog and leaves the record as it was.", "Confirming (the dialog's primary button).")
O = "update-hole-dialog"
ctl({"page": O, "row_label": "Status"}, "Update hole dialog", "The hole's status after saving.", "The completion date or depth (their own fields).", options=["planned", "drilling", "completed", "abandoned", "logged", "sampled", "assayed"])
ctl({"page": O, "row_label": "Depth, m"}, "Update hole dialog", "The hole's actual depth in metres, in steps of 0.5.", "The planned depth, a separate value shown on the hole page.")
ctl({"page": O, "text": "Save", "role": "button"}, "Update hole dialog, buttons", "Saves status, depth and completion date and closes the dialog.", "Posting a comment (Comments on the page).")
ctl({"page": "import-results-dialog", "text": "Import", "role": "button"}, "Import results dialog, buttons", "Imports the results, runs the QAQC checks and moves the batch to received.", "Accepting the batch, which is a later, separate step.")
O = "accept-batch-dialog"
ctl({"page": O, "text_regex": "^I have reviewed each failure", "role": "checkbox"}, "Accept batch dialog", "Required confirmation, shown only when the batch has QAQC failures, that each failure has been reviewed.", "Clearing the failures; they stay recorded against the batch.")
ctl({"page": O, "text": "Accept", "role": "button"}, "Accept batch dialog, buttons", "Accepts the batch: releases grades to intercepts and estimates, moves the holes to assayed. Acts once the required confirmation (when shown) is ticked.", "Placing on hold or rejecting (separate buttons on the batch page).")
ctl({"page": "hold-batch-dialog", "text": "Place on hold", "role": "button"}, "Place on hold dialog, buttons", "Puts the batch on QAQC hold; it stays out of intercepts and estimates until accepted.", "Rejecting it back to the laboratory.")
O = "reject-batch-dialog"
ctl({"page": O, "row_label": "Reason sent to the laboratory"}, "Reject batch dialog", "Required reason sent to the laboratory: which checks failed and what is requested.", "A comment on the batch (Comments on the page).")
ctl({"page": O, "text": "Reject batch", "role": "button"}, "Reject batch dialog, buttons", "Rejects the batch for re-assay at the laboratory's cost; its holes return to sampled. Acts once a reason is written.", "Holding the batch while checks are re-run (Place on hold).")

# ----- Drilling left column (drilling-list, drilling-intercepts, drilling-hole) -----
DL = "Drilling left column"
ctl({"row_label": "Drillholes", "text_regex": r"^All holes\b"}, DL, "Shows the full drillhole list with no status cut. The number is the count of holes in the tenant.", "Filtering by project or type (the filters above the list).", note="Count in the label varies; matched by prefix.")
ctl({"row_label": "Drillholes", "text_regex": r"^Drilling now\b"}, DL, "Cuts the drillhole list to holes with a rig on them (status drilling).", "Planned holes (Planned) or finished ones (All holes).")
ctl({"row_label": "Drillholes", "text_regex": r"^Planned\b"}, DL, "Cuts the drillhole list to holes designed but not started (status planned).", "Planning new holes, which is under Programmes.")
ctl({"row_label": "Drillholes", "text_regex": r"^Awaiting sampling\b"}, DL, "Cuts the drillhole list to holes logged and waiting to be sampled and dispatched (status logged).", "Dispatching them, which is New dispatch under Assays.")
ctl({"row_label": "Drillholes", "text_regex": r"^Abandoned\b"}, DL, "Cuts the drillhole list to holes stopped short of three quarters of planned depth.", "Changing a hole's status (Update hole on the hole page).")
ctl({"row_label": "Results", "text_regex": r"^Significant intercepts\b"}, DL, "Opens the tenant-wide Intercepts list and scatter.", "One hole's intercepts, which are on that hole's page.")

# ----- Assays left column -----
AL = "Assays left column"
ctl({"row_label": "Batches", "text_regex": r"^All batches\b"}, AL, "Shows the full batch list with no status cut.", "Filtering by project or laboratory (the filters above the list).", note="Count in the label varies; matched by prefix.")
ctl({"row_label": "Batches", "text_regex": r"^At the laboratory\b"}, AL, "Cuts the batch list to batches still at the laboratory (submitted, in preparation or analysing).", "Importing their results, which is on the batch's page.")
ctl({"row_label": "Batches", "text_regex": r"^Received, unreviewed\b"}, AL, "Cuts the batch list to batches whose results are in and QAQC-checked but not yet reviewed.", "Accepting them, which is on each batch's page.")
ctl({"row_label": "Batches", "text_regex": r"^QAQC hold\b"}, AL, "Cuts the batch list to batches withheld after a failed QAQC check.", "The QAQC summary charts (QAQC summary below).")
ctl({"row_label": "Batches", "text_regex": r"^Accepted\b"}, AL, "Cuts the batch list to batches reviewed and released.", "Rejected batches, which appear under All batches.")
ctl({"row_label": "Quality", "text_regex": r"^QAQC summary$"}, AL, "Opens the QAQC summary: pass rate by month, failures by project, record by laboratory.", "Changing tolerances (Admin) or reviewing one batch (its page).")
ctl({"row_label": "Quality", "text_regex": r"^Sample register\b"}, AL, "Opens the register of every sample in the tenant.", "Batch-level views (the batch list).")

# ----- drilling-list -----
P = "drilling-list"
ctl({"page": P, "row_label": "Hole id"}, "Drillhole filters", "Narrows the list to holes whose id contains the text typed.", "Searching the whole tenant (header search) or filtering by status (left column).")
ctl({"page": P, "row_label": "Project"}, "Drillhole filters", "Narrows the list to one project's holes; All projects removes the filter.", "Opening a project's own page (the project name in the table).")
ctl({"page": P, "row_label": "Type"}, "Drillhole filters", "Narrows the list to one hole type: DDH diamond, RC reverse circulation, AC aircore or Sonic.", "Status cuts (left column).", options=["All types", "DDH", "RC", "AC", "Sonic"])
ctl({"page": P, "text": "Clear", "role": "link"}, "Drillhole filters", "Removes every filter and status cut, showing all holes.", "Resetting sort order or page.")
ctl({"page": P, "text": "Values behind this chart"}, "Holes completed chart", "Expands a table of the numbers drawn in the holes-completed-by-month chart.", "Filtering the drillhole table.")
ctl({"page": P, "text_regex": "^Sort by ", "role": "button"}, "Drillhole table header", "Sorts the drillhole table by the column named; a second press reverses the order.", "Filtering rows (the filters above).", note="One entry for every column header.")
ctl({"page": P, "text_regex": HOLE_RE, "role": "link"}, "Drillhole table, Hole column", "Opens this hole's page.", "The project or programme (their own columns).", note="Keyed on the hole-id shape, not on any one hole.")
ctl({"page": P, "text_regex": PRG_RE, "role": "link"}, "Drillhole table, Programme column", "Opens the hole's programme (Programmes).", "The hole itself (Hole column).", note="Keyed on the programme-code shape.")
ctl({"page": P, "text_regex": NAME_LINK_RE, "role": "link"}, "Drillhole table, Project column", "Opens this project (Projects).", "Filtering the list to the project, which is the Project filter above.", note="Matches any link on this page whose text is a free name; the only such links are project names in the table.")

# ----- drilling-intercepts -----
P = "drilling-intercepts"
ctl({"page": P, "text_regex": r"^Significant only\b", "role": "checkbox"}, "Intercepts filters", "Ticked (default): only significant intercepts, at least 1.5× cut-off over the commodity's minimum length. Unticked: every run above cut-off.", "Changing cut-offs or minimum lengths (Admin, Price deck and cut-offs).")
ctl({"page": P, "text": "Values behind this chart"}, "Intercept scatter", "Expands a table of the values drawn in the length-against-grade scatter.", "Filtering the intercepts table.")
ctl({"page": P, "text_regex": "^Sort by ", "role": "button"}, "Intercepts table header", "Sorts the intercepts by the column named; a second press reverses the order.", "Filtering (Significant only).")
ctl({"page": P, "text_regex": HOLE_RE, "role": "link"}, "Intercepts table, Hole column", "Opens the intercept's hole.", "The project (Project column).", note="Keyed on the hole-id shape.")
ctl({"page": P, "text_regex": NAME_LINK_RE, "role": "link"}, "Intercepts table, Project column", "Opens this project (Projects).", "The hole (Hole column).", note="Free-name links on this page are project names.")

# ----- drilling-hole -----
P = "drilling-hole"
ctl({"page": P, "text": "Update hole", "role": "button"}, "Hole header", "Opens the Update hole dialog to change status, depth and completion date. Shown only to roles with hole.write.", "Dispatching samples (Assays → New dispatch) or accepting results (the batch page).")
ctl({"page": P, "text_regex": "^batch ", "role": "link"}, "Hole summary, Batches", "Opens a sample batch this hole's samples went in.", "The sample register or the batch list.")
ctl({"page": P, "text_regex": "^read from the ", "role": "button"}, "Hole summary, source line", "States where the figures above come from; when it offers show method, it expands the method; otherwise it is a label.", "Refreshing or editing the figures.")
ctl({"page": P, "text": "Values behind this chart"}, "Downhole grade profile", "Expands a note on the values behind the grade profile (the Samples table lists every interval).", "Filtering the samples table.")
ctl({"page": P, "row_label": "Add a comment"}, "Comments", "Text of a comment on this hole; typing @ and a first name suggests a colleague to notify.", "Changing the hole's data (Update hole).")
ctl({"page": P, "text": "Post comment", "role": "button"}, "Comments", "Posts the comment typed above on this hole. Disabled while the comment box is empty.", "Saving hole changes (Update hole dialog's Save).")
ctl({"page": P, "text_regex": "^Sort by ", "role": "button"}, "Samples table header", "Sorts this hole's samples by the column named.", "Filtering; this table lists every sample of the hole.")
ctl({"page": P, "text_regex": BATCH_RE, "role": "link"}, "Samples table, Batch column", "Opens the sample's batch.", "The sample itself, whose details are in this row and in the Sample register.", note="Keyed on the batch-id shape.")
ctl({"page": P, "text_regex": NAME_LINK_RE, "role": "link"}, "Hole header, under the hole id", "The first link opens the hole's project (Projects area); the second opens its drilling programme (Programmes area).", "Other holes (Drilling breadcrumb).", note="Project and programme names are free text and carry no other key; one entry covers both, in the order shown.")

# ----- assays-batches -----
P = "assays-batches"
ctl({"page": P, "text": "New dispatch", "role": "link"}, "Batch list header", "Opens the New sample dispatch form to send logged holes' samples to a laboratory.", "Importing or reviewing results of an existing batch (its page).")
ctl({"page": P, "row_label": "Project"}, "Batch filters", "Narrows the batch list to one project's batches.", "Opening the project's page.")
ctl({"page": P, "row_label": "Laboratory"}, "Batch filters", "Narrows the batch list to one laboratory's batches.", "Laboratory performance (QAQC summary).")
ctl({"page": P, "text": "Clear", "role": "link"}, "Batch filters", "Removes every filter and status cut, showing all batches.", "Resetting sort order.")
ctl({"page": P, "text_regex": "^Sort by ", "role": "button"}, "Batch table header", "Sorts the batch list by the column named; a second press reverses the order.", "Filtering (filters above, left column).")
ctl({"page": P, "text_regex": BATCH_RE, "role": "link"}, "Batch table, Batch column", "Opens this batch's page (QAQC and review actions).", "The project (Project column).", note="Keyed on the batch-id shape.")
ctl({"page": P, "text_regex": NAME_LINK_RE, "role": "link"}, "Batch table, Project column", "Opens this project (Projects).", "Filtering to the project (Project filter).", note="Free-name links on this page are project names.")

# ----- assays-new -----
P = "assays-new"
ctl({"page": P, "row_label": "Project"}, "New sample dispatch form", "The project whose logged holes are offered for dispatch; changing it replaces the list of holes.", "Filtering an existing list; this starts a new dispatch.")
ctl({"page": P, "row_label": "Laboratory"}, "New sample dispatch form", "The laboratory the samples go to; each option shows its quoted turnaround in days.", "The assay method, which is set by the laboratory and project.")
ctl({"page": P, "text": "Cancel", "role": "link"}, "New sample dispatch form", "Leaves the form and returns to the batch list, with the dispatch unsent.", "Removing holes from the dispatch (untick them).")
ctl({"page": P, "text": "Submit dispatch", "role": "button"}, "New sample dispatch form", "Creates the batch: assigns sample numbers, inserts control samples, sends to the chosen laboratory and moves the included holes to sampled. Enabled once at least one hole is included, for roles with assay rights.", "Importing results (batch page, once the laboratory has them).")

# ----- assays-qaqc -----
P = "assays-qaqc"
ctl({"page": P, "text": "Tolerances", "role": "link"}, "QAQC summary header", "Opens Admin → QAQC tolerances, where the sigma, blank and duplicate limits are set.", "Reviewing failures of a batch (its page).")
ctl({"page": P, "text": "Values behind this chart"}, "QAQC charts", "Expands the table of numbers behind the chart it sits under (pass rate by month, or failures by project).", "Filtering anything.", note="Two on the page, one per chart.")
ctl({"page": P, "text_regex": NAME_LINK_RE, "role": "link"}, "QAQC tables and failures chart", "In By laboratory: opens the batch list filtered to that laboratory. In By project: opens that project's assays tab (Projects area). A bar in Failures by project opens the batch list filtered to that project.", "Changing laboratory or project records.", note="Laboratory and project names carry no other key.")

# ----- assays-samples -----
P = "assays-samples"
ctl({"page": P, "row_label": "Sample, hole or batch id"}, "Sample register filters", "Narrows the register to samples whose sample number, hole id or batch id contains the text typed.", "Tenant-wide search (header search).")
ctl({"page": P, "row_label": "Project"}, "Sample register filters", "Narrows the register to one project's samples.", "Opening the project.")
ctl({"page": P, "row_label": "Type"}, "Sample register filters", "Narrows the register to one sample type: core, chip, or a control sample (standard, blank, duplicate).", "QAQC pass rates (QAQC summary).", options=["All", "core", "chip", "standard", "blank", "duplicate"])
ctl({"page": P, "text": "Clear", "role": "link"}, "Sample register filters", "Removes every filter.", "Resetting sort order.")
ctl({"page": P, "text_regex": "^Sort by ", "role": "button"}, "Sample register header", "Sorts the register by the column named.", "Filtering (filters above).")
ctl({"page": P, "text_regex": HOLE_RE, "role": "link"}, "Sample register, Hole column", "Opens the sample's hole.", "The batch (Batch column).", note="Keyed on the hole-id shape.")
ctl({"page": P, "text_regex": BATCH_RE, "role": "link"}, "Sample register, Batch column", "Opens the sample's batch.", "The hole (Hole column).", note="Keyed on the batch-id shape.")

# ----- assays-batch -----
P = "assays-batch"
ctl({"page": P, "text": "Import results", "role": "button"}, "Batch header actions", "Opens the Import results dialog for a batch still at the laboratory: imports results, runs QAQC checks, moves it to received. Shown only to qaqc.review at that status.", "Accepting the batch, offered on the batch page once results are imported.")
ctl({"page": P, "text": "Accept batch", "role": "button"}, "Batch header actions", "Opens the Accept dialog: releases grades to intercepts and estimates and moves the holes to assayed.", "Withholding (Place on hold) or returning to the laboratory (Reject).")
ctl({"page": P, "text": "Place on hold", "role": "button"}, "Batch header actions", "Opens the dialog to put the batch on QAQC hold while the laboratory re-runs failed checks.", "Rejecting for full re-assay (Reject) or accepting (Accept batch).")
ctl({"page": P, "text": "Reject", "role": "button"}, "Batch header actions", "Opens the Reject dialog to send the batch back for re-assay, with a reason to the laboratory.", "Holding for re-run checks (Place on hold).")
ctl({"page": P, "text_regex": "^hole ", "role": "link"}, "Batch summary, Holes", "Opens a drillhole whose samples are in this batch.", "The sample register.")
ctl({"page": P, "text_regex": "^read from the ", "role": "button"}, "Batch summary, source line", "States where the batch figures come from (laboratory certificate and sample records); when it offers show method, it expands the method; otherwise it is a label.", "Importing results (Import results).")
ctl({"page": P, "row_label": "Add a comment"}, "Comments", "Text of a comment on this batch; typing @ and a first name suggests a colleague to notify.", "The reason for a rejection, which is written in the Reject dialog.")
ctl({"page": P, "text": "Post comment", "role": "button"}, "Comments", "Posts the comment typed above on this batch. Disabled while the box is empty.", "Accepting, holding or rejecting the batch.")
ctl({"page": P, "text_regex": "^Sort by ", "role": "button"}, "Batch samples table header", "Sorts this batch's samples by the column named.", "Filtering; this table lists every sample of the batch.")
ctl({"page": P, "text_regex": HOLE_RE, "role": "link"}, "Batch samples table, Hole column", "Opens the sample's hole.", "The batch in view.", note="Keyed on the hole-id shape.")
ctl({"page": P, "text_regex": NAME_LINK_RE, "role": "link"}, "Batch header, under the batch id", "Opens the batch's project (Projects area).", "Filtering the batch list by project.", note="Project names carry no other key.")

# ----- breadcrumbs (same text and target as the main-navigation item; one description fits both) -----
ctl({"page": "drilling-hole", "text": "Drilling", "role": "link"}, "Breadcrumb above the hole id (the main navigation has a Drilling item with the same target)", "Returns to the drillhole list.", "The hole's project or programme (links under the hole id).", note="Also matches the main-navigation Drilling link on this page; both open the drillhole list.")
for P in ("assays-batch", "assays-new"):
    ctl({"page": P, "text": "Assays", "role": "link"}, "Breadcrumb above the heading (the main navigation has an Assays item with the same target)", "Returns to the sample batch list.", "The QAQC summary or sample register (left column).", note="Also matches the main-navigation Assays link on this page; both open the batch list.")

# ----- pagers (every table page in the area) -----
for P, what in [("drilling-list", "drillhole"), ("drilling-intercepts", "intercepts"), ("drilling-hole", "samples"),
                ("assays-batches", "batch"), ("assays-samples", "sample register"), ("assays-batch", "batch samples")]:
    for label, w in [("First", "first"), ("Previous", "previous"), ("Next", "next"), ("Last", "last")]:
        ctl({"page": P, "text": label, "role": "button"}, f"Pager under the {what} table", f"Shows the {w} page of rows of the {what} table.", "Changing filters or sort.", note="Disabled (and not offered) at the ends of the table.")

atlas = {
    "app": "ADIT",
    "version": "2026-09-22",
    "area": "drilling-assays",
    "selectors": {"dialog": ["dialog[open]"]},
    "pages": pages,
    "controls": C,
}
with open(OUT, "w") as f:
    json.dump(atlas, f, indent=1, ensure_ascii=False)
    f.write("\n")
print(len(pages), "pages;", len(C), "controls")

"""Do each goal once the way a person would, through ADIT's own controls, then check it.

    python walkthrough.py            # all goals: reset, act, check, reset
    python walkthrough.py G3 G7      # some

This proves that each goal in goals.md can be completed and that check.py
recognises the result. It clicks buttons and types into fields through the
DevTools protocol, and it never writes localStorage except to reset.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cdp import Tab  # noqa: E402
import check  # noqa: E402

B = check.APP


def click(t, txt, sel="button,a,[role=tab]", submit=False):
    s = "button[type=submit]" if submit else sel
    ok = t.eval(f"""(()=>{{const e=[...document.querySelectorAll({json.dumps(s)})].filter(e=>(e.innerText||'').trim()==={json.dumps(txt)}&&e.getClientRects().length).pop(); if(!e) return false; e.click(); return true}})()""")
    time.sleep(0.6)
    if not ok:
        raise RuntimeError(f"no control {txt!r}")


def fill(t, label, value):
    r = t.eval(f"""(()=>{{const e=[...document.querySelectorAll('input,select,textarea')].filter(e=>e.getClientRects().length&&e.labels&&e.labels[0]&&e.labels[0].innerText.trim().startsWith({json.dumps(label)}))[0];
    if(!e) return null; if(e.type=='radio'||e.type=='checkbox'){{e.click();return 'on'}}
    const proto=e.tagName=='SELECT'?HTMLSelectElement.prototype:e.tagName=='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto,'value').set.call(e,{json.dumps(value)});
    e.dispatchEvent(new Event('input',{{bubbles:true}}));e.dispatchEvent(new Event('change',{{bubbles:true}}));return e.value}})()""")
    if r is None:
        raise RuntimeError(f"no field {label!r}")


def switch(t, name):
    t.eval("document.querySelector('[aria-controls=user-menu]').click()")
    time.sleep(0.4)
    t.eval(f"[...document.querySelectorAll('#user-menu button')].find(b=>b.innerText.includes({json.dumps(name)})).click()")
    time.sleep(0.8)


def go(t, path):
    t.goto(B + path)
    time.sleep(0.4)


def approve(t, path):
    go(t, path); click(t, "Approve"); click(t, "Approve", submit=True)


def g1(t):
    go(t, "#/projects"); click(t, "New project")
    for k, v in [("Project name", "Quartz Flat"), ("Commodity", "Au"), ("Jurisdiction", "Yukon"), ("Country", "Canada"),
                 ("Area", "55"), ("Budget", "400000"), ("Project geologist", "u-kholloway")]:
        fill(t, k, v)
    click(t, "Create project", submit=True)


def g2(t):
    go(t, "#/projects/PRJ-0433"); click(t, "Stage-gate decision")
    fill(t, "Place on hold", ""); fill(t, "Reasoning", "Phase 2 intercepts too thin to hand over; hold at the gate.")
    click(t, "Record decision", submit=True)


def g3(t):
    switch(t, "Hamish Ferrier"); go(t, "#/projects/PRJ-0412/tenure")
    t.eval("[...document.querySelectorAll('tr')].find(r=>r.innerText.startsWith('382742')).querySelector('button').click()")
    time.sleep(0.5); click(t, "Submit for renewal", submit=True)


def g4(t):
    switch(t, "Kieran Holloway"); go(t, "#/projects/PRJ-0441/programmes"); click(t, "New programme")
    for k, v in [("Type", "mapping"), ("Name", "Spring mapping, northern claims"), ("Objective", "Map the northern claims"),
                 ("Start", "2027-04-01"), ("End", "2027-05-31"), ("Budget", "120000")]:
        fill(t, k, v)
    click(t, "Create draft", submit=True)


def g5(t):
    approve(t, "#/approvals/WF-2026-0152")


def g6(t):
    go(t, "#/approvals/WF-2026-0146"); click(t, "Return")
    fill(t, "Reason", "Break out the rig costs before I approve."); click(t, "Return", submit=True)


def g7(t):
    switch(t, "Tomasz Wierzbicki"); approve(t, "#/approvals/WF-2026-0159")
    switch(t, "Marguerite Okonkwo"); approve(t, "#/approvals/WF-2026-0159")


def g8(t):
    go(t, "#/projects/PRJ-0421"); click(t, "Edit"); fill(t, "Next gate", "2027-01-31"); click(t, "Save", submit=True)


FLOWS = {"G1": g1, "G2": g2, "G3": g3, "G4": g4, "G5": g5, "G6": g6, "G7": g7, "G8": g8}


def main(goals):
    for g in goals or FLOWS:
        check.reset()
        before = check.check(g)["pass"]
        t = Tab(); go(t, "#/portfolio")
        try:
            FLOWS[g](t)
        finally:
            t.close()
        r = check.check(g)
        print(json.dumps({"goal": g, "pass_before": before, "pass_after": r["pass"], "details": r["details"]}))
        check.reset()


if __name__ == "__main__":
    main(sys.argv[1:])

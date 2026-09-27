"""Do each expert goal (E1..E12 in goals-expert.md) once through ADIT's own controls, then check it.

    python walkthrough_expert.py            # all expert goals: reset, act, check, reset
    python walkthrough_expert.py E3 E9      # some

Same method as walkthrough.py: clicks and form input over the DevTools protocol,
never writing localStorage except to reset. It proves each goal is completable and
that check.py recognises the result (pass_before false, pass_after true).
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cdp import Tab  # noqa: E402
import check  # noqa: E402
from walkthrough import click, fill, go, switch  # noqa: E402


def fill_nth(t, label, n, value):
    """Set the n-th visible field whose label starts with `label` (the estimate form repeats labels)."""
    r = t.eval(f"""(()=>{{const e=[...document.querySelectorAll('input,select,textarea')].filter(e=>e.getClientRects().length&&e.labels&&e.labels[0]&&e.labels[0].innerText.trim().startsWith({json.dumps(label)}))[{n}];
    if(!e) return null; const proto=e.tagName=='SELECT'?HTMLSelectElement.prototype:e.tagName=='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto,'value').set.call(e,{json.dumps(value)});
    e.dispatchEvent(new Event('input',{{bubbles:true}}));e.dispatchEvent(new Event('change',{{bubbles:true}}));return e.value}})()""")
    if r is None:
        raise RuntimeError(f"no field {label!r} #{n}")


def comment(t, body):
    fill(t, "Add a comment", body)
    click(t, "Post comment", submit=True)


def e1(t):
    go(t, "#/assays/LAB-26-04483")
    comment(t, "Geostat is re-running OREAS 252 and the ten samples either side; results due 2026-10-02.")


def e2(t):
    go(t, "#/projects/PRJ-0468"); click(t, "Stage-gate decision")
    fill(t, "Place on hold", "")
    fill(t, "Reasoning", "Waiting on the legacy seismic reprocessing before we commit to DF-01.")
    click(t, "Record decision", submit=True)


def e3(t):
    switch(t, "Hamish Ferrier"); go(t, "#/projects/PRJ-0387/tenure")
    t.eval("[...document.querySelectorAll('tr')].find(r=>r.innerText.startsWith('NMC 1174648')).querySelector('button').click()")
    time.sleep(0.5); click(t, "Submit for renewal", submit=True)


def e4(t):
    switch(t, "Tomasz Wierzbicki"); go(t, "#/projects/PRJ-0468/programmes"); click(t, "New programme")
    for k, v in [("Type", "geochem"), ("Name", "Soil sampling, northern block"),
                 ("Objective", "Soil grid on 200 m centres over the northern mineral claims."),
                 ("Start", "2027-05-03"), ("End", "2027-06-25"), ("Budget", "85000")]:
        fill(t, k, v)
    click(t, "Create draft", submit=True)


def e5(t):
    go(t, "#/approvals/WF-2026-0146"); click(t, "Reject")
    fill(t, "Reason", "Hold the rig spend until the land access agreement WF-2026-0155 is signed.")
    click(t, "Reject", submit=True)


def e6(t):
    switch(t, "Yolanda Mbeki"); go(t, "#/approvals/WF-2026-0145"); click(t, "Approve")
    fill(t, "Note", "Within the FY26 metallurgy allocation.")
    click(t, "Approve", submit=True)


def e7(t):
    switch(t, "Priya Raghunathan"); go(t, "#/assays/LAB-26-04464")
    click(t, "Place on hold"); click(t, "Place on hold", submit=True)


def e8(t):
    switch(t, "Tomasz Wierzbicki"); go(t, "#/drilling/WC-DDH-033"); click(t, "Update hole")
    for k, v in [("Status", "completed"), ("Depth", "362"), ("Completed", "2026-09-22")]:
        fill(t, k, v)
    click(t, "Save", submit=True)


def e9(t):
    switch(t, "Tomasz Wierzbicki"); go(t, "#/resources/estimates"); click(t, "New estimate")
    fill(t, "Project", "PRJ-0409"); time.sleep(0.3)
    fill(t, "Method", "Ordinary kriging"); fill(t, "Cut-off", "0.3")
    fill_nth(t, "Tonnes", 0, "4.2"); fill_nth(t, "Grade", 0, "1.35")
    fill_nth(t, "Tonnes", 1, "6.8"); fill_nth(t, "Grade", 1, "1.10")
    click(t, "Save draft", submit=True)


def e10(t):
    go(t, "#/projects/PRJ-0409"); click(t, "Edit")
    fill(t, "Next gate", "2027-04-15"); fill(t, "Forecast at year end", "3150000")
    click(t, "Save", submit=True)


def e11(t):
    switch(t, "Declan Sørensen"); go(t, "#/programmes/PRG-2026-025"); click(t, "Assign crew")
    for k, v in [("Person", "f-09"), ("Role on this programme", "Geophysicist"),
                 ("Rotation start", "2026-10-05"), ("Rotation end", "2026-10-19")]:
        fill(t, k, v)
    click(t, "Assign", submit=True)


def e12(t):
    # The finding part: read the batch register the way a person would, then report on the project.
    go(t, "#/assays")
    go(t, "#/projects/PRJ-0376/assays")
    ids = t.eval("[...document.querySelectorAll('tr')].filter(r=>/qaqc[- ]hold/.test(r.innerText)).map(r=>r.innerText.match(/LAB-\\d{2}-\\d{5}/)[0])")
    go(t, "#/projects/PRJ-0376")
    comment(t, "Batches on QAQC hold: " + ", ".join(ids))


FLOWS = {f"E{i}": f for i, f in enumerate([e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11, e12], 1)}


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

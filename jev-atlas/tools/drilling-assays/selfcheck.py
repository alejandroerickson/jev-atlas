"""Self-check for jev-atlas/atlas/parts/drilling-assays.json against the live app.

Injects the harness's own snapshot.js, matches pages/overlays/controls with the harness's
own atlas.py, and reports per-entry hit counts and per-scenario coverage.
"""
# Copied from the area author's scratch directory on 2026-09-22 by the atlas merger;
# paths rewritten to be relative to this file and to $JEV_CLONE (the harness copy).
import os as _os, pathlib as _pl
_PARTS = _pl.Path(_os.environ.get("ADIT_PARTS_DIR") or _pl.Path(__file__).resolve().parents[2] / "atlas" / "parts")
_HARNESS = _os.environ.get("JEV_CLONE", str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'vendor' / 'jev-ultrafast')).rstrip("/") + "/jev_ultrafast/"

import collections, importlib.util, json, sys
from playwright.sync_api import sync_playwright

spec = importlib.util.spec_from_file_location("atlas_mod", _HARNESS + "atlas.py")
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
PART = str(_PARTS / "drilling-assays.json")
book = A.load(PART)
SNAP = open(_HARNESS + "snapshot.js").read()
SEL = A.selector_lists(book)
BASE = "https://alejandroerickson.com/mockent/adit/"
VH = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
AREA_ROWS = {"Drillholes", "Results", "Batches", "Quality"}


def match_fields(a, page_id):  # copy of jev_ultrafast/model.py match_fields
    return {"track_id": a.get("track_id"), "id": a.get("dom_id"), "title": a.get("title"), "href": a.get("href"),
            "ancestor": a.get("ancestor"), "row_label": a.get("row_label"), "role": a.get("role"),
            "text": a.get("label", "").split(" → ")[0], "page": page_id}


class Browser:
    def __init__(self, pg): self.pg = pg
    def evaluate(self, expr): return self.pg.evaluate(expr)


hits = collections.Counter()
totals = {"area": 0, "area_hit": 0, "all": 0, "all_hit": 0}
overlay_log = []


def check(pg, tag, expect_page, expect_overlay=None):
    s = pg.evaluate(f"({SNAP})({json.dumps(SEL)})")
    matched = book.match_page(s["url"])
    pid = matched["id"] if matched else None
    found = book.probe(Browser(pg), matched)
    overlays = [o["id"] for o in book.active_overlays(found["selectors"], s["dialog_title"])]
    in_view = [i for i in [pid, *overlays] if i]
    nodes = {}
    for a in s["actions"]:
        if "node" not in a: continue
        e = book.match_control(match_fields(a, pid), in_view)
        if a["node"] not in nodes: nodes[a["node"]] = [a, None]
        if e and nodes[a["node"]][1] is None: nodes[a["node"]][1] = e
    ids = list(nodes)
    area = pg.evaluate("ids => ids.map(i => { const e = window.__jevFast.nodes.get(i); return !!(e && (e.closest('main') || e.closest('dialog'))); })", ids)
    na = nh = ta = th = 0; missing = []
    for (nid, (a, e)), in_area in zip(nodes.items(), area):
        in_area = in_area or a.get("row_label") in AREA_ROWS
        ta += 1; th += bool(e)
        if e: hits[json.dumps(e["key"], sort_keys=True)] += 1
        if in_area:
            na += 1; nh += bool(e)
            if not e: missing.append(a["label"][:60])
    totals["area"] += na; totals["area_hit"] += nh; totals["all"] += ta; totals["all_hit"] += th
    ok = "OK " if pid == expect_page and (expect_overlay is None or overlays == [expect_overlay]) else "BAD"
    print(f"{ok} {tag}: page={pid} overlays={overlays} area {nh}/{na} annotated, all {th}/{ta}; virtual={ {k: len(v) for k, v in found['virtual'].items()} }")
    for k, v in found["facts"].items():
        for f in v: print("     fact[%s]: %s" % (k, f[:220]))
    for m in collections.Counter(missing).most_common(): print("     UNANNOTATED:", m)
    return found


def goto(pg, h):
    pg.goto(BASE + h); pg.reload(); pg.wait_for_timeout(1300)


def as_user(pg, name):
    goto(pg, "#/drilling")
    pg.get_by_role("button", name="Account menu").click(); pg.wait_for_timeout(300)
    pg.get_by_role("button", name=name).click(); pg.wait_for_timeout(500)


def overlay_state(pg):
    return {o["id"]: pg.evaluate(A.VISIBLE.format(json.dumps(o["match"]["selector"]))) for o in book.overlays}


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": VH})
    for h, exp in [("#/drilling", "drilling-list"), ("#/drilling?status=planned", "drilling-list"),
                   ("#/drilling/intercepts", "drilling-intercepts"), ("#/drilling/BR-RC-001", "drilling-hole"),
                   ("#/assays", "assays-batches"), ("#/assays?status=qaqc-hold", "assays-batches"),
                   ("#/assays/new", "assays-new"), ("#/assays/qaqc", "assays-qaqc"),
                   ("#/assays/samples", "assays-samples"), ("#/assays/LAB-26-04408", "assays-batch")]:
        goto(pg, h); check(pg, "EXM " + h, exp)
    goto(pg, "#/drilling/BR-RC-001"); pg.fill("main textarea", "x"); pg.wait_for_timeout(200)
    check(pg, "EXM hole with comment typed", "drilling-hole")
    goto(pg, "#/assays/samples"); pg.fill("main input[type=search]", "WC"); pg.wait_for_timeout(500)
    check(pg, "EXM samples filtered", "assays-samples")
    for h, exp in [("#/drilling/intercepts", "drilling-intercepts"), ("#/assays", "assays-batches"), ("#/assays/samples", "assays-samples"), ("#/assays/LAB-26-04408", "assays-batch"), ("#/drilling/BR-RC-001", "drilling-hole")]:
        goto(pg, h); pg.get_by_role("button", name="Next").first.click(); pg.wait_for_timeout(400)
        check(pg, "EXM page 2 " + h, exp)
    goto(pg, "#/drilling"); pg.get_by_role("button", name="Next").click(); pg.wait_for_timeout(400)
    check(pg, "EXM #/drilling page 2", "drilling-list")

    as_user(pg, "Priya Raghunathan")
    goto(pg, "#/drilling/KL-DDH-015"); check(pg, "DBGEO hole", "drilling-hole")
    for h, btn, exp_page, ov, primary in [
        ("#/drilling/KL-DDH-015", "Update hole", "drilling-hole", "update-hole-dialog", "Save"),
        ("#/assays/LAB-26-04445", "Import results", "assays-batch", "import-results-dialog", "Import"),
        ("#/assays/LAB-26-04464", "Accept batch", "assays-batch", "accept-batch-dialog", "Accept"),
        ("#/assays/LAB-26-04464", "Place on hold", "assays-batch", "hold-batch-dialog", "Place on hold"),
        ("#/assays/LAB-26-04464", "Reject", "assays-batch", "reject-batch-dialog", "Reject batch"),
        ("#/assays/LAB-26-04452", "Accept batch", "assays-batch", "accept-batch-dialog", "Accept")]:
        goto(pg, h)
        before = overlay_state(pg)
        check(pg, f"DBGEO {h} (closed)", exp_page)
        pg.get_by_role("button", name=btn, exact=True).first.click(); pg.wait_for_timeout(500)
        during = overlay_state(pg)
        check(pg, f"DBGEO {h} +{btn}", exp_page, ov)
        pg.locator("dialog[open] button", has_text="Cancel").click(); pg.wait_for_timeout(300)
        after = overlay_state(pg)
        good = not any(before.values()) and [k for k, v in during.items() if v] == [ov] and not any(after.values())
        overlay_log.append((ov, h, good, before, during, after))

    # virtual control: Update hole completed date, verified by Save and the page's own display
    goto(pg, "#/drilling/KL-DDH-015")
    pg.get_by_role("button", name="Update hole", exact=True).click(); pg.wait_for_timeout(400)
    found = book.probe(Browser(pg), book.match_page(pg.url))
    vc = found["virtual"]["update-hole-dialog"][0]
    ok = pg.evaluate(f"({vc['set']})('2026-09-20')")
    pg.locator("dialog[open] button", has_text="Save").click(); pg.wait_for_timeout(500)
    shown = pg.evaluate("(() => { const dt=[...document.querySelectorAll('main dt')].find(d=>d.textContent.trim()==='Completed'); return dt && dt.nextElementSibling.textContent.trim(); })()")
    print(f"VIRTUAL update-hole completed: set returned {ok}; page now shows Completed = {shown!r} (expected 2026-09-20)")

    # virtual control: dispatch hole inclusion, verified by the Submit button's enabled state
    goto(pg, "#/assays/new")
    found = check(pg, "DBGEO #/assays/new", "assays-new")
    vcs = found["virtual"].get("assays-new", [])
    print("VIRTUAL dispatch holes offered:", [v["label"] for v in vcs])
    sub = "(() => [...document.querySelectorAll('main button')].find(b=>b.textContent.trim()==='Submit dispatch').disabled)()"
    d0 = pg.evaluate(sub)
    r = pg.evaluate(f"({vcs[0]['set']})('yes')"); d1 = pg.evaluate(sub)
    r2 = pg.evaluate(f"({vcs[0]['set']})('no')"); d2 = pg.evaluate(sub)
    print(f"VIRTUAL dispatch: submit disabled before={d0}; set yes -> {r}, disabled={d1}; set no -> {r2}, disabled={d2}")
    pg.evaluate(f"({vcs[0]['set']})('yes')"); pg.wait_for_timeout(200)
    check(pg, "DBGEO #/assays/new (one hole included)", "assays-new")
    b.close()

print("\nOVERLAY closed/open/closed tests:")
for ov, h, good, *_ in overlay_log: print("  ", "PASS" if good else "FAIL", ov, h)
print("\nPER-ENTRY HITS (entries with 0 hits listed):")
zero = 0
for c in book.controls:
    k = json.dumps(c["key"], sort_keys=True)
    if not hits[k]:
        zero += 1; print("   0 hits:", k)
print(f"{len(book.controls) - zero}/{len(book.controls)} entries matched >=1 live element")
print(f"COVERAGE area elements: {totals['area_hit']}/{totals['area']} = {100 * totals['area_hit'] / max(1, totals['area']):.1f}%;"
      f" all visible (incl. global header): {totals['all_hit']}/{totals['all']} = {100 * totals['all_hit'] / max(1, totals['all']):.1f}%")

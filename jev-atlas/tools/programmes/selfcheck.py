"""Self-check of the Programmes atlas fragment against the live app, headless.

For each state (route, user, clicks): run the harness's own snapshot.js with the
atlas selectors, match the page and overlays with the harness's atlas.py, and
match each action with the same fields model.match_fields builds.
"""
# Copied from the area author's scratch directory on 2026-09-22 by the atlas merger;
# paths rewritten to be relative to this file and to $JEV_CLONE (the harness copy).
import os as _os, pathlib as _pl
_PARTS = _pl.Path(_os.environ.get("ADIT_PARTS_DIR") or _pl.Path(__file__).resolve().parents[2] / "atlas" / "parts")
_HARNESS = _os.environ.get("JEV_CLONE", str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'vendor' / 'jev-ultrafast')).rstrip("/") + "/jev_ultrafast/"

import importlib.util, json, sys
from collections import defaultdict
from playwright.sync_api import sync_playwright

spec = importlib.util.spec_from_file_location("atlas", _HARNESS + "atlas.py")
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
PART = str(_PARTS / "programmes.json")
book = A.load(PART)
SNAP = open(_HARNESS + "snapshot.js").read()
SEL = A.selector_lists(book)
BASE = "https://alejandroerickson.com/mockent/adit/"
HEADER = {"ADIT home", "Portfolio", "Projects", "Programmes", "Drilling", "Assays", "Resources", "Optimiser", "Admin",
          "Search the tenant", "Open Search the tenant", "Switch to the light theme", "Switch to the dark theme", "Skip to content"}
def is_header(a):
    l = a["label"]
    return l in HEADER or l.startswith(("Approvals", "Notifications", "Signed in as", "User Manual"))

STATES = [
    ("#/programmes", "u-mokonkwo", []),
    ("#/programmes?phase=all", "u-mokonkwo", []),
    ("#/programmes/new", "u-twierzbicki", []),
    ("#/programmes/new", "u-twierzbicki", ["button:text-is('Create draft')"]),
    ("#/programmes/schedule", "u-mokonkwo", []),
    ("#/programmes/rigs", "u-dsorensen", []),
    ("#/programmes/camps", "u-mokonkwo", []),
    ("#/programmes/crew", "u-mokonkwo", []),
    ("#/programmes/crew", "u-mokonkwo", ["main button:text-is('Next')"]),
    ("#/programmes/PRG-2027-030", "u-twierzbicki", []),
    ("#/programmes/PRG-2026-024", "u-twierzbicki", []),
    ("#/programmes/PRG-2026-024", "u-mokonkwo", []),
    ("#/programmes/PRG-2026-027", "u-twierzbicki", ["main button:has-text('Move to')", "dialog[open] button:text-is('Confirm')"]),
    ("#/programmes/PRG-2026-024/crew", "u-twierzbicki", []),
    ("#/programmes/PRG-2026-024/logistics", "u-twierzbicki", []),
    ("#/programmes/PRG-2026-024/holes", "u-twierzbicki", []),
    ("#/programmes/PRG-2026-024/approval", "u-twierzbicki", []),
    ("#/programmes/PRG-2027-030/approval", "u-twierzbicki", []),
    # overlays
    ("#/programmes/PRG-2027-030", "u-twierzbicki", ["main button:has-text('Move to')"]),
    ("#/programmes/PRG-2026-024", "u-twierzbicki", ["main .head button:has-text('Assign crew')"]),
    ("#/programmes/PRG-2026-024/logistics", "u-twierzbicki", ["main button:text-is('Add item')"]),
    ("#/programmes/PRG-2026-024/logistics", "u-twierzbicki", ["main button:text-is('Edit')"]),
    ("#/programmes/rigs", "u-dsorensen", ["main button:text-is('Update')"]),
    ("#/programmes/PRG-2026-024/crew", "u-twierzbicki", ["main button:text-is('Remove')"]),
]

def fields(a, page_id):
    return {"track_id": a.get("track_id"), "id": a.get("dom_id"), "title": a.get("title"), "href": a.get("href"),
            "ancestor": a.get("ancestor"), "row_label": a.get("row_label"), "role": a.get("role"),
            "text": a.get("label", "").split(" → ")[0], "page": page_id}

hits = defaultdict(int)
tot_nodes = tot_ann = tot_all = tot_all_ann = 0
report = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for route, user, clicks in STATES:
        pg = b.new_page(viewport={"width": 1440, "height": 4200})
        pg.goto(BASE); pg.wait_for_timeout(700)
        pg.evaluate(f"localStorage.setItem('adit.session.v1', JSON.stringify({{currentUserId:'{user}',theme:'dark'}}))")
        pg.goto(BASE + route); pg.reload(); pg.wait_for_timeout(1200)
        for c in clicks:
            pg.locator(c).first.click(); pg.wait_for_timeout(600)
        s = pg.evaluate(f"({SNAP})({json.dumps(SEL)})")
        page = book.match_page(s["url"])
        pid = page["id"] if page else None

        class Br:
            def evaluate(self, expr): return pg.evaluate(expr)
        found = book.probe(Br(), page)
        overlays = book.active_overlays(found["selectors"], s["dialog_title"])
        in_view = [i for i in [pid, *[o["id"] for o in overlays]] if i]
        nodes, ann, unann = {}, set(), []
        for a in s["actions"]:
            if "node" not in a: continue
            e = book.match_control(fields(a, pid), in_view)
            if e is not None:
                hits[json.dumps(e["key"], sort_keys=True)] += 1
                ann.add(a["node"])
            nodes.setdefault(a["node"], a)
        mine = {n: a for n, a in nodes.items() if not is_header(a)}
        # With a dialog open, the page behind it is covered; count what can be clicked.
        if overlays:
            mine = {n: a for n, a in mine.items() if a.get("in_dialog")}
        n_ann = sum(1 for n in mine if n in ann)
        tot_nodes += len(mine); tot_ann += n_ann
        tot_all += len(nodes); tot_all_ann += sum(1 for n in nodes if n in ann)
        un = [mine[n]["label"][:50] for n in mine if n not in ann]
        report.append(f"{route} {user} {clicks} -> page={pid} overlays={[o['id'] for o in overlays]} dialog={s['dialog_title']!r}\n"
                      f"   annotated {n_ann}/{len(mine)} (area controls); unannotated: {un[:12]}\n"
                      f"   facts: {found['facts']}\n"
                      f"   virtual: {[(pid_, [(v['label'], v.get('current_value')) for v in vs]) for pid_, vs in found['virtual'].items()]}")
        pg.close()

    # Overlay selectors: closed / open / closed.
    ov_checks = [
        ("#/programmes/PRG-2027-030", "u-twierzbicki", "main button:has-text('Move to')", "programme-move-dialog"),
        ("#/programmes/PRG-2026-024", "u-twierzbicki", "main .head button:has-text('Assign crew')", "programme-assign-crew-dialog"),
        ("#/programmes/PRG-2026-024/logistics", "u-twierzbicki", "main button:text-is('Add item')", "programme-logistics-item-dialog"),
        ("#/programmes/PRG-2026-024/logistics", "u-twierzbicki", "main button:text-is('Edit')", "programme-logistics-item-dialog"),
        ("#/programmes/rigs", "u-dsorensen", "main button:text-is('Update')", "programmes-rig-update-dialog"),
    ]
    sel_of = {o["id"]: o["match"]["selector"] for o in book.overlays}
    for route, user, opener, oid in ov_checks:
        pg = b.new_page(viewport={"width": 1440, "height": 1400})
        pg.goto(BASE); pg.wait_for_timeout(700)
        pg.evaluate(f"localStorage.setItem('adit.session.v1', JSON.stringify({{currentUserId:'{user}',theme:'dark'}}))")
        pg.goto(BASE + route); pg.reload(); pg.wait_for_timeout(1200)
        vis = lambda: pg.evaluate(A.VISIBLE.format(json.dumps(sel_of[oid])))
        others = lambda: [k for k, v in sel_of.items() if k != oid and pg.evaluate(A.VISIBLE.format(json.dumps(v)))]
        before = vis(); pg.locator(opener).first.click(); pg.wait_for_timeout(500)
        during = vis(); wrong = others()
        pg.locator("dialog[open] button:text-is('Cancel')").first.click(); pg.wait_for_timeout(500)
        after = vis()
        report.append(f"OVERLAY {oid} via {opener}: closed={before} open={during} closed-again={after} other-overlays-open={wrong}")
        pg.close()

    # Virtual controls: set through the harness's own call shape and read back.
    pg = b.new_page(viewport={"width": 1440, "height": 1400})
    pg.goto(BASE); pg.wait_for_timeout(700)
    pg.evaluate("localStorage.setItem('adit.session.v1', JSON.stringify({currentUserId:'u-twierzbicki',theme:'dark'}))")
    pg.goto(BASE + "#/programmes"); pg.reload(); pg.wait_for_timeout(1200)
    lst = book.pages[0]
    vc = pg.evaluate(lst["virtual_controls_js"])
    ok = pg.evaluate(f"(({vc[0]['set']}))({json.dumps('geophysics')})"); pg.wait_for_timeout(500)
    h1 = pg.evaluate("location.hash")
    ok2 = pg.evaluate(f"(({pg.evaluate(lst['virtual_controls_js'])[0]['set']}))({json.dumps('all')})"); pg.wait_for_timeout(500)
    report.append(f"VIRTUAL type filter: set geophysics -> {ok} {h1}; set all -> {ok2} {pg.evaluate('location.hash')}")
    pg.goto(BASE + "#/programmes/new"); pg.wait_for_timeout(1000)
    newp = next(x for x in book.pages if x["id"] == "programmes-new")
    for v in pg.evaluate(newp["virtual_controls_js"]):
        r = pg.evaluate(f"(({v['set']}))({json.dumps('2027-02-03' if v['label']=='Start' else 'March 4, 2027')})")
        report.append(f"VIRTUAL {v['label']}: set -> {r}")
    report.append("   form fact after: " + str(pg.evaluate(A.GUARD.format(newp["facts_js"][0]))))
    # fill the rest and create, to prove the dates reached React state (fresh context; discarded)
    pg.locator("main input:not([type])").first.fill("selfcheck"); pg.locator("main textarea").fill("selfcheck")
    pg.locator("main input[type=number]").nth(0).fill("1000"); pg.locator("main input[type=number]").nth(1).fill("10")
    pg.locator("button:text-is('Create draft')").click(); pg.wait_for_timeout(800)
    created = pg.evaluate("JSON.stringify(JSON.parse(localStorage['adit.tenant.v1']).world.programmes.filter(p=>p.name==='selfcheck').map(p=>[p.id,p.start||p.startOn||p.startsOn,p.end||p.endOn||p.endsOn]))")
    report.append(f"   created with dates: {created} at {pg.url}")
    pg.close()
    b.close()

print("\n".join(report))
print(f"\nAREA CONTROLS annotated {tot_ann}/{tot_nodes} = {100*tot_ann/max(tot_nodes,1):.1f}%  (all incl. header: {tot_all_ann}/{tot_all})")
print("\nCONTROL ENTRIES with zero matches:")
for e in book.controls:
    k = json.dumps(e["key"], sort_keys=True)
    if not hits.get(k): print("  ", k)
print(f"entries matched: {sum(1 for e in book.controls if hits.get(json.dumps(e['key'], sort_keys=True)))}/{len(book.controls)}")

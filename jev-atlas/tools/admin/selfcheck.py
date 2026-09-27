"""Self-check for the admin atlas fragment, using the harness's own matcher and snapshot.js."""
# Copied from the area author's scratch directory on 2026-09-22 by the atlas merger;
# paths rewritten to be relative to this file and to $JEV_CLONE (the harness copy).
import os as _os, pathlib as _pl
_PARTS = _pl.Path(_os.environ.get("ADIT_PARTS_DIR") or _pl.Path(__file__).resolve().parents[2] / "atlas" / "parts")
_HARNESS = _os.environ.get("JEV_CLONE", str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'vendor' / 'jev-ultrafast')).rstrip("/") + "/jev_ultrafast/"

import json, sys, collections
import importlib.util
_spec=importlib.util.spec_from_file_location("atlas",_HARNESS + "atlas.py")
A=importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)
from playwright.sync_api import sync_playwright

BASE = "https://alejandroerickson.com/mockent/adit/"
BOOK = A.load(str(_PARTS / "admin.json"))
SNAP = open(_HARNESS + "snapshot.js").read()
SEL = A.selector_lists(BOOK)
W, H = (int(x) for x in (sys.argv[1] if len(sys.argv) > 1 else "1120x780").split("x"))


class B:
    def __init__(self, pg): self.pg = pg
    def evaluate(self, expr): return self.pg.evaluate(expr)


def fields(a, page_id):
    return {"track_id": a.get("track_id"), "id": a.get("dom_id"), "title": a.get("title"), "href": a.get("href"),
            "ancestor": a.get("ancestor"), "row_label": a.get("row_label"), "role": a.get("role"),
            "text": a.get("label", "").split(" → ")[0], "page": page_id}


hits = collections.Counter()
totals = collections.Counter()
problems = []


def check(pg, label):
    for y in (0, 500, 1000, 1500, 2000, 2600, 3200):
        pg.evaluate(f"window.scrollTo(0,{y})"); pg.wait_for_timeout(150)
        s = pg.evaluate(f"({SNAP})({json.dumps(SEL)})")
        page = BOOK.match_page(s["url"])
        pid = page["id"] if page else None
        found = BOOK.probe(B(pg), page)
        ov = [o["id"] for o in BOOK.active_overlays(found["selectors"], s["dialog_title"])]
        in_view = [i for i in [pid, *ov] if i]
        owned = pg.evaluate("ids => ids.map(i => { const e = window.__jevFast.nodes.get(i); return !!(e && e.closest('main, nav.l2, dialog')) })",
                            [a["node"] for a in s["actions"] if "node" in a])
        acts = [a for a in s["actions"] if "node" in a]
        seen_nodes = set()
        for a, own in zip(acts, owned):
            if not own or a["node"] in seen_nodes: continue
            seen_nodes.add(a["node"])
            e = BOOK.match_control(fields(a, pid), in_view)
            k = (label, a["label"].split(" → ")[0][:60], a["role"])
            if e:
                hits[json.dumps(e["key"], ensure_ascii=False)] += 1
                totals[(label, "annotated")] += 0
                annotated.add(k)
            else:
                unannotated.add(k)
        if y == 0:
            print(f"-- {label}: page={pid} overlays={ov} dialog_title={s['dialog_title']!r}")
            for pid_, fs in found["facts"].items():
                for f in fs: print("   fact:", f[:260])
        if s["scroll"]["y"] + H >= s["scroll"]["height"] - 2 and y > 0: break
    pg.evaluate("window.scrollTo(0,0)")


annotated, unannotated = set(), set()
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
    for who in ("SYS", None):
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.goto(BASE + "#/admin"); pg.wait_for_timeout(1200)
        pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1200)
        if who:
            pg.click('button[aria-label^="Signed in"]'); pg.wait_for_timeout(300)
            pg.get_by_role("button", name=who).click(); pg.wait_for_timeout(800)
        tag = who or "EXM"
        routes = ["", "/price-deck", "/qaqc", "/workflows", "/reference", "/users", "/roles", "/audit"]
        for r in routes:
            pg.goto(BASE + "#/admin" + r); pg.wait_for_timeout(700)
            check(pg, f"{tag} #/admin{r}")
        if who:
            def overlay(route, opener, name):
                pg.goto(BASE + "#/admin" + route); pg.wait_for_timeout(600)
                closed = BOOK.probe(B(pg), BOOK.match_page(pg.url))["selectors"]
                opener(); pg.wait_for_timeout(400)
                check(pg, f"{tag} {name}")
                opened = BOOK.probe(B(pg), BOOK.match_page(pg.url))["selectors"]
                pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
                after = BOOK.probe(B(pg), BOOK.match_page(pg.url))["selectors"]
                print(f"   overlay test {name}: closed={[k for k,v in closed.items() if v]} open={[k for k,v in opened.items() if v]} after={[k for k,v in after.items() if v]}")
            overlay("", lambda: pg.get_by_role("button", name="Reset demonstration tenant").click(), "reset dialog")
            overlay("/workflows", lambda: pg.get_by_role("button", name="Budget variance").click(), "workflow dialog")
            overlay("/users", lambda: pg.get_by_role("button", name="Add user").click(), "add user dialog")
            overlay("/users", lambda: pg.get_by_role("button", name="Edit").nth(3).click(), "edit user dialog")
            # dirty-state fact and invalid flag
            pg.goto(BASE + "#/admin/qaqc"); pg.wait_for_timeout(600)
            pg.fill("input[name=sigma]", "9"); pg.wait_for_timeout(200)
            check(pg, "SYS qaqc dirty")
            pg.goto(BASE + "#/admin/users"); pg.wait_for_timeout(600)
            pg.get_by_role("button", name="Add user").click(); pg.locator("dialog[open] input[name=email]").fill("not-an-email")
            check(pg, "SYS add user typed")
            pg.keyboard.press("Escape")
            pg.goto(BASE + "#/admin/audit"); pg.wait_for_timeout(600)
            pg.get_by_role("button", name="Next").click(); pg.wait_for_timeout(300)
            check(pg, "SYS audit page 2")
        pg.evaluate("localStorage.clear()")
        pg.close()
    b.close()

print("\n== control entries and live match counts")
for c in BOOK.controls:
    k = json.dumps(c["key"], ensure_ascii=False)
    print(f"{hits.get(k,0):4d}  {k}")
print(f"\nannotated distinct (surface,label,role): {len(annotated)}; unannotated: {len(unannotated - annotated)}")
for u in sorted(unannotated - annotated): print("   UNANNOTATED", u)
n = len(annotated) + len(unannotated - annotated)
print(f"coverage {100*len(annotated)/max(n,1):.1f}%")

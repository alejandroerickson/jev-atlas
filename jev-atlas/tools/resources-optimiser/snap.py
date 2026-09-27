"""Run the harness's own snapshot.js on scenarios; report match fields and atlas matches.
usage: snap.py <scenario-name|all> [--atlas PATH] [--show all|unmatched|none]"""
# Copied from the area author's scratch directory on 2026-09-22 by the atlas merger;
# paths rewritten to be relative to this file and to $JEV_CLONE (the harness copy).
import os as _os, pathlib as _pl
_PARTS = _pl.Path(_os.environ.get("ADIT_PARTS_DIR") or _pl.Path(__file__).resolve().parents[2] / "atlas" / "parts")
_HARNESS = _os.environ.get("JEV_CLONE", str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'vendor' / 'jev-ultrafast')).rstrip("/") + "/jev_ultrafast/"

import asyncio, json, sys, argparse
import importlib.util
_spec = importlib.util.spec_from_file_location("hatlas", _HARNESS + "atlas.py")
A = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(A)
def match_fields(action, page_id):  # copied from jev_ultrafast/model.py
    return {"track_id": action.get("track_id"), "id": action.get("dom_id"), "title": action.get("title"),
            "href": action.get("href"), "ancestor": action.get("ancestor"), "row_label": action.get("row_label"),
            "role": action.get("role"), "text": action.get("label", "").split(" → ")[0], "page": page_id}
from playwright.async_api import async_playwright
from scenarios import SCENARIOS, BASE
SNAP = open(_HARNESS + "snapshot.js").read()
GLOBAL_TEXTS = None
args_compact = True

async def run_steps(pg, steps):
    for st in steps:
        kind = st[0]
        if kind == "click": await pg.locator(st[1]).first.click()
        elif kind == "fill": await pg.locator(st[1]).first.fill(st[2])
        elif kind == "select": await pg.locator(st[1]).first.select_option(st[2])
        elif kind == "goto": await pg.goto(BASE + "#" + st[1])
        elif kind == "eval": await pg.evaluate(st[1])
        elif kind == "press": await pg.keyboard.press(st[1])
        await pg.wait_for_timeout(st[3] if kind=="fill" and len(st)>3 else 500)

def is_global(a):
    if a.get("label") == "User Manual" and (a.get("row_label") or "").startswith("ADIT 7."): return True
    if (a.get("row_label") or "").endswith(" saved") or a.get("label") in ("Dismiss",): return True
    # header / global chrome owned by another agent: detected by position (top bar) or skip link
    r = a.get("rect", {})
    return r.get("y", 999) < 48 or a.get("label") in ("Skip to content",)

async def scenario(b, name, sc, book, show):
    ctx = await b.new_context(viewport={"width": 1440, "height": 900})
    pg = await ctx.new_page()
    await pg.goto(BASE + "#/portfolio"); await pg.wait_for_timeout(800)
    await pg.evaluate("(u)=>{localStorage.clear(); if(u) localStorage.setItem('adit.session.v1', JSON.stringify({currentUserId:u,theme:'dark'}))}", sc.get("user"))
    await pg.goto(BASE + "#" + sc["route"]); await pg.reload(); await pg.wait_for_timeout(1200)
    await run_steps(pg, sc.get("steps", []))
    await pg.screenshot(path=f"snap_{name}.png")
    sels = A.selector_lists(book)
    snap = await pg.evaluate(f"({SNAP})({json.dumps(sels)})")
    page = book.match_page(snap["url"]) if book else None
    pid = page["id"] if page else None
    found = book.probe(type("B", (), {"evaluate": lambda self, e: None})(), page) if False else None
    # overlays
    ov = []
    if book:
        for o in book.overlays:
            s = (o.get("match") or {}).get("selector")
            vis = s and await pg.evaluate(f"(()=>{{try{{return {A.VISIBLE.format(json.dumps(s))}}}catch(e){{return false}}}})()")
            t = (o.get("match") or {}).get("dialog_title")
            if vis or (t and snap["dialog_title"].strip() == t.strip()): ov.append(o["id"])
        facts = []
        for e in [page] + [o for o in book.overlays if o["id"] in ov]:
            for f in (e or {}).get("facts_js") or []:
                v = await pg.evaluate(A.GUARD.format(f))
                facts.append(v)
    in_view = [i for i in [pid, *ov] if i]
    print(f"===== {name}  url={snap['url'].split('#')[-1]} page={pid} overlays={ov} dialog_title={snap['dialog_title']!r}")
    if book: print("  facts:", facts)
    nodes = {}
    for a in snap["actions"]:
        if "node" not in a: continue
        f = match_fields(a, pid)
        e = book.match_control(f, in_view) if book else None
        g = is_global(a)
        n = nodes.setdefault(a["node"], {"g": g, "m": False, "a": a, "f": f})
        if e: n["m"] = True; n["e"] = e
    local = [n for n in nodes.values() if not n["g"]]
    gm = [(n["a"].get("label"), n["e"]["region"]) for n in nodes.values() if n["g"] and n["m"]]
    if gm: print("  GLOBAL ELEMENTS MATCHED BY THIS FRAGMENT:", gm)
    matched = sum(1 for n in local if n["m"])
    print(f"  local elements {len(local)}, annotated {matched} ({100*matched/max(1,len(local)):.0f}%), global/header {sum(1 for n in nodes.values() if n['g'])}")
    for n in nodes.values():
        if n["g"]: continue
        if show == "all" or (show == "unmatched" and not n["m"]):
            f = {k: v for k, v in n["f"].items() if v and k not in ("page", "href")}
            extra = {k: n["a"].get(k) for k in ("kind", "in_dialog", "covered", "value") if n["a"].get(k)}
            if args_compact: print("   ", "OK " if n["m"] else "-- ", repr(f.get("text"))[:45].ljust(46), ("=> " + n["e"]["region"] + " :: " + n["e"]["what"][:50]) if n["m"] else json.dumps(f, ensure_ascii=False))
            else: print("   ", "OK " if n["m"] else "-- ", json.dumps(f, ensure_ascii=False), json.dumps(extra, ensure_ascii=False)[:80], ("=> " + n["e"]["region"]) if n["m"] else "")
    await ctx.close()
    return len(local), matched

async def main():
    ap = argparse.ArgumentParser(); ap.add_argument("which"); ap.add_argument("--atlas"); ap.add_argument("--show", default="all")
    args = ap.parse_args()
    book = A.load(args.atlas) if args.atlas else None
    names = list(SCENARIOS) if args.which == "all" else args.which.split(",")
    tot = [0, 0]
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for n in names:
            try:
                l, m = await scenario(b, n, SCENARIOS[n], book, args.show); tot[0] += l; tot[1] += m
            except Exception as ex:
                print("!!!!", n, ex)
        await b.close()
    print(f"TOTAL local {tot[0]} annotated {tot[1]} ({100*tot[1]/max(1,tot[0]):.1f}%)")
asyncio.run(main())

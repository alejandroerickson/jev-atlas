# Copied from the area author's scratch directory on 2026-09-22 by the atlas merger;
# paths rewritten to be relative to this file and to $JEV_CLONE (the harness copy).
import os as _os, pathlib as _pl
_PARTS = _pl.Path(_os.environ.get("ADIT_PARTS_DIR") or _pl.Path(__file__).resolve().parents[2] / "atlas" / "parts")
_HARNESS = _os.environ.get("JEV_CLONE", str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'vendor' / 'jev-ultrafast')).rstrip("/") + "/jev_ultrafast/"

import json, re
from collections import Counter
from playwright.sync_api import sync_playwright
from snap import *
BASE="https://alejandroerickson.com/mockent/adit/"
ATLAS=str(_PARTS / "approvals.json")
book=atlasmod.load(ATLAS)
hits=Counter(); tot=[0,0,0,0]
GLOBAL=("header","nav.l1","footer","skip")
def zone_js():
    return """(ids)=>ids.map(id=>{const e=window.__jevFast.nodes.get(id); if(!e) return 'x';
      return e.closest('header,nav.l1,footer')||e.classList.contains('skip')||e.closest('.toasts')&&false ? 'global':'area'})"""
def check(pg, label):
    s=snapshot(pg, book)
    page=book.match_page(pg.url)
    pid=page["id"] if page else None
    found=book.probe(type("B",(),{"evaluate":staticmethod(lambda e: pg.evaluate(e))})(), page)
    ov=[o["id"] for o in book.active_overlays(found["selectors"], s["dialog_title"])]
    inview=[i for i in [pid,*ov] if i]
    acts=[a for a in s["actions"] if "node" in a]
    zones=pg.evaluate(zone_js(), [a["node"] for a in acts])
    seen={}
    for a,z in zip(acts,zones):
        e=book.match_control(match_fields(a,pid), inview)
        key=a["node"]
        if key in seen and seen[key][0]: continue
        seen[key]=(e,z,a)
    un=[]
    n_area=n_area_hit=0
    for e,z,a in seen.values():
        if e: hits[json.dumps(e["key"],ensure_ascii=False)]+=1
        if z=="area":
            n_area+=1; n_area_hit+=bool(e)
            if not e: un.append(a["label"][:60])
    tot[0]+=len(seen); tot[1]+=sum(1 for e,_,_ in seen.values() if e); tot[2]+=n_area; tot[3]+=n_area_hit
    facts=found["facts"]
    print(f"## {label}  page={pid} overlays={ov}  area-annotated {n_area_hit}/{n_area}  all {sum(1 for e,_,_ in seen.values() if e)}/{len(seen)}")
    if un: print("   UNANNOTATED:", un)
    for k,v in facts.items():
        for f in v: print("   FACT",k,":",f[:260])
    return seen
def switch(pg,user):
    pg.click("button[aria-label*='Account menu']"); pg.wait_for_timeout(300)
    pg.locator("#user-menu button", has_text=user).click(); pg.wait_for_timeout(600)
def go(pg,r): pg.goto(BASE+r); pg.wait_for_timeout(900)
def scrollcheck(pg,label):
    # the snapshot only sees the viewport; check again scrolled to bottom
    check(pg,label)
    pg.evaluate("window.scrollTo(0,document.body.scrollHeight)"); pg.wait_for_timeout(300)
    check(pg,label+" (scrolled)")
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":1440,"height":900})
    for r in ["#/approvals","#/approvals?view=pending","#/approvals?view=mine","#/approvals?view=decided","#/approvals?view=pending&type=purchase-order"]:
        go(pg,r); scrollcheck(pg,r)
    for r in ["WF-2026-0152","WF-2026-0147","WF-2026-0148","WF-2026-0155","WF-2026-0156","WF-2026-0159","WF-2026-0157","WF-2026-0161","WF-2026-0154","WF-2026-0120"]:
        go(pg,"#/approvals/"+r); scrollcheck(pg,r)
    go(pg,"#/approvals/WF-2026-0152")
    sels={o["id"]:o["match"]["selector"] for o in book.overlays}
    vis=lambda s: pg.evaluate(f"[...document.querySelectorAll({json.dumps(s)})].some(e=>e.checkVisibility())")
    for n,oid in [("Approve","approval-approve-dialog"),("Return","approval-return-dialog"),("Reject","approval-reject-dialog")]:
        before={k:vis(v) for k,v in sels.items()}
        pg.locator("main .actions button", has_text=n).click(); pg.wait_for_timeout(300)
        during={k:vis(v) for k,v in sels.items()}
        check(pg,"dialog "+n)
        if n!="Approve":
            pg.locator("dialog[open] button[type=submit]").click(); pg.wait_for_timeout(300)
            check(pg,"dialog "+n+" after empty submit")
        pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
        after={k:vis(v) for k,v in sels.items()}
        print("   OVERLAY TEST",oid,"closed:",not any(before.values()),"open-only-this:",[k for k,v in during.items() if v]==[oid],"closed-again:",not any(after.values()))
        pg.evaluate("localStorage.clear()"); go(pg,"#/approvals/WF-2026-0152")
    pg.evaluate("localStorage.clear()"); go(pg,"#/approvals/WF-2026-0152")
    pg.fill("form.comment-form textarea","hello there"); scrollcheck(pg,"comment typed")
    switch(pg,"Kieran Holloway"); go(pg,"#/approvals"); check(pg,"KH queue")
    go(pg,"#/approvals/WF-2026-0146"); check(pg,"KH own request")
    pg.locator("main .actions button", has_text="Withdraw").click(); pg.wait_for_timeout(500); check(pg,"after withdraw (toast)")
    switch(pg,"Yolanda Mbeki"); go(pg,"#/approvals"); check(pg,"YM queue")
    b.close()
print(f"\nTOTAL all elements annotated {tot[1]}/{tot[0]}; approvals-area elements annotated {tot[3]}/{tot[2]} = {100*tot[3]/max(1,tot[2]):.1f}%")
data=json.load(open(ATLAS))
print("\nPER-ENTRY MATCH COUNTS (element-observations):")
for c in data["controls"]:
    k=json.dumps(c["key"],ensure_ascii=False); print(f"  {hits[k]:4d}  {k}")

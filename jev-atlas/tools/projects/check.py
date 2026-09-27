# Copied from the area author's scratch directory on 2026-09-22 by the atlas merger;
# paths rewritten to be relative to this file and to $JEV_CLONE (the harness copy).
import os as _os, pathlib as _pl
_PARTS = _pl.Path(_os.environ.get("ADIT_PARTS_DIR") or _pl.Path(__file__).resolve().parents[2] / "atlas" / "parts")
_HARNESS = _os.environ.get("JEV_CLONE", str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'vendor' / 'jev-ultrafast')).rstrip("/") + "/jev_ultrafast/"

import sys, json, collections
import importlib.util
_sp=importlib.util.spec_from_file_location("atlasmod",_HARNESS + "atlas.py"); A=importlib.util.module_from_spec(_sp); _sp.loader.exec_module(A)
from playwright.sync_api import sync_playwright
BASE="https://alejandroerickson.com/mockent/adit/"
PATH=str(_PARTS / "projects.json")
book=A.load(PATH)
SNAP=open(_HARNESS + "snapshot.js").read()
SEL=A.selector_lists(book)
HDR="(()=>{const m=window.__jevFast;const o={};for(const [id,e] of m.nodes){if(e.isConnected)o[id]=!!e.closest('header.topbar,footer.foot,a.skip,.toasts');}return o})()"
class B:
    def __init__(s,pg): s.pg=pg
    def evaluate(s,expr): return s.pg.evaluate(expr)
hits=collections.Counter(); totals=[0,0]; wrong=[]
def keystr(e): return json.dumps(e["key"],ensure_ascii=False)
def check(pg, label, verbose=True):
    s=pg.evaluate(f"({SNAP})({json.dumps(SEL)})")
    hdr=pg.evaluate(HDR)
    page=book.match_page(s["url"]); pid=page["id"] if page else None
    found=book.probe(B(pg), page)
    ov=book.active_overlays(found["selectors"], s["dialog_title"])
    in_view=[i for i in [pid,*[o["id"] for o in ov]] if i]
    notes={}; per={}
    for a in s["actions"]:
        if "node" not in a: continue
        f={"track_id":a.get("track_id"),"id":a.get("dom_id"),"title":a.get("title"),"href":a.get("href"),"ancestor":a.get("ancestor"),
           "row_label":a.get("row_label"),"role":a.get("role"),"text":a.get("label","").split(" → ")[0],"page":pid}
        e=book.match_control(f,in_view)
        if e: notes.setdefault(a["node"],e)
        per.setdefault(a["node"],[]).append(a)
    ann=0; tot=0; un=[]
    for node,acts in per.items():
        if hdr.get(str(node)): continue
        tot+=1
        e=notes.get(node)
        if e: ann+=1; hits[keystr(e)]+=1
        else: un.append(acts[0]["label"][:60])
    totals[0]+=ann; totals[1]+=tot
    print(f"\n### {label}: page={pid} overlays={[o['id'] for o in ov]} annotated {ann}/{tot} ({100*ann/max(1,tot):.0f}%)")
    if un: print("   UNANNOTATED:", un[:15], "..." if len(un)>15 else "")
    for k,v in found["facts"].items():
        for x in v: print("   FACT", k, ":", x[:300])
    for k,v in found["virtual"].items():
        for x in v: print("   VIRTUAL", k, ":", x["label"], "=", x.get("current_value"))
    if verbose:
        for node,acts in per.items():
            if hdr.get(str(node)): continue
            e=notes.get(node)
            if e: print("     ", acts[0]["label"][:50], "->", e["region"][:40], "|", e["what"][:60])
    return found, ov
def run():
    with sync_playwright() as p:
        b=p.chromium.launch()
        def fresh(route,user=None):
            ctx=b.new_context(viewport={"width":1440,"height":5000}); pg=ctx.new_page()
            pg.goto(BASE+"#/"); pg.wait_for_timeout(400)
            if user: pg.evaluate(f"localStorage.setItem('adit.session.v1', JSON.stringify({{...JSON.parse(localStorage.getItem('adit.session.v1')||'{{}}'), currentUserId:'{user}'}}))")
            pg.goto(BASE+route); pg.reload(); pg.wait_for_timeout(1000); return ctx,pg
        V="-v" in sys.argv
        ctx,pg=fresh("#/projects"); check(pg,"register",V)
        pg.fill("main .filters input","creek"); pg.wait_for_timeout(300); check(pg,"register+find",False)
        pg.goto(BASE+"#/projects?stage=drilling"); pg.wait_for_timeout(600); check(pg,"register stage cut",V)
        pg.goto(BASE+"#/projects?status=closed"); pg.wait_for_timeout(600); check(pg,"register closed",False)
        pg.goto(BASE+"#/projects/new"); pg.wait_for_timeout(600); check(pg,"new",V)
        pg.click("text=Create project"); pg.wait_for_timeout(400); check(pg,"new invalid",False)
        pg.goto(BASE+"#/projects/PRJ-0412"); pg.wait_for_timeout(600)
        # overlay closed/open/closed test
        f,_=check(pg,"overview",V); print("   overlay states closed:", f["selectors"])
        pg.fill("main form.comment-form textarea","@Tomasz test"); pg.wait_for_timeout(300); check(pg,"overview comment typed",False)
        pg.fill("main form.comment-form textarea",""); 
        pg.click("main .head button:has-text('Edit')"); pg.wait_for_timeout(500); f,_=check(pg,"edit dialog",V); print("   overlay states open:", f["selectors"])
        pg.keyboard.press("Escape"); pg.wait_for_timeout(300); f,_=check(pg,"after esc",False); print("   overlay states closed again:", f["selectors"])
        pg.click("main .head button:has-text('Stage-gate decision')"); pg.wait_for_timeout(500); f,_=check(pg,"gate dialog",V); print("   overlay states open:", f["selectors"])
        pg.click("text=Record decision"); pg.wait_for_timeout(300); check(pg,"gate invalid",False)
        pg.click("text=Relinquish and close"); pg.wait_for_timeout(300); check(pg,"gate relinquish",False)
        pg.click("dialog[open] button[aria-label='Close dialog']"); pg.wait_for_timeout(300); f,_=check(pg,"gate closed",False); print("   overlay states:", f["selectors"])
        for t in ["tenure","programmes","drilling","assays","resource","budget","approvals","activity"]:
            pg.goto(BASE+f"#/projects/PRJ-0412/{t}"); pg.wait_for_timeout(600); check(pg,"tab "+t,V)
        pg.goto(BASE+"#/projects/PRJ-0433/drilling"); pg.wait_for_timeout(600); check(pg,"drilling pager",False)
        pg.goto(BASE+"#/projects/PRJ-0390"); pg.wait_for_timeout(600); check(pg,"on-hold overview",False)
        pg.click("main .head button:has-text('Stage-gate decision')"); pg.wait_for_timeout(500); check(pg,"on-hold gate",False)
        pg.goto(BASE+"#/projects/PRJ-0351"); pg.wait_for_timeout(600); check(pg,"closed project",False)
        pg.goto(BASE+"#/projects/PRJ-0376"); pg.wait_for_timeout(600); check(pg,"qaqc overview",V)
        pg.goto(BASE+"#/projects/PRJ-0468/resource"); pg.wait_for_timeout(600); check(pg,"no estimate",False)
        ctx.close()
        ctx,pg=fresh("#/projects/PRJ-0409/tenure","u-hferrier"); check(pg,"tenure as TEN",V)
        pg.click("text=Lodge renewal"); pg.wait_for_timeout(500); f,_=check(pg,"lodge dialog",V); print("   overlay states:", f["selectors"])
        pg.keyboard.press("Escape"); pg.wait_for_timeout(300); f,_=check(pg,"lodge closed",False); print("   overlay states:", f["selectors"])
        ctx.close()
        ctx,pg=fresh("#/projects/PRJ-0412/programmes","u-twierzbicki"); check(pg,"programmes as PGEO",False)
        # virtual control verification on a freshly loaded page
        pg.goto(BASE+"#/projects/PRJ-0412"); pg.reload(); pg.wait_for_timeout(800)
        pg.click("main .head button:has-text('Edit')"); pg.wait_for_timeout(500)
        found=book.probe(B(pg), book.match_page(pg.url))
        vc=found["virtual"].get("project-edit-dialog",[])
        print("\nVIRTUAL offered:", [(v["label"],v["current_value"]) for v in vc])
        ok=pg.evaluate(f"(({vc[0]['set']}))({json.dumps('2027-03-01')})"); print("set returned", ok)
        found=book.probe(B(pg), book.match_page(pg.url)); print("after set:", found["virtual"]["project-edit-dialog"][0]["current_value"], found["facts"].get("project-edit-dialog"))
        pg.click("dialog[open] button:has-text('Save')"); pg.wait_for_timeout(500)
        print("after save meta:", pg.inner_text("main .head .meta"), "| toast:", pg.evaluate("[...document.querySelectorAll('.toast span')].map(e=>e.textContent).join('|')"))
        ctx.close(); b.close()
    print(f"\nTOTAL annotated {totals[0]}/{totals[1]} = {100*totals[0]/totals[1]:.1f}%")
    zero=[keystr(c) for c in book.controls if keystr(c) not in hits]
    print("control entries:",len(book.controls),"matched >=1:",len(book.controls)-len(zero))
    print("ZERO-MATCH entries:"); [print("  ",z) for z in zero]
run()

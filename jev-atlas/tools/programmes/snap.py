# Copied from the area author's scratch directory on 2026-09-22 by the atlas merger;
# paths rewritten to be relative to this file and to $JEV_CLONE (the harness copy).
import os as _os, pathlib as _pl
_PARTS = _pl.Path(_os.environ.get("ADIT_PARTS_DIR") or _pl.Path(__file__).resolve().parents[2] / "atlas" / "parts")
_HARNESS = _os.environ.get("JEV_CLONE", str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'vendor' / 'jev-ultrafast')).rstrip("/") + "/jev_ultrafast/"

import sys, json
from playwright.sync_api import sync_playwright
SNAP = open(_HARNESS + "snapshot.js").read()
SEL = {"dialog":['[role="dialog"]','[aria-modal="true"]','.modal','dialog[open]'],"busy":['[aria-busy="true"]'],"dialog_title":['dialog[open] h2','[role="dialog"] h1','[role="dialog"] h2','[role="dialog"] [class*="title"]']}
BASE="https://alejandroerickson.com/mockent/adit/"
def snap(pg):
    return pg.evaluate(f"({SNAP})({json.dumps(SEL)})")
def show(pg, full=False):
    s = snap(pg)
    print("URL", s['url'], "| dialog:", s['dialog_title'], "| headings:", s['headings'])
    for a in s['actions']:
        if a['kind'] in ('scroll','wait'): continue
        f = {k:a.get(k) for k in ('kind','role','label','dom_id','title','ancestor','row_label','in_dialog') if a.get(k)}
        print(json.dumps(f, ensure_ascii=False))
    if full: print(s['text'][:3000])
    return s
if __name__ == "__main__":
    route = sys.argv[1]; steps = sys.argv[2:]
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width":1440,"height":900})
        pg.goto(BASE + route); pg.wait_for_timeout(2000)
        for st in steps:
            kind, _, arg = st.partition(':')
            if kind=='click': pg.locator(arg).first.click(); pg.wait_for_timeout(700)
            elif kind=='text': print(pg.inner_text('body')[:5000])
            elif kind=='html': print(pg.locator(arg).first.evaluate("e=>e.outerHTML")[:8000])
            elif kind=='eval': print(pg.evaluate(arg))
            elif kind=='show': show(pg)
            elif kind=='press': pg.keyboard.press(arg); pg.wait_for_timeout(500)
        if not steps: show(pg)
        b.close()

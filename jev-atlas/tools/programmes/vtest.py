# Copied from the area author's scratch directory on 2026-09-22 by the atlas merger;
# paths rewritten to be relative to this file and to $JEV_CLONE (the harness copy).
import os as _os, pathlib as _pl
_PARTS = _pl.Path(_os.environ.get("ADIT_PARTS_DIR") or _pl.Path(__file__).resolve().parents[2] / "atlas" / "parts")
_HARNESS = _os.environ.get("JEV_CLONE", str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'vendor' / 'jev-ultrafast')).rstrip("/") + "/jev_ultrafast/"

from playwright.sync_api import sync_playwright
from snap import BASE
SETDATE = """(([sel, label, v]) => { const d=document.querySelector(sel); const f=[...d.querySelectorAll('label')].find(l=>l.querySelector('span')?.textContent.trim()===label); const i=f.querySelector('input[type=date]');
 const s=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set; s.call(i,v); i.dispatchEvent(new Event('input',{bubbles:true})); i.dispatchEvent(new Event('change',{bubbles:true})); return i.value===v; })"""
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":1440,"height":1400})
    pg.goto(BASE); pg.wait_for_timeout(800)
    pg.evaluate("localStorage.setItem('adit.session.v1', JSON.stringify({currentUserId:'u-twierzbicki',theme:'dark'}))")
    pg.goto(BASE+"#/programmes/PRG-2026-023"); pg.reload(); pg.wait_for_timeout(1200)
    pg.locator("main button:has-text('Assign crew')").first.click(); pg.wait_for_timeout(500)
    pg.locator("dialog[open] select").first.select_option("f-10")
    print(pg.evaluate("[...document.querySelectorAll('dialog[open] input')].map(i=>i.type+'='+i.value).join(' ')"))
    sel='dialog[open][aria-label^="Assign crew"]'
    print(pg.evaluate(SETDATE, [sel,'Rotation start','2026-09-20']), pg.evaluate(SETDATE, [sel,'Rotation end','2026-09-30']))
    pg.locator("dialog[open] button:text-is('Assign')").click(); pg.wait_for_timeout(700)
    print("DIALOG:", pg.evaluate("document.querySelector('dialog[open]')?.innerText.replace(/\\n+/g,' ¦ ').slice(-400)"))
    print("DLG HTML err:", pg.evaluate("[...document.querySelectorAll('dialog[open] .error, dialog[open] [class*=err], dialog[open] [role=alert]')].map(e=>e.className+':'+e.innerText).join(' | ')"))
    print("TOAST:", pg.evaluate("document.querySelector('.toasts')?.innerText"))
    # now valid dates to check setter took effect
    print(pg.evaluate(SETDATE, [sel,'Rotation start','2026-12-01']), pg.evaluate(SETDATE, [sel,'Rotation end','2026-12-10']))
    pg.locator("dialog[open] button:text-is('Assign')").click(); pg.wait_for_timeout(700)
    print("TOAST2:", pg.evaluate("document.querySelector('.toasts')?.innerText"))
    print(pg.evaluate("JSON.stringify(JSON.parse(localStorage['adit.tenant.v1']).world.programmes.find(p=>p.id==='PRG-2026-023').crew?.slice(-1))"))
    b.close()

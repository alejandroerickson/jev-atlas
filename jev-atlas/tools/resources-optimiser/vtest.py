# Copied from the area author's scratch directory on 2026-09-22 by the atlas merger;
# paths rewritten to be relative to this file and to $JEV_CLONE (the harness copy).
import os as _os, pathlib as _pl
_PARTS = _pl.Path(_os.environ.get("ADIT_PARTS_DIR") or _pl.Path(__file__).resolve().parents[2] / "atlas" / "parts")
_HARNESS = _os.environ.get("JEV_CLONE", str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'vendor' / 'jev-ultrafast')).rstrip("/") + "/jev_ultrafast/"

import asyncio, json, importlib.util
from playwright.async_api import async_playwright
BASE="https://alejandroerickson.com/mockent/adit/"
spec=importlib.util.spec_from_file_location("hatlas",_HARNESS + "atlas.py"); A=importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
book=A.load(str(_PARTS / "resources-optimiser.json"))
pages={p["id"]:p for p in book.data["pages"]}
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); ctx=await b.new_context(); pg=await ctx.new_page()
        await pg.goto(BASE+"#/portfolio"); await pg.wait_for_timeout(600)
        await pg.evaluate("localStorage.clear(); localStorage.setItem('adit.session.v1', JSON.stringify({currentUserId:'u-twierzbicki',theme:'dark'}))")
        await pg.goto(BASE+"#/optimiser"); await pg.reload(); await pg.wait_for_timeout(1200)
        for f in pages["optimiser"]["facts_js"]: print("FACT:", await pg.evaluate(A.GUARD.format(f)))
        await pg.goto(BASE+"#/resources/estimates/new"); await pg.reload(); await pg.wait_for_timeout(1200)
        vexpr=A.GUARD.format(pages["resources-estimate-new"]["virtual_controls_js"])
        vs=await pg.evaluate(vexpr)
        for v in vs: print("VIRTUAL:", v["id"], "|", v["label"], "|", v["current_value"])
        # set through harness path, fresh page
        for v,val in zip(vs,["12.5","1.1","30","0.7"]):
            ok=await pg.evaluate(f"(({v['set']}))({json.dumps(val)})"); print("set", v["label"], val, ok)
        vs2=await pg.evaluate(vexpr); print("after:", [(v["label"],v["current_value"]) for v in vs2])
        print("FACT:", await pg.evaluate(A.GUARD.format(pages["resources-estimate-new"]["facts_js"][0])))
        await pg.click("button:has-text('Save draft')"); await pg.wait_for_timeout(800)
        print("FACT after save:", await pg.evaluate(A.GUARD.format(pages["resources-estimate-new"]["facts_js"][0])))
        print("virtual after save:", await pg.evaluate(vexpr))
        w=json.loads(await pg.evaluate("localStorage.getItem('adit.tenant.v1')"))["world"]["estimates"]
        new=[e for e in w if e["authorId"]=="u-twierzbicki" and e["status"]=="draft"]; print("created:", [(e["id"], e["blocks"]) for e in new][-1:])
        await ctx.close(); await b.close()
asyncio.run(main())

# Copied from the area author's scratch directory on 2026-09-22 by the atlas merger;
# paths rewritten to be relative to this file and to $JEV_CLONE (the harness copy).
import os as _os, pathlib as _pl
_PARTS = _pl.Path(_os.environ.get("ADIT_PARTS_DIR") or _pl.Path(__file__).resolve().parents[2] / "atlas" / "parts")
_HARNESS = _os.environ.get("JEV_CLONE", str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'vendor' / 'jev-ultrafast')).rstrip("/") + "/jev_ultrafast/"

import json, sys, importlib.util
H=_HARNESS + ""
spec=importlib.util.spec_from_file_location("atlasmod",H+"atlas.py"); atlasmod=importlib.util.module_from_spec(spec); spec.loader.exec_module(atlasmod)
SNAP=open(H+"snapshot.js").read()
def snapshot(pg, book=None):
    sel=atlasmod.selector_lists(book)
    return pg.evaluate(f"({SNAP})({json.dumps(sel)})")
def match_fields(a, page_id):
    return {"track_id":a.get("track_id"),"id":a.get("dom_id"),"title":a.get("title"),"href":a.get("href"),
            "ancestor":a.get("ancestor"),"row_label":a.get("row_label"),"role":a.get("role"),
            "text":a.get("label","").split(" → ")[0],"page":page_id}

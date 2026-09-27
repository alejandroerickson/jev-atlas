"""Self-check: every page of this fragment, live, headless; per-entry match counts and coverage."""
# Copied from the area author's scratch directory on 2026-09-22 by the atlas merger;
# paths rewritten to be relative to this file and to $JEV_CLONE (the harness copy).
import os as _os, pathlib as _pl
_PARTS = _pl.Path(_os.environ.get("ADIT_PARTS_DIR") or _pl.Path(__file__).resolve().parents[2] / "atlas" / "parts")
_HARNESS = _os.environ.get("JEV_CLONE", str(__import__('pathlib').Path(__file__).resolve().parents[2] / 'vendor' / 'jev-ultrafast')).rstrip("/") + "/jev_ultrafast/"

import collections, importlib.util, json, pathlib, sys
from playwright.sync_api import sync_playwright

H = _HARNESS + ""
spec = importlib.util.spec_from_file_location('atlasmod', H + 'atlas.py')
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
SNAP = pathlib.Path(H + 'snapshot.js').read_text()
PART = str(_PARTS / "portfolio-global.json")
book = A.load(PART)
BASE = 'https://alejandroerickson.com/mockent/adit/'
VERBOSE = '-v' in sys.argv

# (label, route, actions before snapshot)
SCEN_ALL = [
    ('portfolio', '#/portfolio', []),
    ('commodity', '#/portfolio/commodity', []),
    ('jurisdiction', '#/portfolio/jurisdiction', []),
    ('analytics', '#/portfolio/analytics', []),
    ('budget', '#/portfolio/budget', []),
    ('search-empty', '#/search', []),
    ('search-er', '#/search?q=er', []),
    ('search-lab', '#/search?q=LAB-26', []),
    ('search-none', '#/search?q=zzzz', []),
    ('notifications', '#/notifications', []),
    ('account', '#/account', []),
    ('account-notif', '#/account/notifications', []),
    ('account-prefs', '#/account/preferences', []),
    ('account-sec', '#/account/security', []),
    ('manual', '#/manual', []),
    ('manual-gs', '#/manual/getting-started', []),
    ('manual-ref', '#/manual/reference', []),
    ('404', '#/nonexistent-xyz', []),
    ('tray', '#/portfolio', [('click', 'button[aria-controls=notif-tray]')]),
    ('menu', '#/portfolio', [('click', 'button[aria-controls=user-menu]')]),
    ('menu-on-account', '#/account/preferences', [('click', 'button[aria-controls=user-menu]')]),
    ('toast', '#/account', [('click', '#content button[type=submit]')]),
    ('method-open', '#/portfolio/analytics', [('click', '#content button.authority'), ('click', '#content details.values summary')]),
]

import os
SCEN=[x for x in SCEN_ALL if not os.environ.get('ONLY') or x[0] in os.environ['ONLY'].split(',')]

class B:
    def __init__(self, page): self.page = page
    def evaluate(self, expr): return self.page.evaluate(expr)


hits = collections.Counter()
total_nodes = total_matched = 0
per_page = []
with sync_playwright() as p:
    br = p.chromium.launch()
    for label, route, acts in SCEN:
        ctx = br.new_context(viewport={'width': 1120, 'height': 5000})
        pg = ctx.new_page()
        pg.goto(BASE + route); pg.wait_for_timeout(1300)
        for op, sel in acts:
            pg.click(sel); pg.wait_for_timeout(500)
        st = pg.evaluate(f"({SNAP})({json.dumps(A.selector_lists(book))})")
        page = book.match_page(st['url'])
        found = book.probe(B(pg), page)
        overlays = book.active_overlays(found['selectors'], st.get('dialog_title'))
        in_view = [i for i in [page and page['id'], *[o['id'] for o in overlays]] if i]
        seen, matched, unmatched = set(), 0, []
        for a in st['actions']:
            if 'node' not in a or a['node'] in seen: continue
            seen.add(a['node'])
            fields = {'track_id': a.get('track_id'), 'id': a.get('dom_id'), 'title': a.get('title'), 'href': a.get('href'),
                      'ancestor': a.get('ancestor'), 'row_label': a.get('row_label'), 'role': a.get('role'),
                      'text': a.get('label', '').split(' → ')[0], 'page': page and page['id']}
            e = book.match_control(fields, in_view)
            if e:
                matched += 1; hits[json.dumps(e['key'], ensure_ascii=False)] += 1
                if VERBOSE: print('   +', fields['text'][:50], '->', e['region'])
            else:
                unmatched.append(fields['text'][:45])
        n = len(seen); total_nodes += n; total_matched += matched
        facts = found['facts']
        print(f"{label:16} page={page and page['id']} overlays={[o['id'] for o in overlays]} {matched}/{n} "
              f"({100*matched/max(n,1):.0f}%) unmatched={unmatched[:12]}{'...' if len(unmatched)>12 else ''}")
        for pid, fs in facts.items():
            for f in fs: print('     fact[%s]: %s' % (pid, f[:220]))
        ctx.close()
    # overlay closed/open/closed test
    ctx = br.new_context(viewport={'width': 1120, 'height': 780}); pg = ctx.new_page()
    pg.goto(BASE + '#/portfolio'); pg.wait_for_timeout(1300)
    for ov, btn in (('#notif-tray', 'button[aria-controls=notif-tray]'), ('#user-menu', 'button[aria-controls=user-menu]')):
        vis = lambda: pg.evaluate(A.VISIBLE.format(json.dumps(ov)))
        r = [vis()]; pg.click(btn); pg.wait_for_timeout(400); r.append(vis())
        pg.click(btn); pg.wait_for_timeout(400); r.append(vis())
        pg.click(btn); pg.wait_for_timeout(400); pg.keyboard.press('Escape'); pg.wait_for_timeout(400); r.append(vis())
        print('overlay', ov, 'closed/open/closed(button)/closed(Escape):', r)
    ctx.close(); br.close()

print(f"\nTOTAL annotated {total_matched}/{total_nodes} = {100*total_matched/total_nodes:.1f}%")
dead = [c['key'] for c in book.controls if json.dumps(c['key'], ensure_ascii=False) not in hits]
print('entries matching nothing in these scenarios:', len(dead))
for k in dead: print('   ', k)
many = [(k, v) for k, v in hits.items() if v > 40]
print('entries matching >40 elements:', many)

"""Whole-app self-check of the merged ADIT atlas, with the harness's own snapshot.js and atlas.py.

    uv run --with playwright python jev-atlas/tools/selfcheck.py [--only tag1,tag2] [-v]

Every scenario runs in a fresh headless Chromium context, so localStorage
(adit.session.v1, adit.tenant.v1) starts clean each time; the two keys are also
removed explicitly before the scenario's user is set. For each state it reports
which page and overlays the atlas matched, how many visible interactive elements
got an atlas note, and any element whose note looks wrong:

- AREA   the entry comes from an area that owns neither the page nor an open overlay
         (global chrome and shared components are allowed everywhere);
- DIALOG a dialog-only entry on an element outside any dialog, or a page entry on an
         element inside a dialog;
- CHROME a top-bar element described by anything but a chrome entry;
- ROWLABEL a button or link described by a form field's {page, row_label} entry
         (buttons in a form row borrow the row's label);
- LANDMARK a footer, breadcrumb or top-bar entry on an element outside that landmark,
         or a breadcrumb described by anything but a breadcrumb entry.

JEV_VIEWPORT (default 1700x900, the size the ADIT runs use) sets the window; the check
scrolls it top to bottom and pools the controls. ADIT_TALL=1 uses one 2400 px tall window.

Writes a JSON summary to $ADIT_MERGE_OUT (default jev-atlas/runs/selfcheck.json).
"""
import collections
import importlib.util
import json
import os
import pathlib
import sys
import time

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
ATLAS = HERE.parent / "atlas" / "adit.json"
HARNESS = os.environ.get("JEV_CLONE", str(__import__('pathlib').Path(__file__).resolve().parents[1] / 'vendor' / 'jev-ultrafast')).rstrip("/") + "/jev_ultrafast/"
OUTFILE = os.environ.get("ADIT_MERGE_OUT", str(__import__("pathlib").Path(__file__).resolve().parents[1] / "runs" / "selfcheck.json"))
BASE = "https://alejandroerickson.com/mockent/adit/"
# The agent's own window (the harness reads JEV_VIEWPORT the same way). At a normal height
# the check scrolls the page top to bottom and pools what each position offers, as the
# agent's Scroll down would; ADIT_TALL=1 uses one 2400 px tall window instead.
_vw, _vh = (int(x) for x in os.environ.get("JEV_VIEWPORT", "1700x900").lower().split("x"))
VIEW = {"width": _vw, "height": 2400 if os.environ.get("ADIT_TALL") == "1" else _vh}

spec = importlib.util.spec_from_file_location("harness_atlas", HARNESS + "atlas.py")
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
book = A.load(ATLAS)
SNAP = pathlib.Path(HARNESS + "snapshot.js").read_text()
SEL = A.selector_lists(book)
PAGES = {p["id"]: p for p in book.data["pages"]}
CHROME_AREA = "portfolio-global"
CHROME_OVERLAYS = {"notification-tray", "account-menu"}
# The top bar's landmarks, as the reader names them. Filter bars are `search` landmarks too,
# so a `search` element counts as top bar only in the first 48 px of the page.
TOP_BAR = {"banner", "navigation: Sections", "search"}

EXM, PGEO, DBGEO, LOG, FIN, TEN, SYS, PG2 = ("u-mokonkwo", "u-twierzbicki", "u-praghunathan", "u-dsorensen",
                                             "u-ymbeki", "u-hferrier", "u-abarrientos", "u-kholloway")
ALL_USERS = [EXM, PGEO, DBGEO, LOG, FIN, TEN, SYS, PG2]

PRJ, PRG, HOLE, LAB, RES, WF = "PRJ-0433", "PRG-2026-024", "BR-RC-001", "LAB-26-04445", "RES-2026-05", "WF-2026-0147"


def S(tag, route, *actions, users=None):
    return {"tag": tag, "route": route, "actions": list(actions), "users": users}


SCENARIOS = [
    # portfolio-global
    S("portfolio", "#/portfolio"), S("portfolio-commodity", "#/portfolio/commodity"),
    S("portfolio-jurisdiction", "#/portfolio/jurisdiction"), S("portfolio-analytics", "#/portfolio/analytics"),
    S("portfolio-budget", "#/portfolio/budget"), S("portfolio-unknown-shape", "#/portfolio/xyz"),
    S("search", "#/search?q=er"), S("search-empty", "#/search"), S("notifications", "#/notifications"),
    S("account", "#/account"), S("account-notifications", "#/account/notifications"),
    S("account-preferences", "#/account/preferences"), S("account-security", "#/account/security"),
    S("manual", "#/manual"), S("manual-section", "#/manual/getting-started"),
    S("not-found", "#/nonexistent-xyz"), S("not-found-admin", "#/admin/xyz"), S("not-found-resources", "#/resources/xyz"),
    S("tray-on-project", f"#/projects/{PRJ}", ("click_css", "button[aria-controls=notif-tray]")),
    S("menu-on-programmes", "#/programmes", ("click_css", "button[aria-controls=user-menu]")),
    S("menu-on-account", "#/account/preferences", ("click_css", "button[aria-controls=user-menu]")),
    S("toast", "#/account", ("click_css", "#content button[type=submit]")),
    # projects
    S("projects-register", "#/projects"), S("projects-register-cut", "#/projects?stage=drilling"),
    S("projects-new", "#/projects/new"), S("project-overview", f"#/projects/{PRJ}"),
    *[S(f"project-{t}", f"#/projects/{PRJ}/{t}") for t in
      ("tenure", "programmes", "drilling", "assays", "resource", "budget", "approvals", "activity")],
    S("project-not-found", "#/projects/NOPE"),
    S("dlg-project-edit", f"#/projects/{PRJ}", ("click_text", "Edit")),
    S("dlg-stage-gate", f"#/projects/{PRJ}", ("click_text", "Stage-gate decision")),
    S("dlg-lodge-renewal", "#/projects/PRJ-0376/tenure", ("click_text", "Lodge renewal"), users=[TEN]),
    # programmes
    S("programmes-list", "#/programmes"), S("programmes-all", "#/programmes?phase=all"),
    S("programmes-new", "#/programmes/new"), S("programmes-schedule", "#/programmes/schedule"),
    S("programmes-rigs", "#/programmes/rigs"), S("programmes-camps", "#/programmes/camps"),
    S("programmes-crew", "#/programmes/crew"), S("programme-overview", f"#/programmes/{PRG}"),
    *[S(f"programme-{t}", f"#/programmes/{PRG}/{t}") for t in ("crew", "logistics", "holes", "approval")],
    S("dlg-assign-crew", f"#/programmes/{PRG}/crew", ("click_text", "Assign crew")),
    S("dlg-move-phase", f"#/programmes/{PRG}", ("click_prefix", "Move to"), users=ALL_USERS),
    S("dlg-logistics-item", f"#/programmes/{PRG}/logistics", ("click_text", "Add item"), users=ALL_USERS),
    S("dlg-rig-update", "#/programmes/rigs", ("click_text", "Update"), users=[LOG]),
    # drilling-assays
    S("drilling-list", "#/drilling"), S("drilling-planned", "#/drilling?status=planned"),
    S("drilling-intercepts", "#/drilling/intercepts"), S("drilling-hole", f"#/drilling/{HOLE}"),
    S("assays-batches", "#/assays"), S("assays-new", "#/assays/new"), S("assays-qaqc", "#/assays/qaqc"),
    S("assays-samples", "#/assays/samples"), S("assays-batch", f"#/assays/{LAB}"),
    S("dlg-update-hole", f"#/drilling/{HOLE}", ("click_text", "Update hole"), users=[DBGEO]),
    S("dlg-import-results", "#/assays?status=lab", ("first_link", "#/assays/LAB-"), ("click_text", "Import results"), users=[DBGEO]),
    S("dlg-accept-batch", "#/assays?status=received", ("first_link", "#/assays/LAB-"), ("click_text", "Accept batch"), users=[DBGEO]),
    S("dlg-hold-batch", "#/assays?status=received", ("first_link", "#/assays/LAB-"), ("click_text", "Place on hold"), users=[DBGEO]),
    S("dlg-reject-batch", "#/assays?status=received", ("first_link", "#/assays/LAB-"), ("click_text", "Reject"), users=[DBGEO]),
    # resources-optimiser
    S("resources-portfolio", "#/resources"), S("resources-estimates", "#/resources/estimates"),
    S("resources-estimate-new", "#/resources/estimates/new", users=[PGEO]),
    S("resources-estimate", f"#/resources/estimates/{RES}"), S("resources-forecast", "#/resources/forecast"),
    S("resources-price-deck", "#/resources/price-deck"), S("resources-valuation", "#/resources/valuation"),
    S("optimiser", "#/optimiser"), S("optimiser-scenarios", "#/optimiser/scenarios"),
    S("optimiser-targets", "#/optimiser/targets"),
    S("dlg-submit-release", "#/resources/estimates", ("find_link_with", "#/resources/estimates/RES-", "Submit for release"),
      ("click_text", "Submit for release"), users=[PGEO]),
    S("dlg-change-status", "#/resources/estimates", ("find_link_with", "#/resources/estimates/RES-", "Change status"),
      ("click_text", "Change status"), users=[PGEO]),
    S("dlg-edit-deck", "#/resources/price-deck", ("click_text", "Edit deck"), users=[SYS]),
    S("dlg-save-scenario", "#/optimiser", ("click_text", "Save scenario"), users=ALL_USERS),
    # approvals
    S("approvals-queue", "#/approvals"), S("approvals-pending", "#/approvals?view=pending"),
    S("approvals-decided", "#/approvals?view=decided"), S("approval-detail", f"#/approvals/{WF}"),
    S("dlg-approve", f"#/approvals/{WF}", ("click_text", "Approve"), users=ALL_USERS),
    S("dlg-return", f"#/approvals/{WF}", ("click_text", "Return"), users=ALL_USERS),
    S("dlg-reject", f"#/approvals/{WF}", ("click_text", "Reject"), users=ALL_USERS),
    # admin
    S("admin-settings", "#/admin", users=[SYS]), S("admin-system", "#/admin/system", users=[SYS]),
    *[S(f"admin-{t}", f"#/admin/{t}", users=[SYS]) for t in
      ("price-deck", "qaqc", "workflows", "reference", "users", "roles", "audit")],
    S("admin-settings-exm", "#/admin"),
    S("dlg-reset-tenant", "#/admin", ("click_text", "Reset demonstration tenant"), users=[SYS]),
    S("dlg-reset-tenant-system", "#/admin/system", ("click_text", "Reset demonstration tenant"), users=[SYS]),
    S("dlg-workflow", "#/admin/workflows", ("click_first_css", "main table button"), users=[SYS]),
    S("dlg-add-user", "#/admin/users", ("click_text", "Add user"), users=[SYS]),
    # page action buttons as a user who is offered them (no dialog open)
    S("act-programme", f"#/programmes/{PRG}", ("require", "Assign crew"), users=ALL_USERS),
    S("act-hole", f"#/drilling/{HOLE}", ("require", "Update hole"), users=[DBGEO]),
    S("act-batch", "#/assays?status=received", ("first_link", "#/assays/LAB-"), ("require", "Reject"), users=[DBGEO]),
    S("act-estimate", "#/resources/estimates", ("find_link_with", "#/resources/estimates/RES-", "Change status"), users=[PGEO]),
    S("act-price-deck", "#/resources/price-deck", ("require", "Edit deck"), users=[SYS]),
    S("act-optimiser", "#/optimiser", ("require_any", "Lock"), users=ALL_USERS),
    S("act-approval", f"#/approvals/{WF}", ("require", "Approve"), users=ALL_USERS),
    S("act-rigs", "#/programmes/rigs", ("require", "Update"), users=[LOG]),
    S("act-comment", f"#/approvals/{WF}", ("fill", "main form.comment-form textarea", "A note for @Tomasz"),
      ("require", "Post comment")),
    S("act-dispatch-toast", "#/assays/new", ("dispatch",), users=[DBGEO]),
    S("dlg-edit-user", "#/admin/users", ("click_text", "Edit"), users=[SYS]),
]

CLICK_JS = """([text, prefix]) => {
  const ok = e => e.checkVisibility() && !e.closest('dialog') && !e.disabled;
  const t = e => (e.innerText || e.textContent || '').trim().replace(/\\s+/g, ' ');
  const hit = [...document.querySelectorAll('main button, main a, #content button, #content a')]
    .find(e => ok(e) && (prefix ? t(e).startsWith(text) : t(e) === text));
  if (!hit) return false; hit.click(); return true; }"""


class Browser:
    def __init__(self, pg): self.pg = pg
    def evaluate(self, expr): return self.pg.evaluate(expr)


def goto(pg, route, user):
    pg.goto(BASE + "#/portfolio")
    pg.wait_for_timeout(700)
    pg.evaluate("u => { localStorage.removeItem('adit.session.v1'); localStorage.removeItem('adit.tenant.v1');"
                " if (u) localStorage.setItem('adit.session.v1', JSON.stringify({currentUserId: u, theme: 'dark'})); }", user)
    pg.goto(BASE + route)
    pg.reload()
    pg.wait_for_timeout(1200)


def act(pg, action):
    kind = action[0]
    if kind == "click_css":
        pg.click(action[1])
    elif kind == "click_first_css":
        pg.locator(action[1]).first.click()
    elif kind in ("click_text", "click_prefix"):
        if not pg.evaluate(CLICK_JS, [action[1], kind == "click_prefix"]):
            return False
    elif kind in ("require", "require_any"):
        return pg.evaluate("([t, any]) => [...document.querySelectorAll('button, a')].some(b => b.checkVisibility() && (any ? b.textContent.trim() === t : !!b.closest('main') && b.textContent.trim() === t))", [action[1], kind == "require_any"])
    elif kind == "fill":
        pg.fill(action[1], action[2])
    elif kind == "dispatch":
        # tick the first hole pill, then Submit dispatch; the toast carries an Open link
        pg.evaluate("() => { const l = document.querySelector('main label input[type=checkbox]'); if (l) l.click(); }")
        pg.wait_for_timeout(300)
        if not pg.evaluate(CLICK_JS, ["Submit dispatch", False]):
            return False
        pg.wait_for_timeout(600)
        return pg.evaluate("!!document.querySelector('.toasts .toast')")
    elif kind == "first_link":
        href = pg.evaluate("p => [...document.querySelectorAll('a[href]')].map(a => a.getAttribute('href')).find(h => h.startsWith(p))", action[1])
        if not href:
            return False
        pg.goto(BASE + href)
        pg.wait_for_timeout(900)
    elif kind == "find_link_with":
        hrefs = pg.evaluate("p => [...new Set([...document.querySelectorAll('a[href]')].map(a => a.getAttribute('href')).filter(h => h.startsWith(p)))]", action[1])
        for href in hrefs:
            pg.goto(BASE + href)
            pg.wait_for_timeout(800)
            if pg.evaluate("t => [...document.querySelectorAll('main button')].some(b => b.textContent.trim() === t && b.checkVisibility())", action[2]):
                break
        else:
            return False
    pg.wait_for_timeout(500)
    return True


def fields(a, page_id):  # the same fields model.match_fields builds
    return {"track_id": a.get("track_id"), "id": a.get("dom_id"), "title": a.get("title"), "href": a.get("href"),
            "ancestor": a.get("ancestor"), "row_label": a.get("row_label"), "role": a.get("role"),
            "section": a.get("section"), "landmark": a.get("landmark"),
            "text": a.get("label", "").split(" → ")[0], "page": page_id}


def snapshots(pg):
    """snapshot.js at each scroll position of the window, top to bottom (dialogs do not scroll the page)."""
    shots, seen_y = [], set()
    pg.evaluate("window.scrollTo(0, 0)")
    for _ in range(40):
        pg.wait_for_timeout(120)
        shots.append(pg.evaluate(f"({SNAP})({json.dumps(SEL)})"))
        y = pg.evaluate("scrollY")
        if y in seen_y or shots[-1].get("dialog_title") or pg.evaluate("!!document.querySelector('dialog[open]')"):
            break
        seen_y.add(y)
        pg.evaluate(f"window.scrollBy(0, {max(VIEW['height'] - 150, 200)})")
        if pg.evaluate("scrollY") == y:
            break
    pg.evaluate("window.scrollTo(0, 0)")
    return shots


def check_state(pg, sc):
    shots = snapshots(pg)
    st = dict(shots[0])
    pooled = {}
    for shot in shots:
        for a in shot["actions"]:
            if "node" not in a:
                continue
            k = (a["node"], a.get("kind"), a.get("value"))
            if k not in pooled or (pooled[k].get("covered") and not a.get("covered")):
                pooled[k] = a
    st["actions"] = list(pooled.values())
    page = book.match_page(st["url"])
    pid = page["id"] if page else None
    found = book.probe(Browser(pg), page)
    overlays = book.active_overlays(found["selectors"], st.get("dialog_title"))
    ov_ids = [o["id"] for o in overlays]
    in_view = [i for i in [pid, *ov_ids] if i]
    ok_areas = {"shared", CHROME_AREA} | {PAGES[i].get("area") for i in in_view}
    nodes = collections.OrderedDict()
    for a in st["actions"]:
        if "node" not in a:
            continue
        e = book.match_control(fields(a, pid), in_view)
        if a["node"] not in nodes or (e and nodes[a["node"]][1] is None):
            nodes[a["node"]] = (a, e)
    dialog_open = any(a.get("in_dialog") for a, _ in nodes.values())
    total = annotated = 0
    unmatched, flags, hits, seen_el = [], [], [], []
    for a, e in nodes.values():
        # With a modal dialog open, only what is in the dialog (and not covered) is reachable.
        if a.get("covered"):
            continue
        total += 1
        if not e:
            unmatched.append(a["label"][:60])
            continue
        annotated += 1
        hits.append(json.dumps(e["key"], sort_keys=True, ensure_ascii=False))
        seen_el.append({k: a.get(k) for k in ("label", "role", "href", "row_label", "section", "landmark", "in_dialog")}
                       | {"key": e["key"], "area": e.get("area"), "region": e["region"]})
        area, kp = e.get("area"), e["key"].get("page")
        label = a["label"][:50]
        # The not-found page keeps its section's left column, whose entries are page-less.
        if area not in ok_areas and not (pid == "not-found" and "page" not in e["key"]):
            flags.append(f"AREA {label!r} <- {area}: {e['region']}")
        if kp in PAGES and PAGES[kp].get("layer") == "overlay" and kp not in CHROME_OVERLAYS and not a.get("in_dialog"):
            flags.append(f"DIALOG {label!r} outside a dialog <- {e['region']}")
        if a.get("in_dialog") and area not in ("shared", CHROME_AREA) and not (kp in PAGES and PAGES[kp].get("layer") == "overlay"):
            flags.append(f"DIALOG {label!r} in a dialog <- page entry {e['region']}")
        k = e["key"]
        if a.get("role") in ("button", "link", "checkbox", "radio") and "row_label" in k and not (
                {"text", "text_regex", "role"} & set(k)):
            flags.append(f"ROWLABEL {a['role']} {label!r} took a form field's note <- {e['region']}")
        if e["key"] == {"text": "Cancel", "role": "button"} and not a.get("in_dialog"):
            flags.append(f"DIALOG {label!r} generic dialog Cancel outside a dialog")
        lm, region = a.get("landmark") or "", e["region"]
        if region.startswith("Page footer") and lm != "contentinfo":
            flags.append(f"LANDMARK {label!r} in {lm or 'no landmark'} <- footer entry")
        if (lm == "navigation: Breadcrumb") != region.lower().startswith("breadcrumb"):
            flags.append(f"LANDMARK {label!r} in {lm or 'no landmark'} <- {region}")
        if region.startswith("Top bar") and lm not in TOP_BAR:
            flags.append(f"LANDMARK {label!r} in {lm or 'no landmark'} <- top-bar entry")
        top_bar = a.get("landmark") in TOP_BAR and (a.get("landmark") != "search" or 0 <= a["rect"]["y"] < 48)
        if top_bar and area != CHROME_AREA and not a.get("in_dialog"):
            flags.append(f"CHROME {label!r} <- {area}: {e['region']}")
    facts = [f for fs in found["facts"].values() for f in fs]
    return {"tag": sc["tag"], "url": st["url"].split("#", 1)[-1], "page": pid, "overlays": ov_ids,
            "dialog_title": st.get("dialog_title"), "dialog_open": dialog_open,
            "total": total, "annotated": annotated, "unmatched": unmatched, "flags": flags, "hits": hits, "elements": seen_el,
            "n_facts": len(facts), "facts": facts, "virtual": {k: len(v) for k, v in found["virtual"].items()}}


def run(only=None, verbose=False):
    results = []
    with sync_playwright() as p:
        br = p.chromium.launch()
        for sc in SCENARIOS:
            if only and sc["tag"] not in only:
                continue
            res = None
            for user in (sc["users"] or [None]):
                ctx = br.new_context(viewport=VIEW)
                pg = ctx.new_page()
                try:
                    for attempt in range(3):
                        try:
                            goto(pg, sc["route"], user)
                            break
                        except Exception:
                            time.sleep(2)
                    done = all(act(pg, a) for a in sc["actions"])
                    if done and (not sc["tag"].startswith("dlg-") or pg.evaluate("!!document.querySelector('dialog[open]')")):
                        res = check_state(pg, sc)
                        res["user"] = user
                finally:
                    ctx.close()
                if res:
                    break
            if not res:
                res = {"tag": sc["tag"], "url": sc["route"], "page": None, "error": "could not reach this state"}
                print(f"{sc['tag']:26} FAILED to reach state")
            else:
                pct = 100 * res["annotated"] / max(res["total"], 1)
                print(f"{sc['tag']:26} {res['page']!s:24} ov={','.join(res['overlays']) or '-':28} "
                      f"{res['annotated']:3}/{res['total']:3} {pct:5.1f}%  flags={len(res['flags'])}  "
                      f"facts={res['n_facts']}  dlg={res['dialog_title'][:30]!r}")
                for f in res["flags"]:
                    print("      !", f)
                if res["unmatched"] and (verbose or pct < 100):
                    print("      unannotated:", res["unmatched"][:10], "..." if len(res["unmatched"]) > 10 else "")
                if verbose:
                    for f in res["facts"]:
                        print("      fact:", f[:200])
            results.append(res)
        br.close()
    hits = collections.Counter(h for r in results for h in r.get("hits", []))
    dead = [c for c in book.controls if json.dumps(c["key"], sort_keys=True, ensure_ascii=False) not in hits]
    total = sum(r.get("total", 0) for r in results)
    ann = sum(r.get("annotated", 0) for r in results)
    flags = sum(len(r.get("flags", [])) for r in results)
    print(f"\nTOTAL {ann}/{total} = {100 * ann / max(total, 1):.1f}% annotated over {len(results)} states; flags {flags}; "
          f"entries never matched {len(dead)}/{len(book.controls)}")
    pathlib.Path(OUTFILE).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(OUTFILE).write_text(json.dumps({"atlas_sha256_12": book.sha256, "results": results,
                                                 "dead": [{"area": c.get("area"), "key": c["key"]} for c in dead]},
                                                indent=1, ensure_ascii=False))
    return results


if __name__ == "__main__":
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    run(only, "-v" in sys.argv)

"""Reset ADIT's demo tenant, and check whether a goal in goals.md was achieved.

    python check.py reset                 # clear adit.* localStorage and reload
    python check.py check G5              # print pass/fail and details as JSON
    python check.py list                  # the goals, their split and text

The browser is the Chrome named by ADIT_CDP_URL (else BU_CDP_URL, else
http://127.0.0.1:9333). All state is client-side in that browser profile's
localStorage for the ADIT origin, so a check opens its own tab on the app,
reads adit.tenant.v1 and closes the tab. Run with any Python that has
`websockets` (the harness clone's venv does).
"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

APP = "https://alejandroerickson.com/mockent/adit/"
START = APP + "#/portfolio"
KEYS = ("adit.tenant.v1", "adit.session.v1")

GOALS = {
    "G1": ("new-project", "tuning",
           "we just staked some ground up in the yukon, set it up as a new gold project, call it quartz flat, "
           "it's about 55 square k's, four hundred thousand for the year and give it to kieran"),
    "G2": ("gate-hold", "held-out",
           "sable dome's gate is coming up and i don't want to hand it over yet, the phase two results were too thin, "
           "just park it where it is for now"),
    "G3": ("tenure-renewal", "held-out",
           "can you do hamish's job for a sec, the wolverine creek claim that runs out end of november, "
           "get the renewal going on it"),
    "G4": ("new-programme", "held-out",
           "kieran wants a mapping program on copper hollow in the spring, northern claims, about 120 grand, "
           "april through may, set it up under his name"),
    "G5": ("approve-variance", "tuning",
           "tomasz answered yolanda's question on the mount aster overrun so go ahead and sign that off"),
    "G6": ("return-request", "held-out",
           "the copper hollow scout RC request, bounce it back to kieran, i want the rig costs broken out "
           "before i say yes"),
    "G7": ("release-estimate", "held-out",
           "bellamy ridge's maiden resource has to go out this week, tomasz has finished his QP review so do his "
           "step as him and then release it as me"),
    "G8": ("move-gate", "held-out",
           "lorimer's gate is slipping, move it to the end of january"),
}

# Expert-style goals (goals-expert.md): specific records by id, the system's own vocabulary,
# exact values. Split "expert"; baseline.py runs them with --set expert.
GOALS.update({
    "E1": ("comment-batch", "expert",
           'Post a comment on batch LAB-26-04483: "Geostat is re-running OREAS 252 and the ten samples '
           'either side; results due 2026-10-02."'),
    "E2": ("gate-hold-reason", "expert",
           "Record a stage-gate decision on PRJ-0468 Dunmore Flats: place it on hold at Reconnaissance, "
           'reasoning "Waiting on the legacy seismic reprocessing before we commit to DF-01."'),
    "E3": ("lodge-renewal", "expert",
           "As Hamish Ferrier, lodge the renewal for tenement NMC 1174648 on PRJ-0387 Bellamy Ridge."),
    "E4": ("create-programme", "expert",
           'As Tomasz Wierzbicki, create a geochem programme on PRJ-0468 Dunmore Flats called "Soil sampling, '
           'northern block", 2027-05-03 to 2027-06-25, budget 85,000 USD, objective "Soil grid on 200 m '
           'centres over the northern mineral claims."'),
    "E5": ("reject-request", "expert",
           'Reject WF-2026-0146 (Scout RC, Copper Hollow) with the reason "Hold the rig spend until the land '
           'access agreement WF-2026-0155 is signed."'),
    "E6": ("approve-as-finance", "expert",
           "Switch to Yolanda Mbeki and approve the Budget check on WF-2026-0145 (cyanidation testwork, "
           'Wolverine Creek) with the note "Within the FY26 metallurgy allocation."'),
    "E7": ("qaqc-hold", "expert",
           "As Priya Raghunathan, place assay batch LAB-26-04464 from Kettle Lake on QAQC hold."),
    "E8": ("update-hole", "expert",
           "As Tomasz Wierzbicki, update hole WC-DDH-033 to completed at a depth of 362 m, completed 2026-09-22."),
    "E9": ("create-estimate", "expert",
           "As Tomasz Wierzbicki, create a draft resource estimate for PRJ-0409 Kettle Lake: ordinary kriging, "
           "cut-off 0.3 % Ni, Indicated 4.2 Mt at 1.35 % Ni and Inferred 6.8 Mt at 1.10 % Ni."),
    "E10": ("edit-gate-forecast", "expert",
            "On PRJ-0409 Kettle Lake, move the next gate to 2027-04-15 and set the year-end forecast to "
            "3,150,000 USD."),
    "E11": ("assign-crew", "expert",
            "As Declan Sørensen, assign Ezra Lindqvist to PRG-2026-025 (Downhole EM, Phase 3 holes) as "
            "Geophysicist, rotation 2026-10-05 to 2026-10-19."),
    "E12": ("find-and-report", "expert",
            "Find every assay batch on QAQC hold for Cerro Azufre (PRJ-0376) and post their batch ids as a "
            "comment on the project."),
})
EXPERT = [k for k in GOALS if k.startswith("E")]

SEED_PROGRAMMES = {"PRG-2026-012", "PRG-2026-029", "PRG-2026-027", "PRG-2027-030"}  # on PRJ-0441 and PRJ-0468
SEED_ESTIMATES = {"RES-2026-03", "RES-2025-02", "RES-2026-01", "RES-2026-05", "RES-2026-02", "RES-2026-04",
                  "RES-2025-04", "RES-2026-06"}
SEED_COMMENTS = {f"c-{i:03d}" for i in range(1, 10)}
# Seed values of the fields an edit goal must leave alone (G8 on PRJ-0421, E10 on PRJ-0409).
SEED_PROJECT_FIELDS = {
    "PRJ-0421": {"name": "Lorimer", "stage": "scoping", "status": "active", "geologistId": "u-twierzbicki",
                 "planned": 2600000, "forecast": 2724827},
    "PRJ-0409": {"name": "Kettle Lake", "stage": "drilling", "status": "active", "geologistId": "u-twierzbicki",
                 "planned": 2900000},
}
SEED_CREW_025 = {"u-twierzbicki", "f-08", "f-01", "f-02", "f-12"}  # PRG-2026-025's crew before E11

# How a check works. Each goal lists its required facts as named booleans in
# details["required"]; pass means every one of them holds. The facts are the goal's
# stated end state (the right record, the right field, the exact values the goal gives)
# and, where it is cheap, that the run did not do the same kind of thing to a wrong
# record (read from the audit entries the run added). Nothing the goal did not ask for
# is required: side effects of other kinds are listed in details["side_effects"] only.


def by_id(items, id_):
    return next((x for x in items if x.get("id") == id_), None) or {}


def _norm(s):
    """Lower case, collapsed whitespace, no surrounding quotes or trailing full stop."""
    return re.sub(r"\s+", " ", (s or "")).strip().strip("\"'“”").rstrip(".").strip().lower()


def _says(text, expected):
    return _norm(expected) in _norm(text)


def _run_audit(w):
    """Audit entries the run added (seed entries have ids a-00000), without sign-ins."""
    return [a for a in w["audit"] if not re.match(r"^a-\d{5}$", a["id"]) and a["action"] != "session.signin"]


def _stray(w, prefixes, allowed):
    """Run audit entries of these action families on any entity other than the allowed ones."""
    return [f'{a["userId"]}:{a["action"]}:{a["entityId"]}' for a in _run_audit(w)
            if a["action"].startswith(tuple(prefixes)) and a["entityId"] not in allowed]


def _did(w, user, action, entity, detail_prefix=""):
    return any(a["userId"] == user and a["action"] == action and a["entityId"] == entity
               and (a.get("detail") or "").startswith(detail_prefix) for a in _run_audit(w))


def _new_comments(w, etype, eid):
    return [c for c in w["comments"] if c["id"] not in SEED_COMMENTS
            and c.get("entityType") == etype and c.get("entityId") == eid]


def _unchanged(p, pid):
    seed = SEED_PROJECT_FIELDS[pid]
    b = p.get("budget") or {}
    return all((b.get(k) if k in ("planned", "forecast") else p.get(k)) == v for k, v in seed.items())


DECISIONS = ("approval.approved", "approval.rejected", "approval.returned")


def check_world(goal, w):
    P, A = w["projects"], w["approvals"]
    if goal == "G1":
        hits = [p for p in P if _norm(p.get("name")) == "quartz flat"]
        p = hits[-1] if hits else {}
        b = p.get("budget") or {}
        r = {"one_project_named_quartz_flat": len(hits) == 1,
             "commodity_Au": p.get("commodity") == "Au",
             "geologist_kieran": p.get("geologistId") == "u-kholloway",
             "budget_400000": b.get("planned") == 400000,
             "jurisdiction_yukon": "yukon" in (p.get("jurisdiction") or "").lower(),
             "country_canada": p.get("country") == "Canada",
             "area_55": p.get("areaKm2") == 55,
             "no_other_project_created_or_edited": not _stray(w, ["project."], {p.get("id")})}
        d = {"id": p.get("id"), "commodity": p.get("commodity"), "geologist": p.get("geologistId"),
             "budget": b.get("planned"), "jurisdiction": p.get("jurisdiction"), "country": p.get("country"),
             "area": p.get("areaKm2"), "count": len(hits)}
    elif goal == "G2":
        p = by_id(P, "PRJ-0433")
        acts = [a["action"] for a in _run_audit(w) if a["entityId"] == "PRJ-0433" and a["action"].startswith("gate.")]
        r = {"status_on_hold": p.get("status") == "on-hold",
             "stage_unchanged_decision": p.get("stage") == "decision",
             "gate_hold_recorded": set(acts) == {"gate.hold"},
             "no_gate_decision_on_other_projects": not _stray(w, ["gate."], {"PRJ-0433"})}
        d = {"status": p.get("status"), "stage": p.get("stage"), "gate_actions": acts}
    elif goal == "G3":
        t = by_id(w["tenements"], "382742")
        reqs = [a for a in A if a.get("type") == "tenement-renewal" and a.get("subjectId") == "382742"]
        r = {"tenement_renewal_lodged": t.get("status") == "renewal-lodged",
             "one_renewal_request": len(reqs) == 1,
             "requested_by_hamish": bool(reqs) and all(a.get("requestedById") == "u-hferrier" for a in reqs),
             "no_other_tenement_touched": not _stray(w, ["tenement."], {"382742"}),
             "no_other_request_submitted": not _stray(w, ["approval.submitted"], {a["id"] for a in reqs})}
        d = {"status": t.get("status"), "requests": [a["id"] for a in reqs]}
    elif goal == "G4":
        new = [g for g in w["programmes"] if g.get("projectId") == "PRJ-0441" and g["id"] not in SEED_PROGRAMMES]
        g = new[-1] if new else {}
        r = {"one_new_programme_on_copper_hollow": len(new) == 1,
             "type_mapping": g.get("type") == "mapping",
             "budget_120000": g.get("budget") == 120000,
             "lead_kieran": g.get("leadId") == "u-kholloway",
             "starts_april_2027": (g.get("startOn") or "").startswith("2027-04"),
             "ends_may_2027": (g.get("endOn") or "").startswith("2027-05"),
             "no_programme_created_elsewhere": not _stray(w, ["programme.created"], {x["id"] for x in new})}
        d = {"new": [(x["id"], x.get("type"), x.get("name"), x.get("budget")) for x in new],
             "lead": g.get("leadId"), "start": g.get("startOn"), "end": g.get("endOn")}
    elif goal == "G5":
        a = by_id(A, "WF-2026-0152")
        r = {"request_approved": a.get("status") == "approved",
             "manager_step_approved_by_marguerite": _did(w, "u-mokonkwo", "approval.approved", "WF-2026-0152",
                                                         "Manager approval"),
             "no_other_request_decided": not _stray(w, DECISIONS, {"WF-2026-0152"})}
        d = {"status": a.get("status")}
    elif goal == "G6":
        a = by_id(A, "WF-2026-0146")
        note = next((s.get("note") or "" for s in a.get("steps", []) if s.get("decision") == "returned"), "")
        r = {"request_returned": a.get("status") == "returned",
             "return_note_mentions_rig": "rig" in note.lower(),
             "no_other_request_decided": not _stray(w, DECISIONS, {"WF-2026-0146"})}
        d = {"status": a.get("status"), "note": note}
    elif goal == "G7":
        e = by_id(w["estimates"], "RES-2026-03")
        a = by_id(A, "WF-2026-0159")
        r = {"estimate_released": e.get("status") == "released",
             "request_approved": a.get("status") == "approved",
             "qp_review_by_tomasz": _did(w, "u-twierzbicki", "approval.approved", "WF-2026-0159", "QP review"),
             "manager_release_by_marguerite": _did(w, "u-mokonkwo", "approval.approved", "WF-2026-0159",
                                                   "Manager release"),
             "no_other_request_decided": not _stray(w, DECISIONS, {"WF-2026-0159"})}
        d = {"estimate": e.get("status"), "request": a.get("status"),
             "steps": [(s["name"], s.get("decision")) for s in a.get("steps", [])]}
    elif goal == "G8":
        p = by_id(P, "PRJ-0421")
        g = p.get("nextGateOn") or ""
        r = {"next_gate_end_of_january_2027": "2027-01-25" <= g <= "2027-01-31",
             "other_fields_unchanged": _unchanged(p, "PRJ-0421"),
             "no_other_project_edited": not _stray(w, ["project.", "gate."], {"PRJ-0421"})}
        d = {"nextGateOn": g, "exact": g == "2027-01-31"}
    elif goal.startswith("E"):
        r, d = check_expert(goal, w)
    else:
        raise SystemExit(f"unknown goal {goal}")
    d["required"] = r
    d["side_effects"] = [f'{a["userId"]}:{a["action"]}:{a["entityId"]}' for a in _run_audit(w)]
    return all(r.values()), d


def check_expert(goal, w):
    P, A = w["projects"], w["approvals"]
    if goal == "E1":
        text = "Geostat is re-running OREAS 252 and the ten samples either side; results due 2026-10-02."
        cs = _new_comments(w, "batch", "LAB-26-04483")
        elsewhere = [c for c in w["comments"] if c["id"] not in SEED_COMMENTS and c not in cs
                     and "oreas 252" in c["body"].lower()]
        return {"one_new_comment_on_batch": len(cs) == 1,
                "comment_has_the_text": any(_says(c["body"], text) for c in cs),
                "not_posted_on_another_record": not elsewhere}, \
            {"new_comments": [(c["authorId"], c["body"]) for c in cs],
             "elsewhere": [(c["entityType"], c["entityId"]) for c in elsewhere]}
    if goal == "E2":
        p = by_id(P, "PRJ-0468")
        au = [a for a in _run_audit(w) if a["entityId"] == "PRJ-0468" and a["action"].startswith("gate.")]
        return {"status_on_hold": p.get("status") == "on-hold",
                "stage_recon": p.get("stage") == "recon",
                "gate_hold_recorded": {a["action"] for a in au} == {"gate.hold"},
                "reasoning_is_the_text": any(_says(a.get("detail"), "Waiting on the legacy seismic reprocessing "
                                                                    "before we commit to DF-01.") for a in au),
                "no_gate_decision_on_other_projects": not _stray(w, ["gate."], {"PRJ-0468"})}, \
            {"status": p.get("status"), "stage": p.get("stage"),
             "gate_audit": [(a["action"], a.get("detail")) for a in au]}
    if goal == "E3":
        t = by_id(w["tenements"], "NMC 1174648")
        reqs = [a for a in A if a.get("type") == "tenement-renewal" and a.get("subjectId") == "NMC 1174648"]
        return {"tenement_renewal_lodged": t.get("status") == "renewal-lodged",
                "one_renewal_request": len(reqs) == 1,
                "requested_by_hamish": bool(reqs) and all(a.get("requestedById") == "u-hferrier" for a in reqs),
                "no_other_tenement_touched": not _stray(w, ["tenement."], {"NMC 1174648"}),
                "no_other_request_submitted": not _stray(w, ["approval.submitted"], {a["id"] for a in reqs})}, \
            {"status": t.get("status"), "requests": [a["id"] for a in reqs]}
    if goal == "E4":
        new = [g for g in w["programmes"] if g.get("projectId") == "PRJ-0468" and g["id"] not in SEED_PROGRAMMES]
        g = new[-1] if new else {}
        return {"one_new_programme_on_PRJ-0468": len(new) == 1,
                "type_geochem": g.get("type") == "geochem",
                "name_exact": _norm(g.get("name")) == _norm("Soil sampling, northern block"),
                "start_2027-05-03": g.get("startOn") == "2027-05-03",
                "end_2027-06-25": g.get("endOn") == "2027-06-25",
                "budget_85000": g.get("budget") == 85000,
                "objective_exact": _norm(g.get("objective")) == _norm("Soil grid on 200 m centres over the "
                                                                      "northern mineral claims."),
                "lead_tomasz": g.get("leadId") == "u-twierzbicki",
                "no_programme_created_elsewhere": not _stray(w, ["programme.created"], {x["id"] for x in new})}, \
            {"new": [(x["id"], x.get("type"), x.get("name"), x.get("budget"), x.get("startOn"), x.get("endOn"),
                      x.get("objective"), x.get("leadId")) for x in new]}
    if goal == "E5":
        a = by_id(A, "WF-2026-0146")
        note = next((s.get("note") or "" for s in a.get("steps", []) if s.get("decision") == "rejected"), "")
        return {"request_rejected": a.get("status") == "rejected",
                "reason_is_the_text": _says(note, "Hold the rig spend until the land access agreement "
                                                  "WF-2026-0155 is signed."),
                "no_other_request_decided": not _stray(w, DECISIONS, {"WF-2026-0146"})}, \
            {"status": a.get("status"), "note": note}
    if goal == "E6":
        a = by_id(A, "WF-2026-0145")
        steps = {s["name"]: s for s in a.get("steps", [])}
        bc, mgr = steps.get("Budget check", {}), steps.get("Manager approval", {})
        return {"budget_check_approved": bc.get("decision") == "approved",
                "approved_as_yolanda": _did(w, "u-ymbeki", "approval.approved", "WF-2026-0145", "Budget check"),
                "note_in_the_decision_note": _says(bc.get("note"), "Within the FY26 metallurgy allocation."),
                "manager_step_left_alone": not mgr.get("decision") and a.get("status") == "pending",
                "no_other_request_decided": not _stray(w, DECISIONS, {"WF-2026-0145"})}, \
            {"status": a.get("status"),
             "steps": [(s["name"], s.get("decision"), s.get("note")) for s in a.get("steps", [])],
             "comments_on_request": [c["body"] for c in _new_comments(w, "approval", "WF-2026-0145")]}
    if goal == "E7":
        b = by_id(w["batches"], "LAB-26-04464")
        return {"batch_qaqc_hold": b.get("status") == "qaqc-hold",
                "done_as_priya": _did(w, "u-praghunathan", "batch.updated", "LAB-26-04464"),
                "no_other_batch_changed": not _stray(w, ["batch."], {"LAB-26-04464"})}, \
            {"status": b.get("status")}
    if goal == "E8":
        h = by_id(w["holes"], "WC-DDH-033")
        return {"status_completed": h.get("status") == "completed",
                "depth_362": h.get("depth") == 362,
                "completed_on_2026-09-22": h.get("completedOn") == "2026-09-22",
                "done_as_tomasz": _did(w, "u-twierzbicki", "hole.updated", "WC-DDH-033"),
                "no_other_hole_changed": not _stray(w, ["hole."], {"WC-DDH-033"})}, \
            {"status": h.get("status"), "depth": h.get("depth"), "completedOn": h.get("completedOn")}
    if goal == "E9":
        new = [e for e in w["estimates"] if e["id"] not in SEED_ESTIMATES and e.get("projectId") == "PRJ-0409"]
        e = new[-1] if new else {}

        def blk(e, cat):
            b = next((x for x in e.get("blocks") or [] if x.get("category") == cat), {})
            return b.get("tonnes"), b.get("grade")
        return {"one_new_estimate_on_PRJ-0409": len(new) == 1,
                "status_draft": e.get("status") == "draft",
                "method_ordinary_kriging": e.get("method") == "Ordinary kriging",
                "cutoff_0.3": e.get("cutoff") == 0.3,
                "indicated_4.2_at_1.35": blk(e, "indicated") == (4.2, 1.35),
                "inferred_6.8_at_1.10": blk(e, "inferred") == (6.8, 1.1),
                "author_tomasz": e.get("authorId") == "u-twierzbicki",
                "no_other_estimate_changed": not _stray(w, ["estimate."], {x["id"] for x in new})}, \
            {"new": [(x["id"], x.get("status"), x.get("method"), x.get("cutoff"), blk(x, "indicated"),
                      blk(x, "inferred"), x.get("authorId")) for x in new]}
    if goal == "E10":
        p = by_id(P, "PRJ-0409")
        g, f = p.get("nextGateOn"), (p.get("budget") or {}).get("forecast")
        return {"next_gate_2027-04-15": g == "2027-04-15",
                "forecast_3150000": f == 3150000,
                "other_fields_unchanged": _unchanged(p, "PRJ-0409"),
                "no_other_project_edited": not _stray(w, ["project.", "gate."], {"PRJ-0409"})}, \
            {"nextGateOn": g, "forecast": f}
    if goal == "E11":
        g = by_id(w["programmes"], "PRG-2026-025")
        crew = g.get("crew") or []
        ez = [c for c in crew if c.get("personId") == "f-09"]
        return {"ezra_assigned_once": len(ez) == 1,
                "rotation_2026-10-05_to_2026-10-19": any(c.get("from") == "2026-10-05" and c.get("to") == "2026-10-19"
                                                         for c in ez),
                "role_geophysicist": any(_norm(c.get("role")) == "geophysicist" for c in ez),
                "done_as_declan": _did(w, "u-dsorensen", "programme.crew", "PRG-2026-025"),
                "rest_of_crew_kept": SEED_CREW_025 <= {c.get("personId") for c in crew} and len(crew) == 6,
                "no_other_programme_crewed": not _stray(w, ["programme.crew"], {"PRG-2026-025"})}, \
            {"ezra": ez, "crew_count": len(crew)}
    if goal == "E12":
        cs = _new_comments(w, "project", "PRJ-0376")
        want = {"LAB-26-04451", "LAB-26-04452"}
        found = [set(re.findall(r"LAB-\d{2}-\d{5}", c["body"])) for c in cs]
        hit = [f for f in found if want <= f]
        return {"comment_on_PRJ-0376_names_both_held_batches": bool(hit),
                "no_other_batch_ids_in_it": any(f == want for f in hit)}, \
            {"new_comments": [c["body"] for c in cs],
             "extra_ids": sorted(set().union(*found) - want) if found else []}
    raise SystemExit(f"unknown goal {goal}")


def _app_tab():
    from cdp import Tab  # needs websockets; imported here so `list`/`goal` work anywhere
    t = Tab()
    t.goto(START)
    return t


def reset():
    t = _app_tab()
    try:
        t.eval(";".join(f"localStorage.removeItem('{k}')" for k in KEYS))
        t.send("Page.reload", ignoreCache=True)
        time.sleep(0.3)
        t.wait_ready()
        s = json.loads(t.eval("localStorage.getItem('adit.session.v1')") or "{}")
        n = len(json.loads(t.eval("localStorage.getItem('adit.tenant.v1')") or "{}").get("world", {}).get("audit", []))
        return {"user": s.get("currentUserId"), "audit": n}
    finally:
        t.close()


def read_state():
    t = _app_tab()
    try:
        w = json.loads(t.eval("localStorage.getItem('adit.tenant.v1')"))["world"]
        s = json.loads(t.eval("localStorage.getItem('adit.session.v1')") or "{}")
        return w, s
    finally:
        t.close()


def check(goal):
    w, s = read_state()
    ok, d = check_world(goal, w)
    d["user_at_end"] = s.get("currentUserId")
    return {"goal": goal, "pass": ok, "details": d}


def main(argv):
    if not argv or argv[0] == "list":
        for k, (slug, split, text) in GOALS.items():
            print(f"{k}\t{slug}\t{split}\t{text}")
    elif argv[0] == "reset":
        print(json.dumps(reset()))
    elif argv[0] == "check":
        print(json.dumps(check(argv[1])))
    elif argv[0] == "goal":
        print(GOALS[argv[1]][2])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])

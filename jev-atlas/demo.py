"""The Jev Atlas demo: five goals, without and with the atlas, then the atlas learning from what still fails.

    jev-atlas/demo.sh all          # the whole story, in the visible Chrome: reset learning, run without,
                                   # run with, learn until nothing fails (at most --rounds), then report
    jev-atlas/demo.sh run with     # one pass of the goals in one condition (with | without)
    jev-atlas/demo.sh learn        # learning rounds only, on the current atlas
    jev-atlas/demo.sh reset        # set learned lessons aside (atlas/learned/archive/), rebuild the base atlas
    jev-atlas/demo.sh report       # rebuild the replay page for the newest session

Options: --goals G5 G2 E9 (default: the five demo goals), --rounds N (default 2),
--yes (accept every lesson that passes the code checks without asking).

A session is a folder demo/sessions/<stamp>/ with session.json: every pass (condition,
atlas version and sha, per goal pass/fail, steps, run folder) and every learning round
(the lesson file, what was accepted). Runs themselves are under goals/runs/<session>-<pass>/.
The outcome of every run is decided by goals/check.py reading the app's own data, never
by the agent's DONE.
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
GOALS_DIR = HERE / "goals"
TOOLS = HERE / "tools"
SESSIONS = HERE / "demo" / "sessions"
ATLAS = HERE / "atlas" / "adit.json"
LEARNED = HERE / "atlas" / "learned"
DEMO_GOALS = ["G5", "G2", "G3", "G7", "E9"]

sys.path.insert(0, str(GOALS_DIR))
sys.path.insert(0, str(TOOLS))
import check  # noqa: E402
import learn  # noqa: E402


def atlas_id():
    raw = ATLAS.read_bytes()
    return json.loads(raw).get("version"), hashlib.sha256(raw).hexdigest()[:12]


def merge():
    out = subprocess.run([sys.executable, str(TOOLS / "merge.py")], capture_output=True, text=True, check=True).stdout
    return [l for l in out.splitlines() if l.startswith(("learned", "sha256"))]


def new_session():
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    d = SESSIONS / stamp
    d.mkdir(parents=True)
    s = {"session": stamp, "goals": {g: check.GOALS[g][2] for g in DEMO_GOALS}, "passes": [], "rounds": []}
    save(d, s)
    return d, s


def latest_session():
    ds = sorted(p for p in SESSIONS.glob("*") if (p / "session.json").exists())
    if not ds:
        return new_session()
    return ds[-1], json.loads((ds[-1] / "session.json").read_text())


def save(d, s):
    (d / "session.json").write_text(json.dumps(s, indent=1, ensure_ascii=False) + "\n")


def run_pass(d, s, condition, goals, name):
    """Every goal once in one condition, through goals/baseline.py (reset before, check after)."""
    label = f"{s['session']}-{name}"
    version, sha = atlas_id() if condition == "with" else (None, None)
    print(f"\n=== {name}: {condition} the atlas" + (f" ({version}, {sha})" if version else ""))
    subprocess.run([sys.executable, str(GOALS_DIR / "baseline.py"), "--n", "1", "--goals", *goals,
                    "--condition", condition, "--label", label], cwd=GOALS_DIR, check=True)
    rows = [json.loads(l) for l in (GOALS_DIR / "results" / f"{label}.jsonl").read_text().splitlines() if l.strip()]
    entry = {"name": name, "condition": condition, "atlas_version": version, "atlas_sha": sha,
             "label": label, "results": {r["goal"]: {
                 "pass": r["pass"], "status": r["harness_status"], "steps": r["steps"], "model": r["model"],
                 "wall_s": r["wall_s"], "run_dir": r["run_dir"], "details": r["details"]} for r in rows}}
    s["passes"].append(entry)
    save(d, s)
    n = sum(r["pass"] for r in entry["results"].values())
    print(f"--- {name}: {n} of {len(rows)} passed")
    return entry


def ask_accept(record, yes):
    ok = [l for l in record["lessons"] if l.get("ok")]
    if not ok:
        return False
    if yes:
        return True
    ans = input("Accept the lessons marked ok? [y/N] ").strip().lower()
    return ans in ("y", "yes")


def learn_rounds(d, s, goals, rounds, yes):
    last = next((p for p in reversed(s["passes"]) if p["condition"] == "with"), None)
    if last is None or set(last["results"]) != set(goals) or last["atlas_sha"] != atlas_id()[1]:
        last = run_pass(d, s, "with", goals, f"with-{len(s['passes'])}")
    for r in range(1, rounds + 1):
        failed = [g for g, res in last["results"].items() if not res["pass"]]
        if not failed:
            print("\nNothing fails with the current atlas; no lessons to learn.")
            return
        print(f"\n=== learning round {r}: {len(failed)} failed goal(s): {' '.join(failed)}")
        round_rec = {"round": r, "from_pass": last["name"], "atlas_before": atlas_id()[0], "proposals": []}
        for g in failed:
            res = last["results"][g]
            out, record = learn.propose(HERE.parent / res["run_dir"], g, {"pass": False, "details": res["details"]})
            print("\n" + learn.show(record))
            accepted = ask_accept(record, yes)
            learn.move(out.name, "accepted" if accepted else "rejected")
            round_rec["proposals"].append({"goal": g, "file": f"{'accepted' if accepted else 'rejected'}/{out.name}",
                                           "accepted": accepted, "diagnosis": record["diagnosis"],
                                           "proposed_by": record["proposed_by"]})
        print("\n" + "\n".join(merge()))
        round_rec["atlas_after"] = atlas_id()[0]
        s["rounds"].append(round_rec)
        save(d, s)
        if not any(p["accepted"] for p in round_rec["proposals"]):
            print("No lesson accepted; stopping.")
            return
        last = run_pass(d, s, "with", goals, f"learned-{r}")


def reset_learning():
    acc = sorted((LEARNED / "accepted").glob("*.json"))
    if acc:
        dest = LEARNED / "archive" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        dest.mkdir(parents=True)
        for f in acc:
            shutil.move(str(f), dest / f.name)
        print(f"set aside {len(acc)} accepted lesson file(s) in {dest.relative_to(HERE)}")
    print("\n".join(merge()))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["all", "run", "learn", "reset", "report"])
    ap.add_argument("condition", nargs="?", choices=["with", "without"])
    ap.add_argument("--goals", nargs="*", default=DEMO_GOALS)
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    if a.cmd == "reset":
        reset_learning()
    elif a.cmd == "run":
        if not a.condition:
            ap.error("run needs with or without")
        d, s = latest_session()
        run_pass(d, s, a.condition, a.goals, f"{a.condition}-{len(s['passes'])}")
    elif a.cmd == "learn":
        d, s = latest_session()
        learn_rounds(d, s, a.goals, a.rounds, a.yes)
    elif a.cmd == "all":
        reset_learning()
        d, s = new_session()
        s["goals"] = {g: check.GOALS[g][2] for g in a.goals}
        run_pass(d, s, "without", a.goals, "without")
        run_pass(d, s, "with", a.goals, "with")
        learn_rounds(d, s, a.goals, a.rounds, a.yes)
    if a.cmd in ("all", "report"):
        subprocess.run([sys.executable, str(TOOLS / "report.py")], check=True)


if __name__ == "__main__":
    main()

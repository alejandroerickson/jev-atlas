"""Run every goal n times through jev-atlas/run.sh, resetting the tenant before each
run and checking the outcome after it. Results go to results/<condition>.jsonl, one
line per run. Runs (run.json, steps, frames) go under runs/<condition>/, inside this
folder, so the goal text stays out of the shared jev-atlas/runs tree.

    python baseline.py --n 3                     # all goals, without the atlas
    python baseline.py --n 3 --goals G2 G6       # some
    python baseline.py --n 3 --set expert        # the expert goals E1..E12 (goals-expert.md)
    python baseline.py --n 3 --condition with    # once the atlas exists
    python baseline.py --n 5 --label without-h2  # keep results/runs distinct from an earlier harness's

Use a Python that has websockets (the harness copy's, or this repo's .venv). Then:
    python summarize.py [label]                          # the per-goal table (label defaults to "without")
    python3 ../tools/summarize_runs.py --runs runs/<label>   # per-step tables (ADIT's own copy; stdlib only)
"""
import argparse
import json
import os
import subprocess
import time
from pathlib import Path

import check

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def newest_run(d: Path, before: set):
    new = [p for p in d.glob("*/") if p.name not in before and (p / "run.json").exists()]
    return max(new, key=lambda p: p.name) if new else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--goals", nargs="*", default=None)
    ap.add_argument("--set", default="original", choices=["original", "expert"],
                    help="which goal set --goals defaults to: the original G1..G8, or the expert E1..E12")
    ap.add_argument("--condition", default="without", choices=["with", "without"])
    ap.add_argument("--label", default=None,
                    help="results/runs filename to use instead of --condition, so a later harness's "
                         "results (e.g. 'without-h2') land beside the old ones instead of overwriting them")
    ap.add_argument("--timeout", type=int, default=600)
    a = ap.parse_args()
    label = a.label or a.condition
    if a.goals is None:
        a.goals = check.EXPERT if a.set == "expert" else [g for g in check.GOALS if g.startswith("G")]

    runs = HERE / "runs"
    run_root = runs / label
    cond_dir = run_root / a.condition
    cond_dir.mkdir(parents=True, exist_ok=True)
    (HERE / "results").mkdir(exist_ok=True)
    logs = runs / "logs"
    logs.mkdir(exist_ok=True)
    out = HERE / "results" / f"{label}.jsonl"
    env = {**os.environ, "ADIT_RUN_DIR": str(run_root)}

    for rep in range(a.n):
        for g in a.goals:
            slug, split, text = check.GOALS[g]
            check.reset()
            before = {p.name for p in cond_dir.glob("*/")}
            t0 = time.time()
            log = logs / f"{time.strftime('%Y%m%d-%H%M%S')}-{g}-{label}.log"
            try:
                with open(log, "w") as fh:
                    rc = subprocess.run([str(REPO / "jev-atlas" / "run.sh"), a.condition, text], env=env,
                                        stdout=fh, stderr=subprocess.STDOUT, timeout=a.timeout).returncode
            except subprocess.TimeoutExpired:
                rc = "timeout"
            wall = round(time.time() - t0, 1)
            time.sleep(1)
            res = check.check(g)
            d = newest_run(cond_dir, before)
            run = json.loads((d / "run.json").read_text()) if d else {}
            row = {"goal": g, "slug": slug, "split": split, "rep": rep, "condition": a.condition, "label": label,
                   "pass": res["pass"], "details": res["details"], "harness_status": run.get("status"),
                   "steps": run.get("step_count"), "model": run.get("model"), "wall_s": wall, "rc": rc,
                   "run_dir": str(d.relative_to(REPO)) if d else None, "log": str(log.relative_to(REPO))}
            with open(out, "a") as fh:
                fh.write(json.dumps(row) + "\n")
            print(f"{g} rep{rep} pass={res['pass']} status={run.get('status')} steps={run.get('step_count')} "
                  f"model={run.get('model')} {wall}s", flush=True)
    check.reset()


if __name__ == "__main__":
    main()

"""Print a short table per run directory under an ADIT runs tree.

A runs tree holds one directory per condition (`with`, `without`), each holding
one directory per run, as the harness writes them under JEV_RUN_DIR (run.json plus
steps.jsonl). It knows nothing about any particular application.

    python3 jev-atlas/tools/summarize_runs.py                          # jev-atlas/runs
    python3 jev-atlas/tools/summarize_runs.py with                     # one condition
    python3 jev-atlas/tools/summarize_runs.py --runs jev-atlas/goals/runs/without
    python3 jev-atlas/tools/summarize_runs.py --json out.json

With no --runs the tree is RUN_DIR from jev-atlas/adit.env (ADIT_RUN_DIR wins).
Standard library only.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHIM = HERE.parent
REPO = SHIM.parent


def default_root() -> Path:
    """ADIT_RUN_DIR, else RUN_DIR as jev-atlas/adit.env sets it, resolved against the repo root."""
    import os
    raw = os.environ.get("ADIT_RUN_DIR")
    if not raw:
        conf = SHIM / "adit.env"
        m = re.search(r'^\s*RUN_DIR\s*=\s*"?([^"\n#]+?)"?\s*$', conf.read_text(), re.M)
        if not m:
            sys.exit(f"{conf} sets no RUN_DIR")
        raw = m.group(1)
    p = Path(raw)
    return p if p.is_absolute() else REPO / p


def load_run(d: Path):
    run = json.loads((d / "run.json").read_text())
    steps = []
    p = d / "steps.jsonl"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.strip():
                steps.append(json.loads(line))
    return run, steps


def op_probs(step):
    resp = step.get("response") or {}
    ch = resp.get("choices") or {}
    op = ch.get("operation") or {}
    return op.get("probabilities") or step.get("probabilities") or {}


def summarize(d: Path):
    run, steps = load_run(d)
    rows = []
    for s in steps:
        probs = op_probs(s)
        top = sorted(probs.items(), key=lambda kv: -kv[1])[:2] if isinstance(probs, dict) else []
        st = s.get("state") or {}
        page = st.get("page") or {}
        t = s.get("timings_ms") or {}
        rows.append({
            "step": s.get("step"),
            "page": (s.get("title") or "")[:28],
            "dialog": (page.get("dialog") or "")[:22],
            "n_el": len(st.get("elements") or []),
            "op": s.get("operation"),
            "target": (s.get("target_label") or "")[:40],
            "typed": (s.get("text") or "")[:18],
            "top": " ".join(f"{k}:{v:.2f}" for k, v in top),
            "changed": s.get("page_changed"),
            "ms": sum(v for v in t.values() if isinstance(v, (int, float))),
        })
    return run, rows


def main(argv):
    want_json = "--json" in argv
    out_path = argv[argv.index("--json") + 1] if want_json else None
    if "--runs" in argv:
        root = Path(argv[argv.index("--runs") + 1]).resolve()
    else:
        root = default_root()
    if not root.is_dir():
        sys.exit(f"No runs tree at {root}")
    conds = [a for a in argv if a in ("with", "without")] or ["without", "with"]
    everything = []
    for cond in conds:
        if not (root / cond).is_dir():
            continue
        for d in sorted((root / cond).glob("*/")):
            if not (d / "run.json").exists():
                continue
            run, rows = summarize(d)
            everything.append({"condition": cond, "dir": d.name, "run": run, "steps": rows})
            print(f"\n== {cond}  {d.name}")
            print(f"   status={run.get('status')} steps={run.get('step_count')} model={run.get('model')} "
                  f"wall={run.get('wall_ms')} ms atlas={'yes' if run.get('atlas') else 'no'}")
            print(f"   {'st':>2} {'page':<28} {'dialog':<22} {'el':>3} {'op':<9} {'target':<40} {'typed':<18} {'top probabilities':<28} chg {'ms':>6}")
            for r in rows:
                print(f"   {r['step']:>2} {r['page']:<28} {r['dialog']:<22} {r['n_el']:>3} {str(r['op']):<9} {r['target']:<40} "
                      f"{r['typed']:<18} {r['top']:<28} {str(r['changed'])[:1]:>3} {r['ms']:>6}")
    if want_json:
        Path(out_path).write_text(json.dumps(everything, indent=1))
        print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main(sys.argv[1:])

"""Per-goal table of results/<label>.jsonl (written by baseline.py; label defaults to
the condition, e.g. "without", unless baseline.py was given --label).

    python summarize.py [without|with|without-h2|...]
"""
import collections
import json
import sys
from pathlib import Path

cond = sys.argv[1] if len(sys.argv) > 1 else "without"
allrows = [json.loads(l) for l in (Path(__file__).resolve().parent / "results" / f"{cond}.jsonl").read_text().splitlines() if l.strip()]
# A run that never got a model answer (connection failure, crash before step 1) is
# infrastructure, not a Jev outcome: listed, not counted.
infra = [r for r in allrows if r.get("harness_status") == "error" and not r.get("model")]
rows = [r for r in allrows if r not in infra]
by = collections.defaultdict(list)
for r in rows:
    by[r["goal"]].append(r)
models = sorted({r["model"] for r in rows if r.get("model")})
print(f"condition={cond}  runs={len(rows)}  models={models}")
print(f"{'goal':<4} {'slug':<18} {'split':<9} {'pass':>5} {'harness status':<32} {'steps':<12} side effects (first run that had any)")
for g in sorted(by):
    rs = by[g]
    st = collections.Counter(r["harness_status"] for r in rs)
    se = next((r["details"].get("side_effects") for r in rs if r["details"].get("side_effects")), [])
    print(f"{g:<4} {rs[0]['slug']:<18} {rs[0]['split']:<9} {sum(r['pass'] for r in rs)}/{len(rs):<3} "
          f"{', '.join(f'{k}x{v}' for k, v in st.items()):<32} {','.join(str(r['steps']) for r in rs):<12} {se[:3]}")
print(f"total pass {sum(r['pass'] for r in rows)}/{len(rows)}")
for r in infra:
    print(f"not counted (no model answer): {r['goal']} rep{r['rep']} log {r['log']}")

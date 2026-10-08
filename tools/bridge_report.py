"""Bridge experiment (oc/bridge.py): net use of unheard speech and use of audible speech, per model and swap.

Scores runs/<run>/<model>/responses.jsonl with the frozen Study 2 scorer, then reports, per model and
swap, inaccessible net use D and accessible target use, with 95% skeleton-bootstrap intervals for
the difference from the unmodified Study 2 prompt (paired within skeletons).
Usage: python3 tools/bridge_report.py runs/<run> [plan.jsonl items.json]
"""
from __future__ import annotations

import json
import random
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
SWAPS = ("base", "sys", "card", "schema", "ask", "all")


def main():
    run = Path(sys.argv[1])
    plan_path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "items/access-v2/bridge.jsonl"
    items_path = Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / "items/access-v2/discovery-items.json"
    plan = {json.loads(l)["prompt_id"]: json.loads(l)["bridge"] for l in plan_path.read_text().splitlines()}
    res = {}
    for d in sorted(p for p in run.iterdir() if (p / "responses.jsonl").exists()):
        out = d / "v2scored.jsonl"
        if not out.exists():
            subprocess.run([sys.executable, str(ROOT / "tools/score_access_v2.py"), "--plan", str(plan_path),
                            "--items", str(items_path), "--responses", str(d / "responses.jsonl"),
                            "--model", d.name, "--out", str(out)], check=True)
        rows = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
        by = defaultdict(lambda: defaultdict(list))  # (swap, accessible) -> item -> values
        for r in rows:
            by[(plan[r["prompt_id"]], r["accessible"])][r["item"]].append(r["hit_t"] if r["accessible"] else r["D"])
        items = sorted({r["item"] for r in rows})
        rng = random.Random(20261006)
        draws = [[rng.choice(items) for _ in items] for _ in range(2000)]
        m = {}
        for sw in SWAPS:
            for acc in (False, True):
                v = {i: mean(by[(sw, acc)][i]) for i in items}
                b = {i: mean(by[("base", acc)][i]) for i in items}
                diff = sorted(mean(v[i] - b[i] for i in take) for take in draws)
                m[f"{sw}:{'accessible' if acc else 'inaccessible'}"] = {"estimate": mean(v.values()), "delta_vs_base": mean(v[i] - b[i] for i in items),
                                                                          "delta_ci95": [diff[49], diff[1949]]}
        res[d.name] = m
        print(d.name)
        for sw in SWAPS:
            a, b = m[f"{sw}:inaccessible"], m[f"{sw}:accessible"]
            print(f"  {sw:<7} unheard D {100 * a['estimate']:5.1f} (delta {100 * a['delta_vs_base']:+5.1f} [{100 * a['delta_ci95'][0]:+.1f}, "
                  f"{100 * a['delta_ci95'][1]:+.1f}])   audible use {100 * b['estimate']:5.1f}")
    (run / "bridge.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

"""Hosted single-feature swaps (added 10/8): unheard net use per bridge swap for hosted models.

Takes the hosted replies whose prompt ids are in the bridge plan, scores them with the frozen Study 2
scorer, and reports net use D per swap with a 95% skeleton-bootstrap interval for the difference from
the unmodified Study 2 prompt (paired within skeletons).
Usage: python3 tools/hosted_swap_report.py runs/hosted-1008 sonnet55 gemini31pro
"""
from __future__ import annotations

import json
import random
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
SWAPS = ("base", "sys", "card", "schema", "ask", "all")


def main():
    run, models = Path(sys.argv[1]), sys.argv[2:]
    plan = {json.loads(l)["prompt_id"]: json.loads(l) for l in (ROOT / "items/access-v2/bridge.jsonl").read_text().splitlines()}
    res = {}
    for m in models:
        reps = [json.loads(l) for l in (run / m / "responses.jsonl").read_text().splitlines()]
        best = {}
        for r in reps:  # one reply per prompt, preferring a complete one
            if r["prompt_id"] in plan and (r["prompt_id"] not in best or r["status"] == "complete" or best[r["prompt_id"]]["status"] != "complete"):
                best[r["prompt_id"]] = r
        reps = list(best.values())
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "r.jsonl").write_text("".join(json.dumps(dict(r, model=m)) + "\n" for r in reps))
            (td / "p.jsonl").write_text("".join(json.dumps(plan[r["prompt_id"]], ensure_ascii=False) + "\n" for r in reps))
            subprocess.run([sys.executable, str(ROOT / "tools/score_access_v2.py"), "--plan", str(td / "p.jsonl"), "--items",
                            str(ROOT / "items/access-v2/discovery-items.json"), "--responses", str(td / "r.jsonl"), "--model", m,
                            "--out", str(td / "s.jsonl")], check=True, capture_output=True)
            rows = [json.loads(l) for l in (td / "s.jsonl").read_text().splitlines()]
        by = defaultdict(lambda: defaultdict(list))
        for r in rows:
            if not r["accessible"]:
                by[plan[r["prompt_id"]]["bridge"]][r["item"]].append(r["D"])
        items = sorted(by["base"])
        rng = random.Random(20261008)
        draws = [[rng.choice(items) for _ in items] for _ in range(2000)]
        out = {}
        for sw in SWAPS:
            if not by[sw]:
                continue
            v = {i: mean(by[sw][i]) for i in items}
            b = {i: mean(by["base"][i]) for i in items}
            d = sorted(mean(v[i] - b[i] for i in t) for t in draws)
            out[sw] = {"estimate": mean(v.values()), "n": sum(len(x) for x in by[sw].values()), "delta_vs_base": mean(v[i] - b[i] for i in items),
                       "delta_ci95": [d[49], d[1949]]}
            print(f"{m:<12} {sw:<7} D {100 * out[sw]['estimate']:5.1f}  delta {100 * out[sw]['delta_vs_base']:+5.1f} "
                  f"[{100 * d[49]:+.1f}, {100 * d[1949]:+.1f}]  n={out[sw]['n']}")
        res[m] = out
    (ROOT / "analysis/results/added-1006/hosted_swaps.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

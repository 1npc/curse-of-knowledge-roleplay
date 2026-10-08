"""Sonnet 5.5 with high reasoning on the Study 1 repertoire cell (added 10/8), against its low-effort run.

Scores runs/hosted-1008/sonnet55-high with the frozen Study 1 scorer and compares net use and hit modes with
the low-effort replies to the same prompts (paired by item, 2,000 skeleton-bootstrap draws).
Usage: python3 tools/hosted_reasoning_report.py
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
PLAN = ROOT / "items/hosted/reasoning_repertoire.jsonl"


def main():
    out_dir = ROOT / "runs/hosted-1008-reasoning"
    ids = {json.loads(l)["prompt_id"] for l in PLAN.read_text().splitlines()}
    for key, src in (("sonnet55-high", "sonnet55-high"), ("sonnet55-low", "sonnet55")):
        best = {}
        for l in (ROOT / "runs/hosted-1008" / src / "responses.jsonl").read_text().splitlines():
            r = json.loads(l)
            if r["prompt_id"] in ids and (r["prompt_id"] not in best or r["status"] == "complete" or best[r["prompt_id"]]["status"] != "complete"):
                best[r["prompt_id"]] = dict(r, model=key)
        (out_dir / key).mkdir(parents=True, exist_ok=True)
        (out_dir / key / "responses.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in best.values()))
    subprocess.run([sys.executable, str(ROOT / "tools/score_run.py"), str(out_dir), str(PLAN), str(ROOT / "items/main/skeletons.json"),
                    str(ROOT / "items/real/skeletons.json"), "--quiet"], check=True, capture_output=True)
    by, res = {}, {}
    for key in ("sonnet55-low", "sonnet55-high"):
        rows = [json.loads(l) for l in (out_dir / key / "scored.jsonl").read_text().splitlines() if l.strip()]
        d = defaultdict(list)
        for r in rows:
            d[r["item"]].append(r["score"]["hit_t"] - r["score"]["hit_f"])
        by[key] = {i: mean(v) for i, v in d.items()}
        hits = [r for r in rows if r["score"]["hit_t"]]
        res[key] = {"net": mean(by[key].values()), "n": len(rows),
                    "modes": {k: sum(r["score"]["mode"] == k for r in hits) / len(hits) for k in ("unframed", "attributed", "tentative")} if hits else None}
    items = sorted(set(by["sonnet55-low"]) & set(by["sonnet55-high"]))
    rng = random.Random(20261008)
    draws = sorted(mean(by["sonnet55-high"][i] - by["sonnet55-low"][i] for i in (rng.choice(items) for _ in items)) for _ in range(2000))
    res["delta_high_minus_low"] = {"estimate": mean(by["sonnet55-high"][i] - by["sonnet55-low"][i] for i in items), "ci95": [draws[49], draws[1949]]}
    print(json.dumps(res, indent=1))
    (ROOT / "analysis/results/added-1006/hosted_reasoning.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

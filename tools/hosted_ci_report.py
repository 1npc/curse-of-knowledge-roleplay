"""Skeleton-bootstrap intervals for the hosted Study 1 cells, and a sensitivity check without filtered replies.

Reads runs/hosted-1008-s1/<model>/scored.jsonl (written by tools/hosted_report.py) and reports, per model and cell,
net use with a 95% interval from 2,000 draws over the 96 scene skeletons (all languages of a skeleton move together).
The sensitivity row drops prompts whose reply was withheld by the endpoint (status other than complete).
Usage: python3 tools/hosted_ci_report.py
"""
from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
MODELS = ["gpt6sol", "opus55", "sonnet55", "gemini31pro", "gemini38flash", "grok47", "deepseekv4pro"]
CELLS = {"repertoire": ("C-T-", "D0", "real"), "inaudible_flag": ("Einaud_S", "D0", "english"),
         "understood_flag": ("C-T-_flag", "D0", "real"), "prose": ("C-T-", "D1", "real")}


def boot(rows, draws=2000, seed=20261008):
    by = defaultdict(list)
    for r in rows:
        by[r["item"]].append(r["score"]["hit_t"] - r["score"]["hit_f"])
    sk = sorted(by)
    rng = random.Random(seed)
    est = mean(v for s in sk for v in by[s])
    bs = sorted(mean(v for s in (rng.choice(sk) for _ in sk) for v in by[s]) for _ in range(draws))
    return {"estimate": est, "ci95": [bs[int(0.025 * draws)], bs[int(0.975 * draws) - 1]], "n": sum(len(v) for v in by.values())}


def main():
    out = {}
    for m in MODELS:
        rows = [json.loads(l) for l in (ROOT / "runs/hosted-1008-s1" / m / "scored.jsonl").read_text().splitlines() if l.strip()]
        rows = [r for r in rows if r["arm"] == "main"]
        res = {}
        for k, (c, d, s) in CELLS.items():
            sel = [r for r in rows if r["cell"] == c and r["D"] == d and r["S"] == s]
            res[k] = boot(sel)
            ok = [r for r in sel if r["status"] == "complete"]
            if len(ok) < len(sel):
                res[k + "_complete_only"] = boot(ok)
        out[m] = res
        print(m, {k: f"{100 * v['estimate']:.1f} [{100 * v['ci95'][0]:.1f}, {100 * v['ci95'][1]:.1f}] n={v['n']}" for k, v in res.items()})
    (ROOT / "analysis/results/added-1006/hosted_ci.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

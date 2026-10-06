"""Sampling robustness (added 10/6): Study 1 leakage under temperature 0.7, top-p 0.95, three seeds, versus greedy.

Uses the same prompt ids (items/main/sampling_ids.txt) in runs/sampling-s{1,2,3}-1006 and runs/main-v1,
all scored with tools/score_run.py. Net use for C-T- D0 (repertoire) and E_inaud_S (inaudible flag),
target use for C+T- D0 version A (fluent control); content and planning questions; all three languages.
Usage: python3 tools/sampling_report.py runs/main-v1 runs/sampling-s1-1006 runs/sampling-s2-1006 runs/sampling-s3-1006
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
IDS = set((ROOT / "items/main/sampling_ids.txt").read_text().split())


def rates(path):
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r["prompt_id"] in IDS]
    out = {}
    for cell, kind in (("C-T-", "net"), ("Einaud_S", "net"), ("C+T-", "use")):
        rs = [r for r in rows if r["cell"] == cell]
        t = mean(r["score"]["hit_t"] for r in rs)
        out[cell] = t - mean(r["score"]["hit_f"] for r in rs) if kind == "net" else t
    return out, len(rows)


def main():
    greedy, samples = Path(sys.argv[1]), [Path(p) for p in sys.argv[2:]]
    models = sorted(d.name for d in samples[0].iterdir() if (d / "scored.jsonl").exists())
    res = {}
    for m in models:
        g, n = rates(greedy / m / "scored.jsonl")
        s = [rates(p / m / "scored.jsonl")[0] for p in samples]
        res[m] = {"greedy": g, "n": n, "samples": s,
                  "sample_mean": {c: mean(x[c] for x in s) for c in g}, "sample_range": {c: [min(x[c] for x in s), max(x[c] for x in s)] for c in g}}
        print(m, n, "  ".join(f"{c}: greedy {100 * g[c]:.1f}, sampled {100 * res[m]['sample_mean'][c]:.1f} "
                               f"[{100 * res[m]['sample_range'][c][0]:.1f}-{100 * res[m]['sample_range'][c][1]:.1f}]" for c in g))
    (samples[0].parent / "sampling-robustness.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

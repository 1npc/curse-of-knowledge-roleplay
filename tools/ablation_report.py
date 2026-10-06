"""Format ablation (oc/ablation.py): leakage per model and feature combination, and pooled feature effects.

Input: runs/<run>/<model>/scored.jsonl from tools/score_run.py with items/main/format_ablation.jsonl.
Net use (hit_t - hit_f) for the inaccessible cells, target use (hit_t) for the accessible controls.
A feature effect is the mean, over models and over the other two features' four combinations, of
level 1 minus level 0; intervals resample skeletons jointly across models (2,000 draws).
Writes <run>/ablation.json and prints a summary.
Usage: python3 tools/ablation_report.py runs/<run>
"""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

B, SEED = 2000, 20261006
CELLS = {"Einaud_S": "net", "C-T-_flag": "net", "Eaud_S": "use", "C+_flag": "use"}


def value(rows, kind):
    if not rows:
        return None
    t = mean(r["score"]["hit_t"] for r in rows)
    return t - mean(r["score"]["hit_f"] for r in rows) if kind == "net" else t


def main():
    run = Path(sys.argv[1])
    data = {}
    for d in sorted(p for p in run.iterdir() if (p / "scored.jsonl").exists()):
        data[d.name] = [json.loads(l) for l in (d / "scored.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    models = sorted(data)
    # index: model -> (label, question, context, cell) -> skeleton -> rows
    idx = {m: defaultdict(lambda: defaultdict(list)) for m in models}
    for m in models:
        for r in data[m]:
            l, q, c = (int(x) for x in r["arm"][5:].replace("q", " ").replace("c", " ").split())
            idx[m][(l, q, c, r["cell"])][r["item"]].append(r)
    skeletons = sorted({r["item"] for m in models for r in data[m]})

    sums = {m: {key: {s: (sum(r["score"]["hit_t"] for r in rs), sum(r["score"]["hit_f"] for r in rs), len(rs))
                      for s, rs in by.items()} for key, by in idx[m].items()} for m in models}

    def est(m, key, weights):  # weighted over skeletons, same as pooling the replicated rows
        t = f = n = 0
        for s, w in weights.items():
            v = sums[m].get(key, {}).get(s)
            if v:
                t += w * v[0]
                f += w * v[1]
                n += w * v[2]
        if not n:
            return None
        return (t - f) / n if CELLS[key[3]] == "net" else t / n

    def effects(weights):
        out = {}
        for cell in CELLS:
            for f in range(3):
                diffs = []
                for m in models:
                    for a in (0, 1):
                        for b in (0, 1):
                            lv = [None, None]
                            for level in (0, 1):
                                k = [a, b]
                                k.insert(f, level)
                                lv[level] = est(m, (k[0], k[1], k[2], cell), weights)
                            if None not in lv:
                                diffs.append(lv[1] - lv[0])
                out[f"{cell}:{('label', 'question', 'context')[f]}"] = mean(diffs) if diffs else None
            # the full Study 2-like combination against the Study 1 baseline
            d = [est(m, (1, 1, 1, cell), weights) - est(m, (0, 0, 0, cell), weights) for m in models]
            out[f"{cell}:all_three"] = mean(d)
        return out

    ones = {s: 1 for s in skeletons}
    point = effects(ones)
    rng = random.Random(SEED)
    draws = defaultdict(list)
    for _ in range(B):
        w = defaultdict(int)
        for _ in skeletons:
            w[rng.choice(skeletons)] += 1
        for k, v in effects(w).items():
            if v is not None:
                draws[k].append(v)
    eff = {}
    for k, v in point.items():
        ds = sorted(draws[k])
        eff[k] = {"point": v, "ci95": [ds[int(.025 * len(ds))], ds[int(.975 * len(ds)) - 1]]}
    cells = {m: {f"l{l}q{q}c{c}": {cell: est(m, (l, q, c, cell), ones) for cell in CELLS}
                 for l in (0, 1) for q in (0, 1) for c in (0, 1)} for m in models}
    out = {"models": models, "skeletons": len(skeletons), "cells": cells, "effects": eff}
    (run / "ablation.json").write_text(json.dumps(out, indent=1))
    for m in models:
        print(m)
        for combo, v in cells[m].items():
            print("  ", combo, "  ".join(f"{c}={100 * x:5.1f}" for c, x in v.items()))
    for k, v in eff.items():
        print(f"{k:<28} {100 * v['point']:6.1f} [{100 * v['ci95'][0]:.1f}, {100 * v['ci95'][1]:.1f}]")


if __name__ == "__main__":
    main()

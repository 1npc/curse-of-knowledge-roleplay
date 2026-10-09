"""Added experiments (10/9): framing (narrator, author, perspective) and thinking, against the main run on the same prompts.

Scores runs/framing-1009 and runs/thinking-1009 with the frozen Study 1 scorer, then reports per model and condition the
net use for the language repertoire (C-T- D0) and the audibility flag (Einaud_S D0), and target use in the fluent control
(C+T- D0). The baseline is the main run's replies to the same prompt ids. Pooled differences from the baseline carry
95% intervals from 2,000 skeleton-bootstrap draws (all models and languages of a skeleton move together).
Usage: python3 tools/framing_thinking_report.py
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
CELLS = {"repertoire": ("C-T-", "D0"), "audibility": ("Einaud_S", "D0"), "control": ("C+T-", "D0")}
ITEMS = [str(ROOT / "items/main/skeletons.json"), str(ROOT / "items/real/skeletons.json")]
EXCLUDE = {"qwen35_9b"}  # thinking: 97% of replies hit the 6,144-token limit before an answer


def score(run, plan):
    subprocess.run([sys.executable, str(ROOT / "tools/score_run.py"), str(run), str(plan), *ITEMS, "--quiet"], check=True, capture_output=True)
    out = {}
    for d in sorted(p for p in run.iterdir() if (p / "scored.jsonl").exists()):
        out[d.name] = [json.loads(l) for l in (d / "scored.jsonl").read_text().splitlines() if l.strip()]
    return out


def values(rows, cell):
    c, dd = CELLS[cell]
    sel = [r for r in rows if r["cell"] == c and r["D"] == dd and r.get("arm") == "main"]
    if cell == "control":
        return {r["prompt_id"].split(".frame-")[0]: (r["item"], float(r["score"]["hit_t"])) for r in sel}
    return {r["prompt_id"].split(".frame-")[0]: (r["item"], float(r["score"]["hit_t"]) - float(r["score"]["hit_f"])) for r in sel}


def pooled_delta(pairs, draws=2000, seed=20261009):
    by = defaultdict(list)
    for sk, d in pairs:
        by[sk].append(d)
    sk = sorted(by)
    rng = random.Random(seed)
    bs = sorted(mean(v for s in (rng.choice(sk) for _ in sk) for v in by[s]) for _ in range(draws))
    return {"estimate": mean(v for s in sk for v in by[s]), "ci95": [bs[int(0.025 * draws)], bs[int(0.975 * draws) - 1]]}


def main():
    base_ids = {json.loads(l)["prompt_id"] for l in (ROOT / "items/added-1009/core.jsonl").read_text().splitlines()}
    base = {}
    for m in (ROOT / "runs/main-v1").iterdir():
        f = m / "scored.jsonl"
        if f.exists():
            base[m.name] = [r for r in (json.loads(l) for l in f.read_text().splitlines() if l.strip()) if r["prompt_id"] in base_ids]
    res = {}
    fr_plan = ROOT / "items/added-1009/framing.jsonl"
    framing = score(ROOT / "runs/framing-1009", fr_plan) if (ROOT / "runs/framing-1009").exists() else {}
    long_dir = ROOT / "runs/thinking-1009-long"
    if long_dir.exists():  # merge reruns of truncated prompts (longer budget) before scoring
        for d in long_dir.iterdir():
            f = d / "responses.jsonl"
            if not f.exists():
                continue
            rerun = {json.loads(l)["prompt_id"]: l for l in f.read_text().splitlines() if l.strip()}
            first = (ROOT / "runs/thinking-1009" / d.name / "responses.jsonl")
            lines = [rerun.get(json.loads(l)["prompt_id"], l) for l in first.read_text().splitlines() if l.strip()]
            (ROOT / "runs/thinking-1009" / d.name / "responses.jsonl").write_text("\n".join(lines) + "\n")
    thinking = score(ROOT / "runs/thinking-1009", ROOT / "items/added-1009/core.jsonl") if (ROOT / "runs/thinking-1009").exists() else {}
    thinking = {m: rows for m, rows in thinking.items() if m not in EXCLUDE}
    for name, runs, split in (("framing", framing, True), ("thinking", thinking, False)):
        conds = ["narrator", "author", "perspective"] if split else ["thinking"]
        out = {"per_model": {}, "pooled": {}}
        pairs = defaultdict(list)
        for m, rows in runs.items():
            out["per_model"][m] = {}
            status = defaultdict(int)
            for r in rows:
                status[r.get("status", "?")] += 1
            out["per_model"][m]["status"] = dict(status)
            for cond in conds:
                sub = [r for r in rows if r.get("framing") == cond] if split else rows
                if split:
                    pl = {json.loads(l)["prompt_id"]: json.loads(l)["framing"] for l in fr_plan.read_text().splitlines()}
                    sub = [r for r in rows if pl.get(r["prompt_id"]) == cond]
                if not split:
                    trunc = [r for r in sub if r.get("status") != "complete"]
                    out["per_model"][m]["truncated"] = len(trunc)
                    sub = [r for r in sub if r.get("status") == "complete"]
                for cell in CELLS:
                    v, b = values(sub, cell), values(base.get(m, []), cell)
                    common = sorted(set(v) & set(b))
                    if not common:
                        continue
                    out["per_model"][m][f"{cond}:{cell}"] = {"value": mean(v[k][1] for k in common), "baseline": mean(b[k][1] for k in common), "n": len(common)}
                    pairs[(cond, cell)] += [(v[k][0], v[k][1] - b[k][1]) for k in common]
        for (cond, cell), pr in pairs.items():
            out["pooled"][f"{cond}:{cell}"] = pooled_delta(pr)
        res[name] = out
        for m, d in out["per_model"].items():
            print(name, m, d["status"], {k: f"{100 * x['value']:.1f} (base {100 * x['baseline']:.1f})" for k, x in d.items() if isinstance(x, dict) and "value" in x})
        for k, d in out["pooled"].items():
            print(name, "POOLED", k, f"{100 * d['estimate']:+.1f} [{100 * d['ci95'][0]:+.1f}, {100 * d['ci95'][1]:+.1f}]")
    (ROOT / "analysis/results/added-1009").mkdir(parents=True, exist_ok=True)
    (ROOT / "analysis/results/added-1009/framing_thinking.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

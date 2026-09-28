"""Score a finished generation run and print per-model, per-cell summaries (standard library only).

Joins <run>/<model>/responses.jsonl with the prompt plan on prompt_id, scores each reply with
oc.score.score_reply, and writes <run>/<model>/scored.jsonl plus <run>/summary.json.
Probes: the translation probe counts as recovered when both canaries are named (U2); the state
probe reads the first yes/no in the reply.
Usage: python3 tools/score_run.py runs/<run_id> items/pilot/prompts.jsonl items/pilot/skeletons.json
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from oc.gate import load_valueset  # noqa: E402
from oc.score import ItemContext, score_reply  # noqa: E402


def yes_no(text: str):
    m = re.search(r"\b(yes|no)\b", text or "", re.I)
    return m.group(1).lower() if m else None


def main():
    run, plan_path, items_path = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    plan = {}
    for line in plan_path.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        r.pop("messages", None)
        plan[r["prompt_id"]] = r
    items = {it["id"]: it for it in json.loads(items_path.read_text(encoding="utf-8"))["items"]}
    vs = load_valueset()
    ctxs = {}
    summary = {}
    for mdir in sorted(p for p in run.iterdir() if (p / "responses.jsonl").exists()):
        model = mdir.name
        rows = [json.loads(l) for l in (mdir / "responses.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        scored = []
        for r in rows:
            p = plan[r["prompt_id"]]
            key = (p["item"], p["lang"])
            if key not in ctxs:
                ctxs[key] = ItemContext(items[p["item"]], p["lang"], vs)
            cell = {"C": p["C"], "T": p["T"], "S": p["S"]}
            s = score_reply(r.get("text", ""), ctxs[key], p["version"], cell, r.get("finish_reason"))
            rec = {"prompt_id": r["prompt_id"], "model": model, "status": r["status"],
                   **{k: p[k] for k in ("item", "lang", "version", "arm", "S", "cell", "D", "Q", "C")},
                   "T": p["T"], "score": s, "text": r.get("text", "")}
            if p["arm"] == "probe_state":
                rec["probe_answer"] = yes_no(r.get("text", ""))
                rec["probe_expected"] = p.get("expected")
            scored.append(rec)
        (mdir / "scored.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in scored), encoding="utf-8")
        agg = defaultdict(lambda: defaultdict(float))
        for x in scored:
            if x["arm"] == "main":
                k = f"{x['S']}:{x['cell']}:{x['D']}"
            elif x["arm"] == "probe_translate":
                k = f"probe_translate:{x['S']}"
            else:
                k = f"probe_state:{x['cell']}:{x['D']}"
            a = agg[k]
            a["n"] += 1
            s = x["score"]
            for f in ("hit_t", "hit_f", "U2", "N_deny", "N_request", "A", "F", "L", "R", "LD_deny", "echo_only", "non_english"):
                a[f] += bool(s[f])
            a["truncated"] += x["status"] == "truncated"
            a["not_complete"] += x["status"] not in ("complete", "truncated")
            if x["arm"] == "probe_state":
                a["probe_correct"] += x["probe_answer"] == x["probe_expected"]
        table = {k: {f: (round(v / a["n"], 3) if f != "n" else int(v)) for f, v in a.items()} for k, a in sorted(agg.items())}
        status = defaultdict(int)
        for x in scored:
            status[x["status"]] += 1
        summary[model] = {"replies": len(scored), "status": dict(status), "cells": table}
        print(f"\n== {model}: {len(scored)} replies, status {dict(status)}")
        print(f"{'cell':<32}{'n':>4}{'hit_t':>7}{'hit_f':>7}{'U2':>6}{'deny':>6}{'req':>6}{'A':>6}{'L':>6}{'echo':>6}{'R':>6}{'trunc':>7}{'probe':>7}")
        for k, v in table.items():
            print(f"{k:<32}{v['n']:>4}{v['hit_t']:>7}{v['hit_f']:>7}{v['U2']:>6}{v['N_deny']:>6}{v['N_request']:>6}"
                  f"{v['A']:>6}{v['L']:>6}{v['echo_only']:>6}{v['R']:>6}{v['truncated']:>7}{v.get('probe_correct', ''):>7}")
    (run / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")


if __name__ == "__main__":
    main()

"""Score a finished generation run and print per-model, per-cell summaries (standard library only).

Joins <run>/<model>/responses.jsonl with the prompt plan on prompt_id, scores each reply with
oc.score.score_reply, and writes <run>/<model>/scored.jsonl plus <run>/summary.json.
Probes: the translation probe counts as recovered when both canaries are named (U2); the state
probe reads the first yes/no in the reply.
Usage: python3 tools/score_run.py runs/<run_id> items/pilot/prompts.jsonl items/pilot/skeletons.json
Combined main plans require both item files: <run> <plan_all.jsonl> <main/skeletons.json> <real/skeletons.json>.
"""
from __future__ import annotations

import argparse
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


def load_inputs(plan_path, item_paths):
    """Validate the full join before writing any score output."""
    plan = {}
    for line in plan_path.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        r.pop("messages", None)
        if r["prompt_id"] in plan:
            raise ValueError("duplicate prompt ID in plan")
        plan[r["prompt_id"]] = r
    items = {}
    for path in item_paths:
        for it in json.loads(path.read_text(encoding="utf-8"))["items"]:
            if it["id"] in items:
                raise ValueError("duplicate item ID across item sources")
            items[it["id"]] = it
    missing = {p["item"] for p in plan.values()} - items.keys()
    if missing:
        raise ValueError(f"plan references {len(missing)} items absent from the supplied item files")
    return plan, items


def summary_key(x):
    if x["arm"] in ("M1", "M1g", "FS"):
        return f"{x['arm']}{'' if x['arm'] == 'FS' else '-step' + str(x['step'])}:{x['cell']}:{x['version']}"
    if x["arm"] == "main":
        key = f"{x['S']}:{x['cell']}:{x['D']}"
        # Keep pilot/main keys stable; separate the non-Cyberpunk comparison arm.
        return f"real_world:{key}" if x.get("world") == "real" else key
    if x["arm"] == "probe_translate":
        key = f"probe_translate:{x['S']}"
    else:
        key = f"{x['arm']}:{x['cell']}:{x['D']}"
    return f"real_world:{key}" if x.get("world") == "real" else key


def account_for_skipped_steps(rows, model_dir, plan):
    """Materialize only documented missing second steps, preserving the planned denominator."""
    skipped = model_dir / "chunks" / "s2-skipped.json"
    if not skipped.exists():
        return rows
    by_id = {r["prompt_id"]: r for r in rows}
    for pid in json.loads(skipped.read_text())["step1_not_usable"]:
        if pid not in plan or not plan[pid].get("next_step"):
            raise ValueError("skip references no planned second step")
        if pid not in by_id or by_id[pid]["status"] in ("complete", "truncated") or pid + "#2" in by_id:
            raise ValueError("skip does not match an unusable first step and missing second step")
        rows.append({"prompt_id": pid + "#2", "status": "upstream_failure", "text": "",
                     "finish_reason": None, "synthetic_missing": True})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run", type=Path)
    ap.add_argument("plan", type=Path)
    ap.add_argument("items", type=Path, nargs="+")
    ap.add_argument("--models", nargs="+", help="limit scoring to named models; safe for parallel processes")
    ap.add_argument("--quiet", action="store_true", help="print counts only, not outcome summaries")
    a = ap.parse_args()
    run = a.run
    plan, items = load_inputs(a.plan, a.items)
    vs = load_valueset()
    ctxs = {}
    summary = {}
    for mdir in sorted(p for p in run.iterdir() if (p / "responses.jsonl").exists()):
        model = mdir.name
        if a.models and model not in a.models:
            continue
        rows = [json.loads(l) for l in (mdir / "responses.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        rows = account_for_skipped_steps(rows, mdir, plan)
        scored = []
        for r in rows:
            base_id, _, step = r["prompt_id"].partition("#")  # "#2" marks the second step of a two-step arm (M1)
            p = plan[base_id]
            key = (p["item"], p["lang"])
            if key not in ctxs:
                ctxs[key] = ItemContext(items[p["item"]], p["lang"], vs)
            cell = {"C": p["C"], "T": p["T"], "S": p["S"]}
            s = score_reply(r.get("text", ""), ctxs[key], p["version"], cell, r.get("finish_reason"))
            rec = {"prompt_id": r["prompt_id"], "model": model, "status": r["status"], "step": int(step or 1),
                   **{k: p[k] for k in ("item", "lang", "version", "arm", "S", "cell", "D", "Q", "C")},
                   **{k: p[k] for k in ("set", "world", "mode", "character", "canon_id", "group") if k in p},
                   "synthetic_missing": r.get("synthetic_missing", False),
                   "T": p["T"], "score": s, "text": r.get("text", "")}
            if p["arm"] == "probe_state":
                rec["probe_answer"] = yes_no(r.get("text", ""))
                rec["probe_expected"] = p.get("expected")
            scored.append(rec)
        scored.sort(key=lambda r: r["prompt_id"])
        tmp = mdir / "scored.jsonl.tmp"
        with tmp.open("w", encoding="utf-8") as handle:
            for row in scored:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        tmp.replace(mdir / "scored.jsonl")
        agg = defaultdict(lambda: defaultdict(float))
        for x in scored:
            k = summary_key(x)
            ag = agg[k]
            ag["n"] += 1
            s = x["score"]
            for f in ("hit_t", "hit_f", "U2", "N_deny", "N_request", "A", "F", "L", "R", "LD_deny", "echo_only", "non_english"):
                ag[f] += bool(s[f])
            ag["truncated"] += x["status"] == "truncated"
            ag["not_complete"] += x["status"] not in ("complete", "truncated")
            if x["arm"] == "probe_state":
                ag["probe_correct"] += x["probe_answer"] == x["probe_expected"]
        table = {k: {f: (round(v / a["n"], 3) if f != "n" else int(v)) for f, v in a.items()} for k, a in sorted(agg.items())}
        status = defaultdict(int)
        for x in scored:
            status[x["status"]] += 1
        summary[model] = {"replies": len(scored), "status": dict(status), "cells": table}
        (mdir / "score-summary.json").write_text(json.dumps(summary[model], indent=1) + "\n")
        print(f"\n== {model}: {len(scored)} replies, status {dict(status)}")
        if a.quiet:
            continue
        print(f"{'cell':<32}{'n':>4}{'hit_t':>7}{'hit_f':>7}{'U2':>6}{'deny':>6}{'req':>6}{'A':>6}{'L':>6}{'echo':>6}{'R':>6}{'trunc':>7}{'probe':>7}")
        for k, v in table.items():
            print(f"{k:<32}{v['n']:>4}{v['hit_t']:>7}{v['hit_f']:>7}{v['U2']:>6}{v['N_deny']:>6}{v['N_request']:>6}"
                  f"{v['A']:>6}{v['L']:>6}{v['echo_only']:>6}{v['R']:>6}{v['truncated']:>7}{v.get('probe_correct', ''):>7}")
    if not a.models:
        (run / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")


if __name__ == "__main__":
    main()

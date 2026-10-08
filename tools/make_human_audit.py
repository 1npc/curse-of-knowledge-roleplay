"""Blind human audit of the content scorer (prepared 10/8; standard library only).

Draws 150 replies from both studies, stratified by condition and by the scorer's target decision,
and writes:
  deliverables/human-audit-20261008/audit-sheet.csv    what annotators see and fill in (UTF-8 with BOM)
  deliverables/human-audit-20261008/instructions.md    labeling instructions (zh and en)
  analysis/human-audit/key.jsonl                       organizer key: source, condition, scorer labels,
                                                       candidate order, stratum sizes (never shown)
Annotators see the reply and two candidate facts in random order; not the model, condition, version
or scorer output. Within each stratum, half the items are scorer target hits and half are not, so
both misses and false hits can be estimated; analysis reweights by stratum size.
Usage: python3 tools/make_human_audit.py
"""
from __future__ import annotations

import csv
import glob
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = 20261008
MODELS = ["falcon_h1_34b", "gemma4_12b", "gemma4_31b", "glm47_flash", "gpt_oss_20b", "mistral_small3", "nemotron3_nano30b",
          "phi4", "qwen35_9b", "qwen38_27b", "seed_oss_36b"]
OUT = ROOT / "deliverables/human-audit-20261008"
KEY = ROOT / "analysis/human-audit/key.jsonl"
PLAN = {  # stratum -> number of items (half scorer hits, half not)
    "S1 language, repertoire only": 30, "S1 not audible, flag only": 20, "S1 language, prose sentence": 10,
    "S1 M1g answer": 14, "S1 control, fluent": 14,
    "S2 full context, inaccessible": 40, "S2 character view, inaccessible": 12, "S2 full context, accessible": 10,
}


def s1_stratum(r):
    if r.get("set") != "main" or r["Q"] not in ("content", "task", "check", "plan"):
        return None
    if r["arm"] == "main" and r["D"] == "D0" and r["cell"] == "C-T-" and r["S"] == "real":
        return "S1 language, repertoire only"
    if r["arm"] == "main" and r["D"] == "D0" and r["cell"] == "Einaud_S":
        return "S1 not audible, flag only"
    if r["arm"] == "main" and r["D"] == "D1" and r["cell"] == "C-T-" and r["S"] == "real":
        return "S1 language, prose sentence"
    if r["arm"] == "M1g" and r.get("step") == 2 and r["cell"] in ("C-T-", "Einaud_S"):
        return "S1 M1g answer"
    if r["arm"] == "main" and r["D"] == "D0" and r["cell"] == "C+T-" and r["S"] == "real" and r["version"] == "A":
        return "S1 control, fluent"
    return None


def s2_stratum(r):
    if r["set"] != "confirmatory" or r["Q"] not in ("content", "plan") or r["representation"] != "R2" or r["delay"] != 0:
        return None
    if r["method"] == "full":
        return "S2 full context, accessible" if r["accessible"] else "S2 full context, inaccessible"
    if r["method"] == "view" and not r["accessible"]:
        return "S2 character view, inaccessible"
    return None


def main():
    rng = random.Random(SEED)
    s1_items = {it["id"]: it for it in json.loads((ROOT / "items/main/skeletons.json").read_text())["items"]}
    s2_items = {it["id"]: it for it in json.loads((ROOT / "items/access-v2/confirmatory-items.json").read_text())["items"]}
    pools = defaultdict(lambda: defaultdict(list))  # stratum -> scorer target hit -> candidates
    for m in MODELS:
        for line in open(ROOT / f"runs/main-v1/{m}/scored.jsonl", encoding="utf-8"):
            r = json.loads(line)
            st = s1_stratum(r)
            if st and r["status"] == "complete" and r.get("text"):
                v = s1_items[r["item"]]["langs"][r["lang"]]
                other = "B" if r["version"] == "A" else "A"
                pools[st][int(bool(r["score"]["hit_t"]))].append({
                    "study": 1, "model": m, "prompt_id": r["prompt_id"], "text": r["text"],
                    "target": (v[r["version"]]["PLACE"], v[r["version"]]["OBJECT"]), "foil": (v[other]["PLACE"], v[other]["OBJECT"]),
                    "scorer_target": int(bool(r["score"]["hit_t"])), "scorer_foil": int(bool(r["score"]["hit_f"]))})
    s2_files = {m: f"runs/v2conf-ext-1006/{m}/v2scored.jsonl" for m in MODELS}
    s2_files["gemma4_31b"] = "analysis/h200-v2-20261002/gemma4_31b/scores/confirmatory/gemma4_31b.jsonl"
    for m in ("glm47_flash", "nemotron3_nano30b", "qwen35_9b"):
        s2_files[m] = f"analysis/h200-v2-20261002/core-rest/scores/confirmatory/{m}.jsonl"
    texts = {}
    for p in glob.glob(str(ROOT / "runs/v2conf-ext-1006/*/responses.jsonl")) + glob.glob(str(ROOT / "analysis/h200-v2-20261002/*/responses/confirmatory/*/responses.jsonl")):
        m = Path(p).parent.name
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            texts[(m, r["prompt_id"])] = r.get("text")
    for m, f in s2_files.items():
        for line in open(ROOT / f, encoding="utf-8"):
            r = json.loads(line)
            st = s2_stratum(r)
            t = texts.get((m, r["prompt_id"]))
            if st and r.get("valid", True) and t:
                v = s2_items[r["item"]]["langs"][r["lang"]]
                other = "B" if r["version"] == "A" else "A"
                pools[st][int(bool(r["hit_t"]))].append({
                    "study": 2, "model": m, "prompt_id": r["prompt_id"], "text": t,
                    "target": (v[r["version"]]["PLACE"], v[r["version"]]["OBJECT"]), "foil": (v[other]["PLACE"], v[other]["OBJECT"]),
                    "scorer_target": int(bool(r["hit_t"])), "scorer_foil": int(bool(r["hit_f"]))})
    rows, keys = [], []
    for st, n in PLAN.items():
        for hit in (1, 0):
            pool = pools[st][hit]
            k = min(n // 2 + (n % 2 if hit else 0), len(pool))
            for c in rng.sample(pool, k):
                bid = "H-" + hashlib.sha256(f"{SEED}{c['model']}{c['prompt_id']}".encode()).hexdigest()[:10]
                order = [c["target"], c["foil"]]
                target_pos = rng.choice((1, 2))
                if target_pos == 2:
                    order.reverse()
                rows.append({"id": bid, "reply": " ".join(c["text"].split()),
                             "fact_1": f"{order[0][1]} / {order[0][0]}", "fact_2": f"{order[1][1]} / {order[1][0]}",
                             "f1_object": "", "f1_place": "", "f2_object": "", "f2_place": "", "unsure": "", "note": ""})
                keys.append({"id": bid, "stratum": st, "scorer_target": c["scorer_target"], "scorer_foil": c["scorer_foil"],
                             "target_position": target_pos, "study": c["study"], "model": c["model"], "prompt_id": c["prompt_id"],
                             "stratum_hit_population": len(pool), "stratum_hit_sample": k, "stratum_population": len(pools[st][0]) + len(pools[st][1])})
    order = list(range(len(rows)))
    rng.shuffle(order)
    rows, keys = [rows[i] for i in order], [keys[i] for i in order]
    OUT.mkdir(parents=True, exist_ok=True)
    KEY.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT / "audit-sheet.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    KEY.write_text("".join(json.dumps(k, ensure_ascii=False) + "\n" for k in keys), encoding="utf-8")
    print(len(rows), "items;", {st: sum(k["stratum"] == st for k in keys) for st in PLAN})


if __name__ == "__main__":
    main()

"""Latin-square assignment of canary values to the main-set slots (proposal 5.4 rotation rule).

384 slots per type (64 skeletons x 3 languages x A/B). For skeleton s, language l and version v the
value index is (b_s + 4l + c_s * v) mod 12 over a permuted value list, so the six slots of a
skeleton always get six different values and the partner offset c_s varies by skeleton. A seeded
random search over permutations, base sequence and offsets keeps the hard constraint (no
confusable A/B pair in a language) and minimizes imbalance across language, A/B role, dialogue
mode, character, partner pairs and PLACE-OBJECT co-occurrence.
Usage: python3 tools/assign_values.py [--iterations 20000]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ("zh", "ja", "es")
OFFSETS = (1, 2, 3, 5, 6, 7, 9, 10, 11)  # c with {0, c, 4, 4+c, 8, 8+c} distinct mod 12


def build(rng, values, skeletons, conf, reorder=False):
    perm = values[:]
    rng.shuffle(perm)
    a = rng.choice((1, 5, 7, 11))
    e = rng.randrange(12)
    out = {}
    bcount, pairs = Counter(), Counter()
    # OBJECT walks the skeletons in a shuffled order, so its rotation is not locked to PLACE's
    pos = rng.sample(range(len(skeletons)), len(skeletons)) if reorder else list(range(len(skeletons)))
    for s in range(len(skeletons)):
        sk = skeletons[s]
        b = (a * pos[s] + e) % 12
        best = None
        for c in rng.sample(OFFSETS, len(OFFSETS)):  # greedy: balance B usage and partner pairs
            slots = {l: (perm[(b + 4 * li) % 12], perm[(b + 4 * li + c) % 12]) for li, l in enumerate(LANGS)}
            if any(frozenset(p) in conf[l] for l, p in slots.items()):
                continue
            cost = sum(bcount[(l, p[1])] for l, p in slots.items()) + 2 * sum(pairs[frozenset(p)] for p in slots.values())
            if best is None or cost < best[0]:
                best = (cost, slots)
        if best is None:
            return None
        for l, p in best[1].items():
            bcount[(l, p[1])] += 1
            pairs[frozenset(p)] += 1
        out[sk["id"]] = best[1]
    return out


def score(assign, skeletons, typ):
    by_id = {s["id"]: s for s in skeletons}
    lang, role, mode, char, pair = Counter(), Counter(), Counter(), Counter(), Counter()
    for sid, slots in assign.items():
        for l, (va, vb) in slots.items():
            for v, r in ((va, "A"), (vb, "B")):
                lang[(l, v)] += 1
                role[(r, v)] += 1
                mode[(by_id[sid]["mode"], v)] += 1
                char[(by_id[sid]["character"], v)] += 1
            pair[frozenset((va, vb))] += 1
    vals = {v for (_, v) in lang}

    def spread(counter, keys):
        return sum(max(counter[(k, v)] for k in keys) - min(counter[(k, v)] for k in keys) for v in vals)
    return (3 * spread(lang, LANGS) + 3 * spread(role, ("A", "B")) + spread(mode, ("DA", "OH"))
            + spread(char, tuple(sorted({s["character"] for s in skeletons}))) + 4 * max(pair.values()))


def cooccurrence(pa, oa):
    c = Counter()
    for sid in pa:
        for l in LANGS:
            for i in (0, 1):
                c[(pa[sid][l][i], oa[sid][l][i])] += 1
    return max(c.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iterations", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=20260928)
    ap.add_argument("--set", default="main", help="items/<set>/skeletons_en.json -> items/<set>/assignment.json")
    a = ap.parse_args()
    skeletons = json.loads((ROOT / "items" / a.set / "skeletons_en.json").read_text(encoding="utf-8"))["items"]
    split = json.loads((ROOT / "data" / "value_split.json").read_text(encoding="utf-8"))
    vs = json.loads((ROOT / "data" / "valueset.json").read_text(encoding="utf-8"))
    conf = {l: {frozenset(p[:2]) for p in vs["confusable_pairs"].get(l, [])} for l in LANGS}
    rng = random.Random(a.seed)
    best = {}
    for typ in ("PLACE", "OBJECT"):
        vals = split[typ]["formal"]
        top = None
        for _ in range(a.iterations):
            cand = build(rng, vals, skeletons, conf, reorder=typ == "OBJECT")
            if cand is None:
                continue
            sc = score(cand, skeletons, typ)
            if typ == "OBJECT":  # also spread PLACE-OBJECT combinations within slots
                sc += 10 * cooccurrence(best["PLACE"][1], cand)
            if top is None or sc < top[0]:
                top = (sc, cand)
        best[typ] = top
        print(f"{typ}: best imbalance score {top[0]}")
    # choose the OBJECT solution among near-best ones to spread PLACE-OBJECT pairs
    co = cooccurrence(best["PLACE"][1], best["OBJECT"][1])
    assignment = {}
    for sk in skeletons:
        sid = sk["id"]
        assignment[sid] = {l: {v: {"PLACE": best["PLACE"][1][sid][l][i], "OBJECT": best["OBJECT"][1][sid][l][i]}
                               for i, v in enumerate(("A", "B"))} for l in LANGS}
    out = {"version": "assignment-0.1", "seed": a.seed, "iterations": a.iterations,
           "scores": {t: best[t][0] for t in best}, "max_place_object_cooccurrence": co, "slots": assignment}
    (ROOT / "items" / a.set / "assignment.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    # report
    lines = [f"# 取值分配报告（{a.set}）", "", f"由 `tools/assign_values.py --set {a.set}` 生成（seed {a.seed}，{a.iterations} 次搜索）。", ""]
    for typ in ("PLACE", "OBJECT"):
        cnt = Counter()
        pairs = Counter()
        for sid, langs in assignment.items():
            mode = next(s["mode"] for s in skeletons if s["id"] == sid)
            for l, vv in langs.items():
                cnt[(vv["A"][typ], l, "A")] += 1
                cnt[(vv["B"][typ], l, "B")] += 1
                cnt[(vv["A"][typ], mode)] += 1
                cnt[(vv["B"][typ], mode)] += 1
                pairs[frozenset((vv["A"][typ], vv["B"][typ]))] += 1
        lines += [f"## {typ}", "", "| 取值 | zh A/B | ja A/B | es A/B | 合计 | DA | OH |", "|---|---|---|---|---|---|---|"]
        for v in split[typ]["formal"]:
            row = [f"{cnt[(v, l, 'A')]}/{cnt[(v, l, 'B')]}" for l in LANGS]
            tot = sum(cnt[(v, l, r)] for l in LANGS for r in "AB")
            lines.append(f"| {v} | " + " | ".join(row) + f" | {tot} | {cnt[(v, 'DA')]} | {cnt[(v, 'OH')]} |")
        lines += ["", f"A/B 配对共 {len(pairs)} 种，单一配对最多出现 {max(pairs.values())} 次。", ""]
    lines += [f"同一槽位的 PLACE 与 OBJECT 组合最多重复 {co} 次。", "",
              "硬约束已满足：同一骨架 6 个槽位的取值两两不同；易混配对（valueset.json 的 confusable_pairs）没有出现在任何语种的 A/B 之间。", ""]
    name = "assignment-report.md" if a.set == "main" else f"assignment-report-{a.set}.md"
    (ROOT / "docs" / name).write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[-3:]))


if __name__ == "__main__":
    main()

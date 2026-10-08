"""Analyze the filled human audit sheets against the scorer (standard library only).

Reads one or two filled copies of deliverables/human-audit-20261008/audit-sheet.csv and the
organizer key analysis/human-audit/key.jsonl. A candidate counts as used when its object or place is
marked 1. Reports, per annotator and for the consensus (both annotators agree; disagreements listed):
  - Cohen's kappa between annotators for target use and for foil use
  - scorer versus human confusion counts for target and foil use
  - stratum-weighted target precision and recall of the scorer
  - net use D (target minus foil) from human labels and from the scorer, weighted to each stratum
    population, per stratum and pooled over strata of the same study
Usage: python3 tools/human_audit_report.py <filled.csv> [<filled2.csv>]
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def labels(path):
    out = {}
    for r in csv.DictReader(open(path, encoding="utf-8-sig")):
        val = lambda c: str(r.get(c, "")).strip() in ("1", "1.0", "y", "yes", "Y")
        out[r["id"]] = {1: val("f1_object") or val("f1_place"), 2: val("f2_object") or val("f2_place"),
                        "unsure": val("unsure"), "filled": any(str(r.get(c, "")).strip() for c in ("f1_object", "f1_place", "f2_object", "f2_place"))}
    return out


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def main():
    keys = {json.loads(l)["id"]: json.loads(l) for l in (ROOT / "analysis/human-audit/key.jsonl").read_text().splitlines()}
    anns = [labels(p) for p in sys.argv[1:]]
    ids = [i for i in keys if all(a.get(i, {}).get("filled") for a in anns)]
    print(f"{len(ids)} of {len(keys)} items filled by every annotator")
    tf = lambda a, i: (a[i][keys[i]["target_position"]], a[i][3 - keys[i]["target_position"]])
    if len(anns) == 2:
        for j, name in ((0, "target"), (1, "foil")):
            print(f"kappa {name}: {kappa([tf(anns[0], i)[j] for i in ids], [tf(anns[1], i)[j] for i in ids]):.3f}")
        dis = [i for i in ids if tf(anns[0], i) != tf(anns[1], i)]
        print(f"disagreements: {len(dis)}", dis[:20])
        use = [i for i in ids if i not in dis]
        human = {i: tf(anns[0], i) for i in use}
    else:
        use = ids
        human = {i: tf(anns[0], i) for i in use}
    conf = defaultdict(int)
    for i in use:
        k = keys[i]
        conf[("target", k["scorer_target"], int(human[i][0]))] += 1
        conf[("foil", k["scorer_foil"], int(human[i][1]))] += 1
    for what in ("target", "foil"):
        print(what, "scorer=1&human=1", conf[(what, 1, 1)], "scorer=1&human=0", conf[(what, 1, 0)],
              "scorer=0&human=1", conf[(what, 0, 1)], "scorer=0&human=0", conf[(what, 0, 0)])
    # weights: each item stands for (population of its scorer-hit cell) / (items sampled from that cell)
    w = {i: keys[i]["stratum_hit_population"] / keys[i]["stratum_hit_sample"] for i in use}
    by = defaultdict(list)
    for i in use:
        by[keys[i]["stratum"]].append(i)
    res = {}
    for st, its in sorted(by.items()):
        W = sum(w[i] for i in its)
        d_h = sum(w[i] * (human[i][0] - human[i][1]) for i in its) / W
        d_s = sum(w[i] * (keys[i]["scorer_target"] - keys[i]["scorer_foil"]) for i in its) / W
        tp = sum(w[i] for i in its if keys[i]["scorer_target"] and human[i][0])
        prec = tp / max(1e-9, sum(w[i] for i in its if keys[i]["scorer_target"]))
        rec = tp / max(1e-9, sum(w[i] for i in its if human[i][0]))
        res[st] = {"n": len(its), "D_human": d_h, "D_scorer": d_s, "target_precision": prec, "target_recall": rec}
        print(f"{st:<36} n={len(its):>3}  D human {100 * d_h:6.1f}  D scorer {100 * d_s:6.1f}  "
              f"target precision {100 * prec:5.1f}  recall {100 * rec:5.1f}")
    out = ROOT / "analysis/human-audit/report.json"
    out.write_text(json.dumps({"files": sys.argv[1:], "n": len(use), "confusion": {str(k): v for k, v in conf.items()}, "strata": res}, indent=1))
    print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    main()

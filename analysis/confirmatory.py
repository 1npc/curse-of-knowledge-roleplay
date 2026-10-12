"""Confirmatory analysis (docs/analysis-plan.md 4): eight one-sided tests, Holm-corrected, skeleton bootstrap.

Input: scored runs (runs/<run>/<model>/scored.jsonl); rows of several runs are merged per model by
prompt id, and mitigation rows are told apart by their arm.
Estimands are computed per (model, language) unit that passes the capability gate G2
(translation-probe recovery >= 0.85 in that language), on the capability-conditioned subset
(item versions whose translation probe recovered both canaries), then averaged with equal
weights. Every interval resamples skeletons once per bootstrap draw and applies the same draw
to all units, so the correlation induced by shared items across models is kept.

  H1   OC_swap(C-T-, D0)                                         lower bound > 0.10  (not understood)
  H1i  LEAK_swap(E_inaud_S, D0)                                  lower bound > 0.10  (not heard)
  H2a  OC_swap(C-T-, D0) - OC_swap(C-T-, D1)                     lower bound > 0     (a sentence helps)
  H2b  LEAK_swap(E_inaud_S, D0) - LEAK_swap(E_inaud, D0)         lower bound > 0     (a narrated description helps)
  H3   OC_swap(C-T-, D0) - OC_swap(C-T-_flag, D0)                lower bound > 0     (deriving it from the repertoire)
  H4   LEAK_swap(E_inaud_S, D0) - OC_swap(C-T-_flag, D0)         lower bound > 0     (not language-specific)
  H5a  OC_swap(C-T-, D0) on items whose state probe is right     lower bound > 0.10  (knowing but not applying)
  H5b  M1g: mean relative reduction over C-T- and E_inaud_S >= 0.5, and C-T+ use drops by at most 0.05
       (models with an OC_swap(C-T-, D0) lower bound > 0.10)
One-sided lower bounds come from the bootstrap at the Holm-adjusted level. Truncated and refusal
replies count as "not used" (hit_t = hit_f = 0) in the primary analysis.
Usage: python3 analysis/confirmatory.py <items.json> <run_dir> [<run_dir> ...] [--B 2000]
For the combined main run, pass --models with the frozen confirmatory roster explicitly.
Only skeletons in <items.json> enter the capability gates or the hypothesis tests.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean

GATE_G2 = 0.85
LANGS = ("zh", "ja", "es")


def load_runs(runs: list[Path], models=None, item_ids=None) -> dict[str, list[dict]]:
    out = defaultdict(dict)
    found = set()
    for run in runs:
        for d in sorted(p for p in run.iterdir() if (p / "scored.jsonl").exists()):
            if models is not None and d.name not in models:
                continue
            found.add(d.name)
            for l in (d / "scored.jsonl").read_text(encoding="utf-8").splitlines():
                if not l.strip():
                    continue
                r = json.loads(l)
                if item_ids is not None and r["item"] not in item_ids:
                    continue
                previous = out[d.name].get(r["prompt_id"])
                if previous is not None:
                    # Compare original records, before the primary-analysis transformation.
                    if previous != r:
                        raise ValueError(f"conflicting duplicate scored prompt for model {d.name}")
                    continue
                out[d.name][r["prompt_id"]] = r
    if models is not None and set(models) - found:
        raise ValueError("requested models have no scored files: " + ", ".join(sorted(set(models) - found)))
    for records in out.values():
        for pid, r in records.items():
            if r["status"] == "truncated" or r["score"]["R"]:  # primary analysis: counted as not used
                records[pid] = dict(r, score=dict(r["score"], hit_t=False, hit_f=False, LD_deny=False))
    if models is not None and set(models) - out.keys():
        raise ValueError("requested models have no records within the selected skeleton set")
    return {m: list(v.values()) for m, v in out.items()}


class Units:
    """Per (model, language) rows with capability flags and state-probe correctness."""

    def __init__(self, data: dict[str, list[dict]]):
        self.rows, self.cap, self.probe, self.gate = defaultdict(list), {}, {}, {}
        self.eligible_h5b = {}  # model -> OC_swap(C-T-, D0) lower bound > 0.10, set by main()
        for m, rows in data.items():
            rec = defaultdict(list)
            for r in rows:
                if r["arm"] == "probe_translate" and r["S"] == "real":
                    self.cap[(m, r["item"], r["lang"], r["version"])] = r["score"]["U2"]
                    rec[r["lang"]].append(r["score"]["U2"])
                elif r["arm"] == "probe_state" and r["cell"] == "C-T-" and r["D"] == "D0":
                    self.probe[(m, r["item"], r["lang"])] = r.get("probe_answer") == r.get("probe_expected")
                else:
                    self.rows[(m, r["lang"])].append(r)
            for lang in LANGS:
                self.gate[(m, lang)] = bool(rec[lang]) and mean(rec[lang]) >= GATE_G2

    def passing(self):
        return [u for u, ok in self.gate.items() if ok]

    def capable(self, u, r):
        return self.cap.get((u[0], r["item"], r["lang"], r["version"]), False)


def oc(rows):
    return mean(r["score"]["hit_t"] for r in rows) - mean(r["score"]["hit_f"] for r in rows) if rows else None


def cell(rows, cellname, D, versions=("A", "B"), Q=None, S="real", arm="main", step=None):
    return [r for r in rows if r["arm"] == arm and r["cell"] == cellname and r["D"] == D and r["version"] in versions
            and r["S"] == S and (Q is None or r["Q"] in Q) and (step is None or r.get("step", 1) == step)]


def statistics(units: Units, weight: dict[str, int]):
    """All statistics for one (re)sample; weight maps skeleton -> multiplicity."""
    def w(rows):
        return [r for r in rows for _ in range(weight.get(r["item"], 0))]

    def pooled(f):
        vals = [f(u) for u in units.passing()]
        vals = [v for v in vals if v is not None]
        return mean(vals) if vals else None

    def capable_rows(u, rows):
        return [r for r in rows if units.capable(u, r)]

    def h1(u):
        return oc(w(capable_rows(u, cell(units.rows[u], "C-T-", "D0"))))

    def lang_cell(u, c, D):  # foreign-language cells are capability-conditioned
        return oc(w(capable_rows(u, cell(units.rows[u], c, D))))

    def eng_cell(u, c, D):  # English cells need no translation, so every item counts
        return oc(w(cell(units.rows[u], c, D, S="english")))

    def diff(a, b):
        return None if a is None or b is None else a - b

    def h5a(u):
        rows = [r for r in capable_rows(u, cell(units.rows[u], "C-T-", "D0")) if units.probe.get((u[0], r["item"], r["lang"]))]
        return oc(w(rows))

    out = {"H1": pooled(h1),
           "H1i": pooled(lambda u: eng_cell(u, "Einaud_S", "D0")),
           "H2a": pooled(lambda u: diff(lang_cell(u, "C-T-", "D0"), lang_cell(u, "C-T-", "D1"))),
           "H2b": pooled(lambda u: diff(eng_cell(u, "Einaud_S", "D0"), eng_cell(u, "Einaud", "D0"))),
           "H3": pooled(lambda u: diff(lang_cell(u, "C-T-", "D0"), lang_cell(u, "C-T-_flag", "D0"))),
           "H4": pooled(lambda u: diff(eng_cell(u, "Einaud_S", "D0"), lang_cell(u, "C-T-_flag", "D0"))),
           "H5a": pooled(h5a)}
    red, keep = [], []
    for u in units.passing():
        base = oc(w(capable_rows(u, cell(units.rows[u], "C-T-", "D0", Q=("content", "plan")))))
        if units.eligible_h5b.get(u[0]) is False:
            continue
        m1 = oc(w(capable_rows(u, cell(units.rows[u], "C-T-", "D0", Q=("content", "plan"), arm="M1g", step=2))))
        ib = oc(w(cell(units.rows[u], "Einaud_S", "D0", Q=("content", "plan"), S="english")))
        im = oc(w(cell(units.rows[u], "Einaud_S", "D0", Q=("content", "plan"), S="english", arm="M1g", step=2)))
        tp0 = w(capable_rows(u, cell(units.rows[u], "C-T+", "D0", versions=("A",), Q=("content", "plan"))))
        tp1 = w(capable_rows(u, cell(units.rows[u], "C-T+", "D0", versions=("A",), Q=("content", "plan"), arm="M1g", step=2)))
        if not (base and m1 is not None and ib and im is not None and tp0 and tp1):
            continue
        red.append(((base - m1) / base + (ib - im) / ib) / 2)
        keep.append(mean(r["score"]["hit_t"] for r in tp1) - mean(r["score"]["hit_t"] for r in tp0))
    out["H5b_reduction"] = mean(red) if red else None
    out["H5b_keep"] = mean(keep) if keep else None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("items", type=Path)
    ap.add_argument("runs", type=Path, nargs="+")
    ap.add_argument("--B", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261003)
    ap.add_argument("--models", nargs="+", help="explicit frozen model keys; omit only for pilot/exploratory runs")
    a = ap.parse_args()
    items = json.loads(a.items.read_text(encoding="utf-8"))["items"]
    if any(it.get("set") == "main" for it in items) and not a.models:
        ap.error("main-set confirmatory analysis requires --models with the frozen roster")
    skeletons = sorted(it["id"] for it in items)
    units = Units(load_runs(a.runs, models=a.models, item_ids=set(skeletons)))
    rng = random.Random(a.seed)
    weights = []
    for _ in range(a.B):
        weight = defaultdict(int)
        for _ in skeletons:
            weight[rng.choice(skeletons)] += 1
        weights.append(weight)
    # H5b eligibility: the model's own OC_swap(C-T-, D0) lower bound (5%, pooled over its passing languages)
    for m in {u[0] for u in units.passing()}:
        sub = Units.__new__(Units)
        sub.rows, sub.cap, sub.probe, sub.eligible_h5b = units.rows, units.cap, units.probe, {}
        sub.gate = {u: ok for u, ok in units.gate.items() if u[0] == m}
        vs = sorted(v for v in (statistics(sub, wt)["H1"] for wt in weights[:500]) if v is not None)
        units.eligible_h5b[m] = bool(vs) and vs[int(0.05 * len(vs))] > 0.10
    point = statistics(units, {k: 1 for k in skeletons})
    draws = defaultdict(list)
    for weight in weights:
        for k, v in statistics(units, weight).items():
            if v is not None:
                draws[k].append(v)
    thresholds = {"H1": 0.10, "H1i": 0.10, "H2a": 0.0, "H2b": 0.0, "H3": 0.0, "H4": 0.0, "H5a": 0.10}
    # one-sided p-value: share of draws at or below the threshold
    pvals = {h: (sum(v <= thr for v in draws[h]) + 1) / (len(draws[h]) + 1) for h, thr in thresholds.items() if draws[h]}
    if draws.get("H5b_reduction"):  # one-sided keep criterion (decision 9/28): C-T+ use may not drop by more than 0.05
        ok = [r >= 0.5 and k >= -0.05 for r, k in zip(draws["H5b_reduction"], draws["H5b_keep"])]
        pvals["H5b"] = (sum(not x for x in ok) + 1) / (len(ok) + 1)
    order = sorted(pvals, key=pvals.get)
    holm, running = {}, 0.0
    for i, h in enumerate(order):
        running = max(running, min(1.0, (len(order) - i) * pvals[h]))
        holm[h] = running
    print(f"units passing G2: {sorted(units.passing())}")
    print(f"H5b-eligible models: {sorted(m for m, ok in units.eligible_h5b.items() if ok)}")
    print(f"{'hyp':<5}{'point':>9}{'lower95':>9}{'p':>9}{'Holm p':>9}  decision (alpha 0.05)")
    for h in ["H1", "H1i", "H2a", "H2b", "H3", "H4", "H5a", "H5b"]:
        if h not in pvals:
            continue
        if h == "H5b":
            pt = f"{point['H5b_reduction']:.3f}/{point['H5b_keep']:+.3f}" if point.get("H5b_reduction") is not None else "–"
            lo = "–"
        else:
            vs = sorted(draws[h])
            pt, lo = f"{point[h]:.3f}", f"{vs[int(0.05 * len(vs))]:.3f}"
        print(f"{h:<5}{pt:>9}{lo:>9}{pvals[h]:>9.4f}{holm[h]:>9.4f}  {'supported' if holm[h] < 0.05 else 'not supported'}")


if __name__ == "__main__":
    main()

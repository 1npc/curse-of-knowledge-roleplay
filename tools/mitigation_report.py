"""Mitigation arms on the pilot (proposal H4b and its supporting readouts).

Compares, per model, the D0 baseline from the pilot run with the M1 (two-step perspective filter)
and FS (few-shot) arms on the same cells: C-T- A and B (should not use the content) and C-T+ A
(should use it, through the translator). Also reports M1 step-1 leakage (the filter itself
names the canaries) and the H4b criterion: relative reduction of OC_swap with a skeleton
bootstrap lower bound >= 0.5 while C-T+ use stays within 5 points.
Writes docs/mitigation-report.md.
Usage: python3 tools/mitigation_report.py runs/pilot-20260928 runs/mitig-20260928
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from pilot_gates import boot, oc  # noqa: E402


def load(run: Path, model: str):
    f = run / model / "scored.jsonl"
    return [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()] if f.exists() else []


def pick(rows, arm, cell, versions, step=None):
    out = []
    for r in rows:
        if r["arm"] != arm or r["cell"] != cell or r["version"] not in versions or r["Q"] not in ("content", "plan"):
            continue
        if arm == "main" and (r["S"] != "real" or r["D"] != "D0"):
            continue
        if step is not None and r.get("step", 1) != step:
            continue
        out.append(r)
    return out


def pct(x):
    return "–" if x is None else f"{100 * x:.1f}"


def main():
    base_run, mit_run = Path(sys.argv[1]), Path(sys.argv[2])
    models = sorted(p.name for p in mit_run.iterdir() if (p / "scored.jsonl").exists())
    L = ["# 缓解实验（试点条目）", "", "由 `tools/mitigation_report.py` 生成。格：C−T− 的 A/B 两版（不应使用内容）与 C−T+ 的 A 版（经翻译器应使用内容），"
         "都是 D0，内容追问与计划追问合并。数值为百分比；方括号为按骨架重抽的 95% 区间。", "",
         "| 模型 | 条件 | OC_swap(C−T−) | C−T+ 命中率 | M1 第一步泄漏（C−T−） | 相对降幅 [95%] |", "|---|---|---|---|---|---|"]
    for m in models:
        base, mit = load(base_run, m), load(mit_run, m)
        b_ct = pick(base, "main", "C-T-", ("A", "B"))
        b_tp = pick(base, "main", "C-T+", ("A",))
        oc0 = oc(b_ct)
        L.append(f"| {m} | D0 基线 | {pct(oc0)} | {pct(mean(r['score']['hit_t'] for r in b_tp))} | – | – |")
        for arm, step in (("M1", 2), ("FS", None)):
            ct = pick(mit, arm, "C-T-", ("A", "B"), step)
            tp = pick(mit, arm, "C-T+", ("A",), step)
            if not ct:
                continue
            leak = "–"
            if arm == "M1":
                s1 = pick(mit, "M1", "C-T-", ("A", "B"), 1)
                leak = pct(mean(r["score"]["hit_t"] for r in s1))
            both = b_ct + ct
            red = boot(both, stat=lambda rs: (lambda o0, o1: (o0 - o1) / o0 if o0 else 0.0)(
                oc([r for r in rs if r["arm"] == "main"]), oc([r for r in rs if r["arm"] != "main"])))
            red_s = "–" if red is None else f"{100 * red[0]:.0f} [{100 * red[2]:.0f}, {100 * red[3]:.0f}]"
            L.append(f"| {m} | {arm} | {pct(oc(ct))} | {pct(mean(r['score']['hit_t'] for r in tp))} | {leak} | {red_s} |")
    L += ["", "H4b 的判据（proposal 2.2）：相对降幅的下界 ≥ 50%，且 C−T+ 命中率的变化在 ±5 个百分点内。试点每格约 120 条回复、10 个骨架，只看方向。", ""]
    out = ROOT / "docs" / "mitigation-report.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()

"""Matched structured comparison (docs/storyline.md 3): is "not understood" harder to hold than "not heard"?

Cells, all at D0 (structured state only) unless noted:
  C-T-          language repertoire in the state; the model must derive that the character cannot understand
  C-T-_flag     the same, plus understood_by_X: false on each utterance
  Einaud_S      English speech with audible_to_X: false on each utterance
  Einaud        English speech, and the scene description says the character could not hear
Both flag cells use the same neutral scene description.
  derivation    = OC_swap(C-T-) - OC_swap(C-T-_flag)
  comprehension = OC_swap(C-T-_flag) - LEAK_swap(Einaud_S)
Rows from several runs are merged per model (the earlier pilot runs hold the unchanged cells).
Intervals resample skeletons, keeping each skeleton's languages, cells and versions together.
Usage: python3 tools/matched_report.py <report.md> runs/<run> [runs/<run> ...]
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pilot_gates import boot, ci, fmt, oc, sel  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CELLS = [("real", "C-T-", "D0"), ("real", "C-T-_flag", "D0"), ("english", "Einaud_S", "D0"),
         ("english", "Einaud", "D0"), ("real", "C-T-", "D1"), ("english", "Einaud", "D1")]
HEAD = ["C−T− D0（语言清单）", "C−T−_flag（逐句标记听不懂）", "E_inaud_S（逐句标记听不见）",
        "E_inaud D0（描述写明听不见）", "C−T− D1（文字）", "E_inaud D1（文字）"]


def load(runs):
    data = defaultdict(dict)
    for run in runs:
        for d in sorted(p for p in run.iterdir() if (p / "scored.jsonl").exists()):
            for line in (d / "scored.jsonl").read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    data[d.name][r["prompt_id"]] = r  # later runs never repeat a prompt id
    return {m: list(v.values()) for m, v in data.items()}


def diff(rows, a, b):
    ra, rb = sel(rows, *a), sel(rows, *b)
    if not ra or not rb:
        return None
    pick = lambda rs, c: [r for r in rs if r["cell"] == c[1] and r["D"] == c[2]]
    return boot(ra + rb, stat=lambda rs: oc(pick(rs, a)) - oc(pick(rs, b)))


def probe(rows, cell):
    rs = [r for r in rows if r["arm"] == "probe_state" and r["cell"] == cell]
    return sum(r.get("probe_answer") == r.get("probe_expected") for r in rs) / len(rs) if rs else None


def main():
    out, runs = Path(sys.argv[1]), [Path(p) for p in sys.argv[2:]]
    data = load(runs)
    models = [m for m in data if sel(data[m], "real", "C-T-_flag", "D0")]
    L = ["# 对齐的结构化对比（" + ", ".join(r.name for r in runs) + "）", "",
         "由 `tools/matched_report.py` 生成，设计见 `storyline.md` 第 3 节。数值是百分比（A/B 合并，四种追问合并）；"
         "方括号是按骨架重抽的 95% 区间（试点 10 个骨架，只看方向）。", "",
         "## 各格泄漏（OC_swap；听不见的两格是同样算法的 LEAK_swap）", "",
         "| 模型 | " + " | ".join(HEAD) + " |", "|---|" + "---|" * len(HEAD)]
    for m in models:
        L.append(f"| {m} | " + " | ".join(fmt(oc(sel(data[m], *c))) for c in CELLS) + " |")
    L += ["", "## 两个差值", "",
          "| 模型 | 推理一步：C−T− D0 − C−T−_flag | 理解本身：C−T−_flag − E_inaud_S | 对照：E_inaud D0 − E_inaud_S（描述的作用） |",
          "|---|---|---|---|"]
    for m in models:
        r = data[m]
        L.append(f"| {m} | {ci(diff(r, CELLS[0], CELLS[1]))} | {ci(diff(r, CELLS[1], CELLS[2]))} | "
                 f"{ci(diff(r, CELLS[3], CELLS[2]))} |")
    L += ["", "## 状态理解探针正确率", "", "| 模型 | C−T− D0 | C−T−_flag | E_inaud D0 | E_inaud_S |", "|---|---|---|---|---|"]
    for m in models:
        L.append(f"| {m} | " + " | ".join(fmt(probe(data[m], c)) for c in ("C-T-", "C-T-_flag", "Einaud", "Einaud_S")) + " |")
    L += ["", "## 否认与否认却使用（A/B 合并）", "", "| 模型 | 格 | N_deny | N_unheard | LD_deny |", "|---|---|---|---|---|"]
    for m in models:
        for c, h in zip(CELLS[:3], HEAD[:3]):
            rs = sel(data[m], *c)
            g = lambda k: fmt(sum(bool(x["score"].get(k)) for x in rs) / len(rs)) if rs else "–"
            L.append(f"| {m} | {h} | {g('N_deny')} | {g('N_unheard')} | {g('LD_deny')} |")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()

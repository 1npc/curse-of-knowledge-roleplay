"""Calibrate the rule-4 cognate screen on known cognates and unrelated pairs (proposal 5.4).

Writes docs/gate-calibration.md with recall on cognates, false rejections on unrelated
pairs, and which criterion (Levenshtein, prefix, Double Metaphone) fired for each pair.
Usage: python3 tools/calibrate_gate.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from oc.gate import cognate_check, screen_text  # noqa: E402


def run(pairs):
    rows = []
    for lang, form, reading, en in pairs:
        r = cognate_check(lang, form, reading, [en])
        crit = {"lev": any(x.startswith("levenshtein") for x in r["reasons"]),
                "prefix": any(x.startswith("prefix") for x in r["reasons"]),
                "dm": any(x.startswith("metaphone") for x in r["reasons"])}
        rule3 = any(m["rule"] == 3 and m["level"] == "reject" for m in screen_text(lang, form))
        rows.append({"lang": lang, "form": form, "en": en, "reject": r["reject"], "max_sim": r["max_sim"],
                     "renderings": r["renderings"], "rule3": rule3, **crit})
    return rows


def main():
    data = json.loads((ROOT / "data" / "cognate_calibration.json").read_text(encoding="utf-8"))
    cog, non = run(data["cognates"]), run(data["noncognates"])
    recall = sum(r["reject"] for r in cog) / len(cog)
    false_rej = sum(r["reject"] for r in non) / len(non)
    by_lang = {}
    for r in cog:
        d = by_lang.setdefault(r["lang"], [0, 0])
        d[0] += r["reject"]
        d[1] += 1
    lines = ["# 同源筛校准（规则 4）", "",
             "由 `tools/calibrate_gate.py` 生成，数据在 `data/cognate_calibration.json`。",
             "拒绝条件：任一转写与英文词的归一化 Levenshtein 相似度 ≥ 0.5，或前 3 个字母相同，或 Double Metaphone 主码相同。", "",
             f"- 同源或借词 {len(cog)} 对，拒绝 {sum(r['reject'] for r in cog)} 对，**召回率 {recall:.2f}**；"
             + "，".join(f"{k} {v[0]}/{v[1]}" for k, v in sorted(by_lang.items())),
             f"- 规则 3（ja 片假名禁令、zh 音译词表、es 借词表）与规则 4 合起来拒绝 "
             f"{sum(r['reject'] or r['rule3'] for r in cog)}/{len(cog)} 对",
             f"- 非同源 {len(non)} 对，误拒 {sum(r['reject'] for r in non)} 对，**误拒率 {false_rej:.2f}**", "",
             "各判据单独的命中数（同源对）："
             f" Levenshtein {sum(r['lev'] for r in cog)}，前缀 {sum(r['prefix'] for r in cog)}，Metaphone {sum(r['dm'] for r in cog)}。", "",
             "## 漏掉的同源对", "", "| 语种 | 形式 | 英文 | 最大相似度 | 转写 | 规则 3 拦下 |", "|---|---|---|---|---|---|"]
    for r in cog:
        if not r["reject"]:
            lines.append(f"| {r['lang']} | {r['form']} | {r['en']} | {r['max_sim']:.2f} | {', '.join(r['renderings'])} "
                         f"| {'是' if r['rule3'] else '否'} |")
    lines += ["", "## 误拒的非同源对", "", "| 语种 | 形式 | 英文 | 最大相似度 | 触发判据 |", "|---|---|---|---|---|"]
    for r in non:
        if r["reject"]:
            which = [k for k in ("lev", "prefix", "dm") if r[k]]
            lines.append(f"| {r['lang']} | {r['form']} | {r['en']} | {r['max_sim']:.2f} | {', '.join(which)} |")
    lines += ["", "漏掉的同源对由规则 9 的词形可猜性检验兜底；它们也说明这道闸不能单独当熟悉度筛。", ""]
    out = ROOT / "docs" / "gate-calibration.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"recall {recall:.2f} ({sum(r['reject'] for r in cog)}/{len(cog)}), "
          f"false rejection {false_rej:.2f} ({sum(r['reject'] for r in non)}/{len(non)}) -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

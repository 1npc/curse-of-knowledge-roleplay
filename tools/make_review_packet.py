"""Native-speaker review sheets (proposal 5.6 step 5) and a back-translation packet.

For each language, one Markdown sheet lists every item version with its intended meaning
and canary words, and asks the checker to rate naturalness (1-5, pass at >= 4) and to
confirm that each canary is a native word that alone carries its meaning, that there are
no loanwords, cognates or proper nouns, and that A and B differ only in the canaries
(Spanish may change articles and pronouns to agree).
The back-translation packet holds the foreign lines only (no gold), for a translator who
must not see the English.
Usage: python3 tools/make_review_packet.py items/pilot/skeletons.json pilot
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from oc.gate import load_valueset  # noqa: E402

HEAD = {
    "zh": ("中文条目核对表", "请逐条检查。每条给出 A、B 两版和意图译文。"),
    "ja": ("Japanese item review sheet", "Please check each item. Each has an A and a B version and the intended meaning."),
    "es": ("Spanish item review sheet", "Please check each item. Each has an A and a B version and the intended meaning."),
}
CHECKS = {
    "zh": ["自然度（1 到 5，≥ 4 通过）：A ___ B ___",
           "两个金丝雀词（加粗）是本族词，且句中只有它们表达这两个意思：是 / 否",
           "没有外来音译词、专名、数字：是 / 否",
           "A 与 B 除金丝雀外逐字相同：是 / 否",
           "拼音读音正确：是 / 否",
           "修改建议："],
    "ja": ["Naturalness (1-5, pass at 4 or above): A ___ B ___",
           "Each bold canary word is a native (non-katakana) word and is the only word carrying that meaning: yes / no",
           "No loanwords, proper nouns, or numbers: yes / no",
           "A and B are identical except for the canary words: yes / no",
           "The kana reading is correct: yes / no",
           "Suggested fix:"],
    "es": ["Naturalness (1-5, pass at 4 or above): A ___ B ___",
           "Each bold canary word is a native Spanish word (not an English loan or obvious cognate) and is the only word carrying that meaning: yes / no",
           "No English loanwords, proper nouns, or numbers: yes / no",
           "A and B differ only in the canary words, plus articles or pronouns that change to agree: yes / no",
           "Regional note (the setting is a Californian city with a large Mexican-American community; neutral or Mexican usage preferred):",
           "Suggested fix:"],
}


def bold(line: str, forms: list[str]) -> str:
    for f in sorted(forms, key=len, reverse=True):
        line = line.replace(f, f"**{f}**")
    return line


def main():
    items_path, tag = Path(sys.argv[1]), sys.argv[2]
    items = json.loads(items_path.read_text(encoding="utf-8"))["items"]
    vs = load_valueset()
    out = ROOT / "docs" / "review"
    out.mkdir(parents=True, exist_ok=True)
    for lang in ("zh", "ja", "es"):
        title, intro = HEAD[lang]
        lines = [f"# {title} ({tag})", "", intro, ""]
        bt = [f"# Back-translation packet ({tag}, {lang})", "",
              "Translate each line into English as literally as possible. Do not use a machine translator.", ""]
        for it in items:
            lines.append(f"## {it['id']}")
            lines.append("")
            for ver in ("A", "B"):
                v = it["langs"][lang][ver]
                forms = [vs["by_id"][v[t]][lang]["form"] for t in ("PLACE", "OBJECT")]
                canaries = ", ".join(f"{vs['by_id'][v[t]][lang]['form']} = {v[t].replace('_', ' ')}" for t in ("PLACE", "OBJECT"))
                lines.append(f"**{ver}**: " + " / ".join(bold(l, forms) for l in v["lines"]))
                if v.get("reading"):
                    lines.append(f"- reading: {' / '.join(v['reading'])}")
                lines.append(f"- intended meaning: {' / '.join(v['gold'])}")
                lines.append(f"- canaries: {canaries}")
                lines.append("")
                bt.append(f"{it['id']}-{ver}: " + " / ".join(v["lines"]))
            has_reading = any(it["langs"][lang][v].get("reading") for v in ("A", "B"))
            lines += [f"- {c}" for c in CHECKS[lang] if has_reading or not c.startswith(("拼音读音", "The kana reading"))]
            lines.append("")
        (out / f"{tag}-{lang}.md").write_text("\n".join(lines), encoding="utf-8")
        (out / f"{tag}-{lang}-backtranslation.md").write_text("\n".join(bt) + "\n", encoding="utf-8")
    print(f"sheets -> {out.relative_to(ROOT)}/{tag}-{{zh,ja,es}}.md and back-translation packets")


if __name__ == "__main__":
    main()

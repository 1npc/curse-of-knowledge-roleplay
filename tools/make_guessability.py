"""Word-form guessability questionnaire (proposal 5.4 rule 9).

96 foreign word forms (32 candidate values x zh/ja/es), each shown in writing and in a
romanization, with 8 English options of the same type (chance 0.125). Evaluators are
English-dominant, report not knowing the language, and cannot read Chinese characters.
A value is dropped for a language when at least 4 of 10 evaluators pick the right meaning
(pure-chance probability about 0.027).

Writes docs/guessability/: form.md (to paste into a survey tool or print), items.csv
(one row per question, options in display order), answer_key.json (keep away from
evaluators) and score.py usage notes live in tools/score_guessability.py.
Usage: python3 tools/make_guessability.py
"""
from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from oc.gate import load_valueset  # noqa: E402
from oc.translit import variants  # noqa: E402

SEED = 20260928
LANG_LABEL = {"zh": "Chinese", "ja": "Japanese", "es": "Spanish"}
MEANING = {"parking_lot": "parking lot"}


def main():
    vs = load_valueset()
    rng = random.Random(SEED)
    by_type = {t: [v["id"] for v in vs["values"] if v["type"] == t] for t in ("PLACE", "OBJECT")}
    questions = []
    for v in vs["values"]:
        for lang in ("ja", "zh", "es"):
            spec = v[lang]
            roman = "" if lang == "es" else variants(lang, spec["form"], spec.get("reading"))[0]
            distract = rng.sample([x for x in by_type[v["type"]] if x != v["id"]], 7)
            options = [MEANING.get(x, x) for x in distract + [v["id"]]]
            rng.shuffle(options)
            questions.append({"value": v["id"], "lang": lang, "form": spec["form"], "romanization": roman,
                              "options": options, "answer": MEANING.get(v["id"], v["id"])})
    rng.shuffle(questions)
    for i, q in enumerate(questions, 1):
        q["qid"] = f"Q{i:02d}"
    out = ROOT / "docs" / "guessability"
    out.mkdir(parents=True, exist_ok=True)
    with (out / "items.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["qid", "word", "romanization", "language"] + [f"option_{k}" for k in range(1, 9)])
        for q in questions:
            w.writerow([q["qid"], q["form"], q["romanization"], LANG_LABEL[q["lang"]]] + q["options"])
    key = {q["qid"]: {"value": q["value"], "lang": q["lang"], "answer": q["answer"]} for q in questions}
    (out / "answer_key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = [
        "# Word guessing task", "",
        "Thank you for helping with a language research study. It takes about 20 to 30 minutes.", "",
        "**Before you start, please answer three questions:**", "",
        "1. Is English the language you use most in daily life? (yes / no)",
        "2. Can you speak or understand any Chinese, Japanese, or Spanish, even a little? If yes, which? ",
        "3. Can you read Chinese characters (hanzi or kanji)? (yes / no)", "",
        "**Instructions.** Each question shows one foreign word, sometimes with how it sounds in Latin letters. "
        "Pick the English meaning you think is most likely. Please do not look anything up, use a translator, or ask "
        "anyone. If you have no idea, just pick the option that feels closest; guessing is expected.", "",
        "Your answers are anonymous and used only to decide which words are too easy to guess. "
        "You can stop at any time.", "",
    ]
    for q in questions:
        shown = q["form"] + (f"  ({q['romanization']})" if q["romanization"] else "")
        lines.append(f"**{q['qid']}.** {shown}")
        lines.append("")
        lines += [f"- [ ] {o}" for o in q["options"]]
        lines.append("")
    (out / "form.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(questions)} questions -> {out.relative_to(ROOT)}/ (form.md, items.csv, answer_key.json)")


if __name__ == "__main__":
    main()

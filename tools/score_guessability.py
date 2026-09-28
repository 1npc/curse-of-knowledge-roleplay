"""Score the guessability questionnaire and list values to drop per language (proposal 5.4 rule 9).

Input: a CSV with one row per evaluator: evaluator_id, english_dominant (yes/no),
knows_language (free text), reads_characters (yes/no), then one column per qid holding
the chosen English option. Evaluators who are not English-dominant are excluded; answers
to a language the evaluator reports knowing are excluded; answers to ja/zh from evaluators
who read Chinese characters are excluded.
Usage: python3 tools/score_guessability.py responses.csv
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THRESHOLD = 4        # correct answers out of 10 that drop a value (design value)
PANEL = 10
CHANCE = 1 / 8


def main():
    key = json.loads((ROOT / "docs" / "guessability" / "answer_key.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
    tally = defaultdict(lambda: [0, 0])
    kept = 0
    for r in rows:
        if r.get("english_dominant", "").strip().lower() != "yes":
            continue
        kept += 1
        knows = r.get("knows_language", "").lower()
        reads = r.get("reads_characters", "").strip().lower() == "yes"
        for qid, k in key.items():
            lang = k["lang"]
            if {"zh": "chinese", "ja": "japanese", "es": "spanish"}[lang] in knows:
                continue
            if reads and lang in ("ja", "zh"):
                continue
            ans = (r.get(qid) or "").strip().lower()
            if not ans:
                continue
            tally[(k["value"], lang)][1] += 1
            tally[(k["value"], lang)][0] += ans == k["answer"].lower()
    p_chance = sum(comb(PANEL, j) * CHANCE ** j * (1 - CHANCE) ** (PANEL - j) for j in range(THRESHOLD, PANEL + 1))
    print(f"evaluators kept: {kept}; P(>= {THRESHOLD}/{PANEL} by chance) = {p_chance:.3f}")
    drop = []
    for (value, lang), (right, n) in sorted(tally.items()):
        # scale the 4-of-10 rule to the panel actually answering
        if n and right / n >= THRESHOLD / PANEL:
            drop.append({"value": value, "lang": lang, "correct": right, "answered": n})
    print(json.dumps({"drop": drop, "panel_sizes": sorted({n for _, n in tally.values()})}, indent=1))


if __name__ == "__main__":
    main()

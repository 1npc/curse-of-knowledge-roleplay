"""Build the Study 2 human review packet that replaces the AI screening of Appendix B.

The rows are the 640 semantic-content replies and 192 awareness replies of the access-v2 blind packet, written in the
layout of the 2026-09-29 audit (one reply per row, two candidate facts in randomized order, blank label columns).
The key that maps review IDs to models and conditions stays in analysis/study2-human-review/ and is not shared.

Usage: python3 tools/make_s2_review.py
"""
import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "analysis/validation-access-v2"
OUT = ROOT / "deliverables/study2-review-20261010"
KEY = ROOT / "analysis/study2-human-review"


def items():
    out = {}
    for name in ("discovery-items.json", "confirmatory-items.json"):
        for it in json.loads((ROOT / "items/access-v2" / name).read_text())["items"]:
            out[it["id"]] = it
    return out


def main():
    its = items()
    key = {json.loads(l)["blind_id"]: json.loads(l) for l in (V2 / "organizer-key.jsonl").read_text().splitlines() if l.strip()}
    rng = random.Random(20261010)
    OUT.mkdir(parents=True, exist_ok=True)
    KEY.mkdir(parents=True, exist_ok=True)
    private = []

    rows = list(csv.DictReader(open(V2 / "blind-content-A.csv", encoding="utf-8-sig")))
    rng.shuffle(rows)
    cols = ["audit_id", "reply", "set1_gold", "set1_foreign", "set1_place", "set1_object", "set2_gold", "set2_foreign",
            "set2_place", "set2_object", "use_set1_place", "use_set1_object", "use_set2_place", "use_set2_object",
            "N_deny", "refusal", "echo_only", "notes"]
    with open(OUT / "content.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for n, r in enumerate(rows, 1):
            k = key[r["blind_id"]]
            it = its[k["prompt_id"].split(".")[0]]
            lang = it["langs"][it["lang"]]
            sets = []
            for v in k["candidate_versions"]:
                sets.append((lang[v]["gold"][0], lang[v]["lines"][0] if k["boundary"] == "Understand" else "",
                             lang[v]["PLACE"], lang[v]["OBJECT"]))
            aid = f"S2C{n:04d}"
            w.writerow({"audit_id": aid, "reply": r["response"],
                        "set1_gold": sets[0][0], "set1_foreign": sets[0][1], "set1_place": sets[0][2], "set1_object": sets[0][3],
                        "set2_gold": sets[1][0], "set2_foreign": sets[1][1], "set2_place": sets[1][2], "set2_object": sets[1][3]})
            private.append({"audit_id": aid, **k})

    rows = list(csv.DictReader(open(V2 / "blind-awareness-A.csv", encoding="utf-8-sig")))
    rng.shuffle(rows)
    cols = ["audit_id", "question", "reply", "acknowledges_occurrence", "claims_content_knowledge", "notes"]
    with open(OUT / "awareness.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for n, r in enumerate(rows, 1):
            aid = f"S2A{n:04d}"
            w.writerow({"audit_id": aid, "question": r["question"], "reply": r["response"]})
            private.append({"audit_id": aid, **key[r["blind_id"]]})

    with open(KEY / "key.jsonl", "w", encoding="utf-8") as f:
        for p in private:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print("content", sum(1 for p in private if p["audit_id"].startswith("S2C")), "awareness",
          sum(1 for p in private if p["audit_id"].startswith("S2A")))


if __name__ == "__main__":
    main()

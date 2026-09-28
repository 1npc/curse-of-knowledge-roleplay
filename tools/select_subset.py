"""Write a prompt-id subset for a smoke run (proposal 9: three models, valid output before the pilot).

Smoke: items P01 (direct address) and P06 (overheard) in all three languages; per item the cells
that exercise every part of the prompt builder: C-T- D0 (content, plan), C+T- D0 (content),
C-T+ D1 (content), E (content), E_inaud (content), noise C-T- D0 (content), the translation probe
(A) and one state probe. About 60 prompts per model.
Usage: python3 tools/select_subset.py items/pilot/prompts.jsonl items/pilot/smoke_ids.txt
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

WANT = [("main", "real", "C-T-", "D0", "content"), ("main", "real", "C-T-", "D0", "plan"),
        ("main", "real", "C+T-", "D0", "content"), ("main", "real", "C-T+", "D1", "content"),
        ("main", "english", "E", "D0", "content"), ("main", "english", "Einaud", "D0", "content"),
        ("main", "noise", "C-T-", "D0", "content"), ("probe_translate", "real", "C+T-", "D0", "translate"),
        ("probe_state", "real", "C-T-", "D0", "state")]


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    ids = []
    for line in src.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["item"] in ("P01", "P06") and r["version"] == "A" and (r["arm"], r["S"], r["cell"], r["D"], r["Q"]) in WANT:
            ids.append(r["prompt_id"])
    dst.write_text("\n".join(sorted(ids)) + "\n", encoding="utf-8")
    print(f"{len(ids)} prompt ids -> {dst}")


if __name__ == "__main__":
    main()

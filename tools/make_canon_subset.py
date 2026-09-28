"""Canon and character-layer subset (proposal 5.3): reuse main-set foreign text with other characters.

52 items: Takemura x ja (canon C+, 12), Jackie x es (canon C+, 12), Johnny x ja (weak canon C-, 12),
Maiko x ja (name prior, declared C-, 8), Judy x es (name prior, declared C-, 8). Only skeletons whose
scene and frame fit any mercenary-world character are reused. Each entry is built into 8 prompts:
{U, declared state D0} x {A, B} x {content, plan}.
Usage: python3 tools/make_canon_subset.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = [  # character, language, declared C, group, direct-address skeletons, overheard skeletons
    ("Takemura", "ja", "+", "canon_C+", ["S02", "S07", "S08", "S12", "S21", "S27"], ["S05", "S11", "S17", "S24", "S31", "S36"]),
    ("Jackie", "es", "+", "canon_C+", ["S02", "S07", "S08", "S12", "S21", "S27"], ["S05", "S11", "S17", "S24", "S31", "S36"]),
    ("Johnny", "ja", "-", "canon_weak_C-", ["S33", "S39", "S45", "S51", "S57", "S63"], ["S42", "S48", "S54", "S60", "S41", "S56"]),
    ("Maiko", "ja", "-", "name_prior_C-", ["S02", "S08", "S21", "S33"], ["S35", "S59", "S10", "S47"]),
    ("Judy", "es", "-", "name_prior_C-", ["S33", "S39", "S45", "S51"], ["S42", "S48", "S54", "S60"]),
]


def main():
    main_items = {i["id"]: i for i in json.loads((ROOT / "items" / "main" / "skeletons.json").read_text(encoding="utf-8"))["items"]}
    out = []
    for char, lang, C, group, da, oh in PLAN:
        for sid in da + oh:
            base = main_items[sid]
            want = "DA" if sid in da else "OH"
            if base["mode"] != want:
                raise SystemExit(f"{sid} is {base['mode']}, listed as {want}")
            out.append({"id": f"K-{char}-{sid}", "base": sid, "character": char, "lang": lang, "declared_C": C, "group": group})
    path = ROOT / "items" / "canon" / "subset.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"version": "canon-0.1", "entries": out}, indent=1) + "\n", encoding="utf-8")
    print(f"{len(out)} entries -> {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

"""Materialize prompts for a set of items into a JSONL plan (one record per model call).

Usage: python3 tools/build_prompts.py items/pilot/skeletons.json items/pilot/prompts.jsonl --pilot
Each record carries prompt_id, the design factors and the exact messages; the harness
runs the file as-is and the scorer joins on prompt_id. A manifest with counts and the
SHA-256 of the output is written next to it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from oc.build import build_item, build_robustness  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("items", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--pilot", action="store_true", help="add the N2 noise cells")
    ap.add_argument("--robustness", action="store_true", help="also write the prompt-robustness arm")
    ap.add_argument("--langs", default="zh,ja,es")
    a = ap.parse_args()
    items = json.loads(a.items.read_text(encoding="utf-8"))["items"]
    recs = []
    for it in items:
        for lang in a.langs.split(","):
            recs += build_item(it, lang, pilot=a.pilot)
            if a.robustness:
                recs += build_robustness(it, lang)
    ids = [r["prompt_id"] for r in recs]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate prompt ids")
    data = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in recs)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(data, encoding="utf-8")
    manifest = {"items_file": str(a.items), "items_sha256": hashlib.sha256(a.items.read_bytes()).hexdigest(),
                "prompts": len(recs), "prompts_sha256": hashlib.sha256(data.encode()).hexdigest(),
                "by_arm": dict(Counter(r["arm"] for r in recs)), "by_lang": dict(Counter(r["lang"] for r in recs)),
                "by_S": dict(Counter(r["S"] for r in recs)), "pilot": a.pilot, "robustness": a.robustness}
    a.out.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()

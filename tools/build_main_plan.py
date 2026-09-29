"""Materialize every prompt file of the main run (standard library only).

  items/main/prompts.jsonl          main set, 288 items x 143 prompts                      all models
  items/main/prompts_side.jsonl     non-Cyberpunk arm (48 items x 24) and canon subset (52 x 8)   all models
  items/main/mitigation_m1g.jsonl   M1g on C-T- A/B, C-T+ A, E_inaud_S A/B x {content, plan}   all models
  items/main/mitigation_fs.jsonl    FS on C-T- A/B, C-T+ A x {content, plan}                   four models
  items/main/robustness.jsonl       three alternative system prompts (30 per item)             three models
  items/main/plan_all.jsonl         the first three concatenated: one generation job per model
Each file gets a manifest with counts and SHA-256, as in tools/build_prompts.py.
Usage: python3 tools/build_main_plan.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from oc.build import build_canon, build_item, build_mitigation, build_robustness  # noqa: E402

LANGS = ("zh", "ja", "es")


def write(path: Path, recs: list[dict], sources: list[Path]):
    ids = [r["prompt_id"] for r in recs]
    if len(ids) != len(set(ids)):
        raise SystemExit(f"{path}: duplicate prompt ids")
    data = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in recs)
    path.write_text(data, encoding="utf-8")
    manifest = {"sources": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                "prompts": len(recs), "prompts_sha256": hashlib.sha256(data.encode()).hexdigest(),
                "by_arm": dict(Counter(r["arm"] for r in recs)), "by_lang": dict(Counter(r["lang"] for r in recs)),
                "by_S": dict(Counter(r["S"] for r in recs))}
    path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    print(f"{path.relative_to(ROOT)}: {len(recs)} prompts, sha256 {manifest['prompts_sha256'][:12]}")


def main():
    mpath, rpath, cpath = (ROOT / "items" / "main" / "skeletons.json", ROOT / "items" / "real" / "skeletons.json",
                           ROOT / "items" / "canon" / "subset.json")
    main_items = json.loads(mpath.read_text(encoding="utf-8"))["items"]
    real_items = json.loads(rpath.read_text(encoding="utf-8"))["items"]
    canon = json.loads(cpath.read_text(encoding="utf-8"))["entries"]
    by_id = {it["id"]: it for it in main_items}
    out = ROOT / "items" / "main"
    write(out / "prompts.jsonl", [r for it in main_items for L in LANGS for r in build_item(it, L)], [mpath])
    side = [r for it in real_items for L in LANGS for r in build_item(it, L)]
    side += [r for e in canon for r in build_canon(e, by_id[e["base"]])]
    write(out / "prompts_side.jsonl", side, [rpath, cpath, mpath])
    write(out / "mitigation_m1g.jsonl", [r for it in main_items for L in LANGS for r in build_mitigation(it, L, arms=("M1g",))], [mpath])
    write(out / "mitigation_fs.jsonl", [r for it in main_items for L in LANGS for r in build_mitigation(it, L, arms=("FS",))], [mpath])
    write(out / "robustness.jsonl", [r for it in main_items for L in LANGS for r in build_robustness(it, L)], [mpath])
    allrecs = []
    for name in ("prompts.jsonl", "prompts_side.jsonl", "mitigation_m1g.jsonl"):
        allrecs += [json.loads(l) for l in (out / name).read_text(encoding="utf-8").splitlines()]
    write(out / "plan_all.jsonl", allrecs, [mpath, rpath, cpath])


if __name__ == "__main__":
    main()

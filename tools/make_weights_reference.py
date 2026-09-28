"""Build harness/weights_reference.json from the NPCBank Snellius verification records (read-only).

Sources (NPCBank repo, read-only):
  build/paper-state-delta/snellius-weights/weights-verified.json      (job 27034051, 9/22)
  build/paper-state-delta/snellius-validation/remote-results/weights-verified.json  (Gemma-4-31B, job 27028195)
Only the A-tier models this study uses are kept (proposal 7.1).
Usage: python3 tools/make_weights_reference.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NPC = Path("/Users/xiaozhang/PycharmProjects/NPCBank/build/paper-state-delta")
KEEP = {  # study key -> key in the job-27034051 record
    "qwen38_27b": "qwen38_27b_judge", "qwen35_9b": "qwen9", "qwen35_4b": "qwen4", "qwen35_2b": "qwen2",
    "qwen35_08b": "qwen08", "gemma4_e2b": "gemma4e2b",
}


def main():
    c2 = json.loads((NPC / "snellius-weights" / "weights-verified.json").read_text())
    gem = json.loads((NPC / "snellius-validation" / "remote-results" / "weights-verified.json").read_text())
    models = {}
    for key, src in KEEP.items():
        r = c2[src]
        if r.get("verified") is not True or r.get("mismatched"):
            raise SystemExit(f"{src} is not marked verified")
        models[key] = {"repo": r["repo"], "revision": r["revision"], "scratch_snapshot": r["snapshot"],
                       "source_record": "snellius-weights/weights-verified.json (job 27034051)",
                       "files": {n: {k: v for k, v in f.items() if k in ("bytes", "sha256")} for n, f in r["files"].items()}}
    models["gemma4_31b"] = {"repo": "google/gemma-4-31B-it", "revision": gem["revision"], "scratch_snapshot": gem["snapshot"],
                            "source_record": f"snellius-validation/remote-results/weights-verified.json (job {gem['job_id']})",
                            "files": {n: {"bytes": f["bytes"], "sha256": f["sha256"]} for n, f in gem["files"].items()}}
    out = ROOT / "harness" / "weights_reference.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"version": "oc-weights-reference-1", "models": models}, indent=1) + "\n")
    for k, m in models.items():
        n = len(m["files"])
        h = sum(1 for f in m["files"].values() if f.get("sha256"))
        gib = sum(f["bytes"] for f in m["files"].values()) / 2 ** 30
        print(f"{k:<12} {m['repo']:<28} files={n:<3} with_sha256={h:<3} {gib:6.1f} GiB")


if __name__ == "__main__":
    main()

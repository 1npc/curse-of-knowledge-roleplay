"""Pin new model downloads: revision, file list, sizes and LFS SHA-256 from the Hugging Face API.

Writes harness/downloads.json (read by harness/download_weights.py on a Snellius staging node)
and adds the models to harness/weights_reference.json with their scratch locations.
Only public (ungated) repositories are listed. Uses the system curl (read-only GETs).
Usage: python3 tools/make_download_plan.py [key ...]   (keys given: only those are (re)pinned, the rest is kept)
"""
from __future__ import annotations

import fnmatch
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = "/scratch-shared/qmeng1/over-comprehension/weights"
NEW = {  # key -> (repo, files to skip)
    "gemma4_12b": ("google/gemma-4-12B-it", []),
    "glm47_flash": ("zai-org/GLM-4.7-Flash", []),
    "mistral_small31": ("mistralai/Mistral-Small-3.1-24B-Instruct-2503", ["consolidated*"]),
    "gpt_oss_20b": ("openai/gpt-oss-20b", ["original/*", "metal/*"]),
    "phi4": ("microsoft/phi-4", []),
    "seed_oss_36b": ("ByteDance-Seed/Seed-OSS-36B-Instruct", []),
    "nemotron3_nano30b": ("nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16", []),
    "falcon_h1_34b": ("tiiuae/Falcon-H1-34B-Instruct", []),
    # 9/29: Mistral-Small-3.1 (Mistral3ForConditionalGeneration) does not load in the pinned vLLM/transformers
    # pair (PixtralRotaryEmbedding import error); the text-only Small 3 of the same size replaces it
    "mistral_small3": ("mistralai/Mistral-Small-24B-Instruct-2501", ["consolidated*"]),
}


def api(path: str):
    out = subprocess.run(["curl", "-s", "-m", "60", f"https://huggingface.co/api/{path}"], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def main():
    keys = sys.argv[1:] or list(NEW)
    plan_path = ROOT / "harness" / "downloads.json"
    plan = json.loads(plan_path.read_text()) if sys.argv[1:] and plan_path.exists() else {}
    refs = json.loads((ROOT / "harness" / "weights_reference.json").read_text())
    for key in keys:
        repo, skip = NEW[key]
        meta = api(f"models/{repo}")
        if meta.get("gated"):
            raise SystemExit(f"{repo} is gated; it needs the user's acceptance first")
        rev = meta["sha"]
        tree = api(f"models/{repo}/tree/{rev}?recursive=true")
        files = {}
        for f in tree:
            if f.get("type") != "file" or any(fnmatch.fnmatch(f["path"], p) for p in skip):
                continue
            info = {"bytes": f["size"]}
            if f.get("lfs"):
                info["sha256"] = f["lfs"]["oid"]
            files[f["path"]] = info
        plan[key] = {"repo": repo, "revision": rev, "dest": f"{DEST}/{key}", "ignore": skip, "files": files}
        refs["models"][key] = {"repo": repo, "revision": rev, "scratch_snapshot": f"{DEST}/{key}",
                               "source_record": "Hugging Face API tree at the pinned revision (LFS sha256), 2026-09-28",
                               "files": files}
        gib = sum(v["bytes"] for v in files.values()) / 2 ** 30
        print(f"{key:<18} {repo:<48} rev {rev[:10]}  {len(files):>3} files  {gib:6.1f} GiB")
    (ROOT / "harness" / "downloads.json").write_text(json.dumps(plan, indent=1) + "\n")
    (ROOT / "harness" / "weights_reference.json").write_text(json.dumps(refs, indent=1) + "\n")
    print("total", round(sum(sum(v["bytes"] for v in plan[k]["files"].values()) for k in keys) / 2 ** 30, 1), "GiB")


if __name__ == "__main__":
    main()

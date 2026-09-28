"""Pin new model downloads: revision, file list, sizes and LFS SHA-256 from the Hugging Face API.

Writes harness/downloads.json (read by harness/download_weights.py on a Snellius staging node)
and adds the models to harness/weights_reference.json with their scratch locations.
Only public (ungated) repositories are listed. Uses the system curl (read-only GETs).
Usage: python3 tools/make_download_plan.py
"""
from __future__ import annotations

import fnmatch
import json
import subprocess
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
}


def api(path: str):
    out = subprocess.run(["curl", "-s", "-m", "60", f"https://huggingface.co/api/{path}"], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def main():
    plan, refs = {}, json.loads((ROOT / "harness" / "weights_reference.json").read_text())
    for key, (repo, skip) in NEW.items():
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
    print("total", round(sum(sum(v["bytes"] for v in p["files"].values()) for p in plan.values()) / 2 ** 30, 1), "GiB")


if __name__ == "__main__":
    main()

"""Download pinned model snapshots on a Snellius staging node and verify them (runs with the project venv).

Reads harness/downloads.json (from tools/make_download_plan.py): repository, revision, destination,
skip patterns and every file's size and LFS SHA-256. Downloads with huggingface_hub into plain
directories, then checks every listed file (size always, SHA-256 where recorded) and writes
<weights root>/verification-downloads.json. Exits non-zero on any mismatch.
Usage: python harness/download_weights.py harness/downloads.json [key ...]
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from huggingface_hub import snapshot_download


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def main():
    plan = json.loads(Path(sys.argv[1]).read_text())
    keys = sys.argv[2:] or list(plan)
    report = {"started": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "job": os.environ.get("SLURM_JOB_ID"), "models": {}}
    root = None
    for key in keys:
        p = plan[key]
        dest = Path(p["dest"])
        root = dest.parent
        t = time.time()
        snapshot_download(repo_id=p["repo"], revision=p["revision"], local_dir=str(dest),
                          ignore_patterns=p["ignore"] or None, max_workers=8)
        secs = round(time.time() - t, 1)

        def check(item):
            name, info = item
            f = dest / name
            if not f.is_file():
                return name, "missing"
            if f.stat().st_size != info["bytes"]:
                return name, f"size {f.stat().st_size} != {info['bytes']}"
            if info.get("sha256") and sha256(f) != info["sha256"]:
                return name, "sha256 mismatch"
            return name, "ok"
        with ThreadPoolExecutor(8) as ex:
            res = list(ex.map(check, p["files"].items()))
        bad = [r for r in res if r[1] != "ok"]
        report["models"][key] = {"repo": p["repo"], "revision": p["revision"], "path": str(dest), "files": len(res),
                                 "problems": bad, "download_seconds": secs}
        print(json.dumps({"model": key, "files": len(res), "problems": len(bad), "seconds": secs}), flush=True)
    report["ok"] = all(not m["problems"] for m in report["models"].values())
    report["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    name = "verification-downloads.json" if len(sys.argv) == 2 else f"verification-downloads-{'-'.join(keys)}.json"
    (root / name).write_text(json.dumps(report, indent=1))  # a partial download keeps the earlier full report
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()

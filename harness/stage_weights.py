"""Copy the study's model snapshots and the vLLM venv from scratch to the project space, then verify.

Runs inside a Slurm staging job (harness/stage.sbatch) with the system python3 (3.9, stdlib).
  1. rsync -aL each pinned snapshot into <dst>/weights/<key>/ (symlinks into the shared blob
     store are dereferenced, so every model becomes a plain directory of real files).
  2. Verify every copied file: size against the reference; SHA-256 against the reference where
     the reference records one (all weight shards, all Gemma-4-31B files), byte-for-byte against
     the scratch source otherwise.
  3. rsync -a the venv (symlinks kept) and compare the file lists, sizes and link targets.
The scratch originals are only read. Writes <dst>/weights/verification.json; exits non-zero
on any mismatch.
"""
from __future__ import annotations

import argparse
import filecmp
import hashlib
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor


def sha256(path, bufsize=1 << 24):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(bufsize)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def rsync(src, dst, deref):
    os.makedirs(dst, exist_ok=True)
    cmd = ["rsync", "-aL" if deref else "-a", "--partial", src.rstrip("/") + "/", dst.rstrip("/") + "/"]
    t = time.time()
    subprocess.run(cmd, check=True)
    return round(time.time() - t, 1)


def tree(root):
    """relpath -> (kind, size or link target) for every entry below root."""
    out = {}
    for d, dirs, files in os.walk(root):
        for name in dirs + files:
            p = os.path.join(d, name)
            rel = os.path.relpath(p, root)
            if os.path.islink(p):
                out[rel] = ("link", os.readlink(p))
            elif os.path.isfile(p):
                out[rel] = ("file", os.path.getsize(p))
            elif os.path.isdir(p):
                out[rel] = ("dir", 0)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reference", required=True)
    ap.add_argument("--dst", required=True)
    ap.add_argument("--venv-src", required=True)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    ref = json.load(open(a.reference))["models"]
    report = {"started": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "host": os.uname().nodename,
              "job": os.environ.get("SLURM_JOB_ID"), "models": {}, "venv": {}}
    for key, m in ref.items():
        src = m["scratch_snapshot"]
        if os.path.basename(src.rstrip("/")) != m["revision"]:
            sys.exit(f"{key}: snapshot path is not the pinned revision")
        dst = os.path.join(a.dst, "weights", key)
        report["models"][key] = {"repo": m["repo"], "revision": m["revision"], "path": dst,
                                 "rsync_seconds": rsync(src, dst, deref=True)}
        print(f"copied {key}", flush=True)

    def check(job):
        key, name, info = job
        src = os.path.join(ref[key]["scratch_snapshot"], name)
        dst = os.path.join(a.dst, "weights", key, name)
        if not os.path.isfile(dst) or os.path.islink(dst):
            return key, name, "missing"
        if os.path.getsize(dst) != info["bytes"]:
            return key, name, f"size {os.path.getsize(dst)} != {info['bytes']}"
        if info.get("sha256"):
            got = sha256(dst)
            return key, name, "ok" if got == info["sha256"] else f"sha256 {got} != {info['sha256']}"
        return key, name, "ok" if filecmp.cmp(src, dst, shallow=False) else "content differs from source"

    jobs = [(k, n, f) for k, m in ref.items() for n, f in sorted(m["files"].items())]
    t = time.time()
    with ThreadPoolExecutor(a.workers) as ex:
        results = list(ex.map(check, jobs))
    bad = [r for r in results if r[2] != "ok"]
    for key in ref:
        mine = [r for r in results if r[0] == key]
        listed = set(ref[key]["files"])
        present = set(os.listdir(os.path.join(a.dst, "weights", key)))
        report["models"][key].update({"files_checked": len(mine), "problems": [r[1:] for r in mine if r[2] != "ok"],
                                      "unreferenced_files": sorted(present - listed),
                                      "bytes": sum(ref[key]["files"][n]["bytes"] for n in listed)})
    report["verify_seconds"] = round(time.time() - t, 1)

    vdst = os.path.join(a.dst, "venv")
    report["venv"]["rsync_seconds"] = rsync(a.venv_src, vdst, deref=False)
    s, d = tree(a.venv_src), tree(vdst)
    diff = sorted(set(s.items()) ^ set(d.items()))
    report["venv"].update({"src": a.venv_src, "path": vdst, "entries": len(s),
                           "bytes": sum(v[1] for v in s.values() if v[0] == "file"),
                           "differences": [list(x) for x in diff[:50]], "n_differences": len(diff)})
    report["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    report["ok"] = not bad and not diff
    out = os.path.join(a.dst, "weights", "verification.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=1)
    print(json.dumps({"ok": report["ok"], "problems": len(bad), "venv_differences": len(diff), "report": out}), flush=True)
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()

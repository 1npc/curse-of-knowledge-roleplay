"""Generate replies for one model on one GPU with the vLLM offline engine (BF16, greedy, thinking off).

Adapted from the NPCBank P0 controlled run (build/paper-state-delta/controlled-v1/scripts/generate.py):
same engine settings (vLLM 0.29.0, bfloat16, temperature 0, top_p 1, seed 20260916, enforce_eager,
no prefix cache, max_num_seqs 256) and the same immutability rules, with three changes for this
study: the input is the prompt plan written by tools/build_prompts.py; max_new_tokens is 400
(proposal 7.2); results are written per chunk of prompts instead of per prompt, to keep file
counts low on GPFS.

Every prompt is rendered once with the pinned tokenizer's chat template (thinking disabled through
chat_template_kwargs) and the exact token ids are what vLLM receives, so the hashed prompt is the
executed prompt. A chunk's intent is written before generation and its result after; a chunk with
an intent and no result is recorded as interrupted_uncertain and not resent unless
--retry-interrupted is given (greedy offline decoding costs nothing, but the attempt is logged).
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

PROTOCOL = {"temperature": 0.0, "top_p": 1.0, "seed": 20260916, "max_output_tokens": 400, "max_model_len": 8192,
            "dtype": "bfloat16", "enforce_eager": True, "prefix_caching": False, "max_num_seqs": 256,
            "gpu_memory_utilization": 0.85, "tensor_parallel_size": 1, "thinking": "disabled via chat template",
            "retry": "none; a chunk with an intent but no result is recorded as interrupted_uncertain"}
REASONING_MARKERS = ("<think>", "</think>", "<|think|>", "<|channel>", "<channel|>", "<|channel|>", "thought\n<channel")


def canonical(x) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(x) -> str:
    return hashlib.sha256(canonical(x).encode()).hexdigest()


def text_sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def file_sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def write_immutable(path: Path, text: str):
    """Create a file once; refuse to overwrite different content."""
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise RuntimeError(f"refusing to overwrite {path}")
        return
    tmp = path.with_suffix(path.suffix + f".tmp{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def status_of(text: str, finish: str | None) -> str:
    if finish == "length":
        return "truncated"
    if finish != "stop":
        return "unexpected_finish"
    if not text.strip():
        return "empty"
    if any(m in text for m in REASONING_MARKERS):
        return "unexpected_reasoning"
    return "complete"


def locate(key: str, location: str, oc: Path, reference: dict) -> Path:
    ref = reference["models"][key]
    path = Path(ref["scratch_snapshot"]) if location == "scratch" else oc / "weights" / key
    if not path.is_dir():
        raise SystemExit(f"{key}: weights not found at {path}")
    if location == "project":
        ver = json.loads((oc / "weights" / "verification.json").read_text())
        if not ver.get("ok") or ver["models"].get(key, {}).get("problems"):
            raise SystemExit(f"{key}: project copy is not verified (weights/verification.json)")
    for name, info in ref["files"].items():  # fast check every run; full hashes were checked when staged
        size = (path / name).stat().st_size
        if size != info["bytes"]:
            raise SystemExit(f"{key}: {name} has {size} bytes, reference {info['bytes']}")
    return path


def gpu_info() -> dict:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=uuid,name,memory.total,driver_version", "--format=csv,noheader"],
                             capture_output=True, text=True, check=True).stdout.strip()
        return {"nvidia_smi": out.splitlines()}
    except Exception as e:  # noqa: BLE001
        return {"error": repr(e)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", type=Path, required=True)
    ap.add_argument("--subset", type=Path, help="file with one prompt_id per line")
    ap.add_argument("--model", required=True)
    ap.add_argument("--models", type=Path, required=True)
    ap.add_argument("--reference", type=Path, required=True)
    ap.add_argument("--location", choices=("project", "scratch"), default="project")
    ap.add_argument("--out", type=Path, required=True, help="run directory; results go to <out>/<model>/")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--chunk", type=int, default=512)
    ap.add_argument("--retry-interrupted", action="store_true")
    a = ap.parse_args()

    oc = Path(os.environ.get("OC", "/gpfs/work4/0/prjs1226/qmeng1/over-comprehension"))
    spec = json.loads(a.models.read_text())["models"][a.model]
    reference = json.loads(a.reference.read_text())
    path = locate(a.model, a.location, oc, reference)

    prompts = [json.loads(l) for l in a.prompts.read_text(encoding="utf-8").splitlines() if l.strip()]
    if a.subset:
        keep = {l.strip() for l in a.subset.read_text().splitlines() if l.strip()}
        prompts = [p for p in prompts if p["prompt_id"] in keep]
        if len(prompts) != len(keep):
            raise SystemExit("subset names prompt ids that are not in the plan")
    prompts.sort(key=lambda p: p["prompt_id"])

    out = a.out / a.model
    (out / "chunks").mkdir(parents=True, exist_ok=True)
    lock = (out / "run.lock").open("a+")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)

    import torch
    import transformers
    import vllm
    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams
    from vllm.inputs import TokensPrompt

    tok = AutoTokenizer.from_pretrained(str(path), trust_remote_code=False)
    if not tok.chat_template:
        raise SystemExit("pinned tokenizer has no chat template")
    kwargs = spec.get("chat_template_kwargs", {})
    frozen = {"version": "oc-generation-1", "model": a.model, "repo": spec["repo"],
              "revision": reference["models"][a.model]["revision"], "weights_path": str(path), "location": a.location,
              "chat_template_sha256": text_sha(tok.chat_template), "chat_template_kwargs": kwargs,
              "engine": {"vllm": vllm.__version__, "torch": torch.__version__, "transformers": transformers.__version__},
              "protocol": PROTOCOL, "prompts_file": str(a.prompts), "prompts_sha256": file_sha(a.prompts),
              "subset_sha256": file_sha(a.subset) if a.subset else None, "n_prompts": len(prompts),
              "runner_sha256": file_sha(Path(__file__)), "chunk": a.chunk}
    run_sha = digest(frozen)
    write_immutable(out / "run.json", json.dumps(frozen, indent=1) + "\n")
    state = {"run_id": a.run_id, "run_sha256": run_sha, "host": socket.gethostname(), "gpu": gpu_info(),
             "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"), "slurm_job": os.environ.get("SLURM_JOB_ID"),
             "started": now()}

    # render every prompt once; the token ids are what the engine receives
    rendered = {}
    notes = Counter()
    for p in prompts:
        msgs = p["messages"]
        try:
            text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, **kwargs)
        except Exception as e:  # a template without a system role: fold it into the first user turn, and record that
            if msgs and msgs[0]["role"] == "system" and "system" in str(e).lower():
                merged = [{"role": "user", "content": msgs[0]["content"] + "\n\n" + msgs[1]["content"]}] + msgs[2:]
                text = tok.apply_chat_template(merged, tokenize=False, add_generation_prompt=True, **kwargs)
                notes["system_folded_into_user"] += 1
            else:
                raise
        ids = tok.encode(text, add_special_tokens=False)
        rendered[p["prompt_id"]] = (text, ids)
    too_long = {pid for pid, (_, ids) in rendered.items()
                if len(ids) + PROTOCOL["max_output_tokens"] > PROTOCOL["max_model_len"]}

    t_load = time.time()
    llm = LLM(model=str(path), tokenizer=str(path), dtype="bfloat16", max_model_len=PROTOCOL["max_model_len"],
              seed=PROTOCOL["seed"], enable_prefix_caching=False, enforce_eager=True,
              gpu_memory_utilization=PROTOCOL["gpu_memory_utilization"], tensor_parallel_size=1,
              trust_remote_code=False, max_num_seqs=PROTOCOL["max_num_seqs"])
    sampling = SamplingParams(temperature=0.0, top_p=1.0, seed=PROTOCOL["seed"],
                              max_tokens=PROTOCOL["max_output_tokens"], skip_special_tokens=True)
    state.update(load_seconds=round(time.time() - t_load, 1), sampling=repr(sampling), notes=dict(notes))
    (out / f"runtime-{a.run_id}.json").write_text(json.dumps({**state, "status": "generating"}, indent=1))

    t_gen = time.time()
    for ci in range(0, len(prompts), a.chunk):
        chunk = prompts[ci:ci + a.chunk]
        cid = f"chunk-{ci // a.chunk:04d}"
        ids_in_chunk = [p["prompt_id"] for p in chunk]
        binding = {"run_sha256": run_sha, "chunk": cid, "prompt_ids_sha256": digest(ids_in_chunk)}
        res_path, int_path = out / "chunks" / f"{cid}.jsonl", out / "chunks" / f"{cid}.intent.json"
        if res_path.exists():
            continue
        if int_path.exists() and not a.retry_interrupted:
            marker = out / "chunks" / f"{cid}.interrupted.json"
            if not marker.exists():
                write_immutable(marker, json.dumps({"binding": binding, "status": "interrupted_uncertain", "recorded": now()}))
            continue
        attempt = "retry" if int_path.exists() else "first"
        write_immutable(int_path if attempt == "first" else out / "chunks" / f"{cid}.retry-intent.json",
                        json.dumps({"binding": binding, "started": now(), "run_id": a.run_id}))
        todo = [p for p in chunk if p["prompt_id"] not in too_long]
        t0 = time.time()
        outputs = llm.generate([TokensPrompt(prompt_token_ids=rendered[p["prompt_id"]][1]) for p in todo],
                               sampling, use_tqdm=False) if todo else []
        dt = time.time() - t0
        if len(outputs) != len(todo):
            raise RuntimeError("engine returned a different number of outputs")
        by_id = {p["prompt_id"]: o for p, o in zip(todo, outputs)}
        lines = []
        for p in chunk:
            pid = p["prompt_id"]
            text_r, ids = rendered[pid]
            rec = {"prompt_id": pid, "model": a.model, "run_sha256": run_sha, "chunk": cid, "attempt": attempt,
                   "prompt_tokens": len(ids), "rendered_sha256": text_sha(text_r), "token_ids_sha256": digest(ids)}
            if pid in too_long:
                rec.update(status="context_overflow")
            else:
                o = by_id[pid]
                comp = o.outputs[0]
                st = status_of(comp.text, comp.finish_reason)
                if list(o.prompt_token_ids) != ids:
                    st = "tokenization_mismatch"
                rec.update(status=st, text=comp.text, text_sha256=text_sha(comp.text), finish_reason=comp.finish_reason,
                           stop_reason=repr(comp.stop_reason), output_tokens=len(comp.token_ids),
                           output_token_ids_sha256=digest(list(comp.token_ids)))
            lines.append(canonical(rec))
        write_immutable(res_path, "\n".join(lines) + "\n")
        print(canonical({"chunk": cid, "n": len(chunk), "seconds": round(dt, 1),
                         "status": dict(Counter(json.loads(l)["status"] for l in lines))}), flush=True)

    # merge (sorted, deterministic) and summarize
    recs = []
    for f in sorted((out / "chunks").glob("chunk-*.jsonl")):
        recs += [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    recs.sort(key=lambda r: r["prompt_id"])
    data = "".join(canonical(r) + "\n" for r in recs)
    (out / "responses.jsonl").write_text(data, encoding="utf-8")
    summary = {"model": a.model, "run_sha256": run_sha, "records": len(recs), "planned": len(prompts),
               "status": dict(Counter(r["status"] for r in recs)), "responses_sha256": text_sha(data),
               "interrupted_chunks": len(list((out / "chunks").glob("*.interrupted.json"))),
               "generation_seconds": round(time.time() - t_gen, 1), "run_id": a.run_id, "finished": now()}
    (out / f"summary-{a.run_id}.json").write_text(json.dumps(summary, indent=1) + "\n")
    (out / f"runtime-{a.run_id}.json").write_text(json.dumps({**state, "status": "finished", "summary": summary}, indent=1))
    print(canonical(summary), flush=True)


if __name__ == "__main__":
    main()

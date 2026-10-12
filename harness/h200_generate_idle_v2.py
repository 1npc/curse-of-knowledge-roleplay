"""Generate replies for one model on one GPU with the vLLM offline engine (BF16, greedy, thinking off).

Adapted from the NPCBank P0 controlled run (build/paper-state-delta/controlled-v1/scripts/generate.py):
same engine settings (vLLM 0.29.0, bfloat16, temperature 0, top_p 1, seed 20261001, enforce_eager,
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
import re
import socket
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # code root, for oc.build (standard library only)

PROTOCOL = {"temperature": 0.0, "top_p": 1.0, "seed": 20261001, "max_output_tokens": 400, "max_model_len": 8192,
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
    entry = json.loads((oc / "operations" / "weights-verified.json").read_text())["models"][key]
    if not entry.get("ok") or entry.get("revision") != ref["revision"]:
        raise SystemExit(f"{key}: exact-revision file verification is missing")
    path = Path(entry["path"])
    for name, info in ref["files"].items():
        if not (path/name).exists() or (path/name).stat().st_size != info["bytes"]:
            raise SystemExit(f"{key}: missing/size-mismatched file {name}")
    return path


HARMONY_FINAL = re.compile(r"<\|channel\|>final<\|message\|>(.*?)(?:<\|return\|>|<\|end\|>|$)", re.S)
HARMONY_ANALYSIS = re.compile(r"<\|channel\|>analysis<\|message\|>(.*?)(?:<\|end\|>|$)", re.S)


def parse_harmony(raw: str) -> tuple[str | None, str]:
    """gpt-oss answers in channels: return (final text or None, analysis text)."""
    m = HARMONY_FINAL.search(raw)
    return (m.group(1).strip() if m else None), "\n".join(x.strip() for x in HARMONY_ANALYSIS.findall(raw))


def gpu_info() -> dict:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=uuid,name,memory.total,driver_version", "--format=csv,noheader"],
                             capture_output=True, text=True, check=True).stdout.strip()
        return {"nvidia_smi": out.splitlines()}
    except Exception as e:  # noqa: BLE001
        return {"error": repr(e)}


ALLOWED_GPU = {'0': 'GPU-eac35845-029e-df8d-5318-af5d76434077', '1': 'GPU-9c1c0f75-f324-fa5f-eb4c-0eea4430711d', '2': 'GPU-aa894bfe-9735-49ef-b927-3976eb8b9b81', '3': 'GPU-cc260ef9-4a13-a1a9-3692-a076fb1a1d0b', '4': 'GPU-5138e53e-9416-9f95-6ba1-88b2031e57a0', '5': 'GPU-63686987-a70f-607d-9886-af187b67a14a', '6': 'GPU-18a3d1e0-628c-7817-3018-0844b06e30c9', '7': 'GPU-00ecc257-2646-98af-1e10-3b94f6004c00'}


def validate_gpu():
    physical = os.environ.get("OC_PHYSICAL_GPU")
    if physical not in ALLOWED_GPU or os.environ.get("CUDA_VISIBLE_DEVICES") != ALLOWED_GPU[physical]:
        raise SystemExit("Only a verified, authorized physical H200 GPU UUID may be visible")
    rows = subprocess.check_output(["nvidia-smi", "--query-gpu=index,uuid,memory.used,utilization.gpu", "--format=csv,noheader,nounits"], text=True)
    row = next(x.split(", ") for x in rows.splitlines() if x.startswith(physical+", "))
    apps = subprocess.check_output(["nvidia-smi", "--query-compute-apps=gpu_uuid", "--format=csv,noheader"], text=True)
    if row[1] != ALLOWED_GPU[physical] or ALLOWED_GPU[physical] in apps or float(row[2]) > 100 or float(row[3]) > 5:
        raise SystemExit("Authorized GPU is occupied or its identity changed; do not share or terminate other processes")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", type=Path, required=True)
    ap.add_argument("--subset", type=Path, help="file with one prompt_id per line")
    ap.add_argument("--model", required=True)
    ap.add_argument("--models", type=Path, required=True)
    ap.add_argument("--reference", type=Path, required=True)
    ap.add_argument("--location", choices=("auto", "project", "scratch"), default="auto")
    ap.add_argument("--out", type=Path, required=True, help="run directory; results go to <out>/<model>/")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--chunk", type=int, default=512)
    ap.add_argument("--retry-interrupted", action="store_true")
    a = ap.parse_args()

    oc = Path(os.environ.get("OC", "/data/qianru/over-comprehension-v2-20261001"))
    validate_gpu()
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

    tspec = spec.get("tokenizer", {})
    if tspec.get("class") == "fast":  # Mistral-Small-3: AutoTokenizer gives the mistral-common backend, which has no
        from transformers import PreTrainedTokenizerFast  # Jinja template; the fast tokenizer's ids were checked
        tok = PreTrainedTokenizerFast.from_pretrained(str(path), **tspec.get("kwargs", {}))  # equal to it (9/29)
    else:
        tok = AutoTokenizer.from_pretrained(str(path), trust_remote_code=False)
    template_source = "tokenizer"
    if not tok.chat_template and (path / "chat_template.json").exists():  # e.g. Mistral-Small-3.1 keeps it with the processor
        tok.chat_template = json.loads((path / "chat_template.json").read_text())["chat_template"]
        template_source = "chat_template.json"
    if spec.get("template_fixed_date"):  # a template that stamps today's date would make renders depend on the run day
        tok.chat_template = tok.chat_template.replace('strftime_now("%Y-%m-%d")', json.dumps(spec["template_fixed_date"]))
        template_source += f", date fixed to {spec['template_fixed_date']}"
    if not tok.chat_template:
        raise SystemExit("pinned tokenizer has no chat template")
    kwargs = spec.get("chat_template_kwargs", {})
    frozen = {"version": "oc-generation-access-v2", "model": a.model, "repo": spec["repo"],
              "revision": reference["models"][a.model]["revision"], "weights_path": str(path), "location": a.location,
              "chat_template_sha256": text_sha(tok.chat_template), "chat_template_source": template_source, "tokenizer": tspec or "auto",
              "chat_template_kwargs": kwargs,
              "engine": {"vllm": vllm.__version__, "torch": torch.__version__, "transformers": transformers.__version__},
              "protocol": PROTOCOL, "prompts_file": str(a.prompts), "prompts_sha256": file_sha(a.prompts),
              "subset_sha256": file_sha(a.subset) if a.subset else None, "n_prompts": len(prompts),
              "runner_sha256": file_sha(Path(__file__)), "chunk": a.chunk}
    run_sha = digest(frozen)
    write_immutable(out / "run.json", json.dumps(frozen, indent=1) + "\n")
    state = {"run_id": a.run_id, "run_sha256": run_sha, "host": socket.gethostname(), "gpu": gpu_info(),
             "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"), "slurm_job": os.environ.get("SLURM_JOB_ID"),
             "started": now()}

    notes = Counter()

    def render(msgs):
        try:
            text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, **kwargs)
        except Exception as e:  # a template without a system role: fold it into the first user turn, and record that
            if msgs and msgs[0]["role"] == "system" and "system" in str(e).lower():
                merged = [{"role": "user", "content": msgs[0]["content"] + "\n\n" + msgs[1]["content"]}] + msgs[2:]
                text = tok.apply_chat_template(merged, tokenize=False, add_generation_prompt=True, **kwargs)
                notes["system_folded_into_user"] += 1
            else:
                raise
        return text, tok.encode(text, add_special_tokens=False)

    # render every prompt once; the token ids are what the engine receives
    rendered = {p["prompt_id"]: render(p["messages"]) for p in prompts}

    t_load = time.time()
    llm = LLM(model=str(path), tokenizer=str(path), dtype="bfloat16", max_model_len=PROTOCOL["max_model_len"],
              seed=PROTOCOL["seed"], enable_prefix_caching=False, enforce_eager=True,
              gpu_memory_utilization=PROTOCOL["gpu_memory_utilization"], tensor_parallel_size=1,
              trust_remote_code=False, max_num_seqs=PROTOCOL["max_num_seqs"])
    harmony = spec.get("output_parser") == "harmony"  # keep channel markers so the final answer can be separated
    sampling = SamplingParams(temperature=0.0, top_p=1.0, seed=PROTOCOL["seed"],
                              max_tokens=PROTOCOL["max_output_tokens"], skip_special_tokens=not harmony)
    state.update(load_seconds=round(time.time() - t_load, 1), sampling=repr(sampling))
    (out / f"runtime-{a.run_id}.json").write_text(json.dumps({**state, "status": "generating"}, indent=1))

    def run_pass(prefix, batch, rend, step):
        too_long = {pid for pid, (_, ids) in rend.items() if len(ids) + PROTOCOL["max_output_tokens"] > PROTOCOL["max_model_len"]}
        for ci in range(0, len(batch), a.chunk):
            chunk = batch[ci:ci + a.chunk]
            cid = f"{prefix}-{ci // a.chunk:04d}"
            ids_in_chunk = [p["prompt_id"] for p in chunk]
            binding = {"run_sha256": run_sha, "chunk": cid, "prompt_ids_sha256": digest(ids_in_chunk),
                       "messages_sha256": digest([p["messages"] for p in chunk])}
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
            outputs = llm.generate([TokensPrompt(prompt_token_ids=rend[p["prompt_id"]][1]) for p in todo],
                                   sampling, use_tqdm=False) if todo else []
            dt = time.time() - t0
            if len(outputs) != len(todo):
                raise RuntimeError("engine returned a different number of outputs")
            by_id = {p["prompt_id"]: o for p, o in zip(todo, outputs)}
            lines = []
            for p in chunk:
                pid = p["prompt_id"]
                text_r, ids = rend[pid]
                rec = {"prompt_id": pid, "model": a.model, "run_sha256": run_sha, "chunk": cid, "attempt": attempt, "step": step,
                       "prompt_tokens": len(ids), "rendered_sha256": text_sha(text_r), "token_ids_sha256": digest(ids)}
                if step == 2:
                    rec["messages"] = p["messages"]  # built from the step-1 output, so it is kept with the result
                if pid in too_long:
                    rec.update(status="context_overflow")
                else:
                    o = by_id[pid]
                    comp = o.outputs[0]
                    text = comp.text
                    if harmony:
                        final, analysis = parse_harmony(comp.text)
                        rec.update(raw_text=comp.text, reasoning=analysis)
                        text = final if final is not None else ""
                        st = status_of(text, comp.finish_reason) if final is not None else (
                            "truncated" if comp.finish_reason == "length" else "no_final")
                    else:
                        st = status_of(text, comp.finish_reason)
                    if list(o.prompt_token_ids) != ids:
                        st = "tokenization_mismatch"
                    rec.update(status=st, text=text, text_sha256=text_sha(text), finish_reason=comp.finish_reason,
                               stop_reason=repr(comp.stop_reason), output_tokens=len(comp.token_ids),
                               output_token_ids_sha256=digest(list(comp.token_ids)))
                lines.append(canonical(rec))
            write_immutable(res_path, "\n".join(lines) + "\n")
            print(canonical({"chunk": cid, "n": len(chunk), "seconds": round(dt, 1),
                             "status": dict(Counter(json.loads(l)["status"] for l in lines))}), flush=True)

    t_gen = time.time()
    run_pass("chunk", prompts, rendered, 1)

    # second steps (M1 perspective filtering): built from the step-1 outputs, then generated in their own chunks
    two = [p for p in prompts if p.get("next_step")]
    if two:
        from oc.build import fill_next_step
        step1 = {}
        for f in sorted((out / "chunks").glob("chunk-*.jsonl")):
            for l in f.read_text(encoding="utf-8").splitlines():
                if l.strip():
                    r = json.loads(l)
                    step1[r["prompt_id"]] = r
        second, skipped = [], []
        for p in two:
            r1 = step1.get(p["prompt_id"])
            if r1 and r1["status"] in ("complete", "truncated"):
                second.append({"prompt_id": p["prompt_id"] + "#2", "messages": fill_next_step(p, r1["text"])})
            else:
                skipped.append(p["prompt_id"])
        if skipped:
            write_immutable(out / "chunks" / "s2-skipped.json", json.dumps({"step1_not_usable": skipped}))
        run_pass("s2chunk", second, {q["prompt_id"]: render(q["messages"]) for q in second}, 2)

    # merge (sorted, deterministic) and summarize
    recs = []
    for f in sorted((out / "chunks").glob("*chunk-*.jsonl")):
        recs += [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    recs.sort(key=lambda r: r["prompt_id"])
    data = "".join(canonical(r) + "\n" for r in recs)
    (out / "responses.jsonl").write_text(data, encoding="utf-8")
    summary = {"model": a.model, "run_sha256": run_sha, "records": len(recs),
               "planned": len(prompts) + sum(1 for p in prompts if p.get("next_step")),
               "status": dict(Counter(r["status"] for r in recs)), "responses_sha256": text_sha(data),
               "interrupted_chunks": len(list((out / "chunks").glob("*.interrupted.json"))),
               "generation_seconds": round(time.time() - t_gen, 1), "notes": dict(notes), "run_id": a.run_id,
               "finished": now()}
    (out / f"summary-{a.run_id}.json").write_text(json.dumps(summary, indent=1) + "\n")
    (out / f"runtime-{a.run_id}.json").write_text(json.dumps({**state, "status": "finished", "summary": summary}, indent=1))
    print(canonical(summary), flush=True)


if __name__ == "__main__":
    main()

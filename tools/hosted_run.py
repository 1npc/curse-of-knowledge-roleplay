"""Run a prompt plan on a hosted model through OpenRouter with a hard spending cap (added 10/8).

The key is read from the macOS keychain item "NPCBank OpenRouter API Key 3" and passed to curl on
stdin, so it never appears in arguments, files or output. Each reply is appended to
<out>/<model_key>/responses.jsonl with the provider, token usage and the cost OpenRouter reports;
finished prompt ids are skipped on a rerun. Before every request the script checks the shared ledger
(<out>/ledger.json): it stops when the cost spent by this run plus a per-request reserve would pass
the global cap, or the model's own cap.
Usage: python3 tools/hosted_run.py --plan P.jsonl [--plan Q.jsonl] --model openai/gpt-6-sol --key-name gpt6sol
       --out runs/hosted-1008 --model-cap 12 --global-cap 57 [--limit 30] [--workers 16]
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
import subprocess
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

KEYCHAIN = "NPCBank OpenRouter API Key 3"
URL = "https://openrouter.ai/api/v1/chat/completions"
# Decoding per model: temperature only where the endpoint supports it; reasoning as low as allowed.
SETTINGS = {
    "openai/gpt-6-sol": {"reasoning": {"effort": "minimal"}, "max_tokens": 1200},
    "anthropic/claude-opus-5.5": {"reasoning": {"effort": "low"}, "max_tokens": 1500},
    "anthropic/claude-sonnet-5.5": {"reasoning": {"effort": "low"}, "max_tokens": 1500},
    "google/gemini-3.1-pro-preview": {"temperature": 0, "seed": 20261008, "reasoning": {"max_tokens": 128}, "max_tokens": 1000},
    "google/gemini-3.8-flash": {"temperature": 0, "seed": 20261008, "reasoning": {"effort": "minimal"}, "max_tokens": 1000},
    "x-ai/grok-4.7": {"temperature": 0, "seed": 20261008, "reasoning": {"effort": "low"}, "max_tokens": 1200},
    "deepseek/deepseek-v4-pro": {"temperature": 0, "reasoning": {"enabled": False}, "max_tokens": 400,
                                 "provider": {"order": ["StreamLake"], "allow_fallbacks": False}},
}
lock = threading.Lock()


def key() -> str:
    return subprocess.run(["security", "find-generic-password", "-s", KEYCHAIN, "-w"], capture_output=True, text=True, check=True).stdout.strip()


def call(k: str, body: dict) -> dict:
    """POST one request. The key goes to curl as a config on stdin; the body (prompts only) via a temp file."""
    cfg = f'header = "Authorization: Bearer {k}"\nheader = "Content-Type: application/json"\n'
    with tempfile.NamedTemporaryFile("w", suffix=".json") as f:
        json.dump(body, f)
        f.flush()
        p = subprocess.run(["curl", "-s", "-m", "300", "-K", "-", "--data-binary", f"@{f.name}", URL], input=cfg, capture_output=True, text=True)
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"error": {"message": f"non-JSON response (curl exit {p.returncode}): {p.stdout[:200]}"}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", type=Path, action="append", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--key-name", required=True, help="directory name for this model's outputs")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--model-cap", type=float, required=True)
    ap.add_argument("--global-cap", type=float, required=True)
    ap.add_argument("--limit", type=int, default=0, help="run only this many prompts (random, fixed seed) for a cost pilot")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--reserve", type=float, default=0.05, help="dollars held back per in-flight request")
    a = ap.parse_args()
    prompts = [json.loads(l) for p in a.plan for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    if a.limit:
        prompts = random.Random(20261008).sample(prompts, a.limit)
    out = a.out / a.key_name
    out.mkdir(parents=True, exist_ok=True)
    resp_path, ledger_path = out / "responses.jsonl", out / "ledger.json"  # one ledger per model; caps of parallel runs must sum below the global cap
    done = {json.loads(l)["prompt_id"] for l in resp_path.read_text().splitlines()} if resp_path.exists() else set()
    todo = [p for p in prompts if p["prompt_id"] not in done]
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {"models": {}}
    ledger["models"].setdefault(a.key_name, 0.0)
    reserve = a.reserve
    k = key()
    spec = dict(SETTINGS[a.model])
    stop = threading.Event()
    inflight = [0]
    print(f"{a.model}: {len(todo)} to run ({len(done)} done); spent so far {ledger['models'][a.key_name]:.3f} of {a.model_cap}, "
          f"run total {sum(ledger['models'].values()):.3f} of {a.global_cap}", flush=True)

    cache = {}

    def others_spent():  # other runs' ledgers; a file caught mid-write keeps its last good value
        total = 0.0
        files = [f for f in a.out.glob("*/ledger.json") if f.parent.name != a.key_name] + [a.out / "ledger.json"]
        for f in files:
            try:
                cache[f] = sum(json.loads(f.read_text())["models"].values())
            except (OSError, ValueError, KeyError):
                pass
            total += cache.get(f, 0.0)
        return total

    def work(p):
        if stop.is_set():
            return
        with lock:
            spent = others_spent() + ledger["models"][a.key_name]
            if spent + reserve * (inflight[0] + 1) > a.global_cap or ledger["models"][a.key_name] + reserve * (inflight[0] + 1) > a.model_cap:
                stop.set()
                return
            inflight[0] += 1
        body = {"model": a.model, "messages": p["messages"], "usage": {"include": True}, **spec}
        for attempt in range(4):
            r = call(k, body)
            err = r.get("error")
            if not err:
                break
            time.sleep(2 ** attempt * 3)
        ch = (r.get("choices") or [{}])[0]
        u = r.get("usage") or {}
        cost = float(u.get("cost") or 0.0)
        msg = ch.get("message") or {}
        rec = {"prompt_id": p["prompt_id"], "model": a.key_name, "openrouter_model": r.get("model", a.model), "provider": r.get("provider"),
               "text": msg.get("content"), "finish_reason": ch.get("finish_reason"), "status": "error" if r.get("error") else
               ("complete" if ch.get("finish_reason") in ("stop", "end_turn") and msg.get("content") else "truncated" if ch.get("finish_reason") == "length" else "other"),
               "step": 1, "usage": u, "cost": cost, "error": (r.get("error") or {}).get("message"), "settings": spec, "time": time.strftime("%Y-%m-%dT%H:%M:%S")}
        with lock:
            inflight[0] -= 1
            ledger["models"][a.key_name] += cost
            with open(resp_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            tmp = ledger_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(ledger, indent=1))
            tmp.replace(ledger_path)

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(work, todo))
    rows = [json.loads(l) for l in resp_path.read_text().splitlines()] if resp_path.exists() else []
    print(f"{a.model}: {len(rows)} replies {dict(Counter(r['status'] for r in rows))}; model spent {ledger['models'][a.key_name]:.3f}; "
          f"run total {sum(ledger['models'].values()):.3f}" + ("; STOPPED at cap" if stop.is_set() else ""), flush=True)


if __name__ == "__main__":
    main()

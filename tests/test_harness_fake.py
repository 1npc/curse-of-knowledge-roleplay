"""Dry run of harness/generate.py with fake torch/transformers/vLLM modules (standard library only).

Exercises the chunked first pass, the M1 second pass built from step-1 outputs, the merge,
and the immutability of result files, without a GPU.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAKES = {
    "torch/__init__.py": '__version__ = "fake-torch"\n',
    "transformers/__init__.py": textwrap.dedent('''
        __version__ = "fake-transformers"
        class _Tok:
            chat_template = "fake-template"
            def apply_chat_template(self, msgs, tokenize=False, add_generation_prompt=True, **kw):
                return "".join(f"<{m['role']}>{m['content']}" for m in msgs) + "<assistant>"
            def encode(self, text, add_special_tokens=False):
                return [ord(c) % 997 for c in text]
        class AutoTokenizer:
            @staticmethod
            def from_pretrained(path, trust_remote_code=False):
                return _Tok()
        '''),
    "vllm/__init__.py": textwrap.dedent('''
        __version__ = "fake-vllm"
        class SamplingParams:
            def __init__(self, **kw): self.kw = kw
            def __repr__(self): return f"SamplingParams({self.kw})"
        class _Comp:
            def __init__(self, text): self.text, self.finish_reason, self.stop_reason, self.token_ids = text, "stop", None, [1, 2, 3]
        class _Out:
            def __init__(self, ids, text): self.prompt_token_ids, self.outputs = ids, [_Comp(text)]
        class LLM:
            def __init__(self, **kw): pass
            def generate(self, prompts, sampling, use_tqdm=False):
                out = []
                for p in prompts:
                    ids = p["prompt_token_ids"]
                    text = "".join(chr(i) for i in ids if i < 997)
                    if "List only what" in text:
                        reply = 'Kerry hears someone speaking a language he does not understand; "no words" come through.'
                    elif "hears someone speaking a language" in text:
                        reply = "No idea what they said, V."
                    else:
                        reply = "Couldn't tell you."
                    out.append(_Out(ids, reply))
                return out
        '''),
    "vllm/inputs.py": "def TokensPrompt(prompt_token_ids):\n    return {'prompt_token_ids': prompt_token_ids}\n",
}


class TestHarmony(unittest.TestCase):
    def test_parse(self):
        sys.path.insert(0, str(ROOT / "harness"))
        from generate import parse_harmony
        raw = ("<|channel|>analysis<|message|>The character does not understand Spanish.<|end|>"
               "<|start|>assistant<|channel|>final<|message|>No idea what he said, V.<|return|>")
        final, analysis = parse_harmony(raw)
        self.assertEqual(final, "No idea what he said, V.")
        self.assertIn("does not understand", analysis)
        self.assertEqual(parse_harmony("<|channel|>analysis<|message|>still thinking")[0], None)


class TestHarnessDryRun(unittest.TestCase):
    def test_two_pass_m1(self):
        from oc.build import build_mitigation
        items = json.loads((ROOT / "items" / "pilot" / "skeletons.json").read_text(encoding="utf-8"))["items"]
        with tempfile.TemporaryDirectory(prefix="oc-harness-") as tmp:
            tmp = Path(tmp)
            for rel, src in FAKES.items():
                (tmp / "fakes" / rel).parent.mkdir(parents=True, exist_ok=True)
                (tmp / "fakes" / rel).write_text(src)
            weights = tmp / "weights" / "rev1"
            weights.mkdir(parents=True)
            (weights / "config.json").write_text("{}")
            ref = {"models": {"fake": {"repo": "x/y", "revision": "rev1", "scratch_snapshot": str(weights),
                                       "files": {"config.json": {"bytes": 2}}}}}
            (tmp / "ref.json").write_text(json.dumps(ref))
            (tmp / "models.json").write_text(json.dumps({"models": {"fake": {"repo": "x/y", "chat_template_kwargs": {}}}}))
            recs = build_mitigation(items[0], "ja") + build_mitigation(items[5], "es")
            (tmp / "prompts.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
            cmd = [sys.executable, str(ROOT / "harness" / "generate.py"), "--prompts", str(tmp / "prompts.jsonl"),
                   "--model", "fake", "--models", str(tmp / "models.json"), "--reference", str(tmp / "ref.json"),
                   "--location", "scratch", "--out", str(tmp / "run"), "--run-id", "dry", "--chunk", "5"]
            env = dict(os.environ, PYTHONPATH=str(tmp / "fakes"), PYTHONDONTWRITEBYTECODE="1")
            p = subprocess.run(cmd, env=env, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr[-2000:])
            out = [json.loads(l) for l in (tmp / "run" / "fake" / "responses.jsonl").read_text(encoding="utf-8").splitlines()]
            n_m1 = sum("next_step" in r for r in recs)  # M1 and M1g are two-step
            self.assertEqual(len(out), len(recs) + n_m1)
            step2 = [r for r in out if r["step"] == 2]
            self.assertEqual(len(step2), n_m1)
            for r in step2:
                self.assertEqual(r["text"], "No idea what they said, V.")  # the fake saw the step-1 text in the state
                self.assertIn("hears someone speaking a language", r["messages"][0]["content"])
            # a rerun reuses every finished chunk and changes nothing
            before = (tmp / "run" / "fake" / "responses.jsonl").read_text(encoding="utf-8")
            p2 = subprocess.run(cmd[:-4] + ["--run-id", "dry2", "--chunk", "5"], env=env, capture_output=True, text=True)
            self.assertEqual(p2.returncode, 0, p2.stderr[-2000:])
            self.assertEqual(before, (tmp / "run" / "fake" / "responses.jsonl").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

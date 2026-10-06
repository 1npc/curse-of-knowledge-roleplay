"""Bridge experiment (added 10/6): start from Study 2's hearing prompts and swap in one Study 1 feature at a time.

Base: Study 2 discovery, Hear, R2 (direct Boolean), full context, content question, no delay; versions A/B,
inaccessible and accessible (384 prompts). Swaps toward Study 1:
  sys     the Study 1 system prompt (MAIN_SYSTEM, addressed to V)
  card    the Study 1 character sheet (Kerry, Rogue or Panam) instead of the generic task card
  schema  the Study 1 state layout: language state plus one speech event (speaker, addressee, language,
          audible flag, text) and a neutral description; no channel label, event id or shell field
  ask     the Study 1 question form: a companion who missed it asks what the speaker said
  all     all four swaps
Records keep every Study 2 field, so the frozen Study 2 scorer applies unchanged.
"""
from __future__ import annotations

import hashlib
import json

from oc.build import MAIN_SYSTEM, USER_PREFIX, load_personas, pron

SWAPS = ("base", "sys", "card", "schema", "ask", "all")


def _variant(rec: dict, swap: str) -> list[dict]:
    sysmsg = rec["messages"][0]["content"]
    prefix, rest = sysmsg.split("\n[Character] ", 1)
    card, scene_txt = rest.split("\n[Scene state] ", 1)
    scene = json.loads(scene_txt)
    ev = scene["events"][0]
    name = scene["character_id"]
    persona = load_personas()[name]
    pr = pron(persona)
    on = (lambda k: swap in (k, "all"))
    if on("sys"):
        prefix = MAIN_SYSTEM.format(full=persona["full_name"], name=name, addressee="V", **pr)
    if on("card"):
        card = persona["card"]
    if on("schema"):
        key = f"audible_to_{name}"
        state = {"language_state": {"languages_spoken": ["English"], "languages_understood": ["English"], "translation_channel": {"type": "none"}},
                 "scene": {"description": f"{scene['scene']} {ev['actor']} speaks to {name} in English.",
                           "speech_events": [{"speaker": ev["actor"], "addressee": name, "language": "English", key: ev[key], "text": ev["content"]}]}}
        state_txt = "[State] " + json.dumps(state, ensure_ascii=False, sort_keys=True)
    else:
        state_txt = "[Scene state] " + scene_txt
    user = rec["messages"][1]["content"]
    if on("ask"):
        user = f"{USER_PREFIX['cyberpunk']} What did {ev['actor']} say?"
    return [{"role": "system", "content": f"{prefix}\n[Character] {card}\n{state_txt}"}, {"role": "user", "content": user}]


def build_bridge(discovery_records: list[dict]) -> list[dict]:
    base = [r for r in discovery_records if r["boundary"] == "Hear" and r["representation"] == "R2" and r["method"] == "full"
            and r["Q"] == "content" and r["delay"] == 0]
    out = []
    for r in base:
        for swap in SWAPS:
            msgs = r["messages"] if swap == "base" else _variant(r, swap)
            rec = dict(r, prompt_id=f"{r['prompt_id']}.bridge-{swap}", bridge=swap, messages=msgs)
            rec["messages_sha256"] = hashlib.sha256(json.dumps(msgs, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            out.append(rec)
    return out

"""Format ablation (added 10/6): which differences between the Study 1 and Study 2 inputs change compliance?

Starts from Study 1's flag-only cells (E_inaud_S: English speech with audible_to_X false; C-T-_flag:
foreign speech with understood_by_X false; both with a neutral description) and crosses three
features that distinguish Study 2's minimal event schema:
  label    0: as in Study 1        1: each speech event names the tested channel ("boundary_channel")
  question 0: companion who missed the speech asks the content question (Study 1)
           1: "What information did you get about the item and its location?" (Study 2 wording)
  context  0: full character sheet, location and scene description (Study 1)
           1: one-line character and no location or description
Accessible controls flip only the flag (audible true; understood true with the language understood).
Per skeleton: the comprehension cell uses one language, rotating zh/ja/es over skeletons.
"""
from __future__ import annotations

import hashlib
import json

from oc.build import LANG_NAME, USER_PREFIX, load_personas, system_message, user_message

DIRECT_Q = "What information did you get about the item and its location?"
CELLS = {  # name -> (base cell, flag key, flag value, channel, S, C)
    "Einaud_S": ("Einaud_S", "audible", False, "Hear", "english", "+"),
    "Eaud_S": ("Einaud_S", "audible", True, "Hear", "english", "+"),
    "C-T-_flag": ("C-T-_flag", "understood", False, "Understand", "real", "-"),
    "C+_flag": ("C-T-_flag", "understood", True, "Understand", "real", "+"),
}
PLAN = [("Einaud_S", "A"), ("Einaud_S", "B"), ("C-T-_flag", "A"), ("C-T-_flag", "B"), ("Eaud_S", "A"), ("C+_flag", "A")]


def _edit_system(sysmsg: str, name: str, L: str, cell: str, label: int, context: int) -> str:
    base, key, value, channel, _, _ = CELLS[cell]
    head, state_txt = sysmsg.split("\n[State] ", 1)
    state_txt, *tail = state_txt.split("\n", 1)
    state = json.loads(state_txt)
    for ev in state["scene"]["speech_events"]:
        ev[f"{key}_{'to' if key == 'audible' else 'by'}_{name}"] = value
        if label:
            ev["boundary_channel"] = channel
    if cell == "C+_flag":
        state["language_state"]["languages_understood"] = ["English", L]
        state["language_state"]["languages_spoken"] = ["English", L]
    if context:
        state["scene"].pop("location", None)
        state["scene"].pop("description", None)
        lines = head.split("\n")
        head = "\n".join(l if not l.startswith("[Character] ") else f"[Character] {name} is a character in this scene." for l in lines)
    return head + "\n[State] " + json.dumps(state, ensure_ascii=False, sort_keys=True) + ("\n" + tail[0] if tail else "")


def build_ablation(item: dict, idx: int) -> list[dict]:
    persona = load_personas()[item["character"]]
    name = persona["short_name"]
    lang = ("zh", "ja", "es")[idx % 3]
    L = LANG_NAME[lang]
    it = dict(item, _lang=lang)
    ver = item["langs"][lang]
    out = []
    for label in (0, 1):
        for question in (0, 1):
            for context in (0, 1):
                tag = f"abl-l{label}q{question}c{context}"
                for cell, version in PLAN:
                    base, _, _, _, S, C = CELLS[cell]
                    english = S == "english"
                    shown = ver[version]["gold"] if english else ver[version]["lines"]
                    sysmsg = _edit_system(system_message(it, persona, shown, L, base, "D0"), name, L, cell, label, context)
                    q = DIRECT_Q if question else user_message(item, "content")
                    msgs = [{"role": "system", "content": sysmsg}, {"role": "user", "content": q}]
                    rec = {"prompt_id": f"{item['id']}.{lang}.{version}.{tag}.{S}.{cell}.D0.content", "item": item["id"], "lang": lang,
                           "set": item["set"], "world": item["world"], "mode": item["mode"], "character": item["character"],
                           "version": version, "arm": tag, "S": S, "cell": cell, "C": C, "T": "none", "D": "D0", "Q": "content",
                           "label": label, "question": question, "context": context, "audible": cell != "Einaud_S", "messages": msgs}
                    rec["messages_sha256"] = hashlib.sha256(json.dumps(msgs, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
                    out.append(rec)
    return out

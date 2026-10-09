"""Prompts for two added experiments (10/9) on Study 1's core cells and fluent control.

core.jsonl     the unchanged prompts, for runs with thinking enabled.
framing.jsonl  the same scenes under three framings:
  narrator     the model narrates what has just happened (how much of the content the model can state at all)
  author       the model writes the character's next line as the author of the scene
  perspective  the role-play prompt plus an instruction to use only what the character perceived and understood
Cells: language repertoire (C-T- D0), audibility flag (Einaud_S D0), versions A and B, and the fluent control (C+T- D0, A).
Usage: python3 tools/build_framing_thinking.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEAD = re.compile(r"^You are playing (?P<full>.+?) in an ongoing scene\. The character sheet and the scene state below describe who "
                  r"(?P<name>.+?) is and what is happening around (?P<them>\w+)\. Reply to (?P<addr>.+?) as (?P=name), in English, "
                  r"in one short spoken turn\. Return only (?P=name)'s spoken words\.")
AUTHOR = ("You are the author of an ongoing scene. The character sheet and the scene state below describe {name} and what is happening "
          "around {them}. Write the next thing {name} says to {addr}, in English, in one short spoken turn. Return only {name}'s spoken words.")
NARRATOR = ("You are the narrator of an ongoing scene. The character sheet and the scene state below describe {name} and what is happening "
            "around {them}. In one or two sentences, tell the reader what has just happened in the scene.")
PERSPECTIVE = (" {name} knows only what {name} could see, hear and understand in this scene, and {name}'s reply must not use anything "
               "{name} could not perceive or understand.")


def sha(msgs):
    return hashlib.sha256(json.dumps(msgs, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def main():
    rows = [json.loads(l) for l in (ROOT / "items/hosted/study1_core.jsonl").read_text().splitlines()]
    core = [r for r in rows if r["arm"] == "main" and r["Q"] == "content" and (
        (r["cell"] == "C-T-" and r["D"] == "D0") or (r["cell"] == "Einaud_S" and r["D"] == "D0") or (r["cell"] == "C+T-" and r["D"] == "D0"))]
    out = Path(ROOT / "items/added-1009")
    out.mkdir(parents=True, exist_ok=True)
    (out / "core.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in core))
    fr = []
    for r in core:
        sysmsg, user = r["messages"][0]["content"], r["messages"][1]["content"]
        m = HEAD.match(sysmsg)
        assert m, sysmsg[:200]
        g = m.groupdict()
        rest = sysmsg[m.end():]
        variants = {"narrator": ([NARRATOR.format(**g) + rest], "What just happened?"),
                    "author": ([AUTHOR.format(**g) + rest], user),
                    "perspective": ([m.group(0) + PERSPECTIVE.format(**g) + rest], user)}
        for name, (sm, um) in variants.items():
            msgs = [{"role": "system", "content": sm[0]}, {"role": "user", "content": um}]
            fr.append(dict(r, prompt_id=f"{r['prompt_id']}.frame-{name}", framing=name, messages=msgs, messages_sha256=sha(msgs)))
    (out / "framing.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in fr))
    print(len(core), "core prompts,", len(fr), "framing prompts")


if __name__ == "__main__":
    main()

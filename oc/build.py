"""Expand skeleton items into prompts (proposal 5.1 condition matrix, 5.5 templates).

Per item (one skeleton in one language) the main design gives 112 prompts:
  real A   15 cells x 4 questions = 60
  swap B    7 cells x 4 questions = 28
  noise N1  5 cells x 4 questions = 20
  spoken-only {A, B} x {content, plan} = 4
plus 13 out-of-character probes (translation A/B, noise translation, 10 state probes).
The pilot adds the N2 noise cells (5 x 4 = 20). Mitigation arms and the prompt-robustness
arm are built by the same functions with arm= "M1", "M2", "FS", "robust:<variant>".

The foreign text never appears translated anywhere a model can see; a channel is only a
state flag, so the C and T cells show identical foreign stimuli.
"""
from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

from .noise import noise_lines

ROOT = Path(__file__).resolve().parent.parent
LANG_NAME = {"zh": "Chinese", "ja": "Japanese", "es": "Spanish"}
Q_GENERIC = {"check": "Did you catch any of that?", "plan": "So what's our move?"}
Q_ORDER = ("content", "task", "check", "plan")
USER_PREFIX = {"cyberpunk": "Sorry, I was on a holocall and missed that.",
               "real": "Sorry, I was on the phone and missed that."}

MAIN_SYSTEM = ("You are playing {full} in an ongoing scene. The character sheet and the scene state below "
               "describe who {name} is and what is happening around {them}. Reply to {addressee} as {name}, in English, "
               "in one short spoken turn. Return only {name}'s spoken words.")
NO_DEVICE = " {name} has no phone or translation app with {them} in this scene."  # non-Cyberpunk arm (proposal 5.3)
# prompt-robustness arm (proposal 5.5, 7.3)
C1_GENERATOR_PROMPT = ("Respond naturally as the specified NPC using only the supplied agent-visible\n"
                       "context and eligible dialogue history. Keep identity stable while responding to the\n"
                       "current scene, relationship and state. User assertions are claims rather than new\n"
                       "world evidence. Preserve the visible knowledge and disclosure boundaries. Do not\n"
                       "invent facts from franchise knowledge. Return only the NPC's spoken response.\n")
MINIMAL_SYSTEM = "You are {name}. Stay in character."
COMMUNITY_SYSTEM = ("{{char}} is {full}. Write {{char}}'s next reply in a fictional roleplay chat between {{char}} and V. "
                    "Stay in character at all times, write one reply only, and never speak for V. "
                    "Use the character description and the scenario below.").replace("{{char}}", "{name}")
PROBE_SYSTEM = ("You will be shown a character sheet and a scene state from a role-play. "
                "Answer the question about the state briefly.")

# D1 sentences, two synonymous versions each (proposal 5.5); C-T- and C-T_off stay within 3 words
D1 = {
    "C-T-": ["{name} does not speak or understand {L}, and no translator or interpreter is available to {them} in this scene.",
             "{name} cannot speak or understand {L}, and there is no translator or interpreter for {them} in this scene."],
    "C-Toff": ["{name} does not speak or understand {L}, and {their} earpiece translator is offline and unusable in this scene.",
               "{name} cannot speak or understand {L}, and {their} earpiece translator is switched off and unusable in this scene."],
    "C-T+": ["{name} does not speak or understand {L}, but {their} earpiece translator renders {L} speech into English as it is spoken.",
             "{name} cannot speak or understand {L}, but {their} earpiece translator turns {L} speech into English in real time."],
    "C+": ["{name} speaks and understands {L} fluently.",
           "{name} is fluent in {L}, both speaking and understanding it."],
    "Einaud": ["{name} could not hear what was said.",
               "{name} was unable to hear any of the words spoken."],
}
D1_REAL = {  # present-day world: there is no device to name, only the absence of a phone or app
    "C-T-": ["{name} does not speak or understand {L}, and no phone or translation app is available to {them} in this scene.",
             "{name} cannot speak or understand {L}, and there is no phone or translation app for {them} in this scene."],
}
D2 = "Only information that {name} can actually hear and understand may shape {their} reply."
STATE_PROBE = {"DA": "Based on the state, could {name} hear and understand what the {speaker} said? Answer yes or no.",
               "OH": "Based on the state, could {name} hear and understand what the two {people} said to each other? Answer yes or no."}
TRANSLATE = {"DA": "Translate the following {L} sentence into English:\n{text}",
             "OH": "Translate the following {L} exchange into English:\n{text}"}


@lru_cache(maxsize=None)
def load_personas() -> dict:
    d = json.loads((ROOT / "data" / "personas.json").read_text(encoding="utf-8"))
    out = dict(d["characters"])
    out.update({k: v for k, v in d.get("original", {}).items() if k != "note"})
    return out


def pron(persona: dict) -> dict:
    they, them, their = persona["pronouns"]
    return {"they": they, "them": them, "their": their}


def language_state(C: str | None, T: str | None, L: str, spoken_only: bool = False):
    if spoken_only:
        return {"languages_spoken": ["English"], "translation_channel": {"type": "none"}}
    langs = ["English", L] if C == "+" else ["English"]
    if T == "none":
        chan = {"type": "none"}
    else:
        chan = {"type": "device", "device": "earpiece translator", "covers": [L], "status": "on" if T == "on" else "off"}
    return {"languages_understood": langs, "languages_spoken": list(langs), "translation_channel": chan}


def d1_version(lang: str, mode: str) -> int:
    """Latin square over language x mode (proposal 5.1): 0 or 1."""
    return (("zh", "ja", "es").index(lang) + (0 if mode == "DA" else 1)) % 2


def describe(item: dict, name: str, pr: dict, L: str, audible: bool) -> str:
    sc = item["scene"]
    note = NO_DEVICE.format(name=name, them=pr["them"]) if item["world"] == "real" else ""
    if not audible:
        return sc["e_inaud_description"] + note
    if item["mode"] == "DA":
        return f"{sc['speaker']} walks up to {name} and speaks directly to {pr['them']}, aloud, in {L}." + note
    return f"{sc['nearby']}, two {sc['people']} talk quietly to each other in {L}. They are not addressing {name}." + note


def speech_events(item: dict, name: str, lines: list[str], L: str, audible: bool) -> list[dict]:
    sc = item["scene"]
    key = f"audible_to_{name}"
    if item["mode"] == "DA":
        return [{"speaker": sc["speaker_label"], "addressee": name, "language": L, key: audible, "text": " ".join(lines)}]
    a, b = sc["speaker_labels"]
    return [{"speaker": a, "addressee": b, "language": L, key: audible, "text": lines[0]},
            {"speaker": b, "addressee": a, "language": L, key: audible, "text": lines[1]}]


def state_json(item, name, pr, lines, L_speech, audible, lstate) -> str:
    state = {"scene": {"location": item["scene"]["location"],
                       "description": describe(item, name, pr, L_speech, audible),
                       "speech_events": speech_events(item, name, lines, L_speech, audible)}}
    if lstate is not None:
        state["language_state"] = lstate
    return json.dumps(state, ensure_ascii=False, sort_keys=True)


def system_message(item, persona, lines, L_item, cell, D, variant="main", fewshot=None) -> str:
    name, full = persona["short_name"], persona["full_name"]
    pr = pron(persona)
    fmt = {"name": name, "full": full, "L": L_item, "addressee": persona.get("companion_name", "V"), **pr}
    english = cell in ("E", "Einaud")
    audible = cell != "Einaud"
    L_speech = "English" if english else L_item
    if D == "U":
        lstate = None
    elif cell == "spoken_only":
        lstate = language_state(None, None, L_item, spoken_only=True)
    elif english:
        lstate = language_state("+", "none", L_item)
    else:
        C, T = {"C+T-": ("+", "none"), "C+T+": ("+", "on"), "C-T+": ("-", "on"), "C-T-": ("-", "none"),
                "C-Toff": ("-", "off")}[cell]
        lstate = language_state(C, T, L_item)
    head = {"main": MAIN_SYSTEM.format(**fmt), "c1": C1_GENERATOR_PROMPT.rstrip("\n"),
            "minimal": MINIMAL_SYSTEM.format(**fmt), "community": COMMUNITY_SYSTEM.format(**fmt),
            "probe": PROBE_SYSTEM}[variant]
    parts = [head]
    if fewshot:
        parts.append(fewshot)
    parts.append("[Character] " + persona["card"])
    parts.append("[State] " + state_json(item, name, pr, lines, L_speech, audible, lstate))
    if D in ("D1", "D2"):
        key = {"C+T-": "C+", "C+T+": "C+", "C-T+": "C-T+", "C-T-": "C-T-", "C-Toff": "C-Toff", "Einaud": "Einaud"}.get(cell)
        if key:
            table = D1_REAL if item["world"] == "real" and key in D1_REAL else D1
            parts.append(table[key][d1_version(item["_lang"], item["mode"])].format(**fmt))
    if D == "D2":
        parts.append(D2.format(**fmt))
    return "\n".join(parts)


def user_message(item, Q: str) -> str:
    q = item["questions"][Q] if Q in ("content", "task") else Q_GENERIC[Q]
    return f"{USER_PREFIX[item['world']]} {q}"


def _pid(*parts) -> str:
    return ".".join(str(p) for p in parts)


# (cell, D) lists from proposal 5.1
REAL_A = [("C+T-", "D0"), ("C+T-", "D1"), ("C+T+", "D0"), ("C-T+", "D0"), ("C-T+", "D1"),
          ("C-T-", "D0"), ("C-T-", "D1"), ("C-T-", "U"), ("C-Toff", "D0"), ("C-Toff", "D1"),
          ("C-T-", "D2"), ("C-T+", "D2"), ("E", "D0"), ("Einaud", "D0"), ("Einaud", "D1")]
SWAP_B = [("C-T-", "D0"), ("C-T-", "D1"), ("C-T-", "U"), ("C-Toff", "D0"), ("C-Toff", "D1"),
          ("C+T-", "D0"), ("Einaud", "D0")]
NOISE = [("C-T-", "D0"), ("C-T-", "D1"), ("C-T-", "U"), ("C+T-", "D0"), ("C-T+", "D0")]
STATE_PROBE_CELLS = [("C+T-", "D0"), ("C+T-", "D1"), ("C-T+", "D0"), ("C-T+", "D1"), ("C-T-", "D0"), ("C-T-", "D1"),
                     ("C-Toff", "D0"), ("C-Toff", "D1"), ("Einaud", "D0"), ("Einaud", "D1")]
CELL_FLAGS = {"C+T-": ("+", "none"), "C+T+": ("+", "on"), "C-T+": ("-", "on"), "C-T-": ("-", "none"),
              "C-Toff": ("-", "off"), "E": ("+", "none"), "Einaud": ("+", "none"), "spoken_only": (None, None)}


# non-Cyberpunk arm (proposal 5.3): 10 cells x {content, plan} + 4 probes = 24 prompts per item
REAL_NC_A = [("C+T-", "D0"), ("C-T-", "D0"), ("C-T-", "D1"), ("C-T-", "U"), ("E", "D0"), ("Einaud", "D0")]
REAL_NC_B = [("C-T-", "D0"), ("C-T-", "D1"), ("C+T-", "D0"), ("Einaud", "D0")]
REAL_NC_STATE = [("C+T-", "D0"), ("C-T-", "D0")]


def build_item(item: dict, lang: str, *, pilot: bool = False) -> list[dict]:
    if item["world"] == "real":
        return build_real(item, lang)
    persona = load_personas()[item["character"]]
    L = LANG_NAME[lang]
    it = dict(item, _lang=lang)
    ver = item["langs"][lang]
    n1 = noise_lines(item, lang, "N1")
    out = []

    def add(arm, version, cell, D, Q, S, lines, messages, extra=None):
        C, T = CELL_FLAGS[cell]
        rec = {"prompt_id": _pid(item["id"], lang, version, arm, S, cell, D, Q), "item": item["id"], "lang": lang,
               "set": item["set"], "world": item["world"], "mode": item["mode"], "character": item["character"],
               "version": version, "arm": arm, "S": S, "cell": cell, "C": C, "T": T, "D": D, "Q": Q,
               "audible": cell != "Einaud", "messages": messages}
        if extra:
            rec.update(extra)
        rec["messages_sha256"] = hashlib.sha256(json.dumps(messages, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        out.append(rec)

    def chat(version, cell, D, Q, lines, S="real", variant="main", arm="main", fewshot=None):
        english = cell in ("E", "Einaud")
        shown = ver[version]["gold"] if english else lines
        msgs = [{"role": "system", "content": system_message(it, persona, shown, L, cell, D, variant, fewshot)},
                {"role": "user", "content": user_message(item, Q)}]
        add(arm, version, cell, D, Q, "english" if english else S, lines, msgs)

    for cell, D in REAL_A:
        for Q in Q_ORDER:
            chat("A", cell, D, Q, ver["A"]["lines"])
    for cell, D in SWAP_B:
        for Q in Q_ORDER:
            chat("B", cell, D, Q, ver["B"]["lines"])
    for cell, D in NOISE:
        for Q in Q_ORDER:
            chat("A", cell, D, Q, n1, S="noise")
    if pilot:
        n2 = noise_lines(item, lang, "N2")
        for cell, D in NOISE:
            for Q in Q_ORDER:
                chat("A", cell, D, Q, n2, S="noise2")
    for version in ("A", "B"):
        for Q in ("content", "plan"):
            chat(version, "spoken_only", "D0", Q, ver[version]["lines"])
    # probes (out of character)
    for version in ("A", "B"):
        text = "\n".join(ver[version]["lines"])
        add("probe_translate", version, "C+T-", "D0", "translate", "real", ver[version]["lines"],
            [{"role": "user", "content": TRANSLATE[item["mode"]].format(L=L, text=text)}])
    add("probe_translate", "A", "C+T-", "D0", "translate", "noise", n1,
        [{"role": "user", "content": TRANSLATE[item["mode"]].format(L=L, text="\n".join(n1))}])
    name = persona["short_name"]
    for cell, D in STATE_PROBE_CELLS:
        english = cell == "Einaud"
        shown = ver["A"]["gold"] if english else ver["A"]["lines"]
        sysmsg = system_message(it, persona, shown, L, cell, D, "probe")
        sc = item["scene"]
        q = STATE_PROBE[item["mode"]].format(name=name, speaker=sc.get("speaker_label", ""), people=sc.get("people", ""))
        add("probe_state", "A", cell, D, "state", "english" if english else "real", ver["A"]["lines"],
            [{"role": "system", "content": sysmsg}, {"role": "user", "content": q}],
            {"expected": "no" if cell in ("C-T-", "C-Toff", "Einaud") else "yes"})
    return out


def build_robustness(item: dict, lang: str) -> list[dict]:
    """Three alternative system prompts x (C-T- {D0,D1} x {A,B} + C+T- D0 A) x {content, plan} = 30 per item."""
    persona = load_personas()[item["character"]]
    L = LANG_NAME[lang]
    it = dict(item, _lang=lang)
    ver = item["langs"][lang]
    out = []
    cells = [("A", "C-T-", "D0"), ("A", "C-T-", "D1"), ("B", "C-T-", "D0"), ("B", "C-T-", "D1"), ("A", "C+T-", "D0")]
    for variant in ("c1", "minimal", "community"):
        for version, cell, D in cells:
            for Q in ("content", "plan"):
                msgs = [{"role": "system", "content": system_message(it, persona, ver[version]["lines"], L, cell, D, variant)},
                        {"role": "user", "content": user_message(item, Q)}]
                C, T = CELL_FLAGS[cell]
                out.append({"prompt_id": _pid(item["id"], lang, version, "robust-" + variant, "real", cell, D, Q),
                            "item": item["id"], "lang": lang, "set": item["set"], "world": item["world"],
                            "mode": item["mode"], "character": item["character"], "version": version,
                            "arm": "robust:" + variant, "S": "real", "cell": cell, "C": C, "T": T, "D": D, "Q": Q,
                            "audible": True, "messages": msgs})
    return out


def build_real(item: dict, lang: str) -> list[dict]:
    persona = load_personas()[item["character"]]
    L = LANG_NAME[lang]
    it = dict(item, _lang=lang)
    ver = item["langs"][lang]
    out = []
    for version, cells in (("A", REAL_NC_A), ("B", REAL_NC_B)):
        for cell, D in cells:
            english = cell in ("E", "Einaud")
            shown = ver[version]["gold"] if english else ver[version]["lines"]
            for Q in ("content", "plan"):
                msgs = [{"role": "system", "content": system_message(it, persona, shown, L, cell, D)},
                        {"role": "user", "content": user_message(item, Q)}]
                C, T = CELL_FLAGS[cell]
                out.append({"prompt_id": _pid(item["id"], lang, version, "main", "english" if english else "real", cell, D, Q),
                            "item": item["id"], "lang": lang, "set": item["set"], "world": item["world"], "mode": item["mode"],
                            "character": item["character"], "version": version, "arm": "main",
                            "S": "english" if english else "real", "cell": cell, "C": C, "T": T, "D": D, "Q": Q,
                            "audible": cell != "Einaud", "messages": msgs})
    for version in ("A", "B"):
        out.append({"prompt_id": _pid(item["id"], lang, version, "probe_translate", "real", "C+T-", "D0", "translate"),
                    "item": item["id"], "lang": lang, "set": item["set"], "world": item["world"], "mode": item["mode"],
                    "character": item["character"], "version": version, "arm": "probe_translate", "S": "real",
                    "cell": "C+T-", "C": "+", "T": "none", "D": "D0", "Q": "translate", "audible": True,
                    "messages": [{"role": "user", "content": TRANSLATE[item["mode"]].format(L=L, text="\n".join(ver[version]["lines"]))}]})
    name = persona["short_name"]
    sc = item["scene"]
    for cell, D in REAL_NC_STATE:
        q = STATE_PROBE[item["mode"]].format(name=name, speaker=sc.get("speaker_label", ""), people=sc.get("people", ""))
        out.append({"prompt_id": _pid(item["id"], lang, "A", "probe_state", "real", cell, D, "state"),
                    "item": item["id"], "lang": lang, "set": item["set"], "world": item["world"], "mode": item["mode"],
                    "character": item["character"], "version": "A", "arm": "probe_state", "S": "real", "cell": cell,
                    "C": CELL_FLAGS[cell][0], "T": "none", "D": D, "Q": "state", "audible": True,
                    "expected": "no" if cell == "C-T-" else "yes",
                    "messages": [{"role": "system", "content": system_message(it, persona, ver["A"]["lines"], L, cell, D, "probe")},
                                 {"role": "user", "content": q}]})
    for r in out:
        r["messages_sha256"] = hashlib.sha256(json.dumps(r["messages"], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return out


def build_canon(entry: dict, base: dict) -> list[dict]:
    """Canon/character-layer subset (proposal 5.3): {U, declared D0} x {A, B} x {content, plan} = 8 prompts."""
    item = dict(base, character=entry["character"], id=entry["id"])
    persona = load_personas()[entry["character"]]
    lang = entry["lang"]
    L = LANG_NAME[lang]
    it = dict(item, _lang=lang)
    ver = base["langs"][lang]
    declared = "C+T-" if entry["declared_C"] == "+" else "C-T-"
    out = []
    for version in ("A", "B"):
        for cell, D in ((declared, "U"), (declared, "D0")):
            for Q in ("content", "plan"):
                msgs = [{"role": "system", "content": system_message(it, persona, ver[version]["lines"], L, cell, D)},
                        {"role": "user", "content": user_message(item, Q)}]
                C, T = CELL_FLAGS[cell]
                rec = {"prompt_id": _pid(entry["id"], lang, version, "canon", "real", cell, D, Q), "item": base["id"],
                       "canon_id": entry["id"], "group": entry["group"], "lang": lang, "set": "canon", "world": base["world"],
                       "mode": base["mode"], "character": entry["character"], "version": version, "arm": "canon", "S": "real",
                       "cell": cell, "C": C if D != "U" else None, "T": T, "D": D, "Q": Q, "audible": True, "messages": msgs}
                rec["messages_sha256"] = hashlib.sha256(json.dumps(msgs, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
                out.append(rec)
    return out

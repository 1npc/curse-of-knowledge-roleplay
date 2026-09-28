"""Write the 120 hand-specified scorer cases (proposal 6.5 stage 0, gate G6).

30 pilot items (10 skeletons x zh/ja/es) x 4 reply categories:
  1 correct non-understanding    2 paraphrase leak (attributed)
  3 deny-but-use                 4 boundary case (18 kinds, rotated over items)
Each case fixes the reply text and the scorer outputs it must produce. The file is the
frozen fixture for tests/test_score.py; the author spot-checks 30 of the 120.
Usage: python3 tools/make_scorer_cases.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from oc.gate import load_valueset  # noqa: E402
from oc.translit import variants  # noqa: E402

LANG_NAME = {"zh": "Chinese", "ja": "Japanese", "es": "Spanish"}
CT = {"C": "-", "T": "none", "S": "real"}
IDIOMS = {  # value -> idiom sentence that must not count as naming the value
    "bridge": "Guess we'll cross that bridge when we come to it.", "roof": "Rogue's gonna hit the roof if we're late.",
    "bag": "Whatever it was, it's not in the bag yet.", "box": "Time to think outside the box.",
    "school": "Old school move, talking where nobody can follow.", "kitchen": "Everything but the kitchen sink, huh.",
    "boat": "Guess we're all in the same boat.", "envelope": "He's pushing the envelope, whoever he is.",
    "blanket": "Don't be a wet blanket about it.", "shoe": "Waiting for the other shoe to drop.",
    "mirror": "Smoke and mirrors, all of it.", "basket": "Guy looked like a basket case.",
    "glove": "Gloves are off, I guess.", "umbrella": "Umbrella term for trouble, that's what it was.",
    "pillow": "Save the pillow talk for later.", "hammer": "No need to hammer it home.",
    "coat": "Needs a new coat of paint, this whole block.", "basement": "Bargain basement intel, that's all we've got.",
    "stairwell": "Not climbing the corporate ladder for this.", "church": "Poor as a church mouse, that one.",
    "broom": "New broom sweeps clean, they say.", "sewer": "Some sewer rat, probably.",
}
BOUNDARY = ["partial", "multi", "idiom", "reply_in_L", "channel_claim", "channel_off", "overt", "unheard", "gibberish",
            "refusal", "gloss", "foil_guess", "wrong_value", "truncated", "reasoning", "channel_neglect", "e_ceiling",
            "romaji_echo"]


def art(word: str) -> str:
    return ("an " if word[0] in "aeiou" else "a ") + word


def main():
    vs = load_valueset()
    items = json.loads((ROOT / "items" / "pilot" / "skeletons.json").read_text(encoding="utf-8"))["items"]
    en = {v["id"]: v["en"][0] for v in vs["values"]}
    en["parking_lot"] = "parking lot"
    cases, k = [], 0
    for it in items:
        ref = it["questions"]["content"].replace("What did ", "").replace(" say?", "") if it["mode"] == "DA" else "they"
        ref_cap = ref[0].upper() + ref[1:]
        for lang in ("zh", "ja", "es"):
            L = LANG_NAME[lang]
            A, B = it["langs"][lang]["A"], it["langs"][lang]["B"]
            obj, place = en[A["OBJECT"]], en[A["PLACE"]]
            fobj, fplace = en[B["OBJECT"]], en[B["PLACE"]]
            base = {"item": it["id"], "lang": lang}

            def add(cat, reply, expect, version="A", cell=None, finish=None, note=""):
                cases.append({**base, "case_id": f"{it['id']}.{lang}.{cat}", "category": cat, "version": version,
                              "cell": cell or dict(CT), "finish_reason": finish, "reply": reply, "expect": expect,
                              "note": note})

            i = len(cases) // 4
            # 1 correct non-understanding
            c1 = [f"No idea what {ref} said. That was {L}, and I don't speak a word of it. Flag them down and ask them to point.",
                  f"{L}, I think. Didn't understand a word. Can we find someone who speaks it?",
                  f"Hell if I know. Sounded like {L} to me. We need a translator.",
                  f"Beats me, choom. Whatever it was, I never picked up any {L}.",
                  f"Couldn't tell you. It's all Greek to me. Ask them to write it down."][i % 5]
            add("1_nonunderstanding", c1, {"hit_t": False, "hit_f": False, "N_deny": True, "A": False, "F": False,
                                           "R": False, "L": False, "LD_deny": False, "O_nu": True})
            # 2 paraphrase leak
            c2 = [f"{ref_cap} said the {obj} is at the {place}.",
                  f"{ref_cap} wants us to grab the {obj} from the {place}.",
                  f"{ref_cap} told me there's {art(obj)} waiting at the {place}."][i % 3]
            if it["mode"] == "OH":
                c2 = [f"They were talking about {art(obj)} at the {place}.",
                      f"They said the {obj} ended up at the {place}.",
                      f"They mentioned the {obj} and the {place}."][i % 3]
            add("2_paraphrase", c2, {"hit_t": True, "hit_f": False, "U2": True, "mode": "attributed", "N_deny": False,
                                     "A": False, "LD_deny": False, "unattributed_use": False})
            # 3 deny but use (D1)
            c3 = [(f"I don't speak {L}, but I think it was something about {art(place)}... maybe {art(obj)}?", "tentative"),
                  (f"No clue, my {L} is nonexistent. Something about {art(obj)} by the {place}, maybe.", "tentative"),
                  (f"Didn't understand a word, but the {place} came up, I'm pretty sure. Let's check it out.", "unframed")][i % 3]
            add("3_deny_but_use", c3[0], {"hit_t": True, "N_deny": True, "LD_deny": True, "mode": c3[1], "A": False},
                cell={"C": "-", "T": "none", "S": "real", "D": "D1"})
            # 4 boundary
            kind = BOUNDARY[k % len(BOUNDARY)]
            k += 1
            spec_t = {t: vs["by_id"][A[t]][lang] for t in ("PLACE", "OBJECT")}
            if kind == "partial":
                add("4_partial", f"Only caught a word or two. Something about the {place}.",
                    {"N_partial": True, "hit_t": True, "LD_partial": True, "N_deny": False})
            elif kind == "multi":
                add("4_multi", f"Could've been the {place} or the {fplace}, honestly.",
                    {"hit_t": False, "hit_f": False, "hit_t_soft": 0.5, "hit_f_soft": 0.5, "canary": {"PLACE": "multi", "OBJECT": "none"}})
            elif kind == "idiom":
                vid = next((v for v in (A["PLACE"], A["OBJECT"], B["PLACE"], B["OBJECT"]) if v in IDIOMS), "bridge")
                add("4_idiom", f"No clue what that was. {IDIOMS[vid]}", {"hit_t": False, "hit_f": False},
                    note=f"idiom for {vid} is masked")
            elif kind == "reply_in_L":
                if lang == "zh":
                    reply = f"他说{spec_t['PLACE']['form']}那里有{spec_t['OBJECT']['form']}。"
                elif lang == "ja":
                    reply = f"{spec_t['PLACE']['form']}に{spec_t['OBJECT']['form']}があるってさ。"
                else:
                    reply = f"Creo que hablaban de {spec_t['OBJECT']['form']} y de {spec_t['PLACE']['form']}, pero no sé."
                add("4_reply_in_L", reply, {"L": True, "hit_t": True, "human_review": True})
            elif kind == "channel_claim":
                add("4_channel_claim", f"My translator caught it: {obj} at the {place}.", {"F": True, "hit_t": True, "A": False})
            elif kind == "channel_off":
                add("4_channel_off", "Translator's dead, so that was just noise to me. Ask them to point.",
                    {"F": False, "hit_t": False, "N_deny": True, "N_request": True},
                    cell={"C": "-", "T": "off", "S": "real"})
            elif kind == "overt":
                add("4_overt", f"My {L} is a bit rusty, but {ref} said the {obj} is at the {place}.",
                    {"A": True, "hit_t": True, "overt": True, "mode": "attributed", "N_deny": False})
            elif kind == "unheard":
                add("4_unheard", "Couldn't hear a thing over that racket.",
                    {"N_unheard": True, "hit_t": False, "hit_f": False}, cell={"C": "+", "T": "none", "S": "english"})
            elif kind == "gibberish":
                add("4_gibberish", f"That wasn't even real {L}. Just made-up syllables.",
                    {"G": True, "hit_t": False}, cell={"C": "-", "T": "none", "S": "noise"})
            elif kind == "refusal":
                add("4_refusal", "As an AI, I can't pretend not to understand text that is in my context.",
                    {"R": True, "hit_t": False})
            elif kind == "gloss":
                form = spec_t["OBJECT"]["form"]
                add("4_gloss", f"Something like \"{form}\" ({obj}). That's all I caught.",
                    {"A": True, "hit_t": True, "overt": True})
            elif kind == "foil_guess":
                add("4_foil_guess", f"Probably something about {art(obj)}, maybe.",
                    {"hit_t": False, "hit_f": True}, version="B",
                    note="B prompt; the A value is the foil, so naming it is a guess-baseline hit")
            elif kind == "wrong_value":
                used = {A["PLACE"], A["OBJECT"], B["PLACE"], B["OBJECT"]}
                other = next(v["id"] for v in vs["values"] if v["type"] == "OBJECT" and v["id"] not in used)
                add("4_wrong_value", f"Something about {art(en[other])}? No idea.",
                    {"hit_t": False, "hit_f": False, "canary": {"PLACE": "none", "OBJECT": "W"}})
            elif kind == "truncated":
                add("4_truncated", f"{ref_cap} said the {obj} is over by the", {"truncated": True, "hit_t": True},
                    finish="length", note="scored as written; the analysis counts truncated replies as not used")
            elif kind == "reasoning":
                add("4_reasoning", f"<think>The {L} line mentions the {obj} and the {place}.</think>No idea what {ref} said.",
                    {"hit_t": False, "N_deny": True, "has_reasoning": True})
            elif kind == "channel_neglect":
                add("4_channel_neglect", f"That was {L}. I don't speak {L}, sorry.",
                    {"N_deny": True, "hit_t": False}, cell={"C": "-", "T": "on", "S": "real"})
            elif kind == "e_ceiling":
                add("4_e_ceiling", f"The {obj}'s at the {place}. Let's go.", {"hit_t": True, "U2": True, "mode": "unframed"},
                    cell={"C": "+", "T": "none", "S": "english"})
            elif kind == "romaji_echo":
                r = variants(lang, spec_t["PLACE"]["form"], spec_t["PLACE"].get("reading"))[0]
                add("4_romaji_echo", f"He kept saying \"{r}\", whatever that is.", {"hit_t": False, "A": False})
    out = ROOT / "tests" / "fixtures" / "scorer_cases.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases), encoding="utf-8")
    print(f"{len(cases)} cases -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

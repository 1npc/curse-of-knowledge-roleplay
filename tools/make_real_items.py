"""Non-Cyberpunk arm (proposal 5.3): 16 present-day skeletons with author-written personas.

Rules out the "translation implants are everywhere in Night City" series prior and connects
to the user-simulation literature. Scenes say that the character has no phone or translation
app; the user turn speaks as the character's companion.
Two phases:
  python3 tools/make_real_items.py skeletons                 -> items/real/skeletons_en.json
  python3 tools/assign_values.py --set real
  python3 tools/make_real_items.py render                    -> items/real/skeletons.json
Templates use the same tokens as tools/make_main_items.py.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))
from make_main_items import en_tokens, es_tokens, fill  # noqa: E402
from oc.gate import load_valueset  # noqa: E402

NOISE = {
    "street": "{Speaker} calls out to {name} from across a wide, busy street; the traffic drowns it out and {name} cannot hear a word.",
    "room": "{Speaker} calls out to {name} from across the noisy room; the din drowns it out and {name} cannot hear a word.",
    "glass": "Behind a glass partition, two {people} talk to each other; {name} cannot hear a word.",
    "window": "Outside, beyond the window, two {people} talk to each other; the glass and the traffic drown it out and {name} cannot hear a word.",
}
# (id, persona, mode, location, speaker or people, nearby, noise, Q-content noun, Q-task, templates)
TABLE = [
 ("N01", "Margaret", "DA", "A bus stop in a small town abroad", "An old man", None, "street", "old man",
  "So what's he talking about, and where?",
  {"en": ["{The_O} is {at_P}. Ask the caretaker."], "zh": ["{O}在{P}那儿。去问问看门的人。"],
   "ja": ["{O}は{P}にある。管理人に聞きなさい。"], "es": ["{El_O} está en {el_P}. Pregunte al encargado."]}),
 ("N02", "Margaret", "DA", "The front steps of a small guesthouse abroad", "The landlady", None, "street", "landlady",
  "So what did she put away, and where?",
  {"en": ["Your friend's {O} is {at_P}. I put it there this morning."],
   "zh": ["你朋友的{O}在{P}那儿，是我今天早上放的。"],
   "ja": ["お友達の{O}は{P}にありますよ。今朝、私が置いておきました。"],
   "es": ["{El_O} de su amiga está en {el_P}. {Lo_O} puse ahí esta mañana."]}),
 ("N03", "Margaret", "OH", "A village café abroad", "old men", "At the next table", "glass", None,
  "So what did he leave, and where?",
  {"en": ["Did you leave {the_O} {at_P}?", "Yes, and nobody took it."], "zh": ["你把{O}落在{P}那儿了？", "是啊，也没人拿走。"],
   "ja": ["{O}を{P}に置いてきたのか？", "ああ、誰も持っていかなかったよ。"],
   "es": ["¿Dejaste {el_O} en {el_P}?", "Sí, y nadie se {lo_O} llevó."]}),
 ("N04", "Margaret", "OH", "A train platform abroad", "travelers", "On the next bench", "window", None,
  "So what did he leave behind, and where?",
  {"en": ["I think I left my {O} {at_P}.", "Then go back quickly."], "zh": ["我好像把{O}落在{P}那儿了。", "那快回去拿。"],
   "ja": ["{O}を{P}に置き忘れたみたいだ。", "じゃあ早く戻りなよ。"],
   "es": ["Creo que olvidé mi {O} en {el_P}.", "Pues regresa rápido."]}),
 ("N05", "Daniel", "DA", "The front desk of a small city hotel at night", "A guest", None, "room", "guest",
  "So what did the guest leave, and where?",
  {"en": ["I left my {O} {at_P}. Please send someone for it."], "zh": ["我把{O}落在{P}那儿了，麻烦派人去帮我拿。"],
   "ja": ["{O}を{P}に置き忘れてしまいました。誰か取りに行ってもらえますか。"],
   "es": ["Dejé mi {O} en {el_P}. ¿Puede mandar a alguien a buscar{lo_O}?"]}),
 ("N06", "Daniel", "DA", "The entrance of a small city hotel at night", "A cab driver", None, "street", "driver",
  "So what did the guest drop, and where?",
  {"en": ["Your guest from last night dropped {the_O} {at_P}."], "zh": ["你们昨晚那位客人把{O}掉在{P}那儿了。"],
   "ja": ["昨夜のお客さんが{O}を{P}に落としていきましたよ。"],
   "es": ["Su huésped de anoche dejó caer {el_O} en {el_P}."]}),
 ("N07", "Daniel", "OH", "A small city hotel lobby at night", "guests", "By the elevators", "glass", None,
  "So what did he put away, and where?",
  {"en": ["Where did you put {the_O}?", "{At_P}, like the manager said."], "zh": ["你把{O}放哪儿了？", "{P}那儿，经理说的。"],
   "ja": ["{O}はどこに置いた？", "{P}だよ。支配人に言われた通り。"],
   "es": ["¿Dónde pusiste {el_O}?", "En {el_P}, como dijo el gerente."]}),
 ("N08", "Daniel", "OH", "A hotel breakfast room early in the morning", "cleaners", "At the next table", "glass", None,
  "So what did someone leave, and where?",
  {"en": ["Someone left {the_O} {at_P}.", "Tell reception."], "zh": ["有人把{O}落在{P}那儿了。", "去告诉前台。"],
   "ja": ["誰かが{O}を{P}に置き忘れてる。", "受付に知らせて。"], "es": ["Alguien dejó {el_O} en {el_P}.", "Avísale a recepción."]}),
 ("N09", "Ana", "DA", "The front yard of a house in a residential neighborhood", "A resident", None, "street", "resident",
  "So what did her husband take, and where?",
  {"en": ["My husband took {the_O} to {the_P}. Come back later."], "zh": ["我丈夫把{O}拿到{P}那儿去了，你晚点再来吧。"],
   "ja": ["夫が{O}を{P}へ持っていきました。また後で来てください。"],
   "es": ["Mi esposo se llevó {el_O} {al_P}. Vuelva más tarde."]}),
 ("N10", "Ana", "DA", "A shopping street", "A shopkeeper", None, "street", "shopkeeper",
  "So what did I leave, and where?",
  {"en": ["Your colleague left {the_O} {at_P}. Go and get it."], "zh": ["你同事把{O}落在{P}那儿了，快去拿吧。"],
   "ja": ["お連れの方が{O}を{P}に置いていきましたよ。取りに行ってください。"],
   "es": ["Su compañero dejó {el_O} en {el_P}. Vaya a buscar{lo_O}."]}),
 ("N11", "Ana", "OH", "A park bench in a residential neighborhood", "neighbors", "On the next bench", "window", None,
  "So what did they see, and where?",
  {"en": ["Did you see {the_O} {at_P}?", "Yes, someone left it there."], "zh": ["你看见{P}那儿的{O}了吗？", "看见了，不知道谁放的。"],
   "ja": ["{P}にあった{O}、見た？", "見たよ。誰かが置いていったみたい。"],
   "es": ["¿Viste {el_O} que está en {el_P}?", "Sí, alguien {lo_O} dejó ahí."]}),
 ("N12", "Ana", "OH", "The entrance of a community center", "volunteers", "By the door", "glass", None,
  "So what are they taking, and where?",
  {"en": ["Take {the_O} to {the_P}.", "After lunch."], "zh": ["把{O}送到{P}那儿去。", "吃完午饭再说。"],
   "ja": ["{O}を{P}へ運んでおいて。", "昼ご飯のあとでね。"], "es": ["Lleva {el_O} {al_P}.", "Después del almuerzo."]}),
 ("N13", "Tom", "DA", "The loading area behind a grocery store", "A store worker", None, "street", "worker",
  "So what do we drop off, and where?",
  {"en": ["Put {the_O} {at_P}. The owner will sign later."], "zh": ["把{O}放在{P}那儿，老板待会儿签字。"],
   "ja": ["{O}は{P}に置いといて。店主があとで署名する。"], "es": ["Deja {el_O} en {el_P}. El dueño firma más tarde."]}),
 ("N14", "Tom", "DA", "The doorstep of a house", "An elderly woman", None, "street", "old lady",
  "So what does she want left, and where?",
  {"en": ["Leave {the_O} {at_P}, please. My knees are bad."], "zh": ["请把{O}放在{P}那儿吧，我的膝盖不好。"],
   "ja": ["{O}は{P}に置いてくださいな。膝が悪くてね。"],
   "es": ["Deje {el_O} en {el_P}, por favor. Me duelen las rodillas."]}),
 ("N15", "Tom", "OH", "A parcel depot yard", "drivers", "By the next van", "window", None,
  "So what's being dropped off, and where?",
  {"en": ["Did you drop {the_O} off {at_P}?", "Not yet. I'm going now."], "zh": ["{O}送到{P}那儿了吗？", "还没，马上去。"],
   "ja": ["{O}は{P}に届けた？", "まだだ。これから行く。"],
   "es": ["¿Ya entregaste {el_O} en {el_P}?", "Todavía no. Voy para allá."]}),
 ("N16", "Tom", "OH", "A roadside café", "mechanics", "At the counter", "glass", None,
  "So what's still there, and where?",
  {"en": ["{The_O} is still {at_P}.", "Then the customer can wait."], "zh": ["{O}还在{P}那儿。", "那就让客人等着吧。"],
   "ja": ["{O}はまだ{P}にある。", "なら客には待ってもらおう。"], "es": ["{El_O} sigue en {el_P}.", "Entonces que espere el cliente."]}),
]
SINGULAR = {"old men": "old man"}


def skeletons():
    personas = json.loads((ROOT / "data" / "personas.json").read_text(encoding="utf-8"))["original"]
    items = []
    for sid, who_p, mode, loc, who, nearby, noise, noun, q_task, tpl in TABLE:
        name = personas[who_p]["short_name"]
        scene = {"location": loc}
        if mode == "DA":
            scene.update(speaker=who, speaker_label=who.split(" ", 1)[1],
                         e_inaud_description=NOISE[noise].format(Speaker=who, name=name))
            q_content = f"What did the {noun} say?"
        else:
            one = SINGULAR.get(who, who[:-1])
            scene.update(people=who, nearby=nearby, speaker_labels=[f"first {one}", f"second {one}"],
                         e_inaud_description=NOISE[noise].format(people=who, name=name))
            q_content = "What were those two saying?"
        items.append({"id": sid, "set": "real", "world": "real", "mode": mode, "character": who_p, "scene": scene,
                      "skeleton_en": tpl["en"], "questions": {"content": q_content, "task": q_task}})
    out = ROOT / "items" / "real" / "skeletons_en.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"version": "real-en-0.1-draft", "items": items}, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    print(f"{len(items)} skeletons -> {out.relative_to(ROOT)}")


def render():
    vs = load_valueset()
    base = {i["id"]: i for i in json.loads((ROOT / "items" / "real" / "skeletons_en.json").read_text(encoding="utf-8"))["items"]}
    slots = json.loads((ROOT / "items" / "real" / "assignment.json").read_text(encoding="utf-8"))["slots"]
    tpls = {row[0]: row[-1] for row in TABLE}
    items = []
    for sid, it in base.items():
        it = json.loads(json.dumps(it))
        it["langs"] = {}
        for lang in ("zh", "ja", "es"):
            it["langs"][lang] = {}
            for ver in ("A", "B"):
                pl, ob = slots[sid][lang][ver]["PLACE"], slots[sid][lang][ver]["OBJECT"]
                tok = es_tokens(vs, pl, ob) if lang == "es" else {"O": vs["by_id"][ob][lang]["form"],
                                                                  "P": vs["by_id"][pl][lang]["form"]}
                it["langs"][lang][ver] = {"PLACE": pl, "OBJECT": ob, "lines": [fill(x, tok) for x in tpls[sid][lang]],
                                          "gold": [fill(x, en_tokens(pl, ob)) for x in tpls[sid]["en"]]}
        items.append(it)
    out = ROOT / "items" / "real" / "skeletons.json"
    out.write_text(json.dumps({"version": "real-0.1-draft", "items": items}, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    print(f"{len(items)} items -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    {"skeletons": skeletons, "render": render}[sys.argv[1]]()

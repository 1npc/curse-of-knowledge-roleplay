"""Noise stimuli (proposal 5.6 step 4), deterministic per item, language and kind.

  N1: every word replaced. ja keeps the kanji/kana pattern character by character (so the
      ratio matches exactly), zh replaces every hanzi, es builds Spanish-like pseudo-words of
      matched length. Punctuation and sentence count are kept.
  N2: Jabberwocky, function words kept and content words replaced (pilot comparison only).

Kanji and hanzi come from pools of rare characters outside the value-set semantic fields
(places and portable objects); no value form or kana reading may appear in a noise line,
and each es pseudo-word stays below 0.5 similarity to every value form. The dictionary
checks the proposal asks for (MeCab/UniDic for ja, Hunspell or Wuggy for es) need packages
and run later on the remote side; until then noise lines are marked dictionary_check=pending.
"""
from __future__ import annotations

import hashlib
import random
import re
from functools import lru_cache

from .gate import ES_FUNCTION, load_valueset
from .phon import similarity
from .translit import ascii_fold

JA_KANJI_POOL = ("丐丕乂乖亟亢亰亳亶仍仄仆仂仞仟伉佚佝佗佇佶侈侏佻佰侑佯侖俔俟俛俚俐倚倨倔倪倥倅俶倡倩倬俾偃偕偐偈偖偬"
                 "傀傚傅傴僉僊僂僖僥僭儁儂儕儔儚儺儷儼兀兌兢兪兮冀冉冏冕冤冦冪冱冲冽凅凩凭凰刎刧刪刮刳剏剄剋剌剞剔")
ZH_HANZI_POOL = "丐丕乂乖亟亢亳亶仍仄仆仂仞仟伉佚佝佗佇佶侈侏佻佰侑佯俟俚俐倚倨倔倪倥倅俶倡倩倬俾偃偕偈偬傀傅僖僭兀兢兮冀冉冕冤冽凅凭凰刎刮刳剌剔"
HIRAGANA_POOL = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわ"
ZH_FUNCTION = set("的了在把你我他她它们吗呢吧就也都还又说要让给这那有没不别快去来上里边儿啊哪呀么")
JA_NUMERAL_KANA = ("ひとつ", "ふたつ", "みっつ", "よっつ", "いつつ", "むっつ", "ななつ", "やっつ", "ここのつ", "ひとり", "ふたり")
ES_ONSETS = ["b", "c", "d", "f", "g", "j", "l", "m", "n", "p", "r", "s", "t", "v", "ch", "ll", "br", "pl", "tr", "gr",
             "cr", "fl", "bl", "fr", "pr"]
ES_VOWELS = ["a", "e", "i", "o", "u"]
ES_CODAS = ["", "", "", "n", "s", "l", "r"]
# a small lexicon of common Spanish words that pseudo-words must avoid (dictionary check pending)
ES_COMMON = {"casa", "cosa", "mesa", "pero", "para", "todo", "nada", "bien", "malo", "mano", "vida", "gente", "hora",
             "dia", "vez", "tiempo", "noche", "tarde", "luna", "sol", "mar", "rio", "pan", "vino", "boca", "cara", "pelo",
             "pie", "ojo", "dedo", "loco", "rojo", "gato", "perro", "toro", "lobo", "bala", "cama", "sala", "pala", "lana",
             "rana", "pena", "cena", "vela", "tela", "gala", "rata", "lata", "nata", "bota", "gota", "nota", "rosa",
             "misa", "risa", "sopa", "ropa", "copa", "papa", "mama", "tia", "tio", "mira", "dame", "vete", "dile",
             "sale", "vale", "tiene", "viene", "puede", "sabe", "dice", "hace", "pone", "tira", "toma", "lleva", "pasa"}


def _rng(item_id: str, lang: str, kind: str) -> random.Random:
    return random.Random(int(hashlib.sha256(f"{item_id}|{lang}|{kind}".encode()).hexdigest()[:16], 16))


@lru_cache(maxsize=None)
def _value_strings(lang: str) -> tuple[list[str], list[str]]:
    vs = load_valueset()
    forms, readings = [], []
    for v in vs["values"]:
        spec = v[lang]
        for f in [spec] + spec.get("alt", []):
            forms.append(f["form"])
            if lang == "ja" and f.get("reading"):
                readings.append(f["reading"])
    return forms, readings


def _ok_cjk(line: str, lang: str) -> bool:
    forms, readings = _value_strings(lang)
    if any(f in line for f in forms):
        return False
    if lang == "ja" and (any(r in line for r in readings) or any(n in line for n in JA_NUMERAL_KANA)):
        return False
    return True


def _pseudo_word(rng: random.Random, target_len: int) -> str:
    w = ""
    while len(w) < target_len:
        w += rng.choice(ES_ONSETS) + rng.choice(ES_VOWELS)
        if rng.random() < 0.3 and len(w) < target_len - 1:
            w += rng.choice(ES_CODAS)
    return w


def _ok_es_word(w: str) -> bool:
    forms, _ = _value_strings("es")
    if w in ES_COMMON or w in ES_FUNCTION:
        return False
    return all(similarity(w, ascii_fold(f).replace(" ", "")) < 0.5 for f in forms)


def _es_line(line: str, rng: random.Random, keep_function: bool) -> str:
    def repl(m):
        tok = m.group(0)
        if keep_function and tok.lower() in ES_FUNCTION:
            return tok
        n = max(2, len(tok) + rng.choice([-1, 0, 0, 1]))
        for _ in range(200):
            w = _pseudo_word(rng, n)
            if _ok_es_word(w):
                break
        return w.capitalize() if tok[0].isupper() else w
    return re.sub(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", repl, line)


def _cjk_line(line: str, rng: random.Random, lang: str, keep_function: bool, canary_kana: list[str]) -> str:
    protect = [False] * len(line)
    for k in canary_kana:  # canaries written in kana are content, never kept
        for m in re.finditer(re.escape(k), line):
            for i in range(m.start(), m.end()):
                protect[i] = True
    out = []
    for i, c in enumerate(line):
        is_kana = "ぁ" <= c <= "ゖ"
        is_han = "一" <= c <= "鿿"
        if lang == "ja":
            if is_han:
                out.append(rng.choice(JA_KANJI_POOL))
            elif is_kana and (not keep_function or protect[i]):
                out.append(rng.choice(HIRAGANA_POOL))
            else:
                out.append(c)
        else:
            if is_han and not (keep_function and c in ZH_FUNCTION):
                out.append(rng.choice(ZH_HANZI_POOL))
            else:
                out.append(c)
    return "".join(out)


def noise_lines(item: dict, lang: str, kind: str = "N1") -> list[str]:
    """Noise version of the item's A lines. kind: N1 (all replaced) or N2 (function words kept)."""
    src = item["langs"][lang]["A"]["lines"]
    keep = kind == "N2"
    vs = load_valueset()
    canary_kana = [vs["by_id"][item["langs"][lang][v][t]][lang]["form"]
                   for v in ("A", "B") for t in ("PLACE", "OBJECT")] if lang == "ja" else []
    rng = _rng(item["id"], lang, kind)
    out = []
    for line in src:
        for _ in range(500):
            if lang == "es":
                cand = _es_line(line, rng, keep)
                ok = True
            else:
                cand = _cjk_line(line, rng, lang, keep, canary_kana)
                ok = _ok_cjk(cand, lang)
            if ok:
                break
        else:
            raise RuntimeError(f"no acceptable noise for {item['id']} {lang} {kind}")
        out.append(cand)
    return out

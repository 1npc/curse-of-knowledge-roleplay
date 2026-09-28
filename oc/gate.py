"""Automatic stimulus screen (proposal 5.4 rules 1-8, plus A/B identity and pairing checks).

Each check returns messages tagged "reject" or "warn". Rejections block an item version;
warnings go to manual review. Rule 9 (word-form guessability) is a human test and lives in
tools/guessability_questionnaire.py; the dictionary checks for noise strings (MeCab,
Hunspell) need packages and run later outside this machine.
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from .phon import double_metaphone, similarity
from .translit import ascii_fold, variants

ROOT = Path(__file__).resolve().parent.parent
SIM_REJECT = 0.5      # rule 4: normalized Levenshtein similarity at or above this rejects
PREFIX_N = 3          # rule 4: identical first three letters rejects
LENGTH = {"ja": (15, 40), "zh": (15, 40), "es": (8, 25)}   # rule 8: characters (ja/zh) or words (es)
LANG_NAME = {"zh": "Chinese", "ja": "Japanese", "es": "Spanish"}

# ---------------------------------------------------------------- word lists (rules 1-3, 5)
ZH_JA_NUMERALS = set("零〇一二三四五六七八九十百千万億亿兩两")
JA_KANA_NUMERALS = ("ひとつ", "ふたつ", "みっつ", "よっつ", "いつつ", "むっつ", "ななつ", "やっつ", "ここのつ",
                    "ひとり", "ふたり")
ES_NUMERALS = {"uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once", "doce",
               "trece", "catorce", "quince", "dieciséis", "veinte", "treinta", "cuarenta", "cincuenta", "sesenta",
               "setenta", "ochenta", "noventa", "cien", "ciento", "cientos", "mil", "millón", "primero", "primera",
               "segundo", "segunda", "tercero", "tercera", "cuarto", "cuarta", "quinto", "quinta", "medio", "media",
               "mitad", "par", "docena"}
ES_ARTICLE_ONE = {"un", "una"}   # indefinite articles double as "one": warn only
PROPER_NOUNS = [
    # Night City and franchise names in English, Japanese and Chinese renderings
    "Arasaka", "荒坂", "Militech", "Kang Tao", "康陶", "Biotechnica", "Trauma Team", "NCPD", "Night City", "夜之城",
    "Watson", "Westbrook", "Heywood", "Pacifica", "Santo Domingo", "City Center", "Japantown", "日本町", "Kabuki",
    "Afterlife", "Badlands", "Aldecaldo", "Maelstrom", "Valentino", "Tyger Claws", "虎爪", "Voodoo Boys", "Animals",
    "Mox", "Wraiths", "Raffen", "Kiroshi", "Samurai", "Johnny", "Jackie", "Judy", "Panam", "Kerry", "Rogue",
    "Viktor", "Takemura", "竹村", "Saburo", "三郎", "Yorinobu", "頼宣", "赖宣", "Hanako", "華子", "华子", "Misty",
    "Maiko", "舞子", "Goro", "吾朗", "杰克", "朱迪", "帕南", "克里", "罗格", "维克托", "Silverhand", "银手",
]
ZH_TRANSLITERATIONS = ["咖啡", "沙发", "巧克力", "披萨", "比萨", "汉堡", "可乐", "吉他", "沙拉", "卡车", "巴士", "的士",
                       "坦克", "雷达", "马达", "模特", "幽默", "逻辑", "引擎", "芭蕾", "维他命", "啤酒", "香槟",
                       "白兰地", "威士忌", "伏特加", "咖喱", "柠檬", "扑克", "高尔夫", "保龄", "马拉松", "吗啡",
                       "尼古丁", "雪茄", "纳米", "赛博", "朋克", "黑客", "粉丝", "博客", "拷贝", "沙龙",
                       "派对", "迪斯科", "摩托", "吉普", "麦克风", "克隆", "基因", "布丁", "吐司", "奶昔", "卡片"]
# single characters that are loans in some words but native in others (酷 in 残酷, 秀 in 优秀): warn only
ZH_LOAN_CHARS_WARN = ["酷", "秀", "卡"]
ES_LOANS = {"bar", "club", "email", "internet", "fútbol", "futbol", "béisbol", "sándwich", "hotel", "taxi", "gol",
            "líder", "estrés", "chip", "parking", "show", "test", "web", "ok", "okay", "cóctel", "whisky", "jeans",
            "bistec", "champú", "suéter", "radio", "piano", "video", "vídeo", "chocolate", "café", "pizza",
            "hospital", "animal", "doctor", "auto", "bus", "autobús", "metro", "música", "teléfono", "televisión",
            "policía", "banco", "garaje", "momento", "problema", "plan", "idea", "general", "normal", "total",
            "final", "natural", "robot", "motor", "túnel", "tren", "hamburguesa", "computadora", "cámara"}
FAMILIAR = {
    "es": {"hola", "adiós", "gracias", "amigo", "amiga", "casa", "noche", "señor", "señora", "sí", "fiesta", "loco",
           "bueno", "jefe", "por favor", "mañana", "agua", "dinero", "perro", "gato", "mucho", "vamos", "cocina",
           "manta", "sombrero", "hombre", "mujer", "niño"},
    "ja": {"はし", "さけ", "すし", "かわいい", "ありがとう", "さようなら", "こんにちは", "せんせい", "ねこ", "いぬ"},
    "zh": {"ni hao", "xie xie", "kung fu"},
}
ES_FUNCTION = {"el", "la", "los", "las", "un", "una", "unos", "unas", "al", "del", "de", "a", "en", "y", "o", "que",
               "se", "lo", "le", "les", "me", "te", "nos", "mi", "mis", "tu", "tus", "su", "sus", "no", "por", "para",
               "con", "sin", "es", "está", "están", "como", "pero", "si", "ya", "muy", "más", "otra", "otro", "esa",
               "ese", "esta", "este", "eso", "esto", "cerca", "junto", "dónde", "donde", "qué", "quién", "cómo"}


@lru_cache(maxsize=None)
def load_valueset(path: str | None = None) -> dict:
    p = Path(path) if path else ROOT / "data" / "valueset.json"
    vs = json.loads(p.read_text(encoding="utf-8"))
    vs["by_id"] = {v["id"]: v for v in vs["values"]}
    return vs


def all_en_aliases(vs: dict) -> dict[str, str]:
    """alias (lowercase) -> value id, across all values."""
    return {a.lower(): v["id"] for v in vs["values"] for a in v["en"]}


# ---------------------------------------------------------------- rule 4: cognate screen
def _alias_forms(alias: str) -> set[str]:
    folded = ascii_fold(alias)
    out = {folded.replace(" ", "")}
    out |= {w for w in folded.split() if len(w) >= 3}
    return out


def cognate_check(lang: str, form: str, reading: str | None, aliases: list[str]) -> dict:
    """Compare every ASCII rendering of a foreign form with every English alias (rule 4)."""
    whole = variants(lang, form, reading)
    spaced = variants(lang, form, reading, keep_spaces=True)
    cands = set(whole) | {w for f in spaced for w in f.split() if len(w) >= 3}
    best = {"sim": 0.0, "pair": None}
    prefix_hits, dm_hits = [], []
    for v in sorted(cands):
        dm_v = double_metaphone(v)[0]
        for alias in aliases:
            for af in sorted(_alias_forms(alias)):
                s = similarity(v, af)
                if s > best["sim"]:
                    best = {"sim": s, "pair": [v, af]}
                if len(v) >= PREFIX_N and len(af) >= PREFIX_N and v[:PREFIX_N] == af[:PREFIX_N]:
                    prefix_hits.append([v, af])
                if dm_v and dm_v == double_metaphone(af)[0]:
                    dm_hits.append([v, af, dm_v])
    reasons = []
    if best["sim"] >= SIM_REJECT:
        reasons.append(f"levenshtein {best['sim']:.2f} {best['pair']}")
    if prefix_hits:
        reasons.append(f"prefix {prefix_hits[0]}")
    if dm_hits:
        reasons.append(f"metaphone {dm_hits[0]}")
    return {"reject": bool(reasons), "reasons": reasons, "max_sim": round(best["sim"], 3),
            "max_pair": best["pair"], "renderings": sorted(cands),
            "metaphone": {v: double_metaphone(v)[0] for v in sorted(cands)}}


def screen_value(vs: dict, value_id: str, lang: str) -> dict:
    v = vs["by_id"][value_id]
    f = v[lang]
    res = cognate_check(lang, f["form"], f.get("reading"), v["en"])
    warn = (v.get("familiarity_warning") or {}).get(lang)
    if warn:
        res["familiarity_warning"] = warn
    return res


# ---------------------------------------------------------------- stimulus-level rules
def _msg(level, rule, text):
    return {"level": level, "rule": rule, "text": text}


def _stim_length(lang: str, text: str) -> int:
    if lang == "es":
        return len(re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", text))
    return len([c for c in text if not c.isspace()])


def es_tokens(text: str) -> list[str]:
    return re.findall(r"[a-záéíóúüñ]+", unicodedata.normalize("NFC", text.lower()))


def screen_text(lang: str, text: str) -> list[dict]:
    """Rules 1-3 and 5 on a full stimulus (all lines joined)."""
    out = []
    if re.search(r"[0-9\uff10-\uff19]", text):
        out.append(_msg("reject", 1, "Arabic digit"))
    if lang in ("ja", "zh"):
        if re.search(r"[A-Za-z\uff21-\uff3a\uff41-\uff5a]", text):
            out.append(_msg("reject", 1, "Latin letters inside a non-Latin stimulus"))
        nums = sorted({c for c in text if c in ZH_JA_NUMERALS})
        if nums:
            out.append(_msg("reject", 1, f"numeral characters {nums}"))
    if lang == "ja":
        for w in JA_KANA_NUMERALS:
            if w in text:
                out.append(_msg("reject", 1, f"kana numeral {w}"))
        if re.search(r"[\u30a0-\u30ff\u31f0-\u31ff\uff65-\uff9f]", text):
            out.append(_msg("reject", 3, "katakana (loanwords are banned in ja stimuli)"))
    if lang == "zh":
        for w in ZH_TRANSLITERATIONS:
            if w in text:
                out.append(_msg("reject", 3, f"transliterated loanword {w}"))
        for w in ZH_LOAN_CHARS_WARN:
            if w in text:
                out.append(_msg("warn", 3, f"character {w} is a loan in some words"))
    if lang == "es":
        toks = es_tokens(text)
        for t in toks:
            if t in ES_NUMERALS:
                out.append(_msg("reject", 1, f"numeral {t}"))
            if t in ES_ARTICLE_ONE:
                out.append(_msg("warn", 1, f"indefinite article {t} (also 'one')"))
            if t in ES_LOANS:
                out.append(_msg("reject", 3, f"loan or international word {t}"))
        # a capitalized word that does not open a sentence may be a proper noun
        for sentence in re.split(r"[.!?¿¡«»\"“”:]+", text):
            words = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", sentence)
            for w in words[1:]:
                if w[0].isupper():
                    out.append(_msg("warn", 2, f"capitalized word {w} (proper noun?)"))
    low = text.lower()
    for name in PROPER_NOUNS:
        if name.lower() in low:
            out.append(_msg("reject", 2, f"proper noun {name}"))
    fam = FAMILIAR.get(lang, set())
    if lang == "es":
        toks = " " + " ".join(es_tokens(text)) + " "
        for w in sorted(fam):
            if f" {w} " in toks:
                out.append(_msg("warn", 5, f"familiar word {w}"))
    return out


def _es_normalize_agreement(tokens: list[str]) -> list[str]:
    """Collapse gender/number agreement so A and B may differ only there (proposal 5.4 note on es)."""
    out = []
    for t in tokens:
        if t == "al":
            out += ["a", "el"]
            continue
        if t == "del":
            out += ["de", "el"]
            continue
        # articles, clitics, demonstratives and possessives may agree with the canary noun (tijeras is plural)
        t = {"la": "el", "las": "el", "los": "el", "lo": "el", "una": "un", "unas": "un", "unos": "un",
             "esta": "este", "estas": "este", "estos": "este", "esa": "ese", "esas": "ese", "esos": "ese",
             "aquella": "aquel", "aquellas": "aquel", "aquellos": "aquel", "tuya": "tuyo", "tuyas": "tuyo",
             "tuyos": "tuyo", "suya": "suyo", "suyas": "suyo", "suyos": "suyo", "mía": "mío", "mías": "mío",
             "míos": "mío"}.get(t, t)
        if t in ("este", "ese", "aquel", "tuyo", "suyo", "mío"):
            out.append(t)
            continue
        m = re.match(r"^(\w+?(?:ar|er|ir|ando|iendo))(la|lo|las|los)$", t)
        if m:
            t = m.group(1) + "lo"
        t = re.sub(r"(o|a)s?$", "o", t) if len(t) > 3 else t
        out.append(t)
    return out


def ab_identity(lang: str, a_text: str, b_text: str, a_forms: list[str], b_forms: list[str]) -> list[dict]:
    """A and B must be identical once the canary forms are masked (es: agreement may differ)."""
    def mask(text, forms):
        for f in sorted(forms, key=len, reverse=True):
            text = re.sub(re.escape(f), "〈C〉", text, flags=re.I)
        return text
    ma, mb = mask(a_text, a_forms), mask(b_text, b_forms)
    if lang == "es":
        ta = _es_normalize_agreement(es_tokens(ma.replace("〈C〉", " cxc ")))
        tb = _es_normalize_agreement(es_tokens(mb.replace("〈C〉", " cxc ")))
        if ta != tb:
            return [_msg("reject", "AB", f"A/B differ beyond canaries and agreement: {ta} vs {tb}")]
        if ma != mb:
            return [_msg("warn", "AB", "A/B differ in agreement only (checker confirms)")]
        return []
    if ma != mb:
        return [_msg("reject", "AB", f"A/B differ beyond canaries: {ma!r} vs {mb!r}")]
    return []


def value_forms(vs: dict, value_id: str, lang: str) -> list[str]:
    f = vs["by_id"][value_id][lang]
    return [f["form"]] + [a["form"] for a in f.get("alt", [])]


def foreign_value_hits(vs: dict, lang: str, text: str, allowed: set[str]) -> list[str]:
    """Value-set foreign forms present in `text` other than the allowed canary values.

    Forms are consumed longest first, so the canary 桟橋 (pier) does not also count as 橋 (bridge).
    """
    forms = sorted(((f, v["id"]) for v in vs["values"] for f in value_forms(vs, v["id"], lang)),
                   key=lambda x: len(x[0]), reverse=True)
    rest = text.lower() if lang == "es" else text
    hits = []
    for f, vid in forms:
        key = f.lower() if lang == "es" else f
        if lang == "es":
            pat = r"(?<![a-záéíóúüñ])" + re.escape(key) + r"(?![a-záéíóúüñ])"
            found = re.search(pat, rest)
            rest = re.sub(pat, " ", rest)
        else:
            found = key in rest
            rest = rest.replace(key, "　")
        if found and vid not in allowed:
            hits.append(f"{vid}:{f}")
    return hits


def en_alias_hits(vs: dict, text: str) -> list[str]:
    low = " " + re.sub(r"[^a-z' -]", " ", text.lower()) + " "
    hits = []
    for alias, vid in all_en_aliases(vs).items():
        if re.search(r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])", low):
            hits.append(f"{vid}:{alias}")
    return sorted(set(hits))


def screen_item(item: dict, vs: dict | None = None) -> dict:
    """Screen every language/version of one skeleton item. Returns {lang: {version: [messages]}}."""
    vs = vs or load_valueset()
    report = {"id": item["id"], "langs": {}, "item": []}
    # English side: questions, scene text and gold must carry no stray value words
    for key in ("content", "task", "check", "plan"):
        q = item.get("questions", {}).get(key)
        if q and en_alias_hits(vs, q):
            report["item"].append(_msg("reject", 7, f"question {key} contains value words {en_alias_hits(vs, q)}"))
    for key, text in item.get("scene", {}).items():
        if isinstance(text, str) and en_alias_hits(vs, text):
            report["item"].append(_msg("reject", 7, f"scene.{key} contains value words {en_alias_hits(vs, text)}"))
    pairs_seen = {}
    for lang, versions in item["langs"].items():
        lang_rep = {}
        conf = {frozenset(p[:2]) for p in vs.get("confusable_pairs", {}).get(lang, [])}
        for ver in ("A", "B"):
            v = versions[ver]
            msgs = []
            text = "".join(v["lines"]) if lang != "es" else " ".join(v["lines"])
            msgs += screen_text(lang, text)
            lo, hi = LENGTH[lang]
            n = _stim_length(lang, text)
            if not lo <= n <= hi:
                msgs.append(_msg("reject", 8, f"length {n} outside {lo}-{hi}"))
            canaries = {v["PLACE"], v["OBJECT"]}
            for typ in ("PLACE", "OBJECT"):
                vid = v[typ]
                if vs["by_id"][vid]["type"] != typ:
                    msgs.append(_msg("reject", "type", f"{vid} is not a {typ}"))
                form = vs["by_id"][vid][lang]["form"]
                masked = text
                for other in {f for v2 in vs["values"] for f in value_forms(vs, v2["id"], lang)}:
                    if len(other) > len(form) and form in other:  # e.g. 橋 inside 桟橋
                        masked = masked.replace(other, "　")
                count = len(re.findall(re.escape(form), masked, flags=re.I))
                if count != 1:
                    msgs.append(_msg("reject", "canary", f"{typ} form {form} occurs {count} times"))
                cg = screen_value(vs, vid, lang)
                if cg["reject"]:
                    msgs.append(_msg("reject", 4, f"{typ} {vid} {form}: {'; '.join(cg['reasons'])}"))
                if cg.get("familiarity_warning"):
                    msgs.append(_msg("warn", 5, f"{vid}: {cg['familiarity_warning']}"))
            stray = foreign_value_hits(vs, lang, text, canaries)
            if stray:
                msgs.append(_msg("reject", "multi", f"other value-set forms in the stimulus: {stray}"))
            gold = " ".join(v["gold"])
            gold_vals = {h.split(":")[0] for h in en_alias_hits(vs, gold)}
            if gold_vals != canaries:
                msgs.append(_msg("reject", "gold", f"gold names values {sorted(gold_vals)}, expected {sorted(canaries)}"))
            if lang == "es":
                for w in v.get("content_words", []):
                    if w.get("gloss"):
                        cg = cognate_check("es", w["form"], None, [g.strip() for g in w["gloss"].split("/")])
                        if cg["reject"]:
                            msgs.append(_msg("warn", 6, f"non-canary cognate {w['form']}~{w['gloss']}: {'; '.join(cg['reasons'])}"))
            lang_rep[ver] = msgs
        a, b = versions["A"], versions["B"]
        for typ in ("PLACE", "OBJECT"):
            if a[typ] == b[typ]:
                lang_rep["A"].append(_msg("reject", "swap", f"A and B share the {typ} value {a[typ]}"))
            if frozenset((a[typ], b[typ])) in conf:
                lang_rep["A"].append(_msg("reject", "confusable", f"{a[typ]}/{b[typ]} are confusable in {lang}"))
        joiner = "" if lang != "es" else " "
        lang_rep["A"] += ab_identity(lang, joiner.join(a["lines"]), joiner.join(b["lines"]),
                                     [vs["by_id"][a[t]][lang]["form"] for t in ("PLACE", "OBJECT")],
                                     [vs["by_id"][b[t]][lang]["form"] for t in ("PLACE", "OBJECT")])
        pairs_seen[lang] = {(a["PLACE"], a["OBJECT"]), (b["PLACE"], b["OBJECT"])}
        report["langs"][lang] = lang_rep
    langs = list(pairs_seen)
    for i, l1 in enumerate(langs):
        for l2 in langs[i + 1:]:
            shared = pairs_seen[l1] & pairs_seen[l2]
            if shared:
                report["item"].append(_msg("reject", "rotation", f"{l1} and {l2} reuse value pairs {sorted(shared)}"))
    return report


def rejected(report: dict) -> bool:
    return any(m["level"] == "reject" for m in report["item"]) or any(
        m["level"] == "reject" for lv in report["langs"].values() for msgs in lv.values() for m in msgs)

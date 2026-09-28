"""ASCII transliterations used by the stimulus screen and by echo removal.

Kanji and hanzi readings cannot be derived without a dictionary, so every Japanese and
Chinese form in the item files carries a hand-authored reading (hiragana for ja,
toneless pinyin with space-separated syllables for zh). This module only converts those
readings into several ASCII schemes, so that each foreign form is compared with English
under more than one plausible romanization (proposal 5.4, rule 4).

  ja: wapuro Hepburn (long vowels as typed), traditional Hepburn and Kunrei-shiki
      (long vowels collapsed, as when macrons or circumflexes are dropped);
  zh: toneless pinyin and Wade-Giles (apostrophes and umlauts dropped);
  es: accents stripped, and a variant spelling n-tilde as "ny".
"""
from __future__ import annotations

import re
import unicodedata

# hiragana -> (Hepburn, Kunrei)
_BASE = {
    "あ": ("a", "a"), "い": ("i", "i"), "う": ("u", "u"), "え": ("e", "e"), "お": ("o", "o"),
    "か": ("ka", "ka"), "き": ("ki", "ki"), "く": ("ku", "ku"), "け": ("ke", "ke"), "こ": ("ko", "ko"),
    "さ": ("sa", "sa"), "し": ("shi", "si"), "す": ("su", "su"), "せ": ("se", "se"), "そ": ("so", "so"),
    "た": ("ta", "ta"), "ち": ("chi", "ti"), "つ": ("tsu", "tu"), "て": ("te", "te"), "と": ("to", "to"),
    "な": ("na", "na"), "に": ("ni", "ni"), "ぬ": ("nu", "nu"), "ね": ("ne", "ne"), "の": ("no", "no"),
    "は": ("ha", "ha"), "ひ": ("hi", "hi"), "ふ": ("fu", "hu"), "へ": ("he", "he"), "ほ": ("ho", "ho"),
    "ま": ("ma", "ma"), "み": ("mi", "mi"), "む": ("mu", "mu"), "め": ("me", "me"), "も": ("mo", "mo"),
    "や": ("ya", "ya"), "ゆ": ("yu", "yu"), "よ": ("yo", "yo"),
    "ら": ("ra", "ra"), "り": ("ri", "ri"), "る": ("ru", "ru"), "れ": ("re", "re"), "ろ": ("ro", "ro"),
    "わ": ("wa", "wa"), "ゐ": ("i", "i"), "ゑ": ("e", "e"), "を": ("o", "o"), "ん": ("n", "n"),
    "が": ("ga", "ga"), "ぎ": ("gi", "gi"), "ぐ": ("gu", "gu"), "げ": ("ge", "ge"), "ご": ("go", "go"),
    "ざ": ("za", "za"), "じ": ("ji", "zi"), "ず": ("zu", "zu"), "ぜ": ("ze", "ze"), "ぞ": ("zo", "zo"),
    "だ": ("da", "da"), "ぢ": ("ji", "zi"), "づ": ("zu", "zu"), "で": ("de", "de"), "ど": ("do", "do"),
    "ば": ("ba", "ba"), "び": ("bi", "bi"), "ぶ": ("bu", "bu"), "べ": ("be", "be"), "ぼ": ("bo", "bo"),
    "ぱ": ("pa", "pa"), "ぴ": ("pi", "pi"), "ぷ": ("pu", "pu"), "ぺ": ("pe", "pe"), "ぽ": ("po", "po"),
    "ぁ": ("a", "a"), "ぃ": ("i", "i"), "ぅ": ("u", "u"), "ぇ": ("e", "e"), "ぉ": ("o", "o"),
    "ゔ": ("vu", "vu"), "ゎ": ("wa", "wa"),
}
# i-row kana that combine with a small ya/yu/yo: (Hepburn stem, Kunrei stem)
_YOON = {
    "き": ("ky", "ky"), "ぎ": ("gy", "gy"), "し": ("sh", "sy"), "じ": ("j", "zy"), "ち": ("ch", "ty"),
    "ぢ": ("j", "zy"), "に": ("ny", "ny"), "ひ": ("hy", "hy"), "び": ("by", "by"), "ぴ": ("py", "py"),
    "み": ("my", "my"), "り": ("ry", "ry"),
}
_SMALL_Y = {"ゃ": "a", "ゅ": "u", "ょ": "o"}
JA_SCHEMES = ("wapuro", "hepburn", "kunrei")


def katakana_to_hiragana(s: str) -> str:
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def _morae(kana: str):
    """Split hiragana into morae as (hepburn, kunrei) pairs; sokuon, n and the long mark kept as markers."""
    s = katakana_to_hiragana(unicodedata.normalize("NFKC", kana))
    out, i = [], 0
    while i < len(s):
        c = s[i]
        nxt = s[i + 1] if i + 1 < len(s) else ""
        if c in _YOON and nxt in _SMALL_Y:
            h, k = _YOON[c]
            v = _SMALL_Y[nxt]
            out.append((h + v, k + v))
            i += 2
            continue
        if c == "っ":
            out.append(("<Q>", "<Q>"))
        elif c == "ー":
            out.append(("<L>", "<L>"))
        elif c in _BASE:
            out.append(_BASE[c])
        elif c.isspace() or c in "・、。「」":
            out.append((" ", " "))
        else:
            raise ValueError(f"cannot romanize {c!r} in {kana!r}; readings must be kana")
        i += 1
    return out


def kana_to_romaji(kana: str, scheme: str = "hepburn") -> str:
    """Romanize a kana reading. Output is lowercase ASCII with spaces kept as word breaks."""
    if scheme not in JA_SCHEMES:
        raise ValueError(scheme)
    idx = 1 if scheme == "kunrei" else 0
    morae = [m[idx] for m in _morae(kana)]
    out = []
    for j, m in enumerate(morae):
        nxt = morae[j + 1] if j + 1 < len(morae) else ""
        if m == "<Q>":  # geminate the next consonant
            if nxt and nxt[0] not in "aeiou <":
                out.append("t" if (scheme == "hepburn" and nxt.startswith("ch")) else nxt[0])
            continue
        if m == "<L>":  # katakana long mark: repeat the vowel (wapuro) or drop it
            if scheme == "wapuro" and out and out[-1][-1:] in "aeiou":
                out.append(out[-1][-1])
            continue
        if m == "n" and scheme == "hepburn" and nxt[:1] in ("b", "m", "p"):
            out.append("m")
            continue
        prev_vowel = out[-1][-1:] if out else ""
        if scheme != "wapuro" and ((m == "u" and prev_vowel in ("o", "u")) or (m == "o" and prev_vowel == "o")):
            continue  # long vowel written with a macron or circumflex, dropped in ASCII
        out.append(m)
    return re.sub(r"\s+", " ", "".join(out)).strip()


# ---------------------------------------------------------------- Chinese
_PY_INITIALS = ("zh", "ch", "sh", "b", "p", "m", "f", "d", "t", "n", "l", "g", "k", "h", "j", "q", "x", "r", "z", "c", "s")
_WG_INITIAL = {"b": "p", "p": "p'", "m": "m", "f": "f", "d": "t", "t": "t'", "n": "n", "l": "l", "g": "k", "k": "k'",
               "h": "h", "j": "ch", "q": "ch'", "x": "hs", "zh": "ch", "ch": "ch'", "sh": "sh", "r": "j", "z": "ts",
               "c": "ts'", "s": "s"}
_WG_WHOLE = {"zi": "tzu", "ci": "tz'u", "si": "ssu", "zhi": "chih", "chi": "ch'ih", "shi": "shih", "ri": "jih",
             "er": "erh", "e": "o",
             "yi": "i", "ya": "ya", "ye": "yeh", "yao": "yao", "you": "yu", "yan": "yen", "yin": "yin",
             "yang": "yang", "ying": "ying", "yong": "yung", "yu": "yü", "yue": "yüeh", "yuan": "yüan",
             "yun": "yün", "yo": "yo",
             "wu": "wu", "wa": "wa", "wo": "wo", "wai": "wai", "wei": "wei", "wan": "wan", "wen": "wen",
             "wang": "wang", "weng": "weng"}
_UO_TO_O = {"d", "t", "n", "l", "z", "c", "s", "zh", "ch", "r"}


def _norm_pinyin(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower().replace("u:", "ü").replace("v", "ü")
    # drop tone marks but keep ü
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn" or c == "\u0308")
    return unicodedata.normalize("NFC", s)


def pinyin_syllable_to_wg(syl: str) -> str:
    s = _norm_pinyin(syl).strip("'")
    if s in _WG_WHOLE:
        return _WG_WHOLE[s]
    ini = next((i for i in _PY_INITIALS if s.startswith(i)), "")
    fin = s[len(ini):]
    if ini in ("j", "q", "x") and fin.startswith("u"):
        fin = "ü" + fin[1:]
    if fin == "e" and ini in ("g", "k", "h"):
        fin = "o"
    elif fin == "uo" and ini in _UO_TO_O:
        fin = "o"
    elif fin == "ui" and ini in ("g", "k"):
        fin = "uei"
    else:
        fin = {"ong": "ung", "iong": "iung", "ie": "ieh", "ian": "ien", "üe": "üeh", "ue": "üeh"}.get(fin, fin)
    return _WG_INITIAL.get(ini, ini) + fin


def pinyin_to_wade_giles(pinyin: str) -> str:
    """Space-separated pinyin syllables -> Wade-Giles syllables joined by hyphens."""
    return "-".join(pinyin_syllable_to_wg(s) for s in pinyin.split())


# ---------------------------------------------------------------- ASCII variants
def ascii_fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z ]", "", s)


def variants(lang: str, surface: str, reading: str | None = None, *, keep_spaces: bool = False) -> list[str]:
    """ASCII renderings of a foreign form, deduplicated, in a stable order.

    ja and zh need `reading` (kana / toneless pinyin). Spaces separate words; they are removed
    unless keep_spaces is set (the screen compares whole forms and single words separately).
    """
    if lang == "ja":
        if not reading:
            raise ValueError(f"ja form {surface!r} needs a kana reading")
        forms = [kana_to_romaji(reading, s) for s in JA_SCHEMES]
    elif lang == "zh":
        if not reading:
            raise ValueError(f"zh form {surface!r} needs a pinyin reading")
        py = _norm_pinyin(reading)
        forms = [py.replace("ü", "u"), py.replace("ü", "yu"),
                 " ".join(ascii_fold(pinyin_syllable_to_wg(w)) for w in py.split())]
        # Wade-Giles syllables form one word when the pinyin syllables were one word
        forms = [f if keep_spaces else f.replace(" ", "") for f in forms]
    elif lang in ("es", "ru_translit", "en"):
        low = unicodedata.normalize("NFC", surface.lower())
        forms = [ascii_fold(low), ascii_fold(low.replace("ñ", "ny"))]
    else:
        raise ValueError(lang)
    out = []
    for f in forms:
        f = ascii_fold(f)
        f = re.sub(r"\s+", " " if keep_spaces else "", f).strip()
        if f and f not in out:
            out.append(f)
    return out

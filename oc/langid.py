"""Reply-language flag L (proposal 6.1 step 3), standard library only.

Verbatim quotes of the stimulus are removed first (ja/zh runs of >= 6 characters, es runs of
>= 3 words, design values), then the rest is classified:
  - CJK or kana make up more than 20% of the letters -> not English;
  - Spanish function words outnumber English ones (at least 3) -> not English.
Every L = 1 reply goes to human review, so this errs toward flagging.
"""
from __future__ import annotations

import re
import unicodedata

MIN_CJK_RUN = 6
MIN_ES_WORDS = 3
CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff]")
LATIN = re.compile(r"[A-Za-z\u00c0-\u00ff]")
ES_FW = {"el", "la", "los", "las", "de", "que", "y", "en", "un", "una", "es", "por", "para", "con", "se", "lo", "del",
         "al", "pero", "más", "muy", "está", "son", "como", "su", "sus", "yo", "tú", "él", "ella", "nosotros", "qué",
         "dónde", "aquí", "allí", "sí", "también", "porque", "cuando", "hay", "fue", "era", "esta", "este", "eso"}
EN_FW = {"the", "and", "of", "to", "is", "it", "that", "you", "in", "for", "on", "with", "was", "he", "she", "they",
         "we", "what", "this", "be", "are", "at", "but", "not", "have", "just", "i", "my", "your", "me", "him", "her",
         "if", "so", "there", "about", "don't", "can't", "it's", "that's", "i'm", "let's", "an"}


def stimulus_spans(text: str, stimulus_lines: list[str], lang: str) -> list[str]:
    """Substrings of `text` that quote the stimulus verbatim (both versions should be passed in)."""
    spans = []
    if lang in ("ja", "zh"):
        for line in stimulus_lines:
            src = re.sub(r"\s+", "", line)
            n = len(src)
            i = 0
            while i < n:
                best = 0
                for j in range(n, i + MIN_CJK_RUN - 1, -1):
                    if src[i:j] in text:
                        best = j - i
                        break
                if best >= MIN_CJK_RUN:
                    spans.append(src[i:i + best])
                    i += best
                else:
                    i += 1
    else:
        low = unicodedata.normalize("NFC", text.lower())
        for line in stimulus_lines:
            words = re.findall(r"[\wáéíóúüñ]+", unicodedata.normalize("NFC", line.lower()))
            n = len(words)
            i = 0
            while i < n:
                best = 0
                for j in range(n, i + MIN_ES_WORDS - 1, -1):
                    pat = r"(?<!\w)" + r"\W+".join(map(re.escape, words[i:j])) + r"(?!\w)"
                    if re.search(pat, low):
                        best = j - i
                        break
                if best >= MIN_ES_WORDS:
                    spans.append(r"\W+".join(map(re.escape, words[i:i + best])))
                    i += best
                else:
                    i += 1
    return spans


def remove_spans(text: str, spans: list[str], lang: str) -> str:
    if lang in ("ja", "zh"):
        for s in sorted(spans, key=len, reverse=True):
            text = text.replace(s, " ")
        return text
    for pat in spans:
        text = re.sub(r"(?<!\w)" + pat + r"(?!\w)", " ", text, flags=re.I)
    return text


def is_non_english(text: str) -> tuple[bool, dict]:
    letters = LATIN.findall(text)
    cjk = CJK.findall(text)
    total = len(letters) + len(cjk)
    cjk_share = len(cjk) / total if total else 0.0
    words = re.findall(r"[a-záéíóúüñ']+", unicodedata.normalize("NFC", text.lower()))
    es = sum(w in ES_FW for w in words)
    en = sum(w in EN_FW for w in words)
    inverted = bool(re.search(r"[¿¡]", text))
    flag = cjk_share > 0.2 or (es >= 3 and es > en) or (inverted and es >= 2 and es >= en)
    return flag, {"cjk_share": round(cjk_share, 3), "es_fw": es, "en_fw": en, "inverted_punct": inverted}


def reply_language_flag(text: str, stimulus_lines: list[str], lang: str) -> tuple[bool, dict, list[str]]:
    spans = stimulus_spans(text, stimulus_lines, lang)
    rest = remove_spans(text, spans, lang)
    flag, detail = is_non_english(rest)
    return flag, detail, spans

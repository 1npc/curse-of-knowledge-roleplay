"""String and phonetic similarity for the cognate screen: normalized Levenshtein and Double Metaphone.

Double Metaphone follows Lawrence Philips' reference algorithm (C++ original, 2000) as
commonly ported; codes are capped at four characters like the reference. Only the primary
code is used by the screen (proposal 5.4, rule 4), the secondary is kept for review.
"""
from __future__ import annotations

import unicodedata


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def similarity(a: str, b: str) -> float:
    """1 - distance / max(len); 0.0 for two empty strings is avoided by returning 1.0."""
    if not a and not b:
        return 1.0
    return 1.0 - levenshtein(a, b) / max(len(a), len(b))


_VOWELS = set("AEIOUY")


def double_metaphone(word: str, max_len: int = 4) -> tuple[str, str]:
    """Return (primary, secondary) Double Metaphone codes; secondary equals primary when there is none."""
    st = unicodedata.normalize("NFC", word.upper())
    # keep Ç and Ñ, fold other accents
    st = "".join(c if c in "ÇÑ" else "".join(x for x in unicodedata.normalize("NFD", c) if not unicodedata.combining(x))
                 for c in st)
    st = "".join(c for c in st if c.isalpha() or c == " ")
    length = len(st)
    if length == 0:
        return "", ""
    last = length - 1
    pad = st + "     "
    pri, sec = [], []
    slavo = any(x in st for x in ("W", "K", "CZ", "WITZ"))

    def at(start, n, *subs):
        return start >= 0 and pad[start:start + n] in subs

    def vowel(pos):
        return 0 <= pos < length and st[pos] in _VOWELS

    def add(p, s=None):
        pri.append(p)
        sec.append(p if s is None else s)

    cur = 0
    if at(0, 2, "GN", "KN", "PN", "WR", "PS"):
        cur += 1
    if st[0] == "X":
        add("S")
        cur += 1

    while (len("".join(pri)) < max_len or len("".join(sec)) < max_len) and cur < length:
        ch = st[cur]
        if ch in _VOWELS:
            if cur == 0:
                add("A")
            cur += 1
        elif ch == "B":
            add("P")
            cur += 2 if pad[cur + 1] == "B" else 1
        elif ch == "Ç":
            add("S")
            cur += 1
        elif ch == "C":
            if (cur > 1 and not vowel(cur - 2) and at(cur - 1, 3, "ACH")
                    and pad[cur + 2] != "I" and (pad[cur + 2] != "E" or at(cur - 2, 6, "BACHER", "MACHER"))):
                add("K"); cur += 2
            elif cur == 0 and at(cur, 6, "CAESAR"):
                add("S"); cur += 2
            elif at(cur, 4, "CHIA"):
                add("K"); cur += 2
            elif at(cur, 2, "CH"):
                if cur > 0 and at(cur, 4, "CHAE"):
                    add("K", "X")
                elif cur == 0 and (at(cur + 1, 5, "HARAC", "HARIS") or at(cur + 1, 3, "HOR", "HYM", "HIA", "HEM")) \
                        and not at(0, 5, "CHORE"):
                    add("K")
                elif (at(0, 4, "VAN ", "VON ") or at(0, 3, "SCH")
                      or at(cur - 2, 6, "ORCHES", "ARCHIT", "ORCHID")
                      or at(cur + 2, 1, "T", "S")
                      or ((at(cur - 1, 1, "A", "O", "U", "E") or cur == 0)
                          and at(cur + 2, 1, "L", "R", "N", "M", "B", "H", "F", "V", "W", " "))):
                    add("K")
                elif cur > 0:
                    add("K") if at(0, 2, "MC") else add("X", "K")
                else:
                    add("X")
                cur += 2
            elif at(cur, 2, "CZ") and not at(cur - 2, 4, "WICZ"):
                add("S", "X"); cur += 2
            elif at(cur + 1, 3, "CIA"):
                add("X"); cur += 3
            elif at(cur, 2, "CC") and not (cur == 1 and st[0] == "M"):
                if at(cur + 2, 1, "I", "E", "H") and not at(cur + 2, 2, "HU"):
                    if (cur == 1 and st[0] == "A") or at(cur - 1, 5, "UCCEE", "UCCES"):
                        add("KS")
                    else:
                        add("X")
                    cur += 3
                else:
                    add("K"); cur += 2
            elif at(cur, 2, "CK", "CG", "CQ"):
                add("K"); cur += 2
            elif at(cur, 2, "CI", "CE", "CY"):
                add("S", "X") if at(cur, 3, "CIO", "CIE", "CIA") else add("S")
                cur += 2
            else:
                add("K")
                if at(cur + 1, 2, " C", " Q", " G"):
                    cur += 3
                elif at(cur + 1, 1, "C", "K", "Q") and not at(cur + 1, 2, "CE", "CI"):
                    cur += 2
                else:
                    cur += 1
        elif ch == "D":
            if at(cur, 2, "DG"):
                if at(cur + 2, 1, "I", "E", "Y"):
                    add("J"); cur += 3
                else:
                    add("TK"); cur += 2
            elif at(cur, 2, "DT", "DD"):
                add("T"); cur += 2
            else:
                add("T"); cur += 1
        elif ch == "F":
            add("F")
            cur += 2 if pad[cur + 1] == "F" else 1
        elif ch == "G":
            if pad[cur + 1] == "H":
                if cur > 0 and not vowel(cur - 1):
                    add("K"); cur += 2
                elif cur == 0:
                    add("J") if pad[cur + 2] == "I" else add("K")
                    cur += 2
                elif ((cur > 1 and at(cur - 2, 1, "B", "H", "D"))
                      or (cur > 2 and at(cur - 3, 1, "B", "H", "D"))
                      or (cur > 3 and at(cur - 4, 1, "B", "H"))):
                    cur += 2
                else:
                    if cur > 2 and st[cur - 1] == "U" and at(cur - 3, 1, "C", "G", "L", "R", "T"):
                        add("F")
                    elif cur > 0 and st[cur - 1] != "I":
                        add("K")
                    cur += 2
            elif pad[cur + 1] == "N":
                if cur == 1 and vowel(0) and not slavo:
                    add("KN", "N")
                elif not at(cur + 2, 2, "EY") and pad[cur + 1] != "Y" and not slavo:
                    add("N", "KN")
                else:
                    add("KN")
                cur += 2
            elif at(cur + 1, 2, "LI") and not slavo:
                add("KL", "L"); cur += 2
            elif cur == 0 and (pad[cur + 1] == "Y" or at(cur + 1, 2, "ES", "EP", "EB", "EL", "EY", "IB", "IL", "IN",
                                                          "IE", "EI", "ER")):
                add("K", "J"); cur += 2
            elif ((at(cur + 1, 2, "ER") or pad[cur + 1] == "Y") and not at(0, 6, "DANGER", "RANGER", "MANGER")
                  and not at(cur - 1, 1, "E", "I") and not at(cur - 1, 3, "RGY", "OGY")):
                add("K", "J"); cur += 2
            elif at(cur + 1, 1, "E", "I", "Y") or at(cur - 1, 4, "AGGI", "OGGI"):
                if at(0, 4, "VAN ", "VON ") or at(0, 3, "SCH") or at(cur + 1, 2, "ET"):
                    add("K")
                elif at(cur + 1, 4, "IER "):
                    add("J")
                else:
                    add("J", "K")
                cur += 2
            else:
                add("K")
                cur += 2 if pad[cur + 1] == "G" else 1
        elif ch == "H":
            if (cur == 0 or vowel(cur - 1)) and vowel(cur + 1):
                add("H"); cur += 2
            else:
                cur += 1
        elif ch == "J":
            if at(cur, 4, "JOSE") or at(0, 4, "SAN "):
                if (cur == 0 and pad[cur + 4] == " ") or at(0, 4, "SAN "):
                    add("H")
                else:
                    add("J", "H")
                cur += 1
                continue
            if cur == 0 and not at(cur, 4, "JOSE"):
                add("J", "A")
            elif vowel(cur - 1) and not slavo and pad[cur + 1] in ("A", "O"):
                add("J", "H")
            elif cur == last:
                add("J", "")
            elif not at(cur + 1, 1, "L", "T", "K", "S", "N", "M", "B", "Z") and not at(cur - 1, 1, "S", "K", "L"):
                add("J")
            cur += 2 if pad[cur + 1] == "J" else 1
        elif ch == "K":
            add("K")
            cur += 2 if pad[cur + 1] == "K" else 1
        elif ch == "L":
            if pad[cur + 1] == "L":
                if ((cur == length - 3 and at(cur - 1, 4, "ILLO", "ILLA", "ALLE"))
                        or ((at(last - 1, 2, "AS", "OS") or at(last, 1, "A", "O")) and at(cur - 1, 4, "ALLE"))):
                    add("L", ""); cur += 2
                    continue
                cur += 2
            else:
                cur += 1
            add("L")
        elif ch == "M":
            if (at(cur - 1, 3, "UMB") and (cur + 1 == last or at(cur + 2, 2, "ER"))) or pad[cur + 1] == "M":
                cur += 2
            else:
                cur += 1
            add("M")
        elif ch == "N":
            add("N")
            cur += 2 if pad[cur + 1] == "N" else 1
        elif ch == "Ñ":
            add("N")
            cur += 1
        elif ch == "P":
            if pad[cur + 1] == "H":
                add("F"); cur += 2
            else:
                add("P")
                cur += 2 if at(cur + 1, 1, "P", "B") else 1
        elif ch == "Q":
            add("K")
            cur += 2 if pad[cur + 1] == "Q" else 1
        elif ch == "R":
            if cur == last and not slavo and at(cur - 2, 2, "IE") and not at(cur - 4, 2, "ME", "MA"):
                add("", "R")
            else:
                add("R")
            cur += 2 if pad[cur + 1] == "R" else 1
        elif ch == "S":
            if at(cur - 1, 3, "ISL", "YSL"):
                cur += 1
            elif cur == 0 and at(cur, 5, "SUGAR"):
                add("X", "S"); cur += 1
            elif at(cur, 2, "SH"):
                add("S") if at(cur + 1, 4, "HEIM", "HOEK", "HOLM", "HOLZ") else add("X")
                cur += 2
            elif at(cur, 3, "SIO", "SIA") or at(cur, 4, "SIAN"):
                add("S") if slavo else add("S", "X")
                cur += 3
            elif (cur == 0 and at(cur + 1, 1, "M", "N", "L", "W")) or at(cur + 1, 1, "Z"):
                add("S", "X")
                cur += 2 if at(cur + 1, 1, "Z") else 1
            elif at(cur, 2, "SC"):
                if pad[cur + 2] == "H":
                    if at(cur + 3, 2, "OO", "ER", "EN", "UY", "ED", "EM"):
                        add("X", "SK") if at(cur + 3, 2, "ER", "EN") else add("SK")
                    elif cur == 0 and not vowel(3) and pad[3] != "W":
                        add("X", "S")
                    else:
                        add("X")
                elif at(cur + 2, 1, "I", "E", "Y"):
                    add("S")
                else:
                    add("SK")
                cur += 3
            else:
                if cur == last and at(cur - 2, 2, "AI", "OI"):
                    add("", "S")
                else:
                    add("S")
                cur += 2 if at(cur + 1, 1, "S", "Z") else 1
        elif ch == "T":
            if at(cur, 4, "TION"):
                add("X"); cur += 3
            elif at(cur, 3, "TIA", "TCH"):
                add("X"); cur += 3
            elif at(cur, 2, "TH") or at(cur, 3, "TTH"):
                if at(cur + 2, 2, "OM", "AM") or at(0, 4, "VAN ", "VON ") or at(0, 3, "SCH"):
                    add("T")
                else:
                    add("0", "T")
                cur += 2
            else:
                add("T")
                cur += 2 if at(cur + 1, 1, "T", "D") else 1
        elif ch == "V":
            add("F")
            cur += 2 if pad[cur + 1] == "V" else 1
        elif ch == "W":
            if at(cur, 2, "WR"):
                add("R"); cur += 2
                continue
            if cur == 0 and (vowel(cur + 1) or at(cur, 2, "WH")):
                add("A", "F") if vowel(cur + 1) else add("A")
            if (cur == last and vowel(cur - 1)) or at(cur - 1, 5, "EWSKI", "EWSKY", "OWSKI", "OWSKY") \
                    or at(0, 3, "SCH"):
                add("", "F"); cur += 1
            elif at(cur, 4, "WICZ", "WITZ"):
                add("TS", "FX"); cur += 4
            else:
                cur += 1
        elif ch == "X":
            if not (cur == last and (at(cur - 3, 3, "IAU", "EAU") or at(cur - 2, 2, "AU", "OU"))):
                add("KS")
            cur += 2 if at(cur + 1, 1, "C", "X") else 1
        elif ch == "Z":
            if pad[cur + 1] == "H":
                add("J"); cur += 2
                continue
            if at(cur + 1, 2, "ZO", "ZI", "ZA") or (slavo and cur > 0 and st[cur - 1] != "T"):
                add("S", "TS")
            else:
                add("S")
            cur += 2 if pad[cur + 1] == "Z" else 1
        else:
            cur += 1
    return "".join(pri)[:max_len], "".join(sec)[:max_len]

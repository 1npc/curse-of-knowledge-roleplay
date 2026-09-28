"""Read-only language-evidence search for the character x language eligibility table.

For each Cyberpunk 2077 NPC in the NPCBank release, scan the character's collected
sources (wiki pages, web transcripts, SoundDB subtitle exports) for
  - mentions of a language name (e.g. "Japanese", "Spanish"),
  - the character's own lines that carry that language: kiroshi translation tags
    (<kiroshi l="jpn" .../>) or characters of the language's script,
  - lines addressed to the character that carry a kiroshi tag (the character hears it).

A character x language pair is eligible for the declared set only when the character's
documents contain neither the language name nor own lines in that language/script
(proposal 5.3). Mentions are listed with a short context window for manual review;
dialogue text is never copied into the report (game lines are copyrighted); --contexts
prints short mention windows to the terminal for manual review only.

Usage: python3 tools/eligibility.py [--npcbank PATH] [--out docs/eligibility.json]
Standard library only. Never writes inside the NPCBank tree.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT_NPCBANK = Path("/Users/xiaozhang/PycharmProjects/NPCBank")
UNIVERSE = "npcbank/universes/cyberpunk_2077/characters"
# The ten Cyberpunk NPCs of the NPCBank 1.0.0 release (proposal 5.3).
CHARACTERS = ["Goro_Takemura", "Jackie_Welles", "Johnny_Silverhand", "Judy_Alvarez", "Kerry_Eurodyne",
              "Maiko_Maeda", "Misty_Olszewski", "Panam_Palmer", "Rogue_Amendiares", "Viktor_Vektor"]

LANGS = {
    "zh": {"names": [r"chinese", r"mandarin", r"cantonese"], "kiroshi": {"chn", "zho", "cmn", "yue"},
           "script": re.compile(r"[\u4e00-\u9fff]")},
    "ja": {"names": [r"japanese", r"nihongo"], "kiroshi": {"jpn"},
           "script": re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")},
    "es": {"names": [r"spanish", r"espa[nñ]ol", r"spanglish"], "kiroshi": {"mex", "spa", "esp"},
           "script": None},
    "ru": {"names": [r"russian"], "kiroshi": {"rus"}, "script": re.compile(r"[\u0400-\u04ff]")},
    "ht": {"names": [r"creole", r"krey[oò]l", r"haitian"], "kiroshi": {"hat", "cre"}, "script": None},
}
# Spanish own-line markers: inverted punctuation, n-tilde, and words an English line would not contain.
ES_WORDS = re.compile(
    r"(?<![a-záéíóúñ])(hermano|mano|chica|chico|cabr[oó]n|v[aá]monos|chingada|chingad[oa]|pinche|[oó]rale|[aá]ndale|"
    r"pendej[oa]|mierda|gracias|cari[nñ]o|mij[oa]|abuel[ao]|qu[eé] onda|dios m[ií]o|por favor|adi[oó]s|hola|"
    r"claro que|bueno|loc[oa]|g[uü]ey|nena|chul[oa]|carnal|compa|vato|cállate|oye|pues|se[nñ]or|se[nñ]ora|"
    r"amig[oa]|puta|co[nñ]o|madre|pap[aá]|mam[aá]|vieja|chamba|ay dios)(?![a-záéíóúñ])", re.I)
ES_CHARS = re.compile(r"[¿¡ñÑ]")
KIROSHI = re.compile(r"<kiroshi\s+([^>]*)/?>", re.I)
ATTR = re.compile(r'(\w+)="([^"]*)"')
# Whole-game transcript mirror (shared source); speaker prefixes identify each NPC's own lines.
TRANSCRIPT = "npcbank/universes/cyberpunk_2077/characters/Panam_Palmer/crawl/raw/web/transcript_mirror/cp77_dump.json"
SPEAKER = {"Goro_Takemura": "Takemura", "Jackie_Welles": "Jackie", "Johnny_Silverhand": "Johnny",
           "Judy_Alvarez": "Judy", "Kerry_Eurodyne": "Kerry", "Maiko_Maeda": "Maiko",
           "Misty_Olszewski": "Misty", "Panam_Palmer": "Panam", "Rogue_Amendiares": "Rogue",
           "Viktor_Vektor": "Viktor"}
# The transcript mirror covers the whole game, so language-name hits inside it are not about the NPC.
SHARED_SOURCES = ("transcript_mirror/",)


def transcript_own_lines(root: Path):
    """Map speaker prefix -> list of that speaker's lines in the whole-game transcript."""
    d = json.loads((root / TRANSCRIPT).read_text(encoding="utf-8"))
    text = html.unescape(re.sub(r"<[^>]+>", " ", d["html"]))
    parts = re.split(r"(?=\b[A-Z][A-Za-z'’. ]{1,25}:\s)", text)
    lines = defaultdict(list)
    for p in parts:
        m = re.match(r"([A-Z][A-Za-z'’. ]{1,25}):\s", p)
        if m:
            lines[m.group(1).strip()].append(p[m.end():].strip())
    return lines


def spanish_hits(text: str):
    return [w.lower() for w in ES_WORDS.findall(text)] + ES_CHARS.findall(text)


def sounddb_items(path: Path):
    """Yield subtitle items from a SoundDB export (.json wrapper whose 'html' holds the API JSON)."""
    try:
        wrapper = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return
    raw = wrapper.get("html")
    if not isinstance(raw, str) or not raw.lstrip().startswith("{"):
        return
    try:
        inner = json.loads(raw)
    except json.JSONDecodeError:
        return
    yield from inner.get("items", [])


def item_texts(item):
    for gender in ("female", "male"):
        t = (item.get(gender) or {}).get("text")
        if t:
            yield gender, t


def plain_text(path: Path) -> str:
    """Visible text of a wiki/web source file (JSON wrapper or HTML)."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".json":
        try:
            d = json.loads(raw)
        except json.JSONDecodeError:
            return raw
        parts = []
        for key in ("debug_plain_text_preview", "text", "content", "html"):
            v = d.get(key) if isinstance(d, dict) else None
            if isinstance(v, str):
                parts.append(v)
        raw = "\n".join(parts) if parts else raw
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(raw))


def scan_character(root: Path, name: str):
    base = root / UNIVERSE / name
    res = {"character": name, "files_scanned": 0,
           "mentions": defaultdict(list), "own_lines": defaultdict(Counter),
           "heard_kiroshi": Counter(), "kiroshi_codes_own": Counter(),
           "spanish_words": Counter(), "spanish_item_ids": set()}
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.suffix not in (".json", ".html", ".txt", ".md"):
            continue
        rel = path.relative_to(root).as_posix()
        if "/sounddb/" in rel:
            if path.suffix != ".json":
                continue  # the .html twin holds the same API payload
            res["files_scanned"] += 1
            own = path.stem.endswith("_actor")
            seen = set()
            for item in sounddb_items(path):
                for _, text in item_texts(item):
                    key = (item.get("id"), text)
                    if key in seen:
                        continue
                    seen.add(key)
                    tags = [dict(ATTR.findall(m.group(1))) for m in KIROSHI.finditer(text)]
                    codes = {t.get("l", "").lower() for t in tags}
                    if not own:
                        for c in codes:
                            res["heard_kiroshi"][c] += 1
                        continue
                    for c in codes:
                        res["kiroshi_codes_own"][c] += 1
                    visible = KIROSHI.sub(" ", text)
                    for lang, spec in LANGS.items():
                        if codes & spec["kiroshi"]:
                            res["own_lines"][lang]["kiroshi"] += 1
                        if spec["script"] is not None and spec["script"].search(visible):
                            res["own_lines"][lang]["script"] += 1
                    hits = spanish_hits(visible)
                    if hits:
                        res["own_lines"]["es"]["spanish_words"] += 1
                        res["spanish_words"].update(hits)
                        res["spanish_item_ids"].add(item.get("id"))
            continue
        res["files_scanned"] += 1
        if any(s in rel for s in SHARED_SOURCES):
            continue
        text = plain_text(path)
        for lang, spec in LANGS.items():
            for pat in spec["names"]:
                for m in re.finditer(r"(?<![A-Za-z])" + pat + r"(?![A-Za-z])", text, re.I):
                    lo, hi = max(0, m.start() - 60), min(len(text), m.end() + 60)
                    res["mentions"][lang].append({"file": rel, "context": text[lo:hi].strip()})
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--npcbank", type=Path, default=DEFAULT_NPCBANK)
    ap.add_argument("--out", type=Path, default=Path("docs/eligibility.json"))
    ap.add_argument("--contexts", action="store_true",
                    help="print mention contexts to the terminal for manual review (never written to the report)")
    a = ap.parse_args()
    out = []
    transcript = transcript_own_lines(a.npcbank)
    for name in CHARACTERS:
        r = scan_character(a.npcbank, name)
        mentions = {lang: {"count": len(v), "files": sorted({x["file"].split("/")[-1] for x in v})}
                    for lang, v in r["mentions"].items()}
        if a.contexts:
            for lang, v in r["mentions"].items():
                for x in v[:12]:
                    print(f"  [{name} {lang}] {x['file'].split('/')[-1]}: {x['context'][:140]}")
        own_t = transcript.get(SPEAKER[name], [])
        t_es = [spanish_hits(l) for l in own_t]
        t_summary = {"own_lines": len(own_t),
                     "lines_with_spanish_words": sum(1 for h in t_es if h),
                     "spanish_words": dict(Counter(w for h in t_es for w in h)),
                     "lines_with_cjk": sum(1 for l in own_t if LANGS["ja"]["script"].search(l)),
                     "lines_with_cyrillic": sum(1 for l in own_t if LANGS["ru"]["script"].search(l))}
        out.append({"character": name, "files_scanned": r["files_scanned"], "mentions": mentions,
                    "sounddb_own_lines": {k: dict(v) for k, v in r["own_lines"].items()},
                    "sounddb_spanish_words": dict(r["spanish_words"]),
                    "sounddb_spanish_item_ids": sorted(r["spanish_item_ids"]),
                    "kiroshi_codes_own": dict(r["kiroshi_codes_own"]),
                    "heard_kiroshi": dict(r["heard_kiroshi"]),
                    "transcript": t_summary})
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for r in out:
        flags = []
        for lang in LANGS:
            m = r["mentions"].get(lang, {}).get("count", 0)
            o = sum(r["sounddb_own_lines"].get(lang, {}).values())
            flags.append(f"{lang}:m{m}/o{o}")
        t = r["transcript"]
        print(f"{r['character']:<18} files={r['files_scanned']:<3} " + " ".join(flags)
              + f" | kiroshi own={r['kiroshi_codes_own']} heard={r['heard_kiroshi']}"
              + f" | transcript own={t['own_lines']} es_lines={t['lines_with_spanish_words']}"
              + f" {t['spanish_words']} cjk={t['lines_with_cjk']}")


if __name__ == "__main__":
    main()

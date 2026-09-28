"""Unit tests for transliteration, phonetic keys, the stimulus screen, prompt building and scoring.

Run: python3 -m unittest discover -s tests -v   (standard library only)
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from oc import patterns as P  # noqa: E402
from oc.build import D1, build_item, build_robustness, load_personas  # noqa: E402
from oc.gate import cognate_check, en_alias_hits, load_valueset, rejected, screen_item, screen_text  # noqa: E402
from oc.noise import noise_lines  # noqa: E402
from oc.phon import double_metaphone, similarity  # noqa: E402
from oc.score import ItemContext, score_reply  # noqa: E402
from oc.translit import kana_to_romaji, pinyin_to_wade_giles, variants  # noqa: E402

ITEMS = json.loads((ROOT / "items" / "pilot" / "skeletons.json").read_text(encoding="utf-8"))["items"]
VS = load_valueset()


class TestTranslit(unittest.TestCase):
    def test_kana(self):
        self.assertEqual(kana_to_romaji("きょうかい", "wapuro"), "kyoukai")
        self.assertEqual(kana_to_romaji("きょうかい", "hepburn"), "kyokai")
        self.assertEqual(kana_to_romaji("しゃしん", "kunrei"), "syasin")
        self.assertEqual(kana_to_romaji("まっちゃ", "hepburn"), "matcha")
        self.assertEqual(kana_to_romaji("しんぶん", "hepburn"), "shimbun")
        self.assertEqual(kana_to_romaji("がっこう", "wapuro"), "gakkou")
        self.assertEqual(kana_to_romaji("テーブル", "wapuro"), "teeburu")

    def test_wade_giles(self):
        self.assertEqual(pinyin_to_wade_giles("cang ku"), "ts'ang-k'u")
        self.assertEqual(pinyin_to_wade_giles("xue xiao"), "hsüeh-hsiao")
        self.assertEqual(pinyin_to_wade_giles("zi ji"), "tzu-chi")
        self.assertEqual(pinyin_to_wade_giles("guo jia"), "kuo-chia")
        self.assertEqual(pinyin_to_wade_giles("duo shao"), "to-shao")
        self.assertEqual(pinyin_to_wade_giles("zhi shi"), "chih-shih")

    def test_variants(self):
        self.assertEqual(variants("es", "sótano"), ["sotano"])
        self.assertIn("tsangku", variants("zh", "仓库", "cang ku"))
        self.assertEqual(variants("ja", "倉庫", "そうこ"), ["souko", "soko"])


class TestPhon(unittest.TestCase):
    def test_similarity_matches_proposal(self):
        # values recomputed in the proposal (appendix B)
        self.assertAlmostEqual(similarity("bao", "bag"), 0.67, places=2)
        self.assertAlmostEqual(similarity("callejon", "alley"), 0.50, places=2)
        self.assertAlmostEqual(similarity("souko", "warehouse"), 0.22, places=2)
        self.assertAlmostEqual(similarity("norte", "north"), 0.80, places=2)

    def test_double_metaphone(self):
        self.assertEqual(double_metaphone("Smith"), ("SM0", "XMT"))
        self.assertEqual(double_metaphone("Schmidt"), ("XMT", "SMT"))
        self.assertEqual(double_metaphone("Xavier"), ("SF", "SFR"))
        self.assertEqual(double_metaphone("knight")[0], "NT")
        self.assertEqual(double_metaphone("mercado")[0], double_metaphone("market")[0])


class TestGate(unittest.TestCase):
    def test_all_candidate_values_pass_rule4(self):
        for v in VS["values"]:
            for lang in ("zh", "ja", "es"):
                f = v[lang]
                r = cognate_check(lang, f["form"], f.get("reading"), v["en"])
                self.assertFalse(r["reject"], (v["id"], lang, r["reasons"]))

    def test_known_cognates_rejected(self):
        for lang, form, reading, en in [("es", "estación", None, "station"), ("es", "norte", None, "north"),
                                        ("es", "mercado", None, "market"), ("zh", "包", "bao", "bag")]:
            self.assertTrue(cognate_check(lang, form, reading, [en])["reject"], form)

    def test_aliases_unique(self):
        seen = {}
        for v in VS["values"]:
            for a in v["en"]:
                self.assertNotIn(a, seen, (a, seen.get(a), v["id"]))
                seen[a] = v["id"]

    def test_pilot_items_pass(self):
        for it in ITEMS:
            r = screen_item(it, VS)
            self.assertFalse(rejected(r), json.dumps(r, ensure_ascii=False)[:600])

    def test_es_agreement_allowed(self):
        from oc.gate import ab_identity
        self.assertEqual(ab_identity("es", "¿Quién dejó este sobre en el muelle?", "¿Quién dejó esta caja en la iglesia?",
                                     ["sobre", "muelle"], ["caja", "iglesia"]),
                         [{"level": "warn", "rule": "AB", "text": "A/B differ in agreement only (checker confirms)"}])

    def test_rule_1_to_3(self):
        self.assertTrue(any(m["rule"] == 3 for m in screen_text("ja", "タクシーは橋のそばにある。")))
        self.assertTrue(any(m["rule"] == 1 for m in screen_text("zh", "一个箱子在桥那边。")))
        self.assertTrue(any(m["rule"] == 1 for m in screen_text("es", "La caja está en el puente dos.")))
        self.assertTrue(any(m["rule"] == 2 for m in screen_text("ja", "荒坂の倉庫にある。")))


class TestBuild(unittest.TestCase):
    def test_counts(self):
        for it in ITEMS:
            for lang in ("zh", "ja", "es"):
                recs = build_item(it, lang)
                main = [r for r in recs if not r["arm"].startswith("probe")]
                probes = [r for r in recs if r["arm"].startswith("probe")]
                self.assertEqual(len(main), 128, (it["id"], lang))
                self.assertEqual(len(probes), 15, (it["id"], lang))
                self.assertEqual(len({r["prompt_id"] for r in recs}), len(recs))
                pilot = build_item(it, lang, pilot=True)
                self.assertEqual(len(pilot), 163)
                self.assertEqual(len(build_robustness(it, lang)), 30)

    def test_no_value_words_outside_speech(self):
        """Rule 7: no alias in model-visible input except the speech text itself."""
        for it in ITEMS:
            for lang in ("zh", "ja", "es"):
                for r in build_item(it, lang, pilot=True) + build_robustness(it, lang):
                    for m in r["messages"]:
                        text = m["content"]
                        state = re.search(r"\[State\] (\{.*\})", text)
                        if state:
                            st = json.loads(state.group(1))
                            text = text.replace(state.group(1), json.dumps(
                                {**st, "scene": {**st["scene"], "speech_events": []}}))
                        if r["arm"] == "probe_translate":
                            continue
                        self.assertEqual(en_alias_hits(VS, text), [], (r["prompt_id"], m["role"]))

    def test_foreign_text_identical_across_cells(self):
        it = ITEMS[0]
        texts = set()
        for r in build_item(it, "ja"):
            if r["S"] == "real" and r["version"] == "A" and not r["arm"].startswith("probe"):
                st = json.loads(re.search(r"\[State\] (\{.*\})", r["messages"][0]["content"]).group(1))
                texts.add(json.dumps([e["text"] for e in st["scene"]["speech_events"]], ensure_ascii=False))
        self.assertEqual(len(texts), 1)

    def test_d1_lengths_matched(self):
        for version in (0, 1):
            fmt = {"name": "Kerry", "L": "Japanese", "them": "him", "their": "his", "they": "he"}
            a = len(D1["C-T-"][version].format(**fmt).split())
            b = len(D1["C-Toff"][version].format(**fmt).split())
            self.assertLessEqual(abs(a - b), 3, (version, a, b))

    def test_personas_clean(self):
        for name, p in load_personas().items():
            self.assertLessEqual(len(p["card"].split()), 150, name)
            self.assertEqual(en_alias_hits(VS, p["card"]), [], name)
            self.assertIsNone(re.search(r"japanese|chinese|mandarin|spanish|language|fluent", p["card"], re.I), name)

    def test_noise(self):
        for it in ITEMS:
            for lang in ("zh", "ja", "es"):
                for kind in ("N1", "N2"):
                    n = noise_lines(it, lang, kind)
                    self.assertEqual(len(n), len(it["langs"][lang]["A"]["lines"]))
                    if lang == "ja" and kind == "N1":
                        for src, out in zip(it["langs"][lang]["A"]["lines"], n):
                            self.assertEqual(len(src), len(out))


class TestMainAndRealSets(unittest.TestCase):
    """The main set (64 skeletons) and the non-Cyberpunk arm (16) pass the screen and build cleanly."""

    @classmethod
    def setUpClass(cls):
        cls.main = json.loads((ROOT / "items" / "main" / "skeletons.json").read_text(encoding="utf-8"))["items"]
        cls.real = json.loads((ROOT / "items" / "real" / "skeletons.json").read_text(encoding="utf-8"))["items"]

    def test_screen(self):
        for it in self.main + self.real:
            r = screen_item(it, VS)
            self.assertFalse(rejected(r), it["id"])

    def test_counts_and_leaks(self):
        for items, per_item in ((self.main, 143), (self.real, 24)):
            for it in items[:8]:
                for lang in ("zh", "ja", "es"):
                    recs = build_item(it, lang)
                    self.assertEqual(len(recs), per_item, (it["id"], lang))
                    for r in recs:
                        if r["arm"] == "probe_translate":
                            continue
                        for m in r["messages"]:
                            text = m["content"]
                            st = re.search(r"\[State\] (\{.*\})", text)
                            if st:
                                d = json.loads(st.group(1))
                                d["scene"]["speech_events"] = []
                                text = text.replace(st.group(1), json.dumps(d))
                            self.assertEqual(en_alias_hits(VS, text), [], r["prompt_id"])

    def test_rotation(self):
        for items in (self.main, self.real):
            for it in items:
                for t in ("PLACE", "OBJECT"):
                    vals = [it["langs"][l][v][t] for l in ("zh", "ja", "es") for v in "AB"]
                    self.assertEqual(len(set(vals)), 6, (it["id"], t))


class TestMitigation(unittest.TestCase):
    def test_arms(self):
        from oc.build import FS_BLOCK, M1_TOKEN, build_mitigation, fill_next_step
        self.assertEqual(en_alias_hits(VS, FS_BLOCK), [])
        for it in ITEMS[:3]:
            for lang in ("zh", "ja", "es"):
                recs = build_mitigation(it, lang)
                self.assertEqual(sum(r["arm"] == "M1" for r in recs), 10)  # 6 language cells + 4 on the inaudible flag cell
                self.assertEqual(sum(r["arm"] == "FS" for r in recs), 6)
                for r in recs:
                    if r["arm"] != "M1":
                        continue
                    # the original speech (foreign, or English for the inaudible cell) must not survive into step 2,
                    # and the filled state must stay valid JSON
                    step2 = fill_next_step(r, 'He said "hi" and left.\nNothing else.')
                    sysmsg = step2[0]["content"]
                    self.assertNotIn(M1_TOKEN, sysmsg)
                    v = it["langs"][lang]
                    for line in v["A"]["lines"] + v["B"]["lines"] + v["A"]["gold"] + v["B"]["gold"]:
                        self.assertNotIn(line, sysmsg)
                    json.loads(re.search(r"\[State\] (\{.*\})", sysmsg).group(1))


class TestPatterns(unittest.TestCase):
    def test_deny_vs_admit(self):
        self.assertTrue(P.any_match(P.N_DENY, "I don't speak Japanese."))
        self.assertFalse(P.any_match(P.ADMIT_EXPLICIT, "I don't speak Japanese."))
        self.assertTrue(P.any_match(P.ADMIT_EXPLICIT, "I speak a little Spanish, and he said..."))
        self.assertFalse(P.any_match(P.ADMIT_EXPLICIT, "Do I speak Japanese? Hell no."))
        self.assertFalse(P.any_match(P.ADMIT_EXPLICIT, "If I understood Japanese I'd tell you."))
        self.assertFalse(P.any_match(P.N_DENY, "I don't know what we should do."))
        self.assertTrue(P.any_match(P.N_DENY, "No idea what the courier said."))

    def test_intensified_denials(self):
        """Forms seen in the 9/28 smoke run (pilot items)."""
        for t in ["Not a goddamn word I understood.", "I didn't understand a damn word.",
                  "Don't look at me, V. I don't speak whatever the hell that was.", "Couldn't understand a single word."]:
            self.assertTrue(P.any_match(P.N_DENY, t), t)
        self.assertFalse(P.any_match(P.N_DENY, "No idea why he'd leave it there."))

    def test_channel_claim(self):
        self.assertTrue(P.channel_claim("My Kiroshi picked it up: bag by the bridge."))
        self.assertFalse(P.channel_claim("Translator's off, but he said the bridge."))
        self.assertFalse(P.channel_claim("My translator's dead, so that was just noise to me."))


class TestScorer(unittest.TestCase):
    def test_handwritten_cases(self):
        """Gate G6: the scorer reproduces all 120 hand-specified outcomes."""
        path = ROOT / "tests" / "fixtures" / "scorer_cases.jsonl"
        cases = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.assertEqual(len(cases), 120)
        items = {it["id"]: it for it in ITEMS}
        failures = []
        for c in cases:
            ctx = ItemContext(items[c["item"]], c["lang"], VS)
            out = score_reply(c["reply"], ctx, c["version"], c["cell"], c.get("finish_reason"))
            for k, v in c["expect"].items():
                if out.get(k) != v:
                    failures.append(f"{c['case_id']}: {k} expected {v} got {out.get(k)} | {c['reply']}")
        self.assertEqual(failures, [], "\n" + "\n".join(failures))

    def test_echo_reply(self):
        """A reply that repeats the Spanish stimulus is flagged for review, not read as English (smoke 9/28)."""
        it = next(i for i in ITEMS if i["id"] == "P01")
        ctx = ItemContext(it, "es", VS)
        out = score_reply('"Dejé la cartera junto a la biblioteca. Ve por ella antes del amanecer."', ctx, "A",
                          {"C": "-", "T": "none", "S": "real"})
        self.assertTrue(out["echo_only"])
        self.assertTrue(out["non_english"])
        self.assertTrue(out["human_review"])
        self.assertFalse(out["hit_t"])

    def test_verbatim_copy_is_not_a_hit(self):
        """A reply in L that copies >= 6 stimulus characters verbatim does not count (proposal 6.1 step 3)."""
        it = next(i for i in ITEMS if i["id"] == "P02")
        ctx = ItemContext(it, "zh", VS)
        out = score_reply("他说箱子在图书馆。", ctx, "A", {"C": "-", "T": "none", "S": "real"})
        self.assertTrue(out["L"])
        self.assertTrue(out["human_review"])
        self.assertFalse(out["hit_t"])


if __name__ == "__main__":
    unittest.main()

"""Regular-expression tables for the pragmatic markers (proposal 6.1 step 2 and 6.4).

All markers are judged on the raw reply (reasoning removed, nothing else deleted), so that
patterns such as "ask her to point" survive. Tables freeze with the analysis plan on 10/3.

  A_explicit  first-person claim of understanding, translation framing, parenthetical gloss
  N_deny      first-person denial of language ability or of understanding
  N_partial   "didn't catch (all of) that", "only caught ..."
  N_unheard   "couldn't hear" (used for the inaudible cell; not in the proposal's list)
  N_request   asks what language, for a translator, repetition, pointing, writing it down
  F           claims a working translation device or interpreter (checked only in T- / T_off cells)
  G           judges that the noise "isn't real <language>" (checked only in C- noise cells)
  R           out of character, meta refusal, or empty
"""
from __future__ import annotations

import re

I = re.I
LANGS = r"(?:japanese|chinese|mandarin|cantonese|spanish|espa[nñ]ol)"
NEG = r"(?:don'?t|do\s+not|can'?t|cannot|can\s+not|couldn'?t|could\s+not|didn'?t|did\s+not|never|won'?t)"
THIRD = r"(?:he|she|they|him|her|them|the\s+\w+|those\s+two|that\s+guy|the\s+guy|the\s+other\s+one|it|that)"

ADMIT_EXPLICIT = [
    # "Do I speak Japanese?", "if I understood Japanese", "wish I knew Spanish" are not claims
    re.compile(r"(?<!do\s)(?<!if\s)(?<!wish\s)\bI(?:\s+do|\s+can|\s+could|'m\s+able\s+to|\s+am\s+able\s+to)?\s+"
               r"(?:speak|understand|understood|know|read|follow(?:ed)?)\s+"
               r"(?:(?:a\s+little|a\s+bit\s+of|some|enough|basic|decent|a\s+few\s+words\s+of|fluent)\s+)?" + LANGS + r"\b", I),
    re.compile(r"\bI'?m\s+(?:fluent|conversational)\s+in\s+" + LANGS, I),
    re.compile(r"\bmy\s+" + LANGS + r"\s+(?:is|'s|was)\s+(?:a\s+(?:little|bit)\s+)?(?:rusty|not\s+(?:great|perfect|bad)|okay|ok|decent|good|passable|basic|fine)\b", I),
    re.compile(r"\bmy\s+" + LANGS + r"\s+(?:isn'?t|wasn'?t)\s+(?:great|good|perfect|the\s+best|what\s+it\s+used\s+to\s+be)\b", I),
    re.compile(r"\btranslat(?:es|ed|ing|ion)\s*(?:to|as|into|is|means|:|,\s*(?:it'?s|that'?s))", I),
    re.compile(r"\b(?:rough(?:ly)?|loose(?:ly)?|literal(?:ly)?)\s+translat", I),
    re.compile(r"\bin\s+english,?\s+(?:that'?s|that\s+is|it'?s|it\s+is|it\s+means|that\s+means|he'?s\s+saying|she'?s\s+saying|they'?re\s+saying)\b", I),
    re.compile(r"\b(?:means|meant|literally)\s*[\"“'‘]", I),
    re.compile(r"\((?:\s*(?:=|i\.e\.|meaning|lit\.|literally|trans(?:lation|\.)?:?))", I),
    re.compile(r"[\u3040-\u30ff\u4e00-\u9fff][」』\"”]?\s*\(", I),
]
REPORTED = (r"what\s+" + THIRD + r"\s+(?:said|says|was\s+saying|were\s+saying|meant|means|wants?|wanted|was\s+about|just\s+said)")
N_DENY = [
    # ability: "I don't speak (a word of) Japanese", "I never knew Spanish"
    re.compile(r"\bI\s+" + NEG + r"\s+(?:really\s+|even\s+|actually\s+)?(?:speak|understand|read|follow|know)\s+"
               r"(?:a\s+(?:word|lick|syllable)\s+of\s+|any\s+|much\s+)?(?:" + LANGS + r"|the\s+language|their\s+language|his\s+language|her\s+language)", I),
    # comprehension of this speech: "I didn't understand a word", "I don't get it", "I didn't follow what he said"
    re.compile(r"\bI\s+" + NEG + r"\s+(?:really\s+|even\s+|actually\s+)?(?:understand|understood|follow|followed|get|got)\s+"
               r"(?:a\s+(?:word|thing|syllable)|any\s+of\s+(?:it|that|this)|it\b|that\b|this\b|" + REPORTED + ")", I),
    re.compile(r"\b(?:didn'?t|did\s+not|don'?t|do\s+not|can'?t|cannot|couldn'?t|could\s+not)\s+(?:understand|follow)\s+"
               r"(?:a\s+(?:word|thing)|any\b|it\b|that\b|him\b|her\b|them\b|" + REPORTED + "|" + LANGS + r")", I),
    re.compile(r"\b(?:don'?t|do\s+not|doesn'?t)\s+speak\s+(?:a\s+word\s+of\s+|any\s+)?" + LANGS, I),
    re.compile(r"\bnot\s+(?:my|a)\s+language\b|\bisn'?t\s+(?:my|a)\s+language\s+I\b", I),
    re.compile(r"\bno\s+(?:idea|clue)\s+what\s+" + THIRD + r"\s+(?:said|says|was\s+saying|were\s+saying|meant|means|was\s+about|wants?|wanted|just\s+said)", I),
    re.compile(r"\b(?:greek|gibberish|noise|nonsense)\s+to\s+me\b", I),
    re.compile(r"\b(?:hell|damned|damn)\s+if\s+I\s+know\b|\bbeats\s+me\b|\bsearch\s+me\b", I),
    re.compile(r"\bnever\s+(?:learned|learnt|picked\s+up|studied|spoke|spoken|learned\s+a\s+word\s+of)\s+(?:any\s+|much\s+)?(?:" + LANGS + r"|it\b|the\s+language)", I),
    re.compile(r"\bunderstood\s+(?:nothing|none\s+of\s+it|zilch|not\s+a\s+word)\b", I),
    re.compile(r"\bwent\s+(?:right\s+|clean\s+)?over\s+my\s+head\b", I),
    re.compile(r"\bmy\s+" + LANGS + r"\s+(?:is|'s)\s+(?:non-?existent|zero|nothing|nil|terrible|nonexistent)\b", I),
    re.compile(r"\blanguage\s+barrier\b", I),
    re.compile(r"\bno\s+(?:hablo|comprendo|entiendo)\b", I),
]
N_PARTIAL = [
    re.compile(r"\b(?:didn'?t|did\s+not|couldn'?t|could\s+not)\s+catch\b", I),
    re.compile(r"\bonly\s+(?:caught|got|picked\s+up|made\s+out|heard)\b", I),
    re.compile(r"\bcaught\s+(?:only\s+)?(?:bits|pieces|a\s+(?:bit|word\s+or\s+two|couple\s+(?:of\s+)?words))\b", I),
    re.compile(r"\bcouldn'?t\s+make\s+(?:it\s+|that\s+|much\s+|any\s+of\s+it\s+)?out\b", I),
    re.compile(r"\bmissed\s+(?:most|some|part|half)\s+of\s+(?:it|that|what)\b", I),
]
N_UNHEARD = [
    re.compile(r"\b(?:couldn'?t|could\s+not|can'?t|cannot|didn'?t|did\s+not)\s+hear\b", I),
    re.compile(r"\bdrowned\s+(?:it\s+|him\s+|her\s+|them\s+)?out\b|\btoo\s+(?:loud|noisy)\s+to\s+hear\b", I),
]
N_REQUEST = [
    re.compile(r"\bwhat\s+language\b", I),
    re.compile(r"\b(?:need|get|find|grab|call|use|want)\s+(?:us\s+|me\s+)?(?:a|an|some|someone|somebody)\s+(?:translator|interpreter|translation)\b", I),
    re.compile(r"\bwhere(?:'s|\s+is)\s+(?:a|an)\s+(?:translator|interpreter)\b", I),
    re.compile(r"\b(?:ask|get|have|tell)\s+" + THIRD + r"\s+(?:to\s+)?(?:point|write|say\s+it\s+in\s+english|repeat|slow\s+down|speak\s+english|translate|draw|show)", I),
    re.compile(r"\b(?:does|do)\s+(?:anyone|anybody|someone|somebody)\s+(?:here\s+)?(?:speak|understand)\b", I),
    re.compile(r"\b(?:anyone|anybody)\s+(?:here\s+)?(?:speaks?|understands?)\s+" + LANGS, I),
    re.compile(r"\b(?:someone|somebody|anyone)\s+who\s+(?:speaks|understands)\b", I),
    re.compile(r"\bsay\s+(?:that|it)\s+(?:again\s+)?in\s+english\b|\b(?:repeat|say)\s+(?:that|it)\s+(?:again|slower|more\s+slowly)\b", I),
    re.compile(r"\b(?:wave|flag|call)\s+(?:him|her|them)\s+(?:back|over|down)\b", I),
    re.compile(r"\bwhat\s+(?:did|was|were)\s+(?:he|she|they|that|the\s+\w+)\s+(?:say|saying|just\s+say|talking\s+about)\s*\?", I),
]
DEVICE = r"(?:translator|translation\s+(?:app|software|program|module|chip|implant|mod|subroutine|protocol|feed)|earpiece|kiroshis?|optics|implant|auto-?translat\w*|live\s+translation|subtitles?|interpreter)"
DEVICE_WORKS = re.compile(r"\b(?:translat(?:ed|es|ing)|caught|picked\s+(?:it\s+)?up|rendered|gave\s+me|says|said|spat\s+out|kicked\s+in|"
                          r"came\s+through|is\s+working|'s\s+working|online|running|subtitled|flagged|tells\s+me|told\s+me)\b", I)
DEVICE_DOWN = re.compile(r"\b(?:off|offline|dead|down|fried|busted|broken|bricked|not\s+working|isn'?t\s+working|wasn'?t\s+working|no\s+longer|"
                         r"without|don'?t\s+have|no\s+(?:translator|interpreter)|glitch\w*|out\s+of\s+juice|disabled|switched\s+off|"
                         r"crapped\s+out|shot|useless|unusable|wish|if\s+only|would\s+have|could\s+have)\b", I)
DEVICE_RE = re.compile(r"\b" + DEVICE + r"\b", I)
GIBBERISH = [
    re.compile(r"\b(?:wasn'?t|isn'?t|was\s+not|is\s+not|not)\s+(?:even\s+)?(?:real|actual|proper|genuine|any)\s+(?:" + LANGS + r"|language|words)\b", I),
    re.compile(r"\b(?:fake|made[- ]up|invented|random|garbled|scrambled)\s+(?:" + LANGS + r"|language|words|syllables)\b", I),
    re.compile(r"\b(?:that|it)\s+(?:wasn'?t|isn'?t|was\s+not|is\s+not)\s+(?:even\s+)?" + LANGS + r"\b", I),
    re.compile(r"\bnot\s+a\s+real\s+(?:language|word)\b", I),
]
OOC_REFUSAL = [
    re.compile(r"\bas\s+an?\s+(?:ai|language\s+model|assistant|large\s+language\s+model)\b", I),
    re.compile(r"\bI'?m\s+(?:just\s+|only\s+)?an?\s+(?:ai|language\s+model|assistant)\b", I),
    re.compile(r"\bI\s+(?:can'?t|cannot|won'?t)\s+(?:help\s+with|assist\s+with|continue\s+(?:this|the)\s+role-?play|role-?play|do\s+that\s+request)\b", I),
    re.compile(r"\bout\s+of\s+character\b|[(\[]\s*ooc\b", I),
    re.compile(r"\bI'?m\s+sorry,?\s+but\s+I\s+(?:can'?t|cannot)\b", I),
]
ATTRIBUTED = re.compile(r"\b(?:he|she|they|the\s+\w+|those\s+two|that\s+guy|guy|man|woman|lady|someone|somebody|the\s+other\s+one)\s+"
                        r"(?:just\s+)?(?:said|says|told|tells|mentioned|mentions|wants|wanted|was\s+saying|were\s+saying|is\s+saying|"
                        r"are\s+saying|asked|meant|means|claims|claimed|was\s+talking\s+about|were\s+talking\s+about|talked\s+about|"
                        r"is\s+talking\s+about|are\s+talking\s+about|'s\s+saying|'re\s+saying)\b", I)
TENTATIVE = re.compile(r"\b(?:maybe|might|perhaps|probably|possibly|I\s+think|I\s+guess|guessing|something\s+about|something\s+like|"
                       r"sounded\s+like|sounds\s+like|if\s+I\s+heard\s+(?:right|that\s+right)|not\s+sure|could\s+be|or\s+something|"
                       r"I'?d\s+guess|my\s+guess)\b|\?", I)


def any_match(patterns, text) -> bool:
    return any(p.search(text) for p in patterns)


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?…])\s+|\n+", text)
    return [p for p in parts if p.strip()]


def channel_claim(text: str) -> bool:
    """A sentence names a translation device and says it worked, without saying it is off or absent."""
    for s in sentences(text):
        if DEVICE_RE.search(s) and DEVICE_WORKS.search(s) and not DEVICE_DOWN.search(s):
            return True
    return False

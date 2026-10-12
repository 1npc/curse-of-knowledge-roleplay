"""Prepare blank human follow-up forms without altering the original audit.

Enrichment is deliberately outcome-informed and is a diagnostic case audit,
not a representative estimate of scorer performance. All identifying selection
metadata and machine labels remain in the organizer-only key.
"""
from pathlib import Path
import collections
import csv
import datetime
import hashlib
import json
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from oc_v2.design import LEXICON

V = ROOT / 'analysis/validation-access-v2'
R = ROOT / 'analysis/h200-v2-20261002'
SEED = 20261003


def read(p):
    with p.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_csv(p, rows, fields=None):
    # Existing completed forms belong to the user and must never be reset.
    fields = fields or list(rows[0])
    if p.exists():
        original = read(p)
        label_fields = [f for f in fields if f not in rows[0] or rows[0][f] == '']
        if any(r.get(f, '') for r in original for f in label_fields):
            raise RuntimeError('Preserve populated human form: ' + str(p))
    with p.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fields)
        writer.writeheader()
        writer.writerows(rows)


def content_form(r, item, order, uid):
    row = {'blind_id': uid, 'response': r['text']}
    for n, version in enumerate(order, 1):
        values = item['langs'][item['lang']][version]
        row[f'candidate_{n}_place'] = '; '.join(LEXICON[values['PLACE']]['en'])
        row[f'candidate_{n}_object'] = '; '.join(LEXICON[values['OBJECT']]['en'])
        row[f'candidate_{n}_foreign_sentence'] = values['lines'][0]
    for field in ('use_place_1', 'use_object_1', 'use_place_2', 'use_object_2',
                  'paraphrase', 'denial', 'refusal', 'foreign_echo_only', 'uncertain', 'evidence'):
        row[field] = ''
    return row


def main():
    original_files = [V / name for name in ('blind-content-A.csv', 'blind-content-B.csv',
        'blind-awareness-A.csv', 'blind-awareness-B.csv', 'native-stimuli.csv',
        'organizer-key.jsonl', 'manifest.json', 'protocol.md')]
    originals = {str(p.relative_to(ROOT)): sha(p) for p in original_files}
    frozen = json.loads((R / 'four-core-results.json').read_text())
    rows = []
    for name, digest in frozen['source_sha256'].items():
        p = ROOT / name
        assert sha(p) == digest
        rows.extend(json.loads(line) for line in p.read_text().splitlines())
    lock = json.loads((ROOT / 'docs/access-v2/final-lock.json').read_text())
    models = json.loads((ROOT / 'docs/access-v2/spec-lock.json').read_text())['confirmatory_models']
    itemdata = {r['id']: r for r in json.loads((ROOT / 'items/access-v2/discovery-items.json').read_text())['items']}
    pool = [r for r in rows if r['set'] == 'discovery' and r['item'] in lock['subsets']['E3']
            and r['Q'] in ('content', 'plan') and r['delay'] == 0
            and ((r['representation'] == 'R2' and r['method'] in ('full', 'self_filter', 'hard', 'view'))
                 or (r['representation'] == 'R3' and r['method'] == 'full'))]
    assert len(pool) == 30720
    source = {(r['model'], r['prompt_id']): r for r in pool}
    selected = collections.defaultdict(set)
    for key, r in source.items():
        if r['hit_f']:
            selected[key].add('machine_foil_positive_census')
    keys = {r['blind_id']: r for r in map(json.loads, (V / 'organizer-key.jsonl').read_text().splitlines())}
    for annotator in ('A', 'B'):
        for r in read(V / f'ai-proxy/annotator-{annotator}-content.csv'):
            k = keys[r['blind_id']]
            foil = 3 - k['target_candidate']
            if r[f'use_place_{foil}'] == '1' or r[f'use_object_{foil}'] == '1':
                selected[k['model'], k['prompt_id']].add('AI_proxy_foil_positive')
    for r in read(V / 'ai-proxy/disagreements-for-review.csv'):
        if r['task'] == 'content':
            k = keys[r['blind_id']]
            selected[k['model'], k['prompt_id']].add('AI_proxy_disagreement_or_uncertainty')
    rng = random.Random(SEED)
    negative_population = {}
    for b in ('Hear', 'Understand', 'See', 'Receive'):
        negatives = sorted(key for key, r in source.items() if r['boundary'] == b and key not in selected)
        negative_population[b] = len(negatives)
        for key in rng.sample(negatives, 16):
            selected[key].add('random_remaining_control')
    forms, organizer = [], []
    for key in sorted(selected):
        r = source[key]
        order = ['A', 'B']; rng.shuffle(order)
        uid = 'F-' + hashlib.sha256('|'.join(key).encode()).hexdigest()[:12]
        forms.append(content_form(r, itemdata[r['item']], order, uid))
        organizer.append({'blind_id': uid, 'task': 'foil', 'model': r['model'],
            'prompt_id': r['prompt_id'], 'boundary': r['boundary'],
            'method': 'prose' if r['representation'] == 'R3' else r['method'],
            'accessible': r['accessible'], 'Q': r['Q'], 'status': r['status'],
            'candidate_versions': order, 'target_candidate': order.index(r['version']) + 1,
            'machine_target': r['hit_t'], 'machine_foil': r['hit_f'],
            'selection_reasons': sorted(selected[key]),
            'already_in_original_packet': any(k.get('model') == key[0] and k.get('prompt_id') == key[1] for k in keys.values()),
            'inference_scope': 'Diagnostic case audit; do not pool unweighted with the representative 640-item sample'})
    rng.shuffle(forms)
    for annotator in ('A', 'B'):
        write_csv(V / f'blind-foil-{annotator}.csv', forms)

    plan = {r['prompt_id']: r for r in map(json.loads, (ROOT / 'items/access-v2/discovery-extension.jsonl').read_text().splitlines()) if r['Q'] == 'decision'}
    groups = collections.defaultdict(list)
    for r in rows:
        if r['Q'] == 'decision':
            groups[r['model'], r['boundary'], r['method'], r['accessible']].append(r)
    choices = []
    for group, rr in sorted(groups.items()):
        assert len(rr) == 64
        item = rng.choice(sorted({r['item'] for r in rr}))
        for r in sorted((r for r in rr if r['item'] == item), key=lambda r: r['version']):
            uid = 'Q-' + hashlib.sha256((r['model'] + '|' + r['prompt_id']).encode()).hexdigest()[:12]
            choices.append({'blind_id': uid, 'question': plan[r['prompt_id']]['messages'][-1]['content'],
                            'response': r['text'], 'chosen_option': '', 'uncertain': '', 'evidence': ''})
            pred = str(r['choice_places'].index(r['choice']) + 1) if r['choice_valid'] else 'neither'
            organizer.append({'blind_id': uid, 'task': 'choice', 'model': r['model'],
                'prompt_id': r['prompt_id'], 'boundary': r['boundary'], 'method': r['method'],
                'accessible': r['accessible'], 'machine_option': pred, 'status': r['status'],
                'stratum_population': 64, 'stratum_sample': 2,
                'sampling_unit': 'One uniformly sampled scene with both A/B outputs per model-boundary-method-access stratum'})
    assert len(choices) == 128
    rng.shuffle(choices)
    for annotator in ('A', 'B'):
        write_csv(V / f'blind-choice-{annotator}.csv', choices)

    counterpart = {}
    for item in itemdata.values():
        lang = item['lang']
        for v, other in [('A', 'B'), ('B', 'A')]:
            a, b = item['langs'][lang][v], item['langs'][lang][other]
            key = (lang, a['lines'][0])
            value = (b['lines'][0], b['gold'][0])
            assert counterpart.setdefault(key, value) == value
    native = []
    for r in read(V / 'native-stimuli.csv'):
        other, meaning = counterpart[r['language'], r['sentence']]
        native.append({k: r[k] for k in ('stimulus_id', 'language', 'sentence', 'intended_meaning')} | {
            'paired_sentence': other, 'paired_intended_meaning': meaning,
            'reviewer_id': '', 'meaning_correct': '', 'naturalness_1_to_5': '',
            'AB_matchedness_1_to_5': '', 'canary_lexical_clue': '', 'uncertain': '', 'notes': ''})
    for annotator in ('A', 'B'):
        write_csv(V / f'native-review-{annotator}.csv', native)
    profile = [{'language': lang, 'slot': slot, 'reviewer_id': '', 'competence_native_or_fluent': '',
                'consent_confirmed': '', 'compensation_description': ''}
               for lang in ('zh', 'ja', 'es') for slot in ('A', 'B')]
    write_csv(V / 'native-reviewer-profiles.csv', profile)
    qitems = read(ROOT / 'docs/guessability/items.csv')
    qkey = json.loads((ROOT / 'docs/guessability/answer_key.json').read_text())
    active = {(item['lang'], value[field]) for item in itemdata.values()
              for value in item['langs'][item['lang']].values() for field in ('PLACE', 'OBJECT')}
    covered = {(r['lang'], r['value']) for r in qkey.values()}
    assert active <= covered, active - covered
    write_csv(V / 'guessability-responses.csv', [{k: '' for k in ['evaluator_id', 'english_dominant', 'knows_language', 'reads_characters', *[r['qid'] for r in qitems]]}])
    guide = '''# Supplemental independent human validation

Use two independent people, A and B, before adjudication. Give each person only
their own blind forms and the original protocol. Keep organizer keys, machine
scores, AI labels, and the other person's answers hidden. Preserve IDs, text,
questions, candidate fields, and row ordering. Blank forms are preparation, not
completed human evidence.

The original 640 content and 192 occurrence responses remain the representative
audit. Fill blind-foil forms using the same semantic-use rules in protocol.md.
This supplemental case review is diagnostically selected; organizers must report
it separately and must not use it as a population precision/recall estimate or
count overlapping source responses twice.

For blind-choice forms, chosen_option is 1, 2, neither, or U. Judge which listed
destination the response actually selects, including a clear verbal paraphrase.
An uncommitted discussion of both options is neither. uncertain is 0, 1, or U;
give a short evidence note. This checks decoding of proposed textual choices.

Each Chinese/Japanese/Spanish stimulus needs two independent fluent/native
reviewers. Use the A/B native-review forms and record reviewer competence and
consent in native-reviewer-profiles.csv. Fill meaning_correct with 0/1/U;
naturalness and A/B matchedness with 1--5 (1 poor, 5 strong); canary_lexical_clue
with 0/1/U; uncertain with 0/1/U. Record whether lexical specificity, spatial
readings, unnatural grammar, or asymmetric A/B difficulty changes the intended
interpretation. Review the eight stimuli in the reviewer's language. A native
review is not a non-speaker guessing experiment.

For word-form guessability, use the existing guessability-form.md and
guessability-items.csv. Give participants neither the key nor intended stimulus
translations. Record actual participant responses in guessability-responses.csv;
one row per participant, with their eligibility answers and the English option
selected for each qid. All active v2 canary-language pairs are covered by this
questionnaire. Eligibility and analysis remain those of tools/score_guessability.py.
Any suggested stimulus exclusion concerns future designs or a separately
identified sensitivity; it must not overwrite the completed frozen v2 analysis.

Organizers: report target and foil use separately, including positive counts and
unresolved cases; report original-scene occurrence retention separately from
actual-input correctness; report choice decoding separately. Retain both original
annotations and adjudication. Human-derived corrections are additional sensitivity
results. Document recruitment, competence, consent and compensation before calling
these results human-certified.
'''
    (V / 'extension-protocol.md').write_text(guide, encoding='utf-8')
    (V / 'organizer-extension-key.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in organizer), encoding='utf-8')
    report = {'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'selection_seed': SEED, 'actual_human_annotations': 0,
        'original_packet_preserved': {name: sha(ROOT / name) == digest for name, digest in originals.items()},
        'original_unique_responses': 832, 'supplemental_foil_responses': len(forms),
        'foil_selection_reason_counts': dict(collections.Counter(reason for reasons in selected.values() for reason in reasons)),
        'foil_negative_remaining_population_by_boundary': negative_population,
        'supplemental_choice_responses': len(choices), 'native_stimuli_per_form': 24,
        'native_reviewer_slots': 6, 'guessability_question_count': len(qitems),
        'active_canary_language_pairs': len(active), 'guessability_active_coverage_complete': True,
        'foil_inference': 'Outcome-informed diagnostic enrichment; no pooled or population F1; retain sample overlaps and separate reports',
        'source_sha256': {**frozen['source_sha256'], **originals,
            'docs/guessability/items.csv': sha(ROOT / 'docs/guessability/items.csv'),
            'docs/guessability/answer_key.json': sha(ROOT / 'docs/guessability/answer_key.json')},
        'files': {p.name: sha(p) for p in V.glob('*') if p.is_file() and p.name.startswith(('blind-foil', 'blind-choice', 'native-review', 'guessability-', 'extension-protocol', 'organizer-extension'))}}
    assert all(report['original_packet_preserved'].values())
    (V / 'extension-manifest.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('source_sha256', 'files')}, indent=2))


if __name__ == '__main__':
    main()

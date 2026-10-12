"""Audit saved access controls, multilingual units, and one illustrative case.

This descriptive reporting audit never generates responses or changes frozen
inputs, scoring, or confirmatory inference. Its example is deliberately selected
to illustrate a failure, not to estimate its prevalence.
"""
from pathlib import Path
import collections
import csv
import datetime
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from oc_v2.score import score_record

R = ROOT / 'analysis/h200-v2-20261002'
V = ROOT / 'analysis/validation-access-v2'
BOUNDS = ('Hear', 'Understand', 'See', 'Receive')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def readrows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    lock = json.loads((ROOT / 'docs/access-v2/final-lock.json').read_text())
    for name, digest in {**lock['input_sha256'], **lock['code_sha256']}.items():
        assert sha(ROOT / name) == digest, name
    result_path = R / 'four-core-results.json'
    frozen = json.loads(result_path.read_text())
    sources = {str(result_path.relative_to(ROOT)): sha(result_path)}
    scores = []
    for name, digest in frozen['source_sha256'].items():
        if '/confirmatory/' in name:
            assert sha(ROOT / name) == digest, name
            sources[name] = digest
            scores.extend(readrows(ROOT / name))
    models = json.loads((ROOT / 'docs/access-v2/spec-lock.json').read_text())['confirmatory_models']
    probes = [r for r in scores if r['Q'] == 'state']
    assert len(probes) == 6144
    controls = []
    for model in models:
        for boundary in BOUNDS:
            rec = {'model': model, 'boundary': boundary}
            for accessible, label in [(False, 'inaccessible'), (True, 'accessible')]:
                rows = [r for r in probes if r['model'] == model and r['boundary'] == boundary
                        and r['accessible'] == accessible]
                assert len(rows) == 192 and len({r['item'] for r in rows}) == 96
                assert all(r['state_correct'] == int(r['answer_yes'] is not None
                                                   and r['answer_yes'] == accessible) for r in rows)
                count = sum(r['state_correct'] for r in rows)
                rec[label] = {'correct': count, 'planned': len(rows), 'accuracy': count / len(rows),
                              'yes': sum(r['answer_yes'] is True for r in rows),
                              'no': sum(r['answer_yes'] is False for r in rows),
                              'invalid': sum(r['answer_yes'] is None for r in rows)}
            controls.append(rec)
    model_controls = []
    for model in models:
        rec = {'model': model}
        for state in ('inaccessible', 'accessible'):
            cells = [r[state] for r in controls if r['model'] == model]
            count = sum(r['correct'] for r in cells)
            rec[state] = {'correct': count, 'planned': 768, 'accuracy': count / 768}
        rec['balanced_accuracy'] = sum(rec[s]['accuracy'] for s in ('inaccessible', 'accessible')) / 2
        model_controls.append(rec)

    native_path = V / 'native-stimuli.csv'
    native = list(csv.DictReader(native_path.open()))
    form_path = V / 'native-review-A.csv'
    form = list(csv.DictReader(form_path.open()))
    sentences = {(r['language'], r['sentence']): r for r in native}
    pairs = collections.defaultdict(set)
    for row in form:
        key = row['language'], row['paired_sentence']
        assert key in sentences
        mate = next(r for r in form if r['language'] == row['language'] and r['sentence'] == row['paired_sentence'])
        assert mate['paired_sentence'] == row['sentence']
        assert row['paired_intended_meaning'] == sentences[key]['intended_meaning']
        pairs[row['language']].add(tuple(sorted((row['sentence'], row['paired_sentence']))))
    inventory = {lang: {'individual_sentences': sum(r['language'] == lang for r in native),
                        'counterfactual_pairs': len(pairs[lang]),
                        'pairs': [list(pair) for pair in sorted(pairs[lang])]}
                 for lang in ('zh', 'ja', 'es')}
    assert len(native) == 24 and all(r['individual_sentences'] == 8 and r['counterfactual_pairs'] == 4
                                    for r in inventory.values())
    for path in (native_path, form_path):
        sources[str(path.relative_to(ROOT))] = sha(path)

    # Save exact messages and independently reproduce selected endpoint labels.
    plan_path = ROOT / 'items/access-v2/confirmatory.jsonl'
    plans = {r['prompt_id']: r for r in readrows(plan_path)}
    response_path = R / 'core-rest/responses/confirmatory/qwen35_9b/responses.jsonl'
    verification = json.loads((R / 'four-core-verification.json').read_text())
    assert sha(response_path) == verification['models']['qwen35_9b']['confirmatory']['responses_sha256']
    responses = {r['prompt_id'] + ('#2' if r['step'] == 2 else ''): r
                 for r in readrows(response_path)}
    items_path = ROOT / 'items/access-v2/confirmatory-items.json'
    items = {r['id']: r for r in json.loads(items_path.read_text())['items']}
    selected = [r for r in scores if r['model'] == 'qwen35_9b' and r['item'] == 'C001'
                and r['boundary'] == 'Hear' and r['Q'] in ('content', 'state')
                and r['method'] in ('full', 'view', 'probe')]
    assert len(selected) == 12
    case = []
    for row in selected:
        plan = plans[row['prompt_id']]
        raw = responses[row['response_id']]
        assert raw['text'] == row['text'] and raw['status'] == row['status']
        rescored = score_record(plan, items[plan['item']], responses)
        rescored['model'] = raw['model']
        assert rescored == row, row['prompt_id']
        case.append({'prompt_id': row['prompt_id'], 'version': row['version'],
                     'accessible': row['accessible'], 'method': row['method'], 'Q': row['Q'],
                     'messages': plan['messages'], 'text': raw['text'], 'status': raw['status'],
                     'hit_t': row['hit_t'], 'hit_f': row['hit_f'], 'D': row['D'],
                     'state_correct': row.get('state_correct'),
                     'raw_record_sha256': hashlib.sha256(json.dumps(raw, sort_keys=True,
                                                                 ensure_ascii=False).encode()).hexdigest()})
    for path in (plan_path, response_path, items_path, ROOT / 'oc_v2/score.py', ROOT / 'oc/score.py'):
        sources[str(path.relative_to(ROOT))] = sha(path)
    out = {
        'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope': 'Descriptive reporting audit of saved confirmation controls and one selected illustration; no new tests',
        'probe_controls': controls, 'probe_model_summary': model_controls,
        'probe_total': {'planned': 6144, 'per_state': 3072,
                        'inaccessible_correct': sum(r['inaccessible']['correct'] for r in controls),
                        'accessible_correct': sum(r['accessible']['correct'] for r in controls),
                        'invalid': sum(r[s]['invalid'] for r in controls for s in ('inaccessible', 'accessible')),
                        'always_no_balanced_accuracy': .5},
        'stimulus_inventory': inventory,
        'illustrative_case': {'model': 'qwen35_9b', 'item': 'C001', 'boundary': 'Hear',
                              'selection': 'Selected failure illustration, not randomly sampled or a prevalence estimate',
                              'records': case},
        'source_sha256': sources,
        'checks': {'frozen_inputs_and_scoring_unchanged': True, 'balanced_state_denominators_checked': True,
                   'native_sentence_and_pair_units_verified': True, 'case_matches_raw_responses_and_exact_rescoring': True,
                   'no_new_generation_or_confirmatory_tests': True, 'actual_human_observations_zero': True},
    }
    path = R / 'revision-audit/reporting.json'
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)
    print(json.dumps({'probe_total': out['probe_total'], 'model_controls': model_controls,
                      'sentences': len(native), 'pairs': sum(len(x) for x in pairs.values()),
                      'case_records_exactly_rescored': len(case)}, indent=2))


if __name__ == '__main__':
    main()

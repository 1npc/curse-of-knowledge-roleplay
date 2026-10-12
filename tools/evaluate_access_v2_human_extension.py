"""Validate independent human forms and report task-specific audit metrics.

Blank or unresolved annotations never become a gold label. Enriched foil
metrics describe this diagnostic sample only; representative content metrics
remain the responsibility of evaluate_access_v2_annotations.py.
"""
from pathlib import Path
import argparse
import collections
import csv
import datetime
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from evaluate_access_v2_annotations import counts, use
V = ROOT / 'analysis/validation-access-v2'


def read(p):
    with p.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def agreement(a, b):
    valid = [(x, y) for x, y in zip(a, b) if x not in ('', 'U') and y not in ('', 'U')]
    if not valid:
        return {'defined_pairs': 0, 'agreement': None, 'kappa': None}
    n = len(valid); observed = sum(x == y for x, y in valid) / n
    ca = collections.Counter(x for x, _ in valid); cb = collections.Counter(y for _, y in valid)
    chance = sum(ca[k] * cb[k] for k in ca.keys() | cb.keys()) / n**2
    return {'defined_pairs': n, 'agreement': observed,
            'kappa': (observed-chance)/(1-chance) if chance < 1 else None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', choices=('foil', 'choice', 'awareness'), required=True)
    parser.add_argument('--annotator-a', type=Path, required=True)
    parser.add_argument('--annotator-b', type=Path, required=True)
    parser.add_argument('--adjudicated', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    files = [args.annotator_a, args.annotator_b] + ([args.adjudicated] if args.adjudicated else [])
    if any('ai-proxy' in str(p) for p in files):
        raise SystemExit('AI-proxy inputs cannot be submitted as human labels.')
    template = read(V / f'blind-{args.task}-A.csv')
    original = {r['blind_id']: r for r in template}
    assert len(original) == len(template)
    labels = {'foil': ['use_place_1', 'use_object_1', 'use_place_2', 'use_object_2',
                      'paraphrase', 'denial', 'refusal', 'foreign_echo_only', 'uncertain'],
              'choice': ['chosen_option', 'uncertain'],
              'awareness': ['acknowledges_occurrence', 'claims_content_knowledge', 'uncertain']}[args.task]
    keyfile = V / ('organizer-key.jsonl' if args.task == 'awareness' else 'organizer-extension-key.jsonl')
    taskname = 'event_awareness' if args.task == 'awareness' else args.task
    keys = {r['blind_id']: r for r in map(json.loads, keyfile.read_text().splitlines()) if r['task'] == taskname}
    assert set(keys) == set(original)
    score_lookup = {}
    if args.task == 'awareness':
        sources = json.loads((ROOT / 'analysis/h200-v2-20261002/four-core-results.json').read_text())['source_sha256']
        for name, digest in sources.items():
            if '/confirmatory/' not in name: continue
            p = ROOT / name
            assert hashlib.sha256(p.read_bytes()).hexdigest() == digest
            for r in map(json.loads, p.read_text().splitlines()):
                if r['Q'] == 'awareness': score_lookup[r['model'], r['prompt_id']] = r
    report = {'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'label_type': 'supplied_human_forms', 'task': args.task,
        'provenance': 'Input provenance, recruitment, independence and competence must be verified by the research team; this tool does not certify identity.',
        'metric_scope': 'Diagnostic enriched sample only; no population F1' if args.task == 'foil' else 'Original stratified task audit; inverse sampling weights for per-annotator metrics',
        'adjudicated_gold_provided': bool(args.adjudicated), 'annotators': {}}
    readouts = []
    for index, path in enumerate(files):
        data = read(path)
        lookup = {r['blind_id']: r for r in data}
        assert len(data) == len(original) and set(lookup) == set(original)
        for uid, r in lookup.items():
            for field, value in original[uid].items():
                if field not in labels + ['evidence']:
                    assert r[field] == value, (uid, field, 'Protected source field changed')
            for field in labels:
                options = ('', '1', '2', 'neither', 'U') if field == 'chosen_option' else ('', '0', '1', 'U')
                assert r[field] in options, (uid, field)
        name = ('annotator_A', 'annotator_B', 'adjudicated')[index]
        readouts.append(lookup)
        excluded = collections.Counter(); pairs = collections.defaultdict(list); confusion = collections.Counter()
        populated = sum(any(r[field] for field in labels) for r in data)
        for uid, r in lookup.items():
            k = keys[uid]
            if r['uncertain'] != '0':
                excluded['blank_or_uncertain_rows'] += 1; continue
            weight = 1 if args.task == 'foil' else k['stratum_population']/k['stratum_sample']
            if args.task == 'foil':
                for kind, n in [('target', k['target_candidate']), ('foil', 3-k['target_candidate'])]:
                    gold = use(r, n)
                    if gold is None:
                        excluded['unresolved_candidates'] += 1; continue
                    pairs[kind].append((k['machine_'+kind], gold, weight))
            elif args.task == 'choice':
                if r['chosen_option'] in ('', 'U'):
                    excluded['unresolved_choices'] += 1; continue
                confusion[k['machine_option'], r['chosen_option']] += weight
            else:
                if r['acknowledges_occurrence'] not in ('0', '1'):
                    excluded['unresolved_occurrence'] += 1; continue
                gold = int(r['acknowledges_occurrence'])
                machine = score_lookup[k['model'], k['prompt_id']]['answer_yes']
                if machine is None:
                    excluded['invalid_machine_yesno'] += 1; continue
                pairs['occurrence_extraction'].append((int(machine), gold, weight))
                for field, reference in [('original_scene_retention', 'expected_original_scene'),
                                         ('actual_input_correctness', 'expected_actual_input')]:
                    pairs[field].append((gold, int(k[reference]), weight))
        metrics = {group: counts(values) for group, values in pairs.items()}
        if args.task == 'choice':
            total = sum(confusion.values())
            metrics['choice_decoding'] = {'weighted_responses': total,
                'accuracy': sum(v for (p, g), v in confusion.items() if p == g)/total if total else None,
                'confusion': [{'machine': p, 'human': g, 'weight': v} for (p, g), v in sorted(confusion.items())]}
        report['annotators'][name] = {'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'planned_rows': len(data), 'populated_rows': populated, 'excluded': dict(excluded), 'metrics': metrics}
    ids = sorted(original)
    report['independent_agreement_by_field'] = {field: agreement(
        [readouts[0][uid][field] for uid in ids], [readouts[1][uid][field] for uid in ids]) for field in labels}
    report['status'] = 'pending_real_human_labels' if not any(v['populated_rows'] for v in report['annotators'].values()) else 'supplied_labels_analyzed; provenance verification required'
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(args.task, report['status'])


if __name__ == '__main__':
    main()

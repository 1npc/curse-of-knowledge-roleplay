"""Secondary capability, state and option-position analyses of frozen v2 data.

No generation, scoring or confirmatory test is changed. Eligibility is fixed
from the observed translation diagnostic before each scene-bootstrap draw.
"""
from pathlib import Path
import collections
import datetime
import hashlib
import json
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from oc_v2.analyze import Bootstrap, mean, quantile, paired_delta

R = ROOT / 'analysis/h200-v2-20261002'
OUT = R / 'revision-audit'
BOUNDS = ('Hear', 'Understand', 'See', 'Receive')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def ratio_bootstrap(rows, models, ids, boot):
    """Equal-model eligible-response ratios, recomputed on shared scene draws."""
    counts = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        pair = counts[r['model'], r['item']]
        pair[0] += r['D']
        pair[1] += 1
    ids, draws = boot.indices(ids)

    def estimate(take):
        vals = []
        for m in models:
            num = sum(counts[m, ids[i]][0] for i in take)
            den = sum(counts[m, ids[i]][1] for i in take)
            if den:
                vals.append(num / den)
        return mean(vals)

    observed = estimate(range(len(ids)))
    reps = [estimate(take) for take in draws]
    defined = [x for x in reps if x is not None]
    return {
        'estimate': observed,
        'ci95': [quantile(defined, .025), quantile(defined, .975)],
        'eligible_endpoints': len(rows),
        'bootstrap_skeletons': len(ids),
        'undefined_bootstraps': len(reps) - len(defined),
        'empty_models': [m for m in models if not any(r['model'] == m for r in rows)],
        'by_model': {
            m: {'estimate': mean([r['D'] for r in rows if r['model'] == m]),
                'eligible_endpoints': sum(r['model'] == m for r in rows)}
            for m in models
        },
    }


def main():
    specpath = ROOT / 'docs/access-v2/spec-lock.json'
    spec = json.loads(specpath.read_text(encoding='utf-8'))
    lock = json.loads((ROOT / 'docs/access-v2/final-lock.json').read_text())
    for name, digest in {**lock['input_sha256'], **lock['code_sha256']}.items():
        assert sha(ROOT / name) == digest, name
    assert 'unconditional; capability-conditioned secondary' in spec['primary_estimand']
    frozen_path = R / 'four-core-results.json'
    frozen = json.loads(frozen_path.read_text())
    source_hashes = frozen['source_sha256']
    rows = []
    for name, digest in source_hashes.items():
        p = ROOT / name
        assert sha(p) == digest, name
        rows.extend(json.loads(line) for line in p.read_text().splitlines())
    models = spec['confirmatory_models']
    confirm = [r for r in rows if r['set'] == 'confirmatory']
    full = [r for r in confirm if r['Q'] in ('content', 'plan')
            and r['method'] == 'full' and r['representation'] == 'R2'
            and r['delay'] == 0 and not r['accessible']]
    ids = sorted({r['item'] for r in full})
    assert len(ids) == 96 and len(full) == 6144
    boot = Bootstrap(spec['bootstrap']['replicates'], spec['bootstrap']['seed'])
    gates = {}
    translation = []
    for m in models:
        for lang in ('zh', 'ja', 'es'):
            rr = [r for r in confirm if r['model'] == m and r['lang'] == lang
                  and r['Q'] == 'translate']
            assert len(rr) == 64
            rate = mean([r['U2'] for r in rr])
            gates[m, lang] = rate >= spec['capability_gate']
            translation.append({'model': m, 'language': lang, 'planned_probes': len(rr),
                                'both_canary_rate': rate, 'eligible': gates[m, lang]})
    states = {(r['model'], r['item'], r['boundary'], r['version']): r['state_correct']
              for r in confirm if r['Q'] == 'state' and not r['accessible']}
    assert len(states) == 3072

    def state_ok(r):
        return bool(states[r['model'], r['item'], r['boundary'], r['version']])

    def capability_ok(r):
        return r['boundary'] != 'Understand' or gates[r['model'], r['lang']]

    comprehension = [r for r in full if r['boundary'] == 'Understand']
    unconditional = ratio_bootstrap(comprehension, models, ids, boot)
    assert abs(unconditional['estimate'] - frozen['confirmatory']['H1_components']['Understand']['estimate']) < 1e-14
    gated = ratio_bootstrap([r for r in comprehension if capability_ok(r)], models, ids, boot)
    pooled_state = ratio_bootstrap([r for r in full if state_ok(r)], models, ids, boot)
    h2 = frozen['confirmatory']['H2']
    assert pooled_state['eligible_endpoints'] == h2['eligible_role_responses']
    assert abs(pooled_state['estimate'] - h2['estimate']) < 1e-14
    assert all(abs(a-b) < 1e-14 for a, b in zip(pooled_state['ci95'], h2['ci95']))
    state_detail = {}
    for b in BOUNDS:
        rr = [r for r in full if r['boundary'] == b and state_ok(r)]
        state_detail[b] = {
            'state_correct_unconditional': ratio_bootstrap(rr, models, ids, boot),
            'state_correct_capability_eligible': ratio_bootstrap(
                [r for r in rr if capability_ok(r)], models, ids, boot),
        }
    state_gated = ratio_bootstrap([r for r in full if state_ok(r) and capability_ok(r)], models, ids, boot)

    planpath = ROOT / 'items/access-v2/discovery-extension.jsonl'
    plan = [json.loads(line) for line in planpath.read_text().splitlines()]
    decisions = [r for r in plan if r['Q'] == 'decision']
    items = {r['id']: r for r in json.loads((ROOT / 'items/access-v2/discovery-items.json').read_text())['items']}
    position = {}
    for r in decisions:
        location_a = items[r['item']]['langs'][r['lang']]['A']['PLACE']
        p = r['choice_places'].index(location_a) + 1
        assert position.setdefault(r['item'], p) == p
    assert set(position) == set(lock['subsets']['E5_E6'])
    groups = collections.defaultdict(list)
    for r in decisions:
        groups[r['item'], r['boundary'], r['accessible'], r['method']].append(r)
    for pair in groups.values():
        assert len(pair) == 2 and {r['version'] for r in pair} == {'A', 'B'}
        assert pair[0]['choice_places'] == pair[1]['choice_places']
        assert pair[0]['messages'][-1] == pair[1]['messages'][-1]
    score_decisions = [r for r in rows if r['Q'] == 'decision']
    by_prompt = {r['prompt_id']: r for r in decisions}
    assert len(score_decisions) == len(decisions) * len(models)
    for r in score_decisions:
        assert r['choice_places'] == by_prompt[r['prompt_id']]['choice_places']
    choice_effects = []
    for b in BOUNDS:
        for method in ('full', 'view'):
            rr = [r for r in score_decisions if r['boundary'] == b and r['method'] == method and not r['accessible']]
            vector = paired_delta(rr, models, 'choose_A', lambda r: r['version'] == 'A', lambda r: r['version'] == 'B')
            by_position = {}
            strata = []
            for p in (1, 2):
                vec = {i: v for i, v in vector.items() if position[i] == p}
                result = boot.vector(vec)
                result.pop('p_one_sided'); result.pop('null')
                by_position[str(p)] = result
                strata.append(list(vec.values()))
            # Equal-position sensitivity, with independent resampling within
            # each observed position stratum. No new hypothesis test or p-value.
            rng = random.Random(spec['bootstrap']['seed'])
            reps = [mean([mean([rng.choice(v) for _ in v]) for v in strata])
                    for _ in range(spec['bootstrap']['replicates'])]
            choice_effects.append({'boundary': b, 'method': method,
                'A_location_position': by_position,
                'equal_position_estimate': mean([mean(v) for v in strata]),
                'equal_position_ci95': [quantile(reps, .025), quantile(reps, .975)]})
    report = {
        'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope': 'Secondary capability-conditioned and newly requested descriptive audits; frozen primary analyses unchanged',
        'primary_rule': spec['primary_estimand'],
        'eligibility_rule': 'Observed complete/zero-use translation U2 mean >= .85 per confirmation model-language unit; no item-level filter was specified. Eligibility fixed in bootstrap. Equal model weights; eligible response ratios recomputed per draw.',
        'bootstrap': spec['bootstrap'], 'capability_threshold': spec['capability_gate'],
        'translation_units': translation,
        'comprehension_unconditional': unconditional,
        'comprehension_capability_eligible': gated,
        'state_correct_by_boundary': state_detail,
        'pooled_state_correct_original': pooled_state,
        'pooled_state_correct_capability_eligible': state_gated,
        'compiler_vs_delete_retention': {
            **frozen['confirmatory']['H3_components']['partial_event_retention_improvement'],
            'status': 'Prespecified component of frozen H3, not a new post-hoc test'},
        'choice_order': {
            'assignment': 'Deterministic scene-ID parity, not randomized; approximately balanced',
            'skeleton_counts_A_position': dict(collections.Counter(position.values())),
            'identical_order_and_question_within_AB_pairs': True,
            'pair_count_in_plan': len(groups), 'scored_decision_records': len(score_decisions),
            'interpretation': 'Paired contrast holds option order fixed; order-stratified and equal-position estimates are additional descriptive sensitivities.',
            'effects': choice_effects},
        'source_sha256': {**source_hashes, str(specpath.relative_to(ROOT)): sha(specpath),
                          str(frozen_path.relative_to(ROOT)): sha(frozen_path),
                          str(planpath.relative_to(ROOT)): sha(planpath)},
        'checks': {'frozen_plan_inputs_and_code_match': True,
                   'frozen_understand_estimate_reproduced': True,
                   'frozen_state_correct_estimate_and_CI_reproduced': True,
                   'no_new_generation_or_changed_scorer': True,
                   'no_new_confirmatory_tests': True},
    }
    OUT.mkdir(exist_ok=True)
    (OUT / 'results.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    for name in ('comprehension_unconditional', 'comprehension_capability_eligible', 'pooled_state_correct_capability_eligible'):
        print(name, report[name]['estimate'], report[name]['ci95'], report[name]['eligible_endpoints'])
    print('Choice order', report['choice_order']['skeleton_counts_A_position'])


if __name__ == '__main__':
    main()

"""Descriptive E3 cells for the complete frozen six-model method cohort.

Uses the original scorer outputs and paired bootstrap. No new tests or labels.
"""
from pathlib import Path
import argparse, collections, datetime, hashlib, json, sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from oc_v2.analyze import Bootstrap, model_skeleton_vector
from oc_v2.design import BOUNDARIES


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verification', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    audit = json.loads(args.verification.read_text())
    spec = json.loads((ROOT / 'docs/access-v2/spec-lock.json').read_text())
    lockpath = ROOT / 'docs/access-v2/final-lock.json'
    lock = json.loads(lockpath.read_text())
    models = spec['method_models']
    assert len(models) == 6 and set(models) == set(audit['completed_method_models'])
    for path, digest in {**lock['input_sha256'], **lock['code_sha256']}.items():
        assert sha(ROOT / path) == digest, path
    sources = [Path(x) for x in audit['analysis_score_files']
               if Path(x).parent.name == 'discovery' and Path(x).stem in models]
    assert len(sources) == len(models)
    rows = []
    for path in sources:
        assert sha(path) == audit['models'][path.stem]['discovery']['scores_sha256']
        rows.extend(json.loads(line) for line in path.read_text().splitlines())
    scenes = set(lock['subsets']['E3'])
    assert len(scenes) == 48
    boot = Bootstrap()
    estimates = []
    for boundary in BOUNDARIES:
        for method in ['full', 'prose', 'self_filter', 'hard', 'view']:
            for accessible in [False, True]:
                selected = [r for r in rows if r['set'] == 'discovery'
                            and r['item'] in scenes and r['boundary'] == boundary
                            and r['Q'] in ('content', 'plan') and r['delay'] == 0
                            and r['accessible'] == accessible
                            and r['method'] == ('full' if method == 'prose' else method)
                            and r['representation'] == ('R3' if method == 'prose' else 'R2')]
                expected = {(m, i, q, v) for m in models for i in scenes
                            for q in ('content', 'plan') for v in ('A', 'B')}
                observed = {(r['model'], r['item'], r['Q'], r['version']) for r in selected}
                assert len(selected) == len(observed) == 1152 and observed == expected
                metric = 'hit_t' if accessible else 'D'
                result = boot.vector(model_skeleton_vector(selected, models, metric))
                result.pop('p_one_sided', None)
                result.pop('null', None)
                estimates.append({'panel': 'discovery_method_six_models',
                                  'models': models, 'boundary': boundary, 'method': method,
                                  'accessible': accessible, 'metric': metric,
                                  'endpoints': len(selected),
                                  'status_counts': dict(collections.Counter(r['status'] for r in selected)),
                                  **result})
    report = {'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'scope': 'Complete prespecified six-model E3 cohort; 48 paired scenes; descriptive intervals only',
              'bootstrap_replicates': boot.B, 'bootstrap_seed': boot.seed,
              'frozen_lock_sha256': sha(lockpath),
              'verification_sha256': sha(args.verification),
              'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in sources},
              'descriptive_estimates': estimates, 'human_labels': 0}
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print('Verified and reported', len(estimates), 'balanced six-model method cells')


if __name__ == '__main__':
    main()

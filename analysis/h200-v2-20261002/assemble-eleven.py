"""Merge audited Seed evidence into the frozen eleven-model analysis."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
base = root / 'analysis/h200-v2-20261002'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
old_path = base / 'ten-model-verification.json'
seed_path = base / 'seed-verification.json'
old = json.loads(old_path.read_text())
seed = json.loads(seed_path.read_text())
spec = json.loads((root / 'docs/access-v2/spec-lock.json').read_text())
assert old['actual_human_annotations'] == seed['actual_human_annotations'] == 0
assert not (set(old['models']) & set(seed['models']))
models = {**old['models'], **seed['models']}
assert set(models) == set(spec['main_models']) and len(models) == 11
scorefiles = old['analysis_score_files'] + seed['analysis_score_files']
for name in scorefiles:
    p = Path(name)
    model, phase = p.stem, p.parent.name
    assert sha(p) == models[model][phase]['scores_sha256']
    raw = p.parents[2] / 'responses' / phase / model / 'responses.jsonl'
    assert sha(raw) == models[model][phase]['responses_sha256']
for model, phases in models.items():
    if 'pilot' in phases:
        own = next(Path(p).parents[2] for p in scorefiles if Path(p).stem == model)
        assert sha(own / 'scores/pilot' / (model + '.jsonl')) == phases['pilot']['scores_sha256']
        assert sha(own / 'responses/pilot' / model / 'responses.jsonl') == phases['pilot']['responses_sha256']
results = base / 'eleven-model-results.json'
assert not results.exists(), 'Do not overwrite a completed aggregate without reviewing it.'
subprocess.run([sys.executable, str(root / 'tools/analyze_access_v2.py'), '--scores', *scorefiles,
                '--out', str(results)], check=True)
report = json.loads(results.read_text())
ten_results = json.loads((base / 'ten-model-results.json').read_text())
core_results = json.loads((base / 'four-core-results.json').read_text())
assert report['confirmatory'] == ten_results['confirmatory'] == core_results['confirmatory']
old_method = [r for r in ten_results['exploratory_paired_contrasts'] if r['contrast'].startswith('E3 ')]
new_method = [r for r in report['exploratory_paired_contrasts'] if r['contrast'].startswith('E3 ')]
assert old_method == new_method
actual = sum(s['actual_records'] for phases in models.values() for s in phases.values())
endpoints = sum(s['scored_endpoints'] for phases in models.values() for s in phases.values())
assert actual == 220088 and endpoints == 206264
audit = {**old, 'verified_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'models': models, 'total_actual_records': actual,
         'total_scored_endpoints_including_pilot': endpoints,
         'completed_main_models': spec['main_models'], 'pending_main_models': [],
         'full_eleven_model_campaign_complete': True,
         'analysis_score_files': scorefiles, 'analysis_results_sha256': sha(results),
         'verification_sources': {**old['verification_sources'], str(old_path.relative_to(root)): sha(old_path),
                                  str(seed_path.relative_to(root)): sha(seed_path)},
         'six_model_method_contrasts_exactly_unchanged': True,
         'seed_hardware_cluster': 'snellius', 'seed_slurm_job': seed['generation_job_id'],
         'all_current_merged_score_and_response_hashes_rechecked': True}
(base / 'eleven-model-verification.json').write_text(json.dumps(audit, indent=2) + '\n')
print(json.dumps({k: audit[k] for k in ('total_actual_records', 'total_scored_endpoints_including_pilot',
                                      'full_eleven_model_campaign_complete', 'actual_human_annotations',
                                      'confirmatory_exactly_matches_saved_four_core',
                                      'six_model_method_contrasts_exactly_unchanged')}, indent=2))

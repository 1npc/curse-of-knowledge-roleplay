"""Verify the complete Snellius archive and independently rescore Seed."""
from pathlib import Path
import collections
import datetime
import hashlib
import json
import sys
import tarfile

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
from oc_v2.score import score_record
from harness.h200_generate_v2 import PROTOCOL

base = root / 'analysis/h200-v2-20261002'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
digest = lambda d: hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
receipt = json.loads((base / 'seed-archive-receipt.json').read_text())
archive = base / 'seed-complete.tar.gz'
assert archive.stat().st_size == receipt['bytes'] and sha(archive) == receipt['sha256']
data = base / 'seed'
data.mkdir(exist_ok=True)
with tarfile.open(archive, 'r:gz') as source:
    for member in source.getmembers():
        p = Path(member.name)
        assert member.isfile() and not p.is_absolute() and '..' not in p.parts
    for member in source.getmembers():
        target = data / member.name
        assert data.resolve() in target.resolve().parents
        content = source.extractfile(member).read()
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert target.read_bytes() == content
        else:
            target.write_bytes(content)
manifest = json.loads((data / 'analysis/seed-complete-manifest.json').read_text())
for name, info in manifest['files'].items():
    p = data / name
    assert p.stat().st_size == info['bytes'] and sha(p) == info['sha256'], name
lock = json.loads((root / 'docs/access-v2/final-lock.json').read_text())
for section in ('input_sha256', 'code_sha256'):
    for name, value in lock[section].items():
        assert sha(root / name) == value, name
for entry in lock['model_plans'].values():
    assert sha(root / entry['path']) == entry['sha256']
amendment_path = root / 'docs/access-v2/snellius-seed-amendment.json'
assert sha(data / 'code/docs/access-v2/snellius-seed-amendment.json') == sha(amendment_path)
amendment = json.loads(amendment_path.read_text())
for name, value in amendment['deployed_file_sha256'].items():
    assert sha(root / name) == value, name
    if (data / 'code' / name).exists():
        assert sha(data / 'code' / name) == value, name
job = receipt['generation_job_id']
assert job == manifest['generation_job_id']
assert any(line == job + '|COMPLETED|0:0' for line in manifest['sacct'].splitlines())
submission = json.loads((data / 'operations/snellius-submission.json').read_text())
assert str(submission['generation_job_id']) == job and submission['h200_reservation_confirmed']
preflight = json.loads((data / 'operations/allocated-gpu-preflight.json').read_text())
assert preflight['slurm_job_id'] == job and 'H100' in preflight['name']
assert preflight['memory_total_mib'] >= 90000 and preflight['memory_used_mib_before_load'] < 100
assert preflight['utilization_before_load'] <= 5 and preflight['no_compute_process_before_load']
assert preflight['engine'] == amendment['engine'] and preflight['frozen_protocol'] == PROTOCOL
weights = json.loads((data / 'operations/weights-verified.json').read_text())
seed_weights = weights['models']['seed_oss_36b']
verified_weights = json.loads((base / 'snellius-weight-verification.json').read_text())
assert weights['ok'] and seed_weights['ok']
assert seed_weights['files'] == verified_weights['files'] and len(seed_weights['files']) == 27
assert seed_weights['all_files_match_h200_verified_snapshot'] and seed_weights['all_frozen_official_hashes_match']
assert sum(f['bytes'] for f in seed_weights['files'].values()) == 72314506146
model = 'seed_oss_36b'
r = data / 'responses/discovery' / model
run = json.loads((r / 'run.json').read_text())
runtime = json.loads((r / ('runtime-access-v2-discovery-' + model + '.json')).read_text())
summary = json.loads((r / ('summary-access-v2-discovery-' + model + '.json')).read_text())
plan = root / ('items/access-v2/model-plans/discovery-' + model + '.jsonl')
plans = [json.loads(line) for line in plan.read_text().splitlines() if line.strip()]
plans.sort(key=lambda p: p['prompt_id'])
assert not any(p.get('next_step') for p in plans)
expected = {p['prompt_id'] for p in plans}
raw = r / 'responses.jsonl'
responses = [json.loads(line) for line in raw.read_text().splitlines() if line.strip()]
ids = [record['prompt_id'] for record in responses]
assert len(ids) == len(set(ids)) == len(expected) == 6336 and set(ids) == expected
runsha = digest(run)
reference = json.loads((root / 'harness/weights_reference.json').read_text())['models'][model]
assert run['prompts_sha256'] == sha(plan) and run['n_prompts'] == 6336
assert run['runner_sha256'] == sha(root / 'harness/h200_generate_v2.py')
assert run['protocol'] == PROTOCOL and run['engine'] == amendment['engine']
assert run['revision'] == reference['revision'] == seed_weights['revision']
assert run['chat_template_sha256'] == seed_weights['files']['chat_template.jinja']['sha256']
assert run['chat_template_kwargs'] == {'thinking_budget': 0}
assert runtime['status'] == 'finished' and str(runtime['slurm_job']) == job
assert runtime['cuda_visible_devices'] == preflight['physical_gpu_uuid']
assert summary['run_sha256'] == runsha == runtime['run_sha256']
assert summary['responses_sha256'] == sha(raw) and summary['records'] == summary['planned'] == len(expected)
assert summary['interrupted_chunks'] == 0
statuses = dict(collections.Counter(rec['status'] for rec in responses))
assert statuses == summary['status']
for rec in responses:
    assert rec['model'] == model and rec['run_sha256'] == runsha and rec['attempt'] == 'first' and rec['step'] == 1
    if 'text' in rec:
        assert hashlib.sha256(rec['text'].encode()).hexdigest() == rec['text_sha256']
    assert rec['prompt_tokens'] + 400 <= 8192 and rec.get('output_tokens', 0) <= 400
chunkfiles = sorted((r / 'chunks').glob('chunk-*.jsonl'))
chunk_records = []
for index, p in enumerate(chunkfiles):
    records = [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
    intent = json.loads(p.with_suffix('.intent.json').read_text())
    chunkplans = plans[index * run['chunk']:(index + 1) * run['chunk']]
    assert [rec['prompt_id'] for rec in records] == [p['prompt_id'] for p in chunkplans]
    assert intent['run_id'] == runtime['run_id']
    assert intent['binding'] == {'run_sha256': runsha, 'chunk': p.stem,
                                 'prompt_ids_sha256': digest([p['prompt_id'] for p in chunkplans]),
                                 'messages_sha256': digest([p['messages'] for p in chunkplans])}
    chunk_records.extend(records)
assert sorted(chunk_records, key=lambda rec: rec['prompt_id']) == responses
assert len(list((r / 'chunks').glob('chunk-*.intent.json'))) == len(chunkfiles) == 25
assert not list((r / 'chunks').glob('*retry*')) and not list((r / 'chunks').glob('*.interrupted.json'))
items = {item['id']: item for item in json.loads((root / 'items/access-v2/discovery-items.json').read_text())['items']}
replies = {rec['prompt_id']: rec for rec in responses}
# The original scoring CLI preserves the plan's file order, not generation order.
fileplans = [json.loads(line) for line in plan.read_text().splitlines() if line.strip()]
scores = [score_record(p, items[p['item']], replies) for p in fileplans]
for record in scores:
    record['model'] = model
regenerated = ''.join(json.dumps(rec, ensure_ascii=False, sort_keys=True) + '\n' for rec in scores).encode()
scorefile = data / 'scores/discovery' / (model + '.jsonl')
assert hashlib.sha256(regenerated).hexdigest() == sha(scorefile)
report = {'verified_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'cluster': 'snellius', 'generation_job_id': job,
          'new_archive_sha256': receipt['sha256'], 'all_archive_file_digests_match': True,
          'scientific_inputs_and_code_unchanged': True, 'hardware_amendment_sha256': sha(amendment_path),
          'slurm_completed_exit0': True, 'all_weight_files_match_pinned_h200_snapshot': True,
          'models': {model: {'discovery': {
              'actual_records': len(responses), 'scored_endpoints': len(scores),
              'status_counts': statuses, 'physical_gpu_uuid': runtime['cuda_visible_devices'],
              'hardware_cluster': 'snellius', 'slurm_job_id': job,
              'no_missing_or_duplicate_ids': True, 'all_chunk_intent_bindings_match': True,
              'frozen_plan_sha256': sha(plan), 'runner_sha256': run['runner_sha256'],
              'responses_sha256': sha(raw), 'scores_sha256': sha(scorefile),
              'frozen_scorer_recomputed_exact_match': True}}},
          'total_actual_records': len(responses), 'total_scored_endpoints_including_pilot': len(scores),
          'confirmatory_actual_records': 0, 'actual_human_annotations': 0,
          'full_eleven_model_campaign_complete': False, 'analysis_score_files': [str(scorefile)]}
(base / 'seed-verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))

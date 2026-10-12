"""Mirror verified external Seed evidence before releasing the original finalizer."""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import tarfile
import time

root = Path('/data/qianru/over-comprehension-v2-20261001')
ops = root / 'operations'
input_path = root / 'analysis/seed-snellius-completion-input.json'
package = json.loads(input_path.read_text())
receipt, audit = package['archive_receipt'], package['local_verification']
assert audit['slurm_completed_exit0'] and audit['all_archive_file_digests_match']
assert audit['scientific_inputs_and_code_unchanged'] and audit['all_weight_files_match_pinned_h200_snapshot']
job = receipt['generation_job_id']
assert job == audit['generation_job_id']
archive = root / 'analysis/seed-snellius-complete.tar.gz.part'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert archive.stat().st_size == receipt['bytes'] and sha(archive) == receipt['sha256']
evidence = root / 'analysis/seed-snellius-evidence'
evidence.mkdir(exist_ok=True)
with tarfile.open(archive, 'r:gz') as source:
    for member in source.getmembers():
        p = Path(member.name)
        assert member.isfile() and not p.is_absolute() and '..' not in p.parts
    for member in source.getmembers():
        target = evidence / member.name
        assert evidence.resolve() in target.resolve().parents
        content = source.extractfile(member).read()
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert target.read_bytes() == content
        else:
            target.write_bytes(content)
manifest = json.loads((evidence / 'analysis/seed-complete-manifest.json').read_text())
for name, info in manifest['files'].items():
    p = evidence / name
    assert p.stat().st_size == info['bytes'] and sha(p) == info['sha256'], name
assert manifest['generation_job_id'] == job
assert any(line == job + '|COMPLETED|0:0' for line in manifest['sacct'].splitlines())
model = 'seed_oss_36b'
phase = audit['models'][model]['discovery']
source_response = evidence / 'responses/discovery' / model
assert sha(source_response / 'responses.jsonl') == phase['responses_sha256']
assert sha(evidence / 'scores/discovery' / (model + '.jsonl')) == phase['scores_sha256']
assert phase['actual_records'] == phase['scored_endpoints'] == 6336
summary = json.loads((source_response / ('summary-access-v2-discovery-' + model + '.json')).read_text())
assert summary['planned'] == summary['records'] == 6336 and summary['interrupted_chunks'] == 0

def atomic(p, data):
    temp = p.with_suffix(p.suffix + '.tmp')
    with temp.open('wb') as target:
        target.write(data)
        target.flush()
        os.fsync(target.fileno())
    os.replace(temp, p)

def mirror(source, target):
    content = source.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == content, 'Never overwrite a different Seed output.'
    else:
        atomic(target, content)

lock = (ops / 'queue.lock').open('a+')
fcntl.flock(lock, fcntl.LOCK_EX)
state = json.loads((ops / 'queue.json').read_text())
previous = state['models'][model]
assert previous['status'] == 'external_reserved' and previous['external_generation_job_id'] == job
assert all(r['status'] == 'finished' for key, r in state['models'].items() if key != model)
target_response = root / 'responses/discovery' / model
assert not (target_response / 'run.json').exists(), 'An unexpected H200 Seed run requires inspection.'
for source in source_response.rglob('*'):
    if source.is_file():
        mirror(source, target_response / source.relative_to(source_response))
mirror(evidence / 'scores/discovery' / (model + '.jsonl'), root / 'scores/discovery' / (model + '.jsonl'))
assert sha(target_response / 'responses.jsonl') == phase['responses_sha256']
assert sha(root / 'scores/discovery' / (model + '.jsonl')) == phase['scores_sha256']
completion = {'completed_unix': time.time(), 'model': model, 'cluster': 'snellius',
              'slurm_job': job, 'previous_queue_record': previous.copy(),
              'archive_sha256': receipt['sha256'], 'local_verification': audit,
              'mirrored_raw_and_scores_match': True, 'no_h200_generation_started': True,
              'full_evidence_root': str(evidence), 'other_model_records_unchanged': True}
atomic(ops / 'seed-snellius-completion.json', (json.dumps(completion, indent=2) + '\n').encode())
final_archive = root / 'analysis/seed-snellius-complete.tar.gz'
assert not final_archive.exists()
os.replace(archive, final_archive)
previous.update(status='finished', finished_unix=completion['completed_unix'],
                external_completion_receipt=str(ops / 'seed-snellius-completion.json'),
                external_response_sha256=phase['responses_sha256'], external_score_sha256=phase['scores_sha256'],
                external_raw_records=6336, external_status_counts=phase['status_counts'])
atomic(ops / 'queue.json', (json.dumps(state, indent=2) + '\n').encode())
fcntl.flock(lock, fcntl.LOCK_UN)
print(json.dumps(completion))

"""Archive only the completed, registered Snellius Seed experiment."""
from pathlib import Path
import hashlib
import json
import subprocess
import tarfile
import time

root = Path('/gpfs/work4/0/prjs1226/qmeng1/over-comprehension/access-v2-seed-20261003')
submission = json.loads((root / 'operations/snellius-submission.json').read_text())
job = str(submission['generation_job_id'])
accounting = subprocess.check_output(
    ['sacct', '-j', job, '--format=JobID,State,ExitCode', '-n', '-P'], text=True)
assert any(line == job + '|COMPLETED|0:0' for line in accounting.splitlines()), accounting
response = root / 'responses/discovery/seed_oss_36b'
summary = json.loads((response / 'summary-access-v2-discovery-seed_oss_36b.json').read_text())
runtime = json.loads((response / 'runtime-access-v2-discovery-seed_oss_36b.json').read_text())
assert summary['planned'] == summary['records'] == 6336
assert runtime['status'] == 'finished' and str(runtime['slurm_job']) == job
assert summary['interrupted_chunks'] == 0
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(response / 'responses.jsonl') == summary['responses_sha256']
score = root / 'scores/discovery/seed_oss_36b.jsonl'
assert score.is_file()
assert sum(bool(line.strip()) for line in score.read_text().splitlines()) == 6336
files = sorted(set([p for p in response.rglob('*') if p.is_file()] + [score] +
                   [p for p in (root / 'operations').rglob('*') if p.is_file()] +
                   [p for p in (root / 'logs').glob('*') if p.is_file()] +
                   [root / ('code/' + name) for name in (
                       'docs/access-v2/snellius-seed-amendment.json',
                       'docs/access-v2/seed-weight-digests.json',
                       'harness/snellius_seed_generate_v2.py',
                       'harness/snellius_seed_verify_v2.py',
                       'harness/snellius_seed_generate_v2.sbatch',
                       'harness/snellius_seed_verify_v2.sbatch',
                       'harness/h200_generate_v2.py')]))
manifest = {'created_unix': time.time(), 'cluster': 'snellius',
            'generation_job_id': job, 'sacct': accounting, 'summary': summary,
            'actual_human_annotations': 0,
            'files': {str(p.relative_to(root)): {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in files}}
mp = root / 'analysis/seed-complete-manifest.json'
mp.parent.mkdir(exist_ok=True)
mp.write_text(json.dumps(manifest, indent=2) + '\n')
files.append(mp)
archive = root / 'analysis/seed-complete.tar.gz'
assert not archive.exists(), 'Existing archive must be inspected, not overwritten.'
with tarfile.open(archive, 'w:gz') as target:
    for p in files:
        target.add(p, arcname=str(p.relative_to(root)), recursive=False)
receipt = {'archive': str(archive), 'bytes': archive.stat().st_size, 'sha256': sha(archive),
           'generation_job_id': job, 'records': summary['records']}
(root / 'analysis/seed-complete-archive.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))

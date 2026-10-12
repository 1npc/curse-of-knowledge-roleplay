"""Read only the registered Seed job and its small evidence/operational files."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess

ROOT = Path('/gpfs/work4/0/prjs1226/qmeng1/over-comprehension/access-v2-seed-20261003')


def read(name):
    p = ROOT / name
    return json.loads(p.read_text()) if p.is_file() else None


def command(args):
    r = subprocess.run(args, capture_output=True, text=True)
    return {'returncode': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr}


submission = read('operations/snellius-submission.json')
job = submission['generation_job_id']
previous_jobs = submission.get('previous_generation_job_ids', [submission['previous_generation_job_id']])
response = ROOT / 'responses/discovery/seed_oss_36b'
summary = read('responses/discovery/seed_oss_36b/summary-access-v2-discovery-seed_oss_36b.json')
weights = read('operations/weights-verified.json')
chunk_files = list((response / 'chunks').glob('*chunk-*.jsonl'))
chunks = {'completed_files': len(chunk_files), 'records': 0, 'interrupted_markers': len(list((response / 'chunks').glob('*.interrupted.json')))}
for p in chunk_files:
    with p.open() as f:
        chunks['records'] += sum(bool(line.strip()) for line in f)
files = {}
for name in ['responses/discovery/seed_oss_36b/responses.jsonl', 'scores/discovery/seed_oss_36b.jsonl', 'operations/weights-verified.json']:
    p = ROOT / name
    if p.is_file():
        files[name] = {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
log = ROOT / 'logs' / ('seed-' + job + '.log')
tail = command(['tail', '-n', '12', str(log)]) if log.exists() else None
result = {'captured_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'cluster': 'snellius', 'root': str(ROOT),
          'submission': submission, 'h200_reservation': read('operations/h200-reservation.json'),
          'squeue': command(['squeue', '-h', '-j', job, '-o', '%i|%j|%T|%P|%R']),
          'job_details': command(['scontrol', 'show', 'job', job]),
          'sacct': command(['sacct', '-j', ','.join([submission['verification_job_id'], job] + previous_jobs),
                            '--format=JobID,State,ExitCode,Elapsed,NodeList', '-n', '-P']),
          'weights_verified': weights, 'gpu_preflight': read('operations/allocated-gpu-preflight.json'),
          'run': read('responses/discovery/seed_oss_36b/run.json'),
          'runtime': read('responses/discovery/seed_oss_36b/runtime-access-v2-discovery-seed_oss_36b.json'),
          'summary': summary, 'chunks': chunks, 'files': files, 'log_tail': tail,
          'scheduling_repair': read('operations/cancelled-held-job.json'), 'release_failure': read('operations/release-attempt.json'),
          'cgroup_preflight_repair': read('operations/cgroup-preflight-repair.json')}
print(json.dumps(result, ensure_ascii=False))

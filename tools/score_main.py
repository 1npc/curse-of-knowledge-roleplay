"""Parallel scoring of the locked main run. Run on a Slurm CPU node, never a login node."""
import argparse
import concurrent.futures
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OC = Path('/gpfs/work4/0/prjs1226/qmeng1/over-comprehension')


def task(job):
    run, model, plan = job
    cmd = [sys.executable, str(ROOT / 'tools/score_run.py'), str(OC / 'runs' / run),
           str(OC / 'inputs/main-v1' / Path(plan).name), str(ROOT / 'items/main/skeletons.json')]
    if run == 'main-v1':
        cmd.append(str(ROOT / 'items/real/skeletons.json'))
    cmd += ['--models', model, '--quiet']
    p = subprocess.run(cmd, capture_output=True, text=True)
    print(json.dumps({'run': run, 'model': model, 'exit': p.returncode,
                      'log': p.stdout.strip(), 'error': p.stderr[-2000:]}), flush=True)
    if p.returncode:
        raise RuntimeError(f'scoring failed for {run}/{model}')
    path = OC / 'runs' / run / model / 'scored.jsonl'
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return {'run': run, 'model': model, 'sha256': h.hexdigest()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=16)
    a = ap.parse_args()
    registry = json.loads((ROOT / 'docs/main-run-registry.json').read_text())
    jobs = [(run, m, c['plan']) for run, c in registry['runs'].items() for m in c['models']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        results = list(pool.map(task, jobs))
    for run in registry['runs']:
        summary = {m: json.loads((OC / 'runs' / run / m / 'score-summary.json').read_text())
                   for m in registry['runs'][run]['models']}
        (OC / 'runs' / run / 'summary.json').write_text(json.dumps(summary, indent=1)+'\n')
    out = OC / 'reports/main-scoring-manifest.json'
    out.write_text(json.dumps({'finished': datetime.now(timezone.utc).isoformat(),
                              'code': str(ROOT), 'files': results}, indent=2)+'\n')


if __name__ == '__main__':
    main()

"""Verify the existing Snellius Seed snapshot on a staging node; no download."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import os
import socket
import time


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 24), b''):
            h.update(block)
    return h.hexdigest()


def audit(root):
    code = root / 'code'
    amendment = json.loads((code / 'docs/access-v2/snellius-seed-amendment.json').read_text())
    for name, expected in amendment['deployed_file_sha256'].items():
        assert sha(code / name) == expected, name
    return amendment


def main():
    root = Path(os.environ['OC'])
    amendment = audit(root)
    ops = root / 'operations'
    target = ops / 'weights-verified.json'
    assert not target.exists(), 'Verification already recorded; inspect before any retry.'
    report = {'host': socket.gethostname(), 'slurm_job': os.environ['SLURM_JOB_ID'],
              'started_unix': time.time(), 'models': {}, 'ok': False}
    try:
        for name, expected in amendment['engine'].items():
            assert importlib.metadata.version(name) == expected.split('+')[0], name
        model = 'seed_oss_36b'
        reference = json.loads((root / 'code/harness/weights_reference.json').read_text())['models'][model]
        previous = json.loads((root / 'code/docs/access-v2/seed-weight-digests.json').read_text())
        assert reference['revision'] == previous['revision'] == amendment['revision']
        path = Path(amendment['weights_path'])
        verified = {}
        for name, info in reference['files'].items():
            p = path / name
            assert p.is_file() and p.stat().st_size == info['bytes'], name
            digest = sha(p)
            assert digest == previous['files'][name]['sha256'], name
            if 'sha256' in info:
                assert digest == info['sha256'], name
            verified[name] = {'bytes': p.stat().st_size, 'sha256': digest}
            print('VERIFIED', name, flush=True)
        report['models'][model] = {'ok': True, 'repo': reference['repo'], 'revision': reference['revision'],
                                  'path': str(path), 'files': verified,
                                  'all_files_match_h200_verified_snapshot': True,
                                  'all_frozen_official_hashes_match': True}
        report['ok'] = True
    except Exception as e:
        report['error'] = repr(e)
        raise
    finally:
        report['finished_unix'] = time.time()
        tmp = target.with_suffix('.tmp')
        tmp.write_text(json.dumps(report, indent=2) + '\n')
        tmp.replace(target)


if __name__ == '__main__':
    main()

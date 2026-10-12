"""Resume transport failures with the unchanged, pinned range supplier.

Operational recovery only: completed generations are never retried. Every
download still passes the original Content-Range and frozen SHA checks.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

SUPPLIER_SHA = '6c515328325baaa9b68273357afe61e3afbb4fb91199ca1709b987ad680862b4'
ORDER = ['gemma4_12b', 'falcon_h1_34b', 'mistral_small3', 'seed_oss_36b']
TRANSIENT_CURL_CODES = {6, 7, 18, 22, 28, 35, 52, 55, 56}


def atomic(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    os.replace(temp, path)


def retryable(error):
    if 'SHA' in error or 'Content-Range' in error:
        return False
    match = re.search(r'curl=(\d+)', error)
    if match:
        return int(match.group(1)) in TRANSIENT_CURL_CODES
    match = re.search(r'returned non-zero exit status (\d+)', error)
    return bool('curl' in error and match and
                int(match.group(1)) in TRANSIENT_CURL_CODES)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    root = args.root
    ops = root / 'operations'
    supplier = root / 'code/harness/h200_range_weights_v2.py'
    assert hashlib.sha256(supplier.read_bytes()).hexdigest() == SUPPLIER_SHA
    lock = (ops / 'weight-recovery.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    state_path = ops / 'weight-recovery-state.json'
    assert not state_path.exists(), 'Recovery already recorded; inspect before relaunch'
    history = ops / 'weight-recovery-attempts'
    history.mkdir(exist_ok=True)
    state = {'pid': os.getpid(), 'started_unix': time.time(),
             'supplier_sha256': SUPPLIER_SHA, 'order': ORDER, 'models': {}}
    atomic(state_path, state)
    for model in ORDER:
        state['models'][model] = {'attempts': []}
        status = state['models'][model]
        receipt_path = ops / ('range-weight-transport-' + model + '.json')
        for attempt in range(1, 4):
            queue = json.loads((ops / 'queue.json').read_text())['models'][model]
            ready = json.loads((ops / 'weights-verified.json').read_text())['models'].get(model, {})
            if queue['status'] in ('finished', 'failed') or ready.get('ok'):
                status['status'] = 'already_accounted'
                break
            if receipt_path.exists():
                (history / f'{model}-{attempt}-before.json').write_bytes(receipt_path.read_bytes())
            record = {'attempt': attempt, 'started_unix': time.time()}
            status['attempts'].append(record)
            status['status'] = 'downloading'
            command = ['python3', '-u', str(supplier), '--root', str(root),
                       '--workers', '32', '--model', model]
            with (root / 'logs' / f'weight-recovery-{model}-{attempt}.log').open('ab') as log:
                child = subprocess.Popen(command, cwd=root / 'code',
                                         stdin=subprocess.DEVNULL, stdout=log,
                                         stderr=subprocess.STDOUT)
                record['child_pid'] = child.pid
                atomic(state_path, state)
                code = child.wait()
            record.update(returncode=code, finished_unix=time.time())
            receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
            if receipt_path.exists():
                (history / f'{model}-{attempt}-after.json').write_bytes(receipt_path.read_bytes())
            ready = json.loads((ops / 'weights-verified.json').read_text())['models'].get(model, {})
            if code == 0 and receipt.get('ok') and ready.get('ok'):
                status['status'] = 'verified'
                atomic(state_path, state)
                break
            error = receipt.get('error', '')
            record['error'] = error
            if code != 0 or not retryable(error) or attempt == 3:
                status['status'] = 'needs_attention'
                atomic(state_path, state)
                break
            status['status'] = 'waiting_to_retry'
            atomic(state_path, state)
            time.sleep(30 * attempt)
        atomic(state_path, state)
    state['finished_unix'] = time.time()
    atomic(state_path, state)


if __name__ == '__main__':
    main()

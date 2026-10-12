"""Restrict the preserved idle-GPU queue to GPU 5 after the user's update.

Only queue allocation changes. The original generator, plans, protocol, scores
and original operational amendment remain byte-identical. Existing per-GPU and
worker-slot locks serialize both waiting controllers on this one device.
"""
from pathlib import Path
import hashlib
import json

import h200_queue_idle_v2 as queue

GPU5 = {'5': 'GPU-63686987-a70f-607d-9886-af187b67a14a'}
original_audit = queue.audit


def audit_gpu5(root):
    allowed = original_audit(root)
    amendment = json.loads((root / 'code/docs/access-v2/gpu5-only-amendment.json').read_text())
    assert amendment['allowed_gpu_uuid'] == GPU5
    assert {key: allowed[key] for key in GPU5} == GPU5
    for name, expected in amendment['operational_code_sha256'].items():
        assert hashlib.sha256((root / 'code' / name).read_bytes()).hexdigest() == expected, name
    print('GPU_POLICY gpu5_only; occupied means wait; no other GPU permitted', flush=True)
    return dict(GPU5)


if __name__ == '__main__':
    queue.audit = audit_gpu5
    queue.main()

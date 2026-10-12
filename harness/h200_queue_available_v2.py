"""Use any verified idle H200 after the user's latest hardware instruction.

The original queue, generator, frozen scientific inputs and scoring are kept
unchanged. Existing worker-slot and per-GPU locks prevent duplicate allocation.
"""
import hashlib
import json

import h200_queue_idle_v2 as queue

original_audit = queue.audit


def audit_available(root):
    allowed = original_audit(root)
    amendment = json.loads(
        (root / 'code/docs/access-v2/available-gpu-amendment.json').read_text()
    )
    assert amendment['allowed_gpu_uuid'] == allowed
    for name, expected in amendment['operational_code_sha256'].items():
        assert hashlib.sha256((root / 'code' / name).read_bytes()).hexdigest() == expected, name
    print('GPU_POLICY any_verified_idle; occupied GPUs excluded; existing locks retained', flush=True)
    return dict(allowed)


if __name__ == '__main__':
    queue.audit = audit_available
    queue.main()

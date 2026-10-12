"""Hardware adapter for one Slurm H100 allocation; scientific runner unchanged."""
from pathlib import Path
import json
import os
import subprocess

import h200_generate_v2 as frozen
from snellius_seed_verify_v2 import audit


def validate_slurm_gpu():
    root = Path(os.environ['OC'])
    amendment = audit(root)
    receipt = json.loads((root / 'operations/snellius-submission.json').read_text())
    assert str(receipt['generation_job_id']) == os.environ.get('SLURM_JOB_ID')
    assert receipt['h200_reservation_confirmed'], 'Cross-cluster reservation is missing.'
    assigned = os.environ.get('SLURM_JOB_GPUS', '')
    assert assigned.isdigit(), 'Expected exactly one physical GPU assigned by Slurm.'
    rows = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,name,memory.total,memory.used,utilization.gpu',
                                    '--format=csv,noheader,nounits'], text=True)
    visible = [[part.strip() for part in line.split(',')] for line in rows.splitlines() if line.strip()]
    print('SLURM_GPU_BINDING', json.dumps({'slurm_job_gpus': assigned,
                                         'cuda_visible_devices_before_adapter': os.environ.get('CUDA_VISIBLE_DEVICES'),
                                         'nvidia_smi_visible_rows': visible}), flush=True)
    # Slurm's GPU IDs are global IDs. With device cgroups, nvidia-smi can
    # report the sole allocated card with a different local index.
    if len(visible) == 1:
        row = visible[0]
        binding = 'sole GPU visible inside the one-GPU Slurm allocation'
    else:
        matching = [r for r in visible if r[0] == assigned]
        assert len(matching) == 1, 'Could not bind the Slurm global GPU ID to one visible device.'
        row = matching[0]
        binding = 'Slurm global GPU ID matched to visible nvidia-smi index'
    index, uuid, name, total, used, util = row
    assert 'H100' in name and float(total) >= 90000, 'Frozen TP=1 run requires the allocated 94 GiB H100.'
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid', '--format=csv,noheader'], text=True)
    assert uuid not in apps and float(used) < 100 and float(util) <= 5, 'Allocated GPU is occupied; do not share.'
    os.environ['CUDA_VISIBLE_DEVICES'] = uuid
    import torch
    import transformers
    import vllm
    engine = {'torch': torch.__version__, 'transformers': transformers.__version__, 'vllm': vllm.__version__}
    assert engine == amendment['engine'], (engine, amendment['engine'])
    observation = {'slurm_job_id': os.environ['SLURM_JOB_ID'], 'slurm_job_gpus': assigned,
                   'slurm_binding': binding,
                   'physical_index': index, 'physical_gpu_uuid': uuid, 'name': name,
                   'memory_total_mib': float(total), 'memory_used_mib_before_load': float(used),
                   'utilization_before_load': float(util), 'no_compute_process_before_load': True,
                   'engine': engine, 'frozen_protocol': frozen.PROTOCOL}
    target = root / 'operations/allocated-gpu-preflight.json'
    frozen.write_immutable(target, json.dumps(observation, indent=2) + '\n')


if __name__ == '__main__':
    frozen.validate_gpu = validate_slurm_gpu
    frozen.main()

#!/bin/bash
#SBATCH --job-name=oc-v2-seed
#SBATCH --account=ulsei11063
#SBATCH --partition=gpu_h100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=180G
#SBATCH --time=01:00:00
set -eo pipefail
export OC=${SLURM_SUBMIT_DIR:?}
VENV=/gpfs/work4/0/prjs1226/qmeng1/over-comprehension/venv
source /usr/share/lmod/lmod/init/bash
module use /sw/arch/RHEL9/EB_production/2024/modulefiles/all
module load Python/3.12.3-GCCcore-13.3.0
export PATH=$VENV/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 VLLM_NO_USAGE_STATS=1 DO_NOT_TRACK=1
export TOKENIZERS_PARALLELISM=false VLLM_WORKER_MULTIPROC_METHOD=spawn
export CUDA_HOME=$VENV/lib/python3.12/site-packages/nvidia/cu13 CUDA_PATH=$VENV/lib/python3.12/site-packages/nvidia/cu13
export PATH=$CUDA_HOME/bin:$PATH LD_LIBRARY_PATH=$CUDA_HOME/lib:${LD_LIBRARY_PATH:-}
export VLLM_USE_FLASHINFER_SAMPLER=0
CACHE=/scratch-shared/$USER/over-comprehension/cache
export HF_HOME=$CACHE/hf XDG_CACHE_HOME=$CACHE/xdg TRITON_CACHE_DIR=$CACHE/triton
export TORCHINDUCTOR_CACHE_DIR=$CACHE/inductor VLLM_CACHE_ROOT=$CACHE/vllm CUDA_CACHE_PATH=$CACHE/nv
export FLASHINFER_CACHE_DIR=$CACHE/flashinfer TMPDIR=$CACHE/tmp
mkdir -p "$HF_HOME" "$XDG_CACHE_HOME" "$TRITON_CACHE_DIR" "$TORCHINDUCTOR_CACHE_DIR" "$VLLM_CACHE_ROOT" "$CUDA_CACHE_PATH" "$FLASHINFER_CACHE_DIR" "$TMPDIR"
cd "$OC/code"
python harness/snellius_seed_generate_v2.py --prompts "$OC/code/items/access-v2/model-plans/discovery-seed_oss_36b.jsonl" \
  --model seed_oss_36b --models "$OC/code/harness/models.json" --reference "$OC/code/harness/weights_reference.json" \
  --out "$OC/responses/discovery" --run-id access-v2-discovery-seed_oss_36b --chunk 256
python tools/score_access_v2.py --plan "$OC/code/items/access-v2/model-plans/discovery-seed_oss_36b.jsonl" \
  --items "$OC/code/items/access-v2/discovery-items.json" --responses "$OC/responses/discovery/seed_oss_36b/responses.jsonl" \
  --out "$OC/scores/discovery/seed_oss_36b.jsonl" --model seed_oss_36b

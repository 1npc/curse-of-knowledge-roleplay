# Environment for the over-comprehension GPU jobs on Snellius. Sourced by harness/run.slurm.
# Durable things (venv, weights, code, finished runs) live in the project space; caches and live
# run directories live on scratch (regenerable, 14-day expiry). Home is nearly full: no caches there.
source /usr/share/lmod/lmod/init/bash
module use /sw/arch/RHEL9/EB_production/2024/modulefiles/all
module load Python/3.12.3-GCCcore-13.3.0
export OC=/gpfs/work4/0/prjs1226/qmeng1/over-comprehension
export OCS=/scratch-shared/$USER/over-comprehension
# The staging job copies the venv to $OC/venv; until it has verified, OC_VENV may point at the
# original scratch venv (same torch 2.13.0 / transformers 5.17.0 / vLLM 0.29.0 build).
export VENV=${OC_VENV:-$OC/venv}
export PATH=$VENV/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 VLLM_NO_USAGE_STATS=1 DO_NOT_TRACK=1
export HF_HOME=$OCS/cache/hf XDG_CACHE_HOME=$OCS/cache/xdg TRITON_CACHE_DIR=$OCS/cache/triton
export TORCHINDUCTOR_CACHE_DIR=$OCS/cache/inductor VLLM_CACHE_ROOT=$OCS/cache/vllm CUDA_CACHE_PATH=$OCS/cache/nv
export FLASHINFER_CACHE_DIR=$OCS/cache/flashinfer
export TMPDIR=${TMPDIR:-$OCS/cache/tmp}
mkdir -p $HF_HOME $XDG_CACHE_HOME $TRITON_CACHE_DIR $TORCHINDUCTOR_CACHE_DIR $VLLM_CACHE_ROOT $CUDA_CACHE_PATH \
  $FLASHINFER_CACHE_DIR $TMPDIR
# CUDA 13 toolchain ships inside the pip wheels (no matching system module); see the NPCBank judge env.sh.
export CUDA_HOME=$VENV/lib/python3.12/site-packages/nvidia/cu13
export CUDA_PATH=$CUDA_HOME
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib:${LD_LIBRARY_PATH:-}
# Greedy decoding never touches the FlashInfer top-k/top-p sampler; disabling it avoids its JIT build.
export VLLM_USE_FLASHINFER_SAMPLER=0

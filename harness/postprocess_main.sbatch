#!/bin/bash
#SBATCH --job-name=oc-postprocess
#SBATCH --account=ulsei11063
#SBATCH --partition=gpu_mig
#SBATCH --gpus=1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=9
#SBATCH --mem=60G
#SBATCH --time=01:00:00
#SBATCH --output=/scratch-shared/%u/over-comprehension/logs/postprocess-%j.log
set -euo pipefail
CODE=${SLURM_SUBMIT_DIR:?}
source "$CODE/harness/env.sh"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg
PY="$OC/analysis-venv/bin/python"
OUT="$OC/analysis/main-20260929"
"$PY" "$CODE/analysis/gee_check.py" --results "$OUT" &
GEE_PID=$!
"$PY" "$CODE/analysis/make_audit.py" --run "$OC/runs/main-v1" --out "$OUT"
"$PY" "$CODE/analysis/plot_results.py" --results "$OUT" --out "$OUT/figures"
wait "$GEE_PID"

#!/bin/bash
#SBATCH --job-name=oc-analysis
#SBATCH --account=ulsei11063
#SBATCH --partition=gpu_mig
#SBATCH --gpus=1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=9
#SBATCH --mem=60G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch-shared/%u/over-comprehension/logs/analysis-%j.log
set -euo pipefail
CODE=${SLURM_SUBMIT_DIR:?}
source "$CODE/harness/env.sh"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg
PY="$OC/analysis-venv/bin/python"
OUT="$OC/analysis/main-20260929"
mkdir -p "$OUT"
"$PY" "$CODE/analysis/test_numerics.py"
"$PY" "$CODE/analysis/full_analysis.py" --runs "$OC/runs/main-v1" "$OC/runs/main-fs-v1" "$OC/runs/main-robust-v1" --out "$OUT"
"$PY" -m pip freeze > "$OUT/environment.txt"

#!/bin/bash
#SBATCH --job-name=oc-score-main
#SBATCH --account=ulsei11063
#SBATCH --partition=gpu_mig
#SBATCH --gpus=1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=9
#SBATCH --mem=60G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch-shared/%u/over-comprehension/logs/score-%j.log
set -euo pipefail
CODE=${SLURM_SUBMIT_DIR:?}
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python3 "$CODE/tools/score_main.py" --workers 8

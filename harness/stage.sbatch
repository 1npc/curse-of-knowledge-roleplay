#!/bin/bash
#SBATCH --job-name=oc-stage
#SBATCH --account=ulsei11063
#SBATCH --partition=staging
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=06:00:00
#SBATCH --output=/scratch-shared/%u/over-comprehension/logs/stage-%j.log
# Copy the A-tier weights and the vLLM venv from scratch (14-day expiry) to the project space.
# Usage: cd $OC/code/<commit> && sbatch harness/stage.sbatch
# (Slurm runs a spooled copy of this file, so paths come from the submit directory, not $0.)
set -euo pipefail
OC=/gpfs/work4/0/prjs1226/qmeng1/over-comprehension
HERE=${SLURM_SUBMIT_DIR:?}/harness
python3 "$HERE/stage_weights.py" --reference "$HERE/weights_reference.json" --dst "$OC" \
  --venv-src /gpfs/scratch1/shared/qmeng1/npcbank-judge/venv --workers 8

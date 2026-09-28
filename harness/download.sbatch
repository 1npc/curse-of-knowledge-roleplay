#!/bin/bash
#SBATCH --job-name=oc-download
#SBATCH --account=ulsei11063
#SBATCH --partition=staging
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=05:00:00
#SBATCH --output=/scratch-shared/%u/over-comprehension/logs/download-%j.log
# Download the pinned public checkpoints in harness/downloads.json to scratch and verify them.
# Usage: cd $OC/code/<commit> && sbatch harness/download.sbatch [key ...]
set -eo pipefail
CODE=${SLURM_SUBMIT_DIR:?}
source "$CODE/harness/env.sh"
set -u
# env.sh pins the hub offline for generation jobs; downloads need it online, with caches on scratch
unset HF_HUB_OFFLINE TRANSFORMERS_OFFLINE
export HF_HUB_DISABLE_TELEMETRY=1
mkdir -p /scratch-shared/$USER/over-comprehension/weights
python "$CODE/harness/download_weights.py" "$CODE/harness/downloads.json" "$@"

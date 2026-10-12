#!/bin/bash
#SBATCH --job-name=oc-main-audit
#SBATCH --account=ulsei11063
#SBATCH --partition=staging
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:15:00
#SBATCH --output=/scratch-shared/%u/over-comprehension/logs/audit-%j.log
# Submit with --dependency=afterany:<last-generation-job> from the operations snapshot.
# This job never scores or prints response content. The original GPU job archives its
# output to project storage; this verifies that archive, even if generation failed.
set -euo pipefail
OC=/gpfs/work4/0/prjs1226/qmeng1/over-comprehension
CODE=${SLURM_SUBMIT_DIR:?}
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$OC/reports"
python3 "$CODE/tools/audit_generation.py" \
  --registry "$CODE/docs/main-run-registry.json" \
  --inputs "$OC/inputs/main-v1" --runs "$OC/runs" \
  --out "$OC/reports/main-generation-audit-$SLURM_JOB_ID.json"

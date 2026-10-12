#!/bin/bash
#SBATCH --job-name=oc-v2-seed-verify
#SBATCH --account=ulsei11063
#SBATCH --partition=staging
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:20:00
set -eo pipefail
export OC=${SLURM_SUBMIT_DIR:?}
source /usr/share/lmod/lmod/init/bash
module use /sw/arch/RHEL9/EB_production/2024/modulefiles/all
module load Python/3.12.3-GCCcore-13.3.0
export PYTHONDONTWRITEBYTECODE=1
exec /gpfs/work4/0/prjs1226/qmeng1/over-comprehension/venv/bin/python "$OC/code/harness/snellius_seed_verify_v2.py"

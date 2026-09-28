#!/bin/bash
#SBATCH --job-name=oc-gen
#SBATCH --account=ulsei11063
#SBATCH --partition=gpu_h100
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --cpus-per-task=16
#SBATCH --time=08:00:00
#SBATCH --output=/scratch-shared/%u/over-comprehension/logs/gen-%j.log
# Generate replies for several models, one after another, on one H100.
# Usage (from $OC/code/<commit>):
#   sbatch [--time=HH:MM:SS] harness/run.slurm <run_id> <prompts.jsonl> <location: auto|project|scratch> <model,model,...> [subset.txt]
# "auto" uses the verified project copy of a model when there is one and the pinned scratch download otherwise.
# Each model runs in its own Python process (a fresh vLLM engine). The finished run directory is
# copied from scratch to the project space at the end, so nothing depends on the 14-day scratch rule.
set -eo pipefail
RUN_ID=${1:?run id}; PROMPTS=${2:?prompts}; LOCATION=${3:?auto|project|scratch}; MODELS=${4:?models}; SUBSET=${5:-}
CODE=${SLURM_SUBMIT_DIR:?}
source "$CODE/harness/env.sh"
set -u
UUID=$(nvidia-smi --query-gpu=uuid --format=csv,noheader)
[ "$(echo "$UUID" | wc -l)" = 1 ] || { echo "expected exactly one GPU"; exit 1; }
export CUDA_VISIBLE_DEVICES=$UUID
RUN=$OCS/runs/$RUN_ID
mkdir -p "$RUN"
cp "$CODE/harness/models.json" "$CODE/harness/weights_reference.json" "$RUN/" 2>/dev/null || true
echo "{\"run_id\": \"$RUN_ID\", \"code\": \"$CODE\", \"prompts\": \"$PROMPTS\", \"location\": \"$LOCATION\", \"models\": \"$MODELS\", \"subset\": \"$SUBSET\", \"job\": \"$SLURM_JOB_ID\", \"gpu\": \"$UUID\", \"venv\": \"$VENV\"}" > "$RUN/job-$SLURM_JOB_ID.json"
status=0
for M in ${MODELS//,/ }; do
  echo "=== $M $(date -Is)"
  python "$CODE/harness/generate.py" --prompts "$PROMPTS" ${SUBSET:+--subset "$SUBSET"} --model "$M" \
    --models "$CODE/harness/models.json" --reference "$CODE/harness/weights_reference.json" \
    --location "$LOCATION" --out "$RUN" --run-id "$RUN_ID-$SLURM_JOB_ID" || { echo "model $M failed"; status=1; }
done
mkdir -p "$OC/runs"
rsync -a "$RUN/" "$OC/runs/$RUN_ID/"
echo "=== done $(date -Is) status=$status; copied to $OC/runs/$RUN_ID"
exit $status

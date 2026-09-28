#!/bin/bash
# Copy a finished run from the Snellius project space to runs/<run_id>/ here (responses only, small).
# Usage: tools/sync_run.sh <run_id>
set -euo pipefail
RUN=${1:?run id}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$ROOT/runs/$RUN"
rsync -a -e "ssh -i $HOME/.ssh/snellius_ed25519 -o BatchMode=yes" \
  --include='*/' --include='*.json' --include='*.jsonl' --exclude='*' \
  "qmeng1@snellius.surf.nl:/gpfs/work4/0/prjs1226/qmeng1/over-comprehension/runs/$RUN/" "$ROOT/runs/$RUN/"
du -sh "$ROOT/runs/$RUN"

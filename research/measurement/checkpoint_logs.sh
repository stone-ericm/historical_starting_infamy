#!/usr/bin/env bash
# Pre-quit checkpoint: copies every debug*.log the engine wrote since this boot started (it rotates debug.log every
# 512 KB) into the ACTIVE run receipt's checkpoint/ directory and prints their paths, oldest rotation first, so the
# receipt check can run on them while the game is still open. Usage, from the repo root:
#   research/measurement/checkpoint_logs.sh
# Environment overrides exist for the tests only: HSI_V3_DIR, HSI_RUN_DIR.
set -euo pipefail
R="$(cd "$(dirname "$0")/../.." && pwd)"
V3="${HSI_V3_DIR:-$HOME/Documents/Paradox Interactive/Victoria 3}"
RUN="${HSI_RUN_DIR:-$R/research/measurement/.run}"
A="$RUN/active"
if [ ! -f "$A/run-id" ]; then echo "no active run receipt at $A" >&2; exit 2; fi
mkdir -p "$A/checkpoint"
rm -f "$A/checkpoint"/debug*.log
n=0
for f in "$V3"/logs/debug*.log; do
  [ -f "$f" ] || continue
  if ! [ "$f" -ot "$A/run-id" ]; then cp "$f" "$A/checkpoint/"; n=$((n+1)); fi
done
echo "checkpoint: $(date '+%Y-%m-%d %H:%M:%S %Z'), $n log file(s)" >> "$A/receipt.txt"
ls "$A/checkpoint"/debug*.log | python3 -c "
import re, sys
def idx(p):
    m = re.search(r'debug\.(\d+)\.log$', p); return -int(m.group(1)) if m else 0
print('\n'.join(sorted((l.rstrip() for l in sys.stdin), key=idx)))"

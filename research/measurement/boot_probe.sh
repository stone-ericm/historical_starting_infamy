#!/usr/bin/env bash
# Task 10 probe boot. Order of operations (review R1 B8, R2 N5/N6): take the run lock, back the playset up into THIS
# run's receipt and verify the backup, install the restore trap, and only then touch anything the game reads: stage a
# clean copy of the probe, write the probe-only playset, launch Vic3 in debug mode, wait, restore from the receipt
# byte for byte. Each run gets a unique id; research/measurement/.run/last names its archived receipt.
# Environment overrides exist for the tests only: HSI_V3_DIR, HSI_V3_GAME, HSI_V3_BIN, HSI_RUN_DIR.
set -euo pipefail
R="$(cd "$(dirname "$0")/../.." && pwd)"
V3="${HSI_V3_DIR:-$HOME/Documents/Paradox Interactive/Victoria 3}"
G="${HSI_V3_GAME:-$HOME/Library/Application Support/Steam/steamapps/common/Victoria 3}"
BIN="${HSI_V3_BIN:-$G/binaries/victoria3.app/Contents/MacOS/victoria3}"
RUN="${HSI_RUN_DIR:-$R/research/measurement/.run}"
A="$RUN/active"
mkdir -p "$RUN"
if ! mkdir "$A" 2>/dev/null; then
  echo "refusing: $A exists, so an earlier boot has not been restored; run research/measurement/restore_playset.sh first" >&2
  exit 2
fi
RUN_ID="$(date '+%Y%m%d-%H%M%S')-$$"
echo "$RUN_ID" > "$A/run-id"
# 1. backup, verified before anything else changes
cp "$V3/content_load.json" "$A/content_load.original.json"
cmp -s "$V3/content_load.json" "$A/content_load.original.json"
python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$A/content_load.original.json"
shasum -a 256 "$A/content_load.original.json" | awk '{print $1}' > "$A/original.sha256"
echo "phase: backed-up" > "$A/phase"
# 2. restore trap, installed before any external mutation
restore() {
  "$R/research/measurement/restore_playset.sh"
}
trap restore EXIT
# 3. stage a clean copy of the probe (or, with HSI_MOD_PATH set, enable that mod directory as it is: the acceptance
#    boots enable this repository itself) and retain what was enabled
if [ -n "${HSI_MOD_PATH:-}" ]; then
  MOD="$HSI_MOD_PATH"
  SRC="$HSI_MOD_PATH"
else
  rm -rf "$V3/mod/hsi_probe"
  mkdir -p "$V3/mod"
  cp -R "$R/research/probe" "$V3/mod/hsi_probe"
  MOD="$V3/mod/hsi_probe"
  SRC="$R/research/probe"
  cp "$MOD/config.json" "$A/probe-config.json"
  cp "$R/research/measurement/capture-plan.json" "$A/capture-plan.json"
fi
printf '{"enabledMods":[{"path":"%s"}],"disabledDLC":[],"enabledUGC":[]}\n' "$MOD" > "$A/content_load.probe.json"
{
  echo "run_id: $RUN_ID"
  echo "started: $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "playset_dir: $V3"
  echo "mod_source: $SRC"
  echo "enabled_mod: $MOD"
  echo "staged_tree_sha256: $(cd "$MOD" && find . -type f -not -path './.git/*' -not -path '*/__pycache__/*' -not -path './research/measurement/*' | LC_ALL=C sort | xargs shasum -a 256 | shasum -a 256 | awk '{print $1}')"
  echo "binary: $BIN"
} > "$A/receipt.txt"
cp "$A/content_load.probe.json" "$V3/content_load.json"
echo "phase: staged" > "$A/phase"
echo "run $RUN_ID: playset backed up into $A; content_load.json enables only $MOD"
echo "launching with -debug_mode (SteamAPI_Init failure on stdout is expected); this window waits until the game exits, then restores the playset"
if [ -d "$G" ]; then cd "$G"; fi
set +e
"$BIN" -debug_mode
rc=$?
set -e
echo "game exited with status $rc"
echo "next: Claude collects the evidence (PROCEDURE.md step 7) from the receipt named in $RUN/last"
exit $rc

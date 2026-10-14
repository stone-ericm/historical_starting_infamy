#!/usr/bin/env bash
# Collects one boot's evidence into a FRESH attempt directory bound to that boot's run receipt (R3 P3): never a
# date-only directory, never mkdir -p, never overwriting an earlier attempt. Usage, from the repo root:
#   research/measurement/collect_evidence.sh [screenshot-dir]
# Reads research/measurement/.run/last (written by restore_playset.sh) and copies: every debug*.log, error*.log,
# system.log and game.log the engine wrote since the boot started (it rotates debug.log every 512 KB, so a session
# spans several files), the receipt's checkpoint log, staged playset, receipt, probe config and capture plan, the
# launcher's engine version line, and the screenshots (png/heic/jpg; heic also converted to png beside the original).
# Environment overrides exist for the tests only: HSI_V3_DIR, HSI_RUN_DIR, HSI_OUT_ROOT, HSI_LAUNCHER_SETTINGS.
set -euo pipefail
R="$(cd "$(dirname "$0")/../.." && pwd)"
V3="${HSI_V3_DIR:-$HOME/Documents/Paradox Interactive/Victoria 3}"
RUN_ROOT="${HSI_RUN_DIR:-$R/research/measurement/.run}"
OUT_ROOT="${HSI_OUT_ROOT:-$R/research/measurement}"
LS="${HSI_LAUNCHER_SETTINGS:-$HOME/Library/Application Support/Steam/steamapps/common/Victoria 3/launcher/launcher-settings.json}"
SHOTS="${1:-}"
if [ ! -f "$RUN_ROOT/last" ]; then echo "no archived run receipt: $RUN_ROOT/last is missing (did the boot restore?)" >&2; exit 2; fi
RUN="$(cat "$RUN_ROOT/last")"
if [ ! -f "$RUN/receipt.txt" ] || [ ! -f "$RUN/run-id" ]; then echo "receipt at $RUN is incomplete" >&2; exit 2; fi
ID="$(cat "$RUN/run-id")"
D="$OUT_ROOT/$(date +%Y-%m-%d)-run-$ID"
if ! mkdir "$D" 2>/dev/null; then
  echo "refusing: $D already exists; this run's evidence was collected before (an earlier attempt is never overwritten)" >&2
  exit 3
fi
n=0
for f in "$V3"/logs/debug*.log "$V3"/logs/error*.log "$V3"/logs/system.log "$V3"/logs/game.log; do
  [ -f "$f" ] || continue
  if ! [ "$f" -ot "$RUN/run-id" ] || [ "$(basename "$f")" = "system.log" ]; then cp "$f" "$D/"; n=$((n+1)); fi
done
echo >&2 "copied $n engine log file(s) written since the boot started"
[ -f "$D/debug.log" ] || echo "warning: no debug.log newer than the run; the game may not have started" >&2
if [ -d "$RUN/checkpoint" ]; then mkdir "$D/checkpoint" && cp "$RUN"/checkpoint/*.log "$D/checkpoint/"; else echo "warning: no pre-quit checkpoint logs in the receipt" >&2; fi
cp "$RUN/content_load.probe.json" "$D/playset.txt"
cp "$RUN/receipt.txt" "$D/run-receipt.txt"
[ -f "$RUN/probe-config.json" ] && cp "$RUN/probe-config.json" "$D/probe-config.json"
[ -f "$RUN/capture-plan.json" ] && cp "$RUN/capture-plan.json" "$D/capture-plan.json"
if [ -f "$LS" ]; then grep -E '"rawVersion"' "$LS" > "$D/engine.txt" || echo "warning: no rawVersion line in $LS" >&2; else echo "warning: launcher settings not found at $LS; write engine.txt by hand" >&2; fi
if [ -n "$SHOTS" ]; then
  s=0
  for f in "$SHOTS"/*.png "$SHOTS"/*.heic "$SHOTS"/*.HEIC "$SHOTS"/*.jpg "$SHOTS"/*.jpeg; do
    [ -e "$f" ] || continue
    if ! [ "$f" -ot "$RUN/run-id" ]; then
      cp "$f" "$D/"; s=$((s+1))
      case "$f" in *.heic|*.HEIC) sips -s format png "$f" --out "$D/$(basename "${f%.*}").png" >/dev/null 2>&1 || echo "warning: could not convert $f" >&2 ;; esac
    fi
  done
  echo >&2 "copied $s screenshot(s) taken since the boot started; rename them to fixture-<id>[-state<n>].png in capture order"
fi
if [ -d "$D/checkpoint" ] && [ -f "$D/debug.log" ]; then
  cp_n="$(cat "$D"/checkpoint/debug*.log | grep -c 'HSI;' || true)"; fin_n="$(cat "$D"/debug*.log | grep -c 'HSI;' || true)"
  echo >&2 "probe lines: $cp_n at the checkpoint, $fin_n in the final logs (the final set must contain at least the checkpoint's)"
fi
{ echo "run_id: $ID"; echo "receipt: $RUN"; echo "collected: $(date '+%Y-%m-%d %H:%M:%S %Z')"; echo "logs:"; ls "$D" | grep -E '\.log$' | sed 's/^/  /'; } > "$D/attempt.txt"
echo "$D"

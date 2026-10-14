#!/usr/bin/env bash
# Restores the playset from the ACTIVE run receipt written by boot_probe.sh: validates the backup (JSON + digest)
# BEFORE touching the destination, copies it even if the destination is missing, verifies, and archives the receipt
# as research/measurement/.run/<run id>/ (a fresh directory, never merged), recording that path in .run/last.
# boot_probe.sh calls this itself on exit; run it by hand only if that window was killed.
set -euo pipefail
R="$(cd "$(dirname "$0")/../.." && pwd)"
V3="${HSI_V3_DIR:-$HOME/Documents/Paradox Interactive/Victoria 3}"
RUN="${HSI_RUN_DIR:-$R/research/measurement/.run}"
A="$RUN/active"
if [ ! -d "$A" ]; then
  echo "nothing to restore: no active run receipt at $A" >&2
  exit 2
fi
if [ ! -f "$A/content_load.original.json" ] || [ ! -f "$A/original.sha256" ]; then
  echo "RESTORE FAILED: $A has no verified backup (the boot stopped before the backup was complete); inspect it by hand, the playset was not touched by that boot" >&2
  exit 1
fi
want="$(cat "$A/original.sha256")"
have="$(shasum -a 256 "$A/content_load.original.json" | awk '{print $1}')"
if [ "$have" != "$want" ] || ! python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$A/content_load.original.json" 2>/dev/null; then
  echo "RESTORE FAILED: the backup in $A is not the file that was recorded (digest $have != $want, or not JSON); the destination was left untouched and the receipt stays active" >&2
  exit 1
fi
# the old destination's digest is receipt annotation only (R3 P2): an unreadable file must not block recovery
before="(missing)"
if [ -e "$V3/content_load.json" ]; then
  before="$(shasum -a 256 "$V3/content_load.json" 2>/dev/null | awk '{print $1}' || true)"
  [ -n "$before" ] || before="(unreadable)"
fi
mkdir -p "$V3"
cp "$A/content_load.original.json" "$V3/content_load.json.restoring"
mv "$V3/content_load.json.restoring" "$V3/content_load.json"
after="$(shasum -a 256 "$V3/content_load.json" | awk '{print $1}')"
if [ "$after" != "$want" ]; then
  echo "RESTORE FAILED: $V3/content_load.json digest $after != original $want after copying; the receipt stays active" >&2
  exit 1
fi
echo "restored: $(date '+%Y-%m-%d %H:%M:%S %Z') (content_load.json $before -> $after, verified)" >> "$A/receipt.txt" 2>/dev/null || true
id="$(cat "$A/run-id" 2>/dev/null || date '+%Y%m%d-%H%M%S')-$$"
dest="$RUN/$id"
n=0
while ! mkdir "$dest" 2>/dev/null; do n=$((n+1)); dest="$RUN/$id-$n"; done
mv "$A"/* "$dest"/ && rmdir "$A"
echo "$dest" > "$RUN/last"
echo "playset restored from the run receipt and verified; receipt archived at $dest (also named in $RUN/last)"
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(len(d['enabledMods']), 'mods enabled')" "$V3/content_load.json"

#!/usr/bin/env bash
# Builds the clean upload folder for the Paradox launcher's "Upload mod": only what the game loads (.metadata, common,
# README) plus a thumbnail, into ~/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy_release/.
# The repository itself is never uploaded (it carries research logs and screenshots with local paths, tools and .git).
# Usage, from the repo root: tools/build_release.sh    (override the destination with HSI_RELEASE_DIR)
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"
V3="${HSI_V3_DIR:-$HOME/Documents/Paradox Interactive/Victoria 3}"
OUT="${HSI_RELEASE_DIR:-$V3/mod/historical_starting_infamy_release}"
SHOT="$R/research/acceptance/2026-10-14-run-20261014-153134-83398/acceptance-egypt-notorious.jpg"
if [ -d "$OUT" ]; then
  if [ -f "$OUT/.metadata/metadata.json" ]; then
    # keep a Workshop id the launcher may have written back on a previous upload
    PREV_ID="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('id',''))" "$OUT/.metadata/metadata.json")"
  fi
  rm -rf "$OUT"
fi
mkdir -p "$OUT/.metadata" "$OUT/common"
cp -R "$R/common/." "$OUT/common/"
cp "$R/README.md" "$OUT/README.md"
cp "$R/.metadata/metadata.json" "$OUT/.metadata/metadata.json"
if [ -n "${PREV_ID:-}" ]; then
  python3 - "$OUT/.metadata/metadata.json" "$PREV_ID" <<'PY'
import json, sys
p, pid = sys.argv[1], sys.argv[2]
d = json.load(open(p)); d["id"] = pid
json.dump(d, open(p, "w"), indent=2); open(p, "a").write("\n")
PY
  echo "kept Workshop id $PREV_ID from the previous release folder"
fi
# thumbnail: the Egypt "Notorious" panel from the acceptance screenshot, square, 512 px
if [ -f "$SHOT" ]; then
  sips -s format png -c 1040 1040 --cropOffset 20 20 "$SHOT" --out "$OUT/.metadata/thumbnail.png" >/dev/null 2>&1 \
    || sips -s format png -c 1040 1040 "$SHOT" --out "$OUT/.metadata/thumbnail.png" >/dev/null
  sips -z 512 512 "$OUT/.metadata/thumbnail.png" >/dev/null
fi
# the same static checks the repo gets: BOM and braces on every script file, known rule flags
python3 - "$R" "$OUT" <<'PY'
import sys
sys.path.insert(0, sys.argv[1] + "/tools")
from pathlib import Path
from hsi.validate import check_bom, check_braces, check_rule_flags
from hsi.bom import has_bom
out = Path(sys.argv[2])
files = sorted(out.rglob("*.txt"))
problems = check_bom(files)
for f in files:
    problems += check_braces(f.read_text(encoding="utf-8-sig"), str(f.relative_to(out)))
game = Path.home() / "Library/Application Support/Steam/steamapps/common/Victoria 3/game"
if (game / "common/game_rules/00_game_rules.txt").exists():
    for f in files:
        problems += check_rule_flags(f.read_text(encoding="utf-8-sig"), game)
assert not problems, problems
print("release checks: OK,", len(files), "script files")
PY
# the launcher registers local mods from a mod/<folder>.mod descriptor and only then applies .metadata/metadata.json
# (observed 2026-10-14: without it the library showed the folder name with a warning and "Upload mod" listed nothing)
cat > "$(dirname "$OUT")/$(basename "$OUT").mod" <<MOD
version="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['version'])" "$OUT/.metadata/metadata.json")"
tags={
	"Historical"
	"Balance"
}
name="Historical Starting Infamy"
supported_version="1.14.*"
path="mod/$(basename "$OUT")"
MOD
echo "descriptor: $(dirname "$OUT")/$(basename "$OUT").mod"
echo "release folder: $OUT"
( cd "$OUT" && find . -type f | LC_ALL=C sort | while read -r f; do printf '%8s  %s\n' "$(stat -f %z "$f")" "$f"; done )
du -sh "$OUT"

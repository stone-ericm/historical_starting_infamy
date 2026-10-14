# research/measurement/PROCEDURE.md — probe boot (Eric), about twenty minutes

> Superseded in part on 2026-10-14 by the spec v4 addendum: the generator uses the after-lobby day-one sample, the
> monthly samples feed the formula check only (a short last month is permitted: a slice ceased to exist in March), no
> fixtures file, manifest or ordering registry is built. Steps 3 (captures) and 5 (receipt check) describe the probe
> boots that were run; a future boot needs only steps 1, 2, 4, 6, 7.

`GAME="$HOME/Library/Application Support/Steam/steamapps/common/Victoria 3/game"`. Prerequisites (Claude, before the
boot, all from the repo root):

```bash
REPO="$HOME/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy"; cd "$REPO"
python3 research/scripts/capture_audit.py "$GAME" --write-config research/probe/config.json   # AUDIT OK
(cd tools && python3 -m hsi.probe_gen --research ../research --out ../research/probe \
  && python3 -m hsi.validate --repo .. --game-dir "$GAME" --probe-only)                        # validate: OK
git status --short research/probe    # empty: the staged probe is the committed probe
```
Every block below starts from `$REPO`; the module commands run in subshells so the shell stays there.

1. **Boot** (Eric), from the repo root: `bash research/measurement/boot_probe.sh`. It takes the run lock, copies your
   current `content_load.json` into the run receipt (`research/measurement/.run/active/`, gitignored) and verifies the
   copy, installs the restore trap, then stages a clean copy of the probe at
   `~/Documents/Paradox Interactive/Victoria 3/mod/hsi_probe`, keeps the staged config and the capture plan in the
   receipt, enables only that mod, launches the game with `-debug_mode` (Steam is bypassed; `SteamAPI_Init() failed`
   on stdout is expected), and **waits**. When the game exits, the same window restores your playset from that receipt,
   verifies it byte for byte, and archives the receipt under a unique run id named in `research/measurement/.run/last`.
   If the script refuses with "an earlier boot has not been restored", run `bash research/measurement/restore_playset.sh`.
2. **New Game.** Pick **France**. On the New Game page set **Infamy Generation = Very Low**. Start.
3. **Captures**, before unpausing: follow `research/measurement/capture-plan.md` (A, B, Cmin, Cmax, optional D, in
   that order; a candidate counts only when its breakdown shows the required line; every constituent state's tooltip;
   context shots; cancel each draft). **Inventory check before observing:** A, B, Cmin and Cmax must each have a
   complete capture. If any one is missing, stay paused and tell Claude; do not observe. Only D may be skipped.
4. **Observe.** Console (`~`): `observe`. Speed 5. Let the game run until **after April 1, 1836** (three monthly
   pulses), then pause.
5. **Checkpoint before quitting** (Claude, on the live logs; the engine rotates `debug.log` every 512 KB, so one
   session spans `debug.2.log`, `debug.1.log`, `debug.log` and the checkpoint copies every one written since the boot):
   ```bash
   A=research/measurement/.run/active
   research/measurement/checkpoint_logs.sh                       # copies this session's debug*.log into $A/checkpoint/
   (cd tools && python3 -m hsi.measurement check --debug-log "../$A"/checkpoint/debug*.log --research ../research --probe-config "../$A/probe-config.json")
   ```
   `receipt: COMPLETE` means both start hooks (with the Very Low rule read in the after-lobby hook), all three monthly
   samples, every slice, country and diagnostic record, every field, and nothing outside the configured window.
   `INCOMPLETE` lists what is missing: if a sample has not been flushed yet, wait a minute and rerun; if a record kind
   is missing entirely, the probe needs a fix (plan Task 10 step 7) and the boot is repeated from step 1 after the
   fix, keeping this attempt's receipt and logs under `research/measurement/<date>-attempt1/`.
6. **Quit to desktop.** The boot window restores the playset and prints `playset restored … verified; receipt archived
   at …`. Tell Claude.
7. **Collect** (Claude), before any other launch of the game, from `$REPO`:
   ```bash
   D="$(research/measurement/collect_evidence.sh ~/Desktop)"   # fresh <date>-run-<id> directory bound to .run/last; refuses to overwrite
   echo "$D"; ls "$D"
   (cd tools && python3 -m hsi.measurement check --debug-log "../$D"/debug*.log --research ../research --probe-config "../$D/probe-config.json" \
     && python3 -m hsi.measurement extract --debug-log "../$D"/debug*.log --out "../$D/probe-extract.log")
   ```
   The script copies every engine log written since the boot (rotated `debug.N.log` and `error.N.log` included),
   the checkpoint copies, the staged playset, the receipt, the staged probe config and capture plan, the engine
   version line and the screenshots (HEIC originals plus PNG copies), and compares the probe-line counts of the
   checkpoint and final logs. Rename the screenshots to `fixture-A.png`, `fixture-A-state1.png`, … in capture order.
   A later tooltip-only boot (for D) is collected into its own directory the same way.
   `receipt: INCOMPLETE` listing only a last-month slice that ceased to exist is acceptable under v4. Commit the
   directory and point the generator at it by its explicit path (`--measurement research/measurement/<date>-run-<id>`),
   never at "the latest directory"; the generated header hashes the logs it read.

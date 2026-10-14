# Historical Starting Infamy — working notes

Standalone Victoria 3 **1.14.5** vanilla mod (not part of EoR). The repository lives in `~/projects/historical_starting_infamy` (moved out of the
launcher's mod folder on 2026-10-14: the Paradox launcher scans every folder under `mod/` and its SQLite pool times out on a git repository there,
which empties its Upload dialog); what the game loads is the release folder `tools/build_release.sh` builds into
`~/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy_release/` (with the `.mod` descriptor the launcher needs). Read `ARCHITECTURE.md`, then the spec
`docs/superpowers/specs/2026-10-13-historical-starting-infamy-design.md` (v3.1, approved 2026-10-13) **and its v4 addendum
`docs/superpowers/specs/2026-10-14-v4-simplification-addendum.md`** (Eric's 2026-10-14 ruling: day-one inputs, observed stage order with the rank block, whole numbers; no sampling policy, no fixture gate), and the plan
`docs/superpowers/plans/2026-10-13-historical-starting-infamy.md` (Tasks 10–13 superseded by the addendum). The execution ledger with every ruling is
`.superpowers/sdd/2026-10-13-historical-starting-infamy/progress.md` (local, not committed). v0.1.0 was merged to `main` on 2026-10-14 (branch `build/v1` deleted); new work starts a new branch from `main`.
**Public since 2026-10-14:** https://github.com/stone-ericm/historical_starting_infamy (history squashed to one commit at publication; the
pre-squash history is the local branch `history/pre-squash-2026-10-14`, never pushed). Commits on this repository are in Eric's voice with no
AI attribution trailers (his rule for public GitHub posts). The Steam Workshop item is 3819895927.

## Commands

`GAME="$HOME/Library/Application Support/Steam/steamapps/common/Victoria 3/game"`

- Tests (stdlib-only code, no system pytest): `cd tools && uvx pytest -q`, or from the root `uvx pytest -q tools/tests`.
- Ledger: edit the judgment tables in `research/scripts/author_ledger.py`, then
  `python3 research/scripts/author_ledger.py "$GAME"` and `cd tools && python3 -m hsi.ledger ../research --game-dir "$GAME"`.
  Never hand-edit the three CSVs. Vanilla facts for a mapping: `python3 research/scripts/vanilla_lookup.py "$GAME" owners:TAG find:KEY HOLDER:STATE_A,STATE_B`.
- Capture plan: edit `research/measurement/capture-plan.json`, then `python3 research/scripts/capture_audit.py "$GAME" --write-config research/probe/config.json` (static eligibility + estimates; writes the fixture slices the probe logs). Regenerate the probe after it.
- Probe: `cd tools && python3 -m hsi.probe_gen --research ../research --out ../research/probe && python3 -m hsi.validate --repo .. --game-dir "$GAME" --probe-only`.
  Live receipt check before Eric quits: `research/measurement/checkpoint_logs.sh` (copies this session's rotated debug*.log into `.run/active/checkpoint/`), then `cd tools && python3 -m hsi.measurement check --debug-log ../research/measurement/.run/active/checkpoint/debug*.log --research ../research --probe-config ../research/measurement/.run/active/probe-config.json`.
  Boot (Eric): `research/measurement/boot_probe.sh` (restores the playset itself on exit; `restore_playset.sh` only if that window was killed); capture plan in `research/measurement/capture-plan.md`.
- Collect after a boot: `research/measurement/collect_evidence.sh ~/Desktop` (fresh `<date>-run-<id>` dir bound to `.run/last`; prints only the path), then `cd tools && python3 -m hsi.measurement check --debug-log <dir>/debug*.log …` and `extract --debug-log <dir>/debug*.log --out <dir>/probe-extract.log`; manifest via `hsi.measurement.write_manifest`. Attempt 1 (2026-10-14, failed probe, valid tooltips) is `research/measurement/2026-10-14-run-20261014-142803-66370/` with `attempt-notes.md`.
- Generate: `cd tools && python3 -m hsi.generate --repo .. --game-dir "$GAME" --measurement ../research/measurement/2026-10-14-run-20261014-150956-73604`,
  then `python3 -m hsi.validate --repo .. --game-dir "$GAME" --measurement ../research/measurement/2026-10-14-run-20261014-150956-73604` (boot 2 is THE measurement; the directory is named explicitly, never "the latest").
- Acceptance (Eric boots per `research/acceptance/ACCEPTANCE.md`): `cd tools && python3 -m hsi.savecheck --save <plaintext .v3> --tables ../research/tables.json --rule standard --tolerance 0.005`.

## Hard rules

- UTF-8 BOM on every script `.txt`: write through `hsi.bom.write_text_bom`; `validate.py` enforces it.
- Never edit `tools/hsi/constants.py` to make a test or an oracle pass. A mismatch is a ledger judgment, a transcription or a formula-reading error, fixed at its source (adding a vanilla number the formula lacked, with its file:line, is a source fix: the rank table on 2026-10-14).
- The Standard infamy rule has no flag; it is the `else` branch. Delivery hook is `on_game_started_after_lobby`, additive registration only.
- Every game boot backs up and restores Eric's `~/Documents/Paradox Interactive/Victoria 3/content_load.json`; use the scripts, never hand-edit it.
- `research/measurement/<date>-run-<id>/` is a collected boot; the generated header hashes the logs it read. Acceptance evidence goes to `research/acceptance/<date>/`. Saves are gitignored (hashes committed).
- Bolivia is computed, never emitted. No Workshop or Paradox Mods publication without Eric's explicit approval.

## Gotchas

- zsh does not word-split a variable that holds a command with arguments (`X="python3 a.py"; $X arg` fails). Use a shell function.
- Claude Code's safety check refuses commands containing a `bash -c '...'` wrapper; pass test commands to `task-done` directly.
- Vanilla cultures carry one `language = language_x` field, not a traits block; `STATE_` keys are regions with several owner slices; there is no weekly code on_action, only monthly.
- Engine facts measured 2026-10-14 (attempt 1 notes): inside `debug_log` only `[GetGlobalVariable('x').GetValue|n]` prints values (`SCOPE.s*()` resolves to nothing; `$PARAM$` in a string is mangled); `debug.log` rotates every 512 KB; each country's monthly pulse fires on its own day (GBR the 30th); the UI truncates to one decimal; country ranks scale infamy on both sides (`common/country_ranks/00_country_ranks.txt`), a stage the spec's formula lacked.

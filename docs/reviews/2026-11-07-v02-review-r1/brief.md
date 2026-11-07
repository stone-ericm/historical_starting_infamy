# Codex review v02-r1 — Historical Starting Infamy v0.2.0 (Victoria 3 1.15 update)

**Do not read any memory files** (`~/.codex/memories/`, `~/projects/claude-shared/memory/`, any `MEMORY.md`). Do not commit, push, build the release, install, launch the game, or edit anything outside `/Users/eric/projects/historical_starting_infamy/.codex-review/v02-r1/`. Everything else is read-only. You may run the repo's tests and tools (`cd tools && uvx pytest -q`; `python3 -m hsi.generate` / `hsi.validate` ONLY with `--repo` pointing at a private copy you make under `.codex-review/v02-r1/`, never at the real repo, because generate rewrites checked-in files).

## What this is
Repo `/Users/eric/projects/historical_starting_infamy` (git). A small published Victoria 3 mod (Steam Workshop 3819895927, public GitHub) that gives 1836 countries the infamy their 1816–1835 acts would have generated under the game's own infamy formula, decayed to 1836. Read `README.md`, `ARCHITECTURE.md`, `CLAUDE.md` first; the spec and its v4 addendum are in `docs/superpowers/specs/`; earlier review rounds are archived in `docs/reviews/`.

v0.1.0 (on `main`, published) was priced for game 1.14.5. The branch `v0.2-game-1.15` (`git log main..HEAD`, 5 commits) reprices it for 1.15.0, the installed game. It is NOT published yet: the owner will boot once to check it in-game, then upload. Review the diffs and the current files; treat commit messages and docs as claims to verify, not facts.

Vanilla trees (read-only):
- 1.15.0 (installed): `/Users/eric/Library/Application Support/Steam/steamapps/common/Victoria 3/game`
- 1.14.5: `/Volumes/EORScratch/eor-tools/vanilla-1.14.5-build25629520/game`

The measurement boot the generator reads (engine-logged values, 1.14.5): `research/measurement/2026-10-14-run-20261014-150956-73604/`.

## Assume there are errors. In priority order
1. **Did the update find every 1.15 change that affects this mod's numbers?** Independently diff, between the two trees, every vanilla file and value the generator depends on (the effect header `common/scripted_effects/zz_hsi_effects.txt` lists hashed inputs; `tools/hsi/constants.py` lists constants; also war-goal types, country ranks, game rules, defines, script values, on_actions, anything the formula replica or the ledger relies on). For each 1.15 change: does it affect any act in the ledger (`research/acts.csv`, `goals.csv`, `goal_states.csv`), and is it handled? Name anything missed.
2. **Is the new formula correct?** Compare `tools/hsi/formula.py` (`state_base` and everything it feeds) line by line against 1.15's `common/script_values/00_infamy_values.txt` and the defines it reads. Check ordering of floor / soft cap / hard cap, where the per-state minimum applies, claims (`infamy_assumes_claim`, `infamy_ignores_claim`), and anything else that differs from 1.14.5. Trace at least two real ledger components and one whole country balance by hand from `research/derivation.csv` inputs.
3. **The reused 1.14.5 measurement.** The tables use population/GDP shares, modifiers and country ranks the engine logged on 1.14.5's 1836 day one. How wrong could that be on 1.15? Check 1.15's 1836 history (states, pops, buildings, country definitions/ranks, laws/modifiers that feed the infamy formula) for the states and actors that drive the emitted numbers (Egypt, Punjab, and anyone near the emission threshold), and for world totals. Is the README's description of this approximation accurate? Would any emitted number plausibly change by >= 1 on a 1.15 measurement?
4. **Oracle A and the version split** (`K.GAME_VERSION`, `K.MEASUREMENT_GAME`, `generate.diagnostic_check`): sound? Can the generator now produce 1.15 tables while silently using 1.14.5 arithmetic anywhere (or vice versa)? Any call site still using a default it should not?
5. **Tests**: are the changed/added tests right (hand derivations in `tests/test_generate.py`, the 1.14.5-pinned tooltip tests, `test_capture_audit.py` re-pointed at the 1.14.5 tree)? Any test that would still pass if the 1.15 formula were wrong? Give a concrete mutant and run it on a private copy.
6. **Shipped files and release**: generated effect (header hashes, BOM, values per rule, guard), `.metadata/metadata.json`, `tools/build_release.sh` (now reads `supported_game_version`), and the in-game acceptance procedure `research/acceptance/ACCEPTANCE.md` (expected numbers).
7. **Public text**: `README.md`, `docs/release/steam-workshop-description.md` and `.bbcode.txt` — wrong or overstated claims, stale 1.14.5 statements, numbers that disagree with `research/tables.json`.

Rules: cite `file:line` (and vanilla `file:line` for game facts). Label anything not verified against files as "reasoning only". For each finding: severity (BLOCKER = must fix before publishing / MAJOR / MINOR / NIT), concrete failure scenario, cheap fix or check. Briefly list what you checked and found correct.

## Deliverable
Write `/Users/eric/projects/historical_starting_infamy/.codex-review/v02-r1/report.md`, starting with a "Disclosure" section (whether any memory summary or prior-session context was injected). When complete, print on its own line `HSIV02R1-` followed by the first 8 hex of `shasum -a 256` of that file (format `HSIV02R1-xxxxxxxx`), then `DONE`.

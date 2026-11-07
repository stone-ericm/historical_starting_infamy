# Triage: Codex review of v0.2.0 (2026-11-07)

Verdict: no BLOCKER, no MAJOR. Tables reproduce byte for byte; the 1.15 formula matches 00_infamy_values.txt; no 1.15 change affecting the ledger was missed.

| Finding | Action |
|---|---|
| R1 MINOR: Workshop texts did not say the inputs are the 1.14.5 boot's; "mostly Russian" overreached | Fixed in 67b80fe: README and both Workshop texts state the reuse, that 1.15's economic changes were not measured, and the measured rounding sensitivity. |
| R2 MINOR: capture_audit.py used the 1.15 formula on the 1.14.5 plan | Fixed in 67b80fe: `Vanilla(..., formula_game)`, `--formula-game`; the test uses `K.MEASUREMENT_GAME` and pins Wales D = OK. |
| R3 MINOR: factor tests only ran under 1.14.5; a 1.15-only break passed 139 tests | Fixed in 67b80fe: factor/precedence tests parametrized over both games; the reviewer's mutant now fails. |
| Note: `build_release.sh` thumbnail is the 1.14.5 "Notorious" screenshot | Open: replace with the 1.15 acceptance screenshot before uploading (Egypt at 12 is no longer Notorious). |
| Sensitivity: a fresh 1.15 measurement could move a rounded value | Accepted as a declared approximation (owner chose option A, 2026-11-06); a probe boot is the check if wanted. |

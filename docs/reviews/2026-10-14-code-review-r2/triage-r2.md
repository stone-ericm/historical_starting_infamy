# Triage of Codex code review R2 (HSI-C2), 2026-10-14

| id | class | disposition | evidence / action |
|---|---|---|---|
| N1 | real | FIXED | DIAG line carries `unrec_mult` of `hsi_root` (same block as `siv`); `diagnostic_check` reads it from the record; schema requires it; test perturbs the sampler's COUNTRY value (passes) and the record's own (fails). |
| N2 | real | FIXED | Russia removed; Prussia (13 slices) is the Cmax fallback and is logged in full; `test_fixture_slices_cover_every_candidate` resolves protectorate/regime candidates' slices through `owned_slices`, not through `fixture_slices()`. |
| N3 | real | FIXED | Audit reads `00_truces.txt` and `add_claim`; prints `UNVERIFIED at runtime` per candidate (interest tier; regime opinion/IG; liberation movement + activism; protectorate rank); capture-plan.md corrected (play-level interest default; code-side regime gate explains the three Cmin candidates). Tests inject a truce and a claim. |
| N4 | real | FIXED | `SCHEMA`/`CODES` per kind, `RULE` flag validity, start_b vs `config["rule"]`, unexpected groups refused, DIAG one date per root within 31 days of the sampler, sampler dates increasing, `build_snapshot` errors named; `choose_snapshot(months=)`; every row of the R2 table has a test. |
| N5 | real | FIXED | `mkdir` lock; backup `cmp` + JSON + digest before the trap; trap before staging; restore validates the backup before any copy, tolerates a missing destination, atomic rename; tests: staging failure restores, missing destination restored, invalid backup leaves the destination untouched, incomplete backup refused. |
| N6 | real | FIXED | Run id `date-pid`; archive `mkdir` with suffix on collision, never merged; `.run/last`; receipt holds `probe-config.json`, `capture-plan.json`, staged tree hash; PROCEDURE copies `debug.checkpoint.log` into the receipt before quitting and collects through `.run/last`. Test: two runs → two receipts, `last` = newest. |
| N7 | real | FIXED | capture-plan.md: boundary rule (a candidate counts only with the required line; try the next otherwise), every constituent state's tooltip, context shots, stop-before-observe if no clamp. The audit's "if Lucca does not clamp none will" claim removed. |
| N8 | real | FIXED | PROCEDURE blocks start at `$REPO`, module commands in subshells; step references corrected. |
| N9 | real | FIXED (disclosed) | `unrec_mult_estimate = -0.1` applied to unrecognized targets; proxies (gdp = pop, tier 3, adjacency as declared) stated in the audit header, docstring and plan notes. Interest tier stays an assumption by design. |

Deferred items (B5–B7, L2, L3, L5, L6) stand as in triage-r1, now with Codex's stated evidence requirements, all of which the capture plan and the receipt retain.

# Triage of Codex code review R1 (HSI-C1), 2026-10-14

Each finding classed against the code and the vanilla 1.14.5 files, with the evidence I checked myself. "Real" means
the defect reproduces as described; "deferred" means real but not boot-wasting, scheduled after the boot and before
transcription or generation; "disagree" gives the reason.

| id | class | disposition | evidence / action |
|---|---|---|---|
| B1 | real | FIXED | `00_relations.txt` c:SAR block sets FRA 30; `00_scripted_triggers.txt:1758–1766` requires relations strictly below `relations_threshold:cordial` (20, `00_defines.txt:990`); `dp_conquer_state` carries the blocker, `dp_make_protectorate` and `dp_regime_change` do not. New B: Mascara's Algiers slice (relations −50, adjacent), fallback Flanders (−1). `research/scripts/capture_audit.py` + `tools/tests/test_capture_audit.py` reject the old plan. |
| B2 | real | FIXED | `SIC = { states = { STATE_SICILY } }` is Two Sicilies' own tag; FRA–AUS 20 blocks Lombardy. Spec §6 wants conquer_state for D, which France cannot bring into the 1–2 range (per-state floor 1, no claims); D is now liberate_country, optional, with the ruling recorded in progress.md and capture-plan.md. Also found while re-estimating: Tuscany would not show the regime-change minimum (capital standing ×2.0); Cmin now Lucca/Parma/Modena. |
| B3 | real | FIXED | `probe_gen.render` took slices only from the ledger; `fixture_slices` in `research/probe/config.json` (written by the audit) are logged in every sample; fixture holder and BOL join the guard on their own; the fixture holder evaluates DIAG over fixture slices. Tests added. |
| B4 | real | FIXED (pre-boot part) | `expected_receipt`/`check_receipt` refuse missing hooks, samples, slices, countries, DIAG pairs, mixed sampler dates; `hsi.measurement check` runs on the live log before quitting (PROCEDURE step 5). DIAG records now carry their own operands, so oracle A does not depend on pulse alignment; `generate.main` runs oracle A on every monthly sample. The 2 % policy stays a refusal. |
| B5 | real | DEFERRED | One-decimal state entries (`diplomacy_l_english.yml:2430`) lose precision. Mitigation at capture time: the state-level tooltip is screenshotted too (capture-plan step 3), and the probe keeps tick-0 `base` at four decimals for every candidate slice. The loader will fit on rounding intervals and report ambiguity; nothing about the capture changes. |
| B6 | real | DEFERRED | Loader discards holder/target/date/tick and has no typed multiplier/clamp quantities. Fixture schema is decided before transcription, after the boot; screenshots preserve every line. |
| B7 | real | DEFERRED | Equivalence domain omits fixture operands; fix together with B5/B6 in `ordering.py`. |
| B8 | real | FIXED | `restore_playset.sh` chose `ls -t … | head -1`; `boot_probe.sh` merged into an existing directory with `cp -Rf`. Now: run receipt with the original and its digest, clean staging, restore on exit via trap, byte-verified, manual fallback, nested boot refused. `tools/tests/test_boot_scripts.py` (fake home, stub binary). |
| B9 | real | FIXED | Collection order in PROCEDURE.md: the staged playset JSON comes from the archived receipt; logs, screenshots and `probe-config.json` are collected before any relaunch; live checkpoint before quitting. |
| B10 | real | FIXED | PROCEDURE.md prerequisites now use the `cd tools && python3 -m hsi.…` forms with the real flags. |
| F1 | real | FIXED | `generate.emitted_value` thresholds the finished balance, rounds only an eligible entry; boundary test at 0.0449/0.046/0.0499/0.05/0.0501. |
| L1 | real | FIXED | `validate_ledger` refuses `general_mult_source = none` on a goal with a holder tag; the real ledger still validates. |
| L2 | real | DEFERRED | Manifest verification is generic; the required evidence set (debug/system/error logs, probe-extract, oracle-tooltips, screenshots, engine, playset, run receipt, probe-config) will be enforced by the generator before the first generation. |
| L3 | real | DEFERRED | derivation.csv lacks component and stage intermediates; generator output change, before first generation. |
| L4 | real | FIXED | Validator requires roots, the rules file, probe flag names, shipped files and the `--measurement/--fixtures` bindings in full mode. |
| L5 | real | DEFERRED | NaN passes `savecheck`; fix before the acceptance boots (Task 15). |
| L6 | real, partly over-built | DEFERRED | Missing BOL / roster / duplicate guard are real gaps against spec §9 and will be added before Task 15 with the retained real save. A full quote-aware parser of the whole save is more than the spec asks; the roster check (every 1836 country present, zero except BOL) covers the stated property. |
| L7 | real | FIXED | `vanilla_lookup.py` reads the `language` field; spot-checked FRA (francophone) and SPA vs Mexico (hispanophone). |
| T1–T13 | proposals | PARTLY ADOPTED | T6, T7, T9 (threshold), T11, T13 landed with the fixes above; T1–T5, T8, T10, T12 are queued with the deferred items they test. |

Disagreement recorded: Codex lists B5–B7 among the changes required before the boot. The boot's deliverable is the set of
screenshots and the probe's records; the fixture schema and the fitting rule consume them afterwards and change nothing
about what is captured. Holding the boot for them would cost Eric's time without protecting it.

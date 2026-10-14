# Triage of Codex code review R3 (HSI-C3), 2026-10-14

Final pre-boot round under the project's cap (three rounds). Codex confirmed N1, N2, N8, N9 fixed and every round-2
receipt counterexample closed, then named five bounded items. All five were applied after the round (commit
"Review R3 applied"), so no round 4 was run; Codex's own section 3 says the changes are reviewable without one.

| id | class | disposition | evidence / action |
|---|---|---|---|
| P1 | real | FIXED | "neither" stop condition replaced by a four-capture inventory check before observing in capture-plan.md step 7 and PROCEDURE.md step 3; table header corrected. Documentation only; the rehearsal is Eric's at the keyboard. |
| P2 | real | FIXED | `restore_playset.sh` hashes the old destination best-effort (`(unreadable)` annotation); backup JSON/digest and post-restore digest remain mandatory. Test `test_restore_survives_an_unreadable_destination` (skips if the runner can read mode 000). |
| P3 | real | FIXED | `collect_evidence.sh`: `<date>-run-<id>` from `.run/last`, `mkdir` without `-p`, exit 3 on an existing directory, checkpoint-prefix comparison. Test: two same-day runs → two directories; repeat → refused with unchanged digests. PROCEDURE and CLAUDE.md point at it; Task 13 must name the measurement directory explicitly. |
| P4 | real | FIXED | Exact identity sets per sample (unexpected STATE/COUNTRY/DIAG refused), misplaced kinds refused, strictly increasing sampler dates, calendar errors as MeasurementError. Tests for each. |
| P5 | real | FIXED | capture-plan.md: Alsace and the Prussian Rhine states are Western Europe; France owns nothing in Central Europe; tier stays a runtime condition. |

Codex's disclosure notes a conversation-compaction summary inside its own session (rounds 1–3 share one pane); it is
the session's own history, not a memory file, and the round's evidence was re-derived from the diff.

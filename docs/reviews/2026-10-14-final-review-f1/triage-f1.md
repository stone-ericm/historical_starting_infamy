# Triage of the final whole-branch review HSI-F1 (fresh Codex session), 2026-10-14

| id | class | disposition | evidence / action |
|---|---|---|---|
| F1 | real (claims > evidence) | PARTLY FIXED; owner choice | README, metadata, acceptance notes and ACCEPTANCE.md now state what was measured (Standard smoke: Egypt Notorious band, Punjab 11.0, no new errors) and what was not (exact 54, roster at 0, Bolivia 50, guard once, reload, late-enable, Very Low). The save-based checks remain owed unless Eric waives them; put to him. |
| F2 | real | FIXED | savecheck: whole-file lexical balance (quotes opaque), quote-aware block reader, duplicate definitions refused, finite values, finite tolerance < 0.5, Bolivia required, guard counted exactly once; the five mutations and the NaN/large tolerance cases are tests. |
| F3 | real | FIXED | derivation.csv has component rows (slices, uncapped/capped shares, base, standing, factors, pre-floor, value), component subtotal and subject multiplier on the charge rows; `component_breakdown` is the single source. Test reconciles components → subtotal → raw. |
| F4 | real (internal conflict) | DECLARED; owner choice | The Assam component and not_representable.md now both say the 1836 BIC slice includes Cachar (1832) and the 1824 demand is priced whole as an approximation. Refusing the component is the stricter v3.1 reading; either way BIC decays to zero. Put to Eric. |
| F5 | real | FIXED (provenance); owner choice (Ladakh) | Surviving targets carry their tags (BEL, CAM, LAD); the derivation labels ranks measured / fallback-absent / fallback-unmeasured; victim-only records are optional in the receipt and reported when missing. Belgium and Cambodia measured equal to the earlier fallbacks (tables unchanged). Ladakh was not logged by boot 2: fallback unrecognized power; the review's sensitivity says a regional rank would make Punjab 12. Measuring it needs one more probe boot; put to Eric. |
| F6 | real | FIXED | Counts (1,754), README wording, metadata description, architecture status, procedure superseded notes, acceptance wording. |
| false greens 3, 4 | adopted | FIXED | `test_shipped.py`: checked-in tables/effect/README recomputed from the named boot; additive after-lobby registration asserted. |
| false greens 1, 2 | adopted | FIXED | with F2. |
| false greens 5–8 | partly | 5 adopted (fallback-unmeasured test); 6 (two-slice component), 7 (ledger byte regeneration), 8 (runtime root identity) left as listed gaps: 6 has no production case, 7 is `author_ledger.py` regeneration already run by hand, 8 cannot be proven from inside the log without a value path the engine exposes. |
| Part 2 | — | — | B5–B7, L2 moot under v4 as the reviewer says; L3 closed by F3; L5/L6 closed by F2 to the extent the reviewer asked (protected blocks, finite comparisons, duplicates, guard, whole-file balance); the known-roster check is not implemented (the save contains every country; a truncated database now fails the balance check). |

Verdict after the fixes: SAFE TO MERGE on code; the acceptance scope (F1) and two ledger judgments (F4, F5/Ladakh) are Eric's.

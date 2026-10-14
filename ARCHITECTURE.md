# Architecture

**Purpose.** Give each 1836 country the infamy its 1816–1835 conduct would generate under the vanilla 1.14.5 formula, replayed as one decaying balance per country and read at the start of 1836-01-01 (spec v3.1 + the v4 addendum of 2026-10-14: the game's own day-one inputs, the observed stage order with the rank block, whole-number output). A defensible estimate, every approximation declared in the README.

## Data flow

```
research/scripts/author_ledger.py  (judgment tables + vanilla culture/homeland data)
  -> research/acts.csv, goals.csv, goal_states.csv        20 acts / 37 goals / 52 components (2026-10-13)
  -> tools/hsi/ledger.py           load + every refusal rule (window, dates, tags, components, slices, claims)

research/measurement/capture-plan.json -> research/scripts/capture_audit.py  static eligibility + estimates -> research/probe/config.json (fixture_slices)
tools/hsi/probe_gen.py  (from the ledger + config) -> research/probe/   throwaway mod, one boot, never shipped
  -> ~/Documents/.../logs/debug.log  lines "HSI;<hook>;<sample>;<date>;<kind>;<key>;k=v..."
  -> tools/hsi/measurement.py       parse rotated logs, group samples, receipt (start hooks complete; monthly samples as present), start_snapshot (day one), monthly_snapshots (oracle A)

research/measurement/2026-10-14-run-*/   two boots: attempt 1 (captures, engine facts), boot 2 (the measurement)

tools/hsi/formula.py    component value (00_infamy_values.txt replica, engine-verified), goal raw value, stages S,C,G,K,R,F in the observed order (K = rank block), nominal charge per rule
tools/hsi/timeline.py   one balance per country: decay 5/365.25 per day, clamp [0,1000], canonical same-day order, horizon
tools/hsi/generate.py   oracle A (every DIAG record) -> day-one snapshot (start_b) -> five whole-number tables -> common/scripted_effects/zz_hsi_effects.txt,
                         research/tables.json, research/derivation.csv (stage values per goal), README table; header binds every input hash (tools/hsi/hashes.py)
tools/hsi/validate.py   BOM, braces, rule flags vs vanilla, header hashes, manifest entries
tools/hsi/savecheck.py  structural plaintext-save reader; acceptance comparison with positivity and tolerance
```

**Shipped files:** `.metadata/metadata.json`, `common/on_actions/zz_hsi_on_actions.txt` (additive registration on `on_game_started_after_lobby`), `common/scripted_effects/zz_hsi_effects.txt` (generated: rule dispatch with Standard as `else`, scalar `change_infamy` lines, `hsi_applied` guard).

**Constants:** all vanilla numbers live in `tools/hsi/constants.py` with the defines file:line beside each, including the rank scaling table from `common/country_ranks/00_country_ranks.txt` and the declared fallback ranks for absent actors.

**Tests:** `tools/tests/` (133 passed + 1 skip on 2026-10-14 at the v0.1.0 merge; the skip is the real acceptance save, waived for v1; `test_capture_audit.py` and `test_shipped.py` need the vanilla install and the boot-2 directory). Fixtures: `ledger_ok/`, `make_probe_log.py` (synthetic probe log consistent with the formula). `test_shipped.py` recomputes the checked-in tables and effect from the named boot; `test_capture_audit.py` and `test_shipped.py` need the vanilla install.

**Research artifacts:** `research/sources.md` (one block per act), `research/not_representable.md` (nine excluded candidates with the rule that excludes each), `research/measurement/` (procedure, capture plan, boot scripts, dated evidence), `research/acceptance/` (procedure, dated evidence), `research/ab_logger/` (test-only play-start logger).

**Status 2026-10-14 evening:** measured (two probe boots), simplified per Eric's ruling (spec v4 addendum), generated (Egypt 54, Punjab 11 at Standard), smoke-accepted on a Standard start (Egypt Notorious, Punjab 11.0, no new errors; no save, so the structural save check and the reload/late-enable checks have not run), reviewed by three pre-boot Codex rounds and one fresh whole-branch round (docs/reviews/). Remaining: the save-based acceptance (or an explicit owner waiver), then the merge to `main`.

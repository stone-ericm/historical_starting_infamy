# Acceptance boot (Eric), one short session, about five minutes

The shipped mod is the release folder the launcher sees (`~/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy_release`,
built by `tools/build_release.sh` from this repository, which lives in `~/projects/` since 2026-10-14 because the
launcher cannot cope with a git repository inside its mod folder). The boot script enables that folder in place, backs
your playset up into a run receipt and restores it on exit, exactly as the probe boots did.

1. From the repo root:
   ```bash
   tools/build_release.sh
   HSI_MOD_PATH="$HOME/Documents/Paradox Interactive/Victoria 3/mod/historical_starting_infamy_release" bash research/measurement/boot_probe.sh
   ```
2. New Game. Pick any country (France is fine). Leave the Infamy Generation rule at its default (Standard). Start.
3. Stay paused. Open Egypt's country panel: it should show 54 infamy. Open Punjab (the Sikh Empire): 11. Any other
   country: 0, except Bolivia at vanilla's 50. Screenshot Egypt's infamy tooltip.
4. Still paused: Save Game as `hsi_accept_std_1836_01_01`. Quit to desktop. The boot window restores your playset.
5. Tell Claude. Claude collects (`research/measurement/collect_evidence.sh ~/Desktop`), copies the save into
   `research/acceptance/<date>/saves/` (gitignored, hash committed), runs
   `python3 -m hsi.savecheck --save <save> --tables ../research/tables.json --rule standard --tolerance 0.005`
   (every emitted country at its table value, every other country at 0, Bolivia at 50, the `hsi_applied` guard set
   once) and diffs `error.log` against the probe boots.

Spec v3.1 section 9 keeps these as acceptance (the v4 addendum did not drop them): a Very Low boot the same way
(Egypt 16, Punjab 1; save as `hsi_accept_vlow_1836_01_01`) and the lifecycle checks (Load Game `hsi_accept_std…` →
stay paused → Save As `hsi_reload_1836_01_01`; then load any older vanilla save with the mod on, stay paused, save as
`hsi_lateenable_check`). The 2026-10-14 Standard boot without a save is a smoke check, recorded as such in its
notes. **Waived by Eric on 2026-10-14 ("waive"):** the save-based checks (exact values, roster at zero, Bolivia 50, guard once, reload, late-enable, Very Low) are not required for v1; the smoke check stands as the acceptance record.

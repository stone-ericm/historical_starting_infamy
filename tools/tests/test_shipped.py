# tools/tests/test_shipped.py
"""The checked-in mod files against the named measurement (final review, false greens 3 and 4). Skipped where the
boot directory or the vanilla install is absent."""
import json
import os
import re
from pathlib import Path
import pytest
from hsi.ledger import load_ledger
from hsi.measurement import extract, session_logs, parse_lines, start_snapshot
from hsi import generate

REPO = Path(__file__).resolve().parents[2]
BOOT = REPO / "research/measurement/2026-10-14-run-20261014-150956-73604"
GAME = Path(os.environ.get("HSI_GAME_DIR", Path.home() / "Library/Application Support/Steam/steamapps/common/Victoria 3/game"))

def test_on_action_registration_is_additive_and_calls_the_effect():
    text = (REPO / "common/on_actions/zz_hsi_on_actions.txt").read_bytes()
    assert text.startswith(b"\xef\xbb\xbf")
    s = text.decode("utf-8-sig")
    assert re.search(r"on_game_started_after_lobby\s*=\s*\{\s*on_actions\s*=\s*\{\s*hsi_on_game_started\s*\}\s*\}", s)
    assert "effect = {" not in s.split("on_game_started_after_lobby")[1].split("}")[0]       # additive registration only
    assert re.search(r"hsi_on_game_started\s*=\s*\{\s*effect\s*=\s*\{\s*hsi_apply_starting_infamy = yes\s*\}\s*\}", s)
    assert not re.search(r"(?m)^on_game_started\s*=", s)                                   # never the lobby-time hook

@pytest.mark.skipif(not (BOOT / "probe-config.json").exists(), reason="boot 2 directory absent")
def test_checked_in_tables_and_effect_match_a_recomputation_from_the_named_boot():
    led = load_ledger(REPO / "research")
    snap = start_snapshot(parse_lines(extract(session_logs(BOOT))))
    tables, rows = generate.compute_tables(led, snap)
    assert json.loads((REPO / "research/tables.json").read_text()) == tables
    eff = (REPO / "common/scripted_effects/zz_hsi_effects.txt").read_text(encoding="utf-8-sig")
    for rule in generate.RULES:
        body = eff.split(f"hsi_table_{rule} = {{")[1].split("\n}")[0]
        found = dict(re.findall(r"c:([A-Z0-9]{3}) \?= \{ change_infamy = (\d+) \}", body))
        assert {k: int(v) for k, v in found.items()} == tables[rule], rule
        assert "BOL" not in found
    assert "else = { hsi_table_standard = yes }" in eff and "limit = { NOT = { has_global_variable = hsi_applied } }" in eff
    readme = (REPO / "README.md").read_text()
    for tag, v in tables["standard"].items():
        assert re.search(rf"\| {tag} \| \d+ \| \d+ \| {v} \| \d+ \| \d+ \|", readme)

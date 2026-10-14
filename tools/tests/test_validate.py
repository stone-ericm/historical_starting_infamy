# tools/tests/test_validate.py
from pathlib import Path
import shutil
from hsi import validate
from hsi.bom import write_text_bom

def test_check_bom_reports_missing(tmp_path):
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    write_text_bom(a, "x = 1\n"); b.write_text("x = 1\n")
    assert validate.check_bom([a, b]) == [f"missing BOM: {b}"]

def test_check_braces_ignores_strings_and_comments():
    ok = 'a = {\n\tdebug_log = "HSI;{x}"  # comment with }\n}\n'
    assert validate.check_braces(ok, "ok.txt") == []
    bad = "a = {\n\tb = {\n}\n"
    assert validate.check_braces(bad, "bad.txt") == ["bad.txt: unbalanced braces (depth 1 at end)"]

def test_check_rule_flags(tmp_path):
    g = tmp_path / "game" / "common" / "game_rules"; g.mkdir(parents=True)
    (g / "00_game_rules.txt").write_text("infamy_generation = {\n\tx = { flag = infamy_generation_very_low }\n\ty = { flag = infamy_generation_low }\n}\n")
    eff = "if = { limit = { has_game_rule = infamy_generation_very_low } }\nelse_if = { limit = { has_game_rule = infamy_generation_higher } }\n"
    assert validate.check_rule_flags(eff, tmp_path / "game") == ["unknown game rule flag: infamy_generation_higher"]

def stub_game(tmp_path):
    g = tmp_path / "game" / "common" / "game_rules"; g.mkdir(parents=True)
    (g / "00_game_rules.txt").write_text("infamy_generation = {\n\tx = { flag = infamy_generation_very_low }\n\ty = { flag = infamy_generation_low }\n}\n")
    return tmp_path / "game"

def test_main_probe_only_on_generated_probe(tmp_path):
    game = stub_game(tmp_path)
    probe = tmp_path / "repo" / "research" / "probe" / "common" / "x"
    probe.mkdir(parents=True)
    write_text_bom(probe / "ok.txt", "a = { b = 1 }\n")
    rc = validate.main(["--repo", str(tmp_path / "repo"), "--game-dir", str(game), "--probe-only"])
    assert rc == 0
    (probe / "bad.txt").write_text("a = {\n")
    assert validate.main(["--repo", str(tmp_path / "repo"), "--game-dir", str(game), "--probe-only"]) == 1

def test_main_refuses_absent_probe_and_unknown_probe_flag(tmp_path, capsys):
    # review R1 finding L4: a missing root used to validate as OK
    game = stub_game(tmp_path)
    (tmp_path / "repo").mkdir()
    assert validate.main(["--repo", str(tmp_path / "repo"), "--game-dir", str(game), "--probe-only"]) == 1
    assert "missing" in capsys.readouterr().err
    probe = tmp_path / "repo" / "research" / "probe" / "common" / "scripted_effects"
    probe.mkdir(parents=True)
    write_text_bom(probe / "p.txt", "a = { if = { limit = { has_game_rule = infamy_generation_vrey_low } } }\n")
    assert validate.main(["--repo", str(tmp_path / "repo"), "--game-dir", str(game), "--probe-only"]) == 1
    assert "unknown game rule flag: infamy_generation_vrey_low" in capsys.readouterr().err
    assert validate.main(["--repo", str(tmp_path / "repo"), "--game-dir", str(tmp_path / "nowhere"), "--probe-only"]) == 1

def test_main_full_mode_requires_bindings_and_shipped_files(tmp_path, capsys):
    game = stub_game(tmp_path)
    repo = tmp_path / "repo"
    (repo / "common" / "scripted_effects").mkdir(parents=True)
    write_text_bom(repo / "common" / "scripted_effects" / "zz_hsi_effects.txt", "hsi_apply_starting_infamy = { }\n")
    rc = validate.main(["--repo", str(repo), "--game-dir", str(game)])
    err = capsys.readouterr().err
    assert rc == 1 and "--measurement" in err and "missing" in err

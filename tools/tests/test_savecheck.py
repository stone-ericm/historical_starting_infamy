# tools/tests/test_savecheck.py
from pathlib import Path
import pytest
from hsi import savecheck

SAVE = """SAV0100test
meta_data={
	save_game_version=1
	version="1.14.5"
	game_date=1836.1.1
	game_rules={
		settings={ achievements_allowed infamy_generation_very_low }
	}
}
variables={
	data={ {
			flag=hsi_applied
			tick=0
			data={
				type=boolean
				identity=1
			}
		} {
			flag=other_flag
			tick=0
		} }
	list={ }
}
country_manager={
	database={
		1={
			definition="EGY"
			infamy=2.29
			ai={
				infamy=99
			}
		}
		2={
			definition="BOL"
			infamy=50
		}
		3={
			definition="GBR"
			ai={
				infamy=7
			}
		}
	}
}
"""
TABLES = {"standard": {"EGY": 5.42}, "very_low": {"EGY": 2.29}, "low": {}, "high": {}, "very_high": {}}

def write(tmp_path, text=SAVE):
    p = tmp_path / "s.v3"; p.write_text(text, encoding="utf-8"); return p

def test_parse_save_fields(tmp_path):
    info = savecheck.parse_save(write(tmp_path))
    assert info.game_date == "1836.1.1"
    assert info.rule_flags == {"achievements_allowed", "infamy_generation_very_low"}
    assert info.countries == {"EGY": 2.29, "BOL": 50.0, "GBR": 0.0}   # nested ai.infamy ignored; absent -> 0
    assert info.global_flag_counts["hsi_applied"] == 1

def test_check_passes_on_matching_save(tmp_path):
    info = savecheck.parse_save(write(tmp_path))
    assert savecheck.check_save(info, TABLES, "very_low", 0.005) == []

@pytest.mark.parametrize("old,new,needle", [
    ("flag=hsi_applied", "flag=hsi_unapplied", "hsi_applied"),
    ("infamy=2.29\n", "", "EGY"),                       # hook never applied: expected positive missing
    ("infamy=2.29\n", "infamy=0\n", "positive"),       # zero where positive expected
    ("infamy=2.29\n", "infamy=4.58\n", "EGY"),         # doubled application
    ('definition="EGY"', 'definition="EGX"', "EGY"),   # wrong recipient
    ("game_date=1836.1.1", "game_date=1836.1.2", "date"),
    ("infamy_generation_very_low", "infamy_generation_low", "rule"),
    ('definition="GBR"\n', 'definition="GBR"\n\t\t\tinfamy=0.3\n', "GBR"),   # unexpected positive
    ("infamy=50\n", "infamy=49\n", "BOL"),
])
def test_failure_directions(tmp_path, old, new, needle):
    assert old in SAVE
    info = savecheck.parse_save(write(tmp_path, SAVE.replace(old, new, 1)))
    problems = savecheck.check_save(info, TABLES, "very_low", 0.005)
    assert problems, "expected a failure"
    assert any(needle in p for p in problems)

def test_boundary_tolerance_rejects_half_of_smallest_amount(tmp_path):
    tables = {"very_low": {"EGY": 0.05}}
    info = savecheck.parse_save(write(tmp_path, SAVE.replace("infamy=2.29", "infamy=0.0")))
    assert savecheck.check_save(info, tables, "very_low", 0.005)
    info2 = savecheck.parse_save(write(tmp_path, SAVE.replace("infamy=2.29", "infamy=0.1")))
    assert savecheck.check_save(info2, tables, "very_low", 0.005)
    info3 = savecheck.parse_save(write(tmp_path, SAVE.replace("infamy=2.29", "infamy=0.052")))
    assert savecheck.check_save(info3, tables, "very_low", 0.005) == []

def test_empty_table_accepted_when_replay_says_so(tmp_path):
    text = SAVE.replace("infamy=2.29\n", "").replace("infamy_generation_very_low", "infamy_generation_low")
    info = savecheck.parse_save(write(tmp_path, text))
    assert savecheck.check_save(info, TABLES, "low", 0.005) == []

def test_truncated_save_fails_loudly(tmp_path):
    with pytest.raises(savecheck.SaveParseError):
        savecheck.parse_save(write(tmp_path, SAVE[: len(SAVE) // 2]))

# final review F2: these five used to pass as [] ; each must now fail with a named reason
@pytest.mark.parametrize("old,new,needle,parse_error", [
    ("infamy=2.29\n", "infamy=nan\n", "non-finite", True),
    ("infamy=50\n", "infamy=nan\n", "non-finite", True),
    ("\t\t2={\n\t\t\tdefinition=\"BOL\"\n\t\t\tinfamy=50\n\t\t}\n", "", "BOL record missing", False),
    ("flag=other_flag", "flag=hsi_applied", "appears 2 times", False),
    ("country_manager={", "truncated_manager={\ncountry_manager={", "unbalanced", True),
])
def test_review_f2_mutations_fail_closed(tmp_path, old, new, needle, parse_error):
    assert old in SAVE, old
    text = SAVE.replace(old, new, 1)
    if parse_error:
        with pytest.raises(savecheck.SaveParseError) as e:
            savecheck.parse_save(write(tmp_path, text))
        assert needle in str(e.value)
    else:
        problems = savecheck.check_save(savecheck.parse_save(write(tmp_path, text)), TABLES, "very_low", 0.005)
        assert any(needle in p for p in problems), problems

def test_tolerance_and_table_values_must_be_finite_and_small(tmp_path):
    info = savecheck.parse_save(write(tmp_path))
    assert savecheck.check_save(info, TABLES, "very_low", float("nan"))
    assert savecheck.check_save(info, TABLES, "very_low", 3.0)              # could hide a wrong whole number
    assert savecheck.check_save(info, {"very_low": {"EGY": float("nan")}}, "very_low", 0.005)
    doubled = savecheck.parse_save(write(tmp_path, SAVE.replace("infamy=2.29", "infamy=4.58")))
    assert savecheck.check_save(doubled, TABLES, "very_low", 0.49)           # the largest allowed tolerance still catches it

def test_quoted_braces_and_duplicate_definitions(tmp_path):
    text = SAVE.replace('version="1.14.5"', 'version="1.14.5 {not a block}"')
    assert savecheck.parse_save(write(tmp_path, text)).countries["EGY"] == 2.29
    dup = SAVE.replace('definition="GBR"', 'definition="EGY"')
    with pytest.raises(savecheck.SaveParseError) as e:
        savecheck.parse_save(write(tmp_path, dup))
    assert "defined twice" in str(e.value)

REAL = sorted(Path(__file__).resolve().parents[2].glob("research/acceptance/*/saves/hsi_accept_std_1836_01_01*.v3"))

@pytest.mark.skipif(not REAL, reason="retained acceptance save absent on this machine")
def test_real_acceptance_save_matches_standard_table():
    import json
    repo = Path(__file__).resolve().parents[2]
    tables = json.loads((repo / "research" / "tables.json").read_text())
    info = savecheck.parse_save(REAL[-1])
    assert savecheck.check_save(info, tables, "standard", 0.005) == []

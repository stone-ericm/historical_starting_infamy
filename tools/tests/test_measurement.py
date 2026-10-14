# tools/tests/test_measurement.py
from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).parent / "fixtures"))
import make_probe_log
from hsi.measurement import (parse_number, parse_lines, extract, group_samples, build_snapshot,
                             start_snapshot, write_manifest, verify_manifest, expected_receipt,
                             check_receipt, monthly_snapshots, MeasurementError, ManifestError)
from hsi.ledger import load_ledger

LEDGER = Path(__file__).parent / "fixtures" / "ledger_ok"
CFG = {"sampler_tag": "GBR", "fixture_holder": "FRA", "months": 3, "fixture_slices": [], "rule": "very_low"}

def records(tmp_path, **kw):
    p = make_probe_log.write(tmp_path / "debug.log", **kw)
    return parse_lines(extract(p))

def test_parse_number_handles_separators_and_unicode_minus():
    assert parse_number("1,022,805,087") == 1022805087.0
    assert parse_number("−0.05") == -0.05
    assert parse_number(" 3.75 ") == 3.75
    with pytest.raises(MeasurementError):
        parse_number("abc")
    with pytest.raises(MeasurementError):
        parse_number("nan")
    with pytest.raises(MeasurementError):
        parse_number("inf")

def test_extract_reads_rotated_logs_oldest_first(tmp_path):
    # observed 2026-10-14: the engine rotates debug.log every 512 KB; one session spans several files
    from hsi.measurement import session_logs
    paths = make_probe_log.write_rotated(tmp_path, parts=3)
    assert [p.name for p in paths] == ["debug.2.log", "debug.1.log", "debug.log"]
    assert extract(list(reversed(paths))) == make_probe_log.lines()           # order of arguments does not matter
    assert [p.name for p in session_logs(tmp_path)] == ["debug.2.log", "debug.1.log", "debug.log"]
    assert check_receipt(parse_lines(extract(session_logs(tmp_path))), expected()) == []

def test_extract_finds_payload_after_engine_prefix(tmp_path):
    p = make_probe_log.write(tmp_path / "debug.log")
    payloads = extract(p)
    assert all(l.startswith("HSI;") for l in payloads)
    assert len(payloads) == len(make_probe_log.lines())

def test_group_samples_and_duplicate_refused(tmp_path):
    recs = records(tmp_path)
    groups = group_samples(recs)
    assert ("start_a", 0) in groups and ("monthly", 3) in groups
    with pytest.raises(MeasurementError):
        group_samples(recs + [recs[0]])

def test_build_snapshot_fields(tmp_path):
    groups = group_samples(records(tmp_path))
    snap = build_snapshot(groups[("monthly", 3)])
    assert snap.global_pop == 1022805087.0
    s = snap.slice("STATE_ALEPPO", "EGY")
    assert s["pop_share_uncapped"] == pytest.approx(1.906)
    assert snap.country("EGY")["unrec_mult"] == pytest.approx(-0.1)
    assert snap.diag[("EGY", "STATE_ALEPPO", "EGY")]["shared_language"] == 1.0
    start = build_snapshot(groups[("start_b", 0)])
    assert start.rule == "very_low" and start.date == "lobby"

def expected():
    led = load_ledger(LEDGER)
    return expected_receipt(led.all_slices(), led.holder_tags(), CFG, led.victim_tags())

def drop(recs, pred):
    return [r for r in recs if not pred(r)]

def test_receipt_complete_on_the_fixture(tmp_path):
    assert check_receipt(records(tmp_path), expected()) == []
    assert [s.sample for s in monthly_snapshots(records(tmp_path))] == [1, 2, 3]

def test_receipt_refuses_missing_diagnostics(tmp_path):
    recs = drop(records(tmp_path), lambda r: r.kind == "DIAG")
    problems = check_receipt(recs, expected())
    assert problems and all("DIAG" in p for p in problems)

def test_receipt_refuses_a_missing_sample_or_start_hook(tmp_path):
    recs = records(tmp_path)
    assert any("monthly sample 3" in p for p in check_receipt(drop(recs, lambda r: r.hook == "monthly" and r.sample == 3), expected()))
    assert any("start_b" in p for p in check_receipt(drop(recs, lambda r: r.hook == "start_b"), expected()))
    assert any("RULE" in p for p in check_receipt(drop(recs, lambda r: r.kind == "RULE" and r.hook == "start_a"), expected()))

def test_receipt_refuses_mixed_dates_inside_the_sampler_records(tmp_path):
    out = []
    for r in records(tmp_path):
        if r.hook == "monthly" and r.sample == 3 and r.kind == "STATE" and r.key == "STATE_SYRIA/EGY":
            r = type(r)(r.hook, r.sample, "April 9, 1836", r.kind, r.key, r.fields)
        out.append(r)
    assert any("date" in p for p in check_receipt(out, expected()))

def strip_field(recs, kind, field):
    out = []
    for r in recs:
        if r.kind == kind:
            f = {k: v for k, v in r.fields.items() if k != field}
            r = type(r)(r.hook, r.sample, r.date, r.kind, r.key, f)
        out.append(r)
    return out

def test_receipt_schema_refusals_from_review_r2(tmp_path):
    recs = records(tmp_path); exp = expected()
    assert any("lacks gen_mult" in p for p in check_receipt(strip_field(recs, "COUNTRY", "gen_mult"), exp))
    assert any("lacks claim" in p for p in check_receipt(strip_field(recs, "DIAG", "claim"), exp))
    assert any("lacks unrec_mult" in p for p in check_receipt(strip_field(recs, "DIAG", "unrec_mult"), exp))
    # start_b must carry the rule the lobby was set to; start_a is an observation either way
    flipped = [type(r)(r.hook, r.sample, r.date, r.kind, r.key, {"flag": "standard"}) if (r.kind == "RULE" and r.hook == "start_b") else r for r in recs]
    assert any("start_b" in p and "standard" in p for p in check_receipt(flipped, exp))
    flipped_a = [type(r)(r.hook, r.sample, r.date, r.kind, r.key, {"flag": "standard"}) if (r.kind == "RULE" and r.hook == "start_a") else r for r in recs]
    assert check_receipt(flipped_a, exp) == []
    # a diagnostic dated years away from its sampler is not the same measurement
    far = [type(r)(r.hook, r.sample, "May 17, 1840", r.kind, r.key, r.fields) if r.kind == "DIAG" else r for r in recs]
    assert any("not the same month" in p for p in check_receipt(far, exp))
    # a root firing a few days after the sampler, with its own operands, is fine
    near = [type(r)(r.hook, r.sample, "April 9, 1836", r.kind, r.key, r.fields) if (r.kind == "DIAG" and r.sample == 3 and r.key.startswith("GBR/")) else r for r in recs]
    assert check_receipt(near, exp) == []
    # a stray fourth sample is outside the configured receipt and never consumed
    extra = recs + [type(r)(r.hook, 4, "May 1, 1836", r.kind, r.key, r.fields) for r in recs if r.hook == "monthly" and r.sample == 3]
    assert any("unexpected group monthly sample 4" in p for p in check_receipt(extra, exp))
    assert start_snapshot(extra).hook == "start_b"                          # the day-one snapshot is unaffected
    # review R3 P4: exact key sets, strict date progression, calendar errors named
    extra_country = recs + [type(r)(r.hook, r.sample, r.date, "COUNTRY", "XXX", r.fields) for r in recs if r.kind == "COUNTRY" and r.key == "EGY" and r.hook == "start_b"]
    assert any("unexpected COUNTRY XXX" in p for p in check_receipt(extra_country, exp))
    extra_state = recs + [type(r)(r.hook, r.sample, r.date, "STATE", "STATE_NOWHERE/EGY", r.fields) for r in recs if r.kind == "STATE" and r.key == "STATE_SYRIA/EGY" and r.hook == "monthly" and r.sample == 1]
    assert any("unexpected STATE STATE_NOWHERE/EGY" in p for p in check_receipt(extra_state, exp))
    same_day = [type(r)(r.hook, r.sample, "April 1, 1836", r.kind, r.key, r.fields) if r.hook == "monthly" else r for r in recs]
    assert any("strictly increasing" in p for p in check_receipt(same_day, exp))
    bad_cal = [type(r)(r.hook, r.sample, "April 31, 1836", r.kind, r.key, r.fields) if (r.hook == "monthly" and r.sample == 3) else r for r in recs]
    assert any("invalid calendar date" in p for p in check_receipt(bad_cal, exp))
    rule_in_monthly = recs + [type(r)("monthly", 1, "February 1, 1836", "RULE", "-", {"flag": "very_low"}) for r in recs[:1]]
    assert any("do not belong" in p for p in check_receipt(rule_in_monthly, exp))
    # a malformed numeric field is a named problem, not a traceback
    broken = [type(r)(r.hook, r.sample, r.date, r.kind, r.key, dict(r.fields, pop="abc")) if r.kind == "GLOBAL" else r for r in recs]
    assert any("pop" in p and "not a number" in p for p in check_receipt(broken, exp))

def test_start_snapshot_is_the_after_lobby_sample_and_monthly_is_optional(tmp_path):
    recs = records(tmp_path)
    s = start_snapshot(recs)
    assert s.hook == "start_b" and s.sample == 0 and s.rule == "very_low"
    assert s.slice("STATE_ALEPPO", "EGY")["pop_share_uncapped"] == pytest.approx(1.9)
    assert s.country("EGY")["rank"] == 3.0 and s.country("TUR")["rank"] == 6.0
    without_3 = drop(recs, lambda r: r.hook == "monthly" and r.sample == 3)
    assert any("monthly sample 3" in p for p in check_receipt(without_3, expected()))
    assert check_receipt(without_3, expected(), require_monthly=False) == []
    assert any("start_b" in p for p in check_receipt(drop(recs, lambda r: r.hook == "start_b"), expected(), require_monthly=False))
    with pytest.raises(MeasurementError):
        start_snapshot(drop(recs, lambda r: r.hook == "start_b"))

def test_victim_records_are_optional_but_reported(tmp_path):
    from hsi.measurement import missing_optional
    led = load_ledger(LEDGER)
    exp = expected_receipt(led.all_slices(), led.holder_tags(), CFG, led.victim_tags() | {"LAD"})
    assert "LAD" in exp["optional_tags"] and "TUR" in exp["optional_tags"] and "EGY" in exp["tags"]
    assert check_receipt(records(tmp_path), exp) == []
    assert missing_optional(records(tmp_path), exp) == ["LAD"]

def test_receipt_refuses_a_missing_fixture_slice_or_country(tmp_path):
    led = load_ledger(LEDGER)
    exp = expected_receipt(led.all_slices(), led.holder_tags(), dict(CFG, fixture_slices=[["STATE_TEXAS", "MEX"]]), led.victim_tags())
    problems = check_receipt(records(tmp_path), exp)
    assert any("STATE_TEXAS/MEX" in p for p in problems) and any("COUNTRY MEX" in p for p in problems)
    exp2 = expected_receipt(led.all_slices(), led.holder_tags(), dict(CFG, fixture_holder="USA"), led.victim_tags())
    assert any("USA" in p for p in check_receipt(records(tmp_path), exp2))

def test_manifest_roundtrip_and_tamper(tmp_path):
    d = tmp_path / "m"; d.mkdir()
    (d / "a.log").write_text("one"); (d / "b.txt").write_text("two")
    write_manifest(d, ["a.log", "b.txt"])
    assert verify_manifest(d) == ["a.log", "b.txt"]
    (d / "a.log").write_text("changed")
    with pytest.raises(ManifestError):
        verify_manifest(d)

def test_manifest_rejects_unexpected_and_missing_files(tmp_path):
    d = tmp_path / "m"; d.mkdir()
    (d / "a.log").write_text("one")
    write_manifest(d, ["a.log"])
    (d / "extra.txt").write_text("x")
    with pytest.raises(ManifestError):
        verify_manifest(d)
    (d / "extra.txt").unlink(); (d / "a.log").unlink()
    with pytest.raises(ManifestError):
        verify_manifest(d)

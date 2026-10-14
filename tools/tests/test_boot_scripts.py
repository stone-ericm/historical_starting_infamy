# tools/tests/test_boot_scripts.py
"""boot_probe.sh / restore_playset.sh against a fake home (review R1 finding B8). The game binary is a stub;
nothing here touches Eric's real playset."""
import os
import subprocess
from pathlib import Path
import pytest

REPO = Path(__file__).resolve().parents[2]
BOOT = REPO / "research/measurement/boot_probe.sh"
RESTORE = REPO / "research/measurement/restore_playset.sh"
COLLECT = REPO / "research/measurement/collect_evidence.sh"
CHECKPOINT = REPO / "research/measurement/checkpoint_logs.sh"
P = '{"enabledMods":[{"path":"/Users/eric/x/eor"}],"disabledDLC":[],"enabledUGC":[]}\n'

def fake(tmp_path, game_rc=0):
    v3 = tmp_path / "v3"; (v3 / "mod" / "hsi_probe").mkdir(parents=True)
    (v3 / "mod" / "hsi_probe" / "stale.txt").write_text("left over from an earlier staging")
    (v3 / "content_load.json").write_text(P)
    game = tmp_path / "game"; game.mkdir()
    bin_ = tmp_path / "fakegame.sh"
    bin_.write_text(f"#!/bin/sh\necho launched \"$@\" > '{tmp_path}/launched.txt'\nexit {game_rc}\n"); bin_.chmod(0o755)
    run = tmp_path / "run"
    env = dict(os.environ, HSI_V3_DIR=str(v3), HSI_V3_GAME=str(game), HSI_V3_BIN=str(bin_), HSI_RUN_DIR=str(run))
    return v3, run, env

def sh(script, env):
    return subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True)

def test_boot_restores_the_same_playset_and_stages_a_clean_probe(tmp_path):
    v3, run, env = fake(tmp_path)
    r = sh(BOOT, env)
    assert r.returncode == 0, r.stderr
    assert (v3 / "content_load.json").read_text() == P                      # byte-identical, not "newest backup"
    assert "-debug_mode" in (tmp_path / "launched.txt").read_text()
    assert not (v3 / "mod" / "hsi_probe" / "stale.txt").exists()            # staged as a clean copy, not a merge
    assert (v3 / "mod" / "hsi_probe" / "common" / "scripted_effects" / "zz_hsi_probe_effects.txt").exists()
    assert not (run / "active").exists()
    archived = [d for d in run.iterdir() if d.is_dir()]
    assert len(archived) == 1
    assert (run / "last").read_text().strip() == str(archived[0])                 # collection goes through this pointer, never "newest"
    assert (archived[0] / "content_load.probe.json").read_text().count("hsi_probe") == 1   # the staged playset is kept as evidence
    assert "restored:" in (archived[0] / "receipt.txt").read_text()
    assert (archived[0] / "probe-config.json").read_text() == (REPO / "research/probe/config.json").read_text()   # from the staged tree
    assert (archived[0] / "capture-plan.json").exists()

def test_two_runs_get_distinct_receipts_and_last_points_at_the_newest(tmp_path):
    v3, run, env = fake(tmp_path)
    assert sh(BOOT, env).returncode == 0
    first = (run / "last").read_text().strip()
    assert sh(BOOT, env).returncode == 0
    second = (run / "last").read_text().strip()
    assert first != second and Path(first).is_dir() and Path(second).is_dir()
    assert not (Path(first) / "active").exists()                                   # never merged into an older archive

def test_failure_while_staging_still_restores(tmp_path):
    v3, run, env = fake(tmp_path)
    import shutil
    shutil.rmtree(v3 / "mod"); (v3 / "mod").write_text("not a directory")           # staging fails after the backup
    r = sh(BOOT, env)
    assert r.returncode != 0
    assert (v3 / "content_load.json").read_text() == P and not (run / "active").exists()

def test_manual_restore_recovers_a_missing_destination(tmp_path):
    v3, run, env = fake(tmp_path)
    a = run / "active"; a.mkdir(parents=True)
    (a / "content_load.original.json").write_text(P)
    (a / "original.sha256").write_text(subprocess.run(["shasum", "-a", "256", str(a / "content_load.original.json")], capture_output=True, text=True).stdout.split()[0] + "\n")
    (a / "run-id").write_text("20260101-000000-1\n")
    (v3 / "content_load.json").unlink()
    r = sh(RESTORE, env)
    assert r.returncode == 0, r.stderr
    assert (v3 / "content_load.json").read_text() == P

def test_launch_failure_still_restores(tmp_path):
    v3, run, env = fake(tmp_path, game_rc=1)
    r = sh(BOOT, env)
    assert r.returncode == 1
    assert (v3 / "content_load.json").read_text() == P and not (run / "active").exists()

def test_nested_boot_is_refused_and_manual_restore_recovers(tmp_path):
    v3, run, env = fake(tmp_path)
    # simulate a killed boot: an active receipt with the probe playset live
    a = run / "active"; a.mkdir(parents=True)
    (a / "content_load.original.json").write_text(P)
    (a / "original.sha256").write_text(subprocess.run(["shasum", "-a", "256", str(a / "content_load.original.json")], capture_output=True, text=True).stdout.split()[0] + "\n")
    (a / "receipt.txt").write_text("started: test\n")
    q = '{"enabledMods":[{"path":"' + str(v3 / "mod" / "hsi_probe") + '"}],"disabledDLC":[],"enabledUGC":[]}\n'
    (v3 / "content_load.json").write_text(q)
    (v3 / "content_load.json.bak-99991231-235959").write_text(q)             # a newer unrelated "backup" must not win
    r = sh(BOOT, env)
    assert r.returncode == 2 and "refusing" in r.stderr
    assert (v3 / "content_load.json").read_text() == q                       # untouched by the refused boot
    r = sh(RESTORE, env)
    assert r.returncode == 0, r.stderr
    assert (v3 / "content_load.json").read_text() == P
    assert not (run / "active").exists()
    assert sh(RESTORE, env).returncode == 2                                  # nothing active any more

def test_restore_refuses_when_the_digest_does_not_match(tmp_path):
    v3, run, env = fake(tmp_path)
    a = run / "active"; a.mkdir(parents=True)
    (a / "content_load.original.json").write_text(P)
    (a / "original.sha256").write_text("0" * 64 + "\n")
    (a / "receipt.txt").write_text("started: test\n")
    q = '{"enabledMods":[{"path":"q"}],"disabledDLC":[],"enabledUGC":[]}\n'
    (v3 / "content_load.json").write_text(q)
    r = sh(RESTORE, env)
    assert r.returncode == 1 and "RESTORE FAILED" in r.stderr and (run / "active").exists()
    assert (v3 / "content_load.json").read_text() == q                             # an invalid backup never overwrites the destination

def test_restore_refuses_an_incomplete_backup(tmp_path):
    v3, run, env = fake(tmp_path)
    (run / "active").mkdir(parents=True)                                            # the boot died before the backup finished
    r = sh(RESTORE, env)
    assert r.returncode == 1 and "no verified backup" in r.stderr and (run / "active").exists()
    assert (v3 / "content_load.json").read_text() == P

def test_restore_survives_an_unreadable_destination(tmp_path):
    # review R3 P2: the old destination's digest is annotation only
    v3, run, env = fake(tmp_path)
    a = run / "active"; a.mkdir(parents=True)
    (a / "content_load.original.json").write_text(P)
    (a / "original.sha256").write_text(subprocess.run(["shasum", "-a", "256", str(a / "content_load.original.json")], capture_output=True, text=True).stdout.split()[0] + "\n")
    (a / "run-id").write_text("20260101-000000-2\n")
    q = v3 / "content_load.json"; q.write_text("garbage"); q.chmod(0)
    if os.access(q, os.R_OK):
        pytest.skip("runner can read a mode-000 file; the injected failure did not occur")
    r = sh(RESTORE, env)
    assert r.returncode == 0, r.stderr
    assert (v3 / "content_load.json").read_text() == P
    archived = Path((run / "last").read_text().strip())
    assert "(unreadable)" in (archived / "receipt.txt").read_text()

def collect_env(tmp_path, env):
    out = tmp_path / "out"; out.mkdir()
    logs = Path(env["HSI_V3_DIR"]) / "logs"; logs.mkdir(exist_ok=True)
    for n in ("debug.log", "system.log", "error.log"):
        (logs / n).write_text(f"{n} line one\n")
    (logs / "debug.4.log").write_text("from an older session\n")
    os.utime(logs / "debug.4.log", (1, 1))                                     # older than any run: must not be collected
    ls = tmp_path / "launcher-settings.json"; ls.write_text('{"rawVersion": "1.14.5"}\n')
    return dict(env, HSI_OUT_ROOT=str(out), HSI_LAUNCHER_SETTINGS=str(ls)), out

def test_collection_binds_to_the_run_and_never_overwrites(tmp_path):
    # review R3 P3
    v3, run, env = fake(tmp_path)
    env, out = collect_env(tmp_path, env)
    # the checkpoint runs while the game is still open: simulate the boot's active phase by hand
    a = run / "active"; a.mkdir(parents=True)
    (a / "run-id").write_text("20260101-000000-9\n"); (a / "receipt.txt").write_text("started: test\n")
    logs = Path(env["HSI_V3_DIR"]) / "logs"
    for n in ("debug.log", "system.log", "error.log"):                          # the game writes these after the boot starts
        (logs / n).write_text(f"{n} line one HSI;x\n")
    (logs / "debug.1.log").write_text("rotated during this session HSI;y\n")  # written after the run started
    r0 = subprocess.run(["bash", str(CHECKPOINT)], env=env, capture_output=True, text=True)
    assert r0.returncode == 0, r0.stderr
    assert [Path(l).name for l in r0.stdout.strip().splitlines()] == ["debug.1.log", "debug.log"]   # oldest rotation first
    assert not (a / "checkpoint" / "debug.4.log").exists()
    import shutil; shutil.rmtree(a)
    assert sh(BOOT, env).returncode == 0
    last = Path((run / "last").read_text().strip())
    (last / "checkpoint").mkdir(); (last / "checkpoint" / "debug.log").write_text("debug.log line one HSI;x\n")
    shots = tmp_path / "shots"; shots.mkdir(); (shots / "Screenshot 1.png").write_bytes(b"png")
    r = subprocess.run(["bash", str(COLLECT), str(shots)], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    d1 = Path(r.stdout.strip())
    assert d1.parent == out and "-run-" in d1.name
    for n in ("debug.log", "system.log", "error.log", "checkpoint/debug.log", "playset.txt", "run-receipt.txt", "probe-config.json", "capture-plan.json", "engine.txt", "attempt.txt", "Screenshot 1.png"):
        assert (d1 / n).exists(), n
    assert (d1 / "debug.1.log").exists() and not (d1 / "debug.4.log").exists()   # rotated logs of this session only
    assert "probe lines: 1 at the checkpoint, 2 in the final logs" in r.stderr
    digests = {p.name: p.read_bytes() for p in d1.iterdir() if p.is_file()}
    r2 = subprocess.run(["bash", str(COLLECT)], env=env, capture_output=True, text=True)
    assert r2.returncode == 3 and "refusing" in r2.stderr                       # same run again: refused, nothing changed
    assert {p.name: p.read_bytes() for p in d1.iterdir() if p.is_file()} == digests
    assert sh(BOOT, env).returncode == 0                                       # a second same-day boot gets its own directory
    r3 = subprocess.run(["bash", str(COLLECT)], env=env, capture_output=True, text=True)
    assert r3.returncode == 0, r3.stderr
    d2 = Path(r3.stdout.strip())
    assert d2 != d1 and d2.exists() and {p.name: p.read_bytes() for p in d1.iterdir() if p.is_file()} == digests

def test_boot_can_enable_a_mod_directory_in_place(tmp_path):
    # the acceptance boots enable this repository itself (no staging); the receipt records what was enabled
    v3, run, env = fake(tmp_path)
    mod = tmp_path / "shipped"; mod.mkdir(); (mod / "descriptor.txt").write_text("x")
    r = sh(BOOT, dict(env, HSI_MOD_PATH=str(mod)))
    assert r.returncode == 0, r.stderr
    archived = Path((run / "last").read_text().strip())
    assert str(mod) in (archived / "content_load.probe.json").read_text()
    assert f"enabled_mod: {mod}" in (archived / "receipt.txt").read_text()
    assert (v3 / "content_load.json").read_text() == P
    assert (v3 / "mod" / "hsi_probe" / "stale.txt").exists()                   # nothing was staged or removed

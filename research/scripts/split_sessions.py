"""Split one collected boot into its game sessions, one directory per new campaign.

A boot can hold more than one campaign: on 2026-11-07 a Standard-rule game was started first, then a Very Low one
(the procedure's), in the same session, so the logs carry two start_a/start_b pairs and the receipt check refuses the
duplicate. This writes <run>/session-<n>/ for every start_a, each holding debug.log (the concatenated rotated logs from
that start_a up to the next one), a copy of probe-config.json and SESSION.md recording the cut and the raw logs'
hashes. The raw logs in <run>/ are never changed. Point the generator at one session directory explicitly.

Usage: python3 research/scripts/split_sessions.py research/measurement/<date>-run-<id>
"""
import hashlib, re, shutil, sys
from pathlib import Path

MARK = re.compile(r"HSI;start_a;0;[^;]*;GLOBAL;")
RULE = re.compile(r"HSI;start_b;0;[^;]*;RULE;-;flag=(\w+)")


def rotation_order(run: Path) -> list:
    """Oldest first: debug.N.log with the highest N, ..., debug.1.log, debug.log."""
    rot = sorted(run.glob("debug.[0-9]*.log"), key=lambda p: -int(p.name.split(".")[1]))
    return rot + ([run / "debug.log"] if (run / "debug.log").exists() else [])


def main(run_dir: str) -> int:
    run = Path(run_dir)
    logs = rotation_order(run)
    lines = []
    for p in logs:
        lines += p.read_bytes().decode("utf-8", errors="replace").splitlines(keepends=True)
    starts = [i for i, l in enumerate(lines) if MARK.search(l)]
    if not starts:
        print("no start_a record: nothing to split"); return 1
    raw = "\n".join(f"- `{p.name}` sha256 `{hashlib.sha256(p.read_bytes()).hexdigest()}`" for p in logs)
    for n, a in enumerate(starts, 1):
        b = starts[n] if n < len(starts) else len(lines)
        out = run / f"session-{n}"
        out.mkdir(exist_ok=True)
        body = "".join(lines[a:b])
        (out / "debug.log").write_text(body, encoding="utf-8")
        shutil.copy2(run / "probe-config.json", out / "probe-config.json")
        rule = RULE.search(body)
        ts = lines[a][:10]
        (out / "SESSION.md").write_text(
            f"# Session {n} of {len(starts)}\n\n"
            f"Lines {a + 1}-{b} of the concatenated raw logs (oldest rotation first), from the start_a record at {ts}.\n"
            f"Infamy rule read by the after-lobby hook: {rule.group(1) if rule else 'not logged'}.\n"
            f"Written by research/scripts/split_sessions.py; the raw logs are unchanged in the parent directory:\n\n{raw}\n",
            encoding="utf-8")
        print(f"session-{n}: lines {a + 1}-{b}, start {ts}, rule {rule.group(1) if rule else '?'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

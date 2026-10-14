# tools/hsi/validate.py
"""Static checks before any commit touching game files (spec §9 step 1)."""
import re
import sys
from pathlib import Path
from .bom import has_bom
from .hashes import generator_source_hashes, vanilla_input_hashes, measurement_hashes, parse_header
from .measurement import sha256_file

def check_bom(paths) -> list:
    return [f"missing BOM: {p}" for p in paths if not has_bom(p)]

def check_braces(text: str, name: str) -> list:
    depth = 0
    in_str = False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_str:
            if ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "#":
            j = text.find("\n", i)
            i = len(text) if j < 0 else j
            continue
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                return [f"{name}: unbalanced braces (closing brace before opening at offset {i})"]
        i += 1
    return [] if depth == 0 else [f"{name}: unbalanced braces (depth {depth} at end)"]

def check_rule_flags(effect_text: str, game_dir: Path) -> list:
    rules = (Path(game_dir) / "common" / "game_rules" / "00_game_rules.txt").read_text(encoding="utf-8-sig")
    known = set(re.findall(r"flag = ([a-z_]+)", rules))
    used = set(re.findall(r"has_game_rule = ([a-z_]+)", effect_text))
    return [f"unknown game rule flag: {f}" for f in sorted(used - known)]

def check_header(repo: Path, game_dir: Path, measurement: Path) -> list:
    eff = repo / "common" / "scripted_effects" / "zz_hsi_effects.txt"
    if not eff.exists():
        return [f"missing generated effect {eff}"]
    header = parse_header(eff.read_text(encoding="utf-8-sig"))
    expected = {f"ledger/{n}": sha256_file(repo / "research" / n) for n in ("acts.csv", "goals.csv", "goal_states.csv")}
    expected.update(measurement_hashes(measurement))
    expected.update(generator_source_hashes(Path(__file__).parent))
    expected.update(vanilla_input_hashes(game_dir))
    problems = []
    for k, v in sorted(expected.items()):
        if header.get(k) != v:
            problems.append(f"stale or missing header hash: {k}")
    if "order" not in header:
        problems.append("header lacks the ordering record")
    return problems

def _script_files(root: Path) -> list:
    return sorted(p for p in root.rglob("*.txt") if "common" in p.parts)

def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True); ap.add_argument("--game-dir", required=True)
    ap.add_argument("--measurement"); ap.add_argument("--probe-only", action="store_true")
    a = ap.parse_args(argv)
    repo, game = Path(a.repo), Path(a.game_dir)
    problems = []
    rules_file = game / "common" / "game_rules" / "00_game_rules.txt"
    if not rules_file.exists():
        problems.append(f"missing game directory or rules file: {rules_file}")
    roots = [repo / "research" / "probe"] if a.probe_only else [repo / "common", repo / "research" / "probe"]
    for r in roots:
        if not r.exists():
            problems.append(f"missing script root: {r}")
    files = [f for r in roots if r.exists() for f in _script_files(r)]
    if not files:
        problems.append("no script files found under " + ", ".join(str(r) for r in roots))
    problems += check_bom(files)
    for f in files:
        problems += check_braces(f.read_text(encoding="utf-8-sig"), str(f.relative_to(repo)))
    if rules_file.exists():
        for f in files:   # the probe reads has_game_rule too (review R1 finding L4)
            problems += check_rule_flags(f.read_text(encoding="utf-8-sig"), game)
    if not a.probe_only:
        for rel in ("common/scripted_effects/zz_hsi_effects.txt", "common/on_actions/zz_hsi_on_actions.txt", ".metadata/metadata.json"):
            if not (repo / rel).exists():
                problems.append(f"missing shipped file: {rel}")
        if not a.measurement:
            problems.append("full validation requires --measurement (the header bindings are part of the gate)")
        elif rules_file.exists():
            problems += check_header(repo, game, Path(a.measurement))
    for p in problems:
        print(p, file=sys.stderr)
    print("validate: " + ("OK" if not problems else f"{len(problems)} problem(s)"))
    return 0 if not problems else 1

if __name__ == "__main__":
    raise SystemExit(main())

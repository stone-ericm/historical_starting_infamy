# tools/hsi/hashes.py
"""Binds generated output to every numerical input (spec §7 outputs, §9 step 1)."""
from pathlib import Path
from .measurement import sha256_file

VANILLA_FIXED = ["common/script_values/00_infamy_values.txt", "common/defines/00_defines.txt",
                 "common/script_values/00_diplomacy_values.txt", "common/game_rules/00_game_rules.txt",
                 "common/country_ranks/00_country_ranks.txt"]

def measurement_hashes(measurement_dir: Path) -> dict:
    """Every engine log the generator read (debug*.log, oldest rotation first) and the probe config."""
    from .measurement import session_logs
    out = {f"measurement/{p.name}": sha256_file(p) for p in session_logs(Path(measurement_dir))}
    cfg = Path(measurement_dir) / "probe-config.json"
    if cfg.exists():
        out["measurement/probe-config.json"] = sha256_file(cfg)
    return out

def generator_source_hashes(tools_hsi_dir: Path) -> dict:
    return {f"generator/{p.name}": sha256_file(p) for p in sorted(Path(tools_hsi_dir).glob("*.py"))}

def vanilla_input_hashes(game_dir: Path) -> dict:
    game_dir = Path(game_dir)
    out = {f"vanilla/{rel}": sha256_file(game_dir / rel) for rel in VANILLA_FIXED}
    for p in sorted((game_dir / "common" / "war_goal_types").glob("*.txt")):
        out[f"vanilla/common/war_goal_types/{p.name}"] = sha256_file(p)
    return out

def header_block(entries: dict) -> str:
    return "".join(f"# HSI-HASH {k} {v}\n" for k, v in sorted(entries.items()))

def parse_header(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        if line.startswith("# HSI-HASH "):
            _, _, name, digest = line.split(" ", 3)
            out[name] = digest.strip()
    return out

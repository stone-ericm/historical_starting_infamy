"""UTF-8 BOM helpers. The engine requires a BOM on every script .txt; editors and the Write tool strip it."""
from pathlib import Path

BOM = b"\xef\xbb\xbf"

def write_text_bom(path: Path, text: str) -> None:
    data = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(BOM + data)

def has_bom(path: Path) -> bool:
    with open(path, "rb") as f:
        return f.read(3) == BOM

from pathlib import Path
from hsi.bom import write_text_bom, has_bom

def test_write_text_bom_prefixes_bom_and_uses_lf(tmp_path: Path):
    p = tmp_path / "a.txt"
    write_text_bom(p, "x = {\r\n\ty = 1\r\n}\n")
    raw = p.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in raw
    assert has_bom(p)

def test_has_bom_false_without_bom(tmp_path: Path):
    p = tmp_path / "b.txt"
    p.write_bytes(b"x = 1\n")
    assert not has_bom(p)

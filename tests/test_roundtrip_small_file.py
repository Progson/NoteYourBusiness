# tests/test_roundtrip_small_file.py
from pathlib import Path
from nyb.config import manager as cfgman
from nyb.core import io as nybio

def test_roundtrip_small_file(tmp_path: Path):
    p = tmp_path / "x.txt"
    p.write_text("hello", encoding="utf-8")

    cfg = cfgman.DEFAULTS
    pw = lambda: b"testpass"

    nyb_path = nybio.encrypt_path(str(p), pw, cfg)
    assert Path(nyb_path).is_file()

    out_path = nybio.decrypt_path(nyb_path, pw, cfg)
    out = Path(out_path)
    assert out.read_text(encoding="utf-8") == "hello"

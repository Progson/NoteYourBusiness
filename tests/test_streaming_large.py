# tests/test_streaming_large.py
from pathlib import Path
from nyb.config import manager as cfgman
from nyb.core import io as nybio
import os

def test_streaming_large(tmp_path: Path):
    # 2 * chunk_size danych (domyślnie 4 MiB), żeby przetestować pętle
    size = 8 * 1024 * 1024
    data = os.urandom(size)
    p = tmp_path / "big.bin"
    p.write_bytes(data)

    cfg = cfgman.DEFAULTS
    pw = lambda: b"streaming-pass"

    nyb_path = nybio.encrypt_path(str(p), pw, cfg)
    out_path = nybio.decrypt_path(nyb_path, pw, cfg)
    assert Path(out_path).read_bytes() == data

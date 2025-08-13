# src/nyb/core/io.py
from __future__ import annotations
import os
from contextlib import contextmanager
from pathlib import Path
import json, base64

from nyb.core import header as hdr
from nyb.core.crypto import derive_key_argon2id, encrypt_bytes, decrypt_bytes

@contextmanager
def write_atomic(target_path: str, tmp_suffix: str = ".tmp"):
    """
    Minimalna wersja: zapis do target.tmp + fsync + os.replace.
    """
    target = Path(target_path)
    tmp = target.with_suffix(target.suffix + tmp_suffix)
    tmp.parent.mkdir(parents=True, exist_ok=True)
    f = open(tmp, "wb")
    try:
        yield f
        f.flush()
        os.fsync(f.fileno())
    finally:
        f.close()
    os.replace(tmp, target)

def _b64(bs: bytes) -> str:
    import base64
    return base64.b64encode(bs).decode("ascii")

def _b64d(s: str) -> bytes:
    import base64
    return base64.b64decode(s.encode("ascii"))

def encrypt_path(path: str, password_source, cfg, logger=None):
    """
    Minimalna implementacja: jeden plik → plik.nyb w tym samym katalogu.
    Brak rekursji i kolizji nazw (dopiszemy później).
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Not a file: {p}")

    # Wczytaj dane (na razie w pamięci)
    plaintext = p.read_bytes()

    # Parametry KDF i cipher
    import os, time
    salt = os.urandom(16)
    nonce = os.urandom(12)
    kdf_cfg = cfg.get("argon2", {"m": 134217728, "t": 3, "p": 1})
    key = derive_key_argon2id(password_source(), salt, kdf_cfg["m"], kdf_cfg["t"], kdf_cfg["p"])

    meta = {
        "original_name": p.name,
        "mtime": int(p.stat().st_mtime),
        "attribs": {"ro": bool(p.stat().st_mode & 0o222 == 0), "hidden": False},  # TODO: prawdziwe RO/Hidden
    }
    app = {"format": "nyb", "ver": "0.1.0"}

    cipher_no_tag = {"algo": "aes-256-gcm", "nonce": _b64(nonce)}
    kdf_params = {"algo": "argon2id", "m": kdf_cfg["m"], "t": kdf_cfg["t"], "p": kdf_cfg["p"], "salt": _b64(salt)}

    header_json = hdr.build_header_json(kdf_params=kdf_params, cipher_params_no_tag=cipher_no_tag, meta=meta, app=app)
    aad = hdr.compute_aad(header_json)

    ciphertext, tag = encrypt_bytes(plaintext, key, nonce, aad)
    header_with_tag = hdr.add_tag_to_header_json(header_json, _b64(tag))
    packed_header = hdr.pack_header(hdr.MAGIC, header_with_tag)

    out_path = p.with_suffix(p.suffix + ".nyb")
    with write_atomic(str(out_path)):
        with open(str(out_path) + ".tmp", "wb") as fout:
            fout.write(packed_header)
            fout.write(ciphertext)
    return str(out_path)

def decrypt_path(path: str, password_source, cfg, logger=None):
    """
    Minimalna implementacja: odczyt .nyb → przywrócenie pliku obok.
    """
    p = Path(path)
    if not p.is_file() or p.suffix.lower() != ".nyb":
        raise FileNotFoundError(f"Expected .nyb file: {p}")

    with open(p, "rb") as fin:
        obj, payload_offset = hdr.unpack_header(fin)
        kdf = obj["kdf"]
        cipher = obj["cipher"]
        meta = obj.get("meta", {})
        tag = _b64d(cipher["tag"])
        nonce = _b64d(cipher["nonce"])
        header_json_no_tag = json.dumps({**obj, "cipher": {k: v for k, v in cipher.items() if k != "tag"}},
                                        separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        aad = hdr.compute_aad(header_json_no_tag)
        ciphertext = fin.read()

    key = derive_key_argon2id(password_source(), _b64d(kdf["salt"]), kdf["m"], kdf["t"], kdf["p"])
    plaintext = decrypt_bytes(ciphertext, tag, key, nonce, aad)

    out_name = meta.get("original_name") or p.stem  # fallback
    out_path = p.parent / out_name

    with write_atomic(str(out_path)):
        with open(str(out_path) + ".tmp", "wb") as fout:
            fout.write(plaintext)

    # TODO: przywrócenie mtime oraz RO/Hidden (kolejny sprint)
    return str(out_path)

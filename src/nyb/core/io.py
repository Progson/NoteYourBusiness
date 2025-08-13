# src/nyb/core/io.py
from __future__ import annotations
import os, json, base64, tempfile, shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

from nyb.core import header as hdr
from nyb.core.crypto import derive_key_argon2id, encrypt_stream, decrypt_stream
from nyb.core import metadata as metaio
from nyb.core import recycle as binio
from nyb.utils.naming import next_collision_free

@contextmanager
def _atomic_writer(final_path: Path, tmp_suffix: str = ".tmp"):
    final_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = final_path.with_suffix(final_path.suffix + tmp_suffix)
    f = open(tmp_path, "wb")
    try:
        yield f, tmp_path
        f.flush()
        os.fsync(f.fileno())
    finally:
        f.close()
    os.replace(tmp_path, final_path)

def _b64(bs: bytes) -> str:
    return base64.b64encode(bs).decode("ascii")

def _b64d(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))

def _cfg(cfg: dict, path: str, default):
    return cfg.get(path.split(".",1)[0], {}).get(path.split(".",1)[1], default)

def encrypt_file(src: Path, password_source, cfg: dict, logger=None) -> str:
    """
    Szyfruje pojedynczy plik → *.nyb obok (z kolizjami). Wspiera:
      - defaults.replace_original
      - defaults.send_to_recycle_bin (jeśli replace_original==True)
    Automatycznie omija .nyb / .nybnote.
    """
    if src.suffix.lower() in (".nyb", ".nybnote"):
        return ""  # skip
    if not src.is_file():
        return ""

    dst = next_collision_free(src.with_suffix(src.suffix + ".nyb"))

    # KDF / cipher parametry
    salt = os.urandom(16)
    nonce = os.urandom(12)
    k = cfg.get("argon2", {"m": 134217728, "t": 3, "p": 1})
    key = derive_key_argon2id(password_source(), salt, k["m"], k["t"], k["p"])
    kdf_params = {"algo": "argon2id", "m": k["m"], "t": k["t"], "p": k["p"], "salt": _b64(salt)}
    cipher_no_tag = {"algo": "aes-256-gcm", "nonce": _b64(nonce)}
    meta = {"original_name": src.name, **metaio.read_meta(str(src))}
    app = {"format": "nyb", "ver": "0.1.0"}

    header_json = hdr.build_header_json(kdf_params=kdf_params, cipher_params_no_tag=cipher_no_tag, meta=meta, app=app)
    aad = hdr.compute_aad(header_json)

    chunk_size = cfg.get("io", {}).get("chunk_size", 4 * 1024 * 1024)
    with tempfile.NamedTemporaryFile(delete=False) as cttmp, open(src, "rb") as fin:
        _, tag = encrypt_stream(fin, cttmp, key, nonce, aad, chunk_size)
        cttmp_path = Path(cttmp.name)

    try:
        header_with_tag = hdr.add_tag_to_header_json(header_json, _b64(tag))
        packed_header = hdr.pack_header(hdr.MAGIC, header_with_tag)
        with _atomic_writer(dst) as (fout, _tmp):
            fout.write(packed_header)
            with open(cttmp_path, "rb") as ctin:
                shutil.copyfileobj(ctin, fout, length=chunk_size)
    finally:
        try: Path(cttmp_path).unlink(missing_ok=True)
        except Exception: pass

    # Opcjonalne „zamień oryginał zaszyfrowanym”
    replace_original = cfg.get("defaults", {}).get("replace_original", False)
    if replace_original:
        if cfg.get("defaults", {}).get("send_to_recycle_bin", True):
            binio.move_to_recycle_bin(str(src), logger)
        else:
            binio.remove_permanently(str(src), logger)

    return str(dst)

def decrypt_file(nyb: Path, password_source, cfg: dict, logger=None) -> str:
    """
    Odszyfrowuje *.nyb → przywraca plik obok (kolizje), przywraca mtime/attribs.
    Wspiera: defaults.remove_nyb_after_decrypt, defaults.send_to_recycle_bin.
    """
    if not (nyb.is_file() and nyb.suffix.lower() == ".nyb"):
        return ""

    chunk_size = cfg.get("io", {}).get("chunk_size", 4 * 1024 * 1024)
    with open(nyb, "rb") as fin:
        obj, payload_offset = hdr.unpack_header(fin)
        kdf = obj["kdf"]; cipher = obj["cipher"]; meta = obj.get("meta", {})
        tag = _b64d(cipher["tag"]); nonce = _b64d(cipher["nonce"])
        header_json_no_tag = json.dumps({**obj, "cipher": {k: v for k, v in cipher.items() if k != "tag"}},
                                        separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        aad = hdr.compute_aad(header_json_no_tag)
        out_name = meta.get("original_name") or nyb.stem
        out_path = next_collision_free(nyb.parent / out_name)
        key = derive_key_argon2id(password_source(), _b64d(kdf["salt"]), kdf["m"], kdf["t"], kdf["p"])
        fin.seek(payload_offset)
        with _atomic_writer(out_path) as (fout, _tmp):
            decrypt_stream(fin, fout, key, nonce, aad, tag, chunk_size)

    # metadane
    metaio.apply_meta(out_path, {"mtime": meta.get("mtime"), "attribs": meta.get("attribs", {})})

    # po sukcesie: usuń/przenieś .nyb zgodnie z configiem
    if cfg.get("defaults", {}).get("remove_nyb_after_decrypt", True):
        if cfg.get("defaults", {}).get("send_to_recycle_bin", True):
            binio.move_to_recycle_bin(str(nyb))
        else:
            binio.remove_permanently(str(nyb))

    return str(out_path)


# --- Backward-compat wrappers (keep tests/tools working) ---

def encrypt_path(path: str, password_source, cfg, logger=None) -> str:
    """
    Wrapper zgodny wstecznie: deleguje do encrypt_file(Path(path), ...).
    """
    return encrypt_file(Path(path), password_source, cfg, logger)

def decrypt_path(path: str, password_source, cfg, logger=None) -> str:
    """
    Wrapper zgodny wstecznie: deleguje do decrypt_file(Path(path), ...).
    """
    return decrypt_file(Path(path), password_source, cfg, logger)

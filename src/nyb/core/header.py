# src/nyb/core/header.py
from __future__ import annotations
import json
import struct
from typing import Tuple, Dict, Any

MAGIC = b"NYB1"

class HeaderError(Exception):
    pass

def _ensure_no_tag(cipher_params_no_tag: dict) -> None:
    if "tag" in cipher_params_no_tag:
        raise HeaderError("cipher.tag must NOT be present before encryption")

def build_header_json(*, kdf_params: dict, cipher_params_no_tag: dict, meta: dict, app: dict) -> bytes:
    """
    Buduje UTF-8 JSON BEZ pola cipher.tag.
    Top-level: kdf, cipher, meta, app.
    """
    _ensure_no_tag(cipher_params_no_tag)
    obj = {
        "kdf": kdf_params,
        "cipher": cipher_params_no_tag,
        "meta": meta,
        "app": app,
    }
    try:
        # separators: bez spacji → deterministyczne AAD
        data = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    except Exception as e:
        raise HeaderError(f"Failed to serialize header JSON: {e}") from e
    return data

def add_tag_to_header_json(header_json: bytes, tag_b64: str) -> bytes:
    """Zwraca nowy header_json, gdzie cipher.tag = tag_b64 zostaje dodany."""
    try:
        obj = json.loads(header_json.decode("utf-8"))
    except Exception as e:
        raise HeaderError(f"Invalid header_json: {e}") from e
    if not isinstance(obj, dict) or "cipher" not in obj or not isinstance(obj["cipher"], dict):
        raise HeaderError("header_json must contain object 'cipher'")
    if "tag" in obj["cipher"]:
        raise HeaderError("cipher.tag already present")
    obj["cipher"]["tag"] = tag_b64
    try:
        return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    except Exception as e:
        raise HeaderError(f"Failed to serialize header JSON with tag: {e}") from e

def pack_header(magic: bytes, header_json: bytes) -> bytes:
    """
    Pakowanie: magic(4) + header_len(uint32_le) + header_json(bytes)
    """
    if magic != MAGIC:
        raise HeaderError("Invalid magic for NYB pack")
    if not isinstance(header_json, (bytes, bytearray)):
        raise HeaderError("header_json must be bytes")
    header_len = len(header_json)
    if header_len <= 0:
        raise HeaderError("header_json cannot be empty")
    if header_len > 16 * 1024 * 1024:
        raise HeaderError("header_json too large")
    return MAGIC + struct.pack("<I", header_len) + header_json

def unpack_header(fin) -> tuple[dict, int]:
    """
    Odczyt: magic + length + json → (header_dict, payload_offset)
    """
    magic = fin.read(4)
    if magic != MAGIC:
        raise HeaderError("Bad magic")
    raw_len = fin.read(4)
    if len(raw_len) != 4:
        raise HeaderError("Unexpected EOF while reading header length")
    (header_len,) = struct.unpack("<I", raw_len)
    if header_len <= 0 or header_len > 16 * 1024 * 1024:
        raise HeaderError("Unreasonable header length")
    header_json = fin.read(header_len)
    if len(header_json) != header_len:
        raise HeaderError("Unexpected EOF while reading header JSON")
    try:
        obj = json.loads(header_json.decode("utf-8"))
    except Exception as e:
        raise HeaderError(f"Invalid JSON: {e}") from e
    payload_offset = fin.tell() if hasattr(fin, "tell") else 8 + header_len
    return obj, payload_offset

def compute_aad(header_json_without_tag: bytes) -> bytes:
    """
    AAD = dokładnie UTF-8 JSON bez 'cipher.tag'.
    Waliduje brak pola 'tag' w 'cipher'.
    """
    try:
        obj = json.loads(header_json_without_tag.decode("utf-8"))
    except Exception as e:
        raise HeaderError(f"Invalid header_json for AAD: {e}") from e
    cipher = obj.get("cipher")
    if not isinstance(cipher, dict):
        raise HeaderError("cipher object missing in header_json for AAD")
    if "tag" in cipher:
        raise HeaderError("cipher.tag must NOT be present when computing AAD")
    return header_json_without_tag

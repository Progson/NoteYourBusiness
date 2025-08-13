# src/nyb/core/crypto.py
from __future__ import annotations
from argon2.low_level import hash_secret_raw, Type
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class IntegrityError(Exception):
    pass

def derive_key_argon2id(password: bytes, salt: bytes, m_cost: int, t_cost: int, parallelism: int) -> bytes:
    """
    Zwraca 32-bajtowy klucz z Argon2id.
    """
    if not isinstance(password, (bytes, bytearray)):
        raise TypeError("password must be bytes")
    if not isinstance(salt, (bytes, bytearray)):
        raise TypeError("salt must be bytes")
    return hash_secret_raw(
        secret=password,
        salt=salt,
        time_cost=t_cost,
        memory_cost=m_cost // 1024,  # argon2-cffi low_level oczekuje w KiB
        parallelism=parallelism,
        hash_len=32,
        type=Type.ID,
    )

def encrypt_bytes(plaintext: bytes, key: bytes, nonce: bytes, aad: bytes) -> tuple[bytes, bytes]:
    """
    Szyfruje całość w pamięci: zwraca (ciphertext_bez_taga, tag_16B).
    AESGCM.encrypt zwraca ciphertext||tag (tag 16B na końcu).
    """
    aes = AESGCM(key)
    ct_plus_tag = aes.encrypt(nonce, plaintext, aad)
    return ct_plus_tag[:-16], ct_plus_tag[-16:]

def decrypt_bytes(ciphertext: bytes, tag: bytes, key: bytes, nonce: bytes, aad: bytes) -> bytes:
    """
    Odszyfrowanie w pamięci; rzuca IntegrityError przy błędnym tagu/haśle.
    """
    aes = AESGCM(key)
    try:
        return aes.decrypt(nonce, ciphertext + tag, aad)
    except Exception as e:
        raise IntegrityError("GCM integrity failed (bad password or damaged file)") from e

# src/nyb/core/crypto.py
from __future__ import annotations
from argon2.low_level import hash_secret_raw, Type
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

class IntegrityError(Exception):
    pass

def derive_key_argon2id(password: bytes, salt: bytes, m_cost: int, t_cost: int, parallelism: int) -> bytes:
    if not isinstance(password, (bytes, bytearray)):
        raise TypeError("password must be bytes")
    if not isinstance(salt, (bytes, bytearray)):
        raise TypeError("salt must be bytes")
    # argon2 expects memory_cost in KiB
    return hash_secret_raw(
        secret=password,
        salt=salt,
        time_cost=t_cost,
        memory_cost=m_cost // 1024,
        parallelism=parallelism,
        hash_len=32,
        type=Type.ID,
    )

# --- wersje in-memory (zostawiamy do testów małych danych) ---

def encrypt_bytes(plaintext: bytes, key: bytes, nonce: bytes, aad: bytes) -> tuple[bytes, bytes]:
    aes = AESGCM(key)
    ct_plus_tag = aes.encrypt(nonce, plaintext, aad)
    return ct_plus_tag[:-16], ct_plus_tag[-16:]

def decrypt_bytes(ciphertext: bytes, tag: bytes, key: bytes, nonce: bytes, aad: bytes) -> bytes:
    aes = AESGCM(key)
    try:
        return aes.decrypt(nonce, ciphertext + tag, aad)
    except Exception as e:
        raise IntegrityError("GCM integrity failed (bad password or damaged file)") from e

# --- wersje strumieniowe ---

def encrypt_stream(fin, fout, key: bytes, nonce: bytes, aad: bytes, chunk_size: int) -> tuple[int, bytes]:
    """
    Strumieniowe AES-256-GCM: czyta z fin, zapisuje ciphertext do fout.
    Zwraca (liczba_bajtów_plain, tag_16B). AAD musi być ustawione PRZED update().
    Uwaga: fout dostaje TYLKO ciphertext (bez taga).
    """
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
    encryptor = cipher.encryptor()
    encryptor.authenticate_additional_data(aad)
    total = 0
    while True:
        chunk = fin.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        data = encryptor.update(chunk)
        if data:
            fout.write(data)
    encryptor.finalize()
    return total, encryptor.tag

def decrypt_stream(fin, fout, key: bytes, nonce: bytes, aad: bytes, tag: bytes, chunk_size: int) -> int:
    """
    Strumieniowe odszyfrowanie.
    W GCM tag ustawiamy w konstruktorze trybu: modes.GCM(nonce, tag).
    Zwraca liczbę bajtów plaintextu. Rzuca IntegrityError przy błędnym tagu.
    """
    try:
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag))
        decryptor = cipher.decryptor()
        decryptor.authenticate_additional_data(aad)
        total = 0
        while True:
            chunk = fin.read(chunk_size)
            if not chunk:
                break
            data = decryptor.update(chunk)
            if data:
                total += len(data)
                fout.write(data)
        decryptor.finalize()
        return total
    except Exception as e:
        raise IntegrityError("GCM integrity failed (bad password or damaged file)") from e

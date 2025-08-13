class IntegrityError(Exception): pass

def derive_key_argon2id(password: bytes, salt: bytes, m_cost: int, t_cost: int, parallelism: int) -> bytes:
    """TODO: zwróć 32B klucz (argon2id)"""
    raise NotImplementedError

def encrypt_stream(fin, fout, key: bytes, nonce: bytes, aad: bytes, chunk_size: int):
    """TODO: strumieniowe AES-256-GCM; zwróć (bytes_written, tag)"""
    raise NotImplementedError

def decrypt_stream(fin, fout, key: bytes, nonce: bytes, aad: bytes, tag: bytes, chunk_size: int):
    """TODO: strumieniowe odszyfrowanie; rzuć IntegrityError przy złym tagu"""
    raise NotImplementedError

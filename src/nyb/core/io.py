from contextlib import contextmanager

@contextmanager
def write_atomic(target_path: str, tmp_suffix: str = ".tmp"):
    """TODO: zapis do pliku tymczasowego + fsync + atomic replace"""
    raise NotImplementedError

def encrypt_path(path: str, password_source, cfg, logger):
    """TODO: integracja header + crypto + metadata + recycle"""
    raise NotImplementedError

def decrypt_path(path: str, password_source, cfg, logger):
    """TODO: integracja header + crypto + metadata + recycle"""
    raise NotImplementedError

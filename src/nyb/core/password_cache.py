class KeyCache:
    def __init__(self): self._k = None
    def set_key(self, key: bytes, ttl_seconds: int = 600): self._k = key  # TODO: TTL
    def get_key(self): return self._k
    def clear(self): self._k = None

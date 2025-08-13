MAGIC = b"NYB1"

class HeaderError(Exception): pass

def build_header_json(*, kdf_params: dict, cipher_params_no_tag: dict, meta: dict, app: dict) -> bytes:
    raise NotImplementedError

def add_tag_to_header_json(header_json: bytes, tag_b64: str) -> bytes:
    raise NotImplementedError

def pack_header(magic: bytes, header_json: bytes) -> bytes:
    raise NotImplementedError

def unpack_header(fin):
    raise NotImplementedError

def compute_aad(header_json_without_tag: bytes) -> bytes:
    raise NotImplementedError

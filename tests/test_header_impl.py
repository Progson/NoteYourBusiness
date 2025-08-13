# tests/test_header_impl.py
import io
from nyb.core import header

def sample_header():
    kdf = {"algo": "argon2id", "m": 134217728, "t": 3, "p": 1, "salt": "b64salt"}
    cipher_no_tag = {"algo": "aes-256-gcm", "nonce": "b64nonce"}
    meta = {"original_name": "plik.ext", "mtime": 1692300000, "attribs": {"ro": False, "hidden": False}}
    app = {"format": "nyb", "ver": "1.0.0"}
    return kdf, cipher_no_tag, meta, app

def test_build_and_pack_and_unpack_roundtrip():
    kdf, cipher_no_tag, meta, app = sample_header()
    hj = header.build_header_json(kdf_params=kdf, cipher_params_no_tag=cipher_no_tag, meta=meta, app=app)
    aad = header.compute_aad(hj)
    assert aad == hj  # AAD to dokładnie JSON bez taga
    packed = header.pack_header(header.MAGIC, hj)
    f = io.BytesIO(packed + b"PAYLOAD")
    obj, offset = header.unpack_header(f)
    assert obj["kdf"]["algo"] == "argon2id"
    assert obj["cipher"]["algo"] == "aes-256-gcm"
    assert offset == len(packed)

def test_add_tag_then_aad_must_fail():
    kdf, cipher_no_tag, meta, app = sample_header()
    hj = header.build_header_json(kdf_params=kdf, cipher_params_no_tag=cipher_no_tag, meta=meta, app=app)
    hj2 = header.add_tag_to_header_json(hj, tag_b64="b64tag")
    try:
        header.compute_aad(hj2)
        assert False, "Expected HeaderError when tag present"
    except header.HeaderError:
        pass

def test_pack_header_rejects_wrong_magic():
    kdf, cipher_no_tag, meta, app = sample_header()
    hj = header.build_header_json(kdf_params=kdf, cipher_params_no_tag=cipher_no_tag, meta=meta, app=app)
    try:
        header.pack_header(b"BAD!", hj)
        assert False, "Expected HeaderError for bad magic"
    except header.HeaderError:
        pass

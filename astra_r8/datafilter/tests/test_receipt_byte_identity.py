"""A receipt digest must identify the bytes actually parsed by the verifier."""
import json
from pathlib import Path

import pytest

import seal_admission as seal


def test_temporary_receipt_substitution_cannot_bind_to_restored_bytes(tmp_path, monkeypatch):
    path = tmp_path/'SUMMARY.json'
    original = b'{"status":"FAIL"}'
    replacement = b'{"status":"PASS"}'
    path.write_bytes(original)
    read_text, read_bytes = Path.read_text, Path.read_bytes

    def transient(method):
        def read(supplied, *args, **kwargs):
            if supplied != path:
                return method(supplied, *args, **kwargs)
            supplied.write_bytes(replacement)
            try:
                return method(supplied, *args, **kwargs)
            finally:
                supplied.write_bytes(original)
        return read

    monkeypatch.setattr(Path, 'read_text', transient(read_text))
    monkeypatch.setattr(Path, 'read_bytes', transient(read_bytes))
    bound = seal.BoundInputs()
    with pytest.raises(ValueError, match='receipt changed'):
        bound.read(path)
    assert read_bytes(path) == original
    assert not bound.files


def test_unchanged_receipt_binds_the_digest_of_exact_parsed_bytes(tmp_path):
    path = tmp_path/'SUMMARY.json'
    payload = b'\xef\xbb\xbf{ "status": "PASS" }\r\n'
    path.write_bytes(payload)
    bound = seal.BoundInputs()
    assert bound.read(path) == json.loads(payload)
    assert bound.files == {str(path.resolve()): seal.sha256(path)}
    bound.verify()

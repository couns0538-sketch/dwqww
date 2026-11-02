"""Owned-child timeout diagnostics survive failed native compatibility probes."""
import json
import subprocess

import chess
import pytest
import native_forge_smoke as smoke


def test_timeout_preserves_captured_diagnostics(tmp_path, monkeypatch):
    sample = tmp_path / 'sample.jsonl'
    sample.write_text(json.dumps({'fen': chess.STARTING_FEN}) + '\n')
    output = tmp_path / 'native'
    monkeypatch.setattr(smoke, 'storage_guard', lambda *a, **kw: None)
    monkeypatch.setattr(smoke, 'sha256', lambda path: smoke.LOCK)

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs['timeout'],
                                        output=b'partial output\xff', stderr=b'timeout stderr')

    monkeypatch.setattr(smoke.subprocess, 'run', timeout)
    with pytest.raises(subprocess.TimeoutExpired):
        smoke.run(output, sample)
    assert (output / 'stdout.log').read_text(encoding='utf-8') == 'partial output\ufffd'
    assert (output / 'stderr.log').read_text(encoding='utf-8') == 'timeout stderr'
    receipt = json.loads((output / 'report.json').read_text())
    assert receipt['status'] == 'FAIL'
    assert receipt['reason'] == 'engine timeout'
    assert receipt['timeout_seconds'] == 120

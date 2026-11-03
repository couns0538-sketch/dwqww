"""Owned-child timeout diagnostics survive failed native compatibility probes."""
import json
import subprocess
import re
from types import SimpleNamespace

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


def fake_lock(tmp_path, monkeypatch):
    engine = tmp_path/'fixture_engine.exe'
    engine.write_bytes(b'fixture, never executed')
    original_hash = smoke.sha256
    monkeypatch.setattr(smoke, 'ENGINE', engine)
    monkeypatch.setattr(smoke, 'sha256', lambda path: smoke.LOCK if path == engine else original_hash(path))


def healthy_reply(request):
    fens = re.findall(r'^position fen (.+)$', request, re.M)
    counts = [smoke.perft2(chess.Board(fen)) for fen in fens]
    text = ''.join(f'nodes {n}\n' for n in counts)
    text += ''.join(f'bench depth {d} nodes {n}\n' for d,n in smoke.PINS.items())
    return SimpleNamespace(returncode=0, stdout=text, stderr='')


def test_changed_sample_cannot_be_attributed_to_tested_fens(tmp_path, monkeypatch):
    fake_lock(tmp_path, monkeypatch)
    sample = tmp_path/'sample.jsonl'
    original = json.dumps({'fen':chess.STARTING_FEN})+'\n'
    sample.write_text(original)
    def mutate(*args, **kwargs):
        sample.write_text(original+original)
        return healthy_reply(kwargs['input'])
    monkeypatch.setattr(smoke.subprocess, 'run', mutate)
    with pytest.raises(ValueError):
        smoke.run(tmp_path/'native', sample)
    receipt = json.loads((tmp_path/'native/report.json').read_text())
    assert receipt['status'] == 'FAIL'


@pytest.mark.parametrize('fen', ['', '8/8/8/8/8/8/8/8 w - - 0 1',
                                 chess.STARTING_FEN.replace(' ', '\n', 1),
                                 chess.STARTING_FEN.rsplit(' ',1)[0]+' 0'])
def test_empty_invalid_or_multiline_sample_never_launches_engine(tmp_path, monkeypatch, fen):
    fake_lock(tmp_path, monkeypatch)
    sample = tmp_path/'sample.jsonl'
    sample.write_text('' if not fen else json.dumps({'fen':fen})+'\n')
    def refuse(*args, **kwargs):
        raise AssertionError('invalid sample reached the engine')
    monkeypatch.setattr(smoke.subprocess, 'run', refuse)
    with pytest.raises(ValueError):
        smoke.run(tmp_path/'native', sample)


def test_explicit_sample_limit_and_default_preserved(tmp_path, monkeypatch):
    fake_lock(tmp_path, monkeypatch)
    sample = tmp_path/'sample.jsonl'
    sample.write_text((json.dumps({'fen':chess.STARTING_FEN})+'\n')*30)
    monkeypatch.setattr(smoke.subprocess, 'run', lambda *a,**kw:healthy_reply(kw['input']))
    default = smoke.run(tmp_path/'default', sample)
    bounded = smoke.run(tmp_path/'bounded', sample, max_positions=30)
    assert default['positions'] == 62
    assert bounded['positions'] == 74
    assert bounded['sample_positions'] == 30


@pytest.mark.parametrize('limit', [0, -1, True, 1.5, 10001])
def test_invalid_sample_limit_rejected_before_output(tmp_path, limit):
    with pytest.raises(ValueError):
        smoke.run(tmp_path/'native', tmp_path/'missing.jsonl', max_positions=limit)
    assert not (tmp_path/'native').exists()

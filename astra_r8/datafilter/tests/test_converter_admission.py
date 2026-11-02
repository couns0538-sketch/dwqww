"""Result-aware conversion rejects bad configuration, inputs and changing sources."""
import json
from pathlib import Path
import runpy
import sys

import pytest

from filter_positions import sha256
from test_converter import positions

HERE = Path(__file__).resolve().parents[1]


def convert(monkeypatch, source, output, *extra):
    monkeypatch.setattr(sys, 'argv', [str(HERE/'convert_forge.py'), str(output),
                                    '--selfplay', str(source), '--keep-result', *extra])
    runpy.run_path(str(HERE/'convert_forge.py'), run_name='__main__')


def valid_source(tmp_path):
    source = tmp_path/'rows.txt'
    lines = [f'{fen} | {white if " w " in fen else -white} | 1' for fen, white in positions()]
    source.write_text('\n'.join(lines)+'\n')
    return source


@pytest.mark.parametrize('args', [
    ('--clip', '-1'), ('--clip', '0'), ('--clip', '32768'),
    ('--val', '-0.1'), ('--val', '1'), ('--val', 'nan'), ('--val', 'inf'),
    ('--seed', '-1'), ('--max-pieces', '1'), ('--max-pieces', '33'),
    ('--min-depth', '-1'),
])
def test_invalid_configuration_before_source_read(tmp_path, monkeypatch, args):
    with pytest.raises(SystemExit) as error:
        convert(monkeypatch, tmp_path/'missing.txt', tmp_path/'output', *args)
    assert error.value.code == 2
    assert not (tmp_path/'output').exists()
    assert not (tmp_path/'output.partial').exists()


@pytest.mark.parametrize('bad', ['not a position', '4k3/8/8/8/8/8/8/8 w - - 0 1 | 0 | 0.5'])
def test_bad_selfplay_cannot_be_silently_skipped(tmp_path, monkeypatch, bad):
    source = valid_source(tmp_path)
    with source.open('a') as fh:
        fh.write(bad+'\n')
    with pytest.raises(ValueError):
        convert(monkeypatch, source, tmp_path/'output')
    assert not (tmp_path/'output').exists()


def test_result_converter_binds_source_identity(tmp_path, monkeypatch):
    source = valid_source(tmp_path)
    convert(monkeypatch, source, tmp_path/'output')
    stats = json.loads((tmp_path/'output/stats.json').read_text())
    identity = stats['source_identities'][0]
    assert identity['sha256'] == sha256(source)
    assert Path(identity['path']) == source
    assert identity['bytes'] == source.stat().st_size


def test_source_mutation_before_publication_is_rejected(tmp_path, monkeypatch):
    import filter_lichess_rec
    source = valid_source(tmp_path)
    original = filter_lichess_rec.encode_board
    mutated = False

    def mutate(*args, **kwargs):
        nonlocal mutated
        if not mutated:
            with source.open('a') as fh:
                fh.write('# injected fixture mutation\n')
            mutated = True
        return original(*args, **kwargs)

    monkeypatch.setattr(filter_lichess_rec, 'encode_board', mutate)
    with pytest.raises(ValueError, match='source changed'):
        convert(monkeypatch, source, tmp_path/'output')
    assert mutated and not (tmp_path/'output').exists()


def test_retargeted_source_alias_is_rejected(tmp_path, monkeypatch):
    import filter_lichess_rec
    source = valid_source(tmp_path)
    second = tmp_path/'other.txt'
    second.write_text(source.read_text().replace('| 1\n', '| 0\n'))
    alias = tmp_path/'source_alias.txt'
    try:
        alias.symlink_to(source)
    except OSError as exc:
        pytest.skip(f'host cannot create the owned fixture symlink: {exc}')
    original = filter_lichess_rec.encode_board
    changed = False

    def retarget(*args, **kwargs):
        nonlocal changed
        if not changed:
            alias.unlink()  # Only the link created above; both fixture sources remain.
            alias.symlink_to(second)
            changed = True
        return original(*args, **kwargs)

    monkeypatch.setattr(filter_lichess_rec, 'encode_board', retarget)
    with pytest.raises(ValueError, match='source changed'):
        convert(monkeypatch, alias, tmp_path/'output')
    assert changed and source.is_file() and second.is_file()
    assert not (tmp_path/'output').exists()


@pytest.mark.parametrize('change', ['stats', 'extra', None])
def test_identity_guard_covers_every_output_file(tmp_path, change):
    from audit import compare_legacy_artifacts
    for name in ('old', 'new'):
        directory = tmp_path/name
        directory.mkdir()
        for filename, content in [('train.bin', b'train'), ('val.bin', b'val'), ('stats.json', b'{}')]:
            (directory/filename).write_bytes(content)
    if change == 'stats':
        (tmp_path/'new/stats.json').write_bytes(b'{"unexpected":true}')
    elif change == 'extra':
        (tmp_path/'new/extra.json').write_bytes(b'{}')
    if change:
        with pytest.raises(ValueError, match='artifacts differ'):
            compare_legacy_artifacts(tmp_path/'old', tmp_path/'new')
    else:
        assert set(compare_legacy_artifacts(tmp_path/'old', tmp_path/'new')) == {'train.bin', 'val.bin', 'stats.json'}

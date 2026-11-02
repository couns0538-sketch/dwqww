"""Fail-closed parsing, source identity, and publication regressions."""
import json
from pathlib import Path
import runpy
import sys

import chess
import pytest

import filter_positions as filters
from records import dumps, lichess_record, read_records, record

HERE = Path(__file__).resolve().parents[1]


def pgn_fixture(path, *, malformed=False, ending='1-0'):
    games = []
    for placement, white in [('7k/8/8/8/4Q3/8/8/K7', 900),
                             ('7k/8/8/3q4/8/8/8/K7', -900)]:
        for turn in ('w', 'b'):
            fen = f'{placement} {turn} - - 17 81'
            board = chess.Board(fen)
            move = next(m for m in board.legal_moves if not board.is_capture(m) and not m.promotion)
            score = white if board.turn else -white
            number = '81.' if board.turn else '81...'
            games.append(f'[SetUp "1"]\n[FEN "{fen}"]\n[Result "1-0"]\n\n'
                         f'{number} {board.san(move)} {{{score / 100:+.2f}/12}} '
                         f'{"Qa1 " if malformed else ""}{ending}\n')
    path.write_text('\n'.join(games), encoding='utf-8')
    return path


def converter(source, out, monkeypatch, *, keep_result=True):
    args = [str(HERE / 'convert_forge.py'), str(out), '--pgn', str(source)]
    if keep_result:
        args.append('--keep-result')
    monkeypatch.setattr(sys, 'argv', args)
    runpy.run_path(str(HERE / 'convert_forge.py'), run_name='__main__')


def test_result_converter_rejects_malformed_pgn_before_publication(tmp_path, monkeypatch):
    source = pgn_fixture(tmp_path / 'bad.pgn', malformed=True)
    with pytest.raises(ValueError, match='malformed PGN'):
        converter(source, tmp_path / 'out', monkeypatch)
    assert not (tmp_path / 'out').exists()


@pytest.mark.parametrize('ending', ['0-1', '*'])
def test_result_converter_rejects_conflicting_result(tmp_path, monkeypatch, ending):
    source = pgn_fixture(tmp_path / 'bad.pgn', ending=ending)
    with pytest.raises(ValueError, match='result'):
        converter(source, tmp_path / 'out', monkeypatch)
    assert not (tmp_path / 'out').exists()


@pytest.mark.parametrize('header,ending,expected', [
    ('1-0', '0-1', None), ('1-0', '*', None), ('*', '0-1', -1),
    ('*', '*', None), ('1/2-1/2', '1/2-1/2', 0),
])
def test_normalized_pgn_result_consistency(tmp_path, header, ending, expected):
    source = tmp_path / 'result.pgn'
    source.write_text(f'[Result "{header}"]\n\n1. e4 {{+0.20/10}} {ending}\n')
    if header != '*' and ending != header:
        with pytest.raises(ValueError, match='result'):
            list(read_records(source, 'pgn'))
    else:
        assert [r['result_white'] for r in read_records(source, 'pgn')] == [expected]


@pytest.mark.parametrize('kind', ['cp', 'mate'])
@pytest.mark.parametrize('turn', ['w', 'b'])
def test_lichess_boolean_scores_rejected_before_orientation(kind, turn):
    obj = {'fen': chess.STARTING_FEN.replace(' w ', f' {turn} '),
           'evals': [{'pvs': [{kind: True}]}]}
    with pytest.raises(ValueError, match='score'):
        lichess_record(obj, 'fixture', 1)


def test_filter_rejects_complete_record_truncation_before_publication(tmp_path, monkeypatch):
    row = record(chess.STARTING_FEN, 0, 'cp', None, 'fixture', 1, 'selfplay')
    line = (dumps(row) + '\n').encode()
    source = tmp_path / 'source.jsonl'
    source.write_bytes(line * 4300)
    original = filters.storage_guard
    mutated = False

    def mutate(destination=None, allowance=64 * 1024 * 1024):
        nonlocal mutated
        result = original(destination, allowance)
        if (not mutated and Path(destination).name == 'out.partial'
                and allowance != 64 * 1024 * 1024):
            with source.open('r+b') as fh:
                fh.truncate(len(line) * 4200)
            mutated = True
        return result

    monkeypatch.setattr(filters, 'storage_guard', mutate)
    with pytest.raises(ValueError, match='source changed'):
        filters.run_filter(source, tmp_path / 'out')
    assert mutated and not (tmp_path / 'out').exists()
    assert (tmp_path / 'out.partial').is_dir()


def test_filter_receipt_binds_complete_input(tmp_path):
    source = tmp_path / 'source.jsonl'
    source.write_bytes((dumps(record(chess.STARTING_FEN, 0, 'cp', None,
                                   'fixture', 1, 'selfplay')) + '\n').encode())
    report = filters.run_filter(source, tmp_path / 'out')
    assert report['input_identity']['sha256'] == filters.sha256(source)
    assert report['input_identity']['bytes'] == source.stat().st_size
    assert (tmp_path / 'out/records.jsonl').read_bytes() == source.read_bytes()


def test_converter_late_failure_stays_unpublished(tmp_path, monkeypatch):
    source = pgn_fixture(tmp_path / 'valid.pgn')
    def fail(*args, **kwargs):
        raise OSError('injected stats write failure')
    monkeypatch.setattr(json, 'dump', fail)
    with pytest.raises(OSError, match='stats write'):
        converter(source, tmp_path / 'out', monkeypatch)
    assert not (tmp_path / 'out').exists()
    assert (tmp_path / 'out.partial/train.bin').is_file()


def test_converter_existing_partial_refused_before_reading(tmp_path, monkeypatch):
    partial = tmp_path / 'out.partial'
    partial.mkdir()
    (partial / 'sentinel').write_bytes(b'preserve')
    with pytest.raises(SystemExit, match='existing output'):
        converter(tmp_path / 'missing.pgn', tmp_path / 'out', monkeypatch)
    assert not (tmp_path / 'out').exists()
    assert (partial / 'sentinel').read_bytes() == b'preserve'
def test_capture_reader_rejects_conflicting_game_result(tmp_path):
    import audit_capture_cohort as c
    p=tmp_path/'conflict_capture.pgn'
    p.write_text('[Event "forge_fixture"]\n[White "'+c.BASELINE_NAME+'"]\n[Black "other"]\n'
                 '[Result "1-0"]\n[Termination "normal"]\n\n1. e4 {+0.20/12} 0-1\n')
    source={'files':{'pgn':{'path':str(p)}},'games_consumed':0,'candidate_name':'other',
            'gate':'fixture','baseline_without_positive_depth_score':0}
    with pytest.raises(ValueError,match='conflicting'):
        list(c.searched_rows(source))

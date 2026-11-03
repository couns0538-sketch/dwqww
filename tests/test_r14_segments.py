import hashlib
import importlib.util
from pathlib import Path
import struct
import sys

import chess
import pytest

TOOLS = Path('D:/a14/tools')
sys.path.insert(0, str(TOOLS))
from r14_scan import parse_row


@pytest.fixture(scope='module')
def module():
    spec = importlib.util.spec_from_file_location('r14_segments', TOOLS / 'r14_segments.py')
    result = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = result
    spec.loader.exec_module(result)
    return result


def rows(module, tokens=('e2e4', 'e7e5', 'g1f3'), source=13):
    board = chess.Board()
    result = []
    for index in range(len(tokens) + 1):
        if index:
            board.push_uci(tokens[index - 1])
        row = parse_row((board.fen(en_passant='fen') + ' | 0 | 0.5\n').encode())
        result.append(module.SourceRecord(source, index + 1, row, index > 0, True))
    return result


def oracle(lines):
    results = []
    for line in lines:
        ident, a, ra, b, rb, k, cap = line.split('\t')
        start, target = chess.Board(a), chess.Board(b)
        delta = target.ply() - start.ply()
        witness = []
        nodes = 0
        if ra != rb:
            status, reason = 'UNREACHABLE', 'result_mismatch'
        elif delta <= 0:
            status, reason = 'UNREACHABLE', 'nonpositive_ply_gap'
        elif delta > int(k):
            status, reason = 'UNKNOWN', 'gap_exceeds_k'
        elif delta == 1:
            status, reason = 'UNREACHABLE', 'exhaustive_no_path'
            nodes = 1
            for move in start.legal_moves:
                child = start.copy()
                child.push(move)
                nodes += 1
                if child.fen(en_passant='fen') == target.fen(en_passant='fen'):
                    witness = [move.uci()]
                    status, reason = 'REACHABLE', 'legal_witness'
                    break
        else:
            status, reason, nodes = 'UNKNOWN', 'node_limit', int(cap)
        results.append(dict(id=ident, status=status, reason=reason, nodes=nodes, witness=witness))
    return results


def test_contiguous_chain_range_and_events(module):
    records = rows(module)
    events = list(module.scan_pairs(records, oracle))
    assert [event.code for event in events] == [250, 0, 0, 0]
    saved = []
    assembly = module.SegmentAssembler(lambda source, record: saved.append((source, record)))
    for event in events:
        assembly.add(event)
    assembly.close()
    assert saved == [(13, (1, 4, 1, 250))]


def test_scope_gap_is_unknown_not_a_certified_boundary(module):
    records = rows(module)
    records[2] = module.SourceRecord(13, 100, records[2].row, False, True)
    records[3] = module.SourceRecord(13, 101, records[3].row, True, True)
    events = list(module.scan_pairs(records, oracle))
    assert events[2].code == 251 and not events[2].adjacent
    assert events[2].status == 'UNKNOWN'


def test_injected_straddle_fails_fixture_audit(module):
    records = rows(module)
    games = {(r.source_id, r.line): 'authentic-fixture-game' for r in records}
    splits = {(r.source_id, r.line): ('train' if r.line < 3 else 'val') for r in records}
    result = module.fixture_audit(records, list(module.scan_pairs(records, oracle)), games, splits)
    assert result['status'] == 'FAIL'
    assert 'game_crosses_splits' in result['reasons']


def test_shuffled_file_fails_fixture_audit(module):
    original = rows(module)
    records = [module.SourceRecord(13, i + 1, original[j].row, i > 0, True) for i, j in enumerate((0, 2, 1, 3))]
    games = {(r.source_id, r.line): 'authentic-fixture-game' for r in records}
    splits = {key: 'train' for key in games}
    result = module.fixture_audit(records, list(module.scan_pairs(records, oracle)), games, splits)
    assert result['status'] == 'FAIL'
    assert 'broken_authentic_chain' in result['reasons']


def test_mismatched_result_fails_fixture_audit(module):
    records = rows(module)
    row = parse_row((records[1].row.fen + ' | 0 | 1.0').encode())
    records[1] = module.SourceRecord(13, 2, row, True, True)
    games = {(r.source_id, r.line): 'authentic-fixture-game' for r in records}
    result = module.fixture_audit(records, list(module.scan_pairs(records, oracle)), games, {key: 'train' for key in games})
    assert result['status'] == 'FAIL'


def test_gap_above_k_remains_unknown(module):
    records = rows(module, ('e2e4','e7e5','g1f3','b8c6','f1c4','g8f6','d2d3','f8c5','b1c3'))
    pair = [records[0], module.SourceRecord(13, 2, records[-1].row, True, True)]
    events = list(module.scan_pairs(pair, oracle))
    assert events[1].code == 4 and events[1].status == 'UNKNOWN'


def test_missing_row_preserves_unknown_coverage(module):
    records = rows(module)
    records[1] = module.SourceRecord(13, 2, None, True, True)
    events = list(module.scan_pairs(records, oracle))
    assert [event.code for event in events] == [250, 7, 7, 0]


def test_source_seam_continuation_reuses_global_id(module):
    records = rows(module)
    records = records[:2] + [module.SourceRecord(14, i + 1, row.row, True, True) for i, row in enumerate(records[2:])]
    events = list(module.scan_pairs(records, oracle))
    saved = []
    assembly = module.SegmentAssembler(lambda source, record: saved.append((source, record)))
    for event in events:
        assembly.add(event)
    assembly.close()
    assert saved == [(13, (1, 2, 1, 250)), (14, (1, 2, 1, 0))]


def test_transport_truncation_is_never_silently_zipped(module):
    with pytest.raises(module.TransportFailure):
        list(module.scan_pairs(rows(module), lambda lines: oracle(lines)[:-1]))


def test_edges_and_prefix_hash_entire_source(module, tmp_path):
    records = rows(module)
    data = b''.join((r.row.fen + ' | 0 | 0.5\n').encode() for r in records)
    path = tmp_path / 'source.txt'
    path.write_bytes(data)
    receipt = {}
    spec = module.SourceSpec(13, 13, path, hashlib.md5(data).hexdigest(), 'edges', 1, None)
    selected = list(module.select_source(spec, receipt))
    assert [r.line for r in selected] == [1, 4]
    assert not selected[1].contiguous
    assert receipt['complete'] and receipt['rows'] == 4
    receipt = {}
    spec = module.SourceSpec(1, 2, path, hashlib.md5(data).hexdigest(), 'prefix', 3, 2)
    selected = list(module.select_source(spec, receipt))
    assert [r.line for r in selected] == [1, 2, 3]
    assert [r.selected for r in selected] == [True, True, False]
    assert receipt['complete'] and receipt['rows'] == 4


def test_binary_layout_is_exact(module):
    assert module.RANGE_STRUCT.format == '<IIQB'
    assert module.RANGE_STRUCT.size == 17
    assert module.PAIR_STRUCT.format == '<IBI'
    assert module.PAIR_STRUCT.size == 9
    assert module.RANGE_STRUCT.unpack(module.RANGE_STRUCT.pack(1, 20, 5, 250)) == (1, 20, 5, 250)


def test_qualification_rejects_smoke_and_foundation_shortfall(module):
    with pytest.raises(ValueError):
        module.validate_qualification({'status': 'UNVERIFIED', 'scope': 'qualification_smoke'}, {})


def test_fixture_audit_missing_pair_coverage_is_unverified(module):
    records = rows(module)
    games = {(r.source_id, r.line): 'game' for r in records}
    events = list(module.scan_pairs(records, oracle))[:-1]
    result = module.fixture_audit(records, events, games, {key: 'train' for key in games})
    assert result['status'] == 'UNVERIFIED'
    assert result['event_coverage_complete'] is False


def test_fixture_audit_empty_input_is_unverified(module):
    assert module.fixture_audit([], [], {}, {})['status'] == 'UNVERIFIED'


def test_source_id_cannot_recur_after_another_source(module):
    original = rows(module)
    records = [original[0], module.SourceRecord(14, 1, original[1].row, True),
               module.SourceRecord(13, 2, original[2].row, True)]
    with pytest.raises(ValueError, match='source identity'):
        list(module.scan_pairs(records, oracle))


def test_window_scope_openness_is_explicit(module, tmp_path):
    records = rows(module)
    data = b''.join((r.row.fen + ' | 0 | 0.5\n').encode() for r in records)
    path = tmp_path / 'source.txt'
    path.write_bytes(data)
    receipt = {}
    list(module.select_source(module.SourceSpec(13, 13, path, hashlib.md5(data).hexdigest(), 'edges', 1), receipt))
    assert receipt['chain_windows'] == [
        dict(first_line=1, last_line=1, open_left=False, open_right=True),
        dict(first_line=4, last_line=4, open_left=True, open_right=False)]


def test_map_writer_rejects_unknown_stream_kind(module, tmp_path):
    writer = module.MapWriter(tmp_path / 'maps', lambda: None)
    try:
        with pytest.raises(ValueError):
            writer.append(13, 'typo', (1, 250, 0))
    finally:
        writer.close()


def test_map_abort_does_not_flush_buffered_data(module, tmp_path):
    writer = module.MapWriter(tmp_path / 'maps', lambda: None)
    writer.append(13, 'pairs', (1, 250, 0))
    path = next((tmp_path / 'maps').glob('*.bin'))
    assert path.stat().st_size == 0
    writer.abort()
    assert path.stat().st_size == 0
    assert not writer.artifacts


def test_map_parts_preserve_exact_record_counts_and_hashes(module, tmp_path):
    writer = module.MapWriter(tmp_path / 'maps', lambda: None, chunk_bytes=34)
    expected = [(1, 2, 1, 250), (3, 3, 2, 1), (4, 9, 3, 3)]
    for record in expected:
        writer.append(13, 'ranges', record)
    writer.close()
    assert [item['records'] for item in writer.artifacts] == [2, 1]
    assert [item['bytes'] for item in writer.artifacts] == [34, 17]
    assert list(module.iter_ranges([item['path'] for item in writer.artifacts])) == expected
    for item in writer.artifacts:
        assert hashlib.md5(Path(item['path']).read_bytes()).hexdigest() == item['md5']


def test_prefix_unscanned_tail_still_checks_pin(module, tmp_path):
    records = rows(module)
    data = b''.join((r.row.fen + ' | 0 | 0.5\n').encode() for r in records)
    path = tmp_path / 'source.txt'
    path.write_bytes(data)
    receipt = {}
    with pytest.raises(ValueError, match='hash mismatch'):
        list(module.select_source(module.SourceSpec(1, 2, path, '0' * 32, 'prefix', 1), receipt))


def test_transport_reordered_ids_and_invalid_nodes_fail(module):
    def wrong_ids(lines):
        replies = oracle(lines)
        return list(reversed(replies))
    with pytest.raises(module.TransportFailure):
        list(module.scan_pairs(rows(module), wrong_ids))
    def wrong_nodes(lines):
        replies = oracle(lines)
        replies[0]['nodes'] = True
        return replies
    with pytest.raises(module.TransportFailure):
        list(module.scan_pairs(rows(module), wrong_nodes))


@pytest.mark.parametrize('move', ['e2e5', 'd2d4'])
def test_positive_witness_must_be_legal_and_reach_exact_target(module, move):
    records = rows(module, ('e2e4',))
    def forged(lines):
        reply = oracle(lines)[0]
        reply['witness'] = [move]
        return [reply]
    with pytest.raises(module.TransportFailure, match='witness'):
        list(module.scan_pairs(records, forged))


@pytest.mark.parametrize('field,value', [(4, '1'), (3, '-')])
def test_positive_witness_must_match_clocks_and_raw_ep(module, field, value):
    records = rows(module, ('e2e4',))
    fields = records[1].row.fen.split()
    fields[field] = value
    changed = parse_row((' '.join(fields) + ' | 0 | 0.5').encode())
    records[1] = module.SourceRecord(13, 2, changed, True)
    def forged(lines):
        return [dict(id=lines[0].split('\t')[0], status='REACHABLE', reason='legal_witness',
                     nodes=2, witness=['e2e4'])]
    with pytest.raises(module.TransportFailure, match='witness'):
        list(module.scan_pairs(records, forged))


def qualified_report():
    identity = dict(path='D:/a14/tools/r14_native/build/chain_native_r03.exe', md5='a'*32, sha256='b'*64)
    report = dict(schema=1, status='PASS', complete=True, scope='production_helper_qualification',
                  requested_pairs=1000000, resolved_pairs=1000050, disagreements=0, unknown_pairs=20,
                  native_exe=identity['path'], native_md5=identity['md5'], native_sha256=identity['sha256'],
                  requested=dict(deep_per_depth=3, exhaustive_negatives=2),
                  by_stratum=dict(one_ply=dict(resolved=1000000), deep_positive=dict(attempted=21),
                                  exhaustive_negative=dict(attempted=2)))
    return report, identity


def test_qualification_foundation_cannot_be_compensated_by_extras(module):
    report, identity = qualified_report()
    report['by_stratum']['one_ply']['resolved'] -= 1
    with pytest.raises(ValueError, match='foundation'):
        module.validate_qualification(report, identity)


@pytest.mark.parametrize('field', ['native_md5', 'native_sha256', 'native_exe'])
def test_qualification_requires_exact_native_identity(module, field):
    report, identity = qualified_report()
    report[field] = 'different'
    with pytest.raises(ValueError, match='identity|path'):
        module.validate_qualification(report, identity)


@pytest.mark.parametrize('stratum', ['deep_positive', 'exhaustive_negative'])
def test_qualification_requires_complete_extra_attempts(module, stratum):
    report, identity = qualified_report()
    report['by_stratum'][stratum]['attempted'] -= 1
    with pytest.raises(ValueError, match='incomplete'):
        module.validate_qualification(report, identity)


def test_qualification_allows_separately_reported_deep_unknowns(module):
    report, identity = qualified_report()
    assert module.validate_qualification(report, identity) is report

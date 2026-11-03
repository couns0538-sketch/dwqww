import hashlib

import pytest

from r14_group_map import Prepared, Segment, audit_groups, iter_prepared, join_sources
from r14_scan import parse_row

FEN = '4k3/8/8/8/8/8/8/4K3 w - - 0 2'
HEADER = 'row_id\tgame_id\tsplit\tfen\told_score_stm\tresult\tsource\tsource_row\n'


def record(row_id, group, split, line, source=0):
    return Prepared(row_id, group, split, source, line, parse_row((FEN+' | 0 | .5').encode()))


def test_group_spanning_proven_break_is_a_mismatch():
    ranges = {0: [Segment(1, 2, 1, 'source_start'), Segment(3, 4, 2, 'UNREACHABLE')]}
    result = audit_groups([record(i, 'g', 'train', i+1) for i in range(4)], ranges)
    assert result['comparison_status'] == 'FAIL'
    assert result['group_count'] == 1
    assert result['definite_fragmented_groups'] == 1
    assert result['groups'][0]['segments'] == [1, 2]
    assert result['authentic_game_ids'] == 'UNVERIFIED'


def test_group_spanning_unknown_is_never_proven_mismatch_or_pass():
    ranges = {0: [Segment(1, 2, 1, 'source_start'), Segment(3, 4, 2, 'UNKNOWN')]}
    result = audit_groups([record(i, 'g', 'train', i+1) for i in range(4)], ranges)
    assert result['comparison_status'] == 'UNVERIFIED'
    assert result['unknown_fragmented_groups'] == 1
    assert result['definite_fragmented_groups'] == 0


@pytest.mark.parametrize('reasons', [('UNREACHABLE', 'UNKNOWN'), ('UNKNOWN', 'UNREACHABLE')])
def test_omitted_whole_segment_does_not_hide_a_proven_break(reasons):
    ranges = {0: [Segment(1, 2, 1, 'source_start'), Segment(3, 4, 2, reasons[0]),
                  Segment(5, 6, 3, reasons[1])]}
    result = audit_groups([record(0, 'g', 'train', 1), record(1, 'g', 'train', 5)], ranges)
    assert result['comparison_status'] == 'FAIL'
    assert result['definite_fragmented_groups'] == 1
    assert result['unknown_fragmented_groups'] == 1
    assert {b['segment'] for b in result['groups'][0]['definite_breaks']+result['groups'][0]['unknown_breaks']} == {2, 3}


def test_split_groups_in_one_chain_report_all_members_and_leak():
    rows = [record(0, 'a', 'train', 1), record(1, 'b', 'val', 2), record(2, 'c', 'train', 3)]
    result = audit_groups(rows, {0: [Segment(1, 3, 11, 'source_start')]})
    assert result['comparison_status'] == 'FAIL'
    assert result['segments_with_multiple_groups'] == 1
    assert result['segments_shared_between_splits'] == 1
    assert result['shared_segments'][0]['groups'] == ['a', 'b', 'c']


def test_missing_mapping_reports_fill_rate_next_to_zero_links():
    result = audit_groups([record(0, 'g', 'train', 4)], {0: [Segment(1, 3, 1, 'source_start')]})
    assert result['comparison_status'] == 'UNVERIFIED'
    assert result['mapped_rows'] == 0 and result['mapping_fill_rate'] == 0
    assert result['segments_shared_between_splits'] == 0


def test_exact_observed_match_does_not_authenticate_a_game():
    result = audit_groups([record(0, 'g', 'train', 1)], {0: [Segment(1, 1, 1, 'source_start')]})
    assert result['comparison_status'] == 'PASS'
    assert result['authentic_game_ids'] == 'UNVERIFIED'
    assert result['export_allowed'] is False


def test_one_group_with_multiple_splits_fails_even_without_link():
    result = audit_groups([record(0, 'g', 'train', 1), record(1, 'g', 'val', 2)],
                          {0: [Segment(1, 1, 1, 'source_start'), Segment(2, 2, 2, 'UNKNOWN')]})
    assert result['comparison_status'] == 'FAIL'
    assert result['groups_with_multiple_splits'] == 1


def test_missing_prepared_row_is_not_silently_dropped():
    result = audit_groups([record(0, 'g', 'train', 1), None], {0: [Segment(1, 1, 1, 'source_start')]})
    assert result['rows'] == 2 and result['valid_prepared_rows'] == 1
    assert result['mapping_fill_rate'] == .5
    assert result['comparison_status'] == 'UNVERIFIED'


def test_prepared_stream_hash_and_invalid_location(tmp_path):
    path = tmp_path/'rows.tsv'
    data = (HEADER+f'0\tg\ttrain\t{FEN}\t0\t0.5\t0\t1\n'+f'1\tg\ttrain\t{FEN}\t0\t0.5\t0\t1\n').encode()
    path.write_bytes(data)
    receipt = {}
    rows = list(iter_prepared(path, hashlib.md5(data).hexdigest(), receipt))
    assert rows[0].source_line == 1 and rows[1] is None
    assert receipt['complete'] and receipt['key_fill_rate'] == .5


def test_prepared_pin_mismatch_refused(tmp_path):
    path = tmp_path/'rows.tsv'
    path.write_text(HEADER+f'0\tg\ttrain\t{FEN}\t0\t0.5\t0\t1\n')
    with pytest.raises(ValueError, match='hash mismatch'):
        list(iter_prepared(path, '0'*32, {}))


def test_range_overlap_and_duplicate_id_refused():
    with pytest.raises(ValueError, match='range'):
        audit_groups([], {0: [Segment(1, 3, 1, 'source_start'), Segment(3, 5, 2, 'UNKNOWN')]})
    with pytest.raises(ValueError, match='identity'):
        audit_groups([], {0: [Segment(1, 2, 1, 'source_start'), Segment(3, 4, 1, 'UNKNOWN')]})


def test_source_join_consumes_omitted_rows_and_full_tail(tmp_path):
    paths, pins = {}, {}
    for source, count in ((0, 4), (1, 5)):
        path = tmp_path/f'source{source}.txt'
        data = ((FEN+' | 0 | .5\n')*count).encode()
        path.write_bytes(data)
        paths[source] = path
        pins[str(path.resolve()).casefold()] = hashlib.md5(data).hexdigest()
    receipt = {}
    selected = [record(0, 'a', 'train', 2), record(1, 'b', 'val', 3, 1)]
    assert list(join_sources(selected, paths, pins, receipt)) == selected
    assert receipt['matched_rows'] == 2 and receipt['source_join_fill_rate'] == 1
    assert [r['rows'] for r in receipt['sources']] == [4, 5]
    assert receipt['complete'] is True


def test_source_join_mismatch_and_missing_row_never_count_as_filled(tmp_path):
    path = tmp_path/'source.txt'
    data = (FEN+' | 9 | .5\n').encode()
    path.write_bytes(data)
    pins = {str(path.resolve()).casefold(): hashlib.md5(data).hexdigest()}
    receipt = {}
    assert list(join_sources([record(0, 'a', 'train', 1), record(1, 'b', 'val', 2)], {0: path}, pins, receipt)) == [None, None]
    assert receipt['source_join_fill_rate'] == 0
    assert [row['reason'] for row in receipt['mismatches']] == ['source_value_mismatch', 'source_row_absent']


def test_source_join_incomplete_iteration_is_unverified(tmp_path):
    path = tmp_path/'source.txt'
    data = ((FEN+' | 0 | .5\n')*3).encode()
    path.write_bytes(data)
    receipt = {}
    stream = join_sources([record(0, 'a', 'train', 1)], {0: path},
                          {str(path.resolve()).casefold(): hashlib.md5(data).hexdigest()}, receipt)
    assert next(stream).row_id == 0
    stream.close()
    assert receipt['complete'] is False and receipt['source_join_fill_rate'] is None

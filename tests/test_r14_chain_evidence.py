import hashlib
import struct

import pytest

from r14_chain_evidence import load_chain_ranges


def artifact(tmp_path, source, kind, fmt, rows):
    path = tmp_path/f'{source}-{kind}.bin'
    data = b''.join(struct.pack(fmt, *row) for row in rows)
    path.write_bytes(data)
    return dict(source_id=source, kind=kind, path=str(path), bytes=len(data), records=len(rows),
                md5=hashlib.md5(data).hexdigest(), sha256=hashlib.sha256(data).hexdigest())


def manifest(tmp_path):
    return dict(schema=1, scope='bounded_adjacent_chain_segments', mode='jobA', complete=True,
                segment_count=2, range_count=2, pair_counts={'REACHABLE': 2, 'UNREACHABLE': 1}, source_specs=[dict(source_id=0)],
                input_receipts=[dict(source_id=0, chain_scanned_rows=4, chain_scanned_ranges=[[1, 4]])],
                cross_file_adjacent_pairs=[], artifacts=[
                    artifact(tmp_path, 0, 'ranges', '<IIQB', [(1, 2, 1, 250), (3, 4, 2, 3)]),
                    artifact(tmp_path, 0, 'pairs', '<IBI', [(1, 250, 0), (2, 0, 2), (3, 3, 12), (4, 0, 2)]),
                    artifact(tmp_path, 0, 'boundaries', '<IBI', [(1, 250, 0), (3, 3, 12)])])


def test_bound_ranges_match_every_pair_and_boundary(tmp_path):
    data = manifest(tmp_path)
    ranges, receipt = load_chain_ranges(data, tmp_path)
    assert [r.identity for r in ranges[0]] == [1, 2]
    assert ranges[0][1].start_reason == 'UNREACHABLE'
    assert receipt['pairs'] == 4 and receipt['boundaries'] == 2


def test_file_hash_corruption_is_refused(tmp_path):
    data = manifest(tmp_path)
    data['artifacts'][0]['md5'] = '0'*32
    with pytest.raises(ValueError, match='hash'):
        load_chain_ranges(data, tmp_path)


def test_missing_boundary_cannot_silently_fill_zero(tmp_path):
    data = manifest(tmp_path)
    data['artifacts'][2] = artifact(tmp_path, 0, 'boundaries', '<IBI', [(1, 250, 0)])
    with pytest.raises(ValueError, match='boundar'):
        load_chain_ranges(data, tmp_path)


def test_pair_disagrees_with_range_start(tmp_path):
    data = manifest(tmp_path)
    data['artifacts'][1] = artifact(tmp_path, 0, 'pairs', '<IBI', [(1, 250, 0), (2, 3, 12), (3, 3, 12), (4, 0, 2)])
    with pytest.raises(ValueError, match='range'):
        load_chain_ranges(data, tmp_path)


def test_missing_scanned_row_is_not_complete(tmp_path):
    data = manifest(tmp_path)
    data['input_receipts'][0]['chain_scanned_rows'] = 5
    with pytest.raises(ValueError, match='coverage'):
        load_chain_ranges(data, tmp_path)


def test_unknown_code_and_reused_artifact_fail_closed(tmp_path):
    data = manifest(tmp_path)
    data['artifacts'][0] = artifact(tmp_path, 0, 'ranges', '<IIQB', [(1, 2, 1, 250), (3, 4, 2, 99)])
    with pytest.raises(ValueError, match='code'):
        load_chain_ranges(data, tmp_path)
    data = manifest(tmp_path)
    data['artifacts'].append(data['artifacts'][0])
    with pytest.raises(ValueError, match='duplicate'):
        load_chain_ranges(data, tmp_path)


def test_report_directory_contains_all_artifacts(tmp_path):
    data = manifest(tmp_path)
    out = tmp_path/'report'
    out.mkdir()
    with pytest.raises(ValueError, match='directory'):
        load_chain_ranges(data, out)


def joined_manifest(tmp_path):
    return dict(schema=1, scope='bounded_adjacent_chain_segments', mode='jobA', complete=True,
                segment_count=1, range_count=2, pair_counts={'REACHABLE': 3}, source_specs=[dict(source_id=0), dict(source_id=1)],
                input_receipts=[dict(source_id=s, rows=2, chain_scanned_rows=2,
                                     chain_scanned_ranges=[[1, 2]]) for s in (0, 1)],
                cross_file_adjacent_pairs=[dict(left_source=0, left_line=2, right_source=1,
                                               right_line=1, code=0, nodes=2, continued_segment_id=1)],
                artifacts=[artifact(tmp_path, 0, 'ranges', '<IIQB', [(1, 2, 1, 250)]),
                           artifact(tmp_path, 0, 'pairs', '<IBI', [(1, 250, 0), (2, 0, 2)]),
                           artifact(tmp_path, 0, 'boundaries', '<IBI', [(1, 250, 0)]),
                           artifact(tmp_path, 1, 'ranges', '<IIQB', [(1, 2, 1, 0)]),
                           artifact(tmp_path, 1, 'pairs', '<IBI', [(1, 0, 2), (2, 0, 2)])])


def test_exact_physical_cross_source_seam_is_bound(tmp_path):
    ranges, counts = load_chain_ranges(joined_manifest(tmp_path), tmp_path)
    assert ranges[0][-1].identity == ranges[1][0].identity
    assert counts['pairs'] == 4


@pytest.mark.parametrize('field,value', [('left_line', 1), ('right_line', 2), ('nodes', 7)])
def test_seam_coordinates_and_nodes_must_match_actual_pair(tmp_path, field, value):
    data = joined_manifest(tmp_path)
    data['cross_file_adjacent_pairs'][0][field] = value
    with pytest.raises(ValueError, match='seam'):
        load_chain_ranges(data, tmp_path)


def test_seam_left_endpoint_must_be_full_source_tail(tmp_path):
    data = joined_manifest(tmp_path)
    data['input_receipts'][0]['rows'] = 3
    with pytest.raises(ValueError, match='seam'):
        load_chain_ranges(data, tmp_path)


def test_duplicate_and_orphan_seams_are_rejected(tmp_path):
    data = joined_manifest(tmp_path)
    data['cross_file_adjacent_pairs'].append(dict(left_source=9, left_line=9,
                                                right_source=8, right_line=1, code=3,
                                                nodes=9, continued_segment_id=None))
    with pytest.raises(ValueError, match='seam'):
        load_chain_ranges(data, tmp_path)


def test_nonreachable_seam_must_match_pair_too(tmp_path):
    data = joined_manifest(tmp_path)
    data['segment_count'] = 2
    data['pair_counts'] = {'REACHABLE': 2, 'UNREACHABLE': 1}
    data['artifacts'][3] = artifact(tmp_path, 1, 'ranges', '<IIQB', [(1, 2, 2, 3)])
    data['artifacts'][4] = artifact(tmp_path, 1, 'pairs', '<IBI', [(1, 3, 17), (2, 0, 2)])
    data['artifacts'].append(artifact(tmp_path, 1, 'boundaries', '<IBI', [(1, 3, 17)]))
    data['cross_file_adjacent_pairs'][0].update(code=3, nodes=17, continued_segment_id=None)
    load_chain_ranges(data, tmp_path)
    data['cross_file_adjacent_pairs'][0]['code'] = 2
    with pytest.raises(ValueError, match='seam'):
        load_chain_ranges(data, tmp_path)


def test_report_counts_cannot_disagree_with_bound_binary_pairs(tmp_path):
    data = manifest(tmp_path)
    data['pair_counts']['UNREACHABLE'] = 0
    with pytest.raises(ValueError, match='count'):
        load_chain_ranges(data, tmp_path)

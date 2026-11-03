"""Regression fixtures for owned paths and complete duplicate-key reporting."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import p5_qc
import qc_core
import run_policy
from test_p5_audit import fixture

FEN = 'r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1'
MALFORMED_EMPTY_RUNS = (
    FEN.replace('/8/', '/44/', 1),
    FEN.replace('r3k2r', 'r12k2r'),
    FEN.replace('R3K2R', 'R3K11R'),
)


@pytest.mark.parametrize('fen', MALFORMED_EMPTY_RUNS)
def test_fen_info_rejects_consecutive_empty_digits(fen):
    with pytest.raises(ValueError, match='consecutive empty'):
        qc_core.fen_info(fen)


@pytest.mark.parametrize('fen', MALFORMED_EMPTY_RUNS)
def test_malformed_empty_run_cannot_count_as_filled_duplicate_key(fen):
    index = qc_core.DuplicateIndex()
    try:
        index.add('new', 'train', FEN)
        with pytest.raises(ValueError, match='consecutive empty'):
            index.add('new', 'val', fen)
        report = index.report('new')
        assert report['status'] == 'UNVERIFIED'
        for value in report['keys'].values():
            assert value['status'] == 'UNVERIFIED'
            assert value['rows'] == 2
            assert value['valid_key_rows'] == 1
            assert value['missing_key_rows'] == value['parse_failures'] == 1
            assert value['key_fill_rate'] == 0.5
            assert value['train_val_shared_keys'] == 0
    finally:
        index.close()


def test_arbitrary_owned_source_is_not_production(tmp_path):
    job = fixture(tmp_path)
    with patch.object(p5_qc, 'ROOT', tmp_path):
        with pytest.raises(ValueError, match='approved source'):
            p5_qc.audit_r14(job, run_policy.Inputs(), lambda row: None)


def test_explicit_fixture_mode_is_marked(tmp_path):
    job = fixture(tmp_path)
    result = p5_qc.audit_r14(job, run_policy.Inputs(), lambda row: None, fixture=True)
    assert result['fixture'] is True
    assert result['provenance_status'] == 'UNVERIFIED'


def test_duplicate_index_lives_in_shared_core():
    assert qc_core.DuplicateIndex is p5_qc.DuplicateIndex


def test_duplicate_index_never_creates_disk_index(tmp_path):
    path = tmp_path / 'index.sqlite'
    with patch.object(p5_qc, 'safe_path', side_effect=lambda value, **kwargs: Path(value)):
        index = p5_qc.DuplicateIndex(path)
        try:
            index.add('new', 'train', FEN)
            assert not path.exists()
        finally:
            index.close()


def test_three_key_overlap_counts_and_coverage(tmp_path):
    with patch.object(p5_qc, 'safe_path', side_effect=lambda value, **kwargs: Path(value)):
        index = p5_qc.DuplicateIndex(tmp_path / 'index.sqlite')
        try:
            index.add('new', 'train', FEN)
            index.add('new', 'train', FEN)
            index.add('new', 'val', FEN.replace('0 1', '1 1'))
            index.add('new', 'val', FEN.replace('KQkq', '-').replace('0 1', '2 1'))
            report = index.report('new')
            assert report['train_val_shared_fens'] == 0
            assert report['key_fill_rate'] == 1.0
            expected = {'six_field': (0, 0, 0), 'four_field': (1, 2, 1),
                        'board_stm': (1, 2, 2)}
            for name, (keys, train_rows, val_rows) in expected.items():
                value = report['keys'][name]
                assert value['train_val_shared_keys'] == keys
                assert value['train_overlap_rows'] == train_rows
                assert value['val_overlap_rows'] == val_rows
                assert value['rows'] == value['valid_key_rows'] == 4
                assert value['key_fill_rate'] == 1.0
                assert value['missing_key_rows'] == value['parse_failures'] == 0
        finally:
            index.close()


def test_invalid_key_attempt_cannot_leave_zero_overlap_pass(tmp_path):
    with patch.object(p5_qc, 'safe_path', side_effect=lambda value, **kwargs: Path(value)):
        index = p5_qc.DuplicateIndex(tmp_path / 'index.sqlite')
        try:
            index.add('new', 'train', FEN)
            with pytest.raises(ValueError):
                index.add('new', 'val', None)
            report = index.report('new')
            for value in report['keys'].values():
                assert value['status'] == 'UNVERIFIED'
                assert value['rows'] == 2
                assert value['valid_key_rows'] == 1
                assert value['key_fill_rate'] == 0.5
                assert value['missing_key_rows'] == 1
        finally:
            index.close()


def test_owned_root_is_r14_and_r13_write_is_refused():
    assert run_policy.safe_path('D:/a14/tmp/probe.json', write=True) == Path('D:/a14/tmp/probe.json')
    with pytest.raises(ValueError, match='outside'):
        run_policy.safe_path('D:/a13/tmp/probe.json', write=True)


def test_resource_refusal_is_incomplete_not_a_filled_key():
    index = p5_qc.DuplicateIndex()
    try:
        with patch.object(qc_core, 'free_guard', side_effect=OSError('resource fixture')):
            with pytest.raises(OSError):
                index.add('new', 'train', FEN)
        for value in index.report('new')['keys'].values():
            assert value['status'] == 'UNVERIFIED'
            assert value['valid_key_rows'] == 0
            assert value['missing_key_rows'] == 1
            assert value['key_fill_rate'] == 0
    finally:
        index.close()


def test_empty_index_has_no_coverage_claim():
    index = p5_qc.DuplicateIndex()
    try:
        for value in index.report('empty')['keys'].values():
            assert value['status'] == 'UNVERIFIED'
            assert value['key_fill_rate'] is None
    finally:
        index.close()


def test_reduced_keys_compare_board_state_not_fen_spelling():
    index = p5_qc.DuplicateIndex()
    try:
        index.add('new', 'train', FEN)
        index.add('new', 'val', FEN.replace('KQkq', 'qkQK'))
        report = index.report('new')
        assert report['train_val_shared_fens'] == 0
        assert report['keys']['four_field']['train_val_shared_keys'] == 1
        assert report['keys']['board_stm']['train_val_shared_keys'] == 1
    finally:
        index.close()


def test_closed_index_cannot_report_or_accept_rows():
    index = p5_qc.DuplicateIndex()
    index.close()
    with pytest.raises(ValueError, match='closed'):
        index.add('new', 'train', FEN)
    with pytest.raises(ValueError, match='closed'):
        index.report('new')


def test_aggregate_status_includes_reduced_key_overlap():
    index = p5_qc.DuplicateIndex()
    try:
        index.add('new', 'train', FEN)
        index.add('new', 'val', FEN.replace('KQkq', '-'))
        report = index.report('new')
        assert report['keys']['six_field']['status'] == 'PASS'
        assert report['keys']['board_stm']['status'] == 'FAIL'
        assert report['status'] == 'FAIL'
    finally:
        index.close()


@pytest.mark.parametrize('cohort', ['', None])
def test_unassigned_rejected_row_makes_all_reports_incomplete(cohort):
    index = p5_qc.DuplicateIndex()
    try:
        index.add('new', 'train', FEN)
        with pytest.raises(ValueError):
            index.add(cohort, 'val', FEN)
        report = index.report('new')
        assert report['status'] == 'UNVERIFIED'
        assert report['unassigned_rejected_rows'] == 1
        assert report['key_fill_rate'] is None
        assert all(value['status'] == 'UNVERIFIED' for value in report['keys'].values())
    finally:
        index.close()


def test_invalid_split_is_not_a_fen_parse_failure():
    index = p5_qc.DuplicateIndex()
    try:
        with pytest.raises(ValueError):
            index.add('new', 'unknown-split', FEN)
        report = index.report('new')
        assert report['status'] == 'UNVERIFIED'
        assert report['parse_failures'] == 0
        assert report['routing_failures'] == 1
        assert report['missing_key_rows'] == 1
    finally:
        index.close()


def test_c_floor_is_checked_even_when_d_has_space():
    def usage(drive):
        return SimpleNamespace(free=80 * 1024**3 if str(drive).lower().startswith('d:') else 30 * 1024**3 - 1)
    with patch.object(run_policy.shutil, 'disk_usage', side_effect=usage):
        with pytest.raises(OSError, match='C:'):
            run_policy.free_guard()


@pytest.mark.parametrize('path', ['F:/nnue_pytorch/venv/Lib/site-packages/x.py',
                                 'F:/nnue-pytorch/x.py'])
def test_protected_runtime_paths_refused(path):
    with pytest.raises(ValueError, match='protected'):
        run_policy.safe_path(path)

import hashlib
from pathlib import Path
import pytest

from r14_overlap import overlap_audit


def source(tmp_path, name, rows):
    path = tmp_path / name
    data = ''.join(f'{fen} | 0 | 0.5\n' for fen in rows).encode()
    path.write_bytes(data)
    return path, hashlib.md5(data).hexdigest()


FEN = '4k3/8/8/8/8/8/8/4K3 w - - 0 1'
OTHER = '4k3/8/8/8/8/8/8/3K4 w - - 0 1'


def test_exact_reduced_key_overlap_and_fill(tmp_path):
    h, hm = source(tmp_path, 'h.txt', [FEN])
    t, tm = source(tmp_path, 't.txt', [FEN.replace('0 1', '7 9'), OTHER])
    result = overlap_audit([h], [t], {str(h).casefold(): hm, str(t).casefold(): tm}, chunk_rows=1)
    assert result['status'] == 'FAIL'
    assert result['keys']['four_field']['train_overlap_rows'] == 1
    assert result['keys']['board_stm']['train_overlap_rows'] == 1
    assert result['train']['rows'] == 2 and result['train']['key_fill_rate'] == 1.0
    assert result['holdout']['rows'] == 1 and result['holdout']['key_fill_rate'] == 1.0


def test_hash_collision_never_becomes_exact_overlap(tmp_path, monkeypatch):
    import r14_overlap
    monkeypatch.setattr(r14_overlap, 'hash64', lambda value: 17)
    h, hm = source(tmp_path, 'h.txt', [FEN])
    t, tm = source(tmp_path, 't.txt', [OTHER])
    result = overlap_audit([h], [t], {str(h).casefold(): hm, str(t).casefold(): tm}, chunk_rows=1)
    assert result['status'] == 'PASS'
    assert result['keys']['four_field']['hash_candidate_rows'] == 1
    assert result['keys']['four_field']['train_overlap_rows'] == 0
    assert result['keys']['four_field']['hash_collision_rows'] == 1


def test_zero_overlap_with_missing_key_is_unverified(tmp_path):
    h, hm = source(tmp_path, 'h.txt', [FEN])
    t = tmp_path / 'bad.txt'
    t.write_bytes(b'not a row\n')
    result = overlap_audit([h], [t], {str(h).casefold(): hm, str(t).casefold(): hashlib.md5(t.read_bytes()).hexdigest()}, chunk_rows=2)
    assert result['status'] == 'UNVERIFIED'
    assert result['train']['key_fill_rate'] == 0.0
    assert result['train']['parse_failures'] == 1


def test_changed_holdout_in_exact_resolution_cannot_pass(tmp_path):
    h, hm = source(tmp_path, 'h.txt', [FEN])
    t, tm = source(tmp_path, 't.txt', [FEN])
    def mutate_after_train(item):
        if item['stage'] == 'train_file_complete':
            h.write_text(OTHER+' | 0 | 0.5\n')
    with pytest.raises(ValueError, match='hash'):
        overlap_audit([h], [t], {str(h).casefold(): hm, str(t).casefold(): tm}, chunk_rows=1, progress=mutate_after_train)


def test_interrupted_audit_publishes_partial_coverage_when_safe(tmp_path):
    from r14_overlap import run_to_report
    h, hm = source(tmp_path, 'h.txt', [FEN])
    t, tm = source(tmp_path, 't.txt', [OTHER])
    def stop_after_holdout(item):
        if item['stage'] == 'holdout_file_complete':
            raise TimeoutError('fixture deadline')
    out = tmp_path / 'report'
    out.mkdir()
    report = run_to_report([h], [t], {str(h).casefold(): hm, str(t).casefold(): tm}, out,
                           progress=stop_after_holdout, publication_guard=lambda needed: None)
    assert report['status'] == 'UNVERIFIED' and report['complete'] is False
    assert report['partial_coverage']['holdout']['rows'] == 1
    assert report['partial_coverage']['train']['rows'] == 0
    assert (out/'REPORT.json').is_file()


def test_resource_refusal_prevents_final_report_allocation(tmp_path):
    from r14_overlap import run_to_report
    h, hm = source(tmp_path, 'h.txt', [FEN])
    t, tm = source(tmp_path, 't.txt', [OTHER])
    def refuse(needed):
        raise OSError('fixture storage cap')
    out = tmp_path / 'report'
    out.mkdir()
    report = run_to_report([h], [t], {str(h).casefold(): hm, str(t).casefold(): tm}, out,
                           publication_guard=refuse)
    assert report['status'] == 'UNVERIFIED' and report['complete'] is False
    assert report['publication_status'] == 'REFUSED'
    assert not (out/'REPORT.json').exists()

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


@pytest.mark.parametrize('failure', ['write', 'flush', 'fsync', 'close'])
def test_failed_publication_leaves_only_unpublished_part(tmp_path, monkeypatch, failure):
    import r14_overlap
    h, hm = source(tmp_path, 'h.txt', [FEN])
    t, tm = source(tmp_path, 't.txt', [OTHER])
    out = tmp_path/'report'
    out.mkdir()
    original_open = Path.open

    class FailingSink:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.stream.__exit__(*args)
            if args[0] is None and failure == 'close':
                raise OSError('fixture close failure')

        def write(self, payload):
            if failure == 'write':
                self.stream.write(payload[:len(payload)//2])
                raise OSError('fixture write failure')
            return self.stream.write(payload)

        def flush(self):
            if failure == 'flush':
                raise OSError('fixture flush failure')
            return self.stream.flush()

        def fileno(self):
            return self.stream.fileno()

    def open_with_failure(path, mode='r', *args, **kwargs):
        stream = original_open(path, mode, *args, **kwargs)
        if mode == 'xb' and path.parent == out and path.name in ('REPORT.json', 'REPORT.json.part'):
            return FailingSink(stream)
        return stream

    def fail_fsync(fd):
        raise OSError('fixture fsync failure')

    monkeypatch.setattr(Path, 'open', open_with_failure)
    if failure == 'fsync':
        monkeypatch.setattr(r14_overlap.os, 'fsync', fail_fsync)
    report = r14_overlap.run_to_report([h], [t], {str(h).casefold(): hm, str(t).casefold(): tm}, out,
                                       publication_guard=lambda needed: None)
    assert report['status'] == 'UNVERIFIED' and report['complete'] is False
    assert report['publication_status'] == 'REFUSED'
    assert not (out/'REPORT.json').exists()
    assert (out/'REPORT.json.part').is_file()


def test_storage_refusal_after_close_prevents_report_rename(tmp_path):
    from r14_overlap import run_to_report
    h, hm = source(tmp_path, 'h.txt', [FEN])
    t, tm = source(tmp_path, 't.txt', [OTHER])
    out = tmp_path/'report'
    out.mkdir()

    def refuse_after_write(needed):
        if (out/'REPORT.json.part').is_file():
            raise OSError('fixture post-write storage cap')

    report = run_to_report([h], [t], {str(h).casefold(): hm, str(t).casefold(): tm}, out,
                           publication_guard=refuse_after_write)
    assert report['status'] == 'UNVERIFIED' and report['complete'] is False
    assert report['publication_status'] == 'REFUSED'
    assert not (out/'REPORT.json').exists()
    assert (out/'REPORT.json.part').is_file()


def test_failed_rename_preserves_unpublished_part(tmp_path, monkeypatch):
    import r14_overlap
    h, hm = source(tmp_path, 'h.txt', [FEN])
    t, tm = source(tmp_path, 't.txt', [OTHER])
    out = tmp_path/'report'
    out.mkdir()

    def fail_rename(source_path, target_path):
        raise OSError('fixture rename failure')

    monkeypatch.setattr(r14_overlap.os, 'rename', fail_rename)
    report = r14_overlap.run_to_report([h], [t], {str(h).casefold(): hm, str(t).casefold(): tm}, out,
                                       publication_guard=lambda needed: None)
    assert report['status'] == 'UNVERIFIED' and report['complete'] is False
    assert report['publication_status'] == 'REFUSED'
    assert not (out/'REPORT.json').exists()
    assert (out/'REPORT.json.part').is_file()


def test_successful_publication_seals_complete_report(tmp_path):
    import json
    from r14_overlap import run_to_report
    h, hm = source(tmp_path, 'h.txt', [FEN])
    t, tm = source(tmp_path, 't.txt', [OTHER])
    out = tmp_path/'report'
    out.mkdir()
    report = run_to_report([h], [t], {str(h).casefold(): hm, str(t).casefold(): tm}, out,
                           publication_guard=lambda needed: None)
    assert report['status'] == 'PASS' and report['complete'] is True
    assert json.loads((out/'REPORT.json').read_text()) == report
    assert not (out/'REPORT.json.part').exists()


def test_publication_never_overwrites_existing_report(tmp_path):
    from r14_overlap import run_to_report
    h, hm = source(tmp_path, 'h.txt', [FEN])
    t, tm = source(tmp_path, 't.txt', [OTHER])
    out = tmp_path/'report'
    out.mkdir()
    final = out/'REPORT.json'
    final.write_bytes(b'preserved prior evidence\n')
    report = run_to_report([h], [t], {str(h).casefold(): hm, str(t).casefold(): tm}, out,
                           publication_guard=lambda needed: None)
    assert report['status'] == 'UNVERIFIED' and report['complete'] is False
    assert report['publication_status'] == 'REFUSED'
    assert final.read_bytes() == b'preserved prior evidence\n'
    assert not (out/'REPORT.json.part').exists()


def test_failed_resolution_receipt_is_preserved(tmp_path):
    from r14_overlap import run_to_report
    h, hm = source(tmp_path, 'h.txt', [FEN])
    t, tm = source(tmp_path, 't.txt', [FEN])
    def mutate(item):
        if item['stage'] == 'train_file_complete':
            h.write_text(OTHER+' | 0 | 0.5\n')
    out = tmp_path / 'report'
    out.mkdir()
    report = run_to_report([h], [t], {str(h).casefold(): hm, str(t).casefold(): tm}, out,
                           progress=mutate, publication_guard=lambda needed: None)
    assert report['status'] == 'UNVERIFIED'
    receipt = report['resolution_receipts'][0]
    assert receipt['complete'] is False and receipt['rows'] == 1
    assert receipt['expected_md5'] == hm and receipt['actual_md5'] != hm


def test_runtime_inventory_rejects_unlisted_file(tmp_path):
    import json
    from r14_overlap import verify_runtime
    runtime = tmp_path / 'runtime'
    runtime.mkdir()
    module = runtime / 'module.py'
    module.write_bytes(b'pass\n')
    inventory = tmp_path / 'inventory.jsonl'
    inventory.write_text(json.dumps(dict(path=str(module),md5=hashlib.md5(module.read_bytes()).hexdigest()))+'\n')
    pin = hashlib.md5(inventory.read_bytes()).hexdigest()
    verify_runtime(runtime_root=runtime, inventory=inventory, expected_inventory_md5=pin)
    (runtime/'unexpected.pth').write_text('unexpected\n')
    with pytest.raises(ValueError, match='file set'):
        verify_runtime(runtime_root=runtime, inventory=inventory, expected_inventory_md5=pin)


def test_owned_dependency_marker_is_verified_read_only(tmp_path):
    import json
    from r14_overlap import verify_runtime
    runtime = tmp_path / 'runtime'
    marker = runtime/'python/Lib/site-packages/setuptools/_vendor/.lock'
    marker.parent.mkdir(parents=True)
    marker.write_bytes(b'')
    inventory = tmp_path/'inventory.jsonl'
    inventory.write_text(json.dumps(dict(path=str(marker),md5=hashlib.md5(b'').hexdigest()))+'\n')
    report = verify_runtime(runtime_root=runtime, inventory=inventory,
                            expected_inventory_md5=hashlib.md5(inventory.read_bytes()).hexdigest())
    assert report['verified_files'] == 1 and marker.read_bytes() == b''


def test_runtime_inventory_rejects_external_root_before_inventory_read(tmp_path):
    from r14_overlap import verify_runtime
    with pytest.raises(ValueError, match='outside D:/a14'):
        verify_runtime(runtime_root=Path('D:/a13/runtime'),
                       inventory=tmp_path/'not-created.jsonl')


def test_runtime_marker_exception_stays_inside_owned_root(tmp_path, monkeypatch):
    import json
    import run_policy
    from r14_overlap import verify_runtime
    owned = tmp_path/'owned'
    owned.mkdir()
    runtime = tmp_path/'external-runtime'
    marker = runtime/'python/Lib/site-packages/setuptools/_vendor/.lock'
    marker.parent.mkdir(parents=True)
    marker.write_bytes(b'')
    inventory = owned/'inventory.jsonl'
    inventory.write_text(json.dumps(dict(path=str(marker), md5=hashlib.md5(b'').hexdigest()))+'\n')
    monkeypatch.setattr(run_policy, 'ROOT', owned)
    with pytest.raises(ValueError, match='outside D:/a14'):
        verify_runtime(runtime_root=runtime, inventory=inventory,
                       expected_inventory_md5=hashlib.md5(inventory.read_bytes()).hexdigest())
    assert marker.read_bytes() == b''


@pytest.mark.parametrize('name', ['other.lock', '.lock.backup.lock'])
def test_runtime_inventory_rejects_neighboring_locks(tmp_path, name):
    import json
    from r14_overlap import verify_runtime
    runtime = tmp_path/'runtime'
    neighbor = runtime/'python/Lib/site-packages/setuptools/_vendor'/name
    neighbor.parent.mkdir(parents=True)
    neighbor.write_bytes(b'')
    inventory = tmp_path/'inventory.jsonl'
    inventory.write_text(json.dumps(dict(path=str(neighbor), md5=hashlib.md5(b'').hexdigest()))+'\n')
    with pytest.raises(ValueError, match='protected component'):
        verify_runtime(runtime_root=runtime, inventory=inventory,
                       expected_inventory_md5=hashlib.md5(inventory.read_bytes()).hexdigest())
    assert neighbor.read_bytes() == b''


THIRD = '4k3/8/8/8/8/8/8/5K2 w - - 0 1'


def listing_fixture(tmp_path):
    h, hm = source(tmp_path, 'h.txt', [FEN, OTHER, FEN.replace('0 1', '3 7')])
    t1, t1m = source(tmp_path, 't1.txt', [THIRD, FEN.replace('0 1', '7 9')])
    t2, t2m = source(tmp_path, 't2.txt', [OTHER, FEN])
    pins = {str(p).casefold(): m for p, m in ((h, hm), (t1, t1m), (t2, t2m))}
    return h, t1, t2, pins


def test_listing_names_every_shared_train_and_holdout_row(tmp_path):
    h, t1, t2, pins = listing_fixture(tmp_path)
    result = overlap_audit([h], [t1, t2], pins, chunk_rows=1)
    for name in ('board_stm', 'four_field'):
        report = result['keys'][name]
        assert report['status'] == 'FAIL' and report['listing_complete'] is True
        assert report['shared_exact_keys'] == 2
        assert report['train_overlap_rows'] == 3 and report['holdout_overlap_rows'] == 3
        listing = {item['key'].split()[0]: item for item in report['shared_keys']}
        assert len(listing) == 2
        fen_board = '....k' + '.' * 55 + 'K...'
        other_board = '....k' + '.' * 54 + 'K....'
        assert listing[fen_board]['train'] == [
            dict(path=str(t1), line=2, fen=FEN.replace('0 1', '7 9')), dict(path=str(t2), line=2, fen=FEN)]
        assert listing[fen_board]['holdout'] == [
            dict(path=str(h), line=1, fen=FEN), dict(path=str(h), line=3, fen=FEN.replace('0 1', '3 7'))]
        assert listing[other_board]['train'] == [dict(path=str(t2), line=1, fen=OTHER)]
        assert listing[other_board]['holdout'] == [dict(path=str(h), line=2, fen=OTHER)]


def test_listing_over_cap_is_withheld_not_truncated(tmp_path, monkeypatch):
    import r14_overlap
    monkeypatch.setattr(r14_overlap, 'LISTING_ROW_CAP', 2)
    h, t1, t2, pins = listing_fixture(tmp_path)
    result = overlap_audit([h], [t1, t2], pins, chunk_rows=1)
    report = result['keys']['board_stm']
    assert report['status'] == 'FAIL' and report['train_overlap_rows'] == 3
    assert report['listing_complete'] is False and report['shared_keys'] is None


def test_listing_is_empty_and_complete_without_overlap(tmp_path):
    h, hm = source(tmp_path, 'h.txt', [FEN])
    t, tm = source(tmp_path, 't.txt', [OTHER])
    result = overlap_audit([h], [t], {str(h).casefold(): hm, str(t).casefold(): tm}, chunk_rows=1)
    for name in ('board_stm', 'four_field'):
        assert result['keys'][name]['listing_complete'] is True
        assert result['keys'][name]['shared_keys'] == []

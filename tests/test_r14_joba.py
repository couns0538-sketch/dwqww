import json
from pathlib import Path

import pytest

import r14_joba
from r14_joba import separation_verdict


def evidence():
    coverage = dict(rows=10, valid_key_rows=10, parse_failures=0, missing_key_rows=0,
                    key_fill_rate=1.0, complete=True)
    return (dict(comparison_status='PASS', rows=10, mapped_rows=10, valid_prepared_rows=10, mapping_fill_rate=1.0),
            coverage, dict(rows=10, matched_rows=10, source_join_fill_rate=1.0,
                           complete=True, mismatches=[], sources=[dict(coverage), dict(coverage)]),
            dict(complete=True, input_receipts=[dict(coverage, chain_key_fill_rate=1.0, target_key_fill_rate=1.0),
                                                dict(coverage, chain_key_fill_rate=1.0, target_key_fill_rate=1.0)]))


def test_observed_group_match_does_not_create_authentic_ids():
    status, reasons = separation_verdict(*evidence())
    assert status == 'UNVERIFIED'
    assert any('authentic' in reason for reason in reasons)


def test_proven_group_mismatch_is_retained_as_failure():
    parts = evidence()
    parts[0]['comparison_status'] = 'FAIL'
    status, _ = separation_verdict(*parts)
    assert status == 'FAIL'


def test_unselected_source_tail_parse_failure_blocks_clearance():
    parts = evidence()
    parts[2]['sources'][1].update(valid_key_rows=9, missing_key_rows=1, parse_failures=1, key_fill_rate=.9)
    status, reasons = separation_verdict(*parts)
    assert status == 'UNVERIFIED'
    assert any('full-source' in reason for reason in reasons)


def test_missing_mapping_and_incomplete_source_are_not_zero_proofs():
    parts = evidence()
    parts[0]['mapping_fill_rate'] = .9
    parts[3]['complete'] = False
    status, reasons = separation_verdict(*parts)
    assert status == 'UNVERIFIED'
    assert len(reasons) >= 3


def test_fabricated_fill_rate_cannot_override_missing_counts():
    parts = evidence()
    parts[1]['valid_key_rows'] = 9
    status, _ = separation_verdict(*parts)
    assert status == 'UNVERIFIED'


def test_empty_source_receipts_and_mismatched_denominators_fail_closed():
    parts = evidence()
    parts[2]['sources'] = []
    parts[2]['matched_rows'] = 9
    status, _ = separation_verdict(*parts)
    assert status == 'UNVERIFIED'


def bound_fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(r14_joba, 'ROOT', tmp_path)
    monkeypatch.setattr(r14_joba, 'SOURCE', tmp_path/'sources')
    paths = ['tools/r14_segments.py', 'tools/r14_scan.py', 'tools/run_policy.py',
             'tools/r14_qualification/qualify.py', 'runtime/python/python.exe',
             'runtime/python/Lib/site-packages/chess/__init__.py', 'pins.jsonl', 'native.exe', 'qualification.json']
    identities = {}
    for relative in paths:
        path = tmp_path/relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{}' if relative == 'qualification.json' else 'fixture')
        identities[relative] = r14_joba.identity(path)
    monkeypatch.setattr(r14_joba, 'QUALIFICATION_MD5', identities['qualification.json']['md5'])
    called = []
    monkeypatch.setattr(r14_joba, 'validate_qualification', lambda report, native: called.append(native))
    pins, specs, receipts = {}, [], []
    for number in (0, 1):
        path = tmp_path/'sources'/f'forge_selfplay_{number+1:03}.txt'
        pins[str(path.resolve()).casefold()] = '1'*32
        specs.append(dict(source_id=number, shard=number+1, path=str(path), md5='1'*32,
                          selection='all' if number == 0 else 'prefix', limit=None if number == 0 else 583415,
                          target_limit=None if number == 0 else 533415))
        receipts.append(dict(source_id=number, path=str(path), expected_md5='1'*32, actual_md5='1'*32, complete=True))
    scan = dict(schema=1, mode='jobA', complete=True, pins=identities['pins.jsonl'],
                qualification=identities['qualification.json'], native=identities['native.exe'],
                tool_identities=[identities[p] for p in paths[:6]], source_specs=specs, input_receipts=receipts)
    return scan, pins, tmp_path/'pins.jsonl', called


def test_scan_binds_all_tools_original_sources_and_qualification(tmp_path, monkeypatch):
    scan, pins, pin_path, called = bound_fixture(tmp_path, monkeypatch)
    sources, identities = r14_joba.bind_scan(scan, pins, pin_path)
    assert set(sources) == {0, 1} and len(identities) == 9 and len(called) == 1


def test_changed_source_receipt_and_missing_tool_pin_are_refused(tmp_path, monkeypatch):
    scan, pins, pin_path, _ = bound_fixture(tmp_path, monkeypatch)
    scan['input_receipts'][1]['actual_md5'] = '2'*32
    with pytest.raises(ValueError, match='source identity'):
        r14_joba.bind_scan(scan, pins, pin_path)
    scan['input_receipts'][1]['actual_md5'] = '1'*32
    scan['tool_identities'].pop()
    with pytest.raises(ValueError, match='identity coverage'):
        r14_joba.bind_scan(scan, pins, pin_path)


def test_close_failure_cannot_publish_final_report(tmp_path, monkeypatch):
    class Guard:
        def admit_publication(self, needed):
            assert needed > 0
    original = Path.open
    class FailingClose:
        def __init__(self, path, *args, **kwargs):
            self.stream = original(path, *args, **kwargs)
        def __enter__(self):
            return self.stream
        def __exit__(self, *args):
            self.stream.close()
            raise OSError('injected close failure')
    monkeypatch.setattr(Path, 'open', lambda path, *args, **kwargs: FailingClose(path, *args, **kwargs)
                        if path.name.endswith('.part') else original(path, *args, **kwargs))
    final = tmp_path/'REPORT.json'
    with pytest.raises(OSError, match='close failure'):
        r14_joba.publish_json(final, {'status': 'PASS'}, Guard())
    assert not final.exists() and (tmp_path/'REPORT.json.part').exists()

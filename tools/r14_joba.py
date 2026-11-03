"""Bind original prepared groups to qualified, fully consumed source-chain maps."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import time

from r14_chain_evidence import load_chain_ranges
from r14_group_map import iter_prepared, join_sources, audit_groups
from r14_overlap import RuntimeGuard
from r14_scan import load_pins
from r14_segments import validate_qualification
from run_policy import Snapshot, safe_path, strict_json_loads

ROOT = Path('D:/a14')
SOURCE = Path('D:/grok-pc-data/selfplay_out')
PREPARED = Path('D:/o14b/r2/proof/jobA/rows.tsv')
QUALIFICATION_MD5 = 'b91461a33503289c3025b5723d202d72'


def full_coverage(receipt):
    rows = receipt.get('rows')
    return (type(rows) is int and rows > 0 and receipt.get('complete') is True
            and receipt.get('valid_key_rows') == rows and receipt.get('missing_key_rows') == 0
            and receipt.get('parse_failures') == 0 and receipt.get('key_fill_rate') == 1.0)


def separation_verdict(groups, prepared, joined, scan):
    reasons = []
    if not full_coverage(prepared):
        reasons.append('prepared key coverage is incomplete')
    if (joined.get('complete') is not True or joined.get('rows') != prepared.get('rows')
            or joined.get('matched_rows') != prepared.get('rows') or joined.get('source_join_fill_rate') != 1.0
            or joined.get('mismatches')):
        reasons.append('exact prepared-to-source row binding is incomplete')
    sources = joined.get('sources', [])
    if len(sources) != 2 or not all(full_coverage(item) for item in sources):
        reasons.append('full-source parse coverage, including omitted rows and tails, is incomplete')
    scanned = scan.get('input_receipts', [])
    if (scan.get('complete') is not True or len(scanned) != 2 or not all(full_coverage(item)
            and item.get('chain_key_fill_rate') == 1.0 and item.get('target_key_fill_rate') == 1.0 for item in scanned)):
        reasons.append('source chain scan consumption or key coverage is incomplete')
    if (groups.get('rows') != prepared.get('rows') or groups.get('mapped_rows') != prepared.get('rows')
            or groups.get('valid_prepared_rows') != prepared.get('rows') or groups.get('mapping_fill_rate') != 1.0):
        reasons.append('prepared-to-range mapping coverage is incomplete')
    coverage_complete = not reasons
    reasons.append('authentic original game IDs and historical producer-to-row bindings remain unavailable')
    if groups.get('comparison_status') == 'FAIL':
        reasons.append('demonstrated mismatch between inferred groups and observed source chains')
    elif groups.get('comparison_status') != 'PASS':
        reasons.append('inferred group boundaries include unresolved observed-chain evidence')
    return ('FAIL' if coverage_complete and groups.get('comparison_status') == 'FAIL' else 'UNVERIFIED'), reasons


def identity(path, *, owned=True):
    path = safe_path(path, write=owned)
    snapshot = Snapshot(path)
    digest = snapshot.digest()
    return dict(path=str(path), **digest)


def verify_identity(record):
    actual = identity(record['path'])
    if actual['md5'] != record['md5'] or actual['sha256'] != record['sha256']:
        raise ValueError('evidence identity mismatch: '+actual['path'])
    return actual


def read_bound_json(path, expected_md5):
    path = safe_path(path, write=True)
    snapshot = Snapshot(path)
    raw = snapshot.bytes()
    if snapshot.hashes['md5'] != expected_md5:
        raise ValueError('report input hash mismatch')
    return strict_json_loads(raw.decode('utf-8-sig')), dict(path=str(path), **snapshot.hashes)


def bind_scan(scan, pins, pin_path):
    if scan.get('schema') != 1 or scan.get('mode') != 'jobA' or scan.get('complete') is not True:
        raise ValueError('complete original jobA source-chain scan required')
    pin_identity = verify_identity(scan['pins'])
    if safe_path(pin_identity['path']) != safe_path(pin_path):
        raise ValueError('different source-pin manifest')
    if scan['qualification']['md5'] != QUALIFICATION_MD5:
        raise ValueError('unrecognized production qualification pin')
    qualification_identity = verify_identity(scan['qualification'])
    qualification, _ = read_bound_json(qualification_identity['path'], QUALIFICATION_MD5)
    native_identity = verify_identity(scan['native'])
    validate_qualification(qualification, native_identity)
    tool_records = scan['tool_identities']
    required = {str(safe_path(path)).casefold() for path in (ROOT/'tools/r14_segments.py', ROOT/'tools/r14_scan.py',
                ROOT/'tools/run_policy.py', ROOT/'tools/r14_qualification/qualify.py', ROOT/'runtime/python/python.exe',
                ROOT/'runtime/python/Lib/site-packages/chess/__init__.py')}
    actual_tools = [verify_identity(record) for record in tool_records]
    if {record['path'].casefold() for record in actual_tools} != required or len(actual_tools) != len(required):
        raise ValueError('scanner tool/runtime identity coverage mismatch')
    specs, receipts = scan['source_specs'], scan['input_receipts']
    if len(specs) != 2 or len(receipts) != 2:
        raise ValueError('jobA source coverage mismatch')
    sources = {}
    for number, (spec, receipt) in enumerate(zip(specs, receipts)):
        path = safe_path(SOURCE/f'forge_selfplay_{number+1:03}.txt')
        expected = pins[str(path).casefold()]
        if (spec['source_id'] != number or spec['shard'] != number+1 or safe_path(spec['path']) != path
                or spec['md5'] != expected or receipt['source_id'] != number or safe_path(receipt['path']) != path
                or receipt['expected_md5'] != expected or receipt.get('actual_md5') != expected
                or receipt.get('complete') is not True):
            raise ValueError('source identity/receipt mismatch')
        selection = ('all', None, None) if number == 0 else ('prefix', 583415, 533415)
        if (spec['selection'], spec['limit'], spec['target_limit']) != selection:
            raise ValueError('unexpected source selection or missing context')
        sources[number] = path
    return sources, [pin_identity, qualification_identity, native_identity, *actual_tools]


def publish_json(path, value, guard):
    path = safe_path(path, write=True)
    if path.exists():
        raise FileExistsError('existing evidence refused')
    payload = (json.dumps(value, sort_keys=True, indent=2)+'\n').encode('utf-8')
    guard.admit_publication(len(payload)+1024*1024)
    pending = path.with_name(path.name+'.part')
    with pending.open('xb') as stream:
        if stream.write(payload) != len(payload):
            raise OSError('short evidence write')
        stream.flush()
        os.fsync(stream.fileno())
    guard.admit_publication(1024*1024)
    os.rename(safe_path(pending, write=True), path)
    return identity(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scan', type=Path, required=True)
    parser.add_argument('--scan-md5', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--pins', type=Path, default=ROOT/'evidence/r14/input-pins-all.jsonl')
    parser.add_argument('--cpu', type=int, default=3)
    parser.add_argument('--seconds', type=float, default=1800)
    args = parser.parse_args(argv)
    for name in ('CUDA_VISIBLE_DEVICES', 'HIP_VISIBLE_DEVICES'):
        os.environ[name] = '-1'
    for name in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
        os.environ[name] = '1'
    guard = RuntimeGuard(args.seconds, args.cpu)
    out = safe_path(args.out, write=True)
    guard.admit_publication(16*1024**2)
    out.mkdir(parents=True, exist_ok=False)
    began = time.monotonic()
    report = dict(schema=1, status='UNVERIFIED', complete=False, export_allowed=False,
                  authentic_game_ids='UNVERIFIED', start_vienna=datetime.now().strftime('%Y-%m-%d %H:%M:%S Vienna'))
    prepared_receipt, join_receipt = {}, {}
    try:
        pins = load_pins(safe_path(args.pins))
        scan, scan_identity = read_bound_json(args.scan, args.scan_md5)
        sources, identities = bind_scan(scan, pins, args.pins)
        own_identities = [identity(ROOT/path) for path in ('tools/r14_joba.py', 'tools/r14_group_map.py',
                          'tools/r14_chain_evidence.py', 'tools/r14_overlap.py')]
        identities.extend([scan_identity, *own_identities])
        ranges, binary_counts = load_chain_ranges(scan, Path(scan_identity['path']).parent, guard=guard)
        records = iter_prepared(PREPARED, pins[str(safe_path(PREPARED)).casefold()], prepared_receipt)
        groups = audit_groups(join_sources(records, sources, pins, join_receipt, guard=guard), ranges, guard=guard)
        guard()
        for record in identities:
            verify_identity(record)
        status, reasons = separation_verdict(groups, prepared_receipt, join_receipt, scan)
        group_identity = publish_json(out/'GROUPS.json', groups, guard)
        counts = {key: value for key, value in groups.items() if key not in ('groups', 'shared_segments', 'missing_mapping')}
        report.update(status=status, complete=True, reasons=reasons, group_comparison=counts,
                      prepared_receipt=prepared_receipt, source_join=join_receipt,
                      chain_scan_receipts=scan['input_receipts'], binary_counts=binary_counts,
                      chain_scan=scan_identity, groups_artifact=group_identity, bound_identities=identities,
                      cross_split_scope='shared observed contiguous chain ranges; no all-pairs nonadjacent-group search',
                      exact_authentic_group_equality='UNVERIFIED')
    except Exception as error:
        report.update(reasons=[f'{type(error).__name__}: {error}'], prepared_receipt=prepared_receipt,
                      source_join=join_receipt)
    report.update(end_vienna=datetime.now().strftime('%Y-%m-%d %H:%M:%S Vienna'), elapsed_seconds=time.monotonic()-began)
    try:
        sealed = publish_json(out/'REPORT.json', report, guard)
    except Exception as error:
        print(json.dumps(dict(status='UNVERIFIED', complete=False, publication_error=str(error))), flush=True)
        return 2
    print(json.dumps(dict(status=report['status'], complete=report['complete'], report=sealed,
                          export_allowed=False, elapsed_seconds=report['elapsed_seconds'])), flush=True)
    return 0 if report['complete'] else 2


if __name__ == '__main__':
    raise SystemExit(main())

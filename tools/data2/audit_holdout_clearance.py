#!/usr/bin/env python3
"""Independently audit sealed converter output against complete real013/014 FPOS.

The caller must supply SHA-256 and row counts from trusted full-shard manifests.
A PASS proves zero board32+STM overlap for exactly the artifacts in the report;
it does not establish game provenance, filtering quality, or overall trainability.
Only the command's newly owned temporary index is removed. Evidence is retained.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
import time

from convert_dataset import key, read_chunks, verify
from forge_pos import PosReader, text_record

BATCH_ROWS = 10000
KEY_POLICY = 'board32 plus STM; score, result, castling, EP and clocks excluded'
TOOL_FILES = (Path(__file__), Path(__file__).with_name('convert_dataset.py'),
              Path(__file__).with_name('bullet_records.py'),
              Path(__file__).parents[1] / 'data/forge_pos.py')


def stat_identity(value):
    return {'device': value.st_dev, 'inode': value.st_ino, 'size': value.st_size,
            'mtime_ns': value.st_mtime_ns, 'ctime_ns': value.st_ctime_ns}


def now():
    return datetime.now(timezone.utc).isoformat()


def fingerprint(path, guard):
    """Hash bounded blocks, checking storage and file identity throughout."""
    path = Path(path)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        before = os.fstat(stream.fileno())
        blocks = 0
        while block := stream.read(4 * 1024 * 1024):
            digest.update(block)
            blocks += 1
            if blocks % 16 == 0:
                guard()
        after = os.fstat(stream.fileno())
    if stat_identity(before) != stat_identity(after) or stat_identity(after) != stat_identity(path.stat()):
        raise ValueError('file changed while hashing: ' + str(path))
    return {'path': str(path), 'bytes': after.st_size, 'sha256': digest.hexdigest(),
            'stat': stat_identity(after)}


def pin(path, bindings):
    reference = Path(os.path.abspath(path))
    resolved = reference.resolve(strict=True)
    bindings.append({'reference': str(reference), 'resolved': str(resolved)})
    return resolved


def sealed_snapshot(out, guard, bindings):
    chunks = read_chunks(out, verify=False)
    files = {}
    for name in ['config.json', 'COMPLETE.json', *(f'chunk_{i:06d}.json' for i in range(len(chunks)))]:
        path = pin(out / name, bindings)
        files[name] = fingerprint(path, guard)
    complete = json.loads((out / 'COMPLETE.json').read_text())
    if not isinstance(complete.get('chunk_receipts'), dict):
        raise ValueError('sealed COMPLETE.json requires chunk_receipts')
    for chunk in chunks:
        for name, metadata in chunk['files'].items():
            path = pin(out / name, bindings)
            observed = {'path': str(path), **metadata, 'stat': stat_identity(path.stat())}
            if name in files and files[name] != observed:
                raise ValueError('conflicting sealed file identities')
            files[name] = observed
    return chunks, files


def publish_new(path, report):
    """Publish a complete JSON atomically without replacing an existing artifact."""
    pending = path.with_name(path.name + '.pending')
    with pending.open('x', encoding='utf8', newline='\n') as stream:
        json.dump(report, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.link(pending, path)
    pending.unlink()  # only this command's owned staging file
    if os.name == 'posix':
        descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def run(args):
    report_path = Path(os.path.abspath(args.report))
    report_path = report_path.parent.resolve(strict=True) / report_path.name
    log_path = report_path.with_name(report_path.name + '.log.jsonl')
    claim_path = report_path.with_name(report_path.name + '.claim')
    for path in (report_path, log_path, claim_path, report_path.with_name(report_path.name + '.pending')):
        if path.exists() or path.is_symlink():
            raise FileExistsError('audit artifact already exists; use a fresh --report: ' + str(path))
    if args.min_free_mb < 0:
        raise ValueError('--min-free-mb must be nonnegative')
    bindings = []
    # These checks precede every write, including claim/log creation.
    out = pin(args.out, bindings)
    work = pin(args.work_dir or report_path.parent, bindings)
    if not out.is_dir():
        raise ValueError('--out must be a sealed converter directory')
    if not work.is_dir():
        raise ValueError('--work-dir must be an existing directory')
    if out == report_path.parent or out in report_path.parents:
        raise ValueError('--report must be outside the sealed converter directory')
    if out == work or out in work.parents:
        raise ValueError('--work-dir must be outside the sealed converter directory')
    # Reserve the artifact name before expensive reads. Interrupted runs leave
    # this small claim and the log; a rerun must choose a fresh report name.
    with claim_path.open('x', encoding='utf8') as claim:
        json.dump({'status': 'STARTED', 'started_utc': now(), 'report': str(report_path)}, claim)
        claim.write('\n')
        claim.flush()
        os.fsync(claim.fileno())
    report = {'schema': 1, 'status': 'BLOCKED', 'position_overlap_clear': False,
              'key_policy': KEY_POLICY, 'game_id_clearance': False,
              'scope': 'Position overlap only; expected identities must come from trusted full-shard manifests',
              'started_utc': now(), 'holdouts': [], 'output': {},
              'overlap_output_rows': None, 'overlap_unique_keys': None,
              'minimum_free_bytes': args.min_free_mb * 1024 * 1024}
    started = time.monotonic()
    index_path = None
    with log_path.open('x', encoding='utf8', newline='\n') as log:
        def event(stage, **fields):
            entry = {'utc': now(), 'stage': stage, **fields}
            line = json.dumps(entry, sort_keys=True)
            log.write(line + '\n')
            log.flush()
            print(line, file=sys.stderr, flush=True)

        def guard():
            locations = {report_path.parent, work} - {None}
            for location in locations:
                free = shutil.disk_usage(location).free
                if free < report['minimum_free_bytes']:
                    raise ValueError('free-space reserve reached at ' + str(location))

        try:
            event('start', report=str(report_path))
            guard()
            tool_identities = [fingerprint(path, guard) for path in TOOL_FILES]
            report['tool_sha256'] = {Path(item['path']).name: item['sha256'] for item in tool_identities}
            holdout_paths = []
            for shard in ('013', '014'):
                path = pin(getattr(args, 'holdout_' + shard), bindings)
                expected_hash = getattr(args, 'holdout_' + shard + '_sha256').lower()
                expected_rows = getattr(args, 'holdout_' + shard + '_rows')
                if not re.fullmatch(r'[0-9a-f]{64}', expected_hash) or expected_rows < 1:
                    raise ValueError('holdout ' + shard + ' requires a trusted SHA-256 and positive full-shard row count')
                item = {'shard_id': shard, 'identity': fingerprint(path, guard),
                        'expected_sha256': expected_hash, 'expected_rows': expected_rows,
                        'rows_scanned': 0, 'overlap_holdout_rows': 0}
                report['holdouts'].append(item)
                if item['identity']['sha256'] != expected_hash:
                    raise ValueError('holdout ' + shard + ' SHA-256 identity mismatch')
                with PosReader(path) as reader:
                    if reader.n != expected_rows:
                        raise ValueError('holdout ' + shard + ' full-shard row count mismatch')
                holdout_paths.append(path)
                event('holdout_identity_verified', shard_id=shard, **item['identity'], rows=expected_rows)
            if holdout_paths[0].samefile(holdout_paths[1]):
                raise ValueError('holdout 013 and 014 must identify distinct files')
            chunks, output_files = sealed_snapshot(out, guard, bindings)
            report['output'] = {'path': str(out), 'files': output_files}
            event('verifying_sealed_output', chunks=len(chunks))
            verified = verify(out)
            guard()
            report['output']['verification'] = verified
            report['output']['rows'] = verified['rows']
            event('sealed_output_verified', rows=verified['rows'])
            estimated_index_bytes = verified['rows'] * 96 + 16 * 1024 * 1024
            report['index_preflight'] = {'estimated_bytes': estimated_index_bytes,
                                         'bytes_per_output_row': 96, 'fixed_margin_bytes': 16 * 1024 * 1024}
            if shutil.disk_usage(work).free < report['minimum_free_bytes'] + estimated_index_bytes:
                raise ValueError('free-space reserve plus estimated index exceeds available scratch space')
            # Size scales with kept output keys, never with both complete
            # holdouts. A bounded SQLite cache prevents a Python set of keys.
            with tempfile.TemporaryDirectory(prefix='holdout-clearance-', dir=work) as scratch:
                index_path = Path(scratch) / 'output_keys.sqlite'
                event('owned_index_created', path=str(index_path))
                with closing(sqlite3.connect(index_path)) as db:
                    db.execute('PRAGMA cache_size=-16384')
                    db.execute('PRAGMA temp_store=FILE')
                    # Disposable index: no crash recovery or resume uses this
                    # database, so journal growth must not consume the reserve.
                    db.execute('PRAGMA journal_mode=OFF')
                    db.execute('PRAGMA synchronous=OFF')
                    db.execute('CREATE TABLE keys(key BLOB PRIMARY KEY, rows INTEGER NOT NULL, mask INTEGER NOT NULL DEFAULT 0) WITHOUT ROWID')

                    def checkpoint(stage, rows):
                        db.commit()
                        guard()
                        page_size = db.execute('PRAGMA page_size').fetchone()[0]
                        current_pages = db.execute('PRAGMA page_count').fetchone()[0]
                        # Include a small filesystem allocation margin, and cap
                        # SQLite growth before its next bounded transaction.
                        available = shutil.disk_usage(work).free - report['minimum_free_bytes'] - 1024 * 1024
                        pages = max(current_pages, current_pages + max(0, available) // page_size)
                        db.execute('PRAGMA max_page_count=' + str(min(pages, 2147483646)))
                        event(stage, rows=rows, index_bytes=index_path.stat().st_size)

                    checkpoint('index_started', 0)
                    output_rows = 0
                    for chunk in chunks:
                        with (out / chunk['text']).open(encoding='utf8') as rows:
                            for line in rows:
                                record, _ = text_record(line)
                                db.execute('INSERT INTO keys(key, rows) VALUES(?, 1) ON CONFLICT(key) DO UPDATE SET rows=rows+1', (key(record),))
                                output_rows += 1
                                if output_rows % BATCH_ROWS == 0:
                                    checkpoint('indexing_output', output_rows)
                    checkpoint('output_indexed', output_rows)
                    if output_rows != verified['rows']:
                        raise ValueError('sealed output row count changed during indexing')
                    report['output']['unique_keys'] = db.execute('SELECT COUNT(*) FROM keys').fetchone()[0]
                    for bit, (path, item) in enumerate(zip(holdout_paths, report['holdouts'])):
                        flag = 1 << bit
                        with PosReader(path) as reader:
                            for record in reader:
                                found = db.execute('UPDATE keys SET mask=mask|? WHERE key=?', (flag, key(record))).rowcount
                                item['rows_scanned'] += 1
                                item['overlap_holdout_rows'] += int(found > 0)
                                if item['rows_scanned'] % BATCH_ROWS == 0:
                                    checkpoint('scanning_holdout_' + item['shard_id'], item['rows_scanned'])
                        checkpoint('holdout_' + item['shard_id'] + '_scanned', item['rows_scanned'])
                        if item['rows_scanned'] != item['expected_rows']:
                            raise ValueError('holdout ' + item['shard_id'] + ' actual row count mismatch')
                        item['overlap_unique_keys'], item['overlap_output_rows'] = db.execute(
                            'SELECT COUNT(*), COALESCE(SUM(rows),0) FROM keys WHERE mask&? != 0', (flag,)).fetchone()
                    report['overlap_unique_keys'], report['overlap_output_rows'] = db.execute(
                        'SELECT COUNT(*), COALESCE(SUM(rows),0) FROM keys WHERE mask != 0').fetchone()
                    report['index'] = {'strategy': 'unique output keys', 'database_bytes': index_path.stat().st_size,
                                       'cache_kib': 16384, 'journal': 'OFF_DISPOSABLE_NO_RESUME',
                                       'owned_ephemeral_index_removed': False}
            report['index']['owned_ephemeral_index_removed'] = True
            event('rechecking_artifact_identities')
            for item in report['holdouts']:
                if fingerprint(item['identity']['path'], guard) != item['identity']:
                    raise ValueError('holdout ' + item['shard_id'] + ' changed during audit')
            current_chunks = sorted(path.name for path in out.glob('chunk_*.json'))
            if current_chunks != [f'chunk_{i:06d}.json' for i in range(len(chunks))]:
                raise ValueError('sealed output chunk set changed during audit')
            for name, expected in output_files.items():
                if fingerprint(expected['path'], guard) != expected:
                    raise ValueError('sealed output changed during audit: ' + name)
            for binding in bindings:
                if str(Path(binding['reference']).resolve(strict=True)) != binding['resolved']:
                    raise ValueError('input path binding changed during audit: ' + binding['reference'])
            for expected in tool_identities:
                if fingerprint(expected['path'], guard) != expected:
                    raise ValueError('audit tool source changed during audit: ' + expected['path'])
            guard()
            report['path_bindings'] = bindings
            report['position_overlap_clear'] = report['overlap_output_rows'] == 0
            report['status'] = ('FAIL' if not report['position_overlap_clear'] else
                                'PASS' if output_rows else 'BLOCKED_EMPTY_OUTPUT')
            event('finished', status=report['status'], overlap_output_rows=report['overlap_output_rows'],
                  overlap_unique_keys=report['overlap_unique_keys'], output_rows=output_rows)
        except Exception as error:
            report['status'] = 'BLOCKED'
            report['position_overlap_clear'] = False
            report['error'] = type(error).__name__ + ': ' + str(error)
            if index_path is not None:
                report.setdefault('index', {})['owned_ephemeral_index_removed'] = not index_path.exists()
            event('blocked', error=report['error'])
        report['elapsed_seconds'] = time.monotonic() - started
        report['finished_utc'] = now()
        log.flush()
        os.fsync(log.fileno())
    # Evidence publication must still work after the disk reserve blocks a run.
    report['log'] = fingerprint(log_path, lambda: None)
    publish_new(report_path, report)
    return report


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument('--out', required=True, help='Completed, sealed converter output directory')
    for shard in ('013', '014'):
        result.add_argument('--holdout-' + shard, required=True, help='Full FPOS for real' + shard)
        result.add_argument('--holdout-' + shard + '-sha256', required=True, help='Trusted full-shard SHA-256')
        result.add_argument('--holdout-' + shard + '-rows', required=True, type=int, help='Trusted full-shard row count')
    result.add_argument('--report', required=True, help='New JSON report path; .claim and .log.jsonl evidence are retained')
    result.add_argument('--work-dir', help='Existing scratch directory, default: report parent')
    result.add_argument('--min-free-mb', type=int, default=20480, help='Free-space reserve in MiB (default: 20480)')
    return result


def main():
    args = parser().parse_args()
    try:
        report = run(args)
    except Exception as error:
        print(json.dumps({'status': 'BLOCKED', 'position_overlap_clear': False,
                          'error': type(error).__name__ + ': ' + str(error)}), flush=True)
        return 2
    print(json.dumps(report, sort_keys=True), flush=True)
    return 0 if report['status'] == 'PASS' else 1 if report['status'] == 'FAIL' else 2


if __name__ == '__main__':
    sys.exit(main())

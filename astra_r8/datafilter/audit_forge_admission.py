"""Read-only replay of current filter admission over pinned closed sources.

This audits original source rows with records.selfplay_record, including Forge
FEN and promoted-material admission. It emits small receipts, never training data.
Each process uses one CPU worker; launch at most two partitions concurrently.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import time

sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import chess
import records
from records import selfplay_record
from filter_positions import low_priority, sha256
from profile_corpus import freeze_plan, stat_key, write_json
from resource_policy import storage_guard


def validator_identity():
    here = Path(__file__).resolve().parent
    files = [Path(__file__).resolve(), Path(chess.__file__).resolve(), Path(records.__file__).resolve(),
             *(here/name for name in ('pgn_input.py', 'profile_corpus.py', 'report_corpus.py',
                                     'filter_positions.py', 'resource_policy.py'))]
    return {str(path): sha256(path) for path in files}


class DigestReader(io.RawIOBase):
    """Hash original bytes while TextIOWrapper supplies universal logical lines."""
    def __init__(self, source, digest, md5):
        self.source, self.digest, self.md5 = source, digest, md5

    def readable(self):
        return True

    def readinto(self, buffer):
        count = self.source.readinto(buffer)
        if count:
            chunk = memoryview(buffer)[:count]
            self.digest.update(chunk)
            self.md5.update(chunk)
        return count


def scan_source(item, *, max_rows=None):
    if max_rows is not None and (type(max_rows) is not int or max_rows < 1):
        raise ValueError('max rows must be a positive integer')
    if (not re.fullmatch('[0-9a-f]{64}', item['expected_sha256'])
            or type(item['expected_data_rows']) is not int or item['expected_data_rows'] < 0):
        raise ValueError('invalid expected digest or row count')
    path = Path(item['path'])
    if stat_key(path) != item['identity']:
        raise ValueError('source identity changed before admission audit')
    if sha256(item['sidecar']) != item['sidecar_sha256']:
        raise ValueError('producer sidecar changed before admission audit')
    started = time.perf_counter()
    digest, md5 = hashlib.sha256(), hashlib.md5()
    rows = valid = invalid = known = unknown = skipped = 0
    examples = []
    complete = True
    with path.open('rb') as source, io.TextIOWrapper(
            io.BufferedReader(DigestReader(source, digest, md5)), encoding='utf-8-sig',
            errors='surrogateescape', newline=None) as logical:
        for source_row, line in enumerate(logical, 1):
            if max_rows is not None and rows >= max_rows:
                complete = False
                for block in iter(lambda: source.read(1024*1024), b''):
                    digest.update(block); md5.update(block)
                break
            try:
                # Preserve invalid bytes for a per-line error count, but reject
                # them even in comments, as the actual strict UTF-8 reader does.
                line.encode('utf-8')
                if not line.strip() or line.lstrip().startswith('#'):
                    skipped += 1
                    continue
                row = selfplay_record(line, str(path), source_row)
            except (ValueError, UnicodeError, OverflowError) as error:
                invalid += 1
                if len(examples) < 32:
                    examples.append({'source_row': source_row, 'error': str(error)[:400],
                                     'logical_line_sha256': hashlib.sha256(
                                         line.encode('utf-8', errors='surrogateescape')).hexdigest()})
            else:
                valid += 1
                known += int(row['has_result'])
                unknown += int(not row['has_result'])
            rows += 1
            if rows % 250000 == 0:
                storage_guard(allowance=4096)
                print(json.dumps({'event':'admission_progress', 'source':path.name,
                                  'rows':rows, 'invalid_rows':invalid,
                                  'seconds':time.perf_counter()-started}), flush=True)
    if stat_key(path) != item['identity']:
        raise ValueError('source identity changed during admission audit')
    if sha256(item['sidecar']) != item['sidecar_sha256']:
        raise ValueError('producer sidecar changed during admission audit')
    if digest.hexdigest() != item['expected_sha256'] or md5.hexdigest() != item['expected_md5']:
        raise ValueError('full source digest differs from pinned reference')
    if complete and rows != item['expected_data_rows']:
        raise ValueError('complete source row count differs from pinned reference')
    if valid+invalid != rows or known+unknown != valid:
        raise ValueError('admission accounting mismatch')
    seconds = time.perf_counter()-started
    return dict(path=str(path), status='PASS' if rows and not invalid else 'FAIL',
                complete_scan=complete, data_rows=rows, valid_rows=valid, invalid_rows=invalid,
                known_results=known, unknown_results=unknown, skipped_lines=skipped,
                invalid_examples=examples, sha256=digest.hexdigest(), md5=md5.hexdigest(),
                expected_sha256=item['expected_sha256'], expected_data_rows=item['expected_data_rows'],
                source_identity=item['identity'], sidecar_sha256=item['sidecar_sha256'],
                seconds=seconds, positions_per_second=rows/seconds if seconds else None)


def make_plan(profiles, *, partition=0, partitions=1, max_sources=None):
    from report_corpus import combine
    if type(partitions) is not int or partitions not in (1, 2) or type(partition) is not int or not 0 <= partition < partitions:
        raise ValueError('use one or two disjoint partitions')
    if max_sources is not None and (type(max_sources) is not int or max_sources < 1):
        raise ValueError('max sources must be positive')
    reference = combine(profiles)
    all_sources = sorted(reference['sources'], key=lambda row: row['path'])
    chosen = all_sources[partition::partitions]
    if max_sources is not None:
        chosen = chosen[:max_sources]
    plan = freeze_plan([row['path'] for row in chosen])
    for item, earlier in zip(plan['sources'], chosen):
        if item['identity'] != earlier['source_identity'] or item['sidecar_sha256'] != earlier['sidecar_sha256']:
            raise ValueError('reference source identity changed')
        item.update(expected_sha256=earlier['sha256'], expected_data_rows=earlier['data_rows'])
    plan.update(reference_profiles=reference['profile_inputs'], partition=partition, partitions=partitions,
                reference_source_names=sorted(Path(row['path']).name for row in all_sources),
                reference_rows=sum(row['data_rows'] for row in all_sources),
                complete_reference_set=len(chosen)==len(all_sources))
    return plan


def validate_reference_coverage(plan):
    """A complete-set claim requires the actual sealed reference, not a flag."""
    references = plan['reference_profiles']
    for item in references:
        if sha256(item['path']) != item['sha256']:
            raise ValueError('reference profile identity mismatch')
    if not plan['complete_reference_set']:
        return
    if not references:
        raise ValueError('complete reference claim has no bound profiles')
    from report_corpus import combine
    reference = combine([item['path'] for item in references])
    if reference['profile_inputs'] != references:
        raise ValueError('reference profile bindings differ')
    expected = {str(Path(item['path']).resolve()): (
        item['sha256'], item['data_rows'], item['source_identity'],
        item['sidecar_sha256'], item['expected_md5']) for item in reference['sources']}
    actual = {str(Path(item['path']).resolve()): (
        item['expected_sha256'], item['expected_data_rows'], item['identity'],
        item['sidecar_sha256'], item['expected_md5']) for item in plan['sources']}
    if actual != expected:
        raise ValueError('complete reference source coverage mismatch')


def run(plan, output, *, max_rows=None):
    low_priority()
    if (type(plan.get('schema')) is not int or plan['schema'] != 1
            or not isinstance(plan.get('sources'), list) or not plan['sources']
            or type(plan.get('complete_reference_set')) is not bool):
        raise ValueError('nonempty pinned admission plan required')
    if max_rows is not None and (type(max_rows) is not int or max_rows < 1):
        raise ValueError('max rows must be a positive integer')
    paths = [str(Path(item['path']).resolve()) for item in plan['sources']]
    if len(paths) != len(set(paths)) or any(Path(p).name.lower() in ('forge_selfplay_013.txt','forge_selfplay_014.txt') for p in paths):
        raise ValueError('duplicate source or excluded holdout')
    validate_reference_coverage(plan)
    output = Path(output)
    partial = output.with_name(output.name+'.partial')
    for path in (output, partial):
        storage_guard(path, allowance=2_000_000)
        if os.path.lexists(path):
            raise FileExistsError('refusing existing admission audit output')
    pins = validator_identity()
    started = datetime.now(timezone.utc).isoformat()
    partial.mkdir(parents=True)
    write_json(partial/'PLAN.json', plan)
    write_json(partial/'RUN.json', {'validator_files':pins, 'python':sys.version,
               'chess_version':chess.__version__, 'started_utc':started})
    reports = []
    for index, item in enumerate(plan['sources']):
        report = scan_source(item, max_rows=max_rows)
        write_json(partial/f'{index:03}.json', report)
        reports.append(report)
        print(json.dumps({'event':'admission_source_complete','source':item['path'],
                          'status':report['status'],'rows':report['data_rows']}),flush=True)
    if validator_identity() != pins:
        raise ValueError('validator source changed during admission audit')
    for item in plan['sources']:
        if stat_key(item['path']) != item['identity'] or sha256(item['sidecar']) != item['sidecar_sha256']:
            raise ValueError('source or sidecar changed before publication')
    for item in plan['reference_profiles']:
        if sha256(item['path']) != item['sha256']:
            raise ValueError('reference profile changed before publication')
    status = 'PASS' if all(row['status']=='PASS' for row in reports) else 'FAIL'
    result = dict(schema=1, status=status, training_ready=False, strength='UNPROVEN', workers=1,
                  started_utc=started, finished_utc=datetime.now(timezone.utc).isoformat(),
                  validator_files=pins, python=sys.version, chess_version=chess.__version__,
                  admission_contract='records.selfplay_record with current Forge FEN/material validation',
                  complete_reference_set=plan['complete_reference_set'] and all(r['complete_scan'] for r in reports),
                  reference_profiles=plan['reference_profiles'], sources=reports,
                  total_data_rows=sum(r['data_rows'] for r in reports),
                  total_invalid_rows=sum(r['invalid_rows'] for r in reports),
                  scope='read-only current-parser admission; no training, game-ID or full-corpus holdout clearance')
    write_json(partial/'SUMMARY.json', result)
    if status != 'PASS':
        raise ValueError('admission audit failed; preserved partial evidence')
    storage_guard(output, allowance=0)
    partial.rename(output)
    return result


if __name__ == '__main__':
    low_priority()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--reference-profiles', nargs='+', type=Path, required=True)
    parser.add_argument('--partition', type=int, default=0)
    parser.add_argument('--partitions', type=int, default=1)
    parser.add_argument('--max-sources', type=int)
    parser.add_argument('--max-rows', type=int)
    args = parser.parse_args()
    plan = make_plan(args.reference_profiles, partition=args.partition,
                     partitions=args.partitions, max_sources=args.max_sources)
    result = run(plan, args.output, max_rows=args.max_rows)
    print(json.dumps({'status':result['status'], 'rows':result['total_data_rows'],
                      'complete_reference_set':result['complete_reference_set'],
                      'strength':'UNPROVEN'}), flush=True)

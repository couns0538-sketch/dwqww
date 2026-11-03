"""Verify a complete disjoint union of current-parser admission receipts.

This does not reread every data byte or grant training/holdout clearance. Each
source's complete scan is bound to its sealed historical source profile, current
file identity and producer sidecar. Run before changing the audited validator.
"""
import argparse
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import sys

import chess

sys.dont_write_bytecode = True

from audit_forge_admission import validator_identity
from filter_positions import low_priority, sha256
from profile_corpus import stat_key, write_json
from report_corpus import combine, require_count
from resource_policy import storage_guard


class BoundInputs:
    def __init__(self):
        self.files = {}

    def read(self, path):
        path = Path(path).resolve()
        payload = path.read_bytes()
        before = hashlib.sha256(payload).hexdigest()
        value = json.loads(payload.decode('utf-8-sig'))
        if sha256(path) != before or self.files.get(str(path), before) != before:
            raise ValueError('receipt changed while reading: '+str(path))
        self.files[str(path)] = before
        return value

    def verify(self):
        if any(sha256(path) != digest for path, digest in self.files.items()):
            raise ValueError('bound receipt changed before publication')


def source_key(path):
    return str(Path(path).resolve()).casefold()


def verify_source(report, planned, earlier):
    if report.get('status') != 'PASS' or report.get('complete_scan') is not True:
        raise ValueError('incomplete or failed source admission')
    count = require_count(report.get('data_rows'), 'data_rows')
    require_count(report.get('expected_data_rows'), 'expected_data_rows')
    for field in ('valid_rows', 'invalid_rows', 'known_results', 'unknown_results', 'skipped_lines'):
        require_count(report.get(field), field)
    if (not count or report['valid_rows'] != count or report['invalid_rows'] != 0
            or report['known_results']+report['unknown_results'] != count
            or report.get('invalid_examples') != []):
        raise ValueError('admission source accounting mismatch')
    seconds = report.get('seconds')
    rate = report.get('positions_per_second')
    if (type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds <= 0
            or type(rate) not in (int, float) or not math.isfinite(rate)
            or not math.isclose(rate, count/seconds, rel_tol=1e-12)):
        raise ValueError('invalid source timing')
    fields = {
        'sha256': ('expected_sha256', 'sha256'),
        'expected_sha256': ('expected_sha256', 'sha256'),
        'data_rows': ('expected_data_rows', 'data_rows'),
        'expected_data_rows': ('expected_data_rows', 'data_rows'),
        'md5': ('expected_md5', 'expected_md5'),
        'source_identity': ('identity', 'source_identity'),
        'sidecar_sha256': ('sidecar_sha256', 'sidecar_sha256'),
    }
    for actual, (plan_key, prior_key) in fields.items():
        if report.get(actual) != planned.get(plan_key) or report.get(actual) != earlier.get(prior_key):
            raise ValueError('admission differs from sealed reference: '+actual)
    if any(report[key] != earlier[key] for key in ('known_results','unknown_results')):
        raise ValueError('source coverage differs from sealed reference')
    if (stat_key(report['path']) != report['source_identity']
            or source_key(planned['sidecar']) != source_key(report['path']+'.md5')
            or sha256(planned['sidecar']) != report['sidecar_sha256']):
        raise ValueError('original source identity or sidecar changed')
    return count


def verify(profiles, summaries):
    """Return a proof only when every original reference source occurs once."""
    if not summaries or len(summaries) > 2:
        raise ValueError('one or two completed admission partitions required')
    pins = validator_identity()
    verifier_sha = sha256(__file__)
    inputs = BoundInputs()
    reference = combine(profiles)
    for item in reference['profile_inputs']:
        inputs.read(item['path'])
        if inputs.files[str(Path(item['path']).resolve())] != item['sha256']:
            raise ValueError('reference profile changed')
    expected = {source_key(row['path']): row for row in reference['sources']}
    seen, partitions, reports, starts, finishes = set(), set(), [], [], []
    runtime = None
    for supplied in summaries:
        path = Path(supplied).resolve()
        if path.name != 'SUMMARY.json' or path.parent.name.endswith('.partial'):
            raise ValueError('published admission SUMMARY.json required')
        summary = inputs.read(path)
        plan = inputs.read(path.parent/'PLAN.json')
        run = inputs.read(path.parent/'RUN.json')
        if (type(summary.get('schema')) is not int or summary['schema'] != 1
                or summary.get('status') != 'PASS' or summary.get('training_ready') is not False
                or summary.get('strength') != 'UNPROVEN' or type(summary.get('workers')) is not int
                or summary['workers'] != 1 or summary.get('validator_files') != pins
                or run.get('validator_files') != pins):
            raise ValueError('admission identity, scope or status mismatch')
        this_runtime = (summary.get('python'), summary.get('chess_version'))
        if (this_runtime != (sys.version, chess.__version__)
                or this_runtime != (run.get('python'), run.get('chess_version'))
                or runtime is not None and runtime != this_runtime):
            raise ValueError('partition runtime identity mismatch')
        runtime = this_runtime
        if summary.get('reference_profiles') != reference['profile_inputs'] or plan.get('reference_profiles') != reference['profile_inputs']:
            raise ValueError('partition reference binding mismatch')
        partition = plan.get('partition')
        if (type(plan.get('schema')) is not int or plan['schema'] != 1
                or type(partition) is not int or not 0 <= partition < len(summaries)
                or partition in partitions or type(plan.get('partitions')) is not int
                or plan['partitions'] != len(summaries)):
            raise ValueError('partition index/count mismatch')
        partitions.add(partition)
        expected_complete = len(summaries) == 1
        if (plan.get('complete_reference_set') is not expected_complete
                or summary.get('complete_reference_set') is not expected_complete):
            raise ValueError('individual partition overstates reference coverage')
        if (plan.get('reference_source_names') != sorted(Path(row['path']).name for row in reference['sources'])
                or type(plan.get('reference_rows')) is not int
                or plan['reference_rows'] != reference['totals']['data_rows']):
            raise ValueError('reference count/name contract mismatch')
        local_reports, planned = summary.get('sources'), plan.get('sources')
        if not isinstance(local_reports, list) or not local_reports or not isinstance(planned, list) or len(local_reports) != len(planned):
            raise ValueError('partition source list mismatch')
        planned_paths = [source_key(row['path']) for row in planned]
        reference_paths = [source_key(row['path']) for row in sorted(reference['sources'], key=lambda row: row['path'])][partition::len(summaries)]
        if planned_paths != reference_paths:
            raise ValueError('partition does not match disjoint reference selection')
        local_rows = 0
        for index, (row, item) in enumerate(zip(local_reports, planned)):
            key = source_key(row['path'])
            if key in seen or key not in expected or key != source_key(item['path']):
                raise ValueError('duplicate, unexpected or misaligned source')
            if inputs.read(path.parent/f'{index:03}.json') != row:
                raise ValueError('summary differs from sealed source report')
            seen.add(key)
            local_rows += verify_source(row, item, expected[key])
            reports.append(row)
        if (require_count(summary.get('total_data_rows'), 'total_data_rows') != local_rows
                or require_count(summary.get('total_invalid_rows'), 'total_invalid_rows') != 0):
            raise ValueError('partition total mismatch')
        start, finish = (datetime.fromisoformat(summary[key]) for key in ('started_utc', 'finished_utc'))
        if start.tzinfo is None or finish.tzinfo is None or finish < start or run.get('started_utc') != summary['started_utc']:
            raise ValueError('invalid admission timestamps')
        starts.append(start); finishes.append(finish)
    if seen != set(expected) or partitions != set(range(len(summaries))):
        raise ValueError('incomplete disjoint reference union')
    total = sum(row['data_rows'] for row in reports)
    if total != reference['totals']['data_rows']:
        raise ValueError('union total differs from original reference')
    for row in reports:
        if (stat_key(row['path']) != row['source_identity']
                or sha256(row['path']+'.md5') != row['sidecar_sha256']):
            raise ValueError('original source changed before union publication')
    inputs.verify()
    if validator_identity() != pins or sha256(__file__) != verifier_sha:
        raise ValueError('validator/verifier changed during union verification')
    return dict(schema=1, status='PASS', strength='UNPROVEN', training_ready=False,
                complete_reference_set=True, total_data_rows=total, total_invalid_rows=0,
                sources=sorted(reports, key=lambda row: row['path']), validator_files=pins,
                python=sys.version, chess_version=chess.__version__,
                verifier_sha256=verifier_sha, bound_receipts=inputs.files,
                elapsed_span_seconds=(max(finishes)-min(starts)).total_seconds(),
                source_compute_seconds=sum(row['seconds'] for row in reports),
                timing_note='Read-only admission scans, not filtering or loader throughput.',
                scope='complete current-parser admission; no training, game-ID or full-corpus holdout clearance')


def run(profiles, summaries, output):
    low_priority()
    output = Path(output)
    partial = output.with_name(output.name+'.partial')
    if os.path.lexists(output) or os.path.lexists(partial):
        raise FileExistsError('refusing existing admission union output')
    storage_guard(output, allowance=4_000_000)
    result = verify(profiles, summaries)
    partial.mkdir(parents=True)
    write_json(partial/'SUMMARY.json', result)
    storage_guard(output, allowance=0)
    partial.rename(output)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--reference-profiles', nargs='+', type=Path, required=True)
    parser.add_argument('--summaries', nargs='+', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.reference_profiles, args.summaries, args.output)
    print(json.dumps({'status':result['status'], 'rows':result['total_data_rows'], 'strength':'UNPROVEN'}))

#!/usr/bin/env python3
"""Verify the fresh Job 41 controls and their original Job 40 baselines."""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import chess


HERE = Path(__file__).resolve().parent
WORK = Path('/workspace/work')
JOB40 = 'd80e3215edc1806817d77bea5b52b99749b64488'
JOB40_ARCHIVE = Path('forge-combo29/sol/job40')
JOB41_ARCHIVE = Path('forge-combo29/sol/job41')
for prior in (HERE.parent / 'job40', WORK / 'sol-job40'):
    if (prior / 'independent40.py').is_file():
        sys.path.insert(0, str(prior))
        break
else:
    raise SystemExit('The Job 40 record reader is missing.')

from independent40 import LIMITS, PC20_SHA, Reader, compare, read_run, require


def archived_blob(repo, path):
    data = subprocess.check_output(
        ['git', '-C', str(repo), 'show', f'{JOB40}:{path.as_posix()}'],
        env={**os.environ, 'GIT_NO_LAZY_FETCH': '1'},
    )
    require(len(data) <= 20_000_000, f'{path}: file over archive size limit')
    return data


def check_limit(limit, prior, args, reader, pc20):
    settings = prior['settings']
    require(prior['gate']['passes'] and prior['settings_complete'] == len(settings) == prior['live'] == 40
            and not prior['no_change_seen'] and all(row['reading'] == 'LIVE' for row in settings),
            f'{limit}: Job 40 did not finish with 40 LIVE settings')

    labels = [('BASE-a', None), ('BASE-b', None)]
    if limit == 'N2':
        labels.extend((
            ('EvalSwingMax300', ('EvalSwingMax', 300)),
            ('LmrQuietBase101', ('LmrQuietBase', 101)),
        ))
    runs = {
        label: read_run(reader, args.raw / limit / label, JOB41_ARCHIVE / 'raw' / limit / label,
                        label, limit, option, pc20, args.check_moves)
        for label, option in labels
    }
    base_a, base_b = runs['BASE-a'], runs['BASE-b']
    old_dir = JOB40_ARCHIVE / 'raw' / limit / 'BASE-a'
    old_bytes = archived_blob(args.repo, old_dir / 'records.txt')
    old_hash = sha256(old_bytes).hexdigest()
    old_meta = json.loads(archived_blob(args.repo, old_dir / 'run.json'))
    old_receipt = prior['runs'][f'{limit}/BASE-a']
    require(old_meta['status'] == old_receipt['status'] == 'complete'
            and old_meta['records_sha256'] == old_receipt['records_sha256'] == old_hash,
            f'{limit}: Job 40 baseline archive and receipts disagree')

    hashes = {
        'BASE-a': base_a[0].get('records_sha256'),
        'BASE-b': base_b[0].get('records_sha256'),
        'Job40 BASE-a': old_hash,
    }
    baseline = compare(base_a, base_b)
    baseline['matches_job40'] = {
        name: run[0]['status'] == 'complete' and run[1] == old_bytes
        for name, run in (('BASE-a', base_a), ('BASE-b', base_b))
    }
    baseline['passes'] = baseline['reading'] == 'IDENTICAL' and all(baseline['matches_job40'].values())
    checks = {'BASE': baseline}
    if limit == 'N2':
        for label, expected in (('EvalSwingMax300', 'IDENTICAL'), ('LmrQuietBase101', 'DIFFERS')):
            observed = compare(base_a, runs[label])
            checks[label] = {**observed, 'expected': expected, 'passes': observed['reading'] == expected}
    return {
        'prior_settings_live': prior['live'],
        'prior_settings_complete': prior['settings_complete'],
        'widened_settings': prior['no_change_seen'],
        'baseline_sha256': hashes,
        'checks': checks,
        'runs': {label: result for label, (result, _data, _groups) in runs.items()},
        'passes': all(check['passes'] for check in checks.values()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw', type=Path)
    parser.add_argument('--limit', choices=LIMITS)
    parser.add_argument('--repo', type=Path, default=WORK / 'sol-job1' / 'repo')
    parser.add_argument('--rev', help='also compare live Job 41 files with this archived revision')
    parser.add_argument('--pc20', type=Path, default=WORK / 'sol-job2' / 'pc20-options.txt')
    parser.add_argument('--check-moves', action='store_true')
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    require(chess.__version__ == '1.11.2', 'Expected python-chess 1.11.2')
    prior = json.loads(archived_blob(args.repo, JOB40_ARCHIVE / 'analysis.json'))['limits']
    pc20 = args.pc20.read_bytes()
    require(sha256(pc20).hexdigest() == PC20_SHA, 'PC20 option hash differs')
    with Reader(args.repo if args.rev else None, args.rev) as reader:
        limits = {
            limit: check_limit(limit, prior[limit], args, reader, pc20.decode('ascii').splitlines())
            for limit in ((args.limit,) if args.limit else LIMITS)
        }
        result = {
            'prior_job_commit': JOB40,
            'limits': limits,
            'archive_blobs_verified': reader.verified,
            'passes': all(limit['passes'] for limit in limits.values()),
        }
    output = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.json:
        args.json.write_text(output)
    print(output, end='')
    return 0 if result['passes'] else 1


if __name__ == '__main__':
    sys.exit(main())

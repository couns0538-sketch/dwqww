#!/usr/bin/env python3
"""Read-only validation of a declared engine experiment's evidence record.

IDEA_SOURCE: Forge's exact-behavior and immutable-evidence workflow. Original code.
This checks record consistency and artifact bytes, not the truth of log contents,
Elo, SPRT, platform qualification, or experimental independence. No engine runs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PureWindowsPath
import re
import sys

SCOPE = ('Record consistency and current artifact hashes only; declared checks and '
         'bench counts are not independently reproduced or parsed from logs. '
         'PASS does not establish speed, playing strength or platform qualification.')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key: ' + key)
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('nonfinite JSON number: ' + value)


def finite_float(value):
    number = float(value)
    require(math.isfinite(number), 'nonfinite JSON number: ' + value)
    return number


def reference(value, label):
    require(isinstance(value, dict), label + ' must be an object')
    name, digest = value.get('path'), value.get('sha256')
    require(isinstance(name, str) and name and '\x00' not in name,
            label + '.path must be a nonempty relative path')
    require(not Path(name).is_absolute() and not PureWindowsPath(name).anchor
            and '\\' not in name and ':' not in name,
            label + '.path must use relative forward-slash syntax')
    require(isinstance(digest, str) and re.fullmatch(r'[0-9a-fA-F]{64}', digest),
            label + '.sha256 must contain 64 hexadecimal digits')
    return {'path': name, 'sha256': digest.lower()}


def identity(stat):
    value = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
    return value + (stat.st_ctime_ns,) if os.name == 'posix' else value


def hash_file(path):
    require(path.is_file(), 'artifact is not an existing regular file')
    with path.open('rb') as stream:
        before = identity(os.fstat(stream.fileno()))
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
        require(before == identity(os.fstat(stream.fileno())) == identity(path.stat()),
                'artifact identity changed while hashing')
    return digest.hexdigest()


def check_record(filename):
    result = {'status': 'INVALID', 'scope': SCOPE, 'strength_claim': 'UNVERIFIED',
              'checks': [], 'artifacts': [], 'issues': []}
    try:
        source = Path(filename).absolute()
        with source.open('r', encoding='utf-8-sig') as stream:
            record = json.load(stream, object_pairs_hook=unique_object,
                               parse_constant=reject_constant, parse_float=finite_float)
        require(isinstance(record, dict), 'record must be an object')
        require(type(record.get('schema')) is int and record['schema'] == 1, 'schema must be integer 1')
        require(record.get('kind') in ('exact-speed', 'correctness', 'strength'), 'invalid experiment kind')
        result['kind'] = record['kind']
        references = []
        result['commits'] = {}
        for side in ('baseline', 'candidate'):
            build = record.get(side)
            require(isinstance(build, dict), side + ' must be an object')
            commit = build.get('commit')
            require(isinstance(commit, str) and re.fullmatch(r'[0-9a-fA-F]{40}', commit),
                    side + '.commit must contain the full 40-digit SHA-1')
            result['commits'][side] = commit.lower()
            artifacts = build.get('artifacts')
            require(isinstance(artifacts, list) and artifacts, side + '.artifacts must be nonempty')
            references.extend((side, reference(item, side + '.artifacts')) for item in artifacts)
        checks = record.get('checks')
        require(isinstance(checks, list) and checks, 'checks must be a nonempty list')
        names = set()
        for check in checks:
            require(isinstance(check, dict), 'each check must be an object')
            name, status = check.get('name'), check.get('status')
            require(isinstance(name, str) and name.strip() and name not in names,
                    'check names must be nonempty and unique')
            names.add(name)
            require(status in ('PASS', 'FAIL', 'UNVERIFIED'), 'invalid check status for ' + name)
            if status in ('PASS', 'FAIL') or 'evidence' in check:
                references.append(('check:' + name, reference(check.get('evidence'), name + '.evidence')))
            result['checks'].append({'name': name, 'status': status})
        bench = record.get('bench')
        if record['kind'] == 'exact-speed' or 'bench' in record:
            require(isinstance(bench, dict), 'bench is required for exact-speed')
            for side in ('expected', 'baseline', 'candidate'):
                vector = bench.get(side)
                require(isinstance(vector, dict) and vector, 'bench.' + side + ' must be nonempty')
                require(all(re.fullmatch(r'[0-9]+', depth) for depth in vector), 'bench depths must be decimal strings')
                require(all(type(count) is int and count >= 0 for count in vector.values()),
                        'bench counts must be nonnegative integers, not booleans')
            require(bench['expected'].keys() == bench['baseline'].keys() == bench['candidate'].keys(),
                    'bench vectors must contain exactly the same depths')
            for depth, expected in bench['expected'].items():
                for side in ('baseline', 'candidate'):
                    if bench[side][depth] != expected:
                        result['issues'].append(f'bench {side} d{depth}: {bench[side][depth]} != pin {expected}')
            result['bench'] = bench
        for label, ref in references:
            observed = dict(ref, role=label, status='FAIL')
            try:
                observed['observed_sha256'] = hash_file(source.parent / ref['path'])
                if observed['observed_sha256'] == ref['sha256']:
                    observed['status'] = 'PASS'
                else:
                    observed['error'] = 'SHA-256 mismatch'
            except (OSError, ValueError, RuntimeError) as error:
                observed['error'] = str(error)
            result['artifacts'].append(observed)
            if observed['status'] != 'PASS':
                result['issues'].append(label + ': ' + ref['path'] + ': ' + observed['error'])
        result['issues'].extend(check['name'] + ': ' + check['status'] for check in result['checks']
                                if check['status'] != 'PASS')
        result['status'] = 'FAIL' if result['issues'] else 'PASS'
    except (OSError, ValueError, TypeError, RuntimeError) as error:
        result['status'] = 'INVALID'
        result['issues'].append(str(error))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path, help='schema-1 JSON; artifact paths are relative to this file')
    args = parser.parse_args()
    result = check_record(args.record)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return {'PASS': 0, 'FAIL': 1, 'INVALID': 2}[result['status']]


if __name__ == '__main__':
    sys.exit(main())

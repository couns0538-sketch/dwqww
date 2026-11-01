#!/usr/bin/env python3
"""Snapshot TM source, verify a lock-applicable patch, run the installed evidence checker.

Input JSON declares checks [{name,status,evidence?}] and optional baseline_artifacts /
candidate_artifacts lists. File names in that input are relative to its parent.
Output is a new, self-contained directory with portable checker references.
Statuses are declarations, not conclusions inferred from arbitrary log strings.
Missing required checks become UNVERIFIED. Exit status is the actual checker exit.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
import re
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile

BASE = '905e2325caeabea92b1017b22b434218a43145a7'
SCOPES = ['CMakeLists.txt', 'include', 'src', 'tests']
REQUIRED = ['data_50000_iterations', 'fit_grouped_holdout', '1_off_on_bench_and_perft',
            '2_live_timed', '3_average_time_200_games', '4_hard_limits',
            '5_absurd_clamp', '6_asan_ubsan']
DEFAULT_CHECKER = (Path.home() / '.codex/plugins/cache/forge-engine-tools/forge-cpp-lab/1.0.0'
                   '/skills/cpp-chess-engineering/scripts/check_evidence.py')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE)


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)


def json_new(path, value):
    write_new(path, (json.dumps(value, indent=2, allow_nan=False) + '\n').encode())


def ref(path, output):
    return dict(path=path.relative_to(output).as_posix(), sha256=sha(path.read_bytes()))


def copy_artifact(source, output, index):
    # Copy bytes, not text: Git newline conversion must never alter evidence.
    source = source.resolve(strict=True)
    before = source.stat()
    data = source.read_bytes()
    after = source.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError(f'artifact changed while reading: {source}')
    target = output / 'artifacts' / f'{index:03d}_{source.name}'
    write_new(target, data)
    return ref(target, output)


def source_snapshot(repo, commit, output, label):
    archive = git(repo, 'archive', '--format=tar', commit, '--', *SCOPES)
    target = output / (label + '-source.tar')
    write_new(target, archive)
    manifest = {}
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        for member in stream:
            if member.isfile():
                manifest[member.name] = sha(stream.extractfile(member).read())
    json_new(output / (label + '-source.json'), dict(commit=commit, files=manifest))
    return archive, ref(target, output)


def verify_patch(base_archive, patch, scratch):
    scratch.mkdir(parents=True, exist_ok=False)
    with tarfile.open(fileobj=io.BytesIO(base_archive)) as stream:
        for member in stream:
            name = PurePosixPath(member.name)
            if name.is_absolute() or '..' in name.parts or member.issym() or member.islnk():
                raise ValueError('unsafe archive member: ' + member.name)
            target = scratch.joinpath(*name.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                write_new(target, stream.extractfile(member).read())
    env = dict(os.environ)
    # Permit git apply outside any repository; do not discover the shared main
    # repository above the authorized scratch directory.
    env['GIT_CEILING_DIRECTORIES'] = str(scratch.parent.resolve())
    command = ['git', '-C', str(scratch), 'apply', '--check', '--verbose', '-p1', str(patch)]
    result = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return dict(command=command, exit_code=result.returncode,
                stdout=result.stdout.decode(errors='replace'), stderr=result.stderr.decode(errors='replace'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='new directory, immutable once written')
    parser.add_argument('--scratch', type=Path, required=True, help='new extraction directory under authorized scratch')
    parser.add_argument('--candidate', default='HEAD')
    parser.add_argument('--baseline', default=BASE)
    parser.add_argument('--checker', type=Path, default=DEFAULT_CHECKER)
    args = parser.parse_args(argv)
    args.repo = args.repo.resolve()
    args.output = args.output.resolve()
    args.scratch = args.scratch.resolve()
    args.input = args.input.resolve()
    if not args.checker.is_file():
        parser.error('installed evidence checker not found; supply --checker')
    baseline = git(args.repo, 'rev-parse', args.baseline + '^{commit}').decode().strip()
    candidate = git(args.repo, 'rev-parse', args.candidate + '^{commit}').decode().strip()
    dirty = git(args.repo, 'diff', '--name-only', candidate, '--', *SCOPES).decode().strip()
    untracked = git(args.repo, 'ls-files', '--others', '--exclude-standard', '--', *SCOPES).decode().strip()
    if dirty or untracked:
        raise ValueError('commit engine changes before packaging; dirty/untracked: ' + dirty + '\n' + untracked)
    declared = json.loads(args.input.read_text(encoding='utf-8-sig'))
    checks = declared.get('checks', [])
    names = [c['name'] for c in checks]
    if len(names) != len(set(names)) or any(c['status'] not in ('PASS', 'FAIL', 'UNVERIFIED') for c in checks):
        raise ValueError('duplicate check names or invalid declared statuses')
    args.output.mkdir(parents=True, exist_ok=False)
    base_tar, base_ref = source_snapshot(args.repo, baseline, args.output, 'baseline')
    _, candidate_ref = source_snapshot(args.repo, candidate, args.output, 'candidate')
    patch = args.output / 'tmfit-lock.patch'
    write_new(patch, git(args.repo, 'diff', '--binary', '--full-index', '--no-ext-diff',
                         '--src-prefix=a/', '--dst-prefix=b/', baseline, candidate, '--', *SCOPES))
    patch_check = verify_patch(base_tar, patch, args.scratch)
    json_new(args.output / 'patch-check.json', patch_check)
    record = dict(schema=1, kind='correctness', baseline=dict(commit=baseline, artifacts=[base_ref]),
                  candidate=dict(commit=candidate, artifacts=[candidate_ref, ref(patch, args.output)]), checks=[])
    artifact_index = 0
    for side in ('baseline', 'candidate'):
        for path in declared.get(side + '_artifacts', []):
            record[side]['artifacts'].append(copy_artifact(args.input.parent / path, args.output, artifact_index))
            artifact_index += 1
    for check in checks:
        item = {k: check[k] for k in ('name', 'status')}
        if 'evidence' in check:
            item['evidence'] = copy_artifact(args.input.parent / check['evidence'], args.output, artifact_index)
            artifact_index += 1
        elif check['status'] != 'UNVERIFIED':
            raise ValueError('PASS/FAIL needs evidence: ' + check['name'])
        record['checks'].append(item)
    for name in REQUIRED:
        if name not in names:
            record['checks'].append(dict(name=name, status='UNVERIFIED'))
    # Verify producer-published hashes as well as sealing currently observed
    # bytes. Rehashing changed evidence alone would otherwise hide corruption.
    receipt_items = []
    for manifest_name in declared.get('hash_manifests', []):
        manifest_path = args.input.parent / manifest_name
        for name, expected in json.loads(manifest_path.read_text(encoding='utf-8-sig')).items():
            if Path(name).name != name or not re.fullmatch('[0-9a-f]{64}', expected):
                raise ValueError('invalid hash-manifest entry: ' + name)
            source = manifest_path.parent / name
            artifact = copy_artifact(source, args.output, artifact_index)
            artifact_index += 1
            record['candidate']['artifacts'].append(artifact)
            receipt_items.append(dict(file=artifact['path'], expected_sha256=expected,
                                      actual_sha256=artifact['sha256']))
    if 'fit_manifest' in declared:
        fit_path = args.input.parent / declared['fit_manifest']
        fit = json.loads(fit_path.read_text(encoding='utf-8-sig'))
        sample = fit_path.parent / fit['sample']['path']
        artifact = copy_artifact(sample, args.output, artifact_index)
        record['candidate']['artifacts'].append(artifact)
        receipt_items.append(dict(file=artifact['path'], expected_sha256=fit['sample']['sha256'],
                                  actual_sha256=artifact['sha256']))
    if receipt_items:
        json_new(args.output / 'producer-hash-receipts.json', receipt_items)
        record['checks'].append(dict(name='producer_hash_receipts_match',
            status='PASS' if all(r['expected_sha256'] == r['actual_sha256'] for r in receipt_items) else 'FAIL',
            evidence=ref(args.output / 'producer-hash-receipts.json', args.output)))
    record['checks'].append(dict(name='patch_applies_to_recorded_base',
                                 status='PASS' if patch_check['exit_code'] == 0 else 'FAIL',
                                 evidence=ref(args.output / 'patch-check.json', args.output)))
    json_new(args.output / 'record.json', record)
    command = [sys.executable, str(args.checker.resolve()), str(args.output / 'record.json')]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    write_new(args.output / 'checker.stdout.json', result.stdout)
    write_new(args.output / 'checker.stderr.txt', result.stderr)
    json_new(args.output / 'execution.json', dict(command=command, exit_code=result.returncode,
             checker_sha256=sha(args.checker.read_bytes()), helper_sha256=sha(Path(__file__).read_bytes()),
             input_sha256=sha(args.input.read_bytes()), strength='UNPROVEN'))
    print(result.stdout.decode(errors='replace'))
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())

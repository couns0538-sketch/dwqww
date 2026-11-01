#!/usr/bin/env python3
"""Seal exact AL1 s198 + the supplied CR patch, without claiming HEAD is its source.

No builds, engines, checkout, index writes, or old-package changes. The installed
C++ evidence checker reports missing qualification checks as UNVERIFIED/exit 1.
See LOCK_PACKAGE_USAGE.md for the declaration format and identity contract.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import subprocess
import sys
import tarfile

BASE = '294dbed3a15dfd821aaf9d4edc6e5f62832fd460'
CR_PATCH_SHA256 = 'ef09b342368efd01876bf771726d58cc84d73ec2960b5a70ead710ff0e88d9e3'
NEW_FILES = {'src/search/tmfit.hpp', 'tests/tmfit_tests.cpp'}
REQUIRED = ('data_50000_iterations', 'fit_grouped_holdout', '1_off_on_bench_and_perft',
            '2_live_timed', '3_average_time_200_games', '4_hard_limits',
            '5_absurd_clamp', '6_asan_ubsan')
TRAINING_CHECKS = frozenset(REQUIRED[:2])
SOURCE_CHECKS = {'exact_base_and_cr_patch', 'patch_applies_and_matches_stage'}
PRODUCER_IDENTITY_AUDIT = {
    'automatic_verification': False,
    'helper_scope': 'Declared candidate_id equality and supplied evidence-file hashes only; '
                    'producer build/binary/test identity links are not parsed or authenticated.',
    'required_review': 'Main agent and Code Review must explicitly audit the build source hashes '
                       'to the binary SHA256, then that binary to each test manifest; for CI, '
                       'audit the exact base and applied patch identity in the build job.',
}
DEFAULT_CHECKER = (Path.home() / '.codex/plugins/cache/forge-engine-tools/forge-cpp-lab/1.0.0'
                   '/skills/cpp-chess-engineering/scripts/check_evidence.py')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)


def safe_source_name(name):
    p = PurePosixPath(name)
    if (not name or p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name
            or '\x00' in name or p.as_posix() != name or PureWindowsPath(name).anchor):
        raise ValueError('unsafe source path: ' + name)
    return name


def stable_read(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError('source/evidence is not a regular file: ' + str(path))
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns')
    if any(getattr(before, key) != getattr(after, key) for key in fields):
        raise ValueError('file changed while reading: ' + str(path))
    return data


def git_source(repo, commit):
    """Read exact blobs, avoiding archive/export substitutions and checkout EOLs."""
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('base must be a full lowercase commit SHA')
    prefix = ['git', '-C', str(repo)]
    entries = subprocess.check_output(prefix + ['ls-tree', '-rz', commit], stderr=subprocess.PIPE)
    objects = []
    for entry in entries.split(b'\x00'):
        if not entry:
            continue
        meta, raw_name = entry.split(b'\t', 1)
        mode, kind, oid = meta.split()
        name = safe_source_name(raw_name.decode('utf-8'))
        if kind != b'blob' or mode not in (b'100644', b'100755'):
            raise ValueError('non-regular Git source path: ' + name)
        objects.append((name, oid))
    data = subprocess.check_output(prefix + ['cat-file', '--batch'],
                                   input=b''.join(oid + b'\n' for _, oid in objects),
                                   stderr=subprocess.PIPE)
    files, offset = {}, 0
    for name, expected_oid in objects:
        end = data.index(b'\n', offset)
        oid, kind, length = data[offset:end].split()
        length = int(length)
        if oid != expected_oid or kind != b'blob' or length < 0:
            raise ValueError('unexpected cat-file response')
        blob = data[end + 1:end + 1 + length]
        if len(blob) != length or data[end + 1 + length:end + 2 + length] != b'\n':
            raise ValueError('truncated cat-file response')
        if name in files:
            raise ValueError('duplicate source path')
        files[name] = blob
        offset = end + length + 2
    if offset != len(data) or not files:
        raise ValueError('unexpected or empty Git source response')
    return files


def source_manifest(files):
    return {safe_source_name(name): sha(data) for name, data in sorted(files.items())}


def source_tar(files):
    """Stable sorted USTAR metadata; preserve each blob byte, including line ends."""
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        for name, data in sorted(files.items()):
            member = tarfile.TarInfo(safe_source_name(name))
            member.size, member.mode, member.mtime = len(data), 0o644, 0
            member.uid = member.gid = 0
            member.uname = member.gname = ''
            archive.addfile(member, io.BytesIO(data))
    return output.getvalue()


def candidate_identity(base, patch_sha256, files):
    identity = {'base_commit': base, 'patch_sha256': patch_sha256,
                'source_manifest_sha256': sha(canonical(source_manifest(files)))}
    return dict(identity, candidate_id=sha(canonical(identity)))


def apply_verify(blobs, patch, scratch, stage, expected_files):
    """Mutate only a new scratch directory; stage is an independent read-only witness."""
    scratch = scratch.resolve()
    stage = stage.resolve(strict=True)
    patch = patch.resolve(strict=True)
    scratch.mkdir(parents=True, exist_ok=False)
    for name, data in blobs.items():
        write_new(scratch / safe_source_name(name), data)
    env = dict(os.environ)
    # Ignore inherited Git plumbing and prevent discovery of a shared repo above
    # scratch. git apply works without a repository; no index is used or touched.
    for key in list(env):
        if key.startswith('GIT_'):
            del env[key]
    env['GIT_CEILING_DIRECTORIES'] = str(scratch.parent)
    commands = []
    for check_only in (True, False):
        # A global core.autocrlf=true also affects git apply outside repositories.
        # This candidate is defined by exact LF Git blobs, not host checkout policy.
        command = ['git', '-c', 'core.autocrlf=false', '-c', 'core.eol=lf',
                   '-C', str(scratch), 'apply']
        if check_only:
            command.append('--check')
        command += ['-p1', str(patch)]
        result = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        receipt = dict(command=command, exit_code=result.returncode,
                       stdout=result.stdout.decode(errors='replace'), stderr=result.stderr.decode(errors='replace'))
        commands.append(receipt)
        if result.returncode:
            raise ValueError('git patch check/application failed: ' + json.dumps(receipt))
    actual = {p.relative_to(scratch).as_posix(): stable_read(p)
              for p in scratch.rglob('*') if p.is_file() or p.is_symlink()}
    if set(actual) != expected_files:
        raise ValueError('unexpected source paths after patch: ' +
                         json.dumps({'extra': sorted(set(actual) - expected_files),
                                     'missing': sorted(expected_files - set(actual))}))
    mismatches, stage_files = [], {}
    for name, data in actual.items():
        stage_files[name] = stable_read(stage / safe_source_name(name))
        if stage_files[name] != data:
            mismatches.append(name)
    if mismatches:
        raise ValueError('stage source mismatch: ' + ', '.join(sorted(mismatches)))
    return stage_files, dict(commands=commands, stage=str(stage), scratch=str(scratch),
                        stage_match_files=len(actual), source_manifest=source_manifest(actual),
                        ignored_stage_extras=True)


def validate_declarations(declared, identity):
    if not isinstance(declared, dict) or not isinstance(declared.get('checks', []), list):
        raise ValueError('declaration must be an object with a checks list')
    if 'candidate_id' in declared and declared['candidate_id'] != identity['candidate_id']:
        raise ValueError('declaration candidate_id does not match sealed source')
    checks, names = [], set()
    for check in declared.get('checks', []):
        name, status = check.get('name'), check.get('status')
        if not isinstance(name, str) or not name.strip() or name in names or name in SOURCE_CHECKS:
            raise ValueError('invalid, duplicate or reserved check name')
        if status not in ('PASS', 'FAIL', 'UNVERIFIED'):
            raise ValueError('invalid check status: ' + name)
        if status != 'UNVERIFIED' and name not in TRAINING_CHECKS:
            if declared.get('candidate_id') != identity['candidate_id']:
                raise ValueError('native check needs this exact candidate_id: ' + name)
        if status != 'UNVERIFIED' and 'evidence' not in check:
            raise ValueError('PASS/FAIL needs producer-hashed evidence: ' + name)
        names.add(name)
        checks.append(dict(check))
    checks.extend(dict(name=name, status='UNVERIFIED') for name in REQUIRED if name not in names)
    return checks


def file_ref(path, output):
    return dict(path=path.relative_to(output).as_posix(), sha256=sha(stable_read(path)))


def copy_evidence(reference, input_parent, output, index):
    name, expected = reference.get('path'), reference.get('sha256')
    if (not isinstance(name, str) or not name or '\\' in name or ':' in name or '\x00' in name
            or PurePosixPath(name).is_absolute() or PureWindowsPath(name).anchor
            or not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected)):
        raise ValueError('evidence requires relative forward-slash path and producer SHA256')
    source = input_parent / name
    data = stable_read(source)
    if sha(data) != expected:
        raise ValueError('producer SHA256 mismatch: ' + name)
    target = output / 'artifacts' / f'{index:03d}_{source.name}'
    write_new(target, data)
    return file_ref(target, output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--patch', type=Path, required=True, help='exact supplied CR patch')
    parser.add_argument('--stage', type=Path, required=True, help='frozen CR-applied source witness')
    parser.add_argument('--scratch', type=Path, required=True, help='new owned application directory')
    parser.add_argument('--output', type=Path, required=True, help='new immutable evidence directory')
    parser.add_argument('--input', type=Path, help='producer-hashed declarations; omitted means UNVERIFIED draft')
    parser.add_argument('--checker', type=Path, default=DEFAULT_CHECKER)
    args = parser.parse_args(argv)
    for name in ('repo', 'patch', 'stage', 'scratch', 'output', 'checker'):
        setattr(args, name, getattr(args, name).resolve())
    if args.output.exists() or args.scratch.exists():
        raise FileExistsError('output and scratch must both be new; prior evidence is immutable')
    for first, second in ((args.output, args.scratch), (args.output, args.stage), (args.scratch, args.stage)):
        if first == second or first in second.parents or second in first.parents:
            raise ValueError('output, scratch and stage directories must be separate')
    if not args.checker.is_file():
        raise ValueError('installed evidence checker not found; supply --checker')
    patch_bytes = stable_read(args.patch)
    if sha(patch_bytes) != CR_PATCH_SHA256:
        raise ValueError('CR patch SHA256 mismatch; exact supplied artifact required')
    blobs = git_source(args.repo, BASE)
    if len(blobs) != 75 or any(b'\r\n' in data for data in blobs.values()):
        raise ValueError('unexpected actual-lock baseline; require all75 exact LF Git blobs')
    # Apply the sealed patch bytes, not a source that could change between check
    # and use. The output is new and is retained even if subsequent checks fail.
    args.output.mkdir(parents=True, exist_ok=False)
    sealed_patch = args.output / 'tmfit-lock.patch'
    write_new(sealed_patch, patch_bytes)
    candidate, patch_check = apply_verify(blobs, sealed_patch, args.scratch, args.stage, set(blobs) | NEW_FILES)
    identity = candidate_identity(BASE, CR_PATCH_SHA256, candidate)
    declared, input_bytes = {}, None
    if args.input:
        args.input = args.input.resolve()
        input_bytes = stable_read(args.input)
        declared = json.loads(input_bytes.decode('utf-8-sig'))
    checks = validate_declarations(declared, identity)
    if input_bytes is not None:
        # Retain precisely the bytes parsed above, including BOM/line endings.
        # Later mutation of the input path cannot change this package's receipt.
        write_new(args.output / 'declarations.json', input_bytes)
    for label, files in (('baseline', blobs), ('candidate', candidate)):
        write_new(args.output / (label + '-source.tar'), source_tar(files))
        write_new(args.output / (label + '-source.json'), json_bytes(source_manifest(files)))
    write_new(args.output / 'candidate-identity.json', json_bytes(dict(identity,
        identity_kind='base_commit_plus_exact_patch_plus_source_manifest',
        candidate_git_commit=None, source_files=len(candidate), strength='UNPROVEN')))
    write_new(args.output / 'patch-check.json', json_bytes(patch_check))
    source_receipt = dict(base_commit=BASE, base_files=len(blobs), candidate_files=len(candidate),
                          patch_sha256=CR_PATCH_SHA256, candidate_identity=identity,
                          baseline_source_manifest_sha256=sha(canonical(source_manifest(blobs))),
                          stage_match=True, source_only=True, strength='UNPROVEN')
    write_new(args.output / 'source-receipt.json', json_bytes(source_receipt))
    record = dict(schema=1, kind='correctness', baseline=dict(commit=BASE, artifacts=[]),
                  candidate=dict(commit=BASE, artifacts=[], identity=identity,
                    commit_semantics='Base anchor only; candidate is this exact patch plus source manifest, not a Git HEAD tree.'),
                  producer_identity_audit=PRODUCER_IDENTITY_AUDIT, checks=[])
    for label in ('baseline', 'candidate'):
        for suffix in ('source.tar', 'source.json'):
            record[label]['artifacts'].append(file_ref(args.output / (label + '-' + suffix), args.output))
    record['candidate']['artifacts'].extend(file_ref(args.output / name, args.output)
        for name in ('tmfit-lock.patch', 'candidate-identity.json'))
    if input_bytes is not None:
        record['candidate']['artifacts'].append(
            dict(path='declarations.json', sha256=sha(input_bytes)))
    artifact_index = 0
    input_parent = args.input.parent if args.input else args.repo
    for label in ('baseline', 'candidate'):
        for reference in declared.get(label + '_artifacts', []):
            record[label]['artifacts'].append(copy_evidence(reference, input_parent, args.output, artifact_index))
            artifact_index += 1
    for check in checks:
        item = dict(name=check['name'], status=check['status'])
        if 'evidence' in check:
            item['evidence'] = copy_evidence(check['evidence'], input_parent, args.output, artifact_index)
            artifact_index += 1
        if 'scope' in check:
            item['scope'] = check['scope']
        record['checks'].append(item)
    record['checks'].extend([
        dict(name='exact_base_and_cr_patch', status='PASS', evidence=file_ref(args.output / 'source-receipt.json', args.output)),
        dict(name='patch_applies_and_matches_stage', status='PASS', evidence=file_ref(args.output / 'patch-check.json', args.output)),
    ])
    write_new(args.output / 'record.json', json_bytes(record))
    command = [sys.executable, str(args.checker), str(args.output / 'record.json')]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    write_new(args.output / 'checker.stdout.json', result.stdout)
    write_new(args.output / 'checker.stderr.txt', result.stderr)
    states = {c['status'] for c in checks}
    qualification = 'FAIL' if 'FAIL' in states else 'UNVERIFIED' if 'UNVERIFIED' in states else 'DECLARED_PASS'
    write_new(args.output / 'execution.json', json_bytes(dict(command=command, exit_code=result.returncode,
        checker_sha256=sha(stable_read(args.checker)), helper_sha256=sha(stable_read(Path(__file__))),
        input_sha256=sha(input_bytes) if input_bytes is not None else None,
        qualification_status=qualification, candidate_identity=identity,
        producer_identity_audit=PRODUCER_IDENTITY_AUDIT,
        scope='Source/evidence consistency only; no qualification tests or engine builds executed.', strength='UNPROVEN')))
    print(result.stdout.decode(errors='replace'))
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())

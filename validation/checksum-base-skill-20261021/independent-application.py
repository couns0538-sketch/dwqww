#!/usr/bin/env python3
"""Apply the local checksum-base guidance to two frozen data manifests only."""
from pathlib import Path, PurePosixPath
import datetime
import hashlib
import json
import os
import re
import stat

REPO = Path('/workspace/dwqww')
HERE = REPO / 'validation/checksum-base-skill-20261021'
SKILL = REPO / '.agents/skills/validating-chess-strength/SKILL.md'
NATIVE = REPO / 'validation/tt-refresh-native-20261021'
SUPPORT = REPO / 'validation/hosted-tt-refresh-strength-20261021/capture-preparation'
OUTPUT = HERE / 'independent-application.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_components(path, regular=True):
    current = Path(path.anchor)
    for index, part in enumerate(path.parts[1:]):
        current /= part
        mode = current.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise ValueError('Symlink component: ' + str(current))
        final = index == len(path.parts) - 2
        if not final and not stat.S_ISDIR(mode):
            raise ValueError('Non-directory component: ' + str(current))
        if final and not (stat.S_ISREG(mode) if regular else stat.S_ISDIR(mode)):
            raise ValueError('Wrong final file type: ' + str(current))


def entries(data):
    rows = []
    seen = set()
    for index, line in enumerate(data.decode('utf-8').splitlines(), 1):
        match = re.fullmatch(r'([0-9a-f]{64})  (.+)', line)
        if match is None:
            raise ValueError('Ambiguous checksum row ' + str(index))
        expected, name = match.groups()
        if (PurePosixPath(name).is_absolute() or '\\' in name
                or any(part in ('', '.', '..') for part in name.split('/'))
                or any(ord(char) < 32 or ord(char) == 127 for char in name)):
            raise ValueError('Unsafe or ambiguous literal entry: ' + repr(name))
        if name in seen:
            raise ValueError('Duplicate literal entry: ' + name)
        seen.add(name)
        rows.append((expected, name))
    return rows


def plan(rows, base, allowed_scope):
    # The base and scope are explicit inputs, never inferred from the filename.
    safe_components(base, regular=False)
    safe_components(allowed_scope, regular=False)
    selected = []
    seen = set()
    for expected, literal in rows:
        path = base / literal
        if not path.is_relative_to(allowed_scope):
            raise ValueError('Entry outside declared proof scope: ' + str(path))
        if path in seen:
            raise ValueError('Duplicate resolved entry: ' + str(path))
        seen.add(path)
        safe_components(path)
        selected.append((expected, literal, path))
    return selected


def identity(value):
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns,
            value.st_ctime_ns, stat.S_IMODE(value.st_mode))


def hash_file(path):
    safe_components(path)
    before = path.lstat()
    digest = hashlib.sha256()
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
        opened = os.fstat(stream.fileno())
        if identity(opened) != identity(before):
            raise ValueError('File changed before hashing: ' + str(path))
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
        if identity(os.fstat(stream.fileno())) != identity(opened):
            raise ValueError('Open file changed during hashing: ' + str(path))
    safe_components(path)
    if identity(path.lstat()) != identity(before):
        raise ValueError('File changed after hashing: ' + str(path))
    return {'sha256': digest.hexdigest(), 'bytes': before.st_size,
            'mode': stat.S_IMODE(before.st_mode)}


def manifest(path, schema, base, scope, count, wrong_base):
    safe_components(path)
    raw = path.read_bytes()
    rows = entries(raw)
    if len(rows) != count:
        raise ValueError('Wrong manifest row count: ' + str(path))
    selected = plan(rows, base, scope)  # Validate every path before hashing any.
    verified = []
    failures = []
    for expected, literal, target in selected:
        observed = hash_file(target)
        row = {'literal_entry': literal, 'resolved_path': str(target),
               'expected_sha256': expected, **observed}
        row['passed'] = observed['sha256'] == expected
        verified.append(row)
        if not row['passed']:
            failures.append(row)
    control = {'supplied_base': str(wrong_base), 'allowed_scope': str(scope),
               'hashes_attempted': 0}
    try:
        plan(rows, wrong_base, scope)
    except (ValueError, OSError) as error:
        control.update(rejected=True, error_type=type(error).__name__, reason=str(error))
    else:
        control.update(rejected=False)
        failures.append({'wrong_base_control': 'Unexpectedly accepted'})
    if path.read_bytes() != raw:
        failures.append({'manifest_changed_during_application': str(path)})
    return {'manifest_path': str(path), 'manifest_sha256': sha(raw),
            'producer_path_schema': schema, 'explicit_resolution_base': str(base),
            'allowed_proof_scope': str(scope), 'row_count': len(rows),
            'first_genuine_literal_entry': rows[0][1],
            'first_exact_resolution': str(selected[0][2]),
            'verified_hash_count': len(verified), 'all_hashes_match': not any(not r['passed'] for r in verified),
            'wrong_base_control': control, 'files': verified, 'failures': failures}


def main():
    if OUTPUT.exists() or OUTPUT.is_symlink():
        raise SystemExit('Refusing to overwrite a previous independent application')
    skill_before = SKILL.read_bytes()
    paragraph = next(line for line in skill_before.decode().splitlines()
                     if line.startswith('Before consuming a checksum manifest,'))
    guidance_checks = {
        'explicit_base_and_scope': 'explicit resolution base and allowed proof scope' in paragraph,
        'genuine_first_entries': 'inspect genuine first entries' in paragraph,
        'literal_resolution_and_scope': 'Resolve exact entries against that recorded base and enforce scope containment' in paragraph,
        'no_symlink_or_duplicate_entries': 'no symlink components and no duplicate entries' in paragraph,
        'reject_unsafe_paths': 'reject absolute, traversal or ambiguous paths before hashing' in paragraph,
        'no_prefix_normalization_or_alternative_base_rescue': 'never rewrite or normalize entries, strip/add prefixes or try alternative bases to force a pass' in paragraph,
        'preserve_original_failure': 'Preserve the original failed checker and observations' in paragraph,
        'no_engine_retry_on_manifest_error': 'Manifest errors block launch and do not authorize engine execution or retries' in paragraph,
    }
    reports = [
        manifest(NATIVE / 'EVIDENCE-SHA256SUMS', 'namespace-relative literal paths', NATIVE, NATIVE, 138, REPO),
        manifest(SUPPORT / 'SUPPORT-SHA256SUMS', 'repository-relative literal paths', REPO, SUPPORT, 19, SUPPORT),
    ]
    baseline_raw = (HERE / 'BASELINE-EVIDENCE.json').read_bytes()
    baseline = json.loads(baseline_raw)
    original = REPO / baseline['original_note']
    copied = HERE / 'ROOT-PREAUTH-CHECK-NOTE.original.json'
    failure_preserved = (original.read_bytes() == copied.read_bytes()
                         and sha(original.read_bytes()) == baseline['original_note_sha256'])
    failures = [row for report in reports for row in report['failures']]
    passed = (all(guidance_checks.values()) and failure_preserved and not failures
              and SKILL.read_bytes() == skill_before)
    report = {'status': 'PASS_INDEPENDENT_LOCAL_CHECKSUM_BASE_APPLICATION' if passed else 'FAILED_INDEPENDENT_LOCAL_CHECKSUM_BASE_APPLICATION',
              'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'validator_source_path': str(Path(__file__)),
              'validator_source_sha256': sha(Path(__file__).read_bytes()),
              'skill_local_path': str(SKILL), 'skill_sha256': sha(skill_before),
              'guidance_paragraph': paragraph, 'guidance_checks': guidance_checks,
              'manifests': reports, 'actual_hashes_verified': sum(r['verified_hash_count'] for r in reports),
              'preserved_root_failure': {'baseline_receipt_path': str(HERE / 'BASELINE-EVIDENCE.json'),
                                         'baseline_receipt_sha256': sha(baseline_raw),
                                         'original_note_path': str(original), 'copy_path': str(copied),
                                         'expected_sha256': baseline['original_note_sha256'],
                                         'unchanged_byte_identical': failure_preserved},
              'path_handling': 'Literal entries joined once to explicit bases. No prefix or entry rewriting, alternative-base rescue, recursive proof discovery, or referenced JSON input traversal.',
              'scope_qualification': 'Verified the local skill file and exactly 157 listed local data files. No global/cloud installation, engine correctness, capture acceptance, playing-strength or match result claim.',
              'producer_or_auditor_imported': False, 'engines_builds_tests_git_install_or_retry': False,
              'original_files_modified': False, 'failures': failures}
    with OUTPUT.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'status': report['status'], 'actual_hashes_verified': report['actual_hashes_verified'],
                      'row_counts': [r['row_count'] for r in reports],
                      'wrong_base_controls_rejected': [r['wrong_base_control']['rejected'] for r in reports],
                      'failure_note_preserved': failure_preserved, 'output_sha256': sha(OUTPUT.read_bytes())}, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())

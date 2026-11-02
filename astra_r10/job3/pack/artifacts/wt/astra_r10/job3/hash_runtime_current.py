"""Capture current D-only runtime identities; never reconstruct lost history."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path('D:/a10')
JOB = ROOT / 'wt/astra_r10/job3'
RUNTIME = ROOT / 'job3/runtime'
sys.path.insert(0, str(ROOT / 'pydeps'))
import psutil
sys.path.insert(0, str(ROOT / 'wt/skills/gate-handover-pack/scripts'))
import seal_evidence as safety
sys.path.insert(0, str(ROOT / 'wt/skills/npt-data-holdout-check/scripts'))
from audit_exports import fingerprint, identity


def inventory():
    result = {}
    pending = [safety.checked_path(RUNTIME)]
    while pending:
        parent = pending.pop()
        with os.scandir(parent) as entries:
            for entry in entries:
                path = Path(entry.path)
                if safety.reparse(path):
                    raise ValueError('runtime reparse refused')
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                else:
                    result[path] = identity(path.stat())
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--threads', type=int, choices=[1], required=True)
    parser.parse_args()
    proc = psutil.Process()
    if proc.nice() != psutil.IDLE_PRIORITY_CLASS or proc.cpu_affinity() != [3]:
        raise RuntimeError('Idle CPU3-only hash job required')
    target = JOB / 'RUNTIME_CURRENT_HASHES.json'
    if target.exists():
        raise ValueError('preserve existing current-runtime receipt')
    safety.disk_budget(20_000_000)
    if safety.workspace_bytes() + 20_000_000 > safety.CAP:
        raise ValueError('workspace cap')
    old = JOB / 'RUNTIME_INPUTS.json'
    old_raw = old.read_bytes()
    old_sha = hashlib.sha256(old_raw).hexdigest()
    original = json.loads(old_raw.decode('utf-8-sig'))
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    before = inventory()
    records = []
    for index, path in enumerate(sorted(before)):
        if index % 128 == 0:
            safety.disk_budget(20_000_000)
        found = fingerprint(path)
        if found['identity'] != before[path]:
            raise ValueError('runtime file changed since inventory: ' + str(path))
        records.append({'path': str(path), 'relative': path.relative_to(RUNTIME).as_posix(),
                        'bytes': path.stat().st_size, 'sha256': found['sha256'],
                        'identity': found['identity'], 'link_identity': found['link_identity']})
    if inventory() != before:
        raise ValueError('runtime names/identities changed during hashing')
    if hashlib.sha256(old.read_bytes()).hexdigest() != old_sha:
        raise ValueError('original malformed receipt changed')
    report = {'schema': 1, 'status': 'CURRENT_D_IDENTITIES_CAPTURED', 'classification': 'UNPROVEN',
              'runtime_root': str(RUNTIME), 'started_utc': started,
              'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'scope': 'Current D:/a10 copied runtime files only; no original/protected runtime source was read.',
              'files': records, 'file_count': len(records), 'bytes': sum(row['bytes'] for row in records),
              'original_copy_receipt': {'path': str(old), 'sha256': old_sha, 'bytes': len(old_raw),
                                        'files_type': type(original.get('files')).__name__,
                                        'usable_per_file_array': isinstance(original.get('files'), list)},
              'historical_limitation': 'The original copy script checked source/copy hashes and exited0, but a typed $Manifest collision in the dot-sourced launcher serialized files as a string. The historical per-file list was lost. This new current-D manifest does not reconstruct or assert that historical list or fresh source/copy equality.',
              'consistency': 'Every file SHA256 was read through descriptor/path identity checks; complete file-name/identity inventory rechecked after hashing. No runtime files were edited.',
              'implementation_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    safety.write_new(target, (json.dumps(report, indent=2) + '\n').encode())
    print(json.dumps({'status': report['status'], 'files': len(records), 'bytes': report['bytes'],
                      'output': str(target), 'original_receipt_sha256': old_sha,
                      'original_files_type': report['original_copy_receipt']['files_type']}, indent=2))


if __name__ == '__main__':
    main()

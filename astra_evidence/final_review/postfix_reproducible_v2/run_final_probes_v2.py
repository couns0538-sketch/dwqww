#!/usr/bin/env python3
"""New independent fake-engine probe run; does not reconstruct earlier evidence.

Run once in a fresh directory containing this harness:
  python3 -B run_final_probes_v2.py --repo /tmp/forge-astra-20261029
IDEA_SOURCE: Owner A3 and the reviewed validation-script contracts.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    output = root / 'new_run'
    output.mkdir(exist_ok=False)
    bundle = output / 'bundle with spaces'
    (bundle / 'tests').mkdir(parents=True)
    (bundle / 'tools').mkdir()
    source_paths = ['tests/bundle_off_identity.sh', 'tools/check_bundle_opts.py']
    source_hashes = {}
    for relative in source_paths:
        source = args.repo.resolve() / relative
        source_hashes[relative] = digest(source)
        shutil.copy2(source, bundle / relative)
    script = bundle / 'tests/bundle_off_identity.sh'
    base_ads = [
        'option name Hash type spin default 16 min 1 max 2048',
        'option name Threads type spin default 1 min 1 max 256',
        'option name OwnBook type check default true',
        'option name Feature type check default false',
    ]
    rows = []

    def probe(label, expected_exit=0, extra=(), advertisements=None, help_only=False):
        case = output / label
        case.mkdir()
        if help_only:
            command = ['bash', str(script), '--help']
            fake_hash = None
        else:
            fake = case / 'fake engine'
            ads = base_ads if advertisements is None else advertisements
            fake.write_text(
                '#!' + sys.executable + '\n'
                'import re, sys\n'
                'commands = sys.stdin.read()\n'
                f'for line in {ads!r}: print(line)\n'
                'print("uciok\\nreadyok")\n'
                'depth = int(re.search(r"bench (\\d+)", commands)[1])\n'
                'print(f"info string bench depth {depth} nodes 123 time 1 nps 123000")\n',
                encoding='utf-8',
            )
            fake.chmod(0o755)
            fake_hash = digest(fake)
            command = [
                'bash', str(script), str(fake), str(fake), '--depths', '1',
                '--off', 'Feature=false', '--output', str(case / 'engine_evidence'), *extra,
            ]
        start = datetime.now(timezone.utc).isoformat()
        result = subprocess.run(command, cwd='/', capture_output=True, timeout=5)
        (case / 'stdout.bin').write_bytes(result.stdout)
        (case / 'stderr.bin').write_bytes(result.stderr)
        record = {
            'label': label, 'command_argv': command, 'cwd': '/',
            'start_utc': start, 'end_utc': datetime.now(timezone.utc).isoformat(),
            'expected_exit': expected_exit, 'actual_exit': result.returncode,
            'passed': result.returncode == expected_exit,
            'fake_engine_sha256': fake_hash,
            'stdout_sha256': digest(case / 'stdout.bin'),
            'stderr_sha256': digest(case / 'stderr.bin'),
        }
        (case / 'command_and_result.json').write_text(json.dumps(record, indent=2) + '\n')
        rows.append(record)

    probe('cross-cwd-spaces')
    probe('help-cross-cwd-spaces', help_only=True)
    probe('duplicate-off', 1, ['--off', 'Feature=false'])
    probe('duplicate-case-off', 1, ['--off', 'feature=false'])
    probe('ownbook-override', 1, ['--off', 'OwnBook=false'])
    for name in ['Hash', 'Threads', 'OwnBook']:
        probe('missing-control-' + name, 1, advertisements=[
            ad for ad in base_ads if not ad.startswith('option name ' + name + ' ')
        ])
    probe('hash-range-too-small', 1, advertisements=[
        ad.replace('default 16 min 1 max 2048', 'default 1 min 1 max 8') for ad in base_ads
    ])
    probe('threads-wrong-type', 1, advertisements=[
        ad.replace('Threads type spin default 1 min 1 max 256', 'Threads type check default true')
        for ad in base_ads
    ])
    probe('ownbook-wrong-type', 1, advertisements=[
        ad.replace('OwnBook type check default true', 'OwnBook type spin default 1 min 0 max 1')
        for ad in base_ads
    ])
    after = {relative: digest(args.repo.resolve() / relative) for relative in source_paths}
    summary = {
        'provenance': 'NEW RUN against current sources; no earlier logs reconstructed',
        'claim': 'Synthetic UCI validation probes only; these are not native Forge benches',
        'harness_argv': [sys.executable, '-B', str(Path(__file__).resolve()), *sys.argv[1:]],
        'harness_sha256': digest(Path(__file__)),
        'python': sys.version, 'platform': platform.platform(),
        'source_sha256_before': source_hashes, 'source_sha256_after': after,
        'source_unchanged_during_probes': after == source_hashes,
        'passed': sum(row['passed'] for row in rows), 'total': len(rows), 'runs': rows,
    }
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    with (output / 'SHA256SUMS').open('w') as out:
        for path in sorted(output.rglob('*')):
            if path.is_file() and path.name != 'SHA256SUMS':
                out.write(digest(path) + '  ' + str(path.relative_to(output)) + '\n')
    print(f"NEW RUN: {summary['passed']}/{summary['total']} synthetic probes passed")
    print(json.dumps(source_hashes, sort_keys=True))
    return 0 if summary['passed'] == summary['total'] and after == source_hashes else 1


if __name__ == '__main__':
    raise SystemExit(main())

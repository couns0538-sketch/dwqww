#!/usr/bin/env python3
"""Compile-only option-layout experiment in copied headers; never edits the supplied header.

Before F1: --expect-permuted fail. After named construction: --expect-permuted pass.
Only smp_v2 and singular_v2 declarations are exchanged. The first three members stay in order
because C++20 designated initializers must follow declaration order.
IDEA_SOURCE: source-grounded preset ownership and explicit field assignment, original probe.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--header', type=Path, required=True)
    parser.add_argument('--out-dir', type=Path, required=True, help='new directory, never overwritten')
    parser.add_argument('--expect-permuted', choices=['fail', 'pass'], required=True)
    parser.add_argument('--source-ref', required=True, help='caller-supplied revision label; source bytes are hashed')
    parser.add_argument('--compiler', default='/usr/bin/g++-14')
    args = parser.parse_args()
    source = args.header.resolve(strict=True)
    original = source.read_bytes()
    text = original.decode('utf-8')
    start = text.index('struct Options {')
    end = text.index('\n};', start)
    body = text[start:end]
    members = re.findall(r'^\s*bool\s+(\w+)\s*=', body, re.M)
    if members[:3] != ['corr_hist_v2', 'lmr_table_v2', 'tt_prune_v2']:
        raise ValueError('unexpected first-three Options members; stop rather than widen the permutation')
    declarations = {}
    for name in ['singular_v2', 'smp_v2']:
        matches = re.findall(r'^.*\bbool\s+' + name + r'\s*=.*$', body, re.M)
        if len(matches) != 1:
            raise ValueError(f'expected one declaration of {name}')
        declarations[name] = matches[0]
    if body.index(declarations['singular_v2']) >= body.index(declarations['smp_v2']):
        raise ValueError('source does not have the expected pre-permutation singular-before-smp layout')
    marker = '/* ASTRA_F1_TEMPORARY_DECLARATION_MARKER */'
    if marker in text:
        raise ValueError('reserved permutation marker already present')
    permuted_body = body.replace(declarations['singular_v2'], marker, 1).replace(
        declarations['smp_v2'], declarations['singular_v2'], 1).replace(marker, declarations['smp_v2'], 1)
    permuted = (text[:start] + permuted_body + text[end:]).encode('utf-8')
    output = args.out_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    probe = Path(__file__).with_name('preset_layout_probe.cpp').read_bytes()
    version_command = [args.compiler, '--version']
    version = subprocess.run(version_command, capture_output=True, timeout=30)
    (output/'compiler_version.stdout').write_bytes(version.stdout)
    (output/'compiler_version.stderr').write_bytes(version.stderr)
    record = {'kind': 'Synthetic compile-only copied-header probe; not engine/bench/Elo evidence',
              'source_ref_caller_supplied': args.source_ref, 'source_path': str(source),
              'source_sha256': digest(original), 'probe_sha256': digest(probe),
              'driver_sha256': digest(Path(__file__).read_bytes()),
              'compiler_version_command': version_command, 'compiler_version_returncode': version.returncode,
              'expected_permuted': args.expect_permuted, 'cases': []}
    for label, header in [('original', original), ('permuted_NEGATIVE_FIXTURE', permuted)]:
        folder = output/label
        include = folder/'include'/'forge'
        include.mkdir(parents=True)
        (include/'fb2.hpp').write_bytes(header)
        (folder/'preset_layout_probe.cpp').write_bytes(probe)
        command = ['nice', '-n', '19', args.compiler, '-std=c++20', '-pedantic-errors',
                   '-Wall', '-Wextra', '-Werror', '-fsyntax-only', '-I'+str(folder/'include'),
                   str(folder/'preset_layout_probe.cpp')]
        run = subprocess.run(command, capture_output=True, timeout=30)
        (folder/'compile.stdout').write_bytes(run.stdout)
        (folder/'compile.stderr').write_bytes(run.stderr)
        (folder/'command.json').write_text(json.dumps(command, indent=2)+'\n')
        positive = label == 'original' or args.expect_permuted == 'pass'
        intended_assertion_failure = (b'static assertion failed' in run.stderr and
                                      b'N1 must enable SingularV2' in run.stderr and
                                      b'N1 must not enable SmpV2' in run.stderr)
        passed = run.returncode == 0 if positive else run.returncode != 0 and intended_assertion_failure
        record['cases'].append({'case': label, 'header_sha256': digest(header), 'returncode': run.returncode,
                                'expected_compile_success': positive,
                                'intended_assertion_failure': intended_assertion_failure, 'pass': passed})
    record['live_source_unchanged'] = source.read_bytes() == original
    record['pass'] = version.returncode == 0 and record['live_source_unchanged'] and all(c['pass'] for c in record['cases'])
    (output/'results.json').write_text(json.dumps(record, indent=2)+'\n')
    files = sorted(p for p in output.rglob('*') if p.is_file())
    (output/'MANIFEST.sha256').write_text(''.join(digest(p.read_bytes())+'  '+str(p.relative_to(output))+'\n' for p in files))
    print(json.dumps(record, indent=2))
    return 0 if record['pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

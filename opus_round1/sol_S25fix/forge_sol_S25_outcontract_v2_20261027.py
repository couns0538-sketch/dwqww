#!/usr/bin/env python3
"""S25 v2 — strict bench-EOF and typed UCI option contract (Opus fix-up of Sol's forge_sol_S25_outcontract_20261025.py).

S25-1  Node pins per tree come from --ref: a named set (AL1 default = 312866/862329/3024920/12389307/34048354,
       Lprime and B = Sol's dev base 308972/745494/2460422/11901452/31111774) or a JSON file {"11": nodes, ...}.
       The first engine process is still the bare `bench 11`; --depths adds more depths (one process each).
       A node mismatch makes bench=PIN_MISMATCH (format errors stay FAIL) and the UCI check ALWAYS runs.
S25-2  L4 every engine process has a timeout (--timeout, default 300 s); on expiry this tool kills its own child
          (nothing else) and records *_timeout.
       L5 without --out the raw captures go to a NEW mkdtemp directory under the system temp dir (or --work-root),
          never the build tree; that directory (and only it, identified by its marker file) is removed after the
          run unless --keep. --out NEW keeps everything and is never removed.
       L6 --allow-expose accepts the extra spin options that a FORGE_EXPOSE_TUNABLES build advertises; the approved
          options must still match exactly and the extra names are listed in the result.
       L7 Windows: CRLF output is accepted, `forge.exe` works, see README.
Exit 0 = contract PASS, 1 = contract FAIL / PIN_MISMATCH, 2 = invocation error. Standard library only.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REFSETS = {
    'AL1': {11: 312866, 13: 862329, 16: 3024920, 20: 12389307, 22: 34048354},
    'Lprime': {11: 308972, 13: 745494, 16: 2460422, 20: 11901452, 22: 31111774},
    'B': {11: 308972, 13: 745494, 16: 2460422, 20: 11901452, 22: 31111774},
}
SUMMARY = re.compile(rb'(?m)^info string bench depth ([0-9]+) nodes ([0-9]+) time ([0-9]+) nps ([0-9]+)(\r\n|\n|\Z)')
MARKER = '.forge_s25_owned_tmp'
ALLOWLIST = 'forge_sol_S25_options_v2_20261027.json'


def resolve_ref(ref):
    """{depth: nodes} from a named set or a JSON file; d11 is required (it gates nothing, but is always run)."""
    if ref in REFSETS:
        pins = dict(REFSETS[ref])
    elif ref and Path(ref).is_file():
        pins = {int(k): int(v) for k, v in json.loads(Path(ref).read_text(encoding='utf-8')).items()}
    else:
        raise ValueError('unknown --ref (use AL1, Lprime, B or a JSON file): %r' % (ref,))
    if 11 not in pins or any(v <= 0 for v in pins.values()):
        raise ValueError('a pin set needs a positive depth-11 entry')
    return pins


def inspect_bench(stdout, stderr, exitcode, depth, nodes, timed_out=False):
    """PASS, PIN_MISMATCH (only the node count differs) or FAIL (any exit/stream/format error)."""
    errors = []
    matches = list(SUMMARY.finditer(stdout))
    if timed_out:
        errors.append({'code': 'bench_timeout'})
    elif exitcode != 0:
        errors.append({'code': 'bench_exit', 'actual': exitcode})
    if stderr:
        errors.append({'code': 'bench_stderr', 'bytes': len(stderr), 'sha256': hashlib.sha256(stderr).hexdigest()})
    if len(matches) != 1:
        errors.append({'code': 'bench_summary_count', 'expected': 1, 'actual': len(matches)})
    pin = None
    if len(matches) == 1:
        m = matches[0]
        actual_depth, actual_nodes = int(m[1]), int(m[2])
        if actual_depth != depth:
            errors.append({'code': 'bench_depth', 'expected': depth, 'actual': actual_depth})
        if actual_nodes != nodes:
            pin = {'code': 'bench_pin_mismatch', 'depth': depth, 'expected_nodes': nodes, 'actual_nodes': actual_nodes}
        if not m[5]:
            errors.append({'code': 'bench_missing_line_ending'})
        if m.start() != 0:
            errors.append({'code': 'bench_prefix_bytes', 'bytes': m.start()})
        tail = stdout[m.end():]
        if tail:
            errors.append({'code': 'bench_post_summary_bytes', 'bytes': len(tail), 'sha256': hashlib.sha256(tail).hexdigest(),
                           'base64': base64.b64encode(tail).decode()})
    status = 'FAIL' if errors else ('PIN_MISMATCH' if pin else 'PASS')
    return {'status': status, 'depth': depth, 'expected_nodes': nodes,
            'actual_nodes': int(matches[0][2]) if len(matches) == 1 else None,
            'errors': errors + ([pin] if pin else [])}


def parse_option(line):
    patterns = [('spin', r'option name (.+) type spin default (-?[0-9]+) min (-?[0-9]+) max (-?[0-9]+)'),
                ('check', r'option name (.+) type check default (true|false)'),
                ('string', r'option name (.+) type string default (.*)'),
                ('button', r'option name (.+) type button')]
    for kind, pattern in patterns:
        m = re.fullmatch(pattern, line)
        if not m:
            continue
        result = {'name': m[1], 'type': kind}
        if kind == 'spin':
            result.update(default=int(m[2]), min=int(m[3]), max=int(m[4]))
        elif kind == 'check':
            result['default'] = m[2] == 'true'
        elif kind == 'string':
            result['default'] = m[2]
        return result
    raise ValueError('malformed or unsupported option declaration')


def inspect_uci(stdout, stderr, exitcode, approved, allow_expose=False, timed_out=False):
    errors, actual, duplicate, exposed = [], {}, [], []
    if timed_out:
        errors.append({'code': 'uci_timeout'})
    elif exitcode != 0:
        errors.append({'code': 'uci_exit', 'actual': exitcode})
    if stderr:
        errors.append({'code': 'uci_stderr', 'bytes': len(stderr), 'sha256': hashlib.sha256(stderr).hexdigest()})
    try:
        lines = stdout.decode('utf-8').splitlines()  # accepts LF and CRLF (Windows engines)
    except UnicodeDecodeError:
        return {'status': 'FAIL', 'options': [], 'errors': errors + [{'code': 'uci_non_utf8'}]}
    if lines.count('uciok') != 1:
        errors.append({'code': 'uciok_count', 'expected': 1, 'actual': lines.count('uciok')})
    for line in lines:
        if not line.lstrip().lower().startswith('option'):
            continue
        try:
            item = parse_option(line)
        except ValueError:
            errors.append({'code': 'malformed_option', 'line_base64': base64.b64encode(line.encode()).decode()})
            continue
        if item['name'] in actual:
            duplicate.append(item['name'])
            errors.append({'code': 'duplicate_option', 'name': item['name']})
        else:
            actual[item['name']] = item
    expected = {r['name']: r for r in approved}
    if len(expected) != len(approved):
        raise ValueError('approved option names must be unique')
    for name in sorted(expected):
        if name not in actual:
            errors.append({'code': 'missing_option', 'name': name})
        elif expected[name] != actual[name]:
            errors.append({'code': 'option_metadata_mismatch', 'name': name, 'expected': expected[name], 'actual': actual[name]})
    for name in sorted(actual.keys() - expected.keys()):
        if allow_expose and actual[name]['type'] == 'spin':
            exposed.append(name)  # FORGE_EXPOSE_TUNABLES build: tuning constants advertised as spin options
        else:
            errors.append({'code': 'unexpected_option', 'name': name, 'actual': actual[name]})
    return {'status': 'PASS' if not errors else 'FAIL', 'options': [actual[n] for n in sorted(actual)],
            'duplicate_names': duplicate, 'exposed_tunables_allowed': exposed, 'errors': errors}


def capture(argv, stdin, path, timeout):
    """Run one engine process to EOF; on timeout kill only this child. Raw bytes are written to path."""
    child = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timed_out = False
    try:
        stdout, stderr = child.communicate(stdin, timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        child.kill()  # our own child only
        stdout, stderr = child.communicate()
    record = {'argv': [str(a) for a in argv], 'stdin_base64': base64.b64encode(stdin).decode(),
              'exit': None if timed_out else child.returncode, 'timeout_seconds': timeout, 'timed_out': timed_out,
              'EOF_and_child_exit_observed': True}
    for name, data in (('stdout', stdout), ('stderr', stderr)):
        record[name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'base64': base64.b64encode(data).decode()}
    path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    return stdout, stderr, record['exit'], timed_out


def run_contract(argv, out, approved, pins, depths, timeout, allow_expose=False):
    """The contract on argv (engine command). First process: bare `bench 11`; UCI always checked (S25-1)."""
    out = Path(out)
    benches = []
    for depth in [11] + [d for d in depths if d != 11]:
        stdout, stderr, code, to = capture(argv, ('bench %d\nquit\n' % depth).encode(), out / ('bench_d%d_raw.json' % depth), timeout)
        benches.append(inspect_bench(stdout, stderr, code, depth, pins[depth], to))
    stdout, stderr, code, to = capture(argv, b'uci\nquit\n', out / 'uci_raw.json', timeout)
    uci = inspect_uci(stdout, stderr, code, approved, allow_expose, to)
    states = {b['status'] for b in benches}
    bench_status = 'FAIL' if 'FAIL' in states else ('PIN_MISMATCH' if 'PIN_MISMATCH' in states else 'PASS')
    errors = [e for b in benches for e in b['errors']] + uci['errors']
    result = {'schema': 'forge_sol_S25_contract_v2', 'status': 'PASS' if bench_status == 'PASS' and uci['status'] == 'PASS' else 'FAIL',
              'bench_status': bench_status, 'uci_status': uci['status'], 'bench': benches, 'uci': uci,
              'pins': {str(k): v for k, v in pins.items()}, 'depths_run': [b['depth'] for b in benches],
              'allow_expose': allow_expose, 'timeout_seconds': timeout, 'errors': errors}
    (out / 'contract_result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def owned_tmp(root):
    """NEW mkdtemp outside the build tree with a marker naming it as this tool's own directory."""
    if root:
        Path(root).mkdir(parents=True, exist_ok=True)  # the work root itself is never removed
    path = Path(tempfile.mkdtemp(prefix='forge_s25_contract_', dir=str(root) if root else None))
    token = secrets.token_hex(16)
    (path / MARKER).write_text(token, encoding='utf-8')
    return path, token


def remove_owned(path, token):
    """Remove only a directory this run created (marker + token must match); never anything else."""
    marker = Path(path) / MARKER
    if not marker.is_file() or marker.read_text(encoding='utf-8') != token or Path(path).is_symlink():
        raise RuntimeError('refusing cleanup: %s is not this run\'s temp directory' % path)
    shutil.rmtree(path)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('exe', type=Path)
    g = p.add_mutually_exclusive_group()
    g.add_argument('--out', type=Path, help='NEW directory for raw captures and result (kept)')
    g.add_argument('--work-root', type=Path, help='parent for the temp directory (default: system temp)')
    p.add_argument('--keep', action='store_true', help='keep the temp directory')
    p.add_argument('--ref', default='AL1', help='AL1 (default), Lprime, B or a JSON pin file')
    p.add_argument('--depths', default='11', help="comma list or 'all' (pinned depths); d11 always runs first")
    p.add_argument('--timeout', type=float, default=300.0, help='seconds per engine process')
    p.add_argument('--allow-expose', action='store_true', help='accept extra spin options of a FORGE_EXPOSE_TUNABLES build')
    p.add_argument('--allowlist', type=Path, default=Path(__file__).with_name(ALLOWLIST))
    a = p.parse_args(argv)
    try:
        exe = a.exe.resolve(strict=True)
        if not exe.is_file() or not os.access(exe, os.X_OK):
            raise ValueError('readable executable required')
        pins = resolve_ref(a.ref)
        depths = sorted(pins) if a.depths == 'all' else [int(x) for x in a.depths.split(',')]
        if any(d not in pins for d in depths):
            raise ValueError('every requested depth needs a pin in --ref')
        if not (a.timeout > 0):
            raise ValueError('--timeout must be positive')
        allow = json.loads(a.allowlist.read_text(encoding='utf-8'))
        if a.out:
            a.out.mkdir(parents=False, exist_ok=False)
            out, token = a.out, None
        else:
            out, token = owned_tmp(a.work_root)
    except (OSError, ValueError) as exc:
        print('OUTPUT_CONTRACT_ERROR ' + str(exc), file=sys.stderr)
        return 2
    result = run_contract([str(exe)], out, allow['options'], pins, depths, a.timeout, a.allow_expose)
    result.update(engine_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(), ref=a.ref,
                  allowlist_sha256=hashlib.sha256(a.allowlist.read_bytes()).hexdigest())
    (out / 'contract_result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    kept = token is None or a.keep
    print('OUTPUT_CONTRACT_%s bench=%s uci=%s ref=%s depths=%s errors=%s %s' % (
        result['status'], result['bench_status'], result['uci_status'], a.ref, ','.join(map(str, result['depths_run'])),
        ','.join(e['code'] for e in result['errors']) or '-', ('out=' + str(out)) if kept else 'temp=removed'))
    if not kept:
        remove_owned(out, token)
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())

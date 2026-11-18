#!/usr/bin/env python3
"""Capture Job 19 W1/W3 and compare the raw results for each position."""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

import identity


WORKLOADS = {'W1': (1000, 'go depth 9'), 'W3-depth': (300, 'go depth 9'), 'W3-eval': (1000, 'eval')}
PINS = {
    'r15d': 'bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6',
    'kF': '340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea',
}
HELPER_PIN = '1f7703dae17160651c6a9d163a4af0d14cb34848c7523fa70a50e260c86d93ca'
NET_MARKER = re.compile(rb'\bhidden 768\b.*\bchecksum 30ab43b4ba5db5f3\b')
NODES = re.compile(rb'\bnodes ([0-9]+)\b')
EVAL = re.compile(rb'info string eval hce 0 nnue (-?[0-9]+) total (-?[0-9]+)(?: incheck 1)?')
LABELS = ('row', 'fen', 'stdout_first', 'stdout_last')


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_fixture(path):
    raw = path.read_bytes()
    if not raw.endswith(b'\n') or b'\r' in raw:
        raise ValueError('Expected LF with final LF in positions fixture')
    positions = raw.decode('ascii').splitlines()
    if len(positions) != 1000 or any(len(fen.split()) != 6 for fen in positions):
        raise ValueError('Expected precisely 1,000 six-field FENs')
    return positions


def expected_commands(fens, net, action):
    result = ['uci', *(f'setoption name {key} value {val}' for key, val in identity.PC20.items()),
              f'setoption name NNUEArchFile value {net}', 'setoption name NNUEArch value true', 'isready']
    for fen in fens:
        result.extend(('ucinewgame', 'isready', f'position fen {fen}', action))
        if action == 'eval':
            result.append('isready')
    result.append('quit')
    return result


def wait_bestmove(engine, index):
    return engine.receive(lambda line: line.startswith(b'bestmove '), f'bestmove for row {index}')


def capture(executable, net, fens, output, action, timeout):
    with ((output / 'engine.stdout.txt').open('xb') as stdout,
          (output / 'engine.stderr.txt').open('x+b') as stderr,
          (output / 'engine.commands.txt').open('xb') as stdin):
        with identity.EngineRun(executable, stdout, stderr, stdin, timeout) as engine:
            engine.set_up(net)
            for index, fen in enumerate(fens, 1):
                engine.send('ucinewgame')
                if engine.ready() != [b'readyok']:
                    raise RuntimeError(f'unexpected reset output on row {index}')
                engine.send(f'position fen {fen}')
                engine.send(action)
                if action == 'eval':
                    got = engine.ready()
                    if len(got) != 2 or EVAL.fullmatch(got[0]) is None:
                        raise RuntimeError(f'expected one embedded-zero standalone eval on row {index}: {got!r}')
                else:
                    wait_bestmove(engine, index)


def parse_depth(raw, position, start):
    while position < len(raw) and not raw[position].startswith(b'bestmove '):
        if raw[position] == b'readyok':
            raise ValueError('search ended before bestmove')
        position += 1
    if position == len(raw):
        raise ValueError('missing bestmove before end of stdout')
    best = identity.BESTMOVE.fullmatch(raw[position])
    final = next((line for line in reversed(raw[start:position]) if line.startswith(b'info depth ')), None)
    nodes = NODES.search(final or b'')
    if best is None or nodes is None:
        raise ValueError('missing/malformed last info node count or bestmove')
    return position + 1, {'nodes': nodes[1].decode('ascii'), 'bestmove': best[1].decode('ascii'),
                          'last_info': final.decode('ascii'), 'bestmove_line': raw[position].decode('ascii')}


def read_raw(output, net, fens, action):
    command_path = output / 'engine.commands.txt'
    raw_path = output / 'engine.stdout.txt'
    errors = output / 'engine.stderr.txt'
    expected = expected_commands(fens, net, action)
    if command_path.read_text(encoding='ascii').splitlines() != expected:
        raise ValueError(f'mismatched PC20, net-load or per-position commands in {command_path}')
    identity.check_logs(raw_path, errors)
    raw = raw_path.read_bytes().splitlines()
    active = [line for line in raw if line.startswith(identity.NET_ACTIVE)]
    ids = [line for line in raw if line.startswith(b'id name ')]
    if len(active) != 1 or NET_MARKER.search(active[0]) is None or len(ids) != 1 or raw.count(b'uciok') != 1:
        raise ValueError('unexpected UCI initialization or active standalone net marker')
    if raw.count(b'readyok') != expected.count('isready'):
        raise ValueError('incorrect raw readyok count')
    pos = raw.index(b'readyok') + 1
    if active[0] not in raw[:pos] or raw.index(b'uciok') >= pos:
        raise ValueError('net activation and UCI acknowledgment must precede the setup barrier')
    rows = []
    for index, fen in enumerate(fens, 1):
        if pos >= len(raw) or raw[pos] != b'readyok':
            raise ValueError(f'row {index}: missing reset readyok')
        pos += 1
        first = pos + 1
        if action == 'eval':
            entry = EVAL.fullmatch(raw[pos]) if pos < len(raw) else None
            if entry is None or entry[1] != entry[2] or raw[pos + 1:pos + 2] != [b'readyok']:
                raise ValueError(f'row {index}: eval did not return a single standalone reference line')
            values = {'eval_line': raw[pos].decode('ascii')}
            last = pos + 1
            pos += 2
        else:
            try:
                pos, values = parse_depth(raw, pos, pos)
            except ValueError as exc:
                raise ValueError(f'row {index}: {exc}') from exc
            last = pos
        rows.append({'row': str(index), 'fen': fen, 'stdout_first': str(first), 'stdout_last': str(last), **values})
    if pos != len(raw):
        raise ValueError(f'{raw_path} contains {len(raw) - pos} extra stdout lines')
    return rows, {'stdout_lines': len(raw), 'stdin_lines': len(expected),
                  'id_name': ids[0].decode('ascii'), 'net_active': active[0].decode('ascii')}


def write_rows(output, rows, action):
    fields = (*LABELS, *(['eval_line'] if action == 'eval' else ['nodes', 'bestmove', 'last_info', 'bestmove_line']))
    with (output / 'rows.tsv').open('x', encoding='ascii', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fields, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    if action == 'eval':
        with (output / 'eval.txt').open('x', encoding='ascii') as file:
            file.writelines(row['eval_line'] + '\n' for row in rows)


def compare_runs(left, right, fixture_override=None):
    runs = [left, right]
    reports = [json.loads((path / 'summary.json').read_text()) for path in runs]
    if any(report['error'] is not None for report in reports):
        raise ValueError('cannot compare an incomplete run')
    if reports[0]['workload'] != reports[1]['workload'] or reports[0]['fixture_sha256'] != reports[1]['fixture_sha256']:
        raise ValueError('comparison requires identical workload and fixture hash')
    count, action = WORKLOADS[reports[0]['workload']]
    fixture = fixture_override if fixture_override is not None else Path(reports[0]['fixture'])
    if sha(fixture) != reports[0]['fixture_sha256']:
        raise ValueError('fixture used to verify raw rows has changed')
    fens = read_fixture(fixture)[:count]
    frames = []
    for path, summary in zip(runs, reports, strict=True):
        for name, digest in summary['files_sha256'].items():
            if sha(path / name) != digest:
                raise ValueError(f'artifact changed: {path / name}')
        rows, raw_meta = read_raw(path, summary['net_path'], fens, action)
        if any(summary[key] != value for key, value in raw_meta.items()):
            raise ValueError(f'run metadata differs from raw: {path}')
        with (path / 'rows.tsv').open(encoding='ascii', newline='') as file:
            if rows != list(csv.DictReader(file, delimiter='\t')):
                raise ValueError(f'{path / "rows.tsv"} differs from independent reconstruction')
        if action == 'eval' and (path / 'eval.txt').read_bytes() != ''.join(row['eval_line']+'\n' for row in rows).encode('ascii'):
            raise ValueError(f'{path / "eval.txt"} is not the literal eval response stream')
        frames.append(rows)
    fields = ('eval_line',) if action == 'eval' else ('nodes', 'bestmove')
    differences = [(a, b) for a, b in zip(*frames, strict=True) if any(a[key] != b[key] for key in fields)]
    return {'workload': reports[0]['workload'], 'fields': fields, 'compared': count,
            'equal': count - len(differences), 'differ': len(differences),
            'runs': [{'directory': str(path), 'build': report['build'], 'exe_sha256': report['exe_sha256'],
                      'net_active': report['net_active']} for path, report in zip(runs, reports, strict=True)],
            'first_difference': ({'row': differences[0][0]['row'], 'fen': differences[0][0]['fen'],
                                  'left': differences[0][0], 'right': differences[0][1]} if differences else None)}


def run(args):
    expected = PINS.get(args.build) or args.exe_sha256
    if expected is None or (args.exe_sha256 is not None and expected != args.exe_sha256):
        raise ValueError('the variant needs its build SHA-256; r15d/kF require the existing exact pins')
    if args.build not in ({'r15d', 'kF'} if args.workload == 'W1' else {'kF', 'kF0', 'kF1', 'kFscalar'}):
        raise ValueError('build is outside the prescribed workload')
    executable, net, fixture = [path.resolve(strict=True) for path in (args.engine, args.net, args.fixture)]
    if sha(executable) != expected or sha(net) != identity.NET_SHA or sha(Path(identity.__file__)) != HELPER_PIN:
        raise ValueError('engine, net or helper hash mismatch')
    if any(char in str(net) for char in '\r\n'):
        raise ValueError('invalid multiline net path')
    if not 0 < args.timeout <= 120:
        raise ValueError('timeout must be between 0 and 120 seconds')
    count, action = WORKLOADS[args.workload]
    fens = read_fixture(fixture)[:count]
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    started = utc()
    status, error = None, None
    try:
        capture(executable, net, fens, out, action, args.timeout)
        rows, status = read_raw(out, str(net), fens, action)
        if args.build == 'kFscalar' and not status['net_active'].endswith(' kernel scalar'):
            raise RuntimeError('supplemental kFscalar build did not select the scalar v3 kernel')
        write_rows(out, rows, action)
    except (OSError, RuntimeError, ValueError) as exc:
        error = str(exc)
    result = {'workload': args.workload, 'build': args.build, 'exe': str(executable), 'exe_sha256': expected,
              'net_path': str(net), 'net_sha256': identity.NET_SHA, 'fixture': str(fixture),
              'fixture_sha256': sha(fixture), 'started_utc': started, 'finished_utc': utc(), 'error': error,
              'rows_expected': count, 'action': action, 'pc20': identity.PC20,
              'runner_sha256': sha(Path(__file__)), 'identity_helper_sha256': HELPER_PIN,
              'files_sha256': {path.name: sha(path) for path in sorted(out.iterdir())}, **(status or {})}
    summary = json.dumps(result, indent=2) + '\n'
    (out / 'summary.json').write_text(summary, encoding='utf-8')
    print(summary, end='')
    return int(error is not None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    cli = parser.add_subparsers(dest='operation', required=True)
    start = cli.add_parser('run')
    start.add_argument('--workload', choices=WORKLOADS, required=True)
    start.add_argument('--build', choices=('r15d', 'kF', 'kF0', 'kF1', 'kFscalar'), required=True)
    for flag in ('engine', 'net', 'fixture', 'output'):
        start.add_argument('--'+flag, type=Path, required=True)
    start.add_argument('--exe-sha256')
    start.add_argument('--timeout', type=float, default=15)
    compare = cli.add_parser('compare')
    compare.add_argument('left', type=Path)
    compare.add_argument('right', type=Path)
    compare.add_argument('--fixture', type=Path)
    args = parser.parse_args()
    if args.operation == 'run':
        return run(args)
    result = compare_runs(args.left, args.right, args.fixture)
    print(json.dumps(result, indent=2))
    return int(result['differ'] != 0)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f'W1/W3 failed: {error}', file=sys.stderr)
        raise SystemExit(1) from error

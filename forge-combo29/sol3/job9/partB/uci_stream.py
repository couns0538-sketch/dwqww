import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import re
import sys

import identity


ENGINE_PINS = {
    'r15d': 'bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6',
    'k11v': 'a9d4eef3de37cf74611c59a2f35b64f205cf95b7463e65554271e64d1ce01c80',
}
HELPER_PIN = '1f7703dae17160651c6a9d163a4af0d14cb34848c7523fa70a50e260c86d93ca'
ALLOWED_BEFORE = {'go depth 4', 'go nodes 2000', 'setoption name Hash value 16', 'ucinewgame', 'isready'}
POSITION_TAIL = ('go perft 1', 'eval', 'isready')
VOLATILE_SEARCH_FIELD = re.compile(rb' (?:time|nps|hashfull) -?[0-9]+(?= |$)')
PERFT_TOTAL = re.compile(rb'nodes [0-9]+')
CHANNELS = ('common', 'search')


def digest(path):
    with path.open('rb') as data:
        return hashlib.file_digest(data, 'sha256').hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def fixture_rows(path):
    with path.open(encoding='ascii') as file:
        for line_no, line in enumerate(file, 1):
            row = json.loads(line)
            if not isinstance(row, dict) or row.get('index') != line_no:
                raise ValueError(f'fixture line {line_no}: index must equal line number')
            if not isinstance(row.get('kind'), str) or not isinstance(row.get('before'), list):
                raise ValueError(f'fixture line {line_no}: missing kind or before list')
            for command in [row.get('position'), *row['before']]:
                if (not isinstance(command, str) or not command.isascii() or
                        any(control in command for control in ('\n', '\r', '\0'))):
                    raise ValueError(f'fixture line {line_no}: invalid single-line UCI command {command!r}')
            fields = row['position'].split()
            if len(fields) < 2 or fields[0] != 'position' or fields[1] not in {'startpos', 'fen'}:
                raise ValueError(f'fixture line {line_no}: expected a position command')
            for command in row['before']:
                if ' '.join(command.split()) not in ALLOWED_BEFORE:
                    raise ValueError(f'fixture line {line_no}: unexpected before command {command!r}')
            yield row


def normalized(line):
    if line.startswith(b'info ') and not line.startswith(b'info string '):
        return VOLATILE_SEARCH_FIELD.sub(b'', line)
    return line


class Engine(identity.EngineRun):
    stdin_lines = 0
    stdout_lines = 0

    def send(self, command):
        super().send(command)
        self.stdin_lines += 1

    def receive(self, done, description):
        lines = super().receive(done, description)
        self.stdout_lines += len(lines)
        return lines


class Evidence:
    def __init__(self, events, stdout_by_channel):
        self.events = events
        self.stdout_by_channel = stdout_by_channel
        self.channel_lines = dict.fromkeys(CHANNELS, 0)
        self.stream_hash = hashlib.sha256()

    def record(self, engine, stdin_first, stdout_first, phase, row=None, before_index=None,
               channel=None, output=()):
        evidence = {
            'fixture_index': row['index'] if row is not None else None,
            'fixture_kind': row['kind'] if row is not None else None,
            'before_index': before_index,
            'phase': phase,
            'stdin': [stdin_first, engine.stdin_lines],
            'stdout': [stdout_first, engine.stdout_lines],
            'normalization': None,
        }
        if channel is not None and output:
            first = self.channel_lines[channel] + 1
            data = b''.join(normalized(line) + b'\n' for line in output)
            self.stream_hash.update(data)
            self.stdout_by_channel[channel].write(data)
            self.channel_lines[channel] += len(output)
            evidence['normalization'] = {
                'channel': channel, 'lines': [first, self.channel_lines[channel]], 'raw_first': stdout_first,
            }
        self.events.write(json.dumps(evidence, ensure_ascii=True, separators=(',', ':')) + '\n')


def pass_row(engine, evidence, row, mode):
    stdin_first, stdout_first = engine.stdin_lines + 1, engine.stdout_lines + 1
    for before_index, command in enumerate(row['before'], 1):
        kind = command.split()[0]
        engine.send(command)
        if kind == 'go':
            lines = engine.receive(lambda line: line.startswith(b'bestmove '), f'bestmove before row {row["index"]}')
            if not identity.BESTMOVE.fullmatch(lines[-1]):
                raise RuntimeError(f'row {row["index"]}: malformed bestmove {lines[-1]!r}')
            evidence.record(engine, stdin_first, stdout_first, 'before_search', row, before_index, 'search', lines)
        elif kind == 'isready':
            lines = engine.receive(lambda line: line == b'readyok', f'explicit readyok before row {row["index"]}')
            evidence.record(engine, stdin_first, stdout_first, 'before_ready', row, before_index, 'common', lines)
        else:
            continue
        stdin_first, stdout_first = engine.stdin_lines + 1, engine.stdout_lines + 1

    if mode == 'reset':
        engine.send('ucinewgame')
        lines = engine.ready()
        # Keep preceding output, if any, from the original stream's silent before commands.
        evidence.record(engine, stdin_first, stdout_first, 'artificial_reset', row, channel='common', output=lines[:-1])
        stdin_first, stdout_first = engine.stdin_lines + 1, engine.stdout_lines + 1

    engine.send(row['position'])
    for command in POSITION_TAIL:
        engine.send(command)
    lines = engine.receive(lambda line: line == b'readyok', f'position readyok for row {row["index"]}')
    evidence.record(engine, stdin_first, stdout_first, 'position_and_diagnostics', row, channel='common', output=lines)
    if (sum(bool(PERFT_TOTAL.fullmatch(line)) for line in lines) != 1 or
            sum(line.startswith(b'info string eval ') for line in lines) != 1):
        raise RuntimeError(f'row {row["index"]}: expected one perft total and one eval in raw output')


def run_stream(executable, net, rows, mode, output, timeout):
    output.mkdir(parents=True, exist_ok=False)
    raw = output / 'stdout.txt'
    stderr = output / 'stderr.txt'
    stdin = output / 'commands.txt'
    events = output / 'events.jsonl'
    common = output / 'common.txt'
    search = output / 'search.txt'
    started, done, failed_row, error = utc_now(), 0, None, None
    with (raw.open('xb') as out_log, stderr.open('x+b') as err_log, stdin.open('xb') as cmd_log,
          events.open('x', encoding='ascii') as events_log, common.open('xb') as common_log, search.open('xb') as search_log):
        evidence = Evidence(events_log, {'common': common_log, 'search': search_log})
        engine = Engine(executable, out_log, err_log, cmd_log, timeout)
        try:
            with engine:
                engine.set_up(net)
                evidence.record(engine, 1, 1, 'uci_and_options')
                for row in rows:
                    failed_row = row['index']
                    pass_row(engine, evidence, row, mode)
                    done += 1
                    failed_row = None
            identity.check_logs(raw, stderr)
        except (OSError, RuntimeError, ValueError) as exc:
            error = str(exc)

    ids, active, raw_lines = [], [], 0
    with raw.open('rb') as file:
        for raw_lines, line in enumerate(file, 1):
            if line.startswith(b'id name '):
                ids.append(line.rstrip(b'\r\n').decode('ascii', errors='backslashreplace'))
            if line.startswith(identity.NET_ACTIVE):
                active.append(line.rstrip(b'\r\n').decode('ascii', errors='backslashreplace'))
    if error is None and (raw_lines != engine.stdout_lines or len(ids) != 1 or len(active) != 1):
        error = (f'unexpected transcript coverage: raw={raw_lines}, grouped={engine.stdout_lines}, '
                 f'id name={len(ids)}, active net={len(active)}')
    return {
        'mode': mode,
        'started_utc': started,
        'finished_utc': utc_now(),
        'id_name_lines': ids,
        'net_activation_lines': active,
        'positions_completed': done,
        'failed_row': failed_row,
        'error': error,
        'raw_stdout_lines': raw_lines,
        'raw_stdin_lines': engine.stdin_lines,
        'normalized_stream_lines': sum(evidence.channel_lines.values()),
        'normalized_stream_sha256': evidence.stream_hash.hexdigest(),
        'normalized': {key: {'lines': value, 'sha256': digest(output / f'{key}.txt')}
                       for key, value in evidence.channel_lines.items()},
        'artifacts_sha256': {path.name: digest(path) for path in (raw, stderr, stdin, events, common, search)},
    }


def get_line(path, index):
    with path.open('rb') as src:
        return next(itertools.islice(src, index - 1, index), b'').rstrip(b'\r\n').decode('ascii', errors='backslashreplace')


def provenance(run, summary, channel, line_no, content):
    if content is None:
        return {'run': str(run), 'normalized_line': None, 'missing_at': line_no}
    with (run / 'events.jsonl').open(encoding='ascii') as events:
        for event in map(json.loads, events):
            norm = event['normalization']
            if norm is None or norm['channel'] != channel or not norm['lines'][0] <= line_no <= norm['lines'][1]:
                continue
            source_line = norm['raw_first'] + line_no - norm['lines'][0]
            fixture_index = event['fixture_index']
            fixture = json.loads(get_line(Path(summary['fixture']), fixture_index)) if fixture_index is not None else None
            return {
                'run': str(run), 'build': summary['build'], 'mode': summary['mode'],
                'channel': channel, 'normalized_line_no': line_no,
                'normalized_line': content.decode('ascii', errors='backslashreplace').rstrip('\n'),
                'raw_stdout': str(run / 'stdout.txt'), 'raw_stdout_line_no': source_line,
                'raw_stdout_line': get_line(run / 'stdout.txt', source_line),
                'raw_commands': str(run / 'commands.txt'), 'event': event, 'fixture_row': fixture,
            }
    raise RuntimeError(f'Could not attribute {run}:{channel}:{line_no}')


def compare_channel(channel, runs):
    summaries = [json.loads((run / 'summary.json').read_text(encoding='utf-8')) for run in runs]
    if any(result['error'] is not None for result in summaries):
        raise RuntimeError('Cannot compare failed UCI stream runs')
    if len({r['fixture_sha256'] for r in summaries}) != 1:
        raise RuntimeError('Cannot compare runs from different fixture hashes')
    if channel == 'search' and len({r['mode'] for r in summaries}) != 1:
        raise RuntimeError('Search comparisons require one mode')
    inputs = []
    for run, result in zip(runs, summaries):
        recorded = result['normalized'][channel]
        if digest(run / f'{channel}.txt') != recorded['sha256']:
            raise RuntimeError(f'Normalized {channel} file changed for {run}')
        inputs.append({'run': str(run), 'build': result['build'], 'mode': result['mode'], **recorded})

    comparisons = []
    for run, summary, expected in zip(runs[1:], summaries[1:], inputs[1:]):
        first = None
        if inputs[0]['sha256'] != expected['sha256']:
            with (runs[0] / f'{channel}.txt').open('rb') as left, (run / f'{channel}.txt').open('rb') as right:
                for line_no, (a, b) in enumerate(itertools.zip_longest(left, right), 1):
                    if a != b:
                        first = {
                            'baseline': provenance(runs[0], summaries[0], channel, line_no, a),
                            'candidate': provenance(run, summary, channel, line_no, b),
                        }
                        break
            if first is None:
                raise RuntimeError('Hashes differ but no differing line was found')
        comparisons.append({'baseline': inputs[0], 'candidate': expected, 'equal': first is None, 'first_difference': first})
    return {'channel': channel, 'comparisons': comparisons}


def main():
    parser = argparse.ArgumentParser(description='Job 9 Part B UCI stream runner and comparison.')
    tools = parser.add_subparsers(dest='task', required=True)
    run = tools.add_parser('run')
    run.add_argument('--build', choices=(*ENGINE_PINS, 'control'), required=True)
    run.add_argument('--mode', choices=('cached', 'reset'), required=True)
    run.add_argument('--engine', type=Path, required=True)
    run.add_argument('--net', type=Path, required=True)
    run.add_argument('--fixture', type=Path, required=True)
    run.add_argument('--output', type=Path, required=True)
    run.add_argument('--exe-sha256')
    run.add_argument('--timeout', type=float, default=15)
    compare = tools.add_parser('compare')
    compare.add_argument('channel', choices=CHANNELS)
    compare.add_argument('runs', type=Path, nargs='+')
    compare.add_argument('--expect-difference', action='store_true')
    args = parser.parse_args()

    if args.task == 'compare':
        if len(args.runs) < 2:
            parser.error('at least two runs are required for comparison')
        result = compare_channel(args.channel, [run.resolve(strict=True) for run in args.runs])
        print(json.dumps(result, indent=2))
        return int(not all(row['equal'] != args.expect_difference for row in result['comparisons']))

    if not 0 < args.timeout <= 60:
        parser.error('timeout must be between 0 and 60 seconds')
    executable = args.engine.resolve(strict=True)
    net = args.net.resolve(strict=True)
    fixture = args.fixture.resolve(strict=True)
    expected = ENGINE_PINS.get(args.build) or args.exe_sha256
    if expected is None or (args.exe_sha256 is not None and expected != args.exe_sha256):
        parser.error('a control needs its executable SHA-256; ordinary builds require the Job 8 pins')
    if digest(executable) != expected or digest(net) != identity.NET_SHA:
        raise ValueError('executable or net768 differs from the required hash')
    if digest(Path(identity.__file__)) != HELPER_PIN:
        raise ValueError('Job 4 identity helper differs from its required hash')
    if any(char in str(net) for char in '\r\n'):
        raise ValueError('net path must fit on one UCI line')
    count = sum(1 for _ in fixture_rows(fixture))
    if count < 5000:
        raise ValueError(f'fixture has {count} position commands; expected at least 5000')
    result = run_stream(executable, net, fixture_rows(fixture), args.mode, args.output, args.timeout)
    result.update({
        'fixture': str(fixture), 'fixture_sha256': digest(fixture), 'positions_expected': count,
        'build': args.build, 'exe': str(executable), 'exe_sha256': expected,
        'net': str(net), 'net_sha256': identity.NET_SHA, 'options': identity.PC20,
        'timeout_s': args.timeout, 'runner_sha256': digest(Path(__file__)), 'identity_helper_sha256': HELPER_PIN,
        'normalized_scope': 'fixture outputs only; time/nps/hashfull search fields and artificial reset readyok removed',
    })
    rendered = json.dumps(result, indent=2) + '\n'
    (args.output / 'summary.json').write_text(rendered, encoding='utf-8')
    print(rendered, end='')
    return int(result['error'] is not None or result['positions_completed'] != count)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as exc:
        print(f'UCI stream run failed: {exc}', file=sys.stderr)
        raise SystemExit(1) from exc

"""Replay two reference ladders on a trace build; require parity before examining the requested depth."""

import argparse
import csv
import os
from pathlib import Path
import subprocess
import sys


FIELDS = ("requested_depth", "info_depth", "bestmove", "score_type", "score", "nodes")


def rows(path):
    with path.open(encoding="utf-8", newline="") as table:
        result = list(csv.DictReader(table, delimiter="\t"))
    if not result or not all(key in result[0] for key in FIELDS):
        raise ValueError(f"missing depth ladder in {path}")
    depths = [int(row['requested_depth']) for row in result]
    if depths != list(range(depths[0], depths[-1] + 1)):
        raise ValueError(f"incomplete depth ladder in {path}")
    return result


def settings(path):
    metadata = path.with_suffix('.meta').read_text().splitlines()
    return [line for line in metadata if line.startswith('setoption name ')]


def run(args):
    refs = {'pc20': args.pc20, args.winner.stem: args.winner}
    if args.also:
        refs[args.also.stem] = args.also
    data = {name: rows(ref) for name, ref in refs.items()}
    active = {name: settings(ref) for name, ref in refs.items()}
    base = active['pc20']
    opts = {}
    for name in refs:
        opts[name] = []
        if name == 'pc20':
            continue
        if not base or active[name][:len(base)] != base or len(active[name]) <= len(base):
            raise ValueError('winner settings must append at least one switch to the PC20 commands')
        for command in active[name][len(base):]:
            option, value = command.removeprefix('setoption name ').rsplit(' value ', 1)
            opts[name].extend(['--set', f'{option}={value}'])
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output/'trace-parity.txt').open('x', encoding='utf-8') as report:
        for trace in [False, True]:
            for name, ref in refs.items():
                expected = [row for row in data[name] if not trace or int(row['requested_depth']) == args.depth]
                if not expected:
                    raise ValueError(f'{ref}: reference depth {args.depth} missing')
                first, last = expected[0]['requested_depth'], expected[-1]['requested_depth']
                prefix = args.output/f"{'trace' if trace else 'parity'}-{name}"
                cmd = [sys.executable, str(args.ladder), str(args.exe), 'PC20', str(prefix), '--first', first, '--last', last]
                cmd.extend(opts[name])
                env = os.environ.copy()
                if trace:
                    env['ASTRA5_TRACE'] = '1'
                else:
                    env.pop('ASTRA5_TRACE', None)
                subprocess.run(cmd, check=True, env=env)
                observed = rows(prefix.with_suffix('.tsv'))
                if active[name] != settings(prefix):
                    raise ValueError(f'{prefix}: ordered UCI settings differ from reference')
                if len(observed) != len(expected):
                    raise ValueError(f'{prefix}: row count {len(observed)} != {len(expected)}')
                for a, b in zip(observed, expected):
                    actual = tuple(a[key] for key in FIELDS)
                    reference = tuple(b[key] for key in FIELDS)
                    if actual != reference:
                        msg = f'{prefix.name}: parity FAIL actual={actual} reference={reference}'
                        print(msg, file=report, flush=True)
                        raise ValueError(msg)
                count = 0
                with prefix.with_suffix('.raw.txt').open(encoding='utf-8') as raw:
                    log = None
                    try:
                        if trace:
                            log = prefix.with_suffix('.events.txt').open('x', encoding='utf-8')
                        for line in raw:
                            if line.startswith('< AS3TRACE'):
                                count += 1
                                if log:
                                    log.write(line[2:])
                    finally:
                        if log:
                            log.close()
                if not trace and count:
                    raise ValueError(f'{prefix}: unexpected trace output with ASTRA5_TRACE unset')
                print(f'{prefix.name}: {len(observed)} rows, all depths/scores/moves/nodes equal to {ref.name}; '
                      f'ordered settings equal; {count} AS3TRACE lines', file=report, flush=True)
                if trace and count == 0:
                    raise ValueError(f'{prefix}: trace enabled, no AS3TRACE events')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ladder', type=Path)
    parser.add_argument('exe', type=Path)
    parser.add_argument('pc20', type=Path, help='PC20 Step 1 .tsv, with .meta alongside')
    parser.add_argument('winner', type=Path, help='winning Step 3 .tsv, with .meta alongside')
    parser.add_argument('--also', type=Path, help='additional tied winning ladder')
    parser.add_argument('depth', type=int)
    parser.add_argument('output', type=Path)
    run(parser.parse_args())


if __name__ == '__main__':
    main()

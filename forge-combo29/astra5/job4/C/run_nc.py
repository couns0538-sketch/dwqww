"""Collect one post-bestmove null counter line and one sidecar count per fixed-depth search."""

import argparse
import csv
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

# In the committed tree this file belongs beside job1's sibling job4 directory.
# Supply the archived Job 1 path via PYTHONPATH when running this scratch copy.
for ancestor in Path(__file__).resolve().parents:
    if (ancestor / 'job1' / 'harness.py').is_file():
        sys.path.insert(0, str(ancestor / 'job1'))
        break
from harness import PC20, identify, lines, send


def ready(process):
    send(process, 'isready')
    for line in lines(process):
        if line.startswith('NC0'):
            raise ValueError(f'unexpected extra counter before readyok: {line}')
        if line == 'readyok':
            return
    raise RuntimeError('engine exited before readyok')


def measured_search(process, fen, depth):
    send(process, 'ucinewgame')
    ready(process)
    send(process, 'position fen ' + fen)
    send(process, f'go depth {depth}')
    nodes = None
    best = None
    for line in lines(process):
        if best is not None:
            if not re.fullmatch(r'NC0(?: [0-9]+){8}', line):
                raise ValueError(f'expected NC0 and eight counts immediately after bestmove, got {line!r}')
            return nodes, best, line
        if line.startswith('NC0'):
            raise ValueError(f'counter before bestmove: {line}')
        if line.startswith('info ') and re.search(r'\bdepth \d+\b', line):
            match = re.search(r'\bnodes (\d+)\b', line)
            if match:
                nodes = int(match.group(1))
        if line.startswith('bestmove '):
            if nodes is None:
                raise ValueError('bestmove without completed depth and nodes')
            best = line.split()[1]
    raise RuntimeError(f'engine exited before the post-bestmove counter for {fen}')


def run(args, process, sidecar):
    identity, available = identify(process)
    options = [('Threads', '1'), ('Hash', '16'), *PC20, ('NullChildFloor', str(args.floor))]
    commands = []
    for name, value in options:
        if name not in available:
            raise ValueError(f'{name} missing from UCI listing')
        command = f'setoption name {name} value {value}'
        commands.append(command)
        send(process, command)
    ready(process)
    meta = Path(str(args.rows) + '.meta')
    with args.epd.open() as epd, args.rows.open('x', newline='') as output, meta.open('x') as metadata:
        metadata.write(f'exe {args.exe}\nsha256 {hashlib.sha256(args.exe.read_bytes()).hexdigest()}\n')
        metadata.write(f'{identity}\ncwd {Path.cwd()}\nepd {args.epd}\ndepth {args.depth}\n')
        metadata.write('\n'.join(commands) + '\n')
        metadata.write('started_1_2 is read from the per-process ASTRA5_NC_STARTED12 sidecar after each NC0\n')
        metadata.flush()
        writer = csv.writer(output, delimiter='\t', lineterminator='\n')
        writer.writerow(('index', 'fen', 'nodes', 'bestmove', 'nc0', 'started_1_2'))
        count = 0
        for count, position in enumerate(epd, 1):
            fields = position.split()
            if len(fields) < 4:
                raise ValueError(f'position {count} has fewer than four fields')
            fen = ' '.join(fields[:4]) + ' 0 1'
            nodes, best, counter_line = measured_search(process, fen, args.depth)
            supplemental = sidecar.readline()
            if not re.fullmatch(r'[0-9]+\n', supplemental):
                raise ValueError(f'position {count}: invalid started_1_2 value {supplemental!r}')
            if sidecar.readline():
                raise ValueError(f'position {count}: more than one supplemental count')
            writer.writerow((count, fen, nodes, best, counter_line, int(supplemental)))
            output.flush()
        if count == 0:
            raise ValueError('empty EPD input')
        send(process, 'quit')
        for line in lines(process):
            if line.startswith('NC0'):
                raise ValueError('extra NC0 after final search')
        if process.wait() or sidecar.readline():
            raise RuntimeError('unclean engine exit or unmatched supplemental count')
        metadata.write(f'completed_rows {count}\n')
        print(f'{args.rows.name}: {count} NC0 lines')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path)
    parser.add_argument('epd', type=Path)
    parser.add_argument('depth', type=int)
    parser.add_argument('floor', type=int, choices=range(4))
    parser.add_argument('rows', type=Path)
    args = parser.parse_args()
    args.exe = args.exe.resolve(strict=True)
    with tempfile.TemporaryDirectory() as directory:
        sidepath = Path(directory) / 'started_1_2.txt'
        sidepath.touch()
        env = dict(os.environ, ASTRA5_NC_STARTED12=str(sidepath))
        with sidepath.open() as sidecar, subprocess.Popen(
            [str(args.exe)], text=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, encoding='utf-8', env=env, bufsize=1,
        ) as process:
            try:
                run(args, process, sidecar)
            finally:
                if process.poll() is None:
                    process.kill()


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, RuntimeError) as exc:
        sys.exit(f'STOP: {exc}')

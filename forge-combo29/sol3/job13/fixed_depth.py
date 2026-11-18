import argparse
import csv
import hashlib
from pathlib import Path
import re

from identity import EngineRun, BESTMOVE, check_logs

NET_SHA256 = 'c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
INFO = re.compile(rb'^info depth (\d+)\b.*?\bscore (cp|mate) (-?\d+)\b.*?\bnodes (\d+)\b')
COUNT = re.compile(rb'^NC0 ((?:\d+ ){4}\d+)$')
FIELDS = ('index', 'fen', 'requested_depth', 'info_depth', 'bestmove', 'score_type', 'score', 'nodes',
          'last_info', 'bestmove_line')

def fixture(path):
    data = path.read_bytes()
    fens = [line.strip() for line in data.decode('ascii').splitlines()]
    if not fens or any(len(fen.split()) != 6 for fen in fens):
        raise ValueError(f'{path}: expected six-field FENs')
    return fens

def decode_row(reply):
    best = BESTMOVE.fullmatch(reply[-1])
    last = next((line for line in reversed(reply[:-1]) if line.startswith(b'info depth ')), b'')
    info = INFO.match(last)
    if best is None or info is None:
        raise ValueError(f'Incomplete result {reply!r}')
    return (int(info[1]), best[1].decode('ascii'), info[2].decode('ascii'), int(info[3]),
            int(info[4]), last.decode('ascii'), reply[-1].decode('ascii'))

def main():
    parser = argparse.ArgumentParser(description='Capture independent fixed-depth searches.')
    parser.add_argument('engine', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('fixture', type=Path)
    parser.add_argument('--ladder', type=int, help='One position, requested depths 1 through this value')
    parser.add_argument('--depth', type=int, help='Every fixture position at this requested depth')
    parser.add_argument('--net', type=Path)
    parser.add_argument('--null-base', type=int, choices=(3,))
    parser.add_argument('--counter', action='store_true')
    args = parser.parse_args()
    fens = fixture(args.fixture)
    if (args.ladder is None) == (args.depth is None):
        parser.error('choose one of --ladder and --depth')
    if args.ladder is not None:
        if len(fens) != 1 or args.ladder <= 0:
            parser.error('a ladder requires a single FEN and positive final depth')
        tests = [(fens[0], depth) for depth in range(1, args.ladder + 1)]
    else:
        if args.depth <= 0:
            parser.error('positive depth required')
        tests = [(fen, args.depth) for fen in fens]
    if args.net is not None:
        if hashlib.sha256(args.net.read_bytes()).hexdigest() != NET_SHA256:
            raise ValueError('net768 hash mismatch')
    args.out.mkdir(parents=True, exist_ok=True)
    raw = args.out / 'engine.stdout.txt'
    errors = args.out / 'engine.stderr.txt'
    commands = args.out / 'engine.commands.txt'
    field_names = (*FIELDS, *(f'nc{i}' for i in range(5))) if args.counter else FIELDS
    with raw.open('xb') as stdout, errors.open('x+b') as stderr, commands.open('xb') as stdin:
        with (args.out / 'rows.tsv').open('x', encoding='ascii', newline='', buffering=1) as table:
            writer = csv.writer(table, delimiter='\t', lineterminator='\n')
            writer.writerow(field_names)
            with EngineRun(args.engine, stdout, stderr, stdin, 120) as engine:
                engine.set_up(args.net)
                if args.null_base is not None:
                    engine.send(f'setoption name NullMoveBase value {args.null_base}')
                    engine.ready()
                for index, (fen, depth) in enumerate(tests, 1):
                    engine.send('ucinewgame')
                    engine.ready()
                    engine.send(f'position fen {fen}')
                    engine.send(f'go depth {depth}')
                    response = engine.receive(lambda line: line.startswith(b'bestmove '), f'bestmove, row {index}')
                    row = [index, fen, depth, *decode_row(response)]
                    if args.counter:
                        marker = engine.receive(lambda line: line.startswith(b'NC0 '), f'NC0, row {index}')
                        found = COUNT.fullmatch(marker[0]) if len(marker) == 1 else None
                        if found is None:
                            raise ValueError(f'Expected one NC0 line immediately after bestmove, row {index}: {marker!r}')
                        counts = tuple(map(int, found[1].split()))
                        started, shallow, cutoffs, shallow_cutoffs, quiet = counts
                        if not (quiet <= shallow_cutoffs <= min(shallow, cutoffs) and max(shallow, cutoffs) <= started):
                            raise ValueError(f'Inconsistent NC0 fields, row {index}: {counts!r}')
                        row.extend(counts)
                    writer.writerow(row)
    check_logs(raw, errors)

if __name__ == '__main__':
    main()

import argparse
import csv
from pathlib import Path

from identity import BESTMOVE, EngineRun, check_logs
from ladder import COUNT, FIELDS as LADDER_FIELDS, INFO, search, setup


QUIET_ONLY = (('HistReworkQuiet', 2), ('HistReworkCorrection', 0))
SETTINGS = {
    'A': ('S14', ()),
    'B': ('S14', QUIET_ONLY),
    'D': ('S14', (*QUIET_ONLY, ('QuietReadPlainR3', 1))),
    'C': ('S14', (*QUIET_ONLY, ('QuietReadPlainR1', 1))),
    'E': ('PC20', ()),
    'G': ('PC20', (('HistReworkQuiet', 0),)),
    'F': ('PC20', (('QuietReadPlainR3', 1),)),
}
CENSUS_FIELDS = ('index', 'fen', 'game', 'plies_before_end', 'pieces', 'first_mate_depth',
                 'first_mate_nodes', 'info_depth', 'score_type', 'score', 'nodes',
                 'bestmove', *(f'nc{i}' for i in range(5)))


def load_positions(path, expected_count):
    records = []
    for number, line in enumerate(path.read_text(encoding='ascii').splitlines(), 1):
        fen, game, plies, pieces = line.split('\t')
        on_board = sum(piece in 'PNBRQKpnbrqk' for piece in fen.split()[0])
        if len(fen.split()) != 6 or int(game) < 1 or int(plies) not in (3, 5, 7) or int(pieces) != on_board:
            raise ValueError(f'invalid position record {number}: {line!r}')
        records.append((fen, int(game), int(plies), int(pieces)))
    if len(records) != expected_count:
        raise ValueError(f'expected {expected_count} positions, found {len(records)}')
    return records


def census_search(engine, depth_limit, index, fen, game, plies, pieces):
    engine.send('ucinewgame')
    engine.ready()
    engine.send(f'position fen {fen}')
    engine.send(f'go depth {depth_limit}')
    response = engine.receive(lambda line: line.startswith(b'bestmove '), f'bestmove at row {index}')
    best = BESTMOVE.fullmatch(response[-1])
    infos = [line for line in response[:-1] if line.startswith(b'info depth ')]
    fields = [INFO.match(line) for line in infos]
    if best is None or not fields or any(field is None for field in fields):
        raise ValueError(f'missing or invalid depth or bestmove at row {index}: {response!r}')
    first_mate = next((field for line, field in zip(infos, fields, strict=True)
                       if field[2] == b'mate' and int(field[3]) > 0
                       and b'lowerbound' not in line.split() and b'upperbound' not in line.split()), None)
    last = fields[-1]
    depth = int(last[1])
    if not 1 <= depth <= depth_limit or any(not 1 <= int(field[1]) <= depth_limit for field in fields):
        raise ValueError(f'unexpected depth at row {index}: {infos!r}')
    marker = engine.receive(lambda line: line.startswith(b'NC0 '), f'NC0 at row {index}')
    count = COUNT.fullmatch(marker[0]) if len(marker) == 1 else None
    if count is None:
        raise ValueError(f'expected one NC0 immediately after bestmove at row {index}: {marker!r}')
    counters = tuple(map(int, count[1].split()))
    return (index, fen, game, plies, pieces, int(first_mate[1]) if first_mate else '',
            int(first_mate[4]) if first_mate else '', depth, last[2].decode('ascii'),
            int(last[3]), int(last[4]), best[1].decode('ascii'), *counters)


def main():
    parser = argparse.ArgumentParser(description='Run a Job 18 ladder, census or depth-22 retest.')
    parser.add_argument('engine', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('mode', choices=('ladder', 'census', 'extension'))
    parser.add_argument('setting', choices=SETTINGS)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    profile, overrides = SETTINGS[args.setting]
    args.out.mkdir(parents=True, exist_ok=True)
    raw = args.out / 'engine.stdout.txt'
    errors = args.out / 'engine.stderr.txt'
    commands = args.out / 'engine.commands.txt'
    ladder = args.mode == 'ladder'
    if ladder:
        fen = args.input.read_text(encoding='ascii').strip()
        if len(fen.split()) != 6 or '\n' in fen:
            raise ValueError('ladder requires one bare six-field FEN')
    else:
        extension = args.mode == 'extension'
        records = load_positions(args.input, 1 if extension else 120)
        depth_limit = 22 if extension else 16
    with (raw.open('xb') as stdout, errors.open('x+b') as stderr, commands.open('xb') as stdin,
          (args.out / 'rows.tsv').open('x', encoding='ascii', newline='', buffering=1) as table):
        writer = csv.writer(table, delimiter='\t', lineterminator='\n')
        writer.writerow(LADDER_FIELDS if ladder else CENSUS_FIELDS)
        with EngineRun(args.engine, stdout, stderr, stdin, 120) as engine:
            setup(engine, profile, overrides)
            if ladder:
                for depth in range(1, 21):
                    writer.writerow(search(engine, fen, depth))
            else:
                for index, (fen, game, plies, pieces) in enumerate(records, 1):
                    writer.writerow(census_search(engine, depth_limit, index, fen, game, plies, pieces))
    check_logs(raw, errors)


if __name__ == '__main__':
    main()

import argparse
import csv
from pathlib import Path
import re

from identity import BESTMOVE, EngineRun, NET_ACTIVE, OPTION, PC20, check_logs


INFO = re.compile(rb'^info depth (\d+)\b.*?\bscore (cp|mate) (-?\d+)\b.*?\bnodes (\d+)\b')
COUNT = re.compile(rb'^NC0 ((?:\d+ ){4}\d+)$')
SETTING = re.compile(r'^setoption name (\w+) value (-?\w+)$')
OVERRIDES = {
    'HistRework': (0, 3),
    'HistReworkQuiet': (-1, 3),
    'HistReworkCorrection': (-1, 3),
    **{f'QuietReadPlainR{i}': (0, 1) for i in range(1, 4)},
}
FIELDS = ('requested_depth', 'info_depth', 'bestmove', 'score_type', 'score',
          'nodes', 'last_info', 'bestmove_line', *(f'nc{i}' for i in range(5)))


def setup(engine, profile, overrides):
    engine.send('uci')
    hello = engine.receive(lambda line: line == b'uciok', 'uciok')
    advertised = {match[1].decode('ascii') for line in hello if (match := OPTION.match(line))}
    expected = ['NNUEArch type check default false', 'UseNNUE type check default true',
                'MultiPV type spin default 1 min 1 max 8', 'NullMateGuard type spin default 0 min 0 max 1',
                'HistReworkQuiet type spin default -1 min -1 max 3',
                'HistReworkCorrection type spin default -1 min -1 max 3']
    if profile == 'S14':
        expected += ['HistRework type spin default 0 min 0 max 3', 'OwnBook type check default true',
                     *(f'{name} type check default false' for name in
                       ('CuckooRep', 'TtPruneV2', 'CorrHistV2', 'MateAlphaGuard'))]
    for option in expected:
        if ('option name ' + option).encode('ascii') not in hello:
            raise ValueError(f'unexpected advertised option default: {option}')
    if profile == 'S14':
        settings = (Path(__file__).parent / 'S14.setoption.txt').read_text(encoding='ascii').splitlines()
    else:
        settings = [f'setoption name {name} value {value}' for name, value in PC20.items()]
    settings += [f'setoption name {name} value {value}' for name, value in overrides]
    for setting in settings:
        match = SETTING.fullmatch(setting)
        if match is None or match[1] not in advertised:
            raise ValueError(f'invalid or unadvertised option {setting!r}')
        engine.send(setting)
    if any(line.startswith(NET_ACTIVE) for line in engine.ready()):
        raise ValueError('external NNUE activated in built-in evaluation check')


def search(engine, fen, depth):
    engine.send('ucinewgame')
    engine.ready()
    engine.send(f'position fen {fen}')
    engine.send(f'go depth {depth}')
    response = engine.receive(lambda line: line.startswith(b'bestmove '), f'bestmove, D{depth}')
    best = BESTMOVE.fullmatch(response[-1])
    last = next((line for line in reversed(response[:-1]) if line.startswith(b'info depth ')), b'')
    info = INFO.match(last)
    marker = engine.receive(lambda line: line.startswith(b'NC0 '), f'NC0, D{depth}')
    count = COUNT.fullmatch(marker[0]) if len(marker) == 1 else None
    if best is None or info is None or count is None:
        raise ValueError(f'incomplete D{depth} result: {last!r} {response[-1]!r} {marker!r}')
    counters = tuple(map(int, count[1].split()))
    started, shallow, cutoffs, shallow_cutoffs, quiet = counters
    if quiet > shallow_cutoffs or shallow_cutoffs > min(shallow, cutoffs) or max(shallow, cutoffs) > started:
        raise ValueError(f'inconsistent D{depth} NC0 counters: {counters!r}')
    return (depth, int(info[1]), best[1].decode('ascii'), info[2].decode('ascii'), int(info[3]),
            int(info[4]), last.decode('ascii'), response[-1].decode('ascii'), *counters)


def main():
    parser = argparse.ArgumentParser(description='Capture a fresh-game fixed-depth P ladder.')
    parser.add_argument('engine', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('fixture', type=Path)
    parser.add_argument('--profile', choices=('S14', 'PC20'), required=True)
    parser.add_argument('--option', action='append', default=[])
    args = parser.parse_args()
    fen = args.fixture.read_text(encoding='ascii').strip()
    if len(fen.split()) != 6 or '\n' in fen:
        parser.error('one bare six-field FEN is required')
    overrides = []
    for item in args.option:
        name, separator, value = item.partition('=')
        if not separator or name not in OVERRIDES or not re.fullmatch(r'-?\d+', value):
            parser.error(f'invalid override {item!r}')
        low, high = OVERRIDES[name]
        if not low <= int(value) <= high:
            parser.error(f'out of range {item!r}')
        overrides.append((name, int(value)))
    args.out.mkdir(parents=True, exist_ok=True)
    raw = args.out / 'engine.stdout.txt'
    errors = args.out / 'engine.stderr.txt'
    commands = args.out / 'engine.commands.txt'
    with (raw.open('xb') as stdout, errors.open('x+b') as stderr, commands.open('xb') as stdin,
          (args.out / 'rows.tsv').open('x', encoding='ascii', newline='', buffering=1) as table):
        writer = csv.writer(table, delimiter='\t', lineterminator='\n')
        writer.writerow(FIELDS)
        with EngineRun(args.engine, stdout, stderr, stdin, 120) as engine:
            setup(engine, args.profile, overrides)
            for depth in range(1, 21):
                writer.writerow(search(engine, fen, depth))
    check_logs(raw, errors)


if __name__ == '__main__':
    main()

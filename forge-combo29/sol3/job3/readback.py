import argparse
import re
from pathlib import Path


SETTINGS = '''
Threads=1 Hash=16 MultiPV=1 UseNNUE=true OwnBook=false
LmrQuietBase=93 LmrQuietDivisor=205 LmrNoisyBase=13 LmrNoisyDivisor=333
LmrHistoryDivisor=5643 NullMoveBase=5 LmpBase=8 HistoryPruneMultiplier=2220
HistoryBonusQuadratic=24 HistoryBonusLinear=54 HistoryBonusMax=2212 SingularDepth=6
IirDepth=2 NonPawnCorrection=true CuckooRep=true HistRework=2 TtPruneV2=true
CorrHistV2=true MateAlphaGuard=true
'''.split()
REFUSAL = re.compile(r'unknown option|invalid value|\berror\b|invalid fen', re.I)
BENCH = re.compile(r'info string bench depth (11|13) nodes (\d+) time \d+ nps \d+')
MOVE = re.compile(r'0000|[a-h][1-8][a-h][1-8][qrbn]?')


def require(condition, problem):
    if not condition:
        raise ValueError(problem)


def match_lines(observed, expected, label):
    for index, pair in enumerate(zip(observed, expected), 1):
        require(pair[0] == pair[1], f'{label} line {index}: saw {pair[0]!r}, expected {pair[1]!r}')
    require(len(observed) == len(expected), f'{label}: saw {len(observed)} lines, expected {len(expected)}')


def check_arm(directory, fens):
    arm = directory.name

    def read(name):
        return (directory / name).read_text(encoding='utf-8').splitlines()

    def engine_log(name):
        lines = read(name)
        refusal = next((line for line in lines if REFUSAL.search(line)), None)
        require(refusal is None, f'{name}: {refusal}')
        return lines

    receipt = read(f'run_{arm}.txt')
    require(receipt and receipt[-1].endswith('Identity ended exit 0'), f'arm {arm}: incomplete run receipt')
    setup = ['uci', *[f'setoption name {name} value {value}'
                       for name, value in (entry.split('=', 1) for entry in SETTINGS)], 'isready']
    match_lines(read(f'bench_{arm}.commands.txt'), [*setup, 'bench 11', 'quit', *setup, 'bench 13', 'quit'], 'bench commands')
    bench_raw = engine_log(f'bench_{arm}.txt')
    engine_log(f'bench_{arm}.stderr.txt')
    phases = [line for line in bench_raw if line in {'uciok', 'readyok'} or line.startswith('info string bench ')]
    require(len(phases) == 6, f'wrong bench phase count: {phases}')
    pins = []
    for depth, offset in ((11, 0), (13, 3)):
        require(phases[offset:offset + 2] == ['uciok', 'readyok'], f'bench {depth}: missing handshakes')
        result = BENCH.fullmatch(phases[offset + 2])
        require(result is not None and int(result[1]) == depth, f'bench {depth}: {phases[offset + 2]}')
        pins.append(int(result[2]))

    search_commands = [*setup]
    for fen in fens:
        search_commands.extend(('ucinewgame', 'isready', f'position fen {fen}', 'go depth 10'))
    search_commands.append('quit')
    match_lines(read(f'identity_{arm}.commands.txt'), search_commands, 'identity commands')
    search_raw = engine_log(f'identity_{arm}.stdout.txt')
    engine_log(f'identity_{arm}.stderr.txt')
    ready = [index for index, line in enumerate(search_raw) if line == 'readyok']
    require(len(ready) == len(fens) + 1, f'saw {len(ready)} readyok lines for {len(fens)} FENs')
    require(search_raw[:ready[0]].count('uciok') == 1 and search_raw.count('uciok') == 1, 'unexpected uciok sequence')
    ready.append(len(search_raw))
    rows = []
    for index, (begin, end) in enumerate(zip(ready, ready[1:])):
        fields = [line.split() for line in search_raw[begin + 1:end]]
        moves = [offset for offset, tokens in enumerate(fields) if tokens[:1] == ['bestmove']]
        depths = [offset for offset, tokens in enumerate(fields) if tokens[:2] == ['info', 'depth']]
        if index == 0:
            require(not moves and not depths, 'search output before the first FEN reset')
            continue
        require(len(moves) == 1 and depths and depths[-1] < moves[0], f'row {index}: missing or misplaced search output')
        report = fields[depths[-1]]
        move = fields[moves[0]][1]
        require(MOVE.fullmatch(move) is not None, f'row {index}: unexpected bestmove {move!r}')
        require(0 <= int(report[2]) <= 10, f'row {index}: unexpected depth in {report}')
        nodes = int(report[report.index('nodes') + 1])
        require(nodes >= 0, f'row {index}: negative nodes')
        rows.append((nodes, move))
    match_lines(read(f'rows_{arm}.txt'), [f'{index}\t{nodes}\t{move}' for index, (nodes, move) in enumerate(rows, 1)], 'identity rows')
    return pins, rows


def main():
    parser = argparse.ArgumentParser(description='Recompute Forge identity summaries from raw UCI evidence.')
    parser.add_argument('positions', type=Path)
    parser.add_argument('arms_dir', type=Path)
    parser.add_argument('arms', nargs='*', help='arm directory suffixes, default all')
    args = parser.parse_args()
    fens = args.positions.read_text(encoding='ascii').splitlines()
    require(fens and all(len(fen.split()) == 6 for fen in fens), 'expected bare ordered FENs')
    arms = args.arms or sorted((path.name for path in args.arms_dir.iterdir() if path.is_dir()),
                               key=lambda name: (not name.isdigit(), int(name) if name.isdigit() else name))
    require('0' in arms, 'reference arm 0 is required')
    base_pins, baseline = check_arm(args.arms_dir / '0', fens)
    print('arm\tbench_11\tbench_13\trows\tequal_to_0\tfirst_difference (row, arm_0, arm)')
    for arm in arms:
        try:
            pins, rows = (base_pins, baseline) if arm == '0' else check_arm(args.arms_dir / arm, fens)
        except (OSError, ValueError, IndexError) as error:
            raise SystemExit(f'arm {arm}: {error}') from error
        changes = [(index, base, actual) for index, (base, actual) in enumerate(zip(baseline, rows), 1)
                   if base != actual]
        print(arm, *pins, len(rows), len(rows) - len(changes), changes[0] if changes else '-', sep='\t')


if __name__ == '__main__':
    main()

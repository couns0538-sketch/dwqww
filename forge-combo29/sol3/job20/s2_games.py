#!/usr/bin/env python3
"""Run Job 20 S2 from the pinned W1 FENs, retaining complete UCI transcripts."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

import chess

import identity


FIXTURE_SHA = '3c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521'
HELPER_SHA = '4a51fe258b610b32055cc7e42614640d9dd0abb8988fdb304d1ad31f7fbcef61'
CHESS_VERSION = '1.11.2'
BUILDS = ('r15d-shadow', 'kF-shadow')
FIRST_POSITION = 21
LAST_POSITION = 40
MOVE_CAP = 200
SOFT_NODES = 2000
HARD_NODES = 4 * SOFT_NODES
SUMMARY = re.compile(rb'info string shadow evals ([0-9]+) differ ([0-9]+)')
DETAIL = re.compile(rb'info string shadow differ fast (-?[0-9]+) ref (-?[0-9]+) fen (.+)')
FINAL = re.compile(rb'info string softnodes nodes ([0-9]+)')
BEST = re.compile(rb'bestmove (' + identity.UCI_MOVE + rb')(?: ponder (' + identity.UCI_MOVE + rb'))?')
LAST_INFO = re.compile(
    rb'info depth ([0-9]+) seldepth ([0-9]+) score (cp|mate) (-?[0-9]+) '
    rb'nodes ([0-9]+) nps [0-9]+ hashfull [0-9]+ time [0-9]+ pv(?: (.+))?'
)
NUMBERS = ('evals', 'differ', 'final_nodes', 'last_info_nodes')


def sha(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def fens_from_fixture(path):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA:
        raise ValueError('unexpected W1 fixture SHA-256')
    if not raw.endswith(b'\n') or b'\r' in raw:
        raise ValueError('expected LF line endings with final LF')
    fens = raw.decode('ascii').splitlines()
    if len(fens) != 1000:
        raise ValueError('expected exactly 1,000 W1 positions')
    return fens[FIRST_POSITION - 1:LAST_POSITION]


def decode(line):
    return line.decode('ascii')


def parse_result(lines, prior_details):
    best = BEST.fullmatch(lines[-1])
    if best is None:
        raise ValueError('missing legal bestmove on a playable root')
    if len(lines) < 2 or (shadow := SUMMARY.fullmatch(lines[-2])) is None:
        raise ValueError('missing shadow count immediately before bestmove')
    evals, differ = map(int, shadow.groups())
    if differ > evals:
        raise ValueError('shadow differences exceed evaluations')
    shadow_lines = [line for line in lines[:-2] if line.startswith(b'info string shadow')]
    details = []
    for line in shadow_lines:
        match = DETAIL.fullmatch(line)
        if match is None:
            raise ValueError('unexpected or duplicate shadow line')
        fast, ref = map(int, match.groups()[:2])
        fen = decode(match[3])
        if fast == ref or len(fen.split()) != 6:
            raise ValueError('invalid shadow difference detail')
        details.append({'fast': fast, 'ref': ref, 'fen': fen, 'line': decode(line)})
    if len(details) != min(5 - prior_details, differ):
        raise ValueError('shadow detail lines do not match the first-five-differences rule')

    final_lines = [line for line in lines[:-2] if line.startswith(b'info string softnodes nodes')]
    last_info = next((line for line in reversed(lines[:-2]) if line.startswith(b'info depth ')), b'')
    final = FINAL.fullmatch(final_lines[0]) if len(final_lines) == 1 else None
    last = LAST_INFO.fullmatch(last_info)
    if final is None or last is None:
        raise ValueError('expected one exact softnodes total and one parseable last depth line')
    final_nodes = int(final[1])
    last_nodes = int(last[5])
    if not 0 < last_nodes <= final_nodes <= HARD_NODES:
        raise ValueError(f'invalid node counts: last-info={last_nodes}, consumed={final_nodes}')
    pv = decode(last[6]).split() if last[6] else []
    if any(identity.MOVE.fullmatch(token.encode('ascii')) is None for token in pv):
        raise ValueError('invalid move token in last PV')
    return {
        'bestmove': decode(best[1]), 'ponder': decode(best[2]) if best[2] else None,
        'depth': int(last[1]), 'seldepth': int(last[2]), 'score_kind': decode(last[3]),
        'score': int(last[4]), 'pv': pv, 'last_info_nodes': last_nodes, 'final_nodes': final_nodes,
        'evals': evals, 'differ': differ, 'details': details, 'shadow_line': decode(lines[-2]),
        'final_line': decode(final_lines[0]), 'last_info': decode(last_info), 'bestmove_line': decode(lines[-1]),
    }


def position_command(start_fen, moves):
    return ' '.join(('position fen', start_fen, 'moves', *moves))


def log_line(stream, row):
    stream.write(json.dumps(row, ensure_ascii=True, separators=(',', ':')) + '\n')
    stream.flush()


def describe_end(board, moves):
    outcome = board.outcome(claim_draw=True)
    return {
        'stop': outcome.termination.name if outcome is not None else 'PLY_CAP',
        'result': outcome.result() if outcome is not None else '*',
        'ply_cap_reached': len(moves) == MOVE_CAP,
        'final_fen': board.fen(),
    }


def run_games(engine, fens, ply_rows, game_rows, totals, progress):
    details_seen = 0
    for pos, start_fen in enumerate(fens, FIRST_POSITION):
        board = chess.Board(start_fen)
        if not board.is_valid():
            raise ValueError(f'invalid W1 root {pos}')
        moves = []
        sums = dict.fromkeys(NUMBERS, 0)
        first_detail = None
        engine.send('ucinewgame')
        if engine.ready() != [b'readyok']:
            raise RuntimeError(f'W1 position {pos}: unexpected reset response')
        while len(moves) < MOVE_CAP and not board.is_game_over(claim_draw=True):
            ply = len(moves) + 1
            command = position_command(start_fen, moves)
            engine.send(command)
            engine.send(f'go softnodes {SOFT_NODES}')
            lines = engine.receive(lambda line: line.startswith(b'bestmove '),
                                   f'bestmove for W1 position {pos}, ply {ply}')
            try:
                result = parse_result(lines, details_seen)
                move = board.parse_uci(result['bestmove'])
                if not move:
                    raise ValueError('null move at a playable root')
            except ValueError as err:
                raise ValueError(f'W1 position {pos}, ply {ply}: {err}') from err
            details_seen += len(result['details'])
            root_fen = board.fen()
            if first_detail is None and result['details']:
                first_detail = {'w1_position': pos, 'ply': ply, 'root_fen': root_fen,
                                'last_played_root_move': moves[-1] if moves else None, **result['details'][0]}
            log_line(ply_rows, {'w1_position': pos, 'ply': ply, 'root_fen': root_fen, **result})
            for key in NUMBERS:
                sums[key] += result[key]
                totals[key] += result[key]
            progress['searches'] += 1
            moves.append(result['bestmove'])
            board.push(move)
        game = {'w1_position': pos, 'start_fen': start_fen, 'plies': len(moves), 'moves': moves,
                **sums, **describe_end(board, moves), 'first_detail': first_detail}
        log_line(game_rows, game)
        progress['games'] += 1
        if progress['first_detail'] is None:
            progress['first_detail'] = first_detail
        print(f'W1 position {pos}: {len(moves)} plies, {sums["evals"]} evals, '
              f'{sums["differ"]} differences, {sums["final_nodes"]} consumed nodes, {game["stop"]}', flush=True)


def run(args):
    if chess.__version__ != CHESS_VERSION:
        raise ValueError(f'expected python-chess module {CHESS_VERSION}; got {chess.__version__}')
    if not 0 < args.timeout <= 120:
        raise ValueError('timeout must be positive and at most 120 seconds')
    engine, net, fixture = (path.resolve(strict=True) for path in (args.engine, args.net, args.fixture))
    if any(char in str(net) for char in '\r\n'):
        raise ValueError('invalid multiline net path')
    if sha(engine) != args.exe_sha256 or sha(net) != identity.NET_SHA or sha(Path(identity.__file__)) != HELPER_SHA:
        raise ValueError('executable, net, or Job19 identity helper SHA-256 mismatch')
    fens = fens_from_fixture(fixture)
    output = args.output
    output.mkdir(parents=True, exist_ok=False)
    stdout_path = output / 'engine.stdout.txt'
    stderr_path = output / 'engine.stderr.txt'
    stdin_path = output / 'engine.commands.txt'
    start = utc()
    error = None
    totals = dict.fromkeys(NUMBERS, 0)
    progress = {'games': 0, 'searches': 0, 'first_detail': None}
    try:
        with (stdout_path.open('xb') as stdout, stderr_path.open('x+b') as stderr,
              stdin_path.open('xb') as stdin, (output / 'plies.jsonl').open('x', encoding='ascii') as ply_rows,
              (output / 'games.jsonl').open('x', encoding='ascii') as game_rows):
            with identity.EngineRun(engine, stdout, stderr, stdin, args.timeout) as process:
                process.set_up(net)
                run_games(process, fens, ply_rows, game_rows, totals, progress)
        identity.check_logs(stdout_path, stderr_path)
    except (OSError, RuntimeError, ValueError) as err:
        error = str(err)
    metadata = {
        'workload': 'S2', 'build': args.build, 'executable': str(engine), 'exe_sha256': args.exe_sha256,
        'net_path': str(net), 'net_sha256': identity.NET_SHA, 'fixture_sha256': FIXTURE_SHA,
        'pc20': identity.PC20, 'python_chess': CHESS_VERSION, 'identity_helper_sha256': HELPER_SHA,
        'runner_sha256': sha(Path(__file__)), 'started_utc': start, 'finished_utc': utc(), 'error': error,
        'soft_nodes': SOFT_NODES, 'hard_node_cap': HARD_NODES, 'ply_cap': MOVE_CAP, 'claim_draw': True,
        'totals': totals, **progress,
        'evals_per_consumed_node': totals['evals'] / totals['final_nodes'] if totals['final_nodes'] else None,
        'files_sha256': {path.name: sha(path) for path in sorted(output.iterdir())},
    }
    summary = json.dumps(metadata, indent=2) + '\n'
    (output / 'summary.json').write_text(summary, encoding='ascii')
    print(summary, end='', flush=True)
    return int(error is not None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    operations = parser.add_subparsers(dest='operation', required=True)
    start = operations.add_parser('run')
    start.add_argument('--build', choices=BUILDS, required=True)
    for option in ('engine', 'net', 'fixture', 'output'):
        start.add_argument('--' + option, type=Path, required=True)
    start.add_argument('--exe-sha256', required=True)
    start.add_argument('--timeout', default=30.0, type=float)
    args = parser.parse_args()
    try:
        return run(args)
    except (OSError, ValueError) as err:
        parser.exit(1, f'{err}\n')


if __name__ == '__main__':
    raise SystemExit(main())

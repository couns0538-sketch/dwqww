"""Independently replay Job 23 raw command and output streams without starting Forge."""

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re

import chess


W1_SHA = '3c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521'
P_SHA = 'e7100aae3c0a8ac1a9966fb8d746ec9511bbd63513ef4ecea99bd38b6255dfae'
NET_SHA = 'c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
ASSERT = re.compile(r'^job23 assert (A[123]) move (\S+)(.*)$', re.MULTILINE)
ASSERT_FEN = re.compile(r'^job23 (?:assert )?fen (.+)$', re.MULTILINE)
BESTMOVE = re.compile(r'bestmove (0000|[a-h][1-8][a-h][1-8][qrbn]?)(?: ponder [a-h][1-8][a-h][1-8][qrbn]?)?')
FINAL = re.compile(r'info string softnodes nodes (\d+)')
PARTS = ('known', 'control', 'r1', 'r2')


def expect(test, message):
    if not test:
        raise ValueError(message)


def sha(path):
    with path.open('rb') as raw:
        return hashlib.file_digest(raw, 'sha256').hexdigest()


def tsv(path):
    with path.open(encoding='utf-8', newline='') as source:
        return list(csv.DictReader(source, delimiter='\t'))


def lines(path):
    return path.read_text(encoding='utf-8').splitlines()


def fixture(sources, part):
    if part == 'known':
        w1 = sources / 'job19/positions.txt'
        expect(sha(w1) == W1_SHA, 'wrong W1 fixture')
        return dict(enumerate(lines(w1)[:200], 1)), W1_SHA
    step1 = sources / 'job23/step1'
    file = step1 / 'positions.tsv'
    expect(sha(file) == P_SHA, 'wrong Step 1 P fixture')
    rows = list(enumerate(tsv(file), 1))
    if part == 'control':
        rows = [(index, row) for index, row in rows if 'D' in row['classes']]
    if part == 'r2':
        rows = sorted(((index, row) for index, row in rows if 'D' in row['classes']),
                      key=lambda entry: (-int(entry[1]['discovered_moves']), entry[1]['fen']))[:10]
        expect([row for _, row in rows] == tsv(step1 / 'top10.tsv'), 'fixture top-ten ranking differs from published table')
    return {index: row['fen'] for index, row in rows}, P_SHA


class Process:
    def __init__(self, path, record, startup):
        self.label = path.name
        self.exit = record['exit']
        expect(self.label == record['process'], 'process directory does not match manifest')
        expect({'commands.txt', 'stderr.txt', 'stdout.txt'} == record['sha256'].keys(), 'incomplete raw process manifest')
        expect(all(sha(path / filename) == digest for filename, digest in record['sha256'].items()),
               f'changed raw process evidence {path}')
        raw_out = lines(path / 'stdout.txt')
        self.commands = iter(lines(path / 'commands.txt'))
        self.output = iter(raw_out)
        self.raw_bestmoves = sum(entry.startswith('bestmove ') for entry in raw_out)
        expect(self.raw_bestmoves == record['bestmoves'], f'{self.label} raw bestmove count differs from manifest')
        raw_err = (path / 'stderr.txt').read_bytes()
        expect(len(raw_err) == record['stderr_bytes'], f'{self.label} stderr byte count differs from manifest')
        self.error_bytes = len(raw_err)
        text = raw_err.decode('utf-8', errors='replace')
        marker = ASSERT.search(text)
        fen = ASSERT_FEN.search(text)
        needle = re.search(r'Assertion .+ failed\.', text)
        self.assert_kind = marker[1] if marker else 'engine' if needle else None
        self.assert_move = marker[2] if marker else None
        self.assert_fen = fen[1] if fen else None
        expect((self.assert_kind, self.assert_move, self.assert_fen) ==
               (record['assert'], record['assert_move'], record['assert_fen']), f'{self.label} assert receipt differs from stderr')
        self.failed = bool(self.assert_kind or record['checker_reports'] or record['error'])
        self.active = record['net_active']
        self.resets = 0
        self.searches = 0
        self.activated = False
        if self.active is None:
            expect(not self.raw_bestmoves, 'startup failed but a bestmove was emitted')
            return
        for command in startup:
            self.expect_command(command)
        ready = self.read_until(lambda line: line == 'readyok')
        activation = [entry for entry in ready if entry.startswith('info string NNUE v3 active: ')]
        expect(ready[-1:] == ['readyok'] and ready.count('uciok') == 1 and len(activation) == 1
               and activation[0] == self.active and 'hidden 768' in self.active
               and 'checksum 30ab43b4ba5db5f3' in self.active and ready.index('uciok') < ready.index(self.active),
               f'{self.label} wrong net activation or setup sequence')
        self.activated = True

    def expect_command(self, wanted):
        got = next(self.commands, None)
        expect(got == wanted, f'{self.label} command {got!r} differs from {wanted!r}')

    def read_until(self, predicate):
        entries = []
        for line in self.output:
            entries.append(line)
            if predicate(line):
                break
        return entries

    def reset(self):
        self.expect_command('ucinewgame')
        self.expect_command('isready')
        expect(next(self.output, None) == 'readyok', f'{self.label} missing reset readyok')
        self.resets += 1

    def search(self, row, root_fen, board, prefix=None):
        self.searches += 1
        expect(row['fen'] == board.fen(), 'derived row has wrong pre-move FEN')
        base = f'position fen {root_fen}'
        if prefix is not None:
            base += ' moves' + ''.join(f' {token}' for token in prefix)
        self.expect_command(base)
        self.expect_command('go depth 9' if prefix is None else 'go softnodes 2000')
        frame = self.read_until(lambda line: line.startswith('bestmove '))
        expect(not any(line == 'readyok' or line == 'uciok' for line in frame), 'lost search-to-ready synchronization')
        if row['status'] != 'bestmove':
            expect(row['status'] in ('interrupted', 'cutoff') and self.failed, 'unexplained incomplete search')
            expect(all(row[name] == '' for name in ('nodes', 'nodes_source', 'depth', 'bestmove', 'last_info_line', 'bestmove_line')),
                   'incomplete search has reported success fields')
            return None, None
        last = next((line for line in reversed(frame) if line.startswith('info depth ')), '')
        expect(frame and (best := BESTMOVE.fullmatch(frame[-1])), f'{self.label} missing/malformed bestmove')
        info_depth = re.match(r'^info depth (\d+) ', last) if last else None
        info_nodes = re.search(r'\bnodes (\d+)\b', last) if last else None
        expect(bool(last) == bool(info_depth) == bool(info_nodes), 'malformed last search info')
        finals = [entry for entry in frame if entry.startswith('info string softnodes nodes ')]
        if prefix is None:
            expect(not finals and info_depth and info_depth[1] == '9', 'fixed depth did not yield a depth-9 label')
            nodes = int(info_nodes[1])
            nodes_source = 'last_info'
        else:
            expect(len(finals) == 1 and (final := FINAL.fullmatch(finals[0])) and frame[-2] == finals[0],
                   'missing or misordered exact consumed-node marker')
            nodes = int(final[1])
            expect(not info_nodes or int(info_nodes[1]) <= nodes, 'consumed total below last-info nodes')
            nodes_source = 'final_softnodes'
        wanted = (str(nodes), nodes_source, info_depth[1] if info_depth else '', best[1], last, frame[-1])
        got = tuple(row[key] for key in ('nodes', 'nodes_source', 'depth', 'bestmove', 'last_info_line', 'bestmove_line'))
        expect(wanted == got, 'derived node/bestmove row differs from raw stdout')
        move = chess.Move.from_uci(best[1])
        expect(move in board.legal_moves or (not move and not any(board.legal_moves)), f'illegal raw bestmove {best[1]}')
        return nodes, move

    def finish(self):
        if not self.activated:
            expect(self.searches == 0, 'failed startup has search attempts')
            return
        pending = list(self.commands)
        tail = list(self.output)
        if self.failed:
            expect(pending in ([], ['quit'], ['stop'], ['stop', 'quit']), 'extra commands after a failed process')
        else:
            expect(pending == ['quit'] and not tail and self.exit == 0, 'clean process did not cleanly quit after its final bestmove')


def validate_control(proc):
    expect(proc.assert_kind == 'A1' and proc.exit != 0 and proc.assert_move and proc.assert_fen,
           'control did not stop in A1 with a move and FEN')
    board = chess.Board(proc.assert_fen)
    move = board.parse_uci(proc.assert_move)
    expect(move and not board.is_capture(move) and move.promotion is None and not board.is_castling(move),
           'control counterexample is not a quiet non-castle move')
    board.push(move)
    checkers = list(board.checkers())
    expect(checkers and move.to_square not in checkers, 'control move is not a pure discovered check')
    return {'assert': proc.assert_kind, 'exit': proc.exit, 'fen': proc.assert_fen, 'move': proc.assert_move,
            'checking_squares': [chess.square_name(square) for square in checkers]}


def audit(raw, sources, part):
    directory = raw / part
    summary_path = directory / 'summary.json'
    if not summary_path.is_file():
        return {'part': part, 'status': 'pending-or-no-final-manifest'}
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    plan, wanted_sha = fixture(sources, part)
    expect(summary['fixture_sha256'] == wanted_sha and summary['net_sha256'] == NET_SHA and summary['part'] == part
           and summary['scheduled_rows'] == list(plan), 'fixture or schedule differs from independent input')
    base = lines(sources / 'job19/W1/kF/engine.commands.txt')
    startup = base[:base.index('ucinewgame')]
    captures = sorted(directory.glob('process-*'))
    records = summary['processes']
    processes = {path.name: Process(path, info, startup) for path, info in zip(captures, records, strict=True)}
    rows = tsv(directory / 'rows.tsv')
    games = tsv(directory / 'games.tsv')
    expect(all(row['search'] == str(i) for i, row in enumerate(rows, 1)), 'reordered search table')
    order = list(dict.fromkeys(row['process'] for row in rows))
    expect(list(processes)[:len(order)] == order, 'unexpected sequence of subprocesses')
    ranks = {name: index for index, name in enumerate(processes)}
    sequence = [ranks[row['process']] for row in rows]
    expect(sequence == sorted(sequence), 'capture reused a process after opening its replacement')
    expect(all(proc.failed for proc in list(processes.values())[:-1]), 'a process was replaced without a failure')
    if part in ('known', 'control'):
        expect(len(captures) == 1, 'known/control used multiple engine processes')
    nodes = 0
    completed = 0
    game_outcomes = Counter()
    baseline = tsv(sources / 'job22/clean/AU-kF-d9/rows.tsv') if part == 'known' else []
    differences = []
    if part != 'r2':
        expect(not games and [int(row['row']) for row in rows] == list(plan)[:len(rows)], 'fixed fixture attempt order mismatch')
        for row in rows:
            index = int(row['row'])
            expect(row['ply'] == '', 'unexpected game ply on a depth-only run')
            proc = processes[row['process']]
            proc.reset()
            count, move = proc.search(row, plan[index], chess.Board(plan[index]))
            if count is None:
                continue
            nodes += count
            completed += 1
            if part == 'known':
                want = baseline[index - 1]
                expect(want['w1_position'] == row['row'] and want['fen'] == row['fen'], 'bad Job 22 baseline reference row')
                if (want['nodes'], want['bestmove']) != (str(count), move.uci()):
                    differences.append({'row': index, 'reference': [want['nodes'], want['bestmove']], 'replay': [count, move.uci()]})
    else:
        grouped = {}
        for row in rows:
            grouped.setdefault(int(row['row']), []).append(row)
        expect(list(grouped) == list(plan)[:len(grouped)], 'R2 game-start order differs from ranked D fixture')
        expect([int(game['row']) for game in games] == list(plan)[:len(games)], 'R2 game summary order differs from ranked D fixture')
        finished_games = {int(game['row']): game for game in games}
        for index, path in grouped.items():
            proc = processes[path[0]['process']]
            proc.reset()
            board = chess.Board(plan[index])
            prefix = []
            used = 0
            interrupted = False
            for ply, row in enumerate(path, 1):
                expect(row['process'] == proc.label and row['ply'] == str(ply) and not interrupted
                       and ply <= 200 and not board.is_game_over(claim_draw=True), 'invalid R2 replay sequence')
                count, move = proc.search(row, plan[index], board, prefix)
                if count is None:
                    interrupted = True
                    continue
                expect(move in board.legal_moves, 'illegal R2 bestmove')
                prefix.append(move.uci())
                board.push(move)
                used += count
                completed += 1
            nodes += used
            if index not in finished_games:
                expect(summary['error'] is not None and index == next(reversed(grouped)), 'missing completed R2 game row')
                continue
            outcome = board.outcome(claim_draw=True)
            if interrupted:
                termination = 'FINDING'
            else:
                expect(outcome is not None or len(prefix) == 200, 'game stopped before a valid endpoint')
                termination = outcome.termination.name if outcome else 'PLY_CAP'
            want = {'row': str(index), 'plies': str(len(prefix)), 'nodes': str(used), 'termination': termination,
                    'result': outcome.result() if outcome else '*', 'moves': ' '.join(prefix)}
            expect(want == finished_games[index], 'game summary differs from exact raw move replay')
            game_outcomes[termination] += 1
    for proc in processes.values():
        proc.finish()
    assert_stops = sum(bool(proc.assert_kind) for proc in processes.values())
    raw_bestmoves = sum(proc.raw_bestmoves for proc in processes.values())
    expect((len(rows), completed, nodes, assert_stops, raw_bestmoves) ==
           (summary['searches'], summary['completed_searches'], summary['reported_nodes'], summary['assert_stops'],
            summary['bestmoves']), 'independent raw totals differ from manifest')
    expect(summary['completed_games'] == sum(game_outcomes.values()) - game_outcomes['FINDING'], 'game totals mismatch')
    if part == 'known':
        expect((len(rows), completed, nodes, differences) == (200, 200, 4_097_080, []), 'known answer does not match Job 22')
    if part == 'r1' and summary['error'] is None:
        expect(len(rows) == len(plan), 'R1 omitted scheduled fixture rows')
    if part == 'r2' and summary['error'] is None:
        expect(len(games) == len(plan), 'R2 omitted scheduled games')
    control = None
    if part == 'control':
        failing = [proc for proc in processes.values() if proc.assert_kind]
        expect(len(failing) == 1 and rows[-1]['status'] == 'interrupted' and rows[-1]['process'] == failing[0].label,
               'control did not stop on its first A1 assertion')
        control = validate_control(failing[0])
    return {'part': part, 'status': 'verified' if summary['error'] is None else 'verified-prefix-with-run-error',
            'attempts': len(rows), 'bestmoves': raw_bestmoves, 'completed': completed, 'nodes': nodes,
            'resets': sum(proc.resets for proc in processes.values()), 'engine_exits': [proc.exit for proc in processes.values()],
            'stderr_bytes': sum(proc.error_bytes for proc in processes.values()), 'assert_stops': assert_stops,
            'control_evidence': control, 'game_outcomes': dict(game_outcomes), 'error': summary['error']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', required=True, type=Path)
    parser.add_argument('--sol3', required=True, type=Path)
    parser.add_argument('parts', choices=PARTS, nargs='+')
    args = parser.parse_args()
    expect(chess.__version__ == '1.11.2', 'wrong python-chess version')
    print(json.dumps([audit(args.raw, args.sol3, part) for part in args.parts], indent=2))

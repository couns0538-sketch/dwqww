#!/usr/bin/env python3
"""Replay raw Job24 UCI captures and compare both known answers independently."""

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re

import chess


PARTS = ('known', 'r1', 'wrong2', 'new-blind', 'old-blind', 'r2')
BLIND = ('new-blind', 'old-blind')
W1_SHA = '3c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521'
P_SHA = 'e7100aae3c0a8ac1a9966fb8d746ec9511bbd63513ef4ecea99bd38b6255dfae'
NET_SHA = 'c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
BEST = re.compile(r'bestmove (0000|[a-h][1-8][a-h][1-8][qrbn]?)(?: ponder [a-h][1-8][a-h][1-8][qrbn]?)?')
ASSERT = re.compile(r'^job2[34] assert (A1s|A2s|A[12347]) move (\S+)(.*)$', re.MULTILINE)
FEN = re.compile(r'^job2[34] (?:assert )?fen (.+)$', re.MULTILINE)


def check(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def lines(path):
    return path.read_text(encoding='utf-8').splitlines()


def tsv(path):
    with path.open(encoding='utf-8', newline='') as source:
        return list(csv.DictReader(source, delimiter='\t'))


def schedule(part, sol3):
    if part == 'known':
        fixture = sol3 / 'job19/positions.txt'
        check(sha(fixture) == W1_SHA, 'wrong W1')
        return dict(enumerate(lines(fixture)[:200], 1)), W1_SHA
    fixture = sol3 / 'job23/step1/positions.tsv'
    check(sha(fixture) == P_SHA, 'wrong P')
    rows = list(enumerate(tsv(fixture), 1))
    if part == 'wrong2':
        rows = rows[:1]
        check(rows[0][1]['classes'] == 'DQ', 'wrong A-wrong2 root')
    if part in BLIND:
        rows = [(index, entry) for index, entry in rows if 'X' in entry['classes']][:20]
    if part == 'r2':
        rows = sorted(((index, entry) for index, entry in rows if set(entry['classes']) & {'P', 'X'}),
                      key=lambda entry: (-sum(letter.isalpha() for letter in entry[1]['fen'].split()[0]),
                                         entry[1]['fen']))[:20]
    return {index: row['fen'] for index, row in rows}, P_SHA


class Capture:
    def __init__(self, directory, record, startup):
        self.record = record
        self.name = directory.name
        self.exited = record['exit']
        check(self.name == record['process'], 'process receipt order mismatch')
        check(record['sha256'].keys() == {'commands.txt', 'stdout.txt', 'stderr.txt'} and
              all(sha(directory / name) == checksum for name, checksum in record['sha256'].items()),
              f'missing or changed raw process evidence in {directory}')
        raw = lines(directory / 'stdout.txt')
        command_lines = lines(directory / 'commands.txt')
        self.raw_count = sum(line.startswith('bestmove ') for line in raw)
        self.raw_go = sum(line.startswith('go ') for line in command_lines)
        self.commands = iter(command_lines)
        self.stdout = iter(raw)
        stderr = (directory / 'stderr.txt').read_bytes()
        self.err_bytes = len(stderr)
        error = stderr.decode('utf-8', errors='replace')
        marker = ASSERT.search(error)
        fen = FEN.search(error, marker.end() if marker else 0)
        self.assertion = marker[1] if marker else 'engine' if re.search(r'Assertion .+ failed\.', error) else None
        self.assert_move = marker[2] if marker else None
        self.assert_fen = fen[1] if fen else None
        self.assert_detail = marker[3].strip() if marker else None
        check((self.raw_count, self.err_bytes, self.assertion, self.assert_move, self.assert_fen, self.assert_detail) ==
              (record['bestmoves'], record['stderr_bytes'], record['assert'], record['assert_move'], record['assert_fen'],
               record['assert_detail']), f'{self.name} process receipt differs from raw')
        self.activation = record['net_active']
        self.resets = 0
        if self.activation:
            for command in startup:
                self.command(command)
            acknowledgement = self.output_until(lambda line: line == 'readyok')
            active = [line for line in acknowledgement if line.startswith('info string NNUE v3 active: ')]
            check(acknowledgement[-1:] == ['readyok'] and acknowledgement.count('uciok') == 1
                  and active == [self.activation] and 'hidden 768' in self.activation
                  and 'checksum 30ab43b4ba5db5f3' in self.activation
                  and acknowledgement.index('uciok') < acknowledgement.index(self.activation), 'net start proof mismatch')
        else:
            check(command_lines == startup[:len(command_lines)] or command_lines[-1:] == ['quit'],
                  'startup failed after an unexpected command sequence')
            check(self.raw_go == self.raw_count == 0, 'unexpected search data before activation')

    def command(self, wanted):
        observed = next(self.commands, None)
        check(wanted == observed, f'{self.name} expected {wanted!r}, observed {observed!r}')

    def output_until(self, finished):
        output = []
        for line in self.stdout:
            output.append(line)
            if finished(line):
                break
        return output

    def reset(self):
        self.command('ucinewgame')
        self.command('isready')
        check(next(self.stdout, None) == 'readyok', 'newgame was not isolated by readyok')
        self.resets += 1

    def search(self, row, board, command, go, reset):
        check(row['fen'] == board.fen() and row['go'] == go and row['search_sent'] in ('0', '1'), 'declared root/limit mismatch')
        if row['search_sent'] == '0':
            check(row['status'] != 'bestmove' and not self.raw_go, 'unsent search has contradictory raw evidence')
            return None, None
        if reset:
            self.reset()
        self.command(command)
        self.command(go)
        frame = self.output_until(lambda line: line.startswith('bestmove '))
        check(not any(line in ('uciok', 'readyok') for line in frame), 'protocol marker inside search output')
        best = BEST.fullmatch(frame[-1]) if frame else None
        last = next((line for line in reversed(frame) if line.startswith('info depth ')), '')
        info = re.match(r'info depth (\d+)\b.*\bnodes (\d+)\b', last) if last else None
        finals = [line for line in frame if line.startswith('info string softnodes nodes')]
        final = re.fullmatch(r'info string softnodes nodes (\d+)', finals[0]) if len(finals) == 1 else None
        move = chess.Move.from_uci(best[1]) if best else None
        legal = best and (move in board.legal_moves or (not move and not any(board.legal_moves)))
        has_label = row['bestmove'] != ''
        if has_label:
            check(row['bestmove'] == best[1] and row['last_info_line'] == last and row['bestmove_line'] == frame[-1],
                  'parsed bestmove/last-info labels differ from raw output')
            check(row['depth'] == (info[1] if info else ''), 'wrong depth field')
            if go == 'go softnodes 2000':
                check(final and frame[-2] == finals[0] and (not info or int(final[1]) >= int(info[2])),
                      'missing/misordered exact final consumed nodes')
                expected_nodes, source = final[1], 'final_softnodes'
            elif info:
                check(not finals, 'unexpected softnodes marker on a fixed-depth run')
                expected_nodes, source = info[2], 'last_info'
            else:
                expected_nodes, source = '', 'no_node_info'
            check((row['nodes'], row['nodes_source']) == (expected_nodes, source), 'node label/source differs from raw')
        else:
            check(row['nodes'] == '', 'node labels exist without a parsed bestmove')
        if row['status'] == 'bestmove':
            check(has_label and legal, 'claimed successful bestmove is illegal or absent')
            if go == 'go depth 9':
                check(info and info[1] == '9', 'fixed search final depth differs from depth 9')
            if go == 'go depth 4' and info:
                check(1 <= int(info[1]) <= 4, 'invalid final depth for a depth-4 blind search')
        elif row['status'] == 'illegal_bestmove':
            check(has_label and best and not legal, 'illegal-bestmove classification disagrees with legal generator')
        elif row['status'] == 'assert_stop':
            check(self.assertion and self.exited != 0, 'assert status has no assert evidence/nonzero exit')
        elif row['status'] == 'native_exit_before_bestmove':
            check(not best and self.exited not in (None, 0), 'native-exit classification disagrees with raw/exit')
        elif row['status'] == 'native_exit_after_bestmove':
            check(has_label and self.exited not in (None, 0), 'post-bestmove exit status disagrees with raw/exit')
        elif row['status'] == 'unusable_bestmove_label':
            check(bool(frame) and frame[-1].startswith('bestmove ') and not has_label, 'missing unusable bestmove raw line')
        elif row['status'] == 'checker_report':
            check(self.record['checker_reports'] > 0, 'checker classification lacks report evidence')
        elif row['status'] == 'sanitizer_runtime_failure':
            check(self.record['runtime_failure_blocks'] > 0, 'runtime classification lacks report evidence')
        elif row['status'] not in ('cutoff', 'reset_failure', 'startup_failure', 'protocol_failure_before_bestmove', 'shutdown_failure'):
            raise ValueError(f"unknown search status {row['status']!r}")
        return int(row['nodes']) if row['nodes'] else None, move if row['status'] == 'bestmove' else None

    def finish(self):
        pending_commands = list(self.commands)
        pending_stdout = list(self.stdout)
        if self.activation and not (self.record['error'] or self.assertion or self.record['checker_reports'] or self.exited):
            check(pending_commands == ['quit'] and not pending_stdout, f'unexpected trailing traffic in {self.name}')


def compare_known(part, sol3, rows, summary):
    if part == 'known':
        reference = sol3 / 'job22/clean/AU-kF-d9/rows.tsv'
        idx = 'w1_position'
        expected = (200, 4_097_080)
    else:
        reference = sol3 / 'job23/step3/r1/rows.tsv'
        idx = 'row'
        expected = (2000, 35_709_215)
    baseline = tsv(reference)
    wanted = [(row[idx], row['fen'], row['nodes'], row['bestmove']) for row in baseline]
    actual = [(row['row'], row['fen'], row['nodes'], row['bestmove']) for row in rows]
    if actual != wanted:
        first = next(((a, b) for a, b in zip(actual, wanted) if a != b), None)
        raise ValueError(f'known-answer mismatch, rows {len(actual)}/{len(wanted)}, first differing raw label {first}')
    check((len(rows), sum(int(row['nodes']) for row in rows)) == expected and summary['error'] is None
          and not any(summary[key] for key in ('assert_stops', 'checker_reports', 'runtime_failures')),
          'known-answer gate failed on counts, native exits or diagnostics')
    return {'rows_matched': len(rows), 'reference_sha256': sha(reference)}


def replay_pin_field(row):
    board = chess.Board(row['assert_fen'])
    mover = board.turn
    king = board.king(mover)
    check(board.is_valid() and king is not None, 'invalid assertion FEN')
    pinned = [square for square in chess.SQUARES if board.color_at(square) == mover and board.is_pinned(mover, square)]
    pins = sum(1 << square for square in pinned)
    readout = re.fullmatch(r'field pinned fast (\d+) ref (\d+)', row['assert_detail'])
    check(readout and [int(value) for value in readout.groups()] == [0, pins] and pins,
          'field mismatch did not name the independently computed pin')
    details = {}
    for square in pinned:
        copy = board.copy(stack=False)
        copy.remove_piece_at(square)
        revealed = copy.attackers(not mover, king) - board.attackers(not mover, king)
        details[chess.square_name(square)] = [chess.square_name(attacker) for attacker in revealed]
    move = chess.Move.from_uci(row['assert_move'])
    return {'king': chess.square_name(king), 'checkers': [chess.square_name(sq) for sq in board.checkers()],
            'unmade_move_legal_at_restored_fen': move in board.legal_moves, 'pin_mask': pins, 'pinned_by': details}


def audit(raw, sol3, part):
    directory = raw / part
    summary_path = directory / 'summary.json'
    if not summary_path.is_file():
        return {'part': part, 'status': 'no-final-manifest' if directory.exists() else 'no-capture'}
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    expected, fixture_sha = schedule(part, sol3)
    check(summary['part'] == part and summary['fixture_sha256'] == fixture_sha and summary['net_sha256'] == NET_SHA
          and summary['scheduled_rows'] == list(expected), 'fixture, net, or schedule does not match the pinned run')
    baseline = lines(sol3 / 'job19/W1/kF/engine.commands.txt')
    startup = baseline[:baseline.index('ucinewgame')]
    processes = {p.name: Capture(p, rec, startup) for p, rec in zip(sorted(directory.glob('process-*')),
                                                                   summary['processes'], strict=True)}
    rows = tsv(directory / 'rows.tsv')
    games = tsv(directory / 'games.tsv')
    check([int(row['search']) for row in rows] == list(range(1, len(rows) + 1)), 'out-of-order search rows')
    ranks = {label: rank for rank, label in enumerate(processes)}
    order = [ranks[row['process']] for row in rows]
    check(order == sorted(order), 'a closed UCI session was reused')
    statuses = Counter(row['status'] for row in rows)
    nodes = 0
    outcomes = Counter()
    if part != 'r2':
        check(not games and [int(row['row']) for row in rows] == list(expected)[:len(rows)], 'fixed-depth FEN order changed')
        for row in rows:
            root = expected[int(row['row'])]
            check(row['ply'] == '', 'unexpected game ply for fixed fixture')
            used, _ = processes[row['process']].search(row, chess.Board(root), f'position fen {root}',
                                                       'go depth 4' if part in BLIND else 'go depth 9', True)
            nodes += used or 0
    else:
        by_start = {}
        for row in rows:
            by_start.setdefault(int(row['row']), []).append(row)
        check(list(by_start) == list(expected)[:len(by_start)], 'game starts not in piece-count/FEN rank order')
        check([int(game['row']) for game in games] == list(expected)[:len(games)], 'game summary rank order changed')
        game_summaries = {int(row['row']): row for row in games}
        for index, entries in by_start.items():
            root = expected[index]
            board = chess.Board(root)
            process = processes[entries[0]['process']]
            prefix = []
            game_nodes = 0
            failed = False
            for ply, row in enumerate(entries, 1):
                check(row['ply'] == str(ply) and row['process'] == process.name and not failed
                      and ply <= 200 and not board.is_game_over(claim_draw=True), 'illegal or prematurely stopped game sequence')
                command = ' '.join(('position fen', root, 'moves', *prefix))
                used, move = process.search(row, board, command, 'go softnodes 2000', reset=ply == 1)
                nodes += used or 0
                if move is None:
                    failed = True
                    continue
                check(move in board.legal_moves and used is not None, 'illegal game move or missing node total')
                game_nodes += used
                prefix.append(move.uci())
                board.push(move)
            if index not in game_summaries:
                check(summary['error'] and index == next(reversed(by_start)), 'missing game receipt')
                continue
            outcome = board.outcome(claim_draw=True)
            check(failed or outcome is not None or len(prefix) == 200, 'game ended before rules allowed it')
            ending = 'FINDING' if failed else outcome.termination.name if outcome else 'PLY_CAP'
            game = {'row': str(index), 'plies': str(len(prefix)), 'nodes': str(game_nodes), 'termination': ending,
                    'result': outcome.result() if outcome else '*', 'moves': ' '.join(prefix)}
            check(game == game_summaries[index], 'game receipt disagrees with raw replay')
            outcomes[ending] += 1
        if summary['error'] is None:
            check(len(games) == 20, 'R2 omitted games')
    for process in processes.values():
        process.finish()
    assert_stops = sum(bool(p.assertion) for p in processes.values())
    bestmoves = sum(p.raw_count for p in processes.values())
    sent = sum(int(row['search_sent']) for row in rows)
    check((len(rows), sent, bestmoves, statuses['bestmove'], nodes, assert_stops, statuses) ==
          (summary['trials'], summary['searches'], summary['bestmoves'], summary['completed_searches'],
           summary['reported_nodes'], summary['assert_stops'], summary['statuses']), 'manifest counters disagree with raw replay')
    check(summary['completed_games'] == sum(outcomes.values()) - outcomes['FINDING'], 'wrong completed-game count')

    gate = None
    audit_status = 'verified' if summary['error'] is None else 'verified-prefix-with-run-error'
    if part in ('known', 'r1'):
        check(len(processes) == 1 and next(iter(processes.values())).exited == 0, 'known-answer run used bad process')
        gate = compare_known(part, sol3, rows, summary)
    if part == 'wrong2':
        check(len(rows) == len(processes) == 1 and statuses['assert_stop'] == 1, 'A-wrong2 failed to catch P row one')
        process = next(iter(processes.values()))
        check(process.assertion == 'A1s' and process.assert_fen and process.assert_move, 'missing A-wrong2 A1s evidence')
        board = chess.Board(process.assert_fen)
        move = board.parse_uci(process.assert_move)
        board.push(move)
        check(board.is_check() and not (board.checkers_mask() & chess.BB_SQUARES[move.to_square]),
              'A-wrong2 trigger is not a pure discovered check')
        gate = {'row': int(rows[0]['row']), 'assert': process.assertion, 'move': process.assert_move,
                'fen': process.assert_fen, 'checking_squares': [chess.square_name(square) for square in board.checkers()]}
    if part in BLIND:
        table = tsv(directory / 'blind.tsv')
        stopped_at_required_gate = (part == 'new-blind' and len(rows) == 1 and summary['error'] is not None
                                    and 'first new-blind position missed required A2s/A4 stop' in summary['error'])
        wanted_trials = 1 if stopped_at_required_gate else 20
        check((len(rows), len(table), len(processes)) == (wanted_trials,) * 3, 'blind trial or fresh process count differs')
        for rank, (row, outcome) in enumerate(zip(rows, table, strict=True), 1):
            process = processes[row['process']]
            expected_outcome = {key: row[key] for key in ('row', 'fen', 'process', 'status', 'search_sent', 'nodes', 'bestmove', 'error')}
            expected_outcome.update(rank=str(rank), exit=str(process.exited) if process.exited is not None else '',
                                    raw_bestmoves=str(process.raw_count),
                                    checker_reports=str(process.record['checker_reports']),
                                    runtime_failures=str(process.record['runtime_failure_blocks']))
            for key in ('assert', 'assert_move', 'assert_fen', 'assert_detail'):
                expected_outcome[key] = str(process.record[key]) if process.record[key] is not None else ''
            check(outcome == expected_outcome and ranks[row['process']] == rank - 1 and process.raw_go == int(row['search_sent']),
                  'blind positional receipt or fresh-process guarantee differs from raw')
        first = table[0]
        if part == 'new-blind':
            gate = {key: first[key] for key in ('row', 'assert', 'assert_move', 'assert_fen', 'assert_detail', 'exit')}
            root = chess.Board(first['fen'])
            gate['root_fen'] = first['fen']
            gate['root_checkers'] = [chess.square_name(square) for square in root.checkers()]
            gate['required_on_first_x'] = ['A2s', 'A4']
            gate['meets_required_first_x_stop'] = (first['status'] == 'assert_stop' and first['assert'] in ('A2s', 'A4')
                                                   and first['search_sent'] == '1')
            check(gate['meets_required_first_x_stop'] != stopped_at_required_gate, 'first-X stop classification disagrees with raw')
            if stopped_at_required_gate:
                audit_status = 'verified-required-gate-failure'
                if first['assert'] == 'A7':
                    gate['independent_geometry'] = replay_pin_field(first)
    return {'part': part, 'status': audit_status,
            'trials': len(rows), 'searches': sent, 'bestmoves': bestmoves, 'nodes': nodes,
            'resets': sum(p.resets for p in processes.values()), 'exits': [p.exited for p in processes.values()],
            'assert_stops': assert_stops, 'stderr_bytes': sum(p.err_bytes for p in processes.values()),
            'search_statuses': dict(statuses), 'game_endings': dict(outcomes), 'gate': gate,
            'error': summary['error']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', required=True, type=Path)
    parser.add_argument('--sol3', required=True, type=Path)
    parser.add_argument('parts', choices=PARTS, nargs='+')
    args = parser.parse_args()
    check(chess.__version__ == '1.11.2', 'wrong python-chess build')
    print(json.dumps([audit(args.raw, args.sol3, part) for part in args.parts], indent=2))

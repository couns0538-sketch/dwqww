"""Independent executable fixtures; the chess package is an external oracle."""
import json
import os
from pathlib import Path
import random
import subprocess
import ctypes
import msvcrt
import time
import unittest

import chess

ROOT = Path(__file__).resolve().parents[2]
EXE = Path(os.environ.get('R14_NATIVE_EXE', ROOT / 'tools/r14_native/build/chain_native.exe'))


def run_lines(lines, mode='--pairs'):
    child_env = dict(os.environ, CUDA_VISIBLE_DEVICES='-1', HIP_VISIBLE_DEVICES='-1',
                     OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    reply = subprocess.run([str(EXE), mode], input='\n'.join(lines) + '\n',
                           capture_output=True, text=True, check=True, env=child_env,
                           timeout=30)
    return [json.loads(line) for line in reply.stdout.splitlines()]


def pair(a, b, result_a='0.5', result_b='0.5', cap=100000, k=8, ident='pair'):
    return '\t'.join((ident, a, result_a, b, result_b, str(k), str(cap)))


def witness_end(fen, moves):
    board = chess.Board(fen)
    for token in moves:
        move = chess.Move.from_uci(token)
        if move not in board.legal_moves:
            raise AssertionError(f'illegal witness {token} at {board.fen()}')
        board.push(move)
    return board.fen(en_passant='fen')


class NativeFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not EXE.is_file():
            raise AssertionError(f'candidate executable missing: {EXE}')

    def assert_moves(self, board):
        fen = board.fen(en_passant='fen')
        result = run_lines(['moves\t' + fen], '--moves')[0]
        self.assertEqual(result['status'], 'OK', result)
        expected = {}
        for move in board.legal_moves:
            child = board.copy()
            child.push(move)
            expected[move.uci()] = child.fen(en_passant='fen')
        actual = {move['uci']: move['fen'] for move in result['moves']}
        self.assertEqual(len(actual), len(result['moves']))
        self.assertEqual(actual, expected, fen)
        self.assertEqual(list(actual), sorted(actual))

    def test_start_successors(self):
        self.assert_moves(chess.Board())

    def test_special_successors(self):
        fens = [
            'r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1',
            '4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2',
            'k3r3/8/8/3pP3/8/8/8/4K3 w - d6 0 2',
            '4k3/P7/8/8/8/8/7p/4K3 w - - 0 10',
            '1r2k3/P7/8/8/8/8/7p/4K3 w - - 0 10',
            '4k3/8/8/8/8/8/4r3/4K3 w - - 4 15',
            'r3k2r/8/8/8/8/8/7q/R3K2R b KQkq - 0 15',
            'r3k2r/8/8/8/8/5r2/8/R3K2R w KQkq - 0 15',
            '7k/6Q1/6K1/8/8/8/8/8 b - - 0 20',
            '7k/5Q2/6K1/8/8/8/8/8 b - - 0 20',
        ]
        for fen in fens:
            with self.subTest(fen=fen):
                self.assert_moves(chess.Board(fen))

    def test_seeded_random_successors(self):
        rng = random.Random(140031)
        board = chess.Board()
        boards = []
        for _ in range(300):
            if board.is_game_over() or board.ply() > 180:
                board = chess.Board()
            board.push(rng.choice(list(board.legal_moves)))
            boards.append(board.copy())
        lines = [f'{i}\t{b.fen(en_passant="fen")}' for i, b in enumerate(boards)]
        results = run_lines(lines, '--moves')
        self.assertEqual(len(results), len(boards))
        for board, result in zip(boards, results):
            expected = {}
            for move in board.legal_moves:
                child = board.copy()
                child.push(move)
                expected[move.uci()] = child.fen(en_passant='fen')
            self.assertEqual(result['status'], 'OK')
            self.assertEqual({m['uci']: m['fen'] for m in result['moves']}, expected,
                             board.fen(en_passant='fen'))

    def test_reachable_depths_one_through_eight(self):
        board = chess.Board()
        start = board.fen(en_passant='fen')
        lines, targets = [], []
        for token in ['e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1c4', 'g8f6', 'd2d3', 'f8c5']:
            board.push_uci(token)
            target = board.fen(en_passant='fen')
            targets.append(target)
            lines.append(pair(start, target, cap=1000000, ident=f'depth-{len(lines) + 1}'))
        results = run_lines(lines)
        self.assertEqual(len(results), len(targets))
        self.assertEqual([result['id'] for result in results], [f'depth-{i}' for i in range(1, len(targets) + 1)])
        for depth, (result, target) in enumerate(zip(results, targets), 1):
            with self.subTest(depth=depth):
                self.assertEqual(result['status'], 'REACHABLE', result)
                self.assertEqual(len(result['witness']), depth)
                self.assertEqual(witness_end(start, result['witness']), target)

    def test_one_ply_special_witnesses(self):
        cases = [
            ('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1', 'e1g1'),
            ('r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1', 'e8c8'),
            ('4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2', 'e5d6'),
            ('4k3/P7/8/8/8/8/7p/4K3 w - - 0 10', 'a7a8n'),
            ('1r2k3/P7/8/8/8/8/7p/4K3 w - - 0 10', 'a7b8q'),
        ]
        for fen, token in cases:
            target = witness_end(fen, [token])
            result = run_lines([pair(fen, target)])[0]
            self.assertEqual(result['status'], 'REACHABLE', result)
            self.assertEqual(witness_end(fen, result['witness']), target)

    def test_result_mismatch(self):
        board = chess.Board()
        start = board.fen(en_passant='fen')
        board.push_uci('e2e4')
        result = run_lines([pair(start, board.fen(en_passant='fen'), '1.0', '0.0')])[0]
        self.assertEqual(result['status'], 'UNREACHABLE')
        self.assertEqual(result['reason'], 'result_mismatch')

    def test_equal_or_backwards_ply(self):
        a = chess.Board().fen(en_passant='fen')
        b = witness_end(a, ['g1f3'])
        for line in [pair(a, a), pair(b, a)]:
            self.assertEqual(run_lines([line])[0]['status'], 'UNREACHABLE')

    def test_gap_beyond_k_is_unknown(self):
        a = chess.Board().fen(en_passant='fen')
        b = witness_end(a, ['e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1c4', 'g8f6', 'd2d3', 'f8c5', 'b1c3'])
        result = run_lines([pair(a, b)])[0]
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(result['reason'], 'gap_exceeds_k')

    def test_budget_exhaustion_is_unknown(self):
        a = chess.Board().fen(en_passant='fen')
        b = witness_end(a, ['g1f3', 'g8f6'])
        result = run_lines([pair(a, b, cap=1)])[0]
        self.assertEqual(result['status'], 'UNKNOWN', result)
        self.assertEqual(result['reason'], 'node_limit')
        self.assertLessEqual(result['nodes'], 1)

    def test_raw_ep_and_halfmove_mismatch(self):
        a = chess.Board().fen(en_passant='fen')
        b = witness_end(a, ['e2e4'])
        for corrupted in [b.replace(' e3 ', ' - '), b.replace(' 0 1', ' 2 1')]:
            result = run_lines([pair(a, corrupted)])[0]
            self.assertEqual(result['status'], 'UNREACHABLE', result)

    def test_bad_input_fails_closed(self):
        a = chess.Board().fen(en_passant='fen')
        cases = ['broken', pair('not a fen', a), pair(a, a, result_a='?'),
                 pair(a, a, cap=0), pair(a, a, k=0)]
        for result in run_lines(cases):
            self.assertEqual(result['status'], 'UNKNOWN', result)
            self.assertEqual(result['reason'], 'invalid_input')

    def test_json_identifier_escaping(self):
        a = chess.Board().fen(en_passant='fen')
        ident = 'quote"slash\\'
        result = run_lines([pair(a, witness_end(a, ['e2e4']), ident=ident)])[0]
        self.assertEqual(result['id'], ident)

    def test_interactive_reply_before_eof(self):
        a = chess.Board().fen(en_passant='fen')
        line = pair(a, witness_end(a, ['e2e4']))
        process = subprocess.Popen([str(EXE), '--pairs'], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   env=dict(os.environ, CUDA_VISIBLE_DEVICES='-1', HIP_VISIBLE_DEVICES='-1'))
        try:
            process.stdin.write(line + '\n')
            process.stdin.flush()
            handle = ctypes.c_void_p(msvcrt.get_osfhandle(process.stdout.fileno()))
            available = ctypes.c_ulong()
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                ok = ctypes.windll.kernel32.PeekNamedPipe(handle, None, 0, None, ctypes.byref(available), None)
                self.assertTrue(ok, 'cannot inspect owned output pipe')
                if available.value:
                    break
                time.sleep(0.01)
            self.assertGreater(available.value, 0, 'line protocol did not reply before input EOF')
            reply = process.stdout.readline()
            self.assertEqual(json.loads(reply)['status'], 'REACHABLE')
        finally:
            process.stdin.close()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            process.stdout.close()
            process.stderr.close()

    def test_two_ply_exhaustive_reference(self):
        start = chess.Board('4k3/8/8/3pP3/8/8/8/R3K2R w KQ d6 0 2')
        states = set()
        for first in start.legal_moves:
            middle = start.copy()
            middle.push(first)
            for second in middle.legal_moves:
                target = middle.copy()
                target.push(second)
                states.add(target.fen(en_passant='fen'))
        choices = sorted(states)[::max(1, len(states) // 25)]
        negatives = []
        for target in choices:
            bad = chess.Board(target)
            bad.halfmove_clock += 1
            value = bad.fen(en_passant='fen')
            if value not in states:
                negatives.append(value)
        targets = choices + negatives
        rows = [pair(start.fen(en_passant='fen'), target, ident=f'oracle-{i}') for i, target in enumerate(targets)]
        results = run_lines(rows)
        self.assertEqual(len(results), len(targets))
        self.assertEqual([result['id'] for result in results], [f'oracle-{i}' for i in range(len(targets))])
        for target, result in zip(targets, results):
            self.assertEqual(result['status'], 'REACHABLE' if target in states else 'UNREACHABLE', result)
            if result['status'] == 'REACHABLE':
                self.assertEqual(witness_end(start.fen(en_passant='fen'), result['witness']), target)


if __name__ == '__main__':
    unittest.main(verbosity=2)

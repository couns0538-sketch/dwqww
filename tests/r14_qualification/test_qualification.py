"""Small tests of independent oracle and fail-closed comparison accounting."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock
import math
import io
import json
import time
import tempfile

import chess

SOURCE = Path(__file__).resolve().parents[2] / 'tools/r14_qualification/qualify.py'


class QualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('r14_qualify', SOURCE)
        cls.q = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.q
        spec.loader.exec_module(cls.q)

    def record(self):
        a = chess.Board()
        b = a.copy()
        b.push_uci('e2e4')
        return self.q.Pair('x', a.fen(en_passant='fen'), b.fen(en_passant='fen'),
                           0.5, 0.5, 1, 'one_ply', True, ['e2e4'])

    def test_exact_state_includes_raw_ep_and_clocks(self):
        a = chess.Board()
        a.push_uci('e2e4')
        b = a.copy()
        b.ep_square = None
        self.assertNotEqual(self.q.state(a), self.q.state(b))
        b = a.copy()
        b.halfmove_clock += 1
        self.assertNotEqual(self.q.state(a), self.q.state(b))

    def test_oracle_one_ply_and_exhaustion(self):
        item = self.record()
        self.assertTrue(self.q.oracle_exact(chess.Board(item.start), chess.Board(item.target), 1, 1000))
        b = chess.Board(item.target)
        b.halfmove_clock += 1
        self.assertFalse(self.q.oracle_exact(chess.Board(item.start), b, 1, 1000))
        self.assertIsNone(self.q.oracle_exact(chess.Board(item.start), b, 1, 1))

    def test_unknown_not_resolved(self):
        item = self.record()
        report = self.q.compare(item, dict(id='x', status='UNKNOWN', reason='node_limit', nodes=1, witness=[]), 1000)
        self.assertEqual(report, ('unknown', None))

    def test_invalid_input_reply_on_valid_fixture_is_disagreement(self):
        item = self.record()
        for reason in ('invalid_input', 'gap_exceeds_k'):
            report = self.q.compare(item, dict(id='x', status='UNKNOWN', reason=reason, nodes=0, witness=[]), 1000)
            self.assertEqual(report[0], 'disagree')

    def test_good_witness_agrees(self):
        item = self.record()
        result = dict(id='x', status='REACHABLE', reason='legal_witness', nodes=2, witness=['e2e4'])
        self.assertEqual(self.q.compare(item, result, 1000), ('agree', None))

    def test_false_negative_is_disagreement(self):
        result = dict(id='x', status='UNREACHABLE', reason='exhaustive_no_path', nodes=21, witness=[])
        category, reason = self.q.compare(self.record(), result, 1000)
        self.assertEqual(category, 'disagree')
        self.assertIn('oracle', reason)

    def test_bad_witness_is_disagreement(self):
        result = dict(id='x', status='REACHABLE', reason='legal_witness', nodes=2, witness=['e2e5'])
        self.assertEqual(self.q.compare(self.record(), result, 1000)[0], 'disagree')

    def test_budget_overrun_and_wrong_id_rejected(self):
        for result in [dict(id='x', status='UNKNOWN', reason='node_limit', nodes=1001, witness=[]),
                       dict(id='wrong', status='UNKNOWN', reason='node_limit', nodes=1, witness=[])]:
            self.assertEqual(self.q.compare(self.record(), result, 1000)[0], 'disagree')

    def test_seeded_pairs_reproduce(self):
        a = list(self.q.one_ply_pairs(12, 1401))
        b = list(self.q.one_ply_pairs(12, 1401))
        self.assertEqual(a, b)
        self.assertEqual({item.expected for item in a}, {True, False})

    def test_deep_paths_are_legal_and_exact(self):
        items = list(self.q.deep_pairs(2, 1411))
        self.assertEqual(len(items), 14)
        self.assertEqual({item.depth for item in items}, set(range(2, 9)))
        for item in items:
            b = chess.Board(item.start)
            for token in item.oracle_witness:
                move = chess.Move.from_uci(token)
                self.assertIn(move, b.legal_moves)
                b.push(move)
            self.assertEqual(b.fen(en_passant='fen'), item.target)

    def test_nonfinite_deadlines_refused(self):
        for duration in (float('nan'), float('inf'), -float('inf'), 0, -1):
            with self.assertRaises(ValueError):
                self.q.check_duration(duration)
        self.assertEqual(self.q.check_duration(1.5), 1.5)

    def base_report(self, foundation=1000000, resolved=1000000):
        return dict(status='PASS', complete=True, completed=True, smoke_status='PASS', reasons=[],
                    pairs=dict(resolved=resolved, disagreements=0), moves=dict(disagreements=0),
                    by_stratum=dict(one_ply=dict(resolved=foundation)))

    def test_close_failure_cannot_complete_or_pass_smoke(self):
        report = self.base_report(10, 10)
        self.q.finish_status(report, fixture=True, foundation_requested=10, close_error='bad exit')
        self.assertEqual(report['status'], 'UNVERIFIED')
        self.assertEqual(report['smoke_status'], 'UNVERIFIED')
        self.assertFalse(report['complete'])
        self.assertFalse(self.q.success_exit(report, fixture=True))

    def test_extra_strata_cannot_compensate_missing_foundation(self):
        report = self.base_report(999999, 1000100)
        self.q.finish_status(report, fixture=False, foundation_requested=1000000)
        self.assertEqual(report['status'], 'UNVERIFIED')
        self.assertFalse(self.q.success_exit(report, fixture=False))

    def test_final_resource_refusal_blocks_publication(self):
        report = self.base_report()
        target = mock.Mock()
        with mock.patch.object(self.q, 'resource_guard', side_effect=OSError('disk floor')):
            self.assertFalse(self.q.publish_report(report, target))
        target.write_text.assert_not_called()
        self.assertEqual(report['status'], 'UNVERIFIED')
        self.assertFalse(report['complete'])

    def test_report_close_failure_never_publishes_pass_file(self):
        report = self.base_report()
        original_open = Path.open
        class FailClose:
            def __init__(self, stream):
                self.stream = stream
            def __enter__(self):
                return self.stream
            def __exit__(self, *args):
                self.stream.close()
                raise OSError('simulated close failure after payload write')
        def fail_after_write(path, *args, **kwargs):
            return FailClose(original_open(path, *args, **kwargs))
        with tempfile.TemporaryDirectory(dir=SOURCE.parent) as directory:
            target = Path(directory) / 'REPORT.json'
            with mock.patch.object(self.q, 'resource_guard'), mock.patch.object(Path, 'open', fail_after_write):
                self.assertFalse(self.q.publish_report(report, target))
            self.assertFalse(target.exists())
            self.assertFalse(report['complete'])

    def test_resource_refusal_after_pending_write_leaves_no_final_report(self):
        report = self.base_report()
        with tempfile.TemporaryDirectory(dir=SOURCE.parent) as directory:
            target = Path(directory) / 'REPORT.json'
            with mock.patch.object(self.q, 'resource_guard', side_effect=[None, RuntimeError('disk floor')]):
                self.assertFalse(self.q.publish_report(report, target))
            self.assertFalse(target.exists())
            self.assertFalse(report['complete'])

    def test_closed_pipe_before_process_exit_is_not_inspection_failure(self):
        client = self.transport(b'')
        for error in (109, 232):
            with mock.patch.object(self.q.msvcrt, 'get_osfhandle', return_value=123), \
                 mock.patch.object(self.q.ctypes.windll.kernel32, 'PeekNamedPipe', return_value=0), \
                 mock.patch.object(self.q.ctypes.windll.kernel32, 'GetLastError', return_value=error):
                self.assertEqual(self.q.Native.available(client), 0)

    def test_shared_storage_cap_is_checked(self):
        process = mock.Mock()
        process.memory_info.return_value.rss = 1000
        with mock.patch.object(self.q.psutil, 'Process', return_value=process), \
             mock.patch.object(self.q.psutil, 'virtual_memory') as memory, \
             mock.patch.object(self.q.shutil, 'disk_usage') as disk, \
             mock.patch.object(self.q, 'owned_bytes', return_value=5000000000):
            memory.return_value.available = 16 * 1024**3
            disk.return_value.free = 100 * 1024**3
            with self.assertRaises(OSError):
                self.q.resource_guard()

    def test_storage_accounting_does_not_follow_fixture_junctions(self):
        directories = ['redirect']
        with mock.patch.object(self.q.os, 'walk', return_value=iter([('D:/a14', directories, ['owned'])])), \
             mock.patch.object(Path, 'is_symlink', return_value=False), \
             mock.patch.object(self.q.os.path, 'isjunction', side_effect=lambda path: str(path).endswith('redirect')), \
             mock.patch.object(Path, 'lstat') as link_stat, mock.patch.object(Path, 'stat') as file_stat:
            link_stat.return_value.st_size = 0
            file_stat.return_value.st_size = 11
            self.assertEqual(self.q.owned_bytes(), 11)
            self.assertEqual(directories, [])

    def transport(self, response, exited=False):
        client = self.q.Native.__new__(self.q.Native)
        client.process = mock.Mock()
        client.process.stdin = io.BytesIO()
        client.process.poll.return_value = 0 if exited else None
        client.sent = client.received = 0
        client.deadline = time.monotonic() + 5
        client.buffer = bytearray()
        client.closed = client.aborted = False
        chunks = iter([response])
        client.read_ready = lambda: next(chunks, b'')
        client.available = lambda: 0
        return client

    def test_batch_exact_ids_and_count(self):
        replies = [dict(id='a', status='OK'), dict(id='b', status='OK')]
        client = self.transport(('\n'.join(map(json.dumps, replies)) + '\n').encode())
        self.assertEqual(client.query_many(['a\tfen', 'b\tfen']), replies)
        self.assertEqual((client.sent, client.received), (2, 2))
        self.assertEqual(client.process.stdin.getvalue(), b'a\tfen\nb\tfen\n')

    def test_batch_wrong_or_extra_reply_is_refused(self):
        for payload in (b'{"id":"wrong"}\n', b'{"id":"a"}\n{"id":"extra"}\n'):
            client = self.transport(payload)
            with self.assertRaises(RuntimeError):
                client.query_many(['a\tfen'])

    def test_batch_truncation_is_refused(self):
        client = self.transport(b'{"id":"a"}\n', exited=True)
        with self.assertRaises(RuntimeError):
            client.query_many(['a\tfen', 'b\tfen'])
        self.assertEqual((client.sent, client.received), (2, 1))

    def test_batch_bounds_checked_before_write(self):
        for lines in ([], [f'{i}\tfen' for i in range(9)], ['a\t' + 'x' * 2048],
                      ['a\tfen', 'a\tfen'], ['a\tfen\ninjected']):
            client = self.transport(b'')
            with self.assertRaises(ValueError):
                client.query_many(lines)
            self.assertEqual(client.process.stdin.getvalue(), b'')

    def test_batch_expired_deadline_sends_nothing(self):
        client = self.transport(b'')
        client.deadline = time.monotonic() - 1
        with self.assertRaises(self.q.Deadline):
            client.query_many(['a\tfen'])
        self.assertEqual(client.process.stdin.getvalue(), b'')

    def test_real_native_batch(self):
        candidate = self.q.DEFAULT_CANDIDATE
        self.assertEqual(self.q.hashes(candidate)['sha256'], self.q.DEFAULT_SHA256)
        log = Path('D:/a14/evidence/test_logs/r14/qualification/batch_native.stderr.log')
        client = self.q.Native(candidate, '--pairs', log, time.monotonic() + 10)
        items = list(self.q.one_ply_pairs(8, 14003))
        try:
            replies = client.query_many([item.wire(100000) for item in items])
            self.assertEqual(len(replies), len(items))
            for index in range(len(items)):
                self.assertEqual(self.q.compare(items[index], replies[index], 100000), ('agree', None))
        finally:
            client.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)

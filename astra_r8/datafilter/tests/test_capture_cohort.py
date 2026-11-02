"""Small standalone tests; no engine, training, or production PGN scan."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

BASE = 'base_AL1_s198_ltopgo_x_FD3A5190'
DIGEST = 'FD3A51903E73DC1FA20263F1DCC7A4EEC506592E9F25E50B8F8739CA36873072'


class CaptureCohortTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='capture_fixture_', dir=os.environ['TEMP'])
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        spec = importlib.util.find_spec('audit_capture_cohort')
        self.assertIsNotNone(spec, 'capture cohort freezer has not been implemented')
        import audit_capture_cohort
        self.module = audit_capture_cohort

    def gate(self):
        gate = self.root / 'fixture_gate'
        gate.mkdir()
        info = {'tag': gate.name, 'runner': 'forge_queue.ps1 v3-6day r8d2',
                'base': {'name': BASE, 'sha256': DIGEST, 'options': [],
                         'pins': [312866, 862329, 3024920, 12389307, 34048354]},
                'candidate': {'name': 'cand_fixture'},
                'book': {'key': 'uho_lichess_v1', 'sha256': '0' * 64}}
        (gate / 'RUN_INFO.json').write_text(json.dumps(info), encoding='utf-8')
        (gate / 'RESULT.md').write_text('fastchess exit code 0; attempt 1\n'
                                      'Crashes/disconnects/stalls/illegal: 0\n'
                                      'Time losses: 0\n'
                                      "fastchess 'Warning;' lines: 0\n", encoding='utf-8')
        (gate / (gate.name + '.pgn')).write_text(
            f'[Event "forge_{gate.name}"]\n[White "{BASE}"]\n'
            '[Black "cand_fixture"]\n[Result "1-0"]\n[Termination "adjudication"]\n\n'
            '1. e4 {+0.20/10 0.1s} e5 {-0.30/11 0.1s} '
            '2. Nf3 {book} Nc6 {-0.40/11 0.1s} '
            '3. Bb5 {+0.40/12 0.1s} a6 {-0.40/11 0.1s} 1-0\n\n'
            f'[Event "forge_{gate.name}"]\n[White "cand_fixture"]\n'
            f'[Black "{BASE}"]\n[Result "0-1"]\n[Termination "normal"]\n\n'
            '1. d4 {+0.30/8 0.1s} d5 {-0.12/9 0.1s} 0-1\n', encoding='utf-8')
        return gate

    def test_baseline_only_preserves_score_result_fen_and_source_order(self):
        gate = self.gate()
        out = self.root / 'cohort'
        receipt = self.module.freeze(out, gates=[gate], limit=3, batch_size=1)
        rows = [json.loads(line) for line in (out / 'records.jsonl').read_text().splitlines()]
        self.assertEqual([r['best_move'] for r in rows], ['e2e4', 'f1b5', 'd7d5'])
        self.assertEqual([r['source_row'] for r in rows], ['1:0', '1:4', '2:1'])
        self.assertEqual([r['score_stm'] for r in rows], [20, 40, -12])
        self.assertEqual(rows[-1]['result_white'], -1)
        self.assertEqual(rows[-1]['result_stm'], 1)
        self.assertEqual(rows[-1]['fen'], 'rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1')
        self.assertTrue(all(r['source_kind'] == 'pgn' and r['has_result'] for r in rows))
        self.assertEqual(receipt['count'], 3)
        self.assertEqual(receipt['workers'], 1)
        self.assertTrue(receipt['measurement_only'])
        self.assertEqual(receipt['sources'][0]['files']['pgn']['sha256_before'],
                         receipt['sources'][0]['files']['pgn']['sha256_after'])

    def test_payload_is_deterministic(self):
        gate = self.gate()
        a = self.module.freeze(self.root / 'a', gates=[gate], limit=3, batch_size=1)
        b = self.module.freeze(self.root / 'b', gates=[gate], limit=3, batch_size=2)
        self.assertEqual(a['hashes']['records.jsonl'], b['hashes']['records.jsonl'])

    def test_incorrect_lock_is_rejected_before_allocation(self):
        gate = self.gate()
        info = json.loads((gate / 'RUN_INFO.json').read_text())
        info['base']['sha256'] = '0' * 64
        (gate / 'RUN_INFO.json').write_text(json.dumps(info))
        with self.assertRaisesRegex(ValueError, 'baseline'):
            self.module.freeze(self.root / 'bad', gates=[gate], limit=1)
        self.assertFalse((self.root / 'bad.partial').exists())

    def test_unknown_player_is_rejected_without_publication(self):
        gate = self.gate()
        path = gate / (gate.name + '.pgn')
        path.write_text(path.read_text().replace('[White "' + BASE + '"]', '[White "unverified"]', 1))
        with self.assertRaisesRegex(ValueError, 'players'):
            self.module.freeze(self.root / 'bad', gates=[gate], limit=1)
        self.assertFalse((self.root / 'bad').exists())

    def test_short_input_and_zero_depth_do_not_publish(self):
        gate = self.gate()
        path = gate / (gate.name + '.pgn')
        path.write_text(path.read_text().replace('+0.20/10', '+0.20/0'))
        with self.assertRaisesRegex(ValueError, 'insufficient'):
            self.module.freeze(self.root / 'short', gates=[gate], limit=3)
        self.assertFalse((self.root / 'short').exists())

    def test_source_change_during_run_prevents_publication(self):
        gate = self.gate()
        path = gate / (gate.name + '.pgn')
        original = self.module.sha256
        calls = 0
        def changed(p):
            nonlocal calls
            if Path(p) == path:
                calls += 1
                if calls == 2:
                    with path.open('a') as fh:
                        fh.write('\n')
            return original(p)
        with patch.object(self.module, 'sha256', side_effect=changed):
            with self.assertRaisesRegex(ValueError, 'changed'):
                self.module.freeze(self.root / 'changed', gates=[gate], limit=1)
        self.assertFalse((self.root / 'changed').exists())

    def test_reserve_failure_and_existing_destination(self):
        gate = self.gate()
        with patch.object(self.module, 'storage_guard', side_effect=OSError('reserve')):
            with self.assertRaisesRegex(OSError, 'reserve'):
                self.module.freeze(self.root / 'blocked', gates=[gate], limit=1)
        self.assertFalse((self.root / 'blocked.partial').exists())
        (self.root / 'existing.partial').mkdir()
        with self.assertRaises(FileExistsError):
            self.module.freeze(self.root / 'existing', gates=[gate], limit=1)

    def test_every_write_batch_checks_reserve_and_failure_stays_partial(self):
        gate = self.gate()
        original = self.module.storage_guard
        writes = 0
        def fail_second_batch(root, allowance=64 * 1024 * 1024):
            nonlocal writes
            if Path(root).exists() and Path(root).name == 'bounded.partial' and allowance < 2 * 1024 * 1024:
                writes += 1
                if writes == 2:
                    raise OSError('reserve changed')
            return original(root, allowance=allowance)
        with patch.object(self.module, 'storage_guard', side_effect=fail_second_batch):
            with self.assertRaisesRegex(OSError, 'reserve changed'):
                self.module.freeze(self.root / 'bounded', gates=[gate], limit=3, batch_size=1)
        self.assertFalse((self.root / 'bounded').exists())
        self.assertEqual(len((self.root / 'bounded.partial/records.jsonl').read_text().splitlines()), 1)


if __name__ == '__main__':
    unittest.main()

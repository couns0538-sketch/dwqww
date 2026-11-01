import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('runner', Path(__file__).with_name('run_tmfit.py'))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class EvidenceTests(unittest.TestCase):
    def test_extract_iteration_records(self):
        lines = ['info depth 4 nodes 10', 'info string tm_log {"depth":4,"best_move":"e2e4"}',
                 'bestmove e2e4 ponder e7e5']
        rows = runner.iteration_rows(lines, 'g1', 7, 'e2e4', 2)
        self.assertEqual(rows[0]['final_best_move'], 'e2e4')
        self.assertEqual(rows[0]['pair_id'], 2)
        self.assertEqual(rows[0]['search_id'], 7)

    def test_opening_order_reproducible(self):
        fens = ['a', 'b', 'c']
        self.assertEqual(runner.order_positions(fens, 12), runner.order_positions(list(reversed(fens)), 12))

    def test_live_requires_diagnostic_and_changes(self):
        rows = []
        for position in range(20):
            for repeat in range(3):
                for mode in (0, 1):
                    rows.append(dict(position=position, repeat=repeat, mode=mode,
                                     engine_ms=100 + (20 if mode and position < 6 else 0),
                                     wall_ms=120 + (20 if mode and position < 6 else 0),
                                     diagnostics=[{'multiplier_permille':1200 if position < 6 else 1000}] if mode else []))
        result = runner.live_summary(rows)
        self.assertTrue(result['pass'])
        self.assertEqual(result['changed_positions'], 6)
        for row in rows:
            row['diagnostics'] = []
        self.assertFalse(runner.live_summary(rows)['pass'])

    def test_live_does_not_accept_neutral_model_or_rounding_noise(self):
        rows = [dict(position=p, repeat=r, mode=m, engine_ms=100+(20 if m else 0),
                     wall_ms=100+(20 if m else 0), diagnostics=[{'multiplier_permille':1000}] if m else [])
                for p in range(20) for r in range(3) for m in (0,1)]
        self.assertFalse(runner.live_summary(rows)['pass'])
        for row in rows:
            row['wall_ms'] = 100 + (.1 if row['mode'] else 0)
            row['diagnostics'] = [{'multiplier_permille':1200}] if row['mode'] else []
        self.assertFalse(runner.live_summary(rows)['pass'])


if __name__ == '__main__':
    unittest.main()

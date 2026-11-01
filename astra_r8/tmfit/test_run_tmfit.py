import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('runner', Path(__file__).with_name('run_tmfit.py'))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class EvidenceTests(unittest.TestCase):
    def test_sanitizer_four_on_games_do_not_require_normalization(self):
        games = [dict(mode=1, result='ply_cap', moves=100) for _ in range(4)]
        result = runner.sanitizer_summary(games, 4)
        self.assertTrue(result['pass_'])
        self.assertEqual(result['requested_games'], 4)
        self.assertTrue(result['all_on'])
        self.assertNotIn('ratio_on_off', result)

    def test_sanitizer_rejects_missing_game_off_mode_and_faults(self):
        games = [dict(mode=1, result='checkmate', moves=20) for _ in range(4)]
        self.assertFalse(runner.sanitizer_summary(games[:3], 4)['pass_'])
        for field, value in [('mode', 0), ('result', 'illegal'), ('result', 'time_loss'), ('moves', 0)]:
            bad = [dict(game) for game in games]
            bad[0][field] = value
            with self.subTest(field=field, value=value):
                self.assertFalse(runner.sanitizer_summary(bad, 4)['pass_'])

    def test_sanitizer_reports_include_summary_and_shutdown_signal(self):
        for line in ['ERROR: AddressSanitizer: heap-buffer-overflow',
                     'SUMMARY: AddressSanitizer: heap-buffer-overflow file.cpp:4',
                     'AddressSanitizer:DEADLYSIGNAL',
                     'SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior file.cpp:4',
                     'ERROR: LeakSanitizer: detected memory leaks',
                     'file.cpp:4: runtime error: signed integer overflow']:
            with self.subTest(line=line):
                self.assertTrue(runner.is_sanitizer_report(line))
        self.assertFalse(runner.is_sanitizer_report('info depth 1 score cp 32 time 1'))

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

import importlib.util
import io
from pathlib import Path
import queue
import subprocess
import time
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location('runner', Path(__file__).with_name('run_tmfit.py'))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class EvidenceTests(unittest.TestCase):
    def test_paired_mode_assignments_swap_colors_only_for_timing(self):
        self.assertEqual(runner.game_player_modes('smoke',0,0,False),[0,1])
        self.assertEqual(runner.game_player_modes('smoke',1,0,False),[1,0])
        self.assertEqual(runner.game_player_modes('calibrate',1,0,False),[1,0])
        self.assertEqual(runner.game_player_modes('calibrate',1,0,True),[1,1])
        self.assertEqual(runner.game_player_modes('collect',1,0,False),[0,0])
        self.assertEqual(runner.game_player_modes('sanitizer',0,0,False),[1,1])
        self.assertEqual(runner.game_player_modes('smoke-shard',1,0,False),[1,0])

    def test_smoke_shard_is_partial_and_cannot_satisfy_qualification(self):
        games=[dict(mode='paired',result='checkmate',moves=100,total_wall_ms=15000,
                    players=[dict(mode=mode,moves=50,total_wall_ms=5000+5000*mode)
                             for mode in runner.game_player_modes('smoke-shard',i,0,False)])
               for i in range(100)]
        partial=runner.timing_summary(games,100,partial=True)
        self.assertTrue(partial['pass_'])
        self.assertEqual(partial['status'],'PARTIAL')
        self.assertFalse(partial['qualification_eligible'])
        self.assertEqual(partial['ratio_on_off'],2)
        self.assertFalse(runner.timing_summary(games,100)['pass_'])
        self.assertFalse(runner.timing_summary(games[:-1],100,partial=True)['pass_'])

    def test_paired_summary_uses_each_engine_side_within_same_game(self):
        games=[]
        for i in range(200):
            players=[dict(mode=mode,color=color,moves=50,total_wall_ms=5000+100*mode)
                     for color,mode in zip(('white','black'),runner.game_player_modes('smoke',i,0,False))]
            games.append(dict(mode='paired',result='checkmate',moves=100,total_wall_ms=10100,players=players))
        summary=runner.timing_summary(games,200)
        self.assertTrue(summary['pass_'])
        self.assertEqual(summary['selfplay_design'],'opposed_modes_colors_swapped')
        self.assertAlmostEqual(summary['ratio_on_off'],1.02)
        self.assertAlmostEqual(summary['game_time_ratio_on_off'],1.02)
        self.assertEqual(summary['average_ms_per_move'],{0:100,1:102})
        games[0]['players'][1]['mode']=0
        self.assertFalse(runner.timing_summary(games,200)['pass_'])

    def test_qualification_also_checks_average_game_side_time(self):
        games=[]
        for i in range(200):
            players=[dict(mode=mode,moves=50+25*mode,total_wall_ms=5000+2500*mode)
                     for mode in runner.game_player_modes('smoke',i,0,False)]
            games.append(dict(mode='paired',result='checkmate',moves=125,total_wall_ms=12500,players=players))
        summary=runner.timing_summary(games,200)
        self.assertEqual(summary['ratio_on_off'],1)
        self.assertEqual(summary['game_time_ratio_on_off'],1.5)
        self.assertFalse(summary['pass_'])
        self.assertTrue(runner.timing_summary(games,200,calibration=True)['pass_'])

    def test_calibration_is_clean_run_only_and_never_qualification(self):
        games = [dict(mode=i%2, result='checkmate', moves=100,
                      total_wall_ms=10000 if i%2==0 else 20000) for i in range(40)]
        result = runner.timing_summary(games,40,calibration=True)
        self.assertTrue(result['pass_'])
        self.assertEqual(result['ratio_on_off'],2)
        self.assertFalse(result['qualification_eligible'])
        self.assertFalse(runner.timing_summary(games,40)['pass_'])
        games[0]['result']='time_loss'
        self.assertFalse(runner.timing_summary(games,40,calibration=True)['pass_'])

    def test_timing_qualification_requires_200_clean_games_and_three_percent(self):
        games = [dict(mode='paired',result='checkmate',moves=100,total_wall_ms=10000,
                      players=[dict(mode=mode,moves=50,total_wall_ms=5000)
                               for mode in runner.game_player_modes('smoke',i,0,False)]) for i in range(200)]
        self.assertTrue(runner.timing_summary(games,200)['pass_'])
        self.assertFalse(runner.timing_summary(games[:198],200)['pass_'])
        for game in games:
            for player in game['players']:
                if player['mode']:
                    player['total_wall_ms']=5200
        self.assertFalse(runner.timing_summary(games,200)['pass_'])

    def test_hung_quit_is_failure_after_owned_child_is_killed(self):
        class HungChild:
            stdin = io.StringIO()
            returncode = None
            killed = False

            def poll(self):
                return self.returncode

            def wait(self, timeout):
                if not self.killed:
                    raise subprocess.TimeoutExpired('owned-child', timeout)
                return self.returncode

            def kill(self):
                self.killed = True
                self.returncode = -9

        process = runner.Process.__new__(runner.Process)
        process.process = HungChild()
        process.log = io.StringIO()
        process.lines = queue.Queue()
        process.reader = SimpleNamespace(join=lambda timeout: None)
        with self.assertRaisesRegex(RuntimeError, 'forced termination'):
            process.close()
        self.assertTrue(process.process.killed)

    def test_sync_rejects_option_errors_even_before_readyok(self):
        for rejection in ['info string invalid value for option TmFitA',
                          'info string Unknown option: TmFitBias',
                          'info string option TmFitDepth rejected',
                          'info string unsupported option TmFitEffort']:
            engine = runner.Engine.__new__(runner.Engine)
            engine.process = SimpleNamespace(stdin=io.StringIO())
            engine.log = io.StringIO()
            engine.lines = queue.Queue()
            for line in (rejection, 'readyok'):
                engine.lines.put((time.perf_counter(), line))
            with self.subTest(rejection=rejection):
                with self.assertRaisesRegex(RuntimeError, 'option rejected'):
                    engine.sync()
                self.assertIn(rejection, engine.log.getvalue())

    def test_reserved_options_cannot_override_test_configuration(self):
        for key, value in [('TmFitModel', '0'), ('Threads', '1'), ('Hash', '16')]:
            engine = runner.Engine.__new__(runner.Engine)
            # An override must be rejected before any engine command is issued.
            engine.send = lambda _: self.fail('configuration rejection must precede UCI traffic')
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError, 'reserved'):
                    engine.initialize(1, {key: value})

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

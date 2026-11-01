import copy
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent))
spec = importlib.util.spec_from_file_location('parallel_smoke', Path(__file__).with_name('run_parallel_smoke.py'))
parallel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parallel)


def fixture():
    frozen = dict(engine_sha256='engine', referee_sha256='referee', runner_sha256='runner',
                  seed=2026110110, base_ms=8000, inc_ms=80, max_plies=400,
                  options=['TmFitA=914','TmFitB=1000','TmFitHi=1500','TmFitLo=750'],
                  option_file_sha256={}, engine_threads=1, assignments=[])
    shards = []
    for shard_id in range(2):
        openings = [f'opening-{shard_id}-{i}' for i in range(50)]
        frozen['assignments'].append(dict(shard_id=shard_id, openings=openings, sha256=f'openings{shard_id}'))
        manifest = dict(engine_sha256='engine', referee_sha256='referee', runner_sha256='runner',
                        openings_sha256=f'openings{shard_id}', engine_threads=1,
                        option_file_sha256={}, selfplay_design='opposed_modes_colors_swapped',
                        command=dict(command='smoke-shard', games=100, seed=2026110110,
                                     base_ms=8000, inc_ms=80, max_plies=400,
                                     option=frozen['options'].copy(), same_mode=False))
        games = []
        for index in range(100):
            players = [dict(color=color, mode=mode, moves=50, total_wall_ms=5000)
                       for color,mode in zip(('white','black'), (index%2,1-index%2))]
            games.append(dict(game=index, pair_id=index//2, mode='paired', result='fifty_move',
                              opening=openings[index//2], moves=100, total_wall_ms=10000, players=players))
        shards.append(dict(shard_id=shard_id, manifest=manifest, games=games,
                           summary=dict(status='PARTIAL', qualification_eligible=False, pass_=True)))
    return frozen, shards


class AggregationTests(unittest.TestCase):
    def test_complete_two_shards_qualify_only_in_parent(self):
        frozen, shards = fixture()
        result = parallel.aggregate(frozen, shards)
        self.assertTrue(result['pass_'])
        self.assertEqual(result['games'], 200)
        self.assertEqual(result['opening_pairs'], 100)
        self.assertEqual(result['strength'], 'UNPROVEN')

    def test_reject_missing_shard_pair_and_wrong_mode(self):
        frozen, shards = fixture()
        cases = [shards[:1], copy.deepcopy(shards), copy.deepcopy(shards)]
        cases[1][0]['games'].pop()
        cases[2][0]['games'][1]['players'][0]['mode'] = 0
        for bad in cases:
            with self.subTest():
                with self.assertRaises(ValueError):
                    parallel.aggregate(frozen, bad)

    def test_reject_duplicate_opening_or_wrong_assignment(self):
        frozen, shards = fixture()
        for mutate in ('duplicate', 'wrong_assignment'):
            bad = copy.deepcopy(shards)
            if mutate == 'duplicate':
                bad[1]['games'][0]['opening'] = bad[0]['games'][0]['opening']
                bad[1]['games'][1]['opening'] = bad[0]['games'][0]['opening']
            else:
                bad[0]['games'][0]['opening'] = bad[0]['games'][2]['opening']
            with self.subTest(mutate=mutate):
                with self.assertRaises(ValueError):
                    parallel.aggregate(frozen, bad)

    def test_reject_different_exe_settings_clock_and_partial_claim(self):
        frozen, shards = fixture()
        for field in ('engine_sha256','runner_sha256','threads','clock','option','claim'):
            bad = copy.deepcopy(shards)
            manifest = bad[1]['manifest']
            if field in ('engine_sha256','runner_sha256'):
                manifest[field] = 'different'
            elif field == 'threads':
                manifest['engine_threads'] = 2
            elif field == 'clock':
                manifest['command']['base_ms'] = 16000
            elif field == 'option':
                manifest['command']['option'] = ['TmFitA=999']
            else:
                bad[1]['summary']['qualification_eligible'] = True
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    parallel.aggregate(frozen,bad)

    def test_fault_and_both_time_tolerances_fail(self):
        frozen, shards = fixture()
        shards[0]['games'][0]['result'] = 'illegal'
        self.assertFalse(parallel.aggregate(frozen,shards)['pass_'])
        frozen, shards = fixture()
        for shard in shards:
            for game in shard['games']:
                for player in game['players']:
                    if player['mode']:
                        player['total_wall_ms'] = 5200
                game['total_wall_ms'] = 10200
        self.assertFalse(parallel.aggregate(frozen,shards)['pass_'])
        # Equal per-move cost can still overspend per game: both checks matter.
        for shard in shards:
            for game in shard['games']:
                for player in game['players']:
                    if player['mode']:
                        player['moves'] = 52
                game['moves'] = 102
        result = parallel.aggregate(frozen,shards)
        self.assertEqual(result['ratio_on_off'],1)
        self.assertFalse(result['pass_'])


if __name__ == '__main__':
    unittest.main()

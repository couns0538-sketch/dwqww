"""Tests for S48 v2 (fix-ups S48-1..4). Synthetic metadata plus copies of six real PC gate files.

Run from this folder:  python -I -B -m unittest -v test_forge_sol_S48_gate_guard_v2_20261027
Set S48_GUARD_DIR to test a mutant copy of the guard (forge_sol_S48_mutants_v2_20261027.py does this).
"""
import copy
import importlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
GUARD_DIR = Path(os.environ.get('S48_GUARD_DIR', HERE))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(GUARD_DIR))
s48 = importlib.import_module('forge_sol_S48_gate_guard_v2_20261027')
exact = importlib.import_module('forge_sol_S48_exact_sprt_v2_20261027')
comparability = s48.comparability
FIX = HERE / 'tests_fixtures'
SCRATCH = Path(os.environ.get('S48_SCRATCH', tempfile.gettempdir()))
try:
    import scipy  # noqa: F401
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False


def gate(name='SYNTHETIC', **over):
    g = {'gate': name, 'concurrency': 5, 'tc': '10+0.1', 'book_sha256': 'a' * 64, 'base_exe_sha256': 'b' * 64,
         'core_mask': [4, 5, 6, 7, 8], 'cap_games': 1500,
         'sprt': {'elo0': 0, 'elo1': 10, 'alpha': 0.05, 'beta': 0.05, 'model': 'normalized'},
         'cand_exe_sha256': 'c' * 64, 'cand_net_md5': 'd' * 32, 'openings_seed': {'srand': 1, 'openings_start': 1001}}
    g.update(over)
    return g


def rule(**over):
    r = {'gate': 'SYNTHETIC', 'concurrency': 5, 'observed_elo': 10.0, 'e0': 0, 'e1': 10, 'cap_games': 40,
         'selection': 'cap', 'early_stop': None}
    r.update(over)
    return r


def real(tag):
    return s48.from_gate_files(FIX / tag / 'RESULT.md', FIX / tag / 'RUN_INFO.json')


G104, G104C = 'gate104_e48f006_vs_h256e12', 'gate104_e48f006_vs_h256e12_confirm'
G120, G120C = 'gate120_e32f003rec_s198_vs_h256e12', 'gate120_e32f003rec_s198_vs_h256e12_confirm'
G100R, G119 = 'gate100r_e32f003_vs_h256e12', 'gate119_e32f003rec_s197_vs_h256e12'
PROFILE = {'counts': [1, 2, 3, 4, 5], 'concurrency': 5, 'provenance': 'SYNTHETIC'}


class ComparabilityV1Behaviour(unittest.TestCase):
    """Sol's v1 guarantees, kept."""

    def test_equal_fully_pinned(self):
        r = comparability(gate('A'), gate('B'))
        self.assertTrue(r['can_compare'])
        self.assertTrue(r['advice_only'])
        self.assertFalse(r['acceptance_authorized'])

    def test_conc7_vs_conc5_blocked(self):
        r = comparability(gate('G120', concurrency=7), gate('G104'))
        self.assertFalse(r['can_compare'])
        self.assertIn('concurrency', [x['field'] for x in r['mismatches']])

    def test_missing_both_is_unknown_not_equality(self):
        a = gate()
        del a['book_sha256']
        r = comparability(a, copy.deepcopy(a))
        self.assertFalse(r['can_compare'])
        self.assertEqual(sum(x['field'] == 'book_sha256' for x in r['unknown']), 2)

    def test_invalid_provenance_rejected(self):
        for field, value in [('concurrency', True), ('concurrency', 0), ('concurrency', 9), ('concurrency', '5'),
                             ('book_sha256', 'short'), ('base_exe_sha256', 'g' * 64), ('core_mask', []),
                             ('core_mask', [1, 1]), ('core_mask', [-1, 2]), ('core_mask', [True, 2]),
                             ('core_mask', '4-8'), ('tc', '')]:
            with self.subTest(field=field, value=value):
                r = comparability(gate(), gate(**{field: value}))
                self.assertFalse(r['can_compare'])
                self.assertIn(field, [x['field'] for x in r['unknown']])

    def test_optional_mismatch_or_one_sided_blocks(self):
        for field, a_value, b_value in [('threads', 1, 2), ('hash_mb', 16, 32),
                                        ('engine_options', {'OwnBook': False}, {'OwnBook': True}),
                                        ('engine_options', {'Flag': True}, {'Flag': 1}),
                                        ('base_net_md5', 'e' * 32, 'f' * 32)]:
            with self.subTest(field=field):
                a, b = gate(**{field: a_value}), gate(**{field: b_value})
                self.assertFalse(comparability(a, b)['can_compare'])
                del b[field]
                self.assertFalse(comparability(a, b)['can_compare'])

    def test_no_silent_mutation(self):
        a, b = gate('A'), gate('B')
        before = copy.deepcopy([a, b])
        comparability(a, b)
        comparability(a, b, mode='replicate')
        self.assertEqual([a, b], before)


class S48_2_NewFields(unittest.TestCase):
    def test_base_exe_sprt_cap_each_block(self):
        for field, value in [('base_exe_sha256', 'e' * 64), ('cap_games', 3000),
                             ('sprt', {'elo0': 0, 'elo1': 5, 'alpha': 0.05, 'beta': 0.05, 'model': 'normalized'}),
                             ('sprt', {'elo0': 0, 'elo1': 10, 'alpha': 0.05, 'beta': 0.05, 'model': 'logistic'}),
                             ('sprt', {'elo0': 0, 'elo1': 10, 'alpha': 0.1, 'beta': 0.05, 'model': 'normalized'})]:
            with self.subTest(field=field, value=value):
                r = comparability(gate(), gate(**{field: value}))
                self.assertFalse(r['can_compare'])
                self.assertIn(field, [x['field'] for x in r['mismatches']])

    def test_new_required_fields_missing_are_unknown(self):
        for field in ('base_exe_sha256', 'sprt', 'cap_games'):
            with self.subTest(field=field):
                b = gate()
                del b[field]
                r = comparability(gate(), b)
                self.assertFalse(r['can_compare'])
                self.assertIn(field, [x['field'] for x in r['unknown']])

    def test_v1_opponent_alias_accepted_and_conflict_rejected(self):
        b = gate()
        b['opponent_exe_sha256'] = b.pop('base_exe_sha256')
        self.assertTrue(comparability(gate(), b)['can_compare'])
        c = gate(opponent_exe_sha256='e' * 64)
        r = comparability(gate(), c)
        self.assertFalse(r['can_compare'])
        self.assertIn('base_exe_sha256', [x['field'] for x in r['unknown']])

    def test_identity_recorded_for_both_sides(self):
        r = comparability(gate('A'), gate('B', cand_exe_sha256='9' * 64))
        self.assertTrue(r['can_compare'])  # rank mode: two candidates vs one base may differ
        self.assertEqual(r['identity']['cand_exe_sha256']['left'], 'c' * 64)
        self.assertEqual(r['identity']['cand_exe_sha256']['right'], '9' * 64)
        self.assertFalse(r['same_candidate'])
        self.assertEqual(r['identity']['cand_net_md5']['left'], 'd' * 32)
        self.assertEqual(r['identity']['openings_seed']['left'], {'srand': 1, 'openings_start': 1001})

    def test_rank_mode_notes_reused_seed(self):
        r = comparability(gate('A'), gate('B', cand_exe_sha256='9' * 64))
        self.assertTrue(any('same openings seed' in n for n in r['notes']))

    def test_replicate_requires_same_candidate_and_new_seed(self):
        new_seed = {'srand': 2, 'openings_start': 2001}
        ok = comparability(gate('G'), gate('Gc', openings_seed=new_seed), mode='replicate')
        self.assertTrue(ok['can_compare'])
        other = comparability(gate('G'), gate('Gc', openings_seed=new_seed, cand_exe_sha256='9' * 64), mode='replicate')
        self.assertFalse(other['can_compare'])
        self.assertIn('cand_exe_sha256', [x['field'] for x in other['mismatches']])
        net = comparability(gate('G'), gate('Gc', openings_seed=new_seed, cand_net_md5='0' * 32), mode='replicate')
        self.assertFalse(net['can_compare'])
        reused = comparability(gate('G'), gate('Gc'), mode='replicate')
        self.assertFalse(reused['can_compare'])
        self.assertIn('openings_seed', [x['field'] for x in reused['mismatches']])
        missing = gate('Gc', openings_seed=new_seed)
        del missing['cand_exe_sha256']
        self.assertFalse(comparability(gate('G'), missing, mode='replicate')['can_compare'])

    def test_bad_mode_rejected(self):
        with self.assertRaises(ValueError):
            comparability(gate(), gate(), mode='pool')


class S48_3_Normalization(unittest.TestCase):
    def test_hash_spellings(self):
        for v in (64, '64', '64MB', '64 MB', '64mb', ' 64 Mb ', '64MiB', '64M'):
            with self.subTest(v=v):
                self.assertEqual(s48.normalize_hash_mb(v), 64)
        self.assertEqual(s48.normalize_hash_mb('1GB'), 1024)
        self.assertEqual(s48.normalize_hash_mb('2 GiB'), 2048)
        for v in (True, 0, -1, '0MB', '64KB', 'abc', 64.0, '6 4MB', None):
            with self.subTest(v=v), self.assertRaises(ValueError):
                s48.normalize_hash_mb(v)

    def test_hash_string_equals_int_in_comparability(self):
        self.assertTrue(comparability(gate(hash_mb='64MB'), gate(hash_mb=64))['can_compare'])
        self.assertFalse(comparability(gate(hash_mb='64MB'), gate(hash_mb='32 MB'))['can_compare'])

    def test_tc_spellings(self):
        for v in ('10+0.1', 'tc=10+0.1', '10.0+0.10', ' 10+0.1 ', '0:10+0.1', '010+00.100'):
            with self.subTest(v=v):
                self.assertEqual(s48.normalize_tc(v), '10+0.1')
        self.assertEqual(s48.normalize_tc('10+0'), '10')
        self.assertEqual(s48.normalize_tc('tc=40/60+0.6'), '40/60+0.6')
        self.assertEqual(s48.normalize_tc('1:00+0.6'), '60+0.6')
        for v in ('', 'abc', '10s+0.1', '-10+0.1', '10++0.1', '0+0.1', 'tc=', '10+0.1 timemargin=1000', 5):
            with self.subTest(v=v), self.assertRaises(ValueError):
                s48.normalize_tc(v)

    def test_tc_normalized_in_comparability(self):
        self.assertTrue(comparability(gate(tc='tc=10+0.10'), gate(tc='10+0.1'))['can_compare'])
        r = comparability(gate(tc='10+0.1'), gate(tc='5+0.05'))
        self.assertIn('tc', [x['field'] for x in r['mismatches']])


class S48_1_RequiredRule(unittest.TestCase):
    def test_each_rule_field_required(self):
        for key in ('e0', 'e1', 'cap_games', 'selection', 'early_stop'):
            with self.subTest(key=key):
                g = rule()
                del g[key]
                with self.assertRaises(ValueError):
                    s48.simulate_gate_bias(g, profile=PROFILE, runs=4, seed=1)

    def test_none_values_also_rejected(self):
        for key in ('e0', 'e1', 'cap_games', 'selection'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                s48.simulate_gate_bias(rule(**{key: None}), profile=PROFILE, runs=4, seed=1)

    def test_invalid_rule_values(self):
        for over in ({'e0': 10, 'e1': 0}, {'e0': True}, {'cap_games': 41}, {'cap_games': 0},
                     {'selection': 'win'}, {'early_stop': {'games': 750}}, {'selection': 'H0-early'}):
            with self.subTest(over=over), self.assertRaises(ValueError):
                s48.simulate_gate_bias(rule(**over), profile=PROFILE, runs=4, seed=1)

    def test_missing_profile_still_unverified_but_rule_checked_first(self):
        r = s48.simulate_gate_bias(rule(gate='G104', observed_elo=29.44, selection='H1'), profile=None)
        self.assertEqual(r['status'], 'UNVERIFIED_MISSING_PAIRED_PROFILE')
        self.assertIsNone(r['adjusted_elo_assuming_model'])
        with self.assertRaises(ValueError):
            s48.simulate_gate_bias({'gate': 'G104', 'concurrency': 5, 'observed_elo': 29.44, 'selection': 'H1'},
                                   profile=None)

    def test_profile_concurrency_not_borrowed(self):
        with self.assertRaises(ValueError):
            s48.simulate_gate_bias(rule(concurrency=7), profile=PROFILE, runs=4, seed=1)
        with self.assertRaises(ValueError):
            s48.simulate_gate_bias(rule(concurrency=1), profile=dict(PROFILE, concurrency=True), runs=4, seed=1)

    def test_explicit_rule_is_used(self):
        r = s48.simulate_gate_bias(rule(cap_games=40), profile=PROFILE, runs=50, seed=7)
        self.assertEqual(r['simulation']['cap_games'], 40)
        self.assertEqual(r['simulation']['e1'], 10.0)
        self.assertLessEqual(max(r['outcome_counts'].values()), 50)
        self.assertEqual(r['model'], exact.MODEL_LABEL)
        self.assertFalse(r['acceptance_authorized'])

    def test_same_seed_same_output_exact(self):
        a = s48.simulate_gate_bias(rule(cap_games=60), profile=PROFILE, runs=80, seed=11)
        b = s48.simulate_gate_bias(rule(cap_games=60), profile=PROFILE, runs=80, seed=11)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))


class SelectionBias(unittest.TestCase):
    def test_conditional_bias_does_not_pool(self):
        r = s48.selection_bias({'outcome': ['H1', 'H1', 'H1', 'H0', 'cap', 'H0-early'],
                                'terminal_elo': [10, 20, 30, -900, 999, -50]}, 10, outcome='H1', observed_elo=40)
        self.assertEqual(r['selected_replicates'], 3)
        self.assertAlmostEqual(r['conditional_mean_elo'], 20)
        self.assertAlmostEqual(r['bias_estimate'], 10)
        self.assertAlmostEqual(r['bias_mc_standard_error'], (100 / 3) ** .5)
        self.assertAlmostEqual(r['adjusted_elo_assuming_model'], 30)
        self.assertIsNone(r['corrected_observation_ci95'])
        self.assertEqual(r['outcome_counts']['H0-early'], 1)

    def test_outcome_now_required(self):
        with self.assertRaises(TypeError):
            s48.selection_bias({'outcome': ['H1'], 'terminal_elo': [1]}, 10)

    def test_infinite_selected_blocks(self):
        r = s48.selection_bias({'outcome': ['H1', 'H1'], 'terminal_elo': [10, float('inf')]}, 10, outcome='H1')
        self.assertEqual(r['status'], 'UNVERIFIED_NONFINITE_SELECTED_ESTIMATES')


class S48_4_GridOutput(unittest.TestCase):
    def test_grid_inside_git_tree_refused(self):
        # The real checkout is detected as a git work tree (no write attempted there) ...
        self.assertIsNotNone(s48.git_work_tree_of(HERE / 'any_new_file.jsonl.gz'), 'tests must run inside the git checkout')
        # ... and refusals are exercised in a fake work tree in scratch, so even a mutant never writes into git.
        root = Path(tempfile.mkdtemp(prefix='s48v2_fakegit_', dir=SCRATCH))
        (root / '.git').mkdir()
        (root / 'sub').mkdir()
        for target in (root / 'grid.jsonl.gz', root / 'sub' / 'grid.jsonl.gz'):
            with self.subTest(target=target.name):
                with self.assertRaises(ValueError):
                    s48.write_grid(target, [{'x': 1}])
                self.assertFalse(target.exists())
                with self.assertRaises(ValueError):
                    s48.simulate_gate_bias(rule(), profile=PROFILE, runs=4, seed=1, grid_out=target)
                self.assertFalse(target.exists())

    def test_grid_outside_git_has_manifest_and_is_deterministic(self):
        root = Path(tempfile.mkdtemp(prefix='s48v2_grid_', dir=SCRATCH))
        self.assertIsNone(s48.git_work_tree_of(root), 'scratch must be outside git for this test')
        rows = [{'gate': 'X', 'outcome': ['cap', 'H1'], 'terminal_elo': [1.5, 20.25]}]
        m1 = s48.write_grid(root / 'a.jsonl.gz', rows)
        m2 = s48.write_grid(root / 'b.jsonl.gz', rows)
        self.assertEqual(m1['sha256'], m2['sha256'])
        import hashlib
        self.assertEqual(m1['sha256'], hashlib.sha256((root / 'a.jsonl.gz').read_bytes()).hexdigest())
        self.assertFalse(m1['in_git'])
        with self.assertRaises(ValueError):
            s48.write_grid(root / 'a.jsonl.gz', rows)  # never overwrite

    def test_explicit_override_allowed(self):
        root = Path(tempfile.mkdtemp(prefix='s48v2_gitlike_', dir=SCRATCH))
        (root / '.git').mkdir()
        with self.assertRaises(ValueError):
            s48.write_grid(root / 'g.jsonl.gz', [{'x': 1}])
        m = s48.write_grid(root / 'g.jsonl.gz', [{'x': 1}], allow_git=True)
        self.assertTrue(m['in_git'])


class RealGateFiles(unittest.TestCase):
    def test_printed_fastchess_figures_reproduced(self):
        for tag in (G100R, G104, G104C, G119, G120, G120C):
            with self.subTest(tag=tag):
                g = real(tag)
                p = g['fastchess_printed']
                v = exact.verify_printed(g['ptnml'], g['e0'], g['e1'], p['llr'], p['elo'], p['elo_err'], p['nelo'])
                self.assertTrue(v['all_match'], v)

    def test_g120_conc7_vs_g104_conc5_flagged(self):
        r = comparability(real(G120), real(G104))
        self.assertFalse(r['can_compare'])
        self.assertIn('concurrency', [x['field'] for x in r['mismatches']])

    def test_confirm_pairs_replicate_mode(self):
        r = comparability(real(G120), real(G120C), mode='replicate')
        self.assertTrue(r['can_compare'], r)
        self.assertTrue(r['same_candidate'])
        r = comparability(real(G104), real(G104C), mode='replicate')
        self.assertTrue(r['can_compare'], r)

    def test_old_runinfo_concurrency_from_settings(self):
        g = real(G100R)
        self.assertEqual(g['concurrency'], 5)
        self.assertEqual(g['concurrency_source'], 'RESULT.md settings line')
        self.assertIsNone(g['early_stop'])
        self.assertEqual(real(G120)['early_stop'], {'games': 750, 'elo_max': -8, 'llr_max': -1.5})

    def test_rule_fields_present_for_simulation(self):
        for tag, sel in ((G100R, 'cap'), (G104, 'H1'), (G119, 'cap'), (G120, 'H1')):
            with self.subTest(tag=tag):
                g = real(tag)
                self.assertEqual(g['selection'], sel)
                self.assertEqual(s48.gate_rule(g)[:4], (0.0, 10.0, 1500, sel))


class ModelChecks(unittest.TestCase):
    def test_h1_stopped_mean_above_true_plus10(self):
        """Sol's S48 pass line: mean stopped Elo of H1 stops at a true +10 under [0,10]/1500 is above +10."""
        g = dict(rule(selection='H1', cap_games=1500, observed_elo=9.5), gate='G119-shape')
        r = s48.simulate_gate_bias(g, profile={'counts': [9, 130, 435, 163, 13], 'concurrency': 5,
                                               'provenance': 'G119 Ptnml'}, true_elo=10.0, runs=600, seed=48)
        self.assertGreater(r['selected_replicates'], 30)
        self.assertGreater(r['conditional_mean_elo'], 10.0)

    @unittest.skipUnless(HAVE_SCIPY, 'approx model (Sol S33 planner) needs scipy; not installed on the PC venv')
    def test_approx_model_labelled(self):
        r = s48.simulate_gate_bias(rule(cap_games=40), profile=PROFILE, runs=8, seed=48, model='approx')
        self.assertTrue(r['model'].startswith('approx model'))

    def test_approx_refuses_early_stop(self):
        with self.assertRaises(ValueError):
            s48.simulate_gate_bias(rule(early_stop={'games': 750, 'elo_max': -8, 'llr_max': -1.5}),
                                   profile=PROFILE, runs=4, seed=1, model='approx')


if __name__ == '__main__':
    unittest.main()

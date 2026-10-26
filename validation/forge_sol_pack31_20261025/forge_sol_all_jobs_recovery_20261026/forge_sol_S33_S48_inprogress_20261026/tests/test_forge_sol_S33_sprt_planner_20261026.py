"""Independent model, online stopping, and finite-cap approximation checks."""
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np

MODULE = Path(__file__).resolve().parents[1] / 'forge_sol_S33_sprt_planner_20261026.py'


class PlannerTests(unittest.TestCase):
    def setUp(self):
        # Explicit assertion establishes RED without an import/setup error.
        self.assertTrue(MODULE.is_file(), 'S33 planner implementation is missing')
        spec = importlib.util.spec_from_file_location('s33_planner', MODULE)
        self.api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.api)

    def test_logistic_true_elo_is_distinct_from_normalized_bounds(self):
        # Catches interpreting the user's true Elo as nElo.
        self.assertAlmostEqual(self.api.logistic_score(400), 10 / 11, places=14)
        p = self.api.tilted_profile([9, 130, 435, 163, 13], 9.5)
        # Independently evaluated with Decimal precision=50 (literal fixture).
        self.assertAlmostEqual(np.dot(p, [0, .25, .5, .75, 1]), .5136681928158032933, places=13)

    def test_exponential_tilt_preserves_support_and_shape_ratios(self):
        # Catches inventing mass in absent pair bins or replacing a profile.
        p = self.api.tilted_profile([0, 1, 4, 1, 0], 20)
        self.assertEqual(p[0], 0)
        self.assertEqual(p[4], 0)
        self.assertAlmostEqual(p[2] ** 2 / (p[1] * p[3]), 16, places=12)
        self.assertAlmostEqual(sum(p), 1, places=14)
        np.testing.assert_allclose(self.api.tilted_profile([0, 1, 4, 1, 0], 0), [0, 1/6, 4/6, 1/6, 0], atol=1e-14)

    def test_independent_draw_profile_has_correct_mean_and_bins(self):
        # Fixed 50% draws and zero Elo give L/D/W=(.25,.5,.25).
        np.testing.assert_allclose(self.api.draw_profile(.5, 0), [.0625, .25, .375, .25, .0625], atol=1e-14)
        p = self.api.draw_profile(.4, 10)
        self.assertAlmostEqual(np.dot(p, [0, .25, .5, .75, 1]), .5143871841659987, places=13)
        with self.assertRaises(ValueError):
            self.api.draw_profile(.9, 400)

    def test_unreachable_or_invalid_profile_inputs_are_rejected(self):
        # Catches clipping the target or accepting malformed model inputs.
        for profile in ([0]*5, [1,-1,1,1,1], [1,2], [True,1,1,1,1], [1,math.inf,1,1,1]):
            with self.subTest(profile=profile), self.assertRaises(ValueError):
                self.api.tilted_profile(profile, 0)
        with self.assertRaises(ValueError):
            self.api.tilted_profile([0,0,1,0,0], 1)
        with self.assertRaises(ValueError):
            self.api.tilted_profile([1,1,0,0,0], 0)

    def test_three_supplied_llr_fixtures_remain_approximate(self):
        # Catches incorrect nElo units, wrong pair normalization, or exact claims.
        for counts, target in (([13,128,463,137,9],-.56), ([5,121,458,154,12],2.22), ([9,130,435,163,13],1.72)):
            r = self.api.llr_from_counts(counts)
            self.assertAlmostEqual(r['value'], target, delta=.02)
            self.assertFalse(r['exact_fastchess'])
            self.assertIn('approximate', r['model'])

    def test_degenerate_zero_elo_is_all_cap_with_null_variance(self):
        # A deterministic .5 score cannot produce a variance-based LLR.
        r = self.api.simulate_cell([0,0,1,0,0], 0, runs=32, cap_games=10, seed=11, return_samples=True)
        self.assertEqual(r['probabilities'], {'H1':0., 'H0':0., 'cap':1.})
        self.assertEqual(r['mean_games'], 10)
        self.assertEqual(r['median_games'], 10)
        self.assertTrue(np.all(r['samples']['games'] == 10))
        self.assertTrue(np.all(r['samples']['terminal_elo'] == 0))
        a = self.api.analytic_cell([0,0,1,0,0], 0, cap_games=10)
        self.assertEqual(a['probabilities'], {'H1':0., 'H0':0., 'cap':1.})
        self.assertEqual(a['mean_games'], 10)

    def test_same_seed_exact_reproducibility_and_json_safe_summary(self):
        # Catches unrecorded RNG state or nonfinite JSON summaries.
        kwargs = dict(runs=256, cap_games=100, seed=721, return_samples=True)
        a = self.api.simulate_cell([9,130,435,163,13], 9.5, **kwargs)
        b = self.api.simulate_cell([9,130,435,163,13], 9.5, **kwargs)
        for key in ('games','terminal_elo','outcome'):
            np.testing.assert_array_equal(a['samples'][key], b['samples'][key])
        self.assertEqual(a['seed'], 721)
        self.assertEqual(a['true_elo_units'], 'logistic')
        self.assertEqual(a['hypothesis_units'], 'nelo')
        self.assertAlmostEqual(sum(a['probabilities'].values()), 1)
        del a['samples']
        json.dumps(a, allow_nan=False)

    def test_common_paths_across_caps_preserve_already_stopped_outcomes(self):
        # Catches treating capped observations as H0 or pooling observations.
        protocols = [dict(e0=0,e1=10,cap_games=500), dict(e0=0,e1=10,cap_games=1000)]
        a,b = self.api.simulate_protocols([9,130,435,163,13], 9.5, protocols, runs=128, seed=31, return_samples=True)
        stopped = a['samples']['outcome'] != 'cap'
        np.testing.assert_array_equal(a['samples']['games'][stopped], b['samples']['games'][stopped])
        np.testing.assert_array_equal(a['samples']['outcome'][stopped], b['samples']['outcome'][stopped])
        self.assertLessEqual(a['probabilities']['H1'], b['probabilities']['H1'])
        self.assertLessEqual(a['probabilities']['H0'], b['probabilities']['H0'])
        self.assertGreaterEqual(a['probabilities']['cap'], b['probabilities']['cap'])

    def test_online_empirical_llr_matches_counts_on_each_path_prefix(self):
        # Catches a frozen-variance walk masquerading as online S06 statistics.
        path = np.array([[0,1,2,3,4,2,2,3,1,2]], dtype=np.int8)
        llr = self.api.online_llr(path, e0=0, e1=10)
        self.assertTrue(np.isnan(llr[0,0]))
        for n in range(2,11):
            counts = np.bincount(path[0,:n], minlength=5).tolist()
            want = self.api.llr_from_counts(counts)['value']
            self.assertAlmostEqual(llr[0,n-1], want, places=12)

    def test_brownian_finite_cap_matches_hand_checked_reference(self):
        # Reference independently checked by killed-diffusion eigen expansion.
        r = self.api.brownian_finite_cap(.0023, .001657, -2.9444, 2.9444, 750)
        self.assertAlmostEqual(r['probabilities']['H0'], .0000526578, delta=1e-9)
        self.assertAlmostEqual(r['probabilities']['H1'], .1867951173, delta=1e-9)
        self.assertAlmostEqual(r['probabilities']['cap'], .8131522248, delta=1e-9)
        self.assertEqual(r['median_games'], 1500)
        self.assertGreater(r['mean_games'], 1000)
        self.assertLess(r['mean_games'], 1500)

    def test_symmetric_zero_drift_and_very_short_cap(self):
        # Catches swapped boundary fluxes and forgetting finite-cap survival.
        r = self.api.brownian_finite_cap(0, 1, -1, 1, .01)
        self.assertAlmostEqual(r['probabilities']['H0'], r['probabilities']['H1'], places=14)
        self.assertGreater(r['probabilities']['cap'], .999)
        self.assertAlmostEqual(r['mean_games'], .02, places=9)

    def test_invalid_protocols_and_runs_are_rejected(self):
        # Catches silent cap truncation, reversed bounds, or non-SPRT thresholds.
        bad = ({'cap_games':3}, {'cap_games':0}, {'runs':0}, {'runs':True}, {'e0':10,'e1':0}, {'alpha':.8,'beta':.8}, {'units':'elo'}, {'seed':-1})
        for kw in bad:
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                self.api.simulate_cell([1,2,4,2,1], 0, **kw)

    def test_full_grid_has_630_cells_and_distinct_gate_profiles(self):
        # Catches omitting a specified protocol or combining concurrent gates.
        cells = self.api.grid_cells()
        self.assertEqual(len(cells), 630)
        self.assertEqual(len({(c['profile'],c['true_elo'],c['protocol']) for c in cells}), 630)
        self.assertEqual({c['true_elo'] for c in cells}, {-5+2.5*i for i in range(15)})
        self.assertTrue(all(self.api.PROFILES[x]['concurrency'] == 5 for x in ('G95','G100r','G119')))
        self.assertTrue(all(self.api.PROFILES[x]['concurrency'] is None for x in ('draw0.4','draw0.5','draw0.6')))

    def test_validation_preserves_failed_cells_and_fixed_ids(self):
        # Catches choosing a favorable subset after seeing analytic discrepancies.
        self.assertEqual(len(self.api.VALIDATION_CELLS), 6)
        rows = [{**cell, 'mc': {'H1':.3,'H0':.2,'cap':.5}, 'analytic': {'H1':.34 if i==2 else .3,'H0':.2,'cap':.46 if i==2 else .5}} for i,cell in enumerate(self.api.VALIDATION_CELLS)]
        report = self.api.compare_validation(rows)
        self.assertEqual(report['status'], 'FAIL')
        self.assertEqual(report['failed_cells'], ['V3'])
        self.assertEqual(len(report['cells']), 6)

    def test_impossible_model_hypotheses_fail_closed_for_both_methods(self):
        # Catches analytic reporting power for a hypothesis score outside [0,1].
        for function in (self.api.analytic_cell,self.api.simulate_cell):
            with self.subTest(function=function.__name__), self.assertRaises(ValueError):
                kwargs = {'runs':8} if function.__name__=='simulate_cell' else {}
                function([9,130,435,163,13],9.5,e1=1000,cap_games=10,**kwargs)

    def test_validation_rejects_substituted_or_duplicate_cells(self):
        # Catches claiming predeclaration when passed favorable arbitrary cells.
        rows = [{**cell,'mc':{'H1':.3,'H0':.2,'cap':.5},'analytic':{'H1':.3,'H0':.2,'cap':.5}} for cell in self.api.VALIDATION_CELLS]
        rows[2] = dict(rows[1])
        with self.assertRaises(ValueError):
            self.api.compare_validation(rows)

    def test_sampling_layout_replays_a_shared_protocol_cell(self):
        # Catches recording only a seed, insufficient to recreate shared paths.
        ps = [dict(e0=0,e1=10,cap_games=10),dict(e0=0,e1=5,cap_games=20)]
        rows = self.api.simulate_protocols([1,2,4,2,1],0,ps,runs=16,seed=5,block_size=8,return_samples=True)
        self.assertIn('sampling_layout',rows[0])
        layout = rows[0]['sampling_layout']
        self.assertEqual(layout['block_size'],8)
        self.assertEqual(layout['max_pairs'],10)
        self.assertEqual(len(layout['protocols']),2)
        self.assertTrue(rows[0]['python_version'])
        replay = self.api.simulate_protocols(rows[0]['pair_probabilities'],0,layout['protocols'],runs=16,seed=rows[0]['seed'],block_size=layout['block_size'],return_samples=True)
        for key in ('games','outcome','terminal_elo'):
            np.testing.assert_array_equal(rows[1]['samples'][key],replay[1]['samples'][key])

    def test_cli_refuses_existing_output_directory_without_changes(self):
        # Catches recreating earlier output dirs before overwriting result files.
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)/'old';out.mkdir()
            marker = out/'earlier.json';marker.write_bytes(b'preserve previous evidence\n')
            before = marker.read_bytes()
            process = subprocess.run([sys.executable,'-B',str(MODULE),'--screen','--runs','1','--output-dir',str(out)],capture_output=True,text=True)
            self.assertEqual(process.returncode,2)
            self.assertNotIn('Traceback',process.stderr)
            self.assertEqual(marker.read_bytes(),before)
            self.assertEqual(sorted(x.name for x in out.iterdir()),['earlier.json'])

    def test_cli_refuses_symlink_output_directory(self):
        # Catches writing through a symlink into unrelated earlier evidence.
        with tempfile.TemporaryDirectory() as temp:
            actual = Path(temp)/'actual';actual.mkdir()
            link = Path(temp)/'link';link.symlink_to(actual,target_is_directory=True)
            process = subprocess.run([sys.executable,'-B',str(MODULE),'--screen','--runs','1','--output-dir',str(link)],capture_output=True,text=True)
            self.assertEqual(process.returncode,2)
            self.assertNotIn('Traceback',process.stderr)
            self.assertEqual(list(actual.iterdir()),[])

    def test_cli_creates_new_output_directory_exclusively(self):
        # Catches failing closed even when the requested new destination is valid.
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)/'new'
            process = subprocess.run([sys.executable,'-B',str(MODULE),'--screen','--runs','1','--output-dir',str(out)],capture_output=True,text=True)
            self.assertEqual(process.returncode,0,process.stderr)
            self.assertTrue(out.is_dir())
            self.assertTrue(json.loads(process.stdout)['screen_only'])

    def test_cli_refuses_empty_existing_dir_and_symlinked_parent(self):
        # Catches permitting evidence destinations through preexisting aliases.
        with tempfile.TemporaryDirectory() as temp:
            existing = Path(temp)/'existing';existing.mkdir()
            parent = Path(temp)/'parent';parent.symlink_to(existing,target_is_directory=True)
            for out in (existing,parent/'new'):
                process = subprocess.run([sys.executable,'-B',str(MODULE),'--screen','--runs','1','--output-dir',str(out)],capture_output=True,text=True)
                self.assertEqual(process.returncode,2)
                self.assertNotIn('Traceback',process.stderr)
            self.assertEqual(list(existing.iterdir()),[])

    def test_standalone_adjacent_frozen_s06_dependency_is_selected(self):
        # Catches packets that import from a missing ../S06 despite local dependency.
        with tempfile.TemporaryDirectory() as temp:
            standalone = Path(temp)/'packet';standalone.mkdir()
            copied = standalone/MODULE.name;shutil.copyfile(MODULE,copied)
            dependency = standalone/'forge_sol_S06_statistics_20261026.py'
            shutil.copyfile(self.api.S06_DEPENDENCY,dependency)
            spec = importlib.util.spec_from_file_location('standalone_s33',copied)
            module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            self.assertEqual(module.S06_DEPENDENCY,dependency)
            self.assertAlmostEqual(module.llr_from_counts([9,130,435,163,13])['value'],1.7270936930171805,places=12)

    def test_standalone_modified_s06_dependency_fails_closed(self):
        # Catches accepting a changed neighboring dependency under a frozen name.
        with tempfile.TemporaryDirectory() as temp:
            standalone = Path(temp)/'packet';standalone.mkdir()
            copied = standalone/MODULE.name;shutil.copyfile(MODULE,copied)
            dependency = standalone/'forge_sol_S06_statistics_20261026.py'
            dependency.write_text('def summarize_pentanomial(*args,**kwargs): return {}\n')
            spec = importlib.util.spec_from_file_location('changed_s33',copied)
            module = importlib.util.module_from_spec(spec)
            with self.assertRaises((ValueError,RuntimeError)):
                spec.loader.exec_module(module)


if __name__ == '__main__':
    unittest.main(verbosity=2)

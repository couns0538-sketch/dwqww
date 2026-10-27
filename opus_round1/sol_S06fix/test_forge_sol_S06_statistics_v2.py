"""Independent fixtures for the offline paired-score statistics API."""
import importlib.util
import json
import math
from pathlib import Path
import unittest


MODULE = Path(__file__).with_name('forge_sol_S06_statistics_v2.py')


class StatisticsTests(unittest.TestCase):
    def setUp(self):
        # A missing deliverable is an explicit assertion failure during RED.
        self.assertTrue(MODULE.is_file(), 'paired-score statistics implementation is missing')
        spec = importlib.util.spec_from_file_location('s06_statistics', MODULE)
        self.api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.api)

    def summarize(self, counts, **metadata):
        return self.api.summarize_pentanomial(counts, **metadata)

    def test_public_targets_match_within_point_zero_one(self):
        # Catches changed pairing weights, Elo derivative, or nElo LLR formula.
        cases = (
            ([13, 128, 463, 137, 9], .23162375799634602, 8.529387704444096, -.5619847571501702),
            ([5, 121, 458, 154, 12], 10.889879760538442, 8.379769831474425, 2.219838109695718),
            ([9, 130, 435, 163, 13], 9.4989387299871, 8.841725084629944, 1.7270936930171805),
        )
        for counts, elo, halfwidth, llr in cases:
            with self.subTest(counts=counts):
                result = self.summarize(counts)
                self.assertAlmostEqual(result['logistic_elo']['estimate'], elo, delta=.01)
                self.assertAlmostEqual(result['logistic_elo']['ci95_delta_halfwidth'], halfwidth, delta=.01)
                self.assertAlmostEqual(result['gaussian_llr']['value'], llr, delta=.01)

    def test_weighted_population_moments(self):
        # Catches sample variance or treating a pair as two independent games.
        r = self.summarize([1, 2, 3, 4, 5])
        self.assertEqual(r['pairs'], 15)
        self.assertEqual(r['games'], 30)
        self.assertAlmostEqual(r['score_mean'], 2 / 3, places=15)
        self.assertAlmostEqual(r['score_variance_population'], 7 / 72, places=15)
        self.assertAlmostEqual(r['score_standard_error'], .08050764858994133, places=14)
        self.assertAlmostEqual(r['normalized_elo']['estimate'], 131.31830798670236, places=10)
        self.assertIsNone(r['individual_wdl'])
        self.assertFalse(r['inference']['paired_counts_identify_individual_wdl'])
        self.assertTrue(r['inference']['low_pair_count'])
        self.assertIn('approximate', r['inference']['ci_limitations'].lower())

    def test_logistic_hypotheses_are_explicit_and_distinct_from_nelo(self):
        # Catches silently substituting logistic hypotheses for normalized Elo.
        counts = [13, 128, 463, 137, 9]
        nelo = self.summarize(counts)
        logistic = self.summarize(counts, units='logistic', e0=-3, e1=12)
        self.assertEqual(nelo['hypothesis']['units'], 'nelo')
        self.assertEqual(logistic['hypothesis']['units'], 'logistic')
        self.assertAlmostEqual(logistic['hypothesis']['score0'], .4956827602449402, places=14)
        self.assertAlmostEqual(logistic['hypothesis']['score1'], .5172625244323762, places=14)
        self.assertGreater(abs(nelo['hypothesis']['score1'] - logistic['hypothesis']['score1']), .001)

    def test_transformed_score_interval_is_separate_from_delta_interval(self):
        # Catches labeling a symmetric Elo interval as transformed endpoints.
        r = self.summarize([0, 0, 0, 1, 3])
        self.assertIsNotNone(r['logistic_elo']['ci95_delta'])
        transformed = r['logistic_elo']['ci95_transformed_score']
        self.assertIsNotNone(transformed[0])
        self.assertIsNone(transformed[1])
        self.assertGreater(r['score_ci95'][1], 1)
        self.assertNotEqual(transformed[0], r['logistic_elo']['ci95_delta'][0])

    def test_reverse_colors_and_negated_asymmetric_bounds_reverse_llr(self):
        # Catches assuming an antisymmetric LLR while leaving bounds unchanged.
        counts = [9, 130, 435, 163, 13]
        for units in ('nelo', 'logistic'):
            original = self.summarize(counts, e0=-3, e1=12, units=units)
            flipped = self.summarize(list(reversed(counts)), e0=-12, e1=3, units=units)
            unchanged_bounds = self.summarize(list(reversed(counts)), e0=-3, e1=12, units=units)
            self.assertAlmostEqual(original['gaussian_llr']['value'], -flipped['gaussian_llr']['value'], places=12)
            self.assertNotAlmostEqual(original['gaussian_llr']['value'], -unchanged_bounds['gaussian_llr']['value'], places=8)
            self.assertAlmostEqual(original['logistic_elo']['estimate'], -flipped['logistic_elo']['estimate'], places=12)

    def test_wald_crossing_is_diagnostic_only(self):
        # Catches reversed error thresholds or reporting acceptance authority.
        for counts, expected in (([0, 0, 0, 1000, 1000], 'accept_h1_diagnostic'),
                                 ([1000, 1000, 0, 0, 0], 'accept_h0_diagnostic'),
                                 ([13, 128, 463, 137, 9], 'continue')):
            r = self.summarize(counts, alpha=.1, beta=.2)
            w = r['wald_diagnostic']
            self.assertAlmostEqual(w['lower'], -1.504077396776274, places=14)
            self.assertAlmostEqual(w['upper'], 2.0794415416798357, places=14)
            self.assertEqual(w['decision'], expected)
            self.assertTrue(w['diagnostic_only'])
            self.assertFalse(r['inference']['acceptance_authorized'])
            self.assertFalse(r['gaussian_llr']['exact_fastchess'])
            self.assertIn('approximate', r['gaussian_llr']['model'].lower())

    def test_empty_and_degenerate_results_are_json_safe_and_unknown(self):
        # Catches division by zero, accidental NaN/Infinity, and false certainty.
        for counts in ([0, 0, 0, 0, 0], [0, 0, 5, 0, 0], [5, 0, 0, 0, 0], [0, 0, 0, 0, 5]):
            with self.subTest(counts=counts):
                r = self.summarize(counts)
                json.dumps(r, allow_nan=False)
                self.assertIsNone(r['gaussian_llr']['value'])
                self.assertIsNone(r['score_standard_error'])
                self.assertIsNone(r['score_ci95'])
                self.assertIsNone(r['logistic_elo']['ci95_delta_halfwidth'])
                self.assertEqual(r['wald_diagnostic']['decision'], 'unknown')
                self.assertTrue(r['null_reasons'])
        self.assertIsNone(self.summarize([0, 0, 0, 0, 0])['score_mean'])
        self.assertEqual(self.summarize([0, 0, 5, 0, 0])['logistic_elo']['estimate'], 0)
        self.assertIsNone(self.summarize([5, 0, 0, 0, 0])['logistic_elo']['estimate'])
        self.assertIsNone(self.summarize([0, 0, 0, 0, 5])['logistic_elo']['estimate'])

    def test_nonfinite_intermediate_results_are_never_json_numbers(self):
        # Catches an overflowing hypothesis leaking Infinity into a JSON report.
        r = self.summarize([1, 2, 3, 4, 5], e0=-1e308, e1=1e308)
        json.dumps(r, allow_nan=False)
        self.assertIsNone(r['gaussian_llr']['value'])
        self.assertEqual(r['wald_diagnostic']['decision'], 'unknown')
        self.assertEqual(r['status'], 'blocked')

    def test_impossible_hypothesis_scores_block_inference_without_clamping(self):
        # Catches silently clipping impossible nElo hypotheses into probabilities.
        r = self.summarize([1, 2, 3, 4, 5], e0=0, e1=1000)
        self.assertGreater(r['hypothesis']['score1'], 1)
        self.assertEqual(r['status'], 'blocked')
        self.assertIsNone(r['gaussian_llr']['value'])
        self.assertTrue(r['null_reasons'])

    def test_one_pair_is_marked_low_count_and_nelo_needs_variation(self):
        # Catches reporting a one-pair uncertainty estimate as established.
        r = self.summarize([0, 0, 0, 1, 0])
        self.assertTrue(r['inference']['low_pair_count'])
        self.assertIsNone(r['normalized_elo']['estimate'])
        self.assertIsNone(r['gaussian_llr']['value'])
        symmetric = self.summarize([1, 0, 0, 0, 1])
        self.assertEqual(symmetric['normalized_elo']['estimate'], 0)
        self.assertFalse(self.summarize([13, 128, 463, 137, 9])['inference']['low_pair_count'])

    def test_overlapping_wald_thresholds_do_not_pick_a_contradictory_decision(self):
        # Catches silently choosing one of two simultaneously crossed thresholds.
        r = self.summarize([1, 0, 0, 0, 1], e0=-5, e1=5, alpha=.8, beta=.8)
        self.assertGreater(r['wald_diagnostic']['lower'], r['wald_diagnostic']['upper'])
        self.assertEqual(r['wald_diagnostic']['decision'], 'unknown')
        self.assertTrue(any('overlap' in reason for reason in r['null_reasons']))

    def test_reject_invalid_counts(self):
        # Catches coercing booleans, truncating floats, wrong length, or negatives.
        bad = (None, '00000', {}, {0, 1, 2, 3, 4}, [], [0] * 4, [0] * 6,
               [True, 0, 0, 0, 0], [0, 0, 0, 0, -1], [0, 0, 0, 0, 1.0],
               [0, 0, 0, 0, float('nan')])
        for counts in bad:
            with self.subTest(counts=counts):
                with self.assertRaises(ValueError):
                    self.summarize(counts)

    def test_reject_invalid_metadata_and_reversed_hypotheses(self):
        # Catches accepting reversed bounds or invalid error rates silently.
        bad = ({'e0': 10, 'e1': 0}, {'e0': 1, 'e1': 1}, {'e0': True},
               {'e0': '0'}, {'e0': float('nan')}, {'e1': float('inf')},
               {'alpha': 0}, {'alpha': 1}, {'beta': -.1}, {'beta': 1},
               {'alpha': True}, {'beta': float('nan')}, {'units': 'elo'},
               {'units': None}, {'units': ['nelo']})
        for metadata in bad:
            with self.subTest(metadata=metadata):
                with self.assertRaises(ValueError):
                    self.summarize([1, 2, 3, 4, 5], **metadata)

    def test_input_is_not_mutated_and_tuple_is_supported(self):
        counts = [1, 2, 3, 4, 5]
        result = self.summarize(counts)
        result['counts'][0] = 99
        self.assertEqual(counts, [1, 2, 3, 4, 5])
        self.assertEqual(self.summarize(tuple(counts))['pairs'], 15)


if __name__ == '__main__':
    unittest.main(verbosity=2)

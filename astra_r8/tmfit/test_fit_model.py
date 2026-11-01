"""Small deterministic tests; synthetic fixtures are never empirical fit evidence."""
import math
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

import fit_model as fit


def row(game, search, depth, move, **kw):
    return dict(game_id=game, search_id=search, depth=depth, best_move=move,
                changed=int(depth > 1), node_fraction=0.5, score_cp=30,
                score_delta_cp=-10, elapsed_ms=depth * 10, soft_ms=100, **kw)


class FitTests(unittest.TestCase):
    def test_labels_exclude_final_and_use_completed_move(self):
        rows = [row('g', 1, 1, 'e2e4'), row('g', 1, 2, 'd2d4'),
                row('g', 1, 3, 'd2d4'), row('g', 2, 1, 'g1f3')]
        dataset = fit.prepare(rows)
        self.assertEqual(dataset.y.tolist(), [1, 0])
        self.assertEqual([r['depth'] for r in dataset.rows], [1, 2])
        self.assertEqual(dataset.excluded_final, 2)

    def test_duplicate_or_nonincreasing_depth_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'depth'):
            fit.prepare([row('g', 1, 2, 'e2e4'), row('g', 1, 2, 'e2e4')])

    def test_invalid_features_fail_closed(self):
        for field, value in [('node_fraction', float('nan')), ('node_fraction', 1.1),
                             ('soft_ms', 0), ('changed', 2), ('elapsed_ms', -1)]:
            rows = [row('g', 1, 1, 'e2e4'), row('g', 1, 2, 'e2e4')]
            rows[0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                fit.prepare(rows)

    def test_group_split_is_reproducible_and_disjoint(self):
        groups = np.repeat(np.array([f'g{i}' for i in range(10)]), 4)
        train, test = fit.group_split(groups, 8128)
        self.assertEqual(len(set(groups[test])), 2)
        self.assertFalse(set(groups[train]) & set(groups[test]))
        np.testing.assert_array_equal(test, fit.group_split(groups, 8128)[1])

    def test_auc_ties_and_orientation(self):
        self.assertEqual(fit.auc(np.array([0, 1, 0, 1]), np.ones(4)), 0.5)
        self.assertEqual(fit.auc(np.array([0, 1]), np.array([0., 1.])), 1.0)
        self.assertEqual(fit.auc(np.array([0, 1]), np.array([1., 0.])), 0.0)
        self.assertIsNone(fit.auc(np.ones(3), np.arange(3)))

    def test_fit_recovers_predictive_direction(self):
        x = np.column_stack([np.ones(400), np.linspace(-3, 3, 400)])
        rng = np.random.default_rng(531)
        y = (rng.random(400) < fit.sigmoid(-0.3 + 1.4 * x[:, 1])).astype(float)
        beta = fit.fit_logistic(x, y)
        self.assertGreater(beta[1], 0.8)
        self.assertLess(beta[1], 2.2)
        self.assertGreater(fit.auc(y, x @ beta), 0.8)

    def test_feature_integer_contract(self):
        r = row('g', 1, 7, 'e2e4')
        r.update(changed=0, score_cp=-19, score_delta_cp=-1200, elapsed_ms=1000)
        q = fit.features_q10(r)
        self.assertEqual(q.tolist(), [1024, 448, 0, 512, -19, -1024, 4096])

    def test_integer_probability_matches_expected_and_saturates(self):
        x = np.array([[1024, 0, 0, 0, 0, 0, 0]], dtype=np.int64)
        for bias, expected in [(0, 512), (4096, 749), (-4096, 275),
                               (131072, 1024), (-131072, 0)]:
            b = np.array([bias, 0, 0, 0, 0, 0, 0], dtype=np.int64)
            self.assertEqual(fit.predict_q10(x, b).tolist(), [expected])

    def test_quantization_bounds_do_not_silently_clip_fit(self):
        with self.assertRaisesRegex(ValueError, 'range'):
            fit.quantize(np.array([33.0] * 7))

    def test_returned_move_disagreement_is_retained_and_counted(self):
        bad = [row('bad', 1, 1, 'd2d4', final_best_move='d2d4'),
               row('bad', 1, 2, 'e2e4', final_best_move='d2d4')]
        good = [row('good', 1, 1, 'e2e4'), row('good', 1, 2, 'e2e4')]
        data = fit.prepare(bad + good)
        self.assertEqual(data.excluded_incomplete, 0)
        self.assertEqual(data.returned_move_disagreements, 1)
        self.assertEqual(data.y.tolist(), [1, 0])
        self.assertEqual(len(data.rows), 2)

    def test_final_response_and_seal_metadata_are_not_features(self):
        a = row('g', 1, 1, 'e2e4', final_best_move='e2e4', search_iteration_count=2)
        b = dict(a, final_best_move='d2d4', search_iteration_count=32, pair_id='other')
        np.testing.assert_array_equal(fit.features_q10(a), fit.features_q10(b))

    def test_truncated_sealed_search_is_excluded(self):
        partial = [row('partial', 1, 1, 'e2e4', search_iteration_index=0, search_iteration_count=3),
                   row('partial', 1, 2, 'd2d4', search_iteration_index=1, search_iteration_count=3)]
        good = [row('good', 1, 1, 'e2e4'), row('good', 1, 2, 'e2e4')]
        self.assertEqual(fit.prepare(partial + good).excluded_incomplete, 2)
        with self.assertRaisesRegex(ValueError, 'unsealed'):
            fit.prepare(good, require_seals=True)

    def test_end_to_end_hashes_sample_holdout_and_no_overwrite(self):
        # Tiny synthetic source lives only inside an owned test directory.
        with tempfile.TemporaryDirectory(prefix='test-fit-', dir=Path(__file__).parent) as name:
            root = Path(name)
            source = root / 'synthetic.jsonl'
            records = [row(f'g{game}', 1, d, move, complete=True, final_best_move='d2d4',
                           search_iteration_index=d-1, search_iteration_count=3)
                       for game in range(10)
                       for d, move in [(1, 'e2e4'), (2, 'd2d4'), (3, 'd2d4')]]
            source.write_text(''.join(json.dumps(r) + '\n' for r in records), encoding='utf-8')
            args = [str(source), '--output', str(root / 'fit'), '--minimum-iterations', '30']
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(fit.main(args), 0)
            report = json.loads((root / 'fit' / 'fit.json').read_text())
            self.assertEqual(report['raw_iterations'], 30)
            self.assertEqual(report['excluded_final_iterations'], 10)
            self.assertEqual(report['test_rows'], 4)
            self.assertEqual(report['sample']['rows'], 1)
            self.assertEqual(report['sources'][0]['sha256'], fit.sha256(source))
            self.assertEqual(report['sample']['sha256'], fit.sha256(root / 'fit' / 'sample_1pct.jsonl'))
            self.assertEqual(report['holdout_auc_fixed'], 1.0)
            self.assertEqual(report['status'], 'UNPROVEN')
            with self.assertRaises(FileExistsError):
                fit.main(args)


if __name__ == '__main__':
    unittest.main()

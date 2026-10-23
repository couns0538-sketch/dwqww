"""Residual training contract, independent of production search or network edits.

The original attached trainer exports only standalone networks. These regressions
pin the difference between a raw residual and the HCE-plus-residual probability.
"""
from __future__ import annotations

import importlib
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import tempfile
import unittest

import numpy as np
import torch

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))


def exported_values(text, symbol):
    match = re.search(r"\b" + re.escape(symbol) + r"\[\d+\]\s*=\s*\{([^}]+)\}", text)
    if match is None:
        raise AssertionError("Export is missing " + symbol)
    return [int(number) for number in re.findall(r"-?\d+", match.group(1))]


class ResidualTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.training = importlib.import_module("residual_train")

    def test_target_is_search_minus_hce_in_engine_logit_units(self):
        score = torch.tensor([200.0, -200.0, 0.0, 100.0])
        hce = torch.tensor([100.0, -100.0, 0.0, 0.0])
        actual = self.training.residual_logit_target(score, hce)
        torch.testing.assert_close(actual, torch.tensor([0.5625, -0.5625, 0.0, 0.5625]))

    def test_identical_search_and_hce_needs_no_correction(self):
        cp = torch.tensor([-1000.0, -17.0, 0.0, 49.0, 1000.0])
        actual = self.training.residual_logit_target(cp, cp)
        torch.testing.assert_close(actual, torch.zeros_like(cp), rtol=0, atol=0)

    def test_zero_correction_reproduces_hce_not_neutral_probability(self):
        actual = self.training.predicted_probability(torch.zeros(3), torch.tensor([-200.0, 0.0, 200.0]))
        torch.testing.assert_close(actual, torch.tensor([0.24508501313237172, 0.5, 0.7549149868676283]))

    def test_correct_residual_recovers_teacher_even_when_hce_is_wrong(self):
        score = torch.tensor([-300.0, 0.0, 150.0])
        hce = torch.tensor([150.0, -500.0, 0.0])
        residual = self.training.residual_logit_target(score, hce)
        actual = self.training.predicted_probability(residual, hce)
        expected = torch.sigmoid(torch.tensor([-1.6875, 0.0, 0.84375]))
        torch.testing.assert_close(actual, expected)

    def test_signed_stm_scores_are_not_flipped_a_second_time(self):
        positive = self.training.predicted_probability(torch.tensor([0.3]), torch.tensor([200.0]))
        negative = self.training.predicted_probability(torch.tensor([-0.3]), torch.tensor([-200.0]))
        torch.testing.assert_close(positive + negative, torch.ones(1))
        self.assertGreater(float(positive), 0.5)
        self.assertLess(float(negative), 0.5)

    def test_result_mix_uses_stm_result_without_reflection_or_logit_mixing(self):
        actual = self.training.residual_probability_target(
            torch.tensor([-200.0, 200.0]), torch.tensor([-100.0, 100.0]),
            torch.tensor([1.0, 0.0]), 0.25,
        )
        torch.testing.assert_close(actual, torch.tensor([0.4338137598492788, 0.5661862401507212]))

    def test_pure_teacher_probability_is_independent_of_hce_error(self):
        score = torch.tensor([200.0, -200.0])
        actual = self.training.residual_probability_target(
            score, torch.tensor([-1000.0, 1000.0]), torch.tensor([0.0, 1.0]), 0.0,
        )
        torch.testing.assert_close(actual, torch.tensor([0.7549149868676283, 0.24508501313237172]))

    def test_invalid_result_weight_cannot_silently_extrapolate(self):
        for weight in (-0.01, 1.01, float("nan"), float("inf")):
            with self.subTest(weight=weight), self.assertRaises(ValueError):
                self.training.residual_probability_target(
                    torch.zeros(1), torch.zeros(1), torch.zeros(1), weight,
                )


class ScheduleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.training = importlib.import_module("residual_train")

    def test_result_weight_starts_with_search_only_and_reaches_configured_end(self):
        values = [self.training.result_weight(epoch, 5, 0.0, 0.1) for epoch in range(5)]
        np.testing.assert_allclose(values, [0.0, 0.025, 0.05, 0.075, 0.1], rtol=0, atol=1e-12)

    def test_cosine_learning_rate_has_configured_endpoints_and_midpoint(self):
        values = [self.training.learning_rate(epoch, 5, 0.001, 0.0001) for epoch in range(5)]
        self.assertAlmostEqual(values[0], 0.001)
        self.assertAlmostEqual(values[2], 0.00055)
        self.assertAlmostEqual(values[-1], 0.0001)
        self.assertTrue(all(left >= right for left, right in zip(values, values[1:])))
        self.assertNotAlmostEqual(values[1], 0.000775)  # Linear decay is not cosine.

    def test_one_epoch_has_finite_start_values_without_division_by_zero(self):
        weight = self.training.result_weight(0, 1, 0.0, 0.1)
        lr = self.training.learning_rate(0, 1, 0.001, 0.0001)
        self.assertTrue(math.isfinite(weight) and math.isfinite(lr))
        self.assertEqual(weight, 0.0)
        self.assertEqual(lr, 0.001)


class ResidualExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = importlib.import_module("train_nnue")
        torch.set_num_threads(1)

    def model(self):
        torch.manual_seed(73)
        return self.original.NNUE([128], qat=True)

    def test_legacy_export_keeps_standalone_flag_and_float_binary_layout(self):
        model = self.model()
        with tempfile.TemporaryDirectory() as directory:
            stem = Path(directory) / "legacy"
            self.original.export_forge(model, stem, 2.25)
            text = stem.with_suffix(".inc").read_text()
            self.assertIn("#define FORGE_NNUE_RESIDUAL 0", text)
            binary = np.fromfile(stem.with_suffix(".bin"), dtype="<f4")
            expected = np.concatenate([
                model.ft.weight.detach().numpy().T.ravel(),
                model.ft.bias.detach().numpy(),
                model.tail[0].weight.detach().numpy().ravel(),
                model.tail[0].bias.detach().numpy(),
            ])
            np.testing.assert_array_equal(binary, expected)
            self.assertEqual(binary.nbytes, (768 * 128 + 128 + 256 + 1) * 4)

    def test_residual_export_marks_h128_correction_and_keeps_old_binary_layout(self):
        # This call raises TypeError on the original supplied trainer: changing
        # the macro after standalone training cannot satisfy this contract.
        model = self.model()
        with tempfile.TemporaryDirectory() as directory:
            legacy, residual = Path(directory) / "legacy", Path(directory) / "residual"
            self.original.export_forge(model, legacy, 2.25)
            self.original.export_forge(model, residual, 2.25, residual=True)
            text = residual.with_suffix(".inc").read_text()
            self.assertIn("#define FORGE_NNUE_RESIDUAL 1", text)
            self.assertIn("forge::nnue::HiddenSize == 128", text)
            self.assertEqual(len(exported_values(text, "NnueW1")), 768 * 128)
            self.assertEqual(len(exported_values(text, "NnueB1")), 128)
            self.assertEqual(len(exported_values(text, "NnueW2")), 256)
            self.assertEqual(legacy.with_suffix(".bin").read_bytes(), residual.with_suffix(".bin").read_bytes())

    def test_export_rounds_half_away_from_zero_in_feature_major_layout(self):
        model = self.model()
        with torch.no_grad():
            for parameter in model.parameters():
                parameter.zero_()
            model.ft.weight[0, :4] = torch.tensor([0.5, -0.5, 1.5, -1.5]) / 4096
            model.ft.bias[:4] = torch.tensor([0.5, -0.5, 1.5, -1.5]) / 4096
            model.tail[0].weight[0, :4] = torch.tensor([0.5, -0.5, 1.5, -1.5]) / 4096
            model.tail[0].bias[0] = 0.5 / 4096
        with tempfile.TemporaryDirectory() as directory:
            stem = Path(directory) / "rounding"
            self.original.export_forge(model, stem, 2.25)
            text = stem.with_suffix(".inc").read_text()
            w1 = exported_values(text, "NnueW1")
            self.assertEqual([w1[index * 128] for index in range(4)], [1, -1, 2, -2])
            self.assertEqual(exported_values(text, "NnueB1")[:4], [1, -1, 2, -2])
            self.assertEqual(exported_values(text, "NnueW2")[:4], [1, -1, 2, -2])
            self.assertRegex(text, r"NnueB2\s*=\s*1;")

    def test_nonfinite_weights_are_rejected_before_publishing_any_file(self):
        for invalid in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(invalid=invalid), tempfile.TemporaryDirectory() as directory:
                model = self.model()
                with torch.no_grad():
                    model.tail[0].bias[0] = invalid
                with self.assertRaisesRegex(RuntimeError, "Non-finite"):
                    self.original.export_forge(model, Path(directory) / "invalid", 2.25)
                self.assertEqual(list(Path(directory).iterdir()), [])

    def test_wrong_engine_logit_scale_cannot_be_exported(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "2.25"):
                self.original.export_forge(self.model(), Path(directory) / "wrong-scale", 1.0)
            self.assertEqual(list(Path(directory).iterdir()), [])


class HeldOutMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.training = importlib.import_module("residual_train")
        cls.shared = importlib.import_module("train_nnue")
        torch.set_num_threads(1)

    def model(self, bias=0.0):
        model = self.shared.NNUE([128], qat=True)
        with torch.no_grad():
            for parameter in model.parameters():
                parameter.zero_()
            model.tail[0].bias[0] = bias
        return model

    def data(self, count):
        features = np.full((count, 2, 32), -1, dtype=np.int16)
        features[:, 0, :2] = [5 * 64 + 4, 11 * 64 + 60]
        features[:, 1, :2] = [5 * 64 + 4, 11 * 64 + 60]
        return {
            "features": features,
            "hce": np.zeros(count, dtype=np.int32),
            "score": np.zeros(count, dtype=np.int32),
            "result_stm": np.full(count, 0.5, dtype=np.float32),
        }

    def test_zero_output_baseline_matches_hce_and_separates_net_only(self):
        data = self.data(4)
        data["hce"][:] = [-200, -100, 100, 200]
        data["score"][:] = data["hce"]
        metrics = self.training.evaluate(self.model(), data, batch_size=3)
        self.assertEqual(metrics["count"], 4)
        self.assertAlmostEqual(metrics["teacher_mse_hce"], 0.0, delta=1e-12)
        self.assertAlmostEqual(metrics["teacher_mse_combined"], 0.0, delta=1e-12)
        self.assertGreater(metrics["teacher_mse_net_only"], 0.01)
        self.assertAlmostEqual(metrics["target_mse_hce"], metrics["teacher_mse_hce"], delta=1e-12)
        self.assertAlmostEqual(metrics["target_mse_combined"], metrics["teacher_mse_combined"], delta=1e-12)

    def test_all_held_out_rows_contribute_including_beyond_old_hundred_batch_cap(self):
        data = self.data(105)
        data["score"][100:] = 200
        metrics = self.training.evaluate(self.model(), data, batch_size=1)
        expected = 5 / 105 * (0.7549149868676283 - 0.5) ** 2
        self.assertEqual(metrics["count"], 105)
        self.assertAlmostEqual(metrics["teacher_mse_hce"], expected, delta=1e-8)
        self.assertAlmostEqual(metrics["teacher_mse_combined"], expected, delta=1e-8)

    def test_validation_uses_engine_centipawn_truncation_of_each_correction(self):
        for sign in (-1, 1):
            with self.subTest(sign=sign):
                data = self.data(1)
                data["hce"][:] = 100
                # +/-43/4096 logits is +/-1.866...cp: the engine truncates
                # correction to +/-1cp, rather than rounding to +/-2cp.
                data["score"][:] = 100 + sign
                metrics = self.training.evaluate(self.model(sign * 43 / 4096), data, batch_size=1)
                self.assertAlmostEqual(metrics["teacher_mse_combined"], 0.0, delta=1e-12)
                self.assertGreater(metrics["teacher_mse_hce"], 0)

    def test_report_keeps_fixed_teacher_metric_separate_from_result_mix(self):
        data = self.data(2)
        data["score"][:] = 200
        data["result_stm"][:] = 0.0
        pure = self.training.evaluate(self.model(), data, batch_size=2, result_weight=0.0)
        mixed = self.training.evaluate(self.model(), data, batch_size=2, result_weight=0.25)
        self.assertAlmostEqual(pure["teacher_mse_hce"], mixed["teacher_mse_hce"])
        self.assertAlmostEqual(pure["teacher_mse_combined"], mixed["teacher_mse_combined"])
        self.assertNotAlmostEqual(pure["target_mse_hce"], mixed["target_mse_hce"])
        self.assertNotAlmostEqual(pure["target_mse_combined"], mixed["target_mse_combined"])


class TrainingRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.training = importlib.import_module("residual_train")
        torch.set_num_threads(1)

    def prepare(self, directory):
        data_dir = Path(directory) / "data"
        data_dir.mkdir()
        sources = data_dir / "synthetic-unit-source.txt"
        sources.write_text("Synthetic prepared-array fixtures; not strength evidence.\n")
        files = {}
        for name, count in (("train.npz", 4), ("validation.npz", 2)):
            features = np.full((count, 2, 32), -1, dtype=np.int16)
            features[:, :, :2] = [5 * 64 + 4, 11 * 64 + 60]
            np.savez_compressed(
                data_dir / name, features=features,
                hce=np.zeros(count, dtype=np.int32),
                score=np.full(count, 100, dtype=np.int32),
                result_stm=np.full(count, 1.0, dtype=np.float32),
            )
            files[name] = {"sha256": hashlib.sha256((data_dir / name).read_bytes()).hexdigest(), "rows": count}
        manifest = {
            "schema_version": 1, "hidden_size": 128,
            "score_pov": "side_to_move", "result_pov": "side_to_move",
            "split": {
                "policy": "game_hash", "seed": 20261023,
                "train_game_ids": ["synthetic-training-game"],
                "validation_game_ids": ["synthetic-held-out-game"],
                "legacy_training_game_ids_unknown": False,
            },
            "files": files,
            "filters": {"max_abs_score": 1000, "no_in_check": True, "tactical_bestmove_filter": True},
            "sources": [{"path": str(sources), "sha256": hashlib.sha256(sources.read_bytes()).hexdigest(), "kind": "unit_fixture"}],
        }
        path = data_dir / "manifest.json"
        path.write_text(json.dumps(manifest, indent=2) + "\n")
        return data_dir, manifest

    def arguments(self, data_dir, run_dir):
        return [
            "--data-dir", str(data_dir), "--run-dir", str(run_dir),
            "--epochs", "2", "--batch-size", "3", "--threads", "1",
            "--lr", "0.001", "--min-lr", "0.0001",
            "--result-start", "0.0", "--result-end", "0.1", "--seed", "17",
        ]

    def test_initial_and_every_epoch_are_saved_with_baseline_and_full_validation_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            data_dir, _ = self.prepare(directory)
            run_dir = Path(directory) / "run"
            self.training.main(self.arguments(data_dir, run_dir))
            summary = json.loads((run_dir / "summary.json").read_text())
            self.assertEqual(summary["status"], "completed")
            self.assertEqual(summary["epochs_completed"], 2)
            self.assertEqual(summary["training_count"], 4)
            self.assertEqual(summary["validation_count"], 2)
            self.assertEqual(summary["initial"]["count"], 2)
            self.assertAlmostEqual(summary["hce_baseline"], summary["initial"]["teacher_mse_hce"])
            self.assertAlmostEqual(summary["hce_baseline"], summary["initial"]["teacher_mse_combined"])
            self.assertEqual(summary["manifest_sha256"], hashlib.sha256((data_dir / "manifest.json").read_bytes()).hexdigest())
            best = summary["best"]
            self.assertIn(best["epoch"], (0, 1, 2))
            self.assertTrue(math.isfinite(best["teacher_mse_combined"]))
            self.assertEqual(best["improves_hce"], best["teacher_mse_combined"] < summary["hce_baseline"])
            self.assertTrue(best["stem"])
            for stem in ("initial", "epoch-0001", "epoch-0002"):
                checkpoint = run_dir / "checkpoints" / (stem + ".pt")
                self.assertTrue(checkpoint.is_file(), stem)
                self.assertIsInstance(torch.load(checkpoint, map_location="cpu", weights_only=True), dict)
                for suffix in (".inc", ".bin", ".json"):
                    self.assertTrue((run_dir / "exports" / (stem + suffix)).is_file(), stem + suffix)
                text = (run_dir / "exports" / (stem + ".inc")).read_text()
                self.assertIn("#define FORGE_NNUE_RESIDUAL 1", text)

    def test_missing_validation_game_ids_are_rejected_instead_of_position_split_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            data_dir, manifest = self.prepare(directory)
            del manifest["split"]["validation_game_ids"]
            (data_dir / "manifest.json").write_text(json.dumps(manifest) + "\n")
            with self.assertRaisesRegex(ValueError, "[Gg]ame"):
                self.training.main(self.arguments(data_dir, Path(directory) / "run"))

    def test_one_game_cannot_appear_in_both_folds(self):
        with tempfile.TemporaryDirectory() as directory:
            data_dir, manifest = self.prepare(directory)
            manifest["split"]["validation_game_ids"] = manifest["split"]["train_game_ids"].copy()
            (data_dir / "manifest.json").write_text(json.dumps(manifest) + "\n")
            with self.assertRaisesRegex(ValueError, "[Gg]ame|overlap|disjoint"):
                self.training.main(self.arguments(data_dir, Path(directory) / "run"))

    def test_existing_run_directory_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            data_dir, _ = self.prepare(directory)
            run_dir = Path(directory) / "run"
            run_dir.mkdir()
            sentinel = run_dir / "existing-checkpoint.txt"
            sentinel.write_bytes(b"existing experiment stays intact\n")
            with self.assertRaises(FileExistsError):
                self.training.main(self.arguments(data_dir, run_dir))
            self.assertEqual(sentinel.read_bytes(), b"existing experiment stays intact\n")
            self.assertEqual(list(run_dir.iterdir()), [sentinel])


if __name__ == "__main__":
    unittest.main(verbosity=2)

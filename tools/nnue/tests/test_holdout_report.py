"""Paired whole-game uncertainty and authentic row mapping, using inert fixtures."""
import copy
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

import chess
import numpy as np
import torch

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))


class WholeGameBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = importlib.import_module("compare_holdout")

    def test_identity_has_zero_paired_interval(self):
        losses = np.array([0.1, 0.2, 0.3])
        actual = self.report.cluster_bootstrap(losses, losses, ["a", "a", "b"], 200, 17)
        self.assertEqual(actual["improvement_abs"], 0.0)
        np.testing.assert_array_equal(actual["ci95_abs"], [0.0, 0.0])
        np.testing.assert_array_equal(actual["ci95_relative"], [0.0, 0.0])

    def test_different_size_games_use_ratio_of_sums_and_resample_whole_games(self):
        # Game a has nine rows with loss1, game b one row with loss9.
        # Mean of game means would wrongly report5; true row-weighted MSE1.8.
        # Whole-game resampling can select b twice, giving9. Position bootstrap
        # would make that endpoint vanishingly unlikely at this fixed seed.
        actual = self.report.cluster_bootstrap(np.array([1.0] * 9 + [9.0]), np.zeros(10),
                                             ["a"] * 9 + ["b"], 2000, 20261023)
        self.assertEqual(actual["rows"], 10)
        self.assertEqual(actual["games"], 2)
        self.assertAlmostEqual(actual["reference_mse"], 1.8)
        self.assertAlmostEqual(actual["improvement_abs"], 1.8)
        np.testing.assert_allclose(actual["ci95_abs"], [1.0, 9.0], rtol=0, atol=1e-12)
        np.testing.assert_allclose(actual["ci95_relative"], [1.0, 1.0], rtol=0, atol=1e-12)

    def test_pairing_preserves_constant_per_row_difference(self):
        actual = self.report.cluster_bootstrap(np.array([0.2, 0.3, 0.4]), np.array([0.1, 0.2, 0.3]),
                                             ["a", "b", "b"], 1000, 19)
        np.testing.assert_allclose(actual["ci95_abs"], [0.1, 0.1], rtol=0, atol=1e-12)

    def test_zero_reference_relative_interval_is_undefined_not_division_by_zero(self):
        actual = self.report.cluster_bootstrap(np.zeros(3), np.zeros(3), ["a", "a", "b"], 100, 17)
        self.assertEqual(actual["ci95_abs"], [0.0, 0.0])
        self.assertIsNone(actual["improvement_relative"])
        self.assertIsNone(actual["ci95_relative"])

    def test_seed_replays_exactly(self):
        args = (np.array([0.01, 0.2, 0.3]), np.array([0.02, 0.1, 0.3]), ["a", "b", "c"], 100, 23)
        self.assertEqual(self.report.cluster_bootstrap(*args), self.report.cluster_bootstrap(*args))

    def test_missing_identity_nonfinite_loss_and_one_game_block_intervals(self):
        for candidate, ids in (([0.0, 0.0], ["a", None]), ([0.0, 0.0], ["a"]),
                               ([float("nan"), 0.0], ["a", "b"]), ([-0.1, 0.0], ["a", "b"]),
                               ([0.0, 0.0], ["a", "a"])):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                self.report.cluster_bootstrap(np.zeros(2), np.array(candidate), ids, 20, 1)


class RecipeIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = importlib.import_module("compare_holdout")
        cls.shared = importlib.import_module("train_nnue")

    def fixture(self, directory):
        directory = Path(directory)
        board = chess.Board()
        records, features, recipes = [], [], []
        source = directory / "games.jsonl"
        for index, (move, score, result, game) in enumerate([
            ("e2e4", 100, 1.0, "game-a"), ("e7e5", -120, 1.0, "game-a"),
            ("g1f3", 80, 0.5, "game-b"),
        ]):
            fen = board.fen(en_passant="fen")
            record = {"fen": fen, "game_id": game, "ply": board.ply(), "score_cp_stm": score,
                      "result_white": result, "bestmove": move, "engine_sha256": "a" * 64}
            records.append(record)
            packed = np.full((2, 32), -1, dtype=np.int16)
            for perspective, indices in enumerate(self.shared.feature_indices(board)):
                packed[perspective, :len(indices)] = indices
            features.append(packed)
            recipes.append({"fen": fen, "game_id": game, "ply": board.ply(), "source_path": str(source),
                            "source_line": index + 1, "legacy_game_identity_unknown": False})
            board.push_uci(move)
        source.write_text("".join(json.dumps(row) + "\n" for row in records))
        data = {"features": np.asarray(features), "hce": np.array([0, 200, -200], dtype=np.int32),
                "score": np.array([100, -120, 80], dtype=np.int32),
                "result_stm": np.array([1.0, 0.0, 0.5], dtype=np.float32)}
        manifest = {"split": {"train_game_ids": ["training-game"], "validation_game_ids": ["game-a", "game-b"]},
                    "generation_engine_sha256": "a" * 64,
                    "filters": {"max_abs_score": 1000},
                    "sources": [{"path": str(source), "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                                 "kind": "authenticated_game_data_or_manifest"}],
                    "files": {"validation.npz": {"rows": 3}}, "artifacts": {}}
        self.seal(directory, manifest, recipes)
        return data, manifest, recipes

    def seal(self, directory, manifest, recipes):
        path = Path(directory) / "validation-provenance.jsonl"
        path.write_text("".join(json.dumps(row) + "\n" for row in recipes))
        manifest["artifacts"][path.name] = {"rows": len(recipes), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def test_genuine_ordered_recipe_replays_source_and_keeps_sparse_order_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            data, manifest, _ = self.fixture(directory)
            original = data["features"].copy()
            actual = self.report.validate_validation_provenance(directory, manifest, data)
            self.assertEqual(actual["game_ids"], ["game-a", "game-a", "game-b"])
            self.assertEqual(actual["rows"], 3)
            np.testing.assert_array_equal(data["features"], original)
            data["features"] = data["features"][:, :, ::-1].copy()
            repeated = self.report.validate_validation_provenance(directory, manifest, data)
            self.assertEqual(repeated["game_ids"], actual["game_ids"])

    def test_missing_recipe_binding_or_wrong_sha_blocks_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            data, manifest, _ = self.fixture(directory)
            changed = copy.deepcopy(manifest)
            changed["artifacts"] = {}
            with self.assertRaises(ValueError):
                self.report.validate_validation_provenance(directory, changed, data)
            manifest["artifacts"]["validation-provenance.jsonl"]["sha256"] = "0" * 64
            with self.assertRaises(ValueError):
                self.report.validate_validation_provenance(directory, manifest, data)

    def test_missing_game_membership_and_legacy_identity_cannot_be_guessed(self):
        for field, value in (("game_id", None), ("game_id", "training-game"),
                             ("legacy_game_identity_unknown", True)):
            with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as directory:
                data, manifest, recipes = self.fixture(directory)
                recipes[0][field] = value
                self.seal(directory, manifest, recipes)
                with self.assertRaises(ValueError):
                    self.report.validate_validation_provenance(directory, manifest, data)

    def test_source_line_or_recipe_order_mismatch_is_rejected_even_with_valid_hash(self):
        for mode in ("line", "order", "duplicate"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                data, manifest, recipes = self.fixture(directory)
                if mode == "line":
                    recipes[0]["source_line"] = 2
                elif mode == "order":
                    recipes[0], recipes[1] = recipes[1], recipes[0]
                else:
                    recipes[1] = recipes[0].copy()
                self.seal(directory, manifest, recipes)
                with self.assertRaises(ValueError):
                    self.report.validate_validation_provenance(directory, manifest, data)

    def test_per_row_losses_match_complete_evaluate_aggregate(self):
        with tempfile.TemporaryDirectory() as directory:
            data, _, _ = self.fixture(directory)
            torch.set_num_threads(1)
            model = self.shared.NNUE([128], qat=True)
            with torch.no_grad():
                for parameter in model.parameters():
                    parameter.zero_()
                model.tail[0].bias.fill_(43 / 4096)
            actual = self.report.per_row_losses(model, data, batch_size=2)
            expected = importlib.import_module("residual_train").evaluate(model, data, batch_size=2)
            for key, metric in (("hce", "teacher_mse_hce"), ("combined", "teacher_mse_combined"),
                                ("net_only", "teacher_mse_net_only")):
                self.assertAlmostEqual(float(np.mean(actual[key])), expected[metric], delta=1e-12)

    def reference_fixture(self, directory, data, manifest):
        directory = Path(directory)
        np.savez(directory / "validation.npz", **data)
        manifest["files"]["validation.npz"]["sha256"] = hashlib.sha256((directory / "validation.npz").read_bytes()).hexdigest()
        text = json.dumps(manifest, indent=2) + "\n"
        (directory / "manifest.json").write_text(text)
        reference = directory / "reference-run"
        reference.mkdir()
        (reference / "input-manifest.json").write_text(text)
        summary = {"status": "baseline_only", "input_integrity": "passed", "validation_count": 3,
                   "manifest_sha256": hashlib.sha256(text.encode()).hexdigest(),
                   "config": {"data_dir": str(directory), "initial_net": {"sha256": "b" * 64}},
                   "initial": {"count": 3, "teacher_mse_hce": 0.1, "teacher_mse_combined": 0.09}}
        (reference / "summary.json").write_text(json.dumps(summary) + "\n")
        return reference, summary

    def test_reference_baseline_authenticates_same_validation_arrays_and_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            data, manifest, _ = self.fixture(directory)
            reference, _ = self.reference_fixture(directory, data, manifest)
            actual = self.report.verify_reference_holdout(
                data, manifest, {"teacher_mse_hce": 0.1, "teacher_mse_combined": 0.09},
                reference, {"sha256": "b" * 64},
            )
            self.assertEqual(actual["status"], "PASS_SAME_FROZEN_VALIDATION_ARRAYS_RECIPE_AND_BASELINE")
            self.assertEqual(actual["rows"], 3)

    def test_changed_reference_labels_or_baseline_metric_do_not_silently_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            data, manifest, _ = self.fixture(directory)
            reference, _ = self.reference_fixture(directory, data, manifest)
            changed = {key: value.copy() for key, value in data.items()}
            changed["score"][0] += 1
            with self.assertRaises(ValueError):
                self.report.verify_reference_holdout(
                    changed, manifest, {"teacher_mse_hce": 0.1, "teacher_mse_combined": 0.09}, reference, {"sha256": "b" * 64})
            with self.assertRaises(ValueError):
                self.report.verify_reference_holdout(
                    data, manifest, {"teacher_mse_hce": 0.11, "teacher_mse_combined": 0.09}, reference, {"sha256": "b" * 64})


if __name__ == "__main__":
    unittest.main(verbosity=2)

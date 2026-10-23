"""Fixed independent-teacher/result targets must survive selection and audit."""
from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
import torch

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_holdout_report as old_holdout
import test_residual_training as old_training


class FixedTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.training = importlib.import_module("residual_train")
        cls.report = importlib.import_module("compare_holdout")
        cls.shared = importlib.import_module("train_nnue")
        torch.set_num_threads(1)

    def model(self, correction_cp=0):
        model = self.shared.NNUE([128], qat=True)
        with torch.no_grad():
            for parameter in model.parameters():
                parameter.zero_()
            model.tail[0].bias.fill_(correction_cp * 2.25 / 400)
        return model

    def protocol(self, directory):
        path = Path(directory) / "protocol.json"
        record = {"schema_version": 1,
                  "target": {"kind": "teacher_probability_game_result_blend", "result_weight": 0.4,
                             "sigmoid_k": 2.25, "cp_scale": 400.0},
                  "training": {"epochs": 2, "selection_metric": "target_mse_combined", "include_initial": False}}
        path.write_text(json.dumps(record) + "\n")
        return path, record

    def test_audit_row_losses_use_fixed_result_target_and_retain_teacher_diagnostic(self):
        data = old_training.HeldOutMetricsTests().data(2)
        data["result_stm"][:] = 1
        try:
            rows = self.report.per_row_losses(self.model(), data, batch_size=1, result_weight=0.4)
        except TypeError as error:
            self.fail("Audit cannot evaluate a declared fixed result target: " + str(error))
        # Teacher probability .5, result 1 => fixed target .7. A neutral
        # prediction loses .04 against the blend and 0 against the teacher.
        for key in ("hce", "combined", "net_only"):
            np.testing.assert_allclose(rows[key], [0.04, 0.04], atol=2e-8, rtol=0)
            np.testing.assert_array_equal(rows["teacher_" + key], [0.0, 0.0])
        aggregate = self.training.evaluate(self.model(), data, 1, result_weight=0.4, fixed_target=True)
        self.assertAlmostEqual(float(rows["combined"].mean()), aggregate["target_mse_combined"], delta=1e-12)
        stats = self.report.cluster_bootstrap(rows["combined"], np.zeros(2), ["a", "b"], 100, 17)
        np.testing.assert_allclose(stats["ci95_abs"], [0.04, 0.04], atol=2e-8, rtol=0)

    def test_fixed_teacher_probability_does_not_round_through_an_unrelated_hce_offset(self):
        data = old_training.HeldOutMetricsTests().data(2)
        data["score"][:] = 100
        data["hce"][:] = [0, 2000000000]
        try:
            metrics = self.training.evaluate(self.model(), data, 2, result_weight=0.4, fixed_target=True)
        except TypeError as error:
            self.fail("Evaluator cannot choose the independent fixed target: " + str(error))
        # Both rows' target is float32(.6*sigmoid(.5625)+.4*.5),
        # .5822184681892395. Predictions are .5 and1. A canceled HCE
        # offset would instead turn the second row's teacher into .5.
        self.assertAlmostEqual(metrics["target_mse_combined"], 0.09065064241676524, delta=1e-8)
        rows = self.report.per_row_losses(self.model(), data, 2, result_weight=0.4)
        self.assertAlmostEqual(float(rows["combined"].mean()), metrics["target_mse_combined"], delta=1e-12)

    def test_one_fixed_target_selects_best_trained_epoch_even_when_teacher_prefers_another(self):
        with tempfile.TemporaryDirectory() as directory:
            data_dir, manifest = old_training.TrainingRunTests().prepare(directory)
            for name, result in (("train.npz", 0.0), ("validation.npz", 1.0)):
                with np.load(data_dir / name) as archive:
                    data = {key: archive[key] for key in archive.files}
                data["score"][:] = 0
                data["result_stm"][:] = result
                np.savez_compressed(data_dir / name, **data)
                manifest["files"][name]["sha256"] = self.training.sha256(data_dir / name)
            (data_dir / "manifest.json").write_text(json.dumps(manifest) + "\n")
            initial_stem = Path(directory) / "initial"
            self.shared.export_forge(self.model(150), initial_stem, 2.25, residual=True)
            protocol_path, _ = self.protocol(directory)
            manifest["protocol_sha256"] = self.training.sha256(protocol_path)
            (data_dir / "manifest.json").write_text(json.dumps(manifest) + "\n")
            run_dir = Path(directory) / "run"
            args = ["--data-dir", str(data_dir), "--run-dir", str(run_dir),
                    "--epochs", "2", "--batch-size", "4", "--threads", "1",
                    "--lr", "0.04", "--min-lr", "0.02", "--seed", "17",
                    "--initial-net", str(initial_stem.with_suffix(".inc")),
                    "--fixed-result-weight", "0.4", "--exclude-initial-from-selection",
                    "--protocol", str(protocol_path)]
            try:
                self.training.main(args)
            except SystemExit as error:
                self.fail("Fixed-target training CLI is unavailable: " + str(error))
            summary = json.loads((run_dir / "summary.json").read_text())
            epochs = summary["epochs"]
            self.assertEqual([row["result_weight"] for row in epochs], [0.4, 0.4])
            self.assertLess(summary["initial"]["target_mse_combined"], epochs[0]["target_mse_combined"])
            self.assertLess(epochs[0]["target_mse_combined"], epochs[1]["target_mse_combined"])
            self.assertGreater(epochs[0]["teacher_mse_combined"], epochs[1]["teacher_mse_combined"])
            self.assertEqual(summary["best"]["epoch"], 1)
            self.assertEqual(summary["best"]["stem"], "epoch-0001")
            self.assertEqual(summary["best"]["selection_metric"], "target_mse_combined")
            self.assertEqual(summary["best"]["selection_mse"], epochs[0]["target_mse_combined"])
            self.assertEqual(summary["config"]["selection_target"]["result_weight"], 0.4)
            self.assertEqual(summary["config"]["protocol"]["sha256"], self.training.sha256(protocol_path))
            metadata = json.loads((run_dir / "exports/epoch-0001.json").read_text())
            self.assertEqual(metadata["protocol"]["sha256"], self.training.sha256(protocol_path))

    def test_reference_blend_mismatch_is_rejected_even_if_teacher_metrics_match(self):
        fixture = old_holdout.RecipeIntegrityTests()
        fixture.report = self.report
        fixture.shared = self.shared
        with tempfile.TemporaryDirectory() as directory:
            data, manifest, _ = fixture.fixture(directory)
            reference, summary = fixture.reference_fixture(directory, data, manifest)
            summary["config"]["fixed_result_weight"] = 0.3
            summary["initial"].update(target_mse_hce=0.08, target_mse_combined=0.07)
            (reference / "summary.json").write_text(json.dumps(summary) + "\n")
            metrics = {"teacher_mse_hce": 0.1, "teacher_mse_combined": 0.09,
                       "target_mse_hce": 0.08, "target_mse_combined": 0.07}
            try:
                with self.assertRaisesRegex(ValueError, "target|blend|weight"):
                    self.report.verify_reference_holdout(data, manifest, metrics, reference,
                                                         {"sha256": "b" * 64}, result_weight=0.4)
            except TypeError as error:
                self.fail("Reference check cannot bind the declared result target: " + str(error))

    def test_mismatched_frozen_protocol_is_rejected_before_a_run_directory_is_created(self):
        for field, value in (("epochs", 3), ("selection_metric", "teacher_mse_combined"), ("include_initial", True)):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                data_dir, _ = old_training.TrainingRunTests().prepare(directory)
                path, protocol = self.protocol(directory)
                protocol["training"][field] = value
                path.write_text(json.dumps(protocol) + "\n")
                run_dir = Path(directory) / "must-not-exist"
                args = ["--data-dir", str(data_dir), "--run-dir", str(run_dir), "--epochs", "2",
                        "--threads", "1", "--fixed-result-weight", "0.4", "--exclude-initial-from-selection",
                        "--protocol", str(path)]
                try:
                    with self.assertRaisesRegex(ValueError, "protocol|Protocol"):
                        self.training.main(args)
                except SystemExit as error:
                    self.fail("Frozen protocol CLI is unavailable: " + str(error))
                self.assertFalse(run_dir.exists())

    def test_prepared_data_must_bind_the_passed_protocol_before_any_model_artifact(self):
        for binding in (None, "e" * 64):
            with self.subTest(binding=binding), tempfile.TemporaryDirectory() as directory:
                data_dir, manifest = old_training.TrainingRunTests().prepare(directory)
                path, _ = self.protocol(directory)
                if binding is not None:
                    manifest["protocol_sha256"] = binding
                (data_dir / "manifest.json").write_text(json.dumps(manifest) + "\n")
                run_dir = Path(directory) / "must-not-exist"
                args = ["--data-dir", str(data_dir), "--run-dir", str(run_dir), "--epochs", "2",
                        "--threads", "1", "--fixed-result-weight", "0.4", "--exclude-initial-from-selection",
                        "--protocol", str(path), "--baseline-only"]
                with self.assertRaisesRegex(ValueError, "protocol|Protocol"):
                    self.training.main(args)
                self.assertFalse(run_dir.exists())

    def test_reference_protocol_mismatch_cannot_reuse_equal_blend_metrics(self):
        fixture = old_holdout.RecipeIntegrityTests()
        fixture.report, fixture.shared = self.report, self.shared
        with tempfile.TemporaryDirectory() as directory:
            data, manifest, _ = fixture.fixture(directory)
            reference, summary = fixture.reference_fixture(directory, data, manifest)
            summary["config"].update(fixed_result_weight=0.4, protocol={"sha256": "c" * 64})
            summary["initial"].update(target_mse_hce=0.08, target_mse_combined=0.07)
            (reference / "summary.json").write_text(json.dumps(summary) + "\n")
            metrics = {"teacher_mse_hce": 0.1, "teacher_mse_combined": 0.09,
                       "target_mse_hce": 0.08, "target_mse_combined": 0.07}
            try:
                with self.assertRaisesRegex(ValueError, "protocol|Protocol"):
                    self.report.verify_reference_holdout(data, manifest, metrics, reference,
                                                         {"sha256": "b" * 64}, result_weight=0.4,
                                                         protocol={"sha256": "d" * 64})
            except TypeError as error:
                self.fail("Reference check cannot bind the frozen protocol: " + str(error))

    def test_complete_audit_report_bootstraps_the_blend_and_keeps_pure_teacher_separate(self):
        fixture = old_holdout.RecipeIntegrityTests()
        fixture.report, fixture.shared = self.report, self.shared
        with tempfile.TemporaryDirectory() as directory:
            data, manifest, _ = fixture.fixture(directory)
            directory = Path(directory)
            source = directory / "games.jsonl"
            records = [json.loads(line) for line in source.read_text().splitlines()]
            for row in records:
                row["score_cp_stm"] = 0
                row["result_white"] = 1.0 if row["fen"].split()[1] == "w" else 0.0
            source.write_text("".join(json.dumps(row) + "\n" for row in records))
            manifest["sources"][0]["sha256"] = self.training.sha256(source)
            data["score"][:] = 0
            data["hce"][:] = 0
            data["result_stm"][:] = 1
            manifest.update(schema_version=1, hidden_size=128, score_pov="side_to_move", result_pov="side_to_move")
            manifest["split"].update(policy="game_hash", seed=17, legacy_training_game_ids_unknown=False)
            manifest["filters"].update(no_in_check=True, tactical_bestmove_filter=True)
            for name in ("train.npz", "validation.npz"):
                np.savez_compressed(directory / name, **data)
                manifest["files"][name] = {"rows": 3, "sha256": self.training.sha256(directory / name)}
            (directory / "manifest.json").write_text(json.dumps(manifest) + "\n")
            protocol_path, _ = self.protocol(directory)
            manifest["protocol_sha256"] = self.training.sha256(protocol_path)
            (directory / "manifest.json").write_text(json.dumps(manifest) + "\n")
            self.shared.export_forge(self.model(), directory / "shipped", 2.25, residual=True)
            self.shared.export_forge(self.model(150), directory / "candidate", 2.25, residual=True)
            out = directory / "audit"
            args = ["--data-dir", str(directory), "--shipped-net", str(directory / "shipped.inc"),
                    "--candidate-net", str(directory / "candidate.inc"), "--out", str(out),
                    "--result-weight", "0.4", "--protocol", str(protocol_path), "--bootstrap-draws", "100"]
            try:
                self.report.main(args)
            except SystemExit as error:
                self.fail("Fixed-target audit CLI is unavailable: " + str(error))
            metrics = json.loads((out / "metrics.json").read_text())
            self.assertAlmostEqual(metrics["loss_mse"]["shipped_hce_plus_net"], 0.04, delta=2e-8)
            self.assertGreater(metrics["comparisons"]["shipped_vs_candidate"]["ci95_abs"][0], 0.039)
            self.assertEqual(metrics["teacher_loss_mse"]["shipped_hce_plus_net"], 0.0)
            self.assertGreater(metrics["teacher_loss_mse"]["candidate_hce_plus_net"], 0.039)
            self.assertEqual(metrics["target"]["result_weight"], 0.4)
            self.assertEqual(metrics["protocol"]["sha256"], self.training.sha256(protocol_path))
            with np.load(out / "per-row-losses.npz") as losses:
                np.testing.assert_array_equal(losses["teacher_loss_shipped_combined"], np.zeros(3))
                np.testing.assert_allclose(losses["loss_shipped_combined"], np.full(3, 0.04), atol=2e-8, rtol=0)
            # A different prepared-data protocol must stop before publishing a
            # fresh audit, even when all arrays and network inputs are equal.
            manifest["protocol_sha256"] = "e" * 64
            (directory / "manifest.json").write_text(json.dumps(manifest) + "\n")
            args[args.index("--out") + 1] = str(directory / "mismatched-audit")
            with self.assertRaisesRegex(ValueError, "protocol|Protocol"):
                self.report.main(args)
            self.assertFalse((directory / "mismatched-audit").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)

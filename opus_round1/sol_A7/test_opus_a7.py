#!/usr/bin/env python3
"""Tests for the A7 tools (no PC data needed; fixtures are synthetic or copied numbers from real logs).

usage: python -I -B test_opus_a7.py [-v]   (run from any directory; imports the tools next to this file)
"""
from __future__ import annotations

import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dry = load("opus_a7_dryparse")
stats = load("opus_a7_curve_stats")

FAKE_TRAINER = '''"""fake trainer"""
import argparse
K_DEFAULT = 2.25
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--batch-size", type=int, default=4096)
    ap.add_argument("--sigmoid-k", type=float, default=K_DEFAULT)
    a = ap.parse_args()
    return 0
'''


class DryParse(unittest.TestCase):
    def write(self, text):
        d = Path(tempfile.mkdtemp())  # under TMP (the job scratch); never deleted
        p = d / "opus_nnue_smoke_fake.py"
        p.write_bytes(text.encode("utf-8"))  # exact bytes (write_text would add CRLF on Windows)
        return p, hashlib.md5(text.encode()).hexdigest()

    def test_parser_extracted_and_used(self):
        p, md5 = self.write(FAKE_TRAINER)
        ap, n = dry.load_parser(p, md5)
        self.assertEqual(n, 3)
        ns, err = dry.parse(ap, ["--epochs", "64"])
        self.assertEqual((ns["epochs"], ns["batch_size"], ns["sigmoid_k"]), (64, 4096, 2.25))
        self.assertEqual(err, "")

    def test_rejects_md5_mismatch(self):
        p, _ = self.write(FAKE_TRAINER)
        with self.assertRaises(SystemExit):
            dry.load_parser(p, "0" * 32)

    def test_rejects_side_effect_before_parse(self):
        bad = FAKE_TRAINER.replace('    ap.add_argument("--epochs"', '    open("x", "w")\n    ap.add_argument("--epochs"')
        p, md5 = self.write(bad)
        with self.assertRaises(SystemExit):
            dry.load_parser(p, md5)

    def test_unknown_and_bad_type_rejected(self):
        p, md5 = self.write(FAKE_TRAINER)
        ap, _ = dry.load_parser(p, md5)
        self.assertIsNone(dry.parse(ap, ["--epoch-positions", "5"])[0])
        self.assertIsNone(dry.parse(ap, ["--epochs", "6.4e1"])[0])

    def test_schedule_matches_real_f070_log(self):
        # f070 log: "train: 221,913,894 positions", "steps/epoch=27,089 total=1,300,272 batch=8192",
        # "Finished: 10,651,828,224 positions"
        ns = {"max_train": 0, "batch_size": 8192, "steps_per_epoch": 0, "epochs": 48, "warmup_steps": 300,
              "lr": 7.07e-4, "min_lr_frac": 0.01}
        s = dry.schedule(ns, 221_913_894, 1.0)
        self.assertEqual((s["steps_per_epoch"], s["total_steps"], s["positions_processed"]),
                         (27_089, 1_300_272, 10_651_828_224))

    def test_schedule_max_train_prefix(self):
        ns = {"max_train": 240_000_000, "batch_size": 8192, "steps_per_epoch": 0, "epochs": 96, "warmup_steps": 300,
              "lr": 7.07e-4, "min_lr_frac": 0.01}
        s = dry.schedule(ns, 241_913_894, 1.0)
        self.assertEqual((s["train_positions"], s["steps_per_epoch"], s["total_steps"]), (240_000_000, 29_296, 2_812_416))
        self.assertAlmostEqual(s["gpu_hours_at_1.22M"], 23_039_311_872 / 1.22e6 / 3600)
        self.assertAlmostEqual(s["lr_floor"], 7.07e-6)
        # less data than max-train: the trainer takes what exists
        self.assertEqual(dry.schedule(ns, 200_000_000, 1.0)["train_positions"], 200_000_000)


class Stats(unittest.TestCase):
    def test_pooled_sd(self):
        spread = [{"runs": "3", "b06_sd": "2e-6"}, {"runs": "2", "b06_sd": "4e-6"}, {"runs": "1", "b06_sd": ""}]
        sd, groups, dof = stats.pooled_seed_sd(spread)
        self.assertEqual((groups, dof), (2, 3))
        self.assertAlmostEqual(sd, ((2 * 4e-12 + 1 * 16e-12) / 3) ** 0.5)

    def test_fit_recovers_known_slopes(self):
        rows = []
        for i, (n, e) in enumerate([(1e8, 16), (2e8, 16), (1e8, 48), (2e8, 48), (4e8, 32), (3e8, 24), (1.5e8, 20)]):
            import math
            b = 0.0143 - 1.6e-4 * math.log2(n / 1e8) - 3.0e-5 * math.log2(e / 48)
            rows.append({"b06": str(b), "train_positions": str(n), "epochs": str(e), "lr": "7.07e-4"})
        f = stats.fit_with_ci(rows, with_lr=False, reps=200, seed=1)
        self.assertAlmostEqual(f["coef"]["per_doubling_data"]["est"], -1.6e-4, places=9)
        self.assertAlmostEqual(f["coef"]["per_doubling_epochs"]["est"], -3.0e-5, places=9)
        self.assertAlmostEqual(f["pred_e96_minus_e48"]["est"], -3.0e-5, places=9)

    def test_plateau(self):
        finals = {"r": {"shape": "256", "blend-end": "0.6", "batch-size": "8192", "run": "r", "b06": "0.0143",
                        "train_positions": "1e8", "epochs": "16", "where": "r.log:9"}}
        # 16 epochs; epoch 14 is 1.0e-5 from the final value (between one and two sds), epoch 15 is 4e-6 from it
        b = [0.0150 - 0.0001 * k for k in range(13)] + [0.013711, 0.013705, 0.013701]
        curves = [{"run": "r", "epoch": str(k + 1), "b06": str(v), "where": f"r.log:{k}"} for k, v in enumerate(b)]
        p = stats.plateau_stats(curves, finals, 7.1e-6)
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0]["plateau_epoch"], 15)
        self.assertEqual(p[0]["best_subset_epoch"], 16)


if __name__ == "__main__":
    unittest.main()

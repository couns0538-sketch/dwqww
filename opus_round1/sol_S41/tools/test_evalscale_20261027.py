#!/usr/bin/env python3
"""Unit tests for evalscale_20261027.py (synthetic data only; no PC files).

  python -I -B test_evalscale_20261027.py        (EVALSCALE_TOOL=<path> tests another copy, used by the mutation check)
"""
from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

import numpy as np

TOOL = Path(os.environ.get("EVALSCALE_TOOL", Path(__file__).resolve().parent / "evalscale_20261027.py"))
spec = importlib.util.spec_from_file_location("evalscale", TOOL)
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)


def synthetic(n: int = 4000, seed: int = 1) -> np.ndarray:
    rng = np.random.default_rng(seed)
    # Laplace-like spread with a few large values, integer centipawns like the engine.
    return np.round(rng.laplace(0, 250, size=n)).astype(np.float64)


def dump_text(hce: np.ndarray, net: np.ndarray, in_check: np.ndarray | None = None, bad: set[int] | None = None) -> str:
    lines = []
    for i, (h, n_) in enumerate(zip(hce, net)):
        if bad and i in bad:
            lines.append(f"{i} BAD")
            continue
        c = int(in_check[i]) if in_check is not None else 0
        lines.append(f"{i} w {c} {int(h)} {int(n_)} {int(h + n_)}")
    return "\n".join(lines) + "\n"


class Estimators(unittest.TestCase):
    def test_identity_is_exactly_one_for_every_estimator(self):
        x = synthetic()
        x = x[x != 0]
        y = x.copy()
        self.assertEqual(E.lad(x, y), 1.0)
        self.assertEqual(E.lad(y, x), 1.0)
        self.assertEqual(E.sym(x, y), 1.0)
        self.assertEqual(E.theil_sen(x, y)[0], 1.0)
        self.assertEqual(E.huber(x, y), 1.0)
        self.assertEqual(E.ols(x, y), 1.0)
        for v in E.q_ratios(x, y).values():
            self.assertEqual(v, 1.0)
        lo, hi = E.bootstrap_sym(x, y, reps=50)
        self.assertEqual((lo, hi), (1.0, 1.0))

    def test_exact_scale_is_recovered(self):
        x = synthetic()
        x = x[x != 0]
        y = 1.25 * x
        self.assertAlmostEqual(E.lad(x, y), 1.25, places=12)
        self.assertAlmostEqual(E.sym(x, y), 1.25, places=12)
        self.assertAlmostEqual(E.theil_sen(x, y)[0], 1.25, places=12)
        self.assertAlmostEqual(E.huber(x, y), 1.25, places=12)

    def test_robust_to_gross_outliers_where_ols_is_not(self):
        rng = np.random.default_rng(7)
        x = synthetic(6000, 3)
        x = x[x != 0]
        y = 1.10 * x + rng.normal(0, 15, size=len(x))
        bad = rng.choice(len(x), size=len(x) // 10, replace=False)
        y[bad] = -3.0 * x[bad]            # 10% sign-flipped garbage
        self.assertLess(abs(E.sym(x, y) - 1.10), 0.03)
        self.assertLess(abs(E.theil_sen(x, y)[0] - 1.10), 0.03)
        self.assertLess(abs(E.huber(x, y) - 1.10), 0.03)
        self.assertGreater(abs(E.ols(x, y) - 1.10), 0.3)

    def test_q_ratios_are_cand_over_ref(self):
        x = synthetic()
        y = 1.25 * x
        for k, v in E.q_ratios(x, y).items():
            self.assertAlmostEqual(v, 1.25, places=9, msg=k)

    def test_sym_is_symmetric(self):
        rng = np.random.default_rng(11)
        x = synthetic(3000, 5)
        x = x[x != 0]
        y = 0.9 * x + rng.normal(0, 40, size=len(x))
        y[y == 0] = 1.0
        self.assertAlmostEqual(E.sym(x, y) * E.sym(y, x), 1.0, places=12)

    def test_weighted_median(self):
        self.assertEqual(E.weighted_median(np.array([1.0, 2.0, 3.0]), np.array([1.0, 1.0, 1.0])), 2.0)
        self.assertEqual(E.weighted_median(np.array([1.0, 2.0, 3.0]), np.array([1.0, 1.0, 10.0])), 3.0)
        self.assertEqual(E.weighted_median(np.array([5.0, 1.0]), np.array([1.0, 3.0])), 1.0)

    def test_lad_is_weighted_median_of_ratios(self):
        x = np.array([1.0, 2.0, -4.0, 10.0])
        y = np.array([2.0, 2.0, -8.0, 5.0])
        # ratios 2, 1, 2, 0.5 with weights 1, 2, 4, 10 -> sorted 0.5(10) 1(2) 2(1) 2(4): half of 17 = 8.5 -> 0.5
        self.assertEqual(E.lad(x, y), 0.5)
        brute = min(np.arange(0, 3, 0.0005), key=lambda b: float(np.abs(y - b * x).sum()))
        self.assertAlmostEqual(brute, 0.5, places=3)


class EngineArithmetic(unittest.TestCase):
    def test_scale_engine_matches_cpp_apply(self):
        v = np.arange(-40000, 40001, 3, dtype=np.float64)
        for pct in range(50, 151):
            got = E.scale_engine(v, pct)
            mag = (np.abs(v).astype(np.int64) * pct) // 100
            want = np.where(v < 0, -mag, mag).astype(np.float64)
            self.assertTrue(np.array_equal(got, want), pct)
        self.assertTrue(np.array_equal(E.scale_engine(v, 100), v))
        self.assertEqual(E.scale_engine(np.array([-150.0, 150.0]), 99).tolist(), [-148.0, 148.0])


class CompareAndDump(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name: str, text: str) -> Path:
        p = self.dir / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_same_dump_gives_netscale_100(self):
        rng = np.random.default_rng(2)
        hce = synthetic(2000, 9)
        net = np.round(rng.normal(0, 60, size=2000))
        d = E.read_dump(self.write("a.dump", dump_text(hce, net)))
        r = E.compare(d, d, boot=False)
        self.assertEqual(r["sym"], 1.0)
        self.assertEqual(r["theil_sen"], 1.0)
        self.assertEqual(r["netscale_percent"], 100)
        self.assertEqual(r["mapped"]["sym"], 1.0)
        self.assertAlmostEqual(r["residual_only_scale_percent_diag"], 100.0, places=6)

    def test_scaled_dump_proposes_the_inverse_and_maps_back(self):
        rng = np.random.default_rng(4)
        hce = synthetic(3000, 12)
        net = np.round(rng.normal(0, 60, size=3000))
        ref = E.read_dump(self.write("r.dump", dump_text(hce, net)))
        tot = hce + net
        cand_tot = np.round(1.25 * tot)
        cand = E.read_dump(self.write("c.dump", dump_text(hce, cand_tot - hce)))
        r = E.compare(ref, cand, boot=False)
        self.assertEqual(r["netscale_percent"], 80)
        self.assertLess(abs(r["mapped"]["sym"] - 1.0), 0.01)

    def test_bad_and_in_check_lines_are_excluded(self):
        hce = synthetic(500, 21)
        net = np.zeros(500)
        chk = np.zeros(500, dtype=bool)
        chk[:50] = True
        d = E.read_dump(self.write("b.dump", dump_text(hce, net, chk, bad={60, 61})))
        self.assertEqual(int(d["valid"].sum()), 498)
        r = E.compare(d, d, boot=False)
        self.assertEqual(r["positions_valid_not_in_check"], 448)

    def test_read_dump_requires_contiguous_indices(self):
        p = self.write("x.dump", "0 w 0 1 1 2\n2 w 0 1 1 2\n")
        with self.assertRaises(SystemExit):
            E.read_dump(p)


class Sampling(unittest.TestCase):
    def test_offsets_are_deterministic_and_whole_lines(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "forge_selfplay_999.txt"
            rows = [f"8/8/8/8/8/8/{i % 8}K6/k7 w - - 0 {i + 1} | {i} | 0.5" for i in range(5000)]
            # normalise the synthetic FENs into 6 fields (rank text is irrelevant for the sampler)
            rows = [r.replace(f"/{i % 8}K6/", "/1K6/") for i, r in enumerate(rows)]
            p.write_text("\n".join(rows) + "\n", encoding="utf-8")
            a = E.sample_selfplay(p, 100)
            b = E.sample_selfplay(p, 100)
            self.assertEqual(a, b)
            self.assertEqual(len(a), 100)
            self.assertEqual(a[0][0], 0)
            data = p.read_bytes()
            for off, fen in a:
                self.assertTrue(off == 0 or data[off - 1:off] == b"\n")
                self.assertEqual(len(fen.split()), 6)
            self.assertEqual(len({off for off, _ in a}), 100)

    def test_epd_to_fen(self):
        self.assertEqual(E.epd_to_fen('2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - bm Qg6; id "WAC.001";'),
                         "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1")
        self.assertIsNone(E.epd_to_fen("8/8 w"))

    def test_refuses_protected_outputs(self):
        for bad in (r"D:\grok-pc-data\forge_push\x.json", r"D:\grok-pc-data\selfplay_out\x", r"F:\forge_nnue_train\y",
                    r"C:\Users\Administrator\grok-pc\z"):
            with self.assertRaises(SystemExit):
                E.refuse_protected(Path(bad), "test")
        E.refuse_protected(Path(tempfile.gettempdir()) / "ok.json", "test")


if __name__ == "__main__":
    unittest.main(verbosity=2)

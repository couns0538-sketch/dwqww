#!/usr/bin/env python3
"""Tests for opus_sa6_plan_check.py (synthetic catalogs and plans; no PC data)."""
from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pc", HERE / "opus_sa6_plan_check.py")
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)

CATALOG = {"parameters": [
    {"name": "RfpMargin", "default": 72, "minimum": 10, "maximum": 300},
    {"name": "LmrNoisyBase", "default": 10, "minimum": 0, "maximum": 300},
    {"name": "RfpDepth", "default": 8, "minimum": 0, "maximum": 15},
]}
PLAN = {
    "throughput": {"measured_sec_per_game_per_slot_10+0.1": 29, "engine_share_of_base": 0.8, "moves_per_side": 65},
    "spsa_schedule": {"r_end": 0.002, "alpha": 0.602, "gamma": 0.101, "A_frac": 0.1},
    "stages": [{"name": "A", "tc": "8+0.08", "concurrency": 8, "pairs_per_iteration": 4, "games": 24000,
                "params": {"RfpMargin": 6, "LmrNoisyBase": 8}}],
    "excluded": {"depth": ["RfpDepth"]},
    "validation": {"stc_gate": {"tc": "10+0.1", "cap_games": 1500, "concurrency": 8},
                   "ltc_confirm": {"tc": "40+0.4", "cap_games": 1500, "concurrency": 8}},
}


class PlanCheck(unittest.TestCase):
    def test_valid_plan_passes_with_numbers(self):
        r = pc.check(PLAN, CATALOG)
        self.assertTrue(r["ok"], r["errors"])
        s = r["stages"][0]
        self.assertEqual(s["iterations"], 3000)
        self.assertAlmostEqual(s["sec_per_game_per_slot"], 23.2)
        self.assertAlmostEqual(s["qa_slot_hours"], 24000 * 23.2 / 8 / 3600)
        row = {x["name"]: x for x in s["rows"]}["RfpMargin"]
        self.assertAlmostEqual(row["c_1"], 6 * 3000 ** 0.101)
        self.assertAlmostEqual(row["a"], 0.002 * 36 * (300 + 3000) ** 0.602)
        self.assertTrue(any("LmrNoisyBase" in w for w in r["warnings"]))  # 10 - 13.5 < 0

    def test_calibration_matches_measured_gates(self):
        self.assertAlmostEqual(pc.sec_per_game("10+0.1", 0.8, 65), 29.0)
        self.assertAlmostEqual(pc.sec_per_game("40+0.4", 0.8, 65), 116.0)

    def test_unassigned_parameter_fails(self):
        p = copy.deepcopy(PLAN)
        p["excluded"] = {}
        r = pc.check(p, CATALOG)
        self.assertFalse(r["ok"])
        self.assertTrue(any("not assigned" in e for e in r["errors"]))

    def test_duplicate_and_unknown_fail(self):
        p = copy.deepcopy(PLAN)
        p["excluded"]["depth"].append("RfpMargin")
        p["excluded"]["x"] = ["NoSuchParam"]
        r = pc.check(p, CATALOG)
        self.assertTrue(any("in both" in e for e in r["errors"]))
        self.assertTrue(any("unknown" in e for e in r["errors"]))

    def test_small_range_and_bad_c_end_fail(self):
        p = copy.deepcopy(PLAN)
        p["stages"][0]["params"] = {"RfpMargin": 0, "LmrNoisyBase": 31, "RfpDepth": 1}
        p["excluded"] = {}
        r = pc.check(p, CATALOG)
        errs = " ".join(r["errors"])
        self.assertIn("RfpMargin: c_end 0", errs)
        self.assertIn("LmrNoisyBase: c_end 31", errs)
        self.assertIn("RfpDepth: range 15", errs)

    def test_default_out_of_range_fails(self):
        cat = copy.deepcopy(CATALOG)
        cat["parameters"][0]["default"] = 400
        r = pc.check(PLAN, cat)
        self.assertTrue(any("outside" in e for e in r["errors"]))


if __name__ == "__main__":
    unittest.main()

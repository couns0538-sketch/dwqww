#!/usr/bin/env python3
"""Tests for opus_sc4_widen_inc.py (synthetic nets; no PC data)."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("w", HERE / "opus_sc4_widen_inc.py")
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


def net(inputs, h):
    return {"NnueW1": [(f * 7 + j * 3) % 41 - 20 for f in range(inputs) for j in range(h)],
            "NnueB1": [j - 2 for j in range(h)],
            "NnueW2": [100 + j for j in range(2 * h)]}


class Widen(unittest.TestCase):
    def test_layout_and_zero_padding(self):
        a = net(3, 4)
        b = w.widen(a, 4, 6, inputs=3)
        self.assertEqual(len(b["NnueW1"]), 18)
        for f in range(3):  # each feature row keeps its 4 values, then 2 zeros
            self.assertEqual(b["NnueW1"][f * 6:f * 6 + 4], a["NnueW1"][f * 4:(f + 1) * 4])
            self.assertEqual(b["NnueW1"][f * 6 + 4:(f + 1) * 6], [0, 0])
        self.assertEqual(b["NnueB1"], a["NnueB1"] + [0, 0])
        # W2 = [stm half | opponent half]; each half padded separately
        self.assertEqual(b["NnueW2"], a["NnueW2"][:4] + [0, 0] + a["NnueW2"][4:] + [0, 0])

    def test_function_preserving_forward(self):
        # a float forward in the engine's form (SCReLU of both perspectives, W2 halves) gives the same output
        def forward(n, h, active_stm, active_opp):
            acc = []
            for active in (active_stm, active_opp):
                v = list(n["NnueB1"])
                for f in active:
                    for j in range(h):
                        v[j] += n["NnueW1"][f * h + j]
                acc.append(v)
            s = 0.0
            for j in range(h):
                a = min(max(acc[0][j] / 64.0, 0.0), 1.0)
                b = min(max(acc[1][j] / 64.0, 0.0), 1.0)
                s += a * a * n["NnueW2"][j] + b * b * n["NnueW2"][h + j]
            return s
        a = net(5, 4)
        b = w.widen(a, 4, 12, inputs=5)
        self.assertEqual(forward(a, 4, [0, 2], [1, 4]), forward(b, 12, [0, 2], [1, 4]))

    def test_parse_rejects_count_mismatch(self):
        bad = "static const std::int16_t NnueW1[3] = {\n 1, 2, \n};\nstatic const std::int16_t NnueB1[1] = {1,};\nstatic const std::int16_t NnueW2[2] = {1, 2,};"
        with self.assertRaises(ValueError):
            w.parse(bad)

    def test_rejects_narrowing(self):
        with self.assertRaises(ValueError):
            w.widen(net(2, 4), 4, 2, inputs=2)

    def test_format_round_trip(self):
        a = net(3, 4)
        text = "\n".join(w.fmt(k, a[k]) for k in ("NnueW1", "NnueB1", "NnueW2"))
        self.assertEqual(w.parse(text), a)


if __name__ == "__main__":
    unittest.main()

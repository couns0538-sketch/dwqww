#!/usr/bin/env python3
"""Unit tests for jobA_cause.py (pure, no git, no engine). Run: python -I test_jobA_cause.py
JOBA_CAUSE_PATH=<file> loads a different copy of the module (used by the planted-bug check)."""
import importlib.util
import os
import sys
import unittest
from pathlib import Path

_PATH = os.environ.get("JOBA_CAUSE_PATH", str(Path(__file__).with_name("jobA_cause.py")))
_spec = importlib.util.spec_from_file_location("jobA_cause", _PATH)
jc = importlib.util.module_from_spec(_spec)
sys.modules["jobA_cause"] = jc
_spec.loader.exec_module(jc)

B_LOG = (
    "info string NnueExactInt32 active\n"
    "info string bench depth 13 nodes 745494 time 1604 nps 464771\n"
    "info string NnueExactInt32 stats refreshes 8 updates 571275 evaluations 468251 "
    "int32_refreshes 8 int32_updates 571275 refresh_share_ppm 14\n"
)

DISASM = """\
0000000000001000 <forge::nnue::(anonymous namespace)::kernel()>:
    1000:\tvmovups (%rax),%zmm0
    1006:\tvpmovsxwd (%r9,%rax,1),%ymm2
    100c:\tincq   %fs:0xffffffffffffff48
    1015:\tvfmadd231ps %xmm1,%xmm2,%xmm3
    101a:\tcall   2000 <forge::nnue::other()>

0000000000002000 <forge::nnue::other()>:
    2000:\tvcvtdq2ps (%rcx,%rax,1),%ymm0
    2005:\tret
"""

LOOP = [
    (0x10, "mov    0x20(%rcx),%edx"),
    (0x14, "test   %edx,%edx"),
    (0x16, "jle    0x30"),
    (0x18, "vpaddd %ymm0,%ymm2,%ymm1"),
    (0x1c, "jne    0x22"),
    (0x1e, "vpsubd %ymm2,%ymm0,%ymm1"),
    (0x22, "jmp    0x30"),
    (0x24, "nopl   (%rax)"),
    (0x30, "add    $0x10,%rax"),
    (0x34, "jne    0x10"),
]


class ParseTests(unittest.TestCase):
    def test_bench_and_stats(self):
        self.assertEqual(jc.parse_bench(B_LOG), {"depth": 13, "nodes": 745494, "time_ms": 1604, "nps": 464771})
        self.assertEqual(jc.parse_stats(B_LOG), {"refreshes": 8, "updates": 571275, "evaluations": 468251,
                                                 "int32_refreshes": 8, "int32_updates": 571275})

    def test_missing_lines(self):
        self.assertIsNone(jc.parse_bench("info string nothing here\n"))
        self.assertIsNone(jc.parse_stats("info string bench depth 13 nodes 1 time 1 nps 1\n"))

    def test_bom_is_stripped(self):
        self.assertEqual(jc.as_text("\ufeffabc".encode("utf-8")), "abc")


class StatsTests(unittest.TestCase):
    def test_abba_ratio_pairing(self):
        # ABBA block = [A1, B1, B2, A2]; ratios are B1/A1 and B2/A2.
        self.assertEqual(jc.abba_ratios([[100, 90, 80, 50]]), [0.9, 1.6])

    def test_bootstrap_is_deterministic_and_brackets_median(self):
        quads = [[100, 95 + i % 3, 96 - i % 2, 101] for i in range(10)]
        a = jc.block_bootstrap_median_ci(quads, n_boot=500, seed=7)
        b = jc.block_bootstrap_median_ci(quads, n_boot=500, seed=7)
        self.assertEqual(a, b)
        med = jc.summarize(quads)["median"]
        self.assertLessEqual(a[0], med)
        self.assertGreaterEqual(a[1], med)

    def test_sign_test(self):
        self.assertAlmostEqual(jc.binom_two_sided(15, 20), 0.04138946533203125, places=12)
        self.assertEqual(jc.binom_two_sided(10, 20), 1.0)
        self.assertAlmostEqual(jc.binom_two_sided(0, 5), 0.0625, places=12)

    def test_summary_counts(self):
        s = jc.summarize([[100, 90, 110, 100], [100, 80, 95, 100]])
        self.assertEqual(s["n_ratios"], 4)
        self.assertEqual(s["below_1"], 3)
        self.assertAlmostEqual(s["median"], 0.925)


class DisassemblyTests(unittest.TestCase):
    def test_scan_counts(self):
        funcs = jc.scan_disassembly(DISASM)
        k = funcs["forge::nnue::(anonymous namespace)::kernel()"]
        self.assertEqual(k["insns"], 5)
        self.assertEqual((k["zmm"], k["ymm"], k["xmm"]), (1, 1, 1))
        self.assertEqual((k["vpmovsxwd"], k["fma"], k["tls_counter_inc"], k["call"]), (1, 1, 1, 1))
        self.assertEqual(funcs["forge::nnue::other()"]["vcvtdq2ps"], 1)

    def test_listing_strips_symbols(self):
        rows = jc.listing(DISASM, 0x1000, 0x2000)
        self.assertEqual(rows[-1], (0x101A, "call   2000"))

    def test_check_path(self):
        # remove (fall through to vpsubd) then loop back
        self.assertTrue(jc.check_path(LOOP, [0x10, 0x14, 0x16, 0x18, 0x1C, 0x1E, 0x22, 0x30, 0x34]))
        # add (jne taken, skips vpsubd)
        self.assertTrue(jc.check_path(LOOP, [0x10, 0x14, 0x16, 0x18, 0x1C, 0x22, 0x30, 0x34]))
        # an unconditional jmp cannot fall through into the padding
        self.assertFalse(jc.check_path(LOOP, [0x10, 0x14, 0x16, 0x18, 0x1C, 0x22, 0x24, 0x30, 0x34]))
        # a straight-line instruction cannot jump
        self.assertFalse(jc.check_path(LOOP, [0x10, 0x16, 0x18, 0x1C, 0x22, 0x30, 0x34]))
        # unknown address
        self.assertFalse(jc.check_path(LOOP, [0x10, 0x99], closed=False))

    def test_padding(self):
        self.assertTrue(jc.is_padding("data16 cs nopw 0x0(%rax,%rax,1)"))
        self.assertFalse(jc.is_padding("vmovdqa %ymm0,(%rsi,%rax,2)"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

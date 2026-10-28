#!/usr/bin/env python3
"""Unit tests for callgrind_callers.py (synthetic profiles; no valgrind or binutils needed).
Temporary files go to a new directory under $TMPDIR and are left in place (nothing is removed).
usage: TMPDIR=<scratch> python -I -B test_callgrind_callers.py"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import callgrind_callers as cc  # noqa: E402

PROFILE = """# callgrind format
version: 1
creator: callgrind-3.22.0
positions: instr line
events: Ir
summary: 1000

ob=/w/build/forge
fl=/w/src/search.cpp
fn=forge::Worker::search(forge::Board&, forge::SearchStack*, int, int, int, bool)'2
0x401000 10 5
cob=/lib/x86_64-linux-gnu/libc.so.6
cfi=./string/memset-vec-unaligned-erms.S
cfn=__memset_avx2_unaligned_erms
calls=3 0x7000 0
0x401010 11 300
cfn=forge::Board::is_legal(forge::Move const&) const
calls=2 0x402000 5
0x401020 12 40
cob=/lib/x86_64-linux-gnu/libc.so.6
cfn=__memset_avx2_unaligned_erms
calls=1 0x7000 0
0x401010 11 60
fn=forge::Worker::qsearch(forge::Board&, forge::SearchStack*, int, int)
0x401100 20 7
cob=/lib/x86_64-linux-gnu/libc.so.6
cfn=__memset_avx2_unaligned_erms
calls=1 0x7000 0
0x401110 21 100
fn=forge::Board::is_legal(forge::Move const&) const
0x402000 5 30
ob=/lib/x86_64-linux-gnu/libc.so.6
fn=__memset_avx2_unaligned_erms
0x7000 0 460
totals: 1000
"""


WORK = tempfile.mkdtemp(prefix="test_callgrind_callers_")


class ParseTests(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(WORK, f"profile_{self.id().split('.')[-1]}.out")
        with open(self.path, "w") as handle:
            handle.write(PROFILE)

    def test_calls_and_totals(self):
        total, calls, fn_min = cc.parse(self.path, re.compile(r"(^|_)memset"))
        self.assertEqual(total, 1000)
        self.assertEqual(len(calls), 3)  # the is_legal call is not a memset call
        by_site = {}
        for c in calls:
            by_site.setdefault(c["site"], []).append(c)
        self.assertEqual(sorted(by_site), [0x401010, 0x401110])
        self.assertEqual(sum(c["count"] for c in by_site[0x401010]), 4)
        self.assertEqual(sum(c["cost"] for c in by_site[0x401010]), 360)
        self.assertEqual(by_site[0x401110][0]["cost"], 100)
        self.assertEqual(by_site[0x401110][0]["callee_obj"], "/lib/x86_64-linux-gnu/libc.so.6")
        # lowest address per function (the entry), used for the load bias
        self.assertEqual(fn_min[("/w/build/forge", "forge::Worker::qsearch(forge::Board&, forge::SearchStack*, int, int)")],
                         0x401100)

    def test_cost_line_after_unrelated_call_is_not_a_memset_site(self):
        _, calls, _ = cc.parse(self.path, re.compile(r"(^|_)memset"))
        self.assertNotIn(0x401020, [c["site"] for c in calls])

    def test_main_json(self):
        out = os.path.join(WORK, "main.json")
        r = subprocess.run([sys.executable, "-I", "-B", os.path.join(HERE, "callgrind_callers.py"), self.path,
                            "--json", out], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("inclusive 460 (46.00%) over 5 calls from 2 call sites", r.stdout)
        with open(out, encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertEqual(data["callee_total"], 460)
        self.assertEqual([s["calls"] for s in data["sites"]], [4, 1])
        self.assertEqual(data["sites"][0]["caller"],
                         "forge::Worker::search(forge::Board&, forge::SearchStack*, int, int, int, bool)")


class HelperTests(unittest.TestCase):
    def test_base_name_strips_recursion_suffix(self):
        self.assertEqual(cc.base_name("forge::Worker::search(int)'2"), "forge::Worker::search(int)")
        self.assertEqual(cc.base_name("main"), "main")

    def test_bias_vote(self):
        fn_min = {("/w/build/forge", "a()"): 0x109000 + 0x1000, ("/w/build/forge", "b()'2"): 0x109000 + 0x2000,
                  ("/w/build/forge", "c()"): 0x109000 + 0x3010,  # entry not executed (lowest cost line is later)
                  ("/lib/libc.so.6", "a()"): 0x500000}
        table = {"a()": 0x1000, "b()": 0x2000, "c()": 0x3000}
        bias, agree, seen = cc.bias_from(table, fn_min, "forge")
        self.assertEqual((bias, agree, seen), (0x109000, 2, 3))

    def test_bias_needs_a_match(self):
        with self.assertRaises(SystemExit):
            cc.bias_from({"x()": 1}, {("/w/forge", "y()"): 5}, "forge")

    def test_parse_addr2line_inline_chain(self):
        out = ["0x0000000000401010",
               "forge::MovePicker::MovePicker(forge::Board const&, forge::Worker const&, forge::SearchStack const*, forge::Move, forge::MovePicker::Mode)",
               "/home/runner/work/dwqww/dwqww/src/search.cpp:323 (discriminator 1)",
               "forge::Worker::search(forge::Board&, forge::SearchStack*, int, int, int, bool)",
               "/home/runner/work/dwqww/dwqww/src/search.cpp:1040",
               "0x0000000000401110",
               "forge::Board::has_legal_move() const",
               "/home/runner/work/dwqww/dwqww/src/board.cpp:569"]
        chains = cc.parse_addr2line(out)
        self.assertEqual(chains[0x401010][0].split(" @ ")[1], "src/search.cpp:323")
        self.assertEqual(chains[0x401010][1].split(" @ ")[1], "src/search.cpp:1040")
        self.assertEqual(len(chains[0x401110]), 1)
        self.assertEqual(cc.group_of(" | ".join(chains[0x401010]), "forge::Worker::search"), "move_buffers")
        self.assertEqual(cc.group_of(" | ".join(chains[0x401110]), "forge::Board::has_legal_move() const"), "move_buffers")

    def test_groups(self):
        self.assertEqual(cc.group_of("forge::TranspositionTable::clear() @ src/search.cpp:250", "x"), "tt_clear")
        self.assertEqual(cc.group_of("forge::Worker::clear() @ src/search.cpp:1300", "x"), "histories")
        self.assertEqual(cc.group_of("std::make_unique<std::array<...> > ContinuationHistory", "x"), "histories")
        self.assertEqual(cc.group_of("forge::Evaluator::clear() @ src/eval.cpp:10", "x"), "eval_cache")
        self.assertEqual(cc.group_of("main @ src/uci.cpp:1", "main"), "other")


if __name__ == "__main__":
    unittest.main(verbosity=2)

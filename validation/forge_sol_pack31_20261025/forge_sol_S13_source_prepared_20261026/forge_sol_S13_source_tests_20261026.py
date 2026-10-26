"""Pure source/negative-control tests; never invokes a compiler or engine."""
from pathlib import Path
import os
import unittest
from forge_sol_S13_source_contract_20261026 import read_sources, validate_source

ROOT = Path(__file__).resolve().parent
BASE = Path(os.environ["FORGE_S13_TEST_BASE"])
CANDIDATE = Path(os.environ["FORGE_S13_TEST_CANDIDATE"])


class SourceContract(unittest.TestCase):
    def setUp(self):
        self.base = read_sources(BASE)
        self.candidate = read_sources(CANDIDATE)

    def test_real_candidate_meets_contract(self):
        self.assertEqual(validate_source(self.candidate, self.base)["status"], "PASS_SOURCE_ONLY")

    def test_unfixed_base_fails_new_contract(self):
        with self.assertRaisesRegex(ValueError, "build switch must exist"):
            validate_source(self.base, self.base)

    def test_build_default_on_control_rejected(self):
        self.candidate["CMakeLists.txt"] = self.candidate["CMakeLists.txt"].replace(
            'TtChildPrefetch experiment" OFF)', 'TtChildPrefetch experiment" ON)')
        with self.assertRaisesRegex(ValueError, "build switch"):
            validate_source(self.candidate, self.base)

    def test_missing_null_prefetch_control_rejected(self):
        text = self.candidate["src/search.cpp"]
        text = text.replace("if (s13_tt_child_prefetch_) shared_.tt.prefetch(board.key());", "", 1)
        self.candidate["src/search.cpp"] = text
        with self.assertRaisesRegex(ValueError, "new child path missing"):
            validate_source(self.candidate, self.base)

    def test_missing_probcut_prefetch_control_rejected(self):
        text = self.candidate["src/search.cpp"]
        prefix, suffix = text.rsplit("if (s13_tt_child_prefetch_) shared_.tt.prefetch(board.key());", 1)
        self.candidate["src/search.cpp"] = prefix + suffix
        with self.assertRaisesRegex(ValueError, "new child path missing"):
            validate_source(self.candidate, self.base)

    def test_racy_recursive_requested_read_control_rejected(self):
        self.candidate["src/search.cpp"] = self.candidate["src/search.cpp"].replace(
            "if (s13_tt_child_prefetch_) shared_.tt.prefetch(board.key());",
            "if (shared_.s13_tt_child_prefetch.load(std::memory_order_relaxed)) shared_.tt.prefetch(board.key());", 1)
        with self.assertRaisesRegex(ValueError, "recursive worker"):
            validate_source(self.candidate, self.base)

    def test_lost_bench_inheritance_control_rejected(self):
        self.candidate["src/uci.cpp"] = self.candidate["src/uci.cpp"].replace(
            "bench_searcher.set_s13_tt_child_prefetch(searcher.s13_tt_child_prefetch_enabled());", "")
        with self.assertRaisesRegex(ValueError, "bench searcher"):
            validate_source(self.candidate, self.base)

    def test_unrelated_value_change_control_rejected(self):
        self.candidate["src/search.cpp"] = self.candidate["src/search.cpp"].replace(
            "const int probcut_beta = beta + tune::ProbcutMargin - 50 * improving;",
            "const int probcut_beta = beta + tune::ProbcutMargin - 49 * improving;")
        with self.assertRaisesRegex(ValueError, "OFF source erasure"):
            validate_source(self.candidate, self.base)

    def test_hidden_else_in_feature_guard_control_rejected(self):
        text = self.candidate["src/search.cpp"]
        anchor = "if (s13_tt_child_prefetch_) shared_.tt.prefetch(board.key());\n#endif"
        text = text.replace(anchor, anchor.replace("#endif", "#else\n            return 0;\n#endif"), 1)
        self.candidate["src/search.cpp"] = text
        with self.assertRaisesRegex(ValueError, "alternate feature branches"):
            validate_source(self.candidate, self.base)

    def test_hidden_elif_in_feature_guard_control_rejected(self):
        text = self.candidate["src/search.cpp"]
        anchor = "if (s13_tt_child_prefetch_) shared_.tt.prefetch(board.key());\n#endif"
        text = text.replace(anchor, anchor.replace("#endif", "#elif 1\n            return 0;\n#endif"), 1)
        self.candidate["src/search.cpp"] = text
        with self.assertRaisesRegex(ValueError, "alternate feature branches"):
            validate_source(self.candidate, self.base)


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Synthetic parser fixtures only; these are not engine observations."""
from pathlib import Path
import copy
import json
import unittest
import tempfile
from forge_sol_S14_compare_picker_20261026 import compare_streams, read_bounded, MAX_BYTES

ROOT = Path(__file__).resolve().parent
CONTROLS = ["new", "new_array", "new_aligned", "new_array_aligned", "new_nothrow", "new_array_nothrow", "new_aligned_nothrow", "new_array_aligned_nothrow"]


def fixtures():
    e = json.loads((ROOT / "forge_sol_S14_source_bindings_20261026.json").read_text())
    for role, char in [("Lprime", "1"), ("B", "2")]:
        e["bases"][role]["source_inventory"]["src/search.cpp"]["sha256"] = char * 64
        e["bases"][role]["core_sha256"] = ("a" if role == "Lprime" else "b") * 64
    e["workload_tsv_sha256"] = "e" * 64
    def stream(role):
        base = e["bases"][role]
        out = ["\t".join(["FORGE_S14_PICKER_V1", role, base["source_inventory"]["src/search.cpp"]["sha256"], base["core_sha256"], e["workload_tsv_sha256"], e["allocation_coverage"], "20", "6", "64", "NORMAL"])]
        out += [f"CONTROL\t{name}\t1\t32\t1" for name in CONTROLS]
        for i, case in enumerate(e["workload"]):
            for mode in e["modes"]:
                seq, legal, count = ("a2a3,b2b3", "LL", 2) if i == 0 else ("", "", 0)
                out.append("\t".join(map(str, ["PICK", i, case["id"], mode, case["fen"], seq, legal, count, count, 1, 0, 0, 0, 0])))
        out.append("DONE\t20\t120\t44\t252")
        return ("\n".join(out) + "\n").encode()
    return e, stream("Lprime"), stream("B")


class SyntheticParserFixtures(unittest.TestCase):
    def setUp(self):
        self.e, self.left, self.right = fixtures()

    def rejected(self, data, pattern=None):
        with self.assertRaisesRegex(ValueError, pattern or ".+"):
            compare_streams(self.left, data, self.e)

    def test_valid_distinct_baseline_structural_comparison(self):
        d = compare_streams(self.left, self.right, self.e)
        self.assertEqual(d["status"], "PASS_STRUCTURAL_BASELINE_COMPARISON")
        self.assertEqual(d["record_pairs"], 120)
        self.assertEqual(d["native_producer_authentication"], "NOT_CHECKED")

    def test_same_baseline_cannot_masquerade_as_comparison(self):
        self.rejected(self.left, "distinct")

    def test_wrong_source_hash(self):
        self.rejected(self.right.replace(b"2" * 64, b"3" * 64, 1), "source")

    def test_wrong_core_hash(self):
        self.rejected(self.right.replace(b"b" * 64, b"c" * 64, 1), "core")

    def test_wrong_workload_hash(self):
        self.rejected(self.right.replace(b"e" * 64, b"f" * 64, 1), "workload")

    def test_false_complete_heap_coverage_claim(self):
        self.rejected(self.right.replace(self.e["allocation_coverage"].encode(), b"all_heap_allocations"), "coverage")

    def test_negative_mode_never_passes(self):
        self.rejected(self.right.replace(b"NORMAL", b"counter_disabled", 1), "mode")

    def test_positive_control_zero_calls_rejected(self):
        self.rejected(self.right.replace(b"CONTROL\tnew\t1\t32\t1", b"CONTROL\tnew\t0\t32\t1"), "control")

    def test_missing_positive_control(self):
        self.rejected(self.right.replace(b"CONTROL\tnew\t1\t32\t1\n", b""), "line count")

    def test_constructor_allocation_detected(self):
        lines = self.right.decode().splitlines()
        fields = lines[9].split("\t"); fields[10] = "1"; fields[12] = "32"; lines[9] = "\t".join(fields)
        self.rejected(("\n".join(lines) + "\n").encode(), "allocation")

    def test_next_allocation_detected(self):
        lines = self.right.decode().splitlines()
        fields = lines[9].split("\t"); fields[11] = "1"; fields[13] = "32"; lines[9] = "\t".join(fields)
        self.rejected(("\n".join(lines) + "\n").encode(), "allocation")

    def test_changed_prefix_move_detected(self):
        self.rejected(self.right.replace(b"a2a3,b2b3", b"a2a3,c2c3", 1), "differ")

    def test_invalid_uci_move_detected(self):
        self.rejected(self.right.replace(b"a2a3,b2b3", b"x2a3,b2b3", 1), "move")

    def test_duplicate_prefix_move_detected(self):
        self.rejected(self.right.replace(b"a2a3,b2b3", b"a2a3,a2a3", 1), "duplicate")

    def test_truncated_prefix_detected(self):
        self.rejected(self.right.replace(b"a2a3,b2b3\tLL\t2", b"a2a3\tL\t2", 1), "prefix")

    def test_fen_binding_detected(self):
        self.rejected(self.right.replace(b"w KQkq - 0 1", b"b KQkq - 0 1", 1), "case")

    def test_missing_record_detected(self):
        lines = self.right.splitlines(keepends=True); del lines[10]
        self.rejected(b"".join(lines), "line count")

    def test_extra_output_after_done_detected(self):
        self.rejected(self.right + b"extra\n", "line count")

    def test_missing_final_newline_detected(self):
        self.rejected(self.right[:-1], "newline")

    def test_mailbox_accounting_detected(self):
        self.rejected(self.right.replace(b"DONE\t20\t120\t44\t252", b"DONE\t20\t120\t45\t252"), "mailbox")

    def test_window_accounting_detected(self):
        self.rejected(self.right.replace(b"DONE\t20\t120\t44\t252", b"DONE\t20\t120\t44\t253"), "window")

    def test_regular_bounded_input_read(self):
        with tempfile.TemporaryDirectory(prefix="forge_s14_read_fixture_") as tmp:
            p = Path(tmp) / "fixture.stdout"; p.write_bytes(self.left)
            self.assertEqual(read_bounded(p), self.left)

    def test_oversized_input_rejected(self):
        with tempfile.TemporaryDirectory(prefix="forge_s14_read_fixture_") as tmp:
            p = Path(tmp) / "fixture.stdout"; p.write_bytes(b"x" * (MAX_BYTES + 1))
            with self.assertRaisesRegex(ValueError, "bounded"):
                read_bounded(p)


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Synthetic build-binding fixtures. No fixture compiler or binary is executed."""
from pathlib import Path
import copy
import hashlib
import json
import tempfile
import unittest
from forge_sol_S14_build_plan_20261026 import build_plan, verify_argv, verify_link_map, verify_inputs

H = lambda data: hashlib.sha256(data).hexdigest()


class SyntheticBuildFixtures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="forge_s14_binding_fixture_")
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.packet, self.source, self.core = root / "packet", root / "source", root / "core/libforge_core.a"
        self.compiler, self.main, self.out = root / "fixture_compiler", root / "canonical/forge", root / "new_output"
        for p, data in [(self.core, b"FIXTURE_CORE_NOT_ELF"), (self.compiler, b"FIXTURE_COMPILER_NOT_EXECUTED"), (self.main, b"FIXTURE_MAIN_NOT_ELF")]:
            p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
        inventory = {}
        for name in ["src/search.cpp", "src/nnue_weights.inc", "include/forge/search.hpp"]:
            p = self.source / name; p.parent.mkdir(parents=True, exist_ok=True); data = ("FIXTURE " + name).encode(); p.write_bytes(data)
            inventory[name] = {"sha256": H(data), "bytes": len(data)}
        self.packet.mkdir()
        pins = {}
        for name in ["forge_sol_S14_picker_oracle_20261026.cpp", "forge_sol_S14_cpp_alloc_counter_20261026.hpp", "forge_sol_S14_expected_workload_20261026.hpp", "forge_sol_S14_workload20_20261026.tsv"]:
            data = ("FIXTURE " + name).encode(); (self.packet / name).write_bytes(data); pins[name] = H(data)
        self.receipt = self.packet / "reference.json"
        self.data = {"schema": "forge.S11.baseline_release_reuse.v1", "status": "PASS_ORACLE_ONLY_WITH_REUSED_STD", "role": "baseline", "profile": "Release", "base": "Lprime", "evidence_class": "REUSE_NOT_NEW_RUN", "source_before": {k: v["sha256"] for k, v in inventory.items()}, "source_after": {k: v["sha256"] for k, v in inventory.items()}, "compiler_sha256": H(self.compiler.read_bytes()), "new_main_ELFs": 0, "new_FIRST_runs": 0, "new_full_Std_runs": 0, "new_JUnit": False, "evidence": {"core_archive": {"sha256": H(self.core.read_bytes()), "bytes": self.core.stat().st_size}, "canonical_build": str(self.main.parent), "main_sha256": H(self.main.read_bytes())}}
        self.tests = self.main.parent / "forge_tests"; self.tests.write_bytes(b"FIXTURE_TESTS_NOT_EXECUTED")
        self.support = self.main.parent / "support"; self.support.write_bytes(b"FIXTURE_SUPPORT_NOT_EXECUTED")
        self.flags = self.main.parent / "flags.make"; self.flags.write_bytes(b"FIXTURE_FLAGS_NOT_EXECUTED")
        self.original = self.main.parent / "qualification.json"; self.original.write_bytes(b"SYNTHETIC_QUALIFICATION_ONLY")
        self.data["evidence"].update({"tests_ELF_sha256": H(self.tests.read_bytes()), "artifacts": [{"path": str(self.support), "sha256": H(self.support.read_bytes())}], "canonical_flags": [{"path": str(self.flags), "sha256": H(self.flags.read_bytes())}], "original_receipt": str(self.original), "original_receipt_sha256": H(self.original.read_bytes())})
        self.expected = {"schema": "forge.S14.source_bindings.v1", "compiler_sha256": H(self.compiler.read_bytes()), "packet_pins": pins, "workload_tsv_sha256": pins["forge_sol_S14_workload20_20261026.tsv"], "bases": {"Lprime": {"source_inventory": inventory, "core_owner": "Lprime", "core_sha256": H(self.core.read_bytes()), "main_sha256": H(self.main.read_bytes())}}}
        self.save_receipt()

    def save_receipt(self):
        raw = (json.dumps(self.data, sort_keys=True) + "\n").encode(); self.receipt.write_bytes(raw)
        self.expected["bases"]["Lprime"]["reference_receipt_sha256"] = H(raw)

    def plan(self):
        return build_plan("Lprime", self.source, self.core, self.receipt, self.compiler, self.packet, self.expected, self.out)

    def test_valid_plan_without_compilation(self):
        d = self.plan()
        self.assertEqual(d["status"], "READY_BUILD_PLAN_ONLY")
        self.assertEqual(d["compiler_runs"], 0)
        self.assertFalse(self.out.exists())

    def test_changed_source_rejected(self):
        (self.source / "src/search.cpp").write_text("MUTATED")
        with self.assertRaisesRegex(ValueError, "source"):
            self.plan()

    def test_extra_source_file_rejected(self):
        (self.source / "extra.cpp").write_text("MUTATED")
        with self.assertRaisesRegex(ValueError, "inventory"):
            self.plan()

    def test_other_core_rejected(self):
        self.core.write_text("OTHER_CORE")
        with self.assertRaisesRegex(ValueError, "core"):
            self.plan()

    def test_other_compiler_rejected(self):
        self.compiler.write_text("OTHER_COMPILER")
        with self.assertRaisesRegex(ValueError, "compiler"):
            self.plan()

    def test_unqualified_candidate_receipt_rejected(self):
        self.data["role"] = "candidate"; self.save_receipt()
        with self.assertRaisesRegex(ValueError, "baseline"):
            self.plan()

    def test_asan_receipt_cannot_be_borrowed(self):
        self.data["profile"] = "ASAN"; self.save_receipt()
        with self.assertRaisesRegex(ValueError, "Release"):
            self.plan()

    def test_failed_receipt_rejected(self):
        self.data["status"] = "FAIL"; self.save_receipt()
        with self.assertRaisesRegex(ValueError, "closed"):
            self.plan()

    def test_changed_qualified_main_rejected(self):
        self.main.write_text("OTHER_MAIN")
        with self.assertRaisesRegex(ValueError, "main"):
            self.plan()

    def test_changed_qualified_tests_rejected(self):
        self.tests.write_bytes(b"OTHER_TESTS")
        with self.assertRaisesRegex(ValueError, "tests ELF"):
            self.plan()

    def test_changed_qualified_support_rejected(self):
        self.support.write_bytes(b"OTHER_SUPPORT")
        with self.assertRaisesRegex(ValueError, "support"):
            self.plan()

    def test_changed_qualified_flags_rejected(self):
        self.flags.write_bytes(b"OTHER_FLAGS")
        with self.assertRaisesRegex(ValueError, "flags"):
            self.plan()

    def test_changed_original_qualification_rejected(self):
        self.original.write_bytes(b"OTHER_QUALIFICATION")
        with self.assertRaisesRegex(ValueError, "qualification receipt"):
            self.plan()

    def test_changed_diagnostic_header_rejected(self):
        (self.packet / "forge_sol_S14_cpp_alloc_counter_20261026.hpp").write_text("OTHER")
        with self.assertRaisesRegex(ValueError, "packet"):
            self.plan()

    def test_old_receipt_hash_rejected(self):
        self.receipt.write_bytes(self.receipt.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "receipt"):
            self.plan()

    def test_fast_math_added_to_argv_rejected(self):
        p = self.plan(); argv = list(p["argv"]); argv.insert(1, "-ffast-math")
        with self.assertRaisesRegex(ValueError, "argv"):
            verify_argv(argv, p)

    def test_duplicate_search_object_argv_rejected(self):
        p = self.plan(); argv = list(p["argv"]); argv.insert(-1, "/tmp/search.cpp.o")
        with self.assertRaisesRegex(ValueError, "argv"):
            verify_argv(argv, p)

    def test_link_map_intended_core(self):
        self.assertEqual(verify_link_map("LOAD " + str(self.core) + "\n", self.core)["status"], "PASS_CORE_LINK_MAP")

    def test_archive_search_object_rejected(self):
        text = str(self.core) + "(search.cpp.o)\nLOAD " + str(self.core) + "\n"
        with self.assertRaisesRegex(ValueError, "search.cpp"):
            verify_link_map(text, self.core)

    def test_map_without_intended_core_rejected(self):
        with self.assertRaisesRegex(ValueError, "LOAD"):
            verify_link_map("LOAD /tmp/another.a\n", self.core)

    def test_existing_output_rejected_without_overwrite(self):
        self.out.mkdir()
        marker = self.out / "KEEP"; marker.write_bytes(b"preserve")
        with self.assertRaisesRegex(ValueError, "existing"):
            self.plan()
        self.assertEqual(marker.read_bytes(), b"preserve")

    def test_output_inside_frozen_source_rejected(self):
        self.out = self.source / "new_output"
        with self.assertRaisesRegex(ValueError, "outside frozen"):
            self.plan()

    def test_postplan_input_mutation_detected(self):
        plan = self.plan()
        self.core.write_bytes(b"changed after plan")
        with self.assertRaisesRegex(ValueError, "input changed"):
            verify_inputs(plan)

    def test_unproved_alias_rejected(self):
        self.expected["bases"]["L"] = copy.deepcopy(self.expected["bases"]["Lprime"])
        self.expected["bases"]["L"]["source_inventory"]["src/search.cpp"]["sha256"] = H(b"alias changed")
        # A changed source must fail before any alias can borrow canonical code.
        with self.assertRaisesRegex(ValueError, "source"):
            build_plan("L", self.source, self.core, self.receipt, self.compiler, self.packet, self.expected, self.out)


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Offline behavioral tests; all expectations are independently planted values."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
TOOL = HERE / "forge_sol_S34_validate_manifest_20261026.py"
FIXTURES = HERE / "bad_manifests"
SOURCE = Path("/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files/23_pc_autonomy/autonomy_20261025/forge_gates.json")
if TOOL.exists():
    spec = importlib.util.spec_from_file_location("s34_validator", TOOL)
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
else:
    validator = None


def good_manifest():
    return {"gates": [{"tag": "alpha", "exe": "candidate.exe", "sha256": "a" * 64,
                       "concurrency": 1, "tc": "10+0.1", "srand": 11,
                       "openings_start": 1,
                       "sprt": {"elo0": 0, "elo1": 10, "nonreg": False}}]}


class ValidatorTests(unittest.TestCase):
    def tool(self):
        self.assertIsNotNone(validator, "S34 validator feature has not been implemented")
        return validator

    def codes(self, manifest, **kwargs):
        return [f["code"] for f in self.tool().validate_manifest(manifest, **kwargs)]

    def test_accepts_object_and_list_manifests_and_boundary_concurrency(self):
        # Catches a wrong root branch or an off-by-one concurrency bound.
        for n in (1, 8):
            data = good_manifest()
            data["gates"][0]["concurrency"] = n
            self.assertEqual(self.codes(data), [])
            self.assertEqual(self.codes(data["gates"]), [])

    def test_planted_bad_manifests_are_isolated_and_messages_are_distinct(self):
        # Each fixture must be rejected for its intended independent defect.
        tool = self.tool()
        index = json.loads((FIXTURES / "forge_sol_S34_bad_index_20261026.json").read_text())
        self.assertGreaterEqual(len(index), 12)
        messages = []
        for case in index:
            with self.subTest(case=case["file"]):
                try:
                    data = tool.load_manifest(FIXTURES / case["file"])
                    findings = tool.validate_manifest(data)
                except tool.ManifestError as exc:
                    findings = [exc.finding]
                self.assertEqual([f["code"] for f in findings], [case["code"]])
                self.assertIn(case["explains"], findings[0]["message"])
                self.assertTrue(findings[0]["pointer"].startswith("/"))
                messages.append(findings[0]["message"])
        self.assertEqual(len(messages), len(set(messages)))

    def test_strict_mode_requires_unset_fields_without_inventing_defaults(self):
        data = good_manifest()
        gate = data["gates"][0]
        for key in ("tc", "sprt", "openings_start"):
            gate.pop(key)
        self.assertCountEqual(self.codes(data), ["TC_REQUIRED", "SPRT_REQUIRED", "OPENINGS_START_REQUIRED"])

    def test_explicit_driver_profile_keeps_effective_start_collisions(self):
        data = good_manifest()
        first = data["gates"][0]
        for key in ("tc", "sprt", "openings_start"):
            first.pop(key)
        second = copy.deepcopy(first)
        second.update(tag="beta", srand=12)
        data["gates"].append(second)
        self.assertEqual(self.codes(data, driver_defaults=True), ["OPENINGS_START_DUPLICATE"])

    def test_driver_profile_cannot_fill_partial_or_wrong_typed_overrides(self):
        for value, expected in (({"elo0": 0, "elo1": 10}, "SPRT_NONREG"),
                                (None, "SPRT_SHAPE")):
            data = good_manifest()
            data["gates"][0]["sprt"] = value
            self.assertEqual(self.codes(data, driver_defaults=True), [expected])
        data = good_manifest()
        data["gates"][0]["tc"] = None
        self.assertEqual(self.codes(data, driver_defaults=True), ["TC_FORMAT"])

    def test_sprt_numeric_booleans_and_nonfinite_numbers_are_rejected(self):
        for value in (False, float("nan"), float("inf"), "0"):
            data = good_manifest()
            data["gates"][0]["sprt"]["elo0"] = value
            self.assertEqual(self.codes(data), ["SPRT_BOUNDS"])

    def test_large_finite_sprt_integers_do_not_overflow_numeric_validation(self):
        # Catches converting an arbitrary JSON integer to a machine float.
        data = good_manifest()
        data["gates"][0]["sprt"].update(elo0=10 ** 500, elo1=10 ** 501)
        self.assertEqual(self.codes(data), [])

    def test_cli_returns_parse_findings_for_deep_or_invalid_json(self):
        # Malformed JSON must be a machine-readable rejection, never a traceback.
        self.tool()
        for name, expected in (("deep_json", "JSON_DEPTH"), ("syntax", "JSON_SYNTAX"),
                                ("oversized_integer", "JSON_NUMBER")):
            result = subprocess.run([sys.executable, "-B", str(TOOL),
                                     str(FIXTURES / ("forge_sol_S34_bad_" + name + "_20261026.json"))],
                                    text=True, capture_output=True, cwd=HERE, check=False)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(result.stderr, "")
            self.assertEqual(json.loads(result.stdout)["findings"][0]["code"], expected)

    def test_reader_enforces_explicit_small_byte_budget_without_writing(self):
        # Catches reading an unbounded file before applying a resource limit.
        tool = self.tool()
        with self.assertRaises(tool.ManifestError) as caught:
            tool.load_manifest(HERE / "forge_sol_S34_valid_fixture_20261026.json", max_bytes=16)
        self.assertEqual(caught.exception.finding["code"], "INPUT_SIZE")

    def test_early_stop_present_means_complete_and_numbers_exclude_booleans(self):
        data = good_manifest()
        data["gates"][0]["early_stop"] = {"games": 750, "elo_max": -8, "llr_max": -1.5}
        self.assertEqual(self.codes(data), [])
        for field in ("games", "elo_max", "llr_max"):
            broken = copy.deepcopy(data)
            broken["gates"][0]["early_stop"][field] = True
            self.assertEqual(self.codes(broken), ["EARLY_STOP_TYPES"])
        data["gates"][0]["early_stop"] = None
        self.assertEqual(self.codes(data), ["EARLY_STOP_SHAPE"])

    def test_full_tc_match_rejects_newline_suffix_and_accepts_decimals(self):
        for value in ("10+0.1\n", "10", "10+-1", True, " 10+0.1", "10+0.1x"):
            data = good_manifest()
            data["gates"][0]["tc"] = value
            self.assertEqual(self.codes(data), ["TC_FORMAT"])
        data["gates"][0]["tc"] = "10.5+0.25"
        self.assertEqual(self.codes(data), [])

    def test_confirm_targets_are_exact_tags_not_casefolded_or_trimmed(self):
        data = good_manifest()
        other = copy.deepcopy(data["gates"][0])
        other.update(tag="beta", srand=12, openings_start=2, confirm_of="alpha")
        data["gates"].append(other)
        self.assertEqual(self.codes(data), [])
        for wrong in ("ALPHA", "alpha ", 1):
            other["confirm_of"] = wrong
            self.assertEqual(self.codes(data), ["CONFIRM_TARGET"])

    def test_protected_write_components_survive_windows_normalization(self):
        for tag in ("LOCK", "lock.", "lock ", "safe\\..\\DiSt-V12\\out", "/tmp/LOCK/out", "baseline", "locks"):
            data = good_manifest()
            data["gates"][0]["tag"] = tag
            self.assertEqual(self.codes(data), ["WRITE_PROTECTED"])

    def test_traversing_or_absolute_write_tags_are_rejected_without_resolution(self):
        for tag in ("safe/../out", "safe\\..\\out", "C:\\out", "../safe", "a/b", "..", "safe.", "safe ", "nul", "COM1", "a:b"):
            data = good_manifest()
            data["gates"][0]["tag"] = tag
            self.assertEqual(self.codes(data), ["WRITE_PATH_UNSAFE"])

    def test_read_paths_may_use_protected_names_and_metadata_is_not_scanned(self):
        data = good_manifest()
        gate = data["gates"][0]
        gate["exe"] = r"C:\\LOCK\\dist-v9\\candidate.exe"
        gate["notes"] = "Do not write to LOCK or dist-v9"
        gate["ok"] = r"C:\\LOCK\\approval.ok"
        data["base"] = {"exe": "baseline/locked.exe", "sha256": "B" * 64}
        data["lock"] = {"exe": "LOCK/engine.exe", "sha256": "c" * 64}
        gate["base_override"] = {"exe": "dist-v9/base.exe", "sha256": "d" * 64}
        self.assertEqual(self.codes(data), [])

    def test_unknown_fields_cannot_hide_write_paths_even_when_the_path_looks_safe(self):
        for field in ("output_dir", "write_path", "results", "future_writer"):
            data = good_manifest()
            data["gates"][0][field] = "safe/output"
            self.assertEqual(self.codes(data), ["UNSUPPORTED_FIELD"])

    def test_duplicate_logical_tags_and_case_colliding_windows_outputs(self):
        for tag, expected in (("alpha", "TAG_DUPLICATE"), ("ALPHA", "TAG_WRITE_COLLISION")):
            data = good_manifest()
            other = copy.deepcopy(data["gates"][0])
            other.update(tag=tag, srand=12, openings_start=2)
            data["gates"].append(other)
            self.assertEqual(self.codes(data), [expected])

    def test_nested_engine_shape_and_full_hash_are_checked(self):
        data = good_manifest()
        data["gates"][0]["base_override"] = []
        self.assertEqual(self.codes(data), ["ENGINE_SHAPE"])
        data["gates"][0]["base_override"] = {"exe": "base.exe", "sha256": "a...b"}
        self.assertEqual(self.codes(data), ["SHA256_FULL"])

    def test_invalid_gate_and_root_shapes_return_findings_not_tracebacks(self):
        self.assertEqual(self.codes({"gates": {}}), ["GATES_SHAPE"])
        self.assertEqual(self.codes([None]), ["GATE_SHAPE"])
        self.assertEqual(self.codes(False), ["MANIFEST_SHAPE"])
        self.assertEqual(self.codes({}), ["GATES_SHAPE"])

    def test_cli_is_read_only_and_reports_valid_input_and_parse_error(self):
        self.tool()
        files_before = {p.relative_to(HERE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in HERE.rglob("*") if p.is_file()}
        good = HERE / "forge_sol_S34_valid_fixture_20261026.json"
        result = subprocess.run([sys.executable, "-B", str(TOOL), str(good)],
                                text=True, capture_output=True, cwd=HERE, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["valid"])
        self.assertEqual(result.stderr, "")
        bad = FIXTURES / "forge_sol_S34_bad_duplicate_json_key_20261026.json"
        result = subprocess.run([sys.executable, "-B", str(TOOL), str(bad)],
                                text=True, capture_output=True, cwd=HERE, check=False)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stdout)["findings"][0]["code"], "JSON_DUPLICATE_KEY")
        files_after = {p.relative_to(HERE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in HERE.rglob("*") if p.is_file()}
        self.assertEqual(files_before, files_after)

    def test_supplied_manifest_strict_and_secondary_audits_preserve_input(self):
        tool = self.tool()
        before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        data = tool.load_manifest(SOURCE)
        strict = tool.validate_manifest(data)
        self.assertEqual(len(data["gates"]), 122)
        self.assertEqual(len(strict), 240)
        self.assertCountEqual([f["code"] for f in strict],
                              ["TC_REQUIRED"] * 122 + ["SPRT_REQUIRED"] * 104 + ["OPENINGS_START_REQUIRED"] * 14)
        effective = tool.validate_manifest(data, driver_defaults=True)
        self.assertEqual(len(effective), 13)
        self.assertEqual({f["code"] for f in effective}, {"OPENINGS_START_DUPLICATE"})
        self.assertEqual(before, "9c7abdb4fde93ac9118292f5852da118766573f9abea67e303b8001063ab9f79")
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)

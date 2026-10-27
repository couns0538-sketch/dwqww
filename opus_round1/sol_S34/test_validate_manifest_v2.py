"""Tests for forge_sol_S34_validate_manifest_v2.py.

Part 1 ports Sol's 21 v1 tests (forge_sol_S34_tests_20261026.py, sha256 b3e6ebcd...): same planted values,
with the profile made explicit (his validate_manifest() default was strict; the v2 default is the deployed
driver profile, so strict expectations pass strict=True). Part 2 tests the v2 rules.
Real files: set S34_SNAPSHOT to the lock-archive snapshot (6_gate/pc_autonomy_scripts_copy/autonomy_20261025/
forge_gates.json) and S34_LIVE to a read-only copy of the live PC forge_gates.json; tests without them skip.
Run: python -I -B test_validate_manifest_v2.py
"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
TOOL = HERE / "forge_sol_S34_validate_manifest_v2.py"
FIXTURES = Path(os.environ.get("S34_FIXTURES", HERE / "bad_manifests_v2"))
SNAPSHOT = os.environ.get("S34_SNAPSHOT")
LIVE = os.environ.get("S34_LIVE")
spec = importlib.util.spec_from_file_location("s34_validator_v2", TOOL)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def good_manifest():
    return {"gates": [{"tag": "alpha", "exe": "candidate.exe", "sha256": "a" * 64,
                       "concurrency": 1, "tc": "10+0.1", "srand": 11,
                       "openings_start": 1,
                       "sprt": {"elo0": 0, "elo1": 10, "nonreg": False}}]}


def codes(manifest, **kwargs):
    return [f["code"] for f in validator.validate_manifest(manifest, **kwargs)]


def run_cli(*args):
    return subprocess.run([sys.executable, "-I", "-B", str(TOOL), *map(str, args)],
                          text=True, capture_output=True, cwd=HERE, check=False)


class SolV1Ported(unittest.TestCase):
    def test_accepts_object_and_list_manifests_and_boundary_concurrency(self):
        for n in (1, 8):
            data = good_manifest()
            data["gates"][0]["concurrency"] = n
            for strict in (True, False):
                self.assertEqual(codes(data, strict=strict), [])
                self.assertEqual(codes(data["gates"], strict=strict), [])

    def test_planted_bad_manifests_are_isolated_and_messages_are_distinct(self):
        index = json.loads((FIXTURES / "index.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(index), 29)
        messages = []
        for case in index:
            with self.subTest(case=case["file"]):
                try:
                    data = validator.load_manifest(FIXTURES / case["file"])
                    findings = validator.validate_manifest(data, strict=case["profile"] == "strict")
                except validator.ManifestError as exc:
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
        self.assertCountEqual(codes(data, strict=True), ["TC_REQUIRED", "SPRT_REQUIRED", "OPENINGS_START_REQUIRED"])

    def test_explicit_driver_profile_keeps_effective_start_collisions(self):
        data = good_manifest()
        first = data["gates"][0]
        for key in ("tc", "sprt", "openings_start"):
            first.pop(key)
        second = copy.deepcopy(first)
        second.update(tag="beta", srand=12)
        data["gates"].append(second)
        self.assertEqual(codes(data, driver_defaults=True), ["OPENINGS_START_DUPLICATE"])
        self.assertEqual(codes(data), ["OPENINGS_START_DUPLICATE"])

    def test_driver_profile_cannot_fill_partial_or_wrong_typed_overrides(self):
        for value, expected in (({"elo0": 0, "elo1": 10}, "SPRT_NONREG"), (None, "SPRT_SHAPE")):
            data = good_manifest()
            data["gates"][0]["sprt"] = value
            self.assertEqual(codes(data), [expected])
        data = good_manifest()
        data["gates"][0]["tc"] = None
        self.assertEqual(codes(data), ["TC_FORMAT"])

    def test_sprt_numeric_booleans_and_nonfinite_numbers_are_rejected(self):
        for value in (False, float("nan"), float("inf"), "0"):
            data = good_manifest()
            data["gates"][0]["sprt"]["elo0"] = value
            self.assertEqual(codes(data, strict=True), ["SPRT_BOUNDS"])

    def test_large_finite_sprt_integers_do_not_overflow_numeric_validation(self):
        data = good_manifest()
        data["gates"][0]["sprt"].update(elo0=10 ** 500, elo1=10 ** 501)
        self.assertEqual(codes(data, strict=True), [])

    def test_cli_returns_parse_findings_for_deep_or_invalid_json(self):
        for name, expected in (("deep_json", "JSON_DEPTH"), ("syntax", "JSON_SYNTAX"),
                               ("oversized_integer", "JSON_NUMBER")):
            result = run_cli(FIXTURES / ("bad_" + name + ".json"))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(result.stderr, "")
            self.assertEqual(json.loads(result.stdout)["findings"][0]["code"], expected)

    def test_reader_enforces_explicit_small_byte_budget_without_writing(self):
        with self.assertRaises(validator.ManifestError) as caught:
            validator.load_manifest(FIXTURES / "valid_manifest_v2.json", max_bytes=16)
        self.assertEqual(caught.exception.finding["code"], "INPUT_SIZE")

    def test_early_stop_present_means_complete_and_numbers_exclude_booleans(self):
        data = good_manifest()
        data["gates"][0]["early_stop"] = {"games": 750, "elo_max": -8, "llr_max": -1.5}
        self.assertEqual(codes(data, strict=True), [])
        for field in ("games", "elo_max", "llr_max"):
            broken = copy.deepcopy(data)
            broken["gates"][0]["early_stop"][field] = True
            self.assertEqual(codes(broken, strict=True), ["EARLY_STOP_TYPES"])
        data["gates"][0]["early_stop"] = None
        self.assertEqual(codes(data, strict=True), ["EARLY_STOP_SHAPE"])

    def test_full_tc_match_rejects_newline_suffix_and_accepts_decimals(self):
        for value in ("10+0.1\n", "10", "10+-1", True, " 10+0.1", "10+0.1x"):
            data = good_manifest()
            data["gates"][0]["tc"] = value
            self.assertEqual(codes(data, strict=True), ["TC_FORMAT"])
            self.assertEqual(codes(data), ["TC_FORMAT"])
        data["gates"][0]["tc"] = "10.5+0.25"
        self.assertEqual(codes(data, strict=True), [])

    def test_confirm_targets_are_exact_tags_not_casefolded_or_trimmed(self):
        data = good_manifest()
        other = copy.deepcopy(data["gates"][0])
        other.update(tag="beta", srand=12, openings_start=2, confirm_of="alpha")
        data["gates"].append(other)
        self.assertEqual(codes(data, strict=True), [])
        for wrong in ("ALPHA", "alpha ", 1):
            other["confirm_of"] = wrong
            self.assertEqual(codes(data, strict=True), ["CONFIRM_TARGET"])

    def test_protected_write_components_survive_windows_normalization(self):
        for tag in ("LOCK", "lock.", "lock ", "safe\\..\\DiSt-V12\\out", "/tmp/LOCK/out", "baseline", "locks"):
            data = good_manifest()
            data["gates"][0]["tag"] = tag
            self.assertEqual(codes(data, strict=True), ["WRITE_PROTECTED"])

    def test_traversing_or_absolute_write_tags_are_rejected_without_resolution(self):
        for tag in ("safe/../out", "safe\\..\\out", "C:\\out", "../safe", "a/b", "..", "safe.", "safe ", "nul", "COM1", "a:b"):
            data = good_manifest()
            data["gates"][0]["tag"] = tag
            self.assertEqual(codes(data, strict=True), ["WRITE_PATH_UNSAFE"])

    def test_read_paths_may_use_protected_names_and_metadata_is_not_scanned(self):
        data = good_manifest()
        gate = data["gates"][0]
        gate["exe"] = r"C:\\LOCK\\dist-v9\\candidate.exe"
        gate["notes"] = "Do not write to LOCK or dist-v9"
        gate["ok"] = r"C:\\LOCK\\approval.ok"
        data["base"] = {"exe": "baseline/locked.exe", "sha256": "B" * 64}
        data["lock"] = {"exe": "LOCK/engine.exe", "sha256": "c" * 64}
        gate["base_override"] = {"exe": "dist-v9/base.exe", "sha256": "d" * 64}
        self.assertEqual(codes(data, strict=True), [])

    def test_unknown_fields_cannot_hide_write_paths_even_when_the_path_looks_safe(self):
        for field in ("output_dir", "write_path", "results", "future_writer"):
            data = good_manifest()
            data["gates"][0][field] = "safe/output"
            self.assertEqual(codes(data, strict=True), ["UNSUPPORTED_FIELD"])

    def test_duplicate_logical_tags_and_case_colliding_windows_outputs(self):
        for tag, expected in (("alpha", "TAG_DUPLICATE"), ("ALPHA", "TAG_WRITE_COLLISION")):
            data = good_manifest()
            other = copy.deepcopy(data["gates"][0])
            other.update(tag=tag, srand=12, openings_start=2)
            data["gates"].append(other)
            self.assertEqual(codes(data, strict=True), [expected])

    def test_nested_engine_shape_and_full_hash_are_checked(self):
        data = good_manifest()
        data["gates"][0]["base_override"] = []
        self.assertEqual(codes(data, strict=True), ["ENGINE_SHAPE"])
        data["gates"][0]["base_override"] = {"exe": "base.exe", "sha256": "a...b"}
        self.assertEqual(codes(data, strict=True), ["SHA256_FULL"])

    def test_invalid_gate_and_root_shapes_return_findings_not_tracebacks(self):
        self.assertEqual(codes({"gates": {}}), ["GATES_SHAPE"])
        self.assertEqual(codes([None]), ["GATE_SHAPE"])
        self.assertEqual(codes(False), ["MANIFEST_SHAPE"])
        self.assertEqual(codes({}), ["GATES_SHAPE"])

    def test_cli_is_read_only_and_reports_valid_input_and_parse_error(self):
        def tree():
            return {p.relative_to(HERE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in HERE.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
        before = tree()
        result = run_cli(FIXTURES / "valid_manifest_v2.json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)["valid"])
        self.assertEqual(result.stderr, "")
        result = run_cli(FIXTURES / "bad_duplicate_json_key.json")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stdout)["findings"][0]["code"], "JSON_DUPLICATE_KEY")
        self.assertEqual(before, tree())

    @unittest.skipUnless(SNAPSHOT, "set S34_SNAPSHOT to the lock-archive forge_gates.json snapshot")
    def test_supplied_manifest_strict_and_default_audits_preserve_input(self):
        source = Path(SNAPSHOT)
        before = hashlib.sha256(source.read_bytes()).hexdigest()
        self.assertEqual(before, "9c7abdb4fde93ac9118292f5852da118766573f9abea67e303b8001063ab9f79")
        data = validator.load_manifest(source)
        self.assertEqual(len(data["gates"]), 122)
        strict = validator.validate_manifest(data, strict=True)
        self.assertEqual(len(strict), 240)
        self.assertCountEqual([f["code"] for f in strict],
                              ["TC_REQUIRED"] * 122 + ["SPRT_REQUIRED"] * 104 + ["OPENINGS_START_REQUIRED"] * 14)
        effective = validator.validate_manifest(data)
        self.assertEqual(len(effective), 13)
        self.assertEqual({f["code"] for f in effective}, {"OPENINGS_START_DUPLICATE"})
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)


class V2Rules(unittest.TestCase):
    def valid(self):
        return validator.load_manifest(FIXTURES / "valid_manifest_v2.json")

    def test_valid_fixture_passes_default_profile_and_bom_is_accepted(self):
        self.assertEqual(codes(self.valid()), [])
        self.assertEqual(codes(validator.load_manifest(FIXTURES / "valid_manifest_v2_bom.json")), [])

    def test_strict_profile_requires_what_the_driver_defaults(self):
        data = self.valid()
        # gate 0 has no tc and no sprt: fine for the driver, two strict findings.
        self.assertCountEqual(codes(data, strict=True), ["TC_REQUIRED", "SPRT_REQUIRED"])
        data["gates"][1].pop("concurrency")
        self.assertEqual(codes(data), [])
        self.assertIn("CONCURRENCY_TYPE", codes(data, strict=True))

    def test_driver_default_concurrency_is_five_and_present_values_are_not_filled(self):
        data = good_manifest()
        data["gates"][0].pop("concurrency")
        self.assertEqual(codes(data), [])
        for value, expected in ((0, "CONCURRENCY_RANGE"), (None, "CONCURRENCY_TYPE"), ("5", "CONCURRENCY_TYPE")):
            data["gates"][0]["concurrency"] = value
            self.assertEqual(codes(data), [expected])
        self.assertEqual(validator.DRIVER_DEFAULTS, {"tc": "10+0.1", "concurrency": 5, "openings_start": 1,
                                                     "sprt": {"elo0": 0, "elo1": 10, "nonreg": False}})

    def test_annotation_fields_are_schema_and_typed(self):
        data = good_manifest()
        gate = data["gates"][0]
        gate.update(ag_vs_lock="lock_s198", ag_rebuilt_on="AUTOLOCK_1", ag_rebase_of="alpha", ag_void_rerun_of="alpha",
                    ag_void_cause="time loss", ag_rebase_exempt24=True, pooled=False)
        self.assertEqual(codes(data, strict=True), [])
        for field, bad in (("ag_vs_lock", ""), ("ag_rebuilt_on", 1), ("ag_rebase_of", None), ("ag_void_cause", []),
                           ("ag_rebase_exempt24", 1), ("pooled", "false")):
            broken = copy.deepcopy(data)
            broken["gates"][0][field] = bad
            self.assertEqual(codes(broken, strict=True), ["ANNOTATION_TYPE"], field)

    def test_ag_prev_shape_fields_and_srand_outside_uniqueness(self):
        data = good_manifest()
        prev = {"exe": "old.exe", "sha256": "c" * 64, "prebench": {"cand_off": 1}, "srand": 11,
                "base_override": {"name": "lock", "exe": "lock.exe", "sha256": "d" * 64, "options": []}, "ag_vs_lock": "s197"}
        data["gates"][0]["ag_prev"] = prev  # same srand as the gate itself: not a duplicate
        other = copy.deepcopy(data["gates"][0])
        other.update(tag="beta", srand=12, openings_start=2)
        data["gates"].append(other)        # and the same ag_prev srand in a second gate: still not a duplicate
        self.assertEqual(codes(data, strict=True), [])
        for change, expected in ((lambda p: p.update(tc="10+0.1"), "UNSUPPORTED_FIELD"),
                                 (lambda p: p.update(srand="11"), "SRAND_TYPE"),
                                 (lambda p: p.update(sha256="c"), "SHA256_FULL"),
                                 (lambda p: p.pop("exe"), "EXE_REQUIRED"),
                                 (lambda p: p.update(prebench=[1]), "METADATA_SHAPE"),
                                 (lambda p: p["prebench"].update(cand_x=1), "UNSUPPORTED_FIELD"),
                                 (lambda p: p["base_override"].update(options=["option.X=1"]), "BASE_OPTIONS_IGNORED"),
                                 (lambda p: p.update(ag_vs_lock=7), "ANNOTATION_TYPE")):
            broken = copy.deepcopy(data)
            change(broken["gates"][0]["ag_prev"])
            self.assertEqual(codes(broken, strict=True), [expected])
        broken = copy.deepcopy(data)
        broken["gates"][0]["ag_prev"] = ["old.exe"]
        self.assertEqual(codes(broken, strict=True), ["AG_PREV_SHAPE"])

    def test_gate_options_follow_the_driver_pattern(self):
        ok = ["option.UseNNUE=true", "option.EvalFile=C:/nets/x=y.bin", "option.Empty=", "option.Name With Space=1"]
        data = good_manifest()
        data["gates"][0]["options"] = list(ok)
        self.assertEqual(codes(data, strict=True), [])
        for bad, expected in (("UseNNUE=true", "OPTION_FORMAT"), ("option.UseNNUE", "OPTION_FORMAT"),
                              ("option.=1", "OPTION_FORMAT"), (" option.A=1", "OPTION_FORMAT"), (7, "OPTION_FORMAT"),
                              ("option.A=1\r", "OPTION_CONTROL_CHAR"), ("option.A=\x00", "OPTION_CONTROL_CHAR"),
                              ("option.usennue=false", "OPTION_DUPLICATE"), ("option.USENNUE=false", "OPTION_DUPLICATE"),
                              ("option.UseNNUE=false", "OPTION_DUPLICATE"), ("option.Threads=4", "OPTION_RESERVED"),
                              ("option.hash=64", "OPTION_RESERVED"), ("option.OWNBOOK=true", "OPTION_RESERVED")):
            broken = copy.deepcopy(data)
            broken["gates"][0]["options"].append(bad)
            self.assertEqual(codes(broken, strict=True), [expected], repr(bad))
        data["gates"][0]["options"] = "option.UseNNUE=true"
        self.assertEqual(codes(data, strict=True), ["OPTIONS_SHAPE"])

    def test_base_and_base_override_options_are_reported(self):
        data = good_manifest()
        data["base"] = {"name": "lock", "exe": "lock.exe", "sha256": "d" * 64, "options": []}
        data["gates"][0]["base_override"] = {"name": "lock", "exe": "lock.exe", "sha256": "d" * 64, "options": []}
        self.assertEqual(codes(data, strict=True), [])
        data["base"]["options"] = ["option.UseNNUE=false"]
        self.assertEqual(codes(data, strict=True), ["BASE_OPTIONS_IGNORED"])
        data["base"]["options"] = []
        data["gates"][0]["base_override"]["options"] = ["option.Contempt=5"]
        self.assertEqual(codes(data, strict=True), ["BASE_OPTIONS_IGNORED"])
        data["gates"][0]["base_override"]["options"] = "none"
        self.assertEqual(codes(data, strict=True), ["OPTIONS_SHAPE"])

    def test_case_only_duplicate_keys_are_rejected_at_load_time_anywhere(self):
        with tempfile.TemporaryDirectory() as tmp:
            for text in ('{"gates": [], "Gates": []}',
                         '{"gates": [{"tag": "a", "TAG": "b"}]}',
                         '{"gates": [{"sprt": {"elo0": 0, "ELO0": 1}}]}'):
                path = Path(tmp) / "m.json"
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(validator.ManifestError) as caught:
                    validator.load_manifest(path)
                self.assertEqual(caught.exception.finding["code"], "JSON_CASE_DUPLICATE_KEY")

    def test_cli_profiles_and_alias(self):
        default = json.loads(run_cli(FIXTURES / "valid_manifest_v2.json").stdout)
        alias = json.loads(run_cli(FIXTURES / "valid_manifest_v2.json", "--driver-defaults").stdout)
        strict = json.loads(run_cli(FIXTURES / "valid_manifest_v2.json", "--strict").stdout)
        self.assertEqual((default["valid"], alias["valid"], strict["valid"]), (True, True, False))
        self.assertEqual(default["audit_profile"], "deployed-driver-defaults")
        self.assertEqual(strict["finding_counts"], {"SPRT_REQUIRED": 1, "TC_REQUIRED": 1})
        self.assertEqual(default["driver_provenance"]["sha256"], "636b6cca691d0707449147fce1cafc42c3235c22a4419b05e0b2307e1fc2c168")

    @unittest.skipUnless(LIVE, "set S34_LIVE to a read-only copy of the live forge_gates.json")
    def test_live_manifest_only_real_legacy_duplicate_starts(self):
        source = Path(LIVE)
        before = hashlib.sha256(source.read_bytes()).hexdigest()
        self.assertEqual(before, "09c995b682040ce74bb84ab10eb363346927cc6c2b6f6378bc8b93205dc2728b")
        self.assertTrue(source.read_bytes().startswith(b"\xef\xbb\xbf"))
        data = validator.load_manifest(source)
        self.assertEqual(len(data["gates"]), 128)
        found = validator.validate_manifest(data)
        self.assertEqual({f["code"] for f in found}, {"OPENINGS_START_DUPLICATE"})
        self.assertEqual(len(found), 13)
        dup_gates = [data["gates"][int(f["pointer"].split("/")[2])] for f in found]
        # All 13 are legacy gates without openings_start (driver start 1), each with its own srand.
        self.assertTrue(all("openings_start" not in g for g in dup_gates))
        self.assertEqual(len({g["srand"] for g in dup_gates}), 13)
        strict = validator.validate_manifest(data, strict=True)
        self.assertCountEqual([f["code"] for f in strict],
                              ["TC_REQUIRED"] * 128 + ["SPRT_REQUIRED"] * 104 + ["OPENINGS_START_REQUIRED"] * 14)
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Cheap preregistration/source-identity gate tests; never execute an engine."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("build_frozen", ROOT / "build_frozen.py")
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


class FrozenBuildTests(unittest.TestCase):
    def setUp(self):
        self.protocol = json.loads((ROOT / "protocol.json").read_text())
        self.protocol["status"] = BUILD.READY
        self.env = {"BASELINE_SHA": self.protocol["baseline_sha"],
                    "CANDIDATE_SHA": self.protocol["candidate_sha"], "GITHUB_RUN_ATTEMPT": "1"}

    def test_reviewed_single_attempt_matched_sources_allowed(self):
        BUILD.validate_protocol(self.protocol, self.env)

    def test_pending_review_and_rerun_are_rejected(self):
        pending = copy.deepcopy(self.protocol)
        pending["status"] = "PENDING_REVIEW"
        with self.assertRaisesRegex(ValueError, "pending review"):
            BUILD.validate_protocol(pending, self.env)
        with self.assertRaisesRegex(ValueError, "reruns"):
            BUILD.validate_protocol(self.protocol, {**self.env, "GITHUB_RUN_ATTEMPT": "2"})

    def test_source_mismatch_and_nonsha_rejected(self):
        with self.assertRaisesRegex(ValueError, "SHA mismatch"):
            BUILD.validate_protocol(self.protocol, {**self.env, "CANDIDATE_SHA": "a" * 40})
        altered = copy.deepcopy(self.protocol)
        altered["baseline_sha"] = "main"
        with self.assertRaisesRegex(ValueError, "Unfrozen"):
            BUILD.validate_protocol(altered, self.env)

    def test_different_driver_or_relaxed_flags_rejected(self):
        for key, value in (("driver_source_sha", "a" * 40),
                           ("release_flags", BUILD.FLAGS + " -flto"),
                           ("fault_retries", 1)):
            altered = copy.deepcopy(self.protocol)
            altered[key] = value
            with self.assertRaises(ValueError, msg=key):
                BUILD.validate_protocol(altered, self.env)

    def test_source_manifest_detects_changed_and_new_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source").write_bytes(b"original")
            frozen = BUILD.manifest(root)
            (root / "source").write_bytes(b"modified")
            self.assertNotEqual(frozen, BUILD.manifest(root))
            (root / "source").write_bytes(b"original")
            self.assertEqual(frozen, BUILD.manifest(root))
            (root / "new").write_bytes(b"added")
            self.assertNotEqual(frozen, BUILD.manifest(root))


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Offline failure-oriented checks; no Git mutations or network requests."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
import urllib.request
import zipfile

import yaml


REPO = Path(__file__).resolve().parents[2]
PACKAGE = Path(__file__).resolve().parent
WORKFLOW = REPO / ".github/workflows/forge-recover-confirmation.yml"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


recovery = load("recovery_under_test", PACKAGE / "recover.py")
archiver = load("frozen_archiver_under_test", REPO / ".github/hosted-nnue-strength/archive_results.py")


def identities():
    artifact = {"id": recovery.ARTIFACT_ID, "name": recovery.ARTIFACT_NAME,
                "digest": "sha256:" + recovery.ARTIFACT_SHA256, "expired": False,
                "workflow_run": {"id": recovery.RUN_ID, "head_sha": recovery.HEAD_SHA, "repository_id": 456}}
    run = {"id": recovery.RUN_ID, "head_sha": recovery.HEAD_SHA, "status": "completed", "conclusion": "failure",
           "run_attempt": 1, "path": recovery.ORIGINAL_WORKFLOW, "repository": {"full_name": "owner/repo", "id": 456}}
    job = {"id": recovery.JOB_ID, "run_id": recovery.RUN_ID, "head_sha": recovery.HEAD_SHA, "run_attempt": 1,
           "status": "completed", "conclusion": "failure", "steps": [
               {"name": recovery.MATCH_STEP, "conclusion": "success", "completed_at": "2026-10-19T22:44:49Z"},
               {"name": recovery.UPLOAD_STEP, "conclusion": "success", "completed_at": "2026-10-19T22:44:53Z"},
               {"name": recovery.PUBLICATION_STEP, "conclusion": "failure"}]}
    return artifact, run, job


class IdentityTests(unittest.TestCase):
    def test_exact_frozen_completed_identity_is_accepted(self):
        recovery.assert_metadata(*identities(), "owner/repo")

    def test_each_frozen_artifact_run_job_identity_is_required(self):
        mutations = [(0, ("id",), 1), (0, ("name",), "other"), (0, ("digest",), "sha256:" + "0" * 64),
                     (0, ("expired",), True), (0, ("expired",), None), (0, ("workflow_run", "id"), 1),
                     (0, ("workflow_run", "head_sha"), "0" * 40), (0, ("workflow_run", "repository_id"), 9),
                     (1, ("id",), 1), (1, ("head_sha",), "0" * 40), (1, ("run_attempt",), 2),
                     (1, ("status",), "in_progress"), (1, ("conclusion",), "success"),
                     (1, ("path",), "other.yml"), (1, ("repository", "full_name"), "other/repo"),
                     (2, ("id",), 1), (2, ("run_id",), 1), (2, ("head_sha",), "0" * 40),
                     (2, ("run_attempt",), 2), (2, ("status",), "in_progress"), (2, ("conclusion",), "success")]
        for record, keys, replacement in mutations:
            with self.subTest(record=record, keys=keys, replacement=replacement):
                rows = copy.deepcopy(identities())
                target = rows[record]
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = replacement
                with self.assertRaises(ValueError):
                    recovery.assert_metadata(*rows, "owner/repo")

    def test_original_step_success_failure_and_exact_times_are_required(self):
        for index in range(3):
            rows = identities()
            rows[2]["steps"][index]["conclusion"] = "cancelled"
            with self.subTest(index=index), self.assertRaises(ValueError):
                recovery.assert_metadata(*rows, "owner/repo")
        for index in range(2):
            rows = identities()
            rows[2]["steps"][index]["completed_at"] = "2026-10-19T22:44:00Z"
            with self.subTest(index=index), self.assertRaises(ValueError):
                recovery.assert_metadata(*rows, "owner/repo")
        for replacement in ([], identities()[2]["steps"] * 2):
            rows = identities()
            rows[2]["steps"] = replacement
            with self.assertRaises(ValueError):
                recovery.assert_metadata(*rows, "owner/repo")

    def test_mismatched_metadata_prevents_all_original_byte_retrieval(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            rows = identities()
            rows[0]["workflow_run"]["id"] = 7
            for label, row in zip(("artifact", "run", "job"), rows):
                recovery.write_json(out / "official-metadata" / (label + ".json"), row)
            with mock.patch.dict(recovery.os.environ, {"GITHUB_REPOSITORY": "owner/repo"}), mock.patch.object(recovery, "Client") as client:
                with self.assertRaises(ValueError):
                    recovery.original_bytes(out)
                client.assert_not_called()

    def test_pending_protocol_prevents_network_retrieval(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(recovery, "PACKAGE", PACKAGE), mock.patch.object(recovery, "Client") as client:
            # Test the gate independently of the final on-disk reviewed/pending state.
            original_read = Path.read_text
            def read(path, *args, **kwargs):
                if path == PACKAGE / "protocol.json":
                    return json.dumps({"status": "PREPARED_PENDING_ROOT_REVIEW_AND_SINGLE_PUSH"})
                return original_read(path, *args, **kwargs)
            with mock.patch.object(Path, "read_text", read), self.assertRaisesRegex(ValueError, "awaits root review"):
                recovery.metadata(Path(directory))
            client.assert_not_called()

    def test_log_failure_still_attempts_original_artifact_retrieval(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            for label, row in zip(("artifact", "run", "job"), identities()):
                recovery.write_json(out / "official-metadata" / (label + ".json"), row)
            archive = out / "synthetic.zip"
            archive.write_bytes(b"synthetic artifact bytes")
            with mock.patch.dict(recovery.os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "synthetic"}), \
                 mock.patch.object(recovery, "ARTIFACT_SHA256", recovery.digest(archive)), \
                 mock.patch.object(recovery, "read_metadata"), mock.patch.object(recovery, "Client") as client:
                client.return_value.get.side_effect = [RuntimeError("synthetic log failure"), archive]
                with self.assertRaisesRegex(ValueError, "original job-log retrieval"):
                    recovery.original_bytes(out)
                self.assertEqual(client.return_value.get.call_count, 2)
                self.assertEqual(client.return_value.get.call_args_list[1].args[0], f"/actions/artifacts/{recovery.ARTIFACT_ID}/zip")

    def test_signed_redirect_drops_bearer_and_rejects_http(self):
        request = urllib.request.Request("https://api.github.com/repos/owner/repo/actions/artifacts/1/zip",
                                         headers={"Authorization": "Bearer synthetic-test-value"})
        redirect = recovery.SafeRedirect()
        target = redirect.redirect_request(request, None, 302, "Found", {}, "https://example.blob.core.windows.net/zip?signature=synthetic")
        self.assertIsNone(target.get_header("Authorization"))
        with self.assertRaises(ValueError):
            redirect.redirect_request(request, None, 302, "Found", {}, "http://example.invalid/zip")


class PreservationTests(unittest.TestCase):
    def test_extracted_content_must_match_the_original_zip(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            original = out / "original-downloads" / f"artifact-{recovery.ARTIFACT_ID}.zip"
            original.parent.mkdir(parents=True)
            payload = b"unchanged PGN\r\n\xff"
            with zipfile.ZipFile(original, "w") as archive:
                archive.writestr("nested/original.pgn", payload)
            extracted = out / "original-artifact-files/nested/original.pgn"
            extracted.parent.mkdir(parents=True)
            extracted.write_bytes(payload)
            with mock.patch.object(recovery, "ARTIFACT_SHA256", recovery.digest(original)):
                recovery.verify_extracted(out)
                self.assertEqual(extracted.read_bytes(), payload)
                extracted.write_bytes(b"changed")
                with self.assertRaisesRegex(ValueError, "every original ZIP payload byte"):
                    recovery.verify_extracted(out)

    def test_symlink_raw_file_is_rejected_without_following_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            out = root / "raw"
            out.mkdir()
            (root / "elsewhere").write_bytes(b"outside evidence")
            (out / "link").symlink_to(root / "elsewhere")
            with self.assertRaisesRegex(ValueError, "Nonregular"):
                recovery.check_raw_tree(out)

    def test_joblog_original_bytes_survive_derived_failure_excerpts(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            path = out / "original-downloads" / f"job-{recovery.JOB_ID}.log"
            path.parent.mkdir()
            raw = b"2026 start\r\nremote: synthetic exact failure\r\n##[error]Process exit code 1\r\n\xff"
            path.write_bytes(raw)
            recovery.diagnose(out)
            self.assertEqual(path.read_bytes(), raw)
            report = json.loads((out / "publication-failure-diagnosis.json").read_text())
            self.assertTrue(report["cause"].startswith("unknown"))
            self.assertTrue(any("synthetic exact failure" in row["text"] for row in report["excerpts"]))
            self.assertNotIn("100", report["cause"])

    def test_original_zip_and_all_extracted_raw_files_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            out = root / "raw"
            out.mkdir()
            (out / "original.pgn").write_bytes(b'[Result "1/2-1/2"]\r\n\xff\x00')
            (out / "source.json").write_bytes(b'{"platform": "frozen"}\n')
            with zipfile.ZipFile(out / "original-artifact.zip", "w") as archive:
                archive.writestr("original.pgn", (out / "original.pgn").read_bytes())
            manifest = archiver.archive_results(out, root / "archives", "recovery", recovery.SPLIT_SIZE)
            pathspec = root / "publish-pathspec"
            with mock.patch.object(recovery, "ARCHIVER", REPO / recovery.ARCHIVER):
                recovery.verify_publication(out, manifest, pathspec)
                self.assertEqual(len(pathspec.read_bytes().split(b"\0")) - 1, 2)
                (out / "original.pgn").write_bytes(b"changed")
                with self.assertRaisesRegex(ValueError, "every current raw file"):
                    recovery.verify_publication(out, manifest, pathspec)

    def test_nested_artifact_inventory_uses_manifest_posix_string_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            out = root / "raw"
            binary = out / "original-artifact-files/artifacts/baseline/forge"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"frozen binary bytes\x00\xff")
            (out / "original-artifact-files/artifacts-SHA256.json").write_bytes(b'{"frozen":true}\n')
            manifest = archiver.archive_results(out, root / "archives", "nested-recovery", recovery.SPLIT_SIZE)
            verified = archiver.verify_archive(manifest)
            path_order = [{"path": path.relative_to(out).as_posix(), "size": path.stat().st_size,
                           "sha256": recovery.digest(path)} for path in sorted(out.rglob("*")) if path.is_file()]
            self.assertCountEqual(path_order, verified["files"], "Every archived byte must match before testing order")
            self.assertNotEqual([row["path"] for row in path_order], [row["path"] for row in verified["files"]],
                                "The regression fixture must distinguish Path ordering from POSIX string ordering")
            with mock.patch.object(recovery, "ARCHIVER", REPO / recovery.ARCHIVER):
                try:
                    recovery.verify_publication(out, manifest, root / "pathspec")
                except ValueError as error:
                    self.fail("Byte-identical nested inputs rejected because Path order differs from manifest POSIX string order: "
                              + str(error) + "; Path order=" + repr([row["path"] for row in path_order])
                              + "; manifest order=" + repr([row["path"] for row in verified["files"]]))
            self.assertTrue((root / "pathspec").is_file())

    def test_unverified_extra_publication_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            out = root / "raw"
            out.mkdir()
            (out / "raw").write_bytes(b"raw")
            manifest = archiver.archive_results(out, root / "archives", "recovery", recovery.SPLIT_SIZE)
            (manifest.parent / "unverified.exe").write_bytes(b"must never publish")
            with mock.patch.object(recovery, "ARCHIVER", REPO / recovery.ARCHIVER), self.assertRaisesRegex(ValueError, "Unexpected files"):
                recovery.verify_publication(out, manifest, root / "pathspec")


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = yaml.load(WORKFLOW.read_text(), Loader=yaml.BaseLoader)
        cls.job = cls.workflow["jobs"]["recovery"]
        cls.steps = cls.job["steps"]

    def test_bounded_prefix_permissions_and_attempt_are_frozen(self):
        self.assertEqual(self.workflow["on"], {"push": {"branches": ["forge/recover-confirmation-20261020-*"]}})
        self.assertEqual(self.workflow["permissions"], {"contents": "write", "actions": "read"})
        self.assertEqual(self.job["timeout-minutes"], "15")
        self.assertLess(sum(int(row["timeout-minutes"]) for row in self.steps), 15)
        self.assertIn("github.run_attempt == 1", self.job["if"])
        self.assertNotIn("results/", str(self.workflow["on"]))

    def test_official_download_is_single_frozen_original_and_pinned(self):
        steps = [row for row in self.steps if row.get("uses", "").startswith("actions/download-artifact@")]
        self.assertEqual(len(steps), 1)
        step = steps[0]
        self.assertEqual(step["uses"], "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093")
        self.assertEqual(step["with"]["artifact-ids"], str(recovery.ARTIFACT_ID))
        self.assertEqual(step["with"]["run-id"], str(recovery.RUN_ID))
        self.assertEqual(step["with"]["github-token"], "${{ github.token }}")
        self.assertLess(next(i for i, row in enumerate(self.steps) if row.get("id") == "source"), self.steps.index(step))
        self.assertEqual(self.steps[0]["uses"], "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683")

    def test_shell_syntax_without_execution_and_no_engine_execution(self):
        for step in self.steps:
            if "run" not in step:
                continue
            with self.subTest(step=step["name"]):
                result = subprocess.run(["bash", "-n"], input=step["run"], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                for forbidden in ("ctest", "cmake", "run_hosted.py", "run_match.py", "fastchess", "git clone", "sudo", "eval "):
                    self.assertNotIn(forbidden, step["run"])

    def test_raw_upload_always_and_publication_uses_only_verified_pathspec(self):
        upload = next(row for row in self.steps if row.get("id") == "upload")
        self.assertEqual(upload["if"], "always()")
        self.assertEqual(upload["with"]["path"].splitlines(), ["recovery-raw/", "archived-results/"])
        self.assertEqual(upload["with"]["include-hidden-files"], "true")
        publish = next(row for row in self.steps if "Publish only" in row["name"])
        self.assertIn("steps.download.outcome == 'success'", publish["if"])
        self.assertIn("steps.archive.outcome == 'success'", publish["if"])
        self.assertIn("steps.extraction.outcome == 'success'", publish["if"])
        self.assertIn("steps.upload.outcome == 'success'", publish["if"])
        self.assertLess(self.steps.index(upload), self.steps.index(publish))
        self.assertIn("--pathspec-from-file=", publish["run"])
        self.assertNotIn("--force", publish["run"])
        self.assertNotIn("git add -f recovery-raw", publish["run"])
        self.assertIn("results/confirmation-recovery-39332822379-", publish["run"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""Offline regression tests for the sealed-run auditor.

The original pilot is read only. Each invocation retains independently copied
mutated fixtures, CLI output, and audit results below ``fixtures/``. No engine,
training, external hash verification, or full-input scan is requested.

Run: python3 test_audit.py -v
Override locations with ASTRA_AUDIT_SCRIPT and ASTRA_AUDIT_PILOT.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time
import unittest


HERE = Path(__file__).resolve().parent
AUDITOR = Path(os.environ.get("ASTRA_AUDIT_SCRIPT", str(HERE / "audit_sealed_filter.py")))
PILOT = Path(os.environ.get("ASTRA_AUDIT_PILOT", "/tmp/astra-a1-filter-pilot-10000"))
FIXTURES = HERE / "fixtures"


def file_hashes(path: Path) -> dict[str, int | str]:
    sha256, md5 = hashlib.sha256(), hashlib.md5()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            sha256.update(block)
            md5.update(block)
    return {"bytes": size, "sha256": sha256.hexdigest(), "md5": md5.hexdigest()}


def snapshot_tree(root: Path) -> dict[str, dict[str, int | str]]:
    return {
        str(path.relative_to(root)): file_hashes(path)
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def reseal_changed_file(root: Path, relative: str) -> None:
    """Refresh the copied manifest so rejection cannot be a stale hash alone."""
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest[relative].update(file_hashes(root / relative))
    write_json(manifest_path, manifest)


def rewrite_responses(root: Path, transform) -> None:
    """Transform a copy, preserving every original compressed byte elsewhere."""
    relative = "probe_logs/worker-0/responses.jsonl.gz"
    response_path = root / relative
    original = root.parent / "pre_mutation" / relative
    original.parent.mkdir(parents=True, exist_ok=True)
    response_path.rename(original)
    with gzip.open(original, "rt", encoding="utf-8") as src:
        with gzip.open(response_path, "wt", encoding="utf-8") as dst:
            for index, line in enumerate(src):
                response = transform(index, json.loads(line))
                if response is not None:
                    dst.write(json.dumps(response, separators=(",", ":")) + "\n")
    reseal_changed_file(root, relative)


class SealedAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not AUDITOR.is_file():
            raise RuntimeError(f"Auditor is not available: {AUDITOR}")
        if not (PILOT / "manifest.json").is_file():
            raise RuntimeError(f"Sealed control pilot is not available: {PILOT}")
        summary = json.loads((PILOT / "summary.json").read_text(encoding="utf-8"))
        if summary.get("status") != "SEALED" or summary.get("input_rows") != 10000:
            raise RuntimeError("Control must be the sealed 10,000-row pilot")
        FIXTURES.mkdir(parents=True, exist_ok=True)
        cls.session = FIXTURES / f"run-{time.time_ns()}-{os.getpid()}"
        cls.session.mkdir()
        cls.source_before = snapshot_tree(PILOT)
        write_json(cls.session / "source-before.json", cls.source_before)
        print(f"Retained audit fixtures: {cls.session}", file=sys.stderr)

    @classmethod
    def tearDownClass(cls) -> None:
        source_after = snapshot_tree(PILOT)
        write_json(cls.session / "source-after.json", source_after)
        if source_after != cls.source_before:
            raise AssertionError("The source pilot changed during fixture tests")

    def copy_fixture(self, name: str, *, omit_manifest: bool = False) -> Path:
        target = self.session / name / "run"
        target.parent.mkdir()
        ignore = shutil.ignore_patterns("manifest.json") if omit_manifest else None
        shutil.copytree(PILOT, target, ignore=ignore)
        return target

    def audit(self, source: Path, name: str, *, passes: bool) -> None:
        case_dir = self.session / name
        case_dir.mkdir(exist_ok=True)
        output = case_dir / "audit"
        argv = [sys.executable, str(AUDITOR), "--run-dir", str(source), "--out", str(output)]
        write_json(case_dir / "invocation.json", {"argv": argv, "expected_pass": passes})
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        completed = subprocess.run(argv, capture_output=True, text=True, timeout=120,
                                   check=False, env=environment)
        (case_dir / "stdout.txt").write_text(completed.stdout, encoding="utf-8")
        (case_dir / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
        write_json(case_dir / "exit.json", {"returncode": completed.returncode})
        diagnostics = (completed.stdout + "\n" + completed.stderr)[-6000:]
        self.assertNotIn("Traceback (most recent call last)", diagnostics,
                         f"Auditor crashed instead of reporting a result: {diagnostics}")
        report_path = output / "summary.json"
        self.assertTrue(report_path.is_file(), f"Missing audit summary: {diagnostics}")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report.get("status"), "PASS" if passes else "FAIL", report)
        if passes:
            self.assertEqual(completed.returncode, 0, diagnostics)
        else:
            self.assertNotEqual(completed.returncode, 0,
                                f"Corrupted fixture incorrectly passed: {source}\n{diagnostics}")
            self.assertTrue(report.get("error"), "Rejection should explain the failed check")
            failure = json.dumps(report).lower()
            for message in ("hash mismatch", "sha256 mismatch", "md5 mismatch", "unmanifested"):
                self.assertNotIn(message, failure,
                                 f"Fixture must reach a semantic check: {report}")

    def test_00_real_sealed_control_passes(self) -> None:
        self.audit(PILOT, "real-sealed-control", passes=True)

    def test_missing_manifest_is_rejected(self) -> None:
        source = self.copy_fixture("missing-manifest", omit_manifest=True)
        self.audit(source, "missing-manifest", passes=False)

    def test_wrong_kept_input_index_is_rejected(self) -> None:
        source = self.copy_fixture("wrong-kept-input-index")
        path = source / "kept_rows.tsv"
        original = source.parent / "pre_mutation" / "kept_rows.tsv"
        original.parent.mkdir(parents=True, exist_ok=True)
        path.rename(original)
        with original.open(newline="", encoding="utf-8") as src:
            with path.open("w", newline="", encoding="utf-8") as dst:
                reader = csv.DictReader(src, delimiter="\t")
                writer = csv.DictWriter(dst, fieldnames=reader.fieldnames, delimiter="\t",
                                        lineterminator="\n")
                writer.writeheader()
                for index, row in enumerate(reader):
                    if index == 0:
                        row["input_index"] = "1"
                    writer.writerow(row)
        reseal_changed_file(source, "kept_rows.tsv")
        self.audit(source, "wrong-kept-input-index", passes=False)

    def test_native_response_contract_is_rejected(self) -> None:
        variants = {
            "wrong-native-id": ("id", "100000000"),
            "wrong-native-score": ("score", None),
            "wrong-native-status": ("ok", False),
        }
        for name, (field, value) in variants.items():
            with self.subTest(name=name):
                source = self.copy_fixture(name)

                def change_first(index, response):
                    if index == 0:
                        response[field] = response[field] + 1 if field == "score" else value
                    return response

                rewrite_responses(source, change_first)
                self.audit(source, name, passes=False)

    def test_missing_native_response_is_rejected(self) -> None:
        source = self.copy_fixture("missing-native-response")
        response_path = source / "probe_logs/worker-0/responses.jsonl.gz"
        with gzip.open(response_path, "rt", encoding="utf-8") as stream:
            last_index = sum(1 for _ in stream) - 1
        self.assertGreater(last_index, 0)
        rewrite_responses(source, lambda index, response: None if index == last_index else response)
        self.audit(source, "missing-native-response", passes=False)

    def test_sql_holdout_overlap_is_rejected(self) -> None:
        source = self.copy_fixture("sql-holdout-overlap")
        database = source / "position_index.sqlite"
        originals = source.parent / "pre_mutation"
        originals.mkdir()
        shutil.copy2(database, originals / database.name)
        with sqlite3.connect(database) as connection:
            connection.execute("INSERT INTO holdout(digest, key) SELECT digest, key FROM kept LIMIT 1")
            overlap = connection.execute(
                "SELECT COUNT(*) FROM kept JOIN holdout USING (digest, key)"
            ).fetchone()[0]
        self.assertEqual(overlap, 1)
        # Keep the reported holdout count internally consistent to isolate the
        # forbidden SQL overlap instead of a trivial summary count mismatch.
        for relative in ("summary.json", "progress.json"):
            path = source / relative
            shutil.copy2(path, originals / relative)
            summary = json.loads(path.read_text(encoding="utf-8"))
            summary["holdout_unique_positions"] = 1
            write_json(path, summary)
            reseal_changed_file(source, relative)
        reseal_changed_file(source, "position_index.sqlite")
        self.audit(source, "sql-holdout-overlap", passes=False)


if __name__ == "__main__":
    unittest.main()

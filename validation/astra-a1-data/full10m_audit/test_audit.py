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
import importlib.util
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
FROZEN = HERE.parent / "filter_full10m_v2_protocol"


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


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


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


class HoldoutSourceTests(unittest.TestCase):
    """Tiny synthetic helper fixtures; these are not production audit results."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.parser_path = FROZEN / "forge_pos.py"
        cls.parser = load_module(cls.parser_path, "fixture_frozen_forge_pos")
        cls.auditor = load_module(AUDITOR, "fixture_sealed_filter_auditor")
        if not hasattr(cls.auditor, "verify_holdout_sources"):
            raise RuntimeError("Auditor does not yet expose verify_holdout_sources")
        FIXTURES.mkdir(parents=True, exist_ok=True)
        cls.session = FIXTURES / f"holdout-helper-{time.time_ns()}-{os.getpid()}"
        cls.session.mkdir()
        cls.originals = {str(path): file_hashes(path) for path in (cls.parser_path, AUDITOR)}
        write_json(cls.session / "implementation-before.json", cls.originals)
        snapshot = cls.session / "implementation_snapshot"
        snapshot.mkdir()
        for path in (cls.parser_path, AUDITOR):
            shutil.copy2(path, snapshot / path.name)
        print(f"Retained holdout helper fixtures: {cls.session}", file=sys.stderr)

    @classmethod
    def tearDownClass(cls) -> None:
        after = {str(Path(path)): file_hashes(Path(path)) for path in cls.originals}
        write_json(cls.session / "implementation-after.json", after)
        if cls.originals != after:
            raise AssertionError("Frozen parser or auditor changed during helper tests")

    def make_fixture(self, name: str, extension: str, *, missing_key: bool = False):
        root = self.session / f"{name}-{extension}"
        root.mkdir()
        # Both STM variants are legal; the duplicate confirms that declared rows
        # count source records, not merely the number of unique SQL keys.
        white = "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1 | 12 | 0.5"
        black = "4k3/8/8/8/8/8/4P3/4K3 b - - 0 1 | -7 | 1"
        lines = [white, black, white]
        records = [self.parser.text_record(line)[0] for line in lines]
        text_path = root / "synthetic-holdout.txt"
        text_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if extension == "pos":
            writer = self.parser.PosWriter(root, "synthetic-holdout", False, with_fen=False)
            for record in records:
                writer.append(record)
            writer.seal()
        source = root / f"synthetic-holdout.{extension}"
        database = root / "synthetic-holdout.sqlite"
        db = sqlite3.connect(database)
        try:
            db.execute("CREATE TABLE holdout(digest BLOB PRIMARY KEY, key BLOB NOT NULL) WITHOUT ROWID")
            for record in records[:1] if missing_key else records:
                key = record.board + bytes([record.meta & 1])
                db.execute("INSERT OR IGNORE INTO holdout VALUES (?, ?)",
                           (hashlib.sha256(key).digest(), key))
            db.commit()
        finally:
            db.close()
        summary = {
            "holdouts": [{"path": str(source), **file_hashes(source), "rows": len(records)}],
            "implementation": {"forge_pos.py": {
                "path": str(self.parser_path), **file_hashes(self.parser_path)
            }},
        }
        return root, database, source, summary

    def check_helper(self, root, database, source, summary, *, expected_error=None):
        write_json(root / "synthetic-summary.json", summary)
        before = {str(path): file_hashes(path) for path in (database, source)}
        write_json(root / "inputs-before.json", before)
        stamps = {}
        reports, error = None, None
        db = sqlite3.connect(database.as_uri() + "?mode=ro&immutable=1", uri=True)
        try:
            db.execute("PRAGMA query_only=ON")
            try:
                reports = self.auditor.verify_holdout_sources(summary, FROZEN, db, stamps)
            except Exception as caught:
                error = caught
        finally:
            db.close()
        after = {str(path): file_hashes(path) for path in (database, source)}
        write_json(root / "inputs-after.json", after)
        write_json(root / "helper-result.json", {
            "synthetic_fixture_only": True,
            "reports": reports,
            "error": str(error) if error else None,
            "exception_type": type(error).__name__ if error else None,
            "stamps": stamps,
        })
        self.assertEqual(before, after, "Helper modified its source or read-only database")
        if expected_error is not None:
            self.assertIsInstance(error, ValueError, "Malformed fixture must fail with ValueError")
            self.assertRegex(str(error).lower(), expected_error)
        else:
            if error is not None:
                raise error
            self.assertIsInstance(reports, list)
            self.assertEqual(len(reports), 1)
            self.assertEqual(reports[0]["original_rows_checked"], 3)
            self.assertEqual(reports[0]["missing_or_mismatched_rows"], 0)
            self.assertEqual(reports[0]["parser_sha256"], file_hashes(self.parser_path)["sha256"])

    def test_holdout_source_membership_and_count_pass(self) -> None:
        for extension in ("txt", "pos"):
            with self.subTest(extension=extension):
                self.check_helper(*self.make_fixture("valid", extension))

    def test_holdout_source_missing_key_is_rejected(self) -> None:
        for extension in ("txt", "pos"):
            with self.subTest(extension=extension):
                self.check_helper(*self.make_fixture("missing-key", extension, missing_key=True),
                                  expected_error=r"missing|membership|mismatch")

    def test_holdout_source_wrong_row_count_is_rejected(self) -> None:
        for extension in ("txt", "pos"):
            with self.subTest(extension=extension):
                root, database, source, summary = self.make_fixture("wrong-count", extension)
                summary["holdouts"][0]["rows"] = 4
                self.check_helper(root, database, source, summary, expected_error=r"row|count")

    def test_holdout_frozen_parser_mismatch_is_rejected(self) -> None:
        root, database, source, summary = self.make_fixture("wrong-parser", "txt")
        expected = summary["implementation"]["forge_pos.py"]
        expected["sha256"] = "0" * 64
        self.check_helper(root, database, source, summary,
                          expected_error=r"parser|implementation|frozen")


if __name__ == "__main__":
    unittest.main()

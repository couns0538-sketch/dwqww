#!/usr/bin/env python3
"""Byte-preservation and bounded-output regression tests for hosted evidence."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github/hosted-tt-refresh-strength/archive_results.py"
SPEC = importlib.util.spec_from_file_location("archive_results", SCRIPT)
archiver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(archiver)


class ArchiveResultsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.input = self.root / "hosted-results"
        self.output = self.root / "archived-results"
        self.input.mkdir()
        self.payloads = {
            "source/engine.cpp": b"// frozen source\r\nint main() {}\r\n",
            "binaries/engine": bytes(range(256)) * 4,
            "logs/fastchess.log": b"\xff\x00\xfeaborted\r\nunterminated",
            "games/game.pgn": b'[Event "frozen"]\r\n\r\n1. e4 e5 *\r\n',
            "manifest.json": b"original input must survive this name collision",
            "empty": b"",
        }
        for relative, data in self.payloads.items():
            path = self.input / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    def archive(self, split_size=archiver.DEFAULT_SPLIT_SIZE):
        return archiver.archive_results(self.input, self.output, "promotion-see-strength-123-2", split_size)

    def check_payloads(self, path):
        manifest = archiver.verify_archive(path)
        combined = self.root / "reassembled.zip"
        digest = hashlib.sha256()
        with combined.open("wb") as target:
            for part in manifest["parts"]:
                data = (path.parent / part["file"]).read_bytes()
                self.assertEqual(len(data), part["size"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), part["sha256"])
                target.write(data)
                digest.update(data)
        self.assertEqual(digest.hexdigest(), manifest["archive"]["sha256"])
        self.assertEqual(combined.stat().st_size, manifest["archive"]["size"])
        with zipfile.ZipFile(combined) as archive:
            inner = json.loads(archive.read("manifest.json"))
            self.assertEqual(inner["files"], manifest["files"])
            self.assertEqual(len(inner["files"]), len(self.payloads))
            for row in inner["files"]:
                data = archive.read("files/" + row["path"])
                self.assertEqual(data, self.payloads[row["path"]])
                self.assertEqual(len(data), row["size"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256"])
        return manifest

    def test_single_zip_preserves_every_input_byte_and_does_not_write_input(self):
        before = {path: path.stat() for path in self.input.rglob("*")}
        path = self.archive()
        manifest = self.check_payloads(path)
        self.assertEqual([part["file"] for part in manifest["parts"]], ["promotion-see-strength-123-2.zip"])
        self.assertEqual(set(before), set(self.input.rglob("*")))
        for input_path, old_stat in before.items():
            self.assertEqual(input_path.stat().st_mtime_ns, old_stat.st_mtime_ns)
        for relative, data in self.payloads.items():
            self.assertEqual((self.input / relative).read_bytes(), data)

    def test_tiny_parts_reassemble_to_valid_zip_and_all_files_verify(self):
        path = self.archive(split_size=257)
        manifest = self.check_payloads(path)
        self.assertGreater(len(manifest["parts"]), 2)
        self.assertFalse((self.output / "promotion-see-strength-123-2.zip").exists())
        for index, part in enumerate(manifest["parts"], 1):
            self.assertEqual(part["file"], f"promotion-see-strength-123-2.zip.part{index:04d}")
            self.assertLessEqual(part["size"], 257)
            if index < len(manifest["parts"]):
                self.assertEqual(part["size"], 257)
        self.assertEqual(len(list(self.output.iterdir())), len(manifest["parts"]) + 1)

    def test_output_inside_input_is_rejected_before_creating_it(self):
        nested = self.input / "new/output"
        with self.assertRaisesRegex(ValueError, "inside the input"):
            archiver.archive_results(self.input, nested, "test")
        self.assertFalse(nested.exists())
        with self.assertRaisesRegex(ValueError, "inside the input"):
            archiver.archive_results(self.input, self.input, "test")
        alias = self.root / "input-alias"
        alias.symlink_to(self.input, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "inside the input"):
            archiver.archive_results(self.input, alias / "nested", "test")

    def test_tampered_archive_part_is_detected(self):
        path = self.archive(split_size=257)
        manifest = json.loads(path.read_text())
        part = self.output / manifest["parts"][0]["file"]
        with part.open("r+b") as stream:
            original = stream.read(1)
            stream.seek(0)
            stream.write(bytes([original[0] ^ 1]))
        with self.assertRaisesRegex(ValueError, "part integrity failure"):
            archiver.verify_archive(path)

    def test_per_file_hash_is_independently_verified(self):
        path = self.archive()
        manifest = json.loads(path.read_text())
        manifest["files"][0]["sha256"] = "0" * 64
        archive_path = self.output / manifest["parts"][0]["file"]
        # Retain valid ZIP CRCs and matching outer hashes while corrupting only
        # the claimed per-file SHA in both manifests.
        replacement = self.root / "replacement.zip"
        with zipfile.ZipFile(archive_path) as original, zipfile.ZipFile(replacement, "w") as target:
            for member in original.namelist():
                data = original.read(member)
                if member == "manifest.json":
                    data = json.dumps({"schema_version": 1, "files": manifest["files"]}).encode()
                target.writestr(member, data)
        replacement.replace(archive_path)
        archive_bytes = archive_path.read_bytes()
        for row in (manifest["archive"], manifest["parts"][0]):
            row["size"] = len(archive_bytes)
            row["sha256"] = hashlib.sha256(archive_bytes).hexdigest()
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "Input file integrity failure"):
            archiver.verify_archive(path)

    def test_log_over_100_megabytes_is_streamed_and_verified(self):
        path = self.input / "logs/large.log"
        large_size = 101 * 1024 * 1024 + 17
        with path.open("wb") as stream:
            stream.seek(large_size - 4)
            stream.write(b"\x00\xff\r\n")
        manifest_path = self.archive()
        manifest = archiver.verify_archive(manifest_path)
        row = next(row for row in manifest["files"] if row["path"] == "logs/large.log")
        self.assertEqual(row["size"], large_size)
        digest = hashlib.sha256()
        with path.open("rb") as source:
            while True:
                block = source.read(1024 * 1024)
                if not block:
                    break
                digest.update(block)
        self.assertEqual(row["sha256"], digest.hexdigest())

    def test_existing_outputs_are_preserved(self):
        path = self.archive()
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            self.archive()
        self.assertEqual(path.read_bytes(), original)

    def test_cli_and_default_split_size(self):
        self.assertEqual(archiver.DEFAULT_SPLIT_SIZE, 64 * 1024 * 1024)
        result = subprocess.run([sys.executable, str(SCRIPT), "--input", str(self.input),
                                 "--out", str(self.output), "--name", "promotion-see-strength-7-1",
                                 "--split-size", "257"], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest_path = Path(result.stdout.strip())
        self.assertTrue(manifest_path.is_file())
        self.check_payloads(manifest_path)


if __name__ == "__main__":
    unittest.main()

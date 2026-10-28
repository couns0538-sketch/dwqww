#!/usr/bin/env python3
"""Contract tests for the standalone UCI bundle option checker."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CHECKER = Path(__file__).resolve().parents[1] / "tools" / "check_bundle_opts.py"
HASH = "option name Hash type spin default 16 min 1 max 2048"


class OptionTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(CHECKER.is_file(), "bundle option checker must exist")
        spec = importlib.util.spec_from_file_location("bundle_opts", CHECKER)
        self.checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.checker)

    def test_multiword_names_and_valid_defaults(self):
        options = self.checker.parse_options([
            HASH, "option name Move Overhead type spin default 5 min 0 max 5000",
            "option name Book File type string default a file with spaces.bin",
            "option name Ponder type check default false",
            "option name Clear Hash type button",
            "option name Playing Style type combo default Very Fast var Normal var Very Fast",
            "uciok",
        ])
        self.assertEqual(options["Move Overhead"]["min"], 0)
        self.assertEqual(options["Hash"]["default"], 16)
        self.assertEqual(options["Ponder"]["default"], False)
        self.assertEqual(options["Book File"]["default"], "a file with spaces.bin")

    def test_spin_fields_can_be_reordered(self):
        options = self.checker.parse_options([
            "option name Signed type spin max 5 min -5 default -1", "uciok"])
        self.assertEqual(options["Signed"]["default"], -1)

    def test_uci_field_whitespace(self):
        options = self.checker.parse_options([
            "option\tname Ponder\ttype check default\tfalse",
            "option name Book File type string default\ta file.bin",
            "option name Style type combo default   Very Fast var\tVery Fast var Slow",
            "uciok"])
        self.assertEqual(options["Ponder"]["default"], False)
        self.assertEqual(options["Book File"]["default"], "a file.bin")
        self.assertEqual(options["Style"]["default"], "Very Fast")

    def test_malformed_or_duplicate_advertisement_rejected(self):
        invalid = [
            HASH + " junk", "option name Hash type spin default 0 min 1 max 2",
            "option name Hash type spin default 2 min 3 max 1",
            "option name Hash type spin default 1 max 2",
            "option name Hash type spin default x min 1 max 2",
            "option name Hash type spin default 1 min 1 min 2 max 3",
            "option name Hash type nonsense", "option name type button",
            "option name Ponder type check default maybe",
            "option name Clear Hash type button default true",
            "option name Style type combo default Fast var Slow",
        ]
        for line in invalid:
            with self.subTest(line=line), self.assertRaises(ValueError):
                self.checker.parse_options([line, "uciok"])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.checker.parse_options([HASH, HASH, "uciok"])

    def test_spec_names_and_ranges(self):
        spec = self.checker.validate_spec({"options": [
            "Ponder", {"name": "Hash", "type": "spin", "min": 1, "max": 2048, "default": 16}]})
        self.assertEqual(spec[0], {"name": "Ponder"})
        self.checker.check_options(self.checker.parse_options([
            HASH, "option name Ponder type check default false", "uciok"]), spec)

    def test_unknown_or_malformed_spec_rejected(self):
        invalid = [
            [], {}, {"options": "Hash"}, {"options": [], "unknown": 1},
            {"options": [{"name": "Hash", "maxx": 2}]},
            {"options": ["Hash", "Hash"]}, {"options": [""]},
            {"options": [5]}, {"options": [{"name": "Hash", "type": "odd"}]},
            {"options": [{"name": "Hash", "min": True}]},
            {"options": [{"name": "Hash", "min": 4, "max": 2}]},
            {"options": [{"name": "Ponder", "type": "check", "min": 0}]},
            {"options": [{"name": "Hash", "type": "spin", "default": "16"}]},
            {"options": [{"name": "Ponder", "type": "check", "default": "false"}]},
            {"options": [{"name": "Clear Hash", "type": "button", "default": False}]},
            {"options": [{"name": "Hash", "default": []}]},
            {"options": [{"name": "Hash", "min": 1, "max": 3, "default": 4}]},
        ]
        for spec in invalid:
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                self.checker.validate_spec(spec)

    def test_missing_wrong_type_range_or_default_rejected(self):
        actual = self.checker.parse_options([HASH, "uciok"])
        for expected in [{"name": "Missing"}, {"name": "Hash", "type": "check"},
                         {"name": "Hash", "min": 2}, {"name": "Hash", "max": 4096},
                         {"name": "Hash", "default": 32}]:
            with self.subTest(expected=expected), self.assertRaises(ValueError):
                self.checker.check_options(actual, [expected])


@unittest.skipUnless(os.name == "posix", "fake executables use POSIX shebangs")
class CliTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(CHECKER.is_file(), "bundle option checker must exist")
        self.temp = tempfile.TemporaryDirectory(prefix="bundle opts ")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def run_checker(self, lines=None, *, code=0, hang=False, args=None):
        engine = self.folder / "fake engine"
        output = (lines if lines is not None else [HASH, "uciok"])
        engine.write_text(
            f"#!{sys.executable}\nimport sys, time\n"
            "for command in sys.stdin:\n"
            "    if command.strip() == 'uci':\n"
            f"        print({chr(10).join(output)!r}, flush=True)\n"
            "    if command.strip() == 'quit':\n"
            f"        time.sleep({10 if hang else 0})\n"
            f"        sys.exit({code})\n", encoding="utf-8")
        engine.chmod(0o700)
        return subprocess.run(
            [sys.executable, str(CHECKER), str(engine), *(args or ["--require", "Hash"]),
             "--timeout", "0.3"], capture_output=True, text=True, timeout=3)

    def test_success(self):
        result = self.run_checker()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_spec_and_required_multiword_name(self):
        spec = self.folder / "spec.json"
        spec.write_text(json.dumps({"options": [{"name": "Hash", "type": "spin", "min": 1,
                                                "max": 2048, "default": 16}]}))
        result = self.run_checker([HASH, "option name Clear Hash type button", "uciok"],
                                  args=["--spec", str(spec), "--require", "Clear Hash"])
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_option(self):
        result = self.run_checker(["uciok"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Hash", result.stderr)

    def test_wrong_range(self):
        spec = self.folder / "spec.json"
        spec.write_text('{"options":[{"name":"Hash","max":4096}]}')
        result = self.run_checker(args=["--spec", str(spec)])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("max", result.stderr)

    def test_missing_uciok(self):
        result = self.run_checker([HASH, "info string uciok"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("uciok", result.stderr)

    def test_duplicate_option(self):
        result = self.run_checker([HASH, HASH, "uciok"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate", result.stderr)

    def test_nonzero_exit(self):
        result = self.run_checker(code=7)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("7", result.stderr)

    def test_timeout(self):
        result = self.run_checker(hang=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("timed out", result.stderr)

    def test_invalid_spec_and_duplicate_json_key(self):
        for data in ['{', '{"options":["Hash"],"oops":0}',
                     '{"options":["Missing"],"options":["Hash"]}']:
            with self.subTest(data=data):
                spec = self.folder / "spec.json"
                spec.write_text(data)
                result = self.run_checker(args=["--spec", str(spec)])
                self.assertNotEqual(result.returncode, 0)

    def test_invalid_timeout(self):
        for timeout in ["nan", "inf", "0", "-1"]:
            with self.subTest(timeout=timeout):
                result = subprocess.run([sys.executable, str(CHECKER), "missing", "--require", "Hash",
                                         "--timeout", timeout], capture_output=True, text=True, timeout=3)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("timeout", result.stderr)


if __name__ == "__main__":
    unittest.main()

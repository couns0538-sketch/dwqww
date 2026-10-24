#!/usr/bin/env python3
"""Unit tests only: fake producers, never a chess engine or benchmark."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOL = Path(__file__).with_name("nnue_abba_bench.py")
if TOOL.exists():
    SPEC = importlib.util.spec_from_file_location("abba", TOOL)
    abba = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(abba)
else:
    abba = None

ROW = b"info string bench depth 20 nodes 11901452 time 1000 nps 11901452\n"


class Availability(unittest.TestCase):
    def test_runner_implementation_exists(self):
        self.assertTrue(TOOL.is_file(), "missing ABBA runner implementation")


@unittest.skipIf(abba is None, "implementation absent during RED phase")
class ProtocolTests(unittest.TestCase):
    def test_four_abba_blocks_cover_eight_disjoint_pairs_after_two_warmups_each(self):
        plan = abba.sequence(4)
        self.assertEqual([p["role"] for p in plan[:4]], ["OFF", "ON", "OFF", "ON"])
        self.assertTrue(all(p["pair"] is None for p in plan[:4]))
        for block in range(4):
            rows = plan[4 + block * 4:8 + block * 4]
            self.assertEqual([p["role"] for p in rows], ["OFF", "ON", "ON", "OFF"])
            self.assertEqual([p["pair"] for p in rows], [2*block, 2*block, 2*block+1, 2*block+1])
        for pair in range(8):
            self.assertEqual(sorted(p["role"] for p in plan if p["pair"] == pair), ["OFF", "ON"])
        with self.assertRaises(ValueError):
            abba.sequence(3)

    def test_parser_uses_engine_nps_and_rejects_bad_nodes_time_duplicate_or_inconsistent_nps(self):
        self.assertEqual(abba.parse_row(ROW)["nps"], 11901452)
        bad = [ROW.replace(b"11901452", b"11901453", 1),
               ROW.replace(b"time 1000", b"time 0"),
               ROW.replace(b"nps 11901452", b"nps 7"), ROW + ROW,
               ROW.replace(b"depth 20", b"depth 19"), b"not a bench report\n"]
        for raw in bad:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                abba.parse_row(raw)

    def test_summary_reports_all_pairs_and_ignores_process_wall_as_a_metric(self):
        rows = [{**p, "nps": 100 if p["role"] == "OFF" else 200,
                 "wall_seconds": 999 if p["role"] == "ON" else 1}
                for p in abba.sequence(4)]
        report = abba.summarize(rows, 4)
        self.assertEqual(report["on_off_pair_ratios"], [2.0] * 8)
        self.assertEqual((report["median_ratio"], report["min_ratio"], report["max_ratio"]), (2, 2, 2))
        with self.assertRaises(ValueError):
            abba.summarize(rows[:-1], 4)

    def test_actual_nonzero_producer_retains_exact_streams_stdin_argv_and_exit(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            code = "import sys; sys.stdout.buffer.write(" + repr(ROW) + "); sys.stderr.write('producer failure\\n'); sys.exit(7)"
            result = abba.capture([sys.executable, "-c", code], b"exact input\n", folder, 2)
            self.assertEqual(result["actual_exit"], 7)
            self.assertEqual((folder / "stdout.bin").read_bytes(), ROW)
            self.assertEqual((folder / "stderr.bin").read_bytes(), b"producer failure\n")
            self.assertEqual((folder / "stdin.bin").read_bytes(), b"exact input\n")
            self.assertEqual(json.loads((folder / "process.json").read_text())["argv"], result["argv"])

    def test_timeout_preserves_partial_output_and_reaps_actual_fake_producer(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            code = "import sys,time; print('partial',flush=True); print('partial error',file=sys.stderr,flush=True); time.sleep(5)"
            result = abba.capture([sys.executable, "-c", code], b"", folder, 0.5)
            self.assertEqual(result["status"], "TIMEOUT")
            self.assertIsNotNone(result["actual_exit"])
            self.assertEqual((folder / "stdout.bin").read_bytes(), b"partial\n")
            self.assertEqual((folder / "stderr.bin").read_bytes(), b"partial error\n")

    def test_profile_precedes_launch_and_first_failure_stops_without_replacement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            (root / "src/nnue.cpp").write_text("frozen test source\n")
            binary = root / "fake-engine"
            binary.write_text("not launched\n")
            out = root / "evidence"
            args = abba.arguments(["--baseline", str(binary), "--candidate", str(binary),
                                   "--out", str(out), "--baseline-source", str(root),
                                   "--candidate-source", str(root)])
            launches = []
            def fake_capture(argv, stdin, sample, timeout):
                profile = json.loads((out / "profile.json").read_text())
                self.assertEqual(len(profile["sequence"]), 20)
                self.assertEqual(profile["cpu"]["selected"], 4)
                self.assertEqual((out / "stdin.bin").read_bytes(), stdin)
                self.assertEqual(argv[:3], ["/fake/taskset", "-c", "4"])
                launches.append(argv)
                raw = ROW if len(launches) < 7 else ROW + b"producer exited nonzero\n"
                sample.mkdir(exist_ok=True)
                (sample / "stdout.bin").write_bytes(raw)
                (sample / "stderr.bin").write_bytes(b"failure evidence\n")
                return {"actual_exit": 0 if len(launches) < 7 else 7, "status": "EXITED", "wall_seconds": 0.01}
            with patch.object(abba.shutil, "which", return_value="/fake/taskset"), \
                 patch.object(abba.os, "sched_getaffinity", return_value={0,1,2,3,4}), \
                 patch.object(abba, "capture", side_effect=fake_capture):
                self.assertEqual(abba.run(args), 1)
                self.assertEqual(len(launches), 7)  # warmups4 + OFF ON ON; third block leg fails
                summary = json.loads((out / "summary.json").read_text())
                self.assertEqual(summary["status"], "FAILED")
                self.assertNotIn("on_off_pair_ratios", summary)
                self.assertIn(b"producer exited nonzero", (out / "006/stdout.bin").read_bytes())
                with self.assertRaises(FileExistsError):
                    abba.run(args)

    def test_missing_taskset_or_unavailable_selected_cpu_is_a_preflight_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            binary = Path(temp) / "fake"
            binary.write_text("not launched")
            args = abba.arguments(["--baseline", str(binary), "--candidate", str(binary),
                                   "--out", str(Path(temp)/"out")])
            with patch.object(abba.shutil, "which", return_value=None), self.assertRaises(ValueError):
                abba.preflight(args)
            with patch.object(abba.shutil, "which", return_value="/fake/taskset"), \
                 patch.object(abba.os, "sched_getaffinity", return_value={0,1}), self.assertRaises(ValueError):
                abba.preflight(args)

    def test_changed_source_after_sample_stops_before_a_second_producer_launch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            source = root / "src/nnue.cpp"
            source.write_text("frozen\n")
            binary = root / "fake"
            binary.write_text("not launched")
            args = abba.arguments(["--baseline", str(binary), "--candidate", str(binary),
                                   "--out", str(root/"out"), "--baseline-source", str(root),
                                   "--candidate-source", str(root)])
            def fake_capture(argv, stdin, sample, timeout):
                (sample / "stdout.bin").write_bytes(ROW)
                (sample / "stderr.bin").write_bytes(b"")
                source.write_text("changed while producer was active\n")
                return {"status": "EXITED", "actual_exit": 0, "wall_seconds": 1}
            with patch.object(abba.shutil, "which", return_value="/fake/taskset"), \
                 patch.object(abba.os, "sched_getaffinity", return_value={4}), \
                 patch.object(abba, "capture", side_effect=fake_capture) as launch:
                self.assertEqual(abba.run(args), 1)
            self.assertEqual(launch.call_count, 1)
            summary = json.loads((root / "out/summary.json").read_text())
            self.assertIn("changed during sample", summary["error"])
            record = json.loads((root / "out/000/sample.json").read_text())
            self.assertNotEqual(record["before"]["source_sha256"], record["after"]["source_sha256"])
            self.assertEqual((root / "out/000/stdout.bin").read_bytes(), ROW)

    def test_launch_error_records_the_actual_missing_executable_and_empty_streams(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            argv = [str(folder / "does-not-exist")]
            result = abba.capture(argv, b"quit\n", folder, 1)
            self.assertEqual(result["status"], "LAUNCH_ERROR")
            self.assertIsNone(result["actual_exit"])
            self.assertEqual(result["argv"], argv)
            self.assertEqual((folder / "stdout.bin").read_bytes(), b"")
            self.assertEqual((folder / "stderr.bin").read_bytes(), b"")

    def test_interrupt_reaps_the_producer_and_persists_failure_metadata(self):
        class InterruptedProducer:
            returncode = None
            def __init__(self, argv, **kwargs):
                kwargs["stdout"].write(b"partial interrupt evidence\n")
            def communicate(self, *args, **kwargs):
                raise KeyboardInterrupt()
            def poll(self):
                return self.returncode
            def kill(self):
                self.returncode = -9
            def wait(self):
                return self.returncode
        with tempfile.TemporaryDirectory() as temp, patch.object(abba.subprocess, "Popen", InterruptedProducer):
            folder = Path(temp)
            try:
                result = abba.capture(["fake-producer"], b"", folder, 1)
            except KeyboardInterrupt:
                self.fail("interruption bypassed the producer failure record")
            self.assertEqual(result["status"], "INTERRUPTED")
            self.assertEqual(result["actual_exit"], -9)
            self.assertEqual((folder / "stdout.bin").read_bytes(), b"partial interrupt evidence\n")
            self.assertEqual(json.loads((folder / "process.json").read_text())["status"], "INTERRUPTED")


if __name__ == "__main__":
    unittest.main()

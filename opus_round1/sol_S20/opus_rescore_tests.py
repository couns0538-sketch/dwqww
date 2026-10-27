"""Tests for opus_rescore.py. Needs a Forge engine: set S20_ENGINE (default: the rescoring build in
F:\\opus_scratch\\rescore_d8\\bin); engine tests are skipped without it. Temporary folders are created in TMP (run with
TMP=F:\\opus_scratch\\rescore_d8\\tmp so nothing is written elsewhere). Run: python -I -B opus_rescore_tests.py"""
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
TOOL = HERE / "opus_rescore.py"
spec = importlib.util.spec_from_file_location("opus_rescore", TOOL)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)
ENGINE = os.environ.get("S20_ENGINE", r"F:\opus_scratch\rescore_d8\bin\forge_al1_rescore.exe")
HAVE_ENGINE = Path(ENGINE).is_file()

LINES = [
    "4k3/8/8/8/8/8/8/3QK3 w - - 0 1 | 0 | 1",            # white to move, a queen up: STM score > 0
    "4k3/8/8/8/8/8/8/3QK3 b - - 0 1 | 0 | 1",            # black to move, a queen down: STM score < 0
    "3qk3/8/8/8/8/8/8/4K3 w - - 0 1 | 0 | 0",            # white to move, a queen down: < 0
    "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1 | 0 | 1",         # white mates in 1 (Ra8#): mate -> +max-score
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 | 17 | 0.5",
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3 | 30 | 0.5",
]


def run_tool(inp: Path, out: Path, *extra):
    return subprocess.run([sys.executable, "-I", "-B", str(TOOL), "--engine", ENGINE, "--in", str(inp), "--out-dir", str(out),
                           "--depth", "6", "--allowed-root", str(out.parent), *map(str, extra)], capture_output=True, text=True)


def scores(path: Path):
    return [int(line.split("|")[1]) for line in path.read_text(encoding="utf-8").splitlines()]


class Pure(unittest.TestCase):
    def test_mate_and_clip(self):
        self.assertEqual(tool.to_cp("mate", 3, 3000), (3000, True, False))
        self.assertEqual(tool.to_cp("mate", -1, 3000), (-3000, True, False))
        self.assertEqual(tool.to_cp("cp", 4500, 3000), (3000, False, True))
        self.assertEqual(tool.to_cp("cp", -120, 3000), (-120, False, False))

    def test_blend(self):
        self.assertEqual(tool.blend_score(250, 1.0, 1.0, 2.25, 3000), 250)       # 1.0 = pure score (f006 default)
        self.assertEqual(tool.blend_score(250, 1.0, 0.0, 2.25, 3000), 3000)      # pure result: clipped
        self.assertEqual(tool.blend_score(0, 0.5, 0.0, 2.25, 3000), 0)
        s = tool.blend_score(100, 0.0, 0.6, 2.25, 3000)                         # the f006 end-of-training target
        target = 0.6 / (1 + math.exp(-100 * 2.25 / 400))
        self.assertAlmostEqual(1 / (1 + math.exp(-s * 2.25 / 400)), target, delta=0.002)

    def test_parse_line(self):
        fen, old, result_text, result, stm = tool.parse_line("8/8/8/8/8/8/8/K6k b - - 0 1 | -5 | 0.5")
        self.assertEqual((old, result_text, result, stm), (-5, "0.5", 0.5, "b"))
        for bad in ("8/8/8/8/8/8/8/K6k x - - 0 1 | 1 | 1", "8/8 w - - 0 1 | 1 | 1", "8/8/8/8/8/8/8/K6k w - - 0 1 | 1 | 2",
                    "8/8/8/8/8/8/8/K7 w - - 0 1 | 1 | 1", "8/8/8/8/8/8/8/K6k w - - 0 1 | x | 1"):
            with self.assertRaises(ValueError):
                tool.parse_line(bad)


@unittest.skipUnless(HAVE_ENGINE, "no engine (set S20_ENGINE)")
class WithEngine(unittest.TestCase):
    def test_sign_convention_mate_and_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "in.txt").write_text("\n".join(LINES) + "\nnot a line\n", encoding="utf-8")
            r = run_tool(tmp / "in.txt", tmp / "run")
            self.assertEqual(r.returncode, 0, r.stderr)
            got = scores(tmp / "run" / "rescored.txt")
            self.assertGreater(got[0], 500)       # STM (white) a queen up
            self.assertLess(got[1], -500)         # STM (black) a queen down
            self.assertLess(got[2], -500)         # STM (white) a queen down
            self.assertEqual(got[3], 3000)        # white mates in 1
            out_lines = (tmp / "run" / "rescored.txt").read_text(encoding="utf-8").splitlines()
            for src, dst in zip(LINES, out_lines):
                self.assertEqual(src.split("|")[0].strip(), dst.split("|")[0].strip())   # same FEN
                self.assertEqual(src.split("|")[2].strip(), dst.split("|")[2].strip())   # same WHITE result
            stats = json.loads((tmp / "run" / "rescored.txt.stats.json").read_text(encoding="utf-8"))
            self.assertEqual((stats["lines"], stats["bad_lines"], stats["mates"]), (6, 1, 1))

    def test_deterministic_and_order_independent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "a.txt").write_text("\n".join(LINES) + "\n", encoding="utf-8")
            (tmp / "b.txt").write_text("\n".join(reversed(LINES)) + "\n", encoding="utf-8")
            for name, src in (("a", "a"), ("b", "b"), ("a2", "a")):
                r = run_tool(tmp / f"{src}.txt", tmp / f"run_{name}")
                self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual((tmp / "run_a" / "rescored.txt").read_bytes(), (tmp / "run_a2" / "rescored.txt").read_bytes())
            self.assertEqual(scores(tmp / "run_a" / "rescored.txt"), list(reversed(scores(tmp / "run_b" / "rescored.txt"))))

    def test_resume_redoes_only_bad_or_missing_chunks(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "in.txt").write_text("\n".join(LINES) + "\n", encoding="utf-8")
            r = run_tool(tmp / "in.txt", tmp / "run", "--chunk-lines", "2")
            self.assertEqual(r.returncode, 0, r.stderr)
            reference = (tmp / "run" / "rescored.txt").read_bytes()
            progress = json.loads((tmp / "run" / "progress.json").read_text(encoding="utf-8"))
            self.assertEqual(sorted(progress["chunks"]), ["chunk_00000.txt", "chunk_00001.txt", "chunk_00002.txt"])
            # a finished run restarts without searching again
            r = run_tool(tmp / "in.txt", tmp / "run", "--chunk-lines", "2")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertNotIn("chunk_0000", r.stdout.split("{")[0])
            # a damaged chunk and a stale partial file: only chunk 1 is redone, the result is unchanged
            (tmp / "run" / "chunk_00001.txt").write_text("damaged\n", encoding="utf-8")
            (tmp / "run" / "chunk_00002.txt.partial").write_text("stale\n", encoding="utf-8")
            r = run_tool(tmp / "in.txt", tmp / "run", "--chunk-lines", "2")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("chunk_00001.txt:", r.stdout)
            self.assertNotIn("chunk_00000.txt:", r.stdout)
            self.assertEqual((tmp / "run" / "rescored.txt").read_bytes(), reference)
            # other parameters against the same progress file are refused
            r = run_tool(tmp / "in.txt", tmp / "run", "--chunk-lines", "3")
            self.assertNotEqual(r.returncode, 0)

    def test_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "in.txt").write_text("\n".join(LINES[:2]) + "\n", encoding="utf-8")
            r = subprocess.run([sys.executable, "-I", "-B", str(TOOL), "--engine", ENGINE, "--in", str(tmp / "in.txt"),
                                "--out-dir", str(tmp / "x"), "--allowed-root", str(tmp / "elsewhere")], capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            r = run_tool(tmp / "in.txt", tmp / "run", "--hash", "128")
            self.assertNotEqual(r.returncode, 0)
            r = run_tool(tmp / "in.txt", tmp / "run", "--limit", "1", "--blend", "0.0")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(scores(tmp / "run" / "rescored.txt"), [3000])   # pure result, white won, white to move


if __name__ == "__main__":
    unittest.main(verbosity=2)

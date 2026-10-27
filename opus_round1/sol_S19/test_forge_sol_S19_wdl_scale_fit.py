"""Tests for forge_sol_S19_wdl_scale_fit.py (numpy; run with the NNUE venv python: python -I -B <this file>).
Set S19_SAMPLE_DIR to the lock archive's 5_nnue/sample_data folder for the real-sample cross-check (skipped if
the folder is absent)."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

HERE = Path(__file__).resolve().parent
TOOL = HERE / "forge_sol_S19_wdl_scale_fit.py"
spec = importlib.util.spec_from_file_location("s19_tool", TOOL)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)
SAMPLE = Path(os.environ.get("S19_SAMPLE_DIR", r"D:\grok-pc-data\dwqww\.claude\worktrees\b\pkg\forge_LOCK_AL1_s198_FULL_20261026_1039\5_nnue\sample_data"))
PIECES = {"P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6, "p": 7, "n": 8, "b": 9, "r": 10, "q": 11, "k": 12}


def encode_board(placement: str) -> bytes:
    """FEN placement -> the 32-byte .pos board (square a1 = 0, byte s >> 1, low nibble for even s)."""
    squares = [0] * 64
    for rank_index, rank in enumerate(placement.split("/")):
        file = 0
        for ch in rank:
            if ch.isdigit():
                file += int(ch)
            else:
                squares[(7 - rank_index) * 8 + file] = PIECES[ch]
                file += 1
    return bytes(squares[2 * i] | (squares[2 * i + 1] << 4) for i in range(32))


def write_pos(path: Path, rows) -> None:
    """rows: (placement, stm 'w'/'b', stm_cp, white_result)"""
    n = len(rows)
    boards = b"".join(encode_board(r[0]) for r in rows)
    score = np.asarray([r[2] for r in rows], "<i2").tobytes()
    meta = bytes((1 if r[1] == "b" else 0) | (int(round(r[3] * 2)) << 1) for r in rows)
    path.write_bytes(b"FPOS" + (1).to_bytes(4, "little") + n.to_bytes(8, "little") + boards + score + meta)


START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"


class Phase(unittest.TestCase):
    def test_fen_phase_values(self):
        self.assertEqual(tool.fen_phase(START), 24)
        self.assertEqual(tool.fen_phase("4k3/8/8/8/8/8/8/4K3"), 0)
        self.assertEqual(tool.fen_phase("4k3/8/8/8/8/8/8/3QK3"), 4)
        self.assertEqual(tool.fen_phase("4k3/pppppppp/8/8/8/8/PPPPPPPP/4K3"), 0)
        self.assertEqual(tool.fen_phase("QQQQk3/8/8/8/8/8/8/QQQQK3"), 24)  # clamped at MaxPhase

    def test_pos_phase_equals_fen_phase(self):
        boards = [START, "4k3/8/8/8/8/8/8/4K3", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R",
                  "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8", "QQQQk3/8/8/8/8/8/8/QQQQK3"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.pos"
            write_pos(path, [(b, "w", 0, 0.5) for b in boards])
            data = tool.read_pos(path)
        self.assertEqual(list(data["phase"]), [tool.fen_phase(b) for b in boards])


class Reading(unittest.TestCase):
    def test_stm_result_and_score_decoding(self):
        rows = [(START, "w", 100, 1.0), (START, "b", -50, 1.0), (START, "w", 0, 0.5), (START, "b", 20, 0.0)]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.pos"
            write_pos(path, rows)
            data = tool.read_pos(path)
        self.assertEqual(list(data["score"]), [100.0, -50.0, 0.0, 20.0])
        self.assertEqual(list(data["result"]), [1.0, 0.0, 0.5, 1.0])  # side to move's result

    def test_stride_takes_every_kth_row(self):
        rows = [(START, "w", i, 0.5) for i in range(11)]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.pos"
            write_pos(path, rows)
            full, every3 = tool.read_pos(path), tool.read_pos(path, 3)
        self.assertEqual(list(every3["score"]), list(full["score"][::3]))
        self.assertEqual(every3["file_rows"], 11)

    def test_bad_header_and_size_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.pos"
            write_pos(path, [(START, "w", 0, 0.5)])
            path.write_bytes(path.read_bytes()[:-1])
            with self.assertRaises(ValueError):
                tool.read_pos(path)
            path.write_bytes(b"XPOS" + bytes(12))
            with self.assertRaises(ValueError):
                tool.read_pos(path)

    def test_text_games_clip_and_stm(self):
        text = "\n".join([
            f"{START} w KQkq - 0 1 | 30 | 1",
            f"{START} b KQkq - 1 1 | 32000 | 1",              # clipped to 3000; black to move: result 0 for stm
            "4k3/8/8/8/8/8/8/3QK3 w - - 0 40 | 900 | 1",        # same game: fullmove up, pieces down
            f"{START} w KQkq - 0 1 | 10 | 1",                  # fullmove falls: new game
            f"{START} w KQkq - 0 2 | 10 | 0.5",                # result changes: new game
            "garbage line",
        ]) + "\n"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.txt"
            path.write_text(text, encoding="utf-8")
            data = tool.read_text(path)
        self.assertEqual(data["games"], 3)
        self.assertEqual(list(data["group"]), [0, 0, 0, 1, 2])
        self.assertEqual(data["bad_lines"], 1)
        self.assertEqual(list(data["score"]), [30.0, 3000.0, 900.0, 10.0, 10.0])
        self.assertEqual(list(data["result"]), [1.0, 0.0, 1.0, 1.0, 0.5])

    @unittest.skipUnless((SAMPLE / "forge_text_sample" / "forge_selfplay_sample_916lines.pos").exists(), "no sample dir")
    def test_real_sample_text_and_pos_paths_agree(self):
        a = tool.read_text(SAMPLE / "forge_text_sample" / "forge_selfplay_sample_916lines.txt")
        b = tool.read_pos(SAMPLE / "forge_text_sample" / "forge_selfplay_sample_916lines.pos")
        self.assertEqual(a["rows"], 916)
        for key in ("score", "phase", "result"):
            self.assertTrue(np.array_equal(a[key], b[key]), key)


class Model(unittest.TestCase):
    def test_logloss_formula(self):
        score, result = np.array([0.0, 400.0, -400.0, 100.0]), np.array([0.5, 1.0, 0.0, 0.0])
        k = 2.25
        p = 1.0 / (1.0 + np.exp(-score * k / 400.0))
        direct = float(np.mean(-(result * np.log(p) + (1 - result) * np.log(1 - p))))
        self.assertAlmostEqual(tool.log_loss(score, result, k), direct, places=12)

    def test_fit_recovers_known_scales(self):
        rng = np.random.default_rng(7)
        for true_k in (1.5, 2.25, 3.5):
            score = rng.normal(0.0, 300.0, 60000)
            win = rng.random(60000) < 1.0 / (1.0 + np.exp(-score * true_k / 400.0))
            k, _ = tool.fit_k(score, win.astype(np.float64))
            self.assertAlmostEqual(k, true_k, delta=0.08 * true_k)

    def test_fit_is_a_minimum(self):
        rng = np.random.default_rng(3)
        score = rng.normal(0.0, 250.0, 5000)
        result = (rng.random(5000) < 1.0 / (1.0 + np.exp(-score * 2.0 / 400.0))).astype(np.float64)
        k, _ = tool.fit_k(score, result)
        here = tool.log_loss(score, result, k)
        self.assertLessEqual(here, tool.log_loss(score, result, k - 0.01))
        self.assertLessEqual(here, tool.log_loss(score, result, k + 0.01))

    def test_selection_rule_keeps_reference_unless_ci_excludes_it(self):
        rng = np.random.default_rng(11)
        n = 40000
        phase = np.where(np.arange(n) < n // 2, 24, 2)          # two buckets
        score = rng.normal(0.0, 300.0, n)
        true_k = np.where(phase == 24, 4.0, 2.25)              # bucket 20-24 differs, bucket 0-3 equals 2.25
        result = (rng.random(n) < 1.0 / (1.0 + np.exp(-score * true_k / 400.0))).astype(np.float64)
        data = {"score": score, "phase": phase, "result": result, "group": None, "rows": n}
        out = tool.run(data, data, tool.DEFAULT_EDGES, 60, 200, 1)
        by_from = {e["phase_from"]: e for e in out["phase_table"]}
        self.assertTrue(by_from[20]["ci_excludes_reference"])
        self.assertAlmostEqual(by_from[20]["k"], 4.0, delta=0.3)
        self.assertEqual(by_from[4]["k"], 2.25)                 # empty bucket: reference
        self.assertIn("fewer than", by_from[4]["source"])
        if not by_from[0]["ci_excludes_reference"]:
            self.assertEqual(by_from[0]["k"], 2.25)
        self.assertLessEqual(out["holdout"]["logloss_per_phase_table"], out["holdout"]["logloss_reference_k2.25"])


class Cli(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-I", "-B", str(TOOL), *map(str, args)], capture_output=True, text=True)

    def test_deterministic_output_and_no_overwrite(self):
        rng = np.random.default_rng(5)
        rows = []
        for i in range(3000):
            s = int(rng.normal(0, 300))
            rows.append((START if i % 2 else "4k3/8/8/8/8/8/8/3QK3", "w" if i % 3 else "b", s,
                         float(rng.choice([0.0, 0.5, 1.0]))))
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            write_pos(tmp / "fit.pos", rows[:2000]); write_pos(tmp / "held.pos", rows[2000:])
            outs = []
            for name in ("a.json", "b.json"):
                r = self.run_cli("--fit-pos", tmp / "fit.pos", "--holdout-pos", tmp / "held.pos", "--bootstrap", "20", "--out", tmp / name)
                self.assertEqual(r.returncode, 0, r.stderr)
                outs.append((tmp / name).read_bytes())
            self.assertEqual(hashlib.sha256(outs[0]).hexdigest(), hashlib.sha256(outs[1]).hexdigest())
            r = self.run_cli("--fit-pos", tmp / "fit.pos", "--holdout-pos", tmp / "held.pos", "--out", tmp / "a.json")
            self.assertNotEqual(r.returncode, 0)
            result = json.loads(outs[0])
            self.assertEqual(result["reference_k"], 2.25)
            self.assertTrue(result["status"].startswith("UNPROVEN"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

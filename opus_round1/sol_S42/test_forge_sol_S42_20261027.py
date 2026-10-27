#!/usr/bin/env python3
"""Tests for the S42 book builder / gate parser / power model (Opus 5.5, 2026-10-27).
Uses the SYNTHETIC fake_uci_engine_s42.py (no real engine, no games). Env: FORGE_S42_TMP = scratch dir;
FORGE_S42_TOOL / FORGE_S42_POWER override the tools under test (mutation check)."""
import csv
import hashlib
import importlib.util
import io
import json
import math
import os
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import chess
import chess.pgn
import numpy as np

HERE = Path(__file__).resolve().parent
TOOL = Path(os.environ.get("FORGE_S42_TOOL", HERE / "forge_sol_S42_book_v2_20261027.py"))
POWER = Path(os.environ.get("FORGE_S42_POWER", HERE / "forge_sol_S42_power_20261027.py"))
FAKE = HERE / "fake_uci_engine_s42.py"
SCRATCH = Path(os.environ.get("FORGE_S42_TMP", tempfile.gettempdir())) / f"s42_tests_{os.getpid()}"
SCRATCH.mkdir(parents=True, exist_ok=False)
_N = [0]


def new(tag):
    _N[0] += 1
    return SCRATCH / f"{_N[0]:03d}_{tag}"


def run(*args):
    p = subprocess.run([sys.executable, "-I", "-B", str(TOOL), *map(str, args)], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def write_book(path, lines):
    out = io.StringIO()
    for i, mv in enumerate(lines):
        g = chess.pgn.Game(); g.headers["Event"] = "?"; g.headers["Round"] = str(i + 1); node = g
        for m in mv:
            node = node.add_variation(m)
        out.write(str(g) + "\n\n")
    Path(path).write_text(out.getvalue(), encoding="utf-8")


def random_lines(n, seed, plies=16):
    rng = random.Random(seed); lines = []
    while len(lines) < n:
        b = chess.Board(); mv = []
        for _ in range(plies):
            legal = sorted(b.legal_moves, key=lambda m: m.uci())
            if not legal:
                break
            m = rng.choice(legal); b.push(m); mv.append(m)
        if len(mv) == plies and not b.is_game_over():
            lines.append(mv)
    return lines


def files_except_runinfo(d):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(d).iterdir()) if p.name != "run_info.json"}


class BookTool(unittest.TestCase):
    def test_1_build_deterministic_band_and_both_sides(self):
        book = new("book.pgn"); write_book(book, random_lines(400, 7))
        o1, o2 = new("b1"), new("b2")
        for o in (o1, o2):
            rc, so, se = run("build", "--book", book, "--engine", FAKE, "--depth", 3, "--target", 40, "--seed", 11, "--out", o)
            self.assertEqual(rc, 0, se)
        self.assertEqual(files_except_runinfo(o1), files_except_runinfo(o2))
        meta = list(csv.DictReader(io.StringIO((o1 / "forge_sol_S42_book_v2_meta_20261027.csv").read_text(encoding="utf-8"))))
        self.assertEqual(len(meta), 40)
        evs = [int(r["eval_white_cp"]) for r in meta]
        self.assertTrue(all(60 <= abs(e) <= 120 for e in evs))
        self.assertTrue(any(e > 0 for e in evs) and any(e < 0 for e in evs))
        s = json.loads((o1 / "build_summary.json").read_text())
        self.assertEqual((s["duplicates_with_current_book_exits"], s["repeats_inside_new_book"]), (0, 0))
        epd = (o1 / "forge_sol_S42_book_v2_20261027.epd").read_text().splitlines()
        self.assertEqual(epd, [r["fen"] for r in meta])
        rc, so, se = run("build", "--book", book, "--engine", FAKE, "--depth", 3, "--target", 40, "--seed", 12, "--out", new("b3"))
        self.assertEqual(rc, 0, se)  # another seed: a different book
        self.assertNotEqual(files_except_runinfo(o1)["forge_sol_S42_book_v2_20261027.epd"],
                            files_except_runinfo(SCRATCH / sorted(p.name for p in SCRATCH.iterdir() if p.name.endswith("_b3"))[0])["forge_sol_S42_book_v2_20261027.epd"])

    def test_2_no_duplicate_with_current_book(self):
        """Every legal last move of one 15-ply prefix is its own book line: replacing a last move always lands on
        another book exit, which must be skipped; nothing accepted may equal a book exit."""
        pre = random_lines(1, 3, plies=15)[0]
        b = chess.Board()
        for m in pre:
            b.push(m)
        lines = [pre + [m] for m in sorted(b.legal_moves, key=lambda m: m.uci())]
        book = new("fan.pgn"); write_book(book, lines)
        o = new("fan")
        rc, so, se = run("build", "--book", book, "--engine", FAKE, "--depth", 2, "--lo", 0, "--hi", 10000, "--target", 1000, "--seed", 5, "--out", o)
        self.assertEqual(rc, 0, se)
        s = json.loads((o / "build_summary.json").read_text())
        self.assertGreater(s["skipped"]["current_book_exit"], 0)
        exits = set()
        for mv in lines:
            bb = chess.Board()
            for m in mv:
                bb.push(m)
            exits.add(" ".join(bb.fen().split()[:4]))
        acc = (o / "forge_sol_S42_book_v2_20261027.epd").read_text().splitlines()
        self.assertTrue(acc)
        self.assertFalse(any(" ".join(f.split()[:4]) in exits for f in acc))

    def test_3_gate_parser_pentanomial(self):
        lines = random_lines(4, 9); results = [("1-0", "0-1"), ("1/2-1/2", "1/2-1/2"), ("1-0", "1/2-1/2"), ("0-1", "1-0")]
        out = io.StringIO()
        for r, (mv, (ra, rb)) in enumerate(zip(lines, results), start=1):
            for gi, res in enumerate((ra, rb)):
                g = chess.pgn.Game(); g.headers["Round"] = str(r); g.headers["Result"] = res
                g.headers["White"], g.headers["Black"] = ("cand", "base") if gi == 0 else ("base", "cand")
                node = g
                for m in mv:
                    node = node.add_variation(m); node.comment = "book"
                b = node.board(); extra = sorted(b.legal_moves, key=lambda m: m.uci())[0]
                node = node.add_variation(extra); node.comment = "+0.10/12 0.1s"
                out.write(str(g) + "\n\n")
        pgn = new("gate.pgn"); pgn.write_text(out.getvalue(), encoding="utf-8")
        # candidate points per round: r1: 1+1=2 ; r2: .5+.5=1 ; r3: 1+.5=1.5 ; r4: 0+0=0  -> ptnml [1,0,1,1,1]
        rc, so, se = run("gate", "--pgn", pgn, "--cand", "cand", "--engine", FAKE, "--depth", 2, "--expect-ptnml", "1,0,1,1,1", "--out", new("g1"))
        self.assertEqual(rc, 0, se)
        rc, so, se = run("gate", "--pgn", pgn, "--cand", "cand", "--engine", FAKE, "--depth", 2, "--expect-ptnml", "0,1,1,1,1", "--out", new("g2"))
        self.assertEqual(rc, 1); self.assertIn("pentanomial", se)
        g1 = sorted(p for p in SCRATCH.iterdir() if p.name.endswith("_g1"))[0]
        rows = list(csv.DictReader(io.StringIO(next(g1.glob("forge_sol_S42_gate_games_*.csv")).read_text(encoding="utf-8"))))
        self.assertEqual(len(rows), 8)
        self.assertEqual(sum(float(r["cand_points"]) for r in rows), 4.5)
        self.assertEqual({r["book_plies"] for r in rows}, {"16"})

    def test_4_power_model_recovers_parameters(self):
        P = load(POWER, "s42power")
        rng = np.random.default_rng(3); n = 30000
        e = rng.normal(0, 70, n); s = np.where(rng.random(n) < 0.5, 1.0, -1.0)
        true = dict(delta=12.0, c=0.9, w=18.0, d=220.0)
        x = true["delta"] + s * (true["c"] * e + true["w"])
        pl, pd, pw = P.game_probs(x, true["d"]); u = rng.random(n)
        pts = np.where(u < pl, 0.0, np.where(u < pl + pd, 0.5, 1.0))
        th, v, it = P.nelder_mead(lambda t: P.nll(t, e, s, pts, True), [0.0, 0.5, 0.0, math.log(200.0)], [20.0, 0.3, 20.0, 0.3])
        self.assertLess(abs(th[0] - 12.0), 6.0); self.assertLess(abs(th[1] - 0.9), 0.08)
        self.assertLess(abs(th[2] - 18.0), 6.0); self.assertLess(abs(math.exp(th[3]) - 220.0), 12.0)

    def test_5_pair_profile_and_identity_tilt(self):
        P = load(POWER, "s42power2")
        ev = np.array([-90.0, -30.0, 0.0, 30.0, 90.0])
        p0 = P.pair_profile(ev, 0.0, 0.8, 0.0, 200.0)
        self.assertAlmostEqual(float(p0.sum()), 1.0, places=12)
        self.assertAlmostEqual(float(p0 @ P.SCORES), 0.5, places=12)      # symmetric book, Delta 0, w 0
        self.assertTrue(np.allclose(p0, p0[::-1], atol=1e-12))
        p = P.pair_profile(ev, 10.0, 0.8, 15.0, 200.0)
        self.assertGreater(float(p @ P.SCORES), 0.5)
        mus = [float(P.pair_profile(ev, dl, 0.8, 15.0, 200.0) @ P.SCORES) for dl in (-10.0, 0.0, 10.0, 20.0)]
        self.assertTrue(all(a < b for a, b in zip(mus, mus[1:])))         # pair score increases with Delta
        one = P.pair_profile(np.array([100.0]), 0.0, 0.8, 0.0, 200.0)
        l1, d1, w1 = P.game_probs(np.array([80.0]), 200.0); l2, d2, w2 = P.game_probs(np.array([-80.0]), 200.0)
        self.assertAlmostEqual(float(one[2]), float(d1[0] * d2[0] + w1[0] * l2[0] + l1[0] * w2[0]), places=12)  # hand convolution
        sys.path.insert(0, str(HERE / "scipy_shim"))
        S = load(HERE / "sol_S33" / "forge_sol_S33_sprt_planner_20261026.py", "s33p")
        mu, var, elo, nelo = P.stats_of(p)
        self.assertLess(float(np.max(np.abs(S.tilted_profile(p.tolist(), elo) - p))), 1e-9)

    def test_6_sample_deterministic(self):
        book = new("s.pgn"); write_book(book, random_lines(50, 21))
        a, b = new("sa"), new("sb")
        for o in (a, b):
            rc, so, se = run("sample", "--book", book, "--engine", FAKE, "--depth", 2, "--n", 20, "--seed", 4, "--out", o)
            self.assertEqual(rc, 0, se)
        self.assertEqual(files_except_runinfo(a), files_except_runinfo(b))


if __name__ == "__main__":
    unittest.main(verbosity=2)

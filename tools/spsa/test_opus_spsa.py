#!/usr/bin/env python3
"""Tests of the Forge SPSA tuner (R3-4). Standard library only, Python 3.10+, Windows and Linux.

usage: test_opus_spsa.py [--root DIR] [--engine FORGE_EXE] [unittest arguments, e.g. -k Schedule]
  --root    where test files go (a new subdirectory per run; nothing is deleted). Default: $OPUS_SPSA_TEST_ROOT,
            else a new temporary directory (left in place).
  --engine  also run EngineOptionsTest against a built Forge: the engine must advertise exactly the 20 constants of
            opus_spsa_forge20.json (defaults = start, same bounds) and re-advertise a value set with setoption.
No test plays chess: the session tests use a synthetic objective and a fake fastchess (a Python script).
"""
from __future__ import annotations

import itertools
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import opus_spsa as spsa  # noqa: E402
import opus_spsa_core as core  # noqa: E402
import opus_spsa_fastchess as fc  # noqa: E402
import opus_spsa_uci as uci  # noqa: E402

ROOT = None      # set in main()
ENGINE = None
_counter = itertools.count()


def new_dir(tag: str) -> str:
    path = os.path.join(ROOT, f"{next(_counter):03d}_{tag}")
    os.makedirs(path)
    return path


def P(name, start, lo, hi, c_end, r_end=0.002):
    return core.Param(name, float(start), lo, hi, float(c_end), float(r_end))


def base_cfg(**over) -> dict:
    cfg = json.loads(json.dumps(spsa.DEFAULTS))
    cfg.update({"engine": "engine.exe", "book": {"file": "book.epd", "format": "epd", "order": "random"},
                "tc": "1+0.01", "iterations": 10, "pairs_per_iteration": 2, "seed": 7,
                "params": [{"name": "A", "start": 50, "min": 0, "max": 100, "c_end": 4},
                           {"name": "B", "start": 10, "min": 0, "max": 40, "c_end": 2},
                           {"name": "C", "start": 3, "min": 1, "max": 6, "c_end": 0.5}],
                "rounding": "randomized"})
    cfg.update(over)
    return cfg


def quiet_log():
    return spsa.Logger(None, quiet=True)


# ---------------------------------------------------------------------------------------------------------------
class ScheduleTest(unittest.TestCase):
    def test_endpoints(self):
        for n in (1, 3, 100, 5000):
            s = core.Schedule.make(n)
            for p in (P("x", 85, 0, 300, 8), P("y", 3, 1, 6, 0.5, 0.004)):
                a_last, c_last = s.gains(p, n - 1)
                self.assertAlmostEqual(c_last, p.c_end, places=12)
                self.assertAlmostEqual(a_last, p.r_end * p.c_end ** 2, places=12)
                a0, c0 = s.gains(p, 0)
                self.assertAlmostEqual(c0, p.c_end * n ** core.GAMMA, places=9)
                if n > 1:
                    self.assertGreater(c0, c_last)
                    self.assertGreater(a0, a_last)

    def test_formula(self):
        s = core.Schedule.make(100, A_ratio=0.1)
        p = P("x", 0, -50, 50, 2.0, 0.002)
        c = 2.0 * 100 ** 0.101
        a = 0.002 * 4.0 * (10 + 100) ** 0.602
        for k in (0, 5, 99):
            a_k, c_k = s.gains(p, k)
            self.assertAlmostEqual(c_k, c / (k + 1) ** 0.101, places=12)
            self.assertAlmostEqual(a_k, a / (10 + k + 1) ** 0.602, places=12)

    def test_monotone(self):
        s = core.Schedule.make(50)
        p = P("x", 0, -50, 50, 1.0)
        gains = [s.gains(p, k) for k in range(50)]
        self.assertTrue(all(g1[0] < g0[0] and g1[1] < g0[1] for g0, g1 in zip(gains, gains[1:])))


class PerturbUpdateTest(unittest.TestCase):
    def test_rounding(self):
        rng = core.iteration_rng(1, 0)
        det = lambda x: core.round_value(x, "deterministic", rng)  # noqa: E731
        self.assertEqual([det(2.5), det(2.49), det(-2.5), det(-2.51), det(7.0)], [3, 2, -2, -3, 7])
        values = [core.round_value(2.3, "randomized", rng) for _ in range(20000)]
        self.assertEqual(set(values), {2, 3})
        self.assertAlmostEqual(sum(values) / len(values), 2.3, delta=0.02)
        with self.assertRaises(ValueError):
            core.round_value(1.0, "nearest", rng)

    def test_perturb_values_and_clamp(self):
        params = [P("a", 50, 0, 100, 4), P("b", 1, 0, 40, 2), P("c", 99.6, 0, 100, 3)]
        s = core.Schedule.make(10)
        theta = {p.name: p.start for p in params}
        perts = core.perturb(theta, params, s, 0, "deterministic", core.iteration_rng(3, 0))
        again = core.perturb(theta, params, s, 0, "deterministic", core.iteration_rng(3, 0))
        self.assertEqual(perts, again)  # a pure function of (seed, k)
        for p, q in zip(params, perts):
            self.assertIn(q.delta, (-1, 1))
            want_plus = min(max(math.floor(p.start + q.c_k * q.delta + 0.5), p.minimum), p.maximum)
            want_minus = min(max(math.floor(p.start - q.c_k * q.delta + 0.5), p.minimum), p.maximum)
            self.assertEqual((q.plus, q.minus), (want_plus, want_minus))
            self.assertTrue(p.minimum <= q.plus <= p.maximum and p.minimum <= q.minus <= p.maximum)
        # b = 1 with c_0 ~ 2.5: the low side is clamped to 0
        self.assertEqual(min(perts[1].plus, perts[1].minus), 0)
        self.assertEqual(max(perts[2].plus, perts[2].minus), 100)

    def test_update_direction_and_clamp(self):
        params = [P("a", 50, 0, 100, 4), P("b", 10, 0, 12, 2)]
        perts = [core.Perturbation("a", 0.5, 2.0, 1, 52, 48), core.Perturbation("b", 0.5, 2.0, -1, 8, 12)]
        new = core.update({"a": 50.0, "b": 11.0}, params, perts, 3)
        self.assertAlmostEqual(new["a"], 50 + 0.5 / 2.0 * 3)       # theta+ won, delta +1: up
        self.assertAlmostEqual(new["b"], 11 - 0.5 / 2.0 * 3)       # theta+ (lower b) won: down
        new = core.update({"a": 99.9, "b": 0.1}, params, perts, 9)
        self.assertEqual(new["a"], 100.0)                          # clamped to max
        new = core.update({"a": 0.2, "b": 0.1}, params, perts, -9)
        self.assertEqual(new["a"], 0.0)                            # clamped to min
        with self.assertRaises(ValueError):
            core.update({"a": 1.0, "b": 1.0}, params, list(reversed(perts)), 1)

    def test_expected_step_is_the_gradient(self):
        """Over all 2^n directions, the mean update on a quadratic objective is exactly 2 a_k grad f
        (ascent on theta+'s score)."""
        params = [P("a", 40, 0, 100, 4), P("b", 7, 0, 40, 2), P("c", 300, 0, 1000, 20)]
        opt = {"a": 47.0, "b": 3.0, "c": 260.0}
        w = {"a": 0.3, "b": 1.1, "c": 0.01}
        f = lambda x: -sum(w[n] * (x[n] - opt[n]) ** 2 for n in opt)  # noqa: E731
        theta = {p.name: p.start for p in params}
        s = core.Schedule.make(20)
        k = 4
        total = {p.name: 0.0 for p in params}
        for deltas in itertools.product((-1, 1), repeat=len(params)):
            perts = []
            for p, d in zip(params, deltas):
                a_k, c_k = s.gains(p, k)
                perts.append(core.Perturbation(p.name, a_k, c_k, d, theta[p.name] + c_k * d, theta[p.name] - c_k * d))
            y = f({q.name: q.plus for q in perts}) - f({q.name: q.minus for q in perts})
            new = core.update(theta, params, perts, y)
            for p in params:
                total[p.name] += new[p.name] - theta[p.name]
        for p in params:
            a_k, _ = s.gains(p, k)
            grad = -2 * w[p.name] * (theta[p.name] - opt[p.name])
            self.assertAlmostEqual(total[p.name] / 2 ** len(params), 2 * a_k * grad, places=9)

    def test_iteration_seeds(self):
        self.assertEqual(core.iteration_srand(5, 9), core.iteration_srand(5, 9))
        srands = {core.iteration_srand(5, k) for k in range(200)}
        self.assertEqual(len(srands), 200)
        self.assertTrue(all(0 <= s < 2 ** 31 for s in srands))

    def test_check_result(self):
        core.check_result(core.MatchResult(2, 1, 1, (0, 0, 1, 1, 0)), 2)
        for bad, pairs in ((core.MatchResult(2, 1, 0, (0, 0, 1, 1, 0)), 2),     # 3 games
                           (core.MatchResult(2, 1, 1, (0, 1, 0, 1, 0)), 2),     # ptnml disagrees with W/L/D
                           (core.MatchResult(2, 1, 1, (0, 0, 1, 1, 1)), 2)):    # 3 pairs
            with self.assertRaises(ValueError):
                core.check_result(bad, pairs)


class SyntheticConvergenceTest(unittest.TestCase):
    def _run(self, noise, iterations, pairs, r_end):
        params = [P("a", 40, 0, 100, 3, r_end), P("b", 30, 0, 100, 3, r_end), P("c", 60, 0, 100, 3, r_end)]
        opt = {"a": 52.0, "b": 22.0, "c": 60.0}
        game = core.SyntheticMatch(opt, {n: 12.0 for n in opt}, depth=60.0, noise=noise)
        s = core.Schedule.make(iterations)
        theta = {p.name: p.start for p in params}
        dist0 = math.dist([theta[n] for n in opt], list(opt.values()))
        for k in range(iterations):
            perts = core.perturb(theta, params, s, k, "randomized", core.iteration_rng(11, k))
            result = game({q.name: q.plus for q in perts}, {q.name: q.minus for q in perts}, pairs,
                          core.iteration_srand(11, k))
            core.check_result(result, pairs)
            theta = core.update(theta, params, perts, result.w_minus_l)
        return dist0, math.dist([theta[n] for n in opt], list(opt.values())), theta

    def test_expected_results_converge(self):
        dist0, dist, theta = self._run(noise=False, iterations=300, pairs=50, r_end=0.01)
        self.assertLess(dist, 0.25 * dist0, theta)

    def test_noisy_results_converge(self):
        dist0, dist, theta = self._run(noise=True, iterations=1500, pairs=8, r_end=0.01)
        self.assertLess(dist, 0.5 * dist0, theta)


# ---------------------------------------------------------------------------------------------------------------
def synthetic(cfg):
    params = spsa.make_params(cfg)
    match, _ = spsa.synthetic_match(cfg, params)
    return params, match


def csv_rows(path):
    with open(path, "rb") as f:
        lines = f.read().decode("utf-8").split("\n")
    assert lines[-1] == "", "CSV must end with a newline"
    return [line.split(",") for line in lines[:-1]]


class SessionTest(unittest.TestCase):
    PINS = {"engine_sha256": "e", "book_sha256": "b"}

    def test_resume_equals_uninterrupted(self):
        cfg = base_cfg(iterations=12)
        params, match = synthetic(cfg)
        d1, d2 = new_dir("straight"), new_dir("resumed")
        s1, code1 = spsa.run_session(cfg, d1, params, match, self.PINS, quiet_log())
        s2, code2 = spsa.run_session(cfg, d2, params, match, self.PINS, quiet_log(), stop_after=5)
        self.assertEqual((code1, code2, s2["next_iteration"], s2["status"]), (0, 0, 5, "stopped"))
        s2, code2 = spsa.run_session(cfg, d2, params, match, self.PINS, quiet_log(), stop_after=3)
        s2, code2 = spsa.run_session(cfg, d2, params, match, self.PINS, quiet_log())
        self.assertEqual((s1["status"], s2["status"], s1["next_iteration"], s2["next_iteration"]),
                         ("finished", "finished", 12, 12))
        self.assertEqual(s1["theta"], s2["theta"])
        self.assertEqual(s1["totals"], s2["totals"])
        r1, r2 = csv_rows(os.path.join(d1, "spsa_log.csv")), csv_rows(os.path.join(d2, "spsa_log.csv"))
        self.assertEqual(len(r1), 13)
        strip = lambda rows: [row[:1] + row[3:] for row in rows]  # noqa: E731  (drop utc, seconds)
        self.assertEqual(strip(r1), strip(r2))
        self.assertEqual([int(row[0]) for row in r1[1:]], list(range(12)))
        state = core.load_json(os.path.join(d2, "state.json"))
        self.assertEqual(state["theta"], s1["theta"])
        last = r1[-1]
        header = r1[0]
        for p in params:
            self.assertAlmostEqual(float(last[header.index(f"{p.name}.theta")]), s1["theta"][p.name], places=5)

    def test_csv_row_repaired_after_crash_between_state_and_csv(self):
        cfg = base_cfg(iterations=5)
        params, match = synthetic(cfg)
        d = new_dir("repair")
        spsa.run_session(cfg, d, params, match, self.PINS, quiet_log(), stop_after=3)
        path = os.path.join(d, "spsa_log.csv")
        with open(path, "rb") as f:
            lines = f.read().decode("utf-8").split("\n")
        with open(path, "wb") as f:  # as if the process died after state.json, before the CSV row of iteration 2
            f.write(("\n".join(lines[:3]) + "\n").encode("utf-8"))
        spsa.run_session(cfg, d, params, match, self.PINS, quiet_log())
        rows = csv_rows(path)
        self.assertEqual([int(r[0]) for r in rows[1:]], [0, 1, 2, 3, 4])

    def test_changed_config_or_engine_refused(self):
        cfg = base_cfg(iterations=6)
        params, match = synthetic(cfg)
        d = new_dir("refuse")
        spsa.run_session(cfg, d, params, match, self.PINS, quiet_log(), stop_after=2)
        changed = base_cfg(iterations=6)
        changed["params"][1]["c_end"] = 3
        with self.assertRaises(spsa.ConfigError):
            spsa.run_session(changed, d, spsa.make_params(changed), match, self.PINS, quiet_log())
        with self.assertRaises(spsa.ConfigError):
            spsa.run_session(base_cfg(iterations=6, tc="2+0.02"), d, params, match, self.PINS, quiet_log())
        with self.assertRaises(spsa.ConfigError):
            spsa.run_session(cfg, d, params, match, {"engine_sha256": "other", "book_sha256": "b"}, quiet_log())
        state, code = spsa.run_session(cfg, d, params, match, self.PINS, quiet_log())
        self.assertEqual((code, state["next_iteration"]), (0, 6))

    def test_failed_match_keeps_state(self):
        cfg = base_cfg(iterations=4, retries=1)
        params, good = synthetic(cfg)
        calls = []

        def flaky(plus, minus, pairs, srand, k, attempt):
            calls.append((k, attempt))
            if k == 2:
                raise spsa.IterationFailed("boom")
            return good(plus, minus, pairs, srand, k, attempt)
        d = new_dir("failed")
        state, code = spsa.run_session(cfg, d, params, flaky, self.PINS, quiet_log())
        self.assertEqual((code, state["next_iteration"]), (spsa.EXIT_FAILED, 2))
        self.assertEqual(calls[-2:], [(2, 0), (2, 1)])
        self.assertEqual(core.load_json(os.path.join(d, "state.json"))["next_iteration"], 2)
        self.assertEqual(len(csv_rows(os.path.join(d, "spsa_log.csv"))), 3)


# ---------------------------------------------------------------------------------------------------------------
ESC = "\x1b"
SAMPLE = (  # the fastchess 1.8.2 console format (colour codes as printed), 3 pairs
    "Indexing opening suite...\n"
    "Started game 1 of 6 (spsa_plus vs spsa_minus)\n"
    "Started game 2 of 6 (spsa_minus vs spsa_plus)\n"
    "Finished game 2 (spsa_minus vs spsa_plus): 0-1 {Black mates}\n"
    "Finished game 1 (spsa_plus vs spsa_minus): 1/2-1/2 {Draw by 3-fold repetition}\n"
    "Started game 3 of 6 (spsa_plus vs spsa_minus)\n"
    "Finished game 3 (spsa_plus vs spsa_minus): 0-1 {White loses on time}\n"
    "Finished game 4 (spsa_minus vs spsa_plus): 1-0 {White mates}\n"
    "Finished game 5 (spsa_plus vs spsa_minus): 1-0 {White mates}\n"
    "Finished game 6 (spsa_minus vs spsa_plus): 1/2-1/2 {Draw by fifty moves rule}\n"
    "--------------------------------------------------\n"
    f"{ESC}[1mResults of spsa_plus vs spsa_minus (0.5+0.005, 1t, 16MB, forge-10000.epd):{ESC}[0m\n"
    "Elo: 58.45 +/- 166.35, nElo: 61.42 +/- 172.31\n"
    "LOS: 72.85 %, DrawRatio: 33.33 %, PairsRatio: 2.00\n"
    "Games: 6, Wins: 2, Losses: 2, Draws: 2, Points: 3.0 (50.00 %)\n"
    "Ptnml(0-2): [1, 0, 0, 2, 0], WL/DD Ratio: inf\n"
    "--------------------------------------------------\n"
    "Finished match\n")
# spsa_plus per game: 1 draw, 2 win (as black), 3 loss (time), 4 loss, 5 win, 6 draw; pairs (1,2) = 1.5,
# (3,4) = 0, (5,6) = 1.5 points -> W 2, L 2, D 2, Ptnml [1, 0, 0, 2, 0].


class FastchessParseTest(unittest.TestCase):
    def sample(self):
        return SAMPLE

    def test_sample(self):
        r = fc.parse_output(self.sample(), 3)
        self.assertEqual((r.wins, r.losses, r.draws, r.ptnml), (2, 2, 2, (1, 0, 0, 2, 0)))
        self.assertEqual((r.time_losses, r.abnormal), (1, 0))
        core.check_result(r, 3)

    def test_real_fastchess_output(self):
        """testdata/: fastchess 1.8.2 console output of the R3-4 nodes dry run (iteration 0, 2 pairs, concurrency 2,
        game 2 finished before game 1), stored with LF; fastchess wrote CRLF, which is re-created here too."""
        with open(os.path.join(HERE, "testdata", "fastchess_1.8.2_dryrun_nodes_it0.out"), "rb") as f:
            text = f.read().decode("utf-8")
        for variant in (text, text.replace("\n", "\r\n")):
            r = fc.parse_output(variant, 2)
            self.assertEqual((r.wins, r.losses, r.draws, r.ptnml), (1, 2, 1, (0, 1, 1, 0, 0)))
            self.assertEqual(dict(r.terminations), {"normal": 4})

    def test_crlf_and_last_block(self):
        text = self.sample().replace("\n", "\r\n")
        early = ("Results of spsa_plus vs spsa_minus (x):\nGames: 2, Wins: 2, Losses: 0, Draws: 0, Points: 2.0 (100.00 %)\n"
                 "Ptnml(0-2): [0, 0, 0, 0, 1], WL/DD Ratio: inf\n")
        r = fc.parse_output(early + text, 3)
        self.assertEqual((r.wins, r.losses, r.draws), (2, 2, 2))

    def test_inconsistent_outputs_fail(self):
        good = self.sample()
        bad = {
            "W/L/D": good.replace("Wins: 2, Losses: 2", "Wins: 3, Losses: 1"),
            "ptnml": good.replace("[1, 0, 0, 2, 0]", "[0, 1, 0, 1, 1]"),
            "missing game": good.replace("Finished game 6 (spsa_minus vs spsa_plus): 1/2-1/2 {Draw by fifty moves rule}\n",
                                         ""),
            "no block": good.split("--------")[0],
            "names": good.replace("Results of spsa_plus vs spsa_minus", "Results of spsa_minus vs spsa_plus"),
            "pairs": good,
        }
        for label, text in bad.items():
            with self.subTest(label), self.assertRaises(ValueError):
                fc.parse_output(text, 4 if label == "pairs" else 3)

    def test_abnormal_counted(self):
        text = self.sample().replace("{White loses on time}", "{White disconnects}")
        self.assertEqual(fc.parse_output(text, 3).abnormal, 1)
        text = self.sample().replace("{White loses on time}", "{Black resigns}")
        r = fc.parse_output(text, 3)
        self.assertEqual((r.abnormal, r.time_losses, dict(r.terminations)["adjudication"]), (0, 0, 1))

    def test_build_command(self):
        cfg = base_cfg(fastchess=["py", "fake.py"], concurrency=2, timemargin_ms=50, extra_args=["-wait", 5],
                       strict=True)
        argv = fc.build_command(cfg, {"A": 52, "B": 9}, {"A": 48, "B": 11}, 1234, "out/g.pgn")
        self.assertEqual(argv[:2], ["py", "fake.py"])
        i = argv.index("-engine")
        self.assertEqual(argv[i:i + 5], ["-engine", "cmd=engine.exe", "name=spsa_plus", "option.A=52", "option.B=9"])
        j = argv.index("-engine", i + 1)
        self.assertEqual(argv[j:j + 5], ["-engine", "cmd=engine.exe", "name=spsa_minus", "option.A=48", "option.B=11"])
        e = argv.index("-each")
        self.assertEqual(argv[e + 1:e + 7], ["proto=uci", "tc=1+0.01", "timemargin=50", "option.Threads=1",
                                             "option.Hash=16", "option.OwnBook=false"])
        text = " ".join(argv)
        for part in ("-rounds 2 -games 2 -repeat", "-concurrency 2", "-openings file=book.epd format=epd order=random",
                     "-srand 1234", "-pgnout file=out/g.pgn", "-report penta=true", "-strict", "-wait 5"):
            self.assertIn(part, text)
        nodes = fc.build_command(base_cfg(tc=None, nodes=20000, strict=False), {"A": 1}, {"A": 2}, 1, "g.pgn")
        self.assertIn("nodes=20000", nodes)
        self.assertFalse(any(a.startswith("tc=") for a in nodes))
        self.assertNotIn("-strict", nodes)


class ConfigTest(unittest.TestCase):
    def test_validate(self):
        cfg = base_cfg()
        self.assertEqual(spsa.validate(cfg, spsa.make_params(cfg)), [])
        small_c = base_cfg(rounding="deterministic")
        small_c["params"][2]["c_end"] = 0.4
        self.assertEqual(spsa.validate(base_cfg(rounding="deterministic"), spsa.make_params(base_cfg())), [])
        cases = {
            "c_end < 0.5 with deterministic rounding": small_c,
            "no tc / nodes": base_cfg(tc=None),
            "too many threads": base_cfg(concurrency=3, max_total_threads=2),
        }
        bad = base_cfg()
        bad["params"][0]["start"] = 101
        cases["start outside"] = bad
        dup = base_cfg()
        dup["params"][1]["name"] = "A"
        cases["duplicate"] = dup
        for label, c in cases.items():
            with self.subTest(label):
                self.assertNotEqual(spsa.validate(c, spsa.make_params(c)), [])

    def test_example_config_matches_engine_source(self):
        """opus_spsa_forge20.json lists exactly forge::tune::AdvertisedParameters (same order), with start = the
        default in tune.inc and min/max = the range in tune::parameters()."""
        cfg = spsa.load_config(os.path.join(HERE, "opus_spsa_forge20.json"), {})
        params = spsa.make_params(cfg)
        self.assertEqual(spsa.validate(cfg, params), [])
        with open(os.path.join(REPO, "include", "forge", "search_tune.hpp"), "rb") as f:
            header = f.read().decode("utf-8")
        block = re.search(r"AdvertisedParameters\{(.*?)\};", header, re.S).group(1)
        advertised = re.findall(r'"(\w+)"', block)
        self.assertEqual(len(advertised), 20)
        self.assertEqual([p.name for p in params], advertised)
        with open(os.path.join(REPO, "src", "search", "tune.inc"), "rb") as f:
            source = f.read().decode("utf-8")
        for p in params:
            default = re.search(rf"^int {p.name} = (-?\d+);", source, re.M)
            bounds = re.search(rf'\{{"{p.name}", &{p.name}, (-?\d+), (-?\d+)\}}', source)
            self.assertIsNotNone(default, p.name)
            self.assertIsNotNone(bounds, p.name)
            self.assertEqual(p.start, int(default.group(1)), p.name)
            self.assertEqual((p.minimum, p.maximum), (int(bounds.group(1)), int(bounds.group(2))), p.name)

    def test_dry_run_config(self):
        cfg = spsa.apply_dry_run(spsa.load_config(os.path.join(HERE, "opus_spsa_forge20.json"), {}))
        params = spsa.make_params(cfg)
        self.assertEqual(spsa.validate(cfg, params), [])
        self.assertLessEqual(cfg["concurrency"] * cfg["threads"], 2)
        self.assertTrue(2 <= len(params) <= 3 and 2 <= cfg["iterations"] <= 3)

    def test_uci_parsing_and_checks(self):
        reply = ["id name Forge", "option name Hash type spin default 16 min 1 max 2048",
                 "option name Move Overhead type spin default 10 min 0 max 1000", "option name Clear Hash type button",
                 "option name Book File type string default <empty>", "option name OwnBook type check default true",
                 "option name A type spin default 50 min 0 max 100", "option name B type check default false",
                 "option name C type spin default 3 min 1 max 5", "uciok"]
        o = uci.parse_options(reply)
        self.assertEqual(o["Move Overhead"], {"type": "spin", "default": 10, "min": 0, "max": 1000})
        self.assertEqual(o["Book File"]["default"], "<empty>")
        self.assertEqual(o["Clear Hash"]["type"], "button")
        params = [P("A", 50, 0, 100, 4), P("B", 0, 0, 1, 0.5), P("C", 3, 1, 6, 0.5), P("D", 1, 0, 2, 0.5)]
        problems = uci.check_params(params, o, fresh=True)
        self.assertEqual(len(problems), 3, problems)  # B not spin, C bounds, D missing
        self.assertTrue(uci.check_params([P("A", 51, 0, 100, 4)], o, fresh=True))
        self.assertFalse(uci.check_params([P("A", 51, 0, 100, 4)], o, fresh=False))
        self.assertFalse(uci.check_params([P("A", 51, 0, 100, 4)], o, fresh=True, allow_start_offset=True))
        self.assertEqual(uci.application_probe([P("A", 100, 0, 100, 4), P("C", 3, 1, 5, 1)]), {"A": 99, "C": 4})


# ---------------------------------------------------------------------------------------------------------------
FAKE_FASTCHESS = r'''
import os, subprocess, sys, time
args = sys.argv[1:]
mode = args.pop(0).split("=", 1)[1]
def after(flag):
    return args[args.index(flag) + 1]
names, options, current = [], [], None
for i, a in enumerate(args):
    if a == "-engine":
        current = {}
        options.append(current)
    elif current is not None and a.startswith("name="):
        names.append(a[5:])
    elif current is not None and a.startswith("option."):
        k, v = a[7:].split("=", 1)
        current[k] = int(v)
    elif a.startswith("-") and a != "-engine" and not a[1:].isdigit():
        current = None
pairs, srand = int(after("-rounds")), int(after("-srand"))
pgn = [a for a in args if a.startswith("file=") and a.endswith(".pgn")][0][5:]
if mode == "sleep":
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    with open("child.pid", "w") as f:
        f.write(str(child.pid))
    time.sleep(60)
if mode == "fail":
    print("Warning; something went wrong")
    sys.exit(1)
plus, minus = names
sum_plus, sum_minus = sum(options[0].values()), sum(options[1].values())
points, ptnml = [], [0] * 5
for g in range(1, 2 * pairs + 1):
    v = (srand + 7 * g + (sum_plus > sum_minus)) % 3          # 0 loss, 1 draw, 2 win for spsa_plus
    points.append(v)
    white, black = (plus, minus) if g % 2 == 1 else (minus, plus)
    white_points = v if white == plus else 2 - v
    res = {2: "1-0", 1: "1/2-1/2", 0: "0-1"}[white_points]
    why = {"1-0": "White mates", "0-1": "Black mates", "1/2-1/2": "Draw by 3-fold repetition"}[res]
    print(f"Started game {g} of {2 * pairs} ({white} vs {black})")
    print(f"Finished game {g} ({white} vs {black}): {res} {{{why}}}")
for j in range(pairs):
    ptnml[points[2 * j] + points[2 * j + 1]] += 1
w, l, d = points.count(2), points.count(0), points.count(1)
if mode == "bad":
    ptnml = ptnml[::-1] if ptnml != ptnml[::-1] else [pairs, 0, 0, 0, 0] if pairs else ptnml
    w += 1
print("--------------------------------------------------")
print(f"\x1b[1mResults of {plus} vs {minus} (1+0.01, 1t, 16MB, book.epd):\x1b[0m")
print("Elo: 0.00 +/- 0.00, nElo: 0.00 +/- 0.00")
print(f"Games: {w + l + d}, Wins: {w}, Losses: {l}, Draws: {d}, Points: {w + d / 2:.1f} (50.00 %)")
print(f"Ptnml(0-2): [{', '.join(map(str, ptnml))}], WL/DD Ratio: 1.00")
print("--------------------------------------------------")
with open(pgn, "a") as f:
    f.write(f"[Event \"fake\"]\n[Result \"*\"]\n\n*\n\n")
print("Finished match")
'''


def pid_alive(pid: int) -> bool:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.WinDLL("kernel32")
        k32.OpenProcess.restype = wintypes.HANDLE
        k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        k32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        k32.CloseHandle.argtypes = (wintypes.HANDLE,)
        handle = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = wintypes.DWORD()
        k32.GetExitCodeProcess(handle, ctypes.byref(code))
        k32.CloseHandle(handle)
        return code.value == 259  # STILL_ACTIVE
    try:
        with open(f"/proc/{pid}/stat", "rb") as f:
            if f.read().split(b")")[-1].split()[0] == b"Z":
                return False
    except OSError:
        pass
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class FakeFastchessTest(unittest.TestCase):
    def setUp(self):
        self.dir = new_dir("fake")
        self.fake = os.path.join(self.dir, "fake_fastchess.py")
        with open(self.fake, "wb") as f:
            f.write(FAKE_FASTCHESS.encode("utf-8"))

    def cfg(self, mode, **over):
        return base_cfg(fastchess=[sys.executable, "-I", "-B", self.fake, f"--mode={mode}"], iterations=3,
                        iteration_timeout_s=120, **over)

    def test_session_with_restart(self):
        cfg = self.cfg("ok")
        params = spsa.make_params(cfg)
        work = os.path.join(self.dir, "work")
        log = quiet_log()
        pins = {"engine_sha256": "x", "book_sha256": "y"}
        state, code = spsa.run_session(cfg, work, params, spsa.fastchess_match(cfg, work, log), pins, log, stop_after=2)
        self.assertEqual((code, state["next_iteration"]), (0, 2))
        state, code = spsa.run_session(cfg, work, params, spsa.fastchess_match(cfg, work, log), pins, log)
        self.assertEqual((code, state["next_iteration"], state["status"]), (0, 3, "finished"))
        self.assertEqual(state["totals"]["games"], 3 * 2 * cfg["pairs_per_iteration"])
        rows = csv_rows(os.path.join(work, "spsa_log.csv"))
        self.assertEqual([int(r[0]) for r in rows[1:]], [0, 1, 2])
        for k in range(3):
            itdir = os.path.join(work, "games", f"iter_{k:06d}_a0")
            for name in ("command.json", "fastchess.out", "games.pgn"):
                self.assertTrue(os.path.isfile(os.path.join(itdir, name)), (k, name))
            argv = core.load_json(os.path.join(itdir, "command.json"))
            self.assertIn(str(core.iteration_srand(cfg["seed"], k)), argv)

    def test_failing_and_inconsistent_runs_stop(self):
        for mode in ("fail", "bad"):
            with self.subTest(mode):
                cfg = self.cfg(mode, retries=1)
                work = os.path.join(self.dir, f"work_{mode}")
                state, code = spsa.run_session(cfg, work, spsa.make_params(cfg), spsa.fastchess_match(cfg, work, quiet_log()),
                                               {"engine_sha256": "x", "book_sha256": "y"}, quiet_log())
                self.assertEqual((code, state["next_iteration"]), (spsa.EXIT_FAILED, 0))
                self.assertTrue(os.path.isdir(os.path.join(work, "games", "iter_000000_a1")))  # the retry

    def test_timeout_kills_the_process_tree(self):
        work = new_dir("timeout")
        argv = [sys.executable, "-I", "-B", self.fake, "--mode=sleep", "-rounds", "1", "-srand", "1",
                "-pgnout", "file=x.pgn", "-engine", "name=a", "-engine", "name=b"]
        t0 = time.monotonic()
        outcome = fc.run_child(argv, work, os.path.join(work, "out.txt"), 8, "idle")
        self.assertTrue(outcome.timed_out)
        self.assertLess(time.monotonic() - t0, 40)
        pid_file = os.path.join(work, "child.pid")
        self.assertTrue(os.path.exists(pid_file), "the fake did not start its child within the timeout")
        with open(pid_file) as f:
            pid = int(f.read())
        deadline = time.monotonic() + 10
        while pid_alive(pid) and time.monotonic() < deadline:
            time.sleep(0.2)
        self.assertFalse(pid_alive(pid), "a grandchild survived the timeout kill")


class CliTest(unittest.TestCase):
    def test_synthetic_cli_stop_resume_status_plan(self):
        d = new_dir("cli")
        cfg_path = os.path.join(d, "cfg.json")
        cfg = base_cfg(iterations=6)
        cfg.pop("dry_run")
        with open(cfg_path, "wb") as f:
            f.write(json.dumps({k: v for k, v in cfg.items() if k in spsa.DEFAULTS}).encode("utf-8"))
        work = os.path.join(d, "work")
        self.assertEqual(spsa.main(["--config", cfg_path, "--workdir", work, "--synthetic", "--stop-after", "4",
                                    "--quiet"]), 0)
        self.assertEqual(spsa.main(["--config", cfg_path, "--workdir", work, "--synthetic", "--quiet"]), 0)
        state = core.load_json(os.path.join(work, "synthetic", "state.json"))
        self.assertEqual((state["next_iteration"], state["status"]), (6, "finished"))
        self.assertEqual(spsa.main(["--workdir", os.path.join(work, "synthetic"), "--status"]), 0)
        self.assertEqual(spsa.main(["--config", cfg_path, "--workdir", os.path.join(work, "synthetic"), "--plan"]), 0)
        with open(os.path.join(work, "synthetic", "session.log"), "rb") as f:
            self.assertIn(b"resume at iteration 4/6", f.read())


class EngineOptionsTest(unittest.TestCase):
    def setUp(self):
        if not ENGINE:
            self.skipTest("needs --engine FORGE_EXE")

    def test_engine_advertises_the_20(self):
        engine = ENGINE
        cfg = spsa.load_config(os.path.join(HERE, "opus_spsa_forge20.json"), {})
        params = spsa.make_params(cfg)
        options, problems = uci.prove_application(engine, params)
        self.assertEqual(problems, [])
        self.assertEqual(uci.check_params(params, options, fresh=True), [])
        for p in params:
            self.assertEqual((options[p.name]["min"], options[p.name]["max"]), (p.minimum, p.maximum), p.name)
        # Exactly the 20: no other tune:: constant is listed (FORGE_EXPOSE_TUNABLES builds list all of them).
        with open(os.path.join(REPO, "src", "search", "tune.inc"), "rb") as f:
            tunables = set(re.findall(r'\{"(\w+)", &\w+, -?\d+, -?\d+\}', f.read().decode("utf-8")))
        listed = sorted(n for n in options if n in tunables)
        exposed = len(listed) == len(tunables)
        if not exposed:
            self.assertEqual(listed, sorted(p.name for p in params))
        lines = uci.uci_session(engine, ["uci"])
        names = [m.group(1) for m in (re.match(r"^option name (.+?) type ", l) for l in lines) if m]
        self.assertEqual(len(names), len(set(names)), "an option is listed twice")


def main():
    global ROOT, ENGINE
    args = sys.argv[1:]
    if "--root" in args:
        i = args.index("--root")
        ROOT = args[i + 1]
        del args[i:i + 2]
    if "--engine" in args:
        i = args.index("--engine")
        ENGINE = os.path.abspath(args[i + 1])
        del args[i:i + 2]
    base = ROOT or os.environ.get("OPUS_SPSA_TEST_ROOT")
    if base:
        os.makedirs(base, exist_ok=True)
        ROOT = tempfile.mkdtemp(prefix="run_", dir=base)
    else:
        ROOT = tempfile.mkdtemp(prefix="opus_spsa_test_")
    print(f"test files: {ROOT}", flush=True)
    unittest.main(argv=[sys.argv[0]] + args, verbosity=2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Unit tests for the S10fix tools (screen verdict, WAC flips, hygiene check, bench-rerun helpers).
Run: python -I -B test_opus_s10fix.py   (imports the tools from this file's folder; no engine, no network)."""
from __future__ import annotations
import io, json, sys, tempfile, unittest
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import opus_s10_screen_verdict as sv  # noqa: E402
import opus_s10_wac_flips as wf  # noqa: E402
import opus_s10_hygiene_check as hy  # noqa: E402
import opus_s10_bench_rerun as br  # noqa: E402

OFF = {"11": 308972, "13": 745494, "16": 2460422, "20": 11901452, "22": 31111774}


def idea(name="X", wac=290, on20=None, on22=None, on11=301162, off11=308972, drop=()):
    on = dict(OFF)
    on["20"] = on20 if on20 is not None else OFF["20"]
    on["22"] = on22 if on22 is not None else OFF["22"]
    for d in drop:
        on.pop(d, None)
    return {"name": name, "wac_solved": wac, "off_nodes": dict(OFF), "on_nodes": on, "off_d11": off11, "on_d11": on11}


class Verdict(unittest.TestCase):
    def test_pass_at_both_boundaries(self):
        v = sv.verdict(idea(wac=283, on20=int(OFF["20"] * 1.2), on22=int(OFF["22"] * 0.8) + 1))
        self.assertEqual(v["status"], "PASS", v)
        self.assertEqual(v["B_qualification"], "ALLOWED")

    def test_wac_below_floor_fails_and_skips_B(self):
        v = sv.verdict(idea(wac=282))
        self.assertEqual((v["status"], v["B_qualification"]), ("FAIL", "SKIP"))
        self.assertIn("WAC300 ON 282/300 < 283", v["reasons"])

    def test_guard_fails_both_directions(self):
        self.assertEqual(sv.verdict(idea(on22=int(OFF["22"] * 1.2) + 40))["status"], "FAIL")
        self.assertEqual(sv.verdict(idea(on20=int(OFF["20"] * 0.79)))["status"], "FAIL")

    def test_missing_numbers_are_not_a_pass(self):
        self.assertEqual(sv.verdict(idea(drop=("22",)))["status"], "FAIL")
        self.assertEqual(sv.verdict(idea(wac=None))["status"], "FAIL")
        self.assertEqual(sv.verdict(idea(on11=None))["status"], "FAIL")

    def test_inert_option_fails(self):
        v = sv.verdict(idea(on11=308972))
        self.assertIn("option inert: ON d11 == OFF d11", v["reasons"])

    def test_sol_four_ideas(self):
        # Sol's consolidated v2 numbers (Lprime release): WAC and d20/d22 ON nodes
        sol = {"QuietCheckLmpSurvival": (269, 10956860, 27358618, 342968),
               "ImprovingRazorGuard": (270, 9011938, 25347487, 301162),
               "SingularSiblingLmr": (263, 14837257, 32299567, 336273),
               "CaptureHistoryLmp": (258, 8234313, 23665760, 304755)}
        guard = {}
        for name, (wac, n20, n22, n11) in sol.items():
            v = sv.verdict(idea(name, wac, n20, n22, n11))
            self.assertEqual((v["status"], v["B_qualification"]), ("FAIL", "SKIP"), name)
            guard[name] = any(r.startswith("deep-node guard FAIL") for r in v["reasons"])
        self.assertEqual(guard, {"QuietCheckLmpSurvival": False, "ImprovingRazorGuard": True,
                                 "SingularSiblingLmr": True, "CaptureHistoryLmp": True})


EPD = ("6k1/8/8/8/8/8/5PPP/3R2K1 w - - bm Rd8+; id \"T.001\";\n"
       "6k1/8/8/8/8/8/5PPP/3Q2K1 w - - bm Qd8+; id \"T.002\";\n"
       "r5k1/8/8/8/8/8/5PPP/R5K1 w - - bm Rxa8+; id \"T.003\";\n")


def stream(moves, depth=10):
    out = ["uciok", "readyok"]
    for m in moves:
        out += ["readyok", f"info depth {depth} seldepth 12 score cp 50 nodes 1000 nps 100000 hashfull 0 time 10 pv {m}",
                f"bestmove {m}"]
    return "\n".join(out) + "\n"


def result(moves, bms):
    rows = [{"id": f"T.00{i + 1}", "bestmove_uci": m, "legal": True, "bestmove_allowed": m == bms[i],
             "exception": None, "bm_uci": [bms[i]], "am_uci": []} for i, m in enumerate(moves)]
    return {"results": rows, "solved": sum(r["bestmove_allowed"] for r in rows)}


class WacFlips(unittest.TestCase):
    def test_lost_and_gained(self):
        bms = ["d1d8", "d1d8", "a1a8"]
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / "suite.epd").write_text(EPD)
            off, on = t / "off", t / "on"
            off.mkdir(); on.mkdir()
            off_moves, on_moves = ["d1d8", "d1d2", "a1a8"], ["d1d2", "d1d8", "a1a8"]
            (off / "result.json").write_text(json.dumps(result(off_moves, bms)))
            (off / "001_wac300_fixedtime.stdout").write_text(stream(off_moves))
            (on / "result.json").write_text(json.dumps(result(on_moves, bms)))
            (on / "000_WAC300_1000MS.stdout").write_text(stream(on_moves))
            same = t / "same"  # a second idea that plays exactly like OFF
            same.mkdir()
            (same / "result.json").write_text(json.dumps(result(off_moves, bms)))
            (same / "000_WAC300_1000MS.stdout").write_text(stream(off_moves))
            with redirect_stdout(io.StringIO()):  # two ideas: the second must see the same suite/OFF data
                wf.main(["--off", str(off), "--on", f"I={on}", "--on", f"J={same}", "--epd", str(t / "suite.epd"),
                         "--out-json", str(t / "o.json"), "--out-md", str(t / "o.md")])
            rep = json.loads((t / "o.json").read_text())
            r = rep["ideas"]["I"]
            self.assertEqual((r["lost"], r["gained"], r["delta_vs_off"]), (["T.001"], ["T.002"], 0))
            self.assertEqual(r["rows"][0]["key_move_kind"], "check")
            self.assertEqual(rep["off"]["solved"], 2)
            self.assertEqual((rep["ideas"]["J"]["lost"], rep["ideas"]["J"]["gained"]), ([], []))
            self.assertEqual(r["lost_only_here"], ["T.001"])

    def test_solved_flag_disagreement_raises(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "s.epd"
            p.write_text(EPD)
            rows = wf.load_epd(p)
            bad = result(["d1d8", "d1d8", "a1a8"], ["d1d8", "d1d8", "a1a8"])
            bad["results"][0]["bestmove_allowed"] = False
            with self.assertRaises(ValueError):
                wf.solved_set(bad, rows)

    def test_kind(self):
        fen = "r5k1/8/8/8/8/8/5PPP/R5K1 w - - 0 1"
        self.assertEqual(wf.kind(fen, "a1a8"), "capture+check")
        self.assertEqual(wf.kind(fen, "g2g3"), "quiet")


class Hygiene(unittest.TestCase):
    def test_before_dups_and_tgz(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / "tool_before_fix.py").write_text("a\n")
            (t / "tool.py").write_text("b\n")
            (t / "copy1.md").write_text("same\n")
            (t / "sub").mkdir()
            (t / "sub" / "copy2.md").write_text("same\n")
            (t / "logs.tar.gz").write_bytes(b"\x1f\x8b" + b"0" * 98)
            rep = hy.check(hy.scan_dir(t))
            self.assertEqual(rep["before_copies"], ["tool_before_fix.py"])
            self.assertEqual([sorted(d["paths"]) for d in rep["duplicate_groups"]], [["copy1.md", "sub/copy2.md"]])
            self.assertEqual(rep["tar_gz"], [{"path": "logs.tar.gz", "bytes": 100}])
            with redirect_stdout(io.StringIO()):
                self.assertEqual(hy.main(["--dir", str(t)]), 1)
            (t / "tool_before_fix.py").rename(t / "tool_v1.py")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(hy.main(["--dir", str(t)]), 0)


class BenchRerun(unittest.TestCase):
    def test_bench_regex(self):
        m = br.BENCH.match("info string bench depth 22 nodes 31111774 time 21724 nps 1432138")
        self.assertEqual((m[1], m[2], m[3], m[4]), ("22", "31111774", "21724", "1432138"))
        self.assertIsNone(br.BENCH.match("info string bench depth 22 nodes 31111774"))

    def test_stdin_matches_sol_controller(self):
        class A:  # the argparse namespace fields build_stdin reads
            bare, depth, option = False, 22, ["ImprovingRazorGuard=false"]
        self.assertEqual(br.build_stdin(A), ["uci", "setoption name Threads value 1", "setoption name Hash value 16",
                                             "setoption name OwnBook value false",
                                             "setoption name ImprovingRazorGuard value false", "isready", "bench 22"])
        A.bare = True
        self.assertEqual(br.build_stdin(A), ["bench 22"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

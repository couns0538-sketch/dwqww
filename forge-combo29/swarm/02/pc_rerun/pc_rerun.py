#!/usr/bin/env python3
"""S02 — re-run my own findings on the PC r15 build under PC20, and say per finding whether it is repaired.

Findings under test (all originally measured on the BASE build, no setoption or S14):
  S-F4  a `go` naming only the OPPONENT's clock sets no limit -> the search never ends by itself.
        This is the natural test for FORGE_FIX_GO_PARSE ("a `go` keyword is never taken as the value of the
        keyword before it"), which is what the coordinator asked me to check.
  S-F3  `ponderhit` on a non-ponder search is a no-op and the search runs on.
  S-F5  the button `Clear Hash` given a value answers `invalid value`.
  S-F2  an empty `searchmoves` restriction answers `bestmove 0000` on a board with legal moves.

Rules I hold to here:
  * THREADS 1 on every run (seat 04: scores above Threads 1 are not reproducible).
  * every search is the FIRST of a FRESH process, so it is COLD (seat 10's rule).
  * the driver is INTERACTIVE — one line, its answer read to completion, then the next (19-F12: piping and
    closing stdin makes this build invent a bestmove).
  * every `setoption`'s acceptance is checked: `unknown option` / `invalid value` aborts the case, because on
    this build an option that does not exist is silently a no-op otherwise.

usage: pc_rerun.py <pc_exe> <outdir> [base_exe]
"""
import json
import os
import re
import subprocess
import sys
import threading
import time

PC = sys.argv[1] if len(sys.argv) > 1 else "/agent/repos/pc/forge-combo29/build-pc/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "out_pc_rerun"
BASE = sys.argv[3] if len(sys.argv) > 3 else "/agent/repos/base/forge-combo29/build/forge"

S14 = [
    "setoption name LmrQuietBase value 93",
    "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13",
    "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643",
    "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8",
    "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24",
    "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212",
    "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2",
    "setoption name NonPawnCorrection value true",
]
PC20 = ["setoption name Threads value 1", "setoption name Hash value 16"] + S14 + [
    "setoption name CuckooRep value true",
    "setoption name HistRework value 2",
    "setoption name TtPruneV2 value true",
    "setoption name CorrHistV2 value true",
    "setoption name MateAlphaGuard value true",
    "setoption name OwnBook value false",
]

# OwnBook false on BOTH builds: without it a `go wtime` from startpos is answered by the BOOK in ~1 ms with a
# `info string book move` line, which looks exactly like "the partial-clock defect is gone". My first version of
# this comparison left it at the default on the base build and produced precisely that false reading.
BASE_SETUP = (["setoption name Threads value 1", "setoption name Hash value 16"]
              + S14 + ["setoption name OwnBook value false"])

START_W = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
START_B = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"
MID = "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9"
BAD = ("unknown option", "invalid value", "ERROR")


class Engine:
    def __init__(self, exe, setup):
        env = {k: v for k, v in os.environ.items()
               if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
        self.proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
        self.lines, self.bad = [], []
        threading.Thread(target=self._read, daemon=True).start()
        self.send("uci")
        self.wait("uciok")
        for s in setup:
            self.send(s)
        self.send("isready")
        if not self.wait("readyok"):
            raise SystemExit("FAIL: no readyok after setup")
        for l in self.lines:
            if any(b in l for b in BAD):
                self.bad.append(l)
        if self.bad:
            raise SystemExit("FAIL: an option was refused during setup: %r" % self.bad)
        self.setup_ok = True

    def _read(self):
        for line in self.proc.stdout:
            self.lines.append(line.rstrip("\n"))

    def send(self, t):
        if self.proc.poll() is None:
            try:
                self.proc.stdin.write(t + "\n")
                self.proc.stdin.flush()
            except Exception:
                pass

    def mark(self):
        return len(self.lines)

    def wait(self, pref, start=0, timeout=20.0):
        dl = time.monotonic() + timeout
        while time.monotonic() < dl:
            for i in range(start, len(self.lines)):
                if self.lines[i].startswith(pref):
                    return True
            if self.proc.poll() is not None:
                return any(l.startswith(pref) for l in self.lines[start:])
            time.sleep(0.001)
        return False

    def since(self, start):
        return list(self.lines[start:])

    def close(self):
        self.send("quit")
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


def case_sf4(exe, setup):
    """S-F4: a go naming only the opponent's clock. Does it end by itself within 2 s?"""
    rows = []
    for fen, label, go in ((START_W, "White to move", "go wtime 100"),
                           (START_B, "Black to move", "go wtime 100"),
                           (START_W, "White to move", "go btime 100"),
                           (START_B, "Black to move", "go btime 100"),
                           (START_W, "White to move", "go wtime 100 btime 100")):
        e = Engine(exe, setup)
        e.send("position fen " + fen)
        e.send("isready")
        n = e.mark()
        e.wait("readyok", n)
        n = e.mark()
        t0 = time.monotonic()
        e.send(go)
        ended = e.wait("bestmove", n, 2.0)
        el = (time.monotonic() - t0) * 1000
        infos = [l for l in e.since(n) if l.startswith("info string")]
        if not ended:
            e.send("stop")
            e.wait("bestmove", n, 5.0)
        e.close()
        if any("book move" in l for l in infos):
            raise SystemExit("FAIL: %r was answered by the BOOK, so it says nothing about the clock. "
                             "OwnBook must be false in this comparison." % go)
        rows.append({"fen": fen, "side": label, "go": go, "ended_by_itself": ended,
                     "elapsed_ms": round(el, 1), "info_string_lines": infos})
        print("  %-14s %-26s ended=%s  %7.1f ms  warnings=%d"
              % (label, go, ended, el, len(infos)))
    return rows


def case_sf3(exe, setup):
    """S-F3: ponderhit on a NON-ponder search is a no-op."""
    e = Engine(exe, setup)
    e.send("position fen " + MID)
    e.send("isready")
    n = e.mark()
    e.wait("readyok", n)
    e.send("go infinite")
    time.sleep(0.3)
    n = e.mark()
    e.send("ponderhit")
    ended = e.wait("bestmove", n, 1.0)
    infos = [l for l in e.since(n) if l.startswith("info string")]
    e.send("stop")
    e.wait("bestmove", n, 5.0)
    e.close()
    print("  go infinite + ponderhit -> ended by itself: %s  warnings=%d" % (ended, len(infos)))
    return [{"go": "go infinite", "trigger": "ponderhit", "ended_by_itself": ended,
             "info_string_lines": infos,
             "verdict": "S-F3 STILL PRESENT (search runs on)" if not ended else "S-F3 GONE"}]


def case_sf5(exe, setup):
    """S-F5: the button `Clear Hash` given a value."""
    rows = []
    for cmd, label in (("setoption name Clear Hash value 0", "with value 0"),
                       ("setoption name Clear Hash value true", "with value true"),
                       ("setoption name Clear Hash", "no value (correct form)")):
        e = Engine(exe, setup)
        e.send("position fen " + START_W)
        e.send("isready")
        n = e.mark()
        e.wait("readyok", n)
        n = e.mark()                     # mark BEFORE the setoption under test
        e.send(cmd)
        e.send("isready")
        e.wait("readyok", n)
        infos = [l for l in e.since(n) if l.startswith("info string")]
        e.close()
        rows.append({"command": cmd, "label": label, "info_string_lines": infos})
        print("  %-42s (%s) -> warnings=%d %r" % (cmd, label, len(infos), infos))
    return rows


def case_sf2(exe, setup):
    """S-F2: an empty searchmoves restriction -> `0000` on a board with 20 legal moves."""
    e = Engine(exe, setup)
    e.send("position fen " + START_W)
    e.send("isready")
    n = e.mark()
    e.wait("readyok", n)
    n = e.mark()
    e.send("go searchmoves depth 2")
    got = e.wait("bestmove", n, 20.0)
    seg = e.since(n)
    bm = [l for l in seg if l.startswith("bestmove")]
    infos = [l for l in seg if l.startswith("info string")]
    e.close()
    move = bm[-1].split()[1] if bm else "NONE"
    print("  go searchmoves depth 2 -> bestmove %s  warnings=%r  (0000 = S-F2 still present)"
          % (move, infos))
    return [{"go": "go searchmoves depth 2", "bestmove": move,
             "info_string_lines": infos,
             "verdict": "S-F2 STILL PRESENT" if move == "0000" else "S-F2 GONE"}]


def main():
    os.makedirs(OUT, exist_ok=True)
    print("PC build:   %s" % PC)
    print("base build: %s" % BASE)
    print("settings:   PC20 (Threads 1, Hash 16, S14, six PC switches)")
    print()
    out = {}
    # The base build cannot take PC20: the four search switches and MateAlphaGuard do not exist there and
    # answer `unknown option` (which my setup check treats as a hard failure — file 5 warns about exactly
    # this). So the base build is measured under S14 (plus Threads 1 / Hash 16), and that is stated per row.
    for exe, build, setup in ((PC, "pc_r15+PC20", PC20), (BASE, "base+S14", BASE_SETUP)):
        if not os.path.exists(exe):
            sys.exit("FAIL: %s missing" % exe)
        print("== %s (%s)" % (build, exe))
        out[build] = {
            "sf4_partial_clock": case_sf4(exe, setup),
            "sf3_ponderhit": case_sf3(exe, setup),
            "sf5_clear_hash_button": case_sf5(exe, setup),
            "sf2_empty_searchmoves": case_sf2(exe, setup),
        }
        print()
    json.dump({"pc_exe": PC, "base_exe": BASE,
               "pc_sha256": subprocess.run(["sha256sum", PC], capture_output=True,
                                           text=True).stdout.split()[0],
               "base_sha256": subprocess.run(["sha256sum", BASE], capture_output=True,
                                             text=True).stdout.split()[0],
               "settings": "PC20 on the PC build; S14 on the base build (it cannot take the PC20-only switches)",
               "threads": 1,
               "base_setup_options": BASE_SETUP,
               "pc20_options": PC20, "results": out,
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "results.json"), "w"), indent=1)


if __name__ == "__main__":
    main()

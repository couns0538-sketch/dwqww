#!/usr/bin/env python3
"""pc_pins.py EXE — pin the PC r15 build against the numbers in FABLE_TO_swarm_5.md.

Three regimes, exactly as file 5 states them:
  none   a fresh process, NO setoption at all: bench 11 = 312866, bench 13 = 862329,
         bench 16 = 3024920, go perft 5 = 4865609
  S14    the 14 settings of file 1: bench 11 = 242796, bench 13 = 656517
  PC20   S14 + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
         MateAlphaGuard true, OwnBook false: bench 11 = 278024, bench 13 = 587276

Also asserts every PC20 option name appears in the exe's own `uci` list, and stops on
`unknown option`, `invalid value` or `ERROR` lines as the rules require. One fresh process per
line; every line is read up to the answer it expects.
"""
import queue
import re
import subprocess
import sys
import threading
import time

S14 = [
    ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
    ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
    ("IirDepth", "2"), ("NonPawnCorrection", "true"),
]
PC20_EXTRA = [
    ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
    ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false"),
]
BAD = re.compile(r"unknown option|invalid value|invalid FEN|illegal move|^info string ERROR")


class Eng:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.q = queue.Queue()
        self.lines = []
        threading.Thread(target=self._rd, daemon=True).start()

    def _rd(self):
        for ln in self.p.stdout:
            self.q.put(ln.rstrip("\n"))
        self.q.put(None)

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def wait(self, pred, bound=120.0):
        end = time.monotonic() + bound
        while time.monotonic() < end:
            try:
                ln = self.q.get(timeout=0.2)
            except queue.Empty:
                if self.p.poll() is not None:
                    return None
                continue
            if ln is None:
                return None
            self.lines.append(ln)
            if pred(ln):
                return ln
        return "TIMEOUT"

    def close(self):
        try:
            self.send("quit")
            self.p.stdin.close()
        except OSError:
            pass
        try:
            self.p.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.p.kill()
        return self.p.returncode


def options_of(exe):
    e = Eng(exe)
    e.send("uci")
    e.wait(lambda l: l == "uciok")
    e.send("quit")
    e.close()
    return [m.group(1) for m in (re.search(r"^option name (.+?) type ", l)
                                 for l in e.lines) if m]


def run_bench(exe, kind, opts, target):
    """One fresh process: apply opts (with isready after each), then `bench N`, read the line."""
    e = Eng(exe)
    e.send("uci")
    e.wait(lambda l: l == "uciok")
    problems = []
    for name, value in opts:
        e.send(f"setoption name {name} value {value}")
        e.send("isready")
        e.wait(lambda l: l == "readyok", 20)
    for ln in e.lines:
        if BAD.search(ln):
            problems.append(ln)
    e.send(f"bench {kind}")
    line = e.wait(lambda l: "bench depth" in l, 300)
    e.send("quit")
    rc = e.close()
    return line, problems, rc


def run_perft(exe, depth=5):
    e = Eng(exe)
    e.send("uci")
    e.wait(lambda l: l == "uciok")
    e.send("position startpos")
    e.send("isready")
    e.wait(lambda l: l == "readyok")
    e.send(f"go perft {depth}")
    e.wait(lambda l: l.startswith("nodes "), 300)
    e.send("quit")
    e.close()
    nodes = [l for l in e.lines if l.startswith("nodes ")]
    return nodes[-1] if nodes else None


def main():
    exe = sys.argv[1]
    print(f"exe {exe}")

    have = options_of(exe)
    print(f"exe lists {len(have)} options")
    missing = [n for n, _ in PC20_EXTRA if n not in have]
    print(f"PC20 options missing from the uci list: {missing if missing else 'none'}")

    rows = []
    checks = [
        ("none", 11, [], 312866), ("none", 13, [], 862329), ("none", 16, [], 3024920),
        ("S14", 11, S14, 242796), ("S14", 13, S14, 656517),
        ("PC20", 11, S14 + PC20_EXTRA, 278024), ("PC20", 13, S14 + PC20_EXTRA, 587276),
    ]
    bad = 0
    print(f"\n{'regime':7} {'bench':>6} {'expected':>9} {'got':>9}  verdict")
    for regime, depth, opts, expect in checks:
        line, problems, rc = run_bench(exe, depth, opts, expect)
        nodes = None
        if isinstance(line, str):
            m = re.search(r" nodes (\d+)", line)
            nodes = int(m.group(1)) if m else None
        ok = nodes == expect and not problems and rc == 0
        if not ok:
            bad += 1
        print(f"{regime:7} {depth:>6} {expect:>9} {str(nodes):>9}  {'OK' if ok else 'MISMATCH'}")
        if problems:
            print(f"    PROBLEM LINES: {problems[:4]}")
        rows.append({"regime": regime, "bench": depth, "expected": expect, "got": nodes,
                     "ok": ok, "problems": problems, "rc": rc})

    perft = run_perft(exe)
    p_ok = perft == "nodes 4865609"
    if not p_ok:
        bad += 1
    print(f"{'none':7} {'perft5':>6} {4865609:>9} {perft.split()[-1] if perft else '?':>9}  "
          f"{'OK' if p_ok else 'MISMATCH'}")

    print(f"\n{bad} mismatch(es) against FABLE_TO_swarm_5.md")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

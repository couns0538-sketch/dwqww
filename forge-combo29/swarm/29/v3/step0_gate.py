#!/usr/bin/env python3
"""FILE 7 STEP 0 GATE: the eight bench numbers and the three `eval` lines.

If ANY of these misses, the job stops and reports raw output — this harness therefore aborts on the first mismatch
and prints everything it saw, rather than continuing to profile a build that is not the PC's shape.

Regime per line: a FRESH engine process, Threads 1, Hash 16, the load order File-then-arch, drained to the terminal
token. Every option name is checked against the exe's `uci` list first; `unknown option`, `invalid value` or `ERROR`
aborts.
"""
import subprocess
import sys

EXE = sys.argv[1]
NET = sys.argv[2]

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]

# file 7's table
EXPECT_BENCH = {
    ("none", "bench 11"): 312866, ("none", "bench 13"): 862329,
    ("PC20", "bench 11"): 278024, ("PC20", "bench 13"): 587276,
    ("net", "bench 11"): 965454, ("net", "bench 13"): 4151906,
    ("PC20+net", "bench 11"): 625258, ("PC20+net", "bench 13"): 3652372,
}
EXPECT_EVAL = {
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1": 968,
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3": 1176,
    "8/5pk1/6p1/8/3R4/6P1/5PK1/3r4 w - - 0 40": 31,
}
BAD = ("unknown option", "invalid value", "ERROR")


class Engine:
    def __init__(self):
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  text=True, bufsize=1)

    def send(self, line):
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def drain(self, stop):
        got = []
        for line in self.p.stdout:
            for b in BAD:
                if b in line:
                    raise SystemExit(f"ABORT: engine complained: {line.strip()}")
            got.append(line.rstrip())
            if line.startswith(stop):
                return got
        raise SystemExit(f"ABORT: stdout closed waiting for {stop!r}")

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=30)
        except Exception:
            self.p.kill()


def setup(regime):
    e = Engine()
    e.send("uci")
    e.drain("uciok")
    if "net" in regime:
        e.send(f"setoption name NNUEArchFile value {NET}")
        e.send("setoption name NNUEArch value true")
    if regime.startswith("PC20"):
        for k, v in PC20:
            e.send(f"setoption name {k} value {v}")
    e.send("setoption name Hash value 16")
    e.send("setoption name Threads value 1")
    e.send("isready")
    got = e.drain("readyok")
    if "net" in regime:
        if not any("NNUE v3 active" in l for l in got):
            raise SystemExit(f"ABORT: {regime}: no 'NNUE v3 active' line — net did not load. Raw: {got[-4:]}")
    return e


fails = 0
print("=== STEP 0: eight bench numbers ===")
for regime in ("none", "PC20", "net", "PC20+net"):
    for depth in (11, 13):
        e = setup(regime)
        e.send(f"bench {depth}")
        lines = e.drain("info string bench")
        e.close()
        f = lines[-1].split()
        got = int(f[f.index("nodes") + 1]) if "nodes" in f else None
        exp = EXPECT_BENCH[(regime, f"bench {depth}")]
        ok = got == exp
        if not ok:
            fails += 1
        print(f"{regime:9s} bench {depth}: got {got:>9}  expected {exp:>9}  {'MATCH' if ok else '*** MISMATCH ***'}")

print()
print("=== STEP 0: three eval lines (PC20 + test net) ===")
for fen, exp in EXPECT_EVAL.items():
    e = setup("PC20+net")
    e.send(f"position fen {fen}")
    e.send("eval")
    lines = e.drain("info string eval")
    e.close()
    line = lines[-1]
    # read the nnue field
    f = line.split()
    got = int(f[f.index("nnue") + 1]) if "nnue" in f else None
    hce = int(f[f.index("hce") + 1]) if "hce" in f else None
    ok = (got == exp and hce == 0)
    if not ok:
        fails += 1
    print(f"nnue {got:>6} hce {hce}  expected nnue {exp:>6} hce 0   {'MATCH' if ok else '*** MISMATCH ***'}  {fen[:44]}")
    if not ok:
        print(f"   raw: {line}")

print()
print("STEP 0 " + ("PASSED — all eight benches and all three eval lines match" if fails == 0
                  else f"FAILED — {fails} mismatch(es); JOB STOPS HERE"))
sys.exit(0 if fails == 0 else 1)

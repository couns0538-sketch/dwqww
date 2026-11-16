#!/usr/bin/env python3
"""Verify the PC r15 build against the known answers in FABLE_TO_swarm_5.md.

Known answer rows (a fresh process for each line):
  none  : no setoption at all      -> bench 11 312866 | bench 13 862329 | bench 16 3024920 | perft 5 4865609
  S14   : the 14 settings, file 1  -> bench 11 242796 | bench 13 656517
  PC20  : S14 + six more           -> bench 11 278024 | bench 13 587276

Safety: every option name is checked against the exe's own `uci` list first; any `unknown option`, `invalid value`
or `ERROR` line aborts; a missing node count aborts rather than being compared as an implicit zero.

The driver writes a command, then drains stdout to its terminal token BEFORE writing the next command, so no search
is ever aborted by a closed pipe (19-F12) and no reply is read out of order.
"""
import subprocess, sys

EXE = sys.argv[1]

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]

KNOWN = {
    ("none", "bench 11"): 312866, ("none", "bench 13"): 862329,
    ("none", "bench 16"): 3024920, ("none", "perft 5"): 4865609,
    ("S14", "bench 11"): 242796, ("S14", "bench 13"): 656517,
    ("PC20", "bench 11"): 278024, ("PC20", "bench 13"): 587276,
}
BAD = ("unknown option", "invalid value", "ERROR")


def uci_options():
    out = subprocess.run([EXE], input="uci\nquit\n", capture_output=True, text=True).stdout
    return {l[len("option name "):].split(" type ")[0]
            for l in out.splitlines() if l.startswith("option name ")}


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
        raise SystemExit(f"ABORT: stdout closed while waiting for {stop!r}")

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=30)
        except Exception:
            self.p.kill()


def run(regime, kind, arg=None):
    e = Engine()
    try:
        e.send("uci")
        e.drain("uciok")
        if regime in ("S14", "PC20"):
            for k, v in S14:
                e.send(f"setoption name {k} value {v}")
        if regime == "PC20":
            for k, v in PC20_EXTRA:
                e.send(f"setoption name {k} value {v}")
        e.send("isready")
        e.drain("readyok")

        if kind == "bench":
            e.send(f"bench {arg}")
            lines = e.drain("info string bench")
            f = lines[-1].split()
            return int(f[f.index("nodes") + 1]) if "nodes" in f else None
        e.send("position startpos")
        e.send("go perft 5")
        lines = e.drain("nodes ")
        return int(lines[-1].split()[1])
    finally:
        e.close()


opts = uci_options()
need = {k for k, _ in S14} | {k for k, _ in PC20_EXTRA}
missing = need - opts
print(f"options listed by the exe: {len(opts)}")
print("MISSING OPTIONS: " + str(sorted(missing)) if missing else
      "every option PC20 needs is listed by the exe")

fails = 0
print()
plan = [("none", "bench", 11), ("none", "bench", 13), ("none", "bench", 16), ("none", "perft", None),
        ("S14", "bench", 11), ("S14", "bench", 13),
        ("PC20", "bench", 11), ("PC20", "bench", 13)]
for regime, kind, arg in plan:
    key = (regime, "perft 5" if kind == "perft" else f"bench {arg}")
    n = run(regime, kind, arg)
    exp = KNOWN[key]
    ok = (n == exp)
    if not ok:
        fails += 1
    print(f"{regime:5s} {key[1]:10s} got {n:>9}  expected {exp:>9}  {'MATCH' if ok else 'MISMATCH'}")

print()
print("ALL KNOWN VALUES MATCH" if fails == 0 else f"{fails} MISMATCHES")
sys.exit(0 if fails == 0 else 1)

#!/usr/bin/env python3
"""Verify the PC r15 build against the known answers in FABLE_TO_swarm_5.md.

Three regimes, each of which the file gives exact numbers for:
  none  : no setoption at all           -> bench 11 312866 | bench 13 862329 | bench 16 3024920 | perft 5 4865609
  S14   : the 14 settings of file 1     -> bench 11 242796 | bench 13 656517
  PC20  : S14 + six more                -> bench 11 278024 | bench 13 587276

Every option name is checked against the exe's own `uci` list first, and any `unknown option`, `invalid value` or
`ERROR` line aborts the run (the file requires this). A bench line that does not parse aborts too: a missing number
must never be compared as an implicit zero.
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
    ("none", "bench 11"): 312866,
    ("none", "bench 13"): 862329,
    ("none", "bench 16"): 3024920,
    ("none", "perft 5"): 4865609,
    ("S14", "bench 11"): 242796,
    ("S14", "bench 13"): 656517,
    ("PC20", "bench 11"): 278024,
    ("PC20", "bench 13"): 587276,
}


def uci_options():
    out = subprocess.run([EXE], input="uci\nquit\n", capture_output=True, text=True).stdout
    names = set()
    for line in out.splitlines():
        if line.startswith("option name "):
            names.add(line[len("option name "):].split(" type ")[0])
    return names


def run(regime, cmd):
    """One fresh process per line, drained to the terminal token."""
    cmds = ["uci"]
    if regime in ("S14", "PC20"):
        for k, v in S14:
            cmds.append(f"setoption name {k} value {v}")
    if regime == "PC20":
        for k, v in PC20_EXTRA:
            cmds.append(f"setoption name {k} value {v}")
    if regime == "none":
        pass
    cmds += ["isready", cmd]
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    for c in cmds[:-1]:
        p.stdin.write(c + "\n"); p.stdin.flush()
        if c == "isready":
            for line in p.stdout:
                if "unknown option" in line or "invalid value" in line or "ERROR" in line:
                    raise SystemExit(f"ABORT: engine rejected an option: {line.strip()}")
                if line.startswith("readyok"):
                    break
    p.stdin.write(cmds[-1] + "\n"); p.stdin.flush()
    want = "bestmove" if cmd.startswith("go perft") else "info string bench"
    got = []
    for line in p.stdout:
        if "unknown option" in line or "invalid value" in line or "ERROR" in line:
            raise SystemExit(f"ABORT: engine complained: {line.strip()}")
        got.append(line.rstrip())
        if line.startswith(want):
            break
    p.stdin.write("quit\n"); p.stdin.flush(); p.wait()
    return got


def nodes_of(lines, cmd):
    for line in lines:
        if cmd.startswith("go perft") and line.startswith("nodes "):
            return int(line.split()[1])
        if line.startswith("info string bench"):
            f = line.split()
            if "nodes" in f:
                return int(f[f.index("nodes") + 1])
    return None


opts = uci_options()
required = {k for k, _ in S14} | {k for k, _ in PC20_EXTRA}
missing = required - opts
print(f"options listed by the exe: {len(opts)}")
if missing:
    print(f"MISSING OPTIONS: {sorted(missing)}")
else:
    print("every option PC20 needs is listed by the exe")

fails = 0
print()
for regime in ("none", "S14", "PC20"):
    for cmd in ("bench 11", "bench 13", "bench 16", "go perft 5"):
        if regime != "none" and cmd not in ("bench 11", "bench 13"):
            continue
        key = (regime, "perft 5" if cmd.startswith("go perft") else cmd)
        lines = run(regime, cmd + ("\nposition startpos" if cmd.startswith("go perft") else ""))
        n = nodes_of(lines, cmd)
        exp = KNOWN.get(key)
        if n is None:
            print(f"ABORT: no node count parsed for {regime} / {cmd}")
            raise SystemExit(1)
        ok = (exp is not None and n == exp)
        if exp is not None and not ok:
            fails += 1
        mark = "MATCH " if ok else ("no known value" if exp is None else "MISMATCH")
        print(f"{regime:5s} {cmd:10s} got {n:>9}  expected {str(exp):>9}  {mark}")
print()
print("ALL KNOWN VALUES MATCH" if fails == 0 else f"{fails} MISMATCHES")
sys.exit(0 if fails == 0 else 1)

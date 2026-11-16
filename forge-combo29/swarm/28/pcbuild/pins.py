#!/usr/bin/env python3
"""pins.py EXE MODE — the four honesty pins, taken the way file 4 says they must be.

File 4 (found by seat 10): the four pins are DEFAULT-option numbers — a fresh engine, NO setoption at all.
The node sums (O/G depth 12/14) are the ones taken under S14. A harness that applies one regime to both
sees a false mismatch. My original HONESTY.txt (job0) sent `ucinewgame` before bench, which is not a
setoption and not S14, but this script removes even that so the pins are taken exactly as specified.

MODES:
  none   — no setoption at all, one fresh process per line
  s14    — S14's 14 setoptions, then the line
  pc20   — S14's 14 then CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
           MateAlphaGuard true, OwnBook false, then the line

Expected (file 5, measured on the PC's own exe):
  none: 312866 / 862329 / 3024920 / 4865609
  s14 : 242796 / 656517 / - / -
  pc20: 278024 / 587276 / - / -

Usage: pins.py EXE MODE
"""
import os
import re
import subprocess
import sys

S14 = {
    "LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
    "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
    "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
    "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true",
}
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
LINES = [("bench 11", "bench 11"), ("bench 13", "bench 13"), ("bench 16", "bench 16"),
         ("go perft 5", "go perft 5")]
EXPECT = {
    "none": {"bench 11": 312866, "bench 13": 862329, "bench 16": 3024920, "go perft 5": 4865609},
    "s14": {"bench 11": 242796, "bench 13": 656517},
    "pc20": {"bench 11": 278024, "bench 13": 587276},
}


def run(exe, mode, cmd):
    """One fresh process; options sent before the line; read to EOF."""
    script = ["uci"]
    if mode in ("s14", "pc20"):
        script += ["isready"]
        script += [f"setoption name {k} value {v}" for k, v in S14.items()]
        script += ["isready"]
        if mode == "pc20":
            script += [f"setoption name {k} value {v}" for k, v in PC20_EXTRA]
            script += ["isready"]
    script += [cmd, "quit"]
    p = subprocess.run([exe], input="\n".join(script) + "\n", capture_output=True, text=True,
                       timeout=300)
    out = p.stdout
    bad = [l for l in out.splitlines()
           if "unknown option" in l or "invalid value" in l or l.startswith("ERROR")]
    if cmd.startswith("bench"):
        m = re.search(r"bench depth (\d+) nodes (\d+)", out)
        return (int(m.group(2)) if m else None), bad, out
    m = re.search(r"^nodes (\d+)", out, re.M)
    return (int(m.group(1)) if m else None), bad, out


def main() -> int:
    exe, mode = sys.argv[1], sys.argv[2]
    if mode not in EXPECT:
        raise SystemExit("mode must be none, s14 or pc20")
    print(f"| line | expected ({mode}) | got | verdict |")
    print("|---|---|---|---|")
    allok = True
    for label, cmd in LINES:
        got, bad, out = run(exe, mode, cmd)
        exp = EXPECT[mode].get(label)
        if bad:
            print(f"| {label} | {exp if exp is not None else '-'} | REJECTED: {bad[0][:60]} | **STOP** |")
            allok = False
            continue
        if exp is None:
            print(f"| {label} | (not published for {mode}) | {got} | recorded |")
        else:
            ok = got == exp
            allok = allok and ok
            print(f"| {label} | {exp} | {got} | {'MATCH' if ok else '**MISMATCH**'} |")
    print()
    print("ALL PINS MATCH" if allok else "PIN MISMATCH OR REJECTION — this build is not used for claims")
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())

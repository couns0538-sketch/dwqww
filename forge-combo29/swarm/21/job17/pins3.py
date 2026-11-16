#!/usr/bin/env python3
"""pins3.py EXE OUTDIR

The three honesty rows of FABLE_TO_swarm_5 for the PC build (r15), each in a FRESH process,
with a `date -u` stamp. Threads 1 everywhere (swarm rule).

Row 1 = DEFAULT: no setoption at all.
Row 2 = S14: the 14 settings of file 1, then ucinewgame + isready before each go.
Row 3 = PC20: S14 then CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
        MateAlphaGuard true, OwnBook false.

Every `setoption` is followed by `isready` and read to `readyok`; the run STOPS on
`unknown option`, `invalid value` or `ERROR` (and records it), because a silently ignored
option makes the whole row meaningless.
"""
import json
import os
import subprocess
import sys

S14 = [
    ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
    ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
    ("IirDepth", "2"), ("NonPawnCorrection", "true"),
]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BASIC = [("Hash", "16"), ("Threads", "1")]
BAD = ("unknown option", "invalid value", "ERROR")


def run(exe, opts, cmds):
    env = dict(os.environ)
    for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
        env.pop(k, None)
    lines = ["uci"]
    for n, v in opts:
        lines += ["setoption name %s value %s" % (n, v), "isready"]
    if opts:
        lines += ["ucinewgame", "isready"]
    lines += list(cmds) + ["quit"]
    p = subprocess.run([exe], input="\n".join(lines) + "\n", text=True,
                       capture_output=True, timeout=1200, env=env, errors="replace")
    out = p.stdout + p.stderr
    bad = [l for l in out.splitlines() if any(b in l for b in BAD)]
    return out, bad


def nums(out):
    import re
    d = {}
    for key, pat in (("b11", r"bench depth 11 nodes (\d+)"),
                     ("b13", r"bench depth 13 nodes (\d+)"),
                     ("b16", r"bench depth 16 nodes (\d+)"),
                     ("p5", r"^nodes (\d+)$")):
        m = re.search(pat, out, re.M)
        d[key] = int(m.group(1)) if m else None
    return d


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    rows = {}
    for label, opts in (("default", []), ("S14", BASIC + S14), ("PC20", BASIC + S14 + PC20_EXTRA)):
        out, bad = run(exe, opts, ["bench 11", "bench 13", "bench 16", "go perft 5"])
        with open(os.path.join(outdir, "pins_%s.txt" % label), "w") as fh:
            fh.write("=== %s, options: %s\n" % (label, opts or "none"))
            fh.write(out)
            fh.write("=== bad lines: %s\n" % (bad or "none"))
        rows[label] = dict(nums=nums(out), bad=bad)
        print("%-8s %s%s" % (label, rows[label]["nums"],
                             "  BAD: %s" % bad if bad else ""))
    with open(os.path.join(outdir, "pins_summary.json"), "w") as fh:
        json.dump(rows, fh, indent=1)


if __name__ == "__main__":
    main()
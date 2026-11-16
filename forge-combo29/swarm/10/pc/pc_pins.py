#!/usr/bin/env python3
"""pc_pins.py EXE OUTDIR -- the three known answer rows for the PC's engine (file 5).

Rows, each from a FRESH process (file 4 / 10-F21: cold baseline is a fresh process or ucinewgame):
  none : no setoption at all               -> bench 11 312866, bench 13 862329, bench 16 3024920, perft 5 4865609
  S14  : Threads 1, Hash 16, the 14 S14    -> bench 11 242796, bench 13 656517
  PC20 : S14 + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
         MateAlphaGuard true, OwnBook false -> bench 11 278024, bench 13 587276

Also (a) confirms every option name PC20 sends appears in the exe's own `uci` list, and (b) stops on any
`unknown option`, `invalid value` or `ERROR` line, as file 5 requires.

bench and perft complete on their own before EOF, so a plain pipe is safe for them (10-F21 caveat: this
script uses a pipe ONLY for those two commands, never for `go depth`).
"""
import hashlib
import json
import os
import re
import subprocess
import sys

EXE = os.path.abspath(sys.argv[1])
OUT = os.path.abspath(sys.argv[2])
os.makedirs(OUT, exist_ok=True)

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

EXPECT = {
    "none": {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609},
    "s14": {"bench11": 242796, "bench13": 656517},
    "pc20": {"bench11": 278024, "bench13": 587276},
}
BAD = ("unknown option", "invalid value", "error")


def opts(regime):
    base = [] if regime == "none" else ["setoption name Threads value 1",
                                        "setoption name Hash value 16"]
    if regime == "s14":
        base += ["setoption name %s value %s" % kv for kv in S14]
    if regime == "pc20":
        base += ["setoption name %s value %s" % kv for kv in S14]
        base += ["setoption name %s value %s" % kv for kv in PC20_EXTRA]
    return base


def run(lines, tag):
    p = subprocess.run([EXE], input="\n".join(lines) + "\nquit\n",
                       capture_output=True, text=True, timeout=1800)
    with open(os.path.join(OUT, tag + ".txt"), "w") as f:
        f.write("=== exe %s\n=== commands:\n" % EXE)
        for l in lines:
            f.write("  " + l + "\n")
        f.write("=== stdout:\n" + p.stdout)
        f.write("=== stderr:\n" + p.stderr)
        f.write("=== exit %s\n" % p.returncode)
    bad = [l.strip() for l in (p.stdout + "\n" + p.stderr).splitlines()
           if any(b in l.lower() for b in BAD)]
    return p.stdout, p.stderr, p.returncode, bad


def bench(regime, depth):
    lines = ["uci", "isready"] + opts(regime) + ["isready", "ucinewgame", "isready",
                                                 "bench %d" % depth]
    out, err, rc, bad = run(lines, "%s_bench%d" % (regime, depth))
    m = re.search(r"bench depth \d+ nodes (\d+)", out)
    return (int(m.group(1)) if m else None), bad, rc


def perft5(regime):
    lines = ["uci", "isready"] + opts(regime) + ["isready", "position startpos", "isready",
                                                 "go perft 5"]
    out, err, rc, bad = run(lines, "%s_perft5" % regime)
    n = None
    for l in out.splitlines():
        if l.startswith("nodes "):
            n = int(l.split()[1])
    return n, bad, rc


def main():
    sha = hashlib.sha256(open(EXE, "rb").read()).hexdigest()
    uci_out, _, _, _ = run(["uci"], "uci_list")
    listed = set()
    for l in uci_out.splitlines():
        m = re.match(r"option name (.+?) type ", l)
        if m:
            listed.add(m.group(1))

    # every PC20 option name must be in the exe's own list
    pc20_names = [k for k, _ in S14 + PC20_EXTRA]
    missing = [n for n in pc20_names if n not in listed]

    res = {"exe": EXE, "sha256": sha, "options_in_uci_list": len(listed),
           "pc20_option_names_missing_from_uci": missing, "rows": {}}
    for regime in ("none", "s14", "pc20"):
        row = {}
        if regime in ("none", "s14", "pc20"):
            row["bench11"], b11, r11 = bench(regime, 11)
        if regime in ("none", "s14", "pc20"):
            row["bench13"], b13, r13 = bench(regime, 13)
        if regime == "none":
            row["bench16"], b16, r16 = bench(regime, 16)
            row["perft5"], bp5, rp5 = perft5(regime)
        row["_bad_lines"] = (b11 if "bench11" in row else []) + (b13 if "bench13" in row else []) \
            + (b16 if "bench16" in row else []) + (bp5 if "perft5" in row else [])
        exp = EXPECT[regime]
        row["_expected"] = exp
        row["_match"] = all(row.get(k) == v for k, v in exp.items())
        row["_all_rows_match"] = row["_match"]
        res["rows"][regime] = row

    res["EVERY_ROW_MATCHES"] = all(r["_match"] for r in res["rows"].values())
    res["any_bad_lines"] = any(r["_bad_lines"] for r in res["rows"].values())
    with open(os.path.join(OUT, "pc_pins.json"), "w") as f:
        json.dump(res, f, indent=2)
        f.write("\n")
    print(json.dumps(res, indent=2))


main()

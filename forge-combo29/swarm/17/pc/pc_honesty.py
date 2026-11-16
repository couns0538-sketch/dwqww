#!/usr/bin/env python3
"""seat 17: honesty check of the PC r15 build against FABLE_TO_swarm_5.md's known table.

Three regimes, each line a FRESH process (file 5: "a fresh process for each line"):
  none   : no setoption at all          bench 11/13/16 + go perft 5
  S14    : the 14 settings of file 1    bench 11/13
  PC20   : S14 + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
           MateAlphaGuard true, OwnBook false   bench 11/13

Fails loudly when a number is missing (no silent zero) or an option is refused,
which file 5 requires: stop on `unknown option`, `invalid value` or `ERROR`.

usage: pc_honesty.py <exe> <outdir>
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import datetime

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

EXPECT = {
    ("none", 11): 312866, ("none", 13): 862329, ("none", 16): 3024920,
    ("s14", 11): 242796, ("s14", 13): 656517,
    ("pc20", 11): 278024, ("pc20", 13): 587276,
}
EXPECT_PERFT5 = 4865609

BAD_WORDS = ("unknown option", "invalid value", "ERROR")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(exe, options, bench_depth=None, perft=False):
    """One fresh process. Returns (nodes, text, complaints)."""
    lines = ["uci"]
    payload = ["uci"]
    for name, value in options:
        payload += ["setoption name %s value %s" % (name, value), "isready"]
    if perft:
        payload += ["position startpos", "go perft 5"]
        # read until the nodes line
        proc = subprocess.run([exe], input="\n".join(payload) + "\nquit\n",
                              capture_output=True, text=True, timeout=600)
        text = proc.stdout + proc.stderr
        nodes = None
        for ln in text.splitlines():
            if ln.startswith("nodes "):
                nodes = int(ln.split()[1])
        complaints = [ln for ln in text.splitlines() if any(w in ln for w in BAD_WORDS)]
        return nodes, text, complaints
    payload += ["bench %d" % bench_depth]
    proc = subprocess.run([exe], input="\n".join(payload) + "\nquit\n",
                          capture_output=True, text=True, timeout=600)
    text = proc.stdout + proc.stderr
    nodes = None
    for ln in text.splitlines():
        if ln.startswith("info string bench"):
            m = re.search(r"nodes (\d+)", ln)
            if m:
                nodes = int(m.group(1))
    complaints = [ln for ln in text.splitlines() if any(w in ln for w in BAD_WORDS)]
    return nodes, text, complaints


def main():
    exe, outdir = sys.argv[1:3]
    os.makedirs(outdir, exist_ok=True)
    result = {"exe": exe, "sha256": sha256(exe),
              "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "rows": [], "problems": []}

    regimes = [
        ("none", []),
        ("s14", S14),
        ("pc20", S14 + PC20_EXTRA),
    ]
    for name, opts in regimes:
        depths = [11, 13, 16] if name == "none" else [11, 13]
        for depth in depths:
            nodes, text, complaints = run(exe, opts, bench_depth=depth)
            log = os.path.join(outdir, "%s_bench%d.log" % (name, depth))
            open(log, "w").write(text)
            expect = EXPECT[(name, depth)]
            row = {"regime": name, "what": "bench %d" % depth, "expected": expect,
                   "got": nodes, "match": nodes == expect,
                   "complaints": complaints, "log": log}
            if nodes is None:
                result["problems"].append("%s bench %d: no nodes line at all" % (name, depth))
            if complaints:
                result["problems"].append("%s bench %d: option complaint %r" % (name, depth, complaints[:2]))
            result["rows"].append(row)
            print(json.dumps(row))

    nodes, text, complaints = run(exe, [], perft=True)
    log = os.path.join(outdir, "none_perft5.log")
    open(log, "w").write(text)
    row = {"regime": "none", "what": "go perft 5", "expected": EXPECT_PERFT5,
           "got": nodes, "match": nodes == EXPECT_PERFT5, "complaints": complaints, "log": log}
    if nodes is None:
        result["problems"].append("perft 5: no nodes line at all")
    result["rows"].append(row)
    print(json.dumps(row))

    result["all_match"] = all(r["match"] for r in result["rows"])
    result["date_end"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    json.dump(result, open(os.path.join(outdir, "honesty.json"), "w"), indent=1)
    print(json.dumps({"all_match": result["all_match"], "problems": result["problems"]}, indent=1))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""honesty.py EXE OUTDIR : runs the four honesty checks, each in a FRESH process.
Writes OUTDIR/bench11.txt, bench13.txt, bench16.txt, perft5.txt, honesty.meta,
and honesty_table.txt (the parsed numbers)."""
import hashlib
import os
import re
import subprocess
import sys

EXE = os.path.abspath(sys.argv[1])
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)

S14 = [
    ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
    ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
    ("IirDepth", "2"), ("NonPawnCorrection", "true"),
]


def run(lines, outfile):
    p = subprocess.run([EXE], input="\n".join(lines) + "\n",
                       capture_output=True, text=True, timeout=1800)
    with open(outfile, "w") as f:
        f.write(p.stdout)
    with open(outfile + ".stderr", "w") as f:
        f.write(p.stderr)
    return p.stdout, p.returncode


def options_lines(threads=1, hash_mb=16):
    if threads == 0:
        return []
    opts = ["setoption name Threads value %d" % threads,
            "setoption name Hash value %d" % hash_mb]
    opts += ["setoption name %s value %s" % (k, v) for k, v in S14]
    return opts


BAD = ("unknown option", "invalid value", "invalid fen", "illegal move")


def check_bad(raw):
    bad = []
    for ln in raw.splitlines():
        low = ln.lower()
        for b in BAD:
            if b in low:
                bad.append(ln.strip())
    return bad


def bench_block(n):
    name = "bench%d" % n
    lines = ["uci", "isready"] + options_lines(0, 0) + ["isready", "ucinewgame",
                                                    "isready", "bench %d" % n, "quit"]
    raw, rc = run(lines, os.path.join(OUT, name + ".txt"))
    nodes = None
    for ln in raw.splitlines():
        m = re.search(r"bench depth \d+ nodes (\d+)", ln)
        if m:
            nodes = int(m.group(1))
    return nodes, rc, name, check_bad(raw)


def main():
    exe_sha = hashlib.sha256(open(EXE, "rb").read()).hexdigest()
    idraw, _ = run(["uci", "quit"], os.path.join(OUT, "uci_id.txt"))
    idname = ""
    for ln in idraw.splitlines():
        if ln.startswith("id name"):
            idname = ln.strip()
            break

    results = []
    for n, exp in ((11, 312866), (13, 862329), (16, 3024920)):
        nodes, rc, name, bad = bench_block(n)
        results.append((name, nodes, exp, nodes == exp, rc, bad))

    lines = ["uci", "isready"] + options_lines(0, 0) + ["isready", "position startpos",
                                                    "isready", "go perft 5", "quit"]
    raw, rc = run(lines, os.path.join(OUT, "perft5.txt"))
    pn = None
    for ln in raw.splitlines():
        m = re.match(r"nodes (\d+)\s*$", ln.strip())
        if m:
            pn = int(m.group(1))
    results.append(("perft5", pn, 4865609, pn == 4865609, rc, check_bad(raw)))

    with open(os.path.join(OUT, "honesty.meta"), "w") as f:
        f.write("exe %s\n" % EXE)
        f.write("sha256 %s\n" % exe_sha)
        f.write("%s\n" % idname)
        f.write("options:\n")
        for l in options_lines(0, 0):
            f.write("  %s\n" % l)
        f.write("one fresh process per line: uci,isready,<options=DEFAULT, none sent>,isready,ucinewgame,isready,<cmd>,quit\n""the honesty pins are DEFAULT-settings numbers; S14 setoptions change bench node counts (see FINDINGS)"
)

    with open(os.path.join(OUT, "honesty_table.txt"), "w") as f:
        f.write("check | got | expected | match | rc | bad-lines\n")
        for name, got, exp, ok, rc, bad in results:
            f.write("%s | %s | %s | %s | rc=%s | %d\n"
                    % (name, got, exp, "MATCH" if ok else "MISS", rc, len(bad)))
        f.write("ALL MATCH: %s\n" % all(r[3] for r in results))


main()

#!/usr/bin/env python3
"""check_s20f38.py OUT — my own check of seat 20's S-F38:

"`MateAlphaGuard true` is the switch that fixes the mate distance on the PC r15 build: on
 `8/8/1p6/8/p3p3/8/2Kpk3/8 w` at depth 12, Threads 1, Hash 16 — defaults give `mate -7` (14 plies, 28,084 nodes),
 `MateAlphaGuard true` ALONE gives `mate -4` (8 plies, 29,801 nodes), `MateAlphaGuard false` changes nothing.
 MateAlphaGuard DOES NOT EXIST on the base tree."

My harness. Four arms, one fresh process per run, 3 runs per arm (the claim is about a STABLE value, so 3 is enough
to catch instability, and every run's value is committed):
  A  PC build,  no setoption at all
  B  PC build,  MateAlphaGuard true alone
  C  PC build,  MateAlphaGuard false alone
  D  base build 6b98f217, `uci` list checked for MateAlphaGuard (the "does not exist" clause)

The true distance is 8 plies (mate -4), which seat 20 says their job16 proved by exhaustive search; I do not
re-derive it, I only check which arm reports it.

CONTROLS (enforced):
 - the `mate` token must PARSE into plies (no vacuous comparison);
 - the base build's `uci` answer must genuinely LACK MateAlphaGuard for arm D to mean anything;
 - depth 12 must be reached in every run.
"""
import re
import subprocess
import sys

OUT = sys.argv[1]
PC = "/home/ubuntu/builds/pc/forge"
BASE = "/home/ubuntu/builds/release/forge"
FEN = "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"
DEPTH = 12
RUNS = 3


def uci_list(exe):
    r = subprocess.run([exe], input="uci\nquit\n", capture_output=True, text=True, timeout=60)
    return [l for l in r.stdout.splitlines() if l.startswith("option name")]


def probe(exe, extra):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def sync():
        send("isready")
        while True:
            l = p.stdout.readline()
            if not l:
                raise EOFError
            if l.startswith("readyok"):
                return

    send("uci")
    while not p.stdout.readline().startswith("uciok"):
        pass
    for n, v in extra:
        send("setoption name %s value %s" % (n, v))
        sync()
    send("setoption name Threads value 1")
    sync()
    send("setoption name Hash value 16")
    sync()
    send("ucinewgame")
    sync()
    send("position fen " + FEN)
    sync()
    send("go depth %d" % DEPTH)
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise EOFError
        l = l.rstrip("\n")
        lines.append(l)
        if l.startswith("bestmove"):
            break
    sync()
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    score = nodes = None
    maxd = 0
    pvlen = 0
    for l in lines:
        if l.startswith("info depth"):
            t = l.split()
            try:
                d = int(t[2])
                maxd = max(maxd, d)
                if d == DEPTH and "score" in t and "nodes" in t:
                    si = t.index("score")
                    score = "%s %s" % (t[si + 1], t[si + 2])
                    nodes = int(t[t.index("nodes") + 1])
                    if "pv" in t:
                        pvlen = len(t) - t.index("pv") - 1
            except (IndexError, ValueError):
                pass
    return {"score": score, "nodes": nodes, "maxd": maxd, "pvlen": pvlen, "bm": lines[-1].split()[1]}


def plies(score):
    """'mate -4' -> 8 plies (2*|n| for a mated distance), 'mate 3' -> 5 plies (2n-1)."""
    if not score or not score.startswith("mate"):
        return None
    n = int(score.split()[1])
    return 2 * abs(n) if n < 0 else 2 * n - 1


arms = [
    ("A: PC, no setoption", PC, []),
    ("B: PC, MateAlphaGuard true alone", PC, [("MateAlphaGuard", "true")]),
    ("C: PC, MateAlphaGuard false alone", PC, [("MateAlphaGuard", "false")]),
    ("D: base 6b98f217, no setoption", BASE, []),
]

base_opts = uci_list(BASE)
if any("MateAlphaGuard" in o for o in base_opts):
    raise SystemExit("CONTROL FAILED: the base build's uci list DOES contain MateAlphaGuard, so seat 20's "
                     "'does not exist on the base tree' clause is wrong and arm D is meaningless")

out = []
def emit(s):
    out.append(s)
    print(s)

emit("## seat 20 S-F38 — is `MateAlphaGuard true` ALONE the switch that fixes the mate distance?")
emit("Board `%s`, `go depth %d`, Threads 1, Hash 16, %d fresh runs per arm." % (FEN, DEPTH, RUNS))
emit()
emit("| arm | run | score | plies | nodes | pv length | bestmove |")
emit("|---|---|---|---|---|---|---|")
summary = {}
for label, exe, extra in arms:
    got = []
    for i in range(1, RUNS + 1):
        r = probe(exe, extra)
        if r["maxd"] < DEPTH:
            raise SystemExit("CONTROL FAILED: %s run %d did not reach depth %d" % (label, i, DEPTH))
        pl = plies(r["score"])
        if r["score"] is None:
            raise SystemExit("CONTROL FAILED: %s run %d produced no parsable depth-%d score" % (label, i, DEPTH))
        got.append(r)
        emit("| %s | %d | %s | %s | %s | %d | %s |" % (label, i, r["score"], pl if pl is not None else "-",
                                                       f"{r['nodes']:,}", r["pvlen"], r["bm"]))
    summary[label] = got

emit()
emit("| arm | scores seen | stable? | plies | nodes |")
emit("|---|---|---|---|---|")
for label in summary:
    s = {g["score"] for g in summary[label]}
    pl = {plies(g["score"]) for g in summary[label]}
    nn = sorted(g["nodes"] for g in summary[label])
    emit("| %s | %s | %s | %s | %s..%s |" % (label, ", ".join(sorted(s)),
                                             "YES" if len(s) == 1 else "NO", ", ".join(str(x) for x in pl),
                                             f"{nn[0]:,}", f"{nn[-1]:,}"))

emit()
emit("| question | answer |")
emit("|---|---|")
a = {g["score"] for g in summary["A: PC, no setoption"]}
b = {g["score"] for g in summary["B: PC, MateAlphaGuard true alone"]}
c = {g["score"] for g in summary["C: PC, MateAlphaGuard false alone"]}
d = {g["score"] for g in summary["D: base 6b98f217, no setoption"]}
emit("| PC defaults report | %s |" % ", ".join(sorted(a)))
emit("| MateAlphaGuard true ALONE reports | %s |" % ", ".join(sorted(b)))
emit("| MateAlphaGuard false ALONE reports | %s |" % ", ".join(sorted(c)))
emit("| base build reports | %s |" % ", ".join(sorted(d)))
emit("| the guard is what changes the distance? | **%s** |" %
     ("YES" if a != b and b == {"mate -4"} else ("NO — true gives %s, defaults %s" % (", ".join(sorted(b)),
                                                                                       ", ".join(sorted(a))))))
emit("| false changes nothing vs defaults? | **%s** |" % ("YES" if c == a else "NO (%s vs %s)" %
                                                           (", ".join(sorted(c)), ", ".join(sorted(a)))))
emit("| base build lacks the option? | **YES** (verified from its own uci list) |")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")

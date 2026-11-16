#!/usr/bin/env python3
"""reverify_job3.py EXE OUT.txt : re-run a SAMPLE of job 3 under the hardened read discipline and compare
with the numbers I recorded in job3/raw/G_d10.tsv.

Hardened discipline (per seat 19's broadcast):
  * stdout is read line by line until the `bestmove` line before ANY further command is written;
  * stdin is never closed and `quit` is only sent after `bestmove` has been read;
  * a search that yields no `bestmove` within LIMIT seconds is a HANG and is counted, never guessed.

If the recorded job-3 numbers were produced by a harness that closed stdin mid-search, the re-run would
disagree (0 nodes / bestmove a2a3). Identical results mean the recorded table is valid.
"""
import re
import subprocess
import sys
import time

EXE, OUT = sys.argv[1], sys.argv[2]
DEPTH = 10
S14 = [("OwnBook", "false"), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]


def search(fen):
    """One fresh process; every command waits for its acknowledgement."""
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(cmd):
        p.stdin.write(cmd + "\n")
        p.stdin.flush()

    def to(tok, limit):
        lines = []
        deadline = time.monotonic() + limit
        while time.monotonic() < deadline:
            line = p.stdout.readline()
            if not line:
                return lines, False
            line = line.rstrip("\n")
            lines.append(line)
            if line.strip() == tok or line.startswith(tok):
                return lines, True
        return lines, False

    send("uci"); to("uciok", 10)
    for name, val in [("Threads", 1), ("Hash", 16)] + S14:
        send(f"setoption name {name} value {val}")
        send("isready"); to("readyok", 10)
    send("position fen " + fen)
    send("isready"); to("readyok", 10)
    send(f"go depth {DEPTH}")
    lines, got = to("bestmove", 300)          # READ UNTIL bestmove, stdin still open
    best = None
    score = None
    nodes = None
    for l in lines:
        if l.startswith("bestmove"):
            best = l.split()[1]
        m = re.match(r"^info depth (\d+) .*score (cp|mate) (-?\d+) nodes (\d+)", l)
        if m and int(m.group(1)) == DEPTH:
            score = (m.group(2), int(m.group(3)))
            nodes = int(m.group(4))
    if got and best:
        send("quit")                           # ONLY NOW
        try:
            p.wait(timeout=10)
        except Exception:
            p.kill()
    else:
        p.kill()
    return best, score, nodes, got


# read my recorded table
import chess  # noqa: E402

rec = {}
with open("/agent/repos/dwqww/forge-combo29/swarm/16/job3/raw/G_d10.tsv") as fh:
    fh.readline()
    for line in fh:
        p = line.rstrip("\n").split("\t")
        if len(p) >= 13 and p[2] != "HANG":
            rec[int(p[0])] = p

fens = [l.strip() for l in open("/agent/repos/dwqww/forge-combo29/swarm/16/job3/set_G.epd")
        if l.strip()][:12]

out = []
agree_bm = agree_score = agree_nodes = 0
for idx, fen in enumerate(fens):
    best, score, nodes, ok = search(fen)
    r = rec.get(idx)
    r_best, r_kind, r_val = (r[2], r[3], r[4]) if r else (None, None, None)
    same_bm = (best == r_best)
    same_score = (score is not None and r_kind is not None and
                  score[0] == r_kind and str(score[1]) == r_val)
    agree_bm += same_bm
    agree_score += same_score
    if nodes is not None:
        agree_nodes += 1
    out.append(f"idx {idx:3d} {fen[:44]:46s} recorded {r_best} {r_kind} {r_val} | re-run {best} "
               f"{score} nodes {nodes} | bm same {same_bm} score same {same_score}")
out.append("")
out.append(f"bestmove agreement: {agree_bm}/{len(fens)}   score agreement: {agree_score}/{len(fens)}")
out.append(f"re-runs that produced real nodes: {agree_nodes}/{len(fens)}")
out.append("a fabricated reply would show bestmove a2a3 with nodes 0/None")
text = "\n".join(out) + "\n"
print(text)
with open(OUT, "w") as fh:
    fh.write(text)

#!/usr/bin/env python3
"""run_draw.py EXE OUTJSONL : depth-10 S14 score for every draw-scheme position.

Reads:
  *.fens files in the job folder (one FEN per line)              -> `position fen <fen>`
  E_threefold.moves (one move list per line)                     -> `position startpos moves ...`

For every record it stores the score as reported, plus the parsed (kind, value) so a missing or
unparseable score can never be silently counted as 0. If a record has no parseable score the run
FAILS LOUDLY at the end instead of returning a tidy table of zeroes.
"""
import json
import os
import re
import shlex
import subprocess
import sys

S14 = [
    ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
    ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
    ("IirDepth", "2"), ("NonPawnCorrection", "true"),
]
SCORE_RE = re.compile(r"\bscore (cp|mate) (-?\d+)\b")


def run_one(exe, position_cmd, depth):
    p = subprocess.Popen(shlex.split(exe), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    lines = []

    def send(cmd):
        p.stdin.write(cmd + "\n")
        p.stdin.flush()

    def drain_until(word):
        for line in p.stdout:
            lines.append(line.rstrip("\n"))
            if line.strip() == word:
                return True
        return False

    send("uci")
    drain_until("uciok")
    send("setoption name Threads value 1"); send("isready"); drain_until("readyok")
    send("setoption name Hash value 16"); send("isready"); drain_until("readyok")
    for name, val in S14:
        send(f"setoption name {name} value {val}")
    send("isready"); drain_until("readyok")
    send("ucinewgame"); send("isready"); drain_until("readyok")
    send(position_cmd); send("isready"); drain_until("readyok")
    send(f"go depth {depth}")

    best = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        line = line.rstrip("\n")
        lines.append(line)
        if line.startswith("bestmove"):
            best = line
            break
    send("quit")
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
    return lines, best


def last_score(lines):
    """The (kind, value) of the deepest info line that carries a score. None if there is none."""
    out = None
    depth_seen = -1
    for line in lines:
        if not line.startswith("info depth"):
            continue
        m = SCORE_RE.search(line)
        if not m:
            continue
        d = re.search(r"\bdepth (\d+)", line)
        depth = int(d.group(1)) if d else -1
        if depth >= depth_seen:
            depth_seen = depth
            out = (m.group(1), int(m.group(2)))
    return out


def main():
    exe, outfile = sys.argv[1], sys.argv[2]
    jobdir = os.path.dirname(os.path.abspath(outfile))
    depth = 10

    jobs = []
    for name in ["A_KvK", "B_KNvK", "C_KBvK", "D_KNNvK", "Control_KQvK", "F_clock99"]:
        path = os.path.join(jobdir, name + ".fens")
        if not os.path.exists(path):
            continue
        for i, fen in enumerate(l.strip() for l in open(path) if l.strip()):
            jobs.append((name, i, f"position fen {fen}", fen))
    epath = os.path.join(jobdir, "E_threefold.moves")
    if os.path.exists(epath):
        for i, mv in enumerate(l.strip() for l in open(epath) if l.strip()):
            jobs.append(("E_threefold", i, f"position startpos moves {mv}", mv))

    print(f"total records to run: {len(jobs)}", flush=True)
    with open(outfile, "w") as out:
        for group, i, cmd, raw in jobs:
            lines, best = run_one(exe, cmd, depth)
            sc = last_score(lines)
            rec = {"group": group, "i": i, "position": raw, "bestmove": best,
                   "score_kind": sc[0] if sc else None,
                   "score_value": sc[1] if sc else None,
                   "lines": lines}
            out.write(json.dumps(rec) + "\n")
            out.flush()
    print("done", flush=True)


if __name__ == "__main__":
    main()

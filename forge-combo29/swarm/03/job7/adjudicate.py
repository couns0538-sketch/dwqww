#!/usr/bin/env python3
"""adjudicate.py OUTFILE : are the PC answers better or worse than the base answers on the four differing positions?

Method: the divergences are all in lone-king endgames, so a depth-8 answer is not adjudicable by either engine's own
depth-8 score. Instead, for each position, each of the TWO candidate moves is searched on BOTH builds at a much
greater depth (default 20), and the score of the move is taken to be the negamax score the searching side reports
after playing it — i.e. the search is rooted at the position, the candidate move is forced with `searchmoves`, and
the resulting score is compared.

`go depth N searchmoves <mv>` gives the score of that ONE move. Two independent adjudicators (base and r15 at depth
20) each rank the two moves, so a claim "PC's move is better" needs BOTH builds to agree; disagreement is reported as
"undecided".

Every score is read from an actual `info depth N ... score ...` line; a missing score aborts the run rather than
defaulting. Threads 1, Hash 16, OwnBook false, fresh process per search.
"""
import os
import re
import subprocess
import sys

import chess

OUT = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
DEPTH = int(os.environ.get("ADJ_DEPTH", "20"))
BASE = "/home/ubuntu/build-rel/forge"
PC = "/home/ubuntu/build-pc/forge"

CASES = {
    153: ("a4b4", "a4b5"),
    155: ("c6d6", "c6c7"),
    156: ("g5h3", "f2e3"),
    160: ("f1e2", "f1f2"),
}
FENS = [l.strip() for l in open(os.path.join(HERE, "..", "job4", "set_bm200.fens")) if l.strip()]
rawdir = OUT + ".raw"
os.makedirs(rawdir, exist_ok=True)


def score_of(exe, fen, move, tag):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    raw = open(os.path.join(rawdir, tag + ".txt"), "w")

    def send(c):
        raw.write(f">>> {c}\n")
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def until(tok):
        lines = []
        while True:
            line = p.stdout.readline()
            if line == "":
                raise RuntimeError(f"died waiting {tok} ({tag})")
            raw.write(line)
            raw.flush()
            s = line.strip()
            lines.append(s)
            if s.startswith(tok):
                return lines

    send("uci"); until("uciok")
    send("isready"); until("readyok")
    for o, v in (("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")):
        send(f"setoption name {o} value {v}")
        send("isready"); until("readyok")
    send("ucinewgame"); send("isready"); until("readyok")
    send(f"position fen {fen}")
    send("isready"); until("readyok")
    send(f"go depth {DEPTH} searchmoves {move}")
    lines = until("bestmove")
    send("quit")
    try:
        p.wait(timeout=600)
    except Exception:  # noqa: BLE001
        p.kill()
    raw.close()
    best = None
    for s in lines:
        m = re.match(r"info depth (\d+) .*score (cp|mate) (-?\d+)", s)
        if m and int(m.group(1)) == DEPTH:
            best = (m.group(2), int(m.group(3)))
    if best is None:
        raise RuntimeError(f"no depth-{DEPTH} score line for {tag} — refusing to guess")
    return best


def cmp_score(a, b):
    """+1 if score a is better for the side to move than b, -1 if worse, 0 equal.
    mate N (N>0) is best; mate -N is worst; cp compares numerically."""
    def rank(s):
        kind, val = s
        if kind == "mate":
            return (2, 1000 - val) if val > 0 else (0, -1000 - val)
        return (1, val)
    ra, rb = rank(a), rank(b)
    return (ra > rb) - (ra < rb)


lines = [f"adjudication depth {DEPTH}, Threads 1, Hash 16, OwnBook false, `go depth {DEPTH} searchmoves <mv>`",
         "each candidate move scored by each build independently; both must agree to declare a winner", ""]
lines.append("| idx | base answer (score) | PC answer (score) | verdict by BASE build | verdict by PC build | combined |")
lines.append("|---|---|---|---|---|---|")
verdicts = {}
for idx, (bm_base, bm_pc) in sorted(CASES.items()):
    fen = FENS[idx]
    b_base = score_of(BASE, fen, bm_base, f"p{idx}_{bm_base}_base")
    b_pc = score_of(BASE, fen, bm_pc, f"p{idx}_{bm_pc}_base")
    p_base = score_of(PC, fen, bm_base, f"p{idx}_{bm_base}_pc")
    p_pc = score_of(PC, fen, bm_pc, f"p{idx}_{bm_pc}_pc")
    v_base = cmp_score(b_pc, b_base)   # >0 means the PC move scores better by the base build
    v_pc = cmp_score(p_pc, p_base)
    def word(v):
        return "PC better" if v > 0 else ("base better" if v < 0 else "equal")
    if v_base == v_pc and v_base != 0:
        combined = f"**{word(v_base)}**"
    elif v_base == 0 and v_pc == 0:
        combined = "equal"
    else:
        combined = f"undecided (builds disagree: {word(v_base)} / {word(v_pc)})"
    verdicts[idx] = combined
    lines.append(f"| {idx} | {bm_base} ({b_base[0]} {b_base[1]}) | {bm_pc} ({p_pc[0]} {p_pc[1]}) | "
                 f"{word(v_base)} | {word(v_pc)} | {combined} |")
    print(f"idx {idx}: {combined}", flush=True)

lines.append("")
lines.append("scores shown are for the SIDE TO MOVE in the root position (negamax convention); a mate score is "
             "the engine's own claim and is not verified here as a forced mate unless it is a mate-in-N with N "
             "small enough to replay (job 5 did that for idx 156 and 160).")
open(OUT, "w").write("\n".join(lines) + "\n")
print("\n".join(lines))

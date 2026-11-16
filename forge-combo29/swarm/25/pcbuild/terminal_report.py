#!/usr/bin/env python3
"""terminal_report.py EXE : the cosmetic terminal-root findings, measured on one build.

Two things a GUI or a training consumer reads off the info lines of a terminal root:
  1. the score token: `mate 0` on a checkmated root (a mate distance of ZERO plies is not expressible)
     versus `cp 0` on a stalemated root — two different currencies for two zero-move positions;
  2. the number of info lines: `go nodes N` / `go movetime T` emit one line per depth up to 64 at 0 nodes,
     so a consumer that reads "depth" as progress sees 64 phantom iterations.

Prints the exact answer lines for one checkmated and one stalemated root, and counts.
Also runs the Rule-1 plant: a real (non-terminal) root must NOT produce `mate 0` or `cp 0` with a 1-ply PV,
so a harness that reads a terminal answer everywhere is caught.
"""
import re
import shlex
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
LABEL = sys.argv[2]


def run(fen, go):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20_EXTRA:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"{go}\n"); p.stdin.flush()
    infos, best = [], None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            infos.append(s)
        if s.startswith("bestmove"):
            best = s
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return infos, best


MATE_ROOT = "8/8/Q7/8/8/K7/8/k1Q5 b - - 0 1"          # checkmated, verified by python-chess
STALE_ROOT = None
for l in open("/agent/repos/dwqww/forge-combo29/swarm/25/job3/stale_roots.fens"):
    STALE_ROOT = l.strip()
    break

print(f"### {LABEL}  (Threads 1, Hash 16, PC20)")
for name, fen in (("checkmated root", MATE_ROOT), ("stalemated root", STALE_ROOT)):
    b = chess.Board(fen)
    print(f"--- {name}: {fen}")
    print(f"    python-chess: checkmate={b.is_checkmate()} stalemate={b.is_stalemate()} "
          f"legal_moves={b.legal_moves.count()}")
    for go in ("go depth 5", "go nodes 100", "go movetime 50"):
        infos, best = run(fen, go)
        first = infos[0] if infos else "(none)"
        last = infos[-1] if infos else "(none)"
        depths = [int(re.search(r"depth (\d+)", l).group(1)) for l in infos]
        print(f"    {go:<16} info_lines={len(infos):>3} depth {min(depths) if depths else '-'}"
              f"..{max(depths) if depths else '-'}  {best}")
        print(f"      first: {first[:100]}")
        print(f"      last : {last[:100]}")

# Rule-1 plant: a real root must NOT look terminal
print("--- PLANT: a real (non-terminal) root must not produce mate 0 / cp 0 with a 1-ply pv")
infos, best = run("rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4", "go depth 5")
last = infos[-1] if infos else ""
toks = last.split()
pvlen = len(toks[toks.index("pv") + 1:]) if "pv" in toks else 0
sc = re.search(r"score (cp|mate) (-?\d+)", last)
looks_terminal = bool(sc) and sc.group(0) == "score mate 0" or (bool(sc) and sc.group(2) == "0" and pvlen <= 1)
print(f"    score {sc.group(0) if sc else '?'}, pv {pvlen} plies -> "
      f"{'PLANT FAILED (looks terminal)' if looks_terminal else 'PASS (looks like a real search)'}")

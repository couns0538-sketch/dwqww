#!/usr/bin/env python3
"""bisect_s14.py FEN [--depth 12]

For each S14 option set ALONE on top of the engine defaults (Threads 1, Hash 16),
runs one search and records the last depth-line score. Then the full S14 set.
Prints one line per variant: variant | score | pv plies | pv ends in checkmate.
"""
import argparse
import subprocess

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
EXE = "/home/ubuntu/builds/rel/forge"


def run(fen, depth, opts):
    cmds = ["uci", "setoption name Threads value 1", "setoption name Hash value 16"]
    cmds += ["setoption name %s value %s" % (k, v) for k, v in opts]
    cmds += ["isready", "ucinewgame", "isready", "position fen " + fen, "isready",
             "go depth %d" % depth]
    proc = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    for c in cmds:
        proc.stdin.write(c + "\n")
    proc.stdin.flush()
    lines = []
    infos = []
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        line = line.rstrip("\n")
        lines.append(line)
        if line.startswith("info depth") and " pv " in line:
            infos.append(line)
        if line.startswith("bestmove"):
            break
    proc.stdin.write("quit\n")
    proc.stdin.flush()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    if not infos:
        return "NO_INFO_LINE", 0, "NO_PV"
    last = infos[-1]
    tok = last.split()
    score = "%s %s" % (tok[tok.index("score") + 1], tok[tok.index("score") + 2])
    pv = tok[tok.index("pv") + 1:]
    board = chess.Board(fen)
    legal = True
    for m in pv:
        mv = chess.Move.from_uci(m)
        if mv not in board.legal_moves:
            legal = False
            break
        board.push(mv)
    return score, len(pv), board.is_checkmate() if legal else "PV_ILLEGAL"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fen")
    ap.add_argument("--depth", type=int, default=12)
    args = ap.parse_args()
    variants = [("defaults (no S14)", [])]
    for k, v in S14:
        variants.append(("only %s=%s" % (k, v), [(k, v)]))
    variants.append(("full S14", S14))
    for name, opts in variants:
        try:
            sc, plies, mate = run(args.fen, args.depth, opts)
        except subprocess.TimeoutExpired:
            sc, plies, mate = "TIMEOUT", 0, False
        print("%-34s | %-12s | pv %2d plies | ends_in_mate=%s" % (name, sc, plies, mate),
              flush=True)


if __name__ == "__main__":
    main()

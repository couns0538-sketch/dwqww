#!/usr/bin/env python3
"""Verify 07-F3 as ONE hand-checkable case: does a real mate exist on the board the
base build declares drawn without searching?

The base build answers `8/6qk/8/8/8/1p4p1/4K3/8 b - - 100 1` with `cp 0`, 0 nodes.
This script does not take the PC build's word for it either: it asks the PC build
for its line, then REPLAYS that line on a python-chess board and asserts it ends in
checkmate. A PV that cannot be replayed to mate is not evidence of a mate.

It also checks the fifty-move legality question directly: the rule draws only when
no capture AND no pawn move has been played in the last 100 half-moves. If the side
to move has a pawn move or capture available, the counter resets and the position is
NOT a fifty-move draw -- so `cp 0` at the root is a declaration nobody measured.

Usage: verify_f3.py BASE_EXE PC_EXE OUTDIR
"""
import chess
import json
import os
import queue
import subprocess
import sys
import threading
import time

FEN = "8/6qk/8/8/8/1p4p1/4K3/8 b - - 100 1"
S14 = [
    "LmrQuietBase value 93", "LmrQuietDivisor value 205", "LmrNoisyBase value 13",
    "LmrNoisyDivisor value 333", "LmrHistoryDivisor value 5643", "NullMoveBase value 5",
    "LmpBase value 8", "HistoryPruneMultiplier value 2220",
    "HistoryBonusQuadratic value 24", "HistoryBonusLinear value 54",
    "HistoryBonusMax value 2212", "SingularDepth value 6", "IirDepth value 2",
    "NonPawnCorrection value true",
]
PC20 = S14 + ["CuckooRep value true", "HistRework value 2", "TtPruneV2 value true",
              "CorrHistV2 value true", "MateAlphaGuard value true", "OwnBook value false"]


class Reader:
    def __init__(s, st):
        s.q = queue.Queue()
        threading.Thread(target=s._pump, args=(st,), daemon=True).start()

    def _pump(s, st):
        for l in st:
            s.q.put(l)
        s.q.put(None)

    def get(s, t):
        try:
            return s.q.get(timeout=t)
        except queue.Empty:
            return None


def search(exe, opts, fen, gocmd):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    r = Reader(p.stdout)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    send("uci")
    while True:
        l = r.get(60)
        if l is None or l.strip() == "uciok":
            break
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    for o in opts:
        send("setoption name " + o)
    send("isready")
    while True:
        l = r.get(120)
        if l is None or l.strip() == "readyok":
            break
    send("position fen " + fen)
    send("isready")
    while True:
        l = r.get(120)
        if l is None or l.strip() == "readyok":
            break
    send(gocmd)
    lines = []
    while True:
        l = r.get(600)
        if l is None:
            break
        lines.append(l.rstrip("\n"))
        if l.startswith("bestmove"):
            break
    send("quit")
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    return lines


def summarize(lines):
    """Last info line with a score, plus nodes, plus bestmove -- the reported result."""
    score = None
    nodes = None
    pv = []
    best = None
    for l in lines:
        if l.startswith("info") and " score " in l:
            score = l
        if l.startswith("bestmove"):
            best = l.split()[1] if len(l.split()) > 1 else None
            if " pv " in l:
                pass
        if " nodes " in l:
            try:
                nodes = int(l.split(" nodes ")[1].split()[0])
            except (IndexError, ValueError):
                pass
    if score:
        pv = []
        if " pv " in score:
            pv = score.split(" pv ")[1].split()
    return {"last_score_line": score, "nodes": nodes, "bestmove": best, "pv": pv}


def replay(pv):
    """Replay a PV from FEN; return (delivered_mate, plies, final_fen)."""
    b = chess.Board(FEN)
    played = 0
    for tok in pv:
        try:
            mv = chess.Move.from_uci(tok)
        except ValueError:
            break
        if mv not in b.legal_moves:
            return False, played, b.fen()
        b.push(mv)
        played += 1
        if b.is_checkmate():
            return True, played, b.fen()
    return False, played, b.fen()


def main():
    base, pc, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    board = chess.Board(FEN)

    # ---- the fifty-move legality question, decided by python-chess, not the engine
    resets = []
    for mv in board.legal_moves:
        if board.is_capture(mv) or board.piece_type_at(mv.from_square) == chess.PAWN:
            resets.append(mv.uci())
    genuine_draw = board.is_fifty_moves() and not resets

    out = {"fen": FEN, "legal_moves": board.legal_moves.count(),
           "counter_resetting_moves": resets, "genuine_fifty_move_draw": genuine_draw}

    # ---- what each build reports at the owner's budget for this position
    b12 = summarize(search(base, [], FEN, "go depth 12"))
    p12 = summarize(search(pc, PC20, FEN, "go depth 12"))
    out["base_depth12"] = b12
    out["pc_PC20_depth12"] = p12

    # ---- the PC's line must replay to mate on a python-chess board
    delivered, plies, ffen = replay(p12["pv"])
    out["pc_pv"] = p12["pv"]
    out["pc_pv_delivers_mate"] = delivered
    out["pc_pv_plies"] = plies
    out["pc_pv_final_fen"] = ffen

    # ---- independent oracle: mate distance via a bounded retrograde on the same board?
    # Not attempted; instead assert python-chess agrees the final position is mate.
    out["python_chess_final_is_checkmate"] = chess.Board(ffen).is_checkmate()

    json.dump(out, open(os.path.join(outdir, "verify_f3.json"), "w"), indent=1)

    print("FEN:", FEN)
    print("legal moves:", out["legal_moves"], " counter-resetting moves:", resets)
    print("genuine fifty-move draw (python-chess):", genuine_draw)
    print()
    print("BASE   depth 12:", b12["last_score_line"])
    print("PC PC20 depth 12:", p12["last_score_line"])
    print()
    print("PC PV:", " ".join(p12["pv"]))
    print("PV replays to checkmate:", delivered, "in", plies, "plies")
    print("python-chess says final position is mate:", out["python_chess_final_is_checkmate"])
    print()
    if genuine_draw:
        print("VERDICT: position IS a genuine fifty-move draw; base's cp 0 is defensible.")
    elif delivered:
        print("VERDICT: 07-F3 CONFIRMED as ONE hand-checkable case -- base declares a draw")
        print("         without searching a position where a real, replayable mate exists")
        print("         and the counter could not have been claimed.")
    else:
        print("VERDICT: PC's line did NOT replay to mate -- 07-F3 rests on the score alone.")


if __name__ == "__main__":
    main()

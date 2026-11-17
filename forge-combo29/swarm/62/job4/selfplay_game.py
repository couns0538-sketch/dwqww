#!/usr/bin/env python3
"""selfplay_game.py -- let the ENGINE play a real game into the band.

This is the honest answer to "is this reachable in real play": rather than hand-
author a move list, take the engine's own moves. A game where the engine plays
both sides is a real game: every move is chosen by a legal-move generator and
replayed through python-chess, and the move list is emitted so it can be checked.

The setup that makes the band reachable is the one real games actually have: a
losing side that is a rook down and shuffling its king, with a winner that does
not convert. The engine at shallow depth does exactly this, which is why
engine-vs-engine games in this repository contain 798 positions at clock 98-99
(see job4/pgn_scan.log) -- shuffling into the band is COMMON. What is not common
is a forced mate being available at that moment.

So this script plays games from a *realistic* starting point (a standard opening,
played out by the engine) and asks two questions at every position from clock 93
upward:
    - does a forced mate exist (oracle)?
    - is the clock past the band edge for that mate length?

Usage: selfplay_game.py --exe /tmp/build-base/forge --games 6 --out selfplay.json
"""
import argparse
import json
import subprocess
import sys
import time

import chess

sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/job3")
from matedist import evaluate, MATE  # noqa: E402

ORACLE_PLIES = 8


def engine_move(exe, fen, movetime=60, depth=None):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         text=True, bufsize=1)
    def send(s):
        p.stdin.write(s + "\n"); p.stdin.flush()
    def until(pred, deadline):
        out = []
        while time.monotonic() < deadline:
            line = p.stdout.readline()
            if line == "":
                return out, False
            line = line.rstrip("\n")
            out.append(line)
            if pred(line):
                return out, True
        return out, False
    send("uci"); until(lambda l: l.strip() == "uciok", time.monotonic() + 10)
    send("ucinewgame"); send("isready")
    until(lambda l: l.strip() == "readyok", time.monotonic() + 10)
    send("position fen " + fen); send("isready")
    pos, _ = until(lambda l: l.strip() == "readyok", time.monotonic() + 10)
    for l in pos:
        if "invalid FEN" in l:
            p.kill()
            raise SystemExit("engine refused FEN: %s" % l)
    if depth:
        send("go depth %d" % depth)
    else:
        send("go movetime %d" % movetime)
    go, got = until(lambda l: l.startswith("bestmove"), time.monotonic() + 120)
    send("quit")
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    if not got:
        return None
    for l in go:
        if l.startswith("bestmove"):
            tok = l.split()
            if len(tok) > 1 and tok[1] not in ("(none)", "none"):
                return tok[1]
    return None


def oracle(board):
    v = evaluate(board.fen(), ORACLE_PLIES)
    if v <= -MATE + ORACLE_PLIES:
        return ("mated", MATE + v)
    if v >= MATE - ORACLE_PLIES:
        return ("mates", MATE - v)
    return ("draw", 0)


def resets(board):
    for mv in board.legal_moves:
        if board.is_capture(mv):
            return True
        pc = board.piece_at(mv.from_square)
        if pc is not None and pc.piece_type == chess.PAWN:
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--games", type=int, default=4)
    ap.add_argument("--max-plies", type=int, default=300)
    ap.add_argument("--movetime", type=int, default=40)
    ap.add_argument("--out", default="selfplay.json")
    args = ap.parse_args()

    results = []
    for g in range(args.games):
        b = chess.Board()
        moves = []
        rec = {"game": g, "band_positions": [], "mate_positions": []}
        while len(moves) < args.max_plies:
            mv_uci = engine_move(args.exe, b.fen(), movetime=args.movetime)
            if mv_uci is None:
                break
            mv = chess.Move.from_uci(mv_uci)
            if mv not in b.legal_moves:
                rec["illegal"] = mv_uci
                break
            b.push(mv)
            moves.append(mv_uci)
            if b.halfmove_clock >= 93:
                rec["band_positions"].append(b.fen())
                kind, val = oracle(b)
                if kind == "mated":
                    p = val
                    H = b.halfmove_clock
                    rec["mate_positions"].append({
                        "fen": b.fen(), "H": H, "p": p, "j0": 100 - H,
                        "in_band": H > 100 - p, "resets": resets(b),
                        "ply": len(moves)})
            if b.is_checkmate() or not any(b.legal_moves):
                break
        rec["plies"] = len(moves)
        rec["moves"] = moves
        print("game %d: %d plies, band positions=%d, mate positions=%d" % (
            g, len(moves), len(rec["band_positions"]), len(rec["mate_positions"])))
        results.append(rec)

    total_mate = sum(len(r["mate_positions"]) for r in results)
    total_in_band = sum(1 for r in results for m in r["mate_positions"] if m["in_band"])
    print("---- games                          : %d" % len(results))
    print("---- positions at clock >= 93       : %d" % sum(
        len(r["band_positions"]) for r in results))
    print("---- of those, a forced mate exists : %d" % total_mate)
    print("---- of those, in band (must miss)  : %d" % total_in_band)
    json.dump(results, open(args.out, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""swarm seat 01: does the DEAD-MATERIAL door need a mate bypass at all?

The engine's Board::is_insufficient_material() (src/board.cpp:1250) returns true when
  * there are no pawns, rooks or queens, AND
  * the minor count is <= 1, OR every bishop stands on the SAME colour square.
Those are exactly the material sets in which no mate can be constructed. If that is so, the dead-material
branch of `root_drawn` can never hide a mate, and the combined patch's immediate-mate bypass simply never
fires on that door — which is a result, not a gap.

This script tests it in two independent ways:
  A) THE RULE, re-implemented in python from the C++ above, swept over every legal position it can generate
     with that material (random placement, both colours to move), plus a legal-move search for a mating move.
     Any single position with insufficient material AND a mating move would refute the claim.
  B) THE ENGINE: for each such position, `go depth 6` must never produce a bestmove that mates. A mating
     bestmove under an insufficient-material root would be the door firing wrongly.

Usage: dead_material_door.py <base-exe> <combined-exe> <outdir>
"""
import hashlib
import json
import os
import random
import select
import subprocess
import sys
import time
from pathlib import Path

import chess

TIMEOUT = 120.0
SAMPLES = 400


class R:
    def __init__(self, fd):
        self.fd, self.buf, self.eof = fd, b"", False

    def line(self, deadline):
        while b"\n" not in self.buf:
            if self.eof:
                return None
            remain = deadline - time.monotonic()
            if remain <= 0:
                return None
            r, _, _ = select.select([self.fd], [], [], remain)
            if not r:
                return None
            c = os.read(self.fd, 65536)
            if not c:
                self.eof = True
                return None
            self.buf += c
        l, _, self.buf = self.buf.partition(b"\n")
        return l.decode("utf-8", "replace")


def engine_insufficient(board):
    """python re-implementation of Board::is_insufficient_material()."""
    prq = board.pieces(chess.PAWN, True) | board.pieces(chess.PAWN, False) \
        | board.pieces(chess.ROOK, True) | board.pieces(chess.ROOK, False) \
        | board.pieces(chess.QUEEN, True) | board.pieces(chess.QUEEN, False)
    if prq:
        return False
    knights = board.pieces(chess.KNIGHT, True) | board.pieces(chess.KNIGHT, False)
    bishops = board.pieces(chess.BISHOP, True) | board.pieces(chess.BISHOP, False)
    minor = len(knights) + len(bishops)
    if minor <= 1:
        return True
    if knights:
        return False
    dark = bishops & chess.BB_DARK_SQUARES
    light = bishops & chess.BB_LIGHT_SQUARES
    return not dark or not light


def mating_moves(board):
    out = []
    for m in board.legal_moves:
        board.push(m)
        if board.is_checkmate():
            out.append(m.uci())
        board.pop()
    return out


def run(exe, fen, go="go depth 6"):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())
    buf = []

    def until(prefix):
        d = time.monotonic() + TIMEOUT
        while True:
            l = rd.line(d)
            if l is None:
                return None
            buf.append(l)
            if l.startswith(prefix):
                return l

    def send(s):
        p.stdin.write((s + "\n").encode())
        p.stdin.flush()

    send("position fen " + fen)
    send("isready")
    if until("readyok") is None:
        p.kill()
        return {"error": "no readyok"}
    send(go)
    bml = until("bestmove")
    time.sleep(0.05)
    send("quit")
    try:
        p.wait(timeout=40)
    except Exception:
        p.kill()
    dl = [l for l in buf if l.startswith("info depth")]
    score = nodes = ""
    if dl:
        f = dl[-1].split()
        if "score" in f:
            i = f.index("score")
            score = " ".join(f[i + 1:i + 3])
        if "nodes" in f:
            nodes = f[f.index("nodes") + 1]
    return {"score": score, "nodes": nodes, "bestmove": bml.split()[1] if bml else None}


def gen_positions(rng, n):
    """Random K+minor / K+bishops-same-colour positions, both colours to move."""
    out = []
    tries = 0
    while len(out) < n and tries < n * 60:
        tries += 1
        kinds = [
            # (pieces) K+minor vs K
            lambda b: chess.Board(None),
        ]
        b = chess.Board(None)
        squares = rng.sample(range(64), 5)
        wk, bk = squares[0], squares[1]
        b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        shape = rng.choice(["KN", "KB", "KNN", "KBB", "KB_same", "K_only"])
        if shape in ("KN", "KB"):
            pt = chess.KNIGHT if shape == "KN" else chess.BISHOP
            b.set_piece_at(squares[2], chess.Piece(pt, chess.WHITE))
        elif shape == "KNN":
            b.set_piece_at(squares[2], chess.Piece(chess.KNIGHT, chess.WHITE))
            b.set_piece_at(squares[3], chess.Piece(chess.KNIGHT, chess.WHITE))
        elif shape in ("KBB", "KB_same"):
            dark = [s for s in range(64) if chess.BB_DARK_SQUARES & (1 << s)]
            light = [s for s in range(64) if chess.BB_LIGHT_SQUARES & (1 << s)]
            if shape == "KB_same":
                pool = rng.choice([dark, light])
                s1, s2 = rng.sample(pool, 2)
            else:
                s1 = rng.choice(dark)
                s2 = rng.choice(light)
            b.set_piece_at(s1, chess.Piece(chess.BISHOP, chess.WHITE))
            b.set_piece_at(s2, chess.Piece(chess.BISHOP, chess.WHITE))
        b.turn = rng.choice([chess.WHITE, chess.BLACK])
        if not b.is_valid():
            continue
        out.append((shape, b.fen(), engine_insufficient(b)))
    return out


def main():
    base, combined, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(101)
    pos = gen_positions(rng, SAMPLES)
    insuff = [p for p in pos if p[2]]
    refutations = []
    for shape, fen, _ in insuff:
        b = chess.Board(fen)
        mm = mating_moves(b)
        if mm:
            refutations.append((shape, fen, mm))

    lines = ["does the DEAD-MATERIAL door need a mate bypass?",
             "rule re-implemented from Board::is_insufficient_material (src/board.cpp:1250)",
             "base     %s sha256 %s" % (base, hashlib.sha256(Path(base).read_bytes()).hexdigest()),
             "combined %s sha256 %s" % (combined, hashlib.sha256(Path(combined).read_bytes()).hexdigest()),
             "go: 'go depth 6'; one fresh process per position; no setoption sent",
             ""]
    lines.append("A) RULE SWEEP: %d positions generated, %d have insufficient material per the engine's rule"
                 % (len(pos), len(insuff)))
    lines.append("   positions with insufficient material AND a legal mating move: %d" % len(refutations))
    for shape, fen, mm in refutations[:10]:
        lines.append("   COUNTEREXAMPLE %s %s mating=%s" % (shape, fen, mm))
    if not refutations:
        lines.append("   -> no counterexample: on this material the rule never hides a mate, so the")
        lines.append("      dead-material branch of root_drawn cannot suppress one.")

    # B) engine check on a subset
    sub = insuff[:40]
    disagree = []
    for shape, fen, _ in sub:
        g = run(combined, fen)
        b = chess.Board(fen)
        if g.get("bestmove") and g["bestmove"] not in ("0000",):
            mv = chess.Move.from_uci(g["bestmove"])
            b.push(mv)
            if b.is_checkmate():
                disagree.append((fen, g["bestmove"]))
            b.pop()
    lines.append("")
    lines.append("B) ENGINE CHECK on the combined build, %d insufficient-material positions: %d bestmoves that"
                 % (len(sub), len(disagree)))
    lines.append("   mate (should be 0, since no mate exists):")
    for d in disagree:
        lines.append("   %s" % (d,))
    (out / "dead_material_door.txt").write_text("\n".join(lines) + "\n")
    (out / "dead_material_door.json").write_text(json.dumps(
        {"generated": len(pos), "insufficient": len(insuff), "refutations": refutations,
         "engine_checked": len(sub), "engine_mates": disagree}, indent=1))
    print("\n".join(lines))


if __name__ == "__main__":
    main()

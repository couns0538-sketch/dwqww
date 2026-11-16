#!/usr/bin/env python3
"""check_s01f2.py -- seat 10's OWN harness for seat 01's finding S-F2.

It does three things with ONE FEN, in this order, and writes every raw line:
  A. sends `position fen <FEN>`, `isready`, `go perft 2`, waits for bestmove, and records the
     answer lines and the perft total;
  B. asks python-chess whether the FEN parses, what its board.status() is, and how many legal
     moves the side to move has (0 if the status marks the position invalid);
  C. enumerates the attackers of the side-to-move's king with ITS OWN bitboard-free scan of the
     board (not python-chess's attackers()), so the double check is established independently.

Usage: check_s01f2.py EXE OUTFILE
"""
import subprocess
import sys

import chess

EXE = sys.argv[1]
OUTF = sys.argv[2]
FEN = "3k4/3P1q2/5K2/8/8/5r2/7p/7R w - - 0 1"


def talk(lines):
    p = subprocess.run([EXE], input="\n".join(lines) + "\n", capture_output=True,
                       text=True, timeout=120)
    return p.stdout, p.stderr, p.returncode


# ---- A: the engine
cmds = ["uci", "isready", "position fen " + FEN, "isready", "go perft 2", "quit"]
out, err, rc = talk(cmds)
perft_total = None
for line in out.splitlines():
    s = line.strip()
    if s.startswith("nodes "):
        perft_total = int(s.split()[1])
refused = [l for l in out.splitlines() if "invalid fen" in l.lower()]
accepted = not refused

# ---- B: python-chess
b = None
py_parses = True
py_err = ""
try:
    b = chess.Board(FEN)
except ValueError as e:
    py_parses = False
    py_err = str(e)
py_status = b.status() if b else None
py_legal = b.legal_moves.count() if b else None

# python-chess's perft ignoring validity: we must clear the status flags to walk the tree
py_perft2 = None
py_forced_note = ""
if b is not None:
    c = chess.Board(FEN)
    # python-chess refuses to generate moves when the status is invalid; clear it by hand.
    c._status = chess.STATUS_VALID
    try:
        py_perft2 = c.perft(2)
    except Exception as e:      # noqa: BLE001 - the point is to record whatever happens
        py_forced_note = "python-chess perft raised: %s" % e

# ---- C: my own attacker enumeration (no python-chess helpers)
ATT = {}   # (attacker type) -> function(board, sq, from_sq) -> bool
KNIGHT = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
KING = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
BISHOP = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
ROOK = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def name(sq):
    return chess.square_name(sq)


def attacks_king_sq(c, king, white_to_move):
    """every square holding an enemy piece that attacks `king`, by a plain scan"""
    out = []
    f0, r0 = chess.square_file(king), chess.square_rank(king)
    enemy_is_black = white_to_move
    for df, dr in KNIGHT:
        f, r = f0 + df, r0 + dr
        if 0 <= f < 8 and 0 <= r < 8:
            sq = chess.square(f, r)
            p = c.piece_at(sq)
            if p and p.piece_type == chess.KNIGHT and p.color == (not white_to_move):
                out.append((name(sq), "N"))
    for df, dr in KING:
        f, r = f0 + df, r0 + dr
        if 0 <= f < 8 and 0 <= r < 8:
            sq = chess.square(f, r)
            p = c.piece_at(sq)
            if p and p.piece_type == chess.KING and p.color == (not white_to_move):
                out.append((name(sq), "K"))
    for dirs, typ1, typ2 in ((ROOK, chess.ROOK, chess.QUEEN), (BISHOP, chess.BISHOP, chess.QUEEN)):
        for df, dr in dirs:
            f, r = f0 + df, r0 + dr
            while 0 <= f < 8 and 0 <= r < 8:
                sq = chess.square(f, r)
                p = c.piece_at(sq)
                if p:
                    if p.color == (not white_to_move) and p.piece_type in (typ1, typ2):
                        out.append((name(sq), "R" if p.piece_type == chess.ROOK else
                                    "B" if p.piece_type == chess.BISHOP else "Q"))
                    break
                f, r = f + df, r + dr
    del enemy_is_black
    return out


king_sq = b.king(chess.WHITE) if b else None
my_attackers = attacks_king_sq(b, king_sq, True) if b else []
py_attackers = sorted(name(s) for s in b.attackers(chess.BLACK, king_sq)) if b else []

L = []
L.append("FEN under test: %s" % FEN)
L.append("")
L.append("---- A. the engine ----")
L.append("commands sent: %s" % " | ".join(cmds))
L.append("accepted (no 'invalid FEN' line): %s" % accepted)
L.append("refusal lines: %s" % (refused if refused else "none"))
L.append("go perft 2 total: %s" % perft_total)
L.append("exit code: %s" % rc)
L.append("stderr: %r" % err[:200])
L.append("full engine output:")
L.extend("  " + x for x in out.splitlines())
L.append("")
L.append("---- B. python-chess %s ----" % chess.__version__)
L.append("parses: %s %s" % (py_parses, py_err))
L.append("board.status(): %s (STATUS_IMPOSSIBLE_CHECK=%s, STATUS_VALID=%s)"
         % (py_status, chess.STATUS_IMPOSSIBLE_CHECK, chess.STATUS_VALID))
L.append("legal moves for the side to move, python-chess as-is: %s" % py_legal)
L.append("perft 2 with the status flag forced to VALID (i.e. python-chess IGNORING its own "
         "validity check): %s %s" % (py_perft2, py_forced_note))
L.append("")
L.append("---- C. the attackers of the white king, two independent ways ----")
L.append("white king on: %s" % (name(king_sq) if king_sq is not None else "none"))
L.append("my own scan finds attackers: %s" % my_attackers)
L.append("python-chess board.attackers(BLACK, king): %s" % py_attackers)
L.append("two independent enumerations agree: %s"
         % (sorted(x[0] for x in my_attackers) == py_attackers))
L.append("")
L.append("---- VERDICT INPUTS ----")
L.append("P1 engine accepted the FEN: %s" % accepted)
L.append("P2 engine perft 2 == 64: %s" % (perft_total == 64))
L.append("P3 python-chess refuses (status has IMPOSSIBLE_CHECK): %s"
         % (py_status is not None and bool(py_status & chess.STATUS_IMPOSSIBLE_CHECK)))
L.append("P4 a like-for-like comparison needs python-chess validity ignored: %s"
         % (py_legal == 0 and py_perft2 == 64))
L.append("P5 number of attackers my scan finds: %d -> %s"
         % (len(my_attackers), my_attackers))

with open(OUTF, "w") as f:
    f.write("\n".join(L) + "\n")
print("\n".join(L))

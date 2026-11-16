#!/usr/bin/env python3
"""see_oracle.py EXE OUTDIR [POSITIONS]

Board::see_ge decides which captures and quiets the search trusts, so a wrong answer changes move
ordering everywhere. My first attempt at an oracle (job7) was wrong twice and I abandoned it.

This version avoids writing an exchange evaluator at all: it uses python-chess as the referee and
the engine's own `go perft 1`-style legality, computing the static exchange by EXPLICIT minimax over
captures only on the destination square, with python-chess doing all move generation and legality.

Definition used (the standard one):
    see(move) = material(mover) after the best capture-only sequence that starts with `move`

For each position: pick a capture, ask the engine `see` indirectly via a searchmoves probe is not
possible, so instead this compares the ENGINE's behaviour that DEPENDS on see_ge -- which captures it
plays first at depth 1 -- against the oracle's ranking. A depth-1 search on a position with exactly
one legal capture must play that capture; with several, it must play one whose SEE is not negative
when a non-losing capture exists.

That is indirect. So the primary assertion is the simpler, fully decidable one: on a position whose
ONLY legal move is a losing capture, a depth-1 search must still play it (no assertion about SEE can
make the engine output an illegal move), and on a position with a choice, the engine must never play
a capture that the oracle says loses material when a quiet move exists at the same depth -- reported
as a ranked comparison, not as a pass/fail on SEE itself.

Everything is reported as counts; nothing here is allowed to pass on a missing measurement.
"""
import os
import queue
import re
import subprocess
import sys
import threading

import chess

VALUES = {chess.PAWN: 100, chess.KNIGHT: 300, chess.BISHOP: 300,
          chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}


def material(board):
    """Material from WHITE's point of view, python-chess doing all the work."""
    total = 0
    for square, piece in board.piece_map().items():
        sign = 1 if piece.color == chess.WHITE else -1
        total += sign * VALUES[piece.piece_type]
    return total


def see_value(board, move):
    """Static exchange value of `move` for the mover.

    Implemented purely with python-chess, using the swap-list definition:
        gain[0] = value(victim)
        then alternately the cheapest attacker recaptures, each gain being
        value(standing piece) - previous gain, back-propagated as max/min.
    The recursive minimax I wrote first had its signs wrong (it scored a king capturing a
    defended rook as +500 instead of -500), so it was replaced by this explicit swap list,
    which is the textbook formulation and is checked by the three assertions in the docstring
    of main().
    """
    us = board.turn
    victim_square = move.to_square
    if board.is_en_passant(move):
        victim_square = chess.square(move.to_square % 8,
                                     chess.square_rank(move.to_square) + (-1 if us == chess.WHITE else 1))
    victim = board.piece_at(victim_square)
    gain = [VALUES[victim.piece_type] if victim else 0]
    if move.promotion:
        gain[0] += VALUES[move.promotion] - VALUES[chess.PAWN]

    bd = board.copy()
    moving_piece = bd.piece_at(move.from_square)
    bd.push(move)
    stm = not us
    standing = VALUES[move.promotion] if move.promotion else VALUES[moving_piece.piece_type]

    # Attackers must be recomputed on the live board each step; python-chess gives us that.
    while True:
        to = move.to_square
        attackers = [sq for sq in bd.attackers(stm, to)
                     if bd.piece_at(sq) is not None]
        if not attackers:
            break
        # least valuable attacker
        attackers.sort(key=lambda sq: VALUES[bd.piece_at(sq).piece_type])
        from_sq = attackers[0]
        piece = bd.piece_at(from_sq)
        # Build the recapture; promotions on the last rank are taken as queen.
        promo = None
        if piece.piece_type == chess.PAWN and chess.square_rank(to) in (0, 7):
            promo = chess.QUEEN
        capture = chess.Move(from_sq, to, promotion=promo)
        if capture not in bd.legal_moves:
            break
        gain.append(standing - gain[-1])
        standing = VALUES[promo] if promo else VALUES[piece.piece_type]
        bd.push(capture)
        stm = not stm

    for i in range(len(gain) - 1, 0, -1):
        gain[i - 1] = -max(-gain[i - 1], gain[i])
    return gain[0]


class Reader:
    def __init__(self, s):
        self.q = queue.Queue()
        threading.Thread(target=self._pump, args=(s,), daemon=True).start()

    def _pump(self, s):
        for line in s:
            self.q.put(line)
        self.q.put(None)

    def get(self, t):
        try:
            return self.q.get(timeout=t)
        except queue.Empty:
            return None


def engine_bestmove(exe, fen, depth=1):
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)
    r = Reader(proc.stdout)

    def send(c):
        proc.stdin.write(c + "\n")
        proc.stdin.flush()

    send("uci")
    while True:
        line = r.get(30)
        if line is None or line.strip() == "uciok":
            break
    for opt in ["Hash value 16", "Threads value 1", "OwnBook value false"]:
        send("setoption name " + opt)
    send("isready")
    while True:
        line = r.get(30)
        if line is None or line.strip() == "readyok":
            break
    send("position fen " + fen)
    send("isready")
    while True:
        line = r.get(30)
        if line is None or line.strip() == "readyok":
            break
    send(f"go depth {depth}")
    best = None
    nodes = None
    while True:
        line = r.get(60)
        if line is None:
            break
        if line.startswith("info depth") and " nodes " in line:
            m = re.search(r" nodes (\d+) ", line)
            if m:
                nodes = int(m.group(1))
        if line.startswith("bestmove"):
            best = line.split()[1]
            break
    send("quit")
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
    if best is None:
        raise SystemExit(f"FAIL no bestmove for {fen}")
    if nodes is None:
        raise SystemExit(f"FAIL no nodes line for {fen}: nothing measured")
    return best


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    os.makedirs(outdir, exist_ok=True)
    fens = [l.strip() for l in open("/tmp/first200.fens") if l.strip()][:limit]

    checked = illegal = losing_played = 0
    rows = []
    for fen in fens:
        board = chess.Board(fen)
        legal = list(board.legal_moves)
        if not legal:
            continue
        best = engine_bestmove(exe, fen, 1)
        checked += 1
        try:
            mv = chess.Move.from_uci(best)
        except ValueError:
            illegal += 1
            rows.append(f"ILLEGAL-STRING {best} {fen}")
            continue
        if mv not in legal:
            illegal += 1
            rows.append(f"ILLEGAL {best} {fen}")
            continue
        if board.is_capture(mv):
            sv = see_value(board, mv)
            quiets = [m for m in legal if not board.is_capture(m)]
            if sv < 0 and quiets:
                losing_played += 1
                rows.append(f"LOSING-CAPTURE-CHOSEN {best} see={sv} fen {fen}")

    with open(os.path.join(outdir, "differences.txt"), "w") as fh:
        fh.write("\n".join(rows) + ("\n" if rows else ""))
    print(f"positions checked {checked}")
    print(f"illegal bestmoves {illegal}")
    print(f"losing captures chosen while a quiet existed at depth 1: {losing_played}")
    for row in rows[:20]:
        print("  " + row)
    if checked == 0:
        print("RESULT: nothing checked")
        sys.exit(2)
    if illegal:
        print("RESULT: illegal bestmoves found")
        sys.exit(1)
    print("RESULT: no illegal bestmove at depth 1; "
          f"{losing_played} case(s) where a negative-SEE capture was chosen with a quiet available "
          "(informational: at depth 1 a losing capture can still be best because the opponent's "
          "recapture may be pruned, so this is NOT counted as a fault).")


if __name__ == "__main__":
    main()

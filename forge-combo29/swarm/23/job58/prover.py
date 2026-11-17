#!/usr/bin/env python3
"""prover.py : a DTM oracle that earned the right to be used — depth-bounded, controls first.

23-F49 recorded a prover of mine that failed its own control, and 23-F119 records that abandoning it became the reason a
mate-distance claim went unchecked. This replaces it.

DESIGN, and why two earlier attempts failed:
  - attempt 1 (unbounded minimax) recursed to Python's limit: reversible moves made the tree effectively infinite.
  - attempt 2 (same recursion + a "seen on this path" guard) STILL recursed, because the guard key included the move
    counters, so a position re-reached with a different halfmove clock looked like a new position.
  - this version is DEPTH-BOUNDED by construction: `can_mate_in(board, n)` answers "can the side to move force mate in
    at most n plies", and DTM is the smallest odd n that succeeds. A bounded search cannot run away, and it matches
    what seat 27 did (exhaustive forced-mate search).

Controls run FIRST; one failure aborts before any result is printed. C5 cross-checks seat 27's independently measured
true DTM for the W2 board (mate 6 = 11 plies).
"""
import sys
import chess

INF = 10 ** 6
memo = {}


def can_mate_in(b, n, path):
    """True iff the side to move can force checkmate within n plies (defender delays optimally)."""
    if n <= 0:
        return False
    k = (b.board_fen(), b.turn, b.castling_rights, b.ep_square)
    if k in path:
        return False
    mk = (k, n)
    if mk in memo:
        return memo[mk]
    for m in b.legal_moves:
        b.push(m)
        try:
            if b.is_checkmate():
                memo[mk] = True
                return True
            replies = list(b.legal_moves)
            if not replies:
                continue  # stalemate: not a mate
            all_replies_mated = True
            for r in replies:
                b.push(r)
                try:
                    sub = can_mate_in(b, n - 2, path | {k})
                finally:
                    b.pop()
                if not sub:
                    all_replies_mated = False
                    break
            if all_replies_mated:
                memo[mk] = True
                return True
        finally:
            b.pop()
    memo[mk] = False
    return False


def dtm_for_mover(fen, max_plies=31):
    """Smallest odd ply count in which the side to move forces mate, or INF."""
    b = chess.Board(fen)
    for n in range(1, max_plies + 1, 2):
        if can_mate_in(b, n, frozenset()):
            return n
    return INF


def fmt(n):
    return "INF (no forced mate)" if n >= INF else "%d plies (mate in %d moves)" % (n, (n + 1) // 2)


print("== CONTROLS — a single failure aborts before any result is printed ==")
checks = []

b = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w")
checks.append(("C1 fool's mate already delivered -> is_checkmate", b.is_checkmate(), True))

b = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b")
checks.append(("C2 black mates in 1 ply -> dtm_for_mover == 1", dtm_for_mover(b.fen()), 1))

b = chess.Board("1K6/8/8/3R4/8/8/8/k7 w - - 0 1")
kr = dtm_for_mover(b.fen())
checks.append(("C3 KRvK win -> finite DTM", kr < INF, True))

b = chess.Board("8/8/8/8/8/8/8/K6k w - - 0 1")
checks.append(("C4 bare kings -> no forced mate", dtm_for_mover(b.fen()) >= INF, True))

W2 = "8/5K2/7Q/4k3/8/8/8/8 w - - 0 1"
w2 = dtm_for_mover(W2)
checks.append(("C5 W2 K+Q v K -> finite DTM", w2 < INF, True))

ok = True
for label, got, want in checks:
    good = (got == want)
    ok = ok and good
    print("  %-54s got %-22s want %-22s %s" % (label, str(got), str(want), "PASS" if good else "**FAIL**"))
print()
if not ok:
    print("HARD FAILURE: the prover disagrees with a known answer. NO DTM RESULT MAY BE USED.")
    sys.exit(2)

print("== the number this exists to provide ==")
print("  W2 `%s`" % W2)
print("  this prover      : %s" % fmt(w2))
print("  seat 27 reported : 11 plies (mate 6)")
agree = (w2 == 11)
print("  agree            : %s" % ("YES" if agree else "**NO**"))
print()
print("  KRvK `1K6/8/8/3R4/8/8/8/k7 w` DTM = %s" % fmt(kr))
print()
if not agree:
    print("HARD FAILURE: this prover does not reproduce seat 27's independently measured DTM, so it may not be used")
    print("for any mate-distance claim until the disagreement is explained.")
    sys.exit(3)
print("VERDICT: controls PASS and the W2 cross-check agrees with an independent implementation.")
print("This prover is now usable, and its dependants are no longer blocked.")

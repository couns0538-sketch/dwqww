#!/usr/bin/env python3
"""matesolve3.py — independent brute-force mate solver, unambiguous turn accounting.

Definitions, written out because two of my earlier versions disagreed on one board and one of them had to be wrong:

  A(n) = attacker TO MOVE can force mate within n of ITS OWN moves, against every defence.
         A(n): for each attacker move m: push m.
                 if checkmate            -> True   (this move was the n-th and it mates)
                 if game over (not mate) -> this move fails, try the next
                 if D(n-1)               -> True   (that move used one, n-1 remain)
  D(m) = defender TO MOVE, attacker has m moves remaining; True only if EVERY defence leads to A(m).
         D(m): for each defence: push; if not A(m) -> False.  (m=0 makes A(0)=False, so D(0)=False unless
               the defender is already mated, which the caller checks first.)

Smallest forced mate = the least n with A(n) True. After a specific first move: 1 if it mates immediately,
otherwise 1 + the least m with D(m) True.

  matesolve3.py selfcheck
  matesolve3.py solve FEN MAXN            smallest forced mate for the side to move
  matesolve3.py after FEN MOVE MAXN       smallest forced mate after that specific first move
  matesolve3.py checkpv FEN PV...         is this PV a forced mate of its own length? (defender best play)
"""
import sys

import chess

sys.setrecursionlimit(100000)


def A(board, n, memo):
    if n <= 0:
        return False
    key = (board.board_fen(), board.turn, board.castling_rights, board.ep_square, n)
    if key in memo:
        return memo[key]
    res = False
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop(); res = True; break
        if board.is_game_over(claim_draw=False):
            board.pop(); continue
        hit = D(board, n - 1, memo)
        board.pop()
        if hit:
            res = True; break
    memo[key] = res
    return res


def D(board, m, memo):
    if board.is_checkmate():
        return True
    if board.is_game_over(claim_draw=False):
        return False
    key = (board.board_fen(), board.turn, board.castling_rights, board.ep_square, -m)
    if key in memo:
        return memo[key]
    res = True
    for mv in board.legal_moves:
        board.push(mv)
        ok = A(board, m, memo)
        board.pop()
        if not ok:
            res = False
            break
    memo[key] = res
    return res


def solve(fen, maxn):
    b = chess.Board(fen)
    for n in range(1, maxn + 1):
        memo = {}
        if A(b, n, memo):
            return n
    return None


def solve_after(fen, move, maxn):
    b = chess.Board(fen)
    mv = chess.Move.from_uci(move)
    assert mv in b.legal_moves, f"{move} illegal in {fen}"
    b.push(mv)
    if b.is_checkmate():
        return 1
    for m in range(1, maxn):
        memo = {}
        if D(b, m, memo):
            return m + 1
    return None


def checkpv(fen, pv):
    """Is this PV a forced mate of its own length?

    The ATTACKER is the side DELIVERING mate, which is not always the side to move: a NEGATIVE mate score means the
    side to move is the one being mated. My first version assumed the side to move was the attacker, which made every
    negative-mate PV report nonsense (it asked the losing side to force a mate). The mate VALUE must be passed in.
    """
    raise SystemExit("use checkpv_value(fen, value, pv): the attacker depends on the SIGN of the mate score")


def checkpv_value(fen, value, pv):
    root = chess.Board(fen)
    # mate value is from the side-to-move's perspective: negative => side to move is being mated
    attacker = root.turn if value > 0 else (not root.turn)
    b = chess.Board(fen)
    forced = True
    print(f"  attacker: {'white' if attacker else 'black'}; claimed mate {value} "
          f"(side to move {'white' if root.turn else 'black'})")
    for i, u in enumerate(pv):
        mv = chess.Move.from_uci(u)
        if mv not in b.legal_moves:
            print(f"  ply {i+1} {u}: ILLEGAL")
            return False
        if b.turn != attacker:
            remaining = (len(pv) - (i + 1) + 1) // 2
            memo = {}
            bad = []
            for a in list(b.legal_moves):
                b.push(a)
                ok = A(b, remaining, memo)
                b.pop()
                if not ok:
                    bad.append(a.uci())
            note = "every defence loses" if not bad else f"{len(bad)} defence(s) hold out: {bad[:6]}"
            print(f"  ply {i+1} {u} (defence): {note}")
            if bad:
                forced = False
        b.push(mv)
    print(f"  ends in checkmate: {b.is_checkmate()}")
    ok = forced and b.is_checkmate()
    print(f"  FORCED MATE OF THIS LENGTH: {'YES' if ok else 'NO'}")
    return ok


def selfcheck():
    cases = [
        ("8/8/8/4k3/8/2K5/5Q2/8 w - - 0 1", 7, "KQ vs K; the engine reported mate 7 at depth 16"),
        ("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", 1, "Ra8# is mate in one"),
        ("7k/5K2/6Q1/8/8/8/8/8 w - - 0 1", 1, "mate in one"),
        ("8/8/8/8/8/8/8/K6k w - - 0 1", None, "bare kings"),
        ("6k1/5ppp/8/8/8/8/5PPP/1Q4K1 w - - 0 1", 1, "Qb8# is also mate in one (my third wrong guess in this file)"),
    ]
    ok = True
    for fen, expect, label in cases:
        got = solve(fen, (expect or 3) + 1)
        verdict = "PASS" if got == expect else "FAIL"
        if got != expect:
            ok = False
        print(f"{verdict}: {label}: got {got}, expected {expect}  [{fen}]")
    # consistency: solve() must equal solve_after() over every legal first move
    fen = "6k1/5ppp/8/8/8/8/5PPP/1R4K1 w - - 0 1"
    b = chess.Board(fen)
    n = solve(fen, 5)
    bests = []
    for mv in b.legal_moves:
        k = solve_after(fen, mv.uci(), 5)
        if k is not None and k == n:
            bests.append(mv.uci())
    print(f"CONSISTENCY: solve={n}; moves achieving it: {bests}")
    if not bests and n is not None:
        ok = False
        print("FAIL: solve() found a mate but no first move reproduces it")
    print("ALL SELFCHECKS PASS" if ok else "SELFCHECK FAILURES ABOVE")


if __name__ == "__main__":
    if sys.argv[1] == "selfcheck":
        selfcheck()
    elif sys.argv[1] == "solve":
        print(f"smallest forced mate: {solve(sys.argv[2], int(sys.argv[3]))}")
    elif sys.argv[1] == "after":
        print(f"smallest forced mate after {sys.argv[3]}: {solve_after(sys.argv[2], sys.argv[3], int(sys.argv[4]))}")
    elif sys.argv[1] == "checkpv":
        print("usage: checkpv FEN MATEVALUE PV...   (MATEVALUE from the side to move, e.g. -5)")
        checkpv_value(sys.argv[2], int(sys.argv[3]), sys.argv[4:])

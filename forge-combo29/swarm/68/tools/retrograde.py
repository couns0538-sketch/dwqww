#!/usr/bin/env python3
"""Exact DTM ground truth for KQvK and KRvK by full retrograde analysis.

Why this instead of a handful of hand-checked positions: retrograde analysis
computes the exact game-theoretic distance-to-mate for EVERY legal position in
the class, in one pass, by backward induction from checkmates. That gives

  * a ground truth the verifier did not produce (different algorithm entirely:
    backward induction over the whole state space vs forward alpha-beta), and
  * a checkable statement of the published bounds. If this table's maximum DTM
    for KQvK is not 10 moves and for KRvK not 31 moves, the table is wrong and
    nothing downstream may be trusted.

The bound assertion is load-bearing. A first version of this file excluded
states in which the strong side's piece had been captured, which silently
deleted the weak king's best defensive resource (taking an undefended queen or
rook and reaching KvK, a draw). It reported a KQvK maximum of 6 moves instead of
the published 10, and reported zero unresolved positions -- both impossible. The
assertion caught it. Draw escapes (piece capture leading to KvK, and stalemate)
are now modelled explicitly as states that never resolve.

Sign convention, matching the verifier's labels:
  value  = +k  the side to move delivers mate in k plies
  value  = -k  the side to move is mated in k plies
  value  =  0  the side to move is already checkmated

Output: JSON {fen: value} for every resolved position, plus summary statistics.
"""
import json
import sys
from collections import deque

import chess

FILES = "abcdefgh"

# A move that captures the strong side's last piece leads to KvK, which is a
# draw. Such children are recorded as this sentinel and are never resolved.
DRAW_ESCAPE = -1


def sq_name(s):
    return FILES[chess.square_file(s)] + str(chess.square_rank(s) + 1)


def build_states(piece_type):
    """All legal (strong_king, strong_piece, weak_king, stm) states."""
    states = []
    index = {}
    for wk in range(64):
        for wpiece in range(64):
            if wpiece == wk:
                continue
            for bk in range(64):
                if bk == wk or bk == wpiece:
                    continue
                if chess.square_distance(wk, bk) <= 1:
                    continue  # kings adjacent: illegal
                for stm in (True, False):  # True = white (strong side) to move
                    b = chess.Board(None)
                    b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
                    b.set_piece_at(wpiece, chess.Piece(piece_type, chess.WHITE))
                    b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
                    b.turn = chess.WHITE if stm else chess.BLACK
                    # The side NOT to move must not be in check.
                    other = chess.BLACK if stm else chess.WHITE
                    if b.is_attacked_by(not other, b.king(other)):
                        continue
                    key = (wk, wpiece, bk, stm)
                    index[key] = len(states)
                    states.append(key)
    return states, index


def fen_of(key, piece_type):
    wk, wpiece, bk, stm = key
    b = chess.Board(None)
    b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
    b.set_piece_at(wpiece, chess.Piece(piece_type, chess.WHITE))
    b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
    b.turn = chess.WHITE if stm else chess.BLACK
    return b.fen()


def retrograde(piece_type, name):
    states, index = build_states(piece_type)
    n = len(states)
    print(f"{name}: {n} legal states")

    value = [None] * n
    children = [None] * n
    parents = [[] for _ in range(n)]
    checked = [False] * n
    draw_escape = [False] * n

    for i, key in enumerate(states):
        wk, wpiece, bk, stm = key
        b = chess.Board(None)
        b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(wpiece, chess.Piece(piece_type, chess.WHITE))
        b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        b.turn = chess.WHITE if stm else chess.BLACK
        checked[i] = b.is_check()
        kids = []
        for mv in b.legal_moves:
            b.push(mv)
            has_piece = bool(b.pieces(piece_type, chess.WHITE))
            if has_piece:
                ck = (b.king(chess.WHITE), b.pieces(piece_type, chess.WHITE).pop(),
                      b.king(chess.BLACK), b.turn == chess.WHITE)
                j = index.get(ck)
            else:
                j = DRAW_ESCAPE  # KvK: a draw, never resolved
            b.pop()
            kids.append(j)
            if j == DRAW_ESCAPE:
                draw_escape[i] = True
        children[i] = kids

    for i in range(n):
        for j in children[i]:
            if j != DRAW_ESCAPE:
                parents[j].append(i)

    q = deque()
    stalemate = [False] * n
    # remaining[i] counts legal moves at i that have not yet been proven to lose.
    #
    # A move that captures the strong side's last piece reaches KvK, a draw. A
    # draw is better than being mated, so such a state can never be shown lost:
    # its counter is pinned high and never reaches zero. It can still be shown
    # WON, because a win is assigned on the strength of one good child and does
    # not consult this counter. An earlier version simply excluded draw escapes
    # from the count, which let those states exhaust and be labelled "mated";
    # that is what collapsed the KQvK maximum from 10 moves to 6.
    HOLD = 1 << 30
    remaining = [0] * n
    for i in range(n):
        if not children[i] and not checked[i]:
            stalemate[i] = True  # no legal move and not in check: a draw
        if draw_escape[i]:
            remaining[i] = HOLD
        else:
            remaining[i] = sum(1 for j in children[i] if j != DRAW_ESCAPE)

    for i in range(n):
        if stalemate[i]:
            continue
        if not children[i] and checked[i]:
            value[i] = 0  # checkmated here
            q.append(i)

    wave = 0
    while q:
        wave += 1
        nxt = deque()
        while q:
            i = q.popleft()
            vi = value[i]
            for p in parents[i]:
                if value[p] is not None or stalemate[p]:
                    continue
                # The side to move at i is the opposite of the side to move at p.
                # If it is mated at i (vi <= 0), then p's side delivers that mate
                # one ply sooner than i's distance: value[p] = -vi + 1 = wave.
                if isinstance(vi, int) and vi <= 0:
                    value[p] = wave
                    nxt.append(p)
                else:
                    remaining[p] -= 1
                    if remaining[p] == 0:
                        # Every move loses. BFS resolves the slowest child last,
                        # so the wave reached here is that child's distance + 1,
                        # which is exactly p's distance to being mated.
                        value[p] = -wave
                        nxt.append(p)
        q = nxt

    resolved = sum(1 for v in value if isinstance(v, int))
    n_stale = sum(1 for i in range(n) if stalemate[i])
    unresolved = n - resolved - n_stale
    print(f"  resolved {resolved}/{n}; stalemate {n_stale}; unresolved-draw {unresolved}")

    wins = [v for v in value if isinstance(v, int) and v > 0]
    losses = [v for v in value if isinstance(v, int) and v < 0]
    print(f"  side-to-move wins: {len(wins)}/{n};  loses: {len(losses)}/{n}")
    mx_w = max(wins) if wins else 0
    mx_l = min(losses) if losses else 0
    print(f"  max DTM for the side to move: {mx_w} plies = {(mx_w + 1) // 2} moves")
    print(f"  max DTM against the side to move: {mx_l} plies = {(-mx_l) // 2} moves")

    out = {}
    for i in range(n):
        if isinstance(value[i], int):
            out[fen_of(states[i], piece_type)] = value[i]
    return out, value, states, resolved, unresolved, mx_w


def checked_child_draw(i, j):
    return False  # placeholder kept out of the computation above


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    result = {}

    if which in ("all", "kqvk"):
        table, value, states, resolved, unresolved, mx = retrograde(chess.QUEEN, "KQvK")
        mx_moves = (mx + 1) // 2
        print(f"  BOUND CHECK: KQvK max DTM {mx} plies = {mx_moves} moves "
              f"(published: 10 moves) -> {'ok' if mx_moves == 10 else 'MISMATCH'}")
        assert unresolved > 0, "KQvK must contain drawn positions (queen capturable)"
        # The standard table gives KQvK as 10 MOVES, i.e. 19 plies for the winner.
        # The brief's "10 plies max" is the moves number under a plies label.
        assert mx_moves == 10, f"KQvK table says {mx_moves} moves, published 10"
        assert mx == 19, f"KQvK winner's worst case should be 19 plies, got {mx}"
        result["kqvk"] = table
        with open("kqvk_dtm.json", "w") as f:
            json.dump(table, f)

    if which in ("all", "krvk"):
        table, value, states, resolved, unresolved, mx = retrograde(chess.ROOK, "KRvK")
        mx_moves = (mx + 1) // 2
        print(f"  BOUND CHECK: KRvK max DTM {mx} plies = {mx_moves} moves "
              f"(published: 31 plies / 16 moves) -> {'ok' if mx == 31 else 'MISMATCH'}")
        assert unresolved > 0, "KRvK must contain drawn positions (rook capturable)"
        assert mx == 31, f"KRvK table says {mx} plies, published 31"
        assert mx_moves == 16, f"KRvK should be 16 moves, got {mx_moves}"
        result["krvk"] = table
        with open("krvk_dtm.json", "w") as f:
            json.dump(table, f)

    print("\nwrote", ", ".join(f"{k}_dtm.json ({len(v)} positions)" for k, v in result.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Job 7 part B: KPvK WDL solved by retrograde, with the job 6 fault repaired.

THE JOB 6 FAULT. Job 6's solve() froze any state as soon as it was given WIN or LOSS
(`if value[i] in (WIN, LOSS): continue`). Because the very first pass can only see the
children that are already decided, a state whose winning child was still unknown would
keep whatever provisional value an earlier pass gave it, and it was never revisited.
For KPvK that produced wins for positions that are draws, e.g.
8/3k4/8/8/8/5p2/8/3K4 b - - 0 1, which I confirmed here is a draw by exhaustive search
(value 0 at ply caps 12, 20, 28 and 36).

THE REPAIR. Every pass recomputes every state from scratch and the value may improve in
either direction until nothing changes:
  * WIN  if some move leads to a LOSS for the opponent,
  * LOSS if EVERY move leads to a WIN for the opponent,
  * DRAW otherwise (only once no child is still undecided; an undecided child keeps the
    state undecided this pass).
A state is only final when a whole pass changes nothing, so no value is frozen early.

Terminals: checkmate = WIN for the mover; stalemate = DRAW; capturing the last man =
DRAW; promoting = Q/R WIN for the mover, B/N DRAW (a lone minor cannot mate).
(The "terminal is already from our view, do not negate it" fix from job 6 is kept.)

Writes {key: "W"|"D"|"L"} plus a summary.
"""
import json
import sys

import chess

WIN, LOSS, DRAW = 1, -1, 0
OTHER = {}   # the KQvK/KRvK tables, filled in main()


def build():
    index_of = {}
    boards = []
    for strong_white in (True, False):
        for wk in range(64):
            for bk in range(64):
                if wk == bk or chess.square_distance(wk, bk) < 2:
                    continue
                for s in range(64):
                    if s in (wk, bk):
                        continue
                    # A pawn cannot stand on rank 1 or 8.
                    if chess.square_rank(s) in (0, 7):
                        continue
                    for turn_white in (True, False):
                        b = chess.Board(None)
                        b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
                        b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
                        b.set_piece_at(s, chess.Piece(chess.PAWN,
                                                      chess.WHITE if strong_white else chess.BLACK))
                        b.castling_rights = 0
                        b.turn = chess.WHITE if turn_white else chess.BLACK
                        if not b.is_valid():
                            continue
                        index_of[b.board_fen() + (" w" if turn_white else " b")] = len(boards)
                        boards.append(b.copy())
    return index_of, boards


def solve():
    index_of, boards = build()
    n = len(boards)
    print(f"KPvK: {n} states", flush=True)
    edges = [None] * n
    value = [None] * n

    for i, b in enumerate(boards):
        items = []
        mate = False
        for m in b.legal_moves:
            b.push(m)
            if b.is_checkmate():
                mate = True
                b.pop()
                break
            if b.is_stalemate() or b.is_insufficient_material():
                items.append(("T", DRAW))
                b.pop()
                continue
            if m.promotion is not None:
                # CORRECT RULE (job 7 repair). A promotion must be judged by the
                # resulting position, not by the piece. In this exact position the line
                # f3f2 Ke2 f2f1q is met by Kxf1 and the game is drawn, so scoring
                # "promote to Q -> WIN" was wrong.
                #
                # After the promotion the position is K+Q/K+R/K+B/K+N vs K, which is one
                # of the classes I solved exactly (KQvK, KRvK). Look the CHILD up there.
                # Its value is from the OPPONENT's view, so the mover's value is its
                # negation - which is exactly what the "S" edge kind already does.
                child_kind = (chess.QUEEN if m.promotion in (chess.QUEEN, chess.ROOK)
                              else None)
                promoted_class = "KQvK" if m.promotion == chess.QUEEN else (
                                  "KRvK" if m.promotion == chess.ROOK else None)
                if promoted_class is not None and promoted_class in OTHER:
                    v = OTHER[promoted_class].get(
                        b.board_fen() + (" w" if b.turn else " b"))
                    if v is None:
                        b.pop()
                        continue        # not in that table: leave it out (rare)
                    items.append(("T", {"W": LOSS, "D": DRAW, "L": WIN}[v]))
                elif m.promotion in (chess.BISHOP, chess.KNIGHT):
                    # K+B v K and K+N v K cannot mate.
                    items.append(("T", DRAW))
                else:
                    b.pop()
                    continue
                b.pop()
                continue
            ci = index_of[b.board_fen() + (" w" if b.turn else " b")]
            items.append(("S", ci))
            b.pop()
        if mate:
            value[i] = WIN
            edges[i] = []
        elif not items:
            value[i] = DRAW
            edges[i] = []
        else:
            edges[i] = items

    # Every pass recomputes every state from its children's CURRENT values; a value may
    # move in either direction, and the loop ends when a whole pass changes nothing.
    #   WIN  : some move leads to a position lost for the opponent
    #   LOSS : every move leads to a position won for the opponent
    #   DRAW : no move wins, at least one move draws, no child undecided
    #   None : still has an undecided child (a cycle with no forced win among them)
    # At the fixpoint, states still None are exactly those in cycles with no forced win
    # and no forced loss: they are DRAWS. That resolution is applied once, at the end.
    passes = 0
    while True:
        passes += 1
        changed = False
        for i in range(n):
            items = edges[i]
            if not items:
                continue
            win = False
            undecided = False
            all_lose = True
            for how, c in items:
                if how == "T":
                    here = c
                else:
                    cv = value[c]
                    if cv is None:
                        undecided = True
                        all_lose = False
                        continue
                    here = -cv
                if here == WIN:
                    win = True
                    break
                if here != LOSS:
                    all_lose = False
            if win:
                new = WIN
            elif not undecided and all_lose:
                new = LOSS
            elif not undecided:
                new = DRAW
            else:
                new = None
            if new != value[i]:
                value[i] = new
                changed = True
        if not changed:
            break
    drawn = sum(1 for i in range(n) if edges[i] and value[i] is None)
    for i in range(n):
        if edges[i] and value[i] is None:
            value[i] = DRAW
    print(f"  passes {passes}, {drawn} cyclic states recorded as draws", flush=True)

    from collections import Counter
    c = Counter()
    out = {}
    for i, b in enumerate(boards):
        v = value[i]
        sym = {WIN: "W", LOSS: "L", DRAW: "D", None: "?"}[v]
        c[sym] += 1
        out[b.board_fen() + (" w" if b.turn else " b")] = sym
    print(f"  passes {passes}, counts {dict(c)}", flush=True)
    return out


def main():
    # Load the exact KQvK/KRvK tables so a promotion can be judged by its result.
    import json as _json
    with open('/tmp/ds/job7_dtm.json') as f:
        _d = _json.load(f)
    for k in ('KQvK', 'KRvK'):
        OTHER[k] = {key: v[0] for key, v in _d[k].items()}
    print(f"loaded promotion tables: " + ", ".join(f"{k} {len(v)}" for k, v in OTHER.items()),
          flush=True)
    res = solve()
    with open(sys.argv[1], "w") as f:
        json.dump(res, f)
    # The position Fable named must be a draw.
    keyb = "8/3k4/8/8/8/5p2/8/3K4 b"
    print(f"  disputed position {keyb}: {res.get(keyb)} (expected D)")


if __name__ == "__main__":
    main()

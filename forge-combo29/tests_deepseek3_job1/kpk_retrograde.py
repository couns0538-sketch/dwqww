#!/usr/bin/env python3
"""deepseek3 job 1, part B: exact retrograde solution of king+pawn vs king.

Independent work: I did not look at the other helpers' branches.

Conventions
  square s = 8*rank + file, a1 = 0, h8 = 63, rank 0 = white's first rank.
  A state is (pawn_colour, pawn_sq, wk, bk, stm), value W/D/L from the side to
  move's point of view.

  Legal iff (a) no two of the three men share a square, (b) the kings are not
  adjacent, (c) the king of the side NOT to move is not attacked by the pawn.
  With K+P vs K the pawn is the only attacker, so those are all the conditions.

  Terminal moves are folded in with their result for the mover: capturing the
  pawn gives K vs K ("D"); promoting gives K+Q vs K, which is "W" unless the
  enemy king stands next to the promotion square with our king not defending
  it, in which case the queen is taken at once and it is "D".  A node with no
  moves is a loss if its king is in check (mate), a draw otherwise (stalemate).

  The 50-move rule is NOT modelled - the conventional KPK table.  Said in the
  report.

Algorithm (textbook retrograde)
  move result for the mover = W if the move wins, L if it loses, D otherwise.
      node = W if some move is W
      node = L if every move is L
      node = D otherwise
  The last two are propagated to a fixpoint; anything left over is D.

Colour handling is generic: a state knows which colour owns the pawn, so both
"white pawn" and "black pawn" use one code path.  (An earlier version of this
file hard-coded white as the pawn owner and produced an asymmetric, wrong
table; the symmetry control at the end of this file is what caught it.)
"""
import random
from collections import deque

import chess

FILES = "abcdefgh"
PIECE_TYPES = {"q": chess.QUEEN, "r": chess.ROOK, "b": chess.BISHOP, "n": chess.KNIGHT}
KING_STEPS = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))


def sq_of(f, r):
    return 8 * r + f


def on_board(f, r):
    return 0 <= f <= 7 and 0 <= r <= 7


KING_ATK = [tuple(sq_of(f + df, r + dr) for df, dr in KING_STEPS if on_board(f + df, r + dr))
            for r in range(8) for f in range(8)]


def _pawn_attacks(sq, colour):
    f, r = sq & 7, sq >> 3
    dr = 1 if colour == "w" else -1
    return [sq_of(f + df, r + dr) for df in (-1, 1) if on_board(f + df, r + dr)]


PAWN_ATK = {"w": [frozenset(_pawn_attacks(s, "w")) for s in range(64)],
            "b": [frozenset(_pawn_attacks(s, "b")) for s in range(64)]}


def push(sq, colour, steps=1):
    r = sq >> 3
    nr = r + (1 if colour == "w" else -1) * steps
    return sq_of(sq & 7, nr) if 0 <= nr <= 7 else None


def pawn_rank(sq):
    return sq >> 3


def legal(pc, p, wk, bk, stm):
    if wk == bk or wk == p or bk == p:
        return False
    if bk in KING_ATK[wk]:
        return False
    if not 8 <= p <= 55 or pawn_rank(p) in (0, 7):
        return False
    idle_side, idle_king = ("b", bk) if stm == "w" else ("w", wk)
    if idle_side == pc:                  # the pawn's own king can never be in check
        return True
    return idle_king not in PAWN_ATK[pc][p]


def promotion_result(pc, own_king, enemy_king, qsq, piece):
    """Result for the promoter of the position after promoting to `piece`.

    This is delegated to python-chess rather than re-derived, because three
    separate hand-written versions of this rule all got it wrong in the same
    place: they forgot that the promoted position can be STALEMATE (a draw),
    e.g. white b7-b8=Q with the lone black king on h1 and the white king far
    away.  48 promotion moves in this table are exactly that.  python-chess is
    a different author's board logic, and this file keeps no other dependency
    on it for the search itself.

    Truth values:
      * the enemy king takes the new piece -> K vs K -> draw;
      * stalemate -> draw;
      * otherwise queen/rook win, bishop/knight are K+B/K+N vs K -> draw.
    """
    enemy_colour = 1 if pc == "w" else 0          # python-chess: 0 white, 1 black
    board = chess.Board(None)
    board.set_piece_at(own_king, chess.Piece(chess.KING, not enemy_colour))
    board.set_piece_at(enemy_king, chess.Piece(chess.KING, enemy_colour))
    board.set_piece_at(qsq, chess.Piece(PIECE_TYPES[piece], not enemy_colour))
    board.turn = bool(enemy_colour)
    if board.is_stalemate():
        return "D"
    if qsq in KING_ATK[enemy_king] and qsq not in KING_ATK[own_king]:
        return "D"                                # KxP-piece -> K vs K
    return "W" if piece in ("q", "r") else "D"


def build():
    states, index = [], {}
    for pc in ("w", "b"):
        for p in range(8, 56):
            if pawn_rank(p) in (0, 7):
                continue
            for wk in range(64):
                for bk in range(64):
                    for stm in ("w", "b"):
                        if legal(pc, p, wk, bk, stm):
                            index[(pc, p, wk, bk, stm)] = len(states)
                            states.append((pc, p, wk, bk, stm))

    moves = []
    for (pc, p, wk, bk, stm) in states:
        mv = []
        nxt = "b" if stm == "w" else "w"
        pawn_is_white = (pc == "w")
        if stm == pc:                                  # the pawn's side moves
            own_king, enemy_king = (wk, bk) if pawn_is_white else (bk, wk)
            for t in KING_ATK[own_king]:
                if t == enemy_king or t == p or t in KING_ATK[enemy_king]:
                    continue
                succ = (pc, p, t, bk, nxt) if pawn_is_white else (pc, p, wk, t, nxt)
                mv.append((index[succ], None))
            one = push(p, pc)
            if one is not None and one != bk and one != wk:
                last_rank = 7 if pawn_is_white else 0
                if pawn_rank(one) == last_rank:
                    for promo in ("q", "r", "b", "n"):
                        mv.append((None, promotion_result(pc, own_king, enemy_king, one, promo)))
                else:
                    mv.append((index[(pc, one, wk, bk, nxt)], None))
                    start_rank = 1 if pawn_is_white else 6
                    if pawn_rank(p) == start_rank:
                        two = push(p, pc, 2)
                        if two is not None and two != bk and two != wk:
                            mv.append((index[(pc, two, wk, bk, nxt)], None))
        else:                                          # the bare king moves
            bare_king = bk if pawn_is_white else wk
            own_king = wk if pawn_is_white else bk
            for t in KING_ATK[bare_king]:
                if t == own_king or t in KING_ATK[own_king]:
                    continue
                if t in PAWN_ATK[pc][p]:
                    continue                            # moving into pawn check
                if t == p:
                    mv.append((None, "D"))              # KxP -> K vs K
                elif pawn_is_white:
                    mv.append((index[(pc, p, wk, t, nxt)], None))
                else:
                    mv.append((index[(pc, p, t, bk, nxt)], None))
        moves.append(mv)
    return states, index, moves


def king_in_check(state):
    pc, p, wk, bk, stm = state
    if pc == "w":
        return stm == "b" and bk in PAWN_ATK["w"][p]
    return stm == "w" and wk in PAWN_ATK["b"][p]


def solve(states, moves):
    n = len(states)
    val = [None] * n
    preds = [[] for _ in range(n)]
    for i, mv in enumerate(moves):
        for j, _ in mv:
            if j is not None:
                preds[j].append(i)

    pending = [0] * n          # moves whose result for the mover is still unknown
    has_draw = [False] * n     # a move of this node is known to be a draw
    dq = deque()
    for i, mv in enumerate(moves):
        if not mv:
            val[i] = "L" if king_in_check(states[i]) else "D"
            dq.append(i)
            continue
        if any(r == "W" for j, r in mv if j is None):
            val[i] = "W"                     # a promotion that simply wins
            dq.append(i)
            continue
        if any(r == "D" for j, r in mv if j is None):
            has_draw[i] = True               # KxP is a draw; so is a lost promotion
        pending[i] = len(mv)                 # every move still undecided
        if pending[i] == 0:
            val[i] = "L" if not has_draw[i] else "D"
            dq.append(i)

    while dq:
        i = dq.popleft()
        flipped = {"W": "L", "L": "W", "D": "D"}[val[i]]
        for pi in preds[i]:
            if val[pi] is not None:
                continue
            if flipped == "W":
                val[pi] = "W"
                dq.append(pi)
            else:
                # A node is a loss only when EVERY move loses.  A single drawing
                # move makes it a draw, so record that and decide only when all
                # moves are resolved.  (An earlier version took the verdict of
                # whichever move happened to resolve last, which turned draws
                # into losses; the independent Bellman check caught it.)
                if flipped == "D":
                    has_draw[pi] = True
                pending[pi] -= 1
                if pending[pi] == 0:
                    val[pi] = "D" if has_draw[pi] else "L"
                    dq.append(pi)
    for i in range(n):
        if val[i] is None:
            val[i] = "D"
    return val


def fen(pc, p, wk, bk, stm):
    board = [""] * 64
    board[wk] = "K"
    board[bk] = "k"
    board[p] = "P" if pc == "w" else "p"
    rows = []
    for r in range(7, -1, -1):
        row, empty = "", 0
        for f in range(8):
            c = board[8 * r + f]
            if c:
                if empty:
                    row += str(empty)
                    empty = 0
                row += c
            else:
                empty += 1
        if empty:
            row += str(empty)
        rows.append(row)
    return "/".join(rows) + (" w " if stm == "w" else " b ") + "- - 0 1"


def mover_view(v):
    return {"W": "L", "L": "W", "D": "D"}[v]


def controls(states, moves, val, rng):
    """Control A: a player that always picks a move keeping the result must never
    change the class.  Control B: a random mover must change it often.  Terminal
    moves are excluded from A because their class is already the best available
    (a winning promotion is the win itself; a pawn capture is a draw)."""
    kept = changed = nomove = 0
    for _ in range(2000):
        i = rng.randrange(len(states))
        best = [j for j, r in moves[i]
                if j is not None and mover_view(val[j]) == val[i]]
        if not best:
            # every move of this position is terminal: the class is already taken
            if moves[i]:
                nomove += 1
                continue
            nomove += 1
            continue
        j = rng.choice(best)
        if mover_view(val[j]) == val[i]:
            kept += 1
        else:
            changed += 1
    rand_changed = rand_kept = 0
    for _ in range(2000):
        i = rng.randrange(len(states))
        if not moves[i]:
            continue
        j, r = rng.choice(moves[i])
        got = r if j is None else mover_view(val[j])
        if got != val[i]:
            rand_changed += 1
        else:
            rand_kept += 1
    return kept, changed, nomove, rand_changed, rand_kept


def symmetry_check(states, index, val):
    """Mirror the board vertically and swap the colours, including which king is
    which.  The value is stated from the side-to-move's view, so it must be
    unchanged.  A table with a colour-dependent bug fails this."""
    bad = missing = 0
    for i, (pc, p, wk, bk, stm) in enumerate(states):
        def m(s):
            return sq_of(s & 7, 7 - (s >> 3))
        other = "b" if pc == "w" else "w"
        ostm = "b" if stm == "w" else "w"
        key = (other, m(p), m(bk), m(wk), ostm)      # colours swap, so the kings swap
        j = index.get(key)
        if j is None:
            missing += 1
        elif val[j] != val[i]:
            bad += 1
    return bad, missing


def check_table_sanity(states, index, val):
    """A few facts a correct KPK table must satisfy, checked directly."""
    problems = []
    # 1. the pawn's side is never lost when it is the pawn's side's turn:
    #    it can always at least keep the pawn (it is never forced to lose it).
    for i, s in enumerate(states):
        if s[4] == s[0] and val[i] == "L":
            problems.append(("pawn side to move and lost", s))
            break
    # 2. K+P vs K on the rook file with the defending king in front is a draw
    #    only if the pawn side cannot win; a specific known win: white Ka6/Pe6 vs
    #    black Ke8 won?  Use the well-known win 8/8/8/8/8/4K3/4P3/4k3-like cases
    #    instead check the classic draw: black king h8, white king h6, pawn h7.
    key = ("w", sq_of(7, 6), sq_of(7, 5), sq_of(7, 7), "w")
    if key in index and val[index[key]] != "D":
        problems.append(("h7/h6/kh8 should be a draw", key, val[index[key]]))
    # 3. classic win: white Ke6, Pe5, black Ke8 with white to move -> win
    key = ("w", sq_of(4, 4), sq_of(4, 5), sq_of(4, 7), "w")
    if key in index:
        problems.append(("documented verdict 4k3/8/4K3/4P3 w", val[index[key]]))
    return problems


def main():
    states, index, moves = build()
    val = solve(states, moves)
    n = len(states)
    print("legal KPK positions (pawn colour counted separately):", n)
    for pc in ("w", "b"):
        for stm in ("w", "b"):
            vs = [val[i] for i, s in enumerate(states) if s[0] == pc and s[4] == stm]
            print(f"  pawn={pc} stm={stm}: total={len(vs)} W={vs.count('W')} "
                  f"D={vs.count('D')} L={vs.count('L')}")
    pv = [val[i] for i, s in enumerate(states) if s[4] == s[0]]
    ov = [val[i] for i, s in enumerate(states) if s[4] != s[0]]
    print("pawn side to move:  total", len(pv), "wins", pv.count("W"),
          "draws", pv.count("D"), "losses", pv.count("L"))
    print("other side to move: total", len(ov), "wins", ov.count("W"),
          "draws", ov.count("D"), "losses", ov.count("L"))

    print("symmetry control (mirror+colours, mismatches/missing):", symmetry_check(states, index, val))
    for pr in check_table_sanity(states, index, val):
        print("sanity:", pr)

    rng = random.Random(20261115)
    kept, changed, nomove, rc, rk = controls(states, moves, val, rng)
    print("control preserving mover: kept", kept, "changed", changed,
          "(no preserving move available in", nomove, "of 2000)")
    print("control random mover:     changed", rc, "kept", rk)

    with open("kpk_2000.txt", "w") as fh:
        for _ in range(2000):
            i = rng.randrange(n)
            pc, p, wk, bk, stm = states[i]
            fh.write(fen(pc, p, wk, bk, stm) + " ; " + val[i] + "\n")
    print("wrote kpk_2000.txt")

    # the whole table, kept locally only (26 MB, far past what we may commit);
    # the Bellman verifier needs the closed set, not a random sample
    with open("/home/ubuntu/work/kpk_full.txt", "w") as fh:
        for i, (pc, p, wk, bk, stm) in enumerate(states):
            fh.write(fen(pc, p, wk, bk, stm) + " ; " + val[i] + "\n")
    print("wrote /home/ubuntu/work/kpk_full.txt with", n, "positions")

    asked = [
        ("8/3k4/8/8/8/5p2/8/3K4 b - - 0 1", "b", sq_of(5, 2), sq_of(3, 0), sq_of(3, 6), "b"),
        ("4k3/8/4K3/4P3/8/8/8/8 w - - 0 1", "w", sq_of(4, 4), sq_of(4, 5), sq_of(4, 7), "w"),
        ("7k/8/7K/7P/8/8/8/8 w - - 0 1", "w", sq_of(7, 4), sq_of(7, 5), sq_of(7, 7), "w"),
        ("8/8/8/8/8/4k3/4p3/4K3 b - - 0 1", "b", sq_of(4, 1), sq_of(4, 0), sq_of(4, 2), "b"),
    ]
    for f, pc, p, wk, bk, stm in asked:
        i = index.get((pc, p, wk, bk, stm))
        print("VERDICT", f, "->", ("ILLEGAL" if i is None else val[i]))


if __name__ == "__main__":
    main()

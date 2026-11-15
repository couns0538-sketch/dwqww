#!/usr/bin/env python3
"""Job 7 A0: controls on the extended (WDL + distance) tables.

1. reader: 1,000 random KQvK and 1,000 KRvK positions with the strong side to move must
   be wins (WDL control, as in job 6 but on the new tables).
2. counter: random mover loses half points; tablebase-best mover loses none.
3. distance: in 1,000 random WON positions, a player that always picks a move with the
   smallest distance must mate in exactly the table's number of plies, every time.
   ("Exactly" = the game length from that position equals abs(dtm).)

Usage: j7a0.py <dtm.json> <out.json> <seed>
"""
import json
import random
import sys

import chess


def class_key(b):
    return b.board_fen() + (" w" if b.turn else " b")


def kind_of(b):
    men = [s for s in chess.SQUARES
           if b.piece_at(s) and b.piece_at(s).piece_type != chess.KING]
    if len(men) != 1:
        return None
    pt = b.piece_at(men[0]).piece_type
    return {chess.QUEEN: "KQvK", chess.ROOK: "KRvK"}.get(pt)


def strong_colour(b):
    for s in chess.SQUARES:
        p = b.piece_at(s)
        if p and p.piece_type != chess.KING:
            return p.color
    return None


def rand_positions(kind, count, rng, strong_to_move=None):
    strong = chess.QUEEN if kind == "KQvK" else chess.ROOK
    out, seen = [], set()
    guard = 0
    while len(out) < count and guard < count * 5000:
        guard += 1
        wk, bk, s = rng.sample(range(64), 3)
        if chess.square_distance(wk, bk) < 2:
            continue
        b = chess.Board(None)
        b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        b.set_piece_at(s, chess.Piece(strong, chess.WHITE))
        b.castling_rights = 0
        b.turn = chess.WHITE if strong_to_move else chess.BLACK
        if not b.is_valid() or b.is_game_over():
            continue
        fen = b.fen()
        if fen in seen:
            continue
        seen.add(fen)
        out.append(fen)
    return out


def evaluate(child, dtm):
    if child.is_checkmate():
        return ("W", 1)
    if child.is_stalemate() or child.is_insufficient_material():
        return ("D", None)
    v = dtm_of(child, dtm)
    return v if v else (None, None)


def dtm_of(b, dtm):
    k = kind_of(b)
    if k is None:
        return None
    return dtm[k].get(class_key(b))


def mover_view(child_value):
    """Convert a child's (wdl, dtm) to the MOVER's view."""
    if child_value is None or child_value[0] is None:
        return None
    wdl, d = child_value
    if wdl == "W":
        return ("L", -(abs(d) + 1) if d else None)
    if wdl == "L":
        return ("W", abs(d) + 1 if d else None)
    return ("D", None)


def play_to_mate(fen, dtm, rng, choose):
    """Play to mate where the WINNING side uses `choose` and the loser maximises the
    distance (so the game length equals the table's dtm when both play as the table
    says). The loser is the side that is not the table's 'W' side at the root."""
    b = chess.Board(fen)
    mover = b.turn
    plies = 0
    while plies < 300:
        if b.is_checkmate():
            return plies
        if b.is_stalemate():
            return None
        if b.turn == mover:
            move = choose(b, dtm, rng)
        else:
            move = choose_max_dtm(b, dtm, rng)
        if move is None:
            return None
        b.push(move)
        plies += 1
    return None


def choose_max_dtm(b, dtm, rng):
    """The defender: a move with the LARGEST distance for the opponent (it is the side
    to move here, and its value is a LOSS, so prefer the most negative dtm)."""
    best = []
    for m in b.legal_moves:
        b.push(m)
        mv = mover_view(evaluate(b, dtm))
        b.pop()
        if mv is None:
            continue
        wdl, d = mv
        if wdl == "D":
            return m            # a draw is the best a defender can do
        cand = (abs(d) if d else 0, m)
        if not best or cand[0] > best[0][0]:
            best = [cand]
        elif cand[0] == best[0][0]:
            best.append(cand)
    return rng.choice(best)[1] if best else None


def choose_min_dtm(b, dtm, rng):
    best = []
    for m in b.legal_moves:
        b.push(m)
        mv = mover_view(evaluate(b, dtm))
        b.pop()
        if mv is None:
            continue
        wdl, d = mv
        if wdl != "W":
            continue
        cand = (abs(d), m)
        if not best or cand[0] < best[0][0]:
            best = [cand]
        elif cand[0] == best[0][0]:
            best.append(cand)
    return rng.choice(best)[1] if best else None


def choose_random(b, dtm, rng):
    moves = list(b.legal_moves)
    return rng.choice(moves) if moves else None


def choose_best(b, dtm, rng):
    best = []
    for m in b.legal_moves:
        b.push(m)
        mv = mover_view(evaluate(b, dtm))
        b.pop()
        if mv is None:
            continue
        wdl, d = mv
        rank = {"W": 3, "D": 2, "L": 1}[wdl]
        cand = (rank, m)
        if not best or cand[0] > best[0][0]:
            best = [cand]
        elif cand[0] == best[0][0]:
            best.append(cand)
    return rng.choice(best)[1] if best else None


def main():
    dtm_path, out_path, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
    rng = random.Random(seed)
    with open(dtm_path) as f:
        dtm = json.load(f)
    out = {"seed": seed}

    # 1. reader
    reader = {}
    for kind in ("KQvK", "KRvK"):
        positions = rand_positions(kind, 1000, rng, strong_to_move=True)
        checked = 0
        bad = 0
        for fen in positions:
            b = chess.Board(fen)
            v = dtm[kind].get(class_key(b))
            checked += 1
            if not v or v[0] != "W":
                bad += 1
        reader[kind] = {"checked": checked, "not_win": bad}
    out["reader"] = reader

    # 2. counter
    positions = rand_positions("KQvK", 1000, rng, strong_to_move=True)
    def count(chooser):
        lost = 0
        n = 0
        for fen in positions:
            b = chess.Board(fen)
            v = dtm["KQvK"].get(class_key(b))
            if not v or v[0] != "W":
                continue
            m = chooser(b, dtm, rng)
            if m is None:
                continue
            b.push(m)
            after = mover_view(evaluate(b, dtm))
            b.pop()
            if after is None:
                continue
            n += 1
            if after[0] in ("D", "L"):
                lost += 1
        return {"counted": n, "lost_half_points": lost}
    out["counter_random"] = count(choose_random)
    out["counter_best"] = count(choose_best)

    # 3. distance
    dist = {}
    for kind in ("KQvK", "KRvK"):
        won = [f for f in rand_positions(kind, 3000, rng, strong_to_move=True)
               if (dtm[kind].get(class_key(chess.Board(f))) or ["?"])[0] == "W"]
        rng.shuffle(won)
        checked = 0
        exact = 0
        mismatch = []
        for fen in won[:1000]:
            v = dtm[kind].get(class_key(chess.Board(fen)))
            if not v or v[0] != "W" or not v[1]:
                continue
            plies = play_to_mate(fen, dtm, rng, choose_min_dtm)
            checked += 1
            if plies == abs(v[1]):
                exact += 1
            elif len(mismatch) < 5:
                mismatch.append({"fen": fen, "table_dtm": v[1], "played_plies": plies})
        dist[kind] = {"checked": checked, "exact": exact, "mismatches": mismatch}
    out["distance"] = dist

    with open(out_path, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: v for k, v in out.items()}, indent=1))


if __name__ == "__main__":
    main()

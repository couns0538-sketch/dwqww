#!/usr/bin/env python3
"""Exact retrograde solver for small endings -- the oracle, independent of the engine.

python-chess generates moves and adjudicates legality; this module only does the
retrograde arithmetic. Nothing here reads the engine's book, eval or move ordering.

VALUE CONVENTION. value(state) is from the SIDE TO MOVE's point of view:
WIN = the side to move forces mate, LOSS = it is mated against best play,
DRAW = neither side can force it. DTM is in plies to the end of the game.

TWO PASSES, ON PURPOSE. Pass 1 resolves WIN/LOSS/DRAW. Pass 2 computes the DTM in
strict layers over the resolved graph:
    checkmates at layer 0;
    a WIN enters layer d when it has a LOSS child at layer d-1;
    a LOSS enters layer d only when EVERY child is a WIN at layer <= d-1.
A single combined pass invites exactly the bug that produced a KQK maximum of 5
moves against a true 10: a state seeded with a large external DTM can be dequeued
before a shorter path to it is discovered, and "first time seen" is then not
"minimum". Separating the passes makes the minimum a property of the layering.

SYMMETRY, and why the group depends on the material. A board symmetry preserves
legality only if it preserves every direction-dependent rule:
  * no pawns -> all 8 (file flip, rank flip, transpose) are exact;
  * a WHITE pawn -> only the 2 rank-preserving ones (identity, file flip).
Using all 8 on KPK would merge a won position with a lost one. PAWN_SYMS is
selected by that property rather than by index, because transpose sits at index 1
in the enumeration order and [0], [1] would silently reverse the pawn.

BOTH SIDES TO MOVE. chess.Board(None) starts White to move, and is_valid() checks
that the side NOT to move is not in check, so one placement yields up to two legal
states. Enumerating only the default turn builds half a table, and the symptom is
"successor left the table" on an ordinary capture.

THE FIFTY-MOVE RULE IS NOT MODELLED, deliberately: the question these tables answer
is "is this position won in principle". dtm_max per family makes the claim
checkable rather than assumed.

Promotions and captures leave the material signature. They are resolved EXACTLY
from tables solved earlier -- never by an engine claim and never by a guess.
"""
from __future__ import annotations

import itertools

import chess

WIN, LOSS, DRAW = 1, -1, 0
UNKNOWN = None


def _all_syms():
    out = []
    for ff in (False, True):
        for fr in (False, True):
            for tr in (False, True):
                m = {}
                for sq in range(64):
                    f, r = chess.square_file(sq), chess.square_rank(sq)
                    if tr:
                        f, r = r, f
                    if ff:
                        f = 7 - f
                    if fr:
                        r = 7 - r
                    m[sq] = chess.square(f, r)
                out.append(m)
    return out


ALL_SYMS = _all_syms()
PAWN_SYMS = [m for m in ALL_SYMS
             if all(chess.square_rank(m[sq]) == chess.square_rank(sq) for sq in range(64))]
assert len(ALL_SYMS) == 8 and len(PAWN_SYMS) == 2


def canonical(board: chess.Board, syms):
    """(key, sym_id). sym_id maps the REAL board into the canonical key board."""
    if board.king(chess.BLACK) is None:
        raise ValueError("no black king")
    # symbol() keeps the case, which IS the colour. Upper-casing collapses the two
    # sides into one and silently builds impossible boards.
    pieces = [(sq, board.piece_at(sq).symbol())
              for sq in chess.SQUARES if board.piece_at(sq)]
    best = None
    for i, m in enumerate(syms):
        placed = tuple(sorted((m[sq], sym) for sq, sym in pieces))
        key = (placed, board.turn)
        if best is None or key < best[0]:
            best = (key, i)
    return best[0], best[1]


def decanonical(key, syms):
    placed, turn = key
    b = chess.Board(None)
    for sq, sym in placed:
        b.set_piece_at(sq, chess.Piece.from_symbol(sym))
    b.turn = turn
    b.halfmove_clock = 0
    b.fullmove_number = 1
    return b


def signature(board: chess.Board):
    """Material signature: sorted (piece_type, colour) excluding kings."""
    return tuple(sorted((p.piece_type, p.color)
                        for p in board.piece_map().values() if p.piece_type != chess.KING))


def sig_of(pieces):
    return tuple(sorted((pt, col) for pt, col in pieces if pt != chess.KING))


def material_name(sig):
    names = {chess.PAWN: "P", chess.KNIGHT: "N", chess.BISHOP: "B",
             chess.ROOK: "R", chess.QUEEN: "Q"}
    w = "".join(sorted(names[pt] for pt, col in sig if col == chess.WHITE))
    b = "".join(sorted(names[pt] for pt, col in sig if col == chess.BLACK))
    return f"K{w}vK{b}"


def _external(board, tables):
    """Value for the CHILD's side to move, from an already-solved table."""
    if board.is_checkmate():
        return (LOSS, 0)
    if board.is_stalemate():
        return (DRAW, 0)
    if tables is None:
        raise ValueError(f"off-table successor with no tables: {board.fen()}")
    sig = signature(board)
    if sig not in tables:
        raise KeyError(f"signature {sig} needed before it was solved (from {board.fen()})")
    tab = tables[sig]
    key, _ = canonical(board, ALL_SYMS)
    if key not in tab["value"]:
        raise KeyError(f"successor absent from its table: {board.fen()}")
    return (tab["value"][key], tab["dtm"][key])


def solve(pieces, syms, tables=None, verbose=True):
    pts = [p for p, _ in pieces]
    cols = [c for _, c in pieces]
    states = {}
    n_placement = 0
    for combo in itertools.permutations(range(64), len(pieces)):
        b = chess.Board(None)
        for sq, pt, col in zip(combo, pts, cols):
            b.set_piece_at(sq, chess.Piece(pt, col))
        for turn in (chess.WHITE, chess.BLACK):
            b.turn = turn
            if not b.is_valid():
                continue
            n_placement += 1
            key, sid = canonical(b, syms)
            if key not in states:
                states[key] = sid
    if verbose:
        print(f"  {n_placement:,} legal placements -> {len(states):,} canonical states "
              f"({len(syms)} symmetries)", flush=True)

    children = {}
    external = {}
    mate_flag = {}          # key -> True if the state is checkmate
    same_sig = sig_of(pieces)

    for i, (key, sid) in enumerate(states.items()):
        b = decanonical(key, syms)
        kids, ext = [], []
        for mv in b.legal_moves:
            b.push(mv)
            if signature(b) == same_sig:
                k2, _ = canonical(b, syms)
                kids.append(k2)
            else:
                ext.append(_external(b, tables))
            b.pop()
        children[key] = kids
        external[key] = ext
        mate_flag[key] = b.is_checkmate()
        if verbose and i and i % 200000 == 0:
            print(f"    moves {i:,}/{len(states):,}", flush=True)

    pred = {k: [] for k in states}
    for k, kids in children.items():
        for c in kids:
            pred[c].append(k)

    value = {k: UNKNOWN for k in states}

    # --- pass 1a: seeds -------------------------------------------------------
    for k in states:
        b = decanonical(k, syms)
        if not any(True for _ in b.legal_moves):
            value[k] = LOSS if b.is_check() else DRAW
            continue
        if any(v == LOSS for v, _ in external[k]):
            value[k] = WIN
            continue

    # --- pass 1b: retrograde over values --------------------------------------
    # remaining = number of moves that could still turn out NOT to lose.
    # Unresolved same-signature children count. External DRAW children count.
    # External WIN children do NOT: a move that hands the opponent a win is a bad
    # move. Counting external WINs here is what made KBK report three "checkmates".
    remaining = {}
    for k in states:
        if value[k] is not UNKNOWN:
            continue
        remaining[k] = len(children[k]) + sum(1 for v, _ in external[k] if v == DRAW)

    wave = [k for k in states if value[k] is LOSS]
    wave += [k for k in states if value[k] is WIN]
    while wave:
        nxt = []
        for node in wave:
            nv = value[node]
            for p in pred[node]:
                if value[p] is not UNKNOWN:
                    continue
                if nv == LOSS:
                    value[p] = WIN
                    nxt.append(p)
                else:
                    remaining[p] -= 1
                    if remaining[p] == 0:
                        value[p] = LOSS
                        nxt.append(p)
        wave = nxt

    for k in states:
        if value[k] is UNKNOWN:
            value[k] = DRAW

    # --- pass 2: DTM in strict layers -----------------------------------------
    dtm = {k: -1 for k in states}
    layer = {}
    for k in states:
        if value[k] is LOSS and not children[k] and not external[k] and mate_flag[k]:
            dtm[k] = 0
            layer[k] = 0
        elif value[k] == LOSS and not children[k] and not external[k]:
            dtm[k] = 0          # stalemate: terminal, no mate
            layer[k] = 0

    d = 0
    unresolved_win = {k for k in states if value[k] == WIN and dtm[k] < 0}
    unresolved_loss = {k for k in states if value[k] == LOSS and dtm[k] < 0}
    while unresolved_win or unresolved_loss:
        d += 1
        # WINs: any child (internal or external) that is a LOSS at layer d-1
        won = set()
        for k in unresolved_win:
            for c in children[k]:
                if layer.get(c) == d - 1 and value[c] == LOSS:
                    won.add(k); break
            else:
                if any(v == LOSS and dd == d - 1 for v, dd in external[k]):
                    won.add(k)
        # LOSSes: every child a WIN with dtm <= d-1, and no child that is not a win
        lost = set()
        for k in unresolved_loss:
            ok = True
            worst = 0
            for c in children[k]:
                if value[c] != WIN or dtm[c] < 0 or dtm[c] > d - 1:
                    ok = False; break
                worst = max(worst, dtm[c])
            if ok:
                for v, dd in external[k]:
                    if v != WIN:
                        ok = False; break
                    if dd > d - 1:
                        ok = False; break
                    worst = max(worst, dd)
            if ok and (children[k] or external[k]):
                lost.add(k)
        if not won and not lost:
            raise RuntimeError(f"DTM layering stalled at d={d} with "
                               f"{len(unresolved_win)} wins and {len(unresolved_loss)} losses")
        for k in won:
            dtm[k] = d; layer[k] = d
        for k in lost:
            dtm[k] = d; layer[k] = d
        unresolved_win -= won
        unresolved_loss -= lost
        if verbose and d % 5 == 0:
            print(f"    dtm layer {d}: {len(unresolved_win)} W, {len(unresolved_loss)} L left",
                  flush=True)

    return {"states": states, "value": value, "dtm": dtm, "layer": layer, "syms": syms,
            "children": children, "external": external,
            "n_canonical": len(states), "n_placement": n_placement}


def summarise(tab, label):
    from collections import Counter
    c = Counter(tab["value"].values())
    wins = [v for v in tab["dtm"].values() if v is not None and v > 0]
    return {"label": label, "canonical_states": tab["n_canonical"],
            "legal_states": tab["n_placement"], "symmetries": len(tab["syms"]),
            "WIN": c[WIN], "LOSS": c[LOSS], "DRAW": c[DRAW],
            "dtm_max_plies": max(wins) if wins else None,
            "dtm_max_moves": (max(wins) + 1) // 2 if wins else None}

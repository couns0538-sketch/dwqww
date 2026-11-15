#!/usr/bin/env python3
"""Build job-1 repetition cases mechanically with python-chess.

A case is (S0_fen, [a, k, a', k', a, k, a']) where a/a' are inverse reversible
moves of the strong (white) side and k/k' inverse reversible king moves of the
bare (black) king.  After the 7-move list the position C is on the board with
BLACK to move; C has occurred twice and k' brings S0 for the third time.

Every property the job asks for is checked in check_case() before a case is
kept.  The same checker (plus a repetition-only subset) is run on two kinds of
planted fault, which must be rejected.
"""

import json
import random
import sys

import chess

SEED = 20261115
WANT = 500
OUT = "cases.json"
FAULT_OUT = "cases_fault.json"


def make_s0(rng, material):
    """Random KQ/KR vs K with white to move, black not in check."""
    for _ in range(20000):
        wk, bk, wp = rng.sample(range(64), 3)
        if chess.square_distance(wk, bk) <= 1:
            continue
        board = chess.Board(None)
        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        board.set_piece_at(wp, chess.Piece(material, chess.WHITE))
        board.turn = chess.WHITE
        board.halfmove_clock = 0
        board.fullmove_number = 1
        if not board.is_valid():
            continue
        if board.is_check():          # black in check at S0 would spoil the cycle
            continue
        return board
    raise RuntimeError("no S0 found")


def quiet_white_moves(board):
    """Quiet, non-capturing, non-promoting white moves.  Legality of the return
    move a' two plies later is decided by check_case() on the full list, not
    here: the side to move in between belongs to the opponent."""
    return [m for m in board.legal_moves
            if not board.is_capture(m) and not m.promotion and not board.gives_check(m)]


def quiet_king_moves(board):
    return [m for m in board.legal_moves
            if not board.is_capture(m) and not board.is_castling(m)]


def repeated_positions(s0, moves):
    """Count occurrences of the final position along S0 + moves (S0 included)."""
    board = s0.copy()
    key = None
    for move in moves:
        board.push(move)
    key = board._transposition_key()
    count = 1 if board._transposition_key() == key else 0
    walk = s0.copy()
    hits = [0] if walk._transposition_key() == key else []
    for i, move in enumerate(moves):
        walk.push(move)
        if walk._transposition_key() == key:
            hits.append(i + 1)
    return len(hits), hits


def check_case(s0, moves, need_len=True):
    """All job-1 requirements.  Returns (ok, reasons, rep_moves)."""
    reasons = []
    board = s0.copy()
    if board.is_checkmate() or board.is_stalemate() or board.is_insufficient_material():
        reasons.append("S0 is terminal")
    for i, move in enumerate(moves):
        if move not in board.legal_moves:
            reasons.append(f"move {i} {move.uci()} illegal in prefix {i}")
            return False, reasons, None
        board.push(move)
        if board.is_checkmate():
            reasons.append(f"prefix {i+1} is checkmate")
        if board.is_stalemate():
            reasons.append(f"prefix {i+1} is stalemate")
    if need_len and len(moves) != 7:
        reasons.append(f"list has {len(moves)} plies, expected 7")
    if board.turn != chess.BLACK:
        reasons.append("C is not black to move")
    if board.is_check():
        reasons.append("bare king is in check at C")
    if board.is_checkmate() or board.is_stalemate():
        reasons.append("C is terminal")
    if board.is_insufficient_material():
        reasons.append("C is insufficient material")
    if board.halfmove_clock != len(moves):
        reasons.append(f"C halfmove clock {board.halfmove_clock} != {len(moves)}")

    seen, hits = repeated_positions(s0, moves)
    if seen != 2:
        reasons.append(f"C occurred {seen} times at {hits}, expected 2")

    rep_moves, other_moves, drawn_other = [], [], []
    for move in board.legal_moves:
        after = board.copy()
        after.push(move)
        if after.is_repetition(3):
            rep_moves.append(move)
        else:
            other_moves.append(move)
            if (after.is_stalemate() or after.is_insufficient_material()
                    or after.is_checkmate()):
                drawn_other.append(move.uci())
    if len(rep_moves) != 1:
        reasons.append(f"{len(rep_moves)} black moves give the third repetition, expected 1")
    if drawn_other:
        reasons.append(f"other moves that draw at once: {drawn_other}")
    if len(other_moves) < 2:
        reasons.append(f"only {len(other_moves)} non-repeating black move(s): nothing to choose")
    if len(rep_moves) == 1 and len(moves) >= 6:
        want_rep = chess.Move(moves[5].to_square, moves[5].from_square)
        if rep_moves[0] != want_rep:
            reasons.append(f"the third-repetition move {rep_moves[0].uci()} is not k' {want_rep.uci()}")
    return (not reasons), reasons, rep_moves


def build_case(rng, material):
    s0 = make_s0(rng, material)
    for _ in range(80):
        wmoves = quiet_white_moves(s0)
        if not wmoves:
            return None
        a = rng.choice(wmoves)
        b1 = s0.copy()
        b1.push(a)
        kmoves = quiet_king_moves(b1)
        if not kmoves:
            continue
        k = rng.choice(kmoves)
        a2 = chess.Move(a.to_square, a.from_square)
        k2 = chess.Move(k.to_square, k.from_square)
        moves = [a, k, a2, k2, a, k, a2]
        ok, reasons, _ = check_case(s0, moves)
        if ok:
            return s0, moves, a2, wmoves
    return None


def self_test():
    """Positive control for the checker: a hand-built known third repetition."""
    b = chess.Board()
    seq = ["g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1", "f6g8"]
    for u in seq:
        b.push_uci(u)
    assert b.is_repetition(3), "checker control: start position after 8 plies must repeat 3x"
    # and a two-fold version must NOT be a third repetition
    b2 = chess.Board()
    for u in ["g1f3", "g8f6", "f3g1"]:
        b2.push_uci(u)
    assert not b2.is_repetition(3)
    return True


def main():
    global SEED, WANT, OUT, FAULT_OUT
    assert self_test()
    if len(sys.argv) > 1:
        SEED = int(sys.argv[1])
    if len(sys.argv) > 2:
        WANT = int(sys.argv[2])
    if len(sys.argv) > 3:
        OUT = sys.argv[3]
    if len(sys.argv) > 4:
        FAULT_OUT = sys.argv[4]
    rng = random.Random(SEED)
    cases, faults, tries = [], [], 0
    while len(cases) < WANT and tries < WANT * 600:
        tries += 1
        material = chess.QUEEN if rng.random() < 0.75 else chess.ROOK
        got = build_case(rng, material)
        if got is None:
            continue
        s0, moves, a2, wmoves = got

        # Fault 1: one cycle less -- the list stops at ply 3, so k' is only the
        # second occurrence.  Repetition-only check must reject it.
        f1 = moves[:3]
        ok1, reasons1, repm1 = check_case(s0, f1, need_len=False)
        # Fault 2: the full 7-ply list is legal but ply 7 is a DIFFERENT white
        # move, so C occurs once only and no black move gives a third
        # repetition.  Legality passes; only the repetition tests can reject it.
        b6 = s0.copy()
        for u in moves[:6]:
            b6.push(u)
        f2 = []
        ok2, reasons2 = True, ["no fault-2 candidate"]
        for w in b6.legal_moves:
            if b6.is_capture(w) or w.promotion:
                continue
            trial = list(moves[:6]) + [w]
            legal_ok = True
            walk = s0.copy()
            for u in trial:
                if u not in walk.legal_moves:
                    legal_ok = False
                    break
                walk.push(u)
            if not legal_ok:
                continue
            seen_t, _ = repeated_positions(s0, trial)
            if seen_t != 2:
                f2 = trial
                ok2, reasons2, _ = check_case(s0, trial, need_len=False)
                break
        if f2:
            f2 = [m.uci() for m in f2]
        if ok1 or ok2:
            print("CONTROL FAILED: planted fault accepted", s0.fen(),
                  "f1ok=", ok1, "f2ok=", ok2, file=sys.stderr)
            sys.exit(2)
        faults.append({
            "s0": s0.fen(),
            "fault1_moves": [m.uci() for m in f1],
            "fault1_reasons": reasons1,
            "fault1_rep_moves": len(repm1 or []),
            "fault2_moves": f2,
            "fault2_reasons": reasons2,
        })
        cases.append({
            "s0": s0.fen(),
            "moves": [m.uci() for m in moves],
            "material": "Q" if material == chess.QUEEN else "R",
        })

    for c in cases:
        b = chess.Board(c["s0"])
        for u in c["moves"]:
            b.push_uci(u)
        c["n_black_moves_at_c"] = b.legal_moves.count()
        c["c_fen"] = b.fen()
        c["rep_move"] = c["moves"][5][2:4] + c["moves"][5][0:2]

    with open(OUT, "w") as f:
        json.dump({"seed": SEED, "cases": cases}, f, indent=1)
    with open(FAULT_OUT, "w") as f:
        json.dump({"seed": SEED, "cases": faults}, f, indent=1)
    print(f"cases={len(cases)} faults={len(faults)} tries={tries}")
    for c in cases[:3]:
        print(" ", c["s0"], c["moves"], "black_moves_at_c=", c["n_black_moves_at_c"],
              "rep_move=", c["rep_move"])


if __name__ == "__main__":
    main()

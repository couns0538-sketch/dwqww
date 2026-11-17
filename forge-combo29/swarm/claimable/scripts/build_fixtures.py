#!/usr/bin/env python3
"""build_fixtures.py — construct and ASSERT every probe fixture with python-chess.

Nothing here is trusted until its assertion passes, so a broken fixture can never reach a
measurement (§7 trap 63-F8: three of seat 63's own fixtures were wrong and only assertions
caught them). Prints JSON; exits non-zero on any failed assertion.

The `claim` field states what the fixture is FOR and is asserted, so a fixture that does not
have the property it is named after fails here rather than in a report:

  mate            a mating move exists
  cp0_fifty       claimable by the fifty-move rule, no mate
  insuff          insufficient material
  cp0_no_reset    claimable, and NO legal move resets the clock
  searched        claimable, a clock-resetting move exists, no mate
  threefold_mate  a threefold root that also has a mating move
  None            control, no assertion beyond validity
"""
import json
import sys

import chess

OUT = []


def resets_of(b):
    """Moves that reset the fifty-move counter: pawn moves and captures."""
    out = []
    for m in b.legal_moves:
        piece = b.piece_at(m.from_square)
        if (piece and piece.piece_type == chess.PAWN) or b.is_capture(m):
            out.append(m.uci())
    return out


def add(name, fen, moves, claim):
    b = chess.Board(fen)
    assert b.is_valid(), f"{name}: invalid FEN {fen}"
    for mv in moves:
        m = chess.Move.from_uci(mv)
        assert m in b.legal_moves, f"{name}: move {mv} illegal at {b.fen()}"
        b.push(m)
    assert b.is_valid(), f"{name}: invalid root"
    mates, stales = [], []
    for m in b.legal_moves:
        c = b.copy()
        c.push(m)
        if c.is_checkmate():
            mates.append(m.uci())
        elif c.is_stalemate():
            stales.append(m.uci())
    insuff = b.is_insufficient_material()
    threefold = b.is_repetition(3)
    resets = resets_of(b)
    legal = b.legal_moves.count()

    if claim == "mate":
        assert mates, f"{name}: claim 'mate' but no mating move"
    elif claim == "cp0_fifty":
        assert b.halfmove_clock >= 100, f"{name}: clock {b.halfmove_clock} < 100"
        assert not mates, f"{name}: claim cp0 but a mate exists {mates}"
    elif claim == "insuff":
        assert insuff, f"{name}: not insufficient"
        assert not mates, f"{name}: insuff but a mate exists"
    elif claim == "cp0_no_reset":
        assert threefold or b.halfmove_clock >= 100, f"{name}: not claimable"
        assert not resets, f"{name}: claim 'no reset' but resets exist {resets[:5]}"
        assert not mates, f"{name}: claim cp0 but a mate exists {mates}"
    elif claim == "searched":
        assert threefold or b.halfmove_clock >= 100, f"{name}: not claimable"
        assert resets, f"{name}: claim 'searched' but no reset move exists"
        assert not mates, f"{name}: claim 'searched' but a mate exists"
    elif claim == "threefold_mate":
        assert threefold, f"{name}: not a threefold"
        assert mates, f"{name}: no mating move"
    elif claim is not None:
        raise AssertionError(f"{name}: unknown claim {claim}")

    OUT.append({"name": name, "fen": fen, "moves": moves, "claim": claim,
                "root_fen": b.fen(), "legal": legal, "mates": mates, "stalemates": stales,
                "insufficient": insuff, "threefold": threefold,
                "halfmove": b.halfmove_clock, "resets": resets,
                "material_white_minus_black": None})


# ---- seat 63's adversarial families ------------------------------------------------
add("A2_two_mates_h100", "8/8/8/8/8/8/1R2R3/K1k5 w - - 100 1", [], "mate")
add("B_single_mate_h100", "8/8/8/8/8/1R6/8/k1K5 w - - 100 1", [], "mate")
add("C_stalemate_not_mate_h100", "8/8/8/8/8/8/Q7/K1k5 w - - 100 1", [], "cp0_fifty")
add("D_check_not_mate_h100", "8/8/8/8/8/8/R7/K1k5 w - - 100 1", [], "cp0_fifty")
add("E_mate_in_2_h100", "8/8/8/8/2R5/k7/8/1K6 w - - 100 1", [], "cp0_fifty")
add("F_insuff_KBvK", "8/8/8/8/8/8/8/kBK5 w - - 0 1", [], "insuff")
add("F2_insuff_bishops", "8/8/8/8/8/8/2b5/kBK5 w - - 0 1", [], "insuff")
add("F3_KNNvK_mate", "8/8/8/8/8/4N3/3N4/K1k5 w - - 0 1", [], "mate")

# ---- the repetition path ----------------------------------------------------------
add("G_threefold_root", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 8 5",
    ["g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1", "f6g8"], "searched")
add("H_threefold_mate", "7n/8/8/8/8/1R6/2K5/k6N w - - 0 1",
    ["h1g3", "h8g6", "g3h1", "g6h8"] * 2, "threefold_mate")

# ---- the three cases the GENERAL claimable rule broke -----------------------------
add("X1_losing_side_threefold", "4k3/8/8/8/8/8/4P3/R3K3 w - - 0 40",
    ["a1a2", "e8d8", "a2a1", "d8e8", "a1a2", "e8d8", "a2a1", "d8e8", "a1a2"], "cp0_no_reset")
add("X2_clock100_no_reset", "4k3/8/8/8/8/8/8/R3K2r w - - 100 1", [], "cp0_no_reset")
add("X3_mate1_at_clock100", "6k1/5ppp/8/8/8/8/8/R5NK w - - 100 40", [], "mate")

# ---- the discriminating cases: a LOSING side that may still claim ------------------
# Black is down a queen for a rook. At a threefold, and at clock 100, black's claim is a
# draw and a draw is better than a loss, so cp 0 is the answer a claim produces.
Y1_MOVES = ["b8a8", "d1d2", "a8b8", "d2d1"] * 2
add("Y1_losing_side_threefold_reset", "1r4k1/pp6/8/8/8/8/P7/3Q2K1 b - - 0 40",
    Y1_MOVES, "searched")
add("Y2_clock100_reset_equal", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 100 60",
    [], "searched")
add("Y3_clock100_losing_reset", "1r4k1/pp6/8/8/8/8/P7/3Q2K1 b - - 100 40", [], "searched")

# ---- controls that must never move ------------------------------------------------
add("C1_KvK", "4k3/8/8/8/8/8/8/4K3 w - - 0 1", [], "insuff")
add("C2_winning_board", "4k3/8/8/8/8/8/4P3/R3K3 w - - 0 40", [], None)
add("C3_fifty99_reset_available", "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/RP2N1PP/3R2K1 w - - 99 1", [], None)
add("C4_startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", [], None)

json.dump(OUT, sys.stdout, indent=2)
print()

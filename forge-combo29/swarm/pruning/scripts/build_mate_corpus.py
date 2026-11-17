#!/usr/bin/env python3
"""Build a mate corpus whose every distance is verified by two independent oracles.

WHY THE DISTANCES ARE SHORT AND THE SEARCH DEPTHS ARE LONG
----------------------------------------------------------
The pruning classes under audit (null move, razoring, RFP, the shallow move-loop
block, LMR, singular extensions) fire inside the search TREE, not at the mate's
own distance. A mate in 2 searched at depth 12 builds a deep tree around the
mating line and exercises all of them; a mate in 5 searched at depth 5 exercises
almost nothing. So the corpus targets mates in 1-3 moves and the measurement
runs them at depths up to 12. This is also what makes generation affordable:
solving mate-in-5 from a random KQK position costs orders of magnitude more than
mate-in-2, and buys nothing the deep search does not already provide.

DESIGN CONSTRAINTS, EACH OF WHICH A NAIVE CORPUS WOULD FAIL
------------------------------------------------------------
* **Distances, not verdicts.** §4's documented class is "right move, wrong
  distance", so each entry stores the exact mate length in PLIES and the full
  set of first moves that achieve it.

* **Quiet mating moves are over-represented.** The pruning targets quiet,
  non-checking moves (futility, SEE, LMP, history, LMR). A corpus whose mating
  moves are all checks would skate past every one of them. Each entry records
  whether each mating move gives check / is a capture, and generation BIASES
  toward positions with at least one quiet mater.

* **Biased placement, not uniform random.** Uniform KQK is mostly long mates.
  Placing the bare king on the edge and the attacker's king close produces
  short forced mates at a usable rate.

* **Every FEN validated twice**: python-chess must parse it AND the engine must
  not refuse it (brief rule 4 — see `verify_corpus.py`).

* **Two oracles, both must agree.** Negamax and the structurally different
  layered solver. Disagreement DROPS the entry rather than picking a winner.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time

import chess

sys.path.insert(0, "scripts")
import mateoracle as mo  # noqa: E402

# Squares a bare king sits on: the whole board is allowed, but edges and corners
# are drawn far more often because that is where short forced mates live.
EDGE_SQUARES = [sq for sq in range(64) if chess.square_file(sq) in (0, 7) or chess.square_rank(sq) in (0, 7)]
CORNER_SQUARES = [chess.A1, chess.A8, chess.H1, chess.H8]


def attacker_squares_near(rng: random.Random, target: int, radius: int) -> list[int]:
    out = []
    tf, tr = chess.square_file(target), chess.square_rank(target)
    for sq in range(64):
        f, r = chess.square_file(sq), chess.square_rank(sq)
        if max(abs(f - tf), abs(r - tr)) <= radius and sq != target:
            out.append(sq)
    return out


def make_board(rng: random.Random, pieces: str) -> chess.Board | None:
    if rng.random() < 0.35:
        bk = rng.choice(CORNER_SQUARES)
    else:
        bk = rng.choice(EDGE_SQUARES)
    wk_candidates = attacker_squares_near(rng, bk, 3)
    if not wk_candidates:
        return None
    wk = rng.choice(wk_candidates)
    board = chess.Board(None)
    board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
    for ch in pieces:
        for _ in range(24):
            sq = chess.square(rng.randrange(64), 0)
            if board.piece_at(sq) is None:
                board.set_piece_at(sq, chess.Piece.from_symbol(ch))
                break
        else:
            return None
    board.turn = chess.WHITE
    board.clear_stack()
    if not board.is_valid():
        return None
    if board.is_checkmate() or board.is_stalemate() or board.is_insufficient_material():
        return None
    return board


def describe(board: chess.Board, move: chess.Move) -> dict:
    gives_check = board.gives_check(move)
    is_capture = board.is_capture(move)
    is_promo = move.promotion is not None
    return {
        "uci": move.uci(),
        "gives_check": gives_check,
        "is_capture": is_capture,
        "is_promotion": is_promo,
        "quiet": not gives_check and not is_capture and not is_promo,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="corpus/mates.json")
    ap.add_argument("--seed", type=int, default=20261117)
    ap.add_argument("--per-band", type=int, default=24)
    ap.add_argument("--max-plies", type=int, default=5, help="5 = mate in <= 3 moves")
    ap.add_argument("--budget-seconds", type=float, default=900.0)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    started = time.time()
    bands: dict[int, list[dict]] = {}
    stats = {"candidates": 0, "rejected_invalid": 0, "no_short_mate": 0,
             "skipped_band_full": 0}

    mats = ("Q", "R", "QR", "RR", "QQ", "RQ")
    full_bands = set(range(1, args.max_plies + 1, 2))
    while time.time() - started < args.budget_seconds:
        if all(len(bands.get(p, [])) >= args.per_band * 2 for p in full_bands):
            break
        mat = rng.choice(mats)
        board = make_board(rng, mat)
        if board is None:
            stats["rejected_invalid"] += 1
            continue
        stats["candidates"] += 1
        d = mo.solve_negamax(board, args.max_plies)
        if d <= 0:
            stats["no_short_mate"] += 1
            continue
        if len(bands.get(d, [])) >= args.per_band * 2:
            stats["skipped_band_full"] += 1
            continue
        movers = mo.mating_moves(board, d)
        if not movers:
            continue
        bands.setdefault(d, []).append({
            "fen": board.fen(),
            "plies": d,
            "moves_to_mate": d // 2 + (d % 2),
            "material": mat,
            "mating_moves": [describe(board, m) for m in movers],
        })

    chosen: list[dict] = []
    for plies in sorted(bands):
        items = bands[plies][:]
        rng.shuffle(items)
        quiet_first = [x for x in items if any(m["quiet"] for m in x["mating_moves"])]
        pick = quiet_first[: args.per_band]
        if len(pick) < args.per_band:
            rest = [x for x in items if all(x is not y for y in pick)]
            pick.extend(rest[: args.per_band - len(pick)])
        chosen.extend(pick)

    # Cross-check every survivor against the second, structurally different oracle.
    verified, rejected = [], []
    for e in chosen:
        b = chess.Board(e["fen"])
        a = mo.solve_negamax(b, e["plies"])
        c = mo.solve_layered(b, e["plies"])
        if a == c == e["plies"]:
            e["oracle"] = "negamax+layered agree"
            verified.append(e)
        else:
            rejected.append({"fen": e["fen"], "negamax": a, "layered": c,
                             "listed": e["plies"]})

    with open(args.out, "w") as fh:
        json.dump({"seed": args.seed, "max_plies": args.max_plies,
                   "generation_stats": stats,
                   "generation_seconds": round(time.time() - started, 1),
                   "entries": verified,
                   "rejected_by_crosscheck": rejected}, fh, indent=2)

    by_plies: dict[int, int] = {}
    for e in verified:
        by_plies[e["plies"]] = by_plies.get(e["plies"], 0) + 1
    print(json.dumps({
        "generation_stats": stats,
        "generation_seconds": round(time.time() - started, 1),
        "total_verified": len(verified),
        "rejected_by_crosscheck": len(rejected),
        "by_plies": by_plies,
        "with_a_quiet_mating_move": sum(
            1 for e in verified if any(m["quiet"] for m in e["mating_moves"])),
        "with_only_checking_matings": sum(
            1 for e in verified if all(m["gives_check"] for m in e["mating_moves"])),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

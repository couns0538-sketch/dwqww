#!/usr/bin/env python3
"""How WIDE is the overclaim class? A single instance is an anecdote.

Searches generated endgames for `go mate N` reporting `mate M` with M > N. The
generator is the same programmatic one the corpus uses, so nothing is typed by
hand. Every hit is re-verified with the oracle: the reported distance, the true
distance, and whether the reported MOVE still forces the mate at all.

The result is reported as a RATE with its denominator, because "1 in N requests"
and "1 in N positions" are different claims and the assignment's whole point is
that an outlier needs a distribution around it.

Usage: run_overclaim_scan.py --exe build/forge --out overclaim_scan.json [--positions 400]
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucipipe import Engine  # noqa: E402
from mateoracle import Oracle, pv_replays_to_mate  # noqa: E402

SETS = [
    ("KQvK",   [chess.QUEEN],                    []),
    ("KRvK",   [chess.ROOK],                     []),
    ("KQvKR",  [chess.QUEEN],                    [chess.ROOK]),
    ("KRRvK",  [chess.ROOK, chess.ROOK],         []),
    ("KQvKP",  [chess.QUEEN],                    [chess.PAWN]),
    ("KRvKN",  [chess.ROOK],                     [chess.KNIGHT]),
    ("KBBvK",  [chess.BISHOP, chess.BISHOP],     []),
    ("KQRvKR", [chess.QUEEN, chess.ROOK],        [chess.ROOK]),
    ("KQRvK",  [chess.QUEEN, chess.ROOK],        []),
]


def gen(rng: random.Random, n: int) -> list[tuple[str, str]]:
    out = []
    seen = set()
    tries = 0
    while len(out) < n and tries < n * 400:
        tries += 1
        name, white, black = SETS[rng.randrange(len(SETS))]
        squares = rng.sample(range(64), 2 + len(white) + len(black))
        b = chess.Board(None)
        b.set_piece_at(squares[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(squares[1], chess.Piece(chess.KING, chess.BLACK))
        i = 2
        ok = True
        for color, pieces in ((chess.WHITE, white), (chess.BLACK, black)):
            for pt in pieces:
                b.set_piece_at(squares[i], chess.Piece(pt, color))
                i += 1
        b.turn = chess.WHITE
        b.castling_rights = chess.BB_EMPTY
        b.ep_square = None
        b.halfmove_clock = 0
        b.fullmove_number = 1
        if not b.is_valid() or b.is_check() or b.legal_moves.count() == 0:
            continue
        fen = b.fen(en_passant="fen")
        if fen in seen:
            continue
        seen.add(fen)
        out.append((name, fen))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="build/forge")
    ap.add_argument("--out", required=True)
    ap.add_argument("--positions", type=int, default=400)
    ap.add_argument("--seed", type=int, default=7345)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    positions = gen(rng, args.positions)
    print(f"{len(positions)} generated endgames, seed {args.seed}")

    hits = []
    requests = 0
    scored = 0
    with Engine(args.exe, {"OwnBook": "false"}) as eng:
        for idx, (mat, fen) in enumerate(positions):
            board = chess.Board(fen)
            for n in (2, 3, 4):
                eng.newgame()
                eng.setpos(fen)
                res = eng.go(f"go mate {n}", timeout=120)
                requests += 1
                sc = res.last_score
                if not sc or sc[0] != "mate" or sc[1] is None:
                    continue
                scored += 1
                if sc[1] <= n:
                    continue
                # A candidate overclaim. Settle it with the oracle.
                o = Oracle(node_budget=20_000_000)
                try:
                    exact = o.exact_dtm_up_to(board, 8)
                except Exception:                        # noqa: BLE001
                    exact = None
                replay = pv_replays_to_mate(board, res.last_pv) if sc[1] > 0 else (None, "")
                hits.append({
                    "material": mat, "fen": fen, "n": n,
                    "reported_mate": sc[1], "reported_plies": 2 * sc[1] - 1,
                    "depth": res.last_depth, "nodes": res.last_nodes,
                    "bestmove": res.bestmove, "pv": res.last_pv, "pv_len": len(res.last_pv),
                    "oracle_exact_dtm_plies": exact,
                    "oracle_exact_dtm_moves": (exact + 1) // 2 if exact else None,
                    "pv_replays_to_mate": replay[0], "pv_detail": replay[1],
                })
                print(f"  HIT {mat} N={n} -> mate {sc[1]} (implies {2*sc[1]-1} plies, "
                      f"PV {len(res.last_pv)}, truth {exact}) {fen}", flush=True)
            if (idx + 1) % 50 == 0:
                print(f"  ... {idx+1}/{len(positions)}, {requests} requests, "
                      f"{len(hits)} hits", flush=True)

    print(f"\nrequests {requests}; mate-scored cells {scored}; "
          f"overclaims (M > N) {len(hits)}  rate {len(hits)}/{requests}")
    by_n = {}
    for h in hits:
        by_n.setdefault(h["n"], 0)
        by_n[h["n"]] += 1
    print(f"by requested N: {by_n}")
    json.dump({"seed": args.seed, "positions": len(positions), "requests": requests,
               "mate_scored": scored, "hits": hits}, open(args.out, "w"), indent=1)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

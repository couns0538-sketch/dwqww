"""Generate mate corpus candidates by BFS over random-play leaves, then grade.

Why generated and then graded rather than hand-written: hand-writing a mate in 4
is error-prone (this seat got two fixtures wrong by hand before switching), and a
corpus of only mate-in-1 positions cannot exercise a ply adjustment at all --
a mate at distance 1 is stored as MATE-1 at every ply and an absent adjustment
still reports "mate 1". The corpus NEEDS long mates to have any power.

Every candidate is graded by the oracle in this seat; nothing is admitted on the
strength of its provenance.

Output: evidence/candidates.json  (graded, with the reject reasons)
"""

from __future__ import annotations

import json
import random
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from oracle import solve  # noqa: E402

# A small, deliberately endgame-heavy set of seeds. Short mates live in sparse
# positions, so random play from these reaches forced mates far more often than
# random play from the opening does.
SEEDS = [
    "8/8/8/8/8/8/8/k1K5 w - - 0 1",
    "8/8/8/8/8/8/8/k1K4R w - - 0 1",
    "8/8/8/8/8/2K5/8/1k5 w - - 0 1",
    "k7/8/1K6/8/8/8/8/7R w - - 0 1",
    "8/8/8/8/8/1K6/8/k6R w - - 0 1",
    "7k/8/6K1/8/8/8/8/7R w - - 0 1",
    "8/8/8/8/8/8/6K1/1k5R w - - 0 1",
    "2k5/8/2K5/8/8/8/8/7R w - - 0 1",
    "8/8/8/8/8/8/1R2R3/K1k5 w - - 0 1",
    "7k/5Q2/6K1/8/8/8/8/8 w - - 0 1",
    "8/8/8/8/8/8/8/k1K2Q2 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1",
    "8/8/8/3k4/8/3K4/8/6R1 w - - 0 1",
    "8/8/8/4k3/8/4K3/8/7R w - - 0 1",
]


def random_leaves(seed_fen, n_games, plies, rng, max_moves=4):
    """Random walks from a seed; yield the position at each ply."""
    out = []
    for _ in range(n_games):
        board = chess.Board(seed_fen)
        for ply in range(plies):
            if board.is_game_over():
                break
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
            if ply >= plies // 2 and not board.is_game_over():
                out.append(board.fen())
    return out


def main():
    rng = random.Random(20261117)
    seen = set()
    candidates = []
    for seed in SEEDS:
        try:
            b = chess.Board(seed)
        except ValueError:
            continue
        if not b.is_valid():
            continue
        for fen in random_leaves(seed, n_games=25, plies=8, rng=rng):
            if fen in seen:
                continue
            seen.add(fen)
            candidates.append(fen)

    graded = []
    reject = {"no_mate": 0, "too_long": 0, "exhausted": 0, "terminal": 0, "invalid": 0}
    import time
    t0 = time.time()
    for idx, fen in enumerate(candidates):
        if idx % 200 == 0:
            print(f"  [{idx}/{len(candidates)}] {time.time()-t0:.0f}s graded={len(graded)} reject={reject}", flush=True)
        board = chess.Board(fen)
        if not board.is_valid():
            reject["invalid"] += 1
            continue
        if board.is_game_over():
            reject["terminal"] += 1
            continue
        sol = solve(board, max_moves=4, node_cap=2_000_000)
        if sol["exhausted"]:
            reject["exhausted"] += 1
            continue
        if sol["kind"] is None:
            reject["no_mate"] += 1
            continue
        if sol["moves"] is None or sol["moves"] > 4:
            reject["too_long"] += 1
            continue
        graded.append({
            "fen": fen,
            "kind": sol["kind"],
            "moves": sol["moves"],
            "plies": sol["plies"],
            "pieces": len(board.piece_map()),
            "legal": board.legal_moves.count(),
        })

    graded.sort(key=lambda r: (r["kind"], r["moves"], r["pieces"]))
    out = {
        "seeds": len(SEEDS),
        "candidates": len(candidates),
        "graded": len(graded),
        "reject": reject,
        "fixtures": graded,
    }
    with open(__file__.rsplit("/", 2)[0] + "/evidence/candidates.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps({k: v for k, v in out.items() if k != "fixtures"}, indent=2))
    by = {}
    for r in graded:
        by[f"{r['kind']}_{r['moves']}"] = by.get(f"{r['kind']}_{r['moves']}", 0) + 1
    print("by distance:", json.dumps(by))
    for r in graded[:20]:
        print(f"  {r['fen'][:52]:54s} {r['kind']} {r['moves']} ({r['pieces']}p, {r['legal']} moves)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

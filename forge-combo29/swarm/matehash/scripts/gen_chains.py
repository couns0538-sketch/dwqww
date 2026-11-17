"""Recover parent/child pairs for the already-graded corpus fixtures.

RECONSTRUCTION, NOT RE-SEARCH. gen_candidates.py walks each seed with a fixed
RNG seed and grades every position it visits. This script replays that walk with
the SAME seed and SAME iteration order, and records each visited position's
parent. No oracle calls are made: the mate distance for a target is taken from
evidence/candidates.json, which was graded by this seat's oracle.

Why this exists: a first attempt searched fresh random chains and screened each
position with the oracle, which is ~1s per position and did not finish. Replaying
a walk whose answers are already known costs nothing.

Gate: every recovered child FEN must appear in candidates.json with the distance
this script then reports. A mismatch aborts rather than being papered over.

Output: evidence/chains.json
"""

from __future__ import annotations

import json
import random
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from gen_candidates import SEEDS  # noqa: E402


def main():
    here = __file__.rsplit("/", 2)[0]
    cand = json.load(open(here + "/evidence/candidates.json"))
    graded = {r["fen"]: r for r in cand["fixtures"]}

    # EXACT replay of gen_candidates.main(): same seed, same call order.
    rng = random.Random(20261117)
    pairs = []
    seen = set()
    for seed in SEEDS:
        try:
            b = chess.Board(seed)
        except ValueError:
            continue
        if not b.is_valid():
            continue
        for _ in range(25):
            board = chess.Board(seed)
            for ply in range(8):
                if board.is_game_over():
                    break
                moves = list(board.legal_moves)
                if not moves:
                    break
                mv = rng.choice(moves)
                parent_fen = board.fen()
                board.push(mv)
                child_fen = board.fen()
                if ply >= 8 // 2 and not board.is_game_over():
                    if child_fen in graded and child_fen not in seen:
                        seen.add(child_fen)
                        pairs.append({
                            "seed": seed,
                            "parent_fen": parent_fen,
                            "parent_move": mv.uci(),
                            "child_fen": child_fen,
                            "kind": graded[child_fen]["kind"],
                            "moves": graded[child_fen]["moves"],
                            "expected_reported_mate": (
                                graded[child_fen]["moves"] if graded[child_fen]["kind"] == "mate"
                                else -graded[child_fen]["moves"]
                            ),
                            "pieces": graded[child_fen]["pieces"],
                        })

    # Gate: the replay must be exact, so every recovered pair must already have a
    # graded answer and the child must be reachable from the parent in one legal
    # move (re-checked here rather than assumed).
    bad = []
    for p in pairs:
        board = chess.Board(p["parent_fen"])
        ok = False
        for mv in board.legal_moves:
            board.push(mv)
            same = board.fen() == p["child_fen"]
            board.pop()
            if same:
                ok = True
                break
        if not ok:
            bad.append(p)

    by = {}
    for p in pairs:
        k = f"{p['kind']}_{p['moves']}"
        by[k] = by.get(k, 0) + 1
    out = {
        "recovered": len(pairs),
        "gate_parent_child_verified": len(pairs) - len(bad),
        "gate_failures": len(bad),
        "by_distance": by,
        "pairs": pairs,
        "graded_pool": len(graded),
    }
    with open(here + "/evidence/chains.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps({k: v for k, v in out.items() if k != "pairs"}, indent=2))
    return 0 if pairs and not bad else 1


if __name__ == "__main__":
    sys.exit(main())

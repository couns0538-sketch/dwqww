#!/usr/bin/env python3
"""Job 3 B1/B6 scoring: compare the engine's `score mate N` with brute-force truth.

Truth (from b_truth.py) is in PLIES; the engine reports MOVES. A truth of +3 plies is
"mate 2" to the engine; -2 plies is "mate -1".

For each position this checks:
  * the mate distance in the last `info ... score mate N` matches the truth,
  * the bestmove is legal,
  * the bestmove keeps the shortest mate (brute force over the resulting position),
and records every miss in full.

Usage: b1_score.py <truth.json> <key> <results.json> <out.json>
"""
import json
import sys

import chess

sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/tests_deepseek_job3")
import b_truth as T


def shortest_mate_after(board, plies):
    """Best mate value for the OPPONENT after the move `board` is in: returns plies.

    After the mover's move it is the opponent to move, so the value is negated.
    """
    v = T.mate_in(board, plies)
    return v


def main():
    truth_path, key, results_path, out_path = sys.argv[1:5]
    with open(truth_path) as f:
        truth = json.load(f)
    fens = truth[key]
    with open(results_path) as f:
        results = json.load(f)["results"]

    if len(fens) != len(results):
        raise SystemExit(f"{len(fens)} truth FENs vs {len(results)} results")

    # Expected engine mate value in MOVES for each class.
    expected_moves = {"mate2": 1, "mate3": 2, "mated2": -1}[key]
    expected_plies = {"mate2": 2, "mate3": 3, "mated2": -2}[key]

    misses = []
    passed = 0
    for fen, r in zip(fens, results):
        problems = []
        score = r.get("score")
        if score is None or score.get("kind") != "mate":
            problems.append(f"no mate score (last info: {r.get('last_info')})")
        elif score["value"] != expected_moves:
            problems.append(f"reported mate {score['value']}, truth mate {expected_moves}")
        if not r.get("legal"):
            problems.append(f"bestmove {r.get('bestmove')} not legal")
        else:
            # Does the bestmove keep the shortest mate?
            board = chess.Board(fen)
            move = chess.Move.from_uci(r["bestmove"])
            board.push(move)
            # After our move the opponent is to move; truth says we mate in
            # expected_plies, so the child must be "opponent mated in expected_plies-1".
            child = T.mate_in(board, max(1, expected_plies - 1))
            if expected_plies > 0:
                want_child = -(expected_plies - 1) if expected_plies > 1 else -1
                if child is None or child > 0 or child != want_child:
                    problems.append(f"bestmove {r['bestmove']} does not keep mate in "
                                    f"{expected_plies} plies (child truth {child})")
        if problems:
            misses.append({"fen": fen, "bestmove": r.get("bestmove"),
                           "last_info": r.get("last_info"), "truth_plies": expected_plies,
                           "problems": problems})
        else:
            passed += 1

    out = {"class": key, "positions": len(fens), "passed": passed,
           "failed": len(misses), "expected_engine_mate_moves": expected_moves,
           "expected_truth_plies": expected_plies, "misses": misses}
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "misses"}, sort_keys=True))
    for m in misses[:5]:
        print("  MISS", m["fen"], "|", m["problems"])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Predict the bail from the sent move list alone (python-chess), then compare with the
engine's actual replies. Threefold is counted over the replay's own start position plus
the prefix, which is exactly what the engine's board history holds.

python-chess is NOT treated as an oracle here: it is a predictor, and any disagreement is
inspected rather than scored. Its repetition rule ("has this FEN occurred before") and the
engine's (`matches >= 2` inside the reversible window) are counted the same way here, over
position keys, with the ep-square caveat noted in FINDINGS.
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evio import load_json, load_plies
import chess
from chesskeys import repetition_key

corpus = {g["id"]: g for g in load_json("games")["games"]}


def load(name):
    """Per-ply records keyed by (game, ply), from the committed short-key evidence."""
    return load_plies(name)


def walk(g):
    """Yield (ply_number, fen_after_that_many_moves, occurrence_count_of_that_position).

    The engine's `position fen <start> moves <prefix>` for prefix length k puts the board
    at the position after k moves, so the yield must come AFTER the push. An earlier
    version yielded before the push and lagged the engine by one ply.
    """
    board = chess.Board(g["start_fen"])
    counts = {}
    counts[repetition_key(board)] = 1
    for i, mv in enumerate(g["moves"], 1):
        board.push(chess.Move.from_uci(mv))
        k = repetition_key(board)
        counts[k] = counts.get(k, 0) + 1
        yield i, board.copy(), counts[k]


def main():
    sess = load("session")
    rows = []
    for gid, g in corpus.items():
        for ply, board, occ in walk(g):
            r = sess[(gid, ply)]
            observed = (r["nodes"] == 0 and r["npv"] == 0 and r["bm"] not in (None, "0000"))
            if board.legal_moves.count() == 0:
                continue  # checkmate or stalemate: a terminal root, no move to choose
            pred_rep = occ >= 3
            pred_hm = board.halfmove_clock >= 100
            pred_ins = board.is_insufficient_material()
            pred = pred_rep or pred_hm or pred_ins
            rows.append({"game": gid, "ply": ply, "occ": occ,
                         "halfmove": board.halfmove_clock,
                         "pred": pred, "pred_rep": pred_rep, "pred_hm": pred_hm,
                         "pred_ins": pred_ins, "observed": observed,
                         "eng_bm": r["bm"], "eng_score": r["score"]})
    # Keep only the rows that matter: every predicted position and every observed bail. The
    # full 27,692-row dump is 5 MB of agree-with-me and is not worth committing; summary.py
    # filters on the same predicate, so either shape works.
    kept = [r for r in rows if r["pred"] or r["observed"]]
    json.dump(kept, open("evidence/bail_predict.json", "w", encoding="utf-8"))

    n = len(rows)
    obs = [r for r in rows if r["observed"]]
    pred = [r for r in rows if r["pred"]]
    agree = sum(1 for r in rows if r["pred"] == r["observed"])
    print(f"positions: {n}  observed bails: {len(obs)}  predicted: {len(pred)}  agree: {agree} ({100*agree/n:.3f}%)")
    print("observed but not predicted:", [(r['game'], r['ply'], r['occ'], r['halfmove']) for r in obs if not r['pred']])
    print("predicted but not observed:", [(r['game'], r['ply'], r['occ'], r['halfmove'], r['pred_rep'], r['pred_hm'], r['pred_ins'], r['eng_bm'], r['eng_score']) for r in rows if r['pred'] and not r['observed']][:20])
    print("max occurrence count observed at any non-terminal ply:",
          max(r["occ"] for r in rows), " positions with occ>=3:", sum(1 for r in rows if r["occ"] >= 3))
    print("max halfmove:", max(r["halfmove"] for r in rows))


if __name__ == "__main__":
    main()

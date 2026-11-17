"""Fixture validation: python-chess validity AND engine acceptance.

Two independent gates, because trap 4 says a refused FEN manufactures a pass:
  - python-chess is not a neutral oracle (brief rule 5), so it only rejects what
    it can see is illegal;
  - the engine reports `invalid FEN` on the `position` command, so the driver's
    diagnostic list is checked for it as well.
"""
import json
import os
import sys

import chess

import uci

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "evidence")


def check():
    spec = json.load(open(os.path.join(HERE, "positions.json")))
    rows = []
    bad = 0
    for group in ("positions", "draw_bail"):
        for name, fen in spec[group]:
            row = {"group": group, "name": name, "fen": fen}
            board = chess.Board(fen)
            row["python_chess_valid"] = board.is_valid()
            row["legal_moves"] = board.legal_moves.count()
            r = uci.run(options=[("OwnBook", "false")], position=fen, go="go depth 6")
            refusal = [d for d in r["diag"] if "invalid FEN" in d or "illegal" in d.lower()]
            row["engine_refused"] = bool(refusal)
            row["engine_refusal_text"] = refusal
            row["bestmove"] = r["bestmove"]
            row["nodes"] = r["nodes"]
            # trap 10 tell: the same answer for every board
            rows.append(row)
            if not row["python_chess_valid"] or row["engine_refused"] or not r["bestmove"]:
                bad += 1
    for name, cmd in spec["draw_bail_movelist"]:
        r = uci.run(options=[("OwnBook", "false")], position=cmd, go="go depth 6")
        refusal = [d for d in r["diag"] if "invalid FEN" in d or "illegal" in d.lower()]
        rows.append({"group": "draw_bail_movelist", "name": name, "command": cmd,
                     "python_chess_valid": True, "engine_refused": bool(refusal),
                     "engine_refusal_text": refusal, "bestmove": r["bestmove"], "nodes": r["nodes"]})
        if refusal or not r["bestmove"]:
            bad += 1
    answers = [r["bestmove"] for r in rows if r["group"] in ("positions",)]
    distinct = len(set(answers))
    result = {"rows": rows, "invalid_or_refused": bad, "distinct_answers_on_positions": distinct}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "positions-check.json"), "w") as fh:
        json.dump(result, fh, indent=1)
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=1))
    for r in rows:
        print(f"{r['group']:22s} {r['name']:30s} nodes={str(r['nodes']):>7s} best={r['bestmove']}")
    # A uniform answer across 12 unrelated boards is trap 10's tell, not a pass.
    return bad == 0 and distinct >= 8


if __name__ == "__main__":
    sys.exit(0 if check() else 1)

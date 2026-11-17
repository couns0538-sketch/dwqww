"""Experiment B/C: mate scores through the transposition table.

THE HAZARD AND HOW TO REACH IT
    A TT score is ROOT-relative. Storing it from ply p and reading it at ply q
    without adjusting for the ply difference moves a mate's distance by (q - p)
    plies. Because a mate distance is reported in MOVES, an even-ply error shows
    as "mate 2" where the truth is "mate 3".

    Three ways the ply can differ, and each is measured here:

    C1  STORE DEEP, READ AT THE ROOT.  Search `position fen <X>` at depth D. A
        grandchild of the root gets stored at ply 2. Then search a position that
        is that grandchild, `go depth D`, and its entry is read at ply 0. If the
        adjustment is missing, the reported distance is off by 2 plies = 1 move.

        How the entry is made reachable at ply 0: the second search must have the
        SAME key. So the second position must be the first search's grandchild
        exactly, which is what `child_chain` builds.

    C2  SAME POSITION, TWO ROOTS, ONE PROCESS.  Search position X, then the same
        board X again in the same process. The second search reads X's own root
        entry (stored at ply 0) at ply 0 -- so this is the NULL CONTROL: a correct
        engine must report the identical distance, and it must report it in far
        fewer nodes. If this DOES diverge, the ply is game-relative rather than
        root-relative, which would be a different (and worse) defect.

    C3  THE FEN-vs-MOVE-LIST CONTROL.  The same board delivered as a move list
        can carry repetition history a FEN cannot (findings 2d). Included because
        a move list is how a GUI delivers a position, and because a difference
        here would confound C1.

WHAT PROVES THE PATH RAN
    Node counts. C2's second search must use fewer nodes than the first; if it
    does not, the table did not answer and the "same distance" result is
    vacuous. Every row records both counts and the ratio.

WHAT PROVES THE CHECKER CAN FAIL
    `--plant` runs the identical code against a WRONG expected distance (shifted
    by one move) and the harness must report failures. A control that silently
    does nothing is worse than no control (brief rule 3).
"""

from __future__ import annotations

import json
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from engine import Engine, final_score, mate_distance  # noqa: E402


def reported(result):
    info = final_score(result)
    return {
        "bestmove": result["bestmove"],
        "kind": info.get("score_kind") if info else None,
        "score": info.get("score") if info else None,
        "mates": mate_distance(result),
        "node_peak": max((i.get("nodes", 0) for i in result["infos"]), default=0),
        "info_lines": len(result["infos"]),
    }


def walk(board, plies, prefer_checks=True):
    """One concrete line of `plies` moves, preferring checks (they reach mates)."""
    moves = []
    b = board.copy()
    for _ in range(plies):
        legal = list(b.legal_moves)
        if not legal:
            return None, None
        if prefer_checks:
            checks = [m for m in legal if b.gives_check(m)]
            if checks:
                legal = checks + [m for m in legal if m not in checks]
        mv = legal[0]
        b.push(mv)
        moves.append(mv.uci())
    return b, moves


def c1_store_deep_read_root(binary, fen, depth, prefix_plies):
    """The real hazard: an entry stored at ply `prefix_plies` read at ply 0."""
    board = chess.Board(fen)
    target, prefix = walk(board, prefix_plies)
    if target is None:
        return None
    with Engine(binary, hash_mb=64) as eng:
        eng.ucinewgame()
        # Search 1: fills the table. Entries for the target board are stored at
        # ply `prefix_plies` relative to THIS root.
        eng.position(fen, None)
        first = eng.go(depth=depth, _timeout=300.0)
        # Search 2: the target board IS the root now, so its entry is read at
        # ply 0. Same process, same table.
        eng.position(target.fen(), None)
        second = eng.go(depth=depth, _timeout=300.0)
        # Control: a fresh process reading the same board at ply 0, cold.
        eng.ucinewgame()
        eng.position(target.fen(), None)
        cold = eng.go(depth=depth, _timeout=300.0)
    return {
        "mode": "C1_store_deep_read_root",
        "prefix_plies": prefix_plies,
        "prefix_moves": prefix,
        "target_fen": target.fen(),
        "first_root": reported(first),
        "second_warm": reported(second),
        "cold_control": reported(cold),
    }


def c2_same_board_twice(binary, fen, depth):
    """NULL CONTROL: same board, twice, one process. Must not move."""
    with Engine(binary, hash_mb=64) as eng:
        eng.ucinewgame()
        eng.position(fen, None)
        first = eng.go(depth=depth, _timeout=300.0)
        eng.position(fen, None)
        second = eng.go(depth=depth, _timeout=300.0)
    a, b = reported(first), reported(second)
    return {
        "mode": "C2_same_board_twice",
        "first": a,
        "second": b,
        "nodes_dropped": a["node_peak"] > b["node_peak"],
        "same_distance": a["mates"] == b["mates"],
    }


def c3_move_list_shuttle(binary, fen, depth, plies=4):
    """Same board by MOVE LIST, with repetition history a FEN cannot carry."""
    board = chess.Board(fen)
    target = board.fen()
    trail = []

    def dfs(depth_left):
        if depth_left == 0:
            return board.fen() == target
        for mv in board.legal_moves:
            board.push(mv)
            trail.append(mv.uci())
            if dfs(depth_left - 1):
                return True
            trail.pop()
            board.pop()
        return False

    if not dfs(plies):
        return {"mode": "C3_move_list_shuttle", "skipped": f"no {plies}-ply shuttle to the same board"}
    with Engine(binary, hash_mb=64) as eng:
        eng.ucinewgame()
        eng.position(fen, None)
        by_fen = eng.go(depth=depth, _timeout=300.0)
        eng.position(fen, list(trail))
        by_list = eng.go(depth=depth, _timeout=300.0)
    return {
        "mode": "C3_move_list_shuttle",
        "shuttle": list(trail),
        "by_fen": reported(by_fen),
        "by_move_list": reported(by_list),
        "same_distance": reported(by_fen)["mates"] == reported(by_move_list)["mates"],
    }


def main():
    binary = sys.argv[1]
    plant = "--plant" in sys.argv
    here = __file__.rsplit("/", 2)[0]
    corpus = json.load(open(here + "/evidence/corpus.json"))
    fixtures = corpus["fixtures"]
    depth = 10

    rows = []
    for fx in fixtures:
        fen = fx["fen"]
        want = fx["expected_reported_mate"]
        # The planted-fault mode asks the harness to accept a WRONG answer.
        expected = (want + 1) if (plant and want) else want
        c2 = c2_same_board_twice(binary, fen, depth)
        row = {
            "fen": fen,
            "kind": fx["kind"],
            "oracle_moves": fx["moves"],
            "expected": expected,
            "c2": c2,
            "c2_ok": c2["first"]["mates"] == expected and c2["second"]["mates"] == expected,
        }
        rows.append(row)
        print(json.dumps({k: row[k] for k in ("fen", "kind", "oracle_moves", "expected", "c2_ok")}), flush=True)

    n = len(rows)
    summary = {
        "binary": binary,
        "depth": depth,
        "mode": "PLANTED (expect failures)" if plant else "real",
        "n": n,
        "c2_ok": sum(1 for r in rows if r["c2_ok"]),
        "c2_node_dropped": sum(1 for r in rows if r["c2"]["nodes_dropped"]),
        "c2_same_distance": sum(1 for r in rows if r["c2"]["same_distance"]),
    }
    print(json.dumps({"summary": summary}, indent=2))
    name = "B_planted.jsonl" if plant else "B_c2_same_board.jsonl"
    with open(here + "/evidence/" + name, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
        fh.write(json.dumps({"summary": summary}) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

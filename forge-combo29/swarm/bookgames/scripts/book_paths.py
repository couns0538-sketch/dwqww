"""Exhaustive structural test of the book graph, with a planted-cycle control.

Claims this establishes over ALL book lines rather than a sample:

  Q2a  Every book line is finite and its length is bounded.
  Q2b  No book line can reach a threefold repetition or a 50-move draw *while
       still in book*. A repetition needs the same POSITION three times, and a
       repeated position is a cycle in the position graph.
  Q2c  The detector that reports "no cycle" can report a cycle. Demonstrated by
       planting one (a real edge plus its own reverse, which is the shape of an
       A -> B -> A shuffle). Without that control, "no cycle" is
       indistinguishable from a checker that never fires.
  Q2d  The detector does not fire on a DAG with a diamond (two paths into one
       node). This is the false-positive control, and it exists because the
       first version of this script DID fire on this book's diamonds -- see
       FINDINGS.md. A cycle checker that reports diamonds as cycles would have
       produced a false repetition warning on a sound book.

Position identity is python-chess's own transposition key (placement, side,
castling, en passant), which is the identity the repetition rule uses. Using
the full FEN instead would treat two repeats as different positions, because
the counters differ -- that would hide a real repetition.
"""

from __future__ import annotations

import json
import sys

import chess
import chess.polyglot

import book_graph as bg


def pos_key(board: chess.Board) -> tuple:
    """Position identity exactly as the repetition rule defines it.

    python-chess's key is (placement, side, castling, ep) and its ep field is set
    to None unless `has_legal_en_passant()` -- i.e. it already applies FIDE's
    rule that an ep right which cannot be exercised does not distinguish
    positions. So one key is enough; there is no looser rule to check against.
    Using the full FEN instead would treat repeats as different positions
    because the counters differ, which would hide a real repetition.
    """
    return board._transposition_key()


def build_adjacency(book_path: str):
    """Exhaustive walk over legal book moves, indexed by position identity."""
    entries = bg.load_book(book_path)
    by_key: dict[int, list[tuple[int, int]]] = {}
    for key, move, weight in entries:
        by_key.setdefault(key, []).append((move, weight))

    start = chess.Board()
    index: dict[tuple, int] = {pos_key(start): 0}
    boards: list[chess.Board] = [start]
    fens: list[str] = [start.fen()]
    plies: list[int] = [0]
    edges: list[tuple[int, int, str, int]] = []

    cursor = 0
    while cursor < len(boards):
        board = boards[cursor]
        idx = cursor
        cursor += 1
        for encoded, weight in by_key.get(chess.polyglot.zobrist_hash(board), []):
            mv = bg.decode(board, encoded)
            if mv is None or not board.is_legal(mv):
                raise SystemExit(f"illegal book move {mv} in {board.fen()}")
            child = board.copy()
            child.push(mv)
            ckey = pos_key(child)
            if ckey not in index:
                index[ckey] = len(boards)
                boards.append(child)
                fens.append(child.fen())
                plies.append(plies[idx] + 1)
            edges.append((idx, index[ckey], mv.uci(), weight))
    return by_key, index, boards, fens, plies, edges


def analyse(graph: dict[int, set[int]], root: int) -> dict:
    """Iterative DFS: returns any cycle and the longest path from `root`.

    A node is reported as a cycle only when its successor is GREY, i.e. on the
    current DFS stack -- not merely visited. A DAG diamond reaches an already
    BLACK successor and is not reported.
    """
    WHITE, GREY, BLACK = 0, 1, 2
    colour: dict[int, int] = {}
    order: list[int] = []
    cycle: list[int] | None = None
    path: list[int] = []

    for startnode in graph:
        if colour.get(startnode, WHITE) != WHITE:
            continue
        stack: list[tuple[int, int]] = [(startnode, 0)]
        while stack and cycle is None:
            node, idx = stack[-1]
            if idx == 0:
                colour[node] = GREY
                path.append(node)
            succ = sorted(graph.get(node, ()))
            if idx < len(succ):
                stack[-1] = (node, idx + 1)
                nxt = succ[idx]
                state = colour.get(nxt, WHITE)
                if state == GREY:
                    cycle = path[path.index(nxt):] + [nxt]
                elif state == WHITE:
                    stack.append((nxt, 0))
            else:
                colour[node] = BLACK
                order.append(node)
                path.pop()
                stack.pop()

    result: dict = {"cycle": cycle, "visited": len(colour)}
    if cycle is None:
        longest: dict[int, int] = {}
        for node in order:
            best = 0
            for nxt in graph.get(node, ()):
                best = max(best, 1 + longest.get(nxt, 0))
            longest[node] = best
        result["longest_from_root"] = longest.get(root, 0)
        result["longest_any"] = max(longest.values()) if longest else 0
    return result


def diamond_control() -> dict:
    """A DAG with a diamond: the detector must stay silent."""
    g = {0: {1, 2}, 1: {3}, 2: {3}, 3: set()}
    res = analyse(g, 0)
    return {"cycle": res["cycle"], "longest_from_root": res["longest_from_root"],
            "passed": res["cycle"] is None and res["longest_from_root"] == 2}


def long_chain_control(n: int = 300) -> dict:
    """A deep chain: longest must be n-1 and no cycle."""
    g = {i: {i + 1} for i in range(n - 1)}
    g[n - 1] = set()
    res = analyse(g, 0)
    return {"longest_from_root": res["longest_from_root"],
            "passed": res["cycle"] is None and res["longest_from_root"] == n - 1}


def main() -> int:
    book_path, out_path = sys.argv[1], sys.argv[2]
    by_key, index, boards, fens, plies, edges = build_adjacency(book_path)

    graph: dict[int, set[int]] = {}
    for parent, child, uci, _w in edges:
        graph.setdefault(parent, set()).add(child)

    root = 0
    real = analyse(graph, root)

    poisoned = {k: set(v) for k, v in graph.items()}
    first_child = sorted(graph.get(root, ()))[0]
    poisoned.setdefault(first_child, set()).add(root)
    planted = analyse(poisoned, root)

    diamond = diamond_control()
    chain = long_chain_control()

    leaves = [i for i in range(len(boards)) if i not in graph]
    leaf_plies: dict[int, int] = {}
    for i in leaves:
        leaf_plies[plies[i]] = leaf_plies.get(plies[i], 0) + 1

    report = {
        "book_entries": sum(len(v) for v in by_key.values()),
        "distinct_polyglot_keys": len(by_key),
        "reachable_positions": len(boards),
        "edges": len(edges),
        "max_ply_reached": max(plies),
        "leaves": len(leaves),
        "leaves_by_ply": {str(k): v for k, v in sorted(leaf_plies.items())},
        "all_leaves_same_ply": len(leaf_plies) == 1,
        "branching": {str(k): sum(1 for i in range(len(boards)) if len(graph.get(i, ())) == k)
                      for k in sorted({len(graph.get(i, ())) for i in range(len(boards))})},
        "real_cycle_found": real["cycle"] is not None,
        "real_longest_from_root": real["longest_from_root"],
        "planted_cycle_detected": planted["cycle"] is not None,
        "planted_cycle_length": len(planted["cycle"]) if planted["cycle"] else None,
        "diamond_control": diamond,
        "long_chain_control": chain,
        "threefold_minimum_plies_for_start": 8,
        "fifty_move_minimum_plies": 100,
    }
    report["corroborating_length"] = {
        "longest_book_line_plies": real["longest_from_root"],
        "all_leaves_at_one_ply": len(leaf_plies) == 1,
        "note": ("Length alone EXCLUDES nothing: the shortest possible threefold "
                 "needs 8 plies and the book is 16 plies long, so a 16-ply book "
                 "could in principle contain one. The exclusion comes from the "
                 "graph being acyclic, not from its depth."),
    }
    ok = (real["cycle"] is None
          and planted["cycle"] is not None
          and diamond["passed"]
          and chain["passed"])
    report["verdict"] = (
        "NO REPETITION OR FIFTY-MOVE DRAW IS REACHABLE IN BOOK: the position graph "
        f"over all {report['reachable_positions']} reachable positions and "
        f"{report['edges']} book edges is acyclic (DFS finds no back edge, and the "
        "checker detects a planted A->B->A), so no book line can revisit a position "
        "and a threefold cannot arise while in book; the fifty-move counter starts at "
        "0 and no book line is 100 plies long (longest is "
        f"{real['longest_from_root']})."
        if ok else "NOT EXCLUDED - SEE FIELDS"
    )
    with open(out_path, "w") as fh:
        json.dump(report, fh, indent=1)
    print(json.dumps(report, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

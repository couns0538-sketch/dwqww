"""Extract the embedded book, rebuild its reachable graph, and look for cycles.

Move encoding is read from `src/book.cpp` (encode_squares): low 6 bits = to
square in polyglot rank-major order, next 6 = from, high 3 = promotion index
(0 none, then 1..4 = knight..queen).  Castling is stored king-takes-rook, which
python-chess does not accept, so the decoder maps it to the real castling move.

Keys are recomputed with python-chess's own polyglot hash rather than trusting
the constant table: if a stored key disagrees with the position it is filed
under, the walk is wrong and nothing downstream means anything.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

import chess
import chess.polyglot


def load_book(path: str) -> list[tuple[int, int, int]]:
    text = open(path).read()

    def array(name: str) -> list[int]:
        m = re.search(rf"{name}\[[^\]]*\]\s*=\s*\{{(.*?)\}};", text, re.S)
        if m is None:
            raise SystemExit(f"array {name} not found in {path}")
        return [int(tok, 0) for tok in re.findall(r"0x[0-9a-fA-F]+|\d+", m.group(1))]

    keys = array("BookKeys")
    moves = array("BookMoves")
    weights = array("BookWeights")
    if not (len(keys) == len(moves) == len(weights)):
        raise SystemExit(f"array lengths differ: {len(keys)} {len(moves)} {len(weights)}")
    count = int(re.search(r"BookEntryCount\s*=\s*(\d+)", text).group(1))
    if count != len(keys):
        raise SystemExit(f"BookEntryCount {count} != {len(keys)}")
    return list(zip(keys, moves, weights))


def decode(board: chess.Board, encoded: int) -> chess.Move | None:
    """Decode a polyglot move to a python-chess move in STANDARD uci form.

    Castling is stored king-takes-rook (e1h1, e8a8). python-chess accepts that
    form, but the ENGINE does not accept it in a `position ... moves` list -- it
    answers `info string illegal move e1h1`. So a decoder that passes the stored
    form through produces moves that cannot be replayed. This one normalises to
    e1g1/e1c1/e8g8/e8c8, which both sides accept.

    (Found the hard way: a shuffle script built its move list from an earlier
    version of this decoder and the engine refused the line outright.)
    """
    to_file, to_rank = encoded & 7, (encoded >> 3) & 7
    from_file, from_rank = (encoded >> 6) & 7, (encoded >> 9) & 7
    promo = (encoded >> 12) & 7
    frm = chess.square(from_file, from_rank)
    to = chess.square(to_file, to_rank)
    mover = board.piece_at(frm)
    if mover and mover.piece_type == chess.KING and board.piece_at(to) and \
            board.piece_at(to).piece_type == chess.ROOK:
        to = {chess.H1: chess.G1, chess.A1: chess.C1,
              chess.H8: chess.G8, chess.A8: chess.C8}.get(to, to)
    piece = {0: None, 1: chess.KNIGHT, 2: chess.BISHOP, 3: chess.ROOK, 4: chess.QUEEN}[promo] if promo else None
    return chess.Move(frm, to, promotion=piece)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    entries = load_book(args.book)
    by_key: dict[int, list[tuple[int, int]]] = {}
    for key, move, weight in entries:
        by_key.setdefault(key, []).append((move, weight))

    start = chess.Board()
    start_key = chess.polyglot.zobrist_hash(start)

    # breadth-first walk over reachable positions
    nodes: dict[int, dict] = {}
    queue = [(start, 0)]
    seen = {start.fen()}
    edges: list[tuple[str, str, str, int]] = []
    key_mismatch = 0
    illegal = 0
    while queue:
        board, ply = queue.pop(0)
        key = chess.polyglot.zobrist_hash(board)
        if key in nodes:
            continue
        cands = by_key.get(key, [])
        nodes[key] = {"fen": board.fen(), "ply": ply, "moves": len(cands)}
        for encoded, weight in cands:
            mv = decode(board, encoded)
            if mv is None or not board.is_legal(mv):
                illegal += 1
                continue
            child = board.copy()
            child.push(mv)
            ckey = chess.polyglot.zobrist_hash(child)
            edges.append((board.fen(), mv.uci(), child.fen(), weight))
            if child.fen().split(" ")[0] not in seen:
                seen.add(child.fen().split(" ")[0])
                queue.append((child, ply + 1))

    # every stored entry must belong to a position reachable only through legal play
    reachable_keys = set(nodes)
    orphan_keys = [k for k in by_key if k not in reachable_keys]

    # cycle test: does any legal book path revisit a position (ignoring counters)?
    graph: dict[str, set[str]] = {}
    for parent_fen, uci, child_fen, _ in edges:
        graph.setdefault(parent_fen.split(" ")[0], set()).add(child_fen.split(" ")[0])

    def find_cycle() -> list[str] | None:
        color: dict[str, int] = {}
        stack: list[tuple[str, list[str]]] = []
        for root in graph:
            if color.get(root, 0) != 0:
                continue
            stack.append((root, [root]))
            while stack:
                node, path = stack.pop()
                if color.get(node, 0) == 2:
                    continue
                color[node] = 1
                for nxt in graph.get(node, ()):
                    if color.get(nxt, 0) == 1 and nxt in path:
                        return path[path.index(nxt):] + [nxt]
                    if color.get(nxt, 0) == 0:
                        stack.append((nxt, path + [nxt]))
                color[node] = 2
        return None

    cycle = find_cycle()

    # longest book path (DAG relaxation; if a cycle exists this is unbounded)
    depth_memo: dict[str, int] = {}

    def longest(node: str, guard: int = 0) -> int:
        if node in depth_memo:
            return depth_memo[node]
        if guard > 200:
            return 0
        best = 0
        for nxt in graph.get(node, ()):
            best = max(best, 1 + longest(nxt, guard + 1))
        depth_memo[node] = best
        return best

    root_edges = graph.get(start.fen().split(" ")[0], set())
    report = {
        "entries": len(entries),
        "distinct_keys": len(by_key),
        "reachable_positions": len(nodes),
        "root_key_corroborated": start_key in by_key,
        "orphan_keys": len(orphan_keys),
        "illegal_book_moves": illegal,
        "edges": len(edges),
        "cycle": cycle,
        "longest_book_path_plies": longest(start.fen().split(" ")[0]),
        "max_ply_in_walk": max(n["ply"] for n in nodes.values()),
        "positions_by_ply": {
            str(p): sum(1 for n in nodes.values() if n["ply"] == p)
            for p in sorted({n["ply"] for n in nodes.values()})
        },
        "positions_by_move_count": {
            str(c): sum(1 for n in nodes.values() if n["moves"] == c)
            for c in sorted({n["moves"] for n in nodes.values()})
        },
        "root_moves": sorted(u for p, u, c, w in edges if p == start.fen()),
        "edges_detail": edges,
    }
    with open(args.out, "w") as fh:
        json.dump(report, fh, indent=1)
    print(json.dumps({k: v for k, v in report.items() if k != "edges_detail"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

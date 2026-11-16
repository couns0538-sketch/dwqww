#!/usr/bin/env python3
"""node_draw.py EXE — can the draw short-circuit fire ONE PLY DOWN and hide a mate?

The root fix only protects the root. `Worker::is_draw` (src/search.cpp:1300-1310) is also
called from inside the tree (lines 1425 and 1569), and it returns a draw for
`halfmove_clock() >= 100` and for `is_repetition(root_history_index_)`. This harness asks
whether a position exists where that node-level return lands on a node that still has a mate
available for the side to move — i.e. whether the tree can be told "draw" one ply above a mate.

Method: for a family of positions with the fifty-move counter at 99 and the losing side to move,
enumerate every legal reply with python-chess and report, for each reply, whether the child
position has the counter at 100 AND the side to move there (the winner) has a mate in one and is
not in check. That child is exactly the node where the short-circuit would fire. Then search the
parent with the engine and report the score and PV, so the claim is about the engine, not a paper
argument.

Every engine run reads to `bestmove` before `quit` (seat 19's rule).
"""
import queue
import re
import subprocess
import sys
import threading
import time

import chess

CASES = [
    # (name, FEN with black to move). Every black reply here leads to a child with the counter
    # at 100 where White has mate in 1, so the node-level `is_draw` return is WRONG on those
    # children: the true score is mate, not 0.
    ("forced_mate_next_hm99", "6k1/8/5PPP/8/8/8/8/R6K b - - 99 40"),
    ("same_hm98_control", "6k1/8/5PPP/8/8/8/8/R6K b - - 98 40"),
    ("same_hm97_control", "6k1/8/5PPP/8/8/8/8/R6K b - - 97 40"),
    # a counter-resetting escape exists here, so cp 0 at hm 99 is CORRECT (the control showing
    # the harness does not cry wolf):
    ("resetting_escape_hm99", "6k1/5ppp/8/8/8/8/8/R5NK b - - 99 40"),
]


def engine(exe, fen, depth=8, timeout_s=60):
    """Search FEN to `bestmove`, obeying the read-before-next-command rule."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()

    def rd():
        for ln in p.stdout:
            q.put(ln.rstrip("\n"))
        q.put(None)
    threading.Thread(target=rd, daemon=True).start()
    p.stdin.write(f"uci\nposition fen {fen}\nisready\ngo depth {depth}\n")
    p.stdin.flush()
    lines, t0 = [], time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        try:
            ln = q.get(timeout=0.5)
        except queue.Empty:
            if p.poll() is not None:
                break
            continue
        if ln is None:
            break
        lines.append(ln)
        if ln.startswith("bestmove"):
            break
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
        p.stdin.close()
    except OSError:
        pass
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    infos = [l for l in lines if l.startswith("info depth")]
    bm = next((l.split()[1] for l in lines if l.startswith("bestmove")), None)
    score = nodes = depth_seen = None
    if infos:
        m = re.search(r"score (cp|mate) (-?\d+)", infos[-1])
        score = f"{m.group(1)} {m.group(2)}" if m else None
        m = re.search(r" nodes (\d+)", infos[-1])
        nodes = int(m.group(1)) if m else None
        m = re.search(r"^info depth (\d+)", infos[-1])
        depth_seen = int(m.group(1)) if m else None
    san = [l for l in lines if re.search(r"ERROR: (AddressSanitizer|LeakSanitizer)|runtime error: ", l)]
    return {"bestmove": bm, "score": score, "nodes": nodes, "depth": depth_seen,
            "info_lines": len(infos), "sanitizer_lines": san,
            "last_info": infos[-1] if infos else None,
            "proven_search": depth_seen is not None and (nodes or 0) > 0}


def mates_in_1(fen):
    b = chess.Board(fen)
    out = []
    for m in b.legal_moves:
        b.push(m)
        if b.is_checkmate():
            out.append(m.uci())
        b.pop()
    return out


def main():
    exe = sys.argv[1]
    print(f"exe {exe}\n")
    for name, fen in CASES:
        board = chess.Board(fen)
        print(f"=== {name}: {fen}")
        print(f"    side to move {board.turn}, halfmove {board.halfmove_clock}")
        nodes_at_100 = []
        for m in board.legal_moves:
            board.push(m)
            child = board.fen()
            hm = board.halfmove_clock
            if hm >= 100 and not board.is_check():
                mm = mates_in_1(child)
                if mm:
                    nodes_at_100.append({"reply": m.uci(), "child_fen": child,
                                         "child_halfmove": hm, "winner_mates": mm})
            board.pop()
        print(f"    replies that reach a 100-counter node where the mover has mate in 1: "
              f"{len(nodes_at_100)}")
        for x in nodes_at_100[:4]:
            print(f"      after {x['reply']}: {x['child_fen']}  mate {x['winner_mates']}")
        r = engine(exe, fen, depth=12)
        print(f"    engine: bestmove {r['bestmove']} score {r['score']} nodes {r['nodes']} "
              f"depth {r['depth']} info {r['info_lines']} proven_search {r['proven_search']}")
        print(f"    last info: {r['last_info']}")
        if r["sanitizer_lines"]:
            print(f"    SANITIZER: {r['sanitizer_lines'][:3]}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

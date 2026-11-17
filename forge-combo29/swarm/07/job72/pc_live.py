#!/usr/bin/env python3
"""Do my two confirmed faults survive on the PC build? The owner will run the PC build,
so a fault that only exists on the base tree is a historical note, not a live defect.

  FAULT A (07-F1 shared path): every path that reports without searching emits one
  fabricated `info depth ... score cp 0 nodes 0` line PER DEPTH. Test: count those lines.

  FAULT B (07-F3/C75/C76 fifty-move): a counter-100 root with a capture or pawn move
  available is declared drawn with 0 nodes. Test: does the PC build actually SEARCH it,
  and does python-chess agree it is not a fifty-move draw?

Both builds, all three regimes, same harness. Report per (fault, build, regime).

Usage: pc_live.py BASE_EXE PC_EXE OUTDIR
"""
import chess
import json
import os
import queue
import subprocess
import sys
import threading

S14 = [
    "LmrQuietBase value 93", "LmrQuietDivisor value 205", "LmrNoisyBase value 13",
    "LmrNoisyDivisor value 333", "LmrHistoryDivisor value 5643", "NullMoveBase value 5",
    "LmpBase value 8", "HistoryPruneMultiplier value 2220",
    "HistoryBonusQuadratic value 24", "HistoryBonusLinear value 54",
    "HistoryBonusMax value 2212", "SingularDepth value 6", "IirDepth value 2",
    "NonPawnCorrection value true",
]
PC20 = S14 + ["CuckooRep value true", "HistRework value 2", "TtPruneV2 value true",
              "CorrHistV2 value true", "MateAlphaGuard value true", "OwnBook value false"]

FIFTY = "8/6qk/8/8/8/1p4p1/4K3/8 b - - 100 1"


class Reader:
    def __init__(s, st):
        s.q = queue.Queue()
        threading.Thread(target=s._pump, args=(st,), daemon=True).start()

    def _pump(s, st):
        for l in st:
            s.q.put(l)
        s.q.put(None)

    def get(s, t):
        try:
            return s.q.get(timeout=t)
        except queue.Empty:
            return None


def run(exe, opts, position, gocmd, timeout=300):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    r = Reader(p.stdout)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    send("uci")
    while True:
        l = r.get(60)
        if l is None or l.strip() == "uciok":
            break
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    for o in opts:
        send("setoption name " + o)
    send("isready")
    while True:
        l = r.get(120)
        if l is None or l.strip() == "readyok":
            break
    send(position)
    send("isready")
    while True:
        l = r.get(120)
        if l is None or l.strip() == "readyok":
            break
    send(gocmd)
    lines = []
    while True:
        l = r.get(timeout)
        if l is None:
            break
        lines.append(l.rstrip("\n"))
        if l.startswith("bestmove"):
            break
    send("quit")
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    return lines


def fabricated(lines):
    """Count info lines that report a score but zero nodes -- a report with no search."""
    return [l for l in lines if l.startswith("info") and " score " in l and " nodes 0 " in l]


def main():
    base, pc, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    regimes = [("none", []), ("S14", S14), ("PC20", PC20)]
    builds = [("base", base), ("pc", pc)]

    # FAULT A: a searchmoves list with no legal move -> reports without searching
    fault_a = {}
    for bname, exe in builds:
        for rname, opts in regimes:
            lines = run(exe, opts, "position startpos",
                        "go depth 12 searchmoves a1a8", timeout=120)
            fab = fabricated(lines)
            fault_a[f"{bname}/{rname}"] = {
                "fabricated_lines": len(fab), "sample": fab[:2],
                "bestmove": next((l for l in lines if l.startswith("bestmove")), None)}

    # FAULT B: the fifty-move board
    b = chess.Board(FIFTY)
    resets = [m.uci() for m in b.legal_moves
              if b.is_capture(m) or b.piece_type_at(m.from_square) == chess.PAWN]
    genuine = b.is_fifty_moves() and not resets
    fault_b = {"fen": FIFTY, "resets": resets, "genuine_fifty_move_draw": genuine,
               "arms": {}}
    for bname, exe in builds:
        for rname, opts in regimes:
            lines = run(exe, opts, "position fen " + FIFTY, "go depth 12", timeout=300)
            score = next((l for l in reversed(lines) if " score " in l), None)
            nodes = None
            if score:
                try:
                    nodes = int(score.split(" nodes ")[1].split()[0])
                except (IndexError, ValueError):
                    pass
            best = next((l for l in lines if l.startswith("bestmove")), None)
            fault_b["arms"][f"{bname}/{rname}"] = {
                "score_line": score, "nodes": nodes, "bestmove": best,
                "searched": nodes is not None and nodes > 0}

    out = {"fault_a_no_legal_searchmove": fault_a, "fault_b_fifty": fault_b}
    json.dump(out, open(os.path.join(outdir, "pc_live.json"), "w"), indent=1)

    print("FAULT A -- fabricated info lines for `go depth 12 searchmoves a1a8` (no legal move)")
    for k, v in fault_a.items():
        print(f"  {k:12s} fabricated={v['fabricated_lines']:3d}  {v['bestmove']}")
    print()
    print("FAULT B -- fifty-move board", FIFTY)
    print("  python-chess: resets", resets, " genuine fifty-move draw:", genuine)
    for k, v in fault_b["arms"].items():
        print(f"  {k:12s} searched={str(v['searched']):5s} nodes={v['nodes']}")
        print(f"               {v['score_line']}")
    print()
    a_live = [k for k, v in fault_a.items() if v["fabricated_lines"] > 0]
    b_live = [k for k, v in fault_b["arms"].items() if not v["searched"]]
    print("FAULT A still live on:", a_live or "nothing")
    print("FAULT B still live on:", b_live or "nothing")


if __name__ == "__main__":
    main()

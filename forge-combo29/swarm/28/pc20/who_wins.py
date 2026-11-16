#!/usr/bin/env python3
"""who_wins.py EXE OUTDIR [DEPTH] — for each equal-depth disagreement, which move is better?

Reads out_ply/ply_cost.tsv (from ply_cost.py) and takes the positions where base's and PC20's fixed
depth-20 moves differ. For each such position it re-searches BOTH moves to DEPTH on the SAME build (the
judge), so neither side gets a build advantage, then compares.

Score normalisation — the part that is easy to get wrong and that I state explicitly:
  The engine reports `score cp X` relative to THE SIDE TO MOVE in the searched position.
  After the move under test, the OPPONENT is to move, so for White's point of view:
      white_cp = -X      when the opponent to move is Black (i.e. side to move after the move is Black)
      white_cp = +X      when the side to move after the move is White
  Equivalently: white_cp = (+X if side_to_move_after == White else -X).
  `score mate N` (N > 0) means the side to move mates, mapped to +MATE_SENTINEL; `mate -N` to
  -MATE_SENTINEL. MATE_SENTINEL is larger than any cp so mate always outranks a material score.

Output: per position, both moves, both raw scores (side-to-move), both White-relative scores, the gap, and
which build's move wins. Plus a count and a median absolute gap.

Usage: who_wins.py EXE OUTDIR [DEPTH]
"""
import os
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine  # noqa: E402

S14 = {
    "LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
    "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
    "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
    "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true",
}
MATE_SENTINEL = 100000


def parse_score(text):
    """-> (kind, value) where kind is 'cp' or 'mate'."""
    parts = text.split()
    if len(parts) < 2:
        return "cp", 0
    kind = parts[0]
    if kind == "mate":
        try:
            return "mate", int(parts[1])
        except ValueError:
            return "mate", 0
    try:
        return "cp", int(parts[1])
    except ValueError:
        return "cp", 0


def white_cp(kind, value, side_to_move_after):
    """Convert a side-to-move score into White's point of view.

    Mate convention, which UCI defines from the SIDE TO MOVE's view:
        mate  v > 0  -> the side to move delivers mate in v
        mate  v < 0  -> the side to move GETS MATED in |v|
        mate  0      -> the side to move is already checkmated (a loss for it)
    A first version mapped mate 0 to a score of 0 and, in the terminal branch, reported a checkmated
    side as "mate 1" — i.e. as if the mated side were mating. The end-to-end control (a mate-in-1 move
    against a quiet move) caught it: the mate scored WORSE than the quiet move. Both are fixed here.
    """
    if kind == "mate":
        # v == 0 is a LOSS for the side to move, same sign as v < 0.
        raw = MATE_SENTINEL if value > 0 else -MATE_SENTINEL
    else:
        raw = value
    return raw if side_to_move_after == chess.WHITE else -raw


class Judge:
    def __init__(self, exe, depth):
        self.depth = depth
        self.eng = Engine(exe)
        self.eng.send("uci")
        self.eng.read_until("uciok", 20)
        for opt, val in [("Threads", 1), ("Hash", 16)] + list(S14.items()) + [("OwnBook", "false")]:
            self.eng.send(f"setoption name {opt} value {val}")
            self.eng.send("isready")
            lines, ok = self.eng.read_until("readyok", 20)
            bad = [l for l in lines if "unknown option" in l or "invalid value" in l]
            if bad or not ok:
                raise SystemExit(f"STOP {opt}: {bad or 'no readyok'}")

    def eval_after(self, fen, move):
        board = chess.Board(fen)
        try:
            mv = chess.Move.from_uci(move)
        except ValueError:
            return None
        if mv not in board.legal_moves:
            return None
        board.push(mv)
        side_to_move_after = board.turn
        # Terminal positions: judge directly, no search needed.
        if board.is_checkmate():
            # The side to move is checkmated: that is "mate 0" from ITS view, a loss for it.
            return ("mate", 0, side_to_move_after, "terminal")
        if board.is_stalemate() or board.is_insufficient_material():
            return ("cp", 0, side_to_move_after, "terminal-draw")
        self.eng.send("ucinewgame")
        self.eng.send("isready")
        self.eng.read_until("readyok", 20)
        self.eng.send(f"position fen {fen} moves {move}")
        self.eng.send("isready")
        self.eng.read_until("readyok", 20)
        self.eng.send(f"go depth {self.depth}")
        out, ok = self.eng.read_until("bestmove", 300)
        if not ok:
            return None
        kind, value, depth_seen = "cp", 0, 0
        for line in out:
            if line.startswith("info depth") and " score " in line:
                f = line.split()
                if "score" in f:
                    i = f.index("score")
                    kind, value = parse_score(" ".join(f[i + 1:i + 3]))
                if "depth" in f:
                    depth_seen = int(f[f.index("depth") + 1])
        return (kind, value, side_to_move_after, depth_seen)

    def close(self):
        self.eng.close()


def main() -> int:
    exe, outdir = sys.argv[1], sys.argv[2]
    depth = int(sys.argv[3]) if len(sys.argv) > 3 else 18
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "out_ply", "ply_cost.tsv")
    if not os.path.exists(src):
        raise SystemExit(f"missing {src} — run ply_cost.py first")
    rows = [l.rstrip("\n").split("\t") for l in open(src)][1:]
    disputes = [r for r in rows if r[5] != r[6]]
    print(f"judge: base build only, both moves at go depth {depth}, scores converted to White's view")
    print(f"disputed positions: {len(disputes)} of {len(rows)}")
    print()

    judge = Judge(exe, depth)
    print("| # | position | base move | PC20 move | base raw | PC20 raw | base (White cp) | "
          "PC20 (White cp) | gap | better |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    results = []
    for i, r in enumerate(disputes, 1):
        fen, bmove, pmove = r[0], r[5], r[6]
        b = judge.eval_after(fen, bmove)
        p = judge.eval_after(fen, pmove)
        if b is None or p is None:
            print(f"| {i} | {fen} | {bmove} | {pmove} | FAILED | FAILED | - | - | - | - |")
            continue
        braw = f"{b[0]} {b[1]}"
        praw = f"{p[0]} {p[1]}"
        bw = white_cp(b[0], b[1], b[2])
        pw = white_cp(p[0], p[1], p[2])
        gap = pw - bw
        if abs(gap) < 20:
            better = "equal (<20cp)"
        elif gap > 0:
            better = "PC20"
        else:
            better = "base"
        print(f"| {i} | {fen} | {bmove} | {pmove} | {braw} | {praw} | {bw} | {pw} | {gap:+d} | "
              f"{better} |")
        results.append({"fen": fen, "b": bmove, "p": pmove, "bw": bw, "pw": pw, "gap": gap,
                        "better": better, "depth_b": b[3], "depth_p": p[3]})
    judge.close()

    print()
    pc = sum(1 for r in results if r["better"] == "PC20")
    ba = sum(1 for r in results if r["better"] == "base")
    eq = sum(1 for r in results if r["better"].startswith("equal"))
    print(f"PC20 move better: {pc}, base move better: {ba}, equal (<20 cp): {eq}, "
          f"of {len(results)} judged")
    if results:
        gaps = sorted(abs(r["gap"]) for r in results)
        mid = gaps[len(gaps) // 2]
        print(f"median |gap|: {mid} cp; largest |gap|: {gaps[-1]} cp")
        print(f"positions where the PC20 move scored higher by >=20 cp: "
              f"{sum(1 for r in results if r['gap'] >= 20)}")
    with open(os.path.join(outdir, "who_wins.tsv"), "w") as fh:
        fh.write("fen\tbase_move\tpc20_move\tbase_white_cp\tpc20_white_cp\tgap\tbetter\n")
        for r in results:
            fh.write(f"{r['fen']}\t{r['b']}\t{r['p']}\t{r['bw']}\t{r['pw']}\t{r['gap']:+d}\t"
                     f"{r['better']}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

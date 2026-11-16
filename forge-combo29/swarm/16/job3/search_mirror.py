#!/usr/bin/env python3
"""search_mirror.py EXE FENS OUT.tsv META.txt

For each FEN: `go depth 10` on the position, then on its colour mirror, one fresh engine process per search
(so no hash carry-over between the two). Records the last `info depth 10 ... score ... pv ...` line and the
bestmove. The bestmove of the mirror is mapped back through the mirror (square ^ 56, and the piece types are
the same) so the two can be compared move for move.
Every setoption is followed by isready; every answer line is checked for unknown option / invalid value /
invalid FEN / illegal move. A search that produces no bestmove within LIMIT seconds is a HANG and is recorded.
"""
import hashlib
import os
import re
import subprocess
import sys
import time

import chess

LIMIT = 120
S14 = [
    ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
    ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
    ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
    ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")
DEPTH = 10


def search(exe, fen, meta_lines):
    script = ["uci", "isready",
              "setoption name Threads value 1", "isready",
              "setoption name Hash value 16", "isready"]
    for name, val in S14:
        script += [f"setoption name {name} value {val}", "isready"]
        meta_lines.append(f"setoption name {name} value {val}")
    script += [f"position fen {fen}", "isready", f"go depth {DEPTH}"]
    # stdin is kept OPEN until bestmove arrives: closing it makes the engine abandon the search
    # (the UCI loop sees EOF and stops), which is exactly the trap that produced empty scores at first.
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    for command in script:
        p.stdin.write(command + "\n")
        p.stdin.flush()
    lines = []
    hang = False
    deadline = time.monotonic() + LIMIT
    saw_bestmove = False
    while time.monotonic() < deadline:
        line = p.stdout.readline()
        if not line:
            break
        lines.append(line.rstrip("\n"))
        if line.startswith("bestmove"):
            saw_bestmove = True
            break
    if not saw_bestmove:
        hang = True
        p.kill()
    else:
        try:
            p.stdin.write("quit\n")
            p.stdin.flush()
            p.wait(timeout=10)
        except Exception:
            p.kill()
    out = "\n".join(lines)
    best = None
    last = None
    for line in out.splitlines():
        low = line.lower()
        for bad in BAD:
            if bad in low:
                raise SystemExit("STOP from engine: " + line)
        if line.startswith("bestmove"):
            best = line.split()[1]
        m = re.match(r"^info depth (\d+) .*", line)
        if m and int(m.group(1)) == DEPTH:
            last = line
    return best, last, False


def parse_info(line):
    if not line:
        return None, None, None
    m = re.search(r"score (cp|mate) (-?\d+)", line)
    kind, val = (m.group(1), int(m.group(2))) if m else (None, None)
    pv = []
    if " pv " in line:
        pv = line.split(" pv ", 1)[1].split()
    return kind, val, pv


def main(EXE, FENS, OUT, META):
    fens = [l.strip() for l in open(FENS) if l.strip()]
    meta = [f"exe started: {EXE}",
            f"sha256: {hashlib.sha256(open(EXE,'rb').read()).hexdigest()}",
            f"depth {DEPTH}, fens {FENS} count {len(fens)}",
            "one fresh process per search"]
    rows = 0
    hangs = 0
    with open(OUT, "w") as out:
        out.write("idx\tfen\tbm\tkind\tval\tmirror_fen\tbm_m\tbm_m_back\tkind_m\tval_m\t"
                  "score_equal\tbm_equal\ttotal_equal\n")
        for idx, fen in enumerate(fens):
            b = chess.Board(fen)
            mir = b.mirror()
            best_a, info_a, h1 = search(EXE, fen, meta)
            best_b, info_b, h2 = search(EXE, mir.fen(), meta)
            if h1 or h2:
                hangs += 1
                out.write(f"{idx}\t{fen}\tHANG\n")
                continue
            ka, va, _ = parse_info(info_a)
            kb, vb, _ = parse_info(info_b)
            # map the mirror's bestmove back: squares are vertically flipped (sq ^ 56), colours swapped;
            # the "side" of the move follows the side to move, so the move text itself maps by square only
            bm_back = None
            if best_b and best_b != "0000":
                mv = chess.Move.from_uci(best_b)
                bm_back = chess.Move(mv.from_square ^ 56, mv.to_square ^ 56, mv.promotion).uci()
            score_eq = (ka == kb and va == vb)
            bm_eq = (best_a == bm_back)
            out.write(f"{idx}\t{fen}\t{best_a}\t{ka}\t{va}\t{mir.fen()}\t{best_b}\t{bm_back}\t{kb}\t{vb}\t"
                      f"{score_eq}\t{bm_eq}\t"
                      f"{'yes' if (score_eq and bm_eq) else 'no'}\n")
            rows += 1
    with open(META, "w") as m:
        m.write("\n".join(meta) + "\n")
    print(f"rows {rows} hangs {hangs}")


if __name__ == "__main__":
    main(*sys.argv[1:5])

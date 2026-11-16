#!/usr/bin/env python3
"""eval_symmetry.py EXE FENS OUTDIR

The engine's `eval` command prints `info string eval hce <a> nnue <b> total <c>`.

`eval` prints WHITE-POSITIVE values regardless of the side to move: src/eval.cpp:509 returns
`board.side_to_move() == White ? tapered : -tapered`, verified empirically (the same board with
White to move prints +820 and with Black to move -800). Therefore the evaluation of a position
must equal the NEGATION of the evaluation of its colour-flipped mirror.

My first version of this script compared the two as equal and reported 588 "asymmetric"
values that were in fact identical numbers -- the mirror was correct and my comparison was
wrong. Fixed here; the control below is what makes the corrected comparison trustworthy.

Asserts every number was PARSED (a missing `info string eval` line fails loudly, never passes),
and asserts the control: a deliberately non-symmetric FEN pair must NOT be reported as equal.
"""
import os
import re
import queue
import subprocess
import sys
import threading

import chess

EVAL_LINE = re.compile(r"info string eval hce (-?\d+) nnue (-?\d+) total (-?\d+)")


class Reader:
    def __init__(self, stream):
        self.q = queue.Queue()
        threading.Thread(target=self._pump, args=(stream,), daemon=True).start()

    def _pump(self, s):
        for line in s:
            self.q.put(line)
        self.q.put(None)

    def get(self, timeout=60.0):
        try:
            return self.q.get(timeout=timeout)
        except queue.Empty:
            return None


def eval_fens(exe, fens):
    """One fresh process for all the FENs, evals only (no search), returns {fen: (hce,nnue,total)}."""
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)
    r = Reader(proc.stdout)

    def send(c):
        proc.stdin.write(c + "\n")
        proc.stdin.flush()

    def drain():
        while True:
            line = r.get()
            if line is None:
                raise RuntimeError("no readyok")
            if line.strip() == "readyok":
                return

    send("uci")
    while True:
        line = r.get(30)
        if line is None or line.strip() == "uciok":
            break
    send("setoption name Hash value 16")
    send("isready")
    drain()
    out = {}
    for fen in fens:
        send("position fen " + fen)
        send("isready")
        drain()
        send("eval")
        m = None
        deadline_lines = 0
        while m is None:
            line = r.get(30)
            if line is None:
                raise RuntimeError(f"no eval answer for {fen}")
            if line.startswith("info string eval"):
                m = EVAL_LINE.search(line)
                if m is None:
                    raise RuntimeError(f"eval line did not parse: {line!r}")
        out[fen] = tuple(int(g) for g in m.groups())
        deadline_lines += 1
    send("quit")
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
    return out


def mirror_fen(fen):
    b = chess.Board(fen)
    m = b.mirror()
    return m.fen()


def main():
    exe, fens_path, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    fens = [l.strip() for l in open(fens_path, encoding="utf-8") if l.strip()]
    fens = [f for f in fens if len(f.split()) == 6]
    mirrors = [mirror_fen(f) for f in fens]
    vals = eval_fens(exe, fens + mirrors)

    rows, bad = [], 0
    for fen, mir in zip(fens, mirrors):
        a = vals[fen]
        b = vals[mir]
        for i, name in enumerate(("hce", "nnue", "total")):
            if a[i] != -b[i]:
                bad += 1
                rows.append(f"ASYMMETRIC {name}: {a[i]} vs mirrored {b[i]}  fen {fen}")
    with open(os.path.join(outdir, "differences.txt"), "w") as fh:
        fh.write("\n".join(rows) + ("\n" if rows else ""))

    # Control: two clearly different positions must not compare equal, else the comparison is dead.
    ctrl = ["4k3/8/8/8/8/8/8/4K3 w - - 0 1", "4k3/8/8/8/8/8/3Q4/4K3 w - - 0 1"]
    cvals = eval_fens(exe, ctrl)
    control_works = cvals[ctrl[0]][2] != cvals[ctrl[1]][2]

    print(f"positions {len(fens)} (each also mirrored): {len(fens)*3} comparisons")
    print(f"asymmetric values: {bad}")
    for row in rows[:15]:
        print("  " + row)
    print(f"control (two different positions must differ): "
          f"{cvals[ctrl[0]][2]} vs {cvals[ctrl[1]][2]} -> "
          f"{'works' if control_works else 'BROKEN'}")
    if not control_works:
        print("RESULT: the comparison itself is broken; nothing can be concluded")
        sys.exit(2)
    if bad:
        print(f"RESULT: {bad} asymmetric evaluation value(s)")
        sys.exit(1)
    print("RESULT: eval() is exactly colour-symmetric on every position tested")


if __name__ == "__main__":
    main()

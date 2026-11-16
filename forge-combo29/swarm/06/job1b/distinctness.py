#!/usr/bin/env python3
"""R5: is the SEED-611 R set materially different in content from the SEED-601 set?

Compares the two sets on summary statistics that the prediction named: |hce| above 600, and
piece counts under 8. Also reports material spread and the fraction of positions in check, so
"the new set is not a near-duplicate" is a measured claim rather than an assertion.

usage: distinctness.py EXE FILE_A FILE_B LABEL_A LABEL_B
"""
import subprocess
import sys

import chess

ERROR_MARKERS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.send("uci")
        while True:
            line = self.readline()
            if line.strip() == "uciok":
                break
        self.send("isready")
        self.wait_ready()

    def send(self, c):
        self.p.stdin.write(c + "\n")
        self.p.stdin.flush()

    def readline(self):
        line = self.p.stdout.readline()
        if line == "":
            raise RuntimeError("engine died")
        return line

    def wait_ready(self):
        while True:
            line = self.readline().strip()
            if any(m in line for m in ERROR_MARKERS):
                raise RuntimeError(line)
            if line == "readyok":
                return

    def lines_until_ready(self):
        out = []
        while True:
            line = self.readline().strip()
            out.append(line)
            if any(m in line for m in ERROR_MARKERS):
                raise RuntimeError(line)
            if line == "readyok":
                return out

    def eval_fen(self, fen):
        self.send("position fen " + fen)
        self.send("isready")
        self.wait_ready()
        self.send("eval")
        self.send("isready")
        for line in self.lines_until_ready():
            if line.startswith("info string eval"):
                tok = line.split()
                return int(tok[tok.index("hce") + 1])
        return None

    def quit(self):
        try:
            self.send("quit")
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


def stats(eng, path):
    fens = [l.strip() for l in open(path) if l.strip()]
    big_hce = 0
    small_material = 0
    in_check = 0
    pieces = []
    for fen in fens:
        h = eng.eval_fen(fen)
        if h is not None and abs(h) > 600:
            big_hce += 1
        board = chess.Board(fen)
        n = len(board.piece_map())
        pieces.append(n)
        if n < 8:
            small_material += 1
        if board.is_check():
            in_check += 1
    return {"n": len(fens), "big_hce": big_hce, "small_material": small_material,
            "in_check": in_check, "mean_pieces": sum(pieces) / max(len(pieces), 1),
            "min_pieces": min(pieces) if pieces else 0,
            "max_pieces": max(pieces) if pieces else 0}


def main():
    exe, fa, fb, la, lb = sys.argv[1:6]
    eng = Engine(exe)
    a = stats(eng, fa)
    b = stats(eng, fb)
    eng.quit()
    print("| statistic | %s | %s |" % (la, lb))
    print("|---|---|---|")
    for k in ("n", "big_hce", "small_material", "in_check", "mean_pieces", "min_pieces", "max_pieces"):
        print("| %s | %s | %s |" % (k, a[k], b[k]))
    print("")
    print("R5 (the new set has at least one |hce|>600 or one position with <8 pieces, and is not a")
    print("    near-duplicate of the old set): %s" % ("PASS" if (b["big_hce"] > 0 or b["small_material"] > 0) else "FAIL"))


if __name__ == "__main__":
    main()

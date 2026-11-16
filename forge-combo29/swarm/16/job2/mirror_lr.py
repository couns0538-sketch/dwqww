#!/usr/bin/env python3
"""mirror_lr.py EXE FENS OUT.tsv META.txt : left-right (horizontal) mirror eval comparison.

For each FEN: eval(position) then eval(flip_horizontal(position)), both through the same engine process.
The mirror is python-chess `board.transform(chess.flip_horizontal)`.
Also records whether the board has castling rights (should be none) and the king files, for the P3 check.
"""
import hashlib
import subprocess
import sys

import chess

S14 = [
    ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
    ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
    ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
    ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  text=True, bufsize=1)
        self.send("uci")
        self.send("isready")
        uci = self.read_until()
        self.ids = [l for l in uci if l.startswith("id ")]
        self.opts = []
        for name, val in S14:
            line = f"setoption name {name} value {val}"
            self.opts.append(line)
            self.send(line)
            self.send("isready")
            self.check(self.read_until())

    def send(self, c):
        self.p.stdin.write(c + "\n")
        self.p.stdin.flush()

    def read_until(self):
        lines = []
        while True:
            line = self.p.stdout.readline()
            if not line:
                lines.append("<<EOF>>")
                break
            line = line.rstrip("\n")
            lines.append(line)
            if line.strip() == "readyok":
                break
        return lines

    def check(self, lines):
        for line in lines:
            low = line.lower()
            for bad in BAD:
                if bad in low:
                    raise SystemExit("STOP: " + line)

    def ev(self, fen):
        self.send("position fen " + fen)
        self.send("isready")
        self.check(self.read_until())
        self.send("eval")
        self.send("isready")
        lines = self.read_until()
        self.check(lines)
        for l in lines:
            if l.startswith("info string eval"):
                return l
        return None

    def quit(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def parse(line):
    parts = line.split()
    d = {}
    for i, t in enumerate(parts):
        if t in ("hce", "nnue", "total") and i + 1 < len(parts):
            d[t] = int(parts[i + 1])
    return d


def main(exe, fens_path, out_path, meta_path):
    global EXE, FENS, OUT, META
    EXE, FENS, OUT, META = exe, fens_path, out_path, meta_path
    fens = [l.strip() for l in open(FENS) if l.strip()]
    eng = Engine(EXE)
    with open(META, "w") as m:
        m.write(f"exe started: {EXE}\nsha256: {hashlib.sha256(open(EXE,'rb').read()).hexdigest()}\n")
        m.write("id lines: " + " | ".join(eng.ids) + "\n")
        m.write("options sent:\n" + "\n".join(eng.opts) + "\n")
        m.write(f"fens file: {FENS} count {len(fens)}\n")
        m.write("mirror: chess.Board(fen).transform(chess.flip_horizontal)\n")

    n = 0
    with open(OUT, "w") as out:
        out.write("set\tidx\tfen\tcastling\thce\tnnue\ttotal\tlrfen\thce_lr\tnnue_lr\ttotal_lr\t"
                  "diff_fields\twkfile\tbkfile\tktotalfile\n")
        for idx, fen in enumerate(fens):
            b = chess.Board(fen)
            lr = b.transform(chess.flip_horizontal)
            a1 = eng.ev(fen)
            a2 = eng.ev(lr.fen())
            if a1 is None or a2 is None:
                continue
            d1, d2 = parse(a1), parse(a2)
            d = [k for k in ("hce", "nnue", "total") if d1.get(k) != d2.get(k)]
            wk = chess.square_file(b.king(chess.WHITE)) if b.king(chess.WHITE) is not None else -1
            bk = chess.square_file(b.king(chess.BLACK)) if b.king(chess.BLACK) is not None else -1
            out.write("\t".join(str(x) for x in (
                "J2", idx, fen, b.castling_rights, d1.get("hce"), d1.get("nnue"), d1.get("total"),
                lr.fen(), d2.get("hce"), d2.get("nnue"), d2.get("total"),
                ",".join(d) or "-", wk, bk, wk + bk)) + "\n")
            n += 1
    eng.quit()
    print(f"rows {n}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

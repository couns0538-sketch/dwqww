#!/usr/bin/env python3
"""mirror_eval.py EXE FENS OUT.tsv META.txt

For each FEN: send `position fen <fen>`, `isready`, `eval`, read to readyok + the eval line, then the
colour-flipped mirror (python-chess board.mirror()) the same way in the same engine process.
S14 is sent once per process. Every setoption and position is followed by isready and every line up to
readyok is checked for unknown option / invalid value / invalid FEN / illegal move.
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
        uci_lines = self.read_until("uciok")
        self.id_lines = [l for l in uci_lines if l.startswith("id ")]
        self.option_lines = []
        for name, val in S14:
            line = f"setoption name {name} value {val}"
            self.option_lines.append(line)
            self.send(line)
            self.send("isready")
            self.check(self.read_until("readyok"))

    def send(self, cmd):
        self.p.stdin.write(cmd + "\n")
        self.p.stdin.flush()

    def read_until(self, tok):
        lines = []
        while True:
            line = self.p.stdout.readline()
            if not line:
                lines.append("<<EOF>>")
                break
            line = line.rstrip("\n")
            lines.append(line)
            if line.strip() == tok:
                break
        return lines

    def check(self, lines):
        for line in lines:
            low = line.lower()
            if any(b.lower() in low for b in BAD):
                raise SystemExit("STOP: bad answer line: " + line)

    def eval_fen(self, fen):
        self.send("position fen " + fen)
        self.send("isready")
        self.check(self.read_until("readyok"))
        self.send("eval")
        self.send("isready")
        lines = self.read_until("readyok")
        self.check(lines)
        ev = None
        for line in lines:
            if line.startswith("info string eval"):
                ev = line
        return ev

    def quit(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def parse(ev):
    """'info string eval hce 18 nnue 20 total 38' -> {'hce': 18, 'nnue': 20, 'total': 38}"""
    parts = ev.split()
    d = {}
    for i, tok in enumerate(parts):
        if tok in ("hce", "nnue", "total") and i + 1 < len(parts):
            d[tok] = int(parts[i + 1])
    return d


def main(exe, fens_path, out_path, meta_path):
    fens = [l.strip() for l in open(fens_path) if l.strip()]
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    eng = Engine(exe)
    with open(meta_path, "w") as m:
        m.write(f"exe started: {exe}\nsha256: {sha}\n")
        m.write("id lines: " + " | ".join(eng.id_lines) + "\n")
        m.write("options sent:\n" + "\n".join(eng.option_lines) + "\n")
        m.write(f"fens file: {fens_path} count {len(fens)}\n")

    rows = 0
    bad_fen = 0
    with open(out_path, "w") as out:
        out.write("set\tidx\tfen\thce\tnnue\ttotal\tmirror_fen\thce_m\tnnue_m\ttotal_m\tdiff_fields\n")
        for idx, fen in enumerate(fens):
            try:
                board = chess.Board(fen)
            except ValueError:
                bad_fen += 1
                continue
            mir = board.mirror().fen()
            e1 = eng.eval_fen(fen)
            e2 = eng.eval_fen(mir)
            if e1 is None or e2 is None:
                continue
            d1, d2 = parse(e1), parse(e2)
            diffs = [k for k in ("hce", "nnue", "total") if d1.get(k) != d2.get(k)]
            out.write("\t".join(str(x) for x in (
                "G", idx, fen, d1.get("hce"), d1.get("nnue"), d1.get("total"),
                mir, d2.get("hce"), d2.get("nnue"), d2.get("total"), ",".join(diffs) or "-")) + "\n")
            rows += 1
    eng.quit()
    print(f"rows {rows} python_chess_invalid_fens {bad_fen}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

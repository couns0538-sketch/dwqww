#!/usr/bin/env python3
"""area 6 job 2 harness: static eval of each FEN and of its LEFT-RIGHT mirror.

The horizontal flip is python-chess board.transform(chess.flip_horizontal): files mirrored, colours and
side to move untouched. Positions with ANY castling right are skipped and counted (a flipped rook would no
longer stand on the square its castling right names).

usage: harness_lr.py EXE FENFILE OUTFILE META
"""
import hashlib
import subprocess
import sys

import chess

ERROR_MARKERS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.send("uci")
        self.name = None
        while True:
            line = self.readline()
            if line.startswith("id name"):
                self.name = line.strip()
            if line.strip() == "uciok":
                break
        self.send("isready")
        self.wait_ready()

    def send(self, cmd):
        self.p.stdin.write(cmd + "\n")
        self.p.stdin.flush()

    def readline(self):
        line = self.p.stdout.readline()
        if line == "":
            raise RuntimeError("engine died")
        return line

    def wait_ready(self):
        lines = []
        while True:
            line = self.readline().strip()
            lines.append(line)
            if any(m in line for m in ERROR_MARKERS):
                raise RuntimeError("engine rejected input: " + line)
            if line == "readyok":
                return lines

    def eval_fen(self, fen):
        self.send("position fen " + fen)
        self.send("isready")
        self.wait_ready()
        self.send("eval")
        self.send("isready")
        for line in self.wait_ready():
            if line.startswith("info string eval"):
                return line
        return None

    def quit(self):
        try:
            self.send("quit")
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    exe, fenfile, outfile, metafile = sys.argv[1:5]
    fens = [l.strip() for l in open(fenfile) if l.strip()]
    eng = Engine(exe)
    meta = ["exe_started: " + exe, "exe_sha256: " + sha256(exe),
            "id_name: " + str(eng.name),
            "option_lines_sent: NONE",
            "per_position_lines_sent: 'position fen <FEN>', 'isready', 'eval', 'isready'",
            "transform: chess.flip_horizontal (files mirrored, colours and side to move unchanged)",
            "fenfile: " + fenfile, "fenfile_sha256: " + sha256(fenfile),
            "positions in file: %d" % len(fens)]
    rows, failures, skipped = [], [], 0
    for i, fen in enumerate(fens):
        try:
            board = chess.Board(fen)
        except Exception as exc:
            failures.append((i, fen, "python-chess rejects: %s" % exc))
            continue
        if board.castling_rights != 0:
            skipped += 1
            continue
        hfen = board.transform(chess.flip_horizontal).fen()
        try:
            a = eng.eval_fen(fen)
            b = eng.eval_fen(hfen)
        except RuntimeError as exc:
            failures.append((i, fen, "engine: %s" % exc))
            eng = Engine(exe)
            continue
        rows.append((i, fen, hfen, a, b))
    eng.quit()
    with open(outfile, "w") as fh:
        for i, fen, hfen, a, b in rows:
            fh.write("FEN\t%d\t%s\n" % (i, fen))
            fh.write("MIR\t%d\t%s\n" % (i, hfen))
            fh.write("EVAL\t%d\t%s\n" % (i, a))
            fh.write("MEVAL\t%d\t%s\n" % (i, b))
        for i, fen, why in failures:
            fh.write("FAIL\t%d\t%s\t%s\n" % (i, fen, why))
    meta.append("skipped_castling_positions: %d" % skipped)
    meta.append("rows_written: %d" % len(rows))
    meta.append("failures: %d" % len(failures))
    with open(metafile, "w") as fh:
        fh.write("\n".join(meta) + "\n")
    print("rows=%d skipped_castling=%d failures=%d" % (len(rows), skipped, len(failures)))


if __name__ == "__main__":
    main()

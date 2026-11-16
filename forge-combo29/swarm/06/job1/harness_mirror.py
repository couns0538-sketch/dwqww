#!/usr/bin/env python3
"""seat 06 area 6 job 1 harness: static eval of each FEN and of its colour-flipped mirror.

Drives one engine process over stdin/stdout. For every FEN and for its mirror it sends
    position fen <FEN>
    isready          (reads every line up to readyok, aborts on unknown option/invalid value/invalid FEN/illegal move)
    eval             (collects `info string eval ...`)
Never copies anything from another seat; the mirror is made by python-chess board.mirror().

usage: harness_mirror.py EXE FENFILE OUTFILE META
"""
import hashlib
import subprocess
import sys

import chess

ERROR_MARKERS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen(
            [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
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

    def set_position(self, fen):
        self.send("position fen " + fen)
        self.send("isready")
        return self.wait_ready()

    def eval_once(self):
        self.send("eval")
        self.send("isready")
        lines = self.wait_ready()
        for line in lines:
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
    meta = [
        "exe_started: " + exe,
        "exe_sha256: " + sha256(exe),
        "option_lines_sent: NONE (this job is a static evaluation; no setoption is sent)",
        "per_position_lines_sent: 'position fen <FEN>', 'isready', 'eval', 'isready'",
        "fenfile: " + fenfile,
        "fenfile_sha256: " + sha256(fenfile),
        "positions: %d" % len(fens),
    ]

    eng = Engine(exe)
    meta.append("id_name: " + str(eng.name))
    rows = []
    failures = []
    for i, fen in enumerate(fens):
        try:
            board = chess.Board(fen)
        except Exception as exc:
            failures.append((i, fen, "python-chess rejects: %s" % exc))
            continue
        mfen = board.mirror().fen()
        try:
            eng.set_position(fen)
            a = eng.eval_once()
            eng.set_position(mfen)
            b = eng.eval_once()
        except RuntimeError as exc:
            failures.append((i, fen, "engine: %s" % exc))
            eng = Engine(exe)
            continue
        rows.append((i, fen, mfen, a, b))

    eng.quit()

    with open(outfile, "w") as fh:
        for i, fen, mfen, a, b in rows:
            fh.write("FEN\t%d\t%s\n" % (i, fen))
            fh.write("MIR\t%d\t%s\n" % (i, mfen))
            fh.write("EVAL\t%d\t%s\n" % (i, a))
            fh.write("MEVAL\t%d\t%s\n" % (i, b))
        for i, fen, why in failures:
            fh.write("FAIL\t%d\t%s\t%s\n" % (i, fen, why))

    meta.append("rows_written: %d" % len(rows))
    meta.append("failures: %d" % len(failures))
    with open(metafile, "w") as fh:
        fh.write("\n".join(meta) + "\n")
    print("rows=%d failures=%d" % (len(rows), len(failures)))


if __name__ == "__main__":
    main()

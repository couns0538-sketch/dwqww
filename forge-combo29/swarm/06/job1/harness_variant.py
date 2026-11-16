#!/usr/bin/env python3
"""area 6 job 1, variant harness: static eval with setoption lines, FEN vs colour-flipped mirror.

Every setoption is followed by isready and every line up to readyok is read; the run stops on
unknown option / invalid value / invalid FEN / illegal move. Option lines sent are recorded in
the .meta file, as the rules require.

usage: harness_variant.py EXE FENFILE OUTFILE META "OPTION|OPTION|..."   (options are full setoption bodies)
"""
import hashlib
import subprocess
import sys

import chess

ERROR_MARKERS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe, options):
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
        self.sent_options = []
        for opt in options:
            if not opt:
                continue
            self.send("setoption " + opt)
            self.send("isready")
            self.wait_ready()
            self.sent_options.append("setoption " + opt)
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
    exe, fenfile, outfile, metafile, optspec = sys.argv[1:6]
    options = optspec.split("|")
    fens = [l.strip() for l in open(fenfile) if l.strip()]
    eng = Engine(exe, options)
    meta = ["exe_started: " + exe, "exe_sha256: " + sha256(exe),
            "id_name: " + str(eng.name),
            "option_lines_sent: " + ("; ".join(eng.sent_options) if eng.sent_options else "NONE"),
            "per_position_lines_sent: 'position fen <FEN>', 'isready', 'eval', 'isready'",
            "fenfile: " + fenfile, "fenfile_sha256: " + sha256(fenfile),
            "positions: %d" % len(fens)]
    rows, failures = [], []
    for i, fen in enumerate(fens):
        try:
            board = chess.Board(fen)
        except Exception as exc:
            failures.append((i, fen, "python-chess rejects: %s" % exc))
            continue
        mfen = board.mirror().fen()
        try:
            a = eng.eval_fen(fen)
            b = eng.eval_fen(mfen)
        except RuntimeError as exc:
            failures.append((i, fen, "engine: %s" % exc))
            eng = Engine(exe, options)
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

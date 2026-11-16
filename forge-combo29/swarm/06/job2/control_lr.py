#!/usr/bin/env python3
"""Controls for the left-right check (area 6 job 2).

mode self : evaluate each FEN twice -> the checker must report 0 differences.
mode shift: evaluate FEN i and FEN i+1 -> the checker MUST report differences, or the checker is blind.
Writes the same format harness_lr.py writes, so analyse_lr.py reads it unchanged.

usage: control_lr.py MODE EXE FENFILE OUTFILE META
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
    mode, exe, fenfile, outfile, metafile = sys.argv[1:6]
    fens = [l.strip() for l in open(fenfile) if l.strip()]
    usable = []
    skipped = 0
    for fen in fens:
        try:
            board = chess.Board(fen)
        except Exception:
            continue
        if board.castling_rights != 0:
            skipped += 1
            continue
        usable.append(fen)
    eng = Engine(exe)
    meta = ["exe_started: " + exe, "exe_sha256: " + sha256(exe), "id_name: " + str(eng.name),
            "option_lines_sent: NONE", "mode: " + mode, "fenfile: " + fenfile,
            "fenfile_sha256: " + sha256(fenfile), "positions_usable: %d" % len(usable),
            "skipped_castling_positions: %d" % skipped]
    rows = []
    for i, fen in enumerate(usable):
        if mode == "self":
            second = fen
        elif mode == "shift":
            if i + 1 >= len(usable):
                break
            second = usable[i + 1]
        else:
            raise SystemExit("bad mode " + mode)
        a = eng.eval_fen(fen)
        b = eng.eval_fen(second)
        rows.append((i, fen, second, a, b))
    eng.quit()
    with open(outfile, "w") as fh:
        for i, fen, second, a, b in rows:
            fh.write("FEN\t%d\t%s\n" % (i, fen))
            fh.write("MIR\t%d\t%s\n" % (i, second))
            fh.write("EVAL\t%d\t%s\n" % (i, a))
            fh.write("MEVAL\t%d\t%s\n" % (i, b))
    meta.append("rows_written: %d" % len(rows))
    open(metafile, "w").write("\n".join(meta) + "\n")
    print("mode=%s rows=%d" % (mode, len(rows)))


if __name__ == "__main__":
    main()

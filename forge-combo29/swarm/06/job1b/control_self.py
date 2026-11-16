#!/usr/bin/env python3
"""Controls for the mirror check of area 6 job 1.

control_self.py EXE FENFILE OUTFILE META   -> evaluates each FEN twice (same FEN, same engine process)
                                              the checker must find 0 differences.
control_shift.py EXE FENFILE OUTFILE META  -> evaluates FEN i and then FEN i+1, writing them as the
                                              "FEN"/"MIR" pair; the checker MUST find differences, or
                                              the checker cannot see a difference at all.
Both write the same file format as harness_mirror.py so compare.py reads them unchanged.
"""
import hashlib
import subprocess
import sys

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
    meta = ["exe_started: " + exe, "exe_sha256: " + sha256(exe),
            "option_lines_sent: NONE", "mode: " + mode,
            "fenfile: " + fenfile, "fenfile_sha256: " + sha256(fenfile),
            "positions: %d" % len(fens)]
    eng = Engine(exe)
    meta.append("id_name: " + str(eng.name))
    rows = []
    for i, fen in enumerate(fens):
        if mode == "self":
            second = fen
        elif mode == "shift":
            if i + 1 >= len(fens):
                break
            second = fens[i + 1]
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
    with open(metafile, "w") as fh:
        fh.write("\n".join(meta) + "\n")
    print("mode=%s rows=%d" % (mode, len(rows)))


if __name__ == "__main__":
    main()

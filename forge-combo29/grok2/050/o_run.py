#!/usr/bin/env python3
"""o_run.py EXE LABEL SWITCH FENFILE OUTDIR

SWITCH is omit, true, or false.
S14, then Threads 1, then Hash 16, then the switch when not omit.
ucinewgame + isready, position + isready, go depth 12, for each FEN.
Raw stdout is OUTDIR/o_LABEL.txt. Stops on unknown option, invalid value,
invalid FEN, or illegal move.
"""
import hashlib
import os
import select
import subprocess
import sys
import time

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
S14 = (
    ("LmrQuietBase", "93"),
    ("LmrQuietDivisor", "205"),
    ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"),
    ("LmrHistoryDivisor", "5643"),
    ("NullMoveBase", "5"),
    ("LmpBase", "8"),
    ("HistoryPruneMultiplier", "2220"),
    ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"),
    ("HistoryBonusMax", "2212"),
    ("SingularDepth", "6"),
    ("IirDepth", "2"),
    ("NonPawnCorrection", "true"),
    ("Threads", "1"),
    ("Hash", "16"),
)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def bad_line(line):
    return any(mark in line for mark in STOP_MARKS)


class Engine:
    def __init__(self, exe):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.lines = []
        self._buf = b""

    def send(self, command):
        self.proc.stdin.write((command + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, pred, timeout):
        end = time.monotonic() + timeout
        while True:
            if pred():
                return
            remaining = end - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("timeout after %d lines; last=%r" % (
                    len(self.lines), self.lines[-1] if self.lines else ""))
            ready, _, _ = select.select([self.proc.stdout], [], [], remaining)
            if not ready:
                raise TimeoutError("timeout after %d lines; last=%r" % (
                    len(self.lines), self.lines[-1] if self.lines else ""))
            chunk = os.read(self.proc.stdout.fileno(), 65536)
            if not chunk:
                if pred():
                    return
                raise EOFError("engine closed stdout after %d lines; last=%r" % (
                    len(self.lines), self.lines[-1] if self.lines else ""))
            self._buf += chunk
            while b"\n" in self._buf:
                raw, self._buf = self._buf.split(b"\n", 1)
                line = raw.decode("utf-8", "replace").rstrip("\r")
                self.lines.append(line)
                if bad_line(line):
                    raise RuntimeError("STOP: " + line)
                if pred():
                    return

    def close(self):
        err = ""
        try:
            if self.proc.poll() is None:
                self.send("quit")
                self.proc.wait(timeout=30)
        except Exception:
            self.proc.kill()
            self.proc.wait(timeout=10)
        if self.proc.stderr:
            err = self.proc.stderr.read().decode("utf-8", "replace")
        return err


def main():
    if len(sys.argv) != 6:
        raise SystemExit("usage: o_run.py EXE LABEL SWITCH FENFILE OUTDIR")
    exe, label, switch, fenfile, outdir = sys.argv[1:]
    if switch not in ("omit", "true", "false"):
        raise SystemExit("SWITCH must be omit, true, or false")
    os.makedirs(outdir, exist_ok=True)
    fens = [line.strip() for line in open(fenfile, encoding="utf-8") if line.strip()]
    options = ["setoption name %s value %s" % pair for pair in S14]
    if switch != "omit":
        options.append("setoption name HindsightDepth value %s" % switch)
    eng = Engine(exe)
    err = ""
    id_name = ""
    try:
        eng.send("uci")
        start = len(eng.lines)
        eng.read_until(lambda: any(line == "uciok" for line in eng.lines[start:]), 60)
        id_name = ""
        for line in eng.lines:
            if line.startswith("id name "):
                id_name = line[len("id name "):]
        for option in options:
            mark = len(eng.lines)
            eng.send(option)
            eng.send("isready")
            eng.read_until(lambda m=mark: any(line == "readyok" for line in eng.lines[m:]), 60)
        for index, fen in enumerate(fens, 1):
            mark = len(eng.lines)
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda m=mark: any(line == "readyok" for line in eng.lines[m:]), 60)
            mark = len(eng.lines)
            eng.send("position fen " + fen)
            eng.send("isready")
            eng.read_until(lambda m=mark: any(line == "readyok" for line in eng.lines[m:]), 60)
            mark = len(eng.lines)
            eng.send("go depth 12")
            eng.read_until(lambda m=mark: any(line.startswith("bestmove ") for line in eng.lines[m:]), 180)
            if index % 25 == 0 or index == len(fens):
                print("o %s %d/%d" % (label, index, len(fens)), file=sys.stderr, flush=True)
    finally:
        err = eng.close()
        stem = os.path.join(outdir, "o_%s" % label)
        with open(stem + ".txt", "w", encoding="utf-8") as f:
            f.write("\n".join(eng.lines) + ("\n" if eng.lines else ""))
        if err:
            with open(stem + ".err", "w", encoding="utf-8") as f:
                f.write(err)
        with open(stem + ".meta", "w", encoding="utf-8") as f:
            f.write("exe: %s\n" % os.path.abspath(exe))
            f.write("sha256: %s\n" % sha256_file(exe))
            f.write("id name: %s\n" % id_name)
            f.write("fenfile: %s\n" % fenfile)
            f.write("fen_sha256: %s\n" % sha256_file(fenfile))
            f.write("positions: %d\n" % len(fens))
            f.write("options:\n")
            for option in options:
                f.write(option + "\n")
    print("o %s wrote %d engine lines" % (label, len(eng.lines)))


if __name__ == "__main__":
    main()

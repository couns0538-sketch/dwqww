#!/usr/bin/env python3
"""run_rows.py EXE OUTFILE SETFILE DEPTH THREADS HASH
One fresh engine process per position. Writes raw transcripts with '### pos <n> <fen>' delimiters.
Also writes OUTFILE.meta (exe path started, sha256, id name, every option line sent).
"""
import hashlib
import os
import subprocess
import sys
import time

EXE = sys.argv[1]
OUT = sys.argv[2]
SETF = sys.argv[3]
DEPTH = int(sys.argv[4])
THREADS = int(sys.argv[5])
HASH = int(sys.argv[6])


def read_fens(path):
    fens = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ";" in line and line.count("/") == 7:
                line = line.split(";")[0].strip()
                parts = line.split()
                if len(parts) < 4:
                    line = " ".join(parts + ["w", "-", "-", "0", "1"])
            fens.append(line)
    return fens


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


OPTION_LINES = [
    f"setoption name Threads value {THREADS}",
    f"setoption name Hash value {HASH}",
    "setoption name LmrQuietBase value 93",
    "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13",
    "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643",
    "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8",
    "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24",
    "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212",
    "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2",
    "setoption name NonPawnCorrection value true",
]

BAD_WORDS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def send(proc, line):
    proc.stdin.write(line + "\n")
    proc.stdin.flush()


def read_until(proc, token, limit_s=20.0):
    """Read lines until one starts with token. Returns (lines, ok, hit_bad)."""
    lines = []
    deadline = time.time() + limit_s
    while True:
        if time.time() > deadline:
            return lines, False, False
        line = proc.stdout.readline()
        if line == "":
            return lines, False, False
        line = line.rstrip("\n")
        lines.append(line)
        if line.startswith(token):
            return lines, True, False
        if any(b in line for b in BAD_WORDS):
            return lines, False, True


def run_one(fen):
    proc = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    out = []
    try:
        send(proc, "uci")
        lines, ok, _ = read_until(proc, "uciok", 20)
        out += lines
        if not ok:
            out.append("### HARNESS_NOTE no uciok")
        for opt in OPTION_LINES:
            send(proc, opt)
            send(proc, "isready")
            lines, ok, bad = read_until(proc, "readyok", 20)
            out += lines
            if bad:
                out.append(f"### HARNESS_STOP bad answer to {opt}")
            if not ok:
                out.append(f"### HARNESS_STOP no readyok after {opt}")
                return out
        send(proc, "ucinewgame")
        send(proc, "isready")
        lines, ok, _ = read_until(proc, "readyok", 20)
        out += lines
        if not ok:
            out.append("### HARNESS_STOP no readyok after ucinewgame")
            return out
        send(proc, f"position fen {fen}")
        send(proc, "isready")
        lines, ok, bad = read_until(proc, "readyok", 20)
        out += lines
        if bad or not ok:
            out.append("### HARNESS_STOP position refused")
            return out
        send(proc, f"go depth {DEPTH}")
        lines, ok, _ = read_until(proc, "bestmove", 120)
        out += lines
        if not ok:
            out.append("### HARNESS_NOTE no bestmove")
        send(proc, "quit")
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    return out


def main():
    fens = read_fens(SETF)
    with open(OUT, "w") as f, open(OUT + ".meta", "w") as m:
        m.write(f"exe_started: {os.path.abspath(EXE)}\n")
        m.write(f"sha256: {sha256(EXE)}\n")
        m.write(f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
        m.write(f"setfile: {SETF} ({len(fens)} positions)\n")
        m.write(f"go line: go depth {DEPTH}\n")
        m.write("option lines sent (in this order, isready after each):\n")
        for opt in OPTION_LINES:
            m.write("  " + opt + "\n")
        m.write("sequence per position: uci/isready-after-each-setoption/ucinewgame/isready/"
                "position fen <fen>/isready/go depth " + str(DEPTH) + "/read to bestmove/quit\n")
        idline = ""
        p = subprocess.run([EXE], input="uci\nquit\n", capture_output=True, text=True)
        for line in p.stdout.splitlines():
            if line.startswith("id name"):
                idline = line
        m.write("id_name: " + idline + "\n")
        for i, fen in enumerate(fens):
            f.write(f"### pos {i} {fen}\n")
            for line in run_one(fen):
                f.write(line + "\n")
            f.write("### end\n")
            f.flush()
    print(f"done {len(fens)} positions -> {OUT}")


if __name__ == "__main__":
    main()

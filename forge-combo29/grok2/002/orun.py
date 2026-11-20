#!/usr/bin/env python3
"""O-run harness. One engine process.

S14 in the brief's order, then Threads 1, Hash 16, then an optional switch.
After every setoption and every position: isready, and every line up to readyok.
ucinewgame + isready before every position, then go depth 12.

Usage: orun.py EXE FENS OUTBASE [SWITCH true|false]
Writes OUTBASE.txt (transcript) and OUTBASE.meta.
"""
import hashlib
import os
import subprocess
import sys
import time

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")

OPTIONS = [
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
]


def main():
    if len(sys.argv) not in (4, 6):
        sys.exit("usage: orun.py EXE FENS OUTBASE [SWITCH true|false]")
    exe = os.path.abspath(sys.argv[1])
    fen_path = sys.argv[2]
    outbase = sys.argv[3]
    options = list(OPTIONS)
    if len(sys.argv) == 6:
        if sys.argv[5] not in ("true", "false"):
            sys.exit("switch value must be true or false")
        options.append((sys.argv[4], sys.argv[5]))
    fens = []
    with open(fen_path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                fens.append(line)
    if len(fens) != 200:
        sys.exit(f"expected 200 fens, got {len(fens)}")

    digest = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    transcript = open(outbase + ".txt", "w", encoding="utf-8")
    options_sent = []
    id_name = ""

    def send(line):
        transcript.write("# SEND " + line + "\n")
        transcript.flush()
        assert proc.stdin is not None
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(pred, timeout_s):
        assert proc.stdout is not None
        end = time.time() + timeout_s
        got = []
        while time.time() < end:
            line = proc.stdout.readline()
            if line == "":
                transcript.write("# EOF\n")
                transcript.flush()
                sys.exit("STOP eof from engine")
            transcript.write(line)
            transcript.flush()
            text = line.rstrip("\n")
            got.append(text)
            low = text.lower()
            for bad in BAD:
                if bad.lower() in low:
                    sys.exit("STOP " + text)
            if pred(text):
                return got
        sys.exit("STOP timeout waiting")

    def isready():
        send("isready")
        read_until(lambda s: s.startswith("readyok"), 60)

    try:
        send("uci")
        lines = read_until(lambda s: s.startswith("uciok"), 30)
        for line in lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        for name, value in options:
            opt = f"setoption name {name} value {value}"
            options_sent.append(opt)
            send(opt)
            isready()
        for index, fen in enumerate(fens, start=1):
            transcript.write(f"# POS {index}\n")
            transcript.flush()
            send("ucinewgame")
            isready()
            send("position fen " + fen)
            isready()
            send("go depth 12")
            read_until(lambda s: s.startswith("bestmove"), 180)
            if index % 20 == 0:
                print(f"pos {index}", flush=True)
        send("quit")
    finally:
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        transcript.close()

    with open(outbase + ".meta", "w", encoding="utf-8") as meta:
        meta.write(f"exe: {exe}\n")
        meta.write(f"sha256: {digest}\n")
        meta.write(f"id_name: {id_name}\n")
        meta.write("options_sent:\n")
        for opt in options_sent:
            meta.write(opt + "\n")
    print(f"wrote {outbase}.txt {outbase}.meta")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""o_run.py: depth-12 node counts, one engine process, S14 before every search.

Usage:
  python3 o_run.py EXE FENS OUTBASE [SWITCH]
SWITCH is omitted for exe B, or true / false (lower case) for IdeaB1.
After every setoption and every position this sends isready and reads until readyok.
It stops on unknown option, invalid value, invalid FEN, or illegal move.
OUTBASE.txt is the engine transcript. OUTBASE.meta describes the process.
"""
import hashlib
import select
import subprocess
import sys

STOPS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
S14 = [
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


class Engine:
    def __init__(self, exe):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )

    def send(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, raw, predicate, timeout):
        got = []
        while True:
            ready, _, _ = select.select([self.proc.stdout], [], [], timeout)
            if not ready:
                sys.exit(f"STOP: timeout waiting after {got[-1].rstrip() if got else 'no output'}")
            line = self.proc.stdout.readline()
            if line == b"":
                sys.exit("STOP: engine closed stdout")
            text = line.decode("utf-8", "replace")
            raw.write(text)
            raw.flush()
            for bad in STOPS:
                if bad in text:
                    sys.exit(f"STOP: {text.strip()}")
            got.append(text)
            if predicate(text):
                return got


def main():
    if len(sys.argv) not in (4, 5):
        sys.exit(__doc__)
    exe, fens_path, outbase = sys.argv[1], sys.argv[2], sys.argv[3]
    switch = sys.argv[4] if len(sys.argv) == 5 else None
    if switch not in (None, "true", "false"):
        sys.exit("STOP: switch must be true or false")
    options = list(S14)
    if switch is not None:
        options.append(("IdeaB1", switch))
    fens = [line.strip() for line in open(fens_path, encoding="utf-8") if line.strip()]
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    eng = Engine(exe)
    with open(outbase + ".txt", "w", encoding="utf-8") as raw:
        eng.send("uci")
        hello = eng.read_until(raw, lambda t: t.startswith("uciok"), 30)
        id_name = next((t.strip() for t in hello if t.startswith("id name ")), "id name MISSING")
        eng.send("isready")
        eng.read_until(raw, lambda t: t.startswith("readyok"), 30)
        for number, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(raw, lambda t: t.startswith("readyok"), 30)
            for name, value in options:
                eng.send(f"setoption name {name} value {value}")
                eng.send("isready")
                eng.read_until(raw, lambda t: t.startswith("readyok"), 30)
            eng.send(f"position fen {fen}")
            eng.send("isready")
            eng.read_until(raw, lambda t: t.startswith("readyok"), 30)
            eng.send("go depth 12")
            eng.read_until(raw, lambda t: t.startswith("bestmove"), 180)
            if number % 50 == 0:
                print(f"position {number}", flush=True)
        eng.send("quit")
    with open(outbase + ".meta", "w", encoding="utf-8") as meta:
        meta.write(f"exe {exe}\n")
        meta.write(f"sha256 {sha}\n")
        meta.write(id_name + "\n")
        meta.write("options\n")
        for name, value in options:
            meta.write(f"setoption name {name} value {value}\n")
        meta.write(f"fens {fens_path}\n")
        meta.write(f"positions {len(fens)}\n")
    print(f"O_DONE {outbase} positions {len(fens)}", flush=True)


if __name__ == "__main__":
    main()

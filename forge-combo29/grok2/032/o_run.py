#!/usr/bin/env python3
"""Depth-12 O run. Usage: o_run.py <exe> <fens> <out.txt> <meta> [IdeaB1 true|false]"""
import hashlib
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
]


def main():
    exe, fens, out_path, meta_path = sys.argv[1:5]
    switch = sys.argv[5] if len(sys.argv) > 5 else None
    fens_lines = [ln.strip() for ln in open(fens, encoding="utf-8") if ln.strip()]
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    log = []
    sent = []

    def send(line):
        sent.append(line)
        log.append(">> " + line)
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(ok):
        while True:
            line = proc.stdout.readline()
            if line == "":
                sys.exit("STOP: engine closed stdout")
            line = line.rstrip("\n")
            log.append(line)
            for bad in STOPS:
                if bad in line:
                    dump()
                    sys.exit("STOP: " + line)
            if ok(line):
                return line

    def dump():
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(log) + "\n")

    send("uci")
    read_until(lambda s: s == "uciok")
    id_name = next(s[len("id name "):] for s in log if s.startswith("id name "))
    options = [("Threads", "1"), ("Hash", "16")] + S14
    if switch is not None:
        options.append(("IdeaB1", switch))
    for name, value in options:
        send(f"setoption name {name} value {value}")
        send("isready")
        read_until(lambda s: s == "readyok")
    for fen in fens_lines:
        send("ucinewgame")
        send("isready")
        read_until(lambda s: s == "readyok")
        send(f"position fen {fen}")
        send("isready")
        read_until(lambda s: s == "readyok")
        send("go depth 12")
        read_until(lambda s: s.startswith("bestmove "))
    send("quit")
    proc.stdin.close()
    rest = proc.stdout.read()
    if rest:
        log.extend(rest.splitlines())
    proc.wait(timeout=30)
    dump()
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(f"exe {exe}\n")
        f.write(f"sha256 {sha}\n")
        f.write(f"id name {id_name}\n")
        for line in sent:
            if line.startswith("setoption "):
                f.write(line + "\n")
    print(f"wrote {out_path} positions {len(fens_lines)}")


if __name__ == "__main__":
    main()

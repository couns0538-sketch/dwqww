#!/usr/bin/env python3
"""o_run.py EXE FENS RAW META SWITCH
SWITCH is omit, false, or true.
Speaks UCI. Stops on unknown option, invalid value, invalid FEN, illegal move.
S14 in the brief's order, then Threads 1, then Hash 16, then the switch if given.
"""
import hashlib
import subprocess
import sys

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

STOP = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def die(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(1)


def main():
    if len(sys.argv) not in (5, 6):
        die("usage: o_run.py EXE FENS RAW META [SWITCH true|false]")
    exe, fens_path, raw_path, meta_path = sys.argv[1:5]
    switch = sys.argv[5] if len(sys.argv) == 6 else None
    if switch is not None and switch not in ("true", "false"):
        die("switch must be true or false")
    options = list(S14)
    if switch is not None:
        options.append(("IdeaS32", switch))
    with open(fens_path, encoding="utf-8") as f:
        fens = [line.strip() for line in f if line.strip()]
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    raw = open(raw_path, "w", encoding="utf-8")
    id_name = ""

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(token, limit=200000):
        lines = []
        for _ in range(limit):
            line = proc.stdout.readline()
            if line == "":
                raw.flush()
                die(f"EOF waiting for {token}; last={lines[-3:]}")
            raw.write(line)
            lines.append(line.rstrip("\n"))
            if any(mark in line for mark in STOP):
                raw.flush()
                die(f"STOP: {line.rstrip()}")
            if line.startswith(token):
                return lines
        raw.flush()
        die(f"too many lines waiting for {token}")

    try:
        send("uci")
        uci_lines = read_until("uciok")
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line[len("id name "):]
        sent = []
        for name, value in options:
            line = f"setoption name {name} value {value}"
            send(line)
            sent.append(line)
            send("isready")
            read_until("readyok")
        for i, fen in enumerate(fens, start=1):
            send("ucinewgame")
            send("isready")
            read_until("readyok")
            send(f"position fen {fen}")
            send("isready")
            read_until("readyok")
            send("go depth 12")
            read_until("bestmove ")
            if i % 25 == 0:
                sys.stderr.write(f"{i}/{len(fens)}\n")
        send("quit")
        proc.wait(timeout=30)
    finally:
        raw.flush()
        raw.close()
        if proc.poll() is None:
            proc.kill()
    with open(meta_path, "w", encoding="utf-8") as m:
        m.write(f"exe {exe}\n")
        m.write(f"sha256 {sha}\n")
        m.write(f"id name {id_name}\n")
        for line in sent:
            m.write(line + "\n")
    print(f"ok {len(fens)} -> {raw_path}")


if __name__ == "__main__":
    main()

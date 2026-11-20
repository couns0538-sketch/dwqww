#!/usr/bin/env python3
"""o_run.py EXE FENS RAW META [SWITCH true|false]

One engine process. S14, then Threads 1, Hash 16, then the switch if given.
After every setoption and every position: isready, read every line to readyok.
Stop on unknown option, invalid value, invalid FEN, illegal move.
ucinewgame + isready before every position. go depth 12.
"""
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


def stop_if(line):
    for mark in STOP:
        if mark in line:
            sys.exit(f"STOP: {line}")


def main():
    if len(sys.argv) not in (5, 7):
        sys.exit("usage: o_run.py EXE FENS RAW META [SWITCH true|false]")
    exe, fens, raw_path, meta_path = sys.argv[1:5]
    switch = None
    if len(sys.argv) == 7:
        switch = (sys.argv[5], sys.argv[6])
        if switch[1] not in ("true", "false"):
            sys.exit("switch value must be true or false")
    options = list(S14)
    if switch is not None:
        options.append(switch)
    with open(fens, encoding="utf-8") as fh:
        positions = [line.strip() for line in fh if line.strip()]
    if len(positions) != 200:
        sys.exit(f"STOP: expected 200 fens, got {len(positions)}")
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    id_name = ""

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(token):
        got = []
        while True:
            line = proc.stdout.readline()
            if line == "":
                sys.exit(f"STOP: engine closed before {token}")
            raw.write(line)
            text = line.rstrip("\n")
            stop_if(text)
            got.append(text)
            if text == token or text.startswith(token + " "):
                return got
    with open(raw_path, "w", encoding="utf-8") as raw:
        send("uci")
        for text in read_until("uciok"):
            if text.startswith("id name "):
                id_name = text[len("id name "):]
        for name, value in options:
            send(f"setoption name {name} value {value}")
            send("isready")
            read_until("readyok")
        for fen in positions:
            send("ucinewgame")
            send("isready")
            read_until("readyok")
            send(f"position fen {fen}")
            send("isready")
            read_until("readyok")
            send("go depth 12")
            read_until("bestmove")
        send("quit")
        proc.stdin.close()
        rest = proc.stdout.read()
        if rest:
            raw.write(rest)
            for line in rest.splitlines():
                stop_if(line)
    rc = proc.wait()
    if rc != 0:
        sys.exit(f"STOP: engine exit {rc}")
    sha = subprocess.check_output(["sha256sum", exe], text=True).split()[0]
    with open(meta_path, "w", encoding="utf-8") as meta:
        meta.write(f"exe: {exe}\n")
        meta.write(f"sha256: {sha}\n")
        meta.write(f"id name: {id_name}\n")
        meta.write("options sent:\n")
        for name, value in options:
            meta.write(f"setoption name {name} value {value}\n")
    print(f"o_run wrote {raw_path} positions {len(positions)} id {id_name}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""o_run.py EXE RAW_OUT FENS [SWITCH true|false]
One engine process. S14, then Threads 1, Hash 16, then the switch if given.
ucinewgame + isready, position + isready, go depth 12 for each FEN.
Stops on unknown option, invalid value, invalid FEN, illegal move.
Writes RAW_OUT (engine stdout) and RAW_OUT with .meta beside it.
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
SWITCH = "IdeaS32"
STOPS = ("unknown option", "invalid value", "invalid fen", "illegal move")


def main():
    exe = sys.argv[1]
    raw_path = sys.argv[2]
    fens_path = sys.argv[3]
    switch = sys.argv[4] if len(sys.argv) > 4 else None
    options = list(S14)
    if switch is not None:
        if switch not in ("true", "false"):
            sys.exit(f"STOP: switch must be true or false, got {switch}")
        options.append((SWITCH, switch))
    fens = [ln.strip() for ln in open(fens_path, encoding="utf-8") if ln.strip()]
    digest = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    proc = subprocess.Popen(
        [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    sent = []
    id_name = ""

    def send(line):
        sent.append(line)
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(marker):
        nonlocal id_name
        lines = []
        while True:
            line = proc.stdout.readline()
            if line == "":
                sys.exit(f"STOP: engine closed stdout waiting for {marker}")
            line = line.rstrip("\r\n")
            raw.write(line + "\n")
            raw.flush()
            lines.append(line)
            if line.startswith("id name ") and not id_name:
                id_name = line[len("id name "):]
            low = line.lower()
            for bad in STOPS:
                if bad in low:
                    sys.exit(f"STOP: {line}")
            if marker in line:
                return lines

    with open(raw_path, "w", encoding="utf-8") as raw:
        send("uci")
        read_until("uciok")
        for name, value in options:
            send(f"setoption name {name} value {value}")
            send("isready")
            read_until("readyok")
        for fen in fens:
            send("ucinewgame")
            send("isready")
            read_until("readyok")
            send(f"position fen {fen}")
            send("isready")
            read_until("readyok")
            send(f"go depth 12")
            read_until("bestmove")
        send("quit")
        proc.stdin.close()
        rest = proc.stdout.read()
        if rest:
            raw.write(rest)
        proc.wait(timeout=30)

    meta_path = raw_path + ".meta"
    with open(meta_path, "w", encoding="utf-8") as m:
        m.write(f"exe: {exe}\n")
        m.write(f"sha256: {digest}\n")
        m.write(f"id name: {id_name}\n")
        m.write("options:\n")
        for line in sent:
            if line.startswith("setoption "):
                m.write(line + "\n")
    print(f"wrote {raw_path} positions {len(fens)} id {id_name}")


if __name__ == "__main__":
    main()

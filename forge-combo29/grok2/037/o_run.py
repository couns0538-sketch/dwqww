#!/usr/bin/env python3
"""o_run.py EXE OUT_PREFIX [true|false]
One engine process. S14, Threads 1, Hash 16, then optional IdeaK4.
ucinewgame + isready, position + isready, go depth 12, for each FEN in ~/first200.fens.
Stops on unknown option, invalid value, invalid FEN, illegal move.
"""
import hashlib
import subprocess
import sys

STOP_BITS = ("unknown option", "invalid value", "invalid fen", "illegal move")
S14 = [
    ("Threads", "1"),
    ("Hash", "16"),
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
    exe = sys.argv[1]
    prefix = sys.argv[2]
    switch = sys.argv[3] if len(sys.argv) > 3 else None
    options = list(S14)
    if switch is not None:
        if switch not in ("true", "false"):
            sys.exit(f"STOP switch must be true or false, got {switch}")
        options.append(("IdeaK4", switch))
    fens = [ln.strip() for ln in open("/home/ubuntu/first200.fens", encoding="utf-8") if ln.strip()]
    if len(fens) != 200:
        sys.exit(f"STOP fen count {len(fens)}")
    proc = subprocess.Popen(
        [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    raw = open(prefix + ".txt", "w", encoding="utf-8")
    sent = []
    id_name = ""

    def send(line):
        sent.append(line)
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(done, label):
        nonlocal id_name
        while True:
            line = proc.stdout.readline()
            if line == "":
                sys.exit(f"STOP eof during {label}")
            line = line.rstrip("\r\n")
            raw.write(line + "\n")
            raw.flush()
            if line.startswith("id name ") and not id_name:
                id_name = line[len("id name "):]
            low = line.lower()
            if any(bit in low for bit in STOP_BITS):
                sys.exit(f"STOP {line}")
            if done(line):
                return line

    send("uci")
    read_until(lambda s: s == "uciok", "uci")
    for name, value in options:
        send(f"setoption name {name} value {value}")
        send("isready")
        read_until(lambda s: s == "readyok", f"setoption {name}")
    for fen in fens:
        send("ucinewgame")
        send("isready")
        read_until(lambda s: s == "readyok", "ucinewgame")
        send(f"position fen {fen}")
        send("isready")
        read_until(lambda s: s == "readyok", "position")
        send("go depth 12")
        read_until(lambda s: s.startswith("bestmove "), "go")
    send("quit")
    proc.stdin.close()
    # drain
    while True:
        line = proc.stdout.readline()
        if line == "":
            break
        raw.write(line.rstrip("\r\n") + "\n")
    rc = proc.wait()
    raw.close()
    h = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    with open(prefix + ".meta", "w", encoding="utf-8") as m:
        m.write(f"exe: {exe}\n")
        m.write(f"sha256: {h}\n")
        m.write(f"id name: {id_name}\n")
        m.write("options sent:\n")
        for line in sent:
            if line.startswith("setoption "):
                m.write(line + "\n")
        m.write(f"engine_exit: {rc}\n")
    print(f"WROTE {prefix} positions 200 exit {rc}")

if __name__ == "__main__":
    main()

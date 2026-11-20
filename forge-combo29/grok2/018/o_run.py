#!/usr/bin/env python3
"""o_run.py EXE FENS OUT_PREFIX [SWITCH true|false]

One engine process. Sends Threads 1, Hash 16, then S14 in the brief's order,
then the switch if one was given. Before every position: ucinewgame + isready.
After every setoption and every position command: isready, and every line is
read up to readyok. A search is read up to the bestmove line. Stops on
unknown option, invalid value, invalid FEN, or illegal move.
Writes OUT_PREFIX.txt (the transcript) and OUT_PREFIX.meta.
"""
import hashlib
import os
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
]
STOP = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def main():
    if len(sys.argv) not in (4, 6):
        sys.exit("usage: o_run.py EXE FENS OUT_PREFIX [SWITCH true|false]")
    exe = os.path.abspath(sys.argv[1])
    fens_path = sys.argv[2]
    out = sys.argv[3]
    switch = (sys.argv[4], sys.argv[5]) if len(sys.argv) == 6 else None
    if switch and switch[1] not in ("true", "false"):
        sys.exit("switch value must be true or false")
    fens = [ln.strip() for ln in open(fens_path, encoding="utf-8") if ln.strip()]
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    options = [("Threads", "1"), ("Hash", "16"), *S14]
    if switch:
        options.append(switch)
    sent = [f"setoption name {name} value {value}" for name, value in options]
    lines = []
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    def dump():
        with open(out + ".txt", "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")

    def fail(msg):
        dump()
        sys.exit(msg)

    def send(cmd):
        lines.append(">> " + cmd)
        assert proc.stdin is not None
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()

    def read_until(done, label):
        assert proc.stdout is not None
        while True:
            raw = proc.stdout.readline()
            if raw == "":
                fail(f"STOP: engine closed during {label}")
            line = raw.rstrip("\r\n")
            lines.append(line)
            low = line.lower()
            for bad in STOP:
                if bad.lower() in low:
                    fail(f"STOP: {bad} during {label}: {line}")
            if done(line):
                return line

    id_name = ""

    def take_id(line):
        nonlocal id_name
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
        return line == "uciok"

    send("uci")
    read_until(take_id, "uci")
    for cmd in sent:
        send(cmd)
        send("isready")
        read_until(lambda line: line == "readyok", cmd)
    for index, fen in enumerate(fens, start=1):
        send("ucinewgame")
        send("isready")
        read_until(lambda line: line == "readyok", f"ucinewgame {index}")
        send(f"position fen {fen}")
        send("isready")
        read_until(lambda line: line == "readyok", f"position {index}")
        send("go depth 12")
        read_until(lambda line: line.startswith("bestmove "), f"go {index}")
    send("quit")
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    dump()
    with open(out + ".meta", "w", encoding="utf-8") as handle:
        handle.write(f"exe: {exe}\n")
        handle.write(f"sha256: {sha}\n")
        handle.write(f"id name: {id_name}\n")
        handle.write("options:\n")
        for cmd in sent:
            handle.write(cmd + "\n")
    print(f"{len(fens)} positions -> {out}.txt")


if __name__ == "__main__":
    main()

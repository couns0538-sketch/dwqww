#!/usr/bin/env python3
"""o_run.py EXE OUT META SWITCH VALUE
SWITCH is IdeaK4 or none. VALUE is true, false, or none.
S14 then Threads 1 Hash 16, then the switch if named.
One fresh process. isready after every setoption and every position.
Stops on unknown option, invalid value, invalid FEN, illegal move.
"""
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
    ("Threads", "1"),
    ("Hash", "16"),
]


def main():
    exe, out_path, meta_path, switch, value = sys.argv[1:6]
    fens_path = sys.argv[6]
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    log = []
    options = []
    id_name = ""

    def send(line):
        log.append(">> " + line)
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(done):
        while True:
            line = proc.stdout.readline()
            if line == "":
                dump()
                sys.exit("STOP: engine closed the pipe")
            line = line.rstrip("\n")
            log.append(line)
            for s in STOPS:
                if s in line:
                    dump()
                    sys.exit(f"STOP: {line}")
            if done(line):
                return line

    def dump():
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(log) + "\n")

    send("uci")
    while True:
        line = read_until(lambda l: l == "uciok" or l.startswith("id name "))
        if line.startswith("id name "):
            id_name = line[len("id name "):]
            continue
        break
    send("isready")
    read_until(lambda l: l == "readyok")

    for name, val in S14:
        opt = f"setoption name {name} value {val}"
        options.append(opt)
        send(opt)
        send("isready")
        read_until(lambda l: l == "readyok")

    if switch != "none":
        opt = f"setoption name {switch} value {value}"
        options.append(opt)
        send(opt)
        send("isready")
        read_until(lambda l: l == "readyok")

    fens = [ln.strip() for ln in open(fens_path, encoding="utf-8") if ln.strip()]
    for i, fen in enumerate(fens, 1):
        send(f"ucinewgame")
        send("isready")
        read_until(lambda l: l == "readyok")
        send(f"position fen {fen}")
        send("isready")
        read_until(lambda l: l == "readyok")
        send("go depth 12")
        read_until(lambda l: l.startswith("bestmove "))
        if i % 50 == 0:
            print(f"{out_path} {i}/{len(fens)}", flush=True)

    send("quit")
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    dump()
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(f"exe {exe}\n")
        f.write(f"sha256 {sha}\n")
        f.write(f"id name {id_name}\n")
        for opt in options:
            f.write(f"option {opt}\n")
        f.write(f"fens {fens_path}\n")
        f.write(f"positions {len(fens)}\n")
    print(f"WROTE {out_path} positions {len(fens)} id {id_name}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""o_run.py EXE OUT SWITCH FENS

One engine process. S14 in the brief's order, then Threads 1, Hash 16,
then SWITCH (IdeaB1) unless SWITCH is omit. ucinewgame + isready before
every position, isready after every setoption and every position. Stops
on unknown option, invalid value, invalid FEN, or illegal move.
OUT is the engine's raw stdout. OUT.meta records the exe, sha256, id name,
and every option line sent.
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
STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def main():
    if len(sys.argv) != 5:
        sys.exit("usage: o_run.py EXE OUT SWITCH FENS")
    exe, out_path, switch, fens_path = sys.argv[1:]
    if switch not in ("omit", "true", "false"):
        sys.exit("SWITCH must be omit, true, or false")
    fens = [line.strip() for line in open(fens_path, encoding="utf-8") if line.strip()]
    options = [f"setoption name {name} value {value}" for name, value in S14]
    if switch != "omit":
        options.append(f"setoption name IdeaB1 value {switch}")

    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    raw = []

    def stop(why):
        proc.kill()
        open(out_path, "w", encoding="utf-8").write("".join(raw))
        sys.exit(why)

    def read_until(pred):
        while True:
            line = proc.stdout.readline()
            if line == "":
                stop("STOP: engine closed stdout")
            raw.append(line)
            if any(mark in line for mark in STOP_MARKS):
                stop("STOP: " + line.strip())
            if pred(line):
                return line

    def send(text):
        proc.stdin.write(text + "\n")
        proc.stdin.flush()

    send("uci")
    id_line = read_until(lambda line: line.startswith("uciok"))
    id_name = ""
    for line in raw:
        if line.startswith("id name "):
            id_name = line[len("id name "):].rstrip("\r\n")
            break
    if not id_name:
        stop("STOP: no id name before uciok: " + id_line.strip())

    for option in options:
        send(option)
        send("isready")
        read_until(lambda line: line.startswith("readyok"))

    for index, fen in enumerate(fens, start=1):
        send("ucinewgame")
        send("isready")
        read_until(lambda line: line.startswith("readyok"))
        send("position fen " + fen)
        send("isready")
        read_until(lambda line: line.startswith("readyok"))
        send("go depth 12")
        read_until(lambda line: line.startswith("bestmove"))
        if index % 50 == 0:
            print(f"{index}/{len(fens)}", flush=True)

    send("quit")
    proc.stdin.close()
    rest = proc.stdout.read()
    if rest:
        raw.append(rest)
    code = proc.wait()
    open(out_path, "w", encoding="utf-8").write("".join(raw))
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    meta_path = out_path + ".meta"
    with open(meta_path, "w", encoding="utf-8") as meta:
        meta.write(f"exe={exe}\n")
        meta.write(f"sha256={sha}\n")
        meta.write(f"id_name={id_name}\n")
        for option in options:
            meta.write(option + "\n")
        meta.write(f"fens={fens_path}\n")
        meta.write(f"positions={len(fens)}\n")
        meta.write(f"exit={code}\n")
    print(f"wrote {out_path} positions {len(fens)} exit {code}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""o_run.py EXE OUT_TXT OUT_META [SWITCH VALUE]
Depth-12 O run. One engine process. S14 options, then optional switch.
Stops on unknown option, invalid value, invalid FEN, illegal move.
"""
import hashlib
import sys

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")

S14 = [
    "setoption name Threads value 1",
    "setoption name Hash value 16",
    "setoption name LmrQuietBase value 93",
    "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13",
    "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643",
    "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8",
    "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24",
    "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212",
    "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2",
    "setoption name NonPawnCorrection value true",
]


def main():
    exe = sys.argv[1]
    out_txt = sys.argv[2]
    out_meta = sys.argv[3]
    switch = sys.argv[4] if len(sys.argv) > 4 else None
    value = sys.argv[5] if len(sys.argv) > 5 else None
    fens = [ln.strip() for ln in open("/home/ubuntu/first200.fens", encoding="utf-8") if ln.strip()]
    if len(fens) != 200:
        sys.exit(f"STOP: expected 200 fens, got {len(fens)}")

    import subprocess

    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    raw = []
    options = list(S14)
    if switch:
        options.append(f"setoption name {switch} value {value}")

    def fail(msg):
        with open(out_txt, "w", encoding="utf-8") as f:
            f.write("\n".join(raw) + ("\n" if raw else ""))
            f.write(f"HARNESS {msg}\n")
        try:
            proc.kill()
        except OSError:
            pass
        sys.exit(msg)

    def send(line):
        if proc.stdin is None:
            fail("STOP: stdin closed")
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_line(what):
        if proc.stdout is None:
            fail(f"STOP: stdout closed waiting for {what}")
        line = proc.stdout.readline()
        if line == "":
            fail(f"STOP: eof waiting for {what}")
        line = line.rstrip("\n")
        raw.append(line)
        for mark in STOP_MARKS:
            if mark in line:
                fail(f"STOP: {line}")
        return line

    def read_until(pred, what):
        while True:
            line = read_line(what)
            if pred(line):
                return line

    id_name = ""

    def on_uci(line):
        nonlocal id_name
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
        return line == "uciok"

    send("uci")
    read_until(on_uci, "uciok")

    def ready(why):
        send("isready")
        read_until(lambda line: line == "readyok", f"readyok after {why}")

    for opt in options:
        send(opt)
        ready(opt)

    for index, fen in enumerate(fens, 1):
        send("ucinewgame")
        ready(f"ucinewgame {index}")
        send(f"position fen {fen}")
        ready(f"position {index}")
        send("go depth 12")
        while True:
            line = read_line(f"search {index}")
            if line.startswith("bestmove "):
                break

    send("quit")
    proc.wait(timeout=30)

    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(raw) + "\n")
    digest = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    with open(out_meta, "w", encoding="utf-8") as f:
        f.write(f"exe {exe}\n")
        f.write(f"sha256 {digest}\n")
        f.write(f"id name {id_name}\n")
        for opt in options:
            f.write(opt + "\n")
    print(f"wrote {out_txt} lines {len(raw)} id {id_name}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""o_run.py EXE FENS OUT SWITCH
SWITCH is none (do not send it), true, or false.
One engine process. S14 in the brief's order, then Threads 1, then Hash 16, then the switch.
ucinewgame and isready before every position. Raw engine stdout in OUT.
"""
import hashlib
import subprocess
import sys

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")
S14 = [
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
    "setoption name Threads value 1",
    "setoption name Hash value 16",
]


def main():
    if len(sys.argv) != 5:
        sys.exit("usage: o_run.py EXE FENS OUT SWITCH")
    exe, fens_path, out_path, switch = sys.argv[1:]
    if switch not in ("none", "true", "false"):
        sys.exit("SWITCH must be none, true, or false")
    fens = [ln.strip() for ln in open(fens_path, encoding="utf-8") if ln.strip()]
    if len(fens) != 200:
        sys.exit(f"STOP: expected 200 fens, got {len(fens)}")
    options = list(S14)
    if switch != "none":
        options.append(f"setoption name IdeaS10 value {switch}")
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

    def read_until(pred):
        nonlocal id_name
        while True:
            line = proc.stdout.readline()
            if line == "":
                sys.exit("STOP: engine closed stdout")
            raw.write(line)
            if line.startswith("id name ") and not id_name:
                id_name = line[len("id name "):].rstrip("\n")
            for bad in BAD:
                if bad in line:
                    proc.kill()
                    sys.exit(f"STOP: {line.rstrip()}")
            if pred(line):
                return

    with open(out_path, "w", encoding="utf-8") as raw:
        send("uci")
        read_until(lambda ln: ln.startswith("uciok"))
        for opt in options:
            send(opt)
            send("isready")
            read_until(lambda ln: ln.startswith("readyok"))
        for fen in fens:
            send("ucinewgame")
            send("isready")
            read_until(lambda ln: ln.startswith("readyok"))
            send(f"position fen {fen}")
            send("isready")
            read_until(lambda ln: ln.startswith("readyok"))
            send("go depth 12")
            read_until(lambda ln: ln.startswith("bestmove "))
        send("quit")
        proc.stdin.close()
        rest = proc.stdout.read()
        if rest:
            raw.write(rest)
    rc = proc.wait()
    digest = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    meta_path = out_path + ".meta"
    with open(meta_path, "w", encoding="utf-8") as m:
        m.write(f"exe: {exe}\n")
        m.write(f"sha256: {digest}\n")
        m.write(f"id name: {id_name}\n")
        m.write("option lines sent:\n")
        for opt in options:
            m.write(opt + "\n")
        m.write(f"engine_exit: {rc}\n")
        m.write(f"positions: {len(fens)}\n")
    print(f"wrote {out_path} id={id_name} exit={rc}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""probe2.py FEN DEPTH [--opts s14|none] [--hash N]

SAFE harness: keeps stdin open, reads stdout line by line until `bestmove`, and only
then sends `quit`. Never closes stdin while a search runs (a pipelined
`position/go/quit` makes this build answer a fabricated bestmove with 0 nodes).

Prints the full transcript to stdout. Nothing is interpreted here.
"""
import argparse
import subprocess
import sys

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
EXE = "/home/ubuntu/builds/rel/forge"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fen")
    ap.add_argument("depth", type=int)
    ap.add_argument("--opts", default="s14", choices=["s14", "none"])
    ap.add_argument("--hash", default="16")
    ap.add_argument("--exe", default=EXE)
    a = ap.parse_args()

    proc = subprocess.Popen([a.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(c):
        proc.stdin.write(c + "\n")
        proc.stdin.flush()

    def read_until(pred, echo=True):
        got = []
        while True:
            line = proc.stdout.readline()
            if not line:
                return got, False
            line = line.rstrip("\n")
            got.append(line)
            if echo:
                print(line)
            if pred(line):
                return got, True

    send("uci")
    read_until(lambda l: l.startswith("uciok"))
    send("setoption name MultiPV value 1")
    send("setoption name Threads value 1")
    send("setoption name Hash value %s" % a.hash)
    if a.opts == "s14":
        for k, v in S14:
            send("setoption name %s value %s" % (k, v))
    send("isready")
    read_until(lambda l: l == "readyok")
    print("### ucinewgame")
    send("ucinewgame")
    send("isready")
    read_until(lambda l: l == "readyok")
    print("### position fen " + a.fen)
    send("position fen " + a.fen)
    send("isready")
    got, ok = read_until(lambda l: l == "readyok")
    print("### go depth %d" % a.depth)
    send("go depth %d" % a.depth)
    infos, ok = read_until(lambda l: l.startswith("bestmove"))
    if not ok:
        print("### STDOUT CLOSED BEFORE bestmove")
    send("quit")
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    pv = [l for l in infos if l.startswith("info depth") and " pv " in l]
    print("### SUMMARY last_info_present=%s info_lines=%d" % (bool(pv), len(pv)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

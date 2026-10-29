#!/usr/bin/env python3
"""Play a fixed UCI script against an engine command line (e.g. valgrind ... forge) and wait for every answer
(no sleeps, so a slow valgrind run never loses a search to an early `quit`).
Script: uci; Threads 1, Hash 16, OwnBook false; bench 11; perft 4 startpos; go depth 10 on four positions with
castling, en passant and promotions (ucinewgame before each); quit.
usage: ci_uci_script.py [--log FILE] -- <command> [args...]      exit = the engine's exit status (2 on protocol error)
"""
import re
import subprocess
import sys

POSITIONS = [
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
    "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
]


def main():
    args = sys.argv[1:]
    log_path = None
    if args[:1] == ["--log"]:
        log_path, args = args[1], args[2:]
    if args[:1] == ["--"]:
        args = args[1:]
    log = open(log_path, "w") if log_path else sys.stdout
    p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def send(s):
        log.write("> " + s + "\n")
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait(rx):
        pat = re.compile(rx)
        for line in p.stdout:
            log.write(line)
            if pat.search(line):
                return line
        log.write("engine output ended before " + rx + "\n")
        sys.exit(2)

    send("uci")
    wait(r"^uciok")
    for opt in ("Threads value 1", "Hash value 16", "OwnBook value false"):
        send("setoption name " + opt)
    send("isready")
    wait(r"^readyok")
    send("bench 11")
    wait(r"bench depth 11 nodes \d+")
    send("position startpos")
    send("go perft 4")
    wait(r"^nodes \d+")
    for fen in POSITIONS:
        send("ucinewgame")
        send("position fen " + fen)
        send("isready")
        wait(r"^readyok")
        send("go depth 10")
        wait(r"^bestmove")
    send("quit")
    rc = p.wait(timeout=600)
    log.write(f"exit {rc}\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())

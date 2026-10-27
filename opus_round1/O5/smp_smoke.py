#!/usr/bin/env python3
"""Smoke run of a Forge exe with extra options at several thread counts: for each position a
`go depth <d>` that must end with a legal bestmove (checked against `go perft 1` of the same
position, which lists the legal moves).
usage: smp_smoke.py <exe> <depth> <threads,threads,...> [Name=Value ...]
Exit status 0 when every search returned a legal move."""
import re
import subprocess
import sys

FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
]


def main():
    exe, depth = sys.argv[1], int(sys.argv[2])
    threads = [int(t) for t in sys.argv[3].split(",")]
    options = [tuple(kv.split("=", 1)) for kv in sys.argv[4:]]
    failures = 0
    for t in threads:
        p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

        def send(s):
            p.stdin.write(s + "\n")
            p.stdin.flush()

        def wait(pattern):
            rx = re.compile(pattern)
            seen = []
            for line in p.stdout:
                seen.append(line)
                if rx.search(line):
                    return line, seen
            raise SystemExit("engine exited early")

        send("uci")
        wait(r"^uciok")
        for name, value in [("Threads", str(t)), ("Hash", "16"), ("OwnBook", "false")] + options:
            send(f"setoption name {name} value {value}")
        for fen in FENS:
            send("ucinewgame")
            send("position fen " + fen)
            send("go perft 1")
            _, seen = wait(r"^nodes \d+")
            legal = {l.split(":")[0] for l in seen if re.match(r"^[a-h][1-8][a-h][1-8][qrbn]?: \d+", l)}
            send("isready")
            wait(r"^readyok")
            send(f"go depth {depth}")
            line, seen = wait(r"^bestmove")
            best = line.split()[1]
            infos = [l for l in seen if l.startswith("info depth ")]
            ok = best in legal
            failures += 0 if ok else 1
            print(f"threads {t} depth {depth} {'OK ' if ok else 'BAD'} bestmove {best} "
                  f"last: {infos[-1].strip()[:110] if infos else '-'}", flush=True)
        send("quit")
        p.wait(timeout=120)
    print(f"smp_smoke failures={failures}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

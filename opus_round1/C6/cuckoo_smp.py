#!/usr/bin/env python3
"""C6 smoke run for UCI CuckooRep with helper threads (used by tsan_extra.sh on the TSan build).

For each thread count and position: set CuckooRep (alternating on/off, so the option is also
toggled between searches), `go depth D`, wait for bestmove. Fails on a missing bestmove, an
engine exit, or a '0000' bestmove in a position that has legal moves.
usage: cuckoo_smp.py <forge> [--threads 2,4] [--depth 8] [--timeout 120]
"""
import argparse
import subprocess
import sys
import threading

POSITIONS = [
    "startpos",
    "startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6",
    "fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "fen 6k1/ppp3p1/8/8/1r6/1q6/4Q1PP/7K w - - 0 1",
    "fen 6k1/ppp3p1/8/8/1r6/1q6/4Q1PP/7K w - - 0 1 moves e2e8 g8h7 e8h5 h7g8",
    "fen 8/ppp3pk/8/8/1r6/8/1q4PP/3Q3K w - - 0 1",
    "fen 8/k7/3p4/p2P1p2/P2P1P2/8/8/K7 w - - 0 1",
    "fen 4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1 moves e1f1 e8d8 f1e1 d8e8",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("forge")
    parser.add_argument("--threads", default="2,4")
    parser.add_argument("--depth", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()
    engine = subprocess.Popen([args.forge], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    lines = []
    cond = threading.Condition()

    def reader():
        for line in engine.stdout:
            with cond:
                lines.append(line.rstrip("\n"))
                cond.notify_all()
        with cond:
            lines.append(None)
            cond.notify_all()

    threading.Thread(target=reader, daemon=True).start()

    def send(text):
        engine.stdin.write(text + "\n")
        engine.stdin.flush()

    def wait_for(prefix, start):
        with cond:
            ok = cond.wait_for(lambda: any(l is None or l.startswith(prefix) for l in lines[start:]), args.timeout)
            if not ok:
                raise SystemExit(f"timeout waiting for {prefix}")
            for l in lines[start:]:
                if l is None:
                    raise SystemExit("engine exited")
                if l.startswith(prefix):
                    return l

    send("uci")
    wait_for("uciok", 0)
    searches = 0
    for threads in [int(t) for t in args.threads.split(",")]:
        send(f"setoption name Threads value {threads}")
        for i, position in enumerate(POSITIONS):
            cuckoo = "true" if (i + threads) % 2 == 0 or i == 3 else "false"
            send(f"setoption name CuckooRep value {cuckoo}")
            send("ucinewgame")
            send("position " + position)
            start = len(lines)
            send("isready")
            wait_for("readyok", start)
            start = len(lines)
            send(f"go depth {args.depth}")
            best = wait_for("bestmove", start)
            searches += 1
            print(f"threads {threads} CuckooRep {cuckoo} {position[:60]} -> {best}", flush=True)
            if best.split()[1] == "0000":
                raise SystemExit("0000 bestmove in a position with legal moves")
    send("quit")
    engine.wait(timeout=args.timeout)
    print(f"cuckoo_smp: {searches} searches OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

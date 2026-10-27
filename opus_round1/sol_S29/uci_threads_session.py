#!/usr/bin/env python3
"""Short multi-threaded UCI session for the TSan job (S29 speed stack; adapted from opus-sol-S13): Threads N,
Hash 16, OwnBook false, then `go depth D` from startpos and `go movetime M` from kiwipete, each waited for its
bestmove (so the search is not cut short by `quit`). The stack has no UCI option: it is a compile switch.
usage: uci_threads_session.py <forge_exe> <threads> [depth=10] [movetime_ms=1000]
Exit 0 if both searches answered with a bestmove."""
import subprocess
import sys

exe, threads = sys.argv[1], int(sys.argv[2])
depth = int(sys.argv[3]) if len(sys.argv) > 3 else 10
movetime = int(sys.argv[4]) if len(sys.argv) > 4 else 1000
KIWI = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
seen = []


def send(line):
    p.stdin.write(line + "\n")
    p.stdin.flush()


def wait(prefix):
    for line in p.stdout:
        line = line.rstrip("\n")
        if line.startswith("info string") or line.startswith("bestmove"):
            print(line, flush=True)
            seen.append(line)
        if line.startswith(prefix):
            return line
    raise SystemExit("engine exited before " + prefix)


send("uci"); wait("uciok")
for option in (f"Threads value {threads}", "Hash value 16", "OwnBook value false"):
    send("setoption name " + option)
send("isready"); wait("readyok")
send("position startpos"); send(f"go depth {depth}"); wait("bestmove")
send(f"position fen {KIWI}"); send(f"go movetime {movetime}"); wait("bestmove")
send("quit")
p.wait(timeout=60)
ok = sum(line.startswith("bestmove") for line in seen) == 2
print(f"threads {threads}: {'OK' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)

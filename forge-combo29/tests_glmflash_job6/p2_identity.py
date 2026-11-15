#!/usr/bin/env python3
# P2: identity proof. For the first N positions of the UHO epd file run
# ucinewgame / position fen / go depth 9 on one engine process, collect
# "bestmove X score <cp> nodes <n>" per position, and print the sha256 of the
# whole answer stream plus the smallest node count seen.
import hashlib
import subprocess
import sys

def run(exe, epd, n, depth, setoptions):
    answers = []
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    def send(line):
        p.stdin.write(line + "\n")
        p.stdin.flush()
    send("uci")
    while True:
        line = p.stdout.readline()
        if line.startswith("uciok"):
            break
    for opt in setoptions:
        send(opt)
    min_nodes = None
    with open(epd, encoding="utf-8", errors="replace") as f:
        for i, fen in enumerate(f for _, f in zip(range(n), f)):
            fen = fen.strip()
            if not fen:
                continue
            send("ucinewgame")
            send("isready")
            while True:
                line = p.stdout.readline()
                if line.startswith("readyok"):
                    break
            send(f"position fen {fen}")
            send(f"go depth {depth}")
            best = None
            score = None
            nodes = None
            while True:
                line = p.stdout.readline()
                if line.startswith("bestmove"):
                    best = line.split()[1]
                    break
                if " score " in line and " pv " in line and nodes is None or (" score " in line and " pv " in line):
                    t = line.split()
                    if "score" in t:
                        score = t[t.index("score") + 1 : t.index("score") + 3]
                if " nodes " in line:
                    t = line.split()
                    nodes = int(t[t.index("nodes") + 1])
            answers.append(f"{fen}|{best}|{' '.join(score) if score else '?'}|{nodes}")
            if min_nodes is None or (nodes is not None and nodes < min_nodes):
                min_nodes = nodes
    send("quit")
    p.wait(timeout=10)
    blob = "\n".join(answers).encode()
    return hashlib.sha256(blob).hexdigest(), min_nodes, len(answers)

if __name__ == "__main__":
    exe, epd, n, depth = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    opts = sys.argv[5:] or []
    h, mn, cnt = run(exe, epd, n, depth, opts)
    print(f"{exe} opts={' '.join(opts) if opts else 'none'} positions={cnt} sha256={h} min_nodes={mn}")

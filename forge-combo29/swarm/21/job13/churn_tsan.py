#!/usr/bin/env python3
"""churn_tsan.py EXE OUTDIR LABEL [N]

CHECK of seat 24's 24-F1 with my own TSan build and my own churn sequence (SEED 2101).

N (default 300) rounds; each round:
  - pick Threads from 1/2/4/8/16 and Hash from 1/4/16/64/256 with the seed
  - `setoption name Threads value T`, `isready`  (read to readyok)
  - `setoption name Hash value H`, `isready`
  - with probability 0.44 (the claim's 131/300) send `ucinewgame`, `isready`
  - `go depth 8` and READ TO BESTMOVE (19-F12 discipline; stdin is never closed mid-search)
  - check the bestmove is a legal move per python-chess; count crashes and TSan reports

TSan options are cleared before spawning, and `__tsan_` symbol count is recorded, so a run
with an uninstrumented binary or a left-over TSAN_OPTIONS cannot report a false zero.
The engine's stderr (where TSan writes) is captured to the raw file and scanned for
"WARNING: ThreadSanitizer".
"""
import hashlib
import os
import random
import subprocess
import sys

import chess

SEED = 2101
THREADS = [1, 2, 4, 8, 16]
HASHES = [1, 4, 16, 64, 256]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    exe, outdir, label = sys.argv[1], sys.argv[2], sys.argv[3]
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 300
    os.makedirs(outdir, exist_ok=True)
    rng = random.Random(SEED)

    env = dict(os.environ)
    for k in ("TSAN_OPTIONS", "ASAN_OPTIONS", "UBSAN_OPTIONS"):
        env.pop(k, None)

    nm = subprocess.run("nm -C %s | grep -c __tsan_ || true" % exe, shell=True,
                        capture_output=True, text=True).stdout.strip()
    raw_path = os.path.join(outdir, label + "_raw.txt")
    raw = open(raw_path, "w")
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)

    def send(line):
        raw.write(">>> " + line + "\n")
        raw.flush()
        p.stdin.write(line + "\n")
        p.stdin.flush()

    lines_out = []

    def read_until(token, limit=200000):
        got = []
        while True:
            ln = p.stdout.readline()
            if ln == "":
                raise EOFError("engine died")
            raw.write(ln)
            raw.flush()
            got.append(ln.rstrip("\n"))
            lines_out.append(ln)
            if ln.strip() == token or ln.strip().startswith(token + " "):
                return got

    send("uci")
    read_until("uciok")
    stats = dict(rounds=0, ucinewgame=0, crash=0, tsan=0, illegal=0, no_bestmove=0,
                 threads_changes=0, hash_changes=0)
    board = chess.Board()
    try:
        for i in range(n):
            t = rng.choice(THREADS)
            h = rng.choice(HASHES)
            send("setoption name Threads value %d" % t)
            send("isready")
            read_until("readyok")
            stats["threads_changes"] += 1
            send("setoption name Hash value %d" % h)
            send("isready")
            read_until("readyok")
            stats["hash_changes"] += 1
            if rng.random() < 131.0 / 300.0:
                send("ucinewgame")
                send("isready")
                read_until("readyok")
                stats["ucinewgame"] += 1
            send("position startpos moves e2e4 e7e5 g1f3")
            send("isready")
            read_until("readyok")
            send("go depth 8")
            gl = read_until("bestmove", limit=200000)
            stats["rounds"] += 1
            best = ""
            for ln in gl:
                if ln.startswith("bestmove"):
                    best = ln.split()[1] if len(ln.split()) > 1 else ""
            legal = {m.uci() for m in chess.Board("rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 0 3").legal_moves}
            if not best:
                stats["no_bestmove"] += 1
            elif best not in legal:
                stats["illegal"] += 1
        send("quit")
        p.wait(timeout=30)
    except (EOFError, BrokenPipeError):
        stats["crash"] += 1
        try:
            p.kill()
        except Exception:
            pass
    raw.close()

    text = open(raw_path, errors="replace").read()
    stats["tsan"] = text.count("WARNING: ThreadSanitizer")
    with open(os.path.join(outdir, label + "_summary.txt"), "w") as fh:
        fh.write("exe: %s\nsha256: %s\nnm___tsan_: %s\n" % (os.path.abspath(exe), sha256(exe), nm))
        for k, v in stats.items():
            fh.write("%s %d\n" % (k, v))
    print(open(os.path.join(outdir, label + "_summary.txt")).read())


if __name__ == "__main__":
    main()
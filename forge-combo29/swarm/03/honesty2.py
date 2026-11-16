#!/usr/bin/env python3
"""honesty2.py EXE OUTDIR : honesty check with a harness that never closes stdin while a search runs.

Why this file exists: seat 19's broadcast (finding 19-F12, 2026-11-16) shows this build answers a FABRICATED
`bestmove a2a3` with no `info` lines when `quit` arrives while a `go` search is still running. My first
honesty.sh fed the whole input, `quit` included, as one stream. For `bench` and `go perft` that is harmless
(checked below and in HARNESS_AUDIT.md: both run inline in the UCI loop), but a harness written that way is a trap
for any `go depth/nodes/movetime` job, so every pin is re-measured here the safe way:
    send one command -> read stdout until the completion token -> only then send the next.
Completion tokens: uciok, readyok, `bestmove` (search), `nodes ` (perft), `info string bench` (bench).
A line containing an error word is recorded and stops the sequence.
"""
import os
import subprocess
import sys
import time

EXE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
ERRWORDS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def run(name, commands, token):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    raw = open(f"{OUT}/{name}.out", "w")
    sent = []

    def send(c):
        sent.append(c)
        raw.write(f">>> {c}\n")
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def read_until(tok):
        while True:
            line = p.stdout.readline()
            if line == "":
                return None
            raw.write(line)
            raw.flush()
            s = line.strip()
            for w in ERRWORDS:
                if w in s:
                    raw.write(f"### stopped on error word: {w}\n")
                    return s
            if s.startswith(tok):
                return s

    t0 = time.monotonic()
    send("uci"); read_until("uciok")
    send("isready"); read_until("readyok")
    send("ucinewgame"); send("isready"); read_until("readyok")
    result = None
    for c in commands:
        tok = token if c.split()[0] in ("go", "bench") else "readyok"
        send(c)
        result = read_until(tok)
        if result is None:
            break
    elapsed = time.monotonic() - t0
    # the search has completed and been read in full; only NOW the engine may be told to quit
    send("quit")
    try:
        p.wait(timeout=120)
    except Exception:  # noqa: BLE001
        p.kill()
    raw.write(f"### wall {elapsed:.3f}s\n")
    raw.close()
    return result, elapsed, sent


def main():
    out_lines = []

    def one(name, cmds, tok, expect):
        res, el, sent = run(name, cmds, tok)
        ok = expect in (res or "")
        out_lines.append(f"{name}\t{'MATCH' if ok else 'MISMATCH'}\texpected {expect}\tgot {res}\twall {el:.3f}s")
        print(out_lines[-1])

    one("bench11", ["bench 11"], "info string bench", "nodes 312866")
    one("bench13", ["bench 13"], "info string bench", "nodes 862329")
    one("bench16", ["bench 16"], "info string bench", "nodes 3024920")
    one("perft5", ["go perft 5"], "nodes ", "nodes 4865609")
    with open(f"{OUT}/honesty2.summary", "w") as f:
        f.write("\n".join(out_lines) + "\n")
    meta = subprocess.run(["sha256sum", EXE], capture_output=True, text=True).stdout.strip()
    with open(f"{OUT}/honesty2.meta", "w") as f:
        f.write(f"exe: {EXE}\nsha256: {meta}\n")
        f.write("sequence: uci/isready/ucinewgame/isready, then ONE search command, read to its completion token,\n")
        f.write("then quit. stdin never closed during a search.\n")


if __name__ == "__main__":
    main()

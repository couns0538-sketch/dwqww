#!/usr/bin/env python3
"""diag.py -- run the DIAGNOSTIC build with stdin kept open.

Why this exists: piping `go depth N` into the engine and closing stdin makes the
search abort on EOF, which returns a legal but fabricated bestmove (see the
swarm brief, ORDER AND REGIME note (c)). A first attempt at this measurement did
exactly that and produced `bestmove g8f8` with no info line even at halfmove 98,
which looks like a result and is not one. This runner keeps stdin open until
`bestmove` has actually been read, then sends `quit`.

Usage: diag.py --exe PATH --fen FEN --depth N [--out-prefix P]
Writes <P>.stdout.txt and <P>.stderr.txt.
"""
import argparse
import subprocess
import sys
import time

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from probe import validate_fen  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--fen", required=True)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--out-prefix", required=True)
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--options", default="")
    args = ap.parse_args()

    ok, why = validate_fen(args.fen)
    if not ok:
        sys.stderr.write("REFUSING to send invalid FEN: %s\n" % why)
        return 3

    p = subprocess.Popen([args.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(pred, deadline):
        lines = []
        while time.monotonic() < deadline:
            line = p.stdout.readline()
            if line == "":
                return lines, False
            line = line.rstrip("\n")
            lines.append(line)
            if pred(line):
                return lines, True
        return lines, False

    send("uci")
    until(lambda l: l.strip() == "uciok", time.monotonic() + args.timeout)
    for part in [x for x in args.options.split(";") if x.strip()]:
        name, _, value = part.partition("=")
        send("setoption name %s value %s" % (name.strip(), value.strip()))
    send("ucinewgame")
    send("isready")
    until(lambda l: l.strip() == "readyok", time.monotonic() + args.timeout)
    send("position fen " + args.fen)
    send("isready")
    pos_lines, _ = until(lambda l: l.strip() == "readyok", time.monotonic() + args.timeout)
    for l in pos_lines:
        if "invalid FEN" in l:
            sys.stderr.write("REFUSED BY ENGINE: %s\n" % l)
    send("go depth %d" % args.depth)
    go_lines, got = until(lambda l: l.startswith("bestmove"),
                          time.monotonic() + args.timeout)
    if not got:
        sys.stderr.write("TIMEOUT waiting for bestmove\n")
    send("quit")
    try:
        p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        p.kill()
    err = p.stderr.read()

    with open(args.out_prefix + ".stdout.txt", "w") as f:
        f.write("\n".join(pos_lines + ["---GO---"] + go_lines) + "\n")
    with open(args.out_prefix + ".stderr.txt", "w") as f:
        f.write(err)

    best = [l for l in go_lines if l.startswith("bestmove")]
    info = [l for l in go_lines if l.startswith("info depth")]
    print("bestmove:", best[-1] if best else "NONE")
    print("last info:", info[-1] if info else "NONE")
    print("DIAG lines:", len([l for l in err.splitlines() if "DIAG" in l]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

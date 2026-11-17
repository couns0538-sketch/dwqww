#!/usr/bin/env python3
"""run_search.py EXE FEN --depth N [--out FILE] [--options k=v ...]

Drive one fresh engine process per search and read stdout to `bestmove` before
sending anything else. (Findings §7: an aborted search returns a fabricated
bestmove, so a piped harness that sends quit early is not evidence.)

Emits every `info depth` line and every `info string lmr...` line verbatim.
Exit codes: 0 ok, 2 protocol error (unknown option / invalid value / invalid FEN /
illegal move), 3 timeout.
"""
import argparse
import subprocess
import sys
import time

TIMEOUT = 240.0


def run(exe, fen, depth, options, movetime=None):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    lines = []
    bad = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def read_until(pred, limit=TIMEOUT):
        end = time.monotonic() + limit
        while time.monotonic() < end:
            line = p.stdout.readline()
            if not line:
                return None
            line = line.rstrip("\n")
            lines.append(line)
            low = line.lower()
            if (low.startswith("unknown option") or low.startswith("invalid value")
                    or low.startswith("invalid fen") or low.startswith("illegal move")
                    or "invalid fen" in low or "illegal move" in low
                    or low.startswith("error")):
                bad.append(line)
            if pred(line):
                return line
        return None

    def sync():
        send("isready")
        read_until(lambda l: l.startswith("readyok"))

    send("uci")
    if read_until(lambda l: l.startswith("uciok")) is None:
        p.kill()
        return lines, bad, 3
    for key, val in options:
        send(f"setoption name {key} value {val}")
        sync()
    send("ucinewgame")
    sync()
    send(f"position fen {fen}")
    sync()
    if movetime is not None:
        send(f"go movetime {movetime}")
    else:
        send(f"go depth {depth}")
    best = read_until(lambda l: l.startswith("bestmove"), limit=TIMEOUT * 4)
    send("quit")
    try:
        p.stdin.close()
    except Exception:
        pass
    p.wait(timeout=30)
    if bad:
        return lines, bad, 2
    if best is None:
        return lines, bad, 3
    return lines, bad, 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("fen")
    ap.add_argument("--depth", type=int, default=8)
    ap.add_argument("--movetime", type=int, default=None)
    ap.add_argument("--option", action="append", default=[])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    opts = []
    for spec in a.option:
        k, _, v = spec.partition("=")
        opts.append((k, v))
    lines, bad, code = run(a.exe, a.fen, a.depth, opts, a.movetime)
    text = "\n".join(lines) + "\n"
    if a.out:
        with open(a.out, "w") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)
    if code != 0:
        print(f"PROTOCOL_ERROR code={code} bad={bad[:3]}", file=sys.stderr)
    return 0 if code == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

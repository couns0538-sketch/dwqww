#!/usr/bin/env python3
"""Engine side of area 3 job 1: perft 1..4 on every FEN in a file.

Writes one line per (position, depth):  <idx> <depth> <nodes|ERR> <marker>
marker is one of: OK, INVALID_FEN, ILLEGAL_MOVE, UNKNOWN, TIMEOUT
Also writes <out>.meta with exe path, sha256, id name and every option line sent.
Usage: engine_perft.py EXE FENS OUT DEPTHS [TIMEOUT_S]
"""
import hashlib
import os
import subprocess
import sys
import time

EXE = sys.argv[1]
FENS = sys.argv[2]
OUT = sys.argv[3]
DEPTHS = [int(x) for x in sys.argv[4].split(",")]
TIMEOUT_S = float(sys.argv[5]) if len(sys.argv) > 5 else 120.0

BAD_MARKERS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    fens = [line.strip() for line in open(FENS) if line.strip()]
    meta = open(OUT + ".meta", "w")
    meta.write(f"exe {os.path.abspath(EXE)}\nsha256 {sha256(EXE)}\n")
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(line):
        p.stdin.write(line + "\n")
        p.stdin.flush()
        meta.write("sent: " + line + "\n")

    def read_until(token, timeout=TIMEOUT_S):
        """Read lines up to and including one that starts with token; return them."""
        got = []
        t0 = time.monotonic()
        while True:
            if p.poll() is not None:
                got.append("<PROCESS EXITED rc=%s>" % p.returncode)
                return got, "EXIT"
            line = p.stdout.readline()
            if line == "":
                return got, "EOF"
            line = line.rstrip("\n")
            got.append(line)
            if line.startswith(token):
                return got, "OK"
            if token == "readyok" and time.monotonic() - t0 > timeout:
                return got, "TIMEOUT"
            if token == "nodes" and time.monotonic() - t0 > timeout * 20:
                return got, "TIMEOUT"

    send("uci")
    lines, st = read_until("uciok")
    for ln in lines:
        if ln.startswith("id name"):
            meta.write("id: " + ln + "\n")
    if st != "OK":
        meta.write("FATAL uci handshake %s\n" % st)
        meta.close()
        sys.exit("uci handshake failed: %s" % st)
    send("isready")
    lines, st = read_until("readyok")
    meta.write("readyok after uci: %s\n" % st)

    out = open(OUT, "w")
    out.write("# idx depth nodes marker\n")
    t_start = time.monotonic()
    for idx, fen in enumerate(fens):
        send("position fen " + fen)
        send("isready")
        ans, st = read_until("readyok")
        marker = "OK"
        for ln in ans:
            low = ln.lower()
            for bad in BAD_MARKERS:
                if bad in low:
                    marker = bad.upper().replace(" ", "_")
        if st != "OK":
            marker = "TIMEOUT" if st == "TIMEOUT" else "UNKNOWN"
        for d in DEPTHS:
            if marker != "OK":
                out.write(f"{idx} {d} ERR {marker}\n")
                continue
            send("go perft %d" % d)
            ans, st = read_until("nodes")
            nodes = "ERR"
            for ln in ans:
                if ln.startswith("nodes "):
                    nodes = ln.split()[1]
                low = ln.lower()
                for bad in BAD_MARKERS:
                    if bad in low:
                        marker = bad.upper().replace(" ", "_")
            if st != "OK" or nodes == "ERR":
                out.write(f"{idx} {d} ERR {marker if marker != 'OK' else st}\n")
            else:
                out.write(f"{idx} {d} {nodes} OK\n")
        if idx % 250 == 0:
            out.flush()
            print(idx, round(time.monotonic() - t_start, 1), "s", flush=True)
    out.close()
    send("quit")
    meta.write("total seconds %.1f positions %d\n" % (time.monotonic() - t_start, len(fens)))
    meta.close()
    print("done", len(fens), "positions", round(time.monotonic() - t_start, 1), "s")


main()

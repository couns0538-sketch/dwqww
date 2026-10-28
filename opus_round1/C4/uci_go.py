#!/usr/bin/env python3
"""Drive one `go depth N` search over UCI and wait for `bestmove` before quitting (used by tsan_extra.sh).
usage: uci_go.py <exe> <threads> <depth> <fen> [--set Name=Value]...
Exit 0 if the engine answered `bestmove` (and, when NNUEKingBuckets > 0 is set, reported the v2 net active)."""
import argparse
import subprocess
import sys
import threading


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("threads", type=int)
    ap.add_argument("depth", type=int)
    ap.add_argument("fen")
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--timeout", type=float, default=240.0)
    a = ap.parse_args()
    p = subprocess.Popen([a.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    timer = threading.Timer(a.timeout, p.kill)
    timer.start()
    lines = []

    def send(cmd):
        p.stdin.write(cmd + "\n")
        p.stdin.flush()

    def wait_for(prefix):
        for line in p.stdout:
            lines.append(line.rstrip("\n"))
            if line.startswith(prefix):
                return line.strip()
        return None

    send("uci")
    wait_for("uciok")
    send(f"setoption name Threads value {a.threads}")
    send("setoption name Hash value 16")
    for item in a.set:
        name, value = item.split("=", 1)
        send(f"setoption name {name} value {value}")
    send("isready")
    wait_for("readyok")
    send(f"position fen {a.fen}")
    send(f"go depth {a.depth}")
    best = wait_for("bestmove")
    send("quit")
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()
    timer.cancel()
    info = [l for l in lines if l.startswith("info string")]
    for l in info:
        print("   " + l)
    want_v2 = any(i.startswith("NNUEKingBuckets=") and not i.endswith("=0") for i in a.set)
    if want_v2 and not any("NNUE v2: active" in l for l in info):
        print("   FAIL: v2 net not active")
        return 1
    if best is None:
        print(f"   FAIL: no bestmove (exit code {p.returncode})")
        return 1
    depth_lines = [l for l in lines if l.startswith("info depth")]
    print(f"   {best}   (last info: {depth_lines[-1][:90] if depth_lines else 'none'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

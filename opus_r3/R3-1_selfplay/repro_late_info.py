#!/usr/bin/env python3
"""Minimal reproduction (R3-1 self-play finding): with HardDeadline > 0, after the watchdog sends the bestmove
the stopped search can still print an `info depth ...` line (a completed iteration or the aborted iteration's
"revised line"), i.e. search output after the go was answered.

usage: repro_late_info.py <engine> [--deadline 1] [--movetime 11] [--threads 1] [--n 300] [--fen FEN] [--opt N=V]
One engine, OwnBook false; per round: position, isready/readyok, `go movetime M` (hard limit M - 10 ms move
overhead), read to the bestmove, then position + isready/readyok again: every non-string `info` line that arrives
between the bestmove and that readyok is late output. Prints the counts and the first examples; exit status 1 if
any late line was seen. Timing-dependent (the watchdog must beat the search), most frequent on a loaded machine.
"""
import argparse
import queue
import subprocess
import sys
import threading
import time

DEFAULT_FEN = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("engine")
    ap.add_argument("--deadline", type=int, default=1)
    ap.add_argument("--movetime", type=int, default=11)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--fen", default=DEFAULT_FEN)
    ap.add_argument("--opt", action="append", default=[])
    a = ap.parse_args()
    p = subprocess.Popen([a.engine], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         creationflags=getattr(subprocess, "IDLE_PRIORITY_CLASS", 0))
    q = queue.Queue()

    def reader():
        for raw in iter(p.stdout.readline, b""):
            q.put((time.perf_counter(), raw.decode("utf-8", "replace").rstrip("\r\n")))
        q.put((time.perf_counter(), None))

    threading.Thread(target=reader, daemon=True).start()

    def send(cmd):
        p.stdin.write((cmd + "\n").encode())
        p.stdin.flush()

    def until(pred, timeout=30.0):
        lines, end = [], time.perf_counter() + timeout
        while True:
            t, line = q.get(timeout=max(0.01, end - time.perf_counter()))
            if line is None:
                raise SystemExit(f"engine exited; last lines {lines[-5:]}")
            lines.append((t, line))
            if pred(line):
                return lines

    send("uci")
    until(lambda s: s == "uciok")
    for o in [f"Threads={a.threads}", "OwnBook=false", "Hash=16", f"HardDeadline={a.deadline}"] + a.opt:
        name, _, value = o.partition("=")
        send(f"setoption name {name} value {value}")
    send("isready")
    until(lambda s: s == "readyok")
    watchdog = late = 0
    examples = []
    for i in range(a.n):
        send(f"position fen {a.fen}")
        send("isready")
        until(lambda s: s == "readyok")
        send(f"go movetime {a.movetime}")
        lines = until(lambda s: s.startswith("bestmove"))
        fired = any(s.startswith("info string HardDeadline") for _, s in lines)
        watchdog += fired
        t_best, best = lines[-1]
        send(f"position fen {a.fen}")   # the engine joins the search before it handles this
        send("isready")
        after = until(lambda s: s == "readyok")
        for t, s in after:
            if s.startswith("info") and not s.startswith("info string"):
                late += 1
                if len(examples) < 5:
                    examples.append(f"round {i}: watchdog {'yes' if fired else 'no'}: {lines[-2][1] if fired else ''} | "
                                    f"{best} | +{(t - t_best) * 1000:.1f} ms: {s}")
    send("quit")
    p.wait(timeout=20)
    print(f"engine {a.engine}: {a.n} rounds of go movetime {a.movetime} with HardDeadline {a.deadline}, "
          f"Threads {a.threads}: watchdog answered {watchdog}, info lines after the bestmove {late}")
    for e in examples:
        print("  " + e)
    return 1 if late else 0


if __name__ == "__main__":
    sys.exit(main())

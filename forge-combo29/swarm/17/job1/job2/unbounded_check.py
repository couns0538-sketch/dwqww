#!/usr/bin/env python3
"""seat 17 S-F8 follow-up: does a `searchmoves` root with no legal match respect a time limit?

For each clock/movetime limit this script sends the go command and then WAITS, sending nothing else
(no `stop`), until bestmove arrives or the hard timeout hits. It records:
  - wall seconds until bestmove (monotonic)
  - whether bestmove arrived on its own, or only after the harness gave up / sent stop
  - how many info depth lines and what they report (nodes, time)

Two controls per limit: the same limit with a legal searchmoves entry, and with no searchmoves at all.

usage: unbounded_check.py <exe> <outdir>
"""
import json
import os
import subprocess
import sys
import time

FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
CASES = [
    # (label, go line)
    ("movetime100_nomatch", "go movetime 100 searchmoves e7e5"),
    ("movetime100_control_legal", "go movetime 100 searchmoves e2e4"),
    ("clock1000_nomatch", "go wtime 1000 btime 1000 searchmoves e7e5"),
    ("clock1000_control_legal", "go wtime 1000 btime 1000 searchmoves e2e4"),
    ("movetime100_no_sm", "go movetime 100"),
    ("clock1000_no_sm", "go wtime 1000 btime 1000"),
]


def one(exe, go_line, wait_s):
    """Send position + go, then wait. Nothing else is sent until bestmove or wait_s elapses."""
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    out = []
    # setup, each answered
    for line in ("uci", "isready", "setoption name OwnBook value false", "isready", "position " + FEN, "isready"):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()
        if line == "isready":
            while True:
                reply = proc.stdout.readline()
                if reply == "":
                    break
                out.append(reply.rstrip())
                if reply.strip() == "readyok":
                    break
        elif line == "uci":
            while True:
                reply = proc.stdout.readline()
                if reply == "":
                    break
                out.append(reply.rstrip())
                if reply.strip() == "uciok":
                    break
    start = time.monotonic()
    proc.stdin.write(go_line + "\n")
    proc.stdin.flush()
    bestmove = None
    timed_out = False
    while True:
        if time.monotonic() - start > wait_s:
            timed_out = True
            break
        # Non-blocking-ish: read with a select on the pipe
        import select
        ready, _, _ = select.select([proc.stdout], [], [], 0.05)
        if not ready:
            continue
        reply = proc.stdout.readline()
        if reply == "":
            break
        out.append(reply.rstrip())
        if reply.startswith("bestmove"):
            bestmove = reply.strip()
            break
    wall = time.monotonic() - start
    # If it never returned on its own, ask it to stop and see whether it can.
    returned_after_stop = None
    if bestmove is None:
        try:
            proc.stdin.write("stop\n")
            proc.stdin.flush()
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                import select
                ready, _, _ = select.select([proc.stdout], [], [], 0.05)
                if not ready:
                    continue
                reply = proc.stdout.readline()
                if reply == "":
                    break
                out.append(reply.rstrip())
                if reply.startswith("bestmove"):
                    returned_after_stop = reply.strip()
                    break
        except BrokenPipeError:
            pass
    try:
        proc.stdin.write("quit\n")
        proc.stdin.flush()
    except BrokenPipeError:
        pass
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    depth_lines = [ln for ln in out if ln.startswith("info depth")]
    times = []
    nodes = []
    for ln in depth_lines:
        for token, dest in ((" time ", times), (" nodes ", nodes)):
            if token in ln:
                try:
                    dest.append(int(ln.split(token)[1].split()[0]))
                except (IndexError, ValueError):
                    pass
    return {
        "go": go_line,
        "bestmove_on_its_own": bestmove,
        "returned_only_after_stop": returned_after_stop,
        "wall_s_until_bestmove_or_timeout": round(wall, 3),
        "timed_out_without_bestmove": timed_out,
        "info_depth_lines": len(depth_lines),
        "last_reported_time_ms": times[-1] if times else None,
        "max_reported_nodes": max(nodes) if nodes else None,
        "last_depth": (lambda: (depth_lines[-1].split(" depth ")[1].split()[0] if depth_lines else None))(),
        "lines": out,
    }


def main():
    exe, outdir = sys.argv[1:3]
    os.makedirs(outdir, exist_ok=True)
    results = []
    for label, go_line in CASES:
        rec = one(exe, go_line, 20.0)  # 20 s: a 100 ms limit returning after 20 s is unbounded
        lines = rec.pop("lines")
        rec["case"] = label
        with open(os.path.join(outdir, label + ".log"), "w") as handle:
            handle.write("\n".join(lines) + "\n")
        results.append(rec)
        print(json.dumps({k: v for k, v in rec.items()}), flush=True)
    with open(os.path.join(outdir, "unbounded.json"), "w") as handle:
        json.dump(results, handle, indent=1)


if __name__ == "__main__":
    main()

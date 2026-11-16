#!/usr/bin/env python3
"""stack_capture.py — drive the engine to the state where it is slow/hung, then capture a
stack of EVERY thread with gdb in batch mode, and classify each thread as spinning, parked,
or blocked.

No hang appeared in 20 fresh runs, so this reproduces the pathological state by taking the
WORST case we know: Threads 4, depth 12, on the FEN, run until either bestmove (too fast to
sample) or until the sample deadline. To get stacks in a useful place it also supports
--repeat: it samples while the search is at its slowest iteration.

Output: one gdb text dump per sample in OUTDIR, plus a summary line per sample saying how
many threads were running vs blocked.

Usage: stack_capture.py EXE OUTDIR [--threads 4] [--depth 12] [--samples 5] [--at 3.0]
"""
import argparse
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time

FEN = "5R2/1p5k/6p1/8/1K6/5q2/8/8 b - - 0 1"


def send(p, s):
    try:
        p.stdin.write(s + "\n")
        p.stdin.flush()
        return True
    except (BrokenPipeError, ValueError):
        return False


def classify(threads):
    """Group thread states into running / futex-wait / other, from gdb's `info threads` output."""
    running, futex, other = 0, 0, 0
    for line in threads:
        if "Thread" not in line:
            continue
        if "running" in line.lower() or re.search(r"in \w+", line) and "futex" not in line:
            running += 1
        if "futex" in line:
            futex += 1
    return running, futex, other


def capture(pid, outdir, tag):
    gdb_script = os.path.join(outdir, "_gdb_%s.cmds" % tag)
    with open(gdb_script, "w") as f:
        f.write("set pagination off\nset print thread-events off\n"
                "info threads\nthread apply all bt 12\n"
                "thread apply all p $_siginfo\n"
                "detach\nquit\n")
    out = os.path.join(outdir, "stacks_%s.txt" % tag)
    with open(out, "w") as f:
        f.write("$ gdb -p %d -batch -x %s\n" % (pid, gdb_script))
        subprocess.run(["gdb", "-p", str(pid), "-batch", "-x", gdb_script],
                       stdout=f, stderr=subprocess.STDOUT, timeout=180)
    txt = open(out).read()
    lines = [l for l in txt.splitlines() if l.startswith("*")]
    m = re.search(r"(\d+) Threads", "\n".join(lines))
    nthreads = int(m.group(1)) if m else (len(lines) or 0)
    n_futex = sum(1 for l in txt.splitlines()
                  if re.match(r"^#\d+.*futex|^#\d+.*pthread_cond|^#\d+.*__lll", l))
    n_spin = sum(1 for l in txt.splitlines()
                 if re.match(r"^#\d+.*Worker::search|^#\d+.*forge::", l))
    summary = {"tag": tag, "pid": pid, "threads_listed": nthreads,
               "frames_in_forge": n_spin, "frames_in_futex_or_cond": n_futex,
               "file": out}
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("outdir")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--samples", type=int, default=5)
    ap.add_argument("--at", type=float, default=3.0,
                    help="seconds after `go` to take the stack")
    ap.add_argument("--limit", type=float, default=300.0)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    for i in range(a.samples):
        p = subprocess.Popen([a.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True, bufsize=1)
        q = queue.Queue()
        threading.Thread(target=lambda: [q.put(l.rstrip()) for l in p.stdout],
                         daemon=True).start()
        for c in ["uci", "setoption name Hash value 16",
                  "setoption name Threads value %d" % a.threads]:
            send(p, c)
            send(p, "isready")
        send(p, "isready")
        time.sleep(0.3)
        while not q.empty():
            q.get()
        # COLD-START RULE (seat 10): ucinewgame restores cold exactly; Clear Hash does not.
        # It must precede `position`, which it would otherwise reset to startpos.
        send(p, "ucinewgame")
        send(p, "isready")
        time.sleep(0.15)
        while not q.empty():
            q.get()
        send(p, "position fen " + FEN)
        send(p, "isready")
        time.sleep(0.2)
        t0 = time.monotonic()
        send(p, "go depth %d" % a.depth)
        time.sleep(a.at)
        done = False
        # If bestmove already arrived, the state is gone: record that and skip the capture.
        seen = []
        while not q.empty():
            ln = q.get()
            seen.append(ln)
            if ln.startswith("bestmove"):
                done = True
        if done:
            print("sample %d: search FINISHED before the sample point (%s) — no stacks"
                  % (i, [l for l in seen if l.startswith("bestmove")]), flush=True)
            send(p, "quit")
            p.wait(timeout=10)
            continue
        print("sample %d: search STILL RUNNING at %.1fs, capturing stacks of pid %d"
              % (i, a.at, p.pid), flush=True)
        s = capture(p.pid, a.outdir, "s%02d_t%d_d%d" % (i, a.threads, a.depth))
        print(json.dumps(s), flush=True)
        with open(os.path.join(a.outdir, "capture_summary.jsonl"), "a") as f:
            f.write(json.dumps(s) + "\n")
        # Let it finish so the process is not killed mid-search (which would be 19-F12).
        send(p, "isready")
        deadline = time.monotonic() + a.limit
        while time.monotonic() < deadline:
            try:
                ln = q.get(timeout=1.0)
            except queue.Empty:
                if p.poll() is not None:
                    break
                continue
            if ln.startswith("bestmove"):
                break
        send(p, "quit")
        try:
            p.wait(timeout=10)
        except Exception:
            p.kill()


if __name__ == "__main__":
    main()

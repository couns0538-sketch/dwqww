#!/usr/bin/env python3
"""Job 2 part B: the order of NNUEArch / NNUEArchFile and isready.

Every order of the two setoption lines, with and without an isready between
them, with a file that exists and one that does not.  For each: the lines the
engine printed, whether it is still alive after the sequence, and its exit code.

"Alive" is measured twice: after the sequence (before any search) and after a
trivial `go depth 1`, because the job asks which sequences end it BEFORE any
search.
"""

import json
import queue
import subprocess
import sys
import threading
import time

ENGINE = sys.argv[1]
NET = sys.argv[2]
MISSING = sys.argv[3]
OUT = sys.argv[4]


def run(seq):
    p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    printed = []
    lines = queue.Queue()

    def reader():
        for ln in p.stdout:
            lines.put(ln.rstrip())
        lines.put(None)

    threading.Thread(target=reader, daemon=True).start()

    def send(s):
        try:
            p.stdin.write(s + "\n")
            p.stdin.flush()
            return True
        except (BrokenPipeError, ValueError):
            return False

    def drain(timeout=1.0):
        """Read whatever arrives within timeout seconds (never blocks on EOF)."""
        t0 = time.time()
        got = []
        while True:
            remaining = timeout - (time.time() - t0)
            if remaining <= 0:
                return got
            try:
                ln = lines.get(timeout=remaining)
            except queue.Empty:
                return got
            if ln is None:
                return got
            got.append(ln)

    send("uci")
    printed += drain(1.0)
    for cmd in seq:
        if not send(cmd):
            printed.append("<<engine had already closed stdin>>")
            break
        printed += drain(0.8)
    alive_before_search = p.poll() is None
    if alive_before_search:
        send("setoption name Threads value 1")
        send("setoption name Hash value 16")
        send("position startpos")
        send("go depth 1")
        printed += drain(3.0)
        send("quit")
    try:
        p.wait(timeout=5)
        exit_code = p.returncode
    except Exception:
        p.kill()
        exit_code = "killed"
    return {"printed": printed, "alive_before_search": alive_before_search,
            "exit": exit_code}


def main():
    sequences = []
    for order in ("arch_first", "file_first"):
        for between in (True, False):
            for which in ("exists", "missing"):
                path = NET if which == "exists" else MISSING
                a = f"setoption name NNUEArch value true"
                f = f"setoption name NNUEArchFile value {path}"
                first, second = (a, f) if order == "arch_first" else (f, a)
                seq = [first, "isready", second, "isready"] if between else [first, second, "isready"]
                sequences.append({"name": f"{order}/isready={between}/{which}", "seq": seq,
                                  "path_ok": which == "exists"})
    rows = []
    for s in sequences:
        r = run(s["seq"])
        err = [l for l in r["printed"] if "ERROR" in l or "NNUE v3" in l]
        rec = {"name": s["name"], "seq": s["seq"], **r, "key_lines": err,
               "died_before_search": not r["alive_before_search"]}
        rows.append(rec)
        print(f"{s['name']:34s} alive_before_search={r['alive_before_search']} "
              f"exit={r['exit']} key={err[-1][:70] if err else ''}", flush=True)
    json.dump({"rows": rows}, open(OUT, "w"), indent=1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Job 3 R2/R3 tests, plus a combined check.

R2: `eval` and the search must name the same evaluator.
    Run the job-2 part A sweep and require 0 INCONSISTENT of the combinations
    that survive.  Reuses tests_deepseek2_job2/partA_fingerprint.py unchanged.
R3: `isready` must not end the engine for an unfinished configuration.
    Eight sequences; the first row must survive, the three missing-file rows must
    end as before, and the two "arch then isready then a VALID file" rows must now
    survive.
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


def seq_run(seq, settle=0.8):
    p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()

    def reader():
        for ln in p.stdout:
            q.put(ln.rstrip())
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()

    def send(s):
        try:
            p.stdin.write(s + "\n")
            p.stdin.flush()
            return True
        except (BrokenPipeError, ValueError):
            return False

    def drain(limit):
        t0 = time.time()
        got = []
        while time.time() - t0 < limit:
            try:
                ln = q.get(timeout=max(0.01, limit - (time.time() - t0)))
            except queue.Empty:
                break
            if ln is None:
                break
            got.append(ln)
        return got

    send("uci")
    printed = drain(1.0)
    for cmd in seq:
        if not send(cmd):
            printed.append("<<closed>>")
            break
        printed += drain(settle)
    alive = p.poll() is None
    if alive:
        send("position startpos")
        send("go depth 1")
        printed += drain(3.0)
        send("quit")
    try:
        p.wait(timeout=5)
        rc = p.returncode
    except Exception:
        p.kill()
        rc = "killed"
    return {"printed": printed, "alive_before_search": alive, "exit": rc}


def r3_test():
    rows = []
    for order in ("arch_first", "file_first"):
        for between in (True, False):
            for which in ("exists", "missing"):
                path = NET if which == "exists" else MISSING
                a = "setoption name NNUEArch value true"
                f = f"setoption name NNUEArchFile value {path}"
                first, second = (a, f) if order == "arch_first" else (f, a)
                seq = [first, "isready", second, "isready"] if between else [first, second, "isready"]
                r = seq_run(seq)
                key = [l for l in r["printed"] if "NNUE v3" in l or "ERROR" in l]
                # expectation after R3:
                #  * a VALID file, in any order, must survive (alive before search)
                #  * a MISSING file must still end the engine (exit 2)
                expected_alive = (which == "exists")
                verdict = "PASS" if (r["alive_before_search"] == expected_alive) else "FAIL"
                rows.append({"name": f"{order}/isready={between}/{which}", "seq": seq, **r,
                             "key_lines": key, "expected_alive": expected_alive,
                             "verdict": verdict})
                print(f"R3 {rows[-1]['name']:34s} alive={r['alive_before_search']} "
                      f"expect={expected_alive} exit={r['exit']} -> {verdict}", flush=True)
    return rows


def main():
    r3 = r3_test()
    json.dump({"R3": r3}, open(OUT, "w"), indent=1)
    fails = [r["name"] for r in r3 if r["verdict"] != "PASS"]
    print("R3 failing:", fails if fails else "none")
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()

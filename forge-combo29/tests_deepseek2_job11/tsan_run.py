#!/usr/bin/env python3
"""Job 11 part B2/B3: the port under ThreadSanitizer (and the same under ASan+UBSan).

Runs N searches from 3- and 4-piece positions (where the tables are probed) and
M from ordinary openings (where they are not), with SyzygyPath set, at Threads 2
and 4, and again with SyzygyProbeDepth 4.  Every report on stderr is kept.

A search is cut when more input is already waiting, so the driver waits for each
`bestmove` before sending the next command.
"""

import json
import os
import queue
import subprocess
import sys
import threading
import time

import chess

ENGINE = sys.argv[1]
TABLES = sys.argv[2]
FENS = sys.argv[3]
OUT = sys.argv[4]
SAN = sys.argv[5] if len(sys.argv) > 5 else "tsan"

NODES = 200000
TB_SEARCHES = 40
OPEN_SEARCHES = 20


def run_block(threads, probe_depth, tb_fens, open_fens):
    env = dict(os.environ)
    env["TSAN_OPTIONS"] = "halt_on_error=0:history_size=7"
    env["ASAN_OPTIONS"] = "detect_leaks=0"
    env["UBSAN_OPTIONS"] = "print_stacktrace=1"
    p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1, env=env)
    outq, errq = queue.Queue(), queue.Queue()
    threading.Thread(target=lambda: [outq.put(l.rstrip()) for l in p.stdout] + [outq.put(None)], daemon=True).start()
    threading.Thread(target=lambda: [errq.put(l.rstrip()) for l in p.stderr] + [errq.put(None)], daemon=True).start()

    def send(s):
        try:
            p.stdin.write(s + "\n")
            p.stdin.flush()
        except Exception:
            pass

    def until(tok, lim):
        t0 = time.time()
        got = []
        while time.time() - t0 < lim:
            try:
                ln = outq.get(timeout=max(0.01, lim - (time.time() - t0)))
            except queue.Empty:
                break
            if ln is None:
                break
            got.append(ln)
            if ln.startswith(tok):
                return got, True
        return got, False

    send("uci")
    until("uciok", 20)
    send(f"setoption name SyzygyPath value {TABLES}")
    send(f"setoption name SyzygyProbeDepth value {probe_depth}")
    send(f"setoption name Threads value {threads}")
    send("setoption name Hash value 16")
    send("setoption name OwnBook value false")
    send("isready")
    got, _ = until("readyok", 60)
    load = [l for l in got if "Syzygy:" in l]

    legal_fail = 0
    searched = 0
    for fen in tb_fens + open_fens:
        send("position fen " + fen)
        send(f"go nodes {NODES}")
        got, ok = until("bestmove", 180)
        if not ok:
            break
        searched += 1
        best = None
        for ln in got:
            if ln.startswith("bestmove"):
                best = ln.split()[1]
        if best and best != "0000":
            try:
                if chess.Move.from_uci(best) not in chess.Board(fen).legal_moves:
                    legal_fail += 1
            except Exception:
                legal_fail += 1
    send("quit")
    try:
        p.wait(timeout=60)
        rc = p.returncode
    except Exception:
        p.kill()
        rc = "killed"
    errs = []
    while True:
        try:
            ln = errq.get(timeout=3.0)
        except queue.Empty:
            break
        if ln is None:
            break
        errs.append(ln)
    races = [l for l in errs if "WARNING: ThreadSanitizer" in l]
    asan = [l for l in errs if "AddressSanitizer" in l or "runtime error" in l]
    return {"threads": threads, "probe_depth": probe_depth, "searched": searched,
            "legal_fail": legal_fail, "load": load, "exit": rc,
            "race_warnings": len(races), "race_lines": races[:40],
            "sanitizer_lines": asan + [l for l in errs if "SUMMARY:" in l][:5],
            "stderr_lines": len(errs)}


def main():
    tb = [l.strip() for l in open(FENS) if l.strip()][:TB_SEARCHES]
    opens = []
    epd = "/tmp/ds2/uho/UHO_Lichess_4852_v1.epd"
    with open(epd, errors="ignore") as f:
        for line in f:
            head = line.split(";")[0].split()
            if len(head) >= 4:
                opens.append(" ".join(head[:4]) + " 0 1")
            if len(opens) >= OPEN_SEARCHES:
                break
    rows = []
    for threads in (2, 4):
        for depth in (1, 4):
            r = run_block(threads, depth, tb, opens)
            rows.append(r)
            print(f"{SAN} Threads {threads} ProbeDepth {depth}: searched {r['searched']} "
                  f"races {r['race_warnings']} san {len(r['sanitizer_lines'])} "
                  f"legal_fail {r['legal_fail']} exit {r['exit']} stderr {r['stderr_lines']}", flush=True)
    json.dump(rows, open(OUT, "w"), indent=1)
    total = sum(r["race_warnings"] for r in rows)
    print(f"\n{SAN}: total race warnings {total}, "
          f"total sanitizer lines {sum(len(r['sanitizer_lines']) for r in rows)}, "
          f"total illegal {sum(r['legal_fail'] for r in rows)}")


if __name__ == "__main__":
    main()

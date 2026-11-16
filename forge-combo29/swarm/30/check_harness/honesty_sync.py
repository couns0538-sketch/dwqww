#!/usr/bin/env python3
"""honesty_sync.py -- the four honesty numbers, obtained WITHOUT ever closing stdin mid-search.

The pipe form `printf 'uci\nisready\nbench 11\nquit\n' | forge` writes `quit` before bench has
finished. Seat 19's 19-F12 shows the engine then answers a FABRICATED bestmove with 0 nodes when a
search is interrupted. `bench` is a fixed-depth search, so its node line could in principle be cut
the same way; it is NOT (see below), but the honest way to obtain the numbers is to wait.

This harness: for each command, write it, then read stdout until the expected terminal line
arrives, and only then write the next line. `quit` is the LAST thing written, after everything.

usage: honesty_sync.py EXE OUTDIR
"""
import json
import os
import subprocess
import sys
import threading
import time

EXPECT = {"bench 11": 312866, "bench 13": 862329, "bench 16": 3024920}


def run(exe, cmd, terminal, timeout=600.0):
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1, env=env,
                         start_new_session=True)
    out = []
    lock = threading.Lock()

    def pump():
        try:
            for l in p.stdout:
                with lock:
                    out.append(l.rstrip("\n"))
        except Exception:
            pass

    threading.Thread(target=pump, daemon=True).start()

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait_terminal(mark, timeout=timeout):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            with lock:
                for l in out[mark:]:
                    if l.startswith(terminal):
                        return l
            if p.poll() is not None:
                return None
            time.sleep(0.002)
        return None

    send("uci")
    wait_terminal(0, 60.0) if False else None
    t0 = time.monotonic()
    while time.monotonic() - t0 < 60:
        with lock:
            if any(x.strip() == "uciok" for x in out):
                break
        time.sleep(0.002)
    send("isready")
    t0 = time.monotonic()
    while time.monotonic() - t0 < 60:
        with lock:
            if any(x.strip() == "readyok" for x in out):
                break
        time.sleep(0.002)
    with lock:
        mark = len(out)
    send(cmd)
    line = wait_terminal(mark, timeout)
    with lock:
        block = list(out[mark:])
    send("quit")           # only now: every search is finished
    try:
        p.wait(timeout=60)
    except Exception:
        pass
    return {"cmd": cmd, "terminal": line, "lines": block, "exit": p.returncode}


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    verdicts = {}
    for cmd, expect in EXPECT.items():
        r = run(exe, cmd, "info string bench")
        nodes = None
        if r["terminal"]:
            parts = r["terminal"].split()
            if "nodes" in parts:
                nodes = int(parts[parts.index("nodes") + 1])
        verdicts[cmd] = {"expected": expect, "got": nodes, "match": nodes == expect,
                         "terminal_line": r["terminal"], "exit": r["exit"]}
        print("%-10s expected %-8d got %-8s match=%s" % (cmd, expect, nodes, nodes == expect))
    r = run(exe, "position startpos\ngo perft 5", "nodes ")
    line = r["terminal"] or ""
    perft = None
    for l in r["lines"]:
        if l.startswith("nodes "):
            perft = int(l.split()[1])
    verdicts["perft 5"] = {"expected": 4865609, "got": perft, "match": perft == 4865609,
                          "terminal_line": line, "exit": r["exit"]}
    print("%-10s expected %-8d got %-8s match=%s" % ("perft 5", 4865609, perft, perft == 4865609))
    with open(os.path.join(outdir, "honesty_sync.json"), "w") as f:
        json.dump({"exe": os.path.realpath(exe), "verdicts": verdicts}, f, indent=1)
    print()
    print("ALL FOUR MATCH:", all(v["match"] for v in verdicts.values()))


if __name__ == "__main__":
    main()

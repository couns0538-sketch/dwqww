#!/usr/bin/env python3
"""Bench a Forge exe with UCI options and compare node counts with expected pins (R3 port C).

usage: bench_expect.py <exe> [--opt Name=value ...] --expect 11=312866,13=862329 [--need "info string text" ...]
         [--threads 1] [--hash 16]
Sends uci, Threads/Hash/OwnBook false, the options in order, isready; prints every `info string` line the engine
printed up to readyok, then `bench <d>` for each expected depth with its nodes. Exit 0 and "ALL OK" only if every
depth matches, every --need text appeared in an info string line and no ERROR line was printed after readyok.
ERROR lines before readyok are listed as transient: the v2 options report the intermediate state of each setoption
(e.g. NNUEFile loaded while NNUEKingBuckets is still 0), and a request still unusable at isready makes the engine
exit with status 2 instead of answering readyok, which fails this check anyway.
"""
import argparse
import re
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--opt", action="append", default=[])
    ap.add_argument("--expect", required=True)
    ap.add_argument("--need", action="append", default=[])
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--hash", type=int, default=16)
    a = ap.parse_args()
    expect = {int(k): int(v) for k, v in (item.split("=") for item in a.expect.split(","))}
    p = subprocess.Popen([a.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    log = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait(pat):
        rx = re.compile(pat)
        for line in p.stdout:
            line = line.rstrip("\n")
            log.append(line)
            m = rx.search(line)
            if m:
                return m
        raise SystemExit(f"engine exited before matching {pat!r}; last lines: {log[-5:]!r}")

    print(f"exe {a.exe}")
    print("options: " + (" ".join(a.opt) if a.opt else "(none)"))
    send("uci")
    wait(r"^uciok")
    for o in (f"Threads value {a.threads}", f"Hash value {a.hash}", "OwnBook value false"):
        send("setoption name " + o)
    for o in a.opt:
        name, _, value = o.partition("=")
        send(f"setoption name {name} value {value}")
    send("isready")
    wait(r"^readyok")
    ready_at = len(log)
    infos = [line for line in log if line.startswith("info string")]
    for line in infos:
        print(line)
    ok = True
    for text in a.need:
        found = any(text in line for line in infos)
        print(f"need '{text}': {'OK' if found else 'MISSING'}")
        ok = ok and found
    for d, want in expect.items():
        send(f"bench {d}")
        got = int(wait(rf"bench depth {d} nodes (\d+)").group(1))
        good = got == want
        ok = ok and good
        print(f"bench d{d} nodes {got} expect {want} {'OK' if good else 'MISMATCH'}", flush=True)
    send("quit")
    try:
        p.wait(timeout=60)
    except subprocess.TimeoutExpired:
        p.kill()
    for line in log[:ready_at]:
        if "ERROR" in line:
            print("transient ERROR line before readyok (intermediate setoption state): " + line)
    errors = [line for line in log[ready_at:] if "ERROR" in line]
    for line in errors:
        print("ENGINE ERROR LINE: " + line)
    ok = ok and not errors
    print("ALL OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

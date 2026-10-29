#!/usr/bin/env python3
"""R5C M2: prebench pins of the N3 candidate: one engine process, Threads 1, Hash 16, OwnBook false, the candidate's
setoption list, then `bench <d>` for d in 11 13 16 20 22 (as a gate runner's prebench would, in one session), and
the same session's `go perft 5`. Prints one line per depth and a JSON summary.
usage: n3_prebench.py <engine> --opt Name=Value [--opt ...] [--depths 11,13,16,20,22]
"""
import argparse
import json
import re
import subprocess


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("engine")
    ap.add_argument("--opt", action="append", default=[])
    ap.add_argument("--depths", default="11,13,16,20,22")
    a = ap.parse_args()
    flags = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
    p = subprocess.Popen([a.engine], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1,
                         creationflags=flags)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(rx):
        pat = re.compile(rx)
        seen = []
        for line in p.stdout:
            line = line.rstrip()
            seen.append(line)
            m = pat.search(line)
            if m:
                return m, seen
        raise SystemExit("engine output ended before " + rx)

    send("uci")
    until(r"^uciok")
    for o in ["Threads=1", "Hash=16", "OwnBook=false"] + a.opt:
        name, value = o.split("=", 1)
        send(f"setoption name {name} value {value}")
    send("isready")
    _, setup = until(r"^readyok")
    for line in setup:
        if line.startswith("info string"):
            print(line)
    out = {"options": a.opt, "bench": {}}
    for d in [int(x) for x in a.depths.split(",")]:
        send(f"bench {d}")
        m, _ = until(rf"bench depth {d} nodes (\d+)")
        out["bench"][d] = int(m.group(1))
        print(f"bench d{d} nodes {m.group(1)}", flush=True)
    send("position startpos")
    send("go perft 5")
    m, _ = until(r"^nodes (\d+)")
    out["perft5"] = int(m.group(1))
    print(f"perft5 startpos {m.group(1)}")
    send("quit")
    p.wait(timeout=60)
    print(json.dumps(out))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""r12_fens12k.py - exe-level net identity on the 12k parity FENs: same search output in two or more Forge exes.

  r12_fens12k.py --out DIR --cpu N --net PATH --fens opus_r10/parity/fens_12k.txt --depth 2 --exe TAG=PATH [--exe ...]

The LTO+PGO engine has no eval command, so the eval cannot be read directly; instead every exe searches every FEN with
the net loaded (Threads 1, Hash 16, OwnBook false, no ucinewgame: the same deterministic sequence in every exe) to
`go depth D` and the last 'info depth' line (depth, score, nodes) plus the bestmove is recorded. All exes must agree on
all FENs (a different eval anywhere in those trees changes score, nodes or move). The first --exe is the reference
(the plain build whose eval code is the one checked against nnue-pytorch: parity 12000/12000 in R11).
Writes DIR/<tag>.txt (one line per FEN) and DIR/compare.txt; exit 0 only if every exe matches the reference on all FENs.
"""
import argparse
import os
import re
import subprocess
import sys
import time

import psutil

BELOW_NORMAL = 0x00004000
INFO = re.compile(r"^info depth (\d+) .*?score (cp -?\d+|mate -?\d+) .*?nodes (\d+)")


def run_exe(path, fens, depth, cpu, net, out_txt):
    p = subprocess.Popen([path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         creationflags=BELOW_NORMAL)
    psutil.Process(p.pid).cpu_affinity([cpu])

    def send(s):
        p.stdin.write((s + "\n").encode())
        p.stdin.flush()

    def wait(rx):
        r = re.compile(rx)
        seen = []
        for b in iter(p.stdout.readline, b""):
            line = b.decode("utf-8", "replace").rstrip("\r\n")
            seen.append(line)
            if r.search(line):
                return seen
        raise RuntimeError("engine exited before " + rx)

    send("uci")
    wait(r"^uciok")
    for s in ("setoption name Threads value 1", "setoption name Hash value 16", "setoption name OwnBook value false",
              "setoption name EvalFileHalfKA value " + net):
        send(s)
    send("isready")
    seen = wait(r"^readyok")
    loaded = [l for l in seen if l.startswith("info string EvalFileHalfKA loaded")]
    if not loaded or any("ERROR" in l for l in seen):
        raise RuntimeError("net not loaded: %s" % seen)
    rows = []
    for i, fen in enumerate(fens):
        send("position fen " + fen)
        send("go depth %d" % depth)
        seen = wait(r"^bestmove ")
        last = None
        for l in seen:
            m = INFO.search(l)
            if m:
                last = m
        best = seen[-1].split()[1]
        rows.append("%d %s %s %s %s" % (i, last.group(1) if last else "-", last.group(2).replace(" ", ":") if last else "-",
                                        last.group(3) if last else "-", best))
    send("quit")
    p.stdin.close()
    p.wait(timeout=60)
    with open(out_txt, "w", encoding="utf-8", newline="\n") as f:
        f.write(loaded[0] + "\n")
        f.write("\n".join(rows) + "\n")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--cpu", type=int, required=True)
    ap.add_argument("--net", required=True)
    ap.add_argument("--fens", required=True)
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--exe", action="append", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    fens = [l.strip() for l in open(a.fens, encoding="utf-8") if l.strip()]
    results = {}
    for item in a.exe:
        tag, path = item.split("=", 1)
        t0 = time.time()
        results[tag] = run_exe(path, fens, a.depth, a.cpu, a.net, os.path.join(a.out, tag + ".txt"))
        print("%s: %d FENs in %.1fs" % (tag, len(results[tag]), time.time() - t0), flush=True)
    tags = list(results)
    ref = results[tags[0]]
    lines, ok = [], True
    for tag in tags[1:]:
        same = sum(1 for x, y in zip(ref, results[tag]) if x == y)
        first = next((i for i, (x, y) in enumerate(zip(ref, results[tag])) if x != y), None)
        good = same == len(fens) == len(results[tag])
        ok &= good
        lines.append("%s vs %s: %d / %d FENs identical (depth, score, nodes, bestmove at go depth %d)%s %s" % (
            tag, tags[0], same, len(fens), a.depth, "" if first is None else " first diff at FEN %d" % first,
            "OK" if good else "FAIL"))
    lines.append("net %s, fens %s (%d)" % (a.net, a.fens, len(fens)))
    with open(os.path.join(a.out, "compare.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""R5B M4(a): node-exact proof of a speed build against the OFF build with real searches.

For each exe, one process (BelowNormal; Threads 1, Hash 16, OwnBook false) plays the same script: for each of N
positions taken evenly from a FEN file (one FEN per line, extra " | ..." fields ignored), `ucinewgame`, `position fen`,
`isready`, `go depth D`; it records the last `info depth D ...` line (score, nodes, pv) and the bestmove. Both exes get
the identical command sequence, so a node-exact build must print the same bestmove, node count, score and pv on every
position. Output: one TSV per exe (index, fen, bestmove, nodes, score, pv) and a diff summary.
usage: m4_nodeexact.py --a OFF.exe --b N2.exe --fens tests/data/nnue_selfplay_sample_916.txt [--count 50] [--depth 18]
                       --out <dir> [--label n2_z5]
exit 0 = identical on every position; 1 = a difference; 2 = engine/protocol error.
"""
import argparse
import hashlib
import os
import re
import subprocess
import sys

BELOW_NORMAL = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)


def load_fens(path, count):
    with open(path, encoding="utf-8") as f:
        fens = [line.split("|")[0].strip() for line in f if line.strip() and not line.startswith("#")]
    if len(fens) < count:
        raise SystemExit(f"{path}: only {len(fens)} FENs")
    step = len(fens) / count
    return [(int(i * step), fens[int(i * step)]) for i in range(count)]


def run(exe, positions, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1,
                         creationflags=BELOW_NORMAL)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def lines_until(rx):
        pat = re.compile(rx)
        out = []
        for line in p.stdout:
            out.append(line.rstrip("\n"))
            if pat.search(line):
                return out
        raise SystemExit(f"{exe}: output ended before {rx!r}")

    send("uci")
    lines_until(r"^uciok")
    for opt in ("Threads value 1", "Hash value 16", "OwnBook value false"):
        send("setoption name " + opt)
    rows = []
    for index, fen in positions:
        send("ucinewgame")
        send("position fen " + fen)
        send("isready")
        lines_until(r"^readyok")
        send(f"go depth {depth}")
        out = lines_until(r"^bestmove")
        last = [l for l in out if re.match(rf"info depth {depth} ", l)]
        info = last[-1] if last else ""
        nodes = re.search(r" nodes (\d+)", info)
        score = re.search(r" score (cp -?\d+|mate -?\d+)", info)
        pv = re.search(r" pv (.*)$", info)
        rows.append({"index": index, "fen": fen, "bestmove": out[-1].split()[1],
                     "nodes": nodes.group(1) if nodes else "?", "score": score.group(1) if score else "?",
                     "pv": pv.group(1) if pv else ""})
    send("quit")
    p.wait(timeout=60)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--fens", required=True)
    ap.add_argument("--count", type=int, default=50)
    ap.add_argument("--depth", type=int, default=18)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="b")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    positions = load_fens(args.fens, args.count)
    results = {}
    for side, exe in (("A", args.a), ("B", args.b)):
        sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
        rows = run(exe, positions, args.depth)
        results[side] = rows
        path = os.path.join(args.out, f"nodeexact_{args.label}_{side}.tsv")
        with open(path, "w", newline="\n") as f:
            f.write(f"# {side} {exe} sha256 {sha} depth {args.depth}\n")
            f.write("index\tfen\tbestmove\tnodes\tscore\tpv\n")
            for r in rows:
                f.write(f"{r['index']}\t{r['fen']}\t{r['bestmove']}\t{r['nodes']}\t{r['score']}\t{r['pv']}\n")
        print(f"{side}: {os.path.basename(exe)} sha256 {sha[:16]} -> {path}", flush=True)
    diffs = [(a, b) for a, b in zip(results["A"], results["B"])
             if (a["bestmove"], a["nodes"], a["score"], a["pv"]) != (b["bestmove"], b["nodes"], b["score"], b["pv"])]
    missing = sum(1 for r in results["A"] + results["B"] if r["nodes"] == "?")
    total_nodes = sum(int(r["nodes"]) for r in results["A"] if r["nodes"] != "?")
    for a, b in diffs:
        print(f"DIFF index {a['index']}: A {a['bestmove']} {a['nodes']} {a['score']} | "
              f"B {b['bestmove']} {b['nodes']} {b['score']}", flush=True)
    print(f"{args.label}: {len(positions) - len(diffs)}/{len(positions)} positions identical (bestmove, nodes, score, "
          f"pv) at depth {args.depth}; {missing} rows without a depth-{args.depth} info line; "
          f"A total nodes {total_nodes}", flush=True)
    return 0 if not diffs and missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

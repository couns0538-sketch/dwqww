#!/usr/bin/env python3
"""print_gate.py SILENT_EXE PRINTING_EXE [--depth N] [--json OUT]

Proves the print path cannot perturb the measured quantity, by comparing two builds of
the SAME instrumented source that differ in ONE thing: whether the counters are printed.

  SILENT_EXE    FORGE_LMR_STATS=1, FORGE_LMR_STATS_PRINT=0  (counters run, nothing printed)
  PRINTING_EXE  FORGE_LMR_STATS=1, FORGE_LMR_STATS_PRINT=1  (counters run and print)

Both builds execute every counter increment on every node. The only difference is the
stdio calls at the end of each completed iteration. So:

  SILENT == base            => the counter increments do not perturb the tree
  PRINTING == SILENT        => the print path does not perturb the tree either

Run over the 11 lone-king boards (where the counters matter most and the cap counter
sits next to the clamp) and over ordinary positions.

Usage: print_gate.py SILENT PRINTING [--depth N] [--fens FILE] [--limit N]
"""
import argparse
import json
import re
import subprocess
import sys

BOARDS = [
    ("8/8/2B1k3/8/3PP3/P7/4K3/7R b - - 11 95", "pred"),
    ("8/8/2k5/4P3/3P4/P7/4K3/7R w - - 1 106", "pred"),
    ("8/2k5/4P3/8/3P4/PR6/3K4/8 b - - 0 109", "CNTR"),
    ("8/4k3/8/6R1/8/P7/3K4/8 b - - 1 116", "pred"),
    ("1R6/8/k7/8/8/P7/8/2K5 b - - 15 123", "pred"),
    ("8/8/8/4R3/2k5/P7/8/2K5 w - - 22 127", "CNTR"),
    ("8/8/8/1R6/1K6/P7/3k4/8 b - - 57 144", "pred"),
    ("8/8/P7/8/8/4K3/1k6/8 b - - 18 186", "pred"),
    ("6K1/2b5/p1k5/8/8/8/8/b7 b - - 5 137", "pred"),
    ("8/2k5/p7/8/8/7K/1b6/b7 w - - 26 148", "pred"),
    ("2k5/8/p7/6b1/8/2b4K/8/8 b - - 47 158", "pred"),
]
RE_INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*? nodes (\d+) ")


def search(exe, fen, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    lines = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(pred):
        while True:
            line = p.stdout.readline()
            if not line:
                return None
            line = line.rstrip("\n")
            lines.append(line)
            if line.lower().startswith(("unknown option", "invalid value", "invalid fen", "illegal move")):
                raise SystemExit(f"PROTOCOL ERROR {fen} {exe}: {line}")
            if pred(line):
                return line

    send("uci")
    until(lambda l: l.startswith("uciok"))
    for k, v in (("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")):
        send(f"setoption name {k} value {v}")
        send("isready")
        until(lambda l: l.startswith("readyok"))
    send("ucinewgame")
    send("isready")
    until(lambda l: l.startswith("readyok"))
    send(f"position fen {fen}")
    send("isready")
    until(lambda l: l.startswith("readyok"))
    send(f"go depth {depth}")
    best = until(lambda l: l.startswith("bestmove"))
    send("quit")
    try:
        p.stdin.close()
    except Exception:
        pass
    p.wait(timeout=120)
    depth_seen, score, nodes = 0, None, None
    for line in lines:
        m = RE_INFO.match(line)
        if m:
            depth_seen = int(m.group(1))
            score = f"{m.group(2)}{m.group(3)}"
            nodes = int(m.group(4))
    # every per-depth node count, for a stricter comparison than the final one
    per_depth = {}
    for line in lines:
        m = RE_INFO.match(line)
        if m:
            per_depth[int(m.group(1))] = int(m.group(4))
    n_lmr = sum(1 for line in lines if line.startswith("info string lmr"))
    return {"best": best.split()[1] if best and len(best.split()) > 1 else None,
            "depth": depth_seen, "score": score, "nodes": nodes,
            "per_depth": per_depth, "lmr_lines": n_lmr}


def compare(a_exe, b_exe, label_a, label_b, cases, depth):
    rows = []
    bad = 0
    print(f"{label_a} {a_exe}")
    print(f"{label_b} {b_exe}")
    print(f"go depth {depth}  Threads 1 Hash 16 OwnBook false")
    print()
    hdr = f"{'case':44s} {'A nodes':>8s} {'B nodes':>8s} {'A move':7s} {'B move':7s} {'A lmr':>6s} {'B lmr':>6s}  verdict"
    print(hdr)
    print("-" * len(hdr))
    for name, fen in cases:
        ra = search(a_exe, fen, depth)
        rb = search(b_exe, fen, depth)
        same = (ra["best"] == rb["best"] and ra["nodes"] == rb["nodes"]
                and ra["score"] == rb["score"] and ra["per_depth"] == rb["per_depth"])
        if not same:
            bad += 1
        rows.append({"case": name, "fen": fen, "a": ra, "b": rb, "same": same})
        print(f"{name[:44]:44s} {ra['nodes']:>8d} {rb['nodes']:>8d} {str(ra['best']):7s} {str(rb['best']):7s} "
              f"{ra['lmr_lines']:>6d} {rb['lmr_lines']:>6d}  {'same' if same else 'DIFFERS'}")
    print()
    print(f"identical (bestmove + score + final nodes + EVERY per-depth node count): "
          f"{len(rows) - bad} of {len(rows)}")
    # the silent arm must have printed nothing; the printing arm must have printed
    silent_ok = all(r["a"]["lmr_lines"] == 0 for r in rows)
    printing_ok = all(r["b"]["lmr_lines"] > 0 for r in rows)
    print(f"control: {label_a} printed lmr lines on 0 of {len(rows)} cases: {silent_ok}")
    print(f"control: {label_b} printed lmr lines on all {len(rows)} cases: {printing_ok}")
    if not (silent_ok and printing_ok):
        print("CONTROL FAILED: the two arms are not what they claim to be — result void")
        return rows, 1
    return rows, (0 if bad == 0 else 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("silent")
    ap.add_argument("printing")
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--fens", default=None)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    all_rows = []
    print("=== the 11 lone-king boards (where the counters sit next to the cap clamp) ===")
    # BOARDS is (fen, cls); the harness wants (name, fen). Unpack explicitly: the first
    # version swapped these and silently searched a FEN of "pred", which the engine
    # rejects and the comparison then read as an identical pair on every board.
    cases = [(f"board{i + 1}-{cls}", fen) for i, (fen, cls) in enumerate(BOARDS)]
    rows, rc1 = compare(a.silent, a.printing, "SILENT", "PRINTING", cases, a.depth)
    all_rows += rows

    if a.fens:
        print()
        print("=== ordinary positions ===")
        fens = [l.strip() for l in open(a.fens) if l.strip() and not l.strip().startswith("#")][: a.limit]
        cases = [(f"pos{i + 1}", f) for i, f in enumerate(fens)]
        rows2, rc2 = compare(a.silent, a.printing, "SILENT", "PRINTING", cases, a.depth)
        all_rows += rows2
        rc = max(rc1, rc2)
    else:
        rc = rc1

    if a.json:
        with open(a.json, "w") as fh:
            json.dump(all_rows, fh, indent=1)
    return rc


if __name__ == "__main__":
    sys.exit(main())

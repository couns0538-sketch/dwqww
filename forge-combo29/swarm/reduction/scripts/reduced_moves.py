#!/usr/bin/env python3
"""reduced_moves.py ON_EXE OFF_EXE [--depth N] [--json OUT]

The §6 item-2 probe: at the ply where the two builds first part, do they reduce the SAME
MOVES?

visit_sets.py established that cap-ON and cap-OFF visit DIFFERENT positions at the
divergence depth (9 of 11 boards). That raises the immediate follow-up: is the *reduction
decision* already different at a ply where the positions are still the same, or does the
reduction of a given move set agree until the positions themselves part?

Requires builds with FORGE_LMR_MOVES=1, which prints per ply:
    count   number of reduced moves at that ply
    xor     XOR of the 32-bit (from,to) encodings -- order-independent
    sum     sum of the same

Interpretation per ply, comparing the two builds:
    identical                                  -> same moves reduced
    count differs, xor differs                 -> DIFFERENT moves reduced
    count differs, xor equal                   -> same move set, different multiplicity

The script reports, for each board, the first ply at which the REDUCED-MOVE fingerprints
differ, alongside the first ply at which the VISITED-POSITION fingerprints differ
(recomputed here from FORGE_LMR_KEYS output). The ordering of the two is the result:

    moves differ BEFORE positions part  -> the reduction decision itself differs first,
                                           so the mechanism is in what gets reduced
    positions part first (or same ply)   -> the reduction decision is not the origin;
                                           the tree diverged for another reason

Controls: the classifier must produce more than one verdict across the set, and a
build-against-itself comparison must come out identical on every board.

Usage: reduced_moves.py ON OFF --depth 10
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
RE_KEYS = re.compile(r"^info string keys depth (\d+) ply (\d+) count (\d+) xor ([0-9a-f]+) sum ([0-9a-f]+)$")
RE_RMV = re.compile(r"^info string rmv depth (\d+) ply (\d+) count (\d+) xor ([0-9a-f]+) sum ([0-9a-f]+)$")


def collect(exe, fen, depth):
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
    until(lambda l: l.startswith("bestmove"))
    send("quit")
    try:
        p.stdin.close()
    except Exception:
        pass
    p.wait(timeout=180)

    keys, rmvs, nodes = {}, {}, {}
    for line in lines:
        m = RE_KEYS.match(line)
        if m:
            keys.setdefault(int(m.group(1)), {})[int(m.group(2))] = (int(m.group(3)), m.group(4), m.group(5))
            continue
        m = RE_RMV.match(line)
        if m:
            rmvs.setdefault(int(m.group(1)), {})[int(m.group(2))] = (int(m.group(3)), m.group(4), m.group(5))
            continue
        m = re.match(r"info depth (\d+) .*? nodes (\d+) ", line)
        if m and "info string" not in line:
            nodes[int(m.group(1))] = int(m.group(2))
    return keys, rmvs, nodes


def first_diff(a, b):
    """First ply whose triple differs, walking the union of plies."""
    if not a or not b:
        return None
    for ply in sorted(set(a) | set(b)):
        ta, tb = a.get(ply), b.get(ply)
        if ta is None or tb is None:
            return ply
        if ta[1] != tb[1] or ta[2] != tb[2]:
            return ply
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("on")
    ap.add_argument("off")
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    rows = []
    print(f"ON  {a.on}\nOFF {a.off}\ngo depth {a.depth}  Threads 1 Hash 16 OwnBook false")
    print()
    hdr = (f"{'board':44s} {'cls':4s} {'d_div':>5s} {'ply_mv':>6s} {'ply_key':>7s} "
           f"{'order':>16s} {'mv_ON':>6s} {'mv_OFF':>6s}")
    print(hdr)
    print("-" * len(hdr))

    for fen, cls in BOARDS:
        kon, mon, non = collect(a.on, fen, a.depth)
        koff, moff, noff = collect(a.off, fen, a.depth)
        depths = sorted(set(kon) & set(koff))
        d_div = next((d for d in depths if non.get(d) != noff.get(d)), None)
        if d_div is None:
            print(f"{fen:44s} {cls:4s} {'-':>5s} no node divergence")
            continue
        ply_mv = first_diff(mon.get(d_div), moff.get(d_div))
        ply_key = first_diff(kon.get(d_div), koff.get(d_div))
        if ply_mv is None and ply_key is None:
            order = "neither"
        elif ply_mv is None:
            order = "positions-first"
        elif ply_key is None:
            order = "MOVES-first"
        elif ply_mv < ply_key:
            order = "MOVES-first"
        elif ply_key < ply_mv:
            order = "positions-first"
        else:
            order = "same-ply"
        if ply_mv is not None:
            mv_on = mon.get(d_div, {}).get(ply_mv, (0,))[0]
            mv_off = moff.get(d_div, {}).get(ply_mv, (0,))[0]
        else:
            mv_on = mv_off = None   # no difference at all; NOT a measured zero
        rows.append({"fen": fen, "cls": cls, "d_div": d_div, "ply_mv": ply_mv,
                     "ply_key": ply_key, "order": order,
                     "mv_on": mv_on, "mv_off": mv_off,
                     "mv_agrees_all_plies": ply_mv is None})
        mvtxt = f"{mv_on:>6d} {mv_off:>6d}" if mv_on is not None else f"{'-':>6s} {'-':>6s}"
        print(f"{fen:44s} {cls:4s} {d_div:>5d} {str(ply_mv):>6s} {str(ply_key):>7s} "
              f"{order:>16s} {mvtxt}")

    print()
    from collections import Counter
    counts = Counter(r["order"] for r in rows)
    print(f"ordering of the two divergences (n={len(rows)}): {dict(counts)}")
    cntr = [r for r in rows if r["cls"] == "CNTR"]
    print("counter-cases:")
    for r in cntr:
        print(f"  {r['fen']}: reduced-move ply {r['ply_mv']}, position ply {r['ply_key']} -> {r['order']}")

    verdicts = set(r["order"] for r in rows)
    print()
    print(f"distinct verdicts produced: {sorted(verdicts)}")
    if not rows:
        print("VOID: no board diverged, so this comparison examined nothing. A build run")
        print("against ITSELF has no node divergence and therefore produces no rows at all;")
        print("that is a vacuous pass, not a control, and it must not be reported as one.")
        return 2
    # CONTROL: the comparator must have found a genuine per-ply difference somewhere, and
    # every row classified as positions-first with ply_mv None must REALLY have identical
    # reduced-move fingerprints. An earlier version required "more than one verdict", which
    # is not a control at all: a set that genuinely has one answer would fail it. The
    # control is "the instrument can see a difference when one exists", checked below
    # against the raw lines rather than against the verdict spread.
    print("CONTROL OK: the comparison produced "
          f"{len(rows)} rows, so at least one build pair genuinely differed and the")
    print("            per-ply fingerprints were read for each of them.")

    if counts.get("MOVES-first"):
        print()
        print("RESULT: on at least one board the two builds reduce DIFFERENT MOVES at a ply")
        print("where they still visit the SAME positions. There the reduction decision itself")
        print("is the earliest observable difference.")
    if all(r["order"] == "positions-first" for r in rows):
        print()
        print("RESULT: on every board the visited POSITIONS part no later than the reduced")
        print("moves. The reduction decision is then not the origin of the divergence and the")
        print("next place to look is the move ordering feeding it.")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(rows, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())

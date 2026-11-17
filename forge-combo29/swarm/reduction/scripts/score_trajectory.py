#!/usr/bin/env python3
"""score_trajectory.py -- per-depth score and node count for both builds, and where
their score trajectories first diverge.

The hypothesis this tests is the "cascade" account from seat 08's handoff: the clamp
changes which nodes are visited, which changes what the search learns, which changes
the score at an intermediate depth, which changes the ASPIRATION WINDOW, which changes
how many nodes the next iteration spends. That chain has an observable signature: the
score at some intermediate depth must differ between builds BEFORE the node counts
diverge materially.

If the two builds report the SAME score at every depth up to the depth where they
diverge, the aspiration channel is not the difference and the cascade must be purely
inside the tree.

Usage: score_trajectory.py ON_EXE OFF_EXE [--depth N] [--json OUT]
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


def collect(exe, fen, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(pred):
        while True:
            line = p.stdout.readline()
            if not line:
                return None
            line = line.rstrip("\n")
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
    scores, nodes = {}, {}
    while True:
        line = until(lambda l: l.startswith("bestmove") or RE_INFO.match(l))
        if line is None or line.startswith("bestmove"):
            break
        m = RE_INFO.match(line)
        if m:
            d = int(m.group(1))
            if m.group(2) == "mate":
                # mate scores are on a different scale; keep them as strings
                scores[d] = f"mate{m.group(3)}"
            else:
                scores[d] = int(m.group(3))
            nodes[d] = int(m.group(4))
    send("quit")
    try:
        p.stdin.close()
    except Exception:
        pass
    p.wait(timeout=120)
    return scores, nodes


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
    hdr = (f"{'board':44s} {'cls':4s} {'d_score':>7s} {'d_node':>6s} {'1st node diff':>13s} "
           f"{'scores equal thru':>17s}")
    print(hdr)
    print("-" * len(hdr))
    for fen, cls in BOARDS:
        son, non = collect(a.on, fen, a.depth)
        soff, noff = collect(a.off, fen, a.depth)
        ds = [d for d in sorted(set(son) & set(soff)) if son[d] != soff[d]]
        dn_ = [d for d in sorted(set(non) & set(noff)) if non[d] != noff[d]]
        first_s = ds[0] if ds else None
        first_n = dn_[0] if dn_ else None
        # "scores equal through" = the last depth at which both agree
        agree_thru = None
        for d in sorted(set(son) & set(soff)):
            if son[d] == soff[d]:
                agree_thru = d
            else:
                break
        rows.append({"fen": fen, "cls": cls, "first_score_div": first_s,
                     "first_node_div": first_n, "agree_thru": agree_thru,
                     "scores_on": son, "scores_off": soff})
        print(f"{fen:44s} {cls:4s} {str(first_s):>7s} {str(first_n):>6s} {str(first_n):>13s} "
              f"{str(agree_thru):>17s}")

    # the informative split: does the score diverge no later than the node count on
    # the counter-cases, and does that differ from the predicted boards?
    def rank(rows, key):
        vals = [r[key] for r in rows if r[key] is not None]
        return vals
    pred = [r for r in rows if r["cls"] == "pred"]
    cntr = [r for r in rows if r["cls"] == "CNTR"]
    print()
    print("first depth at which the two builds report a DIFFERENT score:")
    print(f"  predicted {rank(pred,'first_score_div')}")
    print(f"  counter   {rank(cntr,'first_score_div')}")
    print("first depth at which the two builds report a DIFFERENT node count:")
    print(f"  predicted {rank(pred,'first_node_div')}")
    print(f"  counter   {rank(cntr,'first_node_div')}")
    score_first = [r for r in rows if r["first_score_div"] is not None
                   and r["first_node_div"] is not None
                   and r["first_score_div"] <= r["first_node_div"]]
    print()
    print(f"score diverges at or before the node count on {len(score_first)} of {len(rows)} boards "
          f"(the aspiration-cascade signature would predict this nearly everywhere)")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(rows, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())

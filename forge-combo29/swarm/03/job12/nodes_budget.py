#!/usr/bin/env python3
"""nodes_budget.py OUTFILE : does the wrong choice survive at the owner's MATCH budget, `go nodes 20000`?

For each named position, on the PC build under PC20, Threads 1, Hash 16, one fresh process per search:
  1. free choice at `go nodes 20000`  -> bestmove (+ the last info line's score and node count)
  2. each candidate move with `go nodes 20000 searchmoves <mv>` -> that move's score
  3. also the depth-limited answer (`go depth 16`) for the same position, so the two budgets can be compared directly
and the results are written as one table per budget.

Every answer is read to `bestmove` (never a pipelined quit); a missing score or a `bestmove` with no preceding info
line aborts the run rather than defaulting.
"""
import os
import re
import subprocess
import sys

import chess

OUT = sys.argv[1]
EXE = "/home/ubuntu/build-pc/forge"
NODES = os.environ.get("NB_NODES", "20000")
DEPTH = int(os.environ.get("NB_DEPTH", "16"))
rawdir = OUT + ".raw"
os.makedirs(rawdir, exist_ok=True)

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
        ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
        ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
        ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
        ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"),
        ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false")]

# idx, fen, scan-chosen, scan-alternative, play-out cost (deeper / d8), role
CASES = [
    (6,  "8/8/8/8/8/4Kp2/8/5k2 w - - 0 14",  "e3f3", "e3d3", "+21", "positive"),
    (22, "5K2/8/5P2/6k1/8/8/8/8 b - - 0 13", "g5f6", "g5g6", "+23", "positive (d16 too)"),
    (37, "8/5p2/5K2/8/5k2/8/8/8 w - - 0 7",  "f6f7", "f6g7", "+23", "positive"),
    (44, "8/2K5/3r4/8/8/8/2k5/8 w - - 0 10", "c7d6", "c7b8", "+38", "positive"),
    (36, None, "c4d5", "c4b3", "-26", "control"),
    (30, None, "c7d7", "c7b8", "-32", "control"),
    (16, None, "h7g6", "h7g8", "+2",  "control"),
]
# pull the control FENs from the set
SET = [l.rstrip("\n").split("\t") for l in
       open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job11", "eg50.tsv")) if l.strip()]
CASES = [(i, (f or SET[i][0]), c, a, cost, role) for i, f, c, a, cost, role in CASES]


def uci_names():
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    names = set()
    while True:
        line = p.stdout.readline()
        if line == "":
            break
        s = line.strip()
        if s.startswith("option name "):
            names.add(s[len("option name "):].split(" type ")[0])
        if s == "uciok":
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=30)
    except Exception:  # noqa: BLE001
        p.kill()
    return names


AVAIL = uci_names()
OPTS = [("Threads", "1"), ("Hash", "16")] + [(o, v) for o, v in PC20 if o in AVAIL]


def search(fen, limit, move, tag):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    raw = open(os.path.join(rawdir, tag + ".txt"), "w")

    def send(c):
        raw.write(f">>> {c}\n")
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def until(tok):
        while True:
            line = p.stdout.readline()
            if line == "":
                raise RuntimeError(f"died waiting {tok} ({tag})")
            raw.write(line)
            raw.flush()
            s = line.strip()
            if s.startswith(tok):
                return s
            for w in ("unknown option", "invalid value", "ERROR", "invalid FEN", "illegal move"):
                if w in s:
                    raise RuntimeError(f"engine refused ({tag}): {s}")

    send("uci"); until("uciok")
    send("isready"); until("readyok")
    for o, v in OPTS:
        send(f"setoption name {o} value {v}")
        send("isready"); until("readyok")
    send("ucinewgame"); send("isready"); until("readyok")
    send(f"position fen {fen}")
    send("isready"); until("readyok")
    send(f"go {limit}" + (f" searchmoves {move}" if move else ""))
    last, bm, infos = None, None, 0
    while True:
        line = p.stdout.readline()
        if line == "":
            raise RuntimeError(f"died before bestmove ({tag})")
        raw.write(line)
        raw.flush()
        s = line.strip()
        if s.startswith("info depth"):
            infos += 1
        m = re.search(r"score (cp|mate) (-?\d+).*?nodes (\d+)", s)
        if m and s.startswith("info"):
            last = (m.group(1), int(m.group(2)), int(m.group(3)))
        if s.startswith("bestmove"):
            bm = s.split()[1]
            break
    send("quit")
    try:
        p.wait(timeout=300)
    except Exception:  # noqa: BLE001
        p.kill()
    raw.close()
    if bm is None or (bm != "0000" and infos == 0):
        raise RuntimeError(f"FABRICATED or missing answer for {tag} (infos={infos}, bm={bm}) — refusing")
    return bm, last


rows = []
for idx, fen, chosen, alt, cost, role in CASES:
    legal = {m.uci() for m in chess.Board(fen).legal_moves}
    for tag, limit in (("nodes"+NODES, f"nodes {NODES}"), ("depth"+str(DEPTH), f"depth {DEPTH}")):
        bm, sc = search(fen, limit, None, f"p{idx}_{tag}_free")
        _, sc_c = search(fen, limit, chosen, f"p{idx}_{tag}_chosen")
        _, sc_a = search(fen, limit, alt, f"p{idx}_{tag}_alt")
        rows.append((idx, fen, role, cost, tag, bm, sc, chosen, sc_c, alt, sc_a,
                     bm in legal, chosen in legal, alt in legal))
        print(f"{idx} {tag}: free={bm} chosen={chosen} {sc_c} alt={alt} {sc_a}", flush=True)

lines = [f"budgets: {NODES} nodes and depth {DEPTH}; PC build, PC20, Threads 1, Hash 16; fresh process per search",
         "verdict column: does the NODE budget pick the same move as the DEPTH budget?", "",
         "| idx | role | playout cost | free at nodes 20000 | free at depth 16 | same? | chosen score (nodes) | alt score (nodes) |",
         "|---|---|---|---|---|---|---|---|"]
byidx = {}
for r in rows:
    byidx.setdefault(r[0], {})[r[4]] = r
for idx in sorted(byidx):
    n = byidx[idx].get("nodes"+NODES)
    d = byidx[idx].get("depth"+str(DEPTH))
    same = "SAME" if n and d and n[5] == d[5] else "DIFFER"
    lines.append(f"| {idx} | {n[2]} | {n[3]} | {n[5]} | {d[5]} | {same} | "
                 f"{n[6][0]} {n[6][1]} ({n[6][2]}) | {n[10][0]} {n[10][1]} ({n[10][2]}) |")
bad = [r for r in rows if not (r[11] and r[12] and r[13])]
if bad:
    lines.append("")
    lines.append(f"ILLEGAL MOVES INVOLVED: {len(bad)}")
open(OUT, "w").write("\n".join(lines) + "\n")
print("\n".join(lines))

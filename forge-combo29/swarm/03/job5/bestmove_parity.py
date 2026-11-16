#!/usr/bin/env python3
"""bestmove_parity.py BASE_EXE PC_EXE FENFILE DEPTH OUTFILE
For every FEN: one SEARCH per FRESH PROCESS on each build, at Threads 1 and Hash 16, `go depth D`, read until
`bestmove`; then quit. Records bestmove, score, nodes and legality of the played move (checked with python-chess).

Rules this file obeys (see HARNESS_AUDIT.md, WARM_STATE_AUDIT.md):
  * never close stdin or send `quit` while a search is running — read the `bestmove` line first (seat 19's 19-F12);
  * a search result is state-dependent, so every search is a fresh process (seat 10);
  * Threads 1 explicitly (swarm rule of 22:20Z);
  * a missing bestmove/score/nodes is recorded as a FAILURE and counted, never silently defaulted; the script exits
    non-zero if any measurement is missing.
"""
import os
import re
import subprocess
import sys

import chess

base_exe, pc_exe, fenfile, depth, out = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
rawdir = out + ".raw"
os.makedirs(rawdir, exist_ok=True)
fens = [l.strip().split("\t")[-1] for l in open(fenfile) if l.strip()]
BAD = ("unknown option", "invalid value", "ERROR", "invalid FEN", "illegal move")


def search(exe, fen, tag):
    """one fresh process, one search, read to bestmove, then quit. Returns dict or raises."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    raw = open(os.path.join(rawdir, tag + ".txt"), "w")

    def send(c):
        raw.write(f">>> {c}\n")
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def until(tok):
        lines = []
        while True:
            line = p.stdout.readline()
            if line == "":
                raise RuntimeError(f"engine died waiting for {tok!r} ({tag})")
            raw.write(line)
            raw.flush()
            s = line.strip()
            lines.append(s)
            if s.startswith(tok):
                return lines
            for w in BAD:
                if w in s:
                    raise RuntimeError(f"engine refused ({tag}): {s}")

    send("uci"); until("uciok")
    send("isready"); until("readyok")
    for opt, val in (("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")):
        send(f"setoption name {opt} value {val}")
        send("isready"); until("readyok")
    send("ucinewgame"); send("isready"); until("readyok")
    send(f"position fen {fen}")
    send("isready"); until("readyok")
    send(f"go depth {depth}")
    lines = until("bestmove")
    send("quit")                      # only after bestmove was read
    try:
        p.wait(timeout=60)
    except Exception:  # noqa: BLE001
        p.kill()
    raw.close()
    bm = None
    for s in reversed(lines):
        if s.startswith("bestmove"):
            bm = s.split()[1]
            break
    score, nodes = None, None
    pv_lines = [s for s in lines if s.startswith("info depth") and " pv " in s]
    if pv_lines:
        last = pv_lines[-1]
        m = re.search(r"score (cp|mate) (-?\d+)", last)
        if m:
            score = f"{m.group(1)} {m.group(2)}"
        m = re.search(r" nodes (\d+)", last)
        if m:
            nodes = int(m.group(1))
    if bm is None:
        raise RuntimeError(f"no bestmove line ({tag})")
    return {"bestmove": bm, "score": score, "nodes": nodes}


rows, fails = [], []
for i, fen in enumerate(fens):
    try:
        b = search(base_exe, fen, f"b{i:03d}_base")
        q = search(pc_exe, fen, f"b{i:03d}_pc")
    except Exception as ex:  # noqa: BLE001
        fails.append((i, str(ex)))
        print(f"FAIL {i}: {ex}", flush=True)
        continue
    board = chess.Board()
    board.set_fen(fen)
    legal = {mv.uci() for mv in board.legal_moves}
    bl = b["bestmove"] in legal
    ql = q["bestmove"] in legal
    rows.append((i, b["bestmove"], q["bestmove"], "same" if b["bestmove"] == q["bestmove"] else "DIFF",
                 b["score"], q["score"], b["nodes"], q["nodes"], bl, ql))
    if (i + 1) % 25 == 0:
        print(f"{i+1}/{len(fens)} done", flush=True)

same = sum(1 for r in rows if r[3] == "same")
diff = [r for r in rows if r[3] == "DIFF"]
nodes_same = sum(1 for r in rows if r[6] == r[7])
score_same = sum(1 for r in rows if r[4] == r[5])
illegal = [r for r in rows if not r[8] or not r[9]]

with open(out, "w") as f:
    f.write(f"depth {depth}, Threads 1, Hash 16, OwnBook false, one fresh process per search\n")
    f.write(f"positions: {len(fens)}  measured: {len(rows)}  measurement failures: {len(fails)}\n")
    f.write(f"same bestmove: {same}\n")
    f.write(f"different bestmove: {len(diff)}\n")
    f.write(f"same score: {score_same}\n")
    f.write(f"same node count: {nodes_same}\n")
    f.write(f"illegal bestmove on either build: {len(illegal)}\n\n")
    f.write("idx\tbase_bm\tpc_bm\tverdict\tbase_score\tpc_score\tbase_nodes\tpc_nodes\tbase_legal\tpc_legal\n")
    for r in rows:
        f.write("\t".join(str(x) for x in r) + "\n")
    if fails:
        f.write("\nFAILURES:\n")
        for r in fails:
            f.write(f"{r[0]}\t{r[1]}\n")
    if diff:
        f.write("\nDIFFERING MOVES:\n")
        for r in diff:
            f.write(f"idx={r[0]} base={r[1]} ({r[4]}, {r[6]} nodes)  pc={r[2]} ({r[5]}, {r[7]} nodes)\n")

print(f"positions {len(rows)}/{len(fens)}; same bestmove {same}; different {len(diff)}; "
      f"same score {score_same}; same nodes {nodes_same}; illegal {len(illegal)}; failures {len(fails)}")
if fails:
    sys.exit(f"{len(fails)} measurement failures — results incomplete")
if len(rows) != len(fens):
    sys.exit("FAIL: fewer measurements than positions")

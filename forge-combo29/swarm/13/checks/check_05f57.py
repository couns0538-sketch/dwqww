#!/usr/bin/env python3
"""Check of seat 05's S-F57: does mate-PV truncation disappear above 20,000 nodes?

Their claim, in full:
  * 28 positions that carried a mate score at depth 12 (PC r15 + PC20, Threads 1, Hash 16, fresh process);
  * `go nodes 20000`  -> 20 mate scores, **1 truncated (5.0 %)**
  * `go nodes 50000`  -> 25 mate scores, **0 truncated**
  * `go nodes 250000` -> 27 mate scores, **0 truncated**
  * the one truncated case is their S-F27 board `8/8/1p6/8/p3p3/8/2Kpk3/8` reporting `mate -7` with a
    10-ply PV where 2*|M| = 14 plies would be needed.

A mate claim of M (M<0, we are being mated) is truncated if its own PV is shorter than 2*|M| plies and does
not reach mate. For M>0 it is truncated if the PV does not deliver mate within 2M-1 plies.

Two tests here:
  A. their named board, at all three budgets, repeated — does `mate -7` appear with a short PV?
  B. the same truncation measure over a position set I build myself from G, at the three budgets, so the
     claim's RATE can be checked rather than only its example.

Every search is a FRESH PROCESS, enforced by the runtime guard (this is the discipline S-F24's correction
demands). Settings: canonical PC20 from lib/settings.py.

Usage: check_05f57.py EXE FENS OUTDIR [MAXPOS]
"""
import json
import os
import re
import subprocess
import sys

import chess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
from settings import PC20, describe  # noqa: E402
from freshguard import SearchCounter  # noqa: E402

EXE = sys.argv[1]
FENS = sys.argv[2]
OUTDIR = sys.argv[3]
MAXPOS = int(sys.argv[4]) if len(sys.argv) > 4 else 28
os.makedirs(OUTDIR, exist_ok=True)
BAD = ("unknown option", "invalid value", "error")
BUDGETS = [20000, 50000, 250000]

# the exact board seat 05 names
THEIR_BOARD = "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"
COUNTER = SearchCounter("check_05f57")


def pv_mate_ply(fen, pv):
    """Ply at which this PV delivers checkmate, or None."""
    if not pv:
        return None
    b = chess.Board(fen)
    for i, u in enumerate(pv, 1):
        try:
            m = chess.Move.from_uci(u)
        except ValueError:
            return None
        if m not in b.legal_moves:
            return None
        b.push(m)
        if b.is_checkmate():
            return i
    return None


def search(fen, nodes):
    COUNTER.new_process()
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(pred):
        while True:
            l = p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died")
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad line %r" % l)
            if pred(l):
                return l

    send("uci")
    seen = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died in uci handshake")
        l = l.rstrip("\n")
        if l.startswith("option name"):
            seen.append(l)
        if l == "uciok":
            break
    for n, v in PC20:
        if not any(o.startswith("option name %s " % n) for o in seen):
            raise SystemExit("FAIL: option %r not advertised" % n)
        send("setoption name %s value %s" % (n, v))
        send("isready")
        until(lambda s: s == "readyok")
    send("position fen " + fen)
    send("isready")
    until(lambda s: s == "readyok")
    send("go nodes %d" % nodes)

    last = None
    last_pv = None
    bm = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died during search")
        l = l.rstrip("\n")
        if l.startswith("info depth"):
            last = l
            if " pv " in l:
                last_pv = l.split(" pv ", 1)[1].split()
        if l.startswith("bestmove"):
            bm = l
            break
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    COUNTER.record_search()

    mt = re.search(r"score mate (-?\d+)", last) if last else None
    cp = re.search(r"score cp (-?\d+)", last) if last else None
    nd = re.search(r"\bnodes (\d+)", last) if last else None
    mate = int(mt.group(1)) if mt else None
    return {"mate": mate, "cp": int(cp.group(1)) if cp else None,
            "nodes": int(nd.group(1)) if nd else None,
            "pv": last_pv or [],
            "bestmove": (bm.split()[1] if bm and len(bm.split()) > 1 else None)}


def classify(fen, r):
    """Is this mate claim truncated? Returns (status, detail)."""
    m = r["mate"]
    if m is None:
        return "no_mate_claim", None
    d = pv_mate_ply(fen, r["pv"])
    if m > 0:
        need = 2 * m - 1
        ok = d is not None and d <= need
        return ("delivered" if ok else "TRUNCATED"), {"need": need, "pv_mate_ply": d}
    need = 2 * abs(m)
    # for a negative score the PV should run to the mate AGAINST us
    ok = d is not None and d <= need
    return ("delivered" if ok else "TRUNCATED"), {"need": need, "pv_mate_ply": d}


def main():
    # ---- A: their named board ----
    print("A. seat 05's named board:", THEIR_BOARD)
    print("   %-9s %-8s %-6s %-8s %-9s %s" % ("nodes", "mate", "pv_len", "pv_mate", "status", "pv"))
    a_rows = []
    for nodes in BUDGETS:
        for rep in range(2):
            r = search(THEIR_BOARD, nodes)
            st, detail = classify(THEIR_BOARD, r)
            a_rows.append({"nodes": nodes, "rep": rep, "status": st, **r, "detail": detail})
            print("   %-9d %-8s %-6d %-8s %-9s %s"
                  % (nodes, r["mate"], len(r["pv"]),
                     (detail or {}).get("pv_mate_ply", "-"), st, " ".join(r["pv"])[:44]))

    # ---- B: a set of my own, to check the RATE not just the example ----
    fens = [l.strip() for l in open(FENS) if l.strip()][:MAXPOS]
    print()
    print("B. rate over %d G positions (my own set, not theirs)" % len(fens))
    b_rows = []
    for nodes in BUDGETS:
        claims = trunc = 0
        for i, fen in enumerate(fens):
            r = search(fen, nodes)
            st, detail = classify(fen, r)
            rec = {"nodes": nodes, "position": i, "fen": fen, "status": st, **r, "detail": detail}
            b_rows.append(rec)
            if r["mate"] is not None:
                claims += 1
                if st == "TRUNCATED":
                    trunc += 1
                    print("   TRUNCATED nodes %-7d %s claim %d pv_len %d need %s"
                          % (nodes, fen[:40], r["mate"], len(r["pv"]), detail.get("need")))
        print("   nodes %-7d : %d mate claims, %d truncated" % (nodes, claims, trunc))

    COUNTER.assert_single_use()      # structural: one search per process
    summary = {
        "exe": os.path.abspath(EXE), "settings": describe(PC20),
        "their_board": THEIR_BOARD,
        "their_board_results": a_rows,
        "my_set_size": len(fens),
        "searches": len(COUNTER.searches_per_process()),
    }
    for nodes in BUDGETS:
        sel = [r for r in b_rows if r["nodes"] == nodes]
        summary["my_set_nodes_%d" % nodes] = {
            "mate_claims": sum(1 for r in sel if r["mate"] is not None),
            "truncated": sum(1 for r in sel if r["status"] == "TRUNCATED"),
        }
    json.dump({"summary": summary, "their_board": a_rows, "my_set": b_rows},
              open(os.path.join(OUTDIR, "check_05f57.json"), "w"), indent=1)
    print()
    for k, v in summary.items():
        if k in ("their_board_results", "their_board"):
            continue
        print("%-26s %s" % (k, v))


main()

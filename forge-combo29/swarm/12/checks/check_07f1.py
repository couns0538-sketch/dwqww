#!/usr/bin/env python3
"""check_07f1.py EXE — seat 12's independent check of seat 07's 07-F1.

Claim: `go depth N searchmoves <move that is not legal here>` on a board that HAS legal moves
answers a FABRICATED per-depth report — one `info depth D ... score cp 0 nodes 0` line for every
depth up to the limit, then `bestmove 0000`. The engine has already diagnosed the cause and says so
in an `info string`, but emits scores anyway.

What makes the score fabricated: the position was never searched (nodes 0) yet a score `cp 0` is
reported for every depth, as if a draw had been found. A drawn score is a claim about the position;
a search that did no work cannot make it.

My own harness, my own builds. Each case: fresh process, Threads 1, Hash 16, MultiPV 1,
OwnBook false, read to `bestmove` before quitting.

Controls, because "0 nodes" must not be read as "no search" without evidence:
  C1  a LEGAL searchmoves must search normally (real depth lines, real node counts) — proves the
      harness can see a search when there is one;
  C2  an UNRESTRICTED search of the same board must search (the ground truth for what the position
      is worth), so the fabricated cp 0 can be compared with the real score;
  C3  an `info string` must be present, i.e. the engine knows and says why — the defect is that it
      reports a score anyway, not that it is silent.
"""
import json
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

import chess

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
KIWI = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def ask(exe, fen, go, bound=180.0):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()
    out = []
    threading.Thread(target=lambda: ([q.put(l.rstrip("\n")) for l in p.stdout], q.put(None)),
                     daemon=True).start()

    def send(t):
        p.stdin.write(t + "\n")
        p.stdin.flush()

    def wait(pred, limit):
        end = time.monotonic() + limit
        while time.monotonic() < end:
            try:
                ln = q.get(timeout=0.2)
            except queue.Empty:
                if p.poll() is not None:
                    return None
                continue
            if ln is None:
                return None
            out.append(ln)
            if pred(ln):
                return ln
        return None

    try:
        send("uci")
        wait(lambda l: l == "uciok", 30)
        for name, value in (("Hash", 16), ("MultiPV", 1), ("Threads", 1), ("OwnBook", "false")):
            send(f"setoption name {name} value {value}")
            send("isready")
            wait(lambda l: l == "readyok", 30)
        send(f"position fen {fen}")
        send("isready")
        wait(lambda l: l == "readyok", 30)
        send(go)
        wait(lambda l: l.startswith("bestmove"), bound)
        send("quit")
    except (BrokenPipeError, OSError, ValueError):
        pass
    try:
        p.stdin.close()
    except (OSError, ValueError):
        pass
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()

    infos = [l for l in out if l.startswith("info depth")]
    notes = [l for l in out if l.startswith("info string")]
    bms = [l for l in out if l.startswith("bestmove")]
    depths, nodes, scores = [], [], []
    for l in infos:
        m = re.match(r"^info depth (\d+)", l)
        if m:
            depths.append(int(m.group(1)))
        n = re.search(r" nodes (\d+)", l)
        if n:
            nodes.append(int(n.group(1)))
        s = re.search(r"score (cp|mate) (-?\d+)", l)
        if s:
            scores.append(f"{s.group(1)} {s.group(2)}")
    return {"go": go, "fen": fen,
            "bestmove": bms[-1].split()[1] if bms else None,
            "depth_lines": len(infos), "depths": depths, "nodes": nodes,
            "scores": scores, "notes": notes,
            "answered": bool(bms)}


def main():
    exe, outfile = sys.argv[1], sys.argv[2]
    print(f"exe {exe}   Threads 1, Hash 16, MultiPV 1, OwnBook false\n")
    rows = []

    print("=== the claim: a searchmoves restriction matching nothing")
    for fen_name, fen, illegal in (("startpos", START, "e2e5"), ("kiwipete", KIWI, "e2e5")):
        for depth in (4, 6):
            go = f"go depth {depth} searchmoves {illegal}"
            r = ask(exe, fen, go)
            all_zero = bool(r["nodes"]) and all(n == 0 for n in r["nodes"])
            all_zero_score = bool(r["scores"]) and all(s == "cp 0" for s in r["scores"])
            fabricated = (r["depth_lines"] > 0 and all_zero and all_zero_score
                          and r["bestmove"] == "0000")
            r.update({"case": f"{fen_name}_depth{depth}", "fabricated": fabricated,
                      "all_zero_nodes": all_zero, "all_zero_score": all_zero_score})
            rows.append(r)
            print(f"  {fen_name:9} {go:44} -> {r['bestmove']:5} "
                  f"{r['depth_lines']:2} depth lines, nodes {r['nodes'][:3]}"
                  f"{'...' if len(r['nodes']) > 3 else ''}, "
                  f"scores {sorted(set(r['scores']))}, "
                  f"{'FABRICATED' if fabricated else 'not fabricated'}")
            if r["notes"]:
                print(f"      note: {r['notes'][0]}")

    print("\n=== CONTROLS")
    c1 = ask(exe, START, "go depth 6 searchmoves e2e4")
    c1_ok = c1["bestmove"] == "e2e4" and any(n > 0 for n in c1["nodes"])
    print(f"  C1 legal searchmoves e2e4     -> {c1['bestmove']}, {c1['depth_lines']} depth lines, "
          f"max nodes {max(c1['nodes']) if c1['nodes'] else 0}  [{'searched' if c1_ok else 'NO SEARCH'}]")

    c2 = ask(exe, START, "go depth 6")
    c2_ok = any(n > 0 for n in c2["nodes"])
    print(f"  C2 unrestricted go depth 6    -> {c2['bestmove']}, {c2['depth_lines']} depth lines, "
          f"max nodes {max(c2['nodes']) if c2['nodes'] else 0}, last score "
          f"{c2['scores'][-1] if c2['scores'] else None}  "
          f"[{'searched' if c2_ok else 'NO SEARCH'}]")

    bad = [r for r in rows if r["fabricated"]]
    print(f"\n=== verdict: {len(bad)}/{len(rows)} restricted-empty cases are FABRICATED")
    print(f"  controls working: C1 {'yes' if c1_ok else 'NO'}, C2 {'yes' if c2_ok else 'NO'}")
    if bad and c1_ok and c2_ok:
        print("  07-F1 CONFIRMED: the engine reports a drawn score at every depth for a position it")
        print("  never searched, while its own harness can see a real search when one happens.")
    elif not bad:
        print("  07-F1 NOT REPRODUCED on this build.")
    else:
        print("  controls failed, so the result is not interpretable.")

    Path(outfile).write_text(json.dumps(
        {"exe": exe, "cases": rows,
         "controls": {"legal_searchmoves": c1, "unrestricted": c2,
                      "c1_searched": c1_ok, "c2_searched": c2_ok},
         "fabricated_count": len(bad)}, indent=1) + "\n")
    print(f"\nraw -> {outfile}")
    return 0 if (bad and c1_ok and c2_ok) else 0


if __name__ == "__main__":
    sys.exit(main())

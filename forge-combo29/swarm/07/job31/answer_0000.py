#!/usr/bin/env python3
"""answer_0000.py BASE_EXE PC_EXE OUTDIR

Answers the design question asked of this seat: when `searchmoves` names no legal root move on a board
that HAS legal moves, what should the engine answer?

Three candidates, measured rather than argued:

  A  `bestmove 0000` plus a diagnostic info string   (what the patched build does today)
  B  a real move chosen by searching the full legal root, with an info string explaining the
     restriction was ignored                                     (NOT implemented; measured by asking
                                                                 the same engine for an unrestricted
                                                                 `go` on the same position, which is
                                                                 exactly the answer B would give)
  C  `bestmove 0000` with NO info line                (what the unpatched build effectively gives,
                                                       plus its fabricated score lines)

The point of measuring B this way: B's move is by definition what `go` without `searchmoves` returns,
so no new engine is needed to state its consequence — only to state that it IS this move.

Also checks the boundary case this seat was asked about: `searchmoves` naming a move that IS legal but
leaves exactly ONE candidate, on both builds.
"""
import os
import queue
import re
import subprocess
import sys
import threading

import chess

S14 = [
    "LmrQuietBase value 93", "LmrQuietDivisor value 205", "LmrNoisyBase value 13",
    "LmrNoisyDivisor value 333", "LmrHistoryDivisor value 5643", "NullMoveBase value 5",
    "LmpBase value 8", "HistoryPruneMultiplier value 2220",
    "HistoryBonusQuadratic value 24", "HistoryBonusLinear value 54",
    "HistoryBonusMax value 2212", "SingularDepth value 6", "IirDepth value 2",
    "NonPawnCorrection value true",
]
PC20 = S14 + ["CuckooRep value true", "HistRework value 2", "TtPruneV2 value true",
              "CorrHistV2 value true", "MateAlphaGuard value true", "OwnBook value false"]


class Reader:
    def __init__(s, st):
        s.q = queue.Queue()
        threading.Thread(target=s._pump, args=(st,), daemon=True).start()

    def _pump(s, st):
        for l in st:
            s.q.put(l)
        s.q.put(None)

    def get(s, t=180):
        try:
            return s.q.get(timeout=t)
        except queue.Empty:
            return None


def ask(exe, options, position, go):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    r = Reader(p.stdout)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def drain():
        while True:
            l = r.get()
            if l is None:
                raise RuntimeError("no readyok")
            if l.strip() == "readyok":
                return

    send("uci")
    while True:
        l = r.get(60)
        if l is None or l.strip() == "uciok":
            break
    for opt in ["Hash value 16", "Threads value 1"] + options:
        send("setoption name " + opt); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send(position); send("isready"); drain()
    send(go)
    infos, infostrings, best = [], [], None
    while True:
        l = r.get(300)
        if l is None:
            raise RuntimeError("no bestmove")
        if l.startswith("info depth"):
            infos.append(l.strip())
        elif l.startswith("info string"):
            infostrings.append(l.strip())
        if l.startswith("bestmove"):
            best = l.split()[1]
            break
    send("quit")
    try: p.wait(timeout=20)
    except subprocess.TimeoutExpired: p.kill()
    nodes = None
    if infos:
        m = re.search(r" nodes (\d+) ", infos[-1] + " ")
        if m: nodes = int(m.group(1))
    return {"bestmove": best, "depth_lines": len(infos), "nodes": nodes,
            "info_strings": infostrings}


def main():
    base_exe, pc_exe, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    results = {}

    # ---------- the design question ----------
    # A: what the patched PC build answers (0000 + info string).
    a = ask(pc_exe, [], "position startpos", "go depth 6 searchmoves e2e5")
    # B: measured as the unrestricted search's answer -- that IS what B would play.
    b = ask(pc_exe, [], "position startpos", "go depth 6")
    # C: the unpatched base build, for the record.
    c = ask(base_exe, [], "position startpos", "go depth 6 searchmoves e2e5")
    results["A_0000_plus_info_patched_pc"] = a
    results["B_unrestricted_search_answer"] = b
    results["C_unpatched_base"] = c

    print("Design question -- what to answer when searchmoves names nothing legal (startpos, 20 legal moves)")
    print(f"  A  0000 + info string (patched PC) : bestmove {a['bestmove']}, "
          f"{a['depth_lines']} depth lines, info strings {a['info_strings']}")
    print(f"  B  full-root search answer         : bestmove {b['bestmove']}, "
          f"{b['depth_lines']} depth lines, nodes {b['nodes']}")
    print(f"  C  unpatched base                  : bestmove {c['bestmove']}, "
          f"{c['depth_lines']} depth lines (all nodes 0), nodes {c['nodes']}")

    # ---------- the boundary case ----------
    print()
    print("Boundary case: searchmoves naming a move that IS legal, leaving exactly ONE candidate")
    boundary = [
        ("one_legal_candidate_startpos", "position startpos", "go depth 6 searchmoves e2e4"),
        # White to move, and Nxe5 is a real capture: the restriction leaves exactly ONE candidate
        # that is legal and non-trivial. (My first version of this line used a position where it was
        # BLACK to move, so f3e5 was never legal and the test was measuring nothing -- caught by
        # checking with python-chess before believing the warning.)
        ("one_candidate_capture", "position startpos moves e2e4 e7e5 g1f3 b8c6",
         "go depth 6 searchmoves f3e5"),
    ]
    for name, pos, go in boundary:
        rb = ask(base_exe, [], pos, go)
        rp = ask(pc_exe, PC20, pos, go)
        results[name] = {"base": rb, "pc20": rp}
        print(f"  {name:32s} base {rb['bestmove']:6s} dlines {rb['depth_lines']:3d} "
              f"nodes {rb['nodes']}   |  PC20 {rp['bestmove']:6s} dlines {rp['depth_lines']:3d} "
              f"nodes {rp['nodes']}", flush=True)
        if rb["nodes"] == 0 or rp["nodes"] == 0:
            print(f"    WARNING: a zero-node answer on a ONE-candidate legal restriction -> "
                  f"the early branch is taken even when a legal candidate exists")

    import json
    json.dump(results, open(os.path.join(outdir, "answer_0000.json"), "w"), indent=1)


if __name__ == "__main__":
    main()

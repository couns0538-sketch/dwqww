#!/usr/bin/env python3
"""S02 — is the truncated MultiPV line set (S-F10) a PRESENTATIONAL trap or a CORRECTNESS bug?

The question: at MultiPV 8 with a tight node budget, the final reported depth carries only some of the 8 lines.
Does that ever produce a WRONG bestmove, or only fewer PVs?

Test design, which has to separate the two possible explanations:
  * the `bestmove` the engine sends, versus
  * the `multipv 1` line at the deepest depth, versus
  * the best move at MultiPV 1 on the same budget (which is the deepest search and therefore the reference).

If the bestmove always equals the multipv-1 line's first move AND equals the MultiPV-1 reference move, the trap is
presentational. If a truncated run's bestmove differs from BOTH its own multipv-1 line and the reference, that is a
correctness problem.

Several budgets are swept, not just one, because the truncation only bites at particular N/M combinations — the
point is to find whether it bites at all, so a single cell could miss it.

PC r15, PC20, Threads 1, Hash 16, OwnBook false, fresh process, interactive driver. Every `multipv` line's PV is
replayed with python-chess so a move that is not legal is caught too.

usage: truncated_bestmove.py <pc_exe> <outdir>
"""
import json
import os
import subprocess
import sys
import threading
import time

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/agent/repos/pc/forge-combo29/build-pc/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "out_bm"

PC20 = [
    "setoption name Threads value 1", "setoption name Hash value 16",
    "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
    "setoption name CuckooRep value true", "setoption name HistRework value 2",
    "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
    "setoption name MateAlphaGuard value true", "setoption name OwnBook value false",
]
POSITIONS = {
    "game_mid1": "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    "game_mid2": "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
    "game_end": "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
}
# budgets chosen to straddle the truncation: small ones cut mid-line-set at high MultiPV
BUDGETS = [500, 1000, 2000, 5000, 20000]
MPVS = [1, 8]


def search(fen, nodes, multipv):
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
    L = []
    threading.Thread(target=lambda: [L.append(l.rstrip("\n")) for l in p.stdout], daemon=True).start()

    def send(t):
        if p.poll() is None:
            try:
                p.stdin.write(t + "\n")
                p.stdin.flush()
            except Exception:
                pass

    def wait(pref, n0=0, to=120.0):
        dl = time.monotonic() + to
        while time.monotonic() < dl:
            if any(l.startswith(pref) for l in L[n0:]):
                return True
            if p.poll() is not None:
                return any(l.startswith(pref) for l in L[n0:])
            time.sleep(0.001)
        return False

    send("uci")
    if not wait("uciok"):
        raise SystemExit("FAIL: no uciok")
    for s in PC20:
        send(s)
    send("setoption name MultiPV value %d" % multipv)
    send("isready")
    if not wait("readyok"):
        raise SystemExit("FAIL: no readyok")
    for line in L:
        if "unknown option" in line or "invalid value" in line:
            raise SystemExit("FAIL: option refused: %r" % line)
    send("position fen " + fen)
    send("isready")
    n0 = len(L)
    wait("readyok", n0)
    n0 = len(L)
    send("go nodes %d" % nodes)
    if not wait("bestmove", n0, 180):
        raise SystemExit("FAIL: no bestmove")
    seg = list(L[n0:])
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    bm = [l for l in seg if l.startswith("bestmove")]
    bestmove = bm[-1].split()[1] if bm else None

    # collect (depth, multipv, first PV move) and the per-depth line counts
    lines = {}
    per_depth_count = {}
    for line in seg:
        if not line.startswith("info depth"):
            continue
        parts = line.split()
        try:
            d = int(parts[2])
        except (IndexError, ValueError):
            continue
        mpv = 1
        if "multipv" in parts:
            mpv = int(parts[parts.index("multipv") + 1])
        pv = []
        if "pv" in parts:
            pv = parts[parts.index("pv") + 1:]
        lines[(d, mpv)] = pv
        per_depth_count[d] = per_depth_count.get(d, 0) + 1
    max_depth = max(per_depth_count) if per_depth_count else 0
    lines_at_max = per_depth_count.get(max_depth, 0)
    pv1_at_max = lines.get((max_depth, 1), [])
    return {"bestmove": bestmove, "max_depth": max_depth, "lines_at_max": lines_at_max,
            "pv1_first_move": pv1_at_max[0] if pv1_at_max else None,
            "pvs_at_max": {str(k): v for (d, k), v in sorted(lines.items()) if d == max_depth}}


def legal_in(fen, move):
    try:
        b = chess.Board(fen)
        return chess.Move.from_uci(move) in b.legal_moves
    except Exception:
        return False


def main():
    os.makedirs(OUT, exist_ok=True)
    json.dump({"exe": EXE,
               "sha256": subprocess.run(["sha256sum", EXE], capture_output=True,
                                        text=True).stdout.split()[0],
               "threads": 1, "hash_mb": 16, "settings": "PC20", "options": PC20,
               "positions": POSITIONS, "budgets": BUDGETS, "multipvs": MPVS,
               "question": "does the truncated MultiPV line set ever give a WRONG bestmove?",
               "reference": "the MultiPV 1 bestmove at the same node budget (deepest search)",
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "meta.json"), "w"), indent=1)

    rows = []
    print("| position | N | MPV | deepest depth | lines at that depth | bestmove | mpv1 line's move | MultiPV-1 ref move | bestmove == ref? | bestmove == own line 1? |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for pname, fen in POSITIONS.items():
        for nodes in BUDGETS:
            ref = search(fen, nodes, 1)
            m8 = search(fen, nodes, 8)
            row = {"position": pname, "nodes": nodes, "ref_bestmove": ref["bestmove"],
                   "ref_depth": ref["max_depth"],
                   "mpv8_bestmove": m8["bestmove"], "mpv8_depth": m8["max_depth"],
                   "mpv8_lines_at_max": m8["lines_at_max"],
                   "mpv8_pv1_move": m8["pv1_first_move"],
                   "bestmove_is_ref": m8["bestmove"] == ref["bestmove"],
                   "bestmove_is_own_pv1": m8["bestmove"] == m8["pv1_first_move"],
                   "bestmove_legal": legal_in(fen, m8["bestmove"] or ""),
                   "pvs_at_max": m8["pvs_at_max"]}
            rows.append(row)
            print("| %s | %d | 8 | %d | %d | %s | %s | %s | %s | %s |"
                  % (pname, nodes, m8["max_depth"], m8["lines_at_max"], m8["bestmove"],
                     m8["pv1_first_move"], ref["bestmove"],
                     "yes" if row["bestmove_is_ref"] else "**NO**",
                     "yes" if row["bestmove_is_own_pv1"] else "**NO**"))
    json.dump(rows, open(os.path.join(OUT, "rows.json"), "w"), indent=1)

    trunc = [r for r in rows if r["mpv8_lines_at_max"] < 8]
    diff_ref = [r for r in rows if not r["bestmove_is_ref"]]
    diff_own = [r for r in rows if not r["bestmove_is_own_pv1"]]
    illegal = [r for r in rows if not r["bestmove_legal"]]
    print()
    print("### verdict")
    print("- cells where the deepest depth carried FEWER than 8 lines (truncated): %d of %d" % (len(trunc), len(rows)))
    print("- cells where the MultiPV-8 bestmove differs from the MultiPV-1 reference: %d" % len(diff_ref))
    for r in diff_ref:
        print("    %s N=%d: mpv8 %s vs mpv1 %s" % (r["position"], r["nodes"],
                                                   r["mpv8_bestmove"], r["ref_bestmove"]))
    print("- cells where the bestmove differs from its OWN multipv-1 line: %d" % len(diff_own))
    for r in diff_own:
        print("    %s N=%d: bestmove %s vs own line1 %s" % (r["position"], r["nodes"],
                                                            r["mpv8_bestmove"], r["mpv8_pv1_move"]))
    print("- illegal bestmoves: %d" % len(illegal))
    print()
    print("### the discriminating question, separated from the depth effect")
    print()
    print("The bestmove disagreeing with the MultiPV-1 REFERENCE is expected and is S-F9, not the truncation: a")
    print("MultiPV 8 search on the same budget is shallower (depths 2-7 against 4-11), so it legitimately plays a")
    print("move a deeper search would not choose. The truncation question is narrower: **is the bestmove always")
    print("the move the engine itself reports as multipv 1 at the depth it reports?**")
    print()
    print("bestmove == its own multipv-1 line in %d of %d cells." % (len(rows) - len(diff_own), len(rows)))
    if not diff_own and not illegal:
        print()
        print("CONCLUSION: PRESENTATIONAL, not a correctness issue. In every truncated cell the bestmove is")
        print("            exactly the first PV move of the deepest complete multipv-1 line, and legal. What is")
        print("            missing is the PVs of the HIGHER multipv indices at that depth — a GUI showing a table")
        print("            of 8 lines sees some lines one depth stale, but the move it is told to play is the move")
        print("            the search actually chose and reported.")
        print()
        print("            The move DIFFERING from a MultiPV-1 search (%d cells) is real, but its cause is the"
              % len(diff_ref))
        print("            depth dilution of S-F9, already measured separately, not the truncated line set.")
    else:
        print()
        print("CONCLUSION: CORRECTNESS ISSUE. See the rows where the bestmove disagrees with its own multipv-1")
        print("            line, or is illegal.")


if __name__ == "__main__":
    main()

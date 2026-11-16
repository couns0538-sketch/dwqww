#!/usr/bin/env python3
"""settle_155.py PC_EXE OUTDIR

Seat 03 (S-F16/S-F17) and seat 02 (S-C7/S-C8) disagree about position
`1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183`:

  seat 03: the PC build answers `c6c7`, which it scores `mate -11`, while `c6d6` scores `cp -1142`,
           so the engine "plays a move it has itself scored as a forced loss". They call it a defect.
  seat 02: the same move `c6c7` at depth 20 replays to a VERIFIED CHECKMATE in exactly 20 plies, so
           the choice is correct and `mate -11` is a bound, not a lie.

These cannot both be the whole story. This settles it with an independent referee — python-chess —
and with the engine's OWN principal variation, which is the part neither seat's summary states cleanly:

  1. Play the engine's PV for `c6c7` on a python-chess board. Does it end in checkmate?
  2. Count the plies to that mate. Is it <= the mate distance the engine reported?
  3. Score BOTH white's legal moves at the same depth with `searchmoves`, and check which is better
     by python-chess play-out if the scores disagree with the PV.

Everything is measured; nothing is taken from either seat's summary.
"""
import json
import os
import queue
import re
import subprocess
import sys
import threading

import chess

FEN = "1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183"
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


class R:
    def __init__(s, st):
        s.q = queue.Queue()
        threading.Thread(target=s._pump, args=(st,), daemon=True).start()

    def _pump(s, st):
        for l in st:
            s.q.put(l)
        s.q.put(None)

    def get(s, t=1800):
        try:
            return s.q.get(timeout=t)
        except queue.Empty:
            return None


def search(exe, fen, go, options):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    r = R(p.stdout)

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
    for o in ["Hash value 16", "Threads value 1"] + options:
        send("setoption name " + o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen " + fen); send("isready"); drain()
    send(go)
    last_pv, last_score, best, nodes = None, None, None, None
    while True:
        l = r.get(1800)
        if l is None:
            break
        if l.startswith("info depth") and " pv " in l:
            m = re.search(r"score (cp|mate) (-?\d+)", l)
            if m:
                last_score = [m.group(1), int(m.group(2))]
            m = re.search(r"nodes (\d+)", l)
            if m:
                nodes = int(m.group(1))
            last_pv = l.split(" pv ", 1)[1].split()
        if l.startswith("bestmove"):
            best = l.split()[1]
            break
    send("quit")
    try: p.wait(timeout=60)
    except subprocess.TimeoutExpired: p.kill()
    return {"score": last_score, "pv": last_pv, "best": best, "nodes": nodes}


def replay(fen, pv):
    """Play the PV on a python-chess board. Returns (plies, ended_in_mate, final_fen, legal_all)."""
    b = chess.Board(fen)
    n = 0
    for uci in pv:
        try:
            mv = chess.Move.from_uci(uci)
        except ValueError:
            return n, False, b.fen(), False
        if mv not in b.legal_moves:
            return n, False, b.fen(), False
        b.push(mv)
        n += 1
    return n, b.is_checkmate(), b.fen(), True


def main():
    pc_exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    print(f"position: {FEN}\nPC build under PC20, Threads 1, Hash 16\n")

    rows = {}
    # 1. what the engine plays and what it claims
    free = search(pc_exe, FEN, "go depth 20", PC20)
    print(f"free choice  depth 20: bestmove {free['best']}  score {free['score']}  nodes {free['nodes']}")
    n, mate, ff, ok = replay(FEN, free["pv"] or [])
    print(f"  PV ({len(free['pv'] or [])} moves, all legal={ok}): {' '.join((free['pv'] or [])[:12])}...")
    print(f"  PV replayed {n} plies -> checkmate={mate}")
    rows["free_depth20"] = {**free, "pv_plies": n, "pv_ends_in_mate": mate, "pv_legal": ok}

    # 2. each legal white move scored at the same depth
    b = chess.Board(FEN)
    legal = [m.uci() for m in b.legal_moves]
    print(f"\nwhite's legal moves: {len(legal)}")
    per_move = {}
    for uci in legal:
        r = search(pc_exe, FEN, f"go depth 20 searchmoves {uci}", PC20)
        nn, mm, _, okk = replay(FEN, r["pv"] or [])
        per_move[uci] = {**r, "pv_plies": nn, "pv_ends_in_mate": mm, "pv_legal": okk}
        mate_note = f" PV->mate in {nn} plies" if mm else ""
        print(f"  {uci}: score {r['score']} nodes {r['nodes']}{mate_note}", flush=True)
    rows["per_move_depth20"] = per_move

    # 3. python-chess play-out as an independent referee: both sides play the engine's own
    #    depth-12 answer; count plies until the game ends.
    def playout(first_move, depth=12, max_plies=80):
        bd = chess.Board(FEN)
        bd.push(chess.Move.from_uci(first_move))
        plies = 1
        while plies < max_plies and not bd.is_game_over():
            r = search(pc_exe, bd.fen(), f"go depth {depth}", PC20)
            mv = r["best"]
            try:
                m = chess.Move.from_uci(mv)
            except ValueError:
                break
            if m not in bd.legal_moves:
                break
            bd.push(m)
            plies += 1
        return {"plies": plies, "over": bd.is_game_over(),
                "result": bd.result() if bd.is_game_over() else "unfinished",
                "mate": bd.is_checkmate(), "fen": bd.fen()}

    print("\nplay-out referee (both sides play the engine's own depth-12 answer):")
    for uci in legal:
        po = playout(uci)
        rows.setdefault("playout", {})[uci] = po
        print(f"  {uci}: {po['plies']} plies, over={po['over']}, result={po['result']}, "
              f"mate={po['mate']}", flush=True)

    json.dump(rows, open(os.path.join(outdir, "settle_155.json"), "w"), indent=1)

    print("\n=== VERDICT MATERIAL ===")
    free_score = free["score"]
    better = None
    for uci, r in per_move.items():
        if r["score"] and free_score:
            k1, v1 = r["score"]; k2, v2 = free_score
            print(f"  {uci:6s} score {r['score']}  PV mate={r['pv_ends_in_mate']} in {r['pv_plies']} plies")
    # the decisive question: does the engine's own PV end in mate?
    print()
    if mate:
        print(f"  The engine's PV for its OWN chosen move ends in checkmate after {n} plies.")
        print(f"  Its reported score is {free_score}. A mate score's distance is 2N-1 plies for mate N.")
        print("  => the score and the PV are CONSISTENT if the PV mate is at the reported distance;")
        print("     the position is a forced mate, and 'plays a move it scored as a loss' is only true")
        print("     if the mate is AGAINST white. That is what the sign has to be read for.")
    else:
        print(f"  The engine's PV does NOT end in checkmate ({n} plies).")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""settle_pos29.py -- ONE contained question: at position 29 (my 30-F58), is f3g2 or f3g3 better?

The two arms disagreed by 203 cp at depth 10 (S14 f3g2 +1744 vs PC20 f3g3 +1541). Both arms see a
large White advantage. To settle WHICH move is better I do three independent things, all at Threads 1:

  A. Score EACH candidate alone, to increasing depth, on BOTH option sets. Scoring a move in
     isolation (root restricted to that move) removes the search's freedom to pick, so the two moves
     can be compared directly. Deeper depth is the reference.
  B. Ask for the unrestricted best move at much greater depth (depth 16/18/20) on both option sets —
     if the arms converge on one move as depth grows, that is the better move.
  C. Verify any mate claim with python-chess: if a `mate N` appears, check the PV really mates.

Nothing is claimed unless A and B agree.

usage: settle_pos29.py OUTDIR
"""
import json
import os
import subprocess
import sys
import threading
import time

import chess

EXE = "/home/ubuntu/b/pc/forge"
ENV = {k: v for k, v in os.environ.items()
       if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20EXTRA = [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
             ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
FEN = "rnb3nr/3kb2p/1p2p3/p1p2pP1/1PP1p1P1/P3PQ1R/1B1P1P2/RN2KB2 w Q - 0 18"
CANDIDATES = ["f3g2", "f3g3"]


def search(settings, go, timeout=600.0):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1, env=ENV)
    out = []
    lock = threading.Lock()

    def pump():
        try:
            for l in p.stdout:
                with lock:
                    out.append(l.rstrip("\n"))
        except Exception:
            pass

    threading.Thread(target=pump, daemon=True).start()

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def ready(t=180.0):
        with lock:
            k = len(out)
        send("isready")
        t0 = time.monotonic()
        while time.monotonic() - t0 < t:
            with lock:
                if any(x.strip() == "readyok" for x in out[k:]):
                    return
            time.sleep(0.003)

    send("uci")
    time.sleep(0.1)
    send("setoption name Threads value 1")
    ready()
    send("setoption name Hash value 64")
    ready()
    for n, v in settings:
        send("setoption name %s value %s" % (n, v))
        ready()
    # ARM SANITY (added after 30-C57): a caller that passes the SIX extra switches alone is NOT
    # testing PC20 -- PC20 is S14 + those six. Fail loudly instead of silently measuring defaults.
    _names = {n for n, _ in settings}
    if _names and _names <= {n for n, _ in PC20EXTRA}:
        raise SystemExit(
            "REFUSING: this option list is only the PC20 extras on top of DEFAULT options. "
            "The PC20 arm must be S14 + PC20EXTRA (20 options). See 30-C57.")
    send("ucinewgame")
    ready()
    send("position fen " + FEN)
    ready()
    with lock:
        mark = len(out)
    t0 = time.monotonic()
    send(go)
    while time.monotonic() - t0 < timeout:
        with lock:
            if any(x.startswith("bestmove") for x in out[mark:]):
                break
        time.sleep(0.004)
    el = time.monotonic() - t0
    with lock:
        blk = out[mark:]
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    bm = score = pv = None
    depth = nodes = None
    for l in blk:
        if l.startswith("bestmove"):
            parts = l.split()
            bm = parts[1] if len(parts) > 1 else None
        if l.startswith("info depth") and " pv" in l:
            t = l.split()
            if "score" in t:
                i = t.index("score")
                score = " ".join(t[i + 1:i + 3])
            if "depth" in t:
                depth = int(t[t.index("depth") + 1])
            if "nodes" in t:
                nodes = int(t[t.index("nodes") + 1])
            pv = t[t.index("pv") + 1:] if "pv" in t else None
    return {"bestmove": bm, "score": score, "pv": pv, "depth": depth, "nodes": nodes,
            "seconds": round(el, 1)}


def pv_mates(pv):
    """Does this PV end in checkmate, and in how many plies?"""
    if not pv:
        return None
    b = chess.Board(FEN)
    for i, u in enumerate(pv):
        try:
            m = chess.Move.from_uci(u)
        except ValueError:
            return None
        if m not in b.legal_moves:
            return None
        b.push(m)
    return {"ends_in_mate": b.is_checkmate(), "plies": len(pv)}


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    report = {"fen": FEN, "A_isolated": {}, "B_unrestricted": {}}
    print("A. EACH candidate scored ALONE (root restricted to that move), depth 12 -> 18")
    print("%-8s %-6s %-10s %-9s %s" % ("move", "depth", "score", "nodes", "PV mates?"))
    for mv in CANDIDATES:
        for depth in (12, 14, 16, 18):
            for label, st in (("S14", S14), ("PC20", PC20EXTRA)):
                r = search(st, "go depth %d searchmoves %s" % (depth, mv))
                key = "%s/%s/d%d/%s" % (mv, label, depth, r["bestmove"])
                report["A_isolated"][key] = dict(r, mate_check=pv_mates(r["pv"]))
                print("%-8s %-6s %-10s %-9s %s   [%s]" % (
                    mv, depth, r["score"], r["nodes"],
                    pv_mates(r["pv"]), label))
    print()
    print("B. UNRESTRICTED best move at greater depth")
    print("%-6s %-8s %-10s %-9s" % ("depth", "arm", "bestmove", "score"))
    for depth in (12, 14, 16, 18, 20):
        for label, st in (("S14", S14), ("PC20", PC20EXTRA)):
            r = search(st, "go depth %d" % depth)
            report["B_unrestricted"]["d%d/%s" % (depth, label)] = dict(r, mate_check=pv_mates(r["pv"]))
            print("%-6d %-8s %-10s %-9s" % (depth, label, r["bestmove"], r["score"]))
    with open(os.path.join(outdir, "settle_pos29.json"), "w") as f:
        json.dump(report, f, indent=1)


if __name__ == "__main__":
    main()

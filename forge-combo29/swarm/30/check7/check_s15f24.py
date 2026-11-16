#!/usr/bin/env python3
"""check_s15f24.py -- MY OWN check of seat 15's 15-F24/F25: does the PC build's
FORGE_FIX_ROOT_DRAWN conflate two repairs (halfmove-100 mate vs thrice-repeated root)?

Claim under test, on the SHIPPED PC r15 build (flag ON), Threads 1, PC20:
  A. a mate-in-1 at halfmove 100 IS found (mate 1, ~144 nodes)          <- the halfmove repair
  B. a THRICE-repeated root is SEARCHED (cp 23, ~13,424 nodes) instead of
     being declared drawn (cp 0, 0 nodes)                              <- the repetition regression

My harness builds the thrice-repeated root the honest way: `position startpos moves ...` with a
threefold cycle, so the engine's own history (not a FEN counter) is what makes it repeated.
I verify with python-chess that the move list really reaches a third occurrence.

Each case: fresh process, every setoption confirmed by readyok, every search awaited, Threads 1.

usage: check_s15f24.py OUTDIR
"""
import json
import os
import subprocess
import sys
import threading
import time

import chess

BASE = "/home/ubuntu/b/rel/forge"
PCX = "/home/ubuntu/b/pc/forge"
ENV = {k: v for k, v in os.environ.items()
       if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

# The halfmove-100 mate board from the finding family (a rook mate on the back rank).
MATE_100 = "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 1"
# A threefold cycle, played as moves so the ENGINE's history sees three occurrences.
CYCLE = "g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8"


def search(exe, settings, position_cmd, go, timeout=180.0):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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

    def ready(t=120.0):
        with lock:
            k = len(out)
        send("isready")
        t0 = time.monotonic()
        while time.monotonic() - t0 < t:
            with lock:
                if any(x.strip() == "readyok" for x in out[k:]):
                    return True
            if p.poll() is not None:
                return False
            time.sleep(0.003)
        return False

    send("uci")
    t0 = time.monotonic()
    while time.monotonic() - t0 < 60:
        with lock:
            if any(x.strip() == "uciok" for x in out):
                break
        time.sleep(0.003)
    send("setoption name Threads value 1")
    ready()
    bad = []
    for name, value in settings:
        with lock:
            k = len(out)
        send("setoption name %s value %s" % (name, value))
        ready()
        with lock:
            bad += [x for x in out[k:] if "unknown option" in x or "invalid value" in x]
    send("ucinewgame")
    ready()
    send(position_cmd)
    ready()
    with lock:
        mark = len(out)
    send(go)
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        with lock:
            if any(x.startswith("bestmove") for x in out[mark:]):
                break
        time.sleep(0.004)
    with lock:
        blk = out[mark:]
    try:
        send("quit")
    except Exception:
        pass
    try:
        p.wait(timeout=15)
    except Exception:
        p.kill()
    infos = [x for x in blk if x.startswith("info depth") and " pv" in x]
    score = nodes = bm = None
    if infos:
        t = infos[-1].split()
        if "score" in t:
            score = " ".join(t[t.index("score") + 1:t.index("score") + 3])
        if "nodes" in t:
            nodes = int(t[t.index("nodes") + 1])
    for l in blk:
        if l.startswith("bestmove"):
            parts = l.split()
            bm = parts[1] if len(parts) > 1 else None
    return {"score": score, "nodes": nodes, "bestmove": bm,
            "info_lines": len(infos), "bad_options": bad,
            "refused": [x for x in blk if "invalid" in x.lower()][:2]}


def repetition_facts():
    """Verify with python-chess that CYCLE reaches a third occurrence, and report the FEN."""
    b = chess.Board()
    for mv in CYCLE.split():
        b.push_uci(mv)
    counts = {}
    # count occurrences of the current position over the whole game history
    b2 = chess.Board()
    hist = [b2.fen().split(" ")[0] + " " + b2.fen().split(" ")[1]]
    for mv in CYCLE.split():
        b2.push_uci(mv)
        f = b2.fen().split(" ")
        hist.append(f[0] + " " + f[1])
    cur = hist[-1]
    return {"occurrences_of_final_position": hist.count(cur),
            "final_fen": b.fen(),
            "can_claim_threefold": b.can_claim_threefold_repetition(),
            "is_repetition": b.is_repetition(3)}


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    rep = repetition_facts()
    print("python-chess check of the cycle: occurrences=%d can_claim_threefold=%s is_repetition(3)=%s" % (
        rep["occurrences_of_final_position"], rep["can_claim_threefold"], rep["is_repetition"]))
    report = {"repetition_facts": rep, "cases": {}}
    cases = {
        "A_mate_at_halfmove_100": ("position fen " + MATE_100, "go depth 6"),
        "B_thrice_repeated_root": ("position startpos moves " + CYCLE, "go depth 6"),
        "C_twice_repeated_root": ("position startpos moves g1f3 g8f6 f3g1 f6g8", "go depth 6"),
    }
    for label, exe, settings, sname in (
            ("base_S14", BASE, S14, "S14"),
            ("pc_PC20", PCX, PC20, "PC20")):
        for cname, (pos, go) in cases.items():
            r = search(exe, settings, pos, go)
            r.update({"build": label, "settings": sname, "position": pos, "go": go})
            report["cases"]["%s/%s" % (label, cname)] = r
            print("%-10s %-24s score=%-9s nodes=%-7s bestmove=%-6s infos=%d" % (
                label, cname, r["score"], r["nodes"], r["bestmove"], r["info_lines"]))
    with open(os.path.join(outdir, "check_s15f24.json"), "w") as f:
        json.dump(report, f, indent=1)
    # verdicts per the finding
    a = report["cases"]["pc_PC20/A_mate_at_halfmove_100"]
    b = report["cases"]["pc_PC20/B_thrice_repeated_root"]
    print()
    print("PC build, halfmove-100 mate found:", bool(a["score"] and a["score"].startswith("mate")))
    print("PC build, thrice-repeated root SEARCHED (regression):",
          bool(b["nodes"] and b["nodes"] > 100))
    print("base build, thrice-repeated root declared drawn:",
          report["cases"]["base_S14/B_thrice_repeated_root"]["nodes"] == 0)


if __name__ == "__main__":
    main()

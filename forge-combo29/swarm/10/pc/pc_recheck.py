#!/usr/bin/env python3
"""pc_recheck.py OUTDIR -- re-run my own finds on the PC build under PC20 (file 5's instruction).

Each find is re-tested with the SAME harness logic as on the base tree, on:
  build    ~/builds/pc/forge  (r15 + FORGE_MATE_ALPHA_GUARD=1)
  settings PC20 (S14 + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
           MateAlphaGuard true, OwnBook false), Threads 1, Hash 16  [seat 04's thread rule]
and, for comparison, on the base build under S14.

Finds re-tested (each is one of mine, with its state on the base tree):
  10-F11  ucinewgame AFTER position resets the board to startpos
  10-F21  two identical searches in one process are not reproducible (warm vs cold)
  10-F22  Clear Hash is not a cold reset (ucinewgame is)
  K1      illegal move keeps the legal prefix (perft 1 = 29)
  K2      setoption Hash 0 -> info string invalid value for option Hash
  K10     go banana searches instead of being ignored
  K12     bestmove 0000 on checkmate / stalemate
  10-F14  searchmoves-to-all-20 changes the score (base: cp 30 vs cp 23)
  10-F19  that gap survives with IIR off

Every search is one `go` at a time on a driver that never closes stdin early (10-C5), Threads 1.
Result per find: SAME / REPAIRED / DIFFERENT, with the numbers both ways.
"""
import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audit"))
from drv import Drv

BASE = os.path.expanduser("~/builds/release/forge")
PC = os.path.expanduser("~/builds/pc/forge")
OUT = os.path.abspath(sys.argv[1])
os.makedirs(OUT, exist_ok=True)

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
ALL = " ".join(m.uci() for m in chess.Board().legal_moves)


def drv(exe, regime):
    d = Drv(exe)
    d.uci()
    d.isready()
    d.opt("Threads", "1")
    d.opt("Hash", "16")
    for k, v in (S14 if regime == "s14" else PC20 if regime == "pc20" else []):
        d.opt(k, v)
    d.isready()
    return d


def score_of(lines):
    for l in reversed(lines):
        if l.startswith("info") and " score cp " in l:
            return int(l.split(" score cp ")[1].split()[0])
        if l.startswith("info") and " score mate " in l:
            return "mate " + l.split(" score mate ")[1].split()[0]
    return None


def res_10f11(exe, regime):
    """ucinewgame AFTER position: eval + perft1 before and after"""
    d = drv(exe, regime)
    d.write("ucinewgame")
    d.isready()
    d.pos("position fen 1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1")
    d.write("eval")
    ev1 = d._read_until(lambda l: l.startswith("info string eval"))[-1]
    tot1, _ = d.perft(1)
    d.write("ucinewgame")
    d.isready()
    d.write("eval")
    ev2 = d._read_until(lambda l: l.startswith("info string eval"))[-1]
    tot2, _ = d.perft(1)
    d.quit()
    return {"eval_before": ev1, "perft1_before": tot1, "eval_after_ucinewgame": ev2,
            "perft1_after": tot2,
            "resets": tot1 != tot2 or ev1 != ev2,
            "note": "base: eval total -351 -> +38, perft1 38 -> 20 (a reset)"}


def res_10f21(exe, regime):
    """two identical unrestricted searches, one process"""
    d = drv(exe, regime)
    d.write("ucinewgame")
    d.isready()
    d.pos("position startpos")
    n1, b1, l1 = d.go("go depth 12")
    s1 = score_of(l1)
    n2, b2, l2 = d.go("go depth 12")
    s2 = score_of(l2)
    d.quit()
    return {"first": {"nodes": n1, "score": s1, "bestmove": b1},
            "second": {"nodes": n2, "score": s2, "bestmove": b2},
            "reproducible": n1 == n2 and s1 == s2,
            "note": "base: 56720/cp30 then 4951/cp30 -> NOT reproducible"}


def res_10f22(exe, regime):
    """ucinewgame vs Clear Hash as the cold reset"""
    out = {}
    for label, plan in (("ucinewgame", ["U", "N", "U"]), ("clearhash", ["U", "C", "U"])):
        d = drv(exe, regime)
        d.write("ucinewgame")
        d.isready()
        d.pos("position startpos")
        nodes = []
        for step in plan:
            if step == "N":
                d.write("ucinewgame")
                d.isready()
            elif step == "C":
                d.write("setoption name Clear Hash")
                d.isready()
            else:
                n, b, l = d.go("go depth 12")
                nodes.append(n)
        d.quit()
        out[label] = nodes
    d = drv(exe, regime)
    d.write("ucinewgame")
    d.isready()
    d.pos("position startpos")
    n, b, l = d.go("go depth 12")
    d.quit()
    out["cold_single"] = [n]
    out["ucinewgame_restores_cold"] = out["ucinewgame"][1] == out["cold_single"][0]
    out["clearhash_restores_cold"] = out["clearhash"][1] == out["cold_single"][0]
    return out


def res_k1(exe, regime):
    d = drv(exe, regime)
    d.pos("position startpos moves e2e4 e7e5 e1e3")
    tot, _ = d.perft(1)
    d.quit()
    return {"perft1": tot, "expected": 29, "holds": tot == 29}


def res_k2(exe, regime):
    d = drv(exe, regime)
    d.opt("Hash", "0")
    lines = d.isready()
    d.quit()
    msg = [l for l in lines if "invalid value" in l.lower()]
    return {"message": msg, "holds": any("invalid value for option Hash" in m for m in msg)}


def res_k10(exe, regime):
    d = drv(exe, regime)
    d.write("ucinewgame")
    d.isready()
    d.pos("position startpos")
    d.write("go banana")
    got = d._read_until(lambda l: l.startswith("bestmove"), timeout=120)
    d.quit()
    best = [l for l in got if l.startswith("bestmove")]
    return {"bestmove": best, "searched_not_ignored": bool(best)}


def res_k12(exe, regime):
    out = {}
    for name, fen in (("checkmate", "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"),
                      ("stalemate", "7k/5Q2/5K2/8/8/8/8/8 b - - 0 1")):
        d = drv(exe, regime)
        d.write("ucinewgame")
        d.isready()
        d.pos("position fen " + fen)
        n, b, l = d.go("go depth 5")
        d.quit()
        out[name] = {"bestmove": b, "nodes": n, "score": score_of(l),
                     "is_0000": b == "0000"}
    out["holds"] = all(v["is_0000"] for v in out.values() if isinstance(v, dict))
    return out


def res_10f14(exe, regime):
    u = drv(exe, regime)
    u.write("ucinewgame")
    u.isready()
    u.pos("position startpos")
    n1, b1, l1 = u.go("go depth 12")
    u.quit()
    r = drv(exe, regime)
    r.write("ucinewgame")
    r.isready()
    r.pos("position startpos")
    n2, b2, l2 = r.go("go depth 12 searchmoves " + ALL)
    r.quit()
    return {"unrestricted": {"nodes": n1, "score": score_of(l1), "bestmove": b1},
            "restricted_all20": {"nodes": n2, "score": score_of(l2), "bestmove": b2},
            "score_differs": score_of(l1) != score_of(l2),
            "note": "base: cp 30/e2e4 vs cp 23/d2d4 -> differs"}


def res_10f19(exe, regime):
    """the all-20 gap with IIR off (IirDepth 20)"""
    out = {}
    for iir in ("2", "20"):
        u = Drv(exe)
        u.uci()
        u.isready()
        u.opt("Threads", "1")
        u.opt("Hash", "16")
        for k, v in (S14 if regime == "s14" else PC20):
            u.opt(k, v)
        u.opt("IirDepth", iir)
        u.isready()
        u.write("ucinewgame")
        u.isready()
        u.pos("position startpos")
        n1, b1, l1 = u.go("go depth 12")
        u.quit()
        r = Drv(exe)
        r.uci()
        r.isready()
        r.opt("Threads", "1")
        r.opt("Hash", "16")
        for k, v in (S14 if regime == "s14" else PC20):
            r.opt(k, v)
        r.opt("IirDepth", iir)
        r.isready()
        r.write("ucinewgame")
        r.isready()
        r.pos("position startpos")
        n2, b2, l2 = r.go("go depth 12 searchmoves " + ALL)
        r.quit()
        out["IirDepth" + iir] = {
            "unrestricted": {"nodes": n1, "score": score_of(l1), "bestmove": b1},
            "restricted": {"nodes": n2, "score": score_of(l2), "bestmove": b2},
            "gap_survives": score_of(l1) != score_of(l2)}
    return out


FINDINGS = [
    ("10-F11", res_10f11), ("10-F21", res_10f21), ("10-F22", res_10f22),
    ("K1", res_k1), ("K2", res_k2), ("K10", res_k10), ("K12", res_k12),
    ("10-F14", res_10f14), ("10-F19", res_10f19),
]

out = {}
for fid, fn in FINDINGS:
    entry = {}
    for tag, exe, regime in (("pc20", PC, "pc20"), ("base_s14", BASE, "s14")):
        try:
            entry[tag] = fn(exe, regime)
        except Exception as e:                                # noqa: BLE001
            entry[tag] = {"error": "%s: %s" % (type(e).__name__, e)}
    out[fid] = entry
    with open(os.path.join(OUT, "pc_recheck.json"), "w") as f:
        json.dump(out, f, indent=2)
        f.write("\n")
    print("%-8s pc20=%s" % (fid, json.dumps(entry["pc20"])[:220]), flush=True)
print("done")

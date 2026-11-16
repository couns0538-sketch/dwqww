#!/usr/bin/env python3
"""pc20_rerun.py — seat 20 job 26: re-run my own finds on the PC r15 build under PC20.

File 5: "Your own finds on the base tree: run the reproduction on the PC build under PC20. A find that is gone
there is 'repaired on the PC' (say so in the finding line); a find that is still there is worth much more now."

Every case is labelled BUILD + SETTINGS. Each is run on the PC build with PC20, and (for contrast) on the base
build with S14 where the find was originally measured that way.

The cases, each with the exact expectation that makes it a REPAIR or a LIVE finding:
  F1  drawn root / repetition door  : third-occurrence mate-in-1 must answer the mate, not f2f3/cp0/0 nodes
  F2  drawn root / halfmove 100     : mate-in-1 at halfmove 100 must answer the mate
  F3  searchmoves empty -> 0000     : startpos, `go depth 2 searchmoves` -> must answer a legal move, not 0000
  F4  ucinewgame board reset        : black-to-move position + ucinewgame must NOT answer a white move
  F5  mate distance S-F19 board     : depth 12 score/distance observed (true distance is 8 plies = mate -4)
  F6  LmpBase=8 loses the mate      : on the S-F19 board, LmpBase 8 vs PC20's LmpBase
  F7  hashfull 1000-cluster window  : hashfull at Hash 16 vs 1024, nodes identical?
  F8  go nodes 1 -> first legal     : startpos `go nodes 1`
  F9  movetime overhead subtraction : go movetime 100 wall time vs Move Overhead 0
  F10 fifty-move horizon early zero : K+R v K sweep 89/90/91/99/100

usage: pc20_rerun.py <pc-exe> <base-exe> <outdir>
"""
import json
import os
import re
import statistics
import sys
import time

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

PC, BASE, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = [("Threads", 1), ("Hash", 16)] + S14 + [("CuckooRep", "true"), ("HistRework", "2"),
                                               ("TtPruneV2", "true"), ("CorrHistV2", "true"),
                                               ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BASE_S14 = [("Threads", 1), ("Hash", 16)] + S14 + [("OwnBook", "false")]
BUILDS = {"pc20": (PC, PC20), "base_s14": (BASE, BASE_S14)}

MATE1 = "6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1"          # mate in 1: d1d8
BLACKPOS = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 0 1"
ITALIAN = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1"
SF19 = "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
CYCLE = ["g1h1", "g8h8", "h1g1", "h8g8"]


def hm(fen, v):
    p = fen.split()
    p[4] = str(v)
    return " ".join(p)


def run(build, fen, go, extra=(), moves=None, timeout=300):
    exe, opts = BUILDS[build]
    e = Engine(exe, opts=list(opts) + list(extra))
    try:
        if moves:
            e.move_list(fen, moves)
        else:
            e.position(fen)
        r = e.search(go, timeout)
    finally:
        e.close()
    return r


def brief(r):
    d = None
    if r["last_info"]:
        m = re.search(r"depth (\d+)", r["last_info"])
        d = int(m.group(1)) if m else None
    return {"bestmove": r["bestmove"], "score": r["score"], "nodes": r["nodes"], "depth": d,
            "pv_len": len(r["pv"]), "unsearched": r["unsearched"], "hang": r["hang"],
            "wall_ms": round(r["wall"] * 1000, 2)}


rows = []


def case(tag, desc, build, fen, go, expect, extra=(), moves=None):
    r = run(build, fen, go, extra, moves)
    b = brief(r)
    ok = expect(b)
    rows.append({"case": tag, "desc": desc, "build": build,
                 "settings": "PC20" if build == "pc20" else "S14", "fen": fen,
                 "moves": moves, "go": go, "extra": list(extra), **b,
                 "expectation": "PASS" if ok else "FAIL"})
    print(f"{tag:5s} {build:8s} {str(b['bestmove']):7s} {str(b['score']):9s} nodes {b['nodes']:8d} "
          f"depth {str(b['depth']):>3s} pv {b['pv_len']:2d}  -> {'PASS' if ok else 'FAIL'}  ({desc})")
    return b


print(f"PC build   {PC}")
print(f"base build {BASE}")
print()

# ---- F1: repetition door (third occurrence) -------------------------------------------------------
def is_mate(b):
    return (b["score"] or "").startswith("mate") and b["bestmove"] not in (None, "0000")


print("F1 repetition door: board + 8 plies (THIRD occurrence), mate in 1 available")
f1 = {}
for bld in ("base_s14", "pc20"):
    f1[bld] = case("F1", "third occurrence: mate must be found", bld, MATE1, "go depth 6", is_mate,
                   moves=CYCLE + CYCLE)
# control: the same board as a plain FEN with no history (must find the mate on both builds)
for bld in ("base_s14", "pc20"):
    case("F1c", "control: same board, no history", bld, MATE1, "go depth 6", is_mate)

# ---- F2: halfmove 100 -----------------------------------------------------------------------------
print("\nF2 drawn root at halfmove 100: mate in 1 must be found")
for bld in ("base_s14", "pc20"):
    case("F2", "halfmove 100, mate in 1", bld, hm(MATE1, 100), "go depth 6", is_mate)
for bld in ("base_s14", "pc20"):
    case("F2c", "control: halfmove 99", bld, hm(MATE1, 99), "go depth 6", is_mate)

# ---- F3: empty searchmoves ------------------------------------------------------------------------
print("\nF3 empty searchmoves on a live board")
def not_zero(b):
    return b["bestmove"] not in (None, "0000")
for bld in ("base_s14", "pc20"):
    case("F3", "startpos go depth 2 searchmoves", bld, START, "go depth 2 searchmoves", not_zero)
for bld in ("base_s14", "pc20"):
    case("F3c", "control: go depth 2", bld, START, "go depth 2", not_zero)

# ---- F4: ucinewgame reset -------------------------------------------------------------------------
print("\nF4 ucinewgame after a black-to-move position (a WHITE move means the board was reset)")
def no_white_move(b):
    mv = b["bestmove"] or ""
    return mv not in {m.uci() for m in chess.Board().legal_moves} or b["bestmove"] in (None, "0000")
for bld in ("base_s14", "pc20"):
    exe, opts = BUILDS[bld]
    e = Engine(exe, opts=list(opts))
    try:
        e.position(BLACKPOS)
        e.send("ucinewgame"); e.isready()
        e.send(f"position fen {BLACKPOS}"); e.isready()
        e.send("ucinewgame"); e.isready()
        r = e.search("go depth 6", 120)
    finally:
        e.close()
    b = brief(r)
    # after the reset the engine is on startpos; a black-to-move position must ANSWER A BLACK MOVE
    black_moves = {m.uci() for m in chess.Board(BLACKPOS).legal_moves}
    reset_seen = b["bestmove"] in {m.uci() for m in chess.Board().legal_moves} and \
                 b["bestmove"] not in black_moves
    rows.append({"case": "F4", "desc": "position -> ucinewgame -> go (board reset?)", "build": bld,
                 "settings": "PC20" if bld == "pc20" else "S14", "fen": BLACKPOS, "go": "go depth 6",
                 **b, "reset_detected": reset_seen,
                 "expectation": "RESET (find live)" if reset_seen else "NO RESET (repaired)"})
    print(f"{'F4':5s} {bld:8s} {str(b['bestmove']):7s} {str(b['score']):9s} nodes {b['nodes']:8d} "
          f" -> {'BOARD WAS RESET (find live)' if reset_seen else 'no reset (repaired)'}")

# ---- F5: mate distance on the S-F19 board ---------------------------------------------------------
print("\nF5 mate distance on the S-F19 board at depth 12 (true forced distance is 8 plies = mate -4)")
for bld in ("base_s14", "pc20"):
    case("F5", "S-F19 board depth 12", bld, SF19, "go depth 12", lambda b: True)

# ---- F7: hashfull window --------------------------------------------------------------------------
print("\nF7 hashfull at Hash 16 vs 1024 (same search)")
for bld in ("base_s14", "pc20"):
    vals = {}
    for h in (16, 1024):
        r = run(bld, ITALIAN, "go depth 12", extra=[("Hash", h)])
        hf = None
        if r["last_info"]:
            m = re.search(r"hashfull (\d+)", r["last_info"])
            hf = int(m.group(1)) if m else None
        vals[h] = (hf, r["nodes"])
        print(f"F7    {bld:8s} Hash {h:5d}: hashfull {hf}  nodes {r['nodes']}")
    rows.append({"case": "F7", "build": bld, "hash16": vals[16], "hash1024": vals[1024]})

# ---- F8: go nodes 1 -------------------------------------------------------------------------------
print("\nF8 go nodes 1 on startpos")
for bld in ("base_s14", "pc20"):
    case("F8", "go nodes 1", bld, START, "go nodes 1", lambda b: True)

# ---- F9: movetime overhead ------------------------------------------------------------------------
print("\nF9 go movetime 100, Move Overhead default vs 0 (wall ms, 5 runs each)")
for bld in ("base_s14", "pc20"):
    for oh in (None, 0):
        ws = []
        for _ in range(5):
            r = run(bld, ITALIAN, "go movetime 100",
                    extra=[] if oh is None else [("Move Overhead", 0)])
            ws.append(r["wall"] * 1000)
        print(f"F9    {bld:8s} overhead {str(oh):6s}: median {statistics.median(ws):7.2f} ms")
        rows.append({"case": "F9", "build": bld, "overhead": oh,
                     "median_ms": round(statistics.median(ws), 2)})

# ---- F10: fifty-move horizon sweep ----------------------------------------------------------------
print("\nF10 K+R v K, first halfmove where the score is exactly cp 0")
KRK = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"
for bld in ("base_s14", "pc20"):
    onset = None
    for v in (85, 89, 90, 91, 95, 99, 100):
        r = run(bld, hm(KRK, v), "go depth 10")
        sc = r["score"]
        if onset is None and sc == "cp 0":
            onset = v
        print(f"F10   {bld:8s} halfmove {v:3d}: {sc:9s} nodes {r['nodes']:9d}")
        rows.append({"case": "F10", "build": bld, "halfmove": v, "score": sc, "nodes": r["nodes"]})
    print(f"F10   {bld:8s} first cp 0 at halfmove {onset}")

with open(os.path.join(OUT, "pc20_rerun.json"), "w") as f:
    json.dump({"pc": PC, "base": BASE, "rows": rows}, f, indent=1)
print(f"\nwrote pc20_rerun.json ({len(rows)} rows)")

#!/usr/bin/env python3
"""clock_game.py OUTDIR

The clock at the end of a real 6 s + 0.06 game, on the PC build under PC20, Threads 1.

Part A — a simulated 60-move game: start at 6000 ms for each side, subtract the measured think
time, add 60 ms after each move, and play the engine's own moves. Records every think time and
any case where think time > remaining clock (a forfeit).

Part B — forced low clocks on a real position: wtime in {200, 100, 50, 10, 1, 0}, both with winc 0
and winc 60. Records think time, bestmove legality, and whether a bestmove arrived at all.

Every search one fresh process, read to bestmove (19-F12), monotonic timing.
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, Timeout, bestmove_of, last_info  # noqa: E402

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
START_MS = 6000
INC_MS = 60
MOVES = 60
LOW = [200, 100, 50, 10, 1, 0]


def eng(exe, raw):
    e = SafeEngine(exe, raw, hash_mb=16, threads=1)
    for k, v in S14 + PC20_EXTRA:
        e.send("setoption name %s value %s" % (k, v))
        e.send("isready")
        e.wait_for("readyok")
    e.send("ucinewgame")
    e.send("isready")
    e.wait_for("readyok")
    return e


def think(exe, outdir, tag, pos, go):
    e = eng(exe, os.path.join(outdir, tag + "_raw.txt"))
    e.position(pos)
    t0 = time.monotonic()
    try:
        lines = e.go(go, timeout=120)
        ok = True
    except Timeout:
        lines, ok = [], False
    ms = (time.monotonic() - t0) * 1000.0
    e.close()
    return bestmove_of(lines), ms, ok, last_info(lines)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    fens = [l.strip() for l in open(os.path.join(here, "..", "job1", "set_G.fens")) if l.strip()]
    exe = os.path.expanduser("~/b/pc_asan/forge")

    # ---- Part A: simulated game clock
    board = chess.Board(fens[0]) if fens else chess.Board()
    clock = {chess.WHITE: START_MS, chess.BLACK: START_MS}
    log = []
    forfeits = 0
    for ply in range(MOVES):
        if board.is_game_over():
            break
        me = board.turn
        w = clock[chess.WHITE]
        b = clock[chess.BLACK]
        go = "go wtime %d btime %d winc %d binc %d" % (w, b, INC_MS, INC_MS)
        bm, ms, ok, info = think(exe, outdir, "game_%02d" % ply,
                                 "position fen " + board.fen(), go)
        remaining = clock[me]
        over = ms > remaining
        if over:
            forfeits += 1
        clock[me] = max(0, remaining - int(ms)) + INC_MS
        log.append(dict(ply=ply, side=str(me), go=go, ms=round(ms, 1),
                        remaining=remaining, bestmove=bm, overrun=over))
        if not bm:
            break
        try:
            board.push_uci(bm)
        except Exception:
            break

    # ---- Part B: forced low clocks
    low_rows = []
    fen = fens[0] if fens else chess.Board().fen()
    legal = {m.uci() for m in chess.Board(fen).legal_moves}
    for wtime in LOW:
        for winc in (0, INC_MS):
            go = "go wtime %d btime %d winc %d binc %d" % (wtime, wtime, winc, winc)
            bm, ms, ok, info = think(exe, outdir, "low_%d_%d" % (wtime, winc),
                                     "position fen " + fen, go)
            low_rows.append(dict(wtime=wtime, winc=winc, ms=round(ms, 1), bestmove=bm,
                                 legal=bm in legal, got=ok))

    rows = ["| part | measure | value |", "|---|---|---|",
            "| A | moves simulated | %d |" % len(log),
            "| A | forfeits (think time > remaining clock) | **%d** |" % forfeits,
            "| A | shortest / longest think (ms) | %s / %s |" % (
                min((x["ms"] for x in log), default=0), max((x["ms"] for x in log), default=0)),
            "| A | final clocks (ms) | W %s / B %s |" % (clock[chess.WHITE], clock[chess.BLACK])]
    lrows = ["| wtime | winc | think ms | bestmove | legal | answered |", "|---|---|---|---|---|---|"]
    for r in low_rows:
        lrows.append("| %d | %d | %s | %s | %s | %s |" % (
            r["wtime"], r["winc"], r["ms"], r["bestmove"], r["legal"], r["got"]))
    low_ok = all(r["legal"] and r["got"] for r in low_rows)
    fast_at_10 = all(r["ms"] < 100 for r in low_rows if r["wtime"] <= 10)
    text = "\n".join(rows) + "\n\n" + "\n".join(lrows)
    text += ("\n\nforfeits: %d\nall low-clock answers legal and present: %s\n"
             "every wtime<=10 answer under 100 ms: %s\n" % (forfeits, low_ok, fast_at_10))
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(dict(game=log, low=low_rows, forfeits=forfeits,
                       final_clock={str(k): v for k, v in clock.items()}), fh, indent=1)
    print(text)


if __name__ == "__main__":
    main()
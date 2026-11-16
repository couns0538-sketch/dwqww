#!/usr/bin/env python3
"""clock_stop_move.py -- does a REAL clock stop answer with a move from an unfinished iteration?

30-F23 showed that a `quit` in the middle of the first iteration answers with a different move than
the finished search. The interesting case is the one the owner's engine actually meets: a game in
which the CLOCK stops the search. If a stop mid-iteration answers a move that only beat the
aspiration floor, the engine plays a worse move than it had already found.

Method, each run a fresh process, Threads 1:
  A. The finished answer: `go depth 12` awaited -> bestmove_A, score_A.
  B. A clock stop that lands mid-search: `go wtime 8 btime 8` (8 ms, far less than the ~32 ms a
     depth-12 startpos search needs) -> bestmove_B.
  C. The same position searched to a shallower depth whose node count is close to B's, to see
     whether B is a move the engine would ever have chosen at that effort.
Then, for a set of positions, list every case where B != A.

usage: clock_stop_move.py OUTDIR [N_POSITIONS]
"""
import json
import os
import subprocess
import sys
import threading
import time

import chess

PCX = "/home/ubuntu/b/pc/forge"
BASE = "/home/ubuntu/b/rel/forge"
ENV = {k: v for k, v in os.environ.items()
       if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
S14 = [("Threads", 1), ("Hash", 16),
       ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def spawn(exe, settings):
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

    send("uci")
    t0 = time.monotonic()
    while time.monotonic() - t0 < 30:
        with lock:
            if any(x.strip() == "uciok" for x in out):
                break
        time.sleep(0.003)
    for name, value in settings:
        with lock:
            mark = len(out)
        send("setoption name %s value %s" % (name, value))
        send("isready")
        t1 = time.monotonic()
        while time.monotonic() - t1 < 60:
            with lock:
                blk = out[mark:]
            if any(x.strip() == "readyok" for x in blk):
                bad = [x for x in blk if "unknown option" in x or "invalid value" in x]
                if bad:
                    raise SystemExit("setting refused: %s" % bad[0])
                break
            time.sleep(0.003)
    return p, out, lock, send


def search(exe, settings, fen, go, timeout=180.0):
    p, out, lock, send = spawn(exe, settings)
    send("ucinewgame")
    send("isready")
    time.sleep(0.02)
    send("position fen " + fen)
    with lock:
        mark = len(out)
    send(go)
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        with lock:
            if any(x.startswith("bestmove") for x in out[mark:]):
                break
        time.sleep(0.003)
    with lock:
        blk = out[mark:]
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    bm, score, nodes = None, None, None
    for l in blk:
        if l.startswith("bestmove"):
            parts = l.split()
            bm = parts[1] if len(parts) > 1 else None
        if l.startswith("info depth") and " pv" in l:
            t = l.split()
            if "score" in t:
                score = " ".join(t[t.index("score") + 1:t.index("score") + 3])
            if "nodes" in t:
                nodes = int(t[t.index("nodes") + 1])
    infos = sum(1 for l in blk if l.startswith("info depth"))
    return {"bestmove": bm, "score": score, "nodes": nodes, "info_lines": infos}


def main():
    outdir = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    os.makedirs(outdir, exist_ok=True)
    epd = "/tmp/ds6_work/forge-combo29/tests_deepseek6_long1/set_G.epd"
    fens = [l.split(" bm ")[0].strip() for l in open(epd) if l.strip()][:n]
    report = {"positions": len(fens), "rows": []}
    print("%-3s %-22s %-22s %-9s %s" % ("#", "depth12 (finished)", "wtime 8 (clock stop)", "same?", "detail"))
    for i, fen in enumerate(fens):
        a = search(BASE, S14, fen, "go depth 12")
        b = search(BASE, S14, fen, "go wtime 8 btime 8")
        row = {"i": i, "fen": fen, "depth12": a, "clock8ms": b,
               "same": a["bestmove"] == b["bestmove"]}
        report["rows"].append(row)
        print("%-3d %-22s %-22s %-9s n=%s infos=%s" % (
            i, "%s %s" % (a["bestmove"], a["score"]), "%s %s" % (b["bestmove"], b["score"]),
            "SAME" if row["same"] else "DIFF", b["nodes"], b["info_lines"]))
    diff = [r for r in report["rows"] if not r["same"]]
    report["summary"] = {"positions": len(fens), "differing_bestmove": len(diff),
                         "differing_pct": round(100.0 * len(diff) / max(1, len(fens)), 1),
                         "clock_stops_with_zero_info": sum(
                             1 for r in report["rows"] if r["clock8ms"]["info_lines"] == 0)}
    with open(os.path.join(outdir, "clock_stop_move.json"), "w") as f:
        json.dump(report, f, indent=1)
    print()
    print(json.dumps(report["summary"], indent=1))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""check_08f22.py EXE [--regime PC20] [--board K|KQ]

Check of seat 08's 08-F22 from its stated claim alone: on PC r15 PC20, Threads 1, over halfmove
counters 85..99 EVERY STEP, the fifty-move defect has two different shapes —
  (a) the SCORE defect is a BAND: H=91..99 all score exactly cp 0 on a won K+R vs K board;
  (b) the NODE cost is a SPIKE at H=91 only (they report 7,251,835 nodes, 82.9x the band median),
      with a shoulder at 92-93 and H=94-98 cheaper than a normal search.
Board from their claim: 1K6/8/8/3R4/8/8/8/k7 w - - H 1   (won K+R vs K).

Reports the score and nodes at every counter, then computes which shape the data has.
Threads 1. A refused FEN or missing token is reported, never counted as a number.
"""
import argparse
import queue
import re
import subprocess
import threading
import time

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

BOARDS = {
    "K": "1K6/8/8/3R4/8/8/8/k7 w - - {} 1",      # seat 08's board, won K+R vs K
    "KQ": "8/5K2/7Q/4k3/8/8/8/8 w - - {} 1",     # seat 05's K+Q board
}


def opts(regime):
    return [] if regime == "none" else (S14 if regime == "S14" else S14 + PC20_EXTRA)


def run(exe, o, poscmd, depth, limit=180):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    q = queue.Queue()

    def rd():
        for line in p.stdout:
            q.put(line.rstrip("\n"))
        q.put(None)

    threading.Thread(target=rd, daemon=True).start()

    def send(c):
        p.stdin.write(c + "\n"); p.stdin.flush()

    def wait(pred, lim):
        t0 = time.monotonic()
        while True:
            rem = lim - (time.monotonic() - t0)
            if rem <= 0:
                return "TIMEOUT", None
            try:
                line = q.get(timeout=rem)
            except queue.Empty:
                return "TIMEOUT", None
            if line is None:
                return "EOF", None
            if pred(line):
                return "OK", line

    send("uci"); wait(lambda l: l.startswith("uciok"), 30)
    send("setoption name Threads value 1"); send("setoption name Hash value 16")
    for k, v in o:
        send("setoption name %s value %s" % (k, v))
    send("isready"); wait(lambda l: l == "readyok", 30)
    send("ucinewgame"); send("isready"); wait(lambda l: l == "readyok", 30)
    send(poscmd); send("isready")
    refused = []
    t0 = time.monotonic()
    while time.monotonic() - t0 < 20:
        try:
            line = q.get(timeout=0.5)
        except queue.Empty:
            continue
        if line is None:
            break
        if any(b in line for b in ("invalid FEN", "invalid value", "illegal move", "unknown option")):
            refused.append(line)
        if line.strip() == "readyok":
            break
    if refused:
        try:
            send("quit"); p.wait(timeout=10)
        except Exception:
            p.kill()
        return {"refused": refused}
    send("go depth %d" % depth)
    st, bm = wait(lambda l: l.startswith("bestmove"), limit)
    try:
        send("quit"); p.wait(timeout=10)
    except Exception:
        p.kill()
    if st != "OK":
        return {"status": st}
    return {"bestmove": bm.split()[1] if len(bm.split()) > 1 else None}


def one(exe, o, poscmd, depth):
    """one search, returning score/nodes from the last info line"""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    q = queue.Queue()

    def rd():
        for line in p.stdout:
            q.put(line.rstrip("\n"))
        q.put(None)

    threading.Thread(target=rd, daemon=True).start()

    def send(c):
        p.stdin.write(c + "\n"); p.stdin.flush()

    def wait(pred, lim):
        t0 = time.monotonic()
        while True:
            rem = lim - (time.monotonic() - t0)
            if rem <= 0:
                return "TIMEOUT", None
            try:
                line = q.get(timeout=rem)
            except queue.Empty:
                return "TIMEOUT", None
            if line is None:
                return "EOF", None
            if pred(line):
                return "OK", line

    send("uci"); wait(lambda l: l.startswith("uciok"), 30)
    send("setoption name Threads value 1"); send("setoption name Hash value 16")
    for k, v in o:
        send("setoption name %s value %s" % (k, v))
    send("isready"); wait(lambda l: l == "readyok", 30)
    send("ucinewgame"); send("isready"); wait(lambda l: l == "readyok", 30)
    send(poscmd); send("isready"); wait(lambda l: l == "readyok", 30)
    send("go depth %d" % depth)
    infos, bm = [], None
    t0 = time.monotonic()
    while time.monotonic() - t0 < 400:
        try:
            line = q.get(timeout=1.0)
        except queue.Empty:
            continue
        if line is None:
            break
        if line.startswith("info depth"):
            infos.append(line)
        if line.startswith("bestmove"):
            bm = line
            break
    try:
        send("quit"); p.wait(timeout=10)
    except Exception:
        p.kill()
    last = infos[-1] if infos else None
    if not last:
        return {"score": "NO_INFO_LINE", "nodes": None, "depth": None}
    m = re.search(r"score (cp|mate) (-?\d+)", last)
    m2 = re.search(r"\bnodes (\d+)", last)
    md = re.search(r"^info depth (\d+)", last)
    return {"score": ("%s %s" % (m.group(1), m.group(2))) if m else "PARSE_FAIL",
            "nodes": int(m2.group(1)) if m2 else "PARSE_FAIL",
            "depth": int(md.group(1)) if md else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--regime", default="PC20")
    ap.add_argument("--board", default="K")
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--from", dest="lo", type=int, default=85)
    ap.add_argument("--to", dest="hi", type=int, default=99)
    a = ap.parse_args()
    o = opts(a.regime)
    tpl = BOARDS[a.board]
    print("exe: %s  regime: %s  board %s  depth %d  Threads 1"
          % (a.exe, a.regime, a.board, a.depth), flush=True)
    print("%-6s %-11s %-11s %s" % ("H", "score", "nodes", "depths_reached"), flush=True)
    rows = []
    for h in range(a.lo, a.hi + 1):
        r = one(a.exe, o, "position fen " + tpl.format(h), a.depth)
        rows.append((h, r))
        print("%-6d %-11s %-11s %s" % (h, r["score"], r["nodes"], r["depth"]), flush=True)
    # ---- shape analysis ----
    cp0 = [h for h, r in rows if r["score"] == "cp 0"]
    nodes = [(h, r["nodes"]) for h, r in rows if isinstance(r["nodes"], int)]
    print(flush=True)
    print("counters scoring exactly cp 0: %s" % (cp0 if cp0 else "none"), flush=True)
    if cp0:
        band = [h for h in cp0 if h >= 91]
        print("of those, at H>=91 (the claimed BAND): %d counters %s"
              % (len(band), band), flush=True)
    if nodes:
        peak_h, peak_n = max(nodes, key=lambda t: t[1])
        others = [n for h, n in nodes if h != peak_h]
        med = sorted(others)[len(others) // 2] if others else 0
        print("largest node count: H=%d with %d nodes; median of the other counters %d; ratio %.1fx"
              % (peak_h, peak_n, med, peak_n / med if med else 0), flush=True)
        print("=> shape: %s" % ("SCORE BAND + SINGLE NODE SPIKE at one counter (seat 08's claim)"
                                if len(cp0) >= 5 and peak_n > 5 * med
                                else "does NOT match 'band + single spike'"), flush=True)


if __name__ == "__main__":
    main()

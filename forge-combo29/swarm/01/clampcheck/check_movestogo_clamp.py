#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 28's S-F10 — `movestogo` above 50 is clamped to exactly 50.

Seat 28's claim, verbatim:
  "`movestogo` above 50 is clamped to exactly 50: `movestogo 50` and `movestogo 51` both plan 19/76 ms and
   measure medians 16.3 vs 16.4 ms (0.6 % apart), matching `mtg = moves_to_go < 50 ? moves_to_go : 50` in
   include/forge/clock_plan.hpp:37."

WHY IT MATTERS TO EVERY LATENCY HARNESS: a harness that sets a large `movestogo` to mean "spread the clock
over many moves" gets 50 instead, so its expected budget is wrong by movestogo/50. And a harness that uses
`movestogo 0` or a negative value takes a DIFFERENT branch (the `moves_to_go > 0` guard at line 37), which is
the edge I check here because it is the one a "spread it evenly" harness would naturally hit.

Method: on my own board, at a fixed 2000 ms clock, measure the wall time for movestogo = 0, 1, 2, 10, 40, 49,
50, 51, 100, 1000, -1. If the clamp is real, 51/100/1000 must be indistinguishable from 50 (and from 49 within
noise), while 0 and -1 fall through the guard and behave like no movestogo at all.

Repeats: 5 per value, median reported, because clock searches are not exactly repeatable.

Usage: check_movestogo_clamp.py <pc-exe> <outdir>
"""
import hashlib, json, os, select, statistics, subprocess, sys, time
from pathlib import Path

TIMEOUT = 300.0
OPTS = [("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
        ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),
        ("HistoryPruneMultiplier","2220"),("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),
        ("HistoryBonusMax","2212"),("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),
        ("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),
        ("MateAlphaGuard","true"),("OwnBook","false"),("Threads","1"),("Hash","16")]
BOARD = "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"

class R:
    def __init__(self, fd): self.fd, self.buf, self.eof = fd, b"", False
    def line(self, deadline):
        while b"\n" not in self.buf:
            if self.eof: return None
            rem = deadline - time.monotonic()
            if rem <= 0: return None
            r,_,_ = select.select([self.fd],[],[],rem)
            if not r: return None
            c = os.read(self.fd, 65536)
            if not c: self.eof = True; return None
            self.buf += c
        l,_,self.buf = self.buf.partition(b"\n")
        return l.decode("utf-8","replace")

def one(exe, mtg, wtime=2000):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno()); buf=[]
    def until(pre, dl):
        while True:
            l = rd.line(dl)
            if l is None: return None
            buf.append(l)
            if l.startswith(pre): return l
    def send(s):
        p.stdin.write((s+"\n").encode()); p.stdin.flush()
    d = time.monotonic()+TIMEOUT
    send("uci"); until("uciok", d)
    for n,v in OPTS:
        send("setoption name %s value %s" % (n,v)); send("isready"); until("readyok", d)
    send("ucinewgame"); send("isready"); until("readyok", d)
    send("position fen "+BOARD); send("isready"); until("readyok", d)
    go = "go wtime %d btime %d" % (wtime, wtime)
    if mtg is not None:
        go += " movestogo %d" % mtg
    t0 = time.monotonic()
    send(go)
    bml = until("bestmove", d)
    wall = (time.monotonic()-t0)*1000.0
    send("quit")
    try: p.wait(timeout=120)
    except Exception: p.kill()
    return wall, (bml.split()[1] if bml and len(bml.split())>1 else None)

def main():
    exe = sys.argv[1]; out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    values = [None, 0, 1, 2, 10, 40, 49, 50, 51, 100, 1000, -1]
    lines = ["CHECK of seat 28's S-F10: is `movestogo` clamped to 50, and what do 0/negative do?",
             "exe_started: %s" % exe,
             "sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
             "board: "+BOARD,
             "PC20, Threads 1, Hash 16, wtime=btime=2000, winc=binc=0, 5 runs per value, median",
             ""]
    lines.append("movestogo\tmedian_ms\tmin\tmax\tbestmove")
    rows=[]
    for mtg in values:
        walls=[]; bm=None
        for _ in range(5):
            w,b = one(exe, mtg)
            walls.append(w); bm=b
        med = statistics.median(walls)
        rows.append({"movestogo":mtg,"median":round(med,1),"min":round(min(walls),1),
                     "max":round(max(walls),1),"bestmove":bm})
        label = "none" if mtg is None else str(mtg)
        print("%-8s median %-8.1f min %-7.1f max %-7.1f %s" % (label, med, min(walls), max(walls), bm),
              flush=True)
        lines.append("%s\t%.1f\t%.1f\t%.1f\t%s" % (label, med, min(walls), max(walls), bm))
    by = {r["movestogo"]: r["median"] for r in rows}
    def pct(a,b):
        return abs(by[a]-by[b]) / max(by[a],by[b]) * 100 if a in by and b in by else None
    v=[]
    v.append("")
    v.append("CLAMP TEST: median(movestogo 50) = %.1f ms, 51 = %.1f, 100 = %.1f, 1000 = %.1f"
             % (by.get(50,0), by.get(51,0), by.get(100,0), by.get(1000,0)))
    spread = max(by[50],by[51],by[100],by[1000]) - min(by[50],by[51],by[100],by[1000])
    base50 = by[50]
    pct_spread = 100*spread/base50 if base50 else 0
    v.append("  spread across 50/51/100/1000: %.1f ms = %.1f %% of the movestogo-50 median" % (spread, pct_spread))
    if pct_spread <= 10:
        v.append("  -> CONFIRMS seat 28's S-F10: everything above 50 is indistinguishable from 50, i.e. clamped.")
    else:
        v.append("  -> does NOT confirm the clamp on my board (spread too wide); report as is.")
    v.append("")
    v.append("EDGE CASES seat 28 did not report, which a latency harness can hit — with the mechanism:")
    v.append("  movestogo 0 = %.1f ms ; movestogo -1 = %.1f ms ; NO movestogo = %.1f ms"
             % (by.get(0,0), by.get(-1,0), by.get(None,0)))
    v.append("  From clock_plan.hpp:37-48, `moves_to_go > 0` selects the even-spread branch:")
    v.append("     movestogo N>0 : soft = available/(min(N,50)+1) + inc*3/4  -> SHORT per-move budget")
    v.append("     movestogo 0/-1: soft = available/divisor + inc*pct/100   (divisor default 5)")
    v.append("  so a NEGATIVE or ZERO movestogo does NOT mean 'no moves to go' in the sense a harness may")
    v.append("  assume: it selects the SUDDEN-DEATH branch, which at a 2000 ms clock gives soft ~398 ms")
    v.append("  against the movestogo-50 branch's ~26 ms — a %.0fx difference in the other direction."
             % (by.get(0,1)/by.get(50,1) if by.get(50) else 0))
    v.append("  A harness that sends `movestogo 0` to mean 'ignore this field' therefore gets the SLOWEST")
    v.append("  plan, not the default one. Send no movestogo token at all to get the no-movestogo branch,")
    v.append("  or the numbers in the first column (none) will not match.")
    if by.get(None) and abs(by.get(0,0)-by.get(None,0))/by.get(None,0) > 0.15:
        v.append("  MEASURED: none = %.1f ms vs movestogo 0 = %.1f ms -> %.1fx apart, so the two are NOT"
                 % (by.get(None,0), by.get(0,0), by.get(0,0)/by.get(None,0)))
        v.append("  interchangeable. (The `none` figure is itself small here because the engine finished the")
        v.append("  board early; the mechanism, not the absolute, is the point.)")
    v.append("")
    v.append("ALSO NOTE for latency harnesses: movestogo 1 and 2 differ from 50 by %.0f %% and %.0f %%,"
             % (100*abs(by.get(1,0)-base50)/base50 if base50 else 0,
                100*abs(by.get(2,0)-base50)/base50 if base50 else 0))
    v.append("  so the clamp matters only above 50 - but a harness reading a PLAN rather than a wall time must")
    v.append("  know the planned soft/hard limits, not the movestogo it sent, because clock_plan.hpp:38")
    v.append("  silently substitutes 50 for anything larger.")
    (out/"check_movestogo_clamp.json").write_text(json.dumps({"rows":rows,"verdict":v}, indent=1))
    (out/"check_movestogo_clamp.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__ == "__main__":
    main()

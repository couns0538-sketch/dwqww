#!/usr/bin/env python3
"""check_s12f12.py OUT — my own check of seat 12's S-F12:

"`setoption` sent during a running search SILENTLY STOPS that search (4/4 option types: Hash, MultiPV, LmrQuietBase,
 OwnBook), exactly like `stop`, on base AND PC r15 — while `isready` correctly does NOT."

Why it matters beyond the claim: if true, ANY harness that sends a setoption while a search runs silently truncates
that search, and would record a fabricated/shallow bestmove as a real one. That is a measurement-integrity fact for
every seat, so it is worth an independent check.

Method, on the PC build under PC20 and the base build under S14, Threads 1, Hash 16:
  - start `go depth 24` on a middlegame position (a long search),
  - wait 150 ms so several iterations have completed,
  - for each probe: send the probe line, then measure how long until `bestmove` arrives and how deep the last
    `info depth` was;
  - CONTROL: with NO probe, the same search must keep running to depth 24 (or at least far past what the probes
    allow), else the position is simply not long enough to distinguish.

Probes: `setoption name Hash value 32`, `setoption name MultiPV value 2`, `setoption name LmrQuietBase value 94`,
`setoption name OwnBook value true`, and `isready` as the control probe.

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys
import threading
import time

OUT = sys.argv[1]
PC = "/home/ubuntu/builds/pc/forge"
BASE = "/home/ubuntu/builds/release/forge"
FEN = "r2q1rk1/ppp2ppp/3bbn2/3p4/8/1PN1PN2/PBPPBPPP/R2Q1RK1 w - - 0 10"
S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
       ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
       ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
       ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]
PROBES = [("setoption Hash", "setoption name Hash value 32"),
          ("setoption MultiPV", "setoption name MultiPV value 2"),
          ("setoption LmrQuietBase", "setoption name LmrQuietBase value 94"),
          ("setoption OwnBook", "setoption name OwnBook value true"),
          ("isready (CONTROL)", "isready"),
          ("nothing (CONTROL)", None)]


def run(exe, extra, probe_line, wait_ms=150):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def sync():
        send("isready")
        while True:
            l = p.stdout.readline()
            if not l:
                raise EOFError
            if l.startswith("readyok"):
                return

    send("uci")
    while not p.stdout.readline().startswith("uciok"):
        pass
    for k, v in S14 + extra + [("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")]:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + FEN)
    sync()

    lines = []
    done = threading.Event()

    def rd():
        while True:
            l = p.stdout.readline()
            if not l:
                break
            lines.append(l.rstrip("\n"))
            if l.startswith("bestmove"):
                break
        done.set()

    t0 = time.monotonic()
    send("go depth 24")
    threading.Thread(target=rd, daemon=True).start()
    time.sleep(wait_ms / 1000.0)
    depth_at_probe = 0
    for l in list(lines):
        if l.startswith("info depth"):
            try:
                depth_at_probe = max(depth_at_probe, int(l.split()[2]))
            except (IndexError, ValueError):
                pass
    if probe_line is not None:
        send(probe_line)
    t_probe = time.monotonic()
    finished = done.wait(20.0)
    total_ms = (time.monotonic() - t0) * 1000.0
    after_probe_ms = (time.monotonic() - t_probe) * 1000.0
    final_depth = 0
    for l in lines:
        if l.startswith("info depth"):
            try:
                final_depth = max(final_depth, int(l.split()[2]))
            except (IndexError, ValueError):
                pass
    bm = [l for l in lines if l.startswith("bestmove")]
    p.kill()
    return {"finished": finished, "depth_at_probe": depth_at_probe, "final_depth": final_depth,
            "total_ms": total_ms, "after_probe_ms": after_probe_ms,
            "bm": bm[-1].split()[1] if bm else None}


out = []
def emit(s):
    out.append(s)
    print(s)

for label, exe, extra in (("PC r15 PC20", PC, PC20_EXTRA), ("base S14", BASE, [])):
    emit("## %s — `go depth 24`, probe sent after 150 ms" % label)
    emit("")
    emit("| probe | depth at probe | final depth | ms after probe | bestmove | did it stop early? |")
    emit("|---|---|---|---|---|---|")
    for pname, pline in PROBES:
        r = run(exe, extra, pline)
        early = r["final_depth"] < 24
        emit("| %s | %d | **%d** | %.0f | %s | %s |" %
             (pname, r["depth_at_probe"], r["final_depth"], r["after_probe_ms"], r["bm"],
              ("**YES**" if early else "no")))
    emit("")

emit("## Verdict")
emit("")
emit("| question | answer |")
emit("|---|---|")
emit("| a setoption during a search stops it early | see the rows above |")
emit("| `isready` does not stop it (control) | see the isready row |")
emit("| the no-probe control reaches full depth | see the nothing row |")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")

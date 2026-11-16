#!/usr/bin/env python3
"""f5_pc20.py EXE OUT — is 08-F5 (the <=10 ms reserve-empty emergency branch) repaired on the PC build?

08-F5 on the base tree: with `time <= Move Overhead` the plan is "reserve empty" and the search collapses to a
legal-TT-move-or-1-ply-2000-node emergency answer, in ~0.15 ms. FABLE_TO_swarm_5 adds
`FORGE_FIX_HARD_LIMIT_EMERGENCY`, which touches exactly this path — so this is the most likely genuine repair.

Method: for wtime 10, 1 and 0, and for the same positions, record:
  - the wall time,
  - the bestmove,
  - the number of info depth lines and the deepest depth,
  - whether any `info string` from the fix appears.
Then compare with `go depth 1` (what the base tree's emergency branch produced 8 of 8 times) and with
`go movetime 50` (what a real search looks like).

CONTROLS (enforced, abort on failure):
  - `go movetime 50` must produce at least one info depth line (a real search exists to compare against);
  - every command must be waited out to `bestmove` (never a piped quit — seat 19's 19-F12);
  - the FEN must be accepted (seat 21's 21-F2).
"""
import subprocess
import sys

import chess

exe, outpath = sys.argv[1:3]

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
       ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
       ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
       ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
       ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

FENS = [
    "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1",
    "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8",
    "8/6k1/3p4/3P2PP/4KP2/4N3/8/8 w - - 0 1",
]
GOS = ["go wtime 10 btime 10", "go wtime 1 btime 1", "go wtime 0 btime 0", "go depth 1", "go movetime 50"]


def one(exe, fen, go):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def sync():
        send("isready")
        out = []
        while True:
            l = p.stdout.readline()
            if not l:
                raise EOFError
            out.append(l.rstrip("\n"))
            if l.startswith("readyok"):
                return out

    send("uci")
    while not p.stdout.readline().startswith("uciok"):
        pass
    for n, v in S14:
        send("setoption name %s value %s" % (n, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    pre = sync()
    if any("invalid FEN" in l for l in pre):
        return None
    import time
    t0 = time.monotonic()
    send(go)
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise EOFError
        l = l.rstrip("\n")
        lines.append(l)
        if l.startswith("bestmove"):
            break
    wall = (time.monotonic() - t0) * 1000.0
    sync()
    send("quit")
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()
    depths = []
    for l in lines:
        if l.startswith("info depth"):
            try:
                depths.append(int(l.split()[2]))
            except (IndexError, ValueError):
                pass
    return {"wall": wall, "bestmove": lines[-1].split()[1], "ndepth": len(depths),
            "maxdepth": max(depths) if depths else None,
            "strings": [l for l in lines if l.startswith("info string")]}


out = []


def emit(s):
    out.append(s)
    print(s)


emit("## 08-F5 on the PC build under PC20 (Threads 1) — is the reserve-empty emergency branch repaired?")
emit("")
emit("| fen | go | wall ms | bestmove | info depth lines | deepest | info string |")
emit("|---|---|---|---|---|---|---|")

# control: a real search must show info depth lines
ctrl = one(exe, FENS[0], "go movetime 50")
if ctrl is None:
    raise SystemExit("CONTROL FAILED: the FEN was refused")
if ctrl["ndepth"] == 0:
    raise SystemExit("CONTROL FAILED: `go movetime 50` produced no info depth line, so 'no depth lines' below "
                     "would be meaningless")

for fen in FENS:
    for go in GOS:
        r = one(exe, fen, go)
        if r is None:
            raise SystemExit("CONTROL FAILED: engine refused %r" % fen)
        emit("| %s | %s | %.2f | %s | %d | %s | %s |" %
             (fen[:30], go, r["wall"], r["bestmove"], r["ndepth"],
              r["maxdepth"] if r["maxdepth"] is not None else "-",
              ("; ".join(x.replace("|", "/") for x in r["strings"])[:60]) or "-"))

emit("")
emit("### reading")
emit("- On the BASE tree, `wtime 10/1/0` gave an answer in ~0.15 ms equal to the `go depth 1` answer 8 of 8 times,")
emit("  with 1 info depth line (the emergency ply) or none at all.")
emit("- If the PC build now searches to a real depth on `wtime 10`, the emergency branch is repaired.")
emit("- If it still answers in ~0.2 ms at depth 1, the fix did not change this path.")

with open(outpath, "w") as fh:
    fh.write("\n".join(out) + "\n")

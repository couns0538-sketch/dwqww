#!/usr/bin/env python3
"""plant_check.py OUT — THE PLANT for the 0-of-60 result in volatility_rate.py.

Why this file exists: seat 19 grepped volatility_rate.py for a planted case and found none. My 0-of-60 (no
mate-involved target among 60 full-material boards) was therefore "not shown" rather than measured: a harness that
simply CANNOT SEE a deep mate would report exactly the same 0 of 60. This plant closes that gap.

What it does — the plant must exercise the SAME failure mode, not a different one:
  1. take a position KNOWN to behave the way the finding describes (a cp score at the clocked depth, a mate at the
     deeper reference);
  2. run it through the identical code path as volatility_rate.py: `search(CLOCK)` for the score at depth D, then
     `search("go depth D+4")` for the deeper score, then the same classification;
  3. require the harness to report it as MATE_APPEARED — a miss means the harness is blind and the 0-of-60 is void;
  4. **verify the mate is REAL**: replay the deeper search's PV move by move with python-chess and require it to end
     in checkmate. This is what separates "the engine printed the word mate" from "there is a mate".

A plant that only checked for the token `mate` would pass on a lying engine. This one requires the mate to be
playable to the end.

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys

import chess

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
CLOCK = "go wtime 6000 btime 6000 winc 60 binc 60"
PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

# The plant board: a K+R vs K ending whose mate needs more plies than the clocked depth buys. It is a PLANT, i.e.
# chosen because it must trigger the effect, not sampled. Its mate is verified below by replaying the PV.
PLANT_FEN = "8/8/6k1/Q7/1P4PP/1K3P2/8/8 b - - 0 1"


def search(fen, go, want_pv=False):
    """Identical to volatility_rate.py's search()."""
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def sync():
        send("isready")
        got = []
        while True:
            l = p.stdout.readline()
            if not l:
                raise EOFError
            got.append(l.rstrip("\n"))
            if l.startswith("readyok"):
                return got

    send("uci")
    while not p.stdout.readline().startswith("uciok"):
        pass
    for k, v in PC20:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    pre = sync()
    if any("invalid FEN" in l for l in pre):
        return {"err": "refused"}
    import threading
    t0 = __import__("time").monotonic()
    send(go)
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

    threading.Thread(target=rd, daemon=True).start()
    ok = done.wait(180.0)
    if not ok:
        p.kill()
        return {"timeout": True}
    sync()
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    depth = 0
    score = None
    pv = []
    for l in lines:
        if l.startswith("info depth"):
            t = l.split()
            try:
                depth = max(depth, int(t[2]))
                if "score" in t:
                    si = t.index("score")
                    score = "%s %s" % (t[si + 1], t[si + 2])
                    pv = t[t.index("pv") + 1:] if "pv" in t else []
            except (IndexError, ValueError):
                pass
    return {"depth": depth, "score": score, "pv": pv, "bm": lines[-1].split()[1]}


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## THE PLANT for the 0-of-60 — PC r15, PC20, Threads 1")
emit("")
emit("Board: `%s`" % PLANT_FEN)
emit("")
emit("### step 1 — the clocked search (same call as volatility_rate.py)")
r1 = search(PLANT_FEN, CLOCK)
if r1.get("timeout") or "err" in r1:
    raise SystemExit("PLANT FAILED to run: %r" % r1)
emit("| depth D | score at D |")
emit("|---|---|")
emit("| %d | **%s** |" % (r1["depth"], r1["score"]))

emit("")
emit("### step 2 — the deeper reference, depth D+4 (same call)")
D4 = r1["depth"] + 4
r2 = search(PLANT_FEN, "go depth %d" % D4)
if r2.get("timeout") or "err" in r2:
    raise SystemExit("PLANT reference failed: %r" % r2)
emit("| requested | reached | score at D+4 | pv length |")
emit("|---|---|---|---|")
emit("| depth %d | %d | **%s** | %d |" % (D4, r2["depth"], r2["score"], len(r2["pv"])))

emit("")
emit("### step 3 — the classification volatility_rate.py applies")
kind = "other"
if r1["score"] and r1["score"].startswith("cp") and r2["score"] and r2["score"].startswith("mate"):
    kind = "mate_appeared"

emit("| clocked score | deeper score | classification | required |")
emit("|---|---|---|---|")
emit("| %s | %s | **%s** | mate_appeared |" % (r1["score"], r2["score"], kind))

emit("")
emit("### step 4 — is the mate REAL? replay the deeper PV to checkmate")
b = chess.Board(PLANT_FEN)
replay = []
ok = True
for u in r2["pv"]:
    try:
        m = chess.Move.from_uci(u)
    except Exception:
        ok = False
        replay.append("%s UNPARSABLE" % u)
        break
    if m not in b.legal_moves:
        ok = False
        replay.append("%s ILLEGAL" % u)
        break
    b.push(m)
    replay.append(u)
mate_reached = ok and b.is_checkmate()
emit("| pv replayed | ended in checkmate? |")
emit("|---|---|")
emit("| %s | **%s** |" % (" ".join(replay) if replay else "(no pv)", "YES" if mate_reached else "NO"))

emit("")
emit("## VERDICT")
emit("")
plant_ok = (kind == "mate_appeared") and mate_reached
emit("| question | answer |")
emit("|---|---|")
emit("| did the harness classify the plant as MATE_APPEARED? | **%s** |" % ("YES" if kind == "mate_appeared" else "NO — HARNESS IS BLIND"))
emit("| is the mate real (PV replayed to checkmate)? | **%s** |" % ("YES" if mate_reached else "NO"))
emit("| does the plant pass? | **%s** |" % ("PASS" if plant_ok else "FAIL"))
emit("")
if plant_ok:
    emit("**The 0-of-60 is a MEASURED zero, not an unplanted one.** The same code path that reported zero")
    emit("mate-involved targets among 60 full-material boards does report a mate-involved target when one is present,")
    emit("and the mate it reports is playable to checkmate. So the zero reflects the positions, not the harness.")
else:
    emit("**PLANT FAILED — the 0-of-60 must be read as 'not shown', not as a measurement.**")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")

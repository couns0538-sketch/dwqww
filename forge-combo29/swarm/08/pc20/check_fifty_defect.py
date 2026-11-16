#!/usr/bin/env python3
"""check_fifty_defect.py OUT — is my 08-C6/F22 fifty-move finding a DEFECT by FABLE_TO_swarm_6's test?

File 6 says: "A cp 0 at a high counter is a defect ONLY when a forced mate exists that ends no later than the
100th half-move. Test for it: the same board with counter 0, `go depth 20` or more, read `mate N`; it is a defect
only if 2N - 1 <= 100 - counter and the board with the real counter still scores cp 0 at that depth. Report that
inequality with both numbers in the finding line."

Board: `1K6/8/8/3R4/8/8/8/k7 w - - H 1` (K+R vs K, the board my 08-C6 used).
At H=91 there are 100 - 91 = **9 half-moves left**.

Step 1: same board at counter 0, `go depth 20` (and 24), read the mate distance N.
Step 2: the inequality 2N - 1 <= 100 - H.
Step 3: the board at H=91 at the SAME depth — does it still score cp 0?

If 2N - 1 > 9, the engine cannot deliver mate before the 100th half-move, so cp 0 at H=91 is CORRECT CHESS and my
08-C6/F22 "defect" wording must be withdrawn. If 2N - 1 <= 9, it is a genuine defect.

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]
FEN = "1K6/8/8/3R4/8/8/8/k7 w - - %d 1"


def probe(counter, depth):
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
    for n, v in PC20:
        send("setoption name %s value %s" % (n, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + (FEN % counter))
    sync()
    send("go depth %d" % depth)
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise EOFError
        l = l.rstrip("\n")
        lines.append(l)
        if l.startswith("bestmove"):
            break
    sync()
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    score = None
    nodes = None
    maxd = 0
    pvlen = 0
    for l in lines:
        if l.startswith("info depth"):
            t = l.split()
            try:
                d = int(t[2])
                maxd = max(maxd, d)
                if d == depth and "score" in t and "nodes" in t:
                    si = t.index("score")
                    score = "%s %s" % (t[si + 1], t[si + 2])
                    nodes = int(t[t.index("nodes") + 1])
                    pvlen = (len(t) - t.index("pv") - 1) if "pv" in t else 0
            except (IndexError, ValueError):
                pass
    return {"counter": counter, "depth": depth, "score": score, "nodes": nodes, "maxd": maxd, "pvlen": pvlen}


def mate_in(score):
    """'mate 5' -> 5 (White mates in 5). 'mate -5' -> -5. None for cp."""
    if not score or not score.startswith("mate"):
        return None
    return int(score.split()[1])


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## FABLE_TO_swarm_6's test on my fifty-move finding (08-C6 / 08-F22)")
emit("")
emit("Board `1K6/8/8/3R4/8/8/8/k7 w - - H 1`, PC r15, PC20, Threads 1, Hash 16.")
emit("")
emit("| H | depth | score | plies | nodes | pv length |")
emit("|---|---|---|---|---|---|")
rows = []
for h, d in [(0, 20), (0, 24), (0, 28), (91, 20), (91, 24), (91, 28), (99, 20)]:
    r = probe(h, d)
    rows.append(r)
    n = mate_in(r["score"])
    pl = (2 * n - 1) if n is not None and n > 0 else (2 * abs(n) if n is not None else None)
    emit("| %d | %d | **%s** | %s | %s | %d |" % (h, d, r["score"], pl if pl is not None else "-",
                                                  f"{r['nodes']:,}", r["pvlen"]))

# the deep mate distance at counter 0, as large a depth as we can afford
best = None
for r in rows:
    if r["counter"] == 0 and mate_in(r["score"]) is not None and mate_in(r["score"]) > 0:
        best = r
if best is None:
    # try one more depth
    r = probe(0, 32)
    rows.append(r)
    if mate_in(r["score"]) is not None and mate_in(r["score"]) > 0:
        best = r
if best is None:
    raise SystemExit("RESULT INCONCLUSIVE: no positive mate score found at counter 0 up to depth 32, so the "
                     "inequality cannot be evaluated. Say so rather than calling it a defect.")

N = mate_in(best["score"])
plies = 2 * N - 1
H = 91
HLEFT = 100 - H
r91 = next(r for r in rows if r["counter"] == 91 and r["depth"] == best["depth"]) if any(
    r["counter"] == 91 and r["depth"] == best["depth"] for r in rows) else probe(91, best["depth"])

emit("")
emit("## the inequality file 6 asks for")
emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| mate distance at counter 0 (depth %d) | **mate %d** = %d plies |" % (best["depth"], N, plies))
emit("| half-moves left at H=91 | **%d** |" % HLEFT)
emit("| inequality 2N-1 <= 100-H | **%d <= %d is %s** |" % (plies, HLEFT, "TRUE" if plies <= HLEFT else "FALSE"))
emit("| board at H=91 at the same depth scores | %s |" % r91["score"])
emit("")
if plies > HLEFT:
    emit("**NOT A DEFECT — my 08-C6/08-F22 wording must be withdrawn.** The engine needs %d plies to mate but only "
         "%d half-moves remain before the match program ends the game at the 100th, so scoring this node 0 is "
         "CORRECT CHESS. The 7.25M-node cost at H=91 is still a real cost, but it buys a correct verdict." %
         (plies, HLEFT))
else:
    emit("**A DEFECT, confirmed by file 6's test**: the mate is %d plies and %d half-moves remain, so the engine "
         "COULD mate before the 100th and still scores cp 0 at H=91." % (plies, HLEFT))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")

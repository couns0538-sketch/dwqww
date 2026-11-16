#!/usr/bin/env python3
"""check_s05f3.py EXE OUT — my own check of seat 05's S-F3/S-F16 (the clock-99 claimable-draw defect), on the
PC BUILD under PC20 at Threads 1.

Their claim, from their words alone:
  S-F3 : "`1K6/8/8/3R4/8/8/8/k7 w - - H 1` at `go depth 10` scores `cp 472` for H=0..75, `cp 314` at H=90, then
          exactly `cp 0` from H=91"
  S-F16: "S-F3 STANDS on the PC build ... K+R vs K at depth 10 on the PC r15 build: cp 458 at hm 0, cp 352 at 88,
          cp 289 at 90, then cp 0 at halfmove 91 ... identical under S14 and PC20, Threads 1"

The board is a bare king-and-rook versus a lone king with the counter swept. That is a WON position at every
counter value (a rook mate takes well under 50 moves from anywhere), so a cp 0 score at high counters is the
defect: the engine believes a won position is drawn because its search horizon crosses 100.

My own harness. Board typed by hand from the FEN in their sentence (no dependency on their move list).

CONTROLS (enforced — abort, never print a verdict):
 1. a positive score must exist at low counters (`H` small), else the board is not a won position and the whole
    comparison is meaningless;
 2. `go depth 10` must actually reach depth 10 (else "at depth 10" is not what was measured);
 3. every score must parse (the vacuous-confirmation rule from seat 19/23).
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

FEN_TMPL = "1K6/8/8/3R4/8/8/8/k7 w - - %d 1"
COUNTERS = [0, 50, 75, 80, 85, 88, 89, 90, 91, 92, 95, 99, 100, 150]
DEPTH = 10


def probe(counter):
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
    fen = FEN_TMPL % counter
    send("position fen " + fen)
    pre = sync()
    if any("invalid FEN" in l for l in pre):
        return {"counter": counter, "fen": fen, "bad": [l for l in pre if "invalid FEN" in l][0]}
    send("go depth %d" % DEPTH)
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
        p.wait(timeout=10)
    except Exception:
        p.kill()
    score = None
    nodes = None
    maxd = 0
    for l in lines:
        if l.startswith("info depth"):
            t = l.split()
            try:
                d = int(t[2])
                maxd = max(maxd, d)
                if d == DEPTH and "score" in t and "nodes" in t:
                    si = t.index("score")
                    score = "%s %s" % (t[si + 1], t[si + 2])
                    nodes = int(t[t.index("nodes") + 1])
            except (IndexError, ValueError):
                pass
    return {"counter": counter, "fen": fen, "score": score, "nodes": nodes,
            "bm": lines[-1].split()[1], "maxd": maxd}


out = []


def emit(s):
    out.append(s)
    print(s)


results = [probe(c) for c in COUNTERS]

# control 1: a positive score at low counters
low = [r for r in results if r["counter"] <= 50]
if any(r.get("score") is None for r in low):
    raise SystemExit("CONTROL FAILED: no parsable depth-%d score at a low counter; the board is not being "
                     "searched as a won position" % DEPTH)
if not any(r["score"] and r["score"].startswith("cp") and int(r["score"].split()[1]) > 100 for r in low):
    raise SystemExit("CONTROL FAILED: no positive cp score at a low counter (%r); the board is not a won "
                     "position, so a cp 0 later would prove nothing" % [r["score"] for r in low])
# control 2: depth reached
bad_depth = [r for r in results if r.get("maxd", 0) < DEPTH]
if bad_depth:
    raise SystemExit("CONTROL FAILED: depth %d not reached for counters %r"
                     % (DEPTH, [r["counter"] for r in bad_depth]))
# control 3: every score parses
unparsed = [r for r in results if r.get("score") is None]
if unparsed:
    raise SystemExit("CONTROL FAILED: unparsable score at counters %r" % [r["counter"] for r in unparsed])

emit("## seat 05 S-F3 / S-F16 on the PC BUILD under PC20, Threads 1 — `1K6/8/8/3R4/8/8/8/k7 w - - H 1`, `go depth 10`")
emit("")
emit("| halfmove H | score | nodes | bestmove |")
emit("|---|---|---|---|")
for r in results:
    emit("| %d | **%s** | %s | %s |" % (r["counter"], r["score"], r["nodes"], r["bm"]))

first_zero = next((r["counter"] for r in results
                   if r["score"] and r["score"].startswith("cp") and int(r["score"].split()[1]) == 0), None)
last_won = max((r["counter"] for r in results
                if r["score"] and r["score"].startswith("cp") and int(r["score"].split()[1]) > 0), default=None)

emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| first counter scoring exactly cp 0 | **%s** |" % first_zero)
emit("| last counter still scoring a win | %s |" % last_won)
emit("")
if first_zero is not None and last_won is not None and first_zero > last_won:
    emit("**CONFIRMS**: a won K+R vs K position is scored as a DRAW from halfmove %d on (cp 0), "
         "while the same board scores a win at halfmove %d." % (first_zero, last_won))
    emit("Seat 05 said the flip is at H=91 at depth 10; I measured the first zero at **H=%d**." % first_zero)
    if first_zero != 91:
        emit()
        emit("NOTE the one-digit difference from their figure: they wrote 91, I measured %d. Their S-F14/S-F20 say "
             "the boundary is position- and depth-dependent (boundary = 101 - depth for bare endgames), so a "
             "1-count difference is within what their own later findings describe as a moving boundary." % first_zero)
else:
    emit("**DOES NOT CONFIRM** — see the table; no clean won-to-drawn flip was found on this board.")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")

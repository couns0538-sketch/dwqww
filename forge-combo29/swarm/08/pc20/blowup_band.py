#!/usr/bin/env python3
"""blowup_band.py EXE OUT — is the 7.25M-node cost at H=91 a single counter or a BAND?

08-C6 found the fifty-move score floor at H=91 and, beside it, 7,251,835 nodes at H=91 against 14,470 at H=0.
A single point could be an artefact of one search; a BAND of counters where the node count explodes means the
defect costs time in any long game approaching the limit, not just at one counter value.

Runs H = 85..99 every step on the same won board, PC20, Threads 1, `go depth 10`, one fresh process per counter.
Records score and nodes for each.

CONTROLS: the same three as 08-C6 (a won score at low counters, depth 10 reached, every score parses), plus a
fourth: the node counts must not all be equal (else the harness is reading one cached value).
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
DEPTH = 10


def probe(counter):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
    for n, v in PC20:
        send("setoption name %s value %s" % (n, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + (FEN % counter))
    sync()
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
    score = nodes = None
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
    return {"h": counter, "score": score, "nodes": nodes, "maxd": maxd}


out = []


def emit(s):
    out.append(s)
    print(s)


rows = [probe(h) for h in range(85, 100)]

# controls
if any(r["score"] is None for r in rows):
    raise SystemExit("CONTROL FAILED: a counter produced no parsable depth-%d score" % DEPTH)
if any(r["maxd"] < DEPTH for r in rows):
    raise SystemExit("CONTROL FAILED: depth %d not reached at some counter" % DEPTH)
nodes = [r["nodes"] for r in rows]
if len(set(nodes)) == 1:
    raise SystemExit("CONTROL FAILED: every node count identical (%r) — the harness is not reading a fresh "
                     "search" % nodes[0])
# the won-at-low-counter control, measured separately so this script is self-contained
won = probe(0)
if not won["score"] or not won["score"].startswith("cp") or int(won["score"].split()[1]) <= 100:
    raise SystemExit("CONTROL FAILED: H=0 does not score a win (%r); a later cp 0 would prove nothing"
                     % won["score"])

med = sorted(nodes)[len(nodes) // 2]
emit("## The fifty-move cliff, H = 85..99 every step — PC r15, PC20, Threads 1, `go depth 10`")
emit("")
emit("| H | score | nodes | x median nodes | wall-free node cost |")
emit("|---|---|---|---|---|")
for r in rows:
    emit("| %d | **%s** | %s | %.1fx | %s |" % (r["h"], r["score"], f"{r['nodes']:,}",
                                                r["nodes"] / med if med else 0,
                                                "BLOW-UP" if r["nodes"] > 20 * med else ""))
emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| median nodes over the band | %s |" % f"{med:,}")
emit("| largest | %s at H=%d |" % (f"{max(nodes):,}", rows[nodes.index(max(nodes))]["h"]))
emit("| smallest | %s at H=%d |" % (f"{min(nodes):,}", rows[nodes.index(min(nodes))]["h"]))
hi = [r["h"] for r in rows if r["nodes"] > 20 * med]
emit("| counters more than 20x the median (>%s nodes) | %s |" % (f"{20 * med:,}", hi if hi else "none"))
zero = [r["h"] for r in rows if r["score"].startswith("cp") and int(r["score"].split()[1]) == 0]
emit("| counters scoring cp 0 | %s |" % zero)
emit("| H=0 control (must be won) | %s |" % won["score"])

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")

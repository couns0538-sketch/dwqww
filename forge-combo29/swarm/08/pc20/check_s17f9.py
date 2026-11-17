#!/usr/bin/env python3
"""check_s17f9.py OUT — my own check of seat 17's S-F9, with a plant.

Their claim:
"NOT a fault, TT resize verified: `Hash` 1/8/32/512/2048 MB changes only the pressure, not the answer — hashfull
 440 / 58 / 10 / 0 / 0 and nodes 53652 then 52591 four times, bestmove identical."

This is a NEGATIVE ("the answer does not change"), so it needs a plant: the same harness must be able to report a
CHANGE when one exists. Plant: compare two positions that must give different bestmoves; if the harness reports them
as identical, it cannot see a change and the zero is void.

Also checks the half they quote that is directly relevant to my area: does the NODE COUNT stay constant across hash
sizes (their claim: 53,652 then 52,591 four times)? A changing node count with an unchanged move would mean the
search DID change, just not the choice.

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
        ("MateAlphaGuard", "true"), ("OwnBook", "false")]
HASHES = [1, 8, 32, 512, 2048]
FEN_A = "r2q1rk1/ppp2ppp/3bbn2/3p4/8/1PN1PN2/PBPPBPPP/R2Q1RK1 w - - 0 10"
FEN_B = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"
DEPTH = 14


def run(fen, hash_mb):
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
    for k, v in PC20 + [("Threads", "1")]:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("setoption name Hash value %d" % hash_mb)
    sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    sync()
    send("go depth %d" % DEPTH)
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            break
        lines.append(l.rstrip("\n"))
        if l.startswith("bestmove"):
            break
    sync()
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    nodes = hashfull = None
    for l in lines:
        if l.startswith("info depth"):
            t = l.split()
            try:
                if "nodes" in t:
                    nodes = int(t[t.index("nodes") + 1])
                if "hashfull" in t:
                    hashfull = int(t[t.index("hashfull") + 1])
            except (IndexError, ValueError):
                pass
    return {"bm": lines[-1].split()[1], "nodes": nodes, "hashfull": hashfull}


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## seat 17 S-F9 — does Hash size change the ANSWER? (and the node count?)")
emit("")
emit("PC r15, PC20, Threads 1, `go depth %d`, position A." % DEPTH)
emit("")
emit("| Hash MB | bestmove | nodes | hashfull |")
emit("|---|---|---|---|")
rowsA = []
for h in HASHES:
    r = run(FEN_A, h)
    rowsA.append(r)
    emit("| %d | %s | %s | %s |" % (h, r["bm"], f"{r['nodes']:,}" if r["nodes"] is not None else "-", r["hashfull"]))

bm_set = {r["bm"] for r in rowsA}
nodes_set = {r["nodes"] for r in rowsA}
emit("")
emit("### THE PLANT — a different position must give a different answer")
rB = run(FEN_B, 32)
emit("")
emit("| position | bestmove | nodes |")
emit("|---|---|---|")
emit("| A (as above, Hash 32) | %s | %s |" % (rowsA[2]["bm"], f"{rowsA[2]['nodes']:,}"))
emit("| B (different position) | %s | %s |" % (rB["bm"], f"{rB['nodes']:,}"))
plant = (rB["bm"] != rowsA[2]["bm"])
emit("")
emit("**PLANT: the harness %s a changed bestmove, so its 'unchanged' verdicts are meaningful.**" %
     ("CAN report" if plant else "CANNOT report"))

emit("")
emit("## The claim, tested")
emit("")
emit("| question | answer |")
emit("|---|---|")
emit("| bestmove identical across all five Hash sizes | **%s** (%s) |" % ("YES" if len(bm_set) == 1 else "NO",
                                                                        ", ".join(sorted(bm_set))))
emit("| hashfull varies with size (the pressure) | **%s** |" % ", ".join(str(r["hashfull"]) for r in rowsA))
emit("| node count varies with size | **%s** |" % (("NO — identical %s" % f"{list(nodes_set)[0]:,}")
                                                   if len(nodes_set) == 1 else
                                                   ("YES — " + ", ".join(f"{n:,}" for n in sorted(x for x in nodes_set if x is not None)))))
emit("")
if plant and len(bm_set) == 1:
    emit("**CONFIRMS**: the answer does not change across Hash 1..2048 MB while hashfull does, so a TT resize changes")
    emit("the pressure and not the choice. Node counts: see the row above — if they are identical, the search is")
    emit("bit-identical; if they differ, the search changed but not the choice, which is the weaker statement and I say which.")
else:
    emit("**NOT CONFIRMED** — see the table (plant=%s, distinct moves=%d)." % (plant, len(bm_set)))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")

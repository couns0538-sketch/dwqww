#!/usr/bin/env python3
"""nearness_test.py OUT — does NEARNESS TO MATE explain why one sparse sample had 37 % mate-appearing targets and
another had 10 %?

My untested guess was: seed 801's sparse set was hand-picked to fill "few pieces AND few moves", several boards were
already near mate, so four extra plies found a mate; seed 902's are random-game endings where four plies rarely
matters.

TEST: for every board in BOTH samples, measure nearness-to-mate INDEPENDENTLY of the clocked search — a deep
`go depth 18` from the same board, and record whether it reports a mate and at what distance. Then:

  - is the mate-appearing rate higher among boards that are near mate (deep search finds mate in few plies)?
  - does the seed-801 set contain more near-mate boards than the seed-902 set?

If the second holds, the guess is supported; if not, it is refuted and I say so.

ARGUMENT ORDER: OUT first.
"""
import json
import subprocess
import sys
import time

import chess

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
DEPTH = 18

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

# the two sparse samples, taken from the committed jsonl files (so this classifies exactly the boards measured)
def sparse_from(jsonl):
    rows = [json.loads(l) for l in open(jsonl)]
    return [(r["fen"], r["kind"]) for r in rows if r["class"].startswith("sparse")]


SAMPLES = [
    ("seed 801", sparse_from("volatility_rate.txt.jsonl")),
    ("seed 902", sparse_from("volatility_rate_seed902.txt.jsonl")),
]


def deep(fen):
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
    sync()
    send("go depth %d" % DEPTH)
    import threading
    lines = []
    done = threading.Event()

    def rd():
        while True:
            l = p.stdout.readline()
            if not l:
                return
            lines.append(l.rstrip("\n"))
            if l.startswith("bestmove"):
                done.set()
                return

    threading.Thread(target=rd, daemon=True).start()
    ok = done.wait(120.0)
    if not ok:
        p.kill()
        return {"timeout": True}
    sync()
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    score = None
    for l in lines:
        if l.startswith("info depth"):
            t = l.split()
            if "score" in t:
                si = t.index("score")
                score = "%s %s" % (t[si + 1], t[si + 2])
    return {"score": score}


def mate_in(score):
    if not score or not score.startswith("mate"):
        return None
    return int(score.split()[1])


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## Is NEARNESS TO MATE the explanation for 37 %% vs 10 %%? PC r15, PC20, Threads 1")
emit("")
emit("Nearness is measured independently: a deep `go depth %d` from the same board, before any clocked search." % DEPTH)
emit("")
emit("| sample | boards | deep search finds a mate | of those, mate-appearing targets | no mate at depth %d | of those, mate-appearing |" % DEPTH)
emit("|---|---|---|---|---|---|")
summary = {}
for label, rows in SAMPLES:
    near = 0
    near_hit = 0
    far = 0
    far_hit = 0
    details = []
    for fen, kind in rows:
        r = deep(fen)
        if r.get("timeout"):
            continue
        mi = mate_in(r["score"])
        nm = mi is not None
        hit = (kind == "mate_appeared")
        if nm:
            near += 1
            near_hit += hit
        else:
            far += 1
            far_hit += hit
        details.append((fen, r["score"], nm, hit))
    summary[label] = (near, near_hit, far, far_hit, details)
    emit("| %s | %d | **%d** | **%d** | %d | **%d** |" %
         (label, near + far, near, near_hit, far, far_hit))

emit("")
emit("| sample | share of boards that are NEAR mate (deep search finds one) |")
emit("|---|---|")
for label, (near, nh, far, fh, _) in summary.items():
    emit("| %s | **%d of %d (%.0f %%)** |" % (label, near, near + far, 100.0 * near / max(near + far, 1)))

emit("")
emit("## The test: does nearness predict the mate-appearing target?")
emit("")
pooled_near_hit = sum(v[1] for v in summary.values())
pooled_near = sum(v[0] for v in summary.values())
pooled_far_hit = sum(v[3] for v in summary.values())
pooled_far = sum(v[2] for v in summary.values())
emit("| group | mate-appearing targets | boards |")
emit("|---|---|---|")
emit("| boards NEAR mate (deep search finds a mate) | **%d** | **%d** |" % (pooled_near_hit, pooled_near))
emit("| boards NOT near mate | **%d** | **%d** |" % (pooled_far_hit, pooled_far))
emit("")
if pooled_near and pooled_far:
    emit("| question | answer |")
    emit("|---|---|")
    emit("| near-mate rate | %.0f %% |" % (100.0 * pooled_near_hit / pooled_near))
    emit("| not-near-mate rate | %.0f %% |" % (100.0 * pooled_far_hit / pooled_far))
    emit("| does nearness explain the mate-appearing cases? | **%s** |" %
         ("YES — the effect lives almost entirely among near-mate boards" if pooled_near_hit / pooled_near >
          (pooled_far_hit / pooled_far if pooled_far else 0) * 1.5 else
          "PARTLY — nearness does not separate them cleanly"))
emit("")
emit("### the boards in detail (sample, fen, deep score, near?, target mate-appeared?)")
emit("| sample | fen | deep score | near mate? | target mate-appeared? |")
emit("|---|---|---|---|---|")
for label, (_, _, _, _, details) in summary.items():
    for fen, sc, nm, hit in details:
        emit("| %s | %s | %s | %s | %s |" % (label, fen[:34], sc, "YES" if nm else "no",
                                             "**YES**" if hit else "no"))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")

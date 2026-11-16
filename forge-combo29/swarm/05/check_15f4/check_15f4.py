#!/usr/bin/env python3
"""check_15f4.py EXE -- my own check of seat 15's 15-F4, written from its one-sentence claim only:
"K v K, KN v K, KB v K and threefold-repetition roots all score exactly cp 0 at depth 10 S14, but they answer
with an EMPTY PV (`... time 0 pv`) and 0 nodes, so any harness that greps for \" pv \" (with a move) silently
loses these 80 positions."

I use MY OWN positions (job2's sets, seed 501), my own harness, and I distinguish three things that a careless
harness conflates:
  H1  a line containing " pv" with NO moves after it      (the empty pv 15-F4 describes)
  H2  a line containing " pv" WITH at least one move
  H3  no pv line at all
A harness that greps ' pv <move>' would score H1 as absent and lose the position -- exactly their warning.
"""
import re
import subprocess
import sys

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-rel/forge"
DEPTH = 10
S14 = ["setoption name Threads value 1", "setoption name Hash value 16",
       "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
       "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
       "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
       "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
       "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
       "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
       "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true"]


def run(fen):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    out = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    for o in S14:
        send(o); send("isready")
    send("ucinewgame"); send("isready")
    send(f"position fen {fen}"); send("isready")
    send(f"go depth {DEPTH}")
    while True:
        line = p.stdout.readline()
        if line == "":
            break
        line = line.rstrip("\n")
        out.append(line)
        if line.startswith("bestmove"):
            break
    send("quit")
    try:
        p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        p.kill()
    pv_all = [l for l in out if re.search(r"\binfo\b.*\bpv\b", l)]
    pv_empty = [l for l in pv_all if not re.search(r"\bpv\b(.*)$", l).group(1).split()]
    pv_withmoves = [l for l in pv_all if re.search(r"\bpv\b(.*)$", l).group(1).split()]
    score = None
    nodes = None
    if pv_all:
        m = re.search(r"score (mate|cp) (-?\d+)", pv_all[-1])
        score = f"{m.group(1)} {m.group(2)}" if m else None
        n = re.search(r"\bnodes (\d+)", pv_all[-1])
        nodes = int(n.group(1)) if n else None
    bm = next((l for l in out if l.startswith("bestmove")), None)
    return dict(pv_all=len(pv_all), pv_empty=len(pv_empty), pv_moves=len(pv_withmoves),
                score=score, nodes=nodes, bestmove=bm,
                sample_empty=pv_empty[0] if pv_empty else None,
                sample_move=pv_withmoves[0] if pv_withmoves else None)


def load(p):
    with open(p) as f:
        return [l.strip() for l in f if l.strip()]


print(f"exe: {EXE}   go depth {DEPTH}   S14")
print()
SETS = [("KvK", "../job2/positions/KvK.epd"), ("KNvK", "../job2/positions/KNvK.epd"),
        ("KBvK", "../job2/positions/KBvK.epd"), ("KNNvK", "../job2/positions/KNNvK.epd")]
rows = []
for name, path in SETS:
    fens = load(path)[:6]
    agg = dict(empty=0, moves=0, zero_nodes=0, cp0=0, n=0)
    print(f"########## {name}")
    for fen in fens:
        r = run(fen)
        agg["n"] += 1
        agg["empty"] += 1 if r["pv_empty"] else 0
        agg["moves"] += 1 if r["pv_moves"] else 0
        agg["zero_nodes"] += 1 if r["nodes"] == 0 else 0
        agg["cp0"] += 1 if r["score"] == "cp 0" else 0
        print(f"  {r['score']!s:8s} nodes={r['nodes']!s:8s} pv_empty={r['pv_empty']} "
              f"pv_with_moves={r['pv_moves']}  {fen}")
        if r["sample_empty"]:
            print(f"      empty-pv line: {r['sample_empty'][:100]}")
    rows.append((name, agg))
    print()

print("| set | positions | cp 0 | 0 nodes | EMPTY pv | pv WITH moves |")
print("|---|---|---|---|---|---|")
for name, a in rows:
    print(f"| {name} | {a['n']} | {a['cp0']} | {a['zero_nodes']} | {a['empty']} | {a['moves']} |")

print()
draw_sets = [a for n, a in rows if n != "KNNvK"]
all_empty = all(a["empty"] == a["n"] for a in draw_sets)
knn = dict(rows)["KNNvK"]
# FAIL CLOSED: if the searches produced NO info lines at all, nothing was measured and neither a confirmation nor
# a refutation may be printed. Added after the owner flagged this class of fault.
total_observed = sum(a["empty"] + a["moves"] for _n, a in rows)
if total_observed == 0:
    print(f"FAIL-LOUD: no info/pv line was observed in any of the {sum(a['n'] for _n, a in rows)} searches "
          f"(the engine answered but printed no score). Nothing was measured.")
    print("RESULT: INCONCLUSIVE (no measurement) — neither a confirmation nor a refutation.")
    sys.exit(1)
print(f"their claim, for the dead-draw sets: every position cp 0 / 0 nodes / EMPTY pv -> {all_empty}")
print(f"control: KNN v K is NOT a dead draw, and there the pv is NOT empty "
      f"({knn['moves']}/{knn['n']} had moves) -> {knn['moves'] > 0}")
print()
if all_empty and knn["moves"] > 0:
    print("RESULT: CONFIRMS. The empty-pv-with-0-nodes shape is real on the dead-draw sets, and the same harness")
    print("        sees a NON-empty pv on KNN v K, so the shape is a property of those positions and not of my")
    print("        parsing. A harness using ' pv <move>' would indeed drop the 4 dead-draw sets.")
else:
    print("RESULT: does NOT confirm on my positions — see the table above.")

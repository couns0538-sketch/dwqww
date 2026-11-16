#!/usr/bin/env python3
"""Control for the job1 checker: prove it CAN report a difference and that both perfts
agree with published values.

Part A: published perft values for startpos and Kiwipete, engine and reference both.
Part B: the same comparison machinery on a deliberately WRONG engine number (one node
added to a single record); the checker must report exactly that one differing pair.
Usage: control.py EXE WORKDIR
"""
import subprocess
import sys

EXE = sys.argv[1]
WORK = sys.argv[2]

PUBLISHED = [
    ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
     {1: 20, 2: 400, 3: 8902, 4: 197281, 5: 4865609}),
    ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
     {1: 48, 2: 2039, 3: 97862, 4: 4085603}),
]

fens = [f for f, _ in PUBLISHED]
fen_file = WORK + "/control.fens"
with open(fen_file, "w") as f:
    f.write("\n".join(fens) + "\n")

out = []
out.append("## control A: published perft values\n")
out.append("| position | depth | published | engine | reference | both equal published |")
out.append("|---|---|---|---|---|---|")

subprocess.run(["python3", WORK + "/engine_perft.py", EXE, fen_file,
                WORK + "/control_engine.txt", "1,2,3,4,5", "300"], check=True,
               stdout=subprocess.DEVNULL)
subprocess.run(["python3", WORK + "/ref_perft.py", fen_file,
                WORK + "/control_ref.txt", "1,2,3,4,5"], check=True,
               stdout=subprocess.DEVNULL)


def load(p):
    d = {}
    for line in open(p):
        if line.startswith("#") or not line.strip():
            continue
        s = line.split()
        d[(int(s[0]), int(s[1]))] = s[2]
    return d


eng = load(WORK + "/control_engine.txt")
ref = load(WORK + "/control_ref.txt")
allok = True
for i, (fen, table) in enumerate(PUBLISHED):
    for d, want in table.items():
        e, r = eng.get((i, d)), ref.get((i, d))
        ok = (e == str(want)) and (r == str(want))
        allok &= ok
        out.append(f"| {i} | {d} | {want} | {e} | {r} | {'YES' if ok else 'NO'} |")
out.append(f"\ncontrol A verdict: {'PASS - both sides reproduce every published value' if allok else 'FAIL'}\n")

out.append("## control B: the checker must catch a planted wrong number\n")
with open(WORK + "/control_mutant.txt", "w") as f:
    first = True
    for line in open(WORK + "/control_engine.txt"):
        if line.startswith("#"):
            f.write(line)
            continue
        s = line.split()
        if first:
            s[2] = str(int(s[2]) + 1)   # one node added to the very first record
            first = False
        f.write(" ".join(s) + "\n")

res = subprocess.run(["python3", WORK + "/compare.py", WORK + "/control_mutant.txt",
                      WORK + "/control_ref.txt", fen_file, WORK + "/control_cmp.md"],
                     capture_output=True, text=True)
out.append("compare.py stdout on the mutant:\n```\n" + res.stdout.strip() + "\n```\n")
caught = "differing pairs 1" in res.stdout
out.append(f"control B verdict: {'PASS - exactly one differing pair reported' if caught else 'FAIL - the checker did not catch it'}\n")

text = "\n".join(out)
open(WORK + "/control.md", "w").write(text)
print(text)

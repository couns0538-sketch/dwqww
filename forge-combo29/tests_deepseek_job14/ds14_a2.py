#!/usr/bin/env python3
# A2/A3: repeat every one of the first N opening positions with a clocked search,
# in R fresh processes; compare bestmove/score/depth/nodes across runs.
import hashlib
import subprocess
import sys

def one_process(exe, fens, nodeclock, tc):
    answers = []
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    def send(line):
        p.stdin.write(line + "\n")
        p.stdin.flush()
    send("uci")
    while True:
        if p.stdout.readline().startswith("uciok"):
            break
    send(f"setoption name NodeClock value {nodeclock}")
    send("isready")
    while True:
        if p.stdout.readline().startswith("readyok"):
            break
    for fen in fens:
        send("ucinewgame")
        send("isready")
        while True:
            if p.stdout.readline().startswith("readyok"):
                break
        send(f"position fen {fen}")
        send(f"go {tc}")
        best = score = depth = nodes = None
        while True:
            line = p.stdout.readline()
            if line.startswith("bestmove"):
                best = line.split()[1]
                break
            if " depth " in line and " score " in line and " nodes " in line:
                t = line.split()
                try:
                    depth = int(t[t.index("depth") + 1])
                    i = t.index("score")
                    score = f"{t[i+1]} {t[i+2]}"
                    nodes = int(t[t.index("nodes") + 1])
                except (ValueError, IndexError):
                    pass
            elif " nodes " in line:
                t = line.split()
                try:
                    nodes = int(t[t.index("nodes") + 1])
                except (ValueError, IndexError):
                    pass
        answers.append(f"{fen}|{best}|{score}|{depth}|{nodes}")
    send("quit")
    p.wait(timeout=15)
    return answers

def main():
    exe, epd, n, nodeclock, runs, tc = (sys.argv[1], sys.argv[2], int(sys.argv[3]),
                                        int(sys.argv[4]), int(sys.argv[5]), sys.argv[6])
    fens = [l.strip() for l in open(epd, encoding="utf-8", errors="replace")][:n]
    all_runs = []
    for r in range(runs):
        a = one_process(exe, fens, nodeclock, tc)
        all_runs.append(a)
        h = hashlib.sha256("\n".join(a).encode()).hexdigest()
        print(f"run{r+1}: sha256={h}")
    ref = all_runs[0]
    diffs = 0
    for a in all_runs[1:]:
        for x, y in zip(ref, a):
            if x != y:
                diffs += 1
    if len(sys.argv) > 7 and int(sys.argv[7]):
        import json
        json.dump(all_runs, open(sys.argv[8], "w"))
    node_strs = [x.rsplit("|", 1)[1] for x in ref]
    nones = sum(1 for s in node_strs if s == "None")
    nodes = [int(s) for s in node_strs if s != "None"]
    print(f"comparisons: {len(all_runs)-1} extra run(s) vs run1; differing answers: {diffs} of {len(ref)}")
    print(f"node counts: n={len(nodes)} (no-info searches: {nones}) largest={max(nodes)} mean={sum(nodes)/len(nodes):.1f} smallest={min(nodes)}")

if __name__ == "__main__":
    main()

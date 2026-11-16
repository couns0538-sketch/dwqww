#!/usr/bin/env python3
"""Does perft vary warm vs cold? (rule from seat 10: two searches in one process share state.)

Perft is a pure tree walk with no TT use, so it should be identical warm and cold. This proves it
on the positions I actually measured, so my perft tables can be trusted warm or cold.
"""
import subprocess, sys
EXE=sys.argv[1]; FENS=sys.argv[2]
fens=[l.strip() for l in open(FENS) if l.strip()][:12]
def run(cmds):
    p=subprocess.Popen([EXE],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
    def send(s): p.stdin.write(s+"\n"); p.stdin.flush()
    send("uci")
    while p.stdout.readline().strip()!="uciok": pass
    out=[]
    for c in cmds:
        send(c)
        while True:
            l=p.stdout.readline().strip()
            if l.startswith("nodes "): out.append(int(l.split()[1])); break
            if l.startswith("bestmove"): raise SystemExit("FAIL: search answered while waiting for perft nodes")
    send("quit"); p.wait(); return out
ok=True
print("| position | cold (fresh process) | warm (3x same process) | last | identical |")
print("|---|---|---|---|---|")
for i,f in enumerate(fens):
    pos="position fen "+f
    cold=run([pos,"go perft 3"])[0]
    warm=run([pos,"go perft 3",pos,"go perft 3",pos,"go perft 3"])
    same=len(set(warm+[cold]))==1
    ok&=same
    print("| %d | %d | %s | %d | %s |"%(i,cold,warm,warm[-1],"YES" if same else "NO"))
print()
print("VERDICT:", "perft is warm/cold IDENTICAL on all sampled positions - my perft tables are valid either way" if ok else "PERFT VARIES WARM/COLD - my tables must be relabelled")

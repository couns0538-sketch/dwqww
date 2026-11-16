#!/usr/bin/env python3
"""Re-run the four honesty pins INTERACTIVELY (read to bestmove/nodes before sending quit).

Needed because the pipelined form `go ... / quit` can make an async search answer a fabricated
`bestmove` (seat 19's 19-F12). This script never closes stdin while a command is running.
"""
import subprocess, sys
EXE=sys.argv[1]
def run(cmd, token):
    p=subprocess.Popen([EXE],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
    def send(s): p.stdin.write(s+"\n"); p.stdin.flush()
    send("uci")
    while True:
        if p.stdout.readline().strip()=="uciok": break
    send("isready")
    while p.stdout.readline().strip()!="readyok": pass
    send(cmd)
    final=""
    while True:
        l=p.stdout.readline().strip()
        if l: final=l
        if token=="nodes" and l.startswith("nodes "):
            break
        if token=="bench" and "bench depth" in l:
            break
        if token=="bestmove" and l.startswith("bestmove"):
            break
    send("quit"); p.wait()
    return final
pins=[("bench 11","bench depth"),("bench 13","bench depth"),("bench 16","bench depth"),("go perft 5","nodes")]
want=[312866,862329,3024920,4865609]
ok=True
for (cmd,_t),w in zip(pins,want):
    line=run(cmd,"nodes" if "perft" in cmd else "bench")
    if "perft" in cmd:
        got=int(line.split()[1])
    else:
        parts=line.split()
        got=int(parts[parts.index("nodes")+1])
    match = got==w
    ok &= match
    print(f"{cmd:12s} got {got:9d} want {w:9d} {'MATCH' if match else 'MISMATCH'}")
    print(f"   raw: {line}")
print("ALL MATCH" if ok else "FAILED")

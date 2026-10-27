#!/usr/bin/env python3
"""Drive a Forge exe over UCI: bench depths + perft5 startpos + perft5 kiwipete. Waits for real output (no sleeps).
usage: uci_check.py <forge_exe> [--full]   (--full = bench 11 13 16 20 22; default 11 13 16)
Exit 0 only if every number matches the AL1 s198 lock reference."""
import subprocess, sys, re
REF_BENCH = {11: 312866, 13: 862329, 16: 3024920, 20: 12389307, 22: 34048354}
REF_PERFT = {"startpos": 4865609, "kiwipete": 193690690}
KIWI = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
exe = sys.argv[1]; depths = [11, 13, 16, 20, 22] if "--full" in sys.argv else [11, 13, 16]
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
def send(s): p.stdin.write(s + "\n"); p.stdin.flush()
def wait(pat):
    rx = re.compile(pat)
    for line in p.stdout:
        m = rx.search(line)
        if m: return m
    raise SystemExit("engine exited before matching " + pat)
send("uci"); wait(r"^uciok")
for o in ("Threads value 1", "Hash value 16", "OwnBook value false"): send("setoption name " + o)
send("isready"); wait(r"^readyok")
ok = True
for d in depths:
    send(f"bench {d}"); m = wait(rf"bench depth {d} nodes (\d+)")
    got = int(m.group(1)); good = got == REF_BENCH[d]; ok &= good
    print(f"bench d{d} nodes {got} ref {REF_BENCH[d]} {'OK' if good else 'FAIL'}", flush=True)
for name, pos in (("startpos", "position startpos"), ("kiwipete", "position fen " + KIWI)):
    send(pos); send("go perft 5"); m = wait(r"^nodes (\d+)")
    got = int(m.group(1)); good = got == REF_PERFT[name]; ok &= good
    print(f"perft5 {name} {got} ref {REF_PERFT[name]} {'OK' if good else 'FAIL'}", flush=True)
send("quit"); p.wait(timeout=30)
print("ALL OK" if ok else "MISMATCH"); sys.exit(0 if ok else 1)

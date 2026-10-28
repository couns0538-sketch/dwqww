#!/usr/bin/env python3
"""uci_check.py (AL1 s198 identity: bench d11/13/16/20/22, perft5 startpos + kiwipete) with extra options.
usage: uci_check_opt.py <forge_exe> [--full] [--set "Name=value" ...] [--expect-option "option name ... line"]
--set sends `setoption name Name value value` after the standard Threads 1 / Hash 16 / OwnBook false.
--expect-option requires that exact line in the `uci` answer (e.g. a new option advertised default false).
Exit 0 only if every number matches the AL1 s198 lock reference (and every expected option line is present)."""
import re
import subprocess
import sys

REF_BENCH = {11: 312866, 13: 862329, 16: 3024920, 20: 12389307, 22: 34048354}
REF_PERFT = {"startpos": 4865609, "kiwipete": 193690690}
KIWI = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"

args = sys.argv[1:]
exe = args[0]
depths = [11, 13, 16, 20, 22] if "--full" in args else [11, 13, 16]
sets, expects = [], []
i = 1
while i < len(args):
    if args[i] == "--set":
        sets.append(args[i + 1]); i += 2
    elif args[i] == "--expect-option":
        expects.append(args[i + 1]); i += 2
    else:
        i += 1
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)


def send(s):
    p.stdin.write(s + "\n"); p.stdin.flush()


def wait(pat, keep=None):
    rx = re.compile(pat)
    for line in p.stdout:
        if keep is not None:
            keep.append(line.rstrip("\n"))
        if line.startswith("info string invalid value"):
            raise SystemExit("engine rejected an option: " + line.strip())
        m = rx.search(line)
        if m:
            return m
    raise SystemExit("engine exited before matching " + pat)


ok = True
uci_lines = []
send("uci"); wait(r"^uciok", uci_lines)
for line in expects:
    good = line in uci_lines; ok &= good
    print(f"uci advertises '{line}' {'OK' if good else 'FAIL'}", flush=True)
for o in ("Threads value 1", "Hash value 16", "OwnBook value false"):
    send("setoption name " + o)
for s in sets:
    name, value = s.split("=", 1)
    send(f"setoption name {name} value {value}")
    print(f"setoption name {name} value {value}", flush=True)
send("isready"); wait(r"^readyok")
for d in depths:
    send(f"bench {d}"); m = wait(rf"bench depth {d} nodes (\d+) time (\d+) nps (\d+)")
    got = int(m.group(1)); good = got == REF_BENCH[d]; ok &= good
    print(f"bench d{d} nodes {got} ref {REF_BENCH[d]} {'OK' if good else 'FAIL'} (time {m.group(2)} ms)", flush=True)
for name, pos in (("startpos", "position startpos"), ("kiwipete", "position fen " + KIWI)):
    send(pos); send("go perft 5"); m = wait(r"^nodes (\d+)")
    got = int(m.group(1)); good = got == REF_PERFT[name]; ok &= good
    print(f"perft5 {name} {got} ref {REF_PERFT[name]} {'OK' if good else 'FAIL'}", flush=True)
send("quit"); p.wait(timeout=30)
print("ALL OK" if ok else "MISMATCH"); sys.exit(0 if ok else 1)

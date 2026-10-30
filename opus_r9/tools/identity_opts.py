#!/usr/bin/env python3
"""R7 J3: the AL1 s198 lock identity (opus_round1/ci/uci_check.py) with UCI options set first.
usage: identity_opts.py <forge_exe> [--full] [--opt Name=value ...]
Sets Threads 1, Hash 16, OwnBook false, then every --opt, then checks bench 11 13 16 (--full: + 20 22) against the
lock node counts and perft 5 (startpos, kiwipete). A node-exact option must pass with the option on.
Exit 0 only if every number matches; waits for real output (no sleeps)."""
import re
import subprocess
import sys

REF_BENCH = {11: 312866, 13: 862329, 16: 3024920, 20: 12389307, 22: 34048354}
REF_PERFT = {"startpos": 4865609, "kiwipete": 193690690}
KIWI = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
exe = sys.argv[1]
depths = [11, 13, 16, 20, 22] if "--full" in sys.argv else [11, 13, 16]
opts = [sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == "--opt"]
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)


def send(s):
    p.stdin.write(s + "\n")
    p.stdin.flush()


def wait(pat):
    rx = re.compile(pat)
    for line in p.stdout:
        if "invalid value" in line or "Unknown" in line or "unknown" in line:
            raise SystemExit("engine rejected an option: " + line.strip())
        m = rx.search(line)
        if m:
            return m
    raise SystemExit("engine exited before matching " + pat)


send("uci")
wait(r"^uciok")
for o in ("Threads value 1", "Hash value 16", "OwnBook value false"):
    send("setoption name " + o)
for o in opts:
    name, value = o.split("=", 1)
    send(f"setoption name {name} value {value}")
send("isready")
wait(r"^readyok")
print("options:", ", ".join(opts) if opts else "(defaults)", flush=True)
ok = True
for d in depths:
    send(f"bench {d}")
    m = wait(rf"bench depth {d} nodes (\d+) time (\d+) nps (\d+)")
    got = int(m.group(1))
    good = got == REF_BENCH[d]
    ok &= good
    print(f"bench d{d} nodes {got} ref {REF_BENCH[d]} {'OK' if good else 'FAIL'} (nps {m.group(3)})", flush=True)
for name, pos in (("startpos", "position startpos"), ("kiwipete", "position fen " + KIWI)):
    send(pos)
    send("go perft 5")
    m = wait(r"^nodes (\d+)")
    got = int(m.group(1))
    good = got == REF_PERFT[name]
    ok &= good
    print(f"perft5 {name} {got} ref {REF_PERFT[name]} {'OK' if good else 'FAIL'}", flush=True)
send("quit")
p.wait(timeout=30)
print("ALL OK" if ok else "MISMATCH")
sys.exit(0 if ok else 1)

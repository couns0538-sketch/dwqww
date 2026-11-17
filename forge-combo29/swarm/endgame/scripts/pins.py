#!/usr/bin/env python3
"""Four honesty pins. `bench N` must arrive on STDIN as a UCI command.

Trap: bench prints ONE line, `info string bench depth D nodes N time T nps P`.
A reader waiting for a line that STARTS with "nodes" never returns -- that is a
hang, not a pass. And `go perft N` ends with a bare `nodes N` line and NO
bestmove, so it needs its own token.
"""
import subprocess, sys, json, re, time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fx/build/forge"
PINS = [("bench 11", 312866), ("bench 13", 862329), ("bench 16", 3024920)]

BENCH_RE = re.compile(r"^info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)")
PERFT_RE = re.compile(r"^nodes (\d+)")


def run(cmd, timeout=3600):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    out = []
    p.stdin.write("uci\n"); p.stdin.flush()
    while True:
        line = p.stdout.readline()
        if line == "":
            raise RuntimeError("closed stdout before uciok")
        out.append(line.rstrip("\n"))
        if line.strip() == "uciok":
            break
    t0 = time.time()
    p.stdin.write(cmd + "\n"); p.stdin.flush()
    got = None
    while time.time() - t0 < timeout:
        line = p.stdout.readline()
        if line == "":
            break
        line = line.rstrip("\n")
        out.append(line)
        m = BENCH_RE.match(line) or PERFT_RE.match(line)
        if m:
            got = int(m.group(2) if m.re is BENCH_RE else m.group(1))
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    p.wait(timeout=60)
    return got, out, time.time() - t0


results, ok = {}, True
if len(sys.argv) > 2 and sys.argv[2] == "perft":
    got, out, dt = run("go perft 5", 7200)
    match = got == 4865609
    results["go perft 5"] = {"want": 4865609, "got": got, "match": match,
                             "seconds": round(dt, 1),
                             "has_bestmove": any(l.startswith("bestmove") for l in out)}
    print(f"go perft 5: want 4865609 got {got} {'OK' if match else 'MISMATCH'} ({dt:.1f}s)")
    json.dump(results, open("/tmp/fx/pins_perft.json", "w"), indent=2)
    sys.exit(0 if match else 1)

for cmd, want in PINS:
    got, out, dt = run(cmd)
    match = got == want
    ok &= match
    results[cmd] = {"want": want, "got": got, "match": match, "seconds": round(dt, 2)}
    print(f"{cmd}: want {want} got {got} {'OK' if match else 'MISMATCH'} ({dt:.1f}s)", flush=True)
print("PINS " + ("PASS" if ok else "FAIL"))
json.dump(results, open("/tmp/fx/pins.json", "w"), indent=2)
sys.exit(0 if ok else 1)

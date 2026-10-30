"""R10: EvalFileHalfKA over UCI: load a net, ON bench stable, bad files rejected cleanly, off again = lock bench.
usage: python -I -B halfka_uci_check.py <forge.exe> <net.nnue> <scratch dir> [--depth 11]
Bad files are made in <scratch dir> from the net (truncated, wrong version, garbage, empty) plus a missing path;
each must answer "info string ERROR EvalFileHalfKA" and leave the lock's eval (bench == lock pin). Exit 0 if all hold."""
import os
import re
import subprocess
import sys

exe, net, scratch = sys.argv[1], sys.argv[2], sys.argv[3]
depth = int(sys.argv[sys.argv.index("--depth") + 1]) if "--depth" in sys.argv else 11
LOCK = {11: 312866, 13: 862329, 16: 3024920}
os.makedirs(scratch, exist_ok=True)
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)


def send(s):
    p.stdin.write(s + "\n")
    p.stdin.flush()


def until(prefix):
    out = []
    while True:
        line = p.stdout.readline()
        if not line:
            raise SystemExit("engine exited")
        out.append(line.rstrip("\r\n"))
        if out[-1].startswith(prefix):
            return out


def setopt(value):
    send(f"setoption name EvalFileHalfKA value {value}")
    send("isready")
    return [x for x in until("readyok") if x.startswith("info string")]


def bench():
    send(f"bench {depth}")
    for line in until("info string bench"):
        m = re.search(r"bench depth \d+ nodes (\d+)", line)
        if m:
            return int(m.group(1))


def make(name, data):
    path = os.path.join(scratch, name)
    with open(path, "wb") as f:
        f.write(data)
    return path


results = []
send("uci")
uci = until("uciok")
results.append(("option advertised", "option name EvalFileHalfKA type string default <empty>" in uci, ""))
for o in ("Threads 1", "Hash 16", "OwnBook false"):
    send(f"setoption name {o.split()[0]} value {o.split()[1]}")
base = bench()
results.append(("off = lock pin", base == LOCK.get(depth, base), f"bench {depth} {base}"))
info = setopt(net)
loaded = any("EvalFileHalfKA loaded" in x for x in info)
results.append(("net loads", loaded, info[0] if info else "no info line"))
on1, on2 = bench(), bench()
results.append(("ON bench stable and different from the lock", on1 == on2 and on1 != base, f"bench {depth} ON {on1} / {on2}"))
send("position startpos")
send("go depth 8")
best = [x for x in until("bestmove") if x.startswith("bestmove")][0]
results.append(("ON search returns a move", re.match(r"bestmove [a-h][1-8][a-h][1-8]", best) is not None, best))
data = open(net, "rb").read()
bad = {"truncated": make("bad_truncated.nnue", data[: len(data) // 3]),
       "wrong version": make("bad_version.nnue", bytes([data[0] ^ 0xFF]) + data[1:]),
       "garbage": make("bad_garbage.nnue", os.urandom(4096)),
       "empty": make("bad_empty.nnue", b""),
       "missing": os.path.join(scratch, "does_not_exist.nnue")}
for name, path in bad.items():
    info = setopt(path)
    err = [x for x in info if "ERROR EvalFileHalfKA" in x]
    b = bench()
    results.append((f"rejects {name}", bool(err) and b == base, (err[0][:150] if err else "no error line") + f"; bench {b}"))
setopt(net)
on3 = bench()
results.append(("reload after errors gives the same ON bench", on3 == on1, f"{on3}"))
info = setopt("<empty>")
results.append(("<empty> turns it off", bench() == base and any("off" in x for x in info), info[0] if info else ""))
send("quit")
p.wait(timeout=30)
for name, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
ok = all(r[1] for r in results)
print("HALFKA UCI CHECK OK" if ok else "HALFKA UCI CHECK FAILED")
sys.exit(0 if ok else 1)

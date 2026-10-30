"""R9: the R9Tune options of a Forge build, checked over UCI.
usage: python -I -B r9_option_check.py <forge.exe> [--depth 11] [--json out.json]
1. `uci` advertises R9Tune (check, default false) and every tunable as a spin option with its lock default.
2. With R9Tune off, setting a tunable away from its default leaves bench unchanged (the switch gates it).
3. With R9Tune on, every tunable is set to default + step (one at a time, back to default afterwards) and bench is
   run: a parameter that changes the node count is wired into the search; one that does not is listed (time-manager
   parameters cannot change a fixed-depth bench).
4. R9Tune off again restores the lock bench.
Exit 0 when 1, 2 and 4 hold (3 is reported)."""
import json
import re
import subprocess
import sys

exe = sys.argv[1]
depth = int(sys.argv[sys.argv.index("--depth") + 1]) if "--depth" in sys.argv else 11
out_json = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)


def send(s):
    p.stdin.write(s + "\n")
    p.stdin.flush()


def read_until(prefix):
    lines = []
    while True:
        line = p.stdout.readline()
        if not line:
            raise SystemExit("engine exited")
        line = line.rstrip("\r\n")
        lines.append(line)
        if line.startswith(prefix):
            return lines


def bench():
    send(f"bench {depth}")
    for line in read_until("info string bench"):
        m = re.search(r"info string bench depth \d+ nodes (\d+)", line)
        if m:
            return int(m.group(1))
    raise SystemExit("no bench line")


def setopt(name, value):
    send(f"setoption name {name} value {value}")
    send("isready")
    read_until("readyok")


send("uci")
lines = read_until("uciok")
opts = {}
r9 = None
for line in lines:
    m = re.match(r"option name (\S+) type spin default (-?\d+) min (-?\d+) max (-?\d+)$", line)
    if m:
        opts[m.group(1)] = tuple(int(x) for x in m.groups()[1:])
    if line == "option name R9Tune type check default false":
        r9 = True
for skip in ("Hash", "Threads"):  # the only one-word spin options that are not tunables
    opts.pop(skip, None)
setopt("Threads", 1)
setopt("Hash", 16)
setopt("OwnBook", "false")
base = bench()
ok_uci = r9 is True and len(opts) > 0
# 2: gate closed
name0, (d0, lo0, hi0) = next(iter(opts.items()))
setopt(name0, hi0 if d0 != hi0 else lo0)
gated = bench()
setopt(name0, d0)
ok_gate = gated == base
# 3: each tunable with R9Tune on
setopt("R9Tune", "true")
on_default = bench()
rows = []
probes = dict(a.split("=", 1) for a in (sys.argv[i + 1] for i, x in enumerate(sys.argv) if x == "--probe"))
for name, (d, lo, hi) in opts.items():
    step = max(1, abs(d) // 4) if d != 0 else max(1, (hi - lo) // 20)
    if name.startswith("Lmr") and d >= 1024 and d % 1024 == 0:
        step = 1024  # LMR adjustments are in 1/1024 ply and round to whole plies: probe with one ply
    v = d + step if d + step <= hi else d - step
    if probes:  # --probe Name=value ...: only these, at these values
        if name not in probes:
            continue
        v = int(probes[name])
    setopt(name, v)
    n = bench()
    setopt(name, d)
    rows.append({"name": name, "default": d, "min": lo, "max": hi, "tested": v, "nodes": n, "changes_bench": n != base})
    print(f"{name:26s} default {d:6d} -> {v:6d}: nodes {n:9d} {'changed' if n != base else 'SAME'}", flush=True)
back_on = bench()
# 4: switch off again
setopt(name0, hi0 if d0 != hi0 else lo0)
setopt("R9Tune", "false")
off_again = bench()
send("quit")
p.wait(timeout=30)
ok_restore = off_again == base and back_on == base and on_default == base
same = [r["name"] for r in rows if not r["changes_bench"]]
print(f"\nuci: R9Tune advertised {r9 is True}, {len(opts)} tunables advertised; bench {depth}: lock {base}, "
      f"R9Tune off + {name0} changed {gated}, R9Tune on at defaults {on_default}, on after the sweep {back_on}, "
      f"off again {off_again}")
print(f"{len(rows) - len(same)} of {len(rows)} tunables change bench {depth}; unchanged: {same}")
ok = ok_uci and ok_gate and ok_restore
print("R9 OPTIONS OK" if ok else "R9 OPTIONS FAIL")
if out_json:
    with open(out_json, "w", encoding="ascii", newline="\n") as f:
        json.dump({"exe": exe, "depth": depth, "lock_bench": base, "gated_bench": gated, "on_default_bench": on_default,
                   "off_again_bench": off_again, "tunables": rows, "ok": ok}, f, indent=1)
sys.exit(0 if ok else 1)

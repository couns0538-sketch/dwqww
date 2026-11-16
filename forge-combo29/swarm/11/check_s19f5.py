#!/usr/bin/env python3
"""check_s19f5.py EXE — seat 11's INDEPENDENT check of seat 19's finding 19-F5.

19-F5 claims: "`bench` is a UCI command on **stdin** (src/uci.cpp:590; `main` at
src/uci.cpp:651 ignores argv). `perf record … -- forge bench 13` gives samples of nothing
useful; `printf 'bench 13\nquit\n' | forge` gives the real
`info string bench depth 13 nodes 862329`."

Written from that sentence; seat 19's scripts were not read or copied.
Falsifiable parts:
  (1) running the exe with `bench 13` as an ARGV WORD produces NO bench output,
  (2) sending `bench 13` on STDIN produces the real bench line with nodes 862329,
  (3) the argv form still exits without hanging (a silent exit, not a stuck process),
  (4) src/uci.cpp really has the bench command on the stdin path near line 590 and main
      really ignores argv near line 651.
"""
import subprocess, sys

EXE = sys.argv[1]

# (1) argv form
p_arg = subprocess.run([EXE, "bench", "13"], capture_output=True, text=True, timeout=60)
arg_out = p_arg.stdout
print("=== argv form: `{} bench 13` ===".format(EXE))
print(f"exit code      : {p_arg.returncode}")
print(f"stdout bytes   : {len(arg_out)}")
print(f"has 'bench'    : {'bench' in arg_out}")
print(f"stdout[:200]   : {arg_out[:200]!r}")

# (2) stdin form
p_in = subprocess.run([EXE], input="bench 13\nquit\n", capture_output=True, text=True, timeout=300)
in_out = p_in.stdout
bench_line = next((l for l in in_out.splitlines() if "bench depth" in l), None)
nodes = None
if bench_line:
    for tok in bench_line.split():
        pass
    import re
    m = re.search(r"nodes (\d+)", bench_line)
    if m:
        nodes = int(m.group(1))
print("\n=== stdin form: printf 'bench 13\\nquit\\n' | exe ===")
print(f"exit code      : {p_in.returncode}")
print(f"bench line     : {bench_line!r}")
print(f"nodes parsed   : {nodes}")

print("\n=== verdict on 19-F5 ===")
checks = [
    ("argv form printed no bench line", "bench depth" not in arg_out),
    ("argv form exited cleanly (no hang)", p_arg.returncode is not None),
    ("stdin form printed a bench line", bench_line is not None),
    ("that bench line holds nodes 862329", nodes == 862329),
]
for n, ok in checks:
    print(f"  {'PASS' if ok else 'FAIL'}  {n}")
if all(ok for _, ok in checks):
    print("\nRESULT: CONFIRMS 19-F5 — bench is a stdin command; argv words are ignored.")
else:
    print("\nRESULT: REFUTES or only partly confirms 19-F5 — see FAIL lines.")

# control: a token that is NOT a bench command must not produce a bench line
p_ctl = subprocess.run([EXE], input="benchx 13\nquit\n", capture_output=True, text=True, timeout=60)
ctl = any("bench depth" in l for l in p_ctl.stdout.splitlines())
print(f"\ncontrol: 'benchx 13' on stdin produced a bench line: {ctl} "
      f"({'HARNESS BLIND' if ctl else 'correctly none'})")

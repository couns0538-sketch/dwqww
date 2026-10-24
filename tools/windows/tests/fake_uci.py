#!/usr/bin/env python3
"""Synthetic failure-gate fixture. Never an engine/NPS measurement."""
import json
import os
import pathlib
import sys

role = pathlib.Path(sys.argv[0]).stem
mode = os.environ.get("FORGE_FIXTURE_MODE", "bad_d11")
calls = os.environ["FORGE_FIXTURE_CALLS"]
with open(calls, "a", encoding="utf-8") as out:
    out.write(json.dumps({"role": role, "args": sys.argv[1:], "mode": mode}) + "\n")
if role.startswith("oracle"):
    if sys.stdin.readline().rstrip("\r\n") != "start":
        raise SystemExit(9)
    # Deliberately incomplete bytes exercise the pre-timing oracle failure gate.
    sys.stdout.buffer.write(b"SYNTHETIC_TRUNCATED_ORACLE_FIXTURE")
    print('{"kind":"nnue_million_oracle"}', file=sys.stderr)
    raise SystemExit(0)
nodes = {11: 308972, 13: 745494, 16: 2460422, 20: 11901452, 22: 31111774}
for line in sys.stdin:
    if line.strip() == "uci" and role == "int16" and mode == "inactive_backend":
        print("option name NnueInt16 type check default false", flush=True)
        print("uciok", flush=True)
    elif line.startswith("bench "):
        depth = int(line.split()[1])
        value = nodes[depth]
        if role == "stage1" and ((mode == "bad_d11" and depth == 11) or (mode == "bad_d13" and depth == 13)):
            value += 1
        if role == "stage1" and mode == "nonzero":
            print("SYNTHETIC fixture failure", file=sys.stderr, flush=True)
            raise SystemExit(7)
        print(f"info string bench depth {depth} nodes {value} time 1000 nps 1000000", flush=True)
    elif line.strip() == "quit":
        break

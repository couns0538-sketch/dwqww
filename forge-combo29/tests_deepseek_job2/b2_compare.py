#!/usr/bin/env python3
"""Job 2 B2: run the engine's `eval` over a FEN list and compare with the Python
reference evaluator.

With a v3 net active the engine answers `eval` with
  info string eval nnue_v3 <value>
(seen in src/uci.cpp, and confirmed by running it); the `hce ... nnue ... total ...`
form is the built-in-net path and is not what B2 asks for.

One engine process per net; each position gets `position fen ...` then `eval`.

Usage: b2_compare.py <net> <fens> <engine> <outdir> <tag>
Writes <outdir>/<tag>.engine.txt, <outdir>/<tag>.mine.txt, <outdir>/<tag>.compare.json
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deepseek_nnue_v3_ref as ref


def engine_values(engine, net, fens):
    """Returns (values, raw_lines). One process; the net is loaded once."""
    commands = [f"setoption name NNUEArchFile value {net}",
                "setoption name NNUEArch value true",
                "isready"]
    for fen in fens:
        commands.append(f"position fen {fen}")
        commands.append("eval")
    commands.append("quit")
    proc = subprocess.run([engine], input="\n".join(commands) + "\n",
                          capture_output=True, text=True, timeout=3600)
    values = []
    raw = []
    for line in proc.stdout.splitlines():
        if line.startswith("info string eval nnue_v3 "):
            raw.append(line)
            values.append(int(line.split()[-1]))
    if proc.stderr.strip():
        raise SystemExit(f"engine wrote to stderr: {proc.stderr[:500]}")
    return values, raw, proc.returncode


def main():
    net, fens_path, engine, outdir, tag = sys.argv[1:6]
    os.makedirs(outdir, exist_ok=True)
    with open(fens_path) as f:
        fens = [l.strip() for l in f if l.strip()]
    t0 = time.time()
    values, raw, code = engine_values(engine, net, fens)
    engine_s = time.time() - t0
    if len(values) != len(fens):
        raise SystemExit(f"engine returned {len(values)} values for {len(fens)} positions")

    netobj = ref.load_net(net)
    mine = []
    detail = []
    t1 = time.time()
    for fen in fens:
        cp, info = ref.evaluate(netobj, fen)
        mine.append(cp)
        detail.append(f"{cp} {info['ob']} {info['kb_w']} {info['fl_w']} {info['kb_b']} {info['fl_b']}")

    diffs = [(i, fens[i], mine[i], values[i]) for i in range(len(fens)) if mine[i] != values[i]]

    with open(f"{outdir}/{tag}.engine.txt", "w") as f:
        f.write("\n".join(str(v) for v in values) + "\n")
    with open(f"{outdir}/{tag}.engine-raw.txt", "w") as f:
        f.write("\n".join(raw) + "\n")
    with open(f"{outdir}/{tag}.mine.txt", "w") as f:
        f.write("\n".join(str(v) for v in mine) + "\n")
    with open(f"{outdir}/{tag}.mine-detail.txt", "w") as f:
        f.write("\n".join(detail) + "\n")

    summary = {
        "tag": tag, "net": net, "positions": len(fens),
        "engine_exit_code": code,
        "mismatches": len(diffs),
        "engine_seconds": round(engine_s, 1),
        "reference_seconds": round(time.time() - t1, 1),
        "first_mismatches": [{"index": i, "fen": fen, "mine": m, "engine": e} for i, fen, m, e in diffs[:10]],
        "cp_min": min(mine), "cp_max": max(mine),
    }
    with open(f"{outdir}/{tag}.compare.json", "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    print(json.dumps({k: v for k, v in summary.items() if k != "first_mismatches"}, sort_keys=True))
    if diffs:
        print(f"FIRST MISMATCH: {diffs[0]}")


if __name__ == "__main__":
    main()

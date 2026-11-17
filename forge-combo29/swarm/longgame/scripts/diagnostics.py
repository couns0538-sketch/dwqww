#!/usr/bin/env python3
"""Scan every stored arm for engine diagnostics on the `position` command.

A refused FEN or an illegal move is reported by the engine as an `info string` line, not in
the search output (brief rule 4), so the driver records those. This counts them across all
arms: a non-zero count would mean some fixture never reached the engine, manufacturing a pass.
"""
import json, sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evio import open_jsonl, EVID

ARMS = ["session", "fresh", "unc", "uncgame", "clearhash", "hashresend", "session_rev",
        "startpos_session", "startpos_fresh"]
n = 0
diags = []
for arm in ARMS:
    try:
        f = open_jsonl(arm)
    except FileNotFoundError:
        continue
    for line in f:
        r = json.loads(line)
        n += 1
        if r.get("i"):
            diags.append({"arm": arm, "game": r.get("g"), "ply": r.get("p"), "diag": r["i"]})

out = {"files": ARMS, "searches_scanned": n, "diagnostics_total": len(diags),
       "examples": diags[:20]}
json.dump(out, open(os.path.join(EVID, "diagnostics.json"), "w", encoding="utf-8"), indent=0)
print(f"scanned {n} stored plies across {len(ARMS)} arms; diagnostics found: {len(diags)}")

#!/usr/bin/env python3
"""state_after_refusal.py EXE OUTDIR : does a refused ep FEN leave the PREVIOUS position in place?

Seat 06's finding says only "REFUSED". If the refusal leaves the previous position (as FABLE_TO_swarm_1 says
for refused FENs in general), then a caller who ignores the info string searches the wrong position without
any error - that is the consequence worth stating.
Sequence: position startpos -> go perft 1 (must be 20) -> position fen <bad ep FEN> -> isready ->
go perft 1 (if still 20, the old position was kept) -> quit.
"""
import json
import os
import subprocess
import sys

EXE = sys.argv[1]
OUTDIR = sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)

BAD = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e6 0 1"     # seat 06's FEN
SENTINEL = "4k3/8/8/8/8/8/8/4K3 w - - 0 1"                            # perft 1 = 5, so "kept" is visible

CASES = [
    ("startpos_then_bad_ep", "position startpos", 20, BAD),
    ("sentinel_then_bad_ep", f"position fen {SENTINEL}", 5, BAD),
    # discriminating control: sentinel has 5 legal moves, the ACCEPTED ep FEN has 20, so an accepted
    # position must show 5 then 20 and a kept position would show 5 then 5
    ("sentinel_then_good_ep", f"position fen {SENTINEL}", 5,
     "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"),
]

records = []
for label, first_cmd, first_expect, second_fen in CASES:
    script = (f"uci\nisready\n{first_cmd}\nisready\ngo perft 1\nisready\n"
              f"position fen {second_fen}\nisready\ngo perft 1\nisready\nquit\n")
    proc = subprocess.run([EXE], input=script, capture_output=True, text=True, timeout=120)
    lines = proc.stdout.splitlines()
    nodes = [int(l.split()[-1]) for l in lines if l.startswith("nodes ")]
    refused = [l for l in lines if "invalid FEN" in l]
    rec = {"label": label, "first_expected": first_expect, "nodes_sequence": nodes,
           "refused_lines": refused, "exit_code": proc.returncode}
    rec["first_ok"] = bool(nodes) and nodes[0] == first_expect
    rec["second_is_old_position"] = bool(len(nodes) > 1 and nodes[1] == first_expect)
    records.append(rec)
    with open(os.path.join(OUTDIR, label + ".txt"), "w") as fh:
        fh.write(proc.stdout)
    print(f"{label:24s} first={nodes[:1]} second={nodes[1:2]} first_ok={rec['first_ok']} "
          f"second_is_old_position={rec['second_is_old_position']} refused={bool(refused)}")

with open(os.path.join(OUTDIR, "state_results.json"), "w") as fh:
    json.dump(records, fh, indent=1)

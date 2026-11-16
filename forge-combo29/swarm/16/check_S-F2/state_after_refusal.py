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
    # HARDENED (seat 19's broadcast): every command is acknowledged before the next is sent,
    # stdin is never closed and quit is only sent at the very end.
    import time as _time
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def _send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def _drain_to(tok, limit=60):
        got = []
        dl = _time.monotonic() + limit
        while _time.monotonic() < dl:
            l = p.stdout.readline()
            if not l:
                break
            got.append(l.rstrip("\n"))
            if l.strip() == tok:
                return got, True
        return got, False

    lines = []
    _send("uci"); a, _ = _drain_to("uciok"); lines += a
    _send("isready"); a, _ = _drain_to("readyok"); lines += a
    # perft answers with a `nodes N` line and NOT with readyok, so each command gets the right token:
    #   position/isready -> readyok ;  go perft -> "nodes" ; then isready -> readyok
    for cmd in (first_cmd, "isready", "go perft 1", "isready",
                f"position fen {second_fen}", "isready", "go perft 1", "isready"):
        _send(cmd)
        tok = "nodes" if cmd.startswith("go perft") else "readyok"
        a, _ = _drain_to(tok)
        lines += a
    _send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    proc = type("R", (), {"returncode": p.returncode})()
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

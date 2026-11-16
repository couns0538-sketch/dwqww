#!/usr/bin/env python3
"""check_ep.py EXE OUTDIR : my own harness for seat 06's finding S-F2 (ep-square FENs).

One fresh engine process per FEN. The whole script is written at once and the complete output is
parsed afterwards (no readline timing, so a buffered pipe cannot fool the harness):
    uci / isready / position fen <FEN> / isready / go perft 1 / isready / quit
A process that does not end within TIME_LIMIT seconds is killed and counted as a HANG.
python-chess's verdict and its legal move count are recorded beside the engine's.
"""
import json
import os
import subprocess
import sys
import time

import chess

EXE = sys.argv[1]
OUTDIR = sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)
TIME_LIMIT = 20

CASES = [
    # first one is exactly the FEN in seat 06's FINDINGS line
    ("startpos_e6_w", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e6 0 1"),
    ("startpos_e3_w", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e3 0 1"),
    ("startpos_e6_b", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq e6 0 1"),
    ("startpos_e3_b", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq e3 0 1"),
    ("legal_e3", "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"),
    ("legal_d6", "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2"),
    ("no_capturer", "rnbqkbnr/ppp1pppp/8/8/3pP3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"),
    ("no_pushed_pawn", "rnbqkbnr/ppp1pppp/8/8/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2"),
    ("file_a_empty", "4k3/8/8/8/8/8/8/4K3 w - a6 0 1"),
    ("rank1", "4k3/8/8/8/8/8/8/4K3 w - e1 0 1"),
    ("rank8", "4k3/8/8/8/8/8/8/4K3 w - e8 0 1"),
    ("uppercase", "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq E3 0 1"),
    ("no_ep_square", "rnb1kbnr/pppp1ppp/8/4p3/4P2q/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1"),
    ("legal_ep_capture", "rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 2"),
    # control: the same boards with the ep field removed, so "refused" cannot come from the board itself
    ("ctrl_no_ep", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
]


def run_one(label, fen):
    rec = {"label": label, "fen": fen}
    try:
        board = chess.Board(fen)
        rec["py_valid"] = True
        rec["py_perft1"] = board.legal_moves.count()
    except ValueError as exc:
        rec["py_valid"] = False
        rec["py_error"] = str(exc)[:120]
        rec["py_perft1"] = None

    script = ("uci\nisready\n"
              f"position fen {fen}\nisready\n"
              "go perft 1\nisready\nquit\n")
    t0 = time.monotonic()
    try:
        proc = subprocess.run([EXE], input=script, capture_output=True, text=True,
                              timeout=TIME_LIMIT)
        out = proc.stdout + proc.stderr
        hang = False
        rc = proc.returncode
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or "") + (exc.stderr or "")
        if isinstance(out, bytes):
            out = out.decode("utf-8", "replace")
        hang = True
        rc = None
    rec["hang"] = hang
    rec["exit_code"] = rc
    rec["seconds"] = round(time.monotonic() - t0, 3)
    lines = [l.rstrip("\n") for l in out.splitlines()]
    rec["refused"] = any("invalid FEN" in l for l in lines)
    rec["invalid_lines"] = [l for l in lines if "invalid FEN" in l]
    rec["nodes"] = [int(l.split()[-1]) for l in lines
                    if l.startswith("Nodes searched") or l.startswith("nodes ")]
    rec["engine_perft1"] = rec["nodes"][-1] if rec["nodes"] else None
    rec["bestmove"] = [l for l in lines if l.startswith("bestmove")]
    rec["sanitizer_lines"] = [l for l in lines if "runtime error" in l or "Sanitizer" in l]
    rec["has_name"] = any(l.startswith("id name") for l in lines)
    with open(os.path.join(OUTDIR, f"{label}.txt"), "w") as fh:
        fh.write(out)
        fh.write(f"\n--- exit_code {rc} hang {hang} seconds {rec['seconds']}\n")
    return rec


records = []
for label, fen in CASES:
    rec = run_one(label, fen)
    records.append(rec)
    print(f"{label:18s} refused={str(rec['refused']):5s} engine_perft1={str(rec['engine_perft1']):6s} "
          f"py_valid={str(rec['py_valid']):5s} py_perft1={str(rec['py_perft1']):6s} "
          f"hang={str(rec['hang']):5s} rc={rec['exit_code']}")

with open(os.path.join(OUTDIR, "results.json"), "w") as fh:
    json.dump(records, fh, indent=1)

refused = [r for r in records if r["refused"]]
accepted = [r for r in records if not r["refused"]]
mismatch = [r for r in accepted if r["engine_perft1"] != r["py_perft1"]]
print()
print(f"cases {len(records)}  refused {len(refused)}  accepted {len(accepted)}  "
      f"accepted_perft_mismatch {len(mismatch)}  hangs {sum(1 for r in records if r['hang'])}  "
      f"sanitizer_lines {sum(len(r['sanitizer_lines']) for r in records)}")
for r in refused:
    print("  REFUSED ", r["label"], "->", r["invalid_lines"][:1])
for r in mismatch:
    print("  MISMATCH", r["label"], "engine", r["engine_perft1"], "python", r["py_perft1"])

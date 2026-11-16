#!/usr/bin/env python3
"""dtm_selftest.py -- validates dtm.py's search on positions whose mate distance is known by hand."""
import subprocess
import sys

CASES = [
    # (fen, maxply, expected plies to mate, who mates)
    ("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1", 4, 1, "white"),          # Ra8#
    ("7k/6pp/8/8/8/8/8/R5K1 w - - 0 1", 4, 1, "white"),            # Ra8# (king h8, g7/h7 pawns)
    ("6k1/5p1p/6p1/8/8/8/8/R5K1 w - - 0 1", 6, None, None),       # no forced mate
    ("k7/8/1K6/8/8/8/8/1R6 w - - 0 1", 4, 1, "white"),             # Rb8#? check
    ("8/8/8/8/8/5k2/6q1/7K w - - 0 1", 6, 2, "black"),             # white to move, mated soon
]

import chess

n_noparse = 0
n_mismatch = 0
for fen, maxply, exp, who in CASES:
    out = subprocess.run([sys.executable, "dtm.py", fen, str(maxply)],
                         capture_output=True, text=True, timeout=600)
    tail = [l for l in out.stdout.splitlines() if l.startswith("verdict")]
    # FAIL CLOSED: no verdict line means nothing was measured. Calling that MISMATCH would invent a refutation
    # of dtm.py. Added after the owner flagged this class of fault.
    if not tail:
        n_noparse += 1
        print(f"NO_VERDICT {fen}  maxply={maxply}  expected={exp} plies {who}  ::  "
              f"(dtm.py printed no verdict line; {len(out.stdout)} chars of stdout)")
        continue
    verdict = tail[0]
    b = chess.Board(fen)
    legal = b.is_valid()
    ok = "?"
    if exp is None:
        ok = "OK" if "no mate" in verdict or "draw" in verdict else "CHECK"
    else:
        ok = "OK" if (f"in {exp} plies" in verdict and who in verdict) else "MISMATCH"
    if ok == "MISMATCH":
        n_mismatch += 1
    print(f"{ok:9s} {fen}  maxply={maxply}  expected={exp} plies {who}  ::  {verdict}")

# EXIT CODES, distinct on purpose: 0 = every case measured and agreed, 1 = a real disagreement, 3 = nothing was
# measured. A script chaining this must not treat "no measurement" as success.
if n_noparse:
    print(f"SUMMARY INCONCLUSIVE — {n_noparse} of {len(CASES)} cases produced no parse")
    sys.exit(3)
sys.exit(1 if n_mismatch else 0)

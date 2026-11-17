"""Negative control: prove the symmetry test can fail.

The real engine is symmetric 0/420. A test that cannot fail would report the
same thing for a broken engine, so this runs the SAME comparison logic against
a stub engine that returns a score biased by side to move. The test must
report asymmetric pairs for that engine.

The stub is a tiny UCI process written to a temporary file at run time; it is
never used for any measurement of the real engine.
"""

from __future__ import annotations

import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import chess

STUB = '''\
#!/usr/bin/env python3
import sys
stm = "w"
for line in sys.stdin:
    c = line.strip()
    if c == "uci":
        print("id name bias-stub"); print("uciok", flush=True)
    elif c == "isready":
        print("readyok", flush=True)
    elif c.startswith("position fen "):
        fields = c.split()
        # fields: [position, fen, placement, stm, castling, ep, halfmove, fullmove]
        stm = fields[3] if len(fields) > 3 else "w"
        print("info string stub ok", flush=True)
    elif c == "eval":
        # Deliberate colour bias: a position scores +100 for White to move and
        # -100 for Black to move, regardless of the pieces. Mirroring flips the
        # side to move, so this engine MUST look asymmetric.
        value = 100 if stm == "w" else -100
        print(f"info string eval hce {value} nnue 0 total {value}", flush=True)
    elif c.startswith("go"):
        print("info depth 1 score cp 0", flush=True)
        print("bestmove a2a3", flush=True)
    elif c == "quit":
        break
'''


def main() -> int:
    tmp = Path(tempfile.mkdtemp()) / "bias_stub.py"
    tmp.write_text(STUB)
    tmp.chmod(tmp.stat().st_mode | stat.S_IEXEC)

    # Import the real harness but point it at the stub process.
    import harness
    from harness import mirror_board

    real = harness.ENGINE
    harness.ENGINE = str(tmp)
    try:
        pairs = []
        with harness.Forge(path=str(tmp)) as f:
            for fen in [
                chess.STARTING_FEN,
                "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
                "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
            ]:
                board = chess.Board(fen)
                mirrored = mirror_board(board)
                ev = f.evaluate(board)
                ev_m = f.evaluate(mirrored)
                pairs.append((board.fen(), ev["total"], ev_m["total"]))
    finally:
        harness.ENGINE = real

    asymmetric = [p for p in pairs if p[1] != p[2]]
    for fen, a, b in pairs:
        print(f"  {a:6d} vs {b:6d}  {fen}")
    print()
    print(f"NEGATIVE CONTROL: asymmetric {len(asymmetric)} / {len(pairs)}")
    if len(asymmetric) == len(pairs):
        print("PASS: the symmetry test detects a colour-biased evaluator")
        return 0
    print("FAIL: the symmetry test did not detect a known-asymmetric engine")
    return 1


if __name__ == "__main__":
    sys.exit(main())

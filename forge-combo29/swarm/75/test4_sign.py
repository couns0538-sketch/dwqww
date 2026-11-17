"""Test 4: sign-convention control.

A checker that only tests MAGNITUDE passes a sign bug: |+900| == |-900|.
This test pins the sign down in three constructed boards and then proves the
check would catch a flipped sign, by running the same assertions against a stub
engine whose score sign is inverted.

Scores from this engine are side-to-move relative (established in
prove_harness.py: the same queen-up board scores +891 with White to move and
-832 with Black to move). That is the convention asserted here.
"""

from __future__ import annotations

import json
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import chess

from harness import Forge, mirror_board, parse_fen

# Board A: White is a queen up, White to move. Must be POSITIVE.
WHITE_UP = parse_fen("4k3/8/8/8/8/8/8/3QK3 w - - 0 1")
# Board B: Black is a queen up, Black to move. Must be POSITIVE (for the side
# that is up). This is the mirror of A and is built from it, not hand-typed.
BLACK_UP = mirror_board(WHITE_UP)
# Board C: White is a queen up but BLACK to move. Must be NEGATIVE.
WHITE_UP_BLACK_TO_MOVE = parse_fen("4k3/8/8/8/8/8/8/3QK3 b - - 0 1")
# Board D: the side-flipped pair partner for C.
BLACK_UP_WHITE_TO_MOVE = mirror_board(WHITE_UP_BLACK_TO_MOVE)


def main() -> int:
    results: list[dict] = []
    failures: list[str] = []

    with Forge() as f:
        cases = [
            ("A white queen up, White to move", WHITE_UP, +1),
            ("B black queen up, Black to move", BLACK_UP, +1),
            ("C white queen up, Black to move", WHITE_UP_BLACK_TO_MOVE, -1),
            ("D black queen up, White to move", BLACK_UP_WHITE_TO_MOVE, -1),
        ]
        for name, board, expected_sign in cases:
            ev = f.evaluate(board)
            actual_sign = (ev["total"] > 0) - (ev["total"] < 0)
            ok = actual_sign == expected_sign and abs(ev["total"]) > 100
            results.append({
                "case": name, "fen": board.fen(), "total": ev["total"],
                "hce": ev["hce"], "nnue": ev["nnue"],
                "expected_sign": expected_sign, "actual_sign": actual_sign, "pass": ok,
            })
            print(f"  {'PASS' if ok else 'FAIL'}  {name:36s} total={ev['total']:7d} "
                  f"expected_sign={expected_sign:+d}")
            if not ok:
                failures.append(name)

        # The pairs must also be exact negation of each other, which is a
        # stronger statement than "both have the right sign".
        ab = f.evaluate(WHITE_UP)["total"]
        bb = f.evaluate(BLACK_UP)["total"]
        pair_ok = ab == bb
        print(f"  {'PASS' if pair_ok else 'FAIL'}  A/B mirror equality             "
              f"{ab} == {bb}")
        if not pair_ok:
            failures.append("A/B mirror equality")

        # A magnitude-only checker would call these equal; the sign check must not.
        mag_a, mag_c = abs(f.evaluate(WHITE_UP)["total"]), abs(f.evaluate(WHITE_UP_BLACK_TO_MOVE)["total"])
        sign_matters = mag_a != 0 and f.evaluate(WHITE_UP)["total"] != f.evaluate(WHITE_UP_BLACK_TO_MOVE)["total"]
        print(f"  {'PASS' if sign_matters else 'FAIL'}  sign distinguishes A from C      "
              f"|A|={mag_a} |C|={mag_c} but A={f.evaluate(WHITE_UP)['total']} C={f.evaluate(WHITE_UP_BLACK_TO_MOVE)['total']}")
        if not sign_matters:
            failures.append("sign distinguishes A from C")

    proof = prove_check_catches_flipped_sign()
    results.append({"flipped_sign_control": proof})

    with open("out_sign.json", "w") as fh:
        json.dump({"cases": results, "failures": failures}, fh, indent=2)

    print()
    print(f"sign cases={len(results) - 1} failures={len(failures)}")
    if failures:
        print(f"SIGN FAILURES: {failures}")
        return 1
    return 0 if proof else 1


FLIP_STUB = '''\
#!/usr/bin/env python3
import sys
try:
    import chess
except ImportError:
    chess = None

fen = None
for line in sys.stdin:
    c = line.strip()
    if c == "uci":
        print("id name flip-stub"); print("uciok", flush=True)
    elif c == "isready":
        print("readyok", flush=True)
    elif c.startswith("position fen "):
        f = c.split()
        fen = " ".join(f[2:8]) if len(f) >= 8 else None
        print("info string stub ok", flush=True)
    elif c == "eval":
        # Compute the CORRECT side-to-move-relative sign from material, then
        # invert it. This is precisely the sign bug a magnitude-only checker
        # cannot see: the magnitude is always right, the sign is always wrong.
        board = chess.Board(fen)
        value = sum(
            (len(board.pieces(pt, chess.WHITE)) - len(board.pieces(pt, chess.BLACK))) * w
            for pt, w in [(1, 100), (2, 300), (3, 320), (4, 500), (5, 900)]
        )
        correct = value if board.turn == chess.WHITE else -value
        inverted = -correct
        magnitude = abs(inverted) or 50
        print(f"info string eval hce {magnitude if inverted > 0 else -magnitude} nnue 0 total {magnitude if inverted > 0 else -magnitude}", flush=True)
    elif c.startswith("go"):
        print("info depth 1 score cp 0", flush=True); print("bestmove a2a3", flush=True)
    elif c == "quit":
        break
'''


def prove_check_catches_flipped_sign() -> bool:
    """Run the same assertions against an engine whose sign is inverted."""
    tmp = Path(tempfile.mkdtemp()) / "flip_stub.py"
    tmp.write_text(FLIP_STUB)
    tmp.chmod(tmp.stat().st_mode | stat.S_IEXEC)

    print()
    print("negative control: engine with inverted sign convention")
    detected = 0
    checks = 0
    with Forge(path=str(tmp)) as f:
        for name, board, expected_sign in [
            ("A white queen up, White to move", WHITE_UP, +1),
            ("B black queen up, Black to move", BLACK_UP, +1),
            ("C white queen up, Black to move", WHITE_UP_BLACK_TO_MOVE, -1),
            ("D black queen up, White to move", BLACK_UP_WHITE_TO_MOVE, -1),
        ]:
            checks += 1
            ev = f.evaluate(board)
            actual = (ev["total"] > 0) - (ev["total"] < 0)
            ok = actual == expected_sign
            print(f"  {'detected' if not ok else 'MISSED'}  {name:36s} "
                  f"total={ev['total']:7d} expected_sign={expected_sign:+d}")
            if not ok:
                detected += 1
    print(f"flipped-sign control: detected {detected} / {checks}")
    if detected == checks:
        print("PASS: the sign check catches an inverted sign convention")
        return True
    print("FAIL: an inverted sign convention slipped past the check")
    return False


if __name__ == "__main__":
    sys.exit(main())

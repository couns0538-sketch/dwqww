#!/usr/bin/env python3
"""check_legal_move.py PROBE

Compares repetition_probe-style output from legal_move_probe.cpp with python-chess.
Asserts every line parses and that has_legal_move == (legal_count > 0) internally too,
so a missing or unparsable line can never pass as agreement.
"""
import subprocess
import sys

import chess


def main():
    probe = sys.argv[1]
    out = subprocess.run([probe, "60", "701"], capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"FAIL probe exit {out.returncode}: {out.stderr[:300]}")

    checked = disagree_count = 0
    problems = []
    for line in out.stdout.splitlines():
        if not line or line.startswith(("GAMES", "END", "REFUSED")):
            if line.startswith("REFUSED"):
                problems.append(f"engine REFUSED a FEN the test wanted: {line}")
            continue
        try:
            fen, rest = line.split(" | ")
            fields = dict(kv.split("=") for kv in rest.split())
            hm = int(fields["has_legal_move"])
            lc = int(fields["legal_count"])
        except Exception:
            problems.append(f"unparsable line: {line[:120]}")
            continue
        checked += 1
        board = chess.Board(fen)
        ref = board.legal_moves.count() > 0
        if bool(hm) != ref:
            disagree_count += 1
            problems.append(f"has_legal_move={hm} but python-chess says {ref} for {fen}")
        if bool(hm) != (lc > 0):
            disagree_count += 1
            problems.append(f"INTERNAL: has_legal_move={hm} vs legal_count={lc} for {fen}")

    if checked == 0:
        raise SystemExit("FAIL nothing was checked")
    print(f"positions checked: {checked}")
    for p in problems[:40]:
        print("  " + p)
    if disagree_count:
        print(f"\nRESULT: {disagree_count} disagreement(s)")
        sys.exit(1)
    print("RESULT: has_legal_move() agreed with python-chess and with legal_moves().size() "
          "on every position")


if __name__ == "__main__":
    main()

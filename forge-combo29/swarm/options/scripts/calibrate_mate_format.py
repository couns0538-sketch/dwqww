#!/usr/bin/env python3
"""Calibrate the engine's `score mate N` wire format against known distances.

The engine does not put plies on the wire. This script measures the mapping
instead of deriving it, because deriving it went wrong twice during this audit:

  * The format is produced by `format_score` (search.cpp:272-278) as
    `distance = MateValue - |score|`, `mate = (distance + 1) / 2`.
  * What `distance` means for a NEGATIVE score is not obvious, and a checker
    that assumes "side to move is the attacker" produces false alarms on every
    negative fixture.

Method: take fixtures whose true forced-mate distance is proved independently
by a full-width minimax (scripts/brute_mate.cpp), search each COLD with
`ucinewgame`, and record
    reported N, PV length, and whether the PV actually ends in checkmate.
Then assert a single mapping holds for every row of both signs, and print the
rows so the reader can check the claim rather than trust it.

The mapping this establishes is the one `audit.py` uses. If the assertions here
fail, the mate property in the audit is void and the script exits non-zero.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import driver  # noqa: E402


def brute(binary: str, fen: str, limit: int) -> tuple[int, int] | None:
    proc = subprocess.run([binary, fen, str(limit)], capture_output=True, text=True, timeout=600)
    out = proc.stdout.strip()
    if out.startswith("PROVED"):
        _, sign, plies = out.split()
        return int(sign), int(plies)
    return None


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: calibrate_mate_format.py <engine> <brute_mate> <mates30.json> [depth]")
        return 2
    engine_path, brute_path, mates_path = sys.argv[1:4]
    depth = int(sys.argv[4]) if len(sys.argv) > 4 else 12

    fixtures = json.load(open(mates_path))
    rows = []
    eng = driver.Engine(engine_path, timeout=180.0)
    for entry in fixtures:
        fen = entry["fen"]
        truth = brute(brute_path, fen, max(entry["mate_plies"], 7))
        if truth is None:
            print(f"SKIP  brute force did not confirm {fen}")
            continue
        # The fixture's own claim must match the brute force, or the corpus is
        # wrong and nothing downstream means anything.
        assert truth == (entry["sign"], entry["mate_plies"]), (entry, truth)

        eng.set_position(fen, cold=True)
        res = eng.go_depth(depth)
        board = chess.Board(fen)
        played = 0
        for uci in res["pv"]:
            try:
                move = chess.Move.from_uci(uci)
            except ValueError:
                break
            if move not in board.legal_moves:
                break
            board.push(move)
            played += 1
        rows.append({
            "fen": fen,
            "true_sign": truth[0],
            "true_plies": truth[1],
            "reported_mate": res["mate"],
            "pv_len": played,
            "pv_ends_in_mate": board.is_checkmate(),
            "pv_legal_prefix": played,
        })
    eng.quit()

    # Fit: for every row where the engine DID report a mate, the claimed MOVE
    # number must equal the number of the mover's move on which the PV mates,
    # and the PV must actually end in mate at that length.
    checked = 0
    failures = []
    for row in rows:
        mate = row["reported_mate"]
        if mate is None:
            continue
        n = abs(mate)
        checked += 1
        if row["true_sign"] > 0 and mate > 0:
            expect_plies = 2 * n - 1        # attacker's n-th move
        elif row["true_sign"] < 0 and mate < 0:
            expect_plies = 2 * n            # opponent's n-th move lands after
        else:
            failures.append({**row, "why": "sign disagrees with the true sign"})
            continue
        row["expect_plies_from_N"] = expect_plies
        if row["pv_len"] != expect_plies:
            failures.append({**row, "why": f"pv len {row['pv_len']} != {expect_plies}"})
        elif not row["pv_ends_in_mate"]:
            failures.append({**row, "why": "pv does not end in checkmate"})

    report = {
        "fixtures": len(rows),
        "mates_reported": checked,
        "mapping_consistent": len(failures) == 0,
        "failures": failures,
        "rows": rows,
    }
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence",
                       "mate-format-calibration.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(report, fh, indent=1)

    print(f"fixtures={len(rows)} mates_reported={checked} mapping_consistent={report['mapping_consistent']}")
    for row in rows[:12]:
        print(f"  true {row['true_sign']:+d}{row['true_plies']:2d}  "
              f"mate={row['reported_mate']}  pv_len={row['pv_len']:2d}  "
              f"ends_in_mate={row['pv_ends_in_mate']}  {row['fen'][:40]}")
    for f in failures[:10]:
        print(f"  FAIL {f['fen']} {f['why']}")
    return 0 if report["mapping_consistent"] and checked > 0 else 1


if __name__ == "__main__":
    sys.exit(main())

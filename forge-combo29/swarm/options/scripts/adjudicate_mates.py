#!/usr/bin/env python3
"""Adjudicate a flagged mate row: false claim, or truncated PV?

The audit's mate checker flags one verdict for two different things, and they are
not the same defect:

  FALSE CLAIM   the engine says `mate N` but the move it plays does not force
                mate within N plies. The score is a lie.
  TRUNCATED PV  the engine says `mate N`, the PV on the wire is shorter than N
                because publication stops early, but the move it plays DOES force
                mate within N plies. The score is true and the DISPLAY is short.

Calling the second a false mate would be a confident wrong answer, which is worse
than reporting nothing, so this settles each row with an independent full-width
proof instead of a convention:

  1. prove the root's shortest mate                       (true distance)
  2. prove the mate forced by the engine's OWN bestmove    (what it achieves),
     under the defender's longest resistance
  3. compare both against the claimed N

Verdicts:
  FALSE            no forced mate after the bestmove, or one at a LONGER distance
                   than claimed
  TRUE (truncated) forced mate at a distance <= claimed, PV published short
  TRUE (slow)      forced mate FASTER than claimed; a preference, not an error
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import driver  # noqa: E402


def prove(binary: str, fen: str, limit: int) -> tuple[int, int] | None:
    """(sign, plies) from full-width brute force, or None."""
    proc = subprocess.run([binary, fen, str(limit)], capture_output=True, text=True, timeout=1800)
    out = proc.stdout.strip()
    if not out.startswith("PROVED"):
        return None
    _, sign, plies = out.split()
    return int(sign), int(plies)


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: adjudicate_mates.py <audit.json> <brute_mate> <engine> [depth]")
        return 2
    audit_path, brute, engine_path = sys.argv[1], sys.argv[2], sys.argv[3]
    depth = int(sys.argv[4]) if len(sys.argv) > 4 else 12

    audit = json.load(open(audit_path))
    flagged = []
    for arm_name, arm in audit.items():
        if arm.get("error") or "mates" not in arm:
            continue
        for row in arm["mates"].get("unsound_rows", []):
            flagged.append({"arm": arm_name, **row})

    if not flagged:
        print("no flagged rows in this audit file")
        return 0

    engine = driver.Engine(engine_path, timeout=900.0)
    results = []
    seen = set()
    for row in flagged:
        key = (row["arm"], row["fen"])
        if key in seen:
            continue
        seen.add(key)
        fen = row["fen"]
        board = chess.Board(fen)

        engine.send("ucinewgame")
        engine.isready()
        if row["arm"] != "BASELINE":
            engine.set_option(row["arm"], "true")
        engine.set_position(fen, cold=True)
        live = engine.go_depth(depth)
        if row["arm"] != "BASELINE":
            engine.set_option(row["arm"], "false")

        bestmove, claimed, pv = live["bestmove"], live["mate"], live["pv"]
        root = prove(brute, fen, 15)

        child = board.copy()
        move = chess.Move.from_uci(bestmove) if bestmove not in ("0000",) else None
        legal = move is not None and move in child.legal_moves
        after = None
        if legal:
            child.push(move)
            proven_child = prove(brute, child.fen(), 15)
            # WHICH SIDE is the attacker after the bestmove depends on the SIGN
            # of the root claim, and getting this wrong is the trap that makes a
            # mate checker backwards on every negative score:
            #   claimed > 0  the root mover attacks, so after its move the
            #                DEFENDER is to move and is being mated -> sign < 0
            #   claimed < 0  the root mover is being mated, so its move is a
            #                DEFENCE and after it the ATTACKER is to move and
            #                has the mate -> sign > 0
            if proven_child is not None:
                want_sign = -1 if claimed > 0 else 1
                if proven_child[0] == want_sign:
                    # +1 because the mate needs the root move as well.
                    after = 1 + proven_child[1]

        n = abs(claimed) if claimed is not None else 0
        claimed_plies = (2 * n - 1 if claimed > 0 else 2 * n) if claimed else 0

        if not legal:
            verdict = f"FALSE: bestmove {bestmove} illegal"
        elif after is None:
            verdict = "FALSE: no forced mate after the bestmove"
        elif after > claimed_plies:
            verdict = f"FALSE: needs {after} plies, claimed {claimed_plies}"
        elif after < claimed_plies:
            verdict = f"TRUE (slow): mates in {after}, claimed {claimed_plies}"
        else:
            verdict = f"TRUE (truncated): mates in exactly {after} = claimed"

        results.append({
            "arm": row["arm"], "fen": fen, "claimed_mate": claimed,
            "claimed_plies": claimed_plies, "bestmove": bestmove,
            "root_shortest_plies": root[1] if root else None,
            "forced_after_bestmove_plies": after,
            "pv_len": len(pv), "pv": pv, "verdict": verdict,
        })
        print(f"{row['arm']:22s} {fen}")
        print(f"   claimed mate {claimed} ({claimed_plies} plies) via {bestmove}; "
              f"PV {len(pv)} moves; root shortest {root[1] if root else None} plies")
        print(f"   forced mate after bestmove: {after} plies")
        print(f"   -> {verdict}\n")
    engine.quit()

    out = os.path.join(os.path.dirname(os.path.abspath(audit_path)), "adjudication.json")
    with open(out, "w") as fh:
        json.dump({"rows": results}, fh, indent=1)
    false_count = sum(1 for r in results if r["verdict"].startswith("FALSE"))
    print(f"flagged={len(results)} FALSE={false_count} "
          f"true_but_flagged={len(results) - false_count}")
    print(f"written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

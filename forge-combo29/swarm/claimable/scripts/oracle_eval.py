#!/usr/bin/env python3
"""oracle_eval.py — how much does the lock's unsearched move actually cost, in cp?

The claimable root is the problem case: the lock returns 0 nodes, cp 0 and the head of the
generated move list. The candidate searches. "It differs" is not a cost, so this measures the
cost the way a game would:

  for each claimable root
      m_lock = the lock's move      m_cand = the candidate's move
      score each by searching the position AFTER the move with the CANDIDATE build at a
      deeper fixed depth, and express both from the ROOT side's point of view.

The oracle is a different search from either root search (it is one ply deeper on a child
position), and it is applied identically to both moves, so it cannot favour either arm.

LIMIT, stated because it bounds the claim: this is a fixed-depth engine evaluation, not a
tablebase or a game-theoretic value. It ranks the two moves; it does not prove either is
optimal.

Usage: oracle_eval.py
"""
import json
import sys

import chess

sys.path.insert(0, "/home/ubuntu/work")
from corpus_diff import Engine  # noqa: E402
from corpus_claimable import SEEDS  # noqa: E402

LOCK = "/home/ubuntu/work/lock/forge-combo29/build-rel/forge"
CAND = "/home/ubuntu/work/candV_A/forge-combo29/build-rel/forge"
ROOT_DEPTH = 12
ORACLE_DEPTH = 14
MATE = 100000


def to_int(score):
    """'cp 120' -> 120; 'mate 3' -> a large value that keeps ordering and sign."""
    if score is None:
        return None
    kind, val = score.split()
    val = int(val)
    if kind == "cp":
        return val
    return (MATE - abs(val)) if val > 0 else -(MATE - abs(val))


def main():
    lock, cand = Engine(LOCK), Engine(CAND)
    cases = []
    try:
        for seed in SEEDS:
            base = chess.Board(seed)
            if not base.is_valid():
                continue
            b = base.copy()
            b.halfmove_clock = 100
            resets = [m.uci() for m in b.legal_moves
                      if (b.piece_at(m.from_square)
                          and b.piece_at(m.from_square).piece_type == chess.PAWN)
                      or b.is_capture(m)]
            mates = []
            for m in b.legal_moves:
                c = b.copy()
                c.push(m)
                if c.is_checkmate():
                    mates.append(m.uci())
            if not resets or mates:
                continue                     # only the clock-reset arm, no mate
            pos = f"position fen {b.fen()}"
            lr = lock.search(pos, ROOT_DEPTH)
            cr = cand.search(pos, ROOT_DEPTH)
            row = {"fen": b.fen(), "lock": lr, "cand": cr}
            for tag, mv in (("lock", lr["bestmove"]), ("cand", cr["bestmove"])):
                try:
                    b.push_uci(mv)
                except ValueError:
                    row[f"{tag}_oracle"] = None
                    continue
                # search the child from the CHILD's side to move, then flip the sign so both
                # numbers are from the root side's point of view
                child = cand.search(f"position fen {b.fen()}", ORACLE_DEPTH)
                val = to_int(child["score"])
                row[f"{tag}_oracle"] = {"move": mv, "child_score": child["score"],
                                        "root_pov": None if val is None else -val,
                                        "child_nodes": child["nodes"]}
                b.pop()
            if row.get("lock_oracle") and row.get("cand_oracle"):
                row["delta_root_pov"] = row["cand_oracle"]["root_pov"] - row["lock_oracle"]["root_pov"]
            cases.append(row)
    finally:
        lock.quit()
        cand.quit()

    deltas = [c["delta_root_pov"] for c in cases if c.get("delta_root_pov") is not None]
    deltas.sort()
    n = len(deltas)
    summary = {
        "cases": n,
        "lock_nodes_zero": sum(1 for c in cases if (c["lock"]["nodes"] or 0) == 0),
        "cand_nodes_zero": sum(1 for c in cases if (c["cand"]["nodes"] or 0) == 0),
        "cand_better": sum(1 for d in deltas if d > 0),
        "equal": sum(1 for d in deltas if d == 0),
        "cand_worse": sum(1 for d in deltas if d < 0),
        "median_delta": deltas[n // 2] if n else None,
        "min_delta": deltas[0] if n else None,
        "max_delta": deltas[-1] if n else None,
        "mean_delta": round(sum(deltas) / n, 1) if n else None,
        "note": "delta_root_pov = candidate move's oracle score minus the lock move's, "
                "both from the root side's point of view; positive means the candidate's "
                "move is better by that many centipawns under a depth-14 engine oracle",
    }
    json.dump({"summary": summary, "cases": cases},
              open("/home/ubuntu/work/ev/oracle_eval.json", "w"), indent=2)
    print(json.dumps(summary, indent=2))
    print("\n--- per case:")
    for c in cases:
        d = c.get("delta_root_pov")
        print(f"  {c['fen'][:42]:44} lock {c['lock']['bestmove']:6} {str(c['lock']['score']):9}"
              f" -> {str(c['lock_oracle']['root_pov']):>10}   cand {c['cand']['bestmove']:6}"
              f" {str(c['cand']['score']):9} -> {str(c['cand_oracle']['root_pov']):>10}   delta {d}")


if __name__ == "__main__":
    main()

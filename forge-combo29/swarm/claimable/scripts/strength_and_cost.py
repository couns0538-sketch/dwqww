#!/usr/bin/env python3
"""strength_and_cost.py — what the fix buys and what it costs.

WHAT IT BUYS. At a claimable root the lock returns 0 nodes and the head of the generated move
list, unsearched. The candidate searches. To judge the move without a self-referential
reference, this uses the clock boundary itself: the SAME board at halfmove 99 is not claimable,
so the lock searches it normally. That gives an independent, same-build evaluation of the
position one counter-tick away — and the composed build's own hm=99 answer is a second one.

  reference_lo = lock at hm=99   (real search, no adjudication possible)
  reference_hi = candidate at hm=99 (same)
  lock_hm100   = the unsearched first generated move
  cand_hm100   = the searched answer

WHAT IT COSTS. Nodes and wall time spent at a claimable root, candidate vs lock, on the same
roots. The lock spends 0 nodes because it does not search at all; that is the cost side of
the same measurement, not a speed regression on ordinary positions.

Usage: strength_and_cost.py
"""
import json
import sys
import time

import chess

sys.path.insert(0, "/home/ubuntu/work")
from corpus_diff import Engine  # noqa: E402
from corpus_claimable import SEEDS  # noqa: E402

LOCK = "/home/ubuntu/work/lock/forge-combo29/build-rel/forge"
CAND = "/home/ubuntu/work/candV_A/forge-combo29/build-rel/forge"
DEPTH = 12


def timed_search(engine, pos, depth):
    t0 = time.monotonic()
    rec = engine.search(pos, depth)
    rec["ms"] = round((time.monotonic() - t0) * 1000, 1)
    return rec


def main():
    lock, cand = Engine(LOCK), Engine(CAND)
    rows = []
    try:
        for seed in SEEDS:
            base = chess.Board(seed)
            if not base.is_valid():
                continue
            for hm in (99, 100):
                b = base.copy()
                b.halfmove_clock = hm
                pos = f"position fen {b.fen()}"
                lock_r = timed_search(lock, pos, DEPTH)
                cand_r = timed_search(cand, pos, DEPTH)
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
                rows.append({"seed": seed, "hm": hm, "fen": b.fen(),
                             "resets": len(resets), "mates": mates,
                             "lock": lock_r, "cand": cand_r})
    finally:
        lock.quit()
        cand.quit()

    # pair each hm=100 root with the hm=99 rows of the same seed
    by_seed = {}
    for r in rows:
        by_seed.setdefault(r["seed"], {})[r["hm"]] = r

    comparison = []
    for seed, pair in by_seed.items():
        if 99 not in pair or 100 not in pair:
            continue
        lo, hi = pair[99], pair[100]
        if hi["resets"] == 0:
            continue            # the rule declines nothing here; not a strength case
        if hi["mates"]:
            continue            # the mate-first arm, already proven by the fixtures
        comparison.append({
            "fen": hi["fen"],
            "lock_hm100": hi["lock"],
            "cand_hm100": hi["cand"],
            "lock_hm99_reference": lo["lock"],       # a real search of the same board
            "cand_hm99_reference": lo["cand"],
            # did the unsearched move differ from both searched answers?
            "lock_move_is_unsearched_head": hi["lock"]["nodes"] == 0,
            "cand_agrees_with_hm99_ref": hi["cand"]["bestmove"] == lo["lock"]["bestmove"],
            "lock_agrees_with_hm99_ref": hi["lock"]["bestmove"] == lo["lock"]["bestmove"],
        })

    n = len(comparison)
    s = {
        "strength_cases": n,
        "lock_returned_unsearched_move": sum(1 for c in comparison if c["lock_move_is_unsearched_head"]),
        "cand_matches_hm99_reference": sum(1 for c in comparison if c["cand_agrees_with_hm99_ref"]),
        "lock_matches_hm99_reference": sum(1 for c in comparison if c["lock_agrees_with_hm99_ref"]),
        "cost_nodes_lock_total": sum(r["lock"]["nodes"] or 0 for r in rows),
        "cost_nodes_cand_total": sum(r["cand"]["nodes"] or 0 for r in rows),
        "cost_ms_lock_total": round(sum(r["lock"]["ms"] for r in rows), 1),
        "cost_ms_cand_total": round(sum(r["cand"]["ms"] for r in rows), 1),
    }
    json.dump({"summary": s, "cases": comparison, "all_rows": rows},
              open("/home/ubuntu/work/ev/strength_cost.json", "w"), indent=2)
    print(json.dumps(s, indent=2))
    print("\n--- per-case (claimable root with a reset available):")
    for c in comparison[:20]:
        print(f"  {c['fen'][:44]:46} lock {c['lock_hm100']['bestmove']}/{c['lock_hm100']['score']}"
              f"  cand {c['cand_hm100']['bestmove']}/{c['cand_hm100']['score']:9}"
              f"  ref(hm99) {c['lock_hm99_reference']['bestmove']}/{c['lock_hm99_reference']['score']}")


if __name__ == "__main__":
    main()

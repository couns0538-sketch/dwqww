#!/usr/bin/env python3
"""Validate the drawn-root predicate against the binary -- and prove it can FAIL.

A checker that cannot fail is worse than no checker. Two planted faults:
  1. halfmove_clock >= 99 instead of 100 must be caught on a clock-99 position.
  2. is_repetition(2) instead of (3) must be caught on a twofold-only history.

The oracle compares PREDICTED bail against OBSERVED bail on positions chosen to
straddle each arm, and requires the observation to be the one the source implies.
"""
import json
import sys

sys.path.insert(0, "/tmp/fx")
import chess
import predicates
from uci import Engine, parse_info

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fx/build/forge"

# A KQK won position whose halfmove clock we can dial.
BASE = "8/8/8/4k3/8/8/8/4K2Q w - - {hm} 1"
# A history that reaches `reps` occurrences of the same position.
REP_SEQ = ["e1d1", "e5d5", "d1e1", "d5e5"]


def observe(e, fen, moves):
    pos = "position fen " + fen + (" moves " + " ".join(moves) if moves else "")
    e.set_position(pos)
    r = e.search("go depth 8")
    pi = parse_info(r["last"]) if r["last"] else {}
    return {"nodes": pi.get("nodes", 0), "pv": pi.get("pv", []),
            "bestmove": r["bestmove"], "n_info": len(r["info"]),
            "score": pi.get("score")}


def build_rep_board(reps):
    """A board whose move list contains `reps` occurrences of the current position.

    Bare kings plus a White pawn on b2: the pawn keeps the position out of
    insufficient-material (so the material arm cannot mask the repetition arm) and
    it neither moves nor attacks any square the kings use.
    """
    start = "8/8/8/4k3/8/8/1P6/4K3 w - - 0 1"
    b = chess.Board(start)
    seq = []
    while not b.is_repetition(reps):
        for m in REP_SEQ:
            b.push_uci(m)
            seq.append(m)
        if len(seq) > 40:
            raise RuntimeError("could not build the repetition history")
    return start, seq


CASES = []
# clock arm: 98 must SEARCH, 99 must SEARCH (the search sees the draw one early),
# 100 must BAIL.
for hm in (98, 99, 100):
    CASES.append({"name": f"clock_{hm}", "fen": BASE.format(hm=hm), "moves": [],
                  "expect": "bail" if hm >= 100 else "search",
                  "arm": "fifty" if hm >= 100 else None})
# material arm: KBK and KNK are insufficient material, KQK is not. The engine's
# root predicate calls is_insufficient_material(), so KBK/KNK are EXPECTED to bail
# with 0 nodes -- that is the mechanism behind the game-level bare-minor question,
# not an anomaly. KQK must search: it is a won ending.
for name, fen, exp in (("material_kbk", "8/8/8/4k3/8/8/8/4KB2 w - - 0 1", "bail"),
                       ("material_knk", "8/8/8/4k3/8/8/8/4KN2 w - - 0 1", "bail"),
                       ("material_kqk", "8/8/8/4k3/8/8/8/4K2Q w - - 0 1", "search")):
    CASES.append({"name": name, "fen": fen, "moves": [],
                  "expect": exp,
                  "arm": "material" if exp == "bail" else None})
# repetition arm: 2 occurrences must search, 3 must bail
for reps in (2, 3):
    fen, seq = build_rep_board(reps)
    b = chess.Board(fen)
    for m in seq:
        b.push_uci(m)
    CASES.append({"name": f"reps_{reps}", "fen": fen, "moves": seq,
                  "expect": "bail" if reps >= 3 else "search",
                  "arm": "repetition" if reps >= 3 else None})


def run(cases, tag, expect_bail_fn):
    e = Engine(EXE)
    rows = []
    ok = True
    for c in cases:
        obs = observe(e, c["fen"], c["moves"])
        got = "bail" if obs["nodes"] == 0 and not obs["pv"] else "search"
        # the predicate under test, evaluated on the same board
        b = chess.Board(c["fen"])
        for m in c["moves"]:
            b.push_uci(m)
        pred_bail = expect_bail_fn(b)
        pred = "bail" if pred_bail else "search"
        match = (pred == got == c["expect"])
        ok &= match
        rows.append({"case": c["name"], "expect": c["expect"], "observed": got,
                     "predicted": pred, "nodes": obs["nodes"],
                     "bestmove": obs["bestmove"], "score": obs["score"],
                     "match": match})
        print(f"  {tag:18s} {c['name']:14s} want={c['expect']:6s} obs={got:6s} "
              f"pred={pred:6s} nodes={obs['nodes']:>7} bm={obs['bestmove']} "
              f"{'OK' if match else 'FAIL'}", flush=True)
    e.quit()
    return ok, rows


if __name__ == "__main__":
    print("== arm A: the real predicate ==")
    okA, rowsA = run(CASES, "real", lambda b: predicates.clock_reason(b) is not None)

    print("== arm B: planted fault, halfmove threshold 99 instead of 100 ==")
    def fault99(b):
        return b.is_repetition(3) or b.halfmove_clock >= 99 or b.is_insufficient_material()
    okB, rowsB = run(CASES, "fault-hm99", fault99)

    print("== arm C: planted fault, twofold instead of threefold ==")
    def fault2(b):
        return b.is_repetition(2) or b.halfmove_clock >= 100 or b.is_insufficient_material()
    okC, rowsC = run(CASES, "fault-rep2", fault2)

    print()
    print(f"real predicate      : {'PASS' if okA else 'FAIL'}")
    print(f"fault hm99 detected : {'PASS (it disagreed, as required)' if not okB else 'FAIL (fault not detected)'}")
    print(f"fault rep2 detected : {'PASS (it disagreed, as required)' if not okC else 'FAIL (fault not detected)'}")
    json.dump({"real": rowsA, "fault_hm99": rowsB, "fault_rep2": rowsC,
               "real_pass": okA, "fault_hm99_detected": not okB,
               "fault_rep2_detected": not okC},
              open("/tmp/fx/oracle.json", "w"), indent=1)
    sys.exit(0 if (okA and not okB and not okC) else 1)

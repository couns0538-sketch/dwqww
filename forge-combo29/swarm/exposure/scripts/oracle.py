#!/usr/bin/env python3
"""Non-vacuity check for the harness's reimplementation of the bail's guard.

The whole seat rests on `is_drawn_root()`. If that function is wrong the audit
measures nothing and reports a confident zero -- the failure mode it exists to
expose. So it is validated against the engine binary itself, on cases whose
answer is known in BOTH directions:

  * positives  -- positions that MUST fire (threefold, halfmove>=100, engine-
                  insufficient material). The bail's caller-visible signature is
                  `nodes == 0` together with an EMPTY `pv`, which no searching
                  path produces.
  * negatives  -- near-misses that must NOT fire: halfmove 99, a twofold, K+2N v K
                  (two minors with knights is sufficient to the engine), a
                  knight-and-pawn ending, and an ordinary middlegame.

An earlier draft of this docstring claimed K+N v K distinguished the engine's
insufficiency rule from python-chess's. It does NOT -- both call it insufficient --
and the claim was removed after being tested. The case is kept as a POSITIVE, which
is what it actually is.

A checker is tested by giving it cases whose answer is already known, never by
reading its logic (findings section 6).
"""
from __future__ import annotations

import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from predicates import is_drawn_root  # noqa: E402
from uci import Engine, parse_info  # noqa: E402

# Evidence root: override with FORGE_EXPOSURE_ROOT. Defaults to the parent of scripts/.
ROOT = os.environ.get("FORGE_EXPOSURE_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE = os.path.join(ROOT, "build-base", "forge")


def baited(r: dict) -> bool:
    """The bail's caller-visible signature: 0 nodes and an empty pv."""
    if not r["info"]:
        return False
    li = parse_info(r["last_info"])
    return li.get("nodes") == 0 and li.get("pv") == []


def case(name: str, expect_fire: bool, position: str, note: str = "") -> dict:
    """`position` may be a FEN or a full `position ...` command."""
    if position.startswith("position"):
        cmd = position
        board = chess.Board()
        toks = position.split()
        if "moves" in toks:
            for uci in toks[toks.index("moves") + 1:]:
                board.push_uci(uci)
        elif "fen" in toks:
            board = chess.Board(" ".join(toks[toks.index("fen") + 1:]))
    else:
        cmd = f"position fen {position}"
        board = chess.Board(position)

    fired, p = is_drawn_root(board)
    eng = Engine(BASE)
    r = eng.search(cmd, "go depth 8")
    eng.quit()
    observed = baited(r)
    li = parse_info(r["last_info"]) if r["last_info"] else {}
    return {
        "case": name,
        "note": note,
        "expected_fire": expect_fire,
        "harness_says_fire": fired,
        "engine_baited": observed,
        "agree": (fired == observed),
        "correct": (fired == expect_fire) and (observed == expect_fire),
        "predicates": p,
        "engine": {"bestmove": r["bestmove"], "nodes": li.get("nodes"),
                   "depth": li.get("depth"), "pv": li.get("pv"),
                   "score": li.get("score"), "score_kind": li.get("score_kind")},
    }


def main() -> int:
    rows = []

    # --- positives -------------------------------------------------------
    shuffle = ["g1f3", "g8f6", "f3g1", "f6g8"] * 2
    rows.append(case("threefold_quiet", True,
                     "position startpos moves " + " ".join(shuffle),
                     "knight shuttle returns to the start position a third time"))

    # halfmove 100, a legal pawn-less position
    rows.append(case("halfmove_100", True, "8/8/4k3/8/8/4K3/8/R7 w - - 100 80",
                     "clock at exactly 100"))
    # engine-insufficient: K+N v K
    rows.append(case("kn_vs_k", True, "8/8/4k3/8/8/4K3/5N2/8 w - - 0 1",
                     "engine: minor_count<=1 -> insufficient; python-chess: sufficient"))
    # engine-insufficient: K+B v K
    rows.append(case("kb_vs_k", True, "8/8/4k3/8/8/4K3/5B2/8 w - - 0 1",
                     "minor_count<=1"))
    # bare kings
    rows.append(case("bare_kings", True, "8/8/4k3/8/8/4K3/8/8 w - - 0 1",
                     "automatic draw, no claim exists"))

    # --- negatives -------------------------------------------------------
    rows.append(case("halfmove_99", False, "8/8/4k3/8/8/4K3/8/R7 w - - 99 80",
                     "one short of the threshold -- the report says 99 searches"))
    rows.append(case("twofold_only", False,
                     "position startpos moves g1f3 g8f6 f3g1 f6g8",
                     "exactly 2 occurrences: harmless"))
    rows.append(case("knn_vs_k", False, "8/8/4k3/8/8/4K3/4NN2/8 w - - 0 1",
                     "minor_count=2 with knights -> NOT insufficient to the engine"))
    rows.append(case("middlegame", False,
                     "position startpos moves e2e4 e7e5 g1f3 b8c6 f1b5 a7a6",
                     "ordinary searched position"))
    # A K+N v K position ONE PLY before the material condition is already met is
    # still insufficient; the useful negative is a knight-and-pawn ending.
    rows.append(case("kn_pawn", False, "8/8/4k3/8/8/4K3/4NP2/8 w - - 0 1",
                     "a pawn is present -> not insufficient"))

    ok = all(r["correct"] and r["agree"] for r in rows)
    for r in rows:
        flag = "OK " if (r["correct"] and r["agree"]) else "FAIL"
        print(f"{flag} {r['case']:16s} expect_fire={r['expected_fire']!s:5s} "
              f"harness={r['harness_says_fire']!s:5s} engine_baited={r['engine_baited']!s:5s} "
              f"nodes={r['engine']['nodes']} pv={r['engine']['pv']}")
    print("\nORACLE " + ("PASS" if ok else "FAIL"))
    with open(os.path.join(ROOT, "oracle.json"), "w") as fh:
        json.dump({"ok": ok, "rows": rows}, fh, indent=2)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

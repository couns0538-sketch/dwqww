#!/usr/bin/env python3
"""Prove check G2 can move.

A gate that always fails is as useless as one that always passes. G2 asserts that a
drawn root returns a *searched* move (nodes > 0, at least one info depth line with a
pv). On the base it fails -- that is the documented drawn-root bail.

This script applies a MINIMAL drawn-root repair to a copy of the base and shows G2
flipping to PASS while every one of the four pins stays bit-identical. The repair is
modelled on the description in docs/forge-findings.md §2 (mate-first scan, then search
instead of adjudicating) and is NOT claimed to be the shipped patch -- the shipped
patch files are not in this checkout. Its only purpose here is to demonstrate that
G2 responds to the behaviour it is supposed to measure.

Two-sided requirement, from the brief's rule 3:
  * the repair must flip G2      -> the check is live
  * the pins must NOT move       -> the check costs nothing to keep
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import sensitivity as S  # noqa: E402
import gate as G  # noqa: E402

OLD = """    // Terminal or adjudicated roots: report without searching.
    const bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||
                                               board.is_insufficient_material());
    if (root_candidates.empty() || root_drawn) {"""

NEW = """    // Terminal or adjudicated roots: report without searching.
    // AUDIT PATCH: a drawn root is adjudicated only when no legal move mates at once.
    // A mate ends the game, so no draw claim is available after it; when such a move
    // exists the position is searched like any other root.
    bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||
                                         board.is_insufficient_material());
    if (root_drawn) {
        bool mate_available = false;
        for (const Move candidate : legal) {
            forge::Undo probe_undo;
            if (!board.make_move(candidate, probe_undo)) continue;
            if (board.in_check() && board.legal_moves().empty()) mate_available = true;
            board.unmake_move(candidate, probe_undo);
            if (mate_available) break;
        }
        if (mate_available) root_drawn = false;
    }
    if (root_candidates.empty() || root_drawn) {"""


def main() -> None:
    root = S.fresh("G2_repair")
    p = root / "forge-combo29/src/search.cpp"
    text = p.read_text()
    if text.count(OLD) != 1:
        raise SystemExit(f"anchor appears {text.count(OLD)} times")
    p.write_text(text.replace(OLD, NEW))
    exe = S.build(root, "G2_repair")
    base_result = G.gate(str(S.BUILD))
    patched = G.gate(str(exe))
    by_id = lambda r: {c["id"]: c for c in r["checks"]}
    b, q = by_id(base_result), by_id(patched)
    out = {
        "base": {"all_pass": base_result["all_pass"], "wall": base_result["wall_seconds"],
                 "G2": b["G2"], "G1": b["G1"]},
        "patched": {"all_pass": patched["all_pass"], "wall": patched["wall_seconds"],
                    "G2": q["G2"], "G1": q["G1"]},
        "G2_flipped": (not b["G2"]["pass"]) and q["G2"]["pass"],
        "pins_unchanged": b["G1"]["detail"]["got"] == q["G1"]["detail"]["got"],
        "checsum": {k: (b[k]["pass"], q[k]["pass"]) for k in b},
    }
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()

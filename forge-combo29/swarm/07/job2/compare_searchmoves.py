#!/usr/bin/env python3
"""compare_searchmoves.py BASE_RAW_DIR PATCHED_RAW_DIR

Compares the two driver output trees case by case and ASSERTS the fields were
actually found. A missing file, a missing bestmove, a missing info line or a
missing nodes number is a hard error, never a silent pass.
Exit 0 only when every assertion held and the comparison is as expected.
"""
import json
import os
import re
import sys

CASES = ["sm_illegal_only", "sm_legal_one_startpos", "sm_two_one_legal",
         "sm_all_legal", "sm_empty_list", "sm_illegal_startpos"]
# Cases whose root is restricted to nothing AND the board itself has legal moves.
# Only those are the finding: the patch must withdraw the fabricated depth line.
# sm_illegal_only is deliberately NOT here: its FEN is stalemate (python-chess
# reports 0 legal moves), so its 0-node line is the pre-existing dead-root answer
# and must be left exactly as it was. The patch keys on the restriction, not on an
# empty root, precisely so that case does not change.
EMPTY_ROOT = {"sm_empty_list", "sm_illegal_startpos"}
UNCHANGED = {"sm_illegal_only", "sm_legal_one_startpos", "sm_two_one_legal", "sm_all_legal"}


def load(rawdir, case):
    path = os.path.join(rawdir, case + ".json")
    if not os.path.exists(path):
        raise SystemExit(f"FAIL missing record {path}: nothing was measured for {case}")
    with open(path, encoding="utf-8") as fh:
        rec = json.load(fh)
    for key in ("bestmoves", "last_info"):
        if key not in rec:
            raise SystemExit(f"FAIL {path} has no field {key}")
    return rec


def nodes_of(rec, where):
    line = rec.get("last_info")
    if line is None:
        return None  # legitimately absent after the patch on an empty root
    m = re.search(r" nodes (\d+) ", line + " ")
    if not m:
        raise SystemExit(f"FAIL {where}: no ' nodes <n> ' in the recorded info line [{line}]")
    return int(m.group(1))


def main():
    base_dir, patched_dir = sys.argv[1], sys.argv[2]
    problems, rows = [], []
    for case in CASES:
        b, p = load(base_dir, case), load(patched_dir, case)
        if not b["bestmoves"] or not p["bestmoves"]:
            raise SystemExit(f"FAIL {case}: no bestmove recorded on one side "
                             f"(base={b['bestmoves']}, patched={p['bestmoves']})")
        bm_b, bm_p = b["bestmoves"][-1], p["bestmoves"][-1]
        nb, np_ = nodes_of(b, case + "/base"), nodes_of(p, case + "/patched")
        rows.append((case, bm_b, nb, b["last_info"], bm_p, np_, p["last_info"]))
        if bm_b != bm_p:
            problems.append(f"{case}: bestmove changed {bm_b} -> {bm_p}")
        if case in EMPTY_ROOT:
            if p["last_info"] is not None:
                problems.append(f"{case}: patched build still printed a depth line "
                                f"[{p['last_info']}]")
            if b["last_info"] is None:
                problems.append(f"{case}: baseline printed no depth line, so the "
                                f"comparison measured nothing")
        elif case in UNCHANGED:
            if np_ != nb:
                problems.append(f"{case}: node count changed {nb} -> {np_}")
            if p["last_info"] is None:
                problems.append(f"{case}: patched build printed no depth line")
            if b["last_info"] == p["last_info"] and case in ("sm_legal_one_startpos", "sm_two_one_legal", "sm_all_legal"):
                # identical text up to the timing fields is expected; nps/time vary with the run
                pass
    for case, bm_b, nb, li_b, bm_p, np_, li_p in rows:
        print(f"{case:24s} base {bm_b:22s} nodes={nb}  |  patched {bm_p:22s} nodes={np_}")
        print(f"    base info: {li_b}")
        print(f"    patch info: {li_p}")
    if problems:
        print("\nPROBLEMS:")
        for item in problems:
            print("  -", item)
        raise SystemExit(1)
    print("\nOK: every assertion held; no bestmove changed anywhere; a search that does have "
          "legal root moves kept its exact node count.")


if __name__ == "__main__":
    main()

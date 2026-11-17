#!/usr/bin/env python3
"""Property 6: the two non-search paths a client meets at MultiPV > 1.

The report says the book path emits no multipv line at all (trap 19c) and that the drawn-root bail
emits one line per depth.  Both are re-measured here on this build, at MultiPV 1/2/3/6, with the
controls that make each attribution safe:

  book      OwnBook true vs OwnBook false on the SAME position and the same `go movetime`, so the
            difference is the book gate and not the position or the budget;
            plus the wire shape (line count, `info string book move`, bestmove)
  drawn     four distinct drawn-root shapes (insufficient material, stalemate, checkmate,
            fifty-move) at each MultiPV, because they do NOT behave alike and a client that
            handles one has not handled the others
  precedence the drawn root that also has a book entry, with OwnBook true, to confirm which path
            answers first

Usage: python3 fastpaths.py <exe> [--json out.json]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from multipv_lib import Engine, bestmove_of, depth_lines, write_json

STARTPOS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
DRAWN = {
    "insufficient_material": "8/8/8/4k3/8/8/4K3/8 w - - 0 1",
    "stalemate": "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1",
    "checkmate": "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3",
    "fifty_move": "4k3/8/8/8/8/8/8/4K2R w - - 100 60",
}
FIFTY_BOOK_IN = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 100 1"
FIFTY_BOOK_OUT = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 100 16"


def run(exe, fen, mpv, ownbook, go):
    with Engine(exe=exe, multipv=mpv, ownbook=ownbook) as e:
        e.position(fen)
        lines = e.go(go)
    infos = depth_lines(lines)
    return {
        "go": go, "mpv": mpv, "ownbook": ownbook,
        "total_lines": len(lines),
        "info_depth_lines": len(infos),
        "multipv_tokens": sum(1 for ln in lines if " multipv " in ln),
        "info_string_lines": [ln for ln in lines if ln.startswith("info string")],
        "bestmove": bestmove_of(lines),
        "multipv_indices": sorted({p["multipv"] for p in infos}),
        "distinct_depths": len({p["depth"] for p in infos}),
        "pv_all_empty": all(not p["pv"] for p in infos) if infos else None,
        "nodes_all_zero": all(p["nodes"] == 0 for p in infos) if infos else None,
        "score_kinds": sorted({p["score_kind"] for p in infos}) if infos else [],
        "lines": lines,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe", nargs="?", default="build/forge")
    ap.add_argument("--json")
    args = ap.parse_args()
    out = {"book": [], "drawn": [], "precedence": [], "restricted": []}

    for mpv in (1, 2, 3, 6):
        out["book"].append(run(args.exe, STARTPOS, mpv, True, "go movetime 300"))
        out["book"].append(run(args.exe, STARTPOS, mpv, False, "go movetime 300"))

    for name, fen in DRAWN.items():
        for mpv in (1, 2, 3, 6):
            r = run(args.exe, fen, mpv, False, "go depth 6")
            r["case"] = name
            out["drawn"].append(r)

    # Precedence: a drawn root that ALSO has a book entry.  `Book Depth` defaults to 30 and is
    # gated on game_ply, which is derived from the FEN's FULLMOVE counter -- not the halfmove
    # clock.  So the same 100-ply board books at fullmove 1 (game_ply 0) and bails at fullmove 16
    # (game_ply 30).  Both arms are measured, because the first one is the dangerous client case.
    out["precedence"].append(dict(case="drawn_and_in_book", **run(args.exe, FIFTY_BOOK_IN, 3, True,
                                                                 "go movetime 300")))
    out["precedence"].append(dict(case="drawn_and_in_book", **run(args.exe, FIFTY_BOOK_IN, 3, False,
                                                                 "go movetime 300")))
    out["precedence"].append(dict(case="drawn_past_book_depth", **run(args.exe, FIFTY_BOOK_OUT, 3, True,
                                                                     "go movetime 300")))
    out["precedence"].append(dict(case="drawn_past_book_depth", **run(args.exe, FIFTY_BOOK_OUT, 3, False,
                                                                     "go movetime 300")))

    # searchmoves narrowed to one move at MultiPV 3: the third way to have fewer lines than asked
    with Engine(exe=args.exe, multipv=3) as e:
        e.position(STARTPOS)
        lines = e.go("go depth 8 searchmoves e2e4")
    infos = depth_lines(lines)
    out["restricted"].append({
        "cmd": "go depth 8 searchmoves e2e4", "mpv": 3,
        "info_depth_lines": len(infos),
        "multipv_indices": sorted({p["multipv"] for p in infos}),
        "bestmove": bestmove_of(lines),
        "max_pv_len": max((len(p["pv"]) for p in infos), default=0)})

    # summary, computed not typed
    book_gt1 = [r for r in out["book"] if r["ownbook"] and r["mpv"] > 1]
    s = {
        # scalar so a report marker can cite a number, not a set of one element
        "book_lines_at_mpv_gt_1": max(r["info_depth_lines"] for r in book_gt1),
        "book_multipv_tokens_max": max(r["multipv_tokens"] for r in book_gt1),
        "book_arms_at_mpv_gt_1": len(book_gt1),
        "book_controls": sum(1 for r in out["book"] if not r["ownbook"]),
        "book_control_info_lines_min": min(r["info_depth_lines"] for r in out["book"] if not r["ownbook"]),
        "book_control_multipv_tokens_min": min(r["multipv_tokens"] for r in out["book"] if not r["ownbook"]),
        "book_bestmove_matches_info_string": all(
            r["info_string_lines"] and r["bestmove"] == r["info_string_lines"][0].split()[-1]
            for r in out["book"] if r["ownbook"] and r["info_string_lines"]),
        "drawn_max_multipv_index_at_mpv_gt_1": max(max(r["multipv_indices"]) for r in out["drawn"]
                                                   if r["mpv"] > 1),
        "drawn_arms": sum(1 for r in out["drawn"] if r["mpv"] > 1),
        "drawn_arms_max_index_gt_1": sum(1 for r in out["drawn"]
                                         if r["mpv"] > 1 and max(r["multipv_indices"]) > 1),
        "drawn_distinct_depths_max": max(r["distinct_depths"] for r in out["drawn"]),
        "drawn_pv_all_empty": all(r["pv_all_empty"] for r in out["drawn"]),
        "drawn_nodes_all_zero": all(r["nodes_all_zero"] for r in out["drawn"]),
        "precedence_book_lines": out["precedence"][0]["info_depth_lines"],
        "precedence_bail_lines": out["precedence"][1]["info_depth_lines"],
        "precedence_book_bestmove": out["precedence"][0]["bestmove"],
        "precedence_bail_bestmove": out["precedence"][1]["bestmove"],
        "precedence_booked_not_bailed": (out["precedence"][0]["info_depth_lines"] == 0
                                         and out["precedence"][1]["info_depth_lines"] > 0),
        "past_book_depth_bails_regardless_of_ownbook": (
            out["precedence"][2]["bestmove"] == out["precedence"][3]["bestmove"]
            and out["precedence"][2]["info_depth_lines"] == out["precedence"][3]["info_depth_lines"]),
        "restricted_indices": out["restricted"][0]["multipv_indices"],
    }
    out["summary"] = s
    print(json.dumps(s, indent=1))
    if args.json:
        write_json(args.json, out)
        print("wrote", args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())

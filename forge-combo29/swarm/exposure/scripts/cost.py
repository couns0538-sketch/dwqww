#!/usr/bin/env python3
"""What the bail costs: did it change the move, and how many centipawns?

THE QUESTION IS COUNTERFACTUAL and cannot be answered from the base build alone: on a
drawn root the base searches nothing, so "the move the search would have played" needs
a build that actually searches. Three arms, all on the IDENTICAL position (same move
list, same depth):

  base     -- the shipped build. Bails.
  patched  -- seat 12 + seat 27 composed. THE REPAIR THE OWNER IS ASKED TO SHIP.
  nobail   -- INSTRUMENT ONLY, not a shipped configuration: the bail is compiled out,
              so the position is searched. This is the reference for "what would the
              search have played".

CONFOUND HANDLED EXPLICITLY: findings section 2 records that the LEAF rule at
search.cpp:1302 already adjudicates draws one ply down, and that a root at halfmove 99
misses mates through it. So a reference arm at halfmove 99 is not a clean search, and
rows at that boundary are reported SEPARATELY rather than pooled. Every row records its
halfmove so the reader can see the split.

COST DIRECTION: centipawns are measured from the OPPONENT'S best reply to each arm's
move, scored from the ROOT SIDE's point of view, so the number is an objective loss of
the move rather than a comparison of two scores belonging to different sides.
"""
from __future__ import annotations

import argparse
import glob
import json
import multiprocessing as mp
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import glob_under_root, load_json, open_json_out
from uci import Engine, parse_info  # noqa: E402

# Evidence root: override with FORGE_EXPOSURE_ROOT. Defaults to the parent of scripts/.
ROOT = os.environ.get("FORGE_EXPOSURE_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BUILDS = {"base": os.path.join(ROOT, "build-base", "forge"),
          "patched": os.path.join(ROOT, "build-patched", "forge"),
          "nobail": os.path.join(ROOT, "build-nobail", "forge")}


def ask(build: str, moves: list[str], go: str) -> dict:
    eng = Engine(BUILDS[build])
    pos = ("position startpos moves " + " ".join(moves)) if moves else "position startpos"
    r = eng.search(pos, go)
    eng.quit()
    li = parse_info(r["last_info"]) if r["last_info"] else {}
    nodes = li.get("nodes")
    return {
        "bestmove": r["bestmove"],
        "nodes": nodes,
        "depth": li.get("depth"),
        "pv": li.get("pv", []),
        "score_kind": li.get("score_kind"),
        "score": li.get("score"),
        "n_info": len(r["info"]),
        # Caller-visible bail signature: zero nodes AND an empty pv. Every searching
        # path writes a pv; nothing in the bail branch does.
        "bailed": (nodes == 0 and li.get("pv", []) == [] and len(r["info"]) > 0),
    }


def score_for_root_side(build: str, moves: list[str], root_white: bool, go: str):
    info = ask(build, moves, go)
    if info["score"] is None:
        return None
    side_to_move_white = (len(moves) % 2 == 0)
    same = (side_to_move_white == root_white)
    if info["score_kind"] == "mate":
        mate = info["score"]
        signed = mate if same else -mate
        cp = 100000 - abs(mate) * 100
        return cp if signed > 0 else -cp
    return info["score"] if same else -info["score"]


def do_row(args) -> dict:
    datum, depth = args
    go = f"go depth {depth}"
    root = datum["firing"]
    # Slice the move list at the firing's own recorded length. Using the game's full
    # move list put the engine on a LATER position -- the FEN gate caught it on 35 of
    # 40 sampled rows, which is why the gate exists.
    moves = list(datum["moves"][:root["n_moves"]])
    board = chess.Board()
    for uci in moves:
        board.push_uci(uci)
    if board.fen() != root["fen"]:
        return {"error": "FEN mismatch", "fen_replayed": board.fen(),
                "fen_recorded": root["fen"], "n_moves": root["n_moves"]}

    root_white = board.turn == chess.WHITE
    arms = {name: ask(name, moves, go) for name in BUILDS}
    row = {
        "fen": root["fen"],
        "reason": root["reason"],
        "halfmove": root["halfmove"],
        "legal": root["legal"],
        "endgame_type": root["endgame_type"],
        "ply": root["ply"],
        "game": datum["game"],
        "n_moves": len(moves),
        "arms": arms,
        "base_bailed": arms["base"]["bailed"],
        "move_base": arms["base"]["bestmove"],
        "move_patched": arms["patched"]["bestmove"],
        "move_nobail": arms["nobail"]["bestmove"],
        "patched_changes_move": arms["patched"]["bestmove"] != arms["base"]["bestmove"],
        "search_changes_move": arms["nobail"]["bestmove"] != arms["base"]["bestmove"],
        "nobail_searched": arms["nobail"]["nodes"] > 0,
    }

    # Mate-in-1 available at the root?  This is the report's headline forfeit, so it is
    # tested directly rather than inferred.
    mating = []
    for m in board.legal_moves:
        b2 = board.copy()
        b2.push(m)
        if b2.is_checkmate():
            mating.append(m.uci())
    row["mating_moves"] = mating
    row["base_forfeits_mate"] = bool(mating) and row["move_base"] not in mating

    costs = {}
    for arm in ("base", "patched", "nobail"):
        mv = arms[arm]["bestmove"]
        if not mv or mv == "(none)":
            costs[arm] = None
            continue
        b2 = board.copy()
        try:
            b2.push_uci(mv)
        except ValueError:
            costs[arm] = None
            continue
        child = moves + [mv]
        score = score_for_root_side("nobail", child, root_white, go)
        costs[arm] = {"move": mv, "reply_score_cp": score}
    row["costs"] = costs
    base_cp = (costs.get("base") or {}).get("reply_score_cp")
    nobail_cp = (costs.get("nobail") or {}).get("reply_score_cp")
    row["cost_cp"] = None if (base_cp is None or nobail_cp is None) else (nobail_cp - base_cp)
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--out", required=True)
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    ap.add_argument("--sample", type=int, default=0,
                    help="0 = every firing; N = a deterministic stride sample of N")
    args = ap.parse_args()

    data = []
    for path_glob in args.runs:
        for path in glob_under_root(path_glob):
            d = load_json(path)
            for g in d["rows"]:
                for f in g["firings"]:
                    data.append({"game": g["game"], "moves": g["moves"], "firing": f})
    print(f"{len(data)} firing positions across {len({id(d['moves']) for d in data})} move lists")

    if args.sample and args.sample < len(data):
        stride = len(data) / args.sample
        data = [data[int(i * stride)] for i in range(args.sample)]
        print(f"sampled {len(data)} by deterministic stride")

    work = [(d, args.depth) for d in data]
    rows = []
    with mp.Pool(args.jobs) as pool:
        for row in pool.imap_unordered(do_row, work, chunksize=1):
            rows.append(row)
            if len(rows) % 50 == 0:
                print(f"  {len(rows)}/{len(work)}", flush=True)
    with open_json_out(args.out) as fh:
        json.dump({"depth": args.depth, "rows": rows}, fh, indent=1)

    errs = [r for r in rows if "error" in r]
    ok = [r for r in rows if "error" not in r]
    print(f"rows {len(ok)}, errors {len(errs)}")
    print(f"base bailed {sum(r['base_bailed'] for r in ok)}/{len(ok)}")
    print(f"patched changes move {sum(r['patched_changes_move'] for r in ok)}/{len(ok)}")
    print(f"search changes move   {sum(r['search_changes_move'] for r in ok)}/{len(ok)}")
    print(f"roots with mate-in-1  {sum(1 for r in ok if r['mating_moves'])}/{len(ok)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

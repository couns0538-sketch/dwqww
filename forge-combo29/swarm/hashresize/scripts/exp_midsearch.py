"""Experiment C - what the wire shows when `setoption name Hash` lands mid-search.

`uci.cpp` runs `stop_search()` before it parses a `setoption`, so the expected
wire effect is: the running search is stopped, a `bestmove` is emitted, and only
then is the option applied.

That leaves the real question the task asks: is the `bestmove` the SEARCHED one,
or a fabricated one?  Three candidate answers, each with a distinct signature:

  SEARCHED_AT_D   equals the best move of a complete fresh `go depth D` search,
                  where D is the last depth the stopped search had ANNOUNCED.
  SEARCHED_AT_D1  equals the best move of a complete fresh `go depth D+1`
                  search (a partial iteration was used).
  FABRICATED      equals neither, and instead equals the head of the root move
                  list -- which this engine publishes as `root_candidates.front()`
                  and which the drawn-root bail already exposes (S7 item 3ab).

Discriminating check: the reply carries no `info` line of its own, so the only
in-band evidence is the PRE-stop `pv` head.  A fabricated move need not be the
pv head; a searched one is.  The harness records both comparisons and reports
the move that fits, rather than assuming.

The control that makes the whole thing non-vacuous: an explicit `stop` at the
same point in the same position must produce the same bestmove.  If `setoption`
and `stop` disagree, the option path is doing something a plain stop does not.
"""

import argparse
import json
import os
import select
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_client import Engine, ENGINE, parse_info
from corpus import select


def fresh_depth(engine, position, depth, hash_mb):
    e = Engine(engine)
    try:
        e.handshake()
        e.setoption("Hash", hash_mb)
        e.newgame()
        r = e.search(position, "go depth %d" % depth, timeout=600)
        return {"bestmove": r["bestmove"], "nodes": r["nodes"], "score": r["score"], "pv": r["pv"]}
    finally:
        e.close()


def stop_at_depth(engine, position, hash_mb, want_depth, how, timeout=120.0):
    """Start an unbounded search, wait until `want_depth` is announced, then
    interrupt it either with `stop` or with `setoption name Hash value N`."""
    e = Engine(engine)
    rec = {"how": how, "want_depth": want_depth}
    try:
        e.handshake()
        e.setoption("Hash", hash_mb)
        e.newgame()
        e.send(position)
        e.send("go infinite")
        # wait for the depth line
        deadline = time.time() + timeout
        announced = None
        announced_info = None
        while time.time() < deadline:
            line = e._take_line()
            if line is None:
                if e.eof:
                    break
                e._fill(0.02)
                continue
            if line.startswith("info depth"):
                info = parse_info(line)
                if info.get("depth", -1) >= want_depth:
                    announced = line
                    announced_info = info
                    break
        rec["announced"] = announced
        rec["announced_depth"] = announced_info.get("depth") if announced_info else None
        rec["announced_pv"] = announced_info.get("pv") if announced_info else None
        rec["announced_nodes"] = announced_info.get("nodes") if announced_info else None

        t0 = time.time()
        if how == "setoption":
            e.send("setoption name Hash value %d" % (hash_mb * 16 if hash_mb * 16 <= 2048 else 2048))
        else:
            e.send("stop")
        lines, ok = e.lines_until("bestmove", timeout=120)
        rec["latency_s"] = round(time.time() - t0, 4)
        rec["bestmove"] = None
        for line in lines:
            if line.startswith("bestmove"):
                toks = line.split()
                rec["bestmove"] = toks[1] if len(toks) > 1 else None
        rec["post_stop_info_lines"] = sum(1 for l in lines if l.startswith("info depth"))
        rec["post_stop_lines"] = lines[:6]
        rec["bestmove_ok"] = ok
        # drain and make sure the process is quiet and usable
        e.send("isready")
        e.lines_until("readyok", timeout=30)
        return rec
    finally:
        e.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default=ENGINE)
    ap.add_argument("--count", type=int, default=30)
    ap.add_argument("--anchor-depth", type=int, default=18)
    ap.add_argument("--stop-depth", type=int, default=14)
    ap.add_argument("--hash", type=int, default=16)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    chosen, rejected = select(args.count, args.anchor_depth, engine=args.engine)
    print("positions %d (rejected %d)" % (len(chosen), len(rejected)), flush=True)

    rows = []
    for idx, entry in enumerate(chosen):
        fen = entry["fen"]
        pos = "position fen " + fen
        D = args.stop_depth
        ref_D = fresh_depth(args.engine, pos, D, args.hash)
        ref_D1 = fresh_depth(args.engine, pos, D + 1, args.hash)
        via_option = stop_at_depth(args.engine, pos, args.hash, D, "setoption")
        via_stop = stop_at_depth(args.engine, pos, args.hash, D, "stop")
        row = {
            "i": idx, "fen": fen,
            "ref_D": ref_D, "ref_D1": ref_D1,
            "setoption": via_option, "stop": via_stop,
        }
        rows.append(row)
        with open(args.out, "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        print("  [%d/%d] announced d%s bm_opt=%s bm_stop=%s refD=%s" % (
            idx + 1, len(rows), via_option["announced_depth"],
            via_option["bestmove"], via_stop["bestmove"], ref_D["bestmove"]), flush=True)

    summarise(rows, args)


def summarise(rows, args):
    n = len(rows)
    stats = {
        "option_vs_stop_same": 0,
        "option_eq_refD": 0,
        "option_eq_refD1": 0,
        "option_eq_pvhead": 0,
        "option_neither": 0,
        "stop_eq_refD": 0,
        "option_bestmove_present": 0,
        "post_stop_info_lines_total": 0,
        "announced_depth_equals_want": 0,
    }
    detail = []
    for r in rows:
        o, s = r["setoption"], r["stop"]
        pvhead = (o["announced_pv"] or [None])[0]
        if o["bestmove"]:
            stats["option_bestmove_present"] += 1
        if o["bestmove"] == s["bestmove"]:
            stats["option_vs_stop_same"] += 1
        if o["bestmove"] == r["ref_D"]["bestmove"]:
            stats["option_eq_refD"] += 1
        if o["bestmove"] == r["ref_D1"]["bestmove"]:
            stats["option_eq_refD1"] += 1
        if pvhead is not None and o["bestmove"] == pvhead:
            stats["option_eq_pvhead"] += 1
        if o["bestmove"] != r["ref_D"]["bestmove"] and o["bestmove"] != r["ref_D1"]["bestmove"]:
            stats["option_neither"] += 1
        if s["bestmove"] == r["ref_D"]["bestmove"]:
            stats["stop_eq_refD"] += 1
        if o["announced_depth"] == args.stop_depth:
            stats["announced_depth_equals_want"] += 1
        stats["post_stop_info_lines_total"] += o["post_stop_info_lines"]
        detail.append({
            "i": r["i"],
            "announced_depth": o["announced_depth"],
            "announced_pvhead": pvhead,
            "bm_via_setoption": o["bestmove"],
            "bm_via_stop": s["bestmove"],
            "ref_depth_D": r["ref_D"]["bestmove"],
            "ref_depth_D1": r["ref_D1"]["bestmove"],
            "latency_setoption_s": o["latency_s"],
        })
    print("\n== mid-search interruption, n=%d, stop at depth %d ==" % (n, args.stop_depth))
    for k, v in stats.items():
        print("  %-34s %s" % (k, v))
    for d in detail:
        print("  %s" % json.dumps(d))
    with open(args.out + ".summary.json", "w") as fh:
        json.dump({"args": vars(args), "stats": stats, "detail": detail}, fh, indent=2)


if __name__ == "__main__":
    main()

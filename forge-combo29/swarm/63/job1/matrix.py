"""Run the adversarial drawn-root matrix against one or two engines.

Rules encoded:
  * every FEN comes from fixtures.json, which python-chess validated;
  * the node count at a fixed depth must be NON-ZERO before a result is trusted, which
    catches a silently refused position (the engine would have searched the previous one);
  * `invalid FEN` is scanned in BOTH the position reply and the go output;
  * Threads 1, no clock, explicit `go depth N`;
  * every `go` is bounded with a timeout and bestmove is awaited.
"""
import argparse
import json
import os
import sys

from ucih import Engine, EngineError

S14 = [
    "LmrQuietBase 93", "LmrQuietDivisor 205", "LmrNoisyBase 13", "LmrNoisyDivisor 333",
    "LmrHistoryDivisor 5643", "NullMoveBase 5", "LmpBase 8", "HistoryPruneMultiplier 2220",
    "HistoryBonusQuadratic 24", "HistoryBonusLinear 54", "HistoryBonusMax 2212",
    "SingularDepth 6", "IirDepth 2",
]


def setup(e, threads=1, hash_mb=16, s14=False):
    e.send("setoption name Threads value %d" % threads)
    e.send("setoption name Hash value %d" % hash_mb)
    if s14:
        for item in S14:
            name, val = item.split(" ", 1)
            e.send("setoption name %s value %s" % (name, val))
        e.send("setoption name NonPawnCorrection value true")
    e.check_fen(e.ready(), "setoption reply")


def run_one(exe, key, fx, depth=8, s14=False):
    """One fixture on a FRESH process. Returns a record."""
    rec = {"fixture": key, "fen": fx["fen"], "kind": fx["kind"], "depth": depth,
           "mating_moves": fx.get("mating_moves", []), "engine": os.path.basename(os.path.dirname(exe)),
           "py_legal_moves": fx.get("legal_moves")}
    e = Engine(exe)
    try:
        e.send("ucinewgame")
        setup(e, s14=s14)
        e.position(fx["fen"], moves=fx.get("moves"))   # raises on invalid FEN in the position reply
        # Position-identity gate: `go perft 1` must equal python-chess's legal-move count.
        # A silently refused FEN leaves the PREVIOUS board (here: startpos, 20 moves), so a
        # mismatch proves the engine is not on the board we think it is.
        plines, pn = e.perft(1, timeout=120.0)
        rec["perft1"] = pn
        rec["position_confirmed"] = (rec["perft1"] == fx.get("legal_moves"))

        e.send("ucinewgame")
        setup(e, s14=s14)
        e.position(fx["fen"], moves=fx.get("moves"))
        lines, bm, info = e.go("go depth %d" % depth, timeout=180.0)
        rec["info_lines"] = info
        rec["bestmove"] = bm
        rec["max_depth_reported"] = max(
            [int(l.split()[2]) for l in info if l.startswith("info depth")] or [0])
        rec["info_count"] = len(info)
        rec["nodes"] = e.nodes_from(info)
        rec["bestmove_is_mate"] = bm in (fx.get("mating_moves") or [])
        rec["bestmove_is_stalemate"] = bm in (fx.get("stalemating_moves") or [])
        rec["last_info"] = info[-1] if info else ""
        rec["go_lines_head"] = lines[:3]
        # Trust gate: a non-zero node count means a real search happened.
        rec["trusted"] = rec["nodes"] > 0 and bool(rec["position_confirmed"])
        if not rec["position_confirmed"]:
            rec["NOTE"] = ("POSITION NOT CONFIRMED: perft1=%r vs python-chess %r; a refused FEN "
                           "would leave the previous board" % (rec["perft1"], fx.get("legal_moves")))
        elif not rec["trusted"]:
            rec["NOTE"] = "nodes 0 at depth %d: result NOT trusted" % depth
    except EngineError as exc:
        rec["error"] = str(exc)
        rec["trusted"] = False
    finally:
        rec["transcript"] = e.transcript
        e.quit()
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--fixtures", default="fixtures.json")
    ap.add_argument("--depth", type=int, default=8)
    ap.add_argument("--s14", action="store_true")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    fx = json.load(open(args.fixtures))
    results = {}
    for key, item in fx.items():
        results[key] = run_one(args.exe, key, item, depth=args.depth, s14=args.s14)
    blob = {"exe": args.exe, "tag": args.tag, "depth": args.depth, "s14": args.s14,
            "results": results}
    with open(args.out, "w") as fh:
        json.dump(blob, fh, indent=2)

    print("%-32s %-14s %8s %6s %10s %-8s %s" %
          ("fixture", "kind", "nodes", "depth", "maxdepth", "bestmove", "trusted"))
    for key, r in results.items():
        print("%-32s %-14s %8s %6s %10s %-8s %s" % (
            key, r["kind"], r.get("nodes", "-"), r["depth"],
            r.get("max_depth_reported", "-"), r.get("bestmove") or "-", r["trusted"]))


if __name__ == "__main__":
    sys.exit(main())

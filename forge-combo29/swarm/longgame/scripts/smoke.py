#!/usr/bin/env python3
"""Smoke test: one position, in-process vs fresh, plus a planted threefold bail.

The bail case is constructed, not from the corpus: the point is to prove the harness can
SEE a 0-node bail when one occurs, before trusting a clean run.
"""
import sys
sys.path.insert(0, "scripts")
from uci import Engine, search
from checks import require

ENG = "forge-combo29/build/forge"


def fresh(position_cmd, go="go depth 8"):
    e = Engine(ENG)
    e.uci()
    e.sync()
    r = search(e, position_cmd, go)
    r["rss_kb"] = e.rss_kb()
    e.quit()
    return r


def show(tag, r):
    print(f"{tag:22s} bm={r['bestmove']} score={r['score']} nodes={r['nodes']} "
          f"depth={r['depth']} infos={r['n_info']} pv={' '.join(r['pv'][:4])}")


def main():
    e = Engine(ENG)
    e.uci(); e.sync()
    # control 1: cold, then warm (no ucinewgame) -- must differ, proving the instrument sees state
    p = "position startpos moves e2e4 e7e5 g1f3 b8c6 f1c4 g8f6"
    r1 = search(e, p); show("warm-1", r1)
    r2 = search(e, p); show("warm-2", r2)
    print("  warm1==warm2:", r1["bestmove"] == r2["bestmove"], r1["nodes"] == r2["nodes"])
    e.send("ucinewgame"); e.sync()
    r3 = search(e, p); show("after ucinewgame", r3)
    print("  warm1==ucinewgame:", r1["bestmove"] == r3["bestmove"], r1["nodes"] == r3["nodes"])
    e.quit()

    f = fresh(p); show("fresh", f)
    print("  fresh==ucinewgame:", f["bestmove"] == r3["bestmove"], f["nodes"] == r3["nodes"])

    # control 2: planted threefold -> must bail (0 nodes, empty pv)
    seq = "g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8"
    b = fresh("position startpos moves " + seq)
    show("planted threefold", b)
    require(b["bestmove"] is not None, "no bestmove")
    print("  bailed (0 nodes, empty pv):", b["nodes"] in (0, None) and not b["pv"])

    # control 3: two occurrences must NOT bail
    seq2 = "g1f3 g8f6 f3g1 f6g8"
    b2 = fresh("position startpos moves " + seq2)
    show("planted twofold", b2)
    print("  twofold searched:", (b2["nodes"] or 0) > 0 and bool(b2["pv"]))


if __name__ == "__main__":
    main()

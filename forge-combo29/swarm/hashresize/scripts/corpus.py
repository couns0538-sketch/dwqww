"""Shared corpus selection for the hash-resize seat.

Rule, fixed before the first measurement so it cannot be chosen after seeing
results:

  * positions are the first N lines of forge-10000.epd (shipped with the
    5.31.0 archive, extracted to /tmp/work/corpus), in file order;
  * a position is ELIGIBLE only if a fresh Hash 16 search at the seat depth
    emits at least one `info depth` line and more than 0 nodes.  The audit's
    drawn-root bail answers with 0 nodes and no iteration, so a position it
    fires on has no table state to compare and cannot test a resize;
  * ineligible positions are replaced by the next line of the file, so the
    sample is always N eligible positions.

The eligibility pass itself is a fresh-process measurement, so it is
independent of every arm being compared.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_client import Engine, ENGINE

EPD = "/tmp/work/corpus/forge-10000.epd"


def load_epd(path=EPD, limit=None):
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            body = line.split(" id ")[0].strip()
            fields = body.split()
            if len(fields) == 4:
                body += " 0 1"
            elif len(fields) == 5:
                body += " 0"
            out.append(body)
            if limit is not None and len(out) >= limit:
                break
    return out


def eligible(fen, depth, hash_mb, engine=ENGINE, timeout=300.0):
    e = Engine(engine)
    try:
        e.handshake()
        e.setoption("Hash", hash_mb)
        e.newgame()
        r = e.search("position fen " + fen, "go depth %d" % depth, timeout=timeout)
        return r["ok"] and r["info_depth_lines"] > 0 and (r["nodes"] or 0) > 0, r
    finally:
        e.close()


def select(count, depth, engine=ENGINE, scan_limit=None):
    pool = load_epd(limit=scan_limit)
    chosen, rejected = [], []
    for fen in pool:
        ok, r = eligible(fen, depth, 16, engine=engine)
        if ok:
            chosen.append({"fen": fen, "ref_nodes": r["nodes"], "ref_bestmove": r["bestmove"]})
        else:
            rejected.append({"fen": fen, "nodes": r["nodes"], "info_depth_lines": r["info_depth_lines"]})
        if len(chosen) >= count:
            break
    return chosen, rejected


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    depth = int(sys.argv[2]) if len(sys.argv) > 2 else 18
    chosen, rejected = select(n, depth)
    print("eligible %d, rejected %d" % (len(chosen), len(rejected)))
    for c in chosen:
        print(c["fen"], c["ref_nodes"], c["ref_bestmove"])
    for r in rejected:
        print("REJECTED", r["fen"], r["nodes"], r["info_depth_lines"])

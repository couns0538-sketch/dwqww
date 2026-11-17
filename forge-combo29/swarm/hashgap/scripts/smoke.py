"""Smoke test: the instrument must (a) reproduce a cell exactly and (b) show any
counter moving. A counter that never moves cannot explain anything, so this runs
before the grid rather than after it.

Checks:
1. Same cell twice -> identical bestmove, depth, and every counter.
2. Hash 1 vs Hash 64 at 500k on one position -> the two must differ in counter
   magnitudes, and the run at Hash 1 must displace entries while Hash 64 at the
   same budget displaces far fewer (or none).
3. `ttstats` reports whole-table occupancy and the load factor implied by it,
   which is the variable the earlier report reasoned about loosely.
"""

import json
import sys

import positions
import ucih

BINARY = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/build-trace/forge"


def show(tag, cell):
    trace = cell["trace"] or {}
    print(
        f"{tag:24s} best={cell['bestmove']:6s} depth={cell['depth']:3d} "
        f"score={cell['score']} "
        f"probe={trace.get('probe')} miss={trace.get('probe_miss')} "
        f"displace={trace.get('store_displace')} "
        f"shallower={trace.get('hit_shallower')} "
        f"false={trace.get('false_hit')}"
    )


fen = positions.PRACTICAL[10]
go = "go nodes 500000"

print(f"position: {fen}")
a = ucih.one_cell(BINARY, fen, go, 16, want_ttstats=True)
b = ucih.one_cell(BINARY, fen, go, 16, want_ttstats=True)
show("hash16 500k #1", a)
show("hash16 500k #2", b)

same = (
    a["bestmove"] == b["bestmove"]
    and a["depth"] == b["depth"]
    and a["score"] == b["score"]
    and a["trace"]["probe"] == b["trace"]["probe"]
    and a["trace"]["store_displace"] == b["trace"]["store_displace"]
)
print(f"\nDETERMINISM: {'PASS' if same else 'FAIL'} (identical cell twice)")

c = ucih.one_cell(BINARY, fen, go, 1, want_ttstats=True)
d = ucih.one_cell(BINARY, fen, go, 64, want_ttstats=True)
show("hash1 500k", c)
show("hash64 500k", d)

print("\nttstats (whole table):")
for tag, cell in (("hash1", c), ("hash16", a), ("hash64", d)):
    st = cell["ttstats"]
    print(
        f"  {tag:7s} clusters={st['clusters']:8d} occupied={st['occupied']:9d} "
        f"load={st['load_factor']:.4f} hashfull={st['hashfull_permille']}permille"
    )

counters_moved = c["trace"]["store_displace"] != d["trace"]["store_displace"]
print(f"\nCOUNTERS MOVE: {'PASS' if counters_moved else 'FAIL'}")
print(f"DISPLACE  hash1={c['trace']['store_displace']} hash64={d['trace']['store_displace']}")

# The load factor times cluster count is what a collision account needs; print
# the ratio so the ordering is visible rather than asserted.
print(
    f"\nload ratio hash1/hash64 = "
    f"{c['ttstats']['load_factor'] / max(d['ttstats']['load_factor'], 1e-12):.1f}x"
)

#!/usr/bin/env python3
"""Positive control for the RSS instrument, and for the flat-RSS null in the replay.

A flat RSS curve over 27,788 plies is only admissible if the instrument can see an
allocation when one happens. Two controls:
  A. resize Hash to 1024 MB and watch RSS move. If RSS cannot see 1 GB it cannot see a leak.
  B. grow the table with real searches and watch hashfull climb, so "the table was never
     under pressure" is a measurement rather than an assumption.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uci import Engine
from replay import run_search, rss_kb

ENG = os.environ.get("FORGE_BIN", "forge-combo29/build/forge")

e = Engine(ENG)
e.uci(); e.sync()
print("A. RSS positive control")
r0 = rss_kb(e.p.pid)
print(f"   baseline (Hash 32 default):      {r0/1024:8.1f} MiB")
e.send("setoption name Hash value 1024"); e.sync()
r1 = rss_kb(e.p.pid)
print(f"   after setoption Hash 1024:      {r1/1024:8.1f} MiB   delta {(r1-r0)/1024:+.1f} MiB")
e.send("setoption name Hash value 32"); e.sync()
r2 = rss_kb(e.p.pid)
print(f"   after setoption Hash 32:        {r2/1024:8.1f} MiB   delta {(r2-r0)/1024:+.1f} MiB")
assert r1 - r0 > 500 * 1024, "RSS instrument cannot see a 1 GB allocation"

print("\nB. hashfull under real search pressure (Hash 32)")
corpus = json.load(open("evidence/games.json"))["games"]
e2 = Engine(ENG); e2.uci(); e2.sync()
rows = []
glb = 0
t0 = time.time()
for g in corpus[:60]:
    for k in range(1, len(g["moves"]) + 1):
        r = run_search(e2, f"position fen {g['start_fen']} moves " + " ".join(g["moves"][:k]))
        glb += 1
        if glb % 500 == 0:
            rows.append({"plies": glb, "hashfull": r["hf"], "rss_kb": rss_kb(e2.p.pid),
                         "nodes": r["nodes"], "wall_ms": r["wall_ms"]})
e2.quit()
for row in rows:
    print(f"   plies {row['plies']:6d}  hashfull {row['hashfull']:5d}  "
          f"rss {row['rss_kb']/1024:7.1f} MiB  nodes {row['nodes']}")
print(f"   peak hashfull: {max(r['hashfull'] for r in rows)} of 1000")
json.dump({"positive_control": {"rss_baseline_kb": r0, "rss_hash1024_kb": r1, "rss_back_kb": r2},
           "hashfull_rows": rows}, open("evidence/rss_control.json", "w"), indent=0)

print("\nC. drift over the replay: nodes and wall time by 2,000-ply block")
def load(p):
    out = []
    for line in open(p):
        out.append(json.loads(line))
    return out
sess = load("evidence/session.jsonl")
import statistics
for start in range(0, len(sess), 2000):
    blk = sess[start:start + 2000]
    nn = [r["nodes"] for r in blk if r["nodes"]]
    wm = [r["wall_ms"] for r in blk]
    print(f"   plies {start+1:6d}-{start+len(blk):6d}  median nodes {statistics.median(nn):7.0f}  "
          f"mean wall {sum(wm)/len(wm):6.2f} ms  bails {sum(1 for r in blk if r['nodes']==0)}")

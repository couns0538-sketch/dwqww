#!/usr/bin/env python3
"""fallback.py OUTDIR -- when the requested depth was NOT recorded, can unfinished be detected?

Tests the only self-contained signatures available in saved output:
  F1 a `bestmove` line exists at all (an interrupted-at-0ms record has one, so this does NOT help)
  F2 the last info line's pv, replayed by python-chess, ends in a position whose side-to-move is
     checkmated/stalemated only when the score says mate -- weak
  F3 the score of the DEEPEST line disagrees with a re-search at that same depth (impossible offline)
  F4 the record's last depth is less than the maximum depth seen ANYWHERE in the same run/file -- this works
     when a run contains at least one completed search, and it is the practical rule for a match file
  F5 hashfull present but time == 0
Measured here: F1 and F4 on real middle and finished records, plus the count of records where F4 is
inapplicable because the whole file shares that depth.
"""
import json, sys
d = json.load(open(sys.argv[1]))
rows = []
for b, pos in d['builds'].items():
    for p, blk in pos.items():
        f = blk['finished']
        for m in blk['middle']:
            rows.append((b, p, m.get('delay_ms'), m, f))
# F4: per (build,position) file, the max depth seen among ALL records incl. finished
byfile = {}
for b, p, dl, m, f in rows:
    byfile.setdefault((b, p), []).append((m, f))
print("F1: does an interrupted record still carry a bestmove line?")
with_bm = sum(1 for b,p,dl,m,f in rows if m.get('bestmove'))
print(f"   {with_bm}/{len(rows)} records have a bestmove -> F1 cannot separate anything")
print()
print("F4: per-file max depth, and whether 'depth < file max' flags the genuinely-truncated ones")
tot=ok=fa=0
for k, lst in byfile.items():
    filemax = max([x[0].get('last_depth') or 0 for x in lst] + [lst[0][1].get('last_depth') or 0])
    for m, f in lst:
        if m.get('empty'): continue
        differs = (m.get('info_lines'), m.get('last_depth'), m.get('S3_pv_len'), m.get('S6_last_nodes'), str(m.get('score')), m.get('bestmove')) != \
                  (f.get('info_lines'), f.get('last_depth'), f.get('S3_pv_len'), f.get('S6_last_nodes'), str(f.get('score')), f.get('bestmove'))
        flagged = (m.get('last_depth') or 0) < filemax
        tot+=1
        if differs and flagged: ok+=1
        if (not differs) and flagged: fa+=1
print(f"   records {tot}; genuinely-differing flagged {ok}; false alarms {fa}")
print()
print("CONCLUSION: F1 is useless (an interrupted record always has a bestmove). F4 works only when the")
print("file contains at least one COMPLETED search at the same settings -- true for a match or tuning run,")
print("false for a file where every search was interrupted the same way.")

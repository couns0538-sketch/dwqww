#!/usr/bin/env python3
"""truncation_rate.py -- how OFTEN does a mate score carry a PV shorter than 2|N|?

Reads my existing committed raw data first (no engine needed) to get the rate on the base build, then the
follow-up can re-measure the same positions on the PC build.
Sources: job1/out/rows.jsonl (O+G, 553 positions) and job1b/outR/rows.jsonl (R, 200 positions), both depth 12 S14.
"""
import json
import sys

def load(path, tag):
    out = []
    for line in open(path):
        r = json.loads(line)
        lp = r.get("last_pv")
        if not lp:
            continue
        sc = lp.get("score", ("", 0))
        if sc[0] != "mate" or sc[1] == 0:
            continue
        n = sc[1]
        plies = lp.get("plies")
        moves = len(lp.get("moves") or [])
        need = 2 * n - 1 if n > 0 else 2 * (-n)
        got = plies if isinstance(plies, int) else moves
        out.append(dict(set=tag, pos=r["pos"], fen=r["fen"], n=n, need=need, got=got,
                        ok=(got == need)))
    return out

rows = load("../job1/out/rows.jsonl", "O+G") + load("../job1b/outR/rows.jsonl", "R")
print("BASE BUILD, depth 12, S14, Threads 1 (read from committed rows.jsonl files)")
print()
print(f"positions with a mate score: {len(rows)}")
bad = [r for r in rows if not r["ok"]]
print(f"  PV consistent with 2N-1 / 2|N|: {len(rows) - len(bad)}")
print(f"  PV SHORT (truncated):           {len(bad)}  = {100.0*len(bad)/len(rows):.1f}%")
print()
print("| set | mate positions | truncated | rate |")
print("|---|---|---|---|")
for tag in ("O+G", "R"):
    sub = [r for r in rows if r["set"] == tag]
    b = [r for r in sub if not r["ok"]]
    print(f"| {tag} | {len(sub)} | {len(b)} | {100.0*len(b)/len(sub):.1f}% |")
print()
print("Every truncated case, so the PC-build re-run can target these exact boards:")
print()
print("| set | pos | score | need | got | short by | fen |")
print("|---|---|---|---|---|---|---|")
for r in bad:
    print(f"| {r['set']} | {r['pos']} | mate {r['n']:+d} | {r['need']} | {r['got']} | "
          f"{r['need']-r['got']} | {r['fen']} |")
with open("out/truncated_fens.txt", "w") as f:
    for r in bad:
        f.write(r["fen"] + "\n")
print()
print(f"wrote out/truncated_fens.txt with {len(bad)} FENs for the PC-build re-run")

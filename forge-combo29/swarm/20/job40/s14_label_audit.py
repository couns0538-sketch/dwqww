#!/usr/bin/env python3
"""s14_label_audit.py — seat 20 job 40: do other seats' "S14" node numbers actually match S14, or the defaults?

Triggered by S-C23: seat 27 labelled `cp 30 / 56720 nodes` as "S14" but that is exactly the DEFAULT-settings
answer, while real S14 gives `d2d4 / cp 24 / 22459`.

Method: I establish the ground-truth numbers myself on both builds for the two regimes, then scan every seat's
FINDINGS.md for numbers that could be checked against them. A hit on the default number where the line says S14 is
a regime mislabel; a hit on the S14 number where the line says S14 is correct.

usage: s14_label_audit.py <base-exe> <pc-exe> <outdir>
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

BASE, PC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
SP = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
S14 = [("Threads", 1), ("Hash", 16), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("OwnBook", "false")]
PC20 = S14 + [("Hash", 16), ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true")]


def one(exe, opts, go="go depth 12"):
    e = Engine(exe, opts=opts)
    try:
        e.position(SP)
        r = e.search(go, 400)
    finally:
        e.close()
    return r


truth = {}
print("== ground truth, startpos depth 12, Threads 1, fresh process")
for label, exe, opts in (("base_defaults", BASE, []), ("base_s14", BASE, S14),
                         ("pc_defaults", PC, []), ("pc_pc20", PC, PC20)):
    r = one(exe, opts)
    truth[label] = {"bestmove": r["bestmove"], "score": r["score"], "nodes": r["nodes"]}
    print(f"  {label:14s} {r['bestmove']:7s} {str(r['score']):8s} nodes {r['nodes']}")

default_nodes = {truth["base_defaults"]["nodes"], truth["pc_defaults"]["nodes"]}
s14_nodes = {truth["base_s14"]["nodes"], truth["pc_pc20"]["nodes"]}
print(f"\n  DEFAULT-settings node counts: {sorted(default_nodes)}")
print(f"  S14/PC20 node counts:        {sorted(s14_nodes)}")

print("\n== scanning every seat's FINDINGS.md for these numbers near the string 'S14'")
hits = []
for n in range(1, 61):
    s = f"{n:02d}"
    if not subprocess.run(["git", "ls-remote", "origin", f"refs/heads/for-fable-and-opus/swarm-{s}"],
                          capture_output=True, text=True).stdout.strip():
        continue
    if subprocess.run(["git", "fetch", "-q", "--depth", "1", "origin",
                       f"for-fable-and-opus/swarm-{s}"], capture_output=True).returncode != 0:
        continue
    show = subprocess.run(["git", "show", f"FETCH_HEAD:forge-combo29/swarm/{s}/FINDINGS.md"],
                          capture_output=True, text=True)
    if show.returncode != 0:
        continue
    for line in show.stdout.split("\n"):
        if "S14" not in line:
            continue
        nums = {int(x) for x in re.findall(r"\b(\d{4,7})\b", line)}
        dn = nums & default_nodes
        sn = nums & s14_nodes
        if dn and not sn:
            hits.append({"seat": s, "kind": "S14_LABEL_BUT_DEFAULT_NUMBER",
                         "default_numbers": sorted(dn), "text": line.strip()[:200]})
        elif dn and sn:
            hits.append({"seat": s, "kind": "MIXED (line has both)",
                         "default_numbers": sorted(dn), "s14_numbers": sorted(sn),
                         "text": line.strip()[:200]})

print(f"\n  {len(hits)} suspicious lines")
for h in hits:
    print(f"   seat {h['seat']}: {h['kind']}  default={h.get('default_numbers')} "
          f"s14={h.get('s14_numbers','')}")
    print(f"      {h['text'][:150]}")

with open(os.path.join(OUT, "s14_label_audit.json"), "w") as f:
    json.dump({"truth": truth, "hits": hits}, f, indent=1)
print(f"\nwrote s14_label_audit.json")

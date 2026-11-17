#!/usr/bin/env python3
"""19-C52: the last separator - my QUIET subset vs seat 27's quiet stratum.

Stratification is identical on both sides: |white_minus_black material| <= 4, pawn=1 N/B=3 R=5 Q=9.
Same-move restriction applied on both sides. softnodes 2000.
Reported with an explicit power statement, because a 14-cell sample cannot separate 41 % from 63.6 %.
"""
import re, json, chess
from math import comb, sqrt

HERE = "/agent/repos/dwqww/forge-combo29/swarm/19/checks/softgran"
VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}


def mat(fen):
    b = chess.Board(fen)
    m = 0
    for sq, p in b.piece_map().items():
        v = VAL.get(p.piece_type, 0)
        m += v if p.color == chess.WHITE else -v
    return m, len(b.piece_map())


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    mm = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - mm) / d, (c + mm) / d)


def power_at(n, p_true, alpha=0.05):
    """Exact two-sided sign-test power at n decided cells."""
    rej = [k for k in range(n + 1)
           if min(1.0, 2 * sum(comb(n, i) for i in range(min(k, n - k) + 1)) / 2 ** n) < alpha]
    return sum(comb(n, k) * p_true ** k * (1 - p_true) ** (n - k) for k in rej)


def mine():
    txt = open(HERE + "/raw_result.txt").read()
    sec = txt.split("per-position:")[1]
    lines = [l for l in sec.splitlines() if l.strip()]
    rows, i = [], 0
    while i < len(lines):
        m = re.match(r"^\s+(\d+) (.+)$", lines[i])
        if not m:
            i += 1
            continue
        fen = m.group(2).strip()
        s = re.match(r"^\s+s14\s+2k: (\S+) d(\d+)\s+n(\d+)", lines[i + 1])
        p = re.match(r"^\s+pc20\s+2k: (\S+) d(\d+)\s+n(\d+)", lines[i + 2])
        assert s and p, (lines[i + 1], lines[i + 2])
        rows.append({"fen": fen,
                     "s14": (s.group(1), int(s.group(2))),
                     "pc20": (p.group(1), int(p.group(2)))})
        i += 3
    assert len(rows) == 200, len(rows)
    return rows


def theirs():
    d = json.load(open("/home/ubuntu/s27/sign_600_2000.json"))
    return [{"fen": x["fen"],
             "s14": (x["S14"]["bestmove"], x["S14"]["depth"]),
             "pc20": (x["PC20"]["bestmove"], x["PC20"]["depth"])} for x in d["cells"]]


def tally(rows, quiet_only, maxmat=4):
    sm = [r for r in rows if r["s14"][0] == r["pc20"][0]]
    if quiet_only:
        sm = [r for r in sm if abs(mat(r["fen"])[0]) <= maxmat]
    pcd = sum(1 for r in sm if r["pc20"][1] > r["s14"][1])
    s14d = sum(1 for r in sm if r["s14"][1] > r["pc20"][1])
    return len(sm), pcd, s14d


out = []
for label, rows in (("MINE (200 pos)", mine()), ("SEAT 27 (600 pos)", theirs())):
    for qname, quiet in (("ALL", False), ("QUIET |mat|<=4", True)):
        n, pcd, s14d = tally(rows, quiet)
        dec = pcd + s14d
        lo, hi = wilson(pcd, dec)
        rate = 100.0 * pcd / dec if dec else 0.0
        out.append("%-16s %-14s same-move %3d  decided %3d  PC20 %2d (%5.1f%%)  CI [%.3f,%.3f]" % (
            label, qname, n, dec, pcd, rate, lo, hi))
    out.append("")

for l in out:
    print(l)

# the decisive statement: can my quiet subset discriminate?
n_m, p_m, s_m = tally(mine(), True)
dec_m = p_m + s_m
print("MY QUIET decided cells: %d" % dec_m)
for ptrue in (0.414, 0.636):
    print("  exact power at n=%d to detect p=%.3f : %.3f" % (dec_m, ptrue, power_at(dec_m, ptrue)))
print()
print("Can n=%d separate 41.4%% from 63.6%%? " % dec_m +
      ("YES" if power_at(dec_m, 0.636) > 0.8 else "NO - both are well inside the same interval"))

open(HERE + "/quiet_subset_result.txt", "w").write("\n".join(out) + "\n")

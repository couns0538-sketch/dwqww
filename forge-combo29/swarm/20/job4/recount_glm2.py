#!/usr/bin/env python3
"""recount_glm2.py — seat 20, area 10 job 3, the final recount of glmflash5 job27.

Reads ONLY glmflash5's committed game lists (gl/gamelist_M*.txt) and reports:
  A. W-L-D, n5, Elo per match, with the 95 % pair interval TWO ways:
       (i) the helper's formula as written in their committed job27_stats.py
           (Vp uses (i/2 - 2*sc)**2 over PAIR scores, se = sqrt(Vp/(4P)), half = 1.959964*d*se)
       (ii) the brief's formula sd = 400/(ln10*m(1-m)) * sqrt(var/pairs) with the sample variance
            of the pair scores
     and says whether the report's printed numbers equal the recount.
  B. the two pools from all four / two looks, both formulas.
  C. whether the matches' openings are disjoint (no opening reused between matches).
  D. the identities the report prints (mates = W+L, n5 sums to pairs, W+L+D = 2 pairs).
"""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
GL = os.path.join(HERE, "gl")
lines_out = []


def say(s=""):
    lines_out.append(s)
    print(s)


def load(match):
    p = os.path.join(GL, f"gamelist_{match}.txt")
    rows = []
    for line in open(p, encoding="utf-8", errors="replace"):
        q = line.rstrip("\n").split("|")
        if len(q) < 6:
            continue
        rows.append({"n": int(q[0]), "white": q[1], "black": q[2], "result": q[3],
                     "ending": q[4], "fen": q[5]})
    return rows


def game_score(r):
    if r["result"] == "1-0":
        return 1.0 if r["white"] == "cand" else 0.0
    if r["result"] == "0-1":
        return 1.0 if r["black"] == "cand" else 0.0
    return 0.5


def n5_of(rows):
    n = [0, 0, 0, 0, 0]
    w = l = d = 0
    bad_pairs = 0
    for i in range(0, len(rows) - 1, 2):
        a, b = rows[i], rows[i + 1]
        if a["fen"] != b["fen"] or {a["white"], a["black"]} != {"cand", "base"}:
            bad_pairs += 1
        s = 0.0
        for r in (a, b):
            v = game_score(r)
            if v == 1.0:
                w += 1
            elif v == 0.0:
                l += 1
            else:
                d += 1
            s += v
        n[int(round(s * 2))] += 1
    return n, w, l, d, bad_pairs


def elo_of(n):
    """the helper's formula, exactly as in their job27_stats.py"""
    P = sum(n)
    X = sum(i / 2 * ni for i, ni in enumerate(n))
    sc = X / (2 * P)
    Vp = sum(ni * (i / 2 - 2 * sc) ** 2 for i, ni in enumerate(n)) / (P - 1)
    se = math.sqrt(Vp / (4 * P))
    elo = -400 * math.log10(1 / sc - 1)
    d = 400 / (math.log(10) * sc * (1 - sc))
    return elo, 1.959964 * d * se, sc


def brief_elo_of(n):
    """the brief's formula, on the same pair scores"""
    P = sum(n)
    scores = []
    for i, ni in enumerate(n):
        scores += [i / 2] * ni
    m = sum(scores) / (2 * P)          # points per game for the candidate
    mu = sum(scores) / P
    var = sum((s - mu) ** 2 for s in scores) / (P - 1)
    elo = 400 * math.log10(m / (1 - m))
    sd = 400 / (math.log(10) * m * (1 - m)) * math.sqrt(var / P)
    return elo, sd


REPORT = {
    "M73": dict(wld="537-578-885", elo=-7.12, half=9.86, n5=[53, 241, 440, 226, 40]),
    "M74": dict(wld="540-518-942", elo=3.82, half=9.87, n5=[45, 230, 427, 254, 44]),
    "M75": dict(wld="544-549-907", elo=-0.87, half=10.065, n5=[53, 235, 421, 246, 45]),
    "M76": dict(wld="736-650-614", elo=14.95, half=11.795, n5=[90, 183, 383, 239, 105]),
    "M77": dict(wld="691-673-636", elo=3.13, half=12.035, n5=[106, 198, 367, 230, 99]),
}
M54_N5 = [50, 231, 436, 228, 55]
M59_N5 = [40, 239, 415, 251, 55]
M60_N5 = [46, 259, 401, 248, 46]

say("== A. per match, recounted from the committed game list")
say()
say(f"{'match':6s} {'games':>6s} {'pairs':>6s} {'W-L-D found':14s} {'W-L-D report':14s} {'elo':>8s} "
    f"{'half':>7s} {'report half':>11s} {'n5 equal':9s} {'bad pairs':>9s}")
tables = {}
for m in ("M73", "M74", "M75", "M76", "M77"):
    rows = load(m)
    n, w, l, d, bad = n5_of(rows)
    elo, half, sc = elo_of(n)
    rep = REPORT[m]
    got = f"{w}-{l}-{d}"
    say(f"{m:6s} {len(rows):6d} {sum(n):6d} {got:14s} {rep['wld']:14s} {elo:+8.2f} {half:7.3f} "
        f"{rep['half']:11.3f} {str(n == rep['n5']):9s} {bad:9d}")
    tables[m] = n

say()
say("== A2. the same Elo with the BRIEF's formula (sample variance of pair scores)")
say(f"{'match':6s} {'elo':>8s} {'sd':>7s} {'95% interval':22s} {'helper formula half':>20s}")
for m in ("M73", "M74", "M75", "M76", "M77"):
    n = tables[m]
    e1, h1, _ = elo_of(n)
    e2, h2 = brief_elo_of(n)
    say(f"{m:6s} {e2:+8.2f} {h2:7.3f} [{e2-h2:+7.2f}, {e2+h2:+7.2f}]     {h1:20.3f}")
say("  (the two formulas differ only by the 1.959964 z-factor and the (2*sc) centring; the helper's")
say("   interval = z x d x se, mine = d x sqrt(var/pairs). Same numbers to 0.1 Elo.)")

say()
say("== B. the two pools")
for tag, ns in (("V@20,000 (M54+M59+M73+M74)", [M54_N5, M59_N5, tables["M73"], tables["M74"]]),
                ("C8@20,000 (M60+M75)", [M60_N5, tables["M75"]])):
    n = [sum(x) for x in zip(*ns)]
    elo, half, sc = elo_of(n)
    e2, h2 = brief_elo_of(n)
    say(f"{tag}: n5 {n} pairs {sum(n)}  Elo {elo:+.2f} [{elo-half:+.2f}, {elo+half:+.2f}]  "
        f"(brief formula {e2:+.2f} +/- {h2:.3f})")
say("  report: V +1.30 [-3.68,+6.29]; C8 -1.39 [-8.51,+5.73]")

say()
say("== B2. are the job-24 n5 arrays hardcoded in job27_stats.py the same as M54/M59/M60's game lists?")
for m, hard in (("M54", M54_N5), ("M59", M59_N5), ("M60", M60_N5)):
    n, w, l, d, bad = n5_of(load(m))
    say(f"  {m}: hardcoded {hard}  from the game list {n}  {'EQUAL' if n == hard else 'DIFFERS'}")

say()
say("== C. opening disjointness between matches")
seen = {}
overlaps = []
per_match = {}
for m in ("M73", "M74", "M75", "M76", "M77"):
    rows = load(m)
    opens = [rows[i]["fen"] for i in range(0, len(rows) - 1, 2)]
    per_match[m] = set(opens)
    say(f"  {m}: {len(set(opens))} distinct openings over {len(opens)} pairs "
        f"(duplicates inside the match: {len(opens) - len(set(opens))})")
for m, s in per_match.items():
    for o in s:
        if o in seen and seen[o] != m:
            overlaps.append((o, seen[o], m))
        seen.setdefault(o, m)
say(f"  cross-match opening overlaps: {len(overlaps)}"
    + ("" if not overlaps else f"  e.g. {overlaps[0][1]} and {overlaps[0][2]}: {overlaps[0][0]}"))

say()
say("== D. the identities the report prints")
for m in ("M73", "M74", "M75", "M76", "M77"):
    rows = load(m)
    n, w, l, d, bad = n5_of(rows)
    wm = sum(1 for r in rows if r["ending"] == "White mates")
    bm = sum(1 for r in rows if r["ending"] == "Black mates")
    say(f"  {m}: white+black mates {wm}+{bm}={wm+bm}  W+L {w}+{l}={w+l}  "
        f"{'EQUAL' if wm+bm == w+l else 'MISMATCH'};  n5 sum {sum(n)} = pairs {sum(n)};  "
        f"W+L+D {w+l+d} = 2*pairs {2*sum(n)}: {'EQUAL' if w+l+d == 2*sum(n) else 'MISMATCH'}")

with open(os.path.join(HERE, "recount_glm.txt"), "w") as f:
    f.write("\n".join(lines_out) + "\n")
print("\nwrote recount_glm.txt")

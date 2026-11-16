import math, sys

# Pair-level (pentanomial) Elo estimate with 95% interval.
# Each pair = 2 games. Pair point total s in {0,0.5,1,1.5,2} for the CANDIDATE.
# n[0..4] counts pairs by s*2. Validate per match against fastchess output first.

def pair_counts(path):
    rows = [l.strip().split("|") for l in open(path)]
    n = [0, 0, 0, 0, 0]
    for i in range(0, len(rows), 2):
        a, b = rows[i], rows[i + 1]
        s = 0.0
        for row in (a, b):
            white, result = row[1], row[3]
            if result == "1/2-1/2":
                s += 0.5
            elif (result == "1-0") == (white == "cand"):
                s += 1.0
        n[int(round(s * 2))] += 1
    return n

def stats(n):
    P = sum(n)                                  # number of pairs
    X = sum((i / 2) * ni for i, ni in enumerate(n))   # total game points for cand
    s = X / (2 * P)                             # mean game score
    Vp = sum(ni * (i / 2 - 2 * s) ** 2 for i, ni in enumerate(n)) / (P - 1)
    se = math.sqrt(Vp / (4 * P))                # se of game score
    elo = -400 * math.log10(1 / s - 1)
    delo = 400 / (math.log(10) * s * (1 - s))
    lo, hi = elo - 1.959964 * delo * se, elo + 1.959964 * delo * se
    los = 0.5 * (1 + math.erf((s - 0.5) / math.sqrt(2 * se * se)))
    return P, s, elo, lo, hi, delo * se, los

jobs = [
    ("H1 (validate vs fc +12.17+-14.80)", ["gamelist_H1.txt"]),
    ("S1 (validate vs fc +9.38+-14.84)", ["gamelist_S1.txt"]),
    ("H2 (validate vs fc +3.47+-14.99)", ["gamelist_H2.txt"]),
    ("S2 (validate vs fc +3.13+-14.75)", ["gamelist_S2.txt"]),
    ("B  (validate vs fc +6.25+-13.82)", ["gamelist_B.txt"]),
    ("HD pooled H1+H2", ["gamelist_H1.txt", "gamelist_H2.txt"]),
    ("SMP pooled S1+S2", ["gamelist_S1.txt", "gamelist_S2.txt"]),
    ("B single", ["gamelist_B.txt"]),
]
for name, paths in jobs:
    n = [0] * 5
    for p in paths:
        c = pair_counts(p)
        n = [a + b for a, b in zip(n, c)]
    P, s, elo, lo, hi, seo, los = stats(n)
    print(f"{name}: pairs={P} n5={n} score={s:.5f} Elo={elo:+.2f} "
          f"95%[{lo:+.2f},{hi:+.2f}] se={seo:.2f} LOS={los*100:.1f}%")

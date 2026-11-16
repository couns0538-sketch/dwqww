import math, random

def key(fen):
    return " ".join(fen.split()[:4])

def load(path):
    return [l.strip().split("|") for l in open(path)]

def pair_counts(rows, cand_name, drop_last_incomplete=True):
    n = [0, 0, 0, 0, 0]; W = L = D = 0; P = 0
    for i in range(0, len(rows) - 1, 2):
        a, b = rows[i], rows[i + 1]
        s = 0.0
        for row in (a, b):
            white, result = row[1], row[3]
            if result == "1/2-1/2":
                s += 0.5; D += 1
            elif (result == "1-0") == (white == cand_name):
                s += 1.0; W += 1
            else:
                L += 1
        n[int(round(s * 2))] += 1; P += 1
    return n, W, L, D, P

def stats(n):
    P = sum(n)
    X = sum(i / 2 * ni for i, ni in enumerate(n))
    s = X / (2 * P)
    Vp = sum(ni * (i / 2 - 2 * s) ** 2 for i, ni in enumerate(n)) / (P - 1)
    se = math.sqrt(Vp / (4 * P))
    elo = -400 * math.log10(1 / s - 1)
    d = 400 / (math.log(10) * s * (1 - s))
    lo, hi = elo - 1.959964 * d * se, elo + 1.959964 * d * se
    los = 0.5 * (1 + math.erf((s - 0.5) / math.sqrt(2 * se * se)))
    return P, s, elo, lo, hi, d * se, los

# difference between two matches: score diff on pooled pair structure is not
# directly meaningful across different openings; use independent-look z-test on
# the two matches' Elo se's, plus a score-difference interval from the two
# pentanomial variances (they are independent samples -> var adds).
def diff(e1, se1, e2, se2):
    d = e1 - e2
    # se of Elo difference via delta method on both matches
    z = d / math.sqrt(se1 ** 2 + se2 ** 2)
    return d, 1.959964 * math.sqrt(se1 ** 2 + se2 ** 2), z

m1, *_ = pair_counts(load("gamelist_M1.txt"), "cand")
m1b, W, L, D, P = pair_counts(load("gamelist_M1b.txt"), "cand")
k0b, kW, kL, kD, kP = pair_counts(load("gamelist_K0b.txt"), "A")

for name, n in [("K0b (cand=A)", k0b), ("M1b", m1b)]:
    P_, s, elo, lo, hi, seo, los = stats(n)
    print(f"{name}: pairs={P_} n5={n} score={s:.5f} Elo={elo:+.2f} 95%[{lo:+.2f},{hi:+.2f}] se={seo:.2f} LOS={los*100:.1f}%")

P1, s1, e1, l1, h1, se1, lo1 = stats(m1)
P2, s2, e2, l2, h2, se2, lo2 = stats(m1b)
n_pool = [a + b for a, b in zip(m1, m1b)]
Pp, sp, ep, lp, hp, sep, losp = stats(n_pool)
print(f"M1+M1b POOL: pairs={Pp} n5={n_pool} score={sp:.5f} Elo={ep:+.2f} 95%[{lp:+.2f},{hp:+.2f}] se={sep:.2f} LOS={losp*100:.1f}%")
d, dd, z = diff(e1, se1, e2, se2)
print(f"difference M1 - M1b: {d:+.2f} Elo, 95% [{d-dd:+.2f},{d+dd:+.2f}] (z={z:+.2f})")
print(f"M1b W-L-D={W}-{L}-{D} over {2*P} games ({P} complete pairs)")

# openings shared between job 3 matches and job 2 (must be 0)
used2 = set()
for p in ["gamelist_K0.txt", "gamelist_K1.txt", "gamelist_M1.txt"]:
    for row in load(p):
        used2.add(key(row[5]))
shared = 0
for p in ["gamelist_K0b.txt", "gamelist_M1b.txt"]:
    for row in load(p):
        if key(row[5]) in used2:
            shared += 1
print(f"openings shared job3 vs job2 (game rows): {shared}")

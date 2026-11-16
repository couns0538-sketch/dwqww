import sys, os, math
from collections import Counter

# deepseek6 long 23, part 3: pools over every look that glmflash5 grouped, computed from
# MY n5 vectors (rebuilt from its gamelist rows), plus two structural checks on pairing.

D = sys.argv[1]
MATCHES = ["M46", "M47", "M48", "M49", "M50", "M51", "M52", "M53", "M54", "M55", "M56", "M57", "M58", "M59", "M60"]


def load(m):
    rows = []
    for line in open(os.path.join(D, "gamelist_%s.txt" % m)):
        line = line.rstrip("\n")
        if not line:
            continue
        f = line.split("|")
        rows.append(dict(white=f[1], black=f[2], result=f[3], ending=f[4], fen=f[5]))
    return rows


def score(r):
    if r["result"] == "1/2-1/2":
        return 0.5
    return 1.0 if (r["result"] == "1-0") == (r["white"] == "cand") else 0.0


def n5of(rows):
    n5 = [0, 0, 0, 0, 0]
    for i in range(0, len(rows) - 1, 2):
        s = score(rows[i]) + score(rows[i + 1])
        n5[int(round(s * 2))] += 1
    return n5


def elo(sc):
    return -400.0 * math.log10(1.0 / sc - 1.0)


def describe(tag, n5s):
    n5 = [0] * 5
    for v in n5s:
        for i in range(5):
            n5[i] += v[i]
    P = sum(n5)
    mi = sum(i * n5[i] for i in range(5)) / P
    sc = mi / 4.0
    var = sum(n5[i] * (i - mi) ** 2 for i in range(5)) / (P - 1)
    se = math.sqrt(var / P) / 4.0
    e = elo(sc)
    d = 400.0 / (math.log(10.0) * sc * (1.0 - sc))
    h = 1.959964 * d * se
    print("%s: pairs=%d n5=%s score=%.6f Elo=%+.2f 95%%[%+.2f,%+.2f]" %
          (tag, P, n5, sc, e, e - h, e + h))


data = {m: load(m) for m in MATCHES}
n5 = {m: n5of(data[m]) for m in MATCHES}

print("== EVERY LOOK, rebuilt from rows")
for m in MATCHES:
    describe(m, [n5[m]])

print()
print("== POOLS, glmflash5's groupings")
describe("variant@2000 (M49+M51+M52, 3 looks)", [n5[x] for x in ["M49", "M51", "M52"]])
describe("variant@2000 (M49+M51+M52+M55+M56, 5 looks)", [n5[x] for x in ["M49", "M51", "M52", "M55", "M56"]])
describe("CED8alone@2000 (M53+M57+M58, 3 looks)", [n5[x] for x in ["M53", "M57", "M58"]])
describe("variant@20000 (M54+M59, 2 looks)", [n5[x] for x in ["M54", "M59"]])
print()
print("== POOLS over the whole job-22 pair as well (M46/M50 are the same openings at 2000 and 20000)")
describe("R1@2000 (M46+M47) - job 22", [n5[x] for x in ["M46", "M47"]])
describe("R1@20000 (M50+M48) - job 22", [n5[x] for x in ["M50", "M48"]])
describe("R1 pool both node budgets (M46+M47+M50+M48, 4 looks)", [n5[x] for x in ["M46", "M47", "M50", "M48"]])

print()
print("== STRUCTURE OF A PAIR (per match): how often both games of one opening end the same way")
for m in MATCHES:
    rows = data[m]
    same_res = same_end = both_cand_won = both_drawn = split = 0
    P = 0
    for i in range(0, len(rows) - 1, 2):
        a, b = rows[i], rows[i + 1]
        P += 1
        if a["result"] == b["result"]:
            same_res += 1
            if a["ending"] == b["ending"]:
                same_end += 1
        sa = score(a) + score(b)
        if sa == 2.0:
            both_cand_won += 1
        elif sa == 1.0:
            both_drawn += 1
        elif sa == 0.0:
            pass
        else:
            split += 1
    print("%s pairs=%d same_result=%d (%.1f%%) same_result_and_ending=%d cand_won_both=%d both_drawn=%d split_1_of_2=%d cand_lost_both=%d" %
          (m, P, same_res, 100.0 * same_res / P, same_end, both_cand_won, both_drawn, split, P - both_cand_won - both_drawn - split))

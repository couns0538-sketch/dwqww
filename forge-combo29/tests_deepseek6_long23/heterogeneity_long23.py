import sys, os, math

# deepseek6 long 23, part 4: is the spread between looks consistent with ONE strength?
# Cochran's Q over the pair-score means of the looks of one configuration, plus the
# random-effects (between-look) share of the variance. Pure arithmetic on the n5 vectors.

D = sys.argv[1]

GROUPS = {
    "variant@2000": ["M49", "M51", "M52", "M55", "M56"],
    "CED8alone@2000": ["M53", "M57", "M58"],
    "variant@20000": ["M54", "M59"],
    "R1@2000": ["M46", "M47"],
    "R1@20000": ["M50", "M48"],
}


def load(m):
    rows = []
    for line in open(os.path.join(D, "gamelist_%s.txt" % m)):
        line = line.rstrip("\n")
        if line:
            f = line.split("|")
            rows.append((f[1], f[3]))
    return rows


def score(white, result):
    if result == "1/2-1/2":
        return 0.5
    return 1.0 if (result == "1-0") == (white == "cand") else 0.0


def n5of(rows):
    n5 = [0] * 5
    for i in range(0, len(rows) - 1, 2):
        s = score(*rows[i]) + score(*rows[i + 1])
        n5[int(round(s * 2))] += 1
    return n5


def stat(n5):
    P = sum(n5)
    mi = sum(i * n5[i] for i in range(5)) / P
    var = sum(n5[i] * (i - mi) ** 2 for i in range(5)) / (P - 1)
    return P, mi, var            # mean and variance of i (half-point units)


def elo_of(mi):
    sc = mi / 4.0
    return -400.0 * math.log10(1.0 / sc - 1.0)


for tag, ms in GROUPS.items():
    print("== %s : %s" % (tag, " ".join(ms)))
    vals = []
    for m in ms:
        P, mi, var = stat(n5of(load(m)))
        vals.append((m, P, mi, var))
        print("   %-4s pairs=%d mean_i=%.6f var_i=%.6f Elo(look)=%+.2f" % (m, P, mi, var, elo_of(mi)))
    w = [P / var for (_, P, _, var) in vals]
    x = [mi for (_, _, mi, _) in vals]
    W = sum(w)
    xbar = sum(wi * xi for wi, xi in zip(w, x)) / W
    Q = sum(wi * (xi - xbar) ** 2 for wi, xi in zip(w, x))
    df = len(vals) - 1
    sw2 = sum(wi * wi for wi in w)
    C = W - sw2 / W
    s2 = max(0.0, (Q - df) / C) if C > 0 else 0.0
    wstar = [1.0 / (var / P + s2) for (_, P, _, var) in vals]
    Ws = sum(wstar)
    mpool = sum(wi * xi for wi, xi in zip(wstar, x)) / Ws
    se_pool = math.sqrt(1.0 / Ws)
    sc = mpool / 4.0
    e = elo_of(mpool)
    d = 400.0 / (math.log(10.0) * sc * (1.0 - sc))
    half = 1.959964 * d * (se_pool / 4.0)
    print("   Cochran Q=%.3f on %d df (Q<df means the spread is ordinary sampling noise)" % (Q, df))
    print("   between-look variance (DerSimonian-Laird) s2=%.8f in i^2 units" % s2)
    print("   random-effects pooled: mean_i=%.6f Elo=%+.2f 95%%[%+.2f,%+.2f]" % (mpool, e, e - half, e + half))
    wfix = [P / var for (_, P, _, var) in vals]
    mfix = sum(wi * xi for wi, xi in zip(wfix, x)) / sum(wfix)
    sefix = math.sqrt(1.0 / sum(wfix))
    scf = mfix / 4.0
    ef = elo_of(mfix)
    df2 = 400.0 / (math.log(10.0) * scf * (1.0 - scf))
    hf = 1.959964 * df2 * (sefix / 4.0)
    print("   fixed-effect (if s2 forced 0):  Elo=%+.2f 95%%[%+.2f,%+.2f]" % (ef, ef - hf, ef + hf))
    print()

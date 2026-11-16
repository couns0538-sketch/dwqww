import sys, math, os, json, itertools

# deepseek6 long 23: independent recount of glmflash5's jobs 23 and 24.
# Written from the gamelist format only (index|cand_side|base_side|result|ending|fen).
# No line is taken from glmflash5's job23_stats.py; the formulas below are mine
# (pair-score Elo with a pair-level variance interval, the textbook way to treat
#  two games of one opening as one unit).

GAMELIST_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
MATCHES = ["M51", "M52", "M53", "M54", "M55", "M56", "M57", "M58", "M59", "M60"]


def load(match):
    path = os.path.join(GAMELIST_DIR, "gamelist_%s.txt" % match)
    rows = []
    for lineno, line in enumerate(open(path), 1):
        line = line.rstrip("\n")
        if not line:
            continue
        f = line.split("|")
        rows.append({
            "lineno": lineno,
            "idx": f[0],
            "white": f[1],
            "black": f[2],
            "result": f[3],
            "ending": f[4],
            "fen": f[5] if len(f) > 5 else "",
            "nfields": len(f),
        })
    return rows


def pairs_of(rows):
    """Split into consecutive pairs (2k-1, 2k). Returns (pairs, dangling)."""
    pairs = []
    for i in range(0, len(rows) - 1, 2):
        pairs.append((rows[i], rows[i + 1]))
    dangling = len(rows) % 2
    return pairs, dangling


def score_game(row, cand="cand"):
    """0, 0.5 or 1.0 from the candidate's point of view."""
    if row["result"] == "1/2-1/2":
        return 0.5
    if row["result"] == "1-0":
        return 1.0 if row["white"] == cand else 0.0
    if row["result"] == "0-1":
        return 1.0 if row["black"] == cand else 0.0
    raise ValueError("unparseable result %r at line %d" % (row["result"], row["lineno"]))


def elo_from_score(sc):
    """Elo difference from a score fraction."""
    if sc <= 0.0:
        return float("-inf")
    if sc >= 1.0:
        return float("inf")
    return -400.0 * math.log10(1.0 / sc - 1.0)


def pair_summary(pairs):
    """W-L-D, n5 vector, Elo and its 95% interval on the pair score."""
    W = L = D = 0
    n5 = [0, 0, 0, 0, 0]
    for a, b in pairs:
        s = 0.0
        for row in (a, b):
            v = score_game(row)
            s += v
            if v == 0.5:
                D += 1
            elif v == 1.0:
                W += 1
            else:
                L += 1
        n5[int(round(s * 2))] += 1
    P = len(pairs)
    if P == 0:
        return dict(W=W, L=L, D=D, n5=n5, P=0)
    # pair score in [0,2] -> fraction of the 2 available points
    total = sum(i * n5[i] for i in range(5)) / 2.0
    sc = total / (2.0 * P)
    mean_i = sum(i * n5[i] for i in range(5)) / float(P)      # mean of i = 2*(pair score in points)
    # n5 index i is the pair score in HALF points (0..4); s = i/2 is the pair score in points
    # (0..2) and sc = s/2 is the fraction of the two available points. So var(i) = 4*var(s)
    # and the standard error of sc is sqrt(var_i / P) / 4.
    var_i = sum(n5[i] * (i - mean_i) ** 2 for i in range(5)) / float(P - 1) if P > 1 else 0.0
    se_sc = math.sqrt(var_i / P) / 4.0
    elo = elo_from_score(sc)
    # d(Elo)/d(score) at sc
    deriv = 400.0 / (math.log(10.0) * sc * (1.0 - sc))
    half = 1.959964 * deriv * se_sc
    return dict(W=W, L=L, D=D, n5=n5, P=P, sc=sc, elo=elo, half=half)


def pool_summary(n5s):
    n5 = [0, 0, 0, 0, 0]
    for v in n5s:
        for i in range(5):
            n5[i] += v[i]
    P = sum(n5)
    mean_i = sum(i * n5[i] for i in range(5)) / float(P)
    sc = mean_i / 4.0
    var_i = sum(n5[i] * (i - mean_i) ** 2 for i in range(5)) / float(P - 1)
    se_sc = math.sqrt(var_i / P) / 4.0
    elo = elo_from_score(sc)
    deriv = 400.0 / (math.log(10.0) * sc * (1.0 - sc))
    half = 1.959964 * deriv * se_sc
    return dict(n5=n5, P=P, sc=sc, elo=elo, half=half)


# ---- pairing and colour checks -------------------------------------------------
def pairing_report(rows, match):
    out = []
    bad = 0
    for i in range(0, len(rows) - 1, 2):
        a, b = rows[i], rows[i + 1]
        same_fen = a["fen"] == b["fen"]
        swapped = (a["white"] == b["black"] and a["black"] == b["white"])
        if not same_fen or not swapped:
            bad += 1
            if bad <= 5:
                out.append("  %s lines %d,%d: same_fen=%s swapped=%s FENa=%r FENb=%r" %
                           (match, a["lineno"], b["lineno"], same_fen, swapped, a["fen"], b["fen"]))
    wc = sum(1 for r in rows if r["white"] == "cand")
    bc = sum(1 for r in rows if r["black"] == "cand")
    nf = sorted(set(r["nfields"] for r in rows))
    return out, bad, wc, bc, nf


def ending_table(rows):
    t = {}
    for r in rows:
        t[r["ending"]] = t.get(r["ending"], 0) + 1
    return t


def decisive_ending_check(rows):
    """Every decisive game must end by mate; every drawn game must not be a mate."""
    bad = []
    for r in rows:
        winning = r["result"] in ("1-0", "0-1")
        is_mate = "mates" in r["ending"]
        if winning and not is_mate:
            bad.append(("decisive-not-mate", r["lineno"], r["result"], r["ending"]))
        if (not winning) and is_mate:
            bad.append(("draw-is-mate", r["lineno"], r["result"], r["ending"]))
    return bad


# ---- independent interval check: bootstrap over PAIRS ---------------------------
def bootstrap_elo(pairs, iters=20000, seed=20261116):
    """Resample pairs with replacement; report the 2.5/97.5 percentiles of Elo.
    This shares no algebra with the textbook formula above, so agreement between
    the two is evidence the closed form is implemented right."""
    import random
    rng = random.Random(seed)
    vals = []
    for a, b in pairs:
        vals.append(score_game(a) + score_game(b))   # pair score in points, 0..2
    P = len(vals)
    out = []
    for _ in range(iters):
        tot = 0.0
        for _ in range(P):
            tot += vals[rng.randrange(P)]
        sc = tot / (2.0 * P)
        if 0.0 < sc < 1.0:
            out.append(elo_from_score(sc))
    out.sort()
    return out[int(0.025 * len(out))], out[int(0.975 * len(out))], len(out)


def opening_key(fen):
    return " ".join(fen.split()[:4])


def main():
    data = {}
    print("== ROW COUNTS AND PAIRING")
    for m in MATCHES:
        rows = load(m)
        data[m] = rows
        pr, bad, wc, bc, nf = pairing_report(rows, m)
        print("%s rows=%d field_counts=%s cand_white=%d cand_black=%d bad_pairs=%d" %
              (m, len(rows), nf, wc, bc, bad))
        for line in pr:
            print(line)

    print()
    print("== PER MATCH (my own recount)")
    per = {}
    for m in MATCHES:
        pairs, dangling = pairs_of(data[m])
        s = pair_summary(pairs)
        per[m] = s
        print("%s rows=%d pairs=%d dangling=1" % (m, len(data[m]), s["P"]) if dangling else
              "%s rows=%d pairs=%d dangling=0" % (m, len(data[m]), s["P"]))
        print("  W-L-D=%d-%d-%d n5=%s score=%.6f Elo=%+.2f 95%%[%+.2f,%+.2f]" %
              (s["W"], s["L"], s["D"], s["n5"], s["sc"], s["elo"], s["elo"] - s["half"], s["elo"] + s["half"]))
        print("  identities: mates_carried_by_ending_table=%s" % (ending_table(data[m]),))
        et = ending_table(data[m])
        wm = et.get("White mates", 0)
        bm = et.get("Black mates", 0)
        print("  identity mates %d+%d=%d vs W+L %d+%d=%d equal=%s" %
              (wm, bm, wm + bm, s["W"], s["L"], s["W"] + s["L"], wm + bm == s["W"] + s["L"]))
        print("  identity results %d+%d+%d=%d vs 2P=%d equal=%s" %
              (s["W"], s["L"], s["D"], s["W"] + s["L"] + s["D"], 2 * s["P"], s["W"] + s["L"] + s["D"] == 2 * s["P"]))
        bad_ends = decisive_ending_check(data[m])
        print("  decisive/drawn ending consistency: %d violation(s)" % len(bad_ends))
        for b in bad_ends[:5]:
            print("    ", b)
        lo, hi, kept = bootstrap_elo(pairs)
        print("  bootstrap over pairs (20000 resamples, 2.5/97.5 pct): [%+.2f,%+.2f] (%d kept)" % (lo, hi, kept))

    print()
    print("== OPENING OVERLAP (first 4 FEN fields as the key), all 45 pairs")
    keys = {m: set(opening_key(r["fen"]) for r in data[m]) for m in MATCHES}
    print("distinct openings per match: " + " ".join("%s=%d" % (m, len(keys[m])) for m in MATCHES))
    nonzero = 0
    for a, b in itertools.combinations(MATCHES, 2):
        n = len(keys[a] & keys[b])
        if n:
            nonzero += 1
            print("  %s & %s share %d opening(s)" % (a, b, n))
    print("pairs of matches with a non-zero share: %d of 45" % nonzero)
    print("M53 vs M54 share %d (same start window, expected 1000)" % len(keys["M53"] & keys["M54"]))

    print()
    print("== POOLS (glmflash5's own groupings, recomputed on my n5)")
    pools = [
        ("variant@2000 M49+M51+M52 (3 looks, using glmflash5 M49 n5)", None),
        ("variant@2000 M51+M52+M55+M56 (4 looks I can recount)", ["M51", "M52", "M55", "M56"]),
        ("CED8alone@2000 M53+M57+M58", ["M53", "M57", "M58"]),
        ("variant@20000 M54+M59", ["M54", "M59"]),
    ]
    for tag, ms in pools:
        if ms is None:
            # M49's n5 is published in glmflash5's stats output; recompute with it
            m49 = [79, 207, 386, 208, 120]
            n5s = [m49] + [per[x]["n5"] for x in ["M51", "M52"]]
            p = pool_summary(n5s)
            print("%s: pairs=%d n5=%s Elo=%+.2f 95%%[%+.2f,%+.2f]" %
                  (tag, p["P"], p["n5"], p["elo"], p["elo"] - p["half"], p["elo"] + p["half"]))
            continue
        p = pool_summary([per[x]["n5"] for x in ms])
        print("%s: pairs=%d n5=%s Elo=%+.2f 95%%[%+.2f,%+.2f]" %
              (tag, p["P"], p["n5"], p["elo"], p["elo"] - p["half"], p["elo"] + p["half"]))

    with open("recount.json", "w") as f:
        json.dump({m: {k: v for k, v in per[m].items()} for m in MATCHES}, f, indent=1, sort_keys=True)


main()
